#!/usr/bin/env python3
"""Print every table, its row count and its columns from one or more Access .mdb files.

Usage:
    python3 scripts/inspect_mdb.py data/raw/ific3074/*.mdb [--out data/derived/schema_3074.json]

Needs mdbtools on PATH (macOS: brew install mdbtools; Debian/Ubuntu: apt install mdbtools).
The output is the ground truth for backend/radar/schema_map.yaml; nothing in the pipeline may
hard-code a table or column name that this script has not shown.
"""
from __future__ import annotations

import argparse
import csv
import json
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str], timeout: int = 600) -> str:
    try:
        return subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=timeout).stdout
    except subprocess.CalledProcessError as exc:
        sys.stderr.write(f"warning: {' '.join(cmd)} failed: {exc.stderr.strip()}\n")
        return ""
    except subprocess.TimeoutExpired:
        sys.stderr.write(f"warning: {' '.join(cmd)} timed out\n")
        return ""


csv.field_size_limit(1 << 30)  # some SNS memo fields exceed the 128 KB default


def inspect(path: Path, sample_rows: int = 3) -> dict:
    """Stream every table through the csv module, so quoted line breaks do not inflate the row count."""
    tables = [t for t in run(["mdb-tables", "-1", str(path)]).split("\n") if t.strip()]
    result = {"file": str(path), "tables": {}}
    for table in tables:
        proc = subprocess.Popen(["mdb-export", "-D", "%Y-%m-%d", "-T", "%Y-%m-%d %H:%M:%S", "-b", "strip", str(path), table],
                                stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, errors="replace")
        reader = csv.reader(proc.stdout)
        columns = next(reader, [])
        rows, samples = 0, []
        for row in reader:
            rows += 1
            if len(samples) < sample_rows:
                samples.append(row)
        proc.wait()
        if proc.returncode:
            sys.stderr.write(f"warning: mdb-export {table} exited {proc.returncode}: {proc.stderr.read().strip()}\n")
        result["tables"][table] = {"rows": rows, "columns": columns, "sample": samples}
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("files", nargs="+", type=Path, help=".mdb files to inspect")
    parser.add_argument("--out", type=Path, help="write the full listing as JSON to this path")
    args = parser.parse_args()

    if shutil.which("mdb-tables") is None or shutil.which("mdb-export") is None:
        sys.stderr.write("mdbtools not found. macOS: brew install mdbtools. Debian/Ubuntu: sudo apt install mdbtools.\n"
                         "Fallback: ask the partner for CSV extracts (question Q13) or use a Windows machine with Access.\n")
        return 2

    listing = []
    for path in args.files:
        if not path.exists():
            sys.stderr.write(f"missing: {path}\n")
            continue
        info = inspect(path)
        listing.append(info)
        print(f"\n=== {path} : {len(info['tables'])} tables")
        for name, meta in sorted(info["tables"].items(), key=lambda kv: -kv[1]["rows"]):
            cols = ", ".join(meta["columns"][:12]) + (" ..." if len(meta["columns"]) > 12 else "")
            print(f"{name:28s} rows={meta['rows']:>9}  columns={len(meta['columns']):>3}  {cols}")

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(json.dumps(listing, indent=2), encoding="utf-8")
        print(f"\nwritten {args.out}")
    return 0 if listing else 1


if __name__ == "__main__":
    raise SystemExit(main())
