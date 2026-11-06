"""Step C3 of pm_pack/08: the P.1546 engine, its ITU validation, and the terrestrial screening of 3076."""
from __future__ import annotations

import contextlib
import csv
import io
import os
import runpy
import shutil
from pathlib import Path

import pytest

from radar.calc import p1546 as P
from radar.pipeline import terrestrial as TR

HERE = Path(__file__).parent


def _results(path: Path) -> dict:
    out = {}
    for row in csv.reader(path.open()):
        if row and not row[0].startswith("#"):
            out[(row[1].strip(), int(row[2]))] = float(row[4])
    return out


def test_itu_validation_suite_reproduces_all_52_reference_cases(tmp_path, monkeypatch):
    work = tmp_path / "v"
    shutil.copytree(HERE / "p1546_validation", work)
    (work / "validation_results").mkdir()
    monkeypatch.chdir(work)
    monkeypatch.setenv("MPLBACKEND", "Agg")
    with contextlib.redirect_stdout(io.StringIO()):
        runpy.run_path(str(work / "validateP1546.py"), run_name="__main__")
    ref = _results(work / "reference_combined_results.csv")
    got = _results(work / "validation_results" / "combined_results.csv")
    assert len(ref) == 52 and set(got) == set(ref)
    assert max(abs(got[k] - ref[k]) for k in ref) < 1e-6


# ---- the wrapper ----------------------------------------------------------------------------------------------

def test_power_scales_one_to_one():
    a = P.field_strength(153.0, [(30, "Land")], 45, 30.0)
    b = P.field_strength(153.0, [(30, "Land")], 45, 40.0)
    assert b.e_dbuv_m - a.e_dbuv_m == pytest.approx(10.0, abs=0.01)


def test_never_above_free_space_and_falls_with_distance():
    values = [P.field_strength(425.0, [(d, "Land")], 37.5, 30.0) for d in (1, 10, 50, 100, 300, 600)]
    assert all(v.e_dbuv_m <= v.free_space_dbuv_m for v in values)
    assert all(a.e_dbuv_m > b.e_dbuv_m for a, b in zip(values, values[1:]))


def test_sea_carries_further_than_mixed_further_than_land():
    land = P.field_strength(425.0, [(100, "Land")], 37.5, 30.0).e_dbuv_m
    mixed = P.field_strength(425.0, [(40, "Land"), (60, "Cold")], 37.5, 30.0).e_dbuv_m
    sea = P.field_strength(425.0, [(100, "Cold")], 37.5, 30.0).e_dbuv_m
    assert sea > mixed > land


def test_free_space_reference():
    assert P.free_space_dbuv_m(30.0, 1.0) == pytest.approx(106.9)       # 1 kW e.r.p. at 1 km


# ---- T/R 25-08 triggers -----------------------------------------------------------------------------------------

@pytest.mark.parametrize("f_hz, bw_hz, trigger, bc", [
    (35_000_000, 12_500, 0, 0.0), (80_000_000, 25_000, 6, 0.0), (153_000_000, 12_500, 12, 0.0),
    (390_000_000, 25_000, 18, 0.0), (425_825_000, 18_000, 20, 0.0), (450_000_000, 200_000, 20, 9.03),
])
def test_thresholds_and_bandwidth_correction(f_hz, bw_hz, trigger, bc):
    row, corr = TR.threshold_for(f_hz, bw_hz)
    assert row.threshold_dbuv_m == trigger and corr == pytest.approx(bc, abs=0.01)


def test_no_trigger_above_470_mhz():
    assert TR.threshold_for(793_500_000, 5_000_000)[0] is None


# ---- 3076 -------------------------------------------------------------------------------------------------------

needs_db = pytest.mark.skipif(not (Path(__file__).parents[1] / "data/derived/terrestrial_3076.duckdb").exists(),
                              reason="run make convert first")


@pytest.fixture(scope="module")
def run_3076():
    return TR.run(3076)


@needs_db
def test_3076_concerns(run_3076):
    from collections import Counter
    assert Counter(f.concern for f in run_3076.result.findings) == {"none": 3992, "low": 52, "review": 6, "high": 6, "medium": 1}
    assert run_3076.result.provenance_coverage_pct == 100.0


@needs_db
def test_3076_kostomuksha_exceeds_the_trigger(run_3076):
    by_site = [(run_3076.calcs[f.notice_id], f) for f in run_3076.result.findings if f.concern == "high"]
    k = next((c, f) for c, f in by_site if "KOSTOMUKSHA" in f.reason or c.distance_km == 31.5)
    assert k[0].margin_db == pytest.approx(-13.0, abs=0.1) and k[0].trigger_dbuv_m == 12.0


@needs_db
def test_3076_every_computed_trace_cites_its_own_evidence(run_3076):
    for f in run_3076.result.findings:
        if f.calc.method == "p1546_field_strength":
            ids = {e.id for e in f.evidence}
            assert {i.evidence_id for i in f.calc.inputs} <= ids
            assert f.calc.label == "indicative" and f.calc.result_value <= run_3076.calcs[f.notice_id].free_space_dbuv_m


@needs_db
def test_3076_citations_resolve(run_3076):
    from radar import evidence_check
    checks = evidence_check.check(run_3076.result)
    assert checks and not [c for c in checks if c.status != "PASS"]


@pytest.mark.parametrize("f_hz, trigger", [
    (29_700_000, 0), (47_000_000, 0), (108_000_000, 6), (380_000_000, 12), (400_000_000, 18), (470_000_000, 20),
])
def test_shared_band_edge_takes_the_stricter_trigger(f_hz, trigger):
    """T/R 25-08 A1.2.3 ranges share their edges; on an edge the lower (stricter) trigger applies."""
    assert TR.threshold_for(f_hz, 25_000)[0].threshold_dbuv_m == trigger
