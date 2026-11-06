#!/usr/bin/env python3
"""Step E2 of pm_pack/08: case recognition accuracy (criterion D) against every label we have.

    uv run python scripts/golden_report.py        # writes reports/freeze/e2_golden.html and results/proof/accuracy.csv

Three label sources, kept apart because they are not equally strong:
  1. tests/golden/space_3074.yaml: hand-checked group cases (expected candidate, paths, geography). Each case says
     who checked it; "claude-first-pass" means not yet confirmed by a person, so the numbers are a regression check.
  2. The Bureau's own list of groups where Finland is an affected administration (provn.adm = 'FIN'). The rules use
     this list, so a hit here shows the rule is wired through; it is not an independent test.
  3. Reviewer decisions in the audit log (data/decisions/space_3074.jsonl): approve or investigate = relevant,
     dismiss = not relevant. These are the expert labels; precision on them is the honest figure once they exist.
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import duckdb
import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT)]

from radar import decisions as DEC  # noqa: E402
from radar import report_html as R  # noqa: E402
from radar.adapters import space_ific  # noqa: E402
from radar.config import settings  # noqa: E402
from radar.pipeline import assemble  # noqa: E402
from radar.pipeline import relevance as rel  # noqa: E402

ISSUE = 3074


def prf(tp: int, fp: int, fn: int) -> tuple[str, str]:
    p = "n/a" if tp + fp == 0 else f"{tp / (tp + fp):.2f}"
    r = "n/a" if tp + fn == 0 else f"{tp / (tp + fn):.2f}"
    return p, r


def main() -> int:
    golden = yaml.safe_load((ROOT / "tests" / "golden" / f"space_{ISSUE}.yaml").read_text())
    run = assemble.run(ISSUE)
    rows = {r.group_id: r for r in run.rows}
    concern_by_notice = {f.notice_id: f.concern for f in run.result.findings}

    # 1. golden cases
    case_rows, tp = [], dict(tp=0, fp=0, fn=0, tn=0)
    exact = 0
    for c in golden["cases"]:
        r = rows[c["group_id"]]
        exp, got = c["b3"]["candidate"], r.candidate
        tp["tp" if exp and got else "fp" if got else "fn" if exp else "tn"] += 1
        paths_ok = sorted(r.paths) == sorted(c["b2"]["paths"])
        geo_ok = r.geo_relevance == c["b3"]["geo"]
        ok = exp == got and paths_ok and geo_ok
        exact += ok
        case_rows.append([c["group_id"], R.esc(c["notice"]), str(exp), str(got), R.esc(", ".join(sorted(r.paths)) or "none"),
                          R.esc(f"{c['b3']['geo']} / {r.geo_relevance}"), R.esc(c["checked_by"]), R.badge("PASS" if ok else "FAIL")])
    p1, r1 = prf(tp["tp"], tp["fp"], tp["fn"])
    checkers = sorted({c["checked_by"] for c in golden["cases"]})

    # 2. Bureau-named groups
    with duckdb.connect(str(space_ific.db_path(ISSUE)), read_only=True) as con:
        named = rel.finland_named(con)
    named_rows = []
    named_hit = 0
    for g, prov in sorted(named.items()):
        r = rows.get(g)
        conc = concern_by_notice.get(r.notice_id) if r else None
        hit = bool(r and r.candidate and conc == "high")
        named_hit += hit
        named_rows.append([g, r.notice_id if r else "not screened", R.esc(", ".join(prov)), str(bool(r and r.candidate)),
                           conc or "none", R.badge("PASS" if hit else "FAIL")])

    # 3. reviewer decisions
    latest = DEC.latest("space", ISSUE)
    flagged = {f.id for f in run.result.findings if f.concern != "none"}
    d = dict(tp=0, fp=0, fn=0)
    for fid, e in latest.items():
        relevant = e["decision"] in ("approve", "investigate")
        pred = fid in flagged
        if pred and relevant:
            d["tp"] += 1
        elif pred:
            d["fp"] += 1
        elif relevant:
            d["fn"] += 1
    p3, r3 = prf(d["tp"], d["fp"], d["fn"])

    summary = [
        ["Golden cases (tests/golden)", str(len(golden["cases"])), ", ".join(checkers), str(tp["tp"]), str(tp["fp"]), str(tp["fn"]), str(tp["tn"]), p1, r1],
        ["Bureau names Finland (provn)", str(len(named)), "ITU BR (also a rule input)", str(named_hit), "0", str(len(named) - named_hit), "-", "-",
         f"{named_hit / len(named):.2f}" if named else "n/a"],
        ["Reviewer decisions (audit log)", str(len(latest)), "Traficom reviewers", str(d["tp"]), str(d["fp"]), str(d["fn"]), "-", p3, r3],
    ]
    proof = ROOT / "results" / "proof"
    proof.mkdir(parents=True, exist_ok=True)
    with (proof / "accuracy.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh, lineterminator="\n")
        w.writerow(["label_source", "cases", "labelled_by", "tp", "fp", "fn", "tn", "precision", "recall"])
        w.writerows(summary)

    checks = [
        ("Every golden case matches (candidate, paths, geography)", exact == len(golden["cases"]), f"{exact} of {len(golden['cases'])}"),
        ("Every Bureau-named group is a candidate with concern high", named_hit == len(named), f"{named_hit} of {len(named)}"),
        ("No reviewer label contradicts a flag", d["fp"] == 0, f"{len(latest)} decisions recorded"),
    ]
    status = "PASS" if all(ok for _, ok, _ in checks) else "FAIL"
    note = ("" if checkers != ["claude-first-pass"] else
            "<p class='sub'>All golden cases are first-pass labels by the coding agent: they guard against regressions "
            "but are not a specialist judgement. Replace <code>checked_by</code> with a reviewer's name once confirmed.</p>")
    body = (R.tiles([("golden cases", str(len(golden["cases"]))), ("Bureau-named groups", str(len(named))),
                     ("reviewer decisions", str(len(latest))), ("flagged findings", str(len(flagged)))])
            + "<h2>Checks</h2>" + R.table(["Check", "Status", "Detail"], [[c, R.badge("PASS" if ok else "FAIL"), R.esc(x)] for c, ok, x in checks], raw=True)
            + "<h2>Precision and recall by label source</h2>" + note
            + R.table(["Label source", "Cases", "Labelled by", "TP", "FP", "FN", "TN", "Precision", "Recall"], summary)
            + "<p class='sub'>Also in <code>results/proof/accuracy.csv</code>. Reviewer decisions: approve or investigate count as "
              "relevant, dismiss as not relevant; a finding is predicted relevant when its concern is not <i>none</i>.</p>"
            + "<h2>Golden cases</h2>" + R.table(["Group", "Notice", "Expected", "Got", "Paths", "Geography expected / got", "Checked by", "Status"], case_rows, raw=True)
            + "<h2>Groups where the Bureau names Finland</h2>" + R.table(["Group", "Notice", "Provisions", "Candidate", "Concern", "Status"], named_rows, raw=True))
    out = settings.reports_dir / "freeze" / "e2_golden.html"
    R.write(out, R.page(f"Case recognition accuracy: Space IFIC {ISSUE}", f"Step E2 of pm_pack/08 (criterion D). {R.badge(status)}", body),
            {"status": status, "checks": [[c, ok, x] for c, ok, x in checks], "summary": summary})
    print(f"written {out}: {status}")
    for c, ok, x in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {c}  {x}")
    for s in summary:
        print("  ", s)
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
