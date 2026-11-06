"""Finnish table of frequency allocations (Regulation M4 via the Traficom open-data API).

The API returns one row per (sub-band, service, usage, comment). Rows are merged into
*allocation units* keyed by (sub-band, service, usage, direction, class of station), so
seven comment lines for the same amateur sub-band become one unit with seven notes.

Convention used by the table: a service written in CAPITALS is a primary allocation,
mixed case is secondary (the same convention as Article 5 of the Radio Regulations).
"""
from __future__ import annotations

import gzip
import json
import os
import urllib.request
from dataclasses import dataclass, field
from functools import lru_cache
from typing import Optional

from .common import gap_mhz, overlap_mhz

REFERENCE_DIR = os.path.join(os.path.dirname(__file__), "reference")
DEFAULT_SNAPSHOT = os.path.join(REFERENCE_DIR, "taajuusjakotaulukko_2026-11-06.json.gz")
API_URL = "https://opendata.traficom.fi/api/v13/Taajuusjakotaulukko"


@dataclass
class AllocationUnit:
    unit_id: str
    row_ids: list[int]
    f_min_mhz: float
    f_max_mhz: float
    service: str
    usage: str
    direction: str            # TX | RX | TXRX | ''
    station_class: str
    band_label: str           # e.g. "10.000 GHz-10.450 GHz"
    notes: list[str] = field(default_factory=list)

    @property
    def label(self) -> str:
        parts = [f"{self.f_min_mhz:g}-{self.f_max_mhz:g} MHz", self.service or "(no service)"]
        if self.usage:
            parts.append(self.usage)
        return " | ".join(parts)

    @property
    def bandwidth_mhz(self) -> float:
        return self.f_max_mhz - self.f_min_mhz

    @property
    def allocated(self) -> bool:
        return bool(self.service) and "not allocated" not in self.service.lower()

    @property
    def primary(self) -> bool:
        s = self.service
        return self.allocated and any(c.isalpha() for c in s) and s == s.upper()

    @property
    def secondary(self) -> bool:
        return self.allocated and not self.primary

    @property
    def is_space_service(self) -> bool:
        s = self.service.upper()
        return "SATELLITE" in s or "SPACE" in s

    @property
    def is_space_to_earth(self) -> bool:
        return "SPACE-TO-EARTH" in self.service.upper()

    @property
    def is_earth_to_space(self) -> bool:
        return "EARTH-TO-SPACE" in self.service.upper()

    @property
    def is_passive(self) -> bool:
        s = self.service.upper()
        return "RADIO ASTRONOMY" in s or "(PASSIVE)" in s

    @property
    def source_ref(self) -> str:
        ids = ",".join(str(i) for i in self.row_ids[:6])
        more = f" (+{len(self.row_ids) - 6} more)" if len(self.row_ids) > 6 else ""
        return f"M4 Taajuusjakotaulukko ID {ids}{more}"


