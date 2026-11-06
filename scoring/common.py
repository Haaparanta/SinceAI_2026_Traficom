"""Shared arithmetic: interval overlap, dB helpers, binning, score combination, confidence."""
from __future__ import annotations

import math
from typing import Iterable, Optional, Sequence

from .models import Factor


def clamp(x: float, lo: float = 0.0, hi: float = 1.0) -> float:
    return max(lo, min(hi, x))


def overlap_mhz(a_min: float, a_max: float, b_min: float, b_max: float) -> float:
    """Width of the intersection of two frequency intervals, 0 when disjoint."""
    return max(0.0, min(a_max, b_max) - max(a_min, b_min))


def gap_mhz(a_min: float, a_max: float, b_min: float, b_max: float) -> float:
    """Distance between two disjoint intervals (0 when they touch or overlap)."""
    if overlap_mhz(a_min, a_max, b_min, b_max) > 0:
        return 0.0
    return max(0.0, max(a_min, b_min) - min(a_max, b_max))


def db(x: float) -> float:
    return 10.0 * math.log10(x)


def undb(x_db: float) -> float:
    return 10.0 ** (x_db / 10.0)


def bin_lookup(value: float, bins: Sequence[Sequence]) -> float:
    """bins = [[upper_bound_or_None, result], ...] in ascending order of upper bound.

    Returns the result of the first bin whose upper bound is >= value; None bound = catch-all.
    """
    for bound, result in bins:
        if bound is None or value <= bound:
            return float(result)
    return float(bins[-1][1])


def ramp(value: float, zero_at: float, full_at: float) -> float:
    """Linear 0..1 ramp between two thresholds (works in either direction)."""
    if full_at == zero_at:
        return 1.0 if value >= full_at else 0.0
    return clamp((value - zero_at) / (full_at - zero_at))


def weighted_mean(factors: Iterable[Factor]) -> float:
    fs = list(factors)
    total = sum(f.weight for f in fs)
    if total <= 0:
        return 0.0
    return sum(f.weight * f.value for f in fs) / total


def product(factors: Iterable[Factor]) -> float:
    p = 1.0
    for f in factors:
        p *= f.value
    return p


def combine_score(relevance: float, severity: float, urgency: float, cfg: dict) -> int:
    """score = 100 * relevance * (w_s * severity + w_u * urgency)."""
    ws = float(cfg["score"]["severity_weight"])
    wu = float(cfg["score"]["urgency_weight"])
    raw = 100.0 * clamp(relevance) * (ws * clamp(severity) + wu * clamp(urgency))
    return int(round(clamp(raw, 0.0, 100.0)))


def priority_from_score(score: int, cfg: dict) -> str:
    bands = cfg["priority_bands"]
    if score >= bands["A"]:
        return "A"
    if score >= bands["B"]:
        return "B"
    if score >= bands["C"]:
        return "C"
    return "D"


def confidence_from_factors(factors: Iterable[Factor]) -> float:
    """Share of factor weight that rested on actual data (not neutral defaults)."""
    fs = list(factors)
    total = sum(f.weight for f in fs)
    if total <= 0:
        return 0.0
    return sum(f.weight for f in fs if f.available) / total


def missing_inputs(factors: Iterable[Factor]) -> list[str]:
    return [f.name for f in factors if not f.available]


def fmt(x: Optional[float], nd: int = 1, unit: str = "") -> str:
    if x is None:
        return "unknown"
    return f"{x:.{nd}f}{unit}"
