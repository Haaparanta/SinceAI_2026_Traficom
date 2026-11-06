#!/usr/bin/env python3
"""Step B1 visual proof: what the space adapter made of one issue.

    uv run python scripts/ingest_report.py 3074          # writes reports/3074/01_ingest.html and .summary.json

Counts in and out (with every exclusion reason), notices by special section, orbit and administration,
a frequency histogram split by direction, field health against expected ranges, and random plus extreme rows
with their source locators.
"""
from __future__ import annotations

import math
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from radar import report_html as R  # noqa: E402
from radar.adapters import space_ific  # noqa: E402
from radar.config import settings  # noqa: E402

# Expected ranges: outside means a unit or parsing error, not a judgement on the filing [HYPOTHESIS, pm_pack/08 B1].
EXPECTED = {
    "freq_min_hz": (1e6, 300e9, "Hz"),
    "freq_max_hz": (1e6, 300e9, "Hz"),
    "power_density_dbw_hz": (-120.0, 20.0, "dBW/Hz"),
    "max_gain_dbi": (-20.0, 75.0, "dBi"),
}
DIRS = [("space_to_earth", "Space-to-Earth", "--s1"), ("earth_to_space", "Earth-to-space", "--s2"), ("unknown", "Unknown", "--s3")]
EXTRA_CSS = """
:root { --s1:#2a78d6; --s2:#eb6834; --s3:#8a8780; }
@media (prefers-color-scheme: dark) { :root { --s1:#3987e5; --s2:#d95926; --s3:#9a978f; } }
.chart { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:12px; }
svg text { fill:var(--muted); font:11px -apple-system, system-ui, sans-serif; }
svg .grid { stroke:var(--line); stroke-width:1; }
svg rect.bar:hover { opacity:.8; }
.legend { display:flex; gap:16px; font-size:12px; margin:0 0 6px; }
.legend i { display:inline-block; width:10px; height:10px; border-radius:2px; margin-right:6px; vertical-align:-1px; }
.two { display:grid; grid-template-columns:repeat(auto-fit, minmax(320px, 1fr)); gap:16px; }
"""


def fmt_hz(hz: float) -> str:
    for unit, div in (("GHz", 1e9), ("MHz", 1e6), ("kHz", 1e3)):
        if hz >= div:
            return f"{hz / div:.4g} {unit}"
    return f"{hz:g} Hz"


def histogram(groups) -> tuple[str, list[dict]]:
    """Stacked bars of group centre frequency, 10 bins per decade from 100 MHz to 300 GHz, by direction."""
    lo_exp, hi_exp, per = 8.0, 11.5, 10
    nbins = int((hi_exp - lo_exp) * per)
    counts = [Counter() for _ in range(nbins)]
    for g in groups:
        centre = (g.freq_min_hz + g.freq_max_hz) / 2
        i = int((math.log10(max(centre, 1)) - lo_exp) * per)
        counts[min(max(i, 0), nbins - 1)][g.direction] += 1
    W, H, L, B, T = 1100, 260, 48, 28, 8
    pw, ph = W - L - 10, H - B - T
    top = max(sum(c.values()) for c in counts) or 1
    nice = 10 ** math.ceil(math.log10(top))
    nice = next(n for n in (nice / 5, nice / 2, nice) if n >= top)
    bw = pw / nbins
    parts = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Groups by centre frequency and direction">']
    for k in range(5):
        v = nice * k / 4
        y = T + ph - ph * v / nice
        parts.append(f'<line class="grid" x1="{L}" x2="{W - 10}" y1="{y:.1f}" y2="{y:.1f}"/>'
                     f'<text x="{L - 6}" y="{y + 4:.1f}" text-anchor="end">{int(v):,}</text>')
    rows = []
    for i, c in enumerate(counts):
        x = L + i * bw + 1
        y = T + ph
        lo_hz, hi_hz = 10 ** (lo_exp + i / per), 10 ** (lo_exp + (i + 1) / per)
        tip = f"{fmt_hz(lo_hz)} to {fmt_hz(hi_hz)}: " + ", ".join(f"{label} {c[key]:,}" for key, label, _ in DIRS if c[key])
        for key, _, var in DIRS:
            n = c[key]
            if not n:
                continue
            h = ph * n / nice
            y -= h
            parts.append(f'<rect class="bar" x="{x:.1f}" y="{y:.1f}" width="{bw - 2:.1f}" height="{h:.1f}" '
                         f'style="fill:var({var})"><title>{R.esc(tip)}</title></rect>')
        rows.append({"from_hz": round(lo_hz), "to_hz": round(hi_hz), **{k: c[k] for k, _, _ in DIRS}})
    for e in range(9, 12):
        x = L + (e - lo_exp) * per * bw
        parts.append(f'<line class="grid" x1="{x:.1f}" x2="{x:.1f}" y1="{T}" y2="{T + ph}"/>'
                     f'<text x="{x:.1f}" y="{H - 10}" text-anchor="middle">{fmt_hz(10 ** e)}</text>')
    for hz, label in ((4e9, "C"), (12e9, "Ku"), (20e9, "Ka")):
        x = L + (math.log10(hz) - lo_exp) * per * bw
        parts.append(f'<text x="{x:.1f}" y="{T + 10}" text-anchor="middle">{label} band</text>')
    parts.append("</svg>")
    legend = '<div class="legend">' + "".join(f'<span><i style="background:var({v})"></i>{l}</span>' for _, l, v in DIRS) + "</div>"
    return f'<div class="chart">{legend}{"".join(parts)}</div>', rows


