#!/usr/bin/env python3
"""make status: one line per build step of pm_pack/08, PASS, FAIL or WAITING (pm_pack/08 section 4).

Reads the stage report summaries in reports/ (rebuild them with their make targets) and the inputs still missing.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "scripts")]

from radar.config import settings  # noqa: E402
from reports_index import STEPS, build, status_of  # noqa: E402

INPUTS = [("A3", "data/raw/special_interest.xlsx", "special-interest station table from the Since AI platform")]


def main() -> int:
    worst = 0
    for step, rel, what in INPUTS:
        if not (ROOT / rel).exists():
            print(f"{step:3} WAITING  {what}: {rel} not found")
    for rel, step, title in STEPS:
        st = status_of(settings.reports_dir / rel)
        worst = max(worst, {"PASS": 0, "WAITING": 0, "FAIL": 1}.get(st, 0))
        print(f"{step:3} {st:8} {title}")
    build(settings.reports_dir, "Every step of pm_pack/08 with its visual proof. Regenerate a report with its make "
                                "target; this page with <code>make status</code>.")
    return worst


if __name__ == "__main__":
    raise SystemExit(main())
