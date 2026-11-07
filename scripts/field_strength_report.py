#!/usr/bin/env python3
"""Step C3 visual proof: field strength at the Finnish border for the land-mobile notices of one Terrestrial IFIC.

    uv run python scripts/field_strength_report.py 3076     # writes reports/3076/02_field_strength.html

1. P.1546 curves (1 kW e.r.p., 30 m, land, 10 % time) against distance at 153, 425 and 793.5 MHz with free space,
   and every computed notice as a dot at its own distance and field strength.
2. Map with a line from each computed station to its nearest Finnish border point, coloured by concern.
3. The full trace of every high, medium and review case; the engine validation; the trigger table.
"""
from __future__ import annotations

import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT)]

from radar import report_html as R  # noqa: E402
from radar.calc import p1546 as P  # noqa: E402
from radar.config import settings  # noqa: E402
from radar.pipeline import terrestrial as TR  # noqa: E402
from scoring.geometry import Region  # noqa: E402

LEVELS = [("high", "High", "--c4"), ("medium", "Medium", "--c3"), ("review", "Review", "--c5"), ("low", "Low", "--c2")]
CURVES = [(153.0, "153 MHz", "--s1"), (425.0, "425 MHz", "--s2"), (793.5, "793.5 MHz", "--s3")]
EXTRA_CSS = """
:root { --c2:#9ec5ee; --c3:#eda100; --c4:#c2410c; --c5:#8b5cf6; --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a;
  --land:#ece4ea; --fin:#d9c3d2; --ink:#221a20; }
@media (prefers-color-scheme: dark) { :root { --c2:#3c6d9e; --c3:#c98500; --c4:#ea6a3a; --c5:#9f86f0; --s1:#3987e5;
  --s2:#d95926; --s3:#199e70; --land:#2c2430; --fin:#4a3a4f; --ink:#efe7ee; } }
.chart { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:12px; }
svg text { fill:var(--muted); font:11px -apple-system, system-ui, sans-serif; }
svg .grid { stroke:var(--line); } svg .fs { fill:none; stroke:var(--muted); stroke-width:1.5; stroke-dasharray:5 4; }
svg .curve { fill:none; stroke-width:2; }
.legend { display:flex; flex-wrap:wrap; gap:6px 16px; font-size:12px; margin:0 0 6px; }
.legend i { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:6px; vertical-align:-1px; }
.legend b { display:inline-block; width:16px; height:2px; margin-right:6px; vertical-align:3px; }
.lvl { display:inline-block; padding:1px 8px; border-radius:999px; font-size:11px; font-weight:700; color:#fff; }
details.f { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:8px 12px; margin:8px 0; }
.two { display:grid; grid-template-columns:repeat(auto-fit, minmax(360px, 1fr)); gap:16px; }
"""


def lvl(c: str) -> str:
    label, var = next(((l, v) for k, l, v in LEVELS if k == c), ("Not raised", "--s4"))
    return f'<span class="lvl" style="background:var({var})">{label}</span>'


def curve_chart(points) -> str:
    W, H, L, B, T = 1100, 340, 52, 32, 10
    pw, ph = W - L - 10, H - B - T
    dmin, dmax, emin, emax = 1, 1000, -40, 110
    x = lambda d: L + (math.log10(d) - math.log10(dmin)) / (math.log10(dmax) - math.log10(dmin)) * pw  # noqa: E731
    y = lambda e: T + ph - (min(max(e, emin), emax) - emin) / (emax - emin) * ph  # noqa: E731
    p = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Field strength against distance">']
    for e in range(-40, 111, 20):
        p.append(f'<line class="grid" x1="{L}" x2="{W - 10}" y1="{y(e):.1f}" y2="{y(e):.1f}"/><text x="{L - 6}" y="{y(e) + 4:.1f}" text-anchor="end">{e}</text>')
    for d in (1, 3, 10, 30, 100, 300, 1000):
        p.append(f'<line class="grid" x1="{x(d):.1f}" x2="{x(d):.1f}" y1="{T}" y2="{T + ph}"/><text x="{x(d):.1f}" y="{H - 12}" text-anchor="middle">{d} km</text>')
    ds = [round(10 ** (k / 10), 3) for k in range(0, 31)]
    fs = " ".join(f"{x(d):.1f},{y(P.free_space_dbuv_m(30.0, d)):.1f}" for d in ds)
    p.append(f'<polyline class="fs" points="{fs}"><title>Free space, 1 kW e.r.p.</title></polyline>')
    for f, label, var in CURVES:
        pts = " ".join(f"{x(d):.1f},{y(P.field_strength(f, [(d, 'Land')], 30.0, 30.0).e_dbuv_m):.1f}" for d in ds)
        p.append(f'<polyline class="curve" points="{pts}" style="stroke:var({var})"><title>P.1546, {label}, 1 kW, 30 m, land, 10 %</title></polyline>')
    colours = {k: v for k, _, v in LEVELS}
    for n, c, f in points:
        tip = (f"{n.administration} {n.site_name}: {n.freq_hz / 1e6:g} MHz, e.r.p. {n.erp_dbw:g} dBW, {c.distance_km:g} km, "
               f"E {c.e_dbuv_m:g} dB(uV/m), trigger {c.trigger_dbuv_m if c.trigger_dbuv_m is not None else 'none'}, {f.concern}")
        p.append(f'<circle cx="{x(max(c.distance_km, 1)):.1f}" cy="{y(c.e_dbuv_m):.1f}" r="5" style="fill:var({colours.get(f.concern, "--s4")});'
                 f'stroke:var(--card);stroke-width:1.5"><title>{R.esc(tip)}</title></circle>')
    p.append("</svg>")
    leg = ('<div class="legend">' + "".join(f'<span><b style="background:var({v})"></b>P.1546 {l}, 1 kW, 30 m, land</span>' for _, l, v in CURVES)
           + '<span><b style="background:var(--muted)"></b>free space, 1 kW</span>'
           + "".join(f'<span><i style="background:var({v})"></i>{l}</span>' for _, l, v in LEVELS) + "</div>")
    return f'<div class="chart">{leg}{"".join(p)}</div>'


