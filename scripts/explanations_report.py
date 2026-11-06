#!/usr/bin/env python3
"""Step D2 visual proof: grounded explanations and letter drafts, checked number by number.

    uv run python scripts/explanations_report.py 3074     # writes reports/3074/07_explanations.html and .summary.json

For the 20 highest-ranked flagged findings of the cached analysis (data/cache/<kind>_<issue>.json) the explanation
is generated exactly as the API does (cache, Claude when credentials exist, otherwise the template) and shown beside
the finding's evidence table. Every cited ID and every number in the text is highlighted: green when it is in the
finding, red when it is not. A planted bad text (an invented number and an unknown ID) must be rejected, and no
letter may say that it was sent.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT)]

from radar import report_html as R  # noqa: E402
from radar.config import settings  # noqa: E402
from radar.llm import client as C  # noqa: E402
from radar.llm import drafts as D  # noqa: E402
from radar.llm import grounding as G  # noqa: E402

N = 20
SENT = re.compile(r"\b(has|have|was|were|been) (been )?sent\b|\bwe (have )?sent\b", re.I)
ID = re.compile(r"\b[EF]-\d[\d-]*\b")


def highlight(text: str, data: dict) -> str:
    """Escape the text, then mark evidence IDs and numbers green (in the finding) or red (not in it)."""
    allowed = {e["id"] for e in data["evidence"]}
    pool = G.numbers(json.dumps(data, ensure_ascii=False)) | {n for e in data["evidence"] for n in G.numbers(e["id"])}
    out, pos = [], 0
    for m in re.finditer(rf"{ID.pattern}|{G.NUMBER.pattern}", text):
        out.append(R.esc(text[pos:m.start()]))
        tok = m.group(0)
        ok = tok in allowed if ID.fullmatch(tok) else bool(G.numbers(tok)) and G.numbers(tok) <= pool
        out.append(f"<mark class='{'ok' if ok else 'bad'}'>{R.esc(tok)}</mark>")
        pos = m.end()
    return "".join(out) + R.esc(text[pos:])


def main() -> int:
    issue = int(sys.argv[1]) if len(sys.argv) > 1 else 3074
    kind = sys.argv[2] if len(sys.argv) > 2 else ("terrestrial" if issue in (3075, 3076) else "space")
    bundle = json.loads((settings.data_dir / "cache" / f"{kind}_{issue}.json").read_text(encoding="utf-8"))
    flagged = [f for f in bundle["result"]["findings"] if f["concern"] != "none"][:N]

    cards, rows, sources = [], [], {}
    explained_ok = letters_ok = bannered = 0
    for f in flagged:
        ctx = bundle["context"].get(f["id"])
        data = G.payload(f, ctx, kind, issue)
        ex = D.explain(f, ctx, kind, issue)
        le = D.letter(f, ctx, kind, issue)
        ex_check = G.validate([ex.output.text], ex.output.cited_evidence_ids, data)
        le_check = G.validate([le.output.subject, le.output.body_markdown], le.output.cited_evidence_ids, data)
        not_sent = not SENT.search(le.output.body_markdown.replace(D.DRAFT_BANNER, ""))
        explained_ok += ex_check.ok
        bannered += le.output.body_markdown.startswith(f"*{D.DRAFT_BANNER}*")
        letters_ok += le_check.ok and not_sent
        sources[ex.source] = sources.get(ex.source, 0) + 1
        rows.append([f["id"], f["concern"], ex.source, R.badge("PASS" if ex_check.ok else "FAIL"),
                     R.badge("PASS" if le_check.ok and not_sent else "FAIL")])
        ev = R.table(["ID", "Kind", "Locator", "Excerpt"],
                     [[(f"<mark class='ok'>{R.esc(e['id'])}</mark>" if e["id"] in ex.output.cited_evidence_ids else R.esc(e["id"])),
                       R.esc(e["kind"]), R.esc(e["locator"]), R.esc(str(e["excerpt"])[:140])] for e in f["evidence"]], raw=True)
        cards.append(
            f"<section class='card'><h3>{R.esc(f['id'])} · {R.esc((ctx or {}).get('title') or f['notice_id'])} · {R.esc(f['concern'])}</h3>"
            f"<div class='two'><div><p class='sub'>Explanation ({R.esc(ex.source)}; {R.esc(ex_check.summary())})</p>"
            f"<p>{highlight(ex.output.text, data)}</p><p class='sub'>Cites: "
            + " ".join(f"<mark class='{'ok' if i in {e['id'] for e in f['evidence']} else 'bad'}'>{R.esc(i)}</mark>" for i in ex.output.cited_evidence_ids)
            + f"</p><details><summary>Letter draft to {R.esc(le.output.to_administration)}</summary><p><b>{highlight(le.output.subject, data)}</b></p>"
            f"<pre>{highlight(le.output.body_markdown, data)}</pre></details></div><div>{ev}</div></div></section>")

    # Tamper test: the validator must reject an invented number and an unknown evidence ID.
    f0 = flagged[0]
    d0 = G.payload(f0, bundle["context"].get(f0["id"]), kind, issue)
    planted = "The margin is 12.34 dB, see E-999."
    bad = G.validate([planted], ["E-999"], d0)
    tamper_ok = not bad.ok and "E-999" in bad.unknown_ids and "12.34" in bad.unsupported_numbers

    checks = [
        (f"Explanations grounded ({N} findings)", explained_ok == len(flagged), f"{explained_ok} of {len(flagged)}"),
        ("Letters grounded and never say they were sent", letters_ok == len(flagged), f"{letters_ok} of {len(flagged)}"),
        ("Planted invented number and unknown ID are rejected", tamper_ok, bad.summary()),
        ("Every letter starts with the draft banner", bannered == len(flagged), f"{bannered} of {len(flagged)}: {D.DRAFT_BANNER}"),
    ]
    status = "PASS" if all(ok for _, ok, _ in checks) else "FAIL"
    llm = C.status()
    body = (
        R.tiles([("findings shown", str(len(flagged))), ("grounded explanations", str(explained_ok)),
                 ("grounded letters", str(letters_ok)), ("language model", "available" if llm["available"] else "not used")])
        + f"<p class='sub'>Language model: {R.esc(llm['model'])}"
        + ("" if llm["available"] else f" not used ({R.esc(llm.get('reason', ''))}); texts come from the deterministic template")
        + ". Green: in the finding. Red: not in the finding.</p>"
        + "<h2>Checks</h2>" + R.table(["Check", "Status", "Detail"], [[c, R.badge("PASS" if ok else "FAIL"), R.esc(d)] for c, ok, d in checks], raw=True)
        + "<h2>Tamper test</h2><p>" + highlight(planted, d0) + "</p>"
        + "<h2>Summary</h2>" + R.table(["Finding", "Concern", "Source", "Explanation", "Letter"], rows, raw=True)
        + "<h2>Explanations beside their evidence</h2>" + "".join(cards)
    )
    css = ("mark.ok{background:var(--okbg);color:var(--ok);padding:0 2px;border-radius:3px} "
           "mark.bad{background:var(--badbg);color:var(--bad);padding:0 2px;border-radius:3px;font-weight:700} "
           ".card{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:12px 16px;margin:12px 0} "
           ".two{display:grid;grid-template-columns:minmax(0,1fr) minmax(0,1.2fr);gap:16px} "
           "@media (max-width:900px){.two{grid-template-columns:1fr}} pre{white-space:pre-wrap;font-size:13px} .two table{table-layout:fixed;width:100%;overflow-wrap:anywhere}")
    out = settings.reports_dir / str(issue) / "07_explanations.html"
    R.write(out, R.page(f"{kind.title()} IFIC {issue}: explanations and letter drafts",
                        f"Step D2 of pm_pack/08. {R.badge(status)}", body, css),
            {"status": status, "checks": [[c, ok, d] for c, ok, d in checks], "sources": sources, "llm": llm})
    print(f"written {out}: {status}")
    for c, ok, d in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {c}  {d}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
