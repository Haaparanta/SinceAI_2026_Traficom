#!/usr/bin/env python3
"""Step E4 of pm_pack/08: the proof pack. Copies every stage report (and its summary) into results/proof/, which is
committed, and writes results/proof/index.html linking each one with its PASS or FAIL status.

    uv run python scripts/proof_pack.py        # after make index, determinism, golden and e2e

The reports are self-contained HTML (inline SVG, no external links), so the pack opens from disk.
"""
from __future__ import annotations

import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT / "scripts")]

from radar.config import settings  # noqa: E402
from reports_index import STEPS, build, status_of  # noqa: E402

OUT = ROOT / "results" / "proof"


def main() -> int:
    src = settings.reports_dir
    missing = []
    for rel, step, _ in STEPS:
        p = src / rel
        if not p.exists():
            missing.append(f"{step} {rel}")
            continue
        if rel.startswith("playwright/"):
            shutil.rmtree(OUT / "playwright", ignore_errors=True)
            shutil.copytree(p.parent, OUT / "playwright")
            res = src / "playwright-results.json"
            if res.exists():                    # local checkout paths become repository-relative
                text = res.read_text(encoding="utf-8").replace(str(ROOT) + "/", "").replace(str(ROOT), ".")
                (OUT / "playwright-results.json").write_text(text, encoding="utf-8")
            continue
        (OUT / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(p, OUT / rel)
        summary = p.with_suffix(".summary.json")
        if summary.exists():
            shutil.copy2(summary, OUT / rel.replace(".html", ".summary.json"))
    build(OUT, "The proof pack: every stage report of pm_pack/08 as it stood when the results files were frozen. "
               "Copied from <code>reports/</code> by <code>scripts/proof_pack.py</code>; <code>accuracy.csv</code> "
               "holds the precision and recall table. Methods, parameters and assumptions: <a href='../README.md'>results/README.md</a>.")
    failing = [f"{s} {r}" for r, s, _ in STEPS if (OUT / r).exists() and status_of(OUT / r) == "FAIL"]
    for m in missing:
        print(f"  WAITING  {m}")
    for f in failing:
        print(f"  FAIL     {f}")
    print(f"proof pack: {len(STEPS) - len(missing)} of {len(STEPS)} reports, {len(failing)} failing")
    return 1 if missing or failing else 0


if __name__ == "__main__":
    raise SystemExit(main())
