"""Step B4 of pm_pack/08: run the space pipeline for one issue and assemble ranked Finding objects.

One Finding per notice (a notice is as serious as its worst group, scoring/DESIGN.md section 2). The lead group is
the group with the highest concern, then the highest score. Every finding carries evidence that a person, or
radar.evidence_check, can reopen: the notice row, its special sections, the station row, the lead group row,
the Finnish table rows, the Bureau's provn rows when Finland is named, the earth station row for uplinks, and the
geography calculation. The reason is a fixed template; no language model is involved.

    uv run python -m radar.pipeline.assemble 3074      # writes data/derived/findings_space_3074.json
"""
from __future__ import annotations

import sys
from dataclasses import dataclass

import duckdb

from radar import schema_map
from radar.adapters import plans as PLANS
from radar.adapters import space_ific, traficom_table
from radar.adapters import special_interest as SI
from radar.config import settings
from radar.evidence import locator, row_excerpt
from radar.models import AnalysisResult, CalcTrace, Evidence, Finding
from radar.calc import pfd as PFD
from radar.models import CalcInput
from radar.pipeline import geography as G
from radar.pipeline import plans as PL
from radar.pipeline import rank as RK
from radar.pipeline import relevance as rel

MAX_FINNISH_ROWS = 6
MAX_STATION_EVIDENCE = 5          # special-interest stations cited per finding; all of them are in the results file
DIRECTION_TEXT = {"space_to_earth": "space-to-Earth", "earth_to_space": "Earth-to-space", "unknown": "direction unknown"}


@dataclass
class SpaceRun:
    result: AnalysisResult
    rows: list                     # GroupRelevance for every screened group
    scores: dict                   # group_id -> GroupScore
    ingest: space_ific.IngestResult
    pfd: dict = None               # group_id -> PfdResult (C1)
    plan_notices: dict = None      # notice_id -> adapters.plans.PlanNotice: plan sections the issue published
    plan_snapshots: dict = None    # database key -> snapshot number used (empty when the plan databases are missing)

    def notices(self) -> dict:
        """notice_id -> Notice for every finding: the IFIC notices plus the plan sections, as Notice objects."""
        out = {n.notice_id: n for n in self.ingest.notices}
        for nid, p in (self.plan_notices or {}).items():
            out.setdefault(nid, PL.as_notice(self.result.issue, p))
        return out


def _fmt_hz(hz: int) -> str:
    for unit, div in (("GHz", 1e9), ("MHz", 1e6), ("kHz", 1e3)):
        if hz >= div:
            return f"{hz / div:.6g} {unit}"
    return f"{hz} Hz"