def map_svg(points) -> str:
    region = Region.load()
    lon0, lon1, lat0, lat1 = 18.0, 36.0, 58.5, 70.5
    W = 620
    H = int(W * (lat1 - lat0) / ((lon1 - lon0) * math.cos(math.radians(64))))
    x = lambda lon: (lon - lon0) / (lon1 - lon0) * W  # noqa: E731
    y = lambda lat: (lat1 - lat) / (lat1 - lat0) * H  # noqa: E731
    colours = {k: v for k, _, v in LEVELS}
    p = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Stations and their nearest Finnish border point">']
    for code, polys in region.polygons.items():
        for poly in polys:
            d = " ".join(f"{x(lo):.1f},{y(la):.1f}" for lo, la in poly[0])
            p.append(f'<polygon points="{d}" style="fill:{"var(--fin)" if code == "FIN" else "var(--land)"};stroke:var(--line);stroke-width:.6"/>')
    for n, c, f in sorted(points, key=lambda t: TR.CONCERN_ORDER[t[2].concern]):
        if not (lon0 <= n.lon <= lon1 and lat0 <= n.lat <= lat1):
            continue
        col = colours.get(f.concern, "--s4")
        p.append(f'<line x1="{x(n.lon):.1f}" y1="{y(n.lat):.1f}" x2="{x(c.nearest[1]):.1f}" y2="{y(c.nearest[0]):.1f}" '
                 f'style="stroke:var({col});stroke-width:1.5;stroke-dasharray:3 2"/>'
                 f'<circle cx="{x(n.lon):.1f}" cy="{y(n.lat):.1f}" r="5" style="fill:var({col});stroke:var(--card);stroke-width:1.5">'
                 f'<title>{R.esc(f"{n.site_name}: {n.freq_hz / 1e6:g} MHz, {c.distance_km:g} km, E {c.e_dbuv_m:g} dB(uV/m), {f.concern}")}</title></circle>')
    p.append("</svg>")
    return f'<div class="chart">{"".join(p)}</div>'