class FinnishTable:
    def __init__(self, rows: list[dict], meta: Optional[dict] = None):
        self.rows = rows
        self.meta = meta or {}
        self.units = self._build_units(rows)

    # ------------------------------------------------------------------ loading
    @classmethod
    @lru_cache(maxsize=2)
    def load(cls, path: Optional[str] = None) -> "FinnishTable":
        path = path or DEFAULT_SNAPSHOT
        opener = gzip.open if path.endswith(".gz") else open
        with opener(path, "rt", encoding="utf-8") as fh:
            data = json.load(fh)
        if isinstance(data, dict) and "rows" in data:
            return cls(data["rows"], data.get("meta"))
        return cls(data, {})

    @classmethod
    def fetch(cls, save_to: Optional[str] = None, page: int = 1000) -> "FinnishTable":
        """Download the full table from the Traficom API (OData paging)."""
        rows: list[dict] = []
        skip = 0
        while True:
            url = f"{API_URL}?%24top={page}&%24skip={skip}"
            with urllib.request.urlopen(url, timeout=60) as r:
                chunk = json.load(r).get("value", [])
            rows.extend(chunk)
            if len(chunk) < page:
                break
            skip += page
        meta = {"source": API_URL, "rows": len(rows)}
        if save_to:
            with gzip.open(save_to, "wt", encoding="utf-8") as fh:
                json.dump({"meta": meta, "rows": rows}, fh, ensure_ascii=False, separators=(",", ":"))
        return cls(rows, meta)

    # ------------------------------------------------------------------ units
    @staticmethod
    def _build_units(rows: list[dict]) -> list[AllocationUnit]:
        groups: dict[tuple, AllocationUnit] = {}
        for r in rows:
            lo = r.get("Sub_band_lower_limit__Hz_")
            hi = r.get("Sub_band_upper_limit__Hz_")
            if lo is None or hi is None:
                continue
            key = (lo, hi, r.get("Services_in_Finland", ""), r.get("Sub_band_usage", ""),
                   r.get("Direction", ""), r.get("Class_of_station", ""))
            unit = groups.get(key)
            if unit is None:
                unit = AllocationUnit(
                    unit_id=f"M4-{r['ID']}", row_ids=[], f_min_mhz=lo / 1e6, f_max_mhz=hi / 1e6,
                    service=r.get("Services_in_Finland", "") or "", usage=r.get("Sub_band_usage", "") or "",
                    direction=r.get("Direction", "") or "", station_class=r.get("Class_of_station", "") or "",
                    band_label=f"{r.get('Frequency_band_lower_limit', '')}-{r.get('Frequency_band_upper_limit', '')}")
                groups[key] = unit
            unit.row_ids.append(int(r["ID"]))
            for k in ("Additional_information", "Comment"):
                v = (r.get(k) or "").strip()
                if v and v not in unit.notes:
                    unit.notes.append(v)
        units = sorted(groups.values(), key=lambda u: (u.f_min_mhz, u.f_max_mhz, u.service))
        for u in units:
            u.unit_id = f"M4-{min(u.row_ids)}"
        return units

    # ------------------------------------------------------------------ queries
    def overlapping(self, f_min_mhz: float, f_max_mhz: float) -> list[tuple[AllocationUnit, float]]:
        out = []
        for u in self.units:
            if u.f_min_mhz >= f_max_mhz:
                break
            ov = overlap_mhz(f_min_mhz, f_max_mhz, u.f_min_mhz, u.f_max_mhz)
            if ov > 0:
                out.append((u, ov))
        return out

    def adjacent(self, f_min_mhz: float, f_max_mhz: float, guard_mhz: float) -> list[tuple[AllocationUnit, float]]:
        """Units that do not overlap but lie within guard_mhz of the interval."""
        out = []
        for u in self.units:
            if u.f_min_mhz > f_max_mhz + guard_mhz:
                break
            if overlap_mhz(f_min_mhz, f_max_mhz, u.f_min_mhz, u.f_max_mhz) > 0:
                continue
            g = gap_mhz(f_min_mhz, f_max_mhz, u.f_min_mhz, u.f_max_mhz)
            if g <= guard_mhz:
                out.append((u, g))
        return out

    # ------------------------------------------------------------------ interpretation
    @staticmethod
    def sensitivity(unit: AllocationUnit, cfg: dict) -> tuple[float, str]:
        """(tier in [0,1], label) from the configured keyword rules."""
        rules = cfg["finnish_sensitivity"]
        s = unit.service.upper()
        u = unit.usage.upper()
        for rule in rules["rules"]:
            if any(k.upper() in s for k in rule.get("service_any", [])) or any(k.upper() in u for k in rule.get("usage_any", [])):
                return float(rule["tier"]), rule["label"]
        if unit.primary:
            return float(rules["default_primary"]), "Primary allocation (no specific rule)"
        if unit.secondary:
            return float(rules["default_secondary"]), "Secondary allocation (no specific rule)"
        if unit.usage:
            return float(rules["default_usage_only"]), "Usage listed without a service allocation"
        return float(rules["default_none"]), "Not allocated in Finland"

    @staticmethod
    def status_value(unit: AllocationUnit, cfg: dict) -> tuple[float, str]:
        st = cfg["space"]["status"]
        if unit.primary:
            return float(st["primary"]), "primary"
        if unit.secondary:
            return float(st["secondary"]), "secondary"
        if unit.usage:
            return float(st["usage_only"]), "usage only"
        return float(st["unallocated"]), "not allocated"


if __name__ == "__main__":  # python -m scoring.finnish_table fetch [path]
    import sys
    if len(sys.argv) >= 2 and sys.argv[1] == "fetch":
        target = sys.argv[2] if len(sys.argv) > 2 else DEFAULT_SNAPSHOT
        t = FinnishTable.fetch(save_to=target)
        print(f"fetched {len(t.rows)} rows -> {target}; {len(t.units)} allocation units")
    else:
        t = FinnishTable.load()
        print(f"{len(t.rows)} rows, {len(t.units)} allocation units; snapshot meta: {t.meta}")
