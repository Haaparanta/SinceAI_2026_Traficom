#!/usr/bin/env python3
"""Step A3 visual proof: the special-interest stations (Traficom XLS) as read, mapped and checked.

    uv run python scripts/special_interest_report.py     # writes reports/reference/special_interest.html and .summary.json

Checks: every row of the sheet is either a station or an excluded row with a reason; every protected frequency is
a value from the sheet (RX, or TX when RX is empty); every station keeps its spreadsheet row; every adjustment is a
flag on the station. Shows a map of the stations by licence class, their protected channels on a log-frequency
axis, the data-quality flags, the excluded rows and ten random rows next to the sheet's own text.
"""
from __future__ import annotations

import math
import random
import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT)]

from radar import report_html as R  # noqa: E402
from radar.adapters import special_interest as S  # noqa: E402
from radar.config import settings  # noqa: E402
from scoring.geometry import Region  # noqa: E402

CLASSES = [("BC", "BC  FM and AM radio", "--k1"), ("BT", "BT  television", "--k2"), ("FX", "FX  fixed links", "--k3"),
           ("MVV", "MVV  mobile networks", "--k4"), ("MUUT", "MUUT  other", "--k5"), (None, "no class given", "--k6")]
CSS = """
:root { --k1:#2a78d6; --k2:#eb6834; --k3:#1baf7a; --k4:#8b5cf6; --k5:#c99a00; --k6:#7a7280; --land:#ece4ea; --fin:#d9c3d2; }
@media (prefers-color-scheme: dark) { :root { --k1:#3987e5; --k2:#d95926; --k3:#199e70; --k4:#9f86f0; --k5:#e0b23a;
  --k6:#a99fab; --land:#2c2430; --fin:#4a3a4f; } }
.chart { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:12px; }
svg text { fill:var(--muted); font:11px -apple-system, system-ui, sans-serif; } svg .grid { stroke:var(--line); }
.legend { display:flex; flex-wrap:wrap; gap:6px 16px; font-size:12px; margin:0 0 6px; }
.legend i { display:inline-block; width:10px; height:10px; border-radius:50%; margin-right:6px; vertical-align:-1px; }
.two { display:grid; grid-template-columns:repeat(auto-fit, minmax(340px, 1fr)); gap:16px; align-items:start; }
"""
COLOUR = {c: v for c, _, v in CLASSES}


def legend(counts: Counter) -> str:
    return '<div class="legend">' + "".join(
        f'<span><i style="background:var({v})"></i>{R.esc(label)} ({counts.get(c or "none given", 0)})</span>'
        for c, label, v in CLASSES) + '<span><i style="background:none;border:2px solid var(--fg)"></i>flagged</span></div>'


def map_svg(stations) -> str:
    region = Region.load()
    lon0, lon1, lat0, lat1 = 17.5, 33.5, 58.8, 70.6
    W = 520
    H = int(W * (lat1 - lat0) / ((lon1 - lon0) * math.cos(math.radians(64))))
    x = lambda lon: (lon - lon0) / (lon1 - lon0) * W  # noqa: E731
    y = lambda lat: (lat1 - lat) / (lat1 - lat0) * H  # noqa: E731
    p = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Special-interest stations by licence class">']
    for code, polys in region.polygons.items():
        for poly in polys:
            d = " ".join(f"{x(lo):.1f},{y(la):.1f}" for lo, la in poly[0])
            p.append(f'<polygon points="{d}" style="fill:{"var(--fin)" if code == "FIN" else "var(--land)"};stroke:var(--line);stroke-width:.6"/>')
    for s in sorted(stations, key=lambda s: bool(s.quality_flags)):
        ring = "stroke:var(--fg);stroke-width:1.6" if s.quality_flags else "stroke:var(--card);stroke-width:.8"
        tip = f"{s.station_number} ({s.licence_class or 'no class'}): {s.centre_hz / 1e6:g} MHz, row {s.source_row}"
        if s.quality_flags:
            tip += " | " + "; ".join(s.quality_flags)
        p.append(f'<circle cx="{x(s.lon):.1f}" cy="{y(s.lat):.1f}" r="3.2" style="fill:var({COLOUR[s.licence_class]});{ring}">'
                 f'<title>{R.esc(tip)}</title></circle>')
    p.append("</svg>")
    return f'<div class="chart">{"".join(p)}</div>'


def spectrum_svg(stations) -> str:
    """Protected channels on a log-frequency axis, one lane per licence class."""
    f0, f1 = 1e6, 3e10
    W, lane, top, left, right = 760, 30, 10, 120, 34
    H = top + lane * len(CLASSES) + 34
    x = lambda hz: left + (math.log10(hz) - math.log10(f0)) / (math.log10(f1) - math.log10(f0)) * (W - left - right)  # noqa: E731
    p = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Protected channels by frequency and licence class">']
    for dec in range(6, 11):
        for mult in (1, 3):
            hz = mult * 10 ** dec
            if hz > f1:
                continue
            p.append(f'<line class="grid" x1="{x(hz):.1f}" y1="{top}" x2="{x(hz):.1f}" y2="{H - 24}"/>'
                     f'<text x="{x(hz):.1f}" y="{H - 8}" text-anchor="middle">{hz / 1e6:g} MHz</text>' if hz < 1e9 else
                     f'<line class="grid" x1="{x(hz):.1f}" y1="{top}" x2="{x(hz):.1f}" y2="{H - 24}"/>'
                     f'<text x="{x(hz):.1f}" y="{H - 8}" text-anchor="middle">{hz / 1e9:g} GHz</text>')
    for i, (c, label, v) in enumerate(CLASSES):
        y0 = top + i * lane
        p.append(f'<text x="{left - 8}" y="{y0 + lane / 2 + 4}" text-anchor="end">{R.esc(label.split("  ")[0])}</text>')
        for s in (s for s in stations if s.licence_class == c):
            lo, hi = max(f0, s.centre_hz - s.bandwidth_hz / 2), min(f1, s.centre_hz + s.bandwidth_hz / 2)
            w = max(1.5, x(hi) - x(lo))
            p.append(f'<rect x="{x(lo):.1f}" y="{y0 + 5}" width="{w:.1f}" height="{lane - 10}" rx="2" '
                     f'style="fill:var({v});fill-opacity:.55"><title>{R.esc(f"{s.station_number}: {s.centre_hz / 1e6:g} MHz, {s.bandwidth_hz / 1e3:g} kHz")}</title></rect>')
    p.append("</svg>")
    return f'<div class="chart">{"".join(p)}</div>'


