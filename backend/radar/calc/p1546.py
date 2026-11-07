"""Step C3 of pm_pack/08: field strength with the ITU-R P.1546-6 reference implementation.

Engine: Py1546 6.1 by Ivica Stevanovic (OFCOM/BAKOM), the reference code approved by ITU-R Working Party 3K,
pinned in pyproject.toml to commit e235629009ab1a12a33fc4a8fb5612f2883ecb5b (source audited; sha-256 of P1546.py
3440acda732dcc89d5a66436ffa1e0c084609867171cd280f2ef05437def5a5a). Its own validation suite (52 ITU reference
cases) reproduces the published results to 0.0 dB on this machine (pm_pack/08 C3).

Compatibility: Py1546 calls np.mat, which NumPy 2 removed; np.mat was an alias of np.asmatrix in NumPy 1.x, so the
alias is restored before import. The reference code itself is not modified.

Inputs follow ECC/ERC Recommendation T/R 25-08 Annex 1: 10 % of time, 50 % of locations, receiving antenna 10 m above
ground, field strength at the border line. pathinfo = 0 (no terrain profile). heff is the notice's filed effective
height towards the receiver where it files one (else its height above ground, stated in every trace); ha, the antenna
height above ground, lets the engine apply Annex 5 section 3.1.1 on land paths shorter than 15 km:
h1 = ha for d <= 3 km, h1 = ha + (heff - ha)(d - 3)/12 for 3 < d < 15 km, h1 = heff from 15 km.
"""
from __future__ import annotations

import contextlib
import io
import math
from dataclasses import dataclass, field

import numpy as np

if not hasattr(np, "mat"):          # NumPy 2: restore the alias Py1546 uses (identical to np.asmatrix in NumPy 1.x)
    np.mat = np.asmatrix

from Py1546 import P1546  # noqa: E402

ENGINE = "ITU-R P.1546-6 reference implementation (Py1546 6.1, commit e2356290)"
TIME_PCT = 10.0          # T/R 25-08 Annex 1
LOCATION_PCT = 50.0
RX_HEIGHT_M = 10.0
RX_CLUTTER_M = 10.0      # representative clutter height, rural receiver (P.1546 default for 'Land' rural)
FREE_SPACE_1KW_1KM = 106.9   # dB(uV/m) for 1 kW e.r.p. at 1 km


def free_space_dbuv_m(erp_dbw: float, d_km: float) -> float:
    return FREE_SPACE_1KW_1KM + (erp_dbw - 30.0) - 20 * math.log10(max(d_km, 0.001))


def short_path_h1(d_km: float, heff_m: float, ha_m: float) -> float:
    """P.1546-6 Annex 5 section 3.1.1, no terrain information: h1 on a land path shorter than 15 km."""
    if d_km <= 3:
        return ha_m
    return ha_m + (heff_m - ha_m) * (d_km - 3.0) / 12.0 if d_km < 15 else heff_m


@dataclass
class FieldStrengthResult:
    e_dbuv_m: float
    free_space_dbuv_m: float
    inputs: dict
    notes: list[str] = field(default_factory=list)


def field_strength(f_mhz: float, segments: list[tuple[float, str]], heff_m: float, erp_dbw: float,
                   time_pct: float = TIME_PCT, rx_height_m: float = RX_HEIGHT_M, ha_m: float | None = None) -> FieldStrengthResult:
    """E in dB(uV/m) at the end of a path given as [(length_km, 'Land' | 'Cold' | 'Warm' | 'Sea'), ...]
    from the transmitter, for the station's e.r.p. (Py1546 scales with PTx in kW e.r.p.)."""
    d_v = [round(d, 4) for d, _ in segments]
    path_c = [p for _, p in segments]
    ptx_kw = 10 ** (erp_dbw / 10) / 1000.0
    area = "Sea" if path_c[-1] in ("Sea", "Cold", "Warm") else "Rural"   # receiver environment: rural (R2 = 10 m)
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        e, _lb = P1546.bt_loss(f_mhz, time_pct, heff_m, rx_height_m, RX_CLUTTER_M, area, d_v, path_c, 0,
                               LOCATION_PCT, [], ptx_kw, [] if ha_m is None else ha_m)
    engine_notes = sorted({line.strip() for line in buf.getvalue().splitlines() if line.strip()})
    e = float(np.asarray(e).ravel()[0])
    d_tot = sum(d_v)
    fs = free_space_dbuv_m(erp_dbw, d_tot)
    return FieldStrengthResult(round(e, 2), round(fs, 2), {
        "f_mhz": f_mhz, "time_pct": time_pct, "location_pct": LOCATION_PCT, "heff_m": heff_m, "ha_m": ha_m, "h2_m": rx_height_m,
        "R2_m": RX_CLUTTER_M, "receiver_area": area, "d_v_km": d_v, "path_c": path_c, "d_km": round(d_tot, 3),
        "ptx_kw_erp": ptx_kw, "erp_dbw": erp_dbw,
    }, notes=[f"{ENGINE}; t {time_pct:g} %, q {LOCATION_PCT:g} %, h2 {rx_height_m:g} m, no terrain profile (pathinfo 0)"]
             + ([f"land path of {d_tot:.1f} km, under 15 km: the engine uses h1 = {short_path_h1(d_tot, heff_m, ha_m):.1f} m "
                 f"from ha {ha_m:g} m and heff {heff_m:g} m (Annex 5 section 3.1.1, equations 4 and 5)"]
                if ha_m is not None and d_tot < 15 and all(p == "Land" for p in path_c) else [])
             + [f"engine: {n}" for n in engine_notes])
