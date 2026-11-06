"""Step D3 of pm_pack/08: reviewer decisions in an append-only, tamper-evident audit log.

One file per analysis, data/decisions/<kind>_<issue>.jsonl (git-ignored: local reviewer data; DECISIONS_DIR overrides
the folder). Each line is a ReviewDecision (the frozen contract) plus where it applies and a hash chain:

    {"seq": 3, "kind": "space", "issue": 3074, "finding_id": "F-3074-0001", "notice_id": "124520183",
     "concern_at_decision": "high", "decision": "investigate", "reviewer": "...", "note": "...", "at": "...",
     "prev_hash": "<hash of line 2>", "hash": "<sha-256 of this line without 'hash'>"}

Rules (pm_pack/06 rule 1, pm_pack/08 D3): a decision never changes the computed concern; a later decision supersedes
an earlier one for display and export, but nothing is ever rewritten or deleted; verify() detects any edit,
deletion or reordering of earlier lines.
"""
from __future__ import annotations

import hashlib
import json
import os
import threading
from datetime import datetime, timezone
from pathlib import Path

from radar.config import settings
from radar.models import ReviewDecision

GENESIS = "0" * 64
_lock = threading.Lock()


def decisions_dir() -> Path:
    return Path(os.environ.get("DECISIONS_DIR", settings.data_dir / "decisions"))


def _path(kind: str, issue: int) -> Path:
    return decisions_dir() / f"{kind}_{issue}.jsonl"


def _hash(entry: dict) -> str:
    body = {k: v for k, v in entry.items() if k != "hash"}
    return hashlib.sha256(json.dumps(body, sort_keys=True, separators=(",", ":"), ensure_ascii=False).encode()).hexdigest()


def log(kind: str, issue: int) -> list[dict]:
    p = _path(kind, issue)
    if not p.exists():
        return []
    return [json.loads(line) for line in p.read_text(encoding="utf-8").splitlines() if line.strip()]


def verify(kind: str, issue: int) -> dict:
    """Recompute the chain. ok is False at the first line whose hash or link does not match."""
    prev = GENESIS
    entries = log(kind, issue)
    for i, e in enumerate(entries):
        if e.get("seq") != i + 1 or e.get("prev_hash") != prev or e.get("hash") != _hash(e):
            return {"ok": False, "entries": len(entries), "first_bad_seq": i + 1}
        prev = e["hash"]
    return {"ok": True, "entries": len(entries), "first_bad_seq": None, "head": prev}


def record(kind: str, issue: int, *, finding_id: str, notice_id: str, concern: str,
           decision: ReviewDecision) -> dict:
    with _lock:
        chain = verify(kind, issue)
        if not chain["ok"]:
            raise ValueError(f"audit log {kind}_{issue} fails verification at line {chain['first_bad_seq']}; not appending")
        entries = log(kind, issue)
        entry = {
            "seq": len(entries) + 1, "kind": kind, "issue": issue, "finding_id": finding_id, "notice_id": notice_id,
            "concern_at_decision": concern, **json.loads(decision.model_dump_json()),
            "prev_hash": entries[-1]["hash"] if entries else GENESIS,
        }
        entry["hash"] = _hash(entry)
        p = _path(kind, issue)
        p.parent.mkdir(parents=True, exist_ok=True)
        with p.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(entry, ensure_ascii=False, sort_keys=True) + "\n")
        return entry


def latest(kind: str, issue: int) -> dict[str, dict]:
    """finding_id -> the most recent decision for it."""
    out: dict[str, dict] = {}
    for e in log(kind, issue):
        out[e["finding_id"]] = e
    return out


def now() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0)


def export_value(e: dict) -> str:
    """The text written into the results file's decision column."""
    return f"{e['decision']} by {e['reviewer']} at {e['at']}" + (f": {e['note']}" if e.get("note") else "")
