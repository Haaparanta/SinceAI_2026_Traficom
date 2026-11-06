#!/usr/bin/env python3
"""Step B5 visual proof: the results files read back from disk and reconciled with the stage reports.

    uv run python scripts/results_report.py 3074      # writes reports/3074/05_results.html and .summary.json

Checks: every file parses against ResultRow; the notice count equals the findings report; the concern counts equal
the concern bars of 04_findings; the group rows equal the candidates after geography (03_geography); CSV and JSON
agree row by row; every row has evidence references; the rows are in concern order.
"""
from __future__ import annotations

import csv
import hashlib
import json
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT)]

from radar import report_html as R  # noqa: E402
from radar.config import settings  # noqa: E402
from radar.export.results import RESULTS_DIR, concern_order_ok  # noqa: E402
from radar.models import ResultRow  # noqa: E402


def read_csv(path: Path) -> list[ResultRow]:
    with path.open(encoding="utf-8", newline="") as fh:
        return [ResultRow(**{k: (None if v == "" else v) for k, v in row.items()}) for row in csv.DictReader(fh)]


def main() -> int:
    issue = int(sys.argv[1]) if len(sys.argv) > 1 else 3074
    files = {k: RESULTS_DIR / f"space_{issue}{suffix}" for k, suffix in (("csv", ".csv"), ("json", ".json"), ("groups", "_groups.csv"))}
    rows = read_csv(files["csv"])
    jrows = [ResultRow(**r) for r in json.loads(files["json"].read_text(encoding="utf-8"))]
    groups = read_csv(files["groups"])
    rep = settings.reports_dir / str(issue)
    f04 = json.loads((rep / "04_findings.summary.json").read_text())
    f03 = json.loads((rep / "03_geography.summary.json").read_text())
    b3_groups = dict(f03["funnel_groups"])["Candidates after geography (B3)"]

    concern = Counter(r.concern for r in rows)
    checks = [
        ("CSV parses as ResultRow", True, f"{len(rows)} rows"),
        ("CSV and JSON hold the same rows", [r.model_dump() for r in rows] == [r.model_dump() for r in jrows], f"{len(jrows)} JSON rows"),
        ("Rows = notices screened in 04_findings", len(rows) == f04["screened"], f"{len(rows)} vs {f04['screened']}"),
        ("Concern counts = 04_findings bars", dict(concern) == f04["concern"], f"{dict(concern)}"),
        ("Group rows = candidates after geography (03_geography)", len(groups) == b3_groups, f"{len(groups)} vs {b3_groups}"),
        ("Every row has evidence references", all(r.evidence_refs for r in rows + groups), ""),
        ("Rows in concern order", concern_order_ok(rows), ""),
        ("No calculated value without its unit", all((r.calc_value is None) == (r.calc_unit is None) for r in rows), "pfd arrives in C1"),
    ]
    status = "PASS" if all(ok for _, ok, _ in checks) else "FAIL"
    sha = {k: hashlib.sha256(p.read_bytes()).hexdigest()[:16] for k, p in files.items()}

    preview = [[r.notice_id, r.concern, r.administration, r.network_or_station, r.special_section or "",
                f"{r.freq_min_mhz:g} to {r.freq_max_mhz:g}" if r.freq_min_mhz is not None else "", r.direction or "",
                r.geo_relevance, (r.finnish_match or "")[:60]] for r in rows[:30]]
    body = (
        R.tiles([("notice rows", str(len(rows))), ("flagged", str(sum(v for k, v in concern.items() if k != "none"))),
                 ("group detail rows", f"{len(groups):,}"), ("pfd", "not yet evaluated (C1)")])
        + "<h2>Reconciliation</h2>" + R.table(["Check", "Status", "Detail"], [[c, R.badge("PASS" if ok else "FAIL"), R.esc(d)] for c, ok, d in checks], raw=True)
        + "<h2>Files</h2>" + R.table(["File", "Bytes", "SHA-256 (first 16)"], [[str(p.relative_to(ROOT)), f"{p.stat().st_size:,}", sha[k]] for k, p in files.items()])
        + "<h2>First 30 rows of the main file</h2><p class='sub'>As a grader opens it: highest concern first.</p>"
        + R.table(["Notice", "Concern", "Adm", "Network or station", "Section", "MHz", "Direction", "Geography", "Finnish match"], preview)
    )
    out = rep / "05_results.html"
    R.write(out, R.page(f"Space IFIC {issue}: results files", f"Step B5 of pm_pack/08. Read back from results/. {R.badge(status)}", body),
            {"status": status, "checks": [[c, ok, d] for c, ok, d in checks], "sha256_16": sha})
    print(f"written {out}: {status}")
    for c, ok, d in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {c}  {d}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
