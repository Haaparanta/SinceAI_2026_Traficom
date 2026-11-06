#!/usr/bin/env python3
"""Step A5 of pm_pack/08: convert one ITU .mdb into a DuckDB file, keeping every table and column name.

    uv run python scripts/mdb_to_duckdb.py data/raw/ific3074/ific3074.mdb data/derived/space_3074.duckdb

How it works
* Column types come from the Access schema (mdb-schema), not from guessing, so codes with leading zeros stay
  text and Single floats stay 4-byte (27.3, not 27.299999).
* Each table is streamed with mdb-export to a temporary CSV and loaded with DuckDB read_csv.
* Every table gets a `_row` column (1-based export order), so evidence can cite a row even in tables
  without a key.
* Row counts are compared with a csv-module count of the same export; any difference fails the run.
* Writes reports/convert/<db>.html and .summary.json (the visual proof and the test input).

Renaming to our names happens later, through backend/radar/schema_map.yaml.
"""
from __future__ import annotations

import argparse
import csv
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import duckdb  # noqa: E402

from radar import report_html as R  # noqa: E402
from radar.config import settings  # noqa: E402

csv.field_size_limit(1 << 30)

ACCESS_TO_DUCKDB = {
    "text": "VARCHAR", "memo": "VARCHAR", "memo/hyperlink": "VARCHAR", "hyperlink": "VARCHAR",
    "byte": "BIGINT", "integer": "BIGINT", "long integer": "BIGINT",
    "single": "FLOAT", "double": "DOUBLE", "currency": "DOUBLE", "numeric": "DOUBLE",
    "datetime": "TIMESTAMP", "boolean": "BOOLEAN", "replication id": "VARCHAR", "ole": "BLOB",
}
COL_RE = re.compile(r"^\s*\[(?P<name>[^\]]+)\]\s+(?P<type>[A-Za-z/ ]+?)(\s*\(\d+\))?(\s+NOT NULL)?\s*,?\s*$")


def access_schema(mdb: Path) -> dict[str, list[tuple[str, str, str]]]:
    """table -> [(column, access_type, duckdb_type)] in file order."""
    text = subprocess.run(["mdb-schema", str(mdb)], capture_output=True, text=True, check=True).stdout
    tables: dict[str, list[tuple[str, str, str]]] = {}
    current = None
    for line in text.splitlines():
        if line.startswith("CREATE TABLE"):
            current = line.split("[", 1)[1].split("]", 1)[0]
            tables[current] = []
        elif current and (m := COL_RE.match(line)):
            access = m["type"].strip()
            tables[current].append((m["name"], access, ACCESS_TO_DUCKDB.get(access.lower(), "VARCHAR")))
        elif line.startswith(");"):
            current = None
    return tables


def export_table(mdb: Path, table: str, out: Path) -> int:
    """Export with ISO dates; return the data-row count using the csv module."""
    with out.open("w", encoding="utf-8", newline="") as fh:
        subprocess.run(["mdb-export", "-D", "%Y-%m-%d", "-T", "%Y-%m-%d %H:%M:%S", "-b", "strip", str(mdb), table],
                       stdout=fh, check=True, text=True)
    with out.open(encoding="utf-8", newline="") as fh:
        return sum(1 for _ in csv.reader(fh)) - 1


