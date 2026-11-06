"""Space-side scoring: satellite-network frequency groups against Finnish spectrum use.

score(group, unit) = 100 * relevance * (0.65 * severity + 0.35 * urgency)
  relevance = freq_overlap * geography * direction        (any zero screens the pair out)
  severity  = weighted mean of pfd_margin, finnish_sensitivity, finnish_status, bandwidth
  urgency   = weighted mean of stage, deadline, finland_listed, novelty
Weights and thresholds live in weights.json; every factor returns its evidence.
"""
from __future__ import annotations

import json
import os
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from .common import (bin_lookup, clamp, combine_score, confidence_from_factors, fmt, missing_inputs,
                     overlap_mhz, priority_from_score, product, ramp, weighted_mean)
from .explain import explain_finding, summarize_subject
from .finnish_table import AllocationUnit, FinnishTable
from .geometry import distance_to_finland_km, gso_visibility_from_finland, ngso_coverage
from .models import Evidence, Factor, Finding, FinnishSpaceNetwork, ScoredSubject, SpaceGroup
from .pfd import assess_gso, assess_ngso, power_density_dbw_hz

REFERENCE_DIR = os.path.join(os.path.dirname(__file__), "reference")


def _load_admin_codes() -> dict:
    with open(os.path.join(REFERENCE_DIR, "itu_admin_codes.json"), encoding="utf-8") as fh:
        return json.load(fh)


@dataclass
class SpaceContext:
    table: FinnishTable
    cfg: dict
    finnish_networks: list[FinnishSpaceNetwork] = field(default_factory=list)
    as_of: Optional[date] = None          # date for deadline arithmetic; None = the IFIC date (window fully open)
    admin: dict = field(default_factory=_load_admin_codes)


# ----------------------------------------------------------------------------- helpers

SECTION_ALIASES = {
    "PART I-S": "PART-I-S", "PART-I": "PART-I-S", "PART I": "PART-I-S", "I-S": "PART-I-S",
    "PART II-S": "PART-II-S", "PART-II": "PART-II-S", "PART II": "PART-II-S", "II-S": "PART-II-S",
    "PART III-S": "PART-III-S", "PART-III": "PART-III-S", "PART III": "PART-III-S", "III-S": "PART-III-S",
}


def normalise_section(section: Optional[str]) -> str:
    """'CR/C/1234' -> 'CR/C', 'API/A/12345' -> 'API/A', 'Part I-S' -> 'PART-I-S'."""
    if not section:
        return "unknown"
    s = section.strip().upper().replace("_", "/")
    if s in SECTION_ALIASES:
        return SECTION_ALIASES[s]
    parts = s.split("/")
    if parts[0] in ("API", "CR") and len(parts) >= 2:
        return f"{parts[0]}/{parts[1]}"
    if parts[0].startswith("AP30"):
        return "/".join(parts[:2]) if len(parts) >= 2 else parts[0]
    if parts[0].startswith("RES"):
        return parts[0]
    return s


def _service_area_value(group: SpaceGroup, ctx: SpaceContext) -> tuple[float, str, bool]:
    sa = ctx.cfg["space"]["geo"]["service_area"]
    areas = [a.upper() for a in group.srv_area]
    if not areas:
        return sa["not_stated"], "service area not stated in the filing", False
    if ctx.admin["finland"] in areas:
        return sa["finland"], "Finland (FIN) is in the service area", True
    if any(a in areas for a in ctx.admin["region_codes_covering_finland"]):
        return sa["region_covering_finland"], "a regional/global area code covering Finland is in the service area", True
    if any(a in areas for a in ctx.admin["neighbours"]):
        return sa["neighbour"], "a neighbouring administration is in the service area (spill-over)", True
    return sa["elsewhere"], f"service area lists {', '.join(group.srv_area[:5])} only; Finland reached by side lobes at most", True


# ----------------------------------------------------------------------------- relevance factors

