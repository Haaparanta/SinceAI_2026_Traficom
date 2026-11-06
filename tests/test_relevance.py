"""Step B2 of pm_pack/08: frequency relevance. Golden cases come from tests/golden/space_3074.yaml."""
from __future__ import annotations

from pathlib import Path

import duckdb
import pytest
import yaml

from radar.adapters import space_ific
from radar.models import FinnishSubBand, FrequencyGroup, Notice, SpecialInterestStation
from radar.pipeline import relevance as rel

GOLDEN = yaml.safe_load((Path(__file__).parent / "golden" / "space_3074.yaml").read_text())
needs_db = pytest.mark.skipif(not space_ific.db_path(3074).exists(), reason="run make convert first")


def band(id_, lo, hi, services):
    return FinnishSubBand(id=id_, lower_hz=lo, upper_hz=hi, services_in_finland=services, sub_band_usage="x")


def notice(*groups):
    return [Notice(issue=1, notice_id="N1", administration="X", network_name="T", orbit="GSO", groups=list(groups),
                   source_ref="notice.ntc_id=N1")]


def grp(gid, lo, hi, direction="space_to_earth"):
    return FrequencyGroup(group_id=gid, notice_id="N1", freq_min_hz=lo, freq_max_hz=hi, direction=direction,
                          source_ref=f"grp.grp_id={gid}")


# ---- classification of Finnish rows -------------------------------------------------------------------------

@pytest.mark.parametrize("text, category, direction, primary", [
    ("FIXED", "terrestrial", None, True),
    ("Fixed", "terrestrial", None, False),
    ("MARITIME MOBILE", "terrestrial", None, True),
    ("FIXED SATELLITE (SPACE-TO-EARTH)", "space", "downlink", True),
    ("Fixed satellite (space-to-Earth)", "space", "downlink", False),
    ("MOBILE-SATELLITE (EARTH-TO-SPACE)", "space", "uplink", True),
    ("FIXED SATELLITE (EARTH-TO-SPACE, SPACE-TO-EARTH)", "space", "both", True),
    ("RADIONAVIGATION-SATELLITE (SPACE-TO-EARTH, SPACE-TO-SPACE)", "space", "downlink", True),
    ("RADIO ASTRONOMY", "passive", None, True),
    ("EARTH EXPLORATION-SATELLITE (PASSIVE)", "passive", None, True),
    ("(not allocated)", "not_allocated", None, False),
])
def test_classify(text, category, direction, primary):
    rc = rel.classify(text)
    assert (rc.category, rc.space_direction, rc.primary) == (category, direction, primary)


# ---- rules --------------------------------------------------------------------------------------------------

def test_downlink_over_terrestrial_is_the_pfd_path():
    [r] = rel.screen(notice(grp("G1", 100, 200)), (band(1, 0, 300, "FIXED"),))
    assert r.candidate and r.paths == {"pfd_terrestrial": [1]} and r.primary_terrestrial


def test_uplink_is_informational_not_a_candidate():
    [r] = rel.screen(notice(grp("G1", 100, 200, "earth_to_space")), (band(1, 0, 300, "FIXED"),))
    assert not r.candidate and "uplink_terrestrial" in r.paths


def test_downlink_over_uplink_only_rows_is_dropped():
    [r] = rel.screen(notice(grp("G1", 100, 200)), (band(1, 0, 300, "FIXED SATELLITE (EARTH-TO-SPACE)"),))
    assert not r.candidate and r.paths == {}


def test_table_gap_is_uncovered_never_silently_safe():
    [r] = rel.screen(notice(grp("G1", 100, 400)), (band(1, 0, 200, "FIXED SATELLITE (EARTH-TO-SPACE)"),))
    assert r.candidate and "uncovered" in r.paths and r.uncovered_hz == 200


def test_overlap_is_the_union_not_the_sum():
    bands = (band(1, 0, 300, "FIXED"), band(2, 0, 300, "MOBILE"), band(3, 250, 500, "FIXED"))
    [r] = rel.screen(notice(grp("G1", 100, 400)), bands)
    assert r.overlap_hz == 300 and r.uncovered_hz == 0


def test_single_frequency_group_matches_the_band_it_sits_in():
    [r] = rel.screen(notice(grp("G1", 150, 150)), (band(1, 100, 200, "FIXED"), band(2, 200, 300, "FIXED")))
    assert r.matched_subband_ids == [1] and r.candidate


def test_special_interest_station_makes_a_candidate():
    st = SpecialInterestStation(station_number="S-1", centre_hz=150, bandwidth_hz=20, lat=60, lon=25)
    [r] = rel.screen(notice(grp("G1", 100, 200, "earth_to_space")), (band(1, 0, 300, "FIXED"),), stations=[st])
    assert r.candidate and r.matched_station_numbers == ["S-1"]


def test_bureau_naming_finland_makes_a_candidate_even_for_an_uplink():
    [r] = rel.screen(notice(grp("G1", 100, 200, "earth_to_space")), (band(1, 0, 300, "FIXED"),), named={"G1": ["9.14"]})
    assert r.candidate and r.finland_named_provisions == ["9.14"]


# ---- real data and golden cases -----------------------------------------------------------------------------

@pytest.fixture(scope="module")
def rows_3074():
    ing = space_ific.load(3074)
    with duckdb.connect(str(space_ific.db_path(3074)), read_only=True) as con:
        named = rel.finland_named(con)
    return {r.group_id: r for r in rel.screen(ing.notices, named=named)}


@needs_db
@pytest.mark.parametrize("case", GOLDEN["cases"], ids=[c["group_id"] for c in GOLDEN["cases"]])
def test_golden_b2(rows_3074, case):
    r = rows_3074[case["group_id"]]
    assert r.candidate == case["b2"]["candidate"], case["why"]
    assert sorted(r.paths) == sorted(case["b2"]["paths"]), case["why"]


@needs_db
def test_3074_invariants(rows_3074):
    rows = list(rows_3074.values())
    assert len(rows) == 25105
    assert all(r.overlap_hz <= r.freq_max_hz - r.freq_min_hz for r in rows)
    assert not [r for r in rows if r.direction == "earth_to_space" and r.candidate and not r.finland_named_provisions]
    assert len({r.notice_id for r in rows if r.finland_named_provisions}) == 16
