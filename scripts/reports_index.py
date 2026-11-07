#!/usr/bin/env python3
"""reports/index.html: one page linking every stage report with its PASS or FAIL status (pm_pack/08 section 4).

    uv run python scripts/reports_index.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend")]

from radar import report_html as R  # noqa: E402
from radar.config import settings  # noqa: E402

STEPS = [
    ("schema/schema_ific3074.html", "A4", "Schema of the Space IFIC 3074 database"),
    ("schema/schema_brific3075.html", "A4", "Schema of the Terrestrial IFIC 3075 database"),
    ("schema/schema_brific3076.html", "A4", "Schema of the Terrestrial IFIC 3076 database"),
    ("convert/space_3074.html", "A5", "Conversion of 3074 to DuckDB"),
    ("convert/terrestrial_3075.html", "A5", "Conversion of 3075 to DuckDB"),
    ("convert/terrestrial_3076.html", "A5", "Conversion of 3076 to DuckDB"),
    ("reference/special_interest.html", "A3", "Special-interest stations: the Traficom table, read and checked"),
    ("reference/fi_subbands.html", "A6", "Finnish frequency table: spectrum strip"),
    ("3074/01_ingest.html", "B1", "Space 3074: notices and groups"),
    ("3074/02_relevance.html", "B2", "Space 3074: frequency relevance"),
    ("3074/03_geography.html", "B3", "Space 3074: geography"),
    ("3074/04_findings.html", "B4", "Space 3074: ranked findings and evidence check"),
    ("3074/05_results.html", "B5", "Space 3074: results files"),
    ("3074/06_pfd.html", "C1", "Space 3074: worst-case pfd"),
    ("3074/08_plans.html", "C1b", "Space 3074: AP30, AP30A and AP30B plans against Finland's plan entries"),
    ("3076/01_diff.html", "C2", "Terrestrial 3075 to 3076: diff"),
    ("3076/02_field_strength.html", "C3", "Terrestrial 3076: border distance and field strength"),
    ("3076/03_broadcasting.html", "C3+", "Terrestrial 3076: FM and TV broadcasting (GE84, GE06)"),
    ("3074/07_explanations.html", "D2", "Space 3074: grounded explanations and letter drafts"),
    ("3076/07_explanations.html", "D2", "Terrestrial 3076: grounded explanations and letter drafts"),
    ("playwright/index.html", "D1", "Playwright end-to-end tests of the screen (make e2e), incl. the offline demo walk (E3)"),
    ("freeze/e1_determinism.html", "E1", "Determinism: two full runs, byte comparison with the committed files"),
    ("freeze/e2_golden.html", "E2", "Case recognition accuracy: golden cases, Bureau-named groups, reviewer decisions"),
]


def status_of(path: Path) -> str:
    summary = path.with_suffix(".summary.json")
    if not path.exists():
        return "WAITING"
    if path.parent.name == "playwright":          # Playwright writes its counts next to the HTML report
        res = path.parent.parent / "playwright-results.json"
        try:
            st = json.loads(res.read_text())["stats"]
        except (OSError, ValueError, KeyError):
            return "UNKNOWN"
        return "FAIL" if st.get("unexpected", 0) or not st.get("expected", 0) else "PASS"
    try:
        s = json.loads(summary.read_text())
    except (OSError, ValueError):
        return "PASS"
    if isinstance(s, dict) and "status" in s:
        return s["status"]
    if isinstance(s, dict) and "failed" in s:          # conversion summaries
        return "FAIL" if s["failed"] else "PASS"
    if isinstance(s, dict) and "expected_missing" in s:  # schema summaries
        return "FAIL" if s["expected_missing"] else "PASS"
    return "PASS"


def build(base: Path, intro: str) -> Path:
    rows = []
    for rel, step, title in STEPS:
        p = base / rel
        st = status_of(p)
        link = f'<a href="{rel}">{R.esc(title)}</a>' if p.exists() else R.esc(title)
        rows.append([step, link, R.badge(st)])
    body = R.table(["Step", "Report", "Status"], rows, raw=True)
    out = base / "index.html"
    out.write_text(R.page("Filing Radar: stage reports", intro, body, "a { color:var(--fg); }"), encoding="utf-8")
    print(f"written {out}")
    return out


def main() -> int:
    build(settings.reports_dir, "Every step of pm_pack/08 with its visual proof. Regenerate a report with its make "
                                "target; this page with <code>uv run python scripts/reports_index.py</code>.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
