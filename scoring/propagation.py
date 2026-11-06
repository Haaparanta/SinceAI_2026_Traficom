"""Field-strength models for the terrestrial side and the T/R 25-08 trigger lookup.

The challenge brief asks for ITU-R P.1546. No stdlib implementation exists here yet, so
the package ships:

* FreeSpaceModel: E = 76.9 + e.r.p.(dBW) - 20 log10(d_km) dB(uV/m). This is an UPPER
  BOUND (P.1546 never predicts more than free space on land paths; sea paths at 10 % time
  can approach it). It is used only to screen: if even free space stays below the
  trigger, no coordination case is possible. It never confirms a case.
* P1546Model: a hook that imports an external `p1546` module if the team installs one
  (for example a port of the ITU/OFCOM reference implementation). Until then the
  scorer reports the field-strength factor as "not evaluated" and lowers confidence.

To plug in a real model, implement `predict(freq_mhz, erp_dbw, h_tx_m, d_km, path, time_pct, h_rx_m)`
returning dB(uV/m) and register it with `register_model(name, callable)`.
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Callable, Optional

REFERENCE_DIR = os.path.join(os.path.dirname(__file__), "reference")
TR2508_FILE = os.path.join(REFERENCE_DIR, "tr_25-08_thresholds.json")

FREE_SPACE_CONST_ERP = 76.9   # dB(uV/m) at 1 km for 1 W e.r.p. (106.9 for 1 kW)


@dataclass
class FieldStrength:
    value_dbuv_m: float
    model: str
    upper_bound: bool
    assumptions: list[str] = field(default_factory=list)
    inputs: dict = field(default_factory=dict)


class ModelUnavailable(RuntimeError):
    pass


def free_space_dbuv_m(erp_dbw: float, d_km: float) -> float:
    d = max(d_km, 0.001)
    return FREE_SPACE_CONST_ERP + erp_dbw - 20.0 * math.log10(d)


class FreeSpaceModel:
    name = "free-space (upper bound)"
    upper_bound = True

    def predict(self, freq_mhz: float, erp_dbw: float, h_tx_m: Optional[float], d_km: float,
                path: str = "land", time_pct: float = 10.0, h_rx_m: float = 10.0) -> FieldStrength:
        e = free_space_dbuv_m(erp_dbw, d_km)
        return FieldStrength(
            value_dbuv_m=e, model=self.name, upper_bound=True,
            assumptions=["free-space propagation: an upper bound, not a prediction", f"path type {path} ignored"],
            inputs={"freq_mhz": freq_mhz, "erp_dbw": erp_dbw, "d_km": d_km, "h_tx_m": h_tx_m, "time_pct": time_pct, "h_rx_m": h_rx_m})


_REGISTRY: dict[str, Callable] = {}


def register_model(name: str, predict: Callable[..., float]) -> None:
    """Register an external propagation model (for example a P.1546 implementation)."""
    _REGISTRY[name] = predict


class P1546Model:
    name = "ITU-R P.1546"
    upper_bound = False

    def __init__(self) -> None:
        self._predict = _REGISTRY.get("p1546")
        if self._predict is None:
            try:
                import p1546  # type: ignore  # external, optional
                self._predict = getattr(p1546, "predict")
            except Exception as exc:  # noqa: BLE001
                raise ModelUnavailable("No P.1546 implementation registered; see propagation.py docstring") from exc

    def predict(self, freq_mhz: float, erp_dbw: float, h_tx_m: Optional[float], d_km: float,
                path: str = "land", time_pct: float = 10.0, h_rx_m: float = 10.0) -> FieldStrength:
        value = float(self._predict(freq_mhz, erp_dbw, h_tx_m if h_tx_m is not None else 10.0, d_km, path, time_pct, h_rx_m))
        return FieldStrength(value_dbuv_m=value, model=self.name, upper_bound=False,
                             assumptions=[f"P.1546 {path} path, {time_pct:g} % time, 50 % locations, receiver at {h_rx_m:g} m"],
                             inputs={"freq_mhz": freq_mhz, "erp_dbw": erp_dbw, "d_km": d_km, "h_tx_m": h_tx_m, "time_pct": time_pct, "h_rx_m": h_rx_m})


def get_model(name: str = "auto"):
    """'auto' returns P.1546 when available, otherwise free space."""
    if name in ("auto", "p1546"):
        try:
            return P1546Model()
        except ModelUnavailable:
            if name == "p1546":
                raise
    return FreeSpaceModel()


def erp_dbw_from_notified(pwr_dbw: Optional[float], pwr_type: str) -> tuple[Optional[float], str]:
    """Convert a notified radiated power to e.r.p. (dBW). E = e.r.p., I = e.i.r.p., V = e.m.r.p."""
    if pwr_dbw is None:
        return None, "no radiated power"
    t = (pwr_type or "E").upper()
    if t == "I":
        return pwr_dbw - 2.15, "e.i.r.p. - 2.15 dB"
    if t == "V":
        return pwr_dbw + 2.62, "e.m.r.p. + 2.62 dB"
    return pwr_dbw, "e.r.p. as notified"


@lru_cache(maxsize=1)
def _tr2508() -> dict:
    with open(TR2508_FILE, encoding="utf-8") as fh:
        return json.load(fh)


def tr2508_threshold(freq_mhz: float, bandwidth_khz: Optional[float]) -> Optional[dict]:
    """T/R 25-08 Annex 1 indicative coordination threshold for a land-mobile frequency.

    Returns None outside 29.7-470 MHz. The bandwidth correction BC = 10 log10(channel/25 kHz)
    applies to channel spacings above 25 kHz with uniform power distribution.
    """
    data = _tr2508()
    for row in data["narrowband_thresholds"]:
        if row["f_min_mhz"] <= freq_mhz < row["f_max_mhz"] or (freq_mhz == row["f_max_mhz"] == 470.0):
            base = float(row["threshold_dbuv_m"])
            bc = 0.0
            if bandwidth_khz and bandwidth_khz > 25.0:
                bc = 10.0 * math.log10(bandwidth_khz / 25.0)
            return {"threshold_dbuv_m": base + bc, "base_dbuv_m": base, "bandwidth_correction_db": bc,
                    "band": f"{row['f_min_mhz']:g}-{row['f_max_mhz']:g} MHz", "source": data["source"],
                    "conditions": data["scope"]}
    return None