def main() -> int:
    issue = int(sys.argv[1]) if len(sys.argv) > 1 else 3074
    r = space_ific.load(issue)
    groups = [g for n in r.notices for g in n.groups]
    by_notice = {n.notice_id: n for n in r.notices}

    # field health
    health, out_of_range = [], {}
    for f, (lo, hi, unit) in EXPECTED.items():
        vals = [getattr(g, f) for g in groups]
        present = [v for v in vals if v is not None]
        bad = [g for g in groups if getattr(g, f) is not None and not lo <= getattr(g, f) <= hi]
        flagged = {a.group_id for a in r.anomalies if a.field == f}
        unflagged = [g for g in bad if g.group_id not in flagged]
        out_of_range[f] = len(unflagged)
        fmt = fmt_hz if unit == "Hz" else (lambda v: f"{v:g} {unit}")
        health.append([f"<code>{f}</code>", f"{100 * (len(vals) - len(present)) / max(len(vals), 1):.1f} %",
                       R.esc(fmt(min(present)) if present else "-"), R.esc(fmt(max(present)) if present else "-"),
                       R.esc(f"{fmt(lo)} to {fmt(hi)}"),
                       (R.badge("FAIL") + f" {len(unflagged)} outside, not flagged" if unflagged
                        else R.badge("FLAGGED") + f" {len(bad)} source value(s) kept as filed, see anomalies" if bad
                        else R.badge("PASS"))])
    dir_counts = Counter(g.direction for g in groups)
    unknown_share = dir_counts["unknown"] / max(len(groups), 1)
    no_groups = [n for n in r.notices if not n.groups]
    status = "PASS" if (not any(out_of_range.values()) and unknown_share < 0.05
                        and r.stats["groups_kept"] + r.stats["groups_excluded"] == r.stats["groups_in_db"]) else "FAIL"

    chart, hist_rows = histogram(groups)
    sec = Counter((n.special_section or "none").split(" ")[0] if not (n.special_section or "").startswith("Part")
                  else n.special_section for n in r.notices)
    orbit = Counter(n.orbit for n in r.notices)
    adm = Counter(n.administration for n in r.notices)
    adm_groups = Counter()
    for n in r.notices:
        adm_groups[n.administration] += len(n.groups)
    excl = Counter(e.reason.split(" (")[0] for e in r.excluded)

    random.seed(issue)
    sample = random.sample(groups, min(10, len(groups)))
    widest = sorted(groups, key=lambda g: g.freq_max_hz - g.freq_min_hz, reverse=True)[:3]
    loudest = sorted([g for g in groups if g.power_density_dbw_hz is not None], key=lambda g: -g.power_density_dbw_hz)[:2]

    def grow(g, tag=""):
        n = by_notice[g.notice_id]
        return [R.esc(tag), f"<code>{R.esc(g.source_ref)}</code>", R.esc(n.administration), R.esc(n.network_name),
                R.esc(n.special_section), R.esc(fmt_hz(g.freq_min_hz)), R.esc(fmt_hz(g.freq_max_hz)), R.esc(g.direction),
                R.esc(g.beam_name), R.esc(g.power_density_dbw_hz), R.esc(g.max_gain_dbi), R.esc(", ".join(g.service_area_codes))]

    body = (
        R.tiles([("notices", f"{len(r.notices):,}"), ("groups screened (published in this issue)", f"{r.stats['groups_kept']:,}"),
                 ("groups excluded", f"{r.stats['groups_excluded']:,}"),
                 ("direction unknown", f"{100 * unknown_share:.1f} %"),
                 ("notices without a group in this issue", str(len(no_groups))),
                 ("source data anomalies flagged", str(len(r.anomalies)))])
        + "<h2>Counts in and out</h2>"
        + R.table(["Step", "Count"], [["Groups in the database", f"{r.stats['groups_in_db']:,}"]]
                  + [[f"Excluded: {k}", f"{v:,}"] for k, v in excl.items()]
                  + [["Screened", f"{r.stats['groups_kept']:,}"]])
        + "<h2>Groups by centre frequency and direction</h2><p class='sub'>10 bins per decade. Expect peaks in the "
          "C, Ku and Ka satellite bands. Hover a bar for its counts.</p>" + chart
        + "<h2>Field health</h2><p class='sub'>Outside the expected range means a unit or parsing error.</p>"
        + R.table(["Field", "Missing", "Min", "Max", "Expected", "Status"], health, raw=True)
        + '<div class="two"><div><h2>Notices by special section</h2>'
        + R.table(["Section", "Notices"], [[k, str(v)] for k, v in sec.most_common()])
        + "<h2>Notices by orbit</h2>" + R.table(["Orbit", "Notices"], [[k, str(v)] for k, v in orbit.most_common()])
        + "</div><div><h2>Administrations, top 15</h2>"
        + R.table(["Administration", "Notices", "Groups screened"], [[k, str(v), f"{adm_groups[k]:,}"] for k, v in adm.most_common(15)])
        + "</div></div>"
        + "<h2>Ten random groups, the three widest, the two highest power densities</h2>"
          "<p class='sub'>Open the locator in the DuckDB UI to check any row by hand.</p>"
        + R.table(["", "Locator", "Adm", "Network or station", "Section", "From", "To", "Direction", "Beam",
                   "pd dBW/Hz", "Gain dBi", "Service area"],
                  [grow(g) for g in sample] + [grow(g, "widest") for g in widest] + [grow(g, "highest pd") for g in loudest], raw=True)
        + ("<h2>Source data anomalies</h2><p class='sub'>Kept exactly as filed (rule 3) and flagged; later calculations "
           "must not use these values without a reviewer. Candidates for a question to the notifying administration.</p>"
           + R.table(["Locator", "Adm", "Network", "Field", "Value as filed", "Why flagged", "Cross-check"],
                     [[f"<code>{R.esc(a.source_ref)}</code>", R.esc(by_notice[a.notice_id].administration),
                       R.esc(by_notice[a.notice_id].network_name), R.esc(a.field), R.esc(a.value), R.esc(a.reason),
                       R.esc(a.cross_check)] for a in r.anomalies], raw=True)
           if r.anomalies else "")
        + ("<h2>Notices without a group in this issue</h2><p class='sub'>Expected for suppressions (action S).</p>"
           + R.table(["Notice", "Adm", "Name", "Section"], [[n.notice_id, n.administration, n.network_name, n.special_section or ""] for n in no_groups])
           if no_groups else "")
    )
    summary = {
        "status": status, "issue": issue, **r.stats,
        "excluded_by_reason": dict(excl), "direction": dict(dir_counts), "out_of_range": out_of_range,
        "null_share": {f: round(sum(getattr(g, f) is None for g in groups) / max(len(groups), 1), 4) for f in EXPECTED},
        "notices_by_section": dict(sec), "notices_by_orbit": dict(orbit), "notices_without_groups": [n.notice_id for n in no_groups],
        "histogram": hist_rows,
        "anomalies": [a.__dict__ for a in r.anomalies],
    }
    out = settings.reports_dir / str(issue) / "01_ingest.html"
    subtitle = f"Step B1 of pm_pack/08. Space IFIC {issue}, adapter radar.adapters.space_ific. {R.badge(status)}"
    R.write(out, R.page(f"Space IFIC {issue}: ingest", subtitle, body, EXTRA_CSS), summary)
    print(f"written {out}: {status}; groups {r.stats['groups_kept']:,} screened, {r.stats['groups_excluded']:,} excluded; "
          f"direction {dict(dir_counts)}; out of range {out_of_range}; null share {summary['null_share']}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
