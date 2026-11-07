"""Step B5 of pm_pack/08: the graded results files.

    uv run python -m radar.export --issue 3074 --kind space

writes
    results/space_3074.csv, results/space_3074.json          one ResultRow per screened notice (the main file)
    results/space_3074_groups.csv                             one ResultRow per candidate group (detail, Q3 open)

Rows come from the same run as the findings report, so counts match the funnel and the concern bars.
Output is deterministic: same inputs, byte-identical files (tested). No timestamps inside the files.
"""
from __future__ import annotations

import csv
import io
import json
from pathlib import Path

from radar.config import ROOT
from radar.calc import pfd as PFD
from radar.models import ResultRow
from radar.pipeline import assemble
from radar.pipeline import rank as RK

RESULTS_DIR = ROOT / "results"
COLUMNS = list(ResultRow.model_fields)
DIRECTION_TEXT = assemble.DIRECTION_TEXT


def _mhz(hz: int | None) -> float | None:
    return None if hz is None else round(hz / 1e6, 6)


def _finnish_match(ids: list[int], bands: dict) -> str | None:
    if not ids:
        return None
    services = []
    for i in ids:
        s = bands[i].services_in_finland
        if s not in services:
            services.append(s)
    return f"{'; '.join(services)} (IDs {', '.join(str(i) for i in ids)})"


def _plan_match(r) -> str | None:
    """Finnish plan entries behind a group's plan rule, e.g. 'plan: AP30 FIN10300 (22.8 E, 2.10 deg)'."""
    if r is None:
        return None
    bits = [f"{h.entry.plan} {h.entry.satellite} ({h.entry.longitude_deg:g} E, {h.worst_deg:.2f} deg)" for h in r.plan_hits[:2]]
    bits += [f"{b.db} {b.finnish_satellite} (Bureau: {b.summary()})" for b in r.plan_bureau[:2]]
    return f"plan: {'; '.join(bits)}" if bits else None


def _join(*parts) -> str | None:
    parts = [p for p in parts if p]
    return "; ".join(parts) if parts else None


def plan_notice_row(f, pn) -> ResultRow:
    lo = min((g.lo_hz for g in pn.groups), default=None)
    hi = max((g.hi_hz for g in pn.groups), default=None)
    dirs = sorted({DIRECTION_TEXT[g.direction] for g in pn.groups if g.direction in DIRECTION_TEXT})
    return ResultRow(
        issue=f.issue, kind=f.kind, notice_id=f.notice_id,
        special_section=", ".join(pn.sections) or f"{pn.db} {pn.provision or ''}".strip(),
        administration=pn.administration, network_or_station=pn.satellite or "unknown",
        freq_min_mhz=_mhz(lo), freq_max_mhz=_mhz(hi), direction=" and ".join(dirs) or None,
        finnish_match=None, special_interest_station_ids=None, overlap_mhz=None, geo_relevance=f.geo_relevance,
        calc_method=f.calc.method, calc_value=None, calc_unit=None, limit_value=None, margin_db=None,
        concern=f.concern, reason=f.reason, evidence_refs="; ".join(e.locator for e in f.evidence), decision=None)


def notice_rows(run: assemble.SpaceRun, bands: dict) -> list[ResultRow]:
    by_notice = {n.notice_id: n for n in run.ingest.notices}
    rows_by_group = {r.group_id: r for r in run.rows}
    plan_notices = run.plan_notices or {}
    out = []
    for f in run.result.findings:
        if f.notice_id in plan_notices and f.notice_id not in by_notice:
            out.append(plan_notice_row(f, plan_notices[f.notice_id]))
            continue
        n = by_notice[f.notice_id]
        r = rows_by_group.get(f.group_id) if f.group_id else None
        out.append(ResultRow(
            issue=f.issue, kind=f.kind, notice_id=f.notice_id, special_section=n.special_section,
            administration=n.administration, network_or_station=n.network_name,
            freq_min_mhz=_mhz(r.freq_min_hz) if r else None, freq_max_mhz=_mhz(r.freq_max_hz) if r else None,
            direction=DIRECTION_TEXT[r.direction] if r else None,
            finnish_match=_join(_finnish_match(f.matched_subband_ids, bands), _plan_match(r)),
            special_interest_station_ids=", ".join(f.matched_station_numbers) or None,
            overlap_mhz=_mhz(f.overlap_hz) if r else None, geo_relevance=f.geo_relevance,
            calc_method=f.calc.method, calc_value=f.calc.result_value, calc_unit=f.calc.result_unit or None,
            limit_value=f.calc.limit_value, margin_db=f.calc.margin_db, concern=f.concern, reason=f.reason,
            evidence_refs="; ".join(e.locator for e in f.evidence), decision=None,
        ))
    return out


