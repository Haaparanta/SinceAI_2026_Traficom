"""Step B3 of pm_pack/08: geography. Test vectors from pm_pack/08 and the golden cases in tests/golden/space_3074.yaml."""
from __future__ import annotations

from pathlib import Path

import duckdb
import pytest
import yaml

from radar.adapters import space_ific
from radar.pipeline import geography as G
from radar.pipeline import relevance as rel

GOLDEN = yaml.safe_load((Path(__file__).parent / "golden" / "space_3074.yaml").read_text())
needs_db = pytest.mark.skipif(not space_ific.db_path(3074).exists(), reason="run make convert first")


# ---- GSO geometry (pm_pack/06 formula, pm_pack/08 test vectors) ---------------------------------------------

@pytest.mark.parametrize("lat, dlon, elevation", [(60, 0, 21.9), (70, 0, 11.5), (60, 72.4, 0.0), (0, 0, 90.0)])
def test_gso_elevation_vectors(lat, dlon, elevation):
    assert G.gso_look(lat, 25.0, 25.0 + dlon)[0] == pytest.approx(elevation, abs=0.1)


def test_gso_slant_range_bounds():
    assert G.gso_look(0, 0, 0)[1] == pytest.approx(35786.0, abs=1)                 # sub-satellite point
    assert G.gso_look(60, 0, 72.4)[1] == pytest.approx(41679, abs=50)              # horizon at 60 N
    assert 35786 <= G.gso_look(65, 25, 40)[1] <= 41700


def test_west_longitude_is_symmetric():
    assert G.gso_look(60, 25, 25 - 30)[0] == pytest.approx(G.gso_look(60, 25, 25 + 30)[0])


def test_no_gso_satellite_rises_above_23_deg_anywhere_in_finland():
    assert max(G.gso_look(la, lo, s)[0] for _, la, lo in G.reference_points() for s in range(-180, 181)) < 23.0


def test_gso_verdicts():
    assert G.gso_result(25.0).relevance == "visible"
    assert G.gso_result(-77.0).relevance == "not_visible"
    assert G.gso_result(None).relevance == "unknown"
    low = G.gso_result(85.0)   # far east: low over Finland
    assert low.relevance == "low_elevation" and 0 < low.detail["max_elevation_deg"] < 10


# ---- non-GSO and earth stations -----------------------------------------------------------------------------

def test_ngso_coverage_reaches_poles_for_polar_orbits():
    assert G.coverage_lat_limit(97.6, 550, 10) > 80
    assert G.ngso_result("T", [(97.6, 550, 540)]).relevance == "visible"


def test_ngso_equatorial_low_orbit_cannot_see_finland():
    assert G.ngso_result("T", [(0.0, 550, 550)]).relevance == "not_visible"


def test_ngso_other_body_and_missing_orbit():
    assert G.ngso_result("L", [(90, 100, 100)]).relevance == "not_visible"
    assert "Moon" in G.ngso_result("L", []).note
    assert G.ngso_result("T", []).relevance == "unknown"


def test_dms_conversion():
    assert G.dms_to_deg(77, 0, 35, "E") == pytest.approx(77.00972, abs=1e-4)
    assert G.dms_to_deg(43, 30, 0, "S") == -43.5
    assert G.dms_to_deg(None, 0, 0, "N") is None


def test_earth_station_distance():
    assert G.earth_station_result([{"name": "Helsinki", "country": "FIN", "lat": 60.17, "lon": 24.94}]).relevance == "near_border"
    stockholm = G.earth_station_result([{"name": "Stockholm", "country": "S", "lat": 59.33, "lon": 18.07}])
    # nearest Finnish territory is Aland (Eckeroe), about 120 km east; without Aland it was the mainland, over 150 km
    assert stockholm.relevance == "near_border" and 100 < stockholm.detail["nearest"]["distance_km"] < 150
    assert G.earth_station_result([{"name": "Madrid", "country": "E", "lat": 40.4, "lon": -3.7}]).relevance == "far"
    assert G.earth_station_result([{"name": "T", "country": None, "lat": None, "lon": None}]).relevance == "unknown"


# ---- real data and golden cases -----------------------------------------------------------------------------

@pytest.fixture(scope="module")
def rows_3074():
    ing = space_ific.load(3074)
    with duckdb.connect(str(space_ific.db_path(3074)), read_only=True) as con:
        rows = rel.screen(ing.notices, named=rel.finland_named(con))
        types = dict(con.execute("SELECT CAST(ntc_id AS VARCHAR), ntc_type FROM notice").fetchall())
        G.apply(rows, G.for_issue(ing.notices, con), types)
    return {r.group_id: r for r in rows}


@needs_db
@pytest.mark.parametrize("case", GOLDEN["cases"], ids=[c["group_id"] for c in GOLDEN["cases"]])
def test_golden_b3(rows_3074, case):
    r = rows_3074[case["group_id"]]
    assert (r.candidate, r.geo_relevance) == (case["b3"]["candidate"], case["b3"]["geo"]), case["why_b3"]


@needs_db
def test_3074_geography_invariants(rows_3074):
    rows = list(rows_3074.values())
    # Bureau-named groups stay candidates whatever the geography
    assert all(r.candidate for r in rows if r.finland_named_provisions)
    # a downlink of a space station below the horizon is never a candidate unless the Bureau names Finland
    assert not [r for r in rows if r.direction == "space_to_earth" and r.geo_relevance == "not_visible"
                and r.candidate and not r.finland_named_provisions]
    # foreign earth stations inside Finland are found (Tampere, Muonio)
    inside = {r.geo_note for r in rows if "inside Finland" in r.geo_note}
    assert any("TAMPERE" in n for n in inside) and any("MUONIO" in n for n in inside)


@needs_db
def test_bureau_named_groups_from_earlier_issues_are_screened():
    """SECOMSAT-5-78E (CR/C 6344, notice 124520194) is in 3074; the Bureau names Finland only in its groups first
    published in IFIC 3060. They must be screened, so the notice reaches concern high (rule: Bureau-named = high)."""
    from radar.pipeline import assemble
    run = assemble.run(3074)
    f = next(f for f in run.result.findings if f.notice_id == "124520194")
    assert f.concern == "high"
    with duckdb.connect(str(space_ific.db_path(3074)), read_only=True) as con:
        named = rel.finland_named(con)
    screened = {r.group_id: r for r in run.rows}
    assert all(g in screened and screened[g].candidate for g in named)


def test_aland_is_finland():
    """Natural Earth keeps Aland as its own entity (ALD); the region file merges it into FIN."""
    from scoring.geometry import Region
    assert Region.load().contains("FIN", 60.097, 19.935)          # Mariehamn
