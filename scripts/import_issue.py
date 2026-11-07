#!/usr/bin/env python3
"""Import one ITU BR IFIC issue, Space or Terrestrial, from its number to the screen.

    uv run python scripts/import_issue.py --kind space --issue 3077
    uv run python scripts/import_issue.py --kind terrestrial --issue 3077 --zip ~/Downloads/brific3077.zip
    make import KIND=space ISSUE=3077 [ZIP=path] [FORCE=1]

Steps, one line each:

  1. zip       download it from the ITU (or copy the --zip you give) to data/raw/<name>.zip
  2. verify    a real zip, every CRC good, exactly one .mdb, an Access (Jet) database
  3. extract   the .mdb to data/raw/<name>/<name>.mdb (written to a fixed name: nothing in the archive picks a path)
  4. convert   .mdb -> data/derived/<kind>_<issue>.duckdb, row count checked per table (scripts/mdb_to_duckdb.py)
  5. screen    the pipeline, results/<kind>_<issue>.csv|json (radar.export)
  6. evidence  every citation of every finding reopened in the database (radar.evidence_check)
  7. cache     data/cache/<kind>_<issue>.json, so GET /issues and the screen list the issue (scripts/build_cache.py)

A receipt with the source URL, sizes, SHA-256 checksums and counts lands in data/derived/import_<kind>_<issue>.json.
Steps 1 to 4 are skipped when their output is already newer than their input; --force redoes them. Space and
Terrestrial IFICs share issue numbers, so --kind is required. The special-interest XLS (data/raw/special_interest.xlsx)
is screened when it is present; the graded issues (space 3074, terrestrial 3076) are refused without it, because their
committed results carry the station matches.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import time
import zipfile
import zlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT), str(ROOT / "scripts")]

from radar.config import settings  # noqa: E402

URLS = {
    "space": "https://www.itu.int/sns/ific10/ific{n}.zip",
    "terrestrial": "https://www.itu.int/en/ITU-R/terrestrial/brific/BRIFIC/MDB/brific{n}.zip",
}
PREFIX = {"space": "ific", "terrestrial": "brific"}
GRADED = {("space", 3074), ("terrestrial", 3076)}
JET_MAGIC = b"Standard Jet DB"          # bytes 4-18 of every Access 97-2003 .mdb (Jet 3 and Jet 4)


class StepFailed(Exception):
    """A step failed; the message says which and why."""


@dataclass
class Paths:
    kind: str
    issue: int
    raw: Path = field(default_factory=lambda: settings.raw_dir)
    derived: Path = field(default_factory=lambda: settings.derived_dir)

    @property
    def name(self) -> str:
        return f"{PREFIX[self.kind]}{self.issue}"

    @property
    def zip(self) -> Path:
        return self.raw / f"{self.name}.zip"

    @property
    def mdb(self) -> Path:
        return self.raw / self.name / f"{self.name}.mdb"

    @property
    def duckdb(self) -> Path:
        return self.derived / f"{self.kind}_{self.issue}.duckdb"

    @property
    def receipt(self) -> Path:
        return self.derived / f"import_{self.kind}_{self.issue}.json"


def say(status: str, step: str, detail: str = "") -> None:
    print(f"{status:<8} {step:<9} {detail}".rstrip(), flush=True)


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def fresh(out: Path, src: Path) -> bool:
    """out exists, is not empty, and is at least as new as src."""
    return out.exists() and out.stat().st_size > 0 and out.stat().st_mtime >= src.stat().st_mtime


def url(kind: str, issue: int) -> str:
    return URLS[kind].format(n=issue)


# ---- 1. zip -------------------------------------------------------------------------------------------------------

def download(src_url: str, dest: Path) -> None:
    """curl to dest.part, then rename: an interrupted download never leaves a file that looks complete."""
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_name(dest.name + ".part")
    r = subprocess.run(["curl", "-fsSL", "--retry", "3", "--retry-delay", "3", "--connect-timeout", "30",
                        "-o", str(tmp), src_url], capture_output=True, text=True)
    if r.returncode != 0:
        tmp.unlink(missing_ok=True)
        hint = " (the ITU has not published this issue yet, or the number is wrong)" if "404" in r.stderr else ""
        raise StepFailed(f"download failed: {src_url}: {r.stderr.strip() or f'curl exit {r.returncode}'}{hint}")
    try:
        mdb_member(tmp, dest.stem, label=dest.name)
    except StepFailed:
        tmp.unlink(missing_ok=True)
        raise
    tmp.replace(dest)


def get_zip(p: Paths, local: Path | None, force: bool) -> str:
    if local is not None:
        local = local.expanduser().resolve()
        if not local.is_file():
            raise StepFailed(f"--zip {local}: no such file")
        if local == p.zip.resolve():
            say("skip", "zip", f"{p.zip.name} is already in place")
            return str(local)
        mdb_member(local, p.name)              # check it before it lands in data/raw
        p.zip.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.zip.with_name(p.zip.name + ".part")
        shutil.copyfile(local, tmp)
        tmp.replace(p.zip)
        say("PASS", "zip", f"copied {local} -> {p.zip.relative_to(ROOT) if p.zip.is_relative_to(ROOT) else p.zip}")
        return str(local)
    src = url(p.kind, p.issue)
    if p.zip.exists() and p.zip.stat().st_size > 0 and not force:
        say("skip", "zip", f"{p.zip.name} already downloaded ({p.zip.stat().st_size / 1e6:.1f} MB)")
        return src
    t = time.time()
    download(src, p.zip)
    say("PASS", "zip", f"{src} ({p.zip.stat().st_size / 1e6:.1f} MB, {time.time() - t:.0f} s)")
    return src


# ---- 2. verify and 3. extract -------------------------------------------------------------------------------------

def mdb_member(zpath: Path, expected: str, label: str | None = None) -> zipfile.ZipInfo:
    """The single .mdb inside the zip, after a full CRC check. The ITU names it after the issue (ific3074.mdb,
    brific3076.mdb), so a database named for another issue or kind means the wrong file was given."""
    label = label or zpath.name
    if not zipfile.is_zipfile(zpath):
        raise StepFailed(f"{label} is not a zip file (an HTML error page saved as .zip looks like this)")
    try:
        with zipfile.ZipFile(zpath) as zf:
            bad = zf.testzip()                   # reads every member; damaged deflate data raises instead
            mdbs = [i for i in zf.infolist() if not i.is_dir() and i.filename.lower().endswith(".mdb")]
    except (zipfile.BadZipFile, zlib.error, EOFError) as e:
        raise StepFailed(f"{label} is damaged ({e}); download it again (--force)") from None
    if bad is not None:
        raise StepFailed(f"{label}: CRC error in {bad}; download it again (--force)")
    if len(mdbs) != 1:
        found = ", ".join(i.filename for i in mdbs) or "none"
        raise StepFailed(f"{label}: expected exactly one .mdb, found {found}")
    stem = Path(mdbs[0].filename).stem.lower()
    if stem != expected.lower():
        raise StepFailed(f"{label} holds {mdbs[0].filename}, not {expected}.mdb: wrong issue number or --kind for this file")
    return mdbs[0]


def is_jet(path: Path) -> bool:
    with path.open("rb") as f:
        return f.read(19)[4:19] == JET_MAGIC


def extract(p: Paths, force: bool) -> zipfile.ZipInfo:
    member = mdb_member(p.zip, p.name)
    say("PASS", "verify", f"{p.zip.name}: CRC good, one database ({member.filename}, {member.file_size / 1e6:.1f} MB)")
    if not force and fresh(p.mdb, p.zip) and p.mdb.stat().st_size == member.file_size:
        say("skip", "extract", f"{p.mdb.relative_to(p.raw)} is up to date")
    else:
        p.mdb.parent.mkdir(parents=True, exist_ok=True)
        tmp = p.mdb.with_name(p.mdb.name + ".part")
        with zipfile.ZipFile(p.zip) as zf, zf.open(member) as src, tmp.open("wb") as dst:
            shutil.copyfileobj(src, dst, 1 << 20)
        tmp.replace(p.mdb)
        say("PASS", "extract", f"{p.mdb.relative_to(p.raw)}")
    if not is_jet(p.mdb):
        raise StepFailed(f"{p.mdb.name} is not an Access (Jet) database")
    return member


# ---- 4. convert ---------------------------------------------------------------------------------------------------

def convert(p: Paths, force: bool) -> dict | None:
    if not force and fresh(p.duckdb, p.mdb):
        say("skip", "convert", f"{p.duckdb.name} is up to date")
        return None
    if shutil.which("mdb-tables") is None or shutil.which("mdb-export") is None:
        raise StepFailed("mdbtools is not installed (brew install mdbtools, or apt-get install mdbtools)")
    import mdb_to_duckdb

    summary = mdb_to_duckdb.convert(p.mdb, p.duckdb)
    mdb_to_duckdb.render(summary, settings.reports_dir / "convert" / f"{p.duckdb.stem}.html")
    if summary["failed"]:
        p.duckdb.unlink(missing_ok=True)       # a half-right database must not be screened
        raise StepFailed(f"row counts differ in {', '.join(summary['failed'])}; see reports/convert/{p.duckdb.stem}.html")
    say("PASS", "convert", f"{p.duckdb.name}: {len(summary['tables'])} tables, {summary['total_rows']:,} rows, "
                           f"row counts match, {summary['seconds']} s")
    return summary


# ---- 5. screen, 6. evidence, 7. cache -----------------------------------------------------------------------------

def screen(p: Paths, results_dir: Path | None) -> dict:
    from radar.export import results as R

    out = results_dir or R.RESULTS_DIR
    t = time.time()
    ex = (R.export_space if p.kind == "space" else R.export_terrestrial)(p.issue, out_dir=out)
    concern = ", ".join(f"{k} {v}" for k, v in sorted(ex["concern"].items(), key=lambda kv: ORDER.index(kv[0])))
    say("PASS", "screen", f"{ex['rows']:,} notices ({concern}) -> {Path(ex['paths']['csv']).name}, {time.time() - t:.0f} s")
    return ex


ORDER = ["high", "review", "medium", "low", "none"]


def evidence(run_result) -> dict:
    from collections import Counter

    from radar.evidence_check import check

    checks = check(run_result)
    c = Counter(x.status for x in checks)
    fails = [x for x in checks if x.status == "FAIL"]
    detail = f"{c.get('PASS', 0):,} citations reopened and matched, {c.get('UNCHECKED', 0):,} not checkable"
    if fails:
        for x in fails[:5]:
            print(f"         {x.finding_id} {x.evidence_id} {x.locator}: expected {x.expected!r}, found {x.found!r}")
        raise StepFailed(f"{len(fails):,} citations do not match the database ({detail})")
    say("PASS", "evidence", detail)
    return dict(c)


def cache(p: Paths, cache_dir: Path | None) -> Path:
    import build_cache

    path, data = build_cache.write(p.kind, p.issue, cache_dir)
    r = data["result"]
    say("PASS", "cache", f"{path.name}: {r['flagged']:,} flagged of {r['screened']:,}, listed by GET /issues")
    return path


# ---- prerequisites ------------------------------------------------------------------------------------------------

def preflight(p: Paths, force: bool) -> bool:
    """Fail early on what the screening needs; returns whether the special-interest stations are screened."""
    from radar.adapters import special_interest

    table = settings.raw_dir / "taajuusjakotaulukko.json"
    if not table.exists() and not (settings.derived_dir / "fi_subbands.parquet").exists():
        raise StepFailed("the Finnish frequency table is missing (data/raw/taajuusjakotaulukko.json); "
                           "run scripts/fetch_data.sh once")
    has_xlsx = special_interest.path().exists()
    if not has_xlsx:
        if (p.kind, p.issue) in GRADED and not force:
            raise StepFailed(f"{p.kind} {p.issue} is a graded issue and its committed results carry the special-interest "
                               "station matches; save the XLS as data/raw/special_interest.xlsx first (--force to "
                               "screen without it)")
        say("WARN", "stations", "data/raw/special_interest.xlsx is missing: special-interest stations are not screened")
    return has_xlsx


# ---- main ---------------------------------------------------------------------------------------------------------

def run(kind: str, issue: int, local_zip: Path | None = None, force: bool = False,
        results_dir: Path | None = None, cache_dir: Path | None = None, skip_cache: bool = False) -> dict:
    p = Paths(kind, issue)
    started = datetime.now(timezone.utc)
    stations = preflight(p, force)
    source = get_zip(p, local_zip, force)
    member = extract(p, force)
    conv = convert(p, force)
    ex = screen(p, results_dir)
    ev = evidence(ex["run"].result)
    cache_path = None if skip_cache else cache(p, cache_dir)
    receipt = {
        "kind": kind, "issue": issue, "imported_at": started.isoformat(timespec="seconds"),
        "source": source,
        "zip": {"path": str(p.zip), "bytes": p.zip.stat().st_size, "sha256": sha256(p.zip)},
        "mdb": {"path": str(p.mdb), "member": member.filename, "bytes": p.mdb.stat().st_size, "sha256": sha256(p.mdb)},
        "duckdb": {"path": str(p.duckdb), "converted_now": conv is not None,
                   **({"tables": len(conv["tables"]), "rows": conv["total_rows"]} if conv else {})},
        "special_interest_screened": stations,
        "results": ex["paths"], "notices": ex["rows"], "concern": ex["concern"],
        "evidence": ev, "cache": str(cache_path) if cache_path else None,
    }
    p.receipt.parent.mkdir(parents=True, exist_ok=True)
    p.receipt.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    say("PASS", "receipt", f"{p.receipt.relative_to(ROOT) if p.receipt.is_relative_to(ROOT) else p.receipt}")
    return receipt


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Import one ITU BR IFIC issue: download, verify, convert, screen, cache.",
                                 epilog="Example: uv run python scripts/import_issue.py --kind space --issue 3077")
    ap.add_argument("--kind", choices=sorted(URLS), required=True, help="Space and Terrestrial IFICs share issue numbers")
    ap.add_argument("--issue", type=int, required=True, help="IFIC issue number, e.g. 3077")
    ap.add_argument("--zip", type=Path, help="a zip you already have, instead of downloading it from the ITU")
    ap.add_argument("--force", action="store_true", help="download, extract and convert again even when up to date")
    ap.add_argument("--no-cache", action="store_true", help="skip data/cache/ (the screen will not list the issue)")
    ap.add_argument("--print-url", action="store_true", help="print the ITU download URL and stop")
    args = ap.parse_args(argv)
    if not 1000 <= args.issue <= 9999:
        ap.error(f"--issue {args.issue}: IFIC issue numbers have four digits")
    if args.print_url:
        print(url(args.kind, args.issue))
        return 0
    say("", "import", f"{args.kind} IFIC {args.issue}")
    try:
        run(args.kind, args.issue, local_zip=args.zip, force=args.force, skip_cache=args.no_cache)
    except StepFailed as e:
        say("FAIL", "import", str(e))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
