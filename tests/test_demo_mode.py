"""Step E3 of pm_pack/08: demo mode works with the network cut.

Every outgoing connection except loopback raises, a (fake) API key is present to prove DEMO_MODE wins over
credentials, and every endpoint the screen uses must still answer from the committed cache files.
"""
from __future__ import annotations

import socket

import pytest
from fastapi.testclient import TestClient

from radar.config import settings
from radar.llm import client as C

needs_cache = pytest.mark.skipif(not (settings.data_dir / "cache" / "space_3074.json").exists(),
                                 reason="run scripts/build_cache.py")


@pytest.fixture
def offline(monkeypatch, tmp_path):
    attempts: list = []
    real_connect = socket.socket.connect

    def guarded(self, address):
        host = address[0] if isinstance(address, tuple) else address
        if host not in ("127.0.0.1", "::1", "localhost"):
            attempts.append(address)
            raise OSError(f"network is off in this test: {address}")
        return real_connect(self, address)

    monkeypatch.setattr(socket.socket, "connect", guarded)
    monkeypatch.setattr(socket, "create_connection", lambda *a, **k: (_ for _ in ()).throw(OSError("network is off")))
    monkeypatch.setenv("DEMO_MODE", "1")
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-test-not-a-real-key")
    monkeypatch.setenv("DECISIONS_DIR", str(tmp_path / "decisions"))
    monkeypatch.delenv("LLM_DISABLED", raising=False)
    monkeypatch.setattr(C, "get_client", lambda: pytest.fail("demo mode must never build a Claude client"))
    return attempts


def test_demo_mode_blocks_the_language_model(offline):
    st = C.status()
    assert st["demo_mode"] and not st["available"] and "DEMO_MODE=1" in st["reason"]


@needs_cache
@pytest.mark.parametrize("kind, issue", [("space", 3074), ("terrestrial", 3076)])
def test_every_screen_endpoint_answers_offline(offline, kind, issue):
    from radar.main import app
    client = TestClient(app)
    assert client.get("/llm/status").json()["demo_mode"] is True
    assert {(i["kind"], i["issue"]) for i in client.get("/issues").json()} >= {(kind, issue)}
    b = client.get(f"/analysis/{kind}/{issue}").json()
    assert b["result"]["from_cache"] is True
    f = next(x for x in b["result"]["findings"] if x["concern"] != "none")
    assert client.get(f"/findings/{f['id']}").status_code == 200
    assert client.get("/findings", params={"issue": issue, "kind": kind}).status_code == 200
    ex = client.post(f"/findings/{f['id']}/explanation").json()
    le = client.post(f"/findings/{f['id']}/letter").json()
    assert ex["source"] in ("template",) or ex["source"].startswith("cache:")
    assert le["output"]["body_markdown"].startswith("*DRAFT")
    assert any("DEMO_MODE=1" in n for n in ex["notes"]) or ex["source"].startswith("cache:")
    d = client.post(f"/findings/{f['id']}/decision", json={"decision": "investigate", "reviewer": "Demo", "note": "offline test"})
    assert d.status_code == 201
    assert client.get("/audit", params={"issue": issue, "kind": kind}).json()["chain"]["ok"] is True
    assert client.get("/metrics", params={"issue": issue, "kind": kind}).status_code == 200
    assert client.get(f"/export/{issue}", params={"kind": kind}).status_code == 200
    assert client.get("/reference/region").status_code == 200
    assert offline == []
