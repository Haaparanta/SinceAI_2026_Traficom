#!/usr/bin/env python3
"""Step C2 visual proof: what changed in a Terrestrial IFIC and how it compares with the previous issue.

    uv run python scripts/diff_report.py 3076 3075     # writes reports/3076/01_diff.html and .summary.json

Stacked bars of new / modified / withdrawn / recorded per administration, the issue-to-issue comparison per
administration and per land-mobile band and station class, Finland's neighbours, and a map of every located
notice around Finland coloured by change, with the distance to Finland in the tooltip.
"""
from __future__ import annotations

import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT)]

from radar import report_html as R  # noqa: E402
from radar.adapters import terrestrial_ific as T  # noqa: E402
from radar.config import settings  # noqa: E402
from radar.pipeline import diff as D  # noqa: E402
from radar.pipeline import geography as G  # noqa: E402
from scoring.geometry import Region  # noqa: E402

CHANGES = [("new", "New (ADD)", "--s1"), ("modified", "Modified (MODIFY)", "--s3"),
           ("withdrawn", "Withdrawn (SUPPRESS)", "--s4"), ("unchanged", "Recorded (RECORDED)", "--s5")]
EXTRA_CSS = """
:root { --s1:#2a78d6; --s3:#eda100; --s4:#8a8780; --s5:#1baf7a; --land:#ece4ea; --fin:#d9c3d2; --ink:#221a20; }
@media (prefers-color-scheme: dark) { :root { --s1:#3987e5; --s3:#c98500; --s4:#9a978f; --s5:#199e70;
  --land:#2c2430; --fin:#4a3a4f; --ink:#efe7ee; } }
.chart { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:12px; }
svg text { fill:var(--muted); font:11px -apple-system, system-ui, sans-serif; }
.legend { display:flex; flex-wrap:wrap; gap:6px 16px; font-size:12px; margin:0 0 6px; }
.legend i { display:inline-block; width:10px; height:10px; border-radius:2px; margin-right:6px; vertical-align:-1px; }
.two { display:grid; grid-template-columns:repeat(auto-fit, minmax(360px, 1fr)); gap:16px; }
td.up { color:var(--bad); } td.down { color:var(--ok); }
"""


def legend() -> str:
    return '<div class="legend">' + "".join(f'<span><i style="background:var({v})"></i>{l}</span>' for _, l, v in CHANGES) + "</div>"


def stacked_bars(by_adm: dict, top: int = 15) -> str:
    adms = sorted(by_adm, key=lambda a: -sum(by_adm[a].values()))[:top]
    mx = max(sum(by_adm[a].values()) for a in adms) or 1
    W, L, row = 1100, 70, 22
    H = len(adms) * row + 10
    pw = W - L - 70
    p = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Notices per administration by change">']
    for i, a in enumerate(adms):
        y = i * row + 4
        x = L
        p.append(f'<text x="{L - 8}" y="{y + 13}" text-anchor="end" style="fill:var(--ink)">{R.esc(a)}</text>')
        for k, label, var in CHANGES:
            n = by_adm[a][k]
            if not n:
                continue
            w = pw * n / mx
            p.append(f'<rect x="{x:.1f}" y="{y}" width="{max(w - 2, 1):.1f}" height="16" rx="3" style="fill:var({var})">'
                     f'<title>{R.esc(a)}: {n} {label.lower()}</title></rect>')
            x += w
        p.append(f'<text x="{x + 6:.1f}" y="{y + 13}">{sum(by_adm[a].values()):,}</text>')
    p.append("</svg>")
    return f'<div class="chart">{legend()}{"".join(p)}</div>'


def map_svg(notices, extra) -> tuple[str, list[dict]]:
    region = Region.load()
    lon0, lon1, lat0, lat1 = 4.0, 42.0, 53.5, 71.5
    W = 620
    H = int(W * (lat1 - lat0) / ((lon1 - lon0) * math.cos(math.radians(63))))
    x = lambda lon: (lon - lon0) / (lon1 - lon0) * W  # noqa: E731
    y = lambda lat: (lat1 - lat) / (lat1 - lat0) * H  # noqa: E731
    colours = {k: v for k, _, v in CHANGES}
    p = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Located notices around Finland">']
    for code, polys in region.polygons.items():
        fill = "var(--fin)" if code == "FIN" else "var(--land)"
        for poly in polys:
            d = " ".join(f"{x(lo):.1f},{y(la):.1f}" for lo, la in poly[0])
            p.append(f'<polygon points="{d}" style="fill:{fill};stroke:var(--line);stroke-width:.6"><title>{R.esc(region.names[code])}</title></polygon>')
    shown = []
    for n in notices:
        if n.lat is None or not (lon0 <= n.lon <= lon1 and lat0 <= n.lat <= lat1):
            continue
        d = round(G.distance_to_finland_km(round(n.lat, 4), round(n.lon, 4)), 1)
        e = extra[n.notice_id]
        shown.append({"notice_id": n.notice_id, "adm": n.administration, "site": n.site_name, "change": n.change,
                      "class": n.station_class, "mhz": None if n.freq_hz is None else n.freq_hz / 1e6,
                      "erp_dbw": n.erp_dbw, "distance_km": d, "land_mobile": e.land_mobile, "lat": n.lat, "lon": n.lon})
        tip = (f"{n.administration} {n.site_name or ''}: {n.change}, {n.station_class}, "
               f"{(n.freq_hz or 0) / 1e6:g} MHz, e.r.p. {n.erp_dbw} dBW, {d:.0f} km from Finland (fxm_terra.terrakey={n.notice_id})")
        shape = (f'<circle cx="{x(n.lon):.1f}" cy="{y(n.lat):.1f}" r="4.5"' if e.land_mobile else
                 f'<rect x="{x(n.lon) - 4:.1f}" y="{y(n.lat) - 4:.1f}" width="8" height="8" rx="1.5"')
        p.append(f'{shape} style="fill:var({colours[n.change]});stroke:var(--card);stroke-width:1.5"><title>{R.esc(tip)}</title>'
                 f'{"</circle>" if e.land_mobile else "</rect>"}')
    p.append("</svg>")
    leg = legend().replace("</div>", '<span>Circle = land mobile, square = other (fixed, ...)</span></div>')
    return f'<div class="chart">{leg}{"".join(p)}</div>', shown


