#!/usr/bin/env python3
"""Step B3 visual proof: which stations in one Space IFIC can reach Finland.

    uv run python scripts/geography_report.py 3074     # writes reports/3074/03_geography.html and .summary.json

1. Elevation chart: highest and lowest elevation over the Finnish reference points as a function of GSO
   longitude (the expected hump), with every GSO notice of the issue as a dot.
2. Map of Finland and its neighbours with the reference points and every located earth station within
   the near-border distance.
3. Non-GSO table: orbit, latitude reach at 0 and 10 deg elevation, verdict.
4. Funnel B2 -> B3 by group and notice, and the test vectors from pm_pack/08.
"""
from __future__ import annotations

import math
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT)]

import duckdb  # noqa: E402

from radar import report_html as R  # noqa: E402
from radar.adapters import space_ific  # noqa: E402
from radar.config import settings  # noqa: E402
from radar.pipeline import geography as G  # noqa: E402
from radar.pipeline import relevance as rel  # noqa: E402
from scoring.geometry import Region  # noqa: E402

VERDICT = [("visible", "Visible (10 deg or more)", "--s1"), ("low_elevation", "Low elevation (0 to 10 deg)", "--s2"),
           ("not_visible", "Below the horizon", "--s4"), ("unknown", "Unknown", "--s5")]
EXTRA_CSS = """
:root { --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a; --s4:#8a8780; --s5:#e87ba4; --land:#ece4ea; --fin:#d9c3d2; --ink:#221a20; }
@media (prefers-color-scheme: dark) { :root { --s1:#3987e5; --s2:#d95926; --s3:#199e70; --s4:#9a978f; --s5:#d55181;
  --land:#2c2430; --fin:#4a3a4f; --ink:#efe7ee; } }
.chart { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:12px; }
svg text { fill:var(--muted); font:11px -apple-system, system-ui, sans-serif; }
svg .grid { stroke:var(--line); stroke-width:1; }
svg .ref { stroke:var(--muted); stroke-width:1; stroke-dasharray:4 4; }
svg .curve { fill:none; stroke-width:2; }
svg circle.dot { stroke:var(--card); stroke-width:2; }
svg circle.dot:hover { stroke:var(--ink); }
.legend { display:flex; flex-wrap:wrap; gap:6px 16px; font-size:12px; margin:0 0 6px; }
.legend i { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:6px; vertical-align:-1px; }
.legend b { display:inline-block; width:16px; height:2px; margin-right:6px; vertical-align:3px; }
.two { display:grid; grid-template-columns:repeat(auto-fit, minmax(360px, 1fr)); gap:16px; }
"""


def elevation_chart(gso_rows) -> str:
    W, H, L, B, T = 1100, 320, 48, 30, 10
    pw, ph = W - L - 10, H - B - T
    x = lambda lon: L + (lon + 180) / 360 * pw  # noqa: E731
    y = lambda el: T + ph - (max(min(el, 25), -10) + 10) / 35 * ph  # noqa: E731
    p = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Elevation from Finland against GSO longitude">']
    for el in (-10, 0, 10, 20):
        cls = "ref" if el in (0, 10) else "grid"
        p.append(f'<line class="{cls}" x1="{L}" x2="{W - 10}" y1="{y(el):.1f}" y2="{y(el):.1f}"/>'
                 f'<text x="{L - 6}" y="{y(el) + 4:.1f}" text-anchor="end">{el}&#176;</text>')
    for lon in range(-180, 181, 60):
        p.append(f'<line class="grid" x1="{x(lon):.1f}" x2="{x(lon):.1f}" y1="{T}" y2="{T + ph}"/>'
                 f'<text x="{x(lon):.1f}" y="{H - 10}" text-anchor="middle">{abs(lon)}&#176;{"W" if lon < 0 else "E" if lon > 0 else ""}</text>')
    hi_pts, lo_pts = [], []
    for k in range(0, 721):
        lon = -180 + k * 0.5
        els = [G.gso_look(la, lo, lon)[0] for _, la, lo in G.reference_points()]
        hi_pts.append(f"{x(lon):.1f},{y(max(els)):.1f}")
        lo_pts.append(f"{x(lon):.1f},{y(min(els)):.1f}")
    p.append(f'<polyline class="curve" points="{" ".join(hi_pts)}" style="stroke:var(--s3)"><title>Highest elevation over the reference points</title></polyline>')
    p.append(f'<polyline class="curve" points="{" ".join(lo_pts)}" style="stroke:var(--s4)"><title>Lowest elevation over the reference points</title></polyline>')
    colours = {k: v for k, _, v in VERDICT}
    for n, g in gso_rows:
        lon = n.longitude_deg
        el = g.detail["max_elevation_deg"]
        tip = f"{n.administration} {n.network_name}, {lon:g} deg, highest elevation {el:.1f} deg at {g.detail['max_elevation_point']}: {g.relevance}"
        p.append(f'<circle class="dot" cx="{x(lon):.1f}" cy="{y(el):.1f}" r="5" style="fill:var({colours[g.relevance]})"><title>{R.esc(tip)}</title></circle>')
    p.append(f'<text x="{x(28) + 6:.1f}" y="{y(22.5):.1f}">Hanko (highest)</text><text x="{x(28) + 6:.1f}" y="{y(9.5):.1f}">Utsjoki (lowest)</text>')
    p.append("</svg>")
    legend = ('<div class="legend">' + "".join(f'<span><i style="background:var({v})"></i>{l}</span>' for k, l, v in VERDICT if k != "unknown")
              + '<span><b style="background:var(--s3)"></b>Highest over the reference points</span>'
              + '<span><b style="background:var(--s4)"></b>Lowest over the reference points</span></div>')
    return f'<div class="chart">{legend}{"".join(p)}</div>'