def freq_factor(group: SpaceGroup, unit: AllocationUnit, overlap: float, gap: float, cfg: dict) -> Factor:
    c = cfg["space"]["freq"]
    ev = [Evidence("filing", group.source_ref or f"grp_id={group.grp_id}", f"{group.freq_min_mhz:g}-{group.freq_max_mhz:g} MHz, {group.emi_rcp}"),
          Evidence("finnish_table", unit.source_ref, unit.label)]
    if overlap > 0:
        filing_bw = group.freq_max_mhz - group.freq_min_mhz
        frac = min(1.0, overlap / filing_bw) if filing_bw > 0 else 1.0
        value = c["overlap_floor"] + (1.0 - c["overlap_floor"]) * frac
        reason = f"co-frequency: {overlap:g} MHz ({frac:.0%} of the filed {filing_bw:g} MHz) falls inside the Finnish sub-band {unit.f_min_mhz:g}-{unit.f_max_mhz:g} MHz"
    else:
        value = c["adjacent_relevance_passive"] if unit.is_passive else c["adjacent_relevance"]
        reason = f"adjacent band: {gap:g} MHz from the Finnish sub-band {unit.f_min_mhz:g}-{unit.f_max_mhz:g} MHz" + (" (passive service, unwanted emissions matter)" if unit.is_passive else "")
    return Factor("freq_overlap", "relevance", value, 1.0, True, reason, ev)


def geo_factor(group: SpaceGroup, ctx: SpaceContext) -> Factor:
    c = ctx.cfg["space"]["geo"]
    kind = group.orbit.kind if group.orbit.kind != "unknown" else {"G": "GSO", "N": "NGSO"}.get(group.ntc_type, "unknown")
    if group.ntc_type in ("S", "T", "R"):
        if group.earth_station_lat is not None and group.earth_station_lon is not None:
            d, nlat, nlon = distance_to_finland_km(group.earth_station_lat, group.earth_station_lon)
            value = bin_lookup(d, c["earth_station_distance_bins_km"])
            return Factor("geography", "relevance", value, 1.0, True,
                          f"earth station {d:.0f} km from Finnish territory",
                          [Evidence("geometry", "distance_to_finland_km", f"({group.earth_station_lat:.3f}, {group.earth_station_lon:.3f}) -> nearest Finnish point ({nlat:.3f}, {nlon:.3f}), {d:.0f} km")])
        ctry = [x.upper() for x in group.earth_station_ctry]
        if ctx.admin["finland"] in ctry:
            return Factor("geography", "relevance", 1.0, 1.0, True, "earth station located in Finland", [Evidence("filing", "e_stn.ctry", ",".join(ctry))])
        if any(x in ctx.admin["neighbours"] for x in ctry):
            return Factor("geography", "relevance", 0.6, 1.0, True, "earth station located in a neighbouring country", [Evidence("filing", "e_stn.ctry", ",".join(ctry))])
        return Factor("geography", "relevance", 0.1 if ctry else 0.4, 1.0, bool(ctry),
                      "earth station location " + (f"in {','.join(ctry)}, far from Finland" if ctry else "unknown"),
                      [Evidence("filing", "e_stn.ctry", ",".join(ctry) or "unknown")])

    area_value, area_reason, area_known = _service_area_value(group, ctx)
    area_ev = Evidence("filing", "srv_area.ctry", ", ".join(group.srv_area) if group.srv_area else "not stated")

    if kind == "GSO":
        if group.orbit.long_nom_deg is None:
            return Factor("geography", "relevance", 0.5 * area_value, 1.0, False, "GSO longitude unknown; " + area_reason, [area_ev])
        vis = gso_visibility_from_finland(group.orbit.long_nom_deg)
        best = vis["best"]
        r_vis = ramp(best["elevation_deg"], c["gso_elev_zero_deg"], c["gso_elev_full_deg"])
        ev = [Evidence("geometry", "gso_geometry", f"GSO at {group.orbit.long_nom_deg:+.2f} deg E: elevation {best['elevation_deg']:.1f} deg from {best['name']}, slant range {best['slant_range_km']:.0f} km; {vis['visible_points']}/{len(vis['points'])} reference points see it"), area_ev]
        if r_vis <= 0:
            return Factor("geography", "relevance", 0.0, 1.0, True, f"GSO at {group.orbit.long_nom_deg:+.1f} deg E is below the horizon everywhere in Finland", ev)
        return Factor("geography", "relevance", r_vis * area_value, 1.0, True,
                      f"GSO at {group.orbit.long_nom_deg:+.1f} deg E seen at {best['elevation_deg']:.1f} deg elevation from {best['name']} (visibility {r_vis:.2f}); {area_reason} (x{area_value:.2f})", ev)

    if kind == "NGSO":
        inc, alt = group.orbit.inclination_deg, group.orbit.altitude_km
        if inc is None or alt is None:
            return Factor("geography", "relevance", c["ngso_unknown_orbit"] * area_value, 1.0, False,
                          "NGSO orbit parameters missing; coverage of Finland assumed possible; " + area_reason, [area_ev])
        cov = ngso_coverage(inc, alt, c["ngso_min_elev_deg"])
        ev = [Evidence("geometry", "ngso_coverage", f"inclination {inc:g} deg, altitude {alt:g} km -> satellites visible up to latitude {cov['lat_limit_deg']:.1f} deg; Finland (59.8-70.1 N) covered {cov['finland_fraction']:.0%}"), area_ev]
        if cov["finland_fraction"] <= 0:
            return Factor("geography", "relevance", 0.0, 1.0, True, f"orbit (i={inc:g} deg, h={alt:g} km) never rises above the horizon in Finland", ev)
        return Factor("geography", "relevance", cov["finland_fraction"] * area_value, 1.0, True,
                      f"NGSO i={inc:g} deg, h={alt:g} km covers {cov['finland_fraction']:.0%} of Finland's latitude span; {area_reason} (x{area_value:.2f})", ev)

    return Factor("geography", "relevance", 0.5 * area_value, 1.0, False, "orbit type unknown; " + area_reason, [area_ev])


