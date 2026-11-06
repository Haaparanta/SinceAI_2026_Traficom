#!/usr/bin/env python3
"""Steps A1 and A2 of pm_pack/08: check the tools and the raw data before anything else runs.

    python3 scripts/doctor.py tools   # A1: every tool on PATH, native arm64 on Apple silicon
    python3 scripts/doctor.py data    # A2: graded databases, Finnish table, special-interest XLS

Prints one line per check: PASS, FAIL or WAITING (an input a person must still supply).
Exit code 1 on any FAIL; WAITING does not fail.
"""
from __future__ import annotations

import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"

# Exact byte sizes of the extracted databases from the 2026-11-06 download (data/MANIFEST.sha256 holds the hashes).
DATABASES = {
    "ific3074/ific3074.mdb": 286_654_464,
    "brific3075/brific3075.mdb": 32_538_624,
    "brific3076/brific3076.mdb": 25_145_344,
}
FINNISH_TABLE_ROWS = 5917  # [SOURCE DATA] Traficom API v13, 2026-11-06

results: list[tuple[str, str, str]] = []


def report(status: str, name: str, detail: str = "") -> None:
    results.append((status, name, detail))


def run(cmd: list[str]) -> str:
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return (out.stdout or out.stderr).strip().splitlines()[0] if (out.stdout or out.stderr).strip() else ""
    except (OSError, subprocess.TimeoutExpired) as exc:
        return f"error: {exc}"


def check_tools() -> None:
    tools = {
        "uv": ["uv", "--version"],
        "node": ["node", "--version"],
        "npm": ["npm", "--version"],
        "duckdb": ["duckdb", "-no-agent", "--version"],
        "mdb-tables": None,
        "mdb-export": None,
        "mdb-ver": None,
        "gh": ["gh", "--version"],
    }
    apple_silicon = platform.system() == "Darwin" and platform.machine() == "arm64"
    for name, cmd in tools.items():
        path = shutil.which(name)
        if not path:
            report("FAIL", f"tool {name}", "not on PATH (brew install mdbtools duckdb)")
            continue
        detail = run(cmd) if cmd else path
        if apple_silicon and name in {"duckdb", "mdb-tables"}:
            arch = run(["file", "-L", path])
            if "arm64" not in arch:
                report("FAIL", f"tool {name}", f"not a native arm64 build: {arch}")
                continue
        report("PASS", f"tool {name}", detail)


def check_data() -> None:
    if not RAW.exists():
        report("FAIL", "data/raw", "missing; run scripts/fetch_data.sh or link the shared folder (pm_pack/08 step A2)")
        return
    report("PASS", "data/raw", str(RAW.resolve()))

    for rel, size in DATABASES.items():
        path = RAW / rel
        if not path.exists():
            report("FAIL", rel, "missing; unzip the matching zip in data/raw")
            continue
        actual = path.stat().st_size
        if actual != size:
            report("FAIL", rel, f"size {actual} bytes, expected {size}")
            continue
        version = run(["mdb-ver", str(path)]) if shutil.which("mdb-ver") else "mdb-ver missing"
        report("PASS" if version.startswith("JET") else "FAIL", rel, f"{actual:,} bytes, {version}")

    table = RAW / "taajuusjakotaulukko.json"
    try:
        rows = json.loads(table.read_text(encoding="utf-8"))["value"]
        bad = [r["ID"] for r in rows
               if r.get("Sub_band_lower_limit__Hz_") is None or r.get("Sub_band_upper_limit__Hz_") is None]
        status = "PASS" if len(rows) == FINNISH_TABLE_ROWS else "FAIL"
        report(status, "taajuusjakotaulukko.json",
               f"{len(rows)} rows (expected {FINNISH_TABLE_ROWS}), {len(bad)} without Hz limits")
    except (OSError, ValueError, KeyError) as exc:
        report("FAIL", "taajuusjakotaulukko.json", str(exc))

    xls = [p for p in (RAW / "special_interest.xlsx", RAW / "special_interest.xls") if p.exists()]
    if xls:
        report("PASS", "special_interest.xlsx", str(xls[0].name))
    else:
        report("WAITING", "special_interest.xlsx",
               "download by hand from the Since AI platform to data/raw/special_interest.xlsx (step A3)")


def main() -> int:
    what = sys.argv[1:] or ["tools", "data"]
    if "tools" in what:
        check_tools()
    if "data" in what:
        check_data()
    width = max(len(n) for _, n, _ in results)
    for status, name, detail in results:
        print(f"{status:<8} {name:<{width}}  {detail}")
    return 1 if any(s == "FAIL" for s, _, _ in results) else 0


if __name__ == "__main__":
    sys.exit(main())
