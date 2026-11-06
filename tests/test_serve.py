"""The hosted app mounts the API under /api, the prefix the screen calls (frontend/src/api.ts)."""
from fastapi.testclient import TestClient

from radar.serve import app

client = TestClient(app)


def test_health():
    assert client.get("/health").json() == {"ok": True}


def test_api_is_mounted_under_prefix():
    r = client.get("/api/issues")
    assert r.status_code == 200
    assert {(i["kind"], i["issue"]) for i in r.json()} >= {("space", 3074), ("terrestrial", 3076)}
