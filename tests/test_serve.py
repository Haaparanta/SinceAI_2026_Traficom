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


def test_site_headers():
    r = client.get("/api/issues")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["Cache-Control"] == "no-cache"
    assert "X-Robots-Tag" not in r.headers


def test_non_canonical_host_is_not_indexed():
    r = client.get("/api/issues", headers={"host": "filing-radar-ga6ca37kma-lz.a.run.app"})
    assert r.headers["X-Robots-Tag"] == "noindex"


def test_large_responses_are_gzipped():
    r = client.get("/api/analysis/space/3074", headers={"accept-encoding": "gzip"})
    assert r.headers.get("content-encoding") == "gzip"
