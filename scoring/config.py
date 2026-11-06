"""Load scoring weights and thresholds (weights.json) with optional overrides."""
from __future__ import annotations

import copy
import json
import os
from typing import Any, Optional

DEFAULT_WEIGHTS = os.path.join(os.path.dirname(__file__), "weights.json")


def deep_merge(base: dict, override: dict) -> dict:
    out = copy.deepcopy(base)
    for k, v in override.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = deep_merge(out[k], v)
        else:
            out[k] = copy.deepcopy(v)
    return out


def load_config(path: Optional[str] = None, overrides: Optional[dict[str, Any]] = None) -> dict:
    with open(path or DEFAULT_WEIGHTS, encoding="utf-8") as fh:
        cfg = json.load(fh)
    if overrides:
        cfg = deep_merge(cfg, overrides)
    _validate(cfg)
    return cfg


def _validate(cfg: dict) -> None:
    s = cfg["score"]
    total = s["severity_weight"] + s["urgency_weight"]
    if abs(total - 1.0) > 1e-6:
        raise ValueError(f"score.severity_weight + score.urgency_weight must be 1.0, got {total}")
    for side in ("space", "terrestrial"):
        for grp in ("severity_weights", "urgency_weights"):
            w = cfg[side][grp]
            if any(v < 0 for v in w.values()):
                raise ValueError(f"{side}.{grp} has a negative weight")
    bands = cfg["priority_bands"]
    if not (bands["A"] > bands["B"] > bands["C"] >= 0):
        raise ValueError("priority_bands must satisfy A > B > C >= 0")
