"""One process for the hosted demo: the API under /api and the built screen (frontend/dist) at /.

The screen calls /api/... (frontend/src/api.ts); in development Vite proxies that prefix to port 8000, here the
same prefix is mounted directly, so the frontend code is identical in both places.

    uv run uvicorn radar.serve:app --app-dir backend --port 8080
"""
from __future__ import annotations

import base64
import hashlib
import re
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware

from radar.config import ROOT
from radar.main import app as api

DIST = ROOT / "frontend" / "dist"
CANONICAL_HOST = "filingradar.click"   # the run.app address serves the same site but is kept out of search results
LOCAL_HOSTS = ("localhost", "127.0.0.1", "testserver")


def inline_script_hashes(index_html: Path) -> list[str]:
    """CSP hashes of the executable inline scripts in the built page (the pre-paint theme script).

    JSON-LD blocks are data, not scripts, so CSP does not apply to them and they are skipped."""
    if not index_html.exists():
        return []
    out = []
    for attrs, body in re.findall(r"<script([^>]*)>(.*?)</script>", index_html.read_text(encoding="utf-8"), re.S):
        if "src=" in attrs or "application/ld+json" in attrs:
            continue
        out.append("'sha256-" + base64.b64encode(hashlib.sha256(body.encode("utf-8")).digest()).decode() + "'")
    return out


def content_security_policy(script_hashes: list[str]) -> str:
    # style-src keeps 'unsafe-inline' because React style={...} props become style attributes.
    return "; ".join([
        "default-src 'self'",
        "script-src 'self' " + " ".join(script_hashes),
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: blob:",
        "font-src 'self'",
        "connect-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'self'",
        "upgrade-insecure-requests",
    ])


CSP = content_security_policy(inline_script_hashes(DIST / "index.html"))
PERMISSIONS = "camera=(), microphone=(), geolocation=(), payment=(), usb=()"

app = FastAPI(title="Filing Radar (hosted)", docs_url=None, redoc_url=None, openapi_url=None)
app.add_middleware(GZipMiddleware, minimum_size=1024)   # the analysis JSON is about 1 MB, about 10x smaller gzipped


@app.middleware("http")
async def site_headers(request: Request, call_next):
    response = await call_next(request)
    path = request.url.path
    h = response.headers
    h.setdefault("X-Content-Type-Options", "nosniff")
    h.setdefault("Referrer-Policy", "strict-origin-when-cross-origin")
    h.setdefault("X-Frame-Options", "SAMEORIGIN")
    h.setdefault("Permissions-Policy", PERMISSIONS)
    h.setdefault("Cross-Origin-Opener-Policy", "same-origin")
    if request.url.hostname not in LOCAL_HOSTS:             # HTTPS only (Cloud Run); browsers ignore it on plain http
        h.setdefault("Strict-Transport-Security", "max-age=31536000; includeSubDomains")
    if not path.startswith("/api/"):                         # the API docs page loads Swagger UI from a CDN
        h.setdefault("Content-Security-Policy", CSP)
    if path.startswith("/assets/"):                      # Vite file names carry a content hash
        h["Cache-Control"] = "public, max-age=31536000, immutable"
    elif path.startswith("/api/"):
        h.setdefault("Cache-Control", "no-cache")
    else:                                                # index.html, icons, robots.txt, sitemap.xml
        h.setdefault("Cache-Control", "public, max-age=300")
    if request.url.hostname not in (CANONICAL_HOST, *LOCAL_HOSTS):
        h["X-Robots-Tag"] = "noindex"
    return response


@app.get("/health")  # not /healthz: the Cloud Run front end reserves paths ending in z
def health() -> dict:
    return {"ok": True}


app.mount("/api", api)
app.mount("/", StaticFiles(directory=DIST, html=True, check_dir=False), name="screen")
