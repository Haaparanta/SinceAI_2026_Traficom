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
from radar.adapters import space_ific, traficom_table
from radar.config import settings
from radar.evidence import locator, row_excerpt
from radar.models import AnalysisResult, CalcTrace, Evidence, Finding
from radar.pipeline import geography as G
from radar.pipeline import rank as RK
from radar.pipeline import relevance as rel

MAX_FINNISH_ROWS = 6
DIRECTION_TEXT = {"space_to_earth": "space-to-Earth", "earth_to_space": "Earth-to-space", "unknown": "direction unknown"}


@dataclass
class SpaceRun:
    result: AnalysisResult
    rows: list                     # GroupRelevance for every screened group
    scores: dict                   # group_id -> GroupScore
    ingest: space_ific.IngestResult


def _fmt_hz(hz: int) -> str:
    for unit, div in (("GHz", 1e9), ("MHz", 1e6), ("kHz", 1e3)):
        if hz >= div:
            return f"{hz / div:.6g} {unit}"
    return f"{hz} Hz"


def run(issue: int) -> SpaceRun:
    M = schema_map.load()
    T = lambda e: M.table("space", e)  # noqa: E731
    C = lambda e, c: M.col("space", e, c)  # noqa: E731
    ing = space_ific.load(issue)
    bands = traficom_table.subbands()
    bands_by_id = {b.id: b for b in bands}
    classes = {b.id: rel.classify(b.services_in_finland) for b in bands}
    source = f"ific{issue}.mdb (data/derived/space_{issue}.duckdb)"

    con = duckdb.connect(str(space_ific.db_path(issue)), read_only=True)
    named = rel.finland_named(con)
    rows = rel.screen(ing.notices, bands, named=named)
    types = dict(con.execute(f"SELECT CAST({M.q('space','notice','notice_id')} AS VARCHAR), {M.q('space','notice','orbit_code')} "
                             f"FROM {M.t('space','notice')}").fetchall())
    actions = dict(con.execute(f"SELECT CAST({M.q('space','notice','notice_id')} AS VARCHAR), {M.q('space','notice','action')} "
                               f"FROM {M.t('space','notice')}").fetchall())
    geo = G.for_issue(ing.notices, con)
    G.apply(rows, geo, types)

    by_notice = {n.notice_id: n for n in ing.notices}
    scores, lead = {}, {}
    for r in rows:
        n = by_notice[r.notice_id]
        gdet = G.group_relevance(geo, r.notice_id, r.group_id, r.direction).detail
        s = RK.score_group(r, bands=bands_by_id, classes=classes, section=n.special_section,
                           action=actions.get(r.notice_id), geo_detail=gdet)
        scores[r.group_id] = s
        if RK.better(s, scores.get(lead.get(r.notice_id))):
            lead[r.notice_id] = r.group_id
    rows_by_group = {r.group_id: r for r in rows}
    candidates_per_notice = {}
    for r in rows:
        if r.candidate:
            candidates_per_notice[r.notice_id] = candidates_per_notice.get(r.notice_id, 0) + 1

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
        gres = G.group_relevance(geo, n.notice_id, gid, r.direction)
        nearest = gres.detail.get("nearest") if gres.method == "earth_station_distance" else None
        if nearest and nearest.get("seq_no") is not None:
            k = {C("earth_station", "group_id"): gid, C("earth_station", "seq_no"): nearest["seq_no"]}
            add("itu_row", source, locator(T("earth_station"), **k),
                row_excerpt(con, T("earth_station"), k, [C("earth_station", c) for c in ("station_name", "country", "lat_deg", "lon_deg")]))
        geo_key = f"group_id={gid}" if gid in geo.by_group else f"notice_id={n.notice_id}"
        geo_ev = add("calculation", "radar.pipeline.geography", f"geography({geo_key})", f"{gres.relevance}: {gres.note}")

        more = candidates_per_notice.get(n.notice_id, 0) - (1 if r.candidate else 0)
        reason = (f"{s.rule[0].upper()}{s.rule[1:]}. Lead group {gid}: {_fmt_hz(r.freq_min_hz)} to {_fmt_hz(r.freq_max_hz)} "
                  f"{DIRECTION_TEXT[r.direction]}; geography {r.geo_relevance} ({gres.note})"
                  + (f"; {more} more candidate group(s) in this notice" if more > 0 else "")
                  + ". pfd not yet evaluated." if s.concern != "none" else
                  f"Not raised: {r.drop_reason or s.rule}.")
        calc = CalcTrace(method="none", inputs=[], formula="", result_value=None, result_unit="", limit_value=None,
                         limit_evidence_id=None, margin_db=None,
                         notes=[f"pfd not yet computed (step C1); ranking score {s.score} from scoring/weights.json",
                                f"geography evidence {geo_ev}"])
        findings.append(Finding(
            id="", kind="space", issue=issue, notice_id=n.notice_id, group_id=gid,
            matched_subband_ids=[b.id for b in lanes[:MAX_FINNISH_ROWS]],
            matched_station_numbers=r.matched_station_numbers, overlap_hz=r.overlap_hz,
            geo_relevance=r.geo_relevance if r.geo_relevance in ("visible", "low_elevation", "not_visible", "near_border", "far") else "unknown",
            calc=calc, concern=s.concern, reason=reason, evidence=ev,
        ))
    con.close()

    order = sorted(findings, key=lambda f: (-RK.CONCERN_ORDER[f.concern], -(scores[f.group_id].score if f.group_id else 0), f.notice_id))
    for k, f in enumerate(order, start=1):
        f.id = f"F-{issue}-{k:04d}"
    complete = sum(1 for f in order if f.evidence and all(e.excerpt for e in f.evidence))
    result = AnalysisResult(issue=issue, kind="space", screened=len(order), flagged=sum(1 for f in order if f.concern != "none"),
                            provenance_coverage_pct=round(100 * complete / max(len(order), 1), 1), findings=order)
    return SpaceRun(result, rows, scores, ing)


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