def _pfd_columns(res) -> dict:
    if res is None or res.status != "computed":
        return {"calc_method": "pfd_gso_worst_case" if res is not None else "none", "calc_value": None, "calc_unit": None,
                "limit_value": None, "margin_db": None}
    return {"calc_method": "pfd_gso_worst_case", "calc_value": res.pfd_db,
            "calc_unit": f"dB(W/m2) in {PFD.fmt_bw(res.worst['bandwidth_hz'])}", "limit_value": res.limit_db, "margin_db": res.margin_db}


def group_rows(run: assemble.SpaceRun, bands: dict) -> list[ResultRow]:
    by_notice = {n.notice_id: n for n in run.ingest.notices}
    out = []
    for r in sorted((r for r in run.rows if r.candidate), key=lambda r: (r.notice_id, r.group_id)):
        n = by_notice[r.notice_id]
        s = run.scores[r.group_id]
        ids = sorted({i for p in r.paths.values() for i in p}) or r.matched_subband_ids
        refs = [f"grp.grp_id={r.group_id}"] + [f"Taajuusjakotaulukko.ID={i}" for i in ids[:assemble.MAX_FINNISH_ROWS]] + \
               [f"provn.grp_id={r.group_id}&adm=FIN&coord_prov={p}" for p in r.finland_named_provisions] + \
               [h.entry.group_locator for h in r.plan_hits[:2]] + [b.locator for b in r.plan_bureau[:2]]
        out.append(ResultRow(
            issue=run.result.issue, kind="space", notice_id=r.notice_id, special_section=n.special_section,
            administration=n.administration, network_or_station=n.network_name,
            freq_min_mhz=_mhz(r.freq_min_hz), freq_max_mhz=_mhz(r.freq_max_hz), direction=DIRECTION_TEXT[r.direction],
            finnish_match=_join(_finnish_match(ids[:assemble.MAX_FINNISH_ROWS], bands), _plan_match(r)), special_interest_station_ids=", ".join(r.matched_station_numbers) or None,
            overlap_mhz=_mhz(r.overlap_hz), geo_relevance=r.geo_relevance if r.geo_relevance != "unknown" else "unknown",
            **_pfd_columns((run.pfd or {}).get(r.group_id)),
            concern=s.concern, reason=f"{s.rule}; paths: {', '.join(sorted(r.paths))}; score {s.score}",
            evidence_refs="; ".join(refs), decision=None,
        ))
    return out


PLAN_COLUMNS = ["row", "plan", "finnish_satellite", "finnish_longitude_deg", "freq_min_mhz", "freq_max_mhz", "direction",
                "network", "administration", "network_longitude_deg", "provision", "published_ific", "pfd_excess_db",
                "degradation_db", "evidence_ref"]


def plan_watch_rows(snaps: dict) -> list[dict]:
    """Finland's plan entries and every network the Bureau found affecting them (not tied to one issue)."""
    from radar.adapters import plans as PLANS

    if not snaps:
        return []
    out = []
    for e in PLANS.finnish_entries(snaps=snaps):
        out.append({"row": "finnish_entry", "plan": e.plan, "finnish_satellite": e.satellite,
                    "finnish_longitude_deg": e.longitude_deg, "freq_min_mhz": _mhz(e.lo_hz), "freq_max_mhz": _mhz(e.hi_hz),
                    "direction": DIRECTION_TEXT[e.direction], "evidence_ref": e.group_locator})
    for b in PLANS.bureau_effects(snaps=snaps):
        out.append({"row": "bureau_effect", "plan": b.db, "finnish_satellite": b.finnish_satellite, "network": b.satellite,
                    "administration": b.administration, "network_longitude_deg": b.longitude_deg, "provision": b.provision,
                    "published_ific": b.ific_no, "pfd_excess_db": b.pfd_excess_db,
                    "degradation_db": None if b.degradation_db is None else round(b.degradation_db, 3), "evidence_ref": b.locator})
    return out


