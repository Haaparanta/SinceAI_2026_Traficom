#!/usr/bin/env python3
"""Step A6 visual proof: the Finnish frequency table as a spectrum strip, plus health checks.

    uv run python scripts/subbands_report.py            # writes reports/reference/fi_subbands.html

One strip per frequency decade (log scale inside each), one labelled lane per service family, and a
coverage lane that marks every range no sub-band covers. Hover a segment for its Traficom ID and text.
Below: field health, lookup spot checks, the gap list and ten random rows to compare with the Traficom web table.
"""
from __future__ import annotations

import math
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from radar import report_html as R  # noqa: E402
from radar.adapters.traficom_table import coverage_gaps, load_json, at_frequency  # noqa: E402
from radar.config import settings  # noqa: E402

# Service families, first match wins. Colours: validated categorical slots 1-7 (dataviz reference palette).
FAMILIES = [
    ("Satellite services", ("SATELLITE",), "--s1"),
    ("Science and passive", ("RADIO ASTRONOMY", "EARTH EXPLORATION", "SPACE RESEARCH", "METEOROLOGICAL", "STANDARD FREQUENCY"), "--s2"),
    ("Broadcasting", ("BROADCASTING",), "--s3"),
    ("Mobile", ("MOBILE",), "--s4"),
    ("Fixed", ("FIXED",), "--s5"),
    ("Radionavigation and radiolocation", ("RADIONAVIGATION", "RADIOLOCATION", "RADIODETERMINATION"), "--s6"),
    ("Amateur and other", ("",), "--s7"),
]
EXTRA_CSS = """
:root { --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a; --s4:#eda100; --s5:#e87ba4; --s6:#008300; --s7:#6250d6; --gap:#a32035; }
@media (prefers-color-scheme: dark) { :root { --s1:#3987e5; --s2:#d95926; --s3:#199e70; --s4:#c98500; --s5:#d55181;
  --s6:#008300; --s7:#9085e9; --gap:#ff9aa9; } }
.strip { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:8px 8px 4px; margin:10px 0; }
.strip h3 { font-size:13px; margin:0 0 4px; color:var(--muted); font-weight:600; }
svg text { fill:var(--muted); font:11px -apple-system, system-ui, sans-serif; }
svg .lane-bg { fill:var(--bg); }
svg rect.seg:hover { stroke:var(--fg); stroke-width:1; }
.legend { display:flex; flex-wrap:wrap; gap:6px 16px; margin:8px 0 0; font-size:12px; }
.legend i { display:inline-block; width:10px; height:10px; border-radius:2px; margin-right:6px; vertical-align:-1px; }
"""
LANE_H, LANE_GAP, LABEL_W, WIDTH = 12, 3, 230, 1100


def family(services: str) -> int:
    s = services.upper()
    for i, (_, keys, _) in enumerate(FAMILIES):
        if any(k in s for k in keys):
            return i
    return len(FAMILIES) - 1


def fmt_hz(hz: float) -> str:
    for unit, div in (("GHz", 1e9), ("MHz", 1e6), ("kHz", 1e3)):
        if hz >= div:
            return f"{hz / div:g} {unit}"
    return f"{hz:g} Hz"


def strip(decade: int, bands, gaps) -> str:
    lo, hi = 10.0 ** decade, 10.0 ** (decade + 1)
    plot_w = WIDTH - LABEL_W - 10

    def x(hz: float) -> float:
        hz = min(max(hz, lo), hi)
        return LABEL_W + (math.log10(hz) - decade) * plot_w

    lanes = len(FAMILIES) + 1
    height = lanes * (LANE_H + LANE_GAP) + 18
    parts = [f'<svg viewBox="0 0 {WIDTH} {height}" width="100%" role="img" '
             f'aria-label="Finnish sub-bands from {fmt_hz(lo)} to {fmt_hz(hi)}">']
    for i, (name, _, var) in enumerate(FAMILIES + [("No sub-band (gap)", (), "--gap")]):
        y = i * (LANE_H + LANE_GAP)
        parts.append(f'<text x="{LABEL_W - 8}" y="{y + LANE_H - 2}" text-anchor="end">{R.esc(name)}</text>')
        parts.append(f'<rect class="lane-bg" x="{LABEL_W}" y="{y}" width="{plot_w}" height="{LANE_H}" rx="2"/>')
    for b in bands:
        if b.upper_hz <= lo or b.lower_hz >= hi:
            continue
        i = family(b.services_in_finland)
        y = i * (LANE_H + LANE_GAP)
        x0, x1 = x(b.lower_hz), x(b.upper_hz)
        tip = f"ID {b.id}: {fmt_hz(b.lower_hz)} to {fmt_hz(b.upper_hz)}\n{b.services_in_finland}\n{b.sub_band_usage}"
        parts.append(f'<rect class="seg" x="{x0:.2f}" y="{y}" width="{max(x1 - x0, 0.8):.2f}" height="{LANE_H}" '
                     f'rx="2" style="fill:var({FAMILIES[i][2]})"><title>{R.esc(tip)}</title></rect>')
    y = len(FAMILIES) * (LANE_H + LANE_GAP)
    for a, b in gaps:
        if b <= lo or a >= hi:
            continue
        x0, x1 = x(a), x(b)
        parts.append(f'<rect class="seg" x="{x0:.2f}" y="{y}" width="{max(x1 - x0, 1.2):.2f}" height="{LANE_H}" rx="2" '
                     f'style="fill:var(--gap)"><title>No sub-band: {R.esc(fmt_hz(a))} to {R.esc(fmt_hz(b))}</title></rect>')
    ty = lanes * (LANE_H + LANE_GAP) + 12
    for k in (1, 2, 5, 10):
        hz = lo * k
        parts.append(f'<text x="{x(hz):.1f}" y="{ty}" text-anchor="{"end" if k == 10 else "middle"}">{fmt_hz(hz)}</text>')
    parts.append("</svg>")
    return f'<div class="strip"><h3>{fmt_hz(lo)} to {fmt_hz(hi)}</h3>{"".join(parts)}</div>'