def direction_factor(group: SpaceGroup, unit: AllocationUnit, ctx: SpaceContext) -> Factor:
    d = ctx.cfg["space"]["direction"]
    ev = [Evidence("filing", "grp.emi_rcp", group.emi_rcp), Evidence("finnish_table", unit.source_ref, f"{unit.service} direction={unit.direction or 'n/a'}")]
    if group.emi_rcp == "E":
        c = d["E"]
        if unit.is_space_service:
            if unit.is_space_to_earth:
                return Factor("direction", "relevance", c["finnish_space_to_earth"], 1.0, True, "space-to-Earth emission into a Finnish space-to-Earth allocation (Finnish earth stations receive here)", ev)
            if unit.is_earth_to_space:
                return Factor("direction", "relevance", c["finnish_earth_to_space"], 1.0, True, "space-to-Earth emission vs a Finnish Earth-to-space allocation (Finnish stations transmit here; low exposure)", ev)
            return Factor("direction", "relevance", c["finnish_unknown"], 1.0, True, "space-to-Earth emission vs a Finnish space service without stated direction", ev)
        if unit.direction == "TX":
            return Factor("direction", "relevance", c["finnish_tx_only"], 1.0, True, "space-to-Earth emission vs a Finnish transmit-only sub-band (receiver sits in the paired sub-band)", ev)
        if not unit.allocated and not unit.usage:
            return Factor("direction", "relevance", c["finnish_unknown"], 1.0, False, "space-to-Earth emission; Finnish use in the band not stated", ev)
        return Factor("direction", "relevance", c["finnish_rx_terrestrial"], 1.0, True, "space-to-Earth emission into a band where Finnish terrestrial stations receive", ev)

    c = d["R"]
    candidates = [(c["base"], "uplink: the space station only receives; Finnish use is exposed only to the foreign earth stations")]
    for net in ctx.finnish_networks:
        if net.emi_rcp == "R" and overlap_mhz(group.freq_min_mhz, group.freq_max_mhz, net.freq_min_mhz, net.freq_max_mhz) > 0:
            candidates.append((c["finnish_space_network_in_band"], f"Finnish satellite network {net.sat_name} receives in this band (foreign uplink emissions can reach it)"))
            ev.append(Evidence("asset", net.source_ref or "finnish_networks", f"{net.sat_name} {net.freq_min_mhz:g}-{net.freq_max_mhz:g} MHz R"))
            break
    ctry = [x.upper() for x in group.earth_station_ctry]
    if unit.is_earth_to_space:
        # Finnish stations only transmit here; foreign earth stations cannot interfere with them.
        candidates.append((c["finnish_earth_to_space"], "Finnish Earth-to-space allocation shares the uplink band (Finnish stations transmit here; earth-station coordination may follow)"))
    elif ctx.admin["finland"] in ctry:
        candidates.append((c["earth_station_in_finland"], "associated earth stations located in Finland transmit in a band where Finnish stations receive"))
    elif any(x in ctx.admin["neighbours"] for x in ctry):
        candidates.append((c["earth_station_in_neighbour"], f"associated earth stations in a neighbouring country ({','.join(x for x in ctry if x in ctx.admin['neighbours'])}) transmit in a band where Finnish stations receive"))
    value, reason = max(candidates, key=lambda x: x[0])
    return Factor("direction", "relevance", value, 1.0, True, reason, ev)


