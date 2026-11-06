"""FastAPI routes (pm_pack/06 "API"). Only the reference lookup exists so far (step A6); the rest arrive with Phase B.

    uv run uvicorn radar.main:app --app-dir backend --reload
"""
from __future__ import annotations

from fastapi import FastAPI, HTTPException, Query

from radar.adapters import traficom_table
from radar.models import FinnishSubBand

app = FastAPI(title="Filing Radar", version="0.1.0")


@app.get("/reference/subbands", response_model=list[FinnishSubBand])
def reference_subbands(hz: int = Query(..., ge=0, description="Frequency in Hz, e.g. 11000000000")) -> list[FinnishSubBand]:
    """Every Finnish sub-band (Traficom table row) that contains `hz`."""
    try:
        return traficom_table.at_frequency(hz)
    except FileNotFoundError as exc:
        raise HTTPException(503, f"Finnish table not available: {exc}. Run make subbands.") from exc
