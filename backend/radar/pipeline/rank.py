"""Step B4 of pm_pack/08: concern level and ordering.

Two layers, both deterministic:

1. **Concern level** from an explicit rule table (first match wins) [HYPOTHESIS until Q1; pfd refines it in C1]:

   | Rule | Concern |
   |------|---------|
   | Bureau lists Finland as affected (provn) | high |
   | Bureau's plan examination finds a Finnish AP30/30A/30B entry affected | high |
   | Co-frequency with a Finnish plan entry inside the Annex orbital arc (pipeline.plans) | medium |
   | The filing names Finland in the group's service area (srv_area.ctry = FIN) | medium |
   | Uplink from an earth station inside Finland | high |
   | Uplink from an earth station within the near-border distance | medium |
   | Uplink from an earth station within the near-border distance of a special-interest station | medium |
   | Downlink over a Finnish primary terrestrial or passive row, visible or low elevation | medium |
   | Downlink over a secondary terrestrial row | low |
   | Downlink over Finnish satellite downlink rows only (coordination) | low |
   | Part of the group has no Finnish row, or geography unknown | review |
   | Anything else | none |

   After the pfd refinement, a candidate whose band holds a special-interest station it can reach is raised to at
   least medium (station_floor); high and review are never lowered.

2. **Score** for ordering inside a level, the scoring package's formula and weights
   (scoring/weights.json, scoring/DESIGN.md): score = 100 x relevance x (0.65 severity + 0.35 urgency).
   Severity's pfd factor comes from the worst-case pfd margin (C1); neutral 0.5 where pfd is not evaluated.
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
    if r.plan_bureau:
        b = max(r.plan_bureau, key=lambda x: (x.pfd_excess_db or -999, x.degradation_db or -999))
        return "high", f"the Bureau's {b.db} examination finds the Finnish plan entry {b.finnish_satellite} affected ({b.summary()})"
    if "uplink_near_finland" in r.paths and "inside Finland" in r.geo_note:
        return "high", "uplink from an earth station inside Finland"
    if r.plan_hits:
        return "medium", f"{r.plan_hits[0].text()}; the Annex pfd test was not run"
    if "service_area_finland" in r.paths:
        return "medium", "the filing names Finland in the service area of this group"
    if "uplink_near_station" in r.paths and "uplink_near_finland" not in r.paths:
        return "medium", "uplink from an earth station near a special-interest station"
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


def pfd_adjust(concern: str, rule: str, pfd) -> tuple[str, str]:
    """C1: the worst-case pfd refines the downlink rules; Bureau naming and earth stations are left as they are.

    exceeds the limit -> high with a steerable beam, review with a fixed beam of unknown pointing; within 15 dB -> medium; 15 dB or more below -> low (worst case already conservative);
    no Table 21-4 limit -> unchanged with a note; implausible filed input -> review.
    """
    if pfd is None or not rule.startswith("downlink over"):
        return concern, rule
    if pfd.status == "computed" and pfd.orbit != "GSO":
        return _ngso_adjust(concern, rule, pfd)
    if pfd.status == "computed":
        if pfd.margin_db < 0:
            if pfd.worst.get("steerable"):
                return "high", (f"{rule}; worst-case pfd exceeds the RR Article 21 limit by {-pfd.margin_db:.1f} dB with a "
                                f"steerable beam that can be pointed at Finland (indicative)")
            return "review", (f"{rule}; worst-case pfd would exceed the RR Article 21 limit by {-pfd.margin_db:.1f} dB only if "
                              f"the beam peak points at Finland; check the gain contours (indicative)")
        if pfd.margin_db < PFD_LOW_MARGIN_DB:
            return concern, f"{rule}; worst-case pfd {pfd.margin_db:.1f} dB below the RR Article 21 limit (indicative)"
        return "low", f"{rule}; worst-case pfd {pfd.margin_db:.1f} dB below the RR Article 21 limit (indicative)"
    if pfd.status == "no_limit":
        return concern, f"{rule}; no RR Article 21 pfd limit applies in this band"
    if pfd.status == "flagged_input":
        return "review", f"{rule}; filed power density implausible, pfd needs a reviewer"
    return concern, f"{rule}; pfd not computed ({pfd.notes[0] if pfd.notes else pfd.status})"


def station_floor(r: GroupRelevance, concern: str, rule: str) -> tuple[str, str]:
    """pm_pack/06: a special-interest station in the group's band is always at least medium. Applied after the
    downlink, uplink and pfd rules, so it never lowers high or review and never hides an exceeded pfd limit."""
    if not (r.candidate and r.matched_station_numbers):
        return concern, rule
    n = len(r.matched_station_numbers)
    what = f"special-interest station {r.matched_station_numbers[0]}" if n == 1 else f"{n} special-interest stations"
    if CONCERN_ORDER[concern] < CONCERN_ORDER["review"]:
        return "medium", f"{rule}; {what} in the band and in reach"
    return concern, f"{rule}; {what} in the band and in reach"


NGSO_OVERHEAD_DEG = 60.0   # [HYPOTHESIS, Q2] high over Finland: off-nadir angle under about 30 deg for a low orbit


def _ngso_adjust(concern: str, rule: str, pfd) -> tuple[str, str]:
    """Non-GSO [HYPOTHESIS, Q2]. The worst case puts the beam peak on Finland at every elevation, but a constellation
    cuts its power at low angles with a pfd mask that the IFIC does not carry. So a notice is high only when the pfd
    exceeds the limit with the satellite high over Finland (NGSO_OVERHEAD_DEG or more, where a beam near nadir does
    reach Finland); an exceedance only lower down is review (the operator's mask decides). A pass computed with the
    lower bound of X (footnote 13) is not conclusive and lowers nothing."""
    w = pfd.worst
    el = w.get("top_elevation_deg")
    tops = w.get("tops") or ([(el, w.get("top_margin_db"))] if el is not None else [])
    over = [(e, m) for e, m in tops if e is not None and m is not None and e >= NGSO_OVERHEAD_DEG and m < 0]
    if pfd.margin_db < 0:
        if over:
            e, m = min(over, key=lambda t: t[1])
            return "high", (f"{rule}; worst-case pfd of one satellite exceeds the RR Article 21 limit by {-m:.1f} dB with "
                            f"the satellite high over Finland ({e:g} deg elevation) (indicative)")
        return "review", (f"{rule}; worst-case pfd of one satellite would exceed the RR Article 21 limit by {-pfd.margin_db:.1f} dB "
                          f"at {w['elevation_deg']:g} deg elevation with the beam peak on Finland (seen up to {el:g} deg); "
                          f"the operator's pfd mask decides (indicative)")
    if w.get("x_lower_bound") or w.get("y_assumed"):
        which = "the lower bound of X (footnote 13, Nv not filed)" if w.get("x_lower_bound") else "Y = 0 (footnote 22, not filed)"
        return concern, (f"{rule}; worst-case pfd {pfd.margin_db:.1f} dB below the RR Article 21 limit computed with "
                         f"{which}: not conclusive (indicative)")
    if pfd.margin_db < PFD_LOW_MARGIN_DB:
        return concern, f"{rule}; worst-case pfd of one satellite {pfd.margin_db:.1f} dB below the RR Article 21 limit (indicative)"
    return "low", f"{rule}; worst-case pfd of one satellite {pfd.margin_db:.1f} dB below the RR Article 21 limit (indicative)"


PFD_LOW_MARGIN_DB = 15.0   # [HYPOTHESIS] scoring package bin edge; partner question Q2


def score_group(r: GroupRelevance, *, bands: dict[int, FinnishSubBand], classes: dict, section: str | None,
                action: str | None, geo_detail: dict | None, pfd=None) -> GroupScore:
    from radar.calc.pfd import margin_factor

    w = weights()
    sw, uw = w["space"]["severity_weights"], w["space"]["urgency_weights"]
    concern, rule = station_floor(r, *pfd_adjust(*concern_rule(r, classes), pfd))
    pfd_v, pfd_why = margin_factor(pfd.margin_db if pfd is not None and pfd.status == "computed" else None, w)
    geo_v, geo_why = geography_factor(r, geo_detail)
    relevance = (1.0 if r.candidate else 0.0) * geo_v if not (r.finland_named_provisions or r.plan_bureau or r.plan_hits) else 1.0

    matched = [bands[i] for i in r.matched_subband_ids]
    sens = max((sensitivity(b) for b in matched), default=(w["finnish_sensitivity"]["default_none"], "no Finnish row"))
    status = w["space"]["status"]["primary"] if any(classes[i].primary for i in r.matched_subband_ids) else (
        w["space"]["status"]["secondary"] if matched else w["space"]["status"]["unallocated"])
    width = max(r.freq_max_hz - r.freq_min_hz, 1)
    bandwidth = math.sqrt(min(1.0, r.overlap_hz / width)) if r.overlap_hz else 0.1
    severity = (sw["pfd_margin"] * pfd_v + sw["finnish_sensitivity"] * sens[0] + sw["finnish_status"] * status
                + sw["bandwidth"] * bandwidth)

    stage = w["space"]["stage"].get(section_key(section), w["space"]["stage"]["unknown"])
    deadline = w["space"]["deadline_no_window"] if section_key(section) not in ("CR/C", "API/A") else 0.6
    listed = 1.0 if r.finland_named_provisions or r.plan_bureau else 0.6
    novelty = w["space"]["novelty"].get(action or "unknown", w["space"]["novelty"]["unknown"])
    urgency = uw["stage"] * stage + uw["deadline"] * deadline + uw["finland_listed"] * listed + uw["novelty"] * novelty

    score = round(100 * relevance * (w["score"]["severity_weight"] * severity + w["score"]["urgency_weight"] * urgency), 2)
    return GroupScore(r.group_id, concern, rule, score, {
        "relevance": round(relevance, 3), "geography": [geo_v, geo_why],
        "severity": round(severity, 3), "pfd_margin": [pfd_v, pfd_why],
        "finnish_sensitivity": [sens[0], sens[1]], "finnish_status": status, "bandwidth": round(bandwidth, 3),
        "urgency": round(urgency, 3), "stage": [stage, section_key(section)], "deadline": deadline,
        "finland_listed": listed, "novelty": [novelty, action or "unknown"],
    })


def better(a: GroupScore, b: GroupScore | None) -> bool:
    return b is None or (CONCERN_ORDER[a.concern], a.score) > (CONCERN_ORDER[b.concern], b.score)
