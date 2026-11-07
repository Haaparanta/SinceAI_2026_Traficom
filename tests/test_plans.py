"""AP30, AP30A and AP30B: Finnish plan entries, the orbital-arc pre-screen and the plan sections of an issue."""
from __future__ import annotations

import pytest

from radar.adapters import plans as P
from radar.pipeline import plans as PL
from radar.pipeline import rank as RK
from radar.pipeline.relevance import GroupRelevance

needs_plans = pytest.mark.skipif(not P.snapshots(), reason="run make convert-plans first")


def arc(arc_id):
    a = P.arc_by_id(arc_id)
    assert a is not None, arc_id
    return a


def entry(arc_id="AP30-R1", lon=22.8, lo=12_116_760_000, hi=12_489_000_000, direction="space_to_earth", tol=(0.0, 0.0)):
    return P.PlanEntry(plan=arc(arc_id).plan, db="AP30B" if arc_id.startswith("AP30B") else "AP30", snapshot=3083,
                       notice_id="100550080", group_id="3412", satellite="FIN10300", longitude_deg=lon,
                       tol_east_deg=tol[0], tol_west_deg=tol[1], direction=direction, lo_hz=lo, hi_hz=hi,
                       beam_name="E001", gain_dbi=44.24, arc=arc(arc_id))


# ---- the reference table -------------------------------------------------------------------------------------

def test_arcs_table_has_every_plan_band_with_a_source():
    a = P.arcs()
    assert {x.plan for x in a} == {"AP30", "AP30A", "AP30B"}
    assert all(x.source.startswith("RR 2024 Vol. 2") and x.page and x.excerpt_text for x in a)
    # AP30B Ku downlink is two bands with a gap at 10.95-11.20 GHz (RR AP30B Annex 4 section 1.2)
    ku = sorted((x.lo_hz, x.hi_hz) for x in a if x.plan == "AP30B" and x.direction == "space_to_earth" and x.arc_deg == 6)
    assert ku == [(10_700_000_000, 10_950_000_000), (11_200_000_000, 11_450_000_000)]


def test_arc_comparison_follows_the_wording():
    assert arc("AP30-R1").within(8.99) and not arc("AP30-R1").within(9.0)          # "less than 9 deg"
    assert arc("AP30B-Ku-up").within(6.0) and not arc("AP30B-Ku-up").within(6.01)  # "equal to or less than 6 deg"
    assert arc("AP30B-C-down").within(7.0)


# ---- orbital spacing -------------------------------------------------------------------------------------------

def test_separation_subtracts_the_facing_tolerances():
    assert PL.separation(22.8, 0.1, 0.2, 25.8, 0.3, 0.4) == (3.0, 2.5, "filed tolerances")     # east: fin east + other west
    assert PL.separation(22.8, 0.1, 0.2, 19.8, 0.3, 0.4) == (3.0, 2.5, "filed tolerances")     # west: fin west + other east
    nominal, worst, note = PL.separation(22.8, None, None, 25.8, 0.1, 0.1)
    assert (nominal, worst) == (3.0, 2.9) and "not filed for Finnish" in note


def test_separation_wraps_around_180():
    assert PL.separation(179.0, 0, 0, -179.0, 0, 0)[0] == 2.0


# ---- the pre-screen ----------------------------------------------------------------------------------------------

def test_cofrequency_inside_the_arc_is_a_hit():
    h = PL.hits_for("space_to_earth", 12_200_000_000, 12_300_000_000, 26.0, 0.1, 0.1, [entry()])
    assert len(h) == 1 and h[0].worst_deg == pytest.approx(3.1) and "FIN10300" in h[0].text()


def test_outside_the_arc_wrong_direction_or_other_band_is_not():
    e = [entry()]
    assert PL.hits_for("space_to_earth", 12_200_000_000, 12_300_000_000, 33.5, 0, 0, e) == []     # 10.7 deg
    assert PL.hits_for("earth_to_space", 12_200_000_000, 12_300_000_000, 24.0, 0, 0, e) == []     # uplink
    assert PL.hits_for("space_to_earth", 11_000_000_000, 11_100_000_000, 24.0, 0, 0, e) == []     # other band
    assert PL.hits_for("space_to_earth", 12_200_000_000, 12_300_000_000, None, 0, 0, e) == []     # no longitude


def test_nearest_cofrequency_reports_entries_outside_the_arc():
    near = PL.nearest_cofrequency("space_to_earth", 12_200_000_000, 12_300_000_000, 33.5, 0, 0, [entry()])
    assert near is not None and near[2] == pytest.approx(10.7)


# ---- concern rules ------------------------------------------------------------------------------------------------

def _row(**kw):
    r = GroupRelevance(group_id="G1", notice_id="N1", direction="space_to_earth", freq_min_hz=12_200_000_000,
                       freq_max_hz=12_300_000_000, matched_subband_ids=[], overlap_hz=0, uncovered_hz=0,
                       paths={"plan_finnish": []}, primary_terrestrial=False, candidate=True, geo_relevance="visible")
    for k, v in kw.items():
        setattr(r, k, v)
    return r


def test_plan_hit_is_medium_and_bureau_effect_is_high():
    hit = PL.hits_for("space_to_earth", 12_200_000_000, 12_300_000_000, 26.0, 0, 0, [entry()])
    concern, rule = RK.concern_rule(_row(plan_hits=hit), {})
    assert concern == "medium" and "FIN10300" in rule and "pfd test was not run" in rule
    effect = P.BureauEffect(db="AP30", snapshot=3083, notice_id="N1", administration="I", satellite="X", longitude_deg=24.8,
                            provision="4.1.3", ific_no=3019, finnish_notice_id="100550080", finnish_satellite="FIN10300",
                            freq_band=None, pfd_excess_db=26.99, degradation_db=23.27)
    concern, rule = RK.concern_rule(_row(plan_bureau=[effect]), {})
    assert concern == "high" and "26.99 dB" in rule


# ---- the real plan databases --------------------------------------------------------------------------------------

@needs_plans
def test_finnish_plan_entries():
    e = P.finnish_entries()
    assert {(x.plan, x.satellite, x.longitude_deg) for x in e} == {
        ("AP30", "FIN10300", 22.8), ("AP30", "FIN10400", 22.8), ("AP30A", "FIN10300", 22.8), ("AP30A", "FIN10400", 22.8),
        ("AP30B", "FIN00000", 46.8)}
    assert all(x.group_locator.split(":")[0] in ("SPS_ALL_IFIC3083", "30B_3083") and x.group_excerpt for x in e)


@needs_plans
def test_bureau_lists_networks_affecting_finland():
    nets = {b.satellite for b in P.bureau_effects()}
    assert {"ITALY_BSS_24.8E", "EUROPESTAR-FSS-47.5E", "OHO-30B-45E-2"} <= nets


@needs_plans
def test_ap30b_sections_of_3074_are_screened():
    pn = {p.satellite: p for p in P.published_in(3074)}
    assert set(pn) == {"F-SAT-30B-139W", "HISPASAT-93A", "MEASAT-91.5E-30B-E"}
    assert pn["MEASAT-91.5E-30B-E"].sections == ["AP30B/A6A 760"] and pn["MEASAT-91.5E-30B-E"].examined
    findings = PL.plan_notice_findings(3074, list(pn.values()), P.finnish_entries(), P.bureau_effects())
    assert all(f.concern == "none" and f.reason.startswith("Not raised") for f in findings)
    assert any("44.60 deg" in f.reason for f in findings)
