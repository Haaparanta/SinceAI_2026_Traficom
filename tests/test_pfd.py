"""Step C1 of pm_pack/08: worst-case pfd and the RR Article 21 Table 21-4 transcription."""
from __future__ import annotations

import pytest

from radar.adapters import space_ific
from radar.calc import pfd as P
from radar.pipeline import rank as RK

needs_db = pytest.mark.skipif(not space_ific.db_path(3074).exists(), reason="run make convert first")


# ---- the limits table ---------------------------------------------------------------------------------------

def test_every_limit_row_is_continuous_and_plausible():
    for r in P.limits():
        assert r.segments[0][0] == 0 and r.segments[-1][1] == 90, r.id
        for (lo, hi, b, s, ref), (lo2, _, b2, s2, ref2) in zip(r.segments, r.segments[1:]):
            assert hi == lo2, r.id
            assert b + s * (hi - ref) == pytest.approx(b2 + s2 * (lo2 - ref2), abs=0.05), r.id
        assert all(-165 <= r.limit(d) <= -100 for d in (0, 5, 12.5, 25, 60, 90)), r.id
        assert r.source.startswith("RR 2024") and r.page and r.review


@pytest.mark.parametrize("row_id, delta, expected", [
    ("3400-4200_gso", 3, -152), ("3400-4200_gso", 15, -147), ("3400-4200_gso", 30, -142),
    ("17700-19300_gso", 8.036, -113.482), ("13400-13650_gso", 10, -155), ("13400-13650_gso", 82, -150),
    ("2500-2690", 15, -130.5), ("37500-40000_gso", 20, -107), ("40500-42000_gso", 15, -110),
])
def test_limit_values(row_id, delta, expected):
    assert next(r for r in P.limits() if r.id == row_id).limit(delta) == pytest.approx(expected, abs=0.01)


def test_rows_for_listed_countries_do_not_apply_to_finland():
    assert not P.applicable_limits(12_550_000_000, 12_700_000_000, "GSO")
    assert not P.applicable_limits(1_518_000_000, 1_525_000_000, "GSO")        # US-only rows in Table 21-4


def test_ngso_rows_are_not_used_for_gso():
    ids = {r.id for r in P.applicable_limits(10_800_000_000, 10_900_000_000, "GSO")}
    assert ids == {"10700-11700_gso"}


# ---- the formula --------------------------------------------------------------------------------------------

def test_hand_worked_values():
    assert P.spreading_loss_db(38e6) == pytest.approx(162.59, abs=0.01)
    assert P.pfd_db(-40, 0, 4000, 38e6) == pytest.approx(-166.57, abs=0.01)     # per 4 kHz
    assert P.pfd_db(-54, 50, 1e6, 40796.8e3) == pytest.approx(-107.20, abs=0.01)


def em(pd, design="100MG7W--", flagged=False, seq=1):
    from radar.adapters.space_ific import necessary_bandwidth_hz
    return P.Emission(seq, design, pd, necessary_bandwidth_hz(design), flagged)


def test_worst_case_picks_the_smallest_margin_over_points_and_emissions():
    r = P.worst_case(18_700_000_000, 19_200_000_000, 60.5, [em(-60, seq=1), em(-54, seq=2)], 50.0, steerable=True)
    assert r.status == "computed" and r.worst["emission_seq_no"] == 2
    assert r.worst["point"] == "Utsjoki"           # lowest elevation, strictest limit
    assert r.margin_db == pytest.approx(-6.28, abs=0.05)


def test_narrow_emission_uses_its_own_bandwidth():
    r = P.worst_case(3_700_000_000, 3_710_000_000, 25.0, [em(-40, design="2K00G7W--")], 30.0)
    assert r.worst["bandwidth_hz"] == 2000        # narrower than the 4 kHz reference


@pytest.mark.parametrize("args, status", [
    (dict(lo=1_518_000_000, hi=1_525_000_000, lon=25.0, ems=[em(-50)], gain=30.0), "no_limit"),
    (dict(lo=3_700_000_000, hi=3_800_000_000, lon=-100.0, ems=[em(-50)], gain=30.0), "not_visible"),
    (dict(lo=3_700_000_000, hi=3_800_000_000, lon=25.0, ems=[em(73.0, flagged=True)], gain=30.0), "flagged_input"),
    (dict(lo=3_700_000_000, hi=3_800_000_000, lon=25.0, ems=[em(None)], gain=30.0), "no_input"),
    (dict(lo=3_700_000_000, hi=3_800_000_000, lon=25.0, ems=[em(-50)], gain=None), "no_input"),
])
def test_worst_case_statuses(args, status):
    assert P.worst_case(args["lo"], args["hi"], args["lon"], args["ems"], args["gain"]).status == status


# ---- concern adjustment -------------------------------------------------------------------------------------

def res(margin, steerable=True, status="computed"):
    return P.PfdResult(status, -110, -110 + margin, margin, {"steerable": steerable}, notes=["n"])


@pytest.mark.parametrize("pfd, concern", [
    (res(-3, True), "high"), (res(-3, False), "review"), (res(5), "medium"), (res(20), "low"),
    (P.PfdResult("no_limit", notes=["x"]), "medium"), (P.PfdResult("flagged_input", notes=["x"]), "review"),
])
def test_pfd_adjusts_only_downlink_rules(pfd, concern):
    assert RK.pfd_adjust("medium", "downlink over a Finnish primary terrestrial allocation", pfd)[0] == concern
    assert RK.pfd_adjust("high", "the Bureau lists Finland as affected (9.14)", pfd)[0] == "high"


# ---- real data ----------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def run_3074():
    from radar.pipeline import assemble
    return assemble.run(3074)


@needs_db
def test_3074_pfd_results(run_3074):
    P_ = run_3074.pfd
    computed = [r for r in P_.values() if r.status == "computed"]
    assert len(computed) > 500 and all(-250 <= r.pfd_db <= -80 for r in computed if r.orbit == "GSO")
    # non-GSO: one satellite at its perigee; the strongest filings (e.g. YG-1, 54 dBi at 27 GHz from 550 km) reach -68
    assert all(-250 <= r.pfd_db <= -60 for r in computed if r.orbit != "GSO")
    assert P_["124794008"].margin_db == pytest.approx(-6.28, abs=0.05)
    assert P_["124794008"].worst["steerable"] is True


@needs_db
def test_3074_trace_cites_evidence_in_its_own_finding(run_3074):
    traced = [f for f in run_3074.result.findings if f.calc.method == "pfd_gso_worst_case" and f.calc.result_value is not None]
    assert traced
    for f in traced:
        ids = {e.id for e in f.evidence}
        assert {i.evidence_id for i in f.calc.inputs} <= ids and f.calc.limit_evidence_id in ids
        assert f.calc.label == "indicative" and f.calc.margin_db == pytest.approx(f.calc.limit_value - f.calc.result_value, abs=0.02)
    chinasat = next(f for f in run_3074.result.findings if f.notice_id == "124520183")
    assert chinasat.concern == "high" and "steerable" in chinasat.reason