def main() -> int:
    cur_i = int(sys.argv[1]) if len(sys.argv) > 1 else 3076
    prev_i = int(sys.argv[2]) if len(sys.argv) > 2 else cur_i - 1
    cur, prev = T.load(cur_i), T.load(prev_i)
    d = D.compare(cur, prev)

    all_new = d.change["new"] == len(cur.notices)
    sums_ok = sum(d.change.values()) == len(cur.notices) and sum(c for _, _, c in d.adm_compare) == len(cur.notices)
    status = "PASS" if not all_new and sums_ok else "FAIL"

    chart = stacked_bars(d.by_adm)
    map_html, shown = map_svg(cur.notices, cur.extra)
    near = [s for s in shown if s["distance_km"] <= 300]
    adm_rows = []
    for a, p_, c in d.adm_compare[:20]:
        delta = c - p_
        cls = "up" if delta > 0 else "down" if delta < 0 else ""
        adm_rows.append([a, f"{p_:,}", f"{c:,}", f'<span class="{cls}">{delta:+,}</span>'] +
                        [str(d.by_adm.get(a, Counter())[k]) for k, _, _ in CHANGES])
    bc_rows = [[b, c, f"{p_:,}", f"{n:,}", f"{n - p_:+,}"] for b, c, p_, n in d.band_class_compare if p_ or n]
    neigh_rows = [[a] + [str(cnt[k]) for k, _, _ in CHANGES] + [str(sum(cnt.values()))] for a, cnt in d.neighbours.items()]
    near_rows = [[s["adm"], s["site"] or "", s["change"], s["class"] or "", f"{s['mhz']:g}" if s["mhz"] else "",
                  "" if s["erp_dbw"] is None else f"{s['erp_dbw']:g}", f"{s['distance_km']:.0f}", f"<code>fxm_terra.terrakey={s['notice_id']}</code>"]
                 for s in sorted(near, key=lambda s: s["distance_km"])[:40]]

    body = (
        R.tiles([(f"notices in {cur_i}", f"{len(cur.notices):,}"), (f"notices in {prev_i}", f"{len(prev.notices):,}"),
                 ("new / modified / withdrawn / recorded", " / ".join(f"{d.change[k]:,}" for k, _, _ in CHANGES)),
                 ("land mobile", f"{cur.stats['land_mobile']:,}"), ("located within 300 km of Finland", str(len(near)))])
        + f"<h2>What changed in {cur_i}, per administration</h2><p class='sub'>The change comes from the Bureau's intent on "
          "each notice (each extract is the change set of its issue). Top 15 administrations by notices.</p>" + chart
        + "<h2>Within 300 km of Finland</h2><p class='sub'>Every located notice in the map window; hover a marker for its "
          "notice, frequency, e.r.p. and distance. Field strength at the border follows in step C3.</p>"
        + f'<div class="two"><div>{map_html}</div><div>'
        + R.table(["Adm", "Site", "Change", "Class", "MHz", "e.r.p. dBW", "km", "Locator"], near_rows, raw=True) + "</div></div>"
        + "<h2>Finland's neighbours</h2>"
        + R.table(["Adm"] + [l for _, l, _ in CHANGES] + ["Total"], neigh_rows)
        + f"<h2>{prev_i} to {cur_i}: notices per administration</h2>"
        + R.table(["Adm", str(prev_i), str(cur_i), "Change"] + [l for _, l, _ in CHANGES], adm_rows, raw=True)
        + f"<h2>{prev_i} to {cur_i}: land-mobile notices per band and station class</h2>"
        + R.table(["Band", "Class", str(prev_i), str(cur_i), "Change"], bc_rows)
        + "<h2>Cross-check</h2>"
        + R.table(["Check", "Result"], [
            [f"{cur_i} notice IDs also present in {prev_i}", str(d.shared_notice_ids)],
            [f"MODIFY or SUPPRESS targets that are notices of {prev_i}", str(d.targets_in_previous)],
            ["Interpretation", "each extract is a change set; targets point into the Master Register, so the trend comparison above is the diff"],
            ["Every notice classed new", "no" if not all_new else "YES: key problem"],
            ["Counts add up", "yes" if sums_ok else "NO"]])
    )
    summary = {"status": status, "current": cur_i, "previous": prev_i, "change": dict(d.change),
               "stats_current": cur.stats, "stats_previous": prev.stats,
               "neighbours": {a: dict(c) for a, c in d.neighbours.items()},
               "shared_notice_ids": d.shared_notice_ids, "targets_in_previous": d.targets_in_previous,
               "within_300_km": len(near), "near": sorted(near, key=lambda s: s["distance_km"])[:40]}
    out = settings.reports_dir / str(cur_i) / "01_diff.html"
    R.write(out, R.page(f"Terrestrial IFIC {cur_i}: what changed",
                        f"Step C2 of pm_pack/08. radar.adapters.terrestrial_ific and radar.pipeline.diff. {R.badge(status)}",
                        body, EXTRA_CSS), summary)
    print(f"written {out}: {status}; change {dict(d.change)}; within 300 km {len(near)}; neighbours "
          f"{ {a: sum(c.values()) for a, c in d.neighbours.items()} }")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