def _pfd_trace(res, gi, add, source, M, gid, score, geo_ev, station_ev=None, con=None) -> CalcTrace:
    """CalcTrace for the lead group, with an evidence item for every input (pm_pack/06 rule 5)."""
    base_notes = [f"ranking score {score.score} from scoring/weights.json", f"geography evidence {geo_ev}"]
    if res is None:
        return CalcTrace(method="none", inputs=[], formula="", result_value=None, result_unit="", limit_value=None,
                         limit_evidence_id=None, margin_db=None,
                         notes=["pfd not evaluated: only space-station downlinks over Finnish terrestrial or passive rows "
                                "that Finland can see are computed in step C1"] + base_notes)
    formula = PFD.FORMULA if res.orbit == "GSO" else PFD.FORMULA_NGSO
    if res.status != "computed":
        return CalcTrace(method=res.method, inputs=[], formula=formula, result_value=None, result_unit="",
                         limit_value=None, limit_evidence_id=None, margin_db=None, notes=res.notes + base_notes)
    w = res.worst
    row = w["limit_row"]
    t_em, t_beam = M.table("space", "emission"), M.table("space", "beam")
    em_ev = add("itu_row", source, locator(t_em, **{M.col("space", "emission", "group_id"): gid, "seq_no": w["emission_seq_no"]}),
                f"{M.col('space', 'emission', 'designation')}={w['designation']}; "
                f"{M.col('space', 'emission', 'max_power_density_dbw_hz')}={w['p_d_dbw_hz']:.6g}")
    beam_ev = add("itu_row", source, locator(t_beam, **{M.col("space", "beam", "notice_id"): gi.notice_id,
                                                        M.col("space", "beam", "direction"): gi.direction_code,
                                                        M.col("space", "beam", "beam_name"): gi.beam_name}),
                  f"{M.col('space', 'beam', 'max_gain_dbi')}={w['gain_dbi']:.6g}")
    lim_ev = add("regulation", f"{row.source}, page {row.page} (data/reference/pfd_limits.csv)",
                 f"pfd_limits.csv id={row.id}", row.excerpt())
    point_ev = geo_ev
    if res.orbit != "GSO" and con is not None:
        ok = {M.col("space", "orbit", "notice_id"): gi.notice_id, M.col("space", "orbit", "orbit_id"): w["orbit_id"]}
        point_ev = add("itu_row", source, locator(M.table("space", "orbit"), **ok), row_excerpt(
            con, M.table("space", "orbit"), ok, [M.col("space", "orbit", c) for c in
                                                ("inclination_deg", "apogee_km", "perigee_km", "satellites_per_plane")]))
    if w["point"].startswith("station ") and station_ev is not None:
        point_ev = station_ev(w["point"][len("station "):]) or geo_ev
    calc_ev = add("calculation", "radar.calc.pfd", f"pfd(group_id={gid})",
                  f"pfd {res.pfd_db:.2f} dB(W/m2) in {PFD.fmt_bw(w['bandwidth_hz'])} at {w['point']}; limit {res.limit_db:.2f}; margin {res.margin_db:.2f} dB")
    inputs = [
        CalcInput(name="P_d max power density at antenna input", value=w["p_d_dbw_hz"], unit="dBW/Hz", evidence_id=em_ev),
        CalcInput(name="G max beam gain", value=w["gain_dbi"], unit="dBi", evidence_id=beam_ev),
        CalcInput(name="B bandwidth used, min(reference, emission)", value=w["bandwidth_hz"], unit="Hz", evidence_id=lim_ev),
        CalcInput(name=f"d slant range from {w['point']}", value=w["slant_range_km"], unit="km", evidence_id=point_ev),
        CalcInput(name=f"delta angle of arrival at {w['point']}", value=w["elevation_deg"], unit="deg", evidence_id=point_ev),
        CalcInput(name="10 log10(4 pi d^2) spreading loss", value=w["spreading_loss_db"], unit="dB", evidence_id=calc_ev),
    ]
    if res.orbit != "GSO":
        inputs[3:3] = [CalcInput(name=f"h altitude (perigee of orbit {w['orbit_id']})", value=w["altitude_km"], unit="km",
                                 evidence_id=point_ev),
                       CalcInput(name="highest elevation seen from Finland", value=w["max_elevation_deg"], unit="deg",
                                 evidence_id=calc_ev)]
        if row.x_footnote == "13":
            inputs.append(CalcInput(name="X (RR footnote 13) from N satellites", value=w["x_db"], unit="dB", evidence_id=point_ev))
    return CalcTrace(method=res.method, inputs=inputs, formula=formula, result_value=res.pfd_db,
                     result_unit=f"dB(W/m2) in {PFD.fmt_bw(w['bandwidth_hz'])}", limit_value=res.limit_db, limit_evidence_id=lim_ev,
                     margin_db=res.margin_db, label="indicative", notes=res.notes + base_notes)


