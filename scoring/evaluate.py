"""Accuracy evaluation against expert labels (criterion D) and weight ablation.

labels: {subject_id: true/false} or {subject_id: "A"|"B"|"C"|"D"}; A/B count as relevant.
A subject missing from the labels is ignored (not assumed irrelevant).
"""
from __future__ import annotations

from typing import Callable, Optional

from .models import ScoredSubject

RELEVANT_PRIORITIES = {"A", "B"}


def _is_relevant(label) -> bool:
    if isinstance(label, bool):
        return label
    if isinstance(label, (int, float)):
        return label >= 1
    return str(label).strip().upper() in RELEVANT_PRIORITIES or str(label).strip().lower() in ("true", "yes", "relevant", "1")


def confusion(scored: list[ScoredSubject], labels: dict, threshold: int) -> dict:
    tp = fp = fn = tn = 0
    fps, fns = [], []
    for s in scored:
        if s.subject_id not in labels:
            continue
        rel = _is_relevant(labels[s.subject_id])
        pred = s.score >= threshold
        if pred and rel:
            tp += 1
        elif pred and not rel:
            fp += 1
            fps.append((s.subject_id, s.score))
        elif not pred and rel:
            fn += 1
            fns.append((s.subject_id, s.score))
        else:
            tn += 1
    precision = tp / (tp + fp) if tp + fp else 0.0
    recall = tp / (tp + fn) if tp + fn else 0.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0
    return {"threshold": threshold, "tp": tp, "fp": fp, "fn": fn, "tn": tn, "precision": round(precision, 3), "recall": round(recall, 3), "f1": round(f1, 3),
            "false_positives": fps, "false_negatives": fns}


def threshold_sweep(scored: list[ScoredSubject], labels: dict, step: int = 5) -> dict:
    rows = [confusion(scored, labels, t) for t in range(0, 101, step)]
    best = max(rows, key=lambda r: (r["f1"], r["recall"]))
    return {"labelled": sum(1 for s in scored if s.subject_id in labels), "sweep": [{k: v for k, v in r.items() if k not in ("false_positives", "false_negatives")} for r in rows], "best": best}


def ranking_quality(scored: list[ScoredSubject], labels: dict) -> dict:
    """Precision at k and average precision over the ranked list (relevant = A/B or true)."""
    ranked = [s for s in sorted(scored, key=lambda s: -s.score) if s.subject_id in labels]
    rel_total = sum(1 for s in ranked if _is_relevant(labels[s.subject_id]))
    hits, ap, p_at = 0, 0.0, {}
    for i, s in enumerate(ranked, start=1):
        if _is_relevant(labels[s.subject_id]):
            hits += 1
            ap += hits / i
        if i in (5, 10, 20, 50):
            p_at[f"p@{i}"] = round(hits / i, 3)
    return {"relevant": rel_total, "ranked": len(ranked), "average_precision": round(ap / rel_total, 3) if rel_total else None, **p_at}


def priority_agreement(scored: list[ScoredSubject], labels: dict) -> Optional[dict]:
    """When labels are A-D priorities: exact and within-one-band agreement."""
    pairs = [(s.priority, str(labels[s.subject_id]).strip().upper()) for s in scored if s.subject_id in labels and str(labels[s.subject_id]).strip().upper() in "ABCD"]
    if not pairs:
        return None
    order = "ABCD"
    exact = sum(1 for p, l in pairs if p == l)
    near = sum(1 for p, l in pairs if abs(order.index(p) - order.index(l)) <= 1)
    return {"n": len(pairs), "exact": round(exact / len(pairs), 3), "within_one_band": round(near / len(pairs), 3)}


def ablation(rescore: Callable[[dict], list[ScoredSubject]], labels: dict, cfg: dict, side: str) -> list[dict]:
    """Zero each severity/urgency weight in turn and report the best F1 (what each factor buys)."""
    base = threshold_sweep(rescore({}), labels)["best"]["f1"]
    out = [{"factor": "(all)", "best_f1": base, "delta": 0.0}]
    for grp in ("severity_weights", "urgency_weights"):
        for name in cfg[side][grp]:
            override = {side: {grp: {name: 0.0}}}
            f1 = threshold_sweep(rescore(override), labels)["best"]["f1"]
            out.append({"factor": name, "best_f1": f1, "delta": round(f1 - base, 3)})
    return out