def convert(mdb: Path, db_path: Path) -> dict:
    schema = access_schema(mdb)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    if db_path.exists():
        db_path.unlink()
    con = duckdb.connect(str(db_path))
    con.execute(f"SET memory_limit = '{settings.duckdb_memory_limit}'; SET threads = {settings.duckdb_threads};")
    con.execute("SET preserve_insertion_order = true;")
    tables = []
    started = time.time()
    with tempfile.TemporaryDirectory(dir=db_path.parent) as tmp:
        for name, cols in schema.items():
            t0 = time.time()
            path = Path(tmp) / f"{name}.csv"
            exported = export_table(mdb, name, path)
            # Timestamps are read as text and parsed with try_strptime: Access "zero dates" such as
            # 1900-01-00 become NULL (unknown stays unknown) and are counted per column in the report.
            read_types = ", ".join(f"'{c}': '{'VARCHAR' if d == 'TIMESTAMP' else d}'" for c, _, d in cols)
            select = ", ".join(
                f"try_strptime(\"{c}\", '%Y-%m-%d %H:%M:%S') AS \"{c}\"" if d == "TIMESTAMP" else f'"{c}"'
                for c, _, d in cols)
            con.execute(
                f'CREATE TABLE "{name}" AS SELECT row_number() OVER () AS _row, {select} FROM read_csv(?, header = true, '
                f"columns = {{{read_types}}}, quote = '\"', escape = '\"', max_line_size = 1073741824)",
                [str(path)],
            )
            invalid_dates = {}
            ts_cols = [c for c, _, d in cols if d == "TIMESTAMP"]
            if ts_cols:
                raw = con.execute(
                    "SELECT " + ", ".join(
                        f"count(*) FILTER (WHERE \"{c}\" IS NOT NULL AND try_strptime(\"{c}\", '%Y-%m-%d %H:%M:%S') IS NULL)"
                        for c in ts_cols) + " FROM read_csv(?, header = true, all_varchar = true, max_line_size = 1073741824)",
                    [str(path)]).fetchone()
                invalid_dates = {c: n for c, n in zip(ts_cols, raw) if n}
            loaded = con.execute(f'SELECT count(*) FROM "{name}"').fetchone()[0]
            path.unlink()
            tables.append({
                "table": name, "columns": len(cols), "exported_rows": exported, "loaded_rows": loaded,
                "status": "PASS" if exported == loaded else "FAIL",
                "types": {c: d for c, _, d in cols}, "invalid_dates_to_null": invalid_dates, "seconds": round(time.time() - t0, 2),
            })
    con.close()
    return {
        "source": str(mdb), "duckdb": str(db_path), "tables": tables,
        "total_rows": sum(t["loaded_rows"] for t in tables),
        "failed": [t["table"] for t in tables if t["status"] == "FAIL"],
        "invalid_dates_to_null": sum(sum(t["invalid_dates_to_null"].values()) for t in tables),
        "seconds": round(time.time() - started, 1),
        "size_mb": round(db_path.stat().st_size / 1e6, 1),
    }


def render(summary: dict, out: Path) -> None:
    rows = []
    for t in sorted(summary["tables"], key=lambda t: -t["loaded_rows"]):
        types = sorted(set(t["types"].values()))
        bad = "; ".join(f"{c}: {n}" for c, n in t["invalid_dates_to_null"].items())
        rows.append([f"<code>{R.esc(t['table'])}</code>", R.badge(t["status"]), f"{t['exported_rows']:,}",
                     f"{t['loaded_rows']:,}", str(t["columns"]), R.esc(", ".join(types)),
                     R.badge("NULLED") + " " + R.esc(bad) if bad else "", f"{t['seconds']}"])
    ok = not summary["failed"]
    body = (R.tiles([("tables", str(len(summary["tables"]))), ("rows loaded", f"{summary['total_rows']:,}"),
                     ("tables with count mismatch", str(len(summary["failed"]))),
                     ("invalid dates set to NULL", str(summary["invalid_dates_to_null"])),
                     ("DuckDB file size", f"{summary['size_mb']} MB"), ("seconds", str(summary["seconds"]))])
            + "<h2>Row counts: mdb-export (csv parsed) against DuckDB</h2>"
            + R.table(["Table", "Status", "Exported", "Loaded", "Columns", "Types", "Invalid dates set to NULL", "Seconds"], rows, raw=True))
    subtitle = (f"Step A5 of pm_pack/08. {R.esc(summary['source'])} to {R.esc(summary['duckdb'])}. "
                f"{R.badge('PASS' if ok else 'FAIL')} Open the file with <code>duckdb -ui {R.esc(summary['duckdb'])}</code>.")
    R.write(out, R.page(f"Conversion of {Path(summary['source']).name}", subtitle, body), summary)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("mdb", type=Path)
    ap.add_argument("duckdb", type=Path)
    ap.add_argument("--report", type=Path, help="default reports/convert/<duckdb stem>.html")
    args = ap.parse_args()
    summary = convert(args.mdb, args.duckdb)
    render(summary, args.report or settings.reports_dir / "convert" / f"{args.duckdb.stem}.html")
    print(f"{args.duckdb}: {len(summary['tables'])} tables, {summary['total_rows']:,} rows, "
          f"{summary['size_mb']} MB, {summary['seconds']} s, mismatches: {summary['failed'] or 'none'}")
    return 1 if summary["failed"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
