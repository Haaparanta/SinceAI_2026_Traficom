"""Step B4 of pm_pack/08: findings, ranking and the evidence resolver."""
from __future__ import annotations

import pytest

from radar import evidence_check
from radar.adapters import space_ific
from radar.models import FinnishSubBand
from radar.pipeline import assemble
from radar.pipeline import rank as RK
from radar.pipeline.relevance import GroupRelevance, classify

needs_db = pytest.mark.skipif(not space_ific.db_path(3074).exists(), reason="run make convert first")


def row(**kw) -> GroupRelevance:
    base = dict(group_id="G", notice_id="N", direction="space_to_earth", freq_min_hz=100, freq_max_hz=200,
                matched_subband_ids=[1], overlap_hz=100, uncovered_hz=0, paths={}, primary_terrestrial=False,
                candidate=True, geo_relevance="visible")
    base.update(kw)
    return GroupRelevance(**base)


CLASSES = {1: classify("FIXED"), 2: classify("Fixed"), 3: classify("RADIO ASTRONOMY"), 4: classify("FIXED SATELLITE (SPACE-TO-EARTH)")}


# ---- rule table ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize("kw, concern", [
    (dict(candidate=False), "none"),
    (dict(finland_named_provisions=["9.14"], geo_relevance="not_visible"), "high"),
    (dict(direction="earth_to_space", paths={"uplink_near_finland": []}, geo_relevance="near_border",
          geo_note="earth station TAMPERE (FIN) is inside Finland"), "high"),
    (dict(direction="earth_to_space", paths={"uplink_near_finland": []}, geo_relevance="near_border",
          geo_note="nearest earth station UMEA (S) 77 km from Finland"), "medium"),
    (dict(matched_station_numbers=["S-1"]), "medium"),
    (dict(paths={"pfd_terrestrial": [1]}, primary_terrestrial=True), "medium"),
    (dict(paths={"passive_service": [3]}), "medium"),
    (dict(paths={"pfd_terrestrial": [2]}), "low"),
    (dict(paths={"space_cofrequency": [4]}), "low"),
    (dict(paths={"uncovered": []}), "review"),
    (dict(paths={"pfd_terrestrial": [1]}, primary_terrestrial=True, geo_relevance="unknown"), "review"),
])
def test_concern_rules(kw, concern):
    assert RK.concern_rule(row(**kw), CLASSES)[0] == concern


def test_sensitivity_uses_scoring_package_rules():
    ra = FinnishSubBand(id=1, lower_hz=1, upper_hz=2, services_in_finland="RADIO ASTRONOMY", sub_band_usage="Radio astronomy")
    assert RK.sensitivity(ra)[0] == 1.0
    amateur = FinnishSubBand(id=2, lower_hz=1, upper_hz=2, services_in_finland="Amateur", sub_band_usage="Amateur")
    assert RK.sensitivity(amateur)[0] < 0.6


@pytest.mark.parametrize("section, key", [("CR/C 3407 M2", "CR/C"), ("API/A 13924 M1", "API/A"), ("Part II-S", "PART-II-S"), (None, "unknown")])
def test_section_key(section, key):
    assert RK.section_key(section) == key


# ---- real data ----------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def run_3074():
    return assemble.run(3074)


@needs_db
def test_one_finding_per_notice_with_evidence(run_3074):
    res = run_3074.result
    assert res.screened == 196 and len(res.findings) == 196
    assert [f.id for f in res.findings] == [f"F-3074-{k:04d}" for k in range(1, 197)]
    assert all(f.evidence and f.evidence[0].locator.startswith("notice.ntc_id=") for f in res.findings)
    assert res.provenance_coverage_pct == 100.0


@needs_db
def test_ranked_by_concern_then_score(run_3074):
    order = [RK.CONCERN_ORDER[f.concern] for f in run_3074.result.findings]
    assert order == sorted(order, reverse=True)
    assert len({f.concern for f in run_3074.result.findings}) >= 4   # not everything on one level


@needs_db
def test_bureau_named_and_inside_finland_notices_are_high(run_3074):
    by_notice = {f.notice_id: f for f in run_3074.result.findings}
    named = {r.notice_id for r in run_3074.rows if r.finland_named_provisions}
    assert len(named) == 16 and all(by_notice[n].concern == "high" for n in named)
    for nid in ("126500107", "126545119"):            # PLAN-S_MUONIO(FIN) and TAMPERE earth stations
        assert by_notice[nid].concern == "high" and "inside Finland" in by_notice[nid].reason


@needs_db
def test_every_citation_resolves(run_3074):
    checks = evidence_check.check(run_3074.result)
    assert checks and not [c for c in checks if c.status == "FAIL"]


@needs_db
@pytest.mark.parametrize("kind", ["itu_row", "finnish_table_row", "calculation"])
def test_resolver_catches_a_tampered_excerpt(run_3074, kind):
    res = run_3074.result.model_copy(deep=True)
    f = next(f for f in res.findings if any(e.kind == kind for e in f.evidence))
    e = next(e for e in f.evidence if e.kind == kind)
    e.excerpt = e.excerpt.replace("=", "=9", 1) if kind == "itu_row" else e.excerpt + " (edited)"
    res.findings = [f]
    assert [c.status for c in evidence_check.check(res) if c.evidence_id == e.id] == ["FAIL"]
