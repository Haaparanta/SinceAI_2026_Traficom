#!/usr/bin/env python3
"""Broadcasting extension (GE84 FM, GE06 TV) of a terrestrial issue: visual proof.

    uv run python scripts/broadcasting_report.py 3076     # writes reports/3076/03_broadcasting.html and .summary.json

Checks: every FM and TV notice of the issue is screened and has a reason; no notice beyond the P.1546 range is
computed; every computed notice has a trace and an evidence item for its field strength; every citation reopens
(radar.evidence_check.check_broadcasting).
"""
from __future__ import annotations

import sys
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT)]

from radar import evidence_check as EC  # noqa: E402
from radar import report_html as R  # noqa: E402
from radar.config import settings  # noqa: E402
from radar.pipeline import broadcasting as BR  # noqa: E402
from radar.pipeline import terrestrial as TR  # noqa: E402


def main() -> int:
    issue = int(sys.argv[1]) if len(sys.argv) > 1 else 3076
    run = BR.run(issue)
    by_id = {n.notice_id: n for n in run.ingest.notices}
    findings = run.result.findings
    computed = [(by_id[f.notice_id], run.calcs[f.notice_id], f) for f in findings if run.calcs[f.notice_id].status == "computed"]
    checks_ev = EC.check_broadcasting(run.result)
    ev_fail = [c for c in checks_ev if c.status != "PASS"]
    by_adm = Counter((n.administration, n.station_class) for n in run.ingest.notices)
    checks = [
        ("Every FM and TV notice is screened and has a reason", len(findings) == len(run.ingest.notices) and all(f.reason for f in findings),
         f"{len(findings)} notices"),
        ("No notice beyond the P.1546 range is computed", all(c.border.distance_km <= TR.MAX_DISTANCE_KM for _, c, _ in computed), ""),
        ("Every computed notice has a trace and a field-strength evidence item",
         all(f.calc.method == "p1546_field_strength" and any(e.locator.startswith("broadcast_border(") for e in f.evidence) for _, _, f in computed),
         f"{len(computed)} computed"),
        ("Every citation reopens", not ev_fail, f"{len(checks_ev)} citations, {len(ev_fail)} mismatches"),
    ]
    status = "PASS" if all(ok for _, ok, _ in checks) else "FAIL"
    reasons = Counter("beyond the P.1546 range (over 1 000 km from Finland)" if "beyond the" in (c.reason or "") else (c.reason or "computed")
                      for c in run.calcs.values())
    trig_rows = [[t.id, f"{t.f_min_mhz:g}-{t.f_max_mhz:g}", t.system, f"{t.trigger_dbuv_m:g}", f"{t.time_pct:g} %", f"{t.h_rx_m:g} m",
                  R.esc(t.source), t.page, R.esc(t.review)] for t in BR.triggers()]
    rows = []
    for n, c, f in sorted(computed, key=lambda t: t[1].border.distance_km):
        w = BR.deciding(n, c)
        rows.append([f.id, f"{n.administration} {R.esc(n.site_name or '')}", "FM" if n.station_class == "BC" else "TV", f"{n.freq_hz / 1e6:g}",
                     n.change, f"{n.erp_dbw:g}", f"{c.border.distance_km:g}", f"{c.border.e_dbuv_m:g}", str(len(c.stations)),
                     "-" if not c.stations else f"{c.stations[0].name}: {c.stations[0].e_dbuv_m:g} at {c.stations[0].distance_km:g} km",
                     "-" if c.trigger is None else f"{c.trigger.trigger_dbuv_m:g}",
                     "-" if w.margin_db is None else f"{w.margin_db:g}", f.concern])
    body = (
        R.tiles([("FM and TV notices", str(len(findings))), ("computed", str(len(computed))),
                 ("flagged", str(run.result.flagged)), ("triggers loaded", str(len(BR.triggers())))])
        + f"<p class='sub'>Same engine as the land-mobile side quest: P.1546-6 reference implementation, filed effective height towards "
          f"the receiver, land and sea path zones; here at {BR.RX_HEIGHT_M:g} m receiving height and {BR.TIME_PCT:g} % of time. Kept "
          f"apart from the graded land-mobile file, in results/broadcasting_{issue}.csv.</p>"
        + "<h2>Checks</h2>" + R.table(["Check", "Status", "Detail"], [[c, R.badge("PASS" if ok else "FAIL"), R.esc(d)] for c, ok, d in checks], raw=True)
        + "<h2>Who filed what</h2>" + R.table(["Administration", "Class", "Notices"],
                                            [[a, "FM (BC)" if k == "BC" else "TV (BT)", str(v)] for (a, k), v in by_adm.most_common(15)])
        + "<h2>Why notices were not computed</h2>" + R.table(["Reason", "Notices"], [[R.esc(k), str(v)] for k, v in reasons.most_common()])
        + "<h2>Computed notices</h2><p class='sub'>Border: nearest point of the Finnish border. Stations: special-interest stations on the "
          "same channel within 1 000 km; the worst is shown. The deciding point is the one with the higher concern.</p>"
        + R.table(["Finding", "Notice", "Service", "MHz", "Change", "e.r.p. dBW", "Border km", "Border E", "Stations", "Worst station E (km)",
                   "Trigger", "Margin dB", "Concern"], rows)
        + "<h2>GE84 and GE06 triggers</h2>"
        + (R.table(["Row", "MHz", "System", "dB(uV/m)", "Time", "Height", "Source", "Page", "Review"], trig_rows, raw=True) if trig_rows
           else "<p>None loaded: data/reference/ge_triggers.csv is missing, so every computed notice reports its field strength "
                "without a criterion.</p>")
    )
    out = settings.reports_dir / str(issue) / "03_broadcasting.html"
    R.write(out, R.page(f"Terrestrial IFIC {issue}: FM and TV broadcasting", f"Broadcasting extension (GE84, GE06). {R.badge(status)}", body),
            {"status": status, "checks": [[c, ok, d] for c, ok, d in checks], "concern": dict(Counter(f.concern for f in findings))})
    print(f"written {out}: {status}")
    for c, ok, d in checks:
        print(f"  {'PASS' if ok else 'FAIL'}  {c}  {d}")
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
