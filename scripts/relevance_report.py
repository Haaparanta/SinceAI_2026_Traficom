#!/usr/bin/env python3
"""Step B2 visual proof: frequency relevance of every group in one Space IFIC.

    uv run python scripts/relevance_report.py 3074     # writes reports/3074/02_relevance.html and .summary.json

Funnel by group and by notice, counts per concern path, the notices the Bureau itself lists Finland against,
and ten zoomed spectrum views (five candidates, five dropped) for a person to agree or disagree with.
The ten cases are chosen with a fixed seed so the hand check in tests/golden/space_3074.yaml stays valid.
"""
from __future__ import annotations

import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import duckdb  # noqa: E402

from radar import report_html as R  # noqa: E402
from radar.adapters import space_ific, traficom_table  # noqa: E402
from radar.adapters import special_interest as SI  # noqa: E402
from radar.config import settings  # noqa: E402
from radar.pipeline import relevance as rel  # noqa: E402

CLASS_COLOURS = {"terrestrial": "--s1", "space": "--s2", "passive": "--s3", "not_allocated": "--s4"}
EXTRA_CSS = """
:root { --s1:#2a78d6; --s2:#eb6834; --s3:#1baf7a; --s4:#8a8780; --grp:#221a20; --gap:#a32035; }
@media (prefers-color-scheme: dark) { :root { --s1:#3987e5; --s2:#d95926; --s3:#199e70; --s4:#9a978f; --grp:#efe7ee; --gap:#ff9aa9; } }
.case { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:10px 12px; margin:12px 0; }
.case h3 { font-size:14px; margin:0 0 2px; } .case p { margin:0 0 6px; color:var(--muted); font-size:12px; }
svg text { fill:var(--muted); font:11px -apple-system, system-ui, sans-serif; }
svg .lbl { fill:var(--fg); }
.legend { display:flex; flex-wrap:wrap; gap:6px 16px; font-size:12px; margin:6px 0; }
.legend i { display:inline-block; width:10px; height:10px; border-radius:2px; margin-right:6px; vertical-align:-1px; }
.bar { height:14px; background:var(--s1); border-radius:0 4px 4px 0; display:inline-block; vertical-align:middle; }
.two { display:grid; grid-template-columns:repeat(auto-fit, minmax(320px, 1fr)); gap:16px; }
"""


def fmt_hz(hz: float) -> str:
    for unit, div in (("GHz", 1e9), ("MHz", 1e6), ("kHz", 1e3)):
        if abs(hz) >= div:
            return f"{hz / div:.6g} {unit}"
    return f"{hz:g} Hz"


def funnel_table(rows, station_hits=None) -> str:
    g, n = rel.funnel(rows, "group", station_hits), rel.funnel(rows, "notice", station_hits)
    top_g, top_n = g[0][1] or 1, n[0][1] or 1
    out = []
    for (label, cg), (_, cn) in zip(g, n):
        out.append([R.esc(label), f"{cg:,}", f'<span class="bar" style="width:{240 * cg / top_g:.0f}px"></span>',
                    f"{cn:,}", f'<span class="bar" style="width:{160 * cn / top_n:.0f}px"></span>'])
    return R.table(["Stage", "Groups", "", "Notices", ""], out, raw=True)


