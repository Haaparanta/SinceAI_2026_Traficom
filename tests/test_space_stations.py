"""Special-interest stations in the space screening (build step after A3): match, reach, floor, evidence."""
from __future__ import annotations

import json

import pytest

from radar.adapters import special_interest as SI
from radar.calc import pfd as PFD
from radar.config import settings
from radar.models import SpecialInterestStation
from radar.pipeline import geography as G
from radar.pipeline import rank as RK
from radar.pipeline.relevance import GroupRelevance


def st(number, lat=62.0, lon=25.0, centre=2_230_000_000, bw=5_000_000):
    return SpecialInterestStation(station_number=number, centre_hz=centre, bandwidth_hz=bw, lat=lat, lon=lon)


def rel(direction="space_to_earth", stations=("S1",), paths=("pfd_terrestrial",), candidate=True):
    return GroupRelevance(group_id="G", notice_id="N", direction=direction, freq_min_hz=2_200_000_000, freq_max_hz=2_300_000_000,
                          matched_subband_ids=[], overlap_hz=0, uncovered_hz=0, paths={p: [] for p in paths},
                          primary_terrestrial=False, matched_station_numbers=list(stations), candidate=candidate)


# ---- reach from the station's own position -------------------------------------------------------------------------

def test_gso_downlink_keeps_stations_that_see_the_satellite():
    g = G.gso_result(25.0)                                   # due south of Finland: visible everywhere
    kept, detail, dropped = G.station_reach("space_to_earth", g, "G", [st("A", 60.2, 24.9), st("B", 69.9, 27.0)])
    assert kept == ["A", "B"] and detail["A"]["elevation_deg"] > detail["B"]["elevation_deg"] > 0 and not dropped


def test_gso_downlink_drops_a_station_below_its_horizon():
    g = G.gso_result(-100.0)                                 # over the Americas: below the horizon from Finland
    kept, _, dropped = G.station_reach("space_to_earth", g, "G", [st("A")])
    assert kept == [] and "below its horizon" in dropped[0]


def test_uplink_needs_a_located_earth_station_near_the_station():
    near = G.GeoResult("near_border", "earth_station_distance",
                       {"nearest": {"name": "Tartu", "country": "EST", "lat": 58.38, "lon": 26.72, "distance_km": 150.0}})
    kept, detail, _ = G.station_reach("earth_to_space", near, "G", [st("A", 60.2, 24.9), st("B", 69.9, 27.0)])
    assert kept == ["A"] and 200 < detail["A"]["distance_km"] < 260
    typical = G.GeoResult("unknown", "none", note="typical earth station, no location filed")
    kept, _, dropped = G.station_reach("earth_to_space", typical, "G", [st("A")])
    assert kept == [] and "location not filed" in dropped[0]


def test_downlink_with_unknown_geography_keeps_the_station():
    kept, _, _ = G.station_reach("space_to_earth", G.GeoResult("unknown", "none"), "G", [st("A")])
    assert kept == ["A"]


def test_apply_drops_out_of_reach_stations_and_the_path():
    geo = G.IssueGeography({"N": G.gso_result(-100.0)}, {})
    r = rel(paths=("special_interest",))
    r.paths["special_interest"] = []
    G.apply([r], geo, {"N": "G"}, [st("S1")])
    assert r.matched_station_numbers == [] and "special_interest" not in r.paths and not r.candidate


# ---- the floor comes after the pfd rules ---------------------------------------------------------------------------

def test_station_floor_raises_low_and_never_lowers():
    r = rel()
    assert RK.station_floor(r, "low", "downlink over a secondary terrestrial row")[0] == "medium"
    assert RK.station_floor(r, "high", "x")[0] == "high" and RK.station_floor(r, "review", "x")[0] == "review"
    assert RK.station_floor(rel(stations=()), "low", "x")[0] == "low"


def test_an_exceeded_pfd_limit_still_makes_high_when_a_station_matches():
    """Regression: the station rule used to return before the downlink rule, so pfd could not raise it to high."""
    r = rel()
    r.geo_relevance, r.primary_terrestrial = "visible", True
    pfd = PFD.PfdResult("computed", -100.0, -110.0, -10.0, worst={"steerable": True})
    concern, rule = RK.station_floor(r, *RK.pfd_adjust(*RK.concern_rule(r, {}), pfd))
    assert concern == "high" and "special-interest station S1" in rule


def test_station_points_are_only_the_stations_that_see_the_satellite():
    pts = G.station_points(["A", "B"], 25.0, [st("A", 60.2, 24.9), st("B", 60.3, 25.0), st("C", 61.0, 25.0)])
    assert [p[0] for p in pts] == ["station A", "station B"]


# ---- the real 3074 run -------------------------------------------------------------------------------------------

CACHE = settings.data_dir / "cache" / "space_3074.json"
needs = pytest.mark.skipif(not (CACHE.exists() and SI.path().exists()), reason="needs the cache and the XLS")


@needs
def test_3074_station_evidence_points_to_the_sheet():
    b = json.loads(CACHE.read_text())
    rows = SI.by_row()
    with_st = [f for f in b["result"]["findings"] if f["matched_station_numbers"]]
    assert len(with_st) == 62          # 52 before the non-GSO pfd check moved some leads to the exceeding group
    for f in with_st:
        cited = [e for e in f["evidence"] if e["kind"] == "special_interest_row"]
        assert 1 <= len(cited) <= 5
        for e in cited:
            s = rows[int(e["locator"].split("=")[1])]
            assert e["excerpt"] == SI.excerpt(s) and s.station_number in f["matched_station_numbers"]
        assert len(b["context"][f["id"]]["stations"]) == len(f["matched_station_numbers"])


@needs
def test_golden_stations():
    import yaml
    from pathlib import Path
    from radar.pipeline import assemble
    rows = {r.group_id: r for r in assemble.run(3074).rows}
    for c in yaml.safe_load((Path(__file__).parent / "golden" / "space_3074.yaml").read_text())["cases"]:
        assert sorted(rows[c["group_id"]].matched_station_numbers) == sorted(c["stations"]), c["notice"]
