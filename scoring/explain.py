"""Deterministic plain-language explanations built only from factor reasons and evidence.

No language model is involved. The text is a fixed template over the audit trail, so
the same inputs always produce the same explanation and every sentence maps to a factor.
"""
from __future__ import annotations

from .models import Finding, ScoredSubject

GROUP_TITLES = {"relevance": "Relevance (multiplied)", "severity": "Severity (weighted)", "urgency": "Urgency (weighted)"}


def explain_finding(f: Finding, cfg: dict) -> str:
    label = cfg.get("priority_labels", {}).get(f.priority, f.priority)
    lines = [
        f"{f.subject_label} vs {f.target_label}.",
        f"Score {f.score}/100, priority {f.priority} ({label}): relevance {f.relevance:.2f} x "
        f"({cfg['score']['severity_weight']:.2f} x severity {f.severity:.2f} + {cfg['score']['urgency_weight']:.2f} x urgency {f.urgency:.2f}); "
        f"confidence {f.confidence:.0%}.",
    ]
    if f.screened_out_reason:
        lines.append(f"Screened out: {f.screened_out_reason}")
    for group in ("relevance", "severity", "urgency"):
        fs = [x for x in f.factors if x.group == group]
        if not fs:
            continue
        lines.append(GROUP_TITLES[group] + ":")
        for x in fs:
            flag = "" if x.available else " [input missing, neutral value used]"
            ind = " [indicative]" if x.indicative else ""
            w = "" if group == "relevance" else f" (w={x.weight:.2f})"
            lines.append(f"- {x.name} = {x.value:.2f}{w}{ind}{flag}: {x.reason}")
    if f.deadline:
        lines.append(f"Deadline for comments/agreement: {f.deadline}.")
    if f.missing_inputs:
        lines.append("Missing inputs: " + ", ".join(f.missing_inputs) + ".")
    if f.indicative:
        lines.append("Calculated values are indicative; assumptions are listed with the evidence.")
    return "\n".join(lines)


def summarize_subject(s: ScoredSubject, cfg: dict) -> str:
    label = cfg.get("priority_labels", {}).get(s.priority, s.priority)
    if s.status == "withdrawn":
        return f"{s.subject_label}: withdrawn or suppressed; no action, listed for the record."
    if s.status == "screened_out" or not s.findings:
        reason = s.findings[0].screened_out_reason if s.findings else "no Finnish allocation touched"
        return f"{s.subject_label}: screened out ({reason})."
    top = s.findings[0]
    return (f"{s.subject_label}: score {s.score} ({s.priority}, {label}); {s.breadth} Finnish target(s); "
            f"top finding against {top.target_label}; confidence {s.confidence:.0%}"
            + (f"; deadline {s.deadline}" if s.deadline else "") + ".")


def evidence_lines(f: Finding) -> list[str]:
    out = []
    seen = set()
    for x in f.factors:
        for e in x.evidence:
            key = (e.kind, e.source, e.excerpt)
            if key in seen:
                continue
            seen.add(key)
            out.append(f"[{e.kind}] {e.source}: {e.excerpt}")
    return out
