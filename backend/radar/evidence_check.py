"""Evidence resolver (pm_pack/08 section 2): reopen every Evidence.locator and require the excerpt to match.

* itu_row:           query the DuckDB table with the locator keys, rebuild the excerpt for the same fields.
* finnish_table_row: rebuild the excerpt from the Traficom snapshot by ID.
* calculation:       re-run the geography or the pfd for the group and compare the excerpt.
* regulation:        rebuild the excerpt from data/reference/pfd_limits.csv (the RR Table 21-4 transcription) or
                     data/reference/plan_arcs.csv (the AP30/30A/30B orbital arcs), or for Regulation M4 from the Traficom
                     snapshot row it names.
* plan rows:         a locator prefixed with a plan database tag (SPS_ALL_IFIC3083:grp.grp_id=3412) is reopened in
                     that database; plan_arc(...) recomputes the orbital spacing; geography(plan:...) the GSO look angles.

    uv run python -m radar.evidence_check 3074          # exit 1 on any mismatch
"""
from __future__ import annotations

import sys
from collections import Counter
from dataclasses import dataclass

import duckdb

from radar import schema_map
from radar.adapters import plans as PLANS
from radar.adapters import space_ific, traficom_table
from radar.adapters import special_interest as SI
from radar.evidence import parse_excerpt, parse_locator, row_excerpt
from radar.models import AnalysisResult
from radar.calc import pfd as PFD
from radar.pipeline import geography as G


@dataclass
class Check:
    finding_id: str
    evidence_id: str
    kind: str
    locator: str
    status: str            # PASS | FAIL | UNCHECKED
    expected: str
    found: str | None