def main() -> int:
    issue = int(sys.argv[1]) if len(sys.argv) > 1 else 3076
    run = TR.run(issue)
    by_id = {n.notice_id: n for n in run.ingest.notices}
    computed = [(by_id[f.notice_id], run.calcs[f.notice_id], f) for f in run.result.findings
                if run.calcs[f.notice_id].status == "computed"]
    counts = Counter(f.concern for f in run.result.findings)
    above_fs = [n.notice_id for n, c, _ in computed if c.e_dbuv_m > c.free_space_dbuv_m + 0.01]
    rising = []
    for f_mhz, _, _ in CURVES:
        es = [P.field_strength(f_mhz, [(d, "Land")], 30.0, 30.0).e_dbuv_m for d in (1, 10, 100, 1000)]
        if any(b >= a for a, b in zip(es, es[1:])):
            rising.append(f_mhz)
    status = "PASS" if not above_fs and not rising else "FAIL"

    cards = []
    for n, c, f in computed:
        if f.concern not in ("high", "medium", "review"):
            continue
        rows = [[i.name, f"{i.value}", i.unit, i.evidence_id] for i in f.calc.inputs]
        rows += [["E field strength at the border", f"{c.e_dbuv_m:g}", "dB(uV/m)", "P.1546"],
                 ["free space (upper bound)", f"{c.free_space_dbuv_m:g}", "dB(uV/m)", ""],
                 ["T/R 25-08 trigger + BC", "-" if c.trigger_dbuv_m is None else f"{c.trigger_dbuv_m:g}", "dB(uV/m)", f.calc.limit_evidence_id or "no criterion"],
                 ["margin (trigger - E)", "-" if c.margin_db is None else f"{c.margin_db:g}", "dB", "negative = exceeds"]]
        cards.append(f'<details class="f"><summary>{lvl(f.concern)} <b>{f.id}</b> &middot; {R.esc(n.administration)} {R.esc(n.site_name)} '
                     f'&middot; {n.change} {n.station_class} &middot; {n.freq_hz / 1e6:g} MHz &middot; {c.distance_km:g} km</summary>'
                     f"<p>{R.esc(f.reason)}</p>" + R.table(["Input", "Value", "Unit", "Evidence"], rows)
                     + f"<p class='sub'>{R.esc(' | '.join(f.calc.notes))}</p></details>")

    trig_rows = [[t.id, f"{t.f_min_mhz:g}-{t.f_max_mhz:g}", f"{t.threshold_dbuv_m:g}", f"{t.ref_bw_khz:g} kHz", t.review] for t in TR.thresholds()]
    status_rows = [[k, str(v)] for k, v in Counter(c.reason or "computed" for c in run.calcs.values()).most_common(12)]
    body = (
        R.tiles([("field strengths computed", str(len(computed))), ("high", str(counts["high"])), ("medium", str(counts["medium"])),
                 ("review", str(counts["review"])), ("low", str(counts["low"])), ("ITU validation cases", "52 of 52 at 0.0 dB")])
        + "<h2>Field strength against distance</h2><p class='sub'>Lines: P.1546-6 for 1 kW e.r.p., 30 m, land, 10 % of time, "
          "with free space dashed. Dots: every computed notice at its own e.r.p., height and path, coloured by concern. "
          "Hover a dot for its numbers.</p>" + curve_chart(computed)
        + '<div class="two"><div><h2>Path to the nearest Finnish border point</h2>' + map_svg(computed)
        + "</div><div><h2>Engine</h2>"
        + R.table(["Item", "Value"], [["Method", P.ENGINE], ["Validation", "52 ITU reference cases, max difference 0.0 dB (tests/test_p1546.py)"],
                                      ["Time / locations", "10 % / 50 % (T/R 25-08 Annex 1)"], ["Receiving height", "10 m, rural clutter 10 m"],
                                      ["Terrain", "not used (pathinfo 0): transmitting height above ground as effective height"],
                                      ["Sea", "zones outside every loaded country, 'Cold' sea (Baltic)"]])
        + "<h2>Special-interest stations on the same channel</h2><p class='sub'>For each computed notice, every co-channel "
          "station of the Traficom table within 1 000 km gets its own P.1546 field strength over the path to the station, at "
          "the station's antenna height. The worst station is shown; it decides the concern only when it is worse than the "
          "border check.</p>"
        + R.table(["Finding", "Notice", "MHz", "Border E", "Stations", "Worst station", "Distance km", "h2 m", "Station E", "Margin dB", "Decides"],
                  [[f.id, f"{n.administration} {n.site_name}", f"{n.freq_hz / 1e6:g}", f"{c.e_dbuv_m:g}", str(len(c.stations)),
                    c.stations[0]["number"], f"{c.stations[0]['distance_km']:g}", f"{c.stations[0]['h2_m']:g}",
                    f"{c.stations[0]['e_dbuv_m']:g}", "-" if c.stations[0]["margin_db"] is None else f"{c.stations[0]['margin_db']:g}",
                    "yes" if TR.station_decides(n, c) else "no"]
                   for n, c, f in computed if c.stations])
        + "<h2>T/R 25-08 triggers</h2>" + R.table(["Row", "MHz", "dB(uV/m)", "Per", "Review"], trig_rows)
        + "</div></div>"
        + "<h2>Cases for review</h2><p class='sub'>Every high, medium and review finding with its full trace.</p>" + "".join(cards)
        + "<h2>Why the other notices were not computed</h2>" + R.table(["Reason", "Notices"], status_rows)
    )
    summary = {"status": status, "issue": issue, "computed": len(computed), "concern": dict(counts),
               "above_free_space": above_fs, "rising_curves": rising,
               "cases": [{"id": f.id, "notice": n.notice_id, "site": n.site_name, "mhz": n.freq_hz / 1e6, "km": c.distance_km,
                          "e": c.e_dbuv_m, "trigger": c.trigger_dbuv_m, "margin": c.margin_db, "concern": f.concern}
                         for n, c, f in computed if f.concern in ("high", "medium", "review")]}
    out = settings.reports_dir / str(issue) / "02_field_strength.html"
    R.write(out, R.page(f"Terrestrial IFIC {issue}: field strength at the Finnish border",
                        f"Step C3 of pm_pack/08. radar.calc.p1546 and radar.pipeline.terrestrial; indicative. {R.badge(status)}",
                        body, EXTRA_CSS), summary)
    print(f"written {out}: {status}; computed {len(computed)}; {dict(counts)}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
