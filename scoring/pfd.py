"""Power flux-density at the Earth's surface and comparison with Article 21 Table 21-4.

pfd (dB(W/m2) in the reference bandwidth) =
    power density at the antenna input (dBW/Hz)           [emiss.pwr_ds_max]
  + 10 log10(min(reference bandwidth, emission bandwidth)) [grp/freq.bdwdth]
  + maximum antenna gain (dBi)                            [s_beam.gain]
  - 10 log10(4 * pi * d^2)                                 [spreading loss, d in metres]

This is a worst-case estimate: maximum gain is assumed towards Finland (the beam
contours from GIMS are not used), and no atmospheric loss is subtracted. The margin
is limit - pfd; negative means the limit is exceeded. Results are always labelled
indicative; the Bureau's own finding (GIBC) is authoritative.
"""
from __future__ import annotations

import json
import math
import os
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Optional

from .geometry import FINLAND_REFERENCE_POINTS, gso_geometry, slant_range_km

REFERENCE_DIR = os.path.join(os.path.dirname(__file__), "reference")
TABLE_FILE = os.path.join(REFERENCE_DIR, "rr_article21_table21-4.json")


@dataclass
class PfdAssessment:
    pfd_dbw_m2: float
    limit_dbw_m2: Optional[float]
    margin_db: Optional[float]          # limit - pfd; negative = exceeds
    elev_deg: float
    slant_range_km: float
    ref_bw_hz: int
    point_name: str
    limit_row_id: Optional[str]
    limit_verified: bool
    formula: str
    assumptions: list[str] = field(default_factory=list)

    @property
    def exceeds(self) -> Optional[bool]:
        return None if self.margin_db is None else self.margin_db < 0


class Article21Table:
    def __init__(self, data: dict):
        self.data = data
        self.rows = data["rows"]

    @classmethod
    @lru_cache(maxsize=1)
    def load(cls, path: Optional[str] = None) -> "Article21Table":
        with open(path or TABLE_FILE, encoding="utf-8") as fh:
            return cls(json.load(fh))

    def find(self, f_min_mhz: float, f_max_mhz: float, orbit_kind: str) -> list[dict]:
        """Rows whose band overlaps the interval and whose orbit type matches (or is 'any')."""
        out = []
        for row in self.rows:
            if not row.get("applies_to_finland", True):
                continue
            if row["orbit"] not in ("any", orbit_kind):
                continue
            for lo, hi in row["bands_mhz"]:
                if min(hi, f_max_mhz) > max(lo, f_min_mhz):
                    out.append(row)
                    break
        return out

    @staticmethod
    def limit_db(row: dict, elev_deg: float) -> float:
        e = max(0.0, min(90.0, elev_deg))
        for seg in row["segments"]:
            if seg["from_deg"] < e <= seg["to_deg"] or (e == 0 and seg["from_deg"] == 0):
                return seg["base_db"] + seg["slope_db_per_deg"] * (e - seg["ref_deg"])
        return row["segments"][-1]["base_db"]


def spreading_loss_db(d_km: float) -> float:
    return 10.0 * math.log10(4.0 * math.pi * (d_km * 1000.0) ** 2)


def power_density_dbw_hz(pwr_ds_max_dbw_hz: Optional[float], pep_max_dbw: Optional[float],
                         bandwidth_khz: Optional[float]) -> tuple[Optional[float], str]:
    if pwr_ds_max_dbw_hz is not None:
        return pwr_ds_max_dbw_hz, "emiss.pwr_ds_max"
    if pep_max_dbw is not None and bandwidth_khz:
        return pep_max_dbw - 10.0 * math.log10(bandwidth_khz * 1000.0), "emiss.pep_max - 10log10(bandwidth)"
    return None, "unavailable"


def pfd_at_ground(pwr_ds_dbw_hz: float, gain_dbi: float, d_km: float, ref_bw_hz: int,
                  emission_bw_hz: Optional[float] = None) -> tuple[float, str]:
    bw = ref_bw_hz if not emission_bw_hz else min(ref_bw_hz, emission_bw_hz)
    pfd = pwr_ds_dbw_hz + 10.0 * math.log10(bw) + gain_dbi - spreading_loss_db(d_km)
    formula = (f"pfd = {pwr_ds_dbw_hz:.1f} dBW/Hz + 10log10({bw:g} Hz) + {gain_dbi:.1f} dBi"
               f" - 10log10(4*pi*({d_km:.0f} km)^2) = {pfd:.1f} dB(W/m2) in {ref_bw_hz / 1000:g} kHz")
    return pfd, formula