def dicts_to_csv(rows: list[dict], columns: list[str]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=columns, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if r.get(k) is None else r.get(k)) for k in columns})
    return buf.getvalue()


def to_csv(rows: list[ResultRow]) -> str:
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=COLUMNS, lineterminator="\n")
    w.writeheader()
    for r in rows:
        w.writerow({k: ("" if v is None else v) for k, v in r.model_dump().items()})
    return buf.getvalue()


def to_json(rows: list[ResultRow]) -> str:
    return json.dumps([r.model_dump() for r in rows], indent=1, ensure_ascii=False) + "\n"


def export_space(issue: int, out_dir: Path = RESULTS_DIR) -> dict:
    from radar.adapters import traficom_table

    run = assemble.run(issue)
    bands = {b.id: b for b in traficom_table.subbands()}
    main_rows, detail = notice_rows(run, bands), group_rows(run, bands)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "csv": out_dir / f"space_{issue}.csv",
        "json": out_dir / f"space_{issue}.json",
        "groups_csv": out_dir / f"space_{issue}_groups.csv",
        "plans_csv": out_dir / "plans_finland.csv",
    }
    paths["csv"].write_text(to_csv(main_rows), encoding="utf-8")
    paths["json"].write_text(to_json(main_rows), encoding="utf-8")
    paths["groups_csv"].write_text(to_csv(detail), encoding="utf-8")
    watch = plan_watch_rows(run.plan_snapshots or {})
    if watch:
        paths["plans_csv"].write_text(dicts_to_csv(watch, PLAN_COLUMNS), encoding="utf-8")
    else:
        paths.pop("plans_csv")
    from collections import Counter
    return {"paths": {k: str(v) for k, v in paths.items()}, "rows": len(main_rows), "group_rows": len(detail),
            "concern": dict(Counter(r.concern for r in main_rows)),
            "group_concern": dict(Counter(r.concern for r in detail)),
            "run": run}


def concern_order_ok(rows: list[ResultRow]) -> bool:
    order = [RK.CONCERN_ORDER[r.concern] for r in rows]
    return order == sorted(order, reverse=True)


# ---- terrestrial (step C3) --------------------------------------------------------------------------------------

def terrestrial_rows(run) -> list[ResultRow]:
    by_id = {n.notice_id: n for n in run.ingest.notices}
    out = []
    for f in run.result.findings:
        n = by_id[f.notice_id]
        c = run.calcs[f.notice_id]
        e = run.ingest.extra[f.notice_id]
        out.append(ResultRow(
            issue=f.issue, kind="terrestrial", notice_id=f.notice_id, special_section=e.notice_type,
            administration=n.administration, network_or_station=n.site_name or (f"zone {e.zone_id}" if e.zone_id else "unknown"),
            freq_min_mhz=None if n.freq_hz is None else round((n.freq_hz - (n.bandwidth_hz or 0) / 2) / 1e6, 6),
            freq_max_mhz=None if n.freq_hz is None else round((n.freq_hz + (n.bandwidth_hz or 0) / 2) / 1e6, 6),
            direction=n.change, finnish_match=None, special_interest_station_ids=None, overlap_mhz=None,
            geo_relevance=f.geo_relevance, calc_method=f.calc.method,
            calc_value=f.calc.result_value, calc_unit=f.calc.result_unit or None, limit_value=f.calc.limit_value,
            margin_db=f.calc.margin_db, concern=f.concern, reason=f.reason,
            evidence_refs="; ".join(ev.locator for ev in f.evidence), decision=None,
        ))
    return out


def export_terrestrial(issue: int, out_dir: Path = RESULTS_DIR) -> dict:
    from collections import Counter

    from radar.pipeline import terrestrial as TR

    run = TR.run(issue)
    rows = terrestrial_rows(run)
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {"csv": out_dir / f"terrestrial_{issue}.csv", "json": out_dir / f"terrestrial_{issue}.json"}
    paths["csv"].write_text(to_csv(rows), encoding="utf-8")
    paths["json"].write_text(to_json(rows), encoding="utf-8")
    return {"paths": {k: str(v) for k, v in paths.items()}, "rows": len(rows),
            "concern": dict(Counter(r.concern for r in rows)), "run": run}