def check(result: AnalysisResult) -> list[Check]:
    if result.kind == "terrestrial":
        return check_terrestrial(result)
    issue = result.issue
    con = duckdb.connect(str(space_ific.db_path(issue)), read_only=True)
    bands = {b.id: b for b in traficom_table.load_json()}
    geo = None
    ingest = None
    plan_cons: dict[str, duckdb.DuckDBPyConnection] = {}

    def plan_con(t: str):
        if t not in plan_cons:
            db = PLANS.db_for_tag(t)
            plan_cons[t] = PLANS.connect(*db) if db else None
        return plan_cons[t]

    out: list[Check] = []
    for f in result.findings:
        for e in f.evidence:
            found = None
            if e.kind == "itu_row":
                table, keys = parse_locator(e.locator)
                c = con
                if ":" in table:
                    t, table = table.split(":", 1)
                    c = plan_con(t)
                found = row_excerpt(c, table, keys, parse_excerpt(e.excerpt)) if c is not None else None
            elif e.kind == "regulation" and e.locator.startswith("plan_arcs.csv id="):
                a = PLANS.arc_by_id(e.locator.split("=", 1)[1])
                found = a.excerpt() if a else None
            elif e.kind == "calculation" and e.locator.startswith("plan_arc("):
                found = _plan_arc(e.locator, con, plan_con)
            elif e.kind == "calculation" and e.locator.startswith("geography(plan:"):
                t, rest = e.locator[len("geography(plan:"):-1].split(":", 1)
                c = plan_con(t)
                M = schema_map.load()
                row = c.execute(f"SELECT {M.q('plans','gso','longitude_deg')} FROM {M.t('plans','gso')} "
                                f"WHERE CAST({M.q('plans','gso','notice_id')} AS VARCHAR) = ?", [rest.split("=", 1)[1]]).fetchone() if c else None
                lon = None if row is None or row[0] is None else round(float(row[0]), 4)
                g = G.gso_result(lon)
                found = f"{g.relevance}: {g.note}"
            elif e.kind == "special_interest_row":
                st = SI.by_row().get(int(e.locator.split("=", 1)[1]))
                found = SI.excerpt(st) if st else None
            elif e.kind == "finnish_table_row":
                bid = int(e.locator.split("=", 1)[1])
                found = traficom_table.evidence(bands[bid], e.id).excerpt if bid in bands else None
            elif e.kind == "regulation" and e.locator.startswith(traficom_table.M4_LOCATOR_PREFIX):
                bid = int(e.locator[len(traficom_table.M4_LOCATOR_PREFIX):])
                found = traficom_table.m4_evidence(bands[bid], e.id).excerpt if bid in bands else None
            elif e.kind == "regulation" and e.locator.startswith("pfd_limits.csv id="):
                rid = e.locator.split("=", 1)[1]
                row = next((r for r in PFD.limits() if r.id == rid), None)
                found = row.excerpt() if row else None
            elif e.kind == "calculation" and e.locator.startswith("pfd("):
                gid = e.locator[len("pfd(group_id="):-1]
                if ingest is None:
                    ingest = space_ific.load(issue)
                g = next((g for n in ingest.notices for g in n.groups if g.group_id == gid), None)
                n = next((n for n in ingest.notices if g and n.notice_id == g.notice_id), None)
                gi = PFD.load_inputs(con, [gid]).get(gid)
                if g and n and gi:
                    r = PFD.worst_case(g.freq_min_hz, g.freq_max_hz, n.longitude_deg, gi.emissions, gi.gain_dbi, gi.steerable,
                                       extra_points=G.station_points(f.matched_station_numbers, n.longitude_deg, list(SI.stations())))
                    w = r.worst
                    found = (f"pfd {r.pfd_db:.2f} dB(W/m2) in {PFD.fmt_bw(w['bandwidth_hz'])} at {w['point']}; "
                             f"limit {r.limit_db:.2f}; margin {r.margin_db:.2f} dB") if r.status == "computed" else r.status
            elif e.kind == "calculation" and e.locator.startswith("geography("):
                if geo is None:
                    if ingest is None:
                        ingest = space_ific.load(issue)
                    geo = G.for_issue(ingest.notices, con)
                key, val = e.locator[len("geography("):-1].split("=", 1)
                g = geo.by_group.get(val) if key == "group_id" else geo.by_notice.get(val)
                found = f"{g.relevance}: {g.note}" if g else None
            else:
                out.append(Check(f.id, e.id, e.kind, e.locator, "UNCHECKED", e.excerpt, None))
                continue
            out.append(Check(f.id, e.id, e.kind, e.locator, "PASS" if found == e.excerpt else "FAIL", e.excerpt, found))
    con.close()
    for c in plan_cons.values():
        if c is not None:
            c.close()
    return out


def _plan_arc(loc: str, con, plan_con) -> str | None:
    """plan_arc(<origin>:notice_id=<id>&entry=<tag>:<group_id>&arc=<arc id>): recompute the spacing from both rows."""
    from radar.pipeline import plans as PL

    origin, rest = loc[len("plan_arc("):-1].split(":", 1)
    parts = dict(p.split("=", 1) for p in rest.split("&"))
    etag, egid = parts["entry"].split(":", 1)
    db = PLANS.db_for_tag(etag)
    if db is None:
        return None
    entry = next((x for x in PLANS.finnish_entries(snaps={db[0]: db[1]})
                  if x.group_id == egid and x.arc.id == parts["arc"]), None)
    M = schema_map.load()
    kind, c = ("space", con) if origin.startswith("ific") else ("plans", plan_con(origin))
    if entry is None or c is None:
        return None
    row = c.execute(f"SELECT {M.q(kind,'gso','longitude_deg')}, {M.q(kind,'gso','tolerance_east_deg')}, {M.q(kind,'gso','tolerance_west_deg')} "
                    f"FROM {M.t(kind,'gso')} WHERE CAST({M.q(kind,'gso','notice_id')} AS VARCHAR) = ?", [parts["notice_id"]]).fetchone()
    if row is None or row[0] is None:
        return None
    return PL.arc_excerpt(entry, round(float(row[0]), 4), row[1], row[2])