# ----------------------------------------------------------------------------- severity factors

def pfd_factor(group: SpaceGroup, unit: AllocationUnit, ctx: SpaceContext) -> Factor:
    c = ctx.cfg["space"]["pfd"]
    w = ctx.cfg["space"]["severity_weights"]["pfd_margin"]
    if group.emi_rcp != "E":
        return Factor("pfd_margin", "severity", c["unknown_value"], w, False, "uplink group: pfd at the Earth's surface is not produced by the space station", [Evidence("filing", "grp.emi_rcp", "R")])
    pwr_ds, src = power_density_dbw_hz(group.pwr_ds_max_dbw_hz, group.pep_max_dbw, group.bandwidth_khz)
    if pwr_ds is None or group.gain_dbi is None:
        return Factor("pfd_margin", "severity", c["unknown_value"], w, False, "power density or beam gain missing; pfd not calculated", [Evidence("filing", "emiss.pwr_ds_max / s_beam.gain", f"{fmt(group.pwr_ds_max_dbw_hz)} dBW/Hz / {fmt(group.gain_dbi)} dBi")])
    bw_hz = group.bandwidth_khz * 1000.0 if group.bandwidth_khz else None
    kind = group.orbit.kind if group.orbit.kind != "unknown" else {"G": "GSO", "N": "NGSO"}.get(group.ntc_type, "unknown")
    f_lo, f_hi = max(group.freq_min_mhz, unit.f_min_mhz), min(group.freq_max_mhz, unit.f_max_mhz)
    if f_lo >= f_hi:
        f_lo, f_hi = group.freq_min_mhz, group.freq_max_mhz
    if kind == "GSO" and group.orbit.long_nom_deg is not None:
        a = assess_gso(pwr_ds, group.gain_dbi, group.orbit.long_nom_deg, f_lo, f_hi, bw_hz, ctx.cfg)
    elif kind == "NGSO" and group.orbit.altitude_km is not None:
        a = assess_ngso(pwr_ds, group.gain_dbi, group.orbit.altitude_km, f_lo, f_hi, bw_hz, ctx.cfg)
    else:
        return Factor("pfd_margin", "severity", c["unknown_value"], w, False, "orbit data missing; pfd not calculated", [])
    if a is None:
        return Factor("pfd_margin", "severity", 0.05, w, True, "satellite not visible from Finland; no pfd on Finnish territory", [])
    ev = [Evidence("calculation", "pfd.py pfd_at_ground", a.formula + f" at {a.point_name} (elevation {a.elev_deg:.1f} deg); power density from {src}")]
    for s in a.assumptions:
        ev.append(Evidence("calculation", "assumption", s))
    if a.limit_dbw_m2 is not None:
        ev.append(Evidence("regulation", f"RR Article 21 Table 21-4 row {a.limit_row_id}" + ("" if a.limit_verified else " (unverified transcription)"), f"limit {a.limit_dbw_m2:.1f} dB(W/m2) in {a.ref_bw_hz / 1000:g} kHz at {a.elev_deg:.1f} deg"))
        value = bin_lookup(a.margin_db, c["margin_bins_db"])
        verdict = "EXCEEDS the limit" if a.margin_db < 0 else "below the limit"
        reason = f"pfd {a.pfd_dbw_m2:.1f} dB(W/m2) vs limit {a.limit_dbw_m2:.1f} ({a.ref_bw_hz / 1000:g} kHz) at {a.point_name}: margin {a.margin_db:+.1f} dB, {verdict}"
    else:
        ref = c["no_limit_reference_dbw_m2_4khz"] + 10.0 * __import__("math").log10(a.ref_bw_hz / 4000.0)
        margin = ref - a.pfd_dbw_m2
        value = bin_lookup(margin, c["margin_bins_db"]) * 0.8
        reason = f"no Table 21-4 hard limit in this band; pfd {a.pfd_dbw_m2:.1f} dB(W/m2) ({a.ref_bw_hz / 1000:g} kHz) compared with an informative reference of {ref:.1f}: margin {margin:+.1f} dB"
        ev.append(Evidence("calculation", "reference level", f"{c['no_limit_reference_dbw_m2_4khz']} dB(W/m2/4 kHz) configured in weights.json"))
    if group.f_pfd_limit_commit:
        value *= c["commitment_multiplier"]
        reason += "; the filing commits to the pfd limit (A.17)"
        ev.append(Evidence("filing", "f_pfd_limit", "Y"))
    return Factor("pfd_margin", "severity", clamp(value), w, True, reason, ev, indicative=True)


