"""Evidence resolver (pm_pack/08 section 2): reopen every Evidence.locator and require the excerpt to match.

* itu_row:           query the DuckDB table with the locator keys, rebuild the excerpt for the same fields.
* finnish_table_row: rebuild the excerpt from the Traficom snapshot by ID.
* calculation:       re-run the geography for the issue and compare "<relevance>: <note>".
* regulation:        not produced yet; reported as unchecked.

    uv run python -m radar.evidence_check 3074          # exit 1 on any mismatch
"""
from __future__ import annotations

import sys
from collections import Counter
from dataclasses import dataclass

import duckdb

from radar.adapters import space_ific, traficom_table
from radar.evidence import parse_excerpt, parse_locator, row_excerpt
from radar.models import AnalysisResult
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
    issue = result.issue
    con = duckdb.connect(str(space_ific.db_path(issue)), read_only=True)
    bands = {b.id: b for b in traficom_table.load_json()}
    geo = None
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
            elif e.kind == "calculation" and e.locator.startswith("geography("):
                if geo is None:
                    geo = G.for_issue(space_ific.load(issue).notices, con)
                key, val = e.locator[len("geography("):-1].split("=", 1)
                g = geo.by_group.get(val) if key == "group_id" else geo.by_notice.get(val)
                found = f"{g.relevance}: {g.note}" if g else None
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
