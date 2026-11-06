"""Step B4 of pm_pack/08: concern level and ordering.

Two layers, both deterministic:

1. **Concern level** from an explicit rule table (first match wins) [HYPOTHESIS until Q1; pfd refines it in C1]:

   | Rule | Concern |
   |------|---------|
   | Bureau lists Finland as affected (provn) | high |
   | Uplink from an earth station inside Finland | high |
   | Special-interest station in the band | medium (at least) |
   | Uplink from an earth station within the near-border distance | medium |
   | Downlink over a Finnish primary terrestrial or passive row, visible or low elevation | medium |
   | Downlink over a secondary terrestrial row | low |
   | Downlink over Finnish satellite downlink rows only (coordination) | low |
   | Part of the group has no Finnish row, or geography unknown | review |
   | Anything else | none |

2. **Score** for ordering inside a level, the scoring package's formula and weights
   (scoring/weights.json, scoring/DESIGN.md): score = 100 x relevance x (0.65 severity + 0.35 urgency).
   Severity's pfd factor is "not evaluated" (neutral 0.5) until C1. Every factor is kept for the trace.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from radar.config import ROOT
from radar.models import FinnishSubBand
from radar.pipeline.relevance import GroupRelevance, classify

CONCERN_ORDER = {"high": 4, "medium": 3, "review": 2, "low": 1, "none": 0}


@lru_cache(maxsize=1)
def weights() -> dict:
    return json.loads((ROOT / "scoring" / "weights.json").read_text(encoding="utf-8"))


def sensitivity(band: FinnishSubBand) -> tuple[float, str]:
    """Scoring package keyword rules over Services_in_Finland and Sub_band_usage; first rule wins."""
    cfg = weights()["finnish_sensitivity"]
    svc, use = band.services_in_finland.upper(), band.sub_band_usage.upper()
    for rule in cfg["rules"]:
        if any(k.upper() in svc for k in rule.get("service_any", [])) or any(k.upper() in use for k in rule.get("usage_any", [])):
            return rule["tier"], rule["label"]
    primary = classify(band.services_in_finland).primary
    return (cfg["default_primary"], "default primary") if primary else (cfg["default_secondary"], "default secondary")


def section_key(special_section: str | None) -> str:
    if not special_section:
        return "unknown"
    if special_section.startswith("Part "):
        return {"Part I-S": "PART-I-S", "Part II-S": "PART-II-S", "Part III-S": "PART-III-S"}[special_section]
    return special_section.split(" ")[0]


@dataclass
class GroupScore:
    group_id: str
    concern: str
    rule: str
    score: float
    factors: dict = field(default_factory=dict)


def geography_factor(r: GroupRelevance, geo_detail: dict | None) -> tuple[float, str]:
    w = weights()["space"]["geo"]
    g = r.geo_relevance
    if g == "visible":
        return 1.0, "visible"
    if g == "low_elevation":
        el = (geo_detail or {}).get("max_elevation_deg")
        if el is not None:
            v = max(0.0, min(1.0, (el - w["gso_elev_zero_deg"]) / (w["gso_elev_full_deg"] - w["gso_elev_zero_deg"])))
            return round(v, 3), f"low elevation, ramp {el:.1f} deg"
        return 0.5, "low elevation"
    if g == "near_border":
        d = ((geo_detail or {}).get("nearest") or {}).get("distance_km")
        for limit, val in w["earth_station_distance_bins_km"]:
            if limit is None or (d is not None and d <= limit):
                return val, f"earth station {d} km"
    if g == "unknown":
        return w["ngso_unknown_orbit"], "geography unknown"
    return 0.0, g


def concern_rule(r: GroupRelevance, classes: dict[int, object]) -> tuple[str, str]:
    if not r.candidate:
        return "none", "not a candidate after frequency and geography screening"
    if r.finland_named_provisions:
        return "high", f"the Bureau lists Finland as affected ({', '.join(r.finland_named_provisions)})"
    if "uplink_near_finland" in r.paths and "inside Finland" in r.geo_note:
        return "high", "uplink from an earth station inside Finland"
    if r.matched_station_numbers:
        return "medium", "special-interest station in the band"
    if "uplink_near_finland" in r.paths:
        return "medium", "uplink from an earth station near Finland"
    if r.direction == "space_to_earth" and r.geo_relevance in ("visible", "low_elevation"):
        if r.primary_terrestrial:
            return "medium", "downlink over a Finnish primary terrestrial allocation"
        if any(classes[i].primary for i in r.paths.get("passive_service", [])):
            return "medium", "downlink over a Finnish passive (radio astronomy or EESS) allocation"
        if "pfd_terrestrial" in r.paths or "passive_service" in r.paths:
            return "low", "downlink over a secondary Finnish terrestrial or passive allocation"
        if "space_cofrequency" in r.paths and "uncovered" not in r.paths:
            return "low", "co-frequency with Finnish satellite downlink use (coordination review)"
    if "uncovered" in r.paths:
        return "review", "part of the band has no row in the Finnish table"
    if r.geo_relevance == "unknown":
        return "review", "geography unknown"
    return "low", "candidate with no stronger rule"


def score_group(r: GroupRelevance, *, bands: dict[int, FinnishSubBand], classes: dict, section: str | None,
                action: str | None, geo_detail: dict | None) -> GroupScore:
    w = weights()
    sw, uw = w["space"]["severity_weights"], w["space"]["urgency_weights"]
    concern, rule = concern_rule(r, classes)
    geo_v, geo_why = geography_factor(r, geo_detail)
    relevance = (1.0 if r.candidate else 0.0) * geo_v if not r.finland_named_provisions else 1.0

    matched = [bands[i] for i in r.matched_subband_ids]
    sens = max((sensitivity(b) for b in matched), default=(w["finnish_sensitivity"]["default_none"], "no Finnish row"))
    status = w["space"]["status"]["primary"] if any(classes[i].primary for i in r.matched_subband_ids) else (
        w["space"]["status"]["secondary"] if matched else w["space"]["status"]["unallocated"])
    width = max(r.freq_max_hz - r.freq_min_hz, 1)
    bandwidth = math.sqrt(min(1.0, r.overlap_hz / width)) if r.overlap_hz else 0.1
    severity = (sw["pfd_margin"] * 0.5 + sw["finnish_sensitivity"] * sens[0] + sw["finnish_status"] * status
                + sw["bandwidth"] * bandwidth)

    stage = w["space"]["stage"].get(section_key(section), w["space"]["stage"]["unknown"])
    deadline = w["space"]["deadline_no_window"] if section_key(section) not in ("CR/C", "API/A") else 0.6
    listed = 1.0 if r.finland_named_provisions else 0.6
    novelty = w["space"]["novelty"].get(action or "unknown", w["space"]["novelty"]["unknown"])
    urgency = uw["stage"] * stage + uw["deadline"] * deadline + uw["finland_listed"] * listed + uw["novelty"] * novelty

    score = round(100 * relevance * (w["score"]["severity_weight"] * severity + w["score"]["urgency_weight"] * urgency), 2)
    return GroupScore(r.group_id, concern, rule, score, {
        "relevance": round(relevance, 3), "geography": [geo_v, geo_why],
        "severity": round(severity, 3), "pfd_margin": [0.5, "not evaluated until step C1"],
        "finnish_sensitivity": [sens[0], sens[1]], "finnish_status": status, "bandwidth": round(bandwidth, 3),
        "urgency": round(urgency, 3), "stage": [stage, section_key(section)], "deadline": deadline,
        "finland_listed": listed, "novelty": [novelty, action or "unknown"],
    })


def better(a: GroupScore, b: GroupScore | None) -> bool:
    return b is None or (CONCERN_ORDER[a.concern], a.score) > (CONCERN_ORDER[b.concern], b.score)