def sensitivity_factor(unit: AllocationUnit, ctx: SpaceContext) -> Factor:
    tier, label = ctx.table.sensitivity(unit, ctx.cfg)
    w = ctx.cfg["space"]["severity_weights"]["finnish_sensitivity"]
    return Factor("finnish_sensitivity", "severity", tier, w, True, f"Finnish use '{unit.service or unit.usage}' / '{unit.usage}' rated {tier:.2f}: {label}",
                  [Evidence("finnish_table", unit.source_ref, unit.label)])


def status_factor(unit: AllocationUnit, ctx: SpaceContext) -> Factor:
    value, label = ctx.table.status_value(unit, ctx.cfg)
    w = ctx.cfg["space"]["severity_weights"]["finnish_status"]
    return Factor("finnish_status", "severity", value, w, True, f"Finnish allocation status: {label} (capitals = primary in the M4 table)",
                  [Evidence("finnish_table", unit.source_ref, unit.service or "(no service)")])


def bandwidth_factor(unit: AllocationUnit, overlap: float, ctx: SpaceContext) -> Factor:
    w = ctx.cfg["space"]["severity_weights"]["bandwidth"]
    if overlap <= 0:
        return Factor("bandwidth", "severity", 0.1, w, True, "adjacent band only; no co-frequency bandwidth", [])
    frac = min(1.0, overlap / unit.bandwidth_mhz) if unit.bandwidth_mhz > 0 else 1.0
    value = frac ** ctx.cfg["space"]["bandwidth"]["exponent"]
    return Factor("bandwidth", "severity", value, w, True, f"{overlap:g} MHz overlapped = {frac:.0%} of the Finnish sub-band",
                  [Evidence("calculation", "bandwidth", f"overlap {overlap:g} MHz / sub-band {unit.bandwidth_mhz:g} MHz")])


# ----------------------------------------------------------------------------- urgency factors

def stage_factor(group: SpaceGroup, section: str, ctx: SpaceContext) -> Factor:
    st = ctx.cfg["space"]["stage"]
    w = ctx.cfg["space"]["urgency_weights"]["stage"]
    known = section in st
    value = st.get(section, st["unknown"])
    notes = {"CR/C": "coordination request: silence within 4 months counts as agreement (No. 9.52C)",
             "API/A": "advance publication: comments under No. 9.3 within 4 months (only for networks not subject to coordination)",
             "PART-I-S": "notification published for recording in the MIFR",
             "PART-II-S": "already recorded in the MIFR", "PART-III-S": "unfavourable finding returned to the administration"}
    reason = f"special section {section}: " + notes.get(section, "see Preface to the BR IFIC for the procedure")
    if section.startswith("AP30"):
        reason = f"special section {section}: Plan modification under Appendices 30/30A/30B; Finnish Plan assignments may be affected"
    return Factor("stage", "urgency", value, w, known, reason, [Evidence("filing", "special section", group.special_section or "unknown")])


