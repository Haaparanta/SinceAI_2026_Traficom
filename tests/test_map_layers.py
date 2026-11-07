"""Overview-map layers (radar.map_layers), Regulation M4 evidence and the relevance funnel's station line.

Plain inputs only: these run without the raw ITU databases or the special-interest sheet.
"""
from __future__ import annotations

from types import SimpleNamespace

from radar import map_layers as ML
from radar.adapters import traficom_table as T
from radar.models import FinnishSubBand, SpecialInterestStation, TerrestrialNotice
from radar.pipeline import geography as G
from radar.pipeline import relevance as rel
from radar.pipeline.relevance import GroupRelevance


def geo(group_stations=None, notice_stations=None) -> G.IssueGeography:
    return G.IssueGeography(by_notice={}, by_group={}, group_stations=group_stations or {}, notice_stations=notice_stations or {})


# ---- earth stations: every located station, not only the nearest ---------------------------------------------------

def test_every_located_earth_station_of_every_group_is_kept_once():
    g = geo({
        "G1": [{"name": "A", "country": "F", "type": "S", "lat": 48.78, "lon": 2.05},
               {"name": "TYP", "country": "F", "type": "T", "lat": None, "lon": None}],            # typical: no position
        "G2": [{"name": "A", "country": "F", "type": "S", "lat": 48.78, "lon": 2.05},              # same station, other group
               {"name": "B", "country": "FIN", "type": "S", "lat": 61.5, "lon": 23.76}],
        "G9": [{"name": "C", "country": "S", "type": "S", "lat": 59.3, "lon": 18.0}],               # another notice's group
    })
    out = ML.earth_stations("N1", ["G1", "G2"], g)
    assert [e["name"] for e in out] == ["B", "A"]                          # nearest to Finland first; B is inside it
    assert out[0]["distance_km"] == 0 and out[1]["distance_km"] > 1000
    assert out[1]["group_ids"] == ["G1", "G2"] and out[0]["group_ids"] == ["G2"]


def test_the_station_of_an_earth_station_notice_is_included():
    g = geo(notice_stations={"N1": {"name": "TAMPERE", "country": "FIN", "lat": 61.5, "lon": 23.76}})
    out = ML.earth_stations("N1", [], g)
    assert len(out) == 1 and out[0]["name"] == "TAMPERE" and out[0]["group_ids"] == []


def test_no_located_station_gives_an_empty_list():
    assert ML.earth_stations("N1", ["G1"], geo({"G1": [{"name": "T", "lat": None, "lon": None}]})) == []


def test_for_issue_keeps_station_lists_beside_the_nearest():
    # IssueGeography built the old way (two arguments) still works: the new fields default to empty
    g = G.IssueGeography({}, {})
    assert g.group_stations == {} and g.notice_stations == {}


# ---- special-interest stations: the whole sheet, with the findings that reach each one ------------------------------

def st(number, row, lat=62.0, lon=25.0):
    return SpecialInterestStation(station_number=number, centre_hz=2_230_000_000, bandwidth_hz=5_000_000, lat=lat, lon=lon,
                                  source_row=row)


def grp(gid, notice, stations):
    return GroupRelevance(group_id=gid, notice_id=notice, direction="space_to_earth", freq_min_hz=1, freq_max_hz=2,
                          matched_subband_ids=[], overlap_hz=0, uncovered_hz=0, paths={}, primary_terrestrial=False,
                          matched_station_numbers=list(stations), candidate=True)


def test_every_station_of_the_sheet_is_in_the_layer_with_its_findings():
    rows = [grp("G1", "N1", ["S1"]), grp("G2", "N1", ["S2"]), grp("G3", "N2", ["S2"]), grp("G4", "N3", [])]
    reached = ML.reached_by_groups(rows, {"N1": "F-1", "N2": "F-2", "N3": "F-3"})
    assert reached == {"S1": {"F-1"}, "S2": {"F-1", "F-2"}}               # G2 is not N1's lead group, still counted
    out = ML.special_interest([st("S1", 12), st("S2", 13), st("S3", 14), st("S2", 15)], reached,
                              {"F-1": "medium", "F-2": "high", "F-3": "none"})
    assert [e["number"] for e in out] == ["S1", "S2", "S3"]               # repeated number: first row only
    by = {e["number"]: e for e in out}
    assert by["S2"]["finding_ids"] == ["F-1", "F-2"] and by["S2"]["concern"] == "high" and by["S2"]["row"] == 13
    assert by["S3"]["finding_ids"] == [] and by["S3"]["concern"] is None   # on the map, reached by nothing


def test_groups_of_notices_without_a_finding_are_ignored():
    assert ML.reached_by_groups([grp("G1", "N9", ["S1"])], {"N1": "F-1"}) == {}


# ---- terrestrial: every located notice, raised or not ---------------------------------------------------------------

def tn(nid, lat=64.6, lon=30.8, change="new"):
    return TerrestrialNotice(issue=3076, notice_id=nid, administration="RUS", change=change, station_class="FB",
                             site_name=f"SITE {nid}", lat=lat, lon=lon, freq_hz=152_025_000, erp_dbw=15.9, source_ref="x")


def test_every_located_terrestrial_notice_is_in_the_layer():
    notices = [tn("1"), tn("2", change="modified"), tn("3", lat=None, lon=None)]
    findings = [SimpleNamespace(id="F-3076-0001", notice_id="1", concern="high"),
                SimpleNamespace(id="F-3076-0002", notice_id="2", concern="none")]
    out = ML.terrestrial(notices, findings, {"1": SimpleNamespace(notice_type="T12")})
    assert [e["notice_id"] for e in out] == ["1", "2"]                    # the unlocated notice cannot be drawn
    assert out[0] == {**out[0], "finding_id": "F-3076-0001", "concern": "high", "notice_type": "T12", "change": "new"}
    assert out[1]["concern"] == "none" and out[1]["notice_type"] is None and out[1]["change"] == "modified"


# ---- Regulation M4 behind every Finnish-table match ------------------------------------------------------------------

def band() -> FinnishSubBand:
    return FinnishSubBand(id=4438, lower_hz=10_700_000_000, upper_hz=11_700_000_000,
                          services_in_finland="FIXED SATELLITE (SPACE-TO-EARTH)", sub_band_usage="Satellite services")


def test_m4_evidence_cites_the_regulation_and_the_row():
    e = T.m4_evidence(band(), "E-007")
    assert e.kind == "regulation" and e.id == "E-007"
    assert "4 AG/2026 M" in e.source and e.locator == "M4 4 AG/2026 M, Taajuusjakotaulukko.ID=4438"
    assert e.locator.startswith(T.M4_LOCATOR_PREFIX) and ";" not in e.locator   # results files join locators with ";"
    assert e.excerpt == "Regulation M4: Finnish use of 10700000000-11700000000 Hz is FIXED SATELLITE (SPACE-TO-EARTH)"


# ---- B2 funnel: the special-interest line counts real hits ----------------------------------------------------------

def test_funnel_counts_station_hits_from_a_separate_screen():
    rows = [grp("G1", "N1", []), grp("G2", "N1", []), grp("G3", "N2", [])]
    last = rel.funnel(rows, "group", {"G2": ["S1"], "G3": ["S1", "S2"]})[-1]
    assert last == ("  overlap a special-interest station (frequency, before geography)", 2)
    assert rel.funnel(rows, "notice", {"G2": ["S1"]})[-1][1] == 1
    assert rel.funnel([grp("G1", "N1", ["S1"])], "group")[-1][1] == 1    # without the argument: the rows' own matches
