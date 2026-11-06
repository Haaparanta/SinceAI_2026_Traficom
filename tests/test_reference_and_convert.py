"""Checks for steps A5 and A6 of pm_pack/08. They read the same summary JSON the HTML reports show.

Tests that need data/raw or data/derived skip when the data is not present (fresh clone, CI).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from radar.adapters import traficom_table as T
from radar.config import settings
from radar.models import FinnishSubBand

RAW_TABLE = settings.raw_dir / "taajuusjakotaulukko.json"
needs_table = pytest.mark.skipif(not RAW_TABLE.exists(), reason="data/raw/taajuusjakotaulukko.json not present")


def band(id_: int, lo: int, hi: int, services: str = "FIXED") -> FinnishSubBand:
    return FinnishSubBand(id=id_, lower_hz=lo, upper_hz=hi, services_in_finland=services, sub_band_usage="x")


# ---- pure logic, always runs --------------------------------------------------------------------------------

def test_overlap_is_computed_in_hz_with_pm_pack_formula():
    bands = (band(1, 100, 200), band(2, 150, 400), band(3, 500, 600))
    hits = {b.id: w for b, w in T.overlapping(180, 520, bands)}
    assert hits == {1: 20, 2: 220, 3: 20}


def test_touching_edges_do_not_overlap():
    assert T.overlapping(200, 300, (band(1, 100, 200),)) == []


def test_at_frequency_lower_edge_inclusive_upper_exclusive():
    bands = (band(1, 100, 200), band(2, 200, 300))
    assert [b.id for b in T.at_frequency(200, bands)] == [2]
    assert [b.id for b in T.at_frequency(100, bands)] == [1]


def test_coverage_gaps_use_the_union_of_overlapping_rows():
    bands = (band(1, 0, 100), band(2, 50, 150), band(3, 200, 300))
    assert T.coverage_gaps(bands) == [(150, 200)]


def test_evidence_points_at_the_traficom_id():
    e = T.evidence(band(4438, 10_700_000_000, 11_700_000_000, "FIXED SATELLITE (SPACE-TO-EARTH)"), "E-0001")
    assert e.locator == "Taajuusjakotaulukko.ID=4438"
    assert e.kind == "finnish_table_row"


# ---- real data ----------------------------------------------------------------------------------------------

@needs_table
def test_table_has_5917_rows_unique_ids_positive_widths():
    bands = T.load_json()
    assert len(bands) == 5917
    assert len({b.id for b in bands}) == 5917
    assert all(b.upper_hz > b.lower_hz for b in bands)


@needs_table
@pytest.mark.parametrize("hz, needle", [
    (100_000_000, "BROADCASTING"),
    (1_575_420_000, "RADIONAVIGATION-SATELLITE"),
    (11_000_000_000, "FIXED SATELLITE"),
])
def test_known_frequencies_resolve(hz, needle):
    assert any(needle in b.services_in_finland for b in T.at_frequency(hz, tuple(T.load_json())))


@needs_table
def test_api_returns_rows_for_11_ghz():
    from radar.main import app

    r = TestClient(app).get("/reference/subbands", params={"hz": 11_000_000_000})
    assert r.status_code == 200
    rows = r.json()
    assert rows and all(row["lower_hz"] <= 11_000_000_000 < row["upper_hz"] for row in rows)


@pytest.mark.parametrize("name", ["space_3074", "terrestrial_3075", "terrestrial_3076"])
def test_conversion_row_counts_match(name):
    summary = settings.reports_dir / "convert" / f"{name}.summary.json"
    if not summary.exists():
        pytest.skip(f"{summary} not present; run make convert")
    s = json.loads(summary.read_text())
    assert s["failed"] == [], f"row count mismatch in {s['failed']}"
    assert Path(s["duckdb"]).exists()