def deadline_factor(group: SpaceGroup, section: str, ctx: SpaceContext) -> tuple[Factor, Optional[str]]:
    c = ctx.cfg["space"]
    w = c["urgency_weights"]["deadline"]
    window = c["comment_window_days"].get(section)
    if window is None:
        return Factor("deadline", "urgency", c["deadline_no_window"], w, True, f"no comment window attached to {section}", []), None
    if group.ific_date is None:
        return Factor("deadline", "urgency", c["deadline_no_window"], w, False, "IFIC publication date unknown; deadline not computed", []), None
    deadline = group.ific_date + timedelta(days=window)
    as_of = ctx.as_of or group.ific_date
    remaining = (deadline - as_of).days
    value = bin_lookup(remaining, c["deadline_bins_days_remaining"])
    state = "expired" if remaining <= 0 else f"{remaining} days left"
    return Factor("deadline", "urgency", value, w, True, f"4-month window from IFIC {group.ific_no or ''} ({group.ific_date.isoformat()}) ends {deadline.isoformat()}: {state} as of {as_of.isoformat()}",
                  [Evidence("regulation", "RR Nos. 9.3 / 9.52 / AP30 4.1.5", f"{window} days from publication")]), deadline.isoformat()


def listed_factor(group: SpaceGroup, section: str, ctx: SpaceContext) -> Factor:
    c = ctx.cfg["space"]["finland_listed"]
    w = ctx.cfg["space"]["urgency_weights"]["finland_listed"]
    has_list = section.startswith("CR/") or section.startswith("AP30") or section.startswith("PART")
    adms = [a.upper() for a in group.affected_adms]
    ev = [Evidence("filing", "provn / tr_aff_ntw", ", ".join(group.affected_adms) if group.affected_adms else "no administrations listed")]
    if ctx.admin["finland"] in adms:
        return Factor("finland_listed", "urgency", c["listed"], w, True, "Finland is identified as an affected administration in the filing: a response is required", ev)
    if has_list:
        return Factor("finland_listed", "urgency", c["not_listed_with_overlap"], w, True, "Finland is not in the affected list although Finnish use overlaps: inclusion can be requested under No. 9.41 within the 4-month window", ev)
    return Factor("finland_listed", "urgency", c["no_list_for_section"], w, True, f"{section} carries no affected-administration list", ev)


def novelty_factor(group: SpaceGroup, ctx: SpaceContext) -> Factor:
    c = ctx.cfg["space"]["novelty"]
    w = ctx.cfg["space"]["urgency_weights"]["novelty"]
    code = (group.act_code or "").upper()
    if group.ntf_occurs and group.ntf_occurs.upper() == "R":
        code = "R"
    value = c.get(code, c["unknown"])
    text = {"A": "new entry", "M": "modification of an existing network", "R": "resubmission", "S": "suppression"}.get(code, "action code unknown")
    return Factor("novelty", "urgency", value, w, code in c, text, [Evidence("filing", "act_code / ntf_occurs", f"{group.act_code} / {group.ntf_occurs or ''}")])


# ----------------------------------------------------------------------------- assembly

def score_pair(group: SpaceGroup, unit: AllocationUnit, overlap: float, gap: float, ctx: SpaceContext, shared: dict) -> Finding:
    cfg = ctx.cfg
    rel = [freq_factor(group, unit, overlap, gap, cfg), shared["geo"], direction_factor(group, unit, ctx)]
    sev = [pfd_factor(group, unit, ctx), sensitivity_factor(unit, ctx), status_factor(unit, ctx), bandwidth_factor(unit, overlap, ctx)]
    urg = [shared["stage"], shared["deadline"], shared["listed"], shared["novelty"]]
    factors = rel + sev + urg
    relevance = product(rel)
    severity = weighted_mean(sev)
    urgency = weighted_mean(urg)
    score = combine_score(relevance, severity, urgency, cfg)
    screened = None
    if relevance <= 0:
        zero = next(f for f in rel if f.value <= 0)
        screened = f"{zero.name}: {zero.reason}"
        score = 0
    f = Finding(
        finding_id=f"{group.grp_id}:{unit.unit_id}", subject_id=group.grp_id, subject_label=group.label,
        target_id=unit.unit_id, target_label=unit.label, score=score, priority=priority_from_score(score, cfg),
        relevance=relevance, severity=severity, urgency=urgency, confidence=confidence_from_factors(factors),
        factors=factors, screened_out_reason=screened, indicative=any(x.indicative for x in factors),
        missing_inputs=missing_inputs(factors), deadline=shared["deadline_iso"])
    f.explanation = explain_finding(f, cfg)
    return f


