"""Step A6 of pm_pack/08: the Finnish frequency allocation table (Traficom open data, CC BY 4.0) as FinnishSubBand rows.

Source: https://opendata.traficom.fi/api/v13/Taajuusjakotaulukko, snapshot data/raw/taajuusjakotaulukko.json (2026-11-06).
Each row keeps its Traficom `ID`, so every match can be cited as `Taajuusjakotaulukko.ID=<id>`.
Limits are taken from the API's integer Hz fields (`Sub_band_lower_limit__Hz_`, `Sub_band_upper_limit__Hz_`),
never re-parsed from the text fields.

    uv run python -m radar.adapters.traficom_table        # writes data/derived/fi_subbands.parquet
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

import duckdb

from radar.config import settings
from radar.models import Evidence, FinnishSubBand

SOURCE_NAME = "Traficom Taajuusjakotaulukko API v13 (snapshot 2026-11-06)"
SOURCE_URL = "https://opendata.traficom.fi/api/v13/Taajuusjakotaulukko"


def _blank_to_none(v: object) -> str | None:
    return None if v is None or (isinstance(v, str) and not v.strip()) else str(v)


def load_json(path: Path | None = None) -> list[FinnishSubBand]:
    path = path or settings.raw_dir / "taajuusjakotaulukko.json"
    rows = json.loads(path.read_text(encoding="utf-8"))["value"]
    return [
        FinnishSubBand(
            id=r["ID"],
            lower_hz=int(r["Sub_band_lower_limit__Hz_"]),
            upper_hz=int(r["Sub_band_upper_limit__Hz_"]),
            services_in_finland=r["Services_in_Finland"],
            sub_band_usage=r["Sub_band_usage"],
            class_of_station=_blank_to_none(r.get("Class_of_station")),
            direction=_blank_to_none(r.get("Direction")),
            comment=_blank_to_none(r.get("Comment")),
        )
        for r in rows
    ]


def write_parquet(bands: list[FinnishSubBand], out: Path | None = None) -> Path:
    out = out or settings.derived_dir / "fi_subbands.parquet"
    out.parent.mkdir(parents=True, exist_ok=True)
    import pyarrow as pa
    import pyarrow.parquet as pq

    table = pa.Table.from_pylist([b.model_dump() for b in bands])
    pq.write_table(table, out)
    return out


@lru_cache(maxsize=1)
def _cached(path: str) -> tuple[FinnishSubBand, ...]:
    p = Path(path)
    if p.suffix == ".parquet" and p.exists():
        rows = duckdb.sql(f"SELECT * FROM read_parquet('{p}') ORDER BY lower_hz, id").fetchall()
        cols = list(FinnishSubBand.model_fields)
        return tuple(FinnishSubBand(**dict(zip(cols, r))) for r in rows)
    return tuple(sorted(load_json(), key=lambda b: (b.lower_hz, b.id)))


def subbands(path: Path | None = None) -> tuple[FinnishSubBand, ...]:
    return _cached(str(path or settings.derived_dir / "fi_subbands.parquet"))


def at_frequency(hz: int, bands: tuple[FinnishSubBand, ...] | None = None) -> list[FinnishSubBand]:
    """Sub-bands containing hz. Lower edge inclusive, upper edge exclusive, except the very top of the table."""
    bands = bands or subbands()
    return [b for b in bands if b.lower_hz <= hz < b.upper_hz]


def overlapping(lower_hz: int, upper_hz: int, bands: tuple[FinnishSubBand, ...] | None = None) -> list[tuple[FinnishSubBand, int]]:
    """Sub-bands overlapping [lower_hz, upper_hz] with the overlap width in Hz (pm_pack/06 formula)."""
    bands = bands or subbands()
    out = []
    for b in bands:
        overlap = max(0, min(upper_hz, b.upper_hz) - max(lower_hz, b.lower_hz))
        if overlap > 0:
            out.append((b, overlap))
    return out


def evidence(band: FinnishSubBand, evidence_id: str) -> Evidence:
    return Evidence(
        id=evidence_id,
        kind="finnish_table_row",
        source=SOURCE_NAME,
        locator=f"Taajuusjakotaulukko.ID={band.id}",
        excerpt=f"{band.lower_hz}-{band.upper_hz} Hz: {band.services_in_finland} / {band.sub_band_usage}",
    )


M4_SOURCE = ("Traficom Regulation M4, Radio Frequency Regulation 4 AG/2026 M (Finlex, traficom-viestinta 2026/3); "
             "its frequency allocation table as published in the Taajuusjakotaulukko API")
M4_LOCATOR_PREFIX = "M4 4 AG/2026 M, Taajuusjakotaulukko.ID="


def m4_evidence(band: FinnishSubBand, evidence_id: str) -> Evidence:
    """The regulation behind a Finnish-table match: Regulation M4 sets the Finnish use of the sub-band.
    evidence_check rebuilds the excerpt from the same snapshot row."""
    return Evidence(
        id=evidence_id,
        kind="regulation",
        source=M4_SOURCE,
        locator=f"{M4_LOCATOR_PREFIX}{band.id}",
        excerpt=f"Regulation M4: Finnish use of {band.lower_hz}-{band.upper_hz} Hz is {band.services_in_finland}",
    )


def coverage_gaps(bands: tuple[FinnishSubBand, ...]) -> list[tuple[int, int]]:
    """Ranges between the lowest and highest limit that no sub-band covers (union of all rows)."""
    gaps, reach = [], None
    for b in sorted(bands, key=lambda b: b.lower_hz):
        if reach is not None and b.lower_hz > reach:
            gaps.append((reach, b.lower_hz))
        reach = b.upper_hz if reach is None else max(reach, b.upper_hz)
    return gaps


def main() -> int:
    bands = load_json()
    out = write_parquet(bands)
    _cached.cache_clear()
    print(f"{out}: {len(bands)} sub-bands, {bands and min(b.lower_hz for b in bands)} Hz to "
          f"{max(b.upper_hz for b in bands)} Hz, gaps: {len(coverage_gaps(tuple(bands)))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
