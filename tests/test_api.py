"""Step D1 of pm_pack/08: the API the one screen reads. Uses the committed data/cache files."""
from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from radar.config import settings
from radar.main import app

needs_cache = pytest.mark.skipif(not (settings.data_dir / "cache" / "space_3074.json").exists(),
                                 reason="run scripts/build_cache.py")
client = TestClient(app)


@needs_cache
def test_issues_lists_both_analyses():
    got = {(i["kind"], i["issue"]) for i in client.get("/issues").json()}
    assert {("space", 3074), ("terrestrial", 3076)} <= got


@needs_cache
@pytest.mark.parametrize("kind, issue", [("space", 3074), ("terrestrial", 3076)])
def test_analysis_bundle_has_context_for_every_flagged_finding(kind, issue):
    b = client.get(f"/analysis/{kind}/{issue}").json()
    flagged = [f for f in b["result"]["findings"] if f["concern"] != "none"]
    assert flagged and all(f["id"] in b["context"] for f in flagged)
    assert all(f["evidence"] for f in b["result"]["findings"])


@needs_cache
def test_metrics_match_the_results_file_counts():
    m = client.get("/metrics", params={"issue": 3074, "kind": "space"}).json()
    assert m["screened"] == 196 and m["flagged"] == 135 and m["provenance_coverage_pct"] == 100.0
    assert m["concern"]["high"] == 23


@needs_cache
def test_finding_detail_and_unknown_id():
    r = client.get("/findings/F-3074-0001").json()
    assert r["finding"]["id"] == "F-3074-0001" and r["context"]["title"]
    assert client.get("/findings/F-0000-0000").status_code == 404


def test_reference_routes():
    assert len(client.get("/reference/points").json()) == 7
    assert {f["properties"]["itu"] for f in client.get("/reference/region").json()["features"]} >= {"FIN", "S", "NOR", "RUS", "EST"}


def test_export_serves_the_results_csv():
    r = client.get("/export/3074", params={"kind": "space"})
    assert r.status_code == 200 and r.text.startswith("issue,kind,notice_id")
