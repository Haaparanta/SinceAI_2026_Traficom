#!/usr/bin/env python3
"""Step B4 visual proof: ranked findings for one Space IFIC, with every citation re-checked.

    uv run python scripts/findings_report.py 3074     # writes reports/3074/04_findings.html and .summary.json

Runs radar.pipeline.assemble (and saves data/derived/findings_space_<issue>.json), then radar.evidence_check.
Shows the concern levels, which rule produced each level, the top 25 findings with their full evidence and
score factors, and the resolver result per evidence kind.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT)]

from radar import evidence_check  # noqa: E402
from radar import report_html as R  # noqa: E402
from radar.config import settings  # noqa: E402
from radar.pipeline import assemble  # noqa: E402

LEVELS = [("high", "High", "--c4"), ("medium", "Medium", "--c3"), ("review", "Review", "--c5"), ("low", "Low", "--c2"), ("none", "Not raised", "--c1")]
EXTRA_CSS = """
:root { --c1:#cfc8cd; --c2:#9ec5ee; --c3:#eda100; --c4:#c2410c; --c5:#8b5cf6; }
@media (prefers-color-scheme: dark) { :root { --c1:#4a434d; --c2:#3c6d9e; --c3:#c98500; --c4:#ea6a3a; --c5:#9f86f0; } }
.lvl { display:inline-block; padding:1px 8px; border-radius:999px; font-size:11px; font-weight:700; color:#fff; }
.bars div { display:flex; align-items:center; gap:8px; margin:4px 0; font-size:13px; }
.bars span.b { height:16px; border-radius:0 4px 4px 0; display:inline-block; }
.bars span.l { width:90px; }
details.f { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:8px 12px; margin:8px 0; }
details.f summary { font-size:13px; }
details.f p { margin:6px 0; font-size:13px; }
"""


def lvl(concern: str) -> str:
    label, var = next((l, v) for k, l, v in LEVELS if k == concern)
    return f'<span class="lvl" style="background:var({var})">{label}</span>'


def main() -> int:
    issue = int(sys.argv[1]) if len(sys.argv) > 1 else 3074
    run = assemble.run(issue)
    res = run.result
    (settings.derived_dir / f"findings_space_{issue}.json").write_text(res.model_dump_json(indent=1), encoding="utf-8")
    checks = evidence_check.check(res)
    fails = [c for c in checks if c.status == "FAIL"]
    counts = Counter(f.concern for f in res.findings)
    by_notice = run.notices()
    def rule_label(rule: str) -> str:   # group the Bureau rule across provisions; keep other rules whole
        return rule.split(" (")[0] if rule.startswith("the Bureau") else rule

    rules = Counter((run.scores[f.group_id].concern, rule_label(run.scores[f.group_id].rule)) for f in res.findings if f.group_id)

    one_level = max(counts.values()) == len(res.findings)
    evidence_less = [f.id for f in res.findings if not f.evidence]
    status = "PASS" if not fails and not one_level and not evidence_less and res.provenance_coverage_pct == 100.0 else "FAIL"

    top = max(counts.values())
    bars = '<div class="bars">' + "".join(
        f'<div><span class="l">{lab}</span><span class="b" style="width:{360 * counts[k] / top:.0f}px;background:var({v})"></span>{counts[k]}</div>'
        for k, lab, v in LEVELS) + "</div>"

    kinds = Counter((c.kind, c.status) for c in checks)
    resolver_rows = [[k, R.badge(s), f"{n:,}"] for (k, s), n in sorted(kinds.items())]

    cards = []
    for f in [f for f in res.findings if f.concern != "none"][:25]:
        n = by_notice[f.notice_id]
        s = run.scores.get(f.group_id)
        ev = R.table(["ID", "Kind", "Locator", "Excerpt"],
                     [[e.id, e.kind, f"<code>{R.esc(e.locator)}</code>", R.esc(e.excerpt)] for e in f.evidence], raw=True)
        factors = R.table(["Factor", "Value"], [[k, R.esc(v)] for k, v in (s.factors.items() if s else [])])
        cards.append(f'<details class="f"><summary>{lvl(f.concern)} <b>{f.id}</b> &middot; {R.esc(n.administration)} '
                     f'{R.esc(n.network_name)} &middot; {R.esc(n.special_section)} &middot; score {s.score if s else "-"}</summary>'
                     f'<p>{R.esc(f.reason)}</p><p class="sub">{R.esc("; ".join(f.calc.notes))}</p>{ev}{factors}</details>')

    not_raised = Counter(f.reason.split(":")[0] if f.reason.startswith("Not raised") else "" for f in res.findings if f.concern == "none")
    nr = Counter()
    for f in res.findings:
        if f.concern == "none":
            nr[f.reason.replace("Not raised: ", "").split(" (")[0].rstrip(".")] += 1

    body = (
        R.tiles([("notices screened", str(res.screened)), ("flagged", str(res.flagged)),
                 ("provenance coverage", f"{res.provenance_coverage_pct} %"),
                 ("citations re-checked", f"{len(checks):,}"), ("citation mismatches", str(len(fails)))])
        + "<h2>Concern levels</h2>" + bars
        + "<h2>Which rule set each level</h2><p class='sub'>Rule table in radar.pipeline.rank (hypothesis until Q1; "
          "pfd in step C1 will raise or lower the medium cases).</p>"
        + R.table(["Concern", "Rule", "Notices"], [[lvl(c), R.esc(r), str(n)] for (c, r), n in
                                                   sorted(rules.items(), key=lambda t: (-assemble.RK.CONCERN_ORDER[t[0][0]], -t[1]))], raw=True)
        + "<h2>Evidence resolver</h2><p class='sub'>Every locator reopened in DuckDB, the Traficom snapshot or the geography "
          "code; the excerpt must match exactly.</p>" + R.table(["Kind", "Status", "Citations"], resolver_rows, raw=True)
        + (R.table(["Finding", "Evidence", "Locator", "Expected", "Found"],
                   [[c.finding_id, c.evidence_id, c.locator, c.expected, c.found or "row not found"] for c in fails[:30]]) if fails else "")
        + "<h2>Top 25 findings</h2><p class='sub'>Click a finding for its evidence and score factors.</p>" + "".join(cards)
        + "<h2>Why the other notices were not raised</h2>"
        + R.table(["Reason", "Notices"], [[k, str(v)] for k, v in nr.most_common()])
    )
    summary = {"status": status, "issue": issue, "screened": res.screened, "flagged": res.flagged,
               "provenance_coverage_pct": res.provenance_coverage_pct, "concern": dict(counts),
               "citations": len(checks), "citation_mismatches": len(fails),
               "resolver": {f"{k}:{s}": n for (k, s), n in kinds.items()},
               "top": [{"id": f.id, "notice": f.notice_id, "concern": f.concern, "reason": f.reason} for f in res.findings[:25]]}
    out = settings.reports_dir / str(issue) / "04_findings.html"
    R.write(out, R.page(f"Space IFIC {issue}: findings",
                        f"Step B4 of pm_pack/08. radar.pipeline.assemble and rank; radar.evidence_check. {R.badge(status)}",
                        body, EXTRA_CSS), summary)
    print(f"written {out}: {status}; {dict(counts)}; citations {len(checks)}, mismatches {len(fails)}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