def map_svg(stations) -> str:
    region = Region.load()
    lon0, lon1, lat0, lat1 = 4.0, 42.0, 53.5, 71.5
    W = 560
    k = math.cos(math.radians(63))
    H = int(W * (lat1 - lat0) / ((lon1 - lon0) * k))
    x = lambda lon: (lon - lon0) / (lon1 - lon0) * W  # noqa: E731
    y = lambda lat: (lat1 - lat) / (lat1 - lat0) * H  # noqa: E731
    p = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Finland, reference points and nearby earth stations">']
    for code, polys in region.polygons.items():
        fill = "var(--fin)" if code == "FIN" else "var(--land)"
        for poly in polys:
            d = " ".join(f"{x(lo):.1f},{y(la):.1f}" for lo, la in poly[0])
            p.append(f'<polygon points="{d}" style="fill:{fill};stroke:var(--line);stroke-width:.6"><title>{R.esc(region.names[code])}</title></polygon>')
    for name, la, lo in G.reference_points():
        p.append(f'<circle cx="{x(lo):.1f}" cy="{y(la):.1f}" r="4" style="fill:var(--ink)"><title>{name} {la} N {lo} E</title></circle>'
                 f'<text x="{x(lo) + 6:.1f}" y="{y(la) + 4:.1f}" style="fill:var(--ink)">{name}</text>')
    for s in stations:
        if not (lon0 <= s["lon"] <= lon1 and lat0 <= s["lat"] <= lat1):
            continue
        tip = f"{s['name']} ({s['country']}) {s['distance_km']:.0f} km from Finland; {s['groups']} uplink group(s)"
        p.append(f'<rect x="{x(s["lon"]) - 5:.1f}" y="{y(s["lat"]) - 5:.1f}" width="10" height="10" rx="2" '
                 f'style="fill:var(--s2);stroke:var(--card);stroke-width:2"><title>{R.esc(tip)}</title></rect>')
    p.append("</svg>")
    legend = ('<div class="legend"><span><i style="background:var(--ink)"></i>Reference point</span>'
              '<span><i style="background:var(--s2);border-radius:2px"></i>Earth station within '
              f'{G.NEAR_BORDER_KM:.0f} km (uplink groups in this issue)</span></div>')
    return f'<div class="chart">{legend}{"".join(p)}</div>'