def run(issue: int) -> SpaceRun:
    M = schema_map.load()
    T = lambda e: M.table("space", e)  # noqa: E731
    C = lambda e, c: M.col("space", e, c)  # noqa: E731
    ing = space_ific.load(issue)
    bands = traficom_table.subbands()
    bands_by_id = {b.id: b for b in bands}
    classes = {b.id: rel.classify(b.services_in_finland) for b in bands}
    stations = list(SI.stations())               # () when data/raw/special_interest.xlsx is missing
    stations_by_number: dict[str, list] = {}
    for st in stations:
        stations_by_number.setdefault(st.station_number, []).append(st)
    source = f"ific{issue}.mdb (data/derived/space_{issue}.duckdb)"

    con = duckdb.connect(str(space_ific.db_path(issue)), read_only=True)
    named = rel.finland_named(con)
    rows = rel.screen(ing.notices, bands, stations=stations, named=named)
    types = dict(con.execute(f"SELECT CAST({M.q('space','notice','notice_id')} AS VARCHAR), {M.q('space','notice','orbit_code')} "
                             f"FROM {M.t('space','notice')}").fetchall())
    actions = dict(con.execute(f"SELECT CAST({M.q('space','notice','notice_id')} AS VARCHAR), {M.q('space','notice','action')} "
                               f"FROM {M.t('space','notice')}").fetchall())
    geo = G.for_issue(ing.notices, con)
    G.apply(rows, geo, types, stations)

    by_notice = {n.notice_id: n for n in ing.notices}
    # AP30/30A/30B: Finland's own plan entries, from the plan databases (the IFIC database has none)
    snaps = PLANS.snapshots()
    entries = PLANS.finnish_entries(snaps=snaps) if snaps else []
    effects = PLANS.bureau_effects(snaps=snaps) if snaps else []
    PL.apply(rows, by_notice, PL.tolerances(con), entries, effects)
    # C1: worst-case pfd for space-station downlinks (GSO and non-GSO) over Finnish terrestrial or passive rows, visible
    # from Finland
    eligible = [r for r in rows if r.candidate and r.direction == "space_to_earth" and types.get(r.notice_id) in ("G", "N")
                and r.geo_relevance in ("visible", "low_elevation")
                and ("pfd_terrestrial" in r.paths or "passive_service" in r.paths)]
    pfd_inputs = PFD.load_inputs(con, [r.group_id for r in eligible])
    orbits = PFD.load_orbits(con, sorted({r.notice_id for r in eligible if types.get(r.notice_id) == "N"}))
    pfd_results = {}
    for r in eligible:
        gi = pfd_inputs.get(r.group_id)
        if gi is None:
            continue
        if types.get(r.notice_id) == "N":
            if orbits.get(r.notice_id):
                pfd_results[r.group_id] = PFD.worst_case_ngso(r.freq_min_hz, r.freq_max_hz, orbits[r.notice_id], gi.emissions,
                                                              gi.gain_dbi, gi.steerable)
            continue
        lon = by_notice[r.notice_id].longitude_deg
        if lon is not None:
            pfd_results[r.group_id] = PFD.worst_case(r.freq_min_hz, r.freq_max_hz, lon, gi.emissions, gi.gain_dbi, gi.steerable,
                                                     extra_points=G.station_points(r.matched_station_numbers, lon, stations))
    scores, lead = {}, {}
    for r in rows:
        n = by_notice[r.notice_id]
        gdet = G.group_relevance(geo, r.notice_id, r.group_id, r.direction).detail
        s = RK.score_group(r, bands=bands_by_id, classes=classes, section=n.special_section,
                           action=actions.get(r.notice_id), geo_detail=gdet, pfd=pfd_results.get(r.group_id))
        scores[r.group_id] = s
        if RK.better(s, scores.get(lead.get(r.notice_id))):
            lead[r.notice_id] = r.group_id
    rows_by_group = {r.group_id: r for r in rows}
    candidates_per_notice = {}
    for r in rows:
        if r.candidate:
            candidates_per_notice[r.notice_id] = candidates_per_notice.get(r.notice_id, 0) + 1

    plan_tol = PL.tolerances(con)
    findings: list[Finding] = []
    for n in ing.notices:
        ev: list[Evidence] = []

        def add(kind, src, loc, excerpt):
            ev.append(Evidence(id=f"E-{len(ev) + 1:03d}", kind=kind, source=src, locator=loc, excerpt=excerpt))
            return ev[-1].id

        nkey = {C("notice", "notice_id"): n.notice_id}
        add("itu_row", source, locator(T("notice"), **nkey),
            row_excerpt(con, T("notice"), nkey, [C("notice", c) for c in ("administration", "orbit_code", "reason", "action", "ific_no", "ific_part")]))
        for (seq,) in con.execute(f'SELECT "seq_no" FROM {M.t("space","special_section")} WHERE CAST({M.q("space","special_section","notice_id")} AS VARCHAR) = ? ORDER BY 1',
                                  [n.notice_id]).fetchall():
            k = {C("special_section", "notice_id"): n.notice_id, "seq_no": seq}
            add("itu_row", source, locator(T("special_section"), **k),
                row_excerpt(con, T("special_section"), k, [C("special_section", c) for c in ("reference", "number", "revision", "revision_no")]))
        t = types.get(n.notice_id)
        station_entity, station_fields = {"G": ("gso", ("satellite_name", "longitude_deg")),
                                          "N": ("non_gso", ("satellite_name", "reference_body")),
                                          "S": ("earth_station_notice", ("station_name", "satellite_name"))}.get(t, (None, ()))
        if station_entity:
            k = {C(station_entity, "notice_id"): n.notice_id}
            ex = row_excerpt(con, T(station_entity), k, [C(station_entity, c) for c in station_fields])
            if ex:
                add("itu_row", source, locator(T(station_entity), **k), ex)

        gid = lead.get(n.notice_id)
        r = rows_by_group.get(gid) if gid else None
        s = scores.get(gid) if gid else None
        if r is None:
            reason = "No group of this notice was published in this issue (suppression or Part III-S record)."
            findings.append(Finding(id="", kind="space", issue=issue, notice_id=n.notice_id, geo_relevance="unknown",
                                    calc=CalcTrace(method="none", inputs=[], formula="", result_value=None, result_unit="",
                                                   limit_value=None, limit_evidence_id=None, margin_db=None,
                                                   notes=["no group to evaluate"]),
                                    concern="none", reason=reason, evidence=ev))
            continue

        gkey = {C("group", "group_id"): gid}
        add("itu_row", source, locator(T("group"), **gkey),
            row_excerpt(con, T("group"), gkey, [C("group", c) for c in ("notice_id", "direction", "freq_min_mhz", "freq_max_mhz", "beam_name", "ific_no")]))
        lanes, seen = [], set()
        for i in r.matched_subband_ids:
            b = bands_by_id[i]
            key = (b.services_in_finland, b.lower_hz, b.upper_hz)
            if key not in seen:
                seen.add(key)
                lanes.append(b)
        lanes.sort(key=lambda b: ({"terrestrial": 0, "passive": 1, "space": 2}.get(classes[b.id].category, 3), b.lower_hz))
        for b in lanes[:MAX_FINNISH_ROWS]:
            e = traficom_table.evidence(b, f"E-{len(ev) + 1:03d}")
            ev.append(e)
        for prov in r.finland_named_provisions:
            k = {C("affected", "group_id"): gid, C("affected", "administration"): "FIN", C("affected", "provision"): prov}
            ex = row_excerpt(con, T("affected"), k, [C("affected", "provision"), C("affected", "administration"), "agree_st"])
            if ex:
                add("itu_row", source, locator(T("affected"), **k), ex)
        station_ids: dict[str, str] = {}

        def station_ev(number: str) -> str | None:
            if number not in station_ids and number in stations_by_number:
                e = SI.evidence(stations_by_number[number][0], f"E-{len(ev) + 1:03d}")
                ev.append(e)
                station_ids[number] = e.id
            return station_ids.get(number)

        # the stations most exposed first: lowest elevation (longest path, strictest limit) or nearest earth station
        reach = r.station_reach
        for number in sorted(r.matched_station_numbers, key=lambda k: (reach.get(k, {}).get("elevation_deg", 0),
                                                                       reach.get(k, {}).get("distance_km", 0), k))[:MAX_STATION_EVIDENCE]:
            station_ev(number)
        if "service_area_finland" in r.paths:
            sk = {C("service_area", "group_id"): gid, C("service_area", "country"): "FIN"}
            add("itu_row", source, locator(T("service_area"), **sk),
                row_excerpt(con, T("service_area"), sk, [C("service_area", "country"), C("service_area", "excluded_api")]))
        for b in r.plan_bureau[:4]:
            PL.add_effect_evidence(add, b)
        for h in r.plan_hits[:2]:
            PL.add_entry_evidence(add, h.entry)
            te, tw = plan_tol.get(n.notice_id, (None, None))
            add("calculation", "radar.pipeline.plans", PL.arc_locator(f"ific{issue}", n.notice_id, h.entry),
                PL.arc_excerpt(h.entry, n.longitude_deg, te, tw))
        gres = G.group_relevance(geo, n.notice_id, gid, r.direction)
        nearest = gres.detail.get("nearest") if gres.method == "earth_station_distance" else None
        if nearest and nearest.get("seq_no") is not None:
            k = {C("earth_station", "group_id"): gid, C("earth_station", "seq_no"): nearest["seq_no"]}
            add("itu_row", source, locator(T("earth_station"), **k),
                row_excerpt(con, T("earth_station"), k, [C("earth_station", c) for c in ("station_name", "country", "lat_deg", "lon_deg")]))
        geo_key = f"group_id={gid}" if gid in geo.by_group else f"notice_id={n.notice_id}"
        geo_ev = add("calculation", "radar.pipeline.geography", f"geography({geo_key})", f"{gres.relevance}: {gres.note}")

        calc = _pfd_trace(pfd_results.get(gid), pfd_inputs.get(gid), add, source, M, gid, s, geo_ev, station_ev, con)

        more = candidates_per_notice.get(n.notice_id, 0) - (1 if r.candidate else 0)
        reason = (f"{s.rule[0].upper()}{s.rule[1:]}. Lead group {gid}: {_fmt_hz(r.freq_min_hz)} to {_fmt_hz(r.freq_max_hz)} "
                  f"{DIRECTION_TEXT[r.direction]}; geography {r.geo_relevance} ({gres.note})"
                  + (f"; {more} more candidate group(s) in this notice" if more > 0 else "") + "."
                  if s.concern != "none" else f"Not raised: {r.drop_reason or s.rule}.")
        findings.append(Finding(
            id="", kind="space", issue=issue, notice_id=n.notice_id, group_id=gid,
            matched_subband_ids=[b.id for b in lanes[:MAX_FINNISH_ROWS]],
            matched_station_numbers=r.matched_station_numbers, overlap_hz=r.overlap_hz,
            geo_relevance=r.geo_relevance if r.geo_relevance in ("visible", "low_elevation", "not_visible", "near_border", "far") else "unknown",
            calc=calc, concern=s.concern, reason=reason, evidence=ev,
        ))
    con.close()
    plan_notices = PLANS.published_in(issue, snaps) if snaps else []
    findings += PL.plan_notice_findings(issue, plan_notices, entries, effects)

    order = sorted(findings, key=lambda f: (-RK.CONCERN_ORDER[f.concern], -(scores[f.group_id].score if f.group_id else 0), f.notice_id))
    for k, f in enumerate(order, start=1):
        f.id = f"F-{issue}-{k:04d}"
    complete = sum(1 for f in order if f.evidence and all(e.excerpt for e in f.evidence))
    result = AnalysisResult(issue=issue, kind="space", screened=len(order), flagged=sum(1 for f in order if f.concern != "none"),
                            provenance_coverage_pct=round(100 * complete / max(len(order), 1), 1), findings=order)
    return SpaceRun(result, rows, scores, ing, pfd_results, {p.notice_id: p for p in plan_notices}, snaps)


def main() -> int:
    issue = int(sys.argv[1]) if len(sys.argv) > 1 else 3074
    run_ = run(issue)
    out = settings.derived_dir / f"findings_space_{issue}.json"
    out.write_text(run_.result.model_dump_json(indent=1), encoding="utf-8")
    from collections import Counter
    print(f"{out}: screened {run_.result.screened}, flagged {run_.result.flagged}, provenance "
          f"{run_.result.provenance_coverage_pct} %, concern {dict(Counter(f.concern for f in run_.result.findings))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
