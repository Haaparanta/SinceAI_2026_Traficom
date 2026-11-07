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


def test_security_headers_on_pages():
    r = client.get("/health", headers={"host": "filingradar.click"})
    h = r.headers
    assert "default-src 'self'" in h["Content-Security-Policy"]
    assert "object-src 'none'" in h["Content-Security-Policy"]
    assert h["Strict-Transport-Security"].startswith("max-age=")
    assert "camera=()" in h["Permissions-Policy"]
    assert h["Cross-Origin-Opener-Policy"] == "same-origin"


def test_api_docs_keep_working_without_csp():
    # Swagger UI under /api/docs loads from a CDN, so the page CSP is not applied to /api/.
    assert "Content-Security-Policy" not in client.get("/api/issues").headers


def test_inline_script_hashes(tmp_path):
    import base64
    import hashlib

    from radar.serve import inline_script_hashes
    p = tmp_path / "index.html"
    p.write_text('<script>var a=1</script><script type="application/ld+json">{}</script><script src="/x.js"></script>')
    expected = "'sha256-" + base64.b64encode(hashlib.sha256(b"var a=1").digest()).decode() + "'"
    assert inline_script_hashes(p) == [expected]   # only the executable inline script, not JSON-LD or src scripts
