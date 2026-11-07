"""Non-GSO worst-case pfd: geometry, RR Table 21-4 footnotes 11, 13 and 16, and the concern rule."""
from __future__ import annotations

import math

import pytest

from radar.calc import pfd as P
from radar.pipeline import rank as RK
from radar.pipeline.relevance import GroupRelevance

LEO = [P.OrbitIn(1, 97.6, 550.0, 550.0, 20)]           # sun-synchronous, passes over Finland
EMI = [P.Emission(1, "1M00G7W--", -70.0, 1e6)]


# ---- geometry ------------------------------------------------------------------------------------------------------

def test_slant_range_overhead_and_at_the_horizon():
    assert P.slant_range_km(550, 90) == pytest.approx(550, abs=1e-6)
    assert P.slant_range_km(550, 0) == pytest.approx(math.sqrt((P.R_EARTH_KM + 550) ** 2 - P.R_EARTH_KM ** 2), abs=1e-6)


def test_highest_elevation_depends_on_inclination():
    assert P.highest_elevation(97.6, 550)[1] == pytest.approx(90.0)
    name, el = P.highest_elevation(53.0, 550)
    assert name == "Hanko" and 30 < el < 33                 # a 53-degree shell never rises high over Finland
    assert P.highest_elevation(30.0, 550)[1] < 0             # never above the horizon


# ---- Table 21-4 footnotes ------------------------------------------------------------------------------------------

def test_x_follows_footnote_13_and_is_continuous():
    assert P.x_db(50)[0] == 0 and P.x_db(288)[0] == pytest.approx(10.0) and P.x_db(289)[0] == pytest.approx(10.014, abs=1e-3)
    assert P.x_db(999)[0] == pytest.approx(20.3, abs=0.01)
    assert P.x_db(5000) == (20.3, P.x_db(5000)[1]) and "Nv" in P.x_db(5000)[1]
    assert P.x_db(None)[0] == 0.0


def test_the_x_row_moves_only_below_25_degrees():
    row = next(r for r in P.limits() if r.id == "17700-19300_ngso")
    assert row.limit(0, 20.3) == pytest.approx(-135.3) and row.limit(25, 20.3) == pytest.approx(-105.0)
    assert row.limit(15, 20.3) == pytest.approx(-135.3 + (30.3 / 20) * 10)
    assert row.limit(15) == pytest.approx(-110.0)            # X = 0 is the printed fn 14/15 row


def test_highly_inclined_orbits_take_footnote_16_and_footnote_11_counts_satellites():
    heo = P.applicable_limits(17_800_000_000, 17_900_000_000, "HEO")
    assert [r.id for r in heo] == ["17700-19700_heo"]
    assert "17700-19300_ngso" in [r.id for r in P.applicable_limits(17_800_000_000, 17_900_000_000, "NGSO")]
    assert P.orbit_class([P.OrbitIn(1, 63.4, 39_700, 600, 3)]) == "HEO"
    assert P.orbit_class(LEO) == "NGSO"
    assert [r.id for r in P.applicable_limits(37_800_000_000, 37_900_000_000, "NGSO", 99)] == ["37000-38000_srs_ngso", "37500-40000_ngso"]
    assert [r.id for r in P.applicable_limits(37_800_000_000, 37_900_000_000, "NGSO", 100)] == ["37000-38000_srs_ngso"]


# ---- the calculation -----------------------------------------------------------------------------------------------

def test_worst_case_scans_every_elevation_and_reports_the_overhead_margin():
    r = P.worst_case_ngso(2_200_000_000, 2_210_000_000, LEO, [P.Emission(1, "100KG1D--", -60.0, 1e5)], 6.0)
    assert r.status == "computed" and r.orbit == "NGSO" and r.method == "pfd_ngso_worst_case"
    w = r.worst
    assert w["max_elevation_deg"] == pytest.approx(90.0) and w["top_elevation_deg"] == pytest.approx(90.0)
    # overhead: pfd = -60 + 6 + 10 log10(4 kHz) - 10 log10(4 pi (550 km)^2); limit -144 above 25 deg
    overhead = -60 + 6 + 10 * math.log10(4000) - 10 * math.log10(4 * math.pi * 550e3 ** 2)
    assert w["top_margin_db"] == pytest.approx(-144 - overhead, abs=0.01)
    assert r.margin_db <= w["top_margin_db"]


def test_orbits_that_never_rise_over_finland_are_not_visible():
    r = P.worst_case_ngso(2_200_000_000, 2_210_000_000, [P.OrbitIn(1, 30.0, 550, 550, 1)], EMI, 6.0)
    assert r.status == "not_visible"


# ---- concern ------------------------------------------------------------------------------------------------------

def _res(margin, top, top_el, x_lb=False):
    return P.PfdResult("computed", -100.0, -110.0, margin, {"elevation_deg": 5.0, "top_margin_db": top,
                                                            "top_elevation_deg": top_el, "x_lower_bound": x_lb}, orbit="NGSO")


def test_an_orbit_that_stays_low_does_not_make_the_overhead_orbit_high():
    rule = "downlink over a Finnish primary terrestrial allocation"
    r = _res(-21, -20.75, 90)
    r.worst["tops"] = [(90.0, 2.7), (3.24, -20.75)]       # the overhead orbit passes, the low one exceeds
    assert RK.pfd_adjust("medium", rule, r)[0] == "review"
    r.worst["tops"] = [(90.0, -1.0), (3.24, -20.75)]
    assert RK.pfd_adjust("medium", rule, r)[0] == "high"


def test_ngso_high_only_when_the_satellite_is_high_over_finland():
    rule = "downlink over a Finnish primary terrestrial allocation"
    assert RK.pfd_adjust("medium", rule, _res(-5, -2, 90))[0] == "high"
    assert RK.pfd_adjust("medium", rule, _res(-5, -2, 7.3))[0] == "review"      # exceeds, but only seen low
    assert RK.pfd_adjust("medium", rule, _res(-5, 3, 90))[0] == "review"        # exceeds only at low elevation
    assert RK.pfd_adjust("medium", rule, _res(20, 25, 90))[0] == "low"
    concern, why = RK.pfd_adjust("medium", rule, _res(20, 25, 90, x_lb=True))
    assert concern == "medium" and "not conclusive" in why
    r = _res(20, 25, 90)
    r.worst["y_assumed"] = True
    assert RK.pfd_adjust("medium", rule, r)[0] == "medium"


def test_service_area_naming_finland_is_medium():
    r = GroupRelevance(group_id="G", notice_id="N", direction="space_to_earth", freq_min_hz=1, freq_max_hz=2,
                       matched_subband_ids=[], overlap_hz=0, uncovered_hz=0, paths={"service_area_finland": []},
                       primary_terrestrial=False, candidate=True, geo_relevance="visible")
    assert RK.concern_rule(r, {}) == ("medium", "the filing names Finland in the service area of this group")