def zoom(r, bands_by_id, classes, notice) -> str:
    """Linear view of the group range padded by 15 %, the group on top, its Finnish rows below, gaps in red."""
    width = max(r.freq_max_hz - r.freq_min_hz, 1)
    lo, hi = r.freq_min_hz - 0.15 * width, r.freq_max_hz + 0.15 * width
    W, L, lane = 1100, 360, 14
    pw = W - L - 10
    x = lambda hz: L + (min(max(hz, lo), hi) - lo) / (hi - lo) * pw  # noqa: E731
    rows = [bands_by_id[i] for i in r.matched_subband_ids]
    # Identical rows (same service and limits, e.g. one per channel plan) share a lane; terrestrial and passive
    # lanes come first so the rows that decide the verdict are never hidden behind the cut.
    lanes: dict[tuple, list] = {}
    for b in rows:
        lanes.setdefault((b.services_in_finland, b.lower_hz, b.upper_hz), []).append(b)
    order = {"terrestrial": 0, "passive": 1, "space": 2, "not_allocated": 3}
    lane_list = sorted(lanes.values(), key=lambda bs: (order[classes[bs[0].id].category], bs[0].lower_hz))
    shown = lane_list[:12]
    hidden_rows = sum(len(bs) for bs in lane_list[12:])
    H = (len(shown) + 3) * (lane + 4) + 24
    p = [f'<svg viewBox="0 0 {W} {H}" width="100%" role="img" aria-label="Group {r.group_id} against Finnish rows">']
    p.append(f'<text class="lbl" x="{L - 8}" y="{lane - 2}" text-anchor="end">Group {r.group_id} ({r.direction.replace("_", " ")})</text>'
             f'<rect x="{x(r.freq_min_hz):.1f}" y="0" width="{max(x(r.freq_max_hz) - x(r.freq_min_hz), 1.5):.1f}" height="{lane}" rx="3" style="fill:var(--grp)">'
             f'<title>{fmt_hz(r.freq_min_hz)} to {fmt_hz(r.freq_max_hz)}</title></rect>')
    for k, bs in enumerate(shown, start=1):
        b = bs[0]
        y = k * (lane + 4)
        c = classes[b.id]
        tag = f"{c.category}{' ' + c.space_direction if c.space_direction else ''}{'' if c.primary else ', secondary'}"
        ids = f"ID {b.id}" if len(bs) == 1 else f"IDs {bs[0].id}-{bs[-1].id} ({len(bs)})"
        label = f"{ids}: {b.services_in_finland[:30]}"
        p.append(f'<text x="{L - 8}" y="{y + lane - 2}" text-anchor="end">{R.esc(label)}</text>'
                 f'<rect x="{x(b.lower_hz):.1f}" y="{y}" width="{max(x(b.upper_hz) - x(b.lower_hz), 1.5):.1f}" height="{lane}" rx="3" '
                 f'style="fill:var({CLASS_COLOURS[c.category]}){";opacity:.55" if not c.primary else ""}">'
                 f'<title>{R.esc(f"ID {b.id}: {fmt_hz(b.lower_hz)} to {fmt_hz(b.upper_hz)}; {b.services_in_finland}; {b.sub_band_usage}; {tag}")}</title></rect>')
    y = (len(shown) + 1) * (lane + 4)
    if hidden_rows:
        p.append(f'<text x="{L - 8}" y="{y + lane - 2}" text-anchor="end">... {hidden_rows} more rows</text>')
    if r.uncovered_hz:
        # draw uncovered pieces inside the group
        covered = sorted((max(r.freq_min_hz, b.lower_hz), min(r.freq_max_hz, b.upper_hz)) for b in rows)
        cur = r.freq_min_hz
        for a, b in covered + [(r.freq_max_hz, r.freq_max_hz)]:
            if a > cur:
                p.append(f'<rect x="{x(cur):.1f}" y="{y}" width="{max(x(a) - x(cur), 1.5):.1f}" height="{lane}" rx="3" style="fill:var(--gap)">'
                         f'<title>No Finnish row: {fmt_hz(cur)} to {fmt_hz(a)}</title></rect>')
            cur = max(cur, b)
        p.append(f'<text x="{L - 8}" y="{y + lane - 2}" text-anchor="end">No Finnish row (gap)</text>')
    ty = H - 6
    for f in (0, 0.5, 1):
        hz = r.freq_min_hz + f * (r.freq_max_hz - r.freq_min_hz)
        p.append(f'<text x="{x(hz):.1f}" y="{ty}" text-anchor="{"start" if f == 0 else "end" if f == 1 else "middle"}">{fmt_hz(hz)}</text>')
    p.append("</svg>")
    verdict = "CANDIDATE" if r.candidate else "DROPPED"
    paths = ", ".join(sorted(r.paths)) or "none"
    named = f"; Bureau names Finland under {', '.join(r.finland_named_provisions)}" if r.finland_named_provisions else ""
    return (f'<div class="case"><h3>{R.badge(verdict)} {R.esc(notice.administration)} {R.esc(notice.network_name)} '
            f'<code>grp.grp_id={r.group_id}</code></h3>'
            f'<p>{R.esc(notice.special_section)} &middot; {R.esc(notice.orbit)} &middot; {fmt_hz(r.freq_min_hz)} to {fmt_hz(r.freq_max_hz)} &middot; '
            f'paths: {R.esc(paths)}{R.esc(named)}{" &middot; dropped: " + R.esc(r.drop_reason) if r.drop_reason else ""} &middot; '
            f'overlap {fmt_hz(r.overlap_hz)}, uncovered {fmt_hz(r.uncovered_hz)}</p>{"".join(p)}</div>')