def score_group(group: SpaceGroup, ctx: SpaceContext) -> ScoredSubject:
    cfg = ctx.cfg
    section = normalise_section(group.special_section)
    if (group.act_code or "").upper() == "S":
        return ScoredSubject(group.grp_id, group.label, 0, "D", 1.0, 0, [], status="withdrawn",
                             summary=f"{group.label}: suppression; no action, listed for the record.")
    guard = max(cfg["space"]["freq"]["adjacent_guard_min_mhz"], (group.freq_max_mhz - group.freq_min_mhz) * cfg["space"]["freq"]["adjacent_guard_pct"] / 100.0)
    targets = [(u, ov, 0.0) for u, ov in ctx.table.overlapping(group.freq_min_mhz, group.freq_max_mhz)]
    targets += [(u, 0.0, gp) for u, gp in ctx.table.adjacent(group.freq_min_mhz, group.freq_max_mhz, guard)]
    deadline_f, deadline_iso = deadline_factor(group, section, ctx)
    shared = {"geo": geo_factor(group, ctx), "stage": stage_factor(group, section, ctx), "deadline": deadline_f,
              "deadline_iso": deadline_iso, "listed": listed_factor(group, section, ctx), "novelty": novelty_factor(group, ctx)}
    findings = [score_pair(group, u, ov, gp, ctx, shared) for u, ov, gp in targets]
    findings.sort(key=lambda f: (f.screened_out_reason is not None, -f.score, -f.confidence))
    active = [f for f in findings if f.screened_out_reason is None]
    if not active:
        reason = findings[0].screened_out_reason if findings else "no Finnish allocation within the band or its guard band"
        s = ScoredSubject(group.grp_id, group.label, 0, "D", 1.0 if not findings else findings[0].confidence, 0, findings, status="screened_out")
        s.summary = f"{group.label}: screened out ({reason})."
        return s
    top = active[0]
    breadth = len({f.target_label.split(" | ")[1] for f in active if f.score >= cfg["priority_bands"]["C"]})
    s = ScoredSubject(group.grp_id, group.label, top.score, top.priority, top.confidence, breadth, findings, deadline=deadline_iso)
    s.summary = summarize_subject(s, cfg)
    return s


def rank_groups(groups: list[SpaceGroup], ctx: SpaceContext) -> list[ScoredSubject]:
    scored = [score_group(g, ctx) for g in groups]
    scored.sort(key=lambda s: (-s.score, -s.breadth, -s.confidence, s.subject_id))
    return scored


def aggregate_by_notice(scored: list[ScoredSubject], groups: list[SpaceGroup]) -> list[dict]:
    """Roll group-level results up to the satellite network (ntc_id)."""
    by_grp = {g.grp_id: g for g in groups}
    notices: dict[str, dict] = {}
    for s in scored:
        g = by_grp.get(s.subject_id)
        key = g.ntc_id if g else s.subject_id
        n = notices.setdefault(key, {"ntc_id": key, "sat_name": g.sat_name if g else "", "adm": g.adm if g else "",
                                     "special_section": g.special_section if g else "", "score": 0, "priority": "D",
                                     "groups_scored": 0, "groups_active": 0, "top_group": None, "deadline": s.deadline})
        n["groups_scored"] += 1
        if s.status == "active":
            n["groups_active"] += 1
        if s.score > n["score"] or n["top_group"] is None:
            n["score"], n["priority"], n["top_group"] = s.score, s.priority, s.subject_id
    out = list(notices.values())
    out.sort(key=lambda n: (-n["score"], -n["groups_active"], n["ntc_id"]))
    return out
