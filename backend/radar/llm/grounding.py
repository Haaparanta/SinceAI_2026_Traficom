"""Grounding for every language-model output (pm_pack/06 "LLM contract", rule 6).

* payload():  the only thing the model sees: the finding (reason, trace, evidence) and a few context facts.
* validate(): rejects text that cites an evidence id the finding does not have, or writes a number that is not in
  the payload (after normalising: sign and trailing zeros ignored, thousands separators removed).
* cache:      outputs are stored under data/cache/llm/ keyed by the hash of model, prompt and payload, so a rerun or
  demo mode gives the same text without a call.
"""
from __future__ import annotations

import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path

from radar.config import ROOT, settings

NUMBER = re.compile(r"(?<![A-Za-z])-?\d[\d  ]*(?:[.,]\d+)?")


def payload(finding: dict, context: dict | None, kind: str, issue: int) -> dict:
    ctx = context or {}
    notice = ctx.get("notice") or {}
    group = ctx.get("group") or {}
    return {
        "ific": {"kind": kind, "issue": issue},
        "notice_id": finding["notice_id"],
        "title": ctx.get("title"),
        "administration": notice.get("administration"),
        "special_section": notice.get("special_section") or notice.get("notice_type"),
        "orbit_or_station": notice.get("orbit") or notice.get("station_class"),
        "frequency_range_hz": [group.get("freq_min_hz"), group.get("freq_max_hz")] if kind == "space" and group else None,
        "assigned_frequency_hz": notice.get("freq_hz"),
        "bandwidth_hz": notice.get("bandwidth_hz"),
        "direction": group.get("direction"),
        "concern": finding["concern"],
        "reason": finding["reason"],
        "geo_relevance": finding["geo_relevance"],
        "calculation": finding["calc"],
        "evidence": [{"id": e["id"], "kind": e["kind"], "locator": e["locator"], "excerpt": e["excerpt"]}
                     for e in finding["evidence"]],
    }


def _norm(token: str) -> str | None:
    t = token.replace(" ", "").replace(" ", "").lstrip("-")
    if "," in t and "." not in t:
        t = t.replace(",", ".")
    try:
        v = float(t)
    except ValueError:
        return None
    return f"{v:.6f}".rstrip("0").rstrip(".")


def numbers(text: str) -> set[str]:
    out = set()
    for m in NUMBER.findall(text):
        for part in re.split(r"[  ]", m.strip()) + [m]:
            n = _norm(part)
            if n is not None:
                out.add(n)
    return out


@dataclass
class Check:
    ok: bool
    cited: list[str]
    unknown_ids: list[str] = field(default_factory=list)
    unsupported_numbers: list[str] = field(default_factory=list)

    def summary(self) -> str:
        if self.ok:
            return f"checked: {len(self.cited)} evidence id(s) cited, all in the finding; every number appears in the evidence"
        parts = []
        if self.unknown_ids:
            parts.append(f"cites ids not in the finding: {', '.join(self.unknown_ids)}")
        if self.unsupported_numbers:
            parts.append(f"numbers not in the evidence: {', '.join(self.unsupported_numbers[:8])}")
        if not self.cited:
            parts.append("cites no evidence")
        return "; ".join(parts)


def validate(texts: list[str], cited: list[str], data: dict) -> Check:
    allowed = {e["id"] for e in data["evidence"]}
    pool = numbers(json.dumps(data, ensure_ascii=False))
    for e in data["evidence"]:                         # ids such as E-012 and F-3074-0001 contain digits
        pool |= numbers(e["id"])
    unknown = sorted(set(cited) - allowed)
    unsupported = sorted({n for t in texts for n in numbers(t)} - pool, key=lambda s: float(s))
    return Check(ok=not unknown and not unsupported and bool(cited), cited=list(cited), unknown_ids=unknown,
                 unsupported_numbers=unsupported)


def prompt(name: str) -> str:
    return (ROOT / "prompts" / f"{name}.md").read_text(encoding="utf-8")


def cache_path(task: str, data: dict, model: str) -> Path:
    key = hashlib.sha256(json.dumps({"task": task, "model": model, "prompt": prompt(task), "payload": data},
                                    sort_keys=True, ensure_ascii=False).encode()).hexdigest()[:16]
    ific = data["ific"]
    return settings.data_dir / "cache" / "llm" / f"{ific['kind']}_{ific['issue']}" / f"{task}_{key}.json"


def cache_get(task: str, data: dict, model: str) -> dict | None:
    p = cache_path(task, data, model)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else None


def cache_put(task: str, data: dict, model: str, record: dict) -> None:
    p = cache_path(task, data, model)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(record, indent=1, ensure_ascii=False, sort_keys=True) + "\n", encoding="utf-8")
