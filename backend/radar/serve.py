"""One process for the hosted demo: the API under /api and the built screen (frontend/dist) at /.

The screen calls /api/... (frontend/src/api.ts); in development Vite proxies that prefix to port 8000, here the
same prefix is mounted directly, so the frontend code is identical in both places.

    uv run uvicorn radar.serve:app --app-dir backend --port 8080
"""
from __future__ import annotations

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from starlette.middleware.gzip import GZipMiddleware

from radar.config import ROOT
from radar.main import app as api

DIST = ROOT / "frontend" / "dist"
CANONICAL_HOST = "filingradar.click"   # the run.app address serves the same site but is kept out of search results

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
    if path.startswith("/assets/"):                      # Vite file names carry a content hash
        h["Cache-Control"] = "public, max-age=31536000, immutable"
    elif path.startswith("/api/"):
        h.setdefault("Cache-Control", "no-cache")
    else:                                                # index.html, icons, robots.txt, sitemap.xml
        h.setdefault("Cache-Control", "public, max-age=300")
    if request.url.hostname not in (CANONICAL_HOST, "localhost", "127.0.0.1", "testserver"):
        h["X-Robots-Tag"] = "noindex"
    return response


@app.get("/health")  # not /healthz: the Cloud Run front end reserves paths ending in z
def health() -> dict:
    return {"ok": True}


app.mount("/api", api)
app.mount("/", StaticFiles(directory=DIST, html=True, check_dir=False), name="screen")