def main() -> int:
    issue = int(sys.argv[1]) if len(sys.argv) > 1 else 3074
    ing = space_ific.load(issue)
    with duckdb.connect(str(space_ific.db_path(issue)), read_only=True) as con:
        named = rel.finland_named(con)
        types = dict(con.execute('SELECT CAST(ntc_id AS VARCHAR), ntc_type FROM notice').fetchall())
        geo = G.for_issue(ing.notices, con)
        rows = rel.screen(ing.notices, named=named)
    b2_groups = {r.group_id for r in rows if r.candidate}
    b2_notices = {r.notice_id for r in rows if r.candidate}
    G.apply(rows, geo, types)
    by_notice = {n.notice_id: n for n in ing.notices}

    # test vectors (pm_pack/08 step B3)
    vectors = [("60 N, satellite on the same meridian", G.gso_look(60, 25, 25)[0], 21.9, 0.5),
               ("70 N, satellite on the same meridian", G.gso_look(70, 25, 25)[0], 11.5, 0.5),
               ("60 N, 72.4 deg of longitude away (horizon)", G.gso_look(60, 0, 72.4)[0], 0.0, 0.5),
               ("Slant range at 60 N, same meridian, km", G.gso_look(60, 25, 25)[1], 39364.5, 50)]
    vec_ok = all(abs(v - e) <= tol for _, v, e, tol in vectors)
    gso_rows = [(by_notice[k], g) for k, g in geo.by_notice.items() if g.method == "gso_elevation"]
    impossible = [n.notice_id for n, g in gso_rows if g.detail["max_elevation_deg"] > 23.0]
    status = "PASS" if vec_ok and not impossible else "FAIL"

    # near-border earth stations, aggregated over uplink groups
    agg: dict[tuple, dict] = {}
    for gid, g in geo.by_group.items():
        if g.method == "earth_station_distance" and g.relevance == "near_border":
            s = g.detail["nearest"]
            key = (s["name"], s["country"])
            a = agg.setdefault(key, {**s, "groups": 0, "notices": set()})
            a["groups"] += 1
    for r in rows:
        if "uplink_near_finland" in r.paths:
            g = geo.by_group.get(r.group_id)
            if g:
                agg[(g.detail["nearest"]["name"], g.detail["nearest"]["country"])]["notices"].add(r.notice_id)
    stations = sorted(agg.values(), key=lambda s: s["distance_km"])

    ngso = [(by_notice[k], g) for k, g in geo.by_notice.items() if types.get(k) == "N"]
    ngso_rows = []
    for n, g in sorted(ngso, key=lambda t: (t[1].relevance, t[0].network_name)):
        bo = g.detail.get("best_orbit") or {}
        ngso_rows.append([n.notice_id, n.administration, n.network_name, R.badge(g.relevance.upper().replace("_", " ")),
                          R.esc(bo.get("inclination_deg", "")), R.esc(bo.get("apogee_km", "")),
                          R.esc(g.detail.get("lat_limit_0deg", "")), R.esc(g.detail.get("lat_limit_10deg", "")), R.esc(g.note)])

    def stage(by):
        f = (lambda pred: len({r.notice_id for r in rows if pred(r)})) if by == "notice" else (lambda pred: sum(1 for r in rows if pred(r)))
        return [("Candidates after frequency (B2)", len(b2_notices) if by == "notice" else len(b2_groups)),
                ("Dropped by geography (notices: at least one group)", f(lambda r: (r.group_id in b2_groups) and not r.candidate)),
                ("Uplinks promoted: earth station near or inside Finland (notices: at least one group)", f(lambda r: "uplink_near_finland" in r.paths)),
                ("Candidates after geography (B3)", f(lambda r: r.candidate))]

    funnel_rows = [[l, f"{a:,}", f"{b:,}"] for (l, a), (_, b) in zip(stage("group"), stage("notice"))]
    verdicts = Counter(g.relevance for g in geo.by_notice.values())
    body = (
        R.tiles([("GSO notices visible or low", str(sum(1 for _, g in gso_rows if g.relevance in ("visible", "low_elevation")))),
                 ("GSO notices below the horizon", str(sum(1 for _, g in gso_rows if g.relevance == "not_visible"))),
                 ("candidate notices B2 to B3", f"{len(b2_notices)} to {len({r.notice_id for r in rows if r.candidate})}"),
                 ("earth stations near or inside Finland", str(len(stations)))])
        + "<h2>GSO: elevation seen from Finland</h2><p class='sub'>Lines: highest and lowest elevation over the reference "
          "points for every longitude (the expected hump: about 22 deg peak, horizon about 72 deg either side). Dots: the "
          "GSO notices of this issue at their highest elevation. Hover a dot for the network.</p>" + elevation_chart(gso_rows)
        + "<h2>Funnel</h2>" + R.table(["Stage", "Groups", "Notices"], funnel_rows)
        + '<div class="two"><div><h2>Earth stations near or inside Finland</h2>'
          f"<p class='sub'>Specific earth stations of uplink groups within {G.NEAR_BORDER_KM:.0f} km [hypothesis]. "
          "Distance 0 means inside Finland.</p>" + map_svg(stations)
        + R.table(["Station", "Country", "km", "Uplink groups"], [[s["name"], s["country"], f"{s['distance_km']:.0f}", str(s["groups"])] for s in stations])
        + "</div><div><h2>Test vectors</h2>"
        + R.table(["Case", "Computed", "Expected", "Status"],
                  [[c, f"{v:.2f}", f"{e:g} (tolerance {tol:g})", R.badge("PASS" if abs(v - e) <= tol else "FAIL")] for c, v, e, tol in vectors], raw=True)
        + "<h2>Verdicts per notice</h2>" + R.table(["Geography", "Notices"], [[k, str(v)] for k, v in verdicts.most_common()])
        + "</div></div>"
        + "<h2>Non-GSO notices</h2><p class='sub'>Latitude reach = highest latitude that sees the satellite at 0 or 10 deg "
          f"elevation (circular coverage at apogee). Finland starts at {G.FINLAND_LAT_MIN} N.</p>"
        + R.table(["Notice", "Adm", "Network", "Verdict", "Inclination", "Apogee km", "Reach 0 deg", "Reach 10 deg", "Note"], ngso_rows, raw=True)
    )
    summary = {"status": status, "issue": issue, "test_vectors_ok": vec_ok, "impossible_gso_elevations": impossible,
               "notice_verdicts": dict(verdicts), "funnel_groups": stage("group"), "funnel_notices": stage("notice"),
               "near_border_stations": [{k: v for k, v in s.items() if k != "notices"} for s in stations]}
    out = settings.reports_dir / str(issue) / "03_geography.html"
    R.write(out, R.page(f"Space IFIC {issue}: geography",
                        f"Step B3 of pm_pack/08. radar.pipeline.geography; thresholds are hypotheses until Q1. {R.badge(status)}",
                        body, EXTRA_CSS), summary)
    print(f"written {out}: {status}; {summary['funnel_notices']}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
