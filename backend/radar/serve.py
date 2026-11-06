"""One process for the hosted demo: the API under /api and the built screen (frontend/dist) at /.

The screen calls /api/... (frontend/src/api.ts); in development Vite proxies that prefix to port 8000, here the
same prefix is mounted directly, so the frontend code is identical in both places.

    uv run uvicorn radar.serve:app --app-dir backend --port 8080
"""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from radar.config import ROOT
from radar.main import app as api

DIST = ROOT / "frontend" / "dist"

app = FastAPI(title="Filing Radar (hosted)", docs_url=None, redoc_url=None, openapi_url=None)


@app.get("/health")  # not /healthz: the Cloud Run front end reserves paths ending in z
def health() -> dict:
    return {"ok": True}


app.mount("/api", api)
app.mount("/", StaticFiles(directory=DIST, html=True, check_dir=False), name="screen")