def main() -> int:
    res = S.load()
    stations = res.stations
    raw = {n: c for n, c in S._read_sheet(S.path())}
    header_row, col = S._header(sorted(raw.items()))

    def sheet(s, key):
        return raw[s.source_row].get(col[key])

    from_sheet = all(s.centre_hz in (S.parse_hz(sheet(s, "rx")), S.parse_hz(sheet(s, "tx"))) for s in stations)
    rows_accounted = len(stations) + len(res.excluded) == res.stats["rows"]
    rx_fallback = [s for s in stations if S.parse_hz(sheet(s, "rx")) is None]
    checks = [
        ("Every row is a station or an excluded row with a reason", rows_accounted,
         f"{len(stations)} stations + {len(res.excluded)} excluded = {res.stats['rows']} rows"),
        ("Every protected frequency is a value from the sheet (RX, or TX when RX is empty)", from_sheet, f"{len(rx_fallback)} from TX"),
        ("Every station keeps its spreadsheet row", all(s.source_row for s in stations), ""),
        ("Every fallback is flagged", all(any("TX frequency" in f for f in s.quality_flags) for s in rx_fallback), ""),
    ]
    status = "PASS" if all(ok for _, ok, _ in checks) else "FAIL"
    counts = Counter(s.licence_class or "none given" for s in stations)
    flagged = [s for s in stations if s.quality_flags]
    random.seed(3074)
    sample = random.sample(stations, 10)
    body = (
        R.tiles([("rows in the sheet", str(res.stats["rows"])), ("stations", str(len(stations))),
                 ("excluded", str(len(res.excluded))), ("flagged", str(len(flagged))),
                 ("lowest", f"{min(s.centre_hz for s in stations) / 1e6:g} MHz"),
                 ("highest", f"{max(s.centre_hz for s in stations) / 1e9:g} GHz")])
        + f"<p class='sub'>Source: <code>{R.esc(res.source)}</code> (Traficom_SinceAI_Frequencies_of_interest_v05112026.xlsx, "
          "synthetic data provided by Traficom on 5 Nov 2026). Header found on row "
          f"{header_row}. The sheet's own note: coordinates may fall outside Finland and heights may be impossible.</p>"
        + "<h2>Checks</h2>" + R.table(["Check", "Status", "Detail"], [[c, R.badge("PASS" if ok else "FAIL"), R.esc(d)] for c, ok, d in checks], raw=True)
        + "<h2>Where they are and what they use</h2>" + legend(counts)
        + f'<div class="two">{map_svg(stations)}{spectrum_svg(stations)}</div>'
        + "<p class='sub'>Protected channel = RX frequency +- half the channel bandwidth. Hover a point or a bar for the station.</p>"
        + "<h2>Data-quality flags</h2><p class='sub'>Each adjustment the reader made, or each odd value it kept as filed.</p>"
        + R.table(["Flag", "Stations"], [[k, str(v)] for k, v in res.stats["flags"].items()])
        + "<h2>Excluded rows</h2>" + R.table(["Sheet row", "Station number", "Reason"], [[str(e.row), e.station_number, e.reason] for e in res.excluded])
        + "<h2>Ten random stations next to the sheet</h2><p class='sub'>Seed 3074. Left: as read. Right: the cells as written in the sheet.</p>"
        + R.table(["Row", "Station", "Class", "Protected MHz", "Bandwidth kHz", "Lat, lon", "AGL m", "e.r.p. W", "Sheet: RX / TX / bandwidth / power", "Flags"],
                  [[str(s.source_row), s.station_number, s.licence_class or "", f"{s.centre_hz / 1e6:g}", f"{s.bandwidth_hz / 1e3:g}",
                    f"{s.lat:.4f}, {s.lon:.4f}", "" if s.antenna_height_m is None else f"{s.antenna_height_m:g}",
                    "unknown" if s.erp_w is None else f"{s.erp_w:g}",
                    f"{sheet(s, 'rx') or '-'} / {sheet(s, 'tx') or '-'} / {sheet(s, 'chan_bw') or '-'} / {sheet(s, 'power') or '-'} {sheet(s, 'power_unit') or ''}",
                    "; ".join(s.quality_flags)] for s in sample])
    )
    out = settings.reports_dir / "reference" / "special_interest.html"
    R.write(out, R.page("Special-interest stations", f"Step A3 of pm_pack/08: the mandatory Traficom table, read and checked. {R.badge(status)}", body, CSS),
            {"status": status, "checks": [[c, ok, d] for c, ok, d in checks], "stats": res.stats})
    print(f"written {out}: {status}")
    for c, ok, d in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {c}  {d}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
