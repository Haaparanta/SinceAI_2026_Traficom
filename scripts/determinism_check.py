#!/usr/bin/env python3
"""Step E1 of pm_pack/08: run the whole 3074 and 3076 pipeline twice and compare every output byte for byte.

    uv run python scripts/determinism_check.py      # writes reports/freeze/e1_determinism.html and .summary.json

Each run is a fresh process chain from the DuckDB databases: assemble (findings), results export for space and
terrestrial, and the screen cache. After each run every output file is hashed. PASS when run 1 equals run 2 and
both equal the files committed in git (so what a grader downloads is what the code produces).
"""
from __future__ import annotations

import hashlib
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend")]

from radar import report_html as R  # noqa: E402
from radar.config import settings  # noqa: E402

PY = ["uv", "run", "python"]
ENV = {"PYTHONPATH": f"{ROOT / 'backend'}:{ROOT}", "LLM_DISABLED": "1"}
STEPS = [
    PY + ["scripts/findings_report.py", "3074"],
    PY + ["-m", "radar.export", "--issue", "3074", "--kind", "space"],
    PY + ["-m", "radar.export", "--issue", "3076", "--kind", "terrestrial"],
    PY + ["scripts/build_cache.py"],
]
OUTPUTS = ["results/space_3074.csv", "results/space_3074.json", "results/space_3074_groups.csv",
           "results/terrestrial_3076.csv", "results/terrestrial_3076.json",
           "data/cache/space_3074.json", "data/cache/terrestrial_3076.json"]


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def committed(rel: str) -> str | None:
    r = subprocess.run(["git", "show", f"HEAD:{rel}"], cwd=ROOT, capture_output=True)
    return hashlib.sha256(r.stdout).hexdigest() if r.returncode == 0 else None


def run_once() -> tuple[dict[str, str], float]:
    import os
    t0 = time.time()
    for cmd in STEPS:
        subprocess.run(cmd, cwd=ROOT, env={**os.environ, **ENV}, check=True, capture_output=True)
    return {rel: sha(ROOT / rel) for rel in OUTPUTS}, time.time() - t0


def main() -> int:
    (r1, t1), (r2, t2) = run_once(), run_once()
    git = {rel: committed(rel) for rel in OUTPUTS}
    rows, all_ok = [], True
    for rel in OUTPUTS:
        same = r1[rel] == r2[rel]
        in_git = git[rel] == r1[rel]
        all_ok &= same and in_git
        rows.append([rel, f"{(ROOT / rel).stat().st_size:,}", r1[rel][:16], r2[rel][:16],
                     R.badge("PASS" if same else "FAIL"), R.badge("PASS" if in_git else "FAIL")])
    status = "PASS" if all_ok else "FAIL"
    body = (R.tiles([("output files", str(len(OUTPUTS))), ("identical", f"{sum(r1[k] == r2[k] for k in OUTPUTS)} of {len(OUTPUTS)}"),
                     ("run 1", f"{t1:.0f} s"), ("run 2", f"{t2:.0f} s")])
            + "<h2>Steps of each run</h2>" + R.table(["#", "Command"], [[str(i + 1), " ".join(c)] for i, c in enumerate(STEPS)])
            + "<h2>Outputs</h2><p class='sub'>SHA-256, first 16 hex digits. Committed: the file in git HEAD has the same hash.</p>"
            + R.table(["File", "Bytes", "Run 1", "Run 2", "Run 1 = run 2", "= committed"], rows, raw=True))
    out = settings.reports_dir / "freeze" / "e1_determinism.html"
    R.write(out, R.page("Determinism: two full runs", f"Step E1 of pm_pack/08. Space 3074 and terrestrial 3076 from DuckDB. {R.badge(status)}", body),
            {"status": status, "sha256": r1, "seconds": [round(t1, 1), round(t2, 1)]})
    print(f"written {out}: {status}")
    for r in rows:
        print(f"  {r[0]}  {r[2]}  {'same' if r1[r[0]] == r2[r[0]] else 'DIFFERENT'}  {'= git' if git[r[0]] == r1[r[0]] else '!= git'}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