# Spot checks a person can confirm without the table: well-known Finnish uses [HYPOTHESIS: expected family].
SPOT_CHECKS = [
    (100_000_000, "Broadcasting", "FM radio"),
    (1_575_420_000, "Satellite services", "GPS L1"),
    (3_500_000_000, "Mobile", "5G band n78"),
    (11_000_000_000, "Satellite services", "Ku-band satellite downlink"),
    (1_420_405_752, "Science and passive", "hydrogen line, radio astronomy"),
]


def main() -> int:
    bands = sorted(load_json(), key=lambda b: (b.lower_hz, b.id))
    gaps = coverage_gaps(tuple(bands))
    ids = [b.id for b in bands]
    checks = {
        "rows": len(bands),
        "rows_expected": 5917,
        "duplicate_ids": len(ids) - len(set(ids)),
        "zero_or_negative_width": sum(1 for b in bands if b.upper_hz <= b.lower_hz),
        "lowest_hz": bands[0].lower_hz,
        "highest_hz": max(b.upper_hz for b in bands),
        "gaps": len(gaps),
        "gap_total_hz": sum(b - a for a, b in gaps),
    }
    status = "PASS" if (checks["rows"] == 5917 and not checks["duplicate_ids"]
                        and not checks["zero_or_negative_width"]) else "FAIL"

    fam_counts = [sum(1 for b in bands if family(b.services_in_finland) == i) for i in range(len(FAMILIES))]
    legend = '<div class="legend">' + "".join(
        f'<span><i style="background:var({v})"></i>{R.esc(n)} ({c})</span>'
        for (n, _, v), c in zip(FAMILIES, fam_counts)) + '<span><i style="background:var(--gap)"></i>No sub-band (gap)</span></div>'
    strips = "".join(strip(d, bands, gaps) for d in range(3, 12))

    spot_rows, spot_summary = [], []
    for hz, expect, what in SPOT_CHECKS:
        hits = at_frequency(hz, tuple(bands))
        fams = sorted({FAMILIES[family(b.services_in_finland)][0] for b in hits})
        ok = expect in fams
        spot_summary.append({"hz": hz, "expected": expect, "found": fams, "ok": ok})
        spot_rows.append([fmt_hz(hz), R.esc(what), R.esc(expect), R.esc(", ".join(fams) or "none"),
                          R.badge("PASS" if ok else "FAIL"), R.esc(", ".join(str(b.id) for b in hits[:6]))])

    nulls = {f: sum(1 for b in bands if getattr(b, f) is None) for f in ("class_of_station", "direction", "comment")}
    health = [[f, f"{n:,}", f"{100 * n / len(bands):.1f} %"] for f, n in nulls.items()]

    gap_rows = [[fmt_hz(a), fmt_hz(b), fmt_hz(b - a)] for a, b in sorted(gaps, key=lambda g: g[0] - g[1])[:20]]
    random.seed(3074)
    sample = random.sample(bands, 10)
    sample_rows = [[str(b.id), fmt_hz(b.lower_hz), fmt_hz(b.upper_hz), b.services_in_finland, b.sub_band_usage,
                    b.direction or "", b.class_of_station or ""] for b in sample]

    body = (
        R.tiles([("sub-bands", f"{checks['rows']:,}"), ("duplicate IDs", str(checks["duplicate_ids"])),
                 ("zero or negative widths", str(checks["zero_or_negative_width"])),
                 ("range", f"{fmt_hz(checks['lowest_hz'])} to {fmt_hz(checks['highest_hz'])}"),
                 ("uncovered ranges", f"{checks['gaps']} ({fmt_hz(checks['gap_total_hz'])} in total)")])
        + "<h2>Spectrum strip</h2><p class='sub'>One strip per decade, log scale. Hover a segment for its Traficom ID. "
          "Overlapping rows (several uses of one band) sit on top of each other in their lane.</p>"
        + legend + strips
        + "<h2>Spot checks</h2>"
        + R.table(["Frequency", "What", "Expected family", "Families found", "Status", "Sub-band IDs"], spot_rows, raw=True)
        + "<h2>Field health</h2>" + R.table(["Field", "Empty", "Share"], health)
        + "<h2>Uncovered ranges, largest 20</h2><p class='sub'>No Finnish row covers these ranges. A notice that falls here "
          "must be reported as unknown (no Finnish table row), never as no concern.</p>"
        + R.table(["From", "To", "Width"], gap_rows)
        + "<h2>Ten random rows</h2><p class='sub'>Compare with the Traficom web version of the table.</p>"
        + R.table(["ID", "Lower", "Upper", "Services in Finland", "Usage", "Direction", "Class of station"], sample_rows)
    )
    subtitle = (f"Step A6 of pm_pack/08. Source: Traficom Taajuusjakotaulukko API v13, snapshot 2026-11-06 "
                f"(CC BY 4.0). {R.badge(status)}")
    out = settings.reports_dir / "reference" / "fi_subbands.html"
    R.write(out, R.page("Finnish frequency table", subtitle, body, EXTRA_CSS),
            {"status": status, **checks, "spot_checks": spot_summary, "family_counts": dict(zip([f[0] for f in FAMILIES], fam_counts))})
    print(f"written {out}: {status}, spot checks {sum(s['ok'] for s in spot_summary)}/{len(spot_summary)}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
