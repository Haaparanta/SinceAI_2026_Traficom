#!/usr/bin/env python3
"""Step C1 visual proof: worst-case pfd of GSO downlinks against RR Article 21 Table 21-4.

    uv run python scripts/pfd_report.py 3074       # writes reports/3074/06_pfd.html and .summary.json

Margin histogram with zero marked, status counts, the hand-worked check, the ten worst cases with their full
trace, the limit rows used (with review status), and why the remaining medium notices have no pfd.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT)]

from radar import report_html as R  # noqa: E402
from radar.calc import pfd as PFD  # noqa: E402
from radar.config import settings  # noqa: E402
from radar.pipeline import assemble  # noqa: E402

EXTRA_CSS = """
:root { --s1:#2a78d6; --s2:#c2410c; --ink:#221a20; }
@media (prefers-color-scheme: dark) { :root { --s1:#3987e5; --s2:#ea6a3a; --ink:#efe7ee; } }
.chart { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:12px; }
svg text { fill:var(--muted); font:11px -apple-system, system-ui, sans-serif; }
svg .grid { stroke:var(--line); } svg .zero { stroke:var(--ink); stroke-width:1.5; stroke-dasharray:4 3; }
.legend { display:flex; gap:16px; font-size:12px; margin:0 0 6px; }
.legend i { display:inline-block; width:10px; height:10px; border-radius:2px; margin-right:6px; vertical-align:-1px; }
details.f { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:8px 12px; margin:8px 0; }
"""


def histogram(margins: list[tuple[float, bool]]) -> str:
    lo, hi, step = -10, 30, 1
    bins = [[0, 0] for _ in range((hi - lo) // step)]
    for m, steer in margins:
        i = min(max(int((m - lo) // step), 0), len(bins) - 1)
        bins[i][0 if steer else 1] += 1
    W, H, L, B, T = 1100, 260, 48, 30, 10
    pw, ph = W - L - 10, H - B - T
    top = max(a + b for a, b in bins) or 1
    bw = pw / len(bins)
    x = lambda v: L + (v - lo) / (hi - lo) * pw  # noqa: E731
    p = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Margin to the Article 21 limit">']
    for k in range(5):
        v = top * k / 4
        y = T + ph - ph * k / 4
        p.append(f'<line class="grid" x1="{L}" x2="{W - 10}" y1="{y:.1f}" y2="{y:.1f}"/><text x="{L - 6}" y="{y + 4:.1f}" text-anchor="end">{v:.0f}</text>')
    for i, (st, fx) in enumerate(bins):
        y = T + ph
        for n, var, label in ((st, "--s2", "steerable beam"), (fx, "--s1", "fixed beam")):
            if not n:
                continue
            h = ph * n / top
            y -= h
            a = lo + i * step
            p.append(f'<rect x="{L + i * bw + 1:.1f}" y="{y:.1f}" width="{bw - 2:.1f}" height="{h:.1f}" style="fill:var({var})">'
                     f'<title>{a} to {a + step} dB: {n} group(s), {label}</title></rect>')
    p.append(f'<line class="zero" x1="{x(0):.1f}" x2="{x(0):.1f}" y1="{T}" y2="{T + ph}"/>'
             f'<text x="{x(0) + 4:.1f}" y="{T + 12}" style="fill:var(--ink)">limit</text>'
             f'<text x="{x(-5):.1f}" y="{T + 12}" text-anchor="middle">exceeds</text>'
             f'<text x="{x(15):.1f}" y="{T + 12}" text-anchor="middle">below the limit</text>')
    for v in range(lo, hi + 1, 5):
        p.append(f'<text x="{x(v):.1f}" y="{H - 10}" text-anchor="middle">{v} dB</text>')
    p.append("</svg>")
    legend = ('<div class="legend"><span><i style="background:var(--s2)"></i>Steerable beam (can point at Finland)</span>'
              '<span><i style="background:var(--s1)"></i>Fixed beam (pointing unknown)</span></div>')
    return f'<div class="chart">{legend}{"".join(p)}</div>'


def main() -> int:
    issue = int(sys.argv[1]) if len(sys.argv) > 1 else 3074
    run = assemble.run(issue)
    P = run.pfd
    rg = {r.group_id: r for r in run.rows}
    bn = {n.notice_id: n for n in run.ingest.notices}
    comp = [(g, r) for g, r in P.items() if r.status == "computed"]
    status = Counter(r.status for r in P.values())

    # Hand-worked check (pm_pack/08 C1): -40 dBW/Hz, 0 dBi, 4 kHz, 38 000 km
    hand = PFD.pfd_db(-40, 0, 4000, 38e6)
    vectors = [("Spreading loss at 38 000 km", PFD.spreading_loss_db(38e6), 162.59, 0.05),
               ("pfd for -40 dBW/Hz, 0 dBi, 4 kHz, 38 000 km: -40 + 36.02 - 162.59 (solution plan 01 says -130.6; that is a 36 dB slip)",
                hand, -166.57, 0.05),
               ("CHINASAT-H by hand: -54 + 50 + 60 - 163.21", PFD.pfd_db(-54, 50, 1e6, 40796.8e3), -107.21, 0.05),
               ("Limit 17.7-19.3 GHz GSO at 8.036 deg: -115 + 0.5 x 3.036", next(r for r in PFD.limits() if r.id == "17700-19300_gso").limit(8.036), -113.48, 0.01)]
    vec_ok = all(abs(v - e) <= t for _, v, e, t in vectors)
    pfd_range_ok = all(-250 <= r.pfd_db <= -80 for _, r in comp)
    unlabelled = [f.id for f in run.result.findings if f.calc.method == "pfd_gso_worst_case" and f.calc.label != "indicative"]
    ok = vec_ok and pfd_range_ok and not unlabelled

    worst = sorted(comp, key=lambda t: t[1].margin_db)[:10]
    cards = []
    for g, r in worst:
        w = r.worst
        n = bn[rg[g].notice_id]
        rows = [["P_d max power density", f"{w['p_d_dbw_hz']:g} dBW/Hz", f"emiss grp_id={g} seq_no={w['emission_seq_no']} ({w['designation']})"],
                ["G max beam gain", f"{w['gain_dbi']:g} dBi", "s_beam; " + ("steerable" if w["steerable"] else "fixed, pointing unknown")],
                ["B bandwidth", f"{PFD.fmt_bw(w['bandwidth_hz'])}", f"min(reference {PFD.fmt_bw(w['ref_bw_hz'])}, emission)"],
                ["d slant range", f"{w['slant_range_km']:g} km", f"{w['point']} ({w['lat']} N, {w['lon']} E)"],
                ["delta angle of arrival", f"{w['elevation_deg']:g} deg", "geography"],
                ["spreading loss", f"{w['spreading_loss_db']:g} dB", "10 log10(4 pi d^2)"],
                ["pfd", f"{r.pfd_db:g} dB(W/m2)", PFD.FORMULA.split(";")[0]],
                ["limit", f"{r.limit_db:g} dB(W/m2)", f"{w['limit_row'].id}, RR page {w['limit_row'].page}"],
                ["margin", f"{r.margin_db:g} dB", "limit - pfd; negative = exceeds"]]
        cards.append(f'<details class="f"><summary><b>{R.esc(n.administration)} {R.esc(n.network_name)}</b> &middot; group {g} &middot; '
                     f'{rg[g].freq_min_hz / 1e6:g}-{rg[g].freq_max_hz / 1e6:g} MHz &middot; margin <b>{r.margin_db:g} dB</b></summary>'
                     + R.table(["Input", "Value", "Source"], rows) + f"<p class='sub'>{R.esc(' | '.join(r.notes))}</p></details>")

    used = Counter(r.worst["limit_row"].id for _, r in comp)
    lim_rows = [[row.id, f"{row.band_min_mhz:g}-{row.band_max_mhz:g}", row.orbit, f"{row.ref_bw_hz:g}", row.segments_text(),
                 row.page, str(used.get(row.id, 0)), row.review] for row in PFD.limits() if row.applies_to_finland]

    medium = [f for f in run.result.findings if f.concern == "medium"]
    why = Counter()
    for f in medium:
        res = P.get(f.group_id)
        why["pfd computed, within 15 dB of the limit" if res and res.status == "computed" else
            "no Article 21 limit in this band" if res and res.status == "no_limit" else
            "non-GSO: pfd not evaluated in C1" if bn[f.notice_id].orbit == "NGSO" else
            "uplink near Finland (pfd not applicable)" if "uplink" in run.scores[f.group_id].rule else
            f"other: {res.status if res else 'not eligible'}"] += 1

    exceed = [(g, r) for g, r in comp if r.margin_db < 0]
    body = (
        R.tiles([("GSO downlink groups eligible", str(len(P))), ("computed", str(status["computed"])),
                 ("no limit in band", str(status["no_limit"])), ("input missing", str(status["no_input"])),
                 ("exceed (steerable / fixed)", f"{sum(1 for _, r in exceed if r.worst['steerable'])} / {sum(1 for _, r in exceed if not r.worst['steerable'])}"),
                 ("notices exceeding", str(len({rg[g].notice_id for g, _ in exceed})))])
        + "<h2>Margin to the RR Article 21 limit</h2><p class='sub'>One bar per 1 dB, every computed group. Left of the dashed "
          "line the worst case exceeds the limit. Worst case means peak beam gain towards Finland: real for a steerable beam, "
          "an assumption for a fixed one.</p>" + histogram([(r.margin_db, bool(r.worst["steerable"])) for _, r in comp])
        + "<h2>Hand-worked checks</h2>"
        + R.table(["Case", "Computed", "Expected", "Status"],
                  [[c, f"{v:.2f}", f"{e:g}", R.badge("PASS" if abs(v - e) <= t else "FAIL")] for c, v, e, t in vectors], raw=True)
        + "<h2>Ten smallest margins</h2>" + "".join(cards)
        + "<h2>Why 99 notices stay medium</h2>" + R.table(["Lead group", "Notices"], [[k, str(v)] for k, v in why.most_common()])
        + "<h2>Limit rows</h2><p class='sub'>data/reference/pfd_limits.csv, transcribed from RR 2024 Vol. 1 Article 21 "
          "Table 21-4 (Rev.WRC-23). Every row needs a second reviewer (pm_pack/06).</p>"
        + R.table(["Row", "MHz", "Orbit", "Ref bw Hz", "Limit by angle of arrival", "RR page", "Worst cases", "Review"], lim_rows)
    )
    summary = {"status": "PASS" if ok else "FAIL", "issue": issue, "pfd_status": dict(status), "vectors_ok": vec_ok,
               "pfd_range_ok": pfd_range_ok, "exceeding_groups": len(exceed),
               "exceeding_notices": sorted({rg[g].notice_id for g, _ in exceed}), "medium_why": dict(why),
               "worst": [{"group": g, "notice": rg[g].notice_id, "margin_db": r.margin_db, "pfd": r.pfd_db, "limit": r.limit_db} for g, r in worst]}
    out = settings.reports_dir / str(issue) / "06_pfd.html"
    R.write(out, R.page(f"Space IFIC {issue}: worst-case pfd",
                        f"Step C1 of pm_pack/08. radar.calc.pfd; indicative upper bound. {R.badge('PASS' if ok else 'FAIL')}",
                        body, EXTRA_CSS), summary)
    print(f"written {out}: {summary['status']}; {dict(status)}; exceeding notices {len(summary['exceeding_notices'])}; medium why {dict(why)}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
