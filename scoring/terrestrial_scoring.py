"""Terrestrial side quest: land-mobile notices from neighbouring administrations.

score(notice, target) = 100 * relevance * (0.65 * severity + 0.35 * urgency)
  relevance = freq_overlap * geography * action
  severity  = field_strength_margin (T/R 25-08 trigger), interference_potential, finnish_sensitivity, protected_station
  urgency   = novelty (IFIC diff), provision (9.21 agreement vs 11.2 notification), framework

Also provides the IFIC-to-IFIC diff (new / modified / withdrawn) and simple trend
and anomaly statistics per administration, band and station class.
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional

from .common import bin_lookup, clamp, combine_score, confidence_from_factors, fmt, missing_inputs, overlap_mhz, gap_mhz, priority_from_score, product, weighted_mean
from .explain import explain_finding, summarize_subject
from .finnish_table import AllocationUnit, FinnishTable
from .geometry import Region, angular_difference_deg, haversine_km, initial_bearing_deg
from .models import Evidence, Factor, Finding, ProtectedStation, ScoredSubject, TerrestrialNotice
from .propagation import FreeSpaceModel, get_model, tr2508_threshold


@dataclass
class TerrestrialContext:
    table: FinnishTable
    cfg: dict
    region: Region = field(default_factory=Region.load)
    protected: list[ProtectedStation] = field(default_factory=list)
    model: object = field(default_factory=FreeSpaceModel)
    as_of: Optional[date] = None


# ----------------------------------------------------------------------------- per-notice factors

def geo_factor(n: TerrestrialNotice, ctx: TerrestrialContext) -> tuple[Factor, dict]:
    c = ctx.cfg["terrestrial"]["geo"]
    d, nlat, nlon = ctx.region.distance_to_country_km("FIN", n.lat, n.lon)
    path = ctx.region.path_profile(n.lat, n.lon, nlat, nlon) if d > 0 else {"path_type": "land", "sea_fraction": 0.0, "land_fraction": 1.0}
    d_eff = d * (1.0 - path["sea_fraction"] * (1.0 - c["sea_path_distance_factor"]))
    base = bin_lookup(d_eff, c["distance_bins_km"])
    bearing = initial_bearing_deg(n.lat, n.lon, nlat, nlon) if d > 0 else 0.0
    p = c["pointing"]
    if n.ant_dir.upper() == "D" and n.azm_max_deg is not None and d > 0:
        off = angular_difference_deg(n.azm_max_deg, bearing)
        half = (n.beamwidth_deg or 0.0) / 2.0
        if off <= max(half, p["sideways_deg"]):
            point_v, point_t = p["toward"], f"antenna azimuth {n.azm_max_deg:g} deg points towards Finland (bearing {bearing:.0f} deg, off-axis {off:.0f} deg)"
        elif off <= p["away_deg"]:
            point_v, point_t = p["sideways"], f"antenna azimuth {n.azm_max_deg:g} deg is sideways to Finland (off-axis {off:.0f} deg)"
        else:
            point_v, point_t = p["away"], f"antenna azimuth {n.azm_max_deg:g} deg points away from Finland (off-axis {off:.0f} deg)"
    else:
        point_v, point_t = p["nondirectional"], "non-directional antenna or azimuth not given"
    value = base * point_v
    ev = [Evidence("geometry", "distance_to_finland_km", f"site ({n.lat:.4f}, {n.lon:.4f}) -> nearest Finnish territory ({nlat:.4f}, {nlon:.4f}): {d:.1f} km, path {path['path_type']} (sea {path['sea_fraction']:.0%})"),
          Evidence("filing", "t_ant_dir / t_azm_max_e / t_bmwdth", f"{n.ant_dir} / {fmt(n.azm_max_deg, 0)} / {fmt(n.beamwidth_deg, 0)}")]
    reason = f"{d:.0f} km from Finnish territory over a {path['path_type']} path (effective {d_eff:.0f} km -> {base:.2f}); {point_t} (x{point_v:.2f})"
    info = {"distance_km": d, "nearest_lat": nlat, "nearest_lon": nlon, "path_type": path["path_type"], "sea_fraction": path["sea_fraction"], "bearing_deg": bearing}
    return Factor("geography", "relevance", value, 1.0, True, reason, ev), info


def action_factor(n: TerrestrialNotice, ctx: TerrestrialContext) -> Factor:
    c = ctx.cfg["terrestrial"]["action"]
    a = (n.action or "").upper()
    value = c.get(a, 1.0)
    return Factor("action", "relevance", value, 1.0, a in c, f"notice action {a or 'unknown'}", [Evidence("filing", "t_action", a)])


def field_strength_factor(n: TerrestrialNotice, geo: dict, ctx: TerrestrialContext) -> Factor:
    c = ctx.cfg["terrestrial"]["field_strength"]
    w = ctx.cfg["terrestrial"]["severity_weights"]["field_strength_margin"]
    thr = tr2508_threshold(n.freq_assgn_mhz, n.bandwidth_khz)
    if thr is None:
        return Factor("field_strength_margin", "severity", c["not_evaluated_value"], w, False,
                      f"{n.freq_assgn_mhz:g} MHz is outside the T/R 25-08 range (29.7-470 MHz); no coordination trigger loaded for this band", [])
    if n.erp_dbw is None:
        return Factor("field_strength_margin", "severity", c["not_evaluated_value"], w, False, "radiated power missing; field strength not calculated",
                      [Evidence("regulation", thr["source"], f"trigger {thr['threshold_dbuv_m']:.1f} dB(uV/m) ({thr['band']})")])
    if geo["distance_km"] <= 0:
        return Factor("field_strength_margin", "severity", 1.0, w, True, "station is inside Finnish territory", [])
    fs = ctx.model.predict(n.freq_assgn_mhz, n.erp_dbw, n.hgt_agl_m, geo["distance_km"], geo["path_type"], c["time_pct"], c["rx_height_m"])
    ev = [Evidence("calculation", fs.model, f"E = {fs.value_dbuv_m:.1f} dB(uV/m) at the nearest Finnish point ({geo['distance_km']:.1f} km, {geo['path_type']} path), e.r.p. {n.erp_dbw:.1f} dBW"),
          Evidence("regulation", thr["source"], f"trigger {thr['threshold_dbuv_m']:.1f} dB(uV/m) in {thr['band']} (base {thr['base_dbuv_m']:.0f} + bandwidth correction {thr['bandwidth_correction_db']:.1f} dB); {thr['conditions']}")]
    for a in fs.assumptions:
        ev.append(Evidence("calculation", "assumption", a))
    margin = fs.value_dbuv_m - thr["threshold_dbuv_m"]
    if getattr(fs, "upper_bound", False):
        bound = fs.value_dbuv_m + (c["sea_upper_bound_margin_db"] if geo["path_type"] != "land" else 0.0)
        if bound < thr["threshold_dbuv_m"]:
            return Factor("field_strength_margin", "severity", 0.05, w, True,
                          f"even free-space field strength ({bound:.1f} dB(uV/m)) stays below the T/R 25-08 trigger {thr['threshold_dbuv_m']:.1f} dB(uV/m): no coordination case possible", ev, indicative=True)
        return Factor("field_strength_margin", "severity", c["not_evaluated_value"], w, False,
                      f"free-space upper bound {fs.value_dbuv_m:.1f} dB(uV/m) exceeds the trigger {thr['threshold_dbuv_m']:.1f} dB(uV/m) (margin {margin:+.1f} dB); a P.1546 calculation is needed to decide", ev, indicative=True)
    value = bin_lookup(margin, c["margin_bins_db"])
    verdict = "ABOVE the trigger" if margin > 0 else "below the trigger"
    return Factor("field_strength_margin", "severity", value, w, True,
                  f"{fs.model}: {fs.value_dbuv_m:.1f} dB(uV/m) vs trigger {thr['threshold_dbuv_m']:.1f} dB(uV/m): margin {margin:+.1f} dB, {verdict}", ev, indicative=True)


def potential_factor(n: TerrestrialNotice, ctx: TerrestrialContext) -> Factor:
    c = ctx.cfg["terrestrial"]["potential"]
    w = ctx.cfg["terrestrial"]["severity_weights"]["interference_potential"]
    if n.erp_dbw is None:
        return Factor("interference_potential", "severity", 0.5, w, False, "radiated power missing", [])
    h = n.hgt_agl_m if n.hgt_agl_m and n.hgt_agl_m > 0 else c["height_ref_m"]
    p = n.erp_dbw + 10.0 * math.log10(h / c["height_ref_m"])
    value = bin_lookup(p, c["bins_dbw"])
    return Factor("interference_potential", "severity", value, w, n.hgt_agl_m is not None,
                  f"e.r.p. {n.erp_dbw:.1f} dBW with antenna {h:g} m above ground: potential index {p:.1f} dBW (height term 10log10(h/{c['height_ref_m']:g} m))",
                  [Evidence("filing", "t_pwr_dbw / t_hgt_agl", f"{n.erp_dbw:.1f} dBW e.r.p. / {fmt(n.hgt_agl_m, 0, ' m')}")])


def protected_station_factor(n: TerrestrialNotice, ctx: TerrestrialContext, station: Optional[ProtectedStation]) -> Factor:
    w = ctx.cfg["terrestrial"]["severity_weights"]["protected_station"]
    bins = ctx.cfg["terrestrial"]["protected_station_bins_km"]
    half = (n.bandwidth_khz or 25.0) / 2000.0
    cands = [station] if station else [s for s in ctx.protected if overlap_mhz(n.freq_assgn_mhz - half, n.freq_assgn_mhz + half, s.f_min_mhz, s.f_max_mhz) > 0]
    if not cands:
        return Factor("protected_station", "severity", 0.0, w, bool(ctx.protected), "no Finnish station of special interest shares the frequency" if ctx.protected else "no list of stations of special interest loaded", [])
    best = min(cands, key=lambda s: haversine_km(n.lat, n.lon, s.lat, s.lon))
    d = haversine_km(n.lat, n.lon, best.lat, best.lon)
    value = bin_lookup(d, bins)
    txt = f"nearest co-frequency Finnish station of special interest: {best.name} ({best.station_id}) at {d:.0f} km"
    if best.antenna_directivity.upper() == "D" and best.antenna_azimuth_deg is not None:
        off = angular_difference_deg(best.antenna_azimuth_deg, initial_bearing_deg(best.lat, best.lon, n.lat, n.lon))
        if off <= 45:
            value = clamp(value * 1.2)
            txt += f"; its antenna (azimuth {best.antenna_azimuth_deg:g} deg) looks towards the notified site (off-axis {off:.0f} deg)"
        else:
            txt += f"; its antenna looks away (off-axis {off:.0f} deg)"
    return Factor("protected_station", "severity", value, w, True, txt,
                  [Evidence("asset", best.source_ref or f"special-interest station {best.station_id}", f"{best.name} {best.f_center_mhz:g} MHz +/- {best.bandwidth_khz / 2:g} kHz at ({best.lat:.4f}, {best.lon:.4f})")])


def novelty_factor(n: TerrestrialNotice, ctx: TerrestrialContext) -> Factor:
    c = ctx.cfg["terrestrial"]["novelty"]
    w = ctx.cfg["terrestrial"]["urgency_weights"]["novelty"]
    status = n.change_status or "unknown"
    if status == "modified" and any(f in ctx.cfg["terrestrial"]["technical_fields"] for f in n.changed_fields):
        status = "modified_technical"
    value = c.get(status, c["unknown"])
    txt = {"new": "not present in the previous IFIC", "modified_technical": "technical parameters changed since the previous IFIC: " + ", ".join(n.changed_fields),
           "modified": "changed since the previous IFIC (non-technical fields)", "unchanged": "unchanged re-publication", "withdrawn": "withdrawn", "unknown": "no previous IFIC supplied for comparison"}[status if status in c else "unknown"]
    return Factor("novelty", "urgency", value, w, status != "unknown", txt, [Evidence("history", "ific diff", status)])


def provision_factor(n: TerrestrialNotice, ctx: TerrestrialContext) -> tuple[Factor, Optional[str]]:
    c = ctx.cfg["terrestrial"]["provision"]
    w = ctx.cfg["terrestrial"]["urgency_weights"]["provision"]
    key = n.fragment if n.fragment in c else (n.prov if n.prov in c else "unknown")
    value = c[key]
    deadline = None
    if key in ("Req_agrt", "RR9.21"):
        txt = "agreement sought under No. 9.21: Finland must comment within the 4-month window or is deemed to agree"
        if n.ific_date:
            deadline = (n.ific_date + timedelta(days=ctx.cfg["terrestrial"]["comment_window_days"]["RR9.21"])).isoformat()
            txt += f" (ends {deadline})"
    elif key in ("NTFD_RR", "RR11.2"):
        txt = "notification for recording in the MIFR under No. 11.2; objections possible through the Article 11 examination"
    else:
        txt = "provision not recognised"
    return Factor("provision", "urgency", value, w, key != "unknown", txt, [Evidence("filing", "t_fragment / t_prov", f"{n.fragment} / {n.prov}")]), deadline


def framework_factor(n: TerrestrialNotice, ctx: TerrestrialContext) -> Factor:
    c = ctx.cfg["terrestrial"]["framework"]
    w = ctx.cfg["terrestrial"]["urgency_weights"]["framework"]
    thr = tr2508_threshold(n.freq_assgn_mhz, n.bandwidth_khz)
    if thr:
        return Factor("framework", "urgency", c["quantitative_trigger"], w, True, f"ECC/ERC Rec. T/R 25-08 gives a quantitative coordination trigger for {thr['band']}", [Evidence("regulation", thr["source"], thr["band"])])
    return Factor("framework", "urgency", c["general_only"], w, True, "no quantitative trigger loaded for this band; only the general RR Article 9/11 framework applies", [])


# ----------------------------------------------------------------------------- per-target factors

def freq_factor(n: TerrestrialNotice, lo: float, hi: float, unit_label: str, unit_ref: str, overlap: float, gap: float, ctx: TerrestrialContext) -> Factor:
    c = ctx.cfg["terrestrial"]["freq"]
    half = (n.bandwidth_khz or 25.0) / 2000.0
    ev = [Evidence("filing", "t_freq_assgn / t_bdwdth_cde", f"{n.freq_assgn_mhz:g} MHz, {fmt(n.bandwidth_khz, 1, ' kHz')}"), Evidence("finnish_table", unit_ref, unit_label)]
    if overlap > 0:
        frac = min(1.0, overlap / (2 * half)) if half > 0 else 1.0
        value = c["overlap_floor"] + (1.0 - c["overlap_floor"]) * frac
        return Factor("freq_overlap", "relevance", value, 1.0, True, f"co-frequency: {frac:.0%} of the notified emission falls in {lo:g}-{hi:g} MHz", ev)
    return Factor("freq_overlap", "relevance", c["adjacent_relevance"], 1.0, True, f"adjacent: {gap * 1000:.1f} kHz from {lo:g}-{hi:g} MHz", ev)


def sensitivity_factor_unit(unit: AllocationUnit, ctx: TerrestrialContext) -> Factor:
    tier, label = ctx.table.sensitivity(unit, ctx.cfg)
    w = ctx.cfg["terrestrial"]["severity_weights"]["finnish_sensitivity"]
    return Factor("finnish_sensitivity", "severity", tier, w, True, f"Finnish use '{unit.service}' / '{unit.usage}' rated {tier:.2f}: {label}", [Evidence("finnish_table", unit.source_ref, unit.label)])


def sensitivity_factor_station(st: ProtectedStation, ctx: TerrestrialContext) -> Factor:
    w = ctx.cfg["terrestrial"]["severity_weights"]["finnish_sensitivity"]
    fake = AllocationUnit("station", [], st.f_min_mhz, st.f_max_mhz, st.service.upper(), st.service, "RX", "", "")
    tier, label = ctx.table.sensitivity(fake, ctx.cfg)
    tier = max(tier, 0.8)   # a station on the special-interest list is important by definition
    return Factor("finnish_sensitivity", "severity", tier, w, True, f"station of special interest '{st.name}' ({st.service or 'service not stated'}) rated {tier:.2f}", [Evidence("asset", st.source_ref or st.station_id, st.name)])


# ----------------------------------------------------------------------------- assembly

def score_notice(n: TerrestrialNotice, ctx: TerrestrialContext) -> ScoredSubject:
    cfg = ctx.cfg
    act = (n.action or "").upper()
    if act in ("SUPPRESS", "WITHDRAW") or n.change_status == "withdrawn":
        return ScoredSubject(n.notice_id, n.label, 0, "D", 1.0, 0, [], status="withdrawn", summary=f"{n.label}: {act.lower() or 'withdrawn'}; no action, listed for the record.")
    geo, info = geo_factor(n, ctx)
    shared_rel = {"geo": geo, "action": action_factor(n, ctx)}
    prov, deadline = provision_factor(n, ctx)
    shared_sev = {"fs": field_strength_factor(n, info, ctx), "pot": potential_factor(n, ctx)}
    shared_urg = [novelty_factor(n, ctx), prov, framework_factor(n, ctx)]
    half = (n.bandwidth_khz or 25.0) / 2000.0
    f_lo, f_hi = n.freq_assgn_mhz - half, n.freq_assgn_mhz + half
    guard = cfg["terrestrial"]["freq"]["adjacent_guard_khz"] / 1000.0
    targets: list[tuple] = [("unit", u, ov, 0.0) for u, ov in ctx.table.overlapping(f_lo, f_hi)]
    targets += [("unit", u, 0.0, gp) for u, gp in ctx.table.adjacent(f_lo, f_hi, guard)]
    for st in ctx.protected:
        ov = overlap_mhz(f_lo, f_hi, st.f_min_mhz, st.f_max_mhz)
        gp = gap_mhz(f_lo, f_hi, st.f_min_mhz, st.f_max_mhz)
        if ov > 0 or gp <= guard:
            targets.append(("station", st, ov, gp))
    findings: list[Finding] = []
    for kind, tgt, ov, gp in targets:
        if kind == "unit":
            u: AllocationUnit = tgt
            rel = [freq_factor(n, u.f_min_mhz, u.f_max_mhz, u.label, u.source_ref, ov, gp, ctx), shared_rel["geo"], shared_rel["action"]]
            sev = [shared_sev["fs"], shared_sev["pot"], sensitivity_factor_unit(u, ctx), protected_station_factor(n, ctx, None)]
            tid, tlabel = u.unit_id, u.label
        else:
            st: ProtectedStation = tgt
            rel = [freq_factor(n, st.f_min_mhz, st.f_max_mhz, f"{st.name} {st.f_center_mhz:g} MHz", st.source_ref or st.station_id, ov, gp, ctx), shared_rel["geo"], shared_rel["action"]]
            sev = [shared_sev["fs"], shared_sev["pot"], sensitivity_factor_station(st, ctx), protected_station_factor(n, ctx, st)]
            tid, tlabel = st.station_id, f"{st.name} | {st.service or 'special interest'} | {st.f_center_mhz:g} MHz"
        factors = rel + sev + shared_urg
        relevance, severity, urgency = product(rel), weighted_mean(sev), weighted_mean(shared_urg)
        score = combine_score(relevance, severity, urgency, cfg)
        screened = None
        if relevance <= 0:
            zero = next(f for f in rel if f.value <= 0)
            screened, score = f"{zero.name}: {zero.reason}", 0
        f = Finding(f"{n.notice_id}:{tid}", n.notice_id, n.label, tid, tlabel, score, priority_from_score(score, cfg), relevance, severity, urgency,
                    confidence_from_factors(factors), factors, screened, any(x.indicative for x in factors), missing_inputs(factors), deadline=deadline)
        f.explanation = explain_finding(f, cfg)
        findings.append(f)
    findings.sort(key=lambda f: (f.screened_out_reason is not None, -f.score, -f.confidence))
    active = [f for f in findings if f.screened_out_reason is None]
    if not active:
        reason = findings[0].screened_out_reason if findings else "no Finnish use within the emission or its guard band"
        return ScoredSubject(n.notice_id, n.label, 0, "D", findings[0].confidence if findings else 1.0, 0, findings, status="screened_out", summary=f"{n.label}: screened out ({reason}).")
    top = active[0]
    breadth = len({f.target_label.split(" | ")[1] if " | " in f.target_label else f.target_label for f in active if f.score >= cfg["priority_bands"]["C"]})
    s = ScoredSubject(n.notice_id, n.label, top.score, top.priority, top.confidence, breadth, findings, deadline=deadline)
    s.summary = summarize_subject(s, cfg)
    return s


def rank_notices(notices: list[TerrestrialNotice], ctx: TerrestrialContext) -> list[ScoredSubject]:
    scored = [score_notice(n, ctx) for n in notices]
    scored.sort(key=lambda s: (-s.score, -s.breadth, -s.confidence, s.subject_id))
    return scored


# ----------------------------------------------------------------------------- IFIC diff and trends

def _key(n: TerrestrialNotice) -> tuple:
    return (n.adm, n.adm_ref_id) if n.adm_ref_id else n.identity_key()


def diff_notices(previous: list[TerrestrialNotice], current: list[TerrestrialNotice], technical_fields: list[str]) -> dict:
    """Set change_status/changed_fields on current notices; return counts and the withdrawn list."""
    prev = {_key(n): n for n in previous}
    cur_keys = set()
    counts = {"new": 0, "modified": 0, "unchanged": 0, "withdrawn": 0}
    for n in current:
        k = _key(n)
        cur_keys.add(k)
        if (n.action or "").upper() in ("SUPPRESS", "WITHDRAW"):
            n.change_status = "withdrawn"
            counts["withdrawn"] += 1
            continue
        old = prev.get(k)
        if old is None:
            n.change_status, n.changed_fields = "new", []
            counts["new"] += 1
            continue
        changed = [f for f in technical_fields + ["action", "stn_cls", "emi_cls", "site_name"] if getattr(old, f, None) != getattr(n, f, None)]
        if changed:
            n.change_status, n.changed_fields = "modified", changed
            counts["modified"] += 1
        else:
            n.change_status, n.changed_fields = "unchanged", []
            counts["unchanged"] += 1
    withdrawn = [n for k, n in prev.items() if k not in cur_keys]
    counts["withdrawn"] += len(withdrawn)
    return {"counts": counts, "withdrawn": withdrawn}


def band_bucket(freq_mhz: float, edges: list[float]) -> str:
    for lo, hi in zip(edges, edges[1:]):
        if lo <= freq_mhz < hi:
            return f"{lo:g}-{hi:g} MHz"
    return "<29.7 MHz" if freq_mhz < edges[0] else f">={edges[-1]:g} MHz"


def trends(current: list[TerrestrialNotice], history: list[list[TerrestrialNotice]], cfg: dict, region: Optional[Region] = None) -> list[dict]:
    """Counts per (adm, band, station class) now vs earlier IFICs, with z-scores; plus near-border clusters."""
    edges = cfg["terrestrial"]["trend_band_edges_mhz"]
    zthr = cfg["terrestrial"]["trend_z_threshold"]

    def count(ns: list[TerrestrialNotice]) -> dict[tuple, int]:
        out: dict[tuple, int] = {}
        for n in ns:
            if (n.action or "").upper() in ("SUPPRESS", "WITHDRAW"):
                continue
            k = (n.adm, band_bucket(n.freq_assgn_mhz, edges), n.stn_cls)
            out[k] = out.get(k, 0) + 1
        return out

    now = count(current)
    hist = [count(h) for h in history]
    items = []
    for k, c in sorted(now.items(), key=lambda kv: -kv[1]):
        series = [h.get(k, 0) for h in hist]
        mean = statistics.mean(series) if series else 0.0
        sd = statistics.pstdev(series) if len(series) > 1 else 0.0
        z = (c - mean) / sd if sd > 0 else (float("inf") if c > mean and mean == 0 and c >= 3 else 0.0)
        flag = (sd > 0 and z >= zthr) or (sd == 0 and mean == 0 and c >= 3) or (sd == 0 and mean > 0 and c >= 2 * mean and c >= 3)
        items.append({"adm": k[0], "band": k[1], "stn_cls": k[2], "count": c, "baseline_mean": round(mean, 2), "baseline_sd": round(sd, 2),
                      "z": None if z == float("inf") else round(z, 2), "flag": bool(flag),
                      "note": "new activity (no history)" if (mean == 0 and c >= 3) else ("above baseline" if flag else "")})
    region = region or Region.load()
    near = {}
    for n in current:
        d, _, _ = region.distance_to_country_km("FIN", n.lat, n.lon)
        if d <= 50:
            near[n.adm] = near.get(n.adm, 0) + 1
    for adm, c in near.items():
        items.append({"adm": adm, "band": "all", "stn_cls": "all", "count": c, "baseline_mean": None, "baseline_sd": None, "z": None, "flag": c >= 3, "note": "stations within 50 km of Finnish territory"})
    wide = [n for n in current if (n.bandwidth_khz or 0) > 200]
    if wide:
        by_adm: dict[str, int] = {}
        for n in wide:
            by_adm[n.adm] = by_adm.get(n.adm, 0) + 1
        for adm, c in by_adm.items():
            items.append({"adm": adm, "band": "all", "stn_cls": "all", "count": c, "baseline_mean": None, "baseline_sd": None, "z": None, "flag": c >= 3, "note": "wideband (> 200 kHz) notices"})
    return items
