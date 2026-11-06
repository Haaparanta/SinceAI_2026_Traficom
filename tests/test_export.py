"""Step B5 of pm_pack/08: results files. Determinism is plan step E1."""
from __future__ import annotations

import csv
import json

import pytest

from radar.adapters import space_ific
from radar.export import results as X
from radar.models import ResultRow

needs_db = pytest.mark.skipif(not space_ific.db_path(3074).exists(), reason="run make convert first")


def test_columns_follow_the_contract():
    assert X.COLUMNS[:3] == ["issue", "kind", "notice_id"] and X.COLUMNS[-1] == "decision"
    assert set(X.COLUMNS) == set(ResultRow.model_fields)


def test_csv_writes_empty_for_none_and_round_trips():
    r = ResultRow(issue=1, kind="space", notice_id="N", special_section=None, administration="X", network_or_station="S",
                  freq_min_mhz=1.5, freq_max_mhz=None, direction=None, finnish_match="A; B (IDs 1, 2)",
                  special_interest_station_ids=None, overlap_mhz=None, geo_relevance="unknown", calc_method="none",
                  calc_value=None, calc_unit=None, limit_value=None, margin_db=None, concern="low",
                  reason='quote " and, comma', evidence_refs="a; b")
    text = X.to_csv([r])
    back = next(csv.DictReader(text.splitlines()))
    assert back["freq_max_mhz"] == "" and back["reason"] == 'quote " and, comma'
    assert ResultRow(**{k: (None if v == "" else v) for k, v in back.items()}) == r


@needs_db
def test_export_is_byte_identical_across_runs(tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    X.export_space(3074, a)
    X.export_space(3074, b)
    for name in ("space_3074.csv", "space_3074.json", "space_3074_groups.csv"):
        assert (a / name).read_bytes() == (b / name).read_bytes(), name


@needs_db
def test_exported_rows_match_the_findings(tmp_path):
    s = X.export_space(3074, tmp_path)
    rows = [ResultRow(**r) for r in json.loads((tmp_path / "space_3074.json").read_text())]
    assert len(rows) == 196 == s["run"].result.screened
    assert s["concern"] == {"high": 18, "medium": 104, "review": 1, "low": 12, "none": 61}
    assert X.concern_order_ok(rows)
    assert rows[0].notice_id == s["run"].result.findings[0].notice_id
    assert all(r.evidence_refs.startswith("notice.ntc_id=") for r in rows)
    assert s["group_rows"] == sum(1 for r in s["run"].rows if r.candidate)
