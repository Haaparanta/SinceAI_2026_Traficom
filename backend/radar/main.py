"""FastAPI routes (pm_pack/06 "API").

The screen reads the analyses from data/cache/<kind>_<issue>.json (built by scripts/build_cache.py from a live run),
so it needs neither the .mdb nor DuckDB, and demo mode is the same code path. Every number the screen shows comes
from these files: findings, CalcTraces and counted queries, never a literal in the UI (pm_pack/06 rule 5).

    uv run uvicorn radar.main:app --app-dir backend --port 8000
"""
from __future__ import annotations

import csv
import io
import json
from functools import lru_cache
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

from radar import decisions
from radar.adapters import traficom_table
from radar.config import ROOT, settings
from radar.models import AnalysisResult, FinnishSubBand, ReviewDecision

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
    """The whole analysis for the screen: AnalysisResult, the per-finding context and the latest decisions."""
    return {**bundle(kind, issue), "decisions": decisions.latest(kind, issue)}


@app.get("/findings")
def findings(issue: int = Query(...), kind: str = Query("space")) -> list[dict]:
    return bundle(kind, issue)["result"]["findings"]


def _locate(finding_id: str) -> tuple[str, int, dict, dict]:
    for p in _cache_files():
        kind, issue = p.stem.split("_", 1)
        if kind not in KINDS:
            continue
        b = bundle(kind, int(issue))
        for f in b["result"]["findings"]:
            if f["id"] == finding_id:
                return kind, int(issue), f, b
    raise HTTPException(404, f"finding {finding_id} not found")


@app.get("/findings/{finding_id}")
def finding(finding_id: str) -> dict:
    kind, issue, f, b = _locate(finding_id)
    return {"finding": f, "context": b["context"].get(finding_id),
            "decisions": [e for e in decisions.log(kind, issue) if e["finding_id"] == finding_id]}


class DecisionIn(BaseModel):
    decision: Literal["approve", "dismiss", "investigate"]
    reviewer: str = Field(min_length=2, max_length=80)
    note: str = Field(min_length=3, max_length=500)


@app.post("/findings/{finding_id}/decision", status_code=201)
def decide(finding_id: str, body: DecisionIn) -> dict:
    """Append a reviewer decision to the audit log. The computed concern is never changed (pm_pack/06 rule 1)."""
    kind, issue, f, _ = _locate(finding_id)
    d = ReviewDecision(finding_id=finding_id, decision=body.decision, reviewer=body.reviewer.strip(),
                       note=body.note.strip(), at=decisions.now())
    try:
        return decisions.record(kind, issue, finding_id=finding_id, notice_id=f["notice_id"], concern=f["concern"], decision=d)
    except ValueError as exc:
        raise HTTPException(409, str(exc)) from exc


@app.get("/findings/{finding_id}/decisions")
def finding_decisions(finding_id: str) -> list[dict]:
    kind, issue, _, _ = _locate(finding_id)
    return [e for e in decisions.log(kind, issue) if e["finding_id"] == finding_id]


@app.get("/llm/status")
def llm_status() -> dict:
    """Whether explanations and letters come from Claude or from the deterministic template."""
    from radar.llm import client as llm_client
    return llm_client.status()


@app.post("/findings/{finding_id}/explanation")
def explanation(finding_id: str) -> dict:
    """Plain-language explanation that cites only the finding's evidence (cache, then Claude, then template)."""
    from radar.llm import drafts
    kind, issue, f, b = _locate(finding_id)
    return drafts.explain(f, b["context"].get(finding_id), kind, issue).as_dict()


@app.post("/findings/{finding_id}/letter")
def letter(finding_id: str) -> dict:
    """Correspondence draft to the notifying administration. Always a draft; nothing is sent."""
    from radar.llm import drafts
    kind, issue, f, b = _locate(finding_id)
    return drafts.letter(f, b["context"].get(finding_id), kind, issue).as_dict()


@app.get("/audit")
def audit(issue: int = Query(...), kind: str = Query("space")) -> dict:
    """Every decision for the analysis, newest first, and the result of re-checking the hash chain."""
    bundle(kind, issue)
    return {"chain": decisions.verify(kind, issue), "entries": list(reversed(decisions.log(kind, issue)))}


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
def export(issue: int, kind: str = Query("space")) -> Response:
    """The results file with the latest reviewer decision per notice in the decision column."""
    p = ROOT / "results" / f"{kind}_{issue}.csv"
    if not p.exists():
        raise HTTPException(404, f"{p.name} not written yet")
    latest = decisions.latest(kind, issue)
    by_notice: dict[str, dict] = {}
    for e in latest.values():                      # one decision per notice: the most recent one
        if e["notice_id"] not in by_notice or e["seq"] > by_notice[e["notice_id"]]["seq"]:
            by_notice[e["notice_id"]] = e
    src = io.StringIO(p.read_text(encoding="utf-8"))
    reader = csv.DictReader(src)
    out = io.StringIO()
    w = csv.DictWriter(out, fieldnames=reader.fieldnames, lineterminator="\n")
    w.writeheader()
    for row in reader:
        e = by_notice.get(row["notice_id"])
        if e:
            row["decision"] = decisions.export_value(e)
        w.writerow(row)
    return Response(out.getvalue(), media_type="text/csv",
                    headers={"Content-Disposition": f'attachment; filename="{p.name}"'})


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