def pick_cases(rows, seed: int):
    rnd = random.Random(seed)
    cands = sorted([r for r in rows if r.candidate], key=lambda r: r.group_id)
    s2e_drop = sorted([r for r in rows if not r.candidate and r.direction == "space_to_earth"], key=lambda r: r.group_id)
    e2s_drop = sorted([r for r in rows if not r.candidate and r.direction == "earth_to_space"], key=lambda r: r.group_id)
    return rnd.sample(cands, 5), rnd.sample(s2e_drop, 3) + rnd.sample(e2s_drop, 2)


def main() -> int:
    issue = int(sys.argv[1]) if len(sys.argv) > 1 else 3074
    ing = space_ific.load(issue)
    with duckdb.connect(str(space_ific.db_path(issue)), read_only=True) as con:
        named = rel.finland_named(con)
    bands = traficom_table.subbands()
    rows = rel.screen(ing.notices, bands, named=named)
    # Special-interest stations: a second screen with the sheet, used only for the station counts, so the funnel,
    # the paths and the seeded hand-check cases above stay the frequency-only screen (tests/golden/space_3074.yaml).
    stations = list(SI.stations())
    station_hits = ({r.group_id: r.matched_station_numbers for r in rel.screen(ing.notices, bands, stations=stations, named=named)
                     if r.matched_station_numbers} if stations else None)
    stations_hit = len({s for v in (station_hits or {}).values() for s in v})
    by_notice = {n.notice_id: n for n in ing.notices}
    bands_by_id = {b.id: b for b in bands}
    classes = {b.id: rel.classify(b.services_in_finland) for b in bands}

    bad_overlap = [r.group_id for r in rows if r.overlap_hz > r.freq_max_hz - r.freq_min_hz]
    s2e = [r for r in rows if r.direction == "space_to_earth"]
    kept_share = sum(r.candidate for r in s2e) / max(len(s2e), 1)
    e2s_candidates = [r.group_id for r in rows if r.direction == "earth_to_space" and r.candidate and not r.finland_named_provisions]
    status = "PASS" if not bad_overlap and not e2s_candidates else "FAIL"

    paths = Counter(p for r in rows for p in r.paths)
    path_notices = Counter(p for p, nid in {(p, r.notice_id) for r in rows for p in r.paths})
    path_rows = [[p, "candidate" if p in rel.CANDIDATE_PATHS else "informational", f"{paths[p]:,}", f"{path_notices[p]:,}"]
                 for p in rel.CANDIDATE_PATHS + rel.INFORMATIONAL_PATHS if paths[p] or p == "special_interest"]

    named_notices = sorted({r.notice_id for r in rows if r.finland_named_provisions})
    named_rows = []
    for nid in named_notices:
        n = by_notice[nid]
        grs = [r for r in rows if r.notice_id == nid and r.finland_named_provisions]
        provs = sorted({p for r in grs for p in r.finland_named_provisions})
        lo, hi = min(r.freq_min_hz for r in grs), max(r.freq_max_hz for r in grs)
        named_rows.append([nid, n.administration, n.network_name, n.special_section or "", n.orbit,
                           ", ".join(provs), str(len(grs)), f"{fmt_hz(lo)} to {fmt_hz(hi)}",
                           ", ".join(sorted({p for r in grs for p in r.paths})) or "none"])

    cands, drops = pick_cases(rows, issue)
    cases_html = "".join(zoom(r, bands_by_id, classes, by_notice[r.notice_id]) for r in cands + drops)
    legend = ('<div class="legend">' + "".join(f'<span><i style="background:var({v})"></i>Finnish row: {k.replace("_", " ")}</span>'
                                              for k, v in CLASS_COLOURS.items())
              + '<span><i style="background:var(--grp)"></i>the group</span><span><i style="background:var(--gap)"></i>no Finnish row</span>'
              + "<span>Faded = secondary allocation</span></div>")

    body = (
        R.tiles([("groups screened", f"{len(rows):,}"), ("candidate groups", f"{sum(r.candidate for r in rows):,}"),
                 ("space-to-Earth groups kept", f"{100 * kept_share:.1f} %"),
                 ("notices the Bureau lists Finland against", str(len(named_notices))),
                 ("special-interest stations overlapped (before geography)",
                  f"{stations_hit:,} of {len({s.station_number for s in stations}):,}" if stations else "sheet missing")])
        + "<h2>Funnel</h2><p class='sub'>Frequency alone keeps almost every downlink: satellites file in satellite bands, "
          "and Finland allocates the same bands to satellite and terrestrial services. This is expected, not a join error "
          "(bounds and direction are tested). The ranking must therefore rest on geography (B3), pfd (C1) and the Bureau's "
          "own list of affected administrations, shown below.</p>" + funnel_table(rows, station_hits)
        + "<h2>Concern paths</h2>" + R.table(["Path", "Kind", "Groups", "Notices"], path_rows)
        + "<h2>Notices where the Bureau lists Finland as affected</h2><p class='sub'>From <code>provn.adm = 'FIN'</code>. "
          "These are the ITU's own identification and should rank first for review.</p>"
        + R.table(["Notice", "Adm", "Network or station", "Section", "Orbit", "Provisions", "Groups", "Range", "Paths"], named_rows)
        + "<h2>Ten cases to check by hand</h2><p class='sub'>Five random candidates, three random dropped downlinks, two random "
          "dropped uplinks (seed = issue number). Agree or disagree with each; the agreed outcome goes into "
          "<code>tests/golden/space_3074.yaml</code>.</p>" + legend + cases_html
    )
    summary = {
        "status": status, "issue": issue, "funnel_groups": rel.funnel(rows, "group", station_hits), "funnel_notices": rel.funnel(rows, "notice", station_hits),
        "special_interest": {"stations": len({s.station_number for s in stations}), "overlapped_before_geography": stations_hit},
        "paths_groups": dict(paths), "paths_notices": dict(path_notices),
        "space_to_earth_kept_share": round(kept_share, 4), "overlap_wider_than_group": bad_overlap,
        "uplink_candidates_without_bureau_naming": e2s_candidates, "finland_named_notices": named_notices,
        "hand_check_cases": [{"group_id": r.group_id, "notice_id": r.notice_id, "candidate": r.candidate,
                              "paths": sorted(r.paths), "drop_reason": r.drop_reason} for r in cands + drops],
    }
    out = settings.reports_dir / str(issue) / "02_relevance.html"
    R.write(out, R.page(f"Space IFIC {issue}: frequency relevance",
                        f"Step B2 of pm_pack/08. Rules in radar.pipeline.relevance (pm_pack/06, hypothesis until Q1). {R.badge(status)}",
                        body, EXTRA_CSS), summary)
    print(f"written {out}: {status}")
    for c in summary["hand_check_cases"]:
        print(c)
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