def check_terrestrial(result: AnalysisResult) -> list[Check]:
    """itu_row in the terrestrial DuckDB; border and p1546 recomputed; T/R 25-08 row rebuilt from the CSV; Finnish table
    rows and Regulation M4 rebuilt from the Traficom snapshot."""
    from radar.adapters import terrestrial_ific as TI
    from radar.pipeline import terrestrial as TR

    con = duckdb.connect(str(TI.db_path(result.issue)), read_only=True)
    bands = {b.id: b for b in traficom_table.load_json()}
    ing = TI.load(result.issue, con)
    by_id = {n.notice_id: n for n in ing.notices}
    cache: dict[str, TR.TerrestrialCalc] = {}

    def calc(nid: str) -> TR.TerrestrialCalc:
        if nid not in cache:
            cache[nid] = TR.evaluate(by_id[nid], ing.extra[nid])
        return cache[nid]

    out: list[Check] = []
    for f in result.findings:
        for e in f.evidence:
            found = None
            if e.kind == "itu_row":
                table, keys = parse_locator(e.locator)
                found = row_excerpt(con, table, keys, parse_excerpt(e.excerpt))
            elif e.kind == "finnish_table_row":
                bid = int(e.locator.split("=", 1)[1])
                found = traficom_table.evidence(bands[bid], e.id).excerpt if bid in bands else None
            elif e.kind == "regulation" and e.locator.startswith(traficom_table.M4_LOCATOR_PREFIX):
                bid = int(e.locator[len(traficom_table.M4_LOCATOR_PREFIX):])
                found = traficom_table.m4_evidence(bands[bid], e.id).excerpt if bid in bands else None
            elif e.kind == "regulation" and e.locator.startswith("tr2508_thresholds.csv id="):
                rid = e.locator.split("=", 1)[1]
                row = next((t for t in TR.thresholds() if t.id == rid), None)
                found = row.excerpt() if row else None
            elif e.kind == "calculation" and e.locator.startswith("border("):
                c = calc(e.locator[len("border(notice_id="):-1])
                found = TR.border_excerpt(c) if c.status == "computed" else c.status
            elif e.kind == "special_interest_row":
                st = SI.by_row().get(int(e.locator.split("=", 1)[1]))
                found = SI.excerpt(st) if st else None
            elif e.kind == "calculation" and e.locator.startswith("p1546_station("):
                nid, num = e.locator[len("p1546_station(notice_id="):-1].split(";station=")
                w = next((s for s in calc(nid).stations if s["number"] == num), None)
                found = TR.station_excerpt(w) if w else None
            elif e.kind == "calculation" and e.locator.startswith("p1546("):
                c = calc(e.locator[len("p1546(notice_id="):-1])
                found = f"E {c.e_dbuv_m:.2f} dB(uV/m); free space {c.free_space_dbuv_m:.2f}" if c.status == "computed" else c.status
            else:
                out.append(Check(f.id, e.id, e.kind, e.locator, "UNCHECKED", e.excerpt, None))
                continue
            out.append(Check(f.id, e.id, e.kind, e.locator, "PASS" if found == e.excerpt else "FAIL", e.excerpt, found))
    con.close()
    return out


def main() -> int:
    from radar.config import settings

    issue = int(sys.argv[1]) if len(sys.argv) > 1 else 3074
    path = settings.derived_dir / f"findings_space_{issue}.json"
    result = AnalysisResult.model_validate_json(path.read_text(encoding="utf-8"))
    checks = check(result)
    c = Counter((x.kind, x.status) for x in checks)
    for (kind, status), n in sorted(c.items()):
        print(f"{status:<9} {kind:<18} {n:>6,}")
    fails = [x for x in checks if x.status == "FAIL"]
    for x in fails[:20]:
        print(f"FAIL {x.finding_id} {x.evidence_id} {x.locator}\n  expected {x.expected}\n  found    {x.found}")
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
