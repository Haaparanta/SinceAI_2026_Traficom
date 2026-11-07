#!/usr/bin/env python3
"""Visual proof of the space plan check (AP30, AP30A, AP30B) for one issue.

    uv run python scripts/plans_report.py 3074      # writes reports/3074/08_plans.html and .summary.json

Finland's plan entries, the orbital arcs of RR Appendices 30, 30A and 30B, a strip of the geostationary orbit with the
Finnish positions, their arcs, the co-frequency networks of the issue and the networks the Bureau found affecting
Finland, the plan sections of the issue with their reasons, and the evidence check of every plan citation.
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

import duckdb

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT)]

from radar import evidence_check  # noqa: E402
from radar import report_html as R  # noqa: E402
from radar.adapters import plans as P  # noqa: E402
from radar.adapters import space_ific  # noqa: E402
from radar.config import settings  # noqa: E402
from radar.pipeline import assemble  # noqa: E402
from radar.pipeline import plans as PL  # noqa: E402

EXTRA_CSS = """
:root { --fin:#b0407a; --net:#2a78d6; --bur:#c2410c; --arc:#f6d9e8; }
@media (prefers-color-scheme: dark) { :root { --fin:#f08cc0; --net:#3987e5; --bur:#ea6a3a; --arc:#3a2232; } }
.chart { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:12px; }
svg text { fill:var(--muted); font:11px -apple-system, system-ui, sans-serif; }
svg .axis { stroke:var(--line); } svg .arc { fill:var(--arc); } svg .fin { fill:var(--fin); }
svg .net { stroke:var(--net); stroke-width:2; } svg .bur { fill:var(--bur); }
.legend { display:flex; gap:16px; flex-wrap:wrap; font-size:12px; margin:0 0 6px; }
td.long { min-width:300px; } td:not(.long) { white-space:nowrap; }
.legend i { display:inline-block; width:10px; height:10px; border-radius:2px; margin-right:6px; vertical-align:-1px; }
"""
LON_MIN, LON_MAX = -60.0, 120.0
LEVEL = {"high": ("bad", "high"), "medium": ("warn", "medium"), "review": ("warn", "review"), "low": ("warn", "low"),
         "none": ("ok", "not raised")}


def level(concern: str) -> str:
    cls, text = LEVEL.get(concern, ("warn", concern))
    return f'<span class="badge {cls}">{R.esc(text)}</span>'


def unique_closest(rows):
    seen, out = set(), []
    for n, w, e in rows:
        key = (n.network_name, e.plan, e.satellite)
        if key not in seen:
            seen.add(key)
            out.append((n, w, e))
    return out


def effect_on(b: P.BureauEffect, e: P.PlanEntry) -> bool:
    """Does Bureau row b concern this plan band? sps_results: freq_band '17 G' (or '14 G') is the AP30A feeder link,
    empty is the AP30 downlink; ap30b_tr_res: '6/4' is the C band, '10-11' and '13' the Ku band [CHECKED on 3083 rows]."""
    if b.finnish_satellite != e.satellite or b.db != e.db:
        return False
    band = (b.freq_band or "").strip()
    if b.db == "AP30":
        return (e.plan == "AP30A") == band.endswith("G")
    c_band = e.hi_hz < 8_000_000_000
    return ("6/4" in band) == c_band


def strip(rows: list[tuple[str, list]], effects: list[P.BureauEffect]) -> str:
    """One lane per Finnish plan band: its arc, its position, the co-frequency networks of the issue, Bureau networks."""
    w, left, lane_h = 1000, 215, 34
    h = 30 + lane_h * len(rows)
    x = lambda lon: left + (lon - LON_MIN) / (LON_MAX - LON_MIN) * (w - left - 10)  # noqa: E731
    out = [f'<svg viewBox="0 0 {w} {h}" width="100%" role="img" aria-label="Geostationary orbit strip">']
    for lon in range(int(LON_MIN), int(LON_MAX) + 1, 20):
        out.append(f'<line class="axis" x1="{x(lon):.1f}" x2="{x(lon):.1f}" y1="14" y2="{h - 4}"/>'
                   f'<text x="{x(lon):.1f}" y="10" text-anchor="middle">{lon}{"E" if lon >= 0 else "W"}</text>'.replace(f">{lon}W", f">{-lon}W"))
    for i, (label, (e, nets)) in enumerate(rows):
        y = 22 + i * lane_h
        a = e.arc.arc_deg
        out.append(f'<text x="4" y="{y + 15}">{R.esc(label)}</text>')
        out.append(f'<rect class="arc" x="{x(e.longitude_deg - a):.1f}" y="{y}" width="{x(e.longitude_deg + a) - x(e.longitude_deg - a):.1f}" height="{lane_h - 10}" rx="3"/>')
        for lon, name in nets:
            if LON_MIN <= lon <= LON_MAX:
                out.append(f'<line class="net" x1="{x(lon):.1f}" x2="{x(lon):.1f}" y1="{y + 3}" y2="{y + lane_h - 13}"><title>{R.esc(name)} {lon:g}</title></line>')
        for b in effects:
            if effect_on(b, e) and b.longitude_deg is not None:
                out.append(f'<circle class="bur" cx="{x(b.longitude_deg):.1f}" cy="{y + (lane_h - 10) / 2:.1f}" r="4"><title>{R.esc(b.satellite)}: {R.esc(b.summary())}</title></circle>')
        out.append(f'<rect class="fin" x="{x(e.longitude_deg) - 3:.1f}" y="{y - 2}" width="6" height="{lane_h - 6}" rx="2"><title>{R.esc(e.satellite)}</title></rect>')
    out.append("</svg>")
    legend = ('<div class="legend"><span><i style="background:var(--fin)"></i>Finnish plan position</span>'
              '<span><i style="background:var(--arc)"></i>Annex arc (affected inside)</span>'
              '<span><i style="background:var(--net)"></i>co-frequency network in this issue</span>'
              '<span><i style="background:var(--bur)"></i>Bureau: affects the Finnish entry</span></div>')
    return f'<div class="chart">{legend}{"".join(out)}</div>'


def main() -> int:
    issue = int(sys.argv[1]) if len(sys.argv) > 1 else 3074
    snaps = P.snapshots()
    run = assemble.run(issue)
    entries = P.finnish_entries(snaps=snaps) if snaps else []
    effects = P.bureau_effects(snaps=snaps) if snaps else []

    # co-frequency GSO networks of the issue per Finnish plan band, with their worst-case spacing
    ing = run.ingest
    con = duckdb.connect(str(space_ific.db_path(issue)), read_only=True)
    tol = PL.tolerances(con)
    con.close()
    per_entry: dict[int, dict[str, tuple]] = {i: {} for i in range(len(entries))}
    for n in ing.notices:
        if n.notice_id not in tol or n.longitude_deg is None:
            continue
        te, tw = tol[n.notice_id]
        for g in n.groups:
            for i, e in enumerate(entries):
                if g.direction != e.direction or min(g.freq_max_hz, e.hi_hz) <= max(g.freq_min_hz, e.lo_hz):
                    continue
                _, worst, _ = PL.separation(e.longitude_deg, e.tol_east_deg, e.tol_west_deg, n.longitude_deg, te, tw)
                per_entry[i][n.notice_id] = (n, worst)
    inside = sum(1 for r in run.rows if r.plan_hits)
    closest = unique_closest(sorted(((n, w, e) for i, e in enumerate(entries) for n, w in per_entry[i].values()),
                                    key=lambda t: (t[1], t[0].network_name, t[2].plan, t[2].satellite)))

    lane_rows = [(f"{e.plan} {e.satellite} {e.lo_hz / 1e9:.2f}-{e.hi_hz / 1e9:.2f} GHz",
                  (e, sorted({(n.longitude_deg, n.network_name) for n, _ in per_entry[i].values()})))
                 for i, e in enumerate(entries)]

    # evidence check restricted to the plan citations
    checks = [c for c in evidence_check.check(run.result)
              if ":" in c.locator.split(".")[0] or c.locator.startswith(("plan_arc(", "plan_arcs.csv", "geography(plan:"))]
    fails = [c for c in checks if c.status != "PASS"]
    plan_findings = [f for f in run.result.findings if f.notice_id in (run.plan_notices or {})]

    ok = bool(snaps) and len({e.satellite for e in entries}) == 3 and not fails and all(a.source and a.page for a in P.arcs()) \
        and len(plan_findings) == len(run.plan_notices or {})
    st = "PASS" if ok else "FAIL"

    body = (
        R.tiles([("plan snapshot", ", ".join(P.tag(d, n) for d, n in sorted(snaps.items())) or "missing"),
                 ("Finnish plan bands", str(len(entries))), ("Bureau rows naming Finland", str(len(effects))),
                 ("networks affecting Finland", str(len({b.notice_id for b in effects}))),
                 (f"plan sections in {issue}", str(len(plan_findings))),
                 (f"IFIC {issue} groups inside an arc", str(inside)),
                 ("plan citations re-checked", f"{len(checks)} ({len(fails)} mismatches)")])
        + "<h2>The geostationary orbit around the Finnish plan positions</h2><p class='sub'>One lane per Finnish plan band. "
          "The shaded band is the Annex arc: a co-frequency, co-directional network inside it is considered affected. Blue ticks "
          f"are the networks of IFIC {issue} in the same band and direction; orange dots are the networks the Bureau's own "
          "examination found affecting the Finnish entry (from earlier issues).</p>" + strip(lane_rows, effects)
        + "<h2>Finnish plan entries</h2>"
        + R.table(["Plan", "Satellite", "Position", "Band (MHz)", "Direction", "Beam", "Gain dBi", "Evidence"],
                  [[e.plan, e.satellite, f"{e.longitude_deg:g} E", f"{e.lo_hz / 1e6:g}-{e.hi_hz / 1e6:g}",
                    assemble.DIRECTION_TEXT[e.direction], e.beam_name or "", f"{e.gain_dbi:g}" if e.gain_dbi is not None else "",
                    f"<code>{R.esc(e.group_locator)}</code>"] for e in entries], raw=True)
        + "<h2>Orbital arcs</h2><p class='sub'>data/reference/plan_arcs.csv, typed from RR 2024 Vol. 2. The arc is a pre-screen; "
          "the Annex pfd and C/I tests that can clear a case are the Bureau's.</p>"
        + R.table(["Row", "Plan", "Band (MHz)", "Direction", "Affected if spacing", "Source", "Page"],
                  [[a.id, a.plan, f"{a.lo_hz / 1e6:g}-{a.hi_hz / 1e6:g}", assemble.DIRECTION_TEXT[a.direction], a.rule_text(),
                    a.source, a.page] for a in P.arcs()])
        + f"<h2>Plan sections published in IFIC {issue}</h2><p class='sub'>Notices of the plan databases whose record carries "
          f"wic_no = {issue}. Each one is a finding of its own in the results file.</p>"
        + R.table(["Finding", "Concern", "Network", "Section", "Reason"],
                  [[f.id, level(f.concern),
                    R.esc(f"{run.plan_notices[f.notice_id].administration} {run.plan_notices[f.notice_id].satellite}"),
                    R.esc(", ".join(run.plan_notices[f.notice_id].sections)), R.esc(f.reason)] for f in plan_findings], raw=True)
          .replace("<td>Not raised", '<td class="long">Not raised').replace("<td>The Bureau", '<td class="long">The Bureau')
          .replace("<td>Co-frequency", '<td class="long">Co-frequency')
        + f"<h2>Closest co-frequency networks of IFIC {issue}</h2>"
        + R.table(["Network", "Position", "Finnish entry", "Worst-case spacing", "Arc", "Inside"],
                  [[n.network_name, f"{n.longitude_deg:g}", f"{e.plan} {e.satellite} ({e.longitude_deg:g} E)", f"{w:.2f} deg",
                    e.arc.rule_text(), "yes" if e.arc.within(w) else "no"] for n, w, e in closest[:12]])
        + "<h2>Networks the Bureau found affecting Finland</h2><p class='sub'>The watch list in results/plans_finland.csv: "
          "examination rows of the plan databases whose affected entry is Finnish, largest pfd excess first.</p>"
        + R.table(["Network", "Adm", "Position", "Provision", "Published", "Finnish entry", "Band", "pfd excess dB", "Degradation dB"],
                  [[b.satellite or "", b.administration, f"{b.longitude_deg:g}" if b.longitude_deg is not None else "",
                    b.provision or "", str(b.ific_no or ""), b.finnish_satellite or "", b.freq_band or "",
                    "" if b.pfd_excess_db is None else f"{b.pfd_excess_db:.2f}",
                    "" if b.degradation_db is None else f"{b.degradation_db:.2f}"]
                   for b in sorted(effects, key=lambda b: -(b.pfd_excess_db or -1))])
        + "<h2>Evidence check of the plan citations</h2>"
        + R.table(["Kind", "Status", "Citations"], [[k, R.badge(s), str(n)] for (k, s), n in sorted(Counter((c.kind, c.status) for c in checks).items())], raw=True)
        + "<p class='sub'>Caveat: ITU keeps only the latest plan snapshot online. It holds the latest record of each network, so "
          "a plan section of an older issue that was later modified carries the later issue number.</p>"
    )
    summary = {"status": st, "issue": issue, "snapshots": snaps, "finnish_entries": len(entries), "bureau_rows": len(effects),
               "networks_affecting_finland": sorted({b.satellite for b in effects if b.satellite}),
               "plan_sections": [{"notice_id": f.notice_id, "concern": f.concern} for f in plan_findings],
               "groups_inside_arc": inside, "plan_citations": len(checks), "plan_citation_mismatches": len(fails)}
    out = settings.reports_dir / str(issue) / "08_plans.html"
    R.write(out, R.page(f"Space IFIC {issue}: AP30, AP30A and AP30B plans",
                        f"Finland's plan entries against the issue. radar.adapters.plans, radar.pipeline.plans. {R.badge(st)}",
                        body, EXTRA_CSS), summary)
    print(f"written {out}: {st}; entries {len(entries)}, Bureau rows {len(effects)}, plan sections {len(plan_findings)}, "
          f"groups inside an arc {inside}, plan citations {len(checks)} ({len(fails)} mismatches)")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
