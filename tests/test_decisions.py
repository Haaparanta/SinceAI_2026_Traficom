"""Step D3 of pm_pack/08: reviewer decisions and the tamper-evident audit log."""
from __future__ import annotations

import csv
import io
import json

import pytest
from fastapi.testclient import TestClient

from radar import decisions as D
from radar.config import settings
from radar.main import app
from radar.models import ReviewDecision

needs_cache = pytest.mark.skipif(not (settings.data_dir / "cache" / "space_3074.json").exists(),
                                 reason="run scripts/build_cache.py")


@pytest.fixture(autouse=True)
def isolated_log(tmp_path, monkeypatch):
    monkeypatch.setenv("DECISIONS_DIR", str(tmp_path / "decisions"))
    yield tmp_path / "decisions"


def rd(fid="F-1", decision="investigate", note="check the beam"):
    return ReviewDecision(finding_id=fid, decision=decision, reviewer="Tester", note=note, at=D.now())


# ---- the log ----------------------------------------------------------------------------------------------------

def test_chain_links_every_entry_and_verifies():
    for i, dec in enumerate(["investigate", "approve", "dismiss"]):
        D.record("space", 1, finding_id=f"F-{i}", notice_id=f"N-{i}", concern="high", decision=rd(f"F-{i}", dec))
    log = D.log("space", 1)
    assert [e["seq"] for e in log] == [1, 2, 3]
    assert log[0]["prev_hash"] == D.GENESIS and log[1]["prev_hash"] == log[0]["hash"]
    assert D.verify("space", 1) == {"ok": True, "entries": 3, "first_bad_seq": None, "head": log[2]["hash"]}


@pytest.mark.parametrize("tamper", ["edit", "delete", "reorder"])
def test_any_change_to_an_earlier_line_is_detected(isolated_log, tamper):
    for i in range(3):
        D.record("space", 1, finding_id=f"F-{i}", notice_id=f"N-{i}", concern="high", decision=rd(f"F-{i}"))
    p = isolated_log / "space_1.jsonl"
    lines = p.read_text().splitlines()
    if tamper == "edit":
        e = json.loads(lines[0]); e["decision"] = "dismiss"; lines[0] = json.dumps(e, sort_keys=True)
    elif tamper == "delete":
        del lines[1]
    else:
        lines[0], lines[1] = lines[1], lines[0]
    p.write_text("\n".join(lines) + "\n")
    v = D.verify("space", 1)
    assert not v["ok"] and v["first_bad_seq"] in (1, 2)
    with pytest.raises(ValueError):
        D.record("space", 1, finding_id="F-9", notice_id="N-9", concern="low", decision=rd("F-9"))


def test_latest_keeps_the_most_recent_decision_per_finding():
    D.record("space", 1, finding_id="F-1", notice_id="N-1", concern="high", decision=rd("F-1", "investigate"))
    D.record("space", 1, finding_id="F-1", notice_id="N-1", concern="high", decision=rd("F-1", "approve"))
    assert D.latest("space", 1)["F-1"]["decision"] == "approve"
    assert len(D.log("space", 1)) == 2            # nothing is rewritten


# ---- the API ----------------------------------------------------------------------------------------------------

client = TestClient(app)


@needs_cache
def test_post_decision_records_it_and_never_changes_the_concern():
    before = client.get("/findings/F-3074-0001").json()["finding"]
    r = client.post("/findings/F-3074-0001/decision", json={"decision": "investigate", "reviewer": "Aino", "note": "steerable beam, ask CHN"})
    assert r.status_code == 201
    e = r.json()
    assert e["concern_at_decision"] == before["concern"] and e["notice_id"] == before["notice_id"] and e["seq"] == 1
    after = client.get("/findings/F-3074-0001").json()
    assert after["finding"]["concern"] == before["concern"]
    assert [d["decision"] for d in after["decisions"]] == ["investigate"]
    assert client.get("/analysis/space/3074").json()["decisions"]["F-3074-0001"]["reviewer"] == "Aino"
    audit = client.get("/audit", params={"issue": 3074, "kind": "space"}).json()
    assert audit["chain"]["ok"] and len(audit["entries"]) == 1


@needs_cache
@pytest.mark.parametrize("body, status", [
    ({"decision": "delete", "reviewer": "Aino", "note": "x" * 5}, 422),
    ({"decision": "approve", "reviewer": "", "note": "x" * 5}, 422),
    ({"decision": "approve", "reviewer": "Aino", "note": ""}, 422),
])
def test_invalid_decisions_are_rejected(body, status):
    assert client.post("/findings/F-3074-0001/decision", json=body).status_code == status
    assert client.post("/findings/F-0000-0000/decision", json={"decision": "approve", "reviewer": "Aino", "note": "fine"}).status_code == 404


@needs_cache
def test_export_carries_the_latest_decision_for_the_notice():
    notice = client.get("/findings/F-3074-0002").json()["finding"]["notice_id"]
    client.post("/findings/F-3074-0002/decision", json={"decision": "dismiss", "reviewer": "Aino", "note": "outside the service area"})
    rows = list(csv.DictReader(io.StringIO(client.get("/export/3074", params={"kind": "space"}).text)))
    row = next(r for r in rows if r["notice_id"] == notice)
    assert row["decision"].startswith("dismiss by Aino at ") and row["decision"].endswith("outside the service area")
    assert sum(1 for r in rows if r["decision"]) == 1
