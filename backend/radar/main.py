"""FastAPI routes (pm_pack/06 "API").

The screen reads the analyses from data/cache/<kind>_<issue>.json (built by scripts/build_cache.py from a live run),
so it needs neither the .mdb nor DuckDB, and demo mode is the same code path. Every number the screen shows comes
from these files: findings, CalcTraces and counted queries, never a literal in the UI (pm_pack/06 rule 5).

    uv run uvicorn radar.main:app --app-dir backend --port 8000
"""
from __future__ import annotations

import json
from functools import lru_cache
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse

from radar.adapters import traficom_table
from radar.config import ROOT, settings
from radar.models import AnalysisResult, FinnishSubBand

app = FastAPI(title="Filing Radar", version="0.2.0")
CACHE = settings.data_dir / "cache"
KINDS = ("space", "terrestrial")


def _cache_files() -> list[Path]:
    return sorted(CACHE.glob("*_*.json"))


@lru_cache(maxsize=8)
def _bundle(kind: str, issue: int, mtime: float) -> dict:
    data = json.loads((CACHE / f"{kind}_{issue}.json").read_text(encoding="utf-8"))
    AnalysisResult.model_validate(data["result"])          # contract check on every load
    return data


def bundle(kind: str, issue: int) -> dict:
    p = CACHE / f"{kind}_{issue}.json"
    if kind not in KINDS or not p.exists():
        raise HTTPException(404, f"no analysis for {kind} {issue}; run scripts/build_cache.py")
    return _bundle(kind, issue, p.stat().st_mtime)


@app.get("/issues")
def issues() -> list[dict]:
    out = []
    for p in _cache_files():
        kind, issue = p.stem.split("_", 1)
        if kind not in KINDS:
            continue
        r = bundle(kind, int(issue))["result"]
        out.append({"kind": kind, "issue": int(issue), "screened": r["screened"], "flagged": r["flagged"],
                    "provenance_coverage_pct": r["provenance_coverage_pct"]})
    return out


@app.get("/analysis/{kind}/{issue}")
def analysis(kind: str, issue: int) -> dict:
    """The whole analysis for the screen: AnalysisResult plus the per-finding context."""
    return bundle(kind, issue)


@app.get("/findings")
def findings(issue: int = Query(...), kind: str = Query("space")) -> list[dict]:
    return bundle(kind, issue)["result"]["findings"]


@app.get("/findings/{finding_id}")
def finding(finding_id: str) -> dict:
    for p in _cache_files():
        kind, issue = p.stem.split("_", 1)
        b = bundle(kind, int(issue))
        for f in b["result"]["findings"]:
            if f["id"] == finding_id:
                return {"finding": f, "context": b["context"].get(finding_id)}
    raise HTTPException(404, f"finding {finding_id} not found")


@app.get("/metrics")
def metrics(issue: int = Query(...), kind: str = Query("space")) -> dict:
    b = bundle(kind, issue)
    r = b["result"]
    from collections import Counter
    return {"issue": issue, "kind": kind, "screened": r["screened"], "flagged": r["flagged"],
            "provenance_coverage_pct": r["provenance_coverage_pct"],
            "concern": dict(Counter(f["concern"] for f in r["findings"])),
            "evidence_items": sum(len(f["evidence"]) for f in r["findings"])}


@app.get("/export/{issue}")
def export(issue: int, kind: str = Query("space")) -> FileResponse:
    p = ROOT / "results" / f"{kind}_{issue}.csv"
    if not p.exists():
        raise HTTPException(404, f"{p.name} not written yet")
    return FileResponse(p, media_type="text/csv", filename=p.name)


@app.get("/reference/subbands", response_model=list[FinnishSubBand])
def reference_subbands(hz: int = Query(..., ge=0, description="Frequency in Hz, e.g. 11000000000")) -> list[FinnishSubBand]:
    """Every Finnish sub-band (Traficom table row) that contains `hz`."""
    try:
        return traficom_table.at_frequency(hz)
    except FileNotFoundError as exc:
        raise HTTPException(503, f"Finnish table not available: {exc}. Run make subbands.") from exc


@app.get("/reference/region")
def reference_region() -> dict:
    """Finland and its neighbours (Natural Earth 1:50m, public domain) for the map tab."""
    return json.loads((ROOT / "scoring" / "reference" / "finland_region.geojson").read_text(encoding="utf-8"))


@app.get("/reference/points")
def reference_points() -> list[dict]:
    from radar.pipeline.geography import reference_points as pts
    return [{"name": n, "lat": la, "lon": lo} for n, la, lo in pts()]