def _assess_at(pwr_ds: float, gain: float, d_km: float, elev: float, row: Optional[dict], ref_bw: int,
               emission_bw_hz: Optional[float], point: str, assumptions: list[str]) -> PfdAssessment:
    pfd, formula = pfd_at_ground(pwr_ds, gain, d_km, ref_bw, emission_bw_hz)
    limit = Article21Table.limit_db(row, elev) if row else None
    return PfdAssessment(
        pfd_dbw_m2=pfd, limit_dbw_m2=limit, margin_db=(limit - pfd) if limit is not None else None,
        elev_deg=elev, slant_range_km=d_km, ref_bw_hz=ref_bw, point_name=point,
        limit_row_id=row["id"] if row else None, limit_verified=bool(row and row.get("verified")),
        formula=formula, assumptions=list(assumptions))


def assess_gso(pwr_ds: float, gain: float, sat_lon: float, f_min_mhz: float, f_max_mhz: float,
               emission_bw_hz: Optional[float], cfg: dict) -> Optional[PfdAssessment]:
    """Worst-case (lowest margin) pfd assessment over the Finnish reference points that see the satellite."""
    table = Article21Table.load()
    rows = table.find(f_min_mhz, f_max_mhz, "GSO")
    row = rows[0] if rows else None
    ref_bw = row["ref_bw_hz"] if row else 4000
    assumptions = ["maximum beam gain assumed towards Finland", "no atmospheric or polarisation loss"]
    if row and not row.get("verified"):
        assumptions.append(f"limit row {row['id']} not yet verified against RR 2024 Table 21-4")
    if not row:
        assumptions.append("no Table 21-4 hard limit for this band; pfd reported for information only")
    best: Optional[PfdAssessment] = None
    for name, lat, lon in FINLAND_REFERENCE_POINTS:
        g = gso_geometry(lat, lon, sat_lon)
        if g["elevation_deg"] <= 0:
            continue
        a = _assess_at(pwr_ds, gain, g["slant_range_km"], g["elevation_deg"], row, ref_bw, emission_bw_hz, name, assumptions)
        key = a.margin_db if a.margin_db is not None else -a.pfd_dbw_m2
        if best is None or key < (best.margin_db if best.margin_db is not None else -best.pfd_dbw_m2):
            best = a
    return best


def assess_ngso(pwr_ds: float, gain: float, altitude_km: float, f_min_mhz: float, f_max_mhz: float,
                emission_bw_hz: Optional[float], cfg: dict) -> Optional[PfdAssessment]:
    """Worst-case pfd assessment over a set of elevation angles (config pfd.ngso_elevation_samples_deg)."""
    table = Article21Table.load()
    rows = table.find(f_min_mhz, f_max_mhz, "NGSO")
    row = rows[0] if rows else None
    ref_bw = row["ref_bw_hz"] if row else 4000
    assumptions = ["single satellite, maximum beam gain assumed towards the ground point", "circular orbit at mean altitude", "no atmospheric loss"]
    if row and not row.get("verified"):
        assumptions.append(f"limit row {row['id']} not yet verified against RR 2024 Table 21-4")
    if not row:
        assumptions.append("no Table 21-4 hard limit for this band; pfd reported for information only")
    best: Optional[PfdAssessment] = None
    for elev in cfg["space"]["pfd"]["ngso_elevation_samples_deg"]:
        d = slant_range_km(altitude_km, float(elev))
        a = _assess_at(pwr_ds, gain, d, float(elev), row, ref_bw, emission_bw_hz, f"elevation {elev} deg", assumptions)
        key = a.margin_db if a.margin_db is not None else -a.pfd_dbw_m2
        if best is None or key < (best.margin_db if best.margin_db is not None else -best.pfd_dbw_m2):
            best = a
    return best
