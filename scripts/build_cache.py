#!/usr/bin/env python3
"""Build the screen's data: data/cache/<kind>_<issue>.json = AnalysisResult + per-finding context.

    uv run python scripts/build_cache.py            # space 3074 and terrestrial 3076

The context holds what the one screen draws and the contracts do not carry: notice details, the Finnish rows under
the lead group (spectrum tab), the geometry (map tab), the score factors, every located earth station of the notice,
and under the bundle key "map" every special-interest station and (terrestrial) every located notice, raised or not,
for the overview map (radar.map_layers). The API serves these files, so the
screen and demo mode need neither the .mdb nor DuckDB (pm_pack/06 "Demo mode"). Output is deterministic.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT / "backend"), str(ROOT)]

from radar import map_layers  # noqa: E402
from radar.adapters import special_interest as SI  # noqa: E402
from radar.adapters import traficom_table  # noqa: E402
from radar.config import settings  # noqa: E402
from radar.pipeline import assemble  # noqa: E402
from radar.pipeline import geography as G  # noqa: E402
from radar.pipeline import relevance as rel  # noqa: E402
from radar.pipeline import terrestrial as TR  # noqa: E402

MAX_LANES = 24


def lanes_for(ids: list[int], bands: dict, lo: int, hi: int) -> list[dict]:
    seen, out = {}, []
    for i in ids:
        b = bands[i]
        key = (b.services_in_finland, b.lower_hz, b.upper_hz)
        if key in seen:
            seen[key]["ids"].append(i)
            continue
        c = rel.classify(b.services_in_finland)
        lane = {"ids": [i], "lower_hz": b.lower_hz, "upper_hz": b.upper_hz, "services": b.services_in_finland,
                "usage": b.sub_band_usage, "category": c.category, "space_direction": c.space_direction, "primary": c.primary}
        seen[key] = lane
        out.append(lane)
    order = {"terrestrial": 0, "passive": 1, "space": 2, "not_allocated": 3}
    out.sort(key=lambda l: (order[l["category"]], l["lower_hz"]))
    return out[:MAX_LANES]


def space(issue: int) -> dict:
    run = assemble.run(issue)
    bands = {b.id: b for b in traficom_table.subbands()}
    by_notice = run.notices()
    rows = {r.group_id: r for r in run.rows}
    geo = None
    ctx = {}
    import duckdb
    from radar.adapters import space_ific
    with duckdb.connect(str(space_ific.db_path(issue)), read_only=True) as con:
        geo = G.for_issue(run.ingest.notices, con)
    for f in run.result.findings:
        n = by_notice[f.notice_id]
        r = rows.get(f.group_id) if f.group_id else None
        s = run.scores.get(f.group_id) if f.group_id else None
        g = G.group_relevance(geo, f.notice_id, f.group_id, r.direction) if r else geo.by_notice.get(f.notice_id)
        detail = dict(g.detail) if g else {}
        ctx[f.id] = {
            "title": f"{n.administration} {n.network_name}",
            "notice": {"administration": n.administration, "network": n.network_name, "special_section": n.special_section,
                       "all_sections": run.ingest.special_sections.get(n.notice_id, [n.special_section] if n.special_section else []),
                       "orbit": n.orbit,
                       "longitude_deg": n.longitude_deg, "groups_in_issue": len(n.groups)},
            "group": None if r is None else {"group_id": r.group_id, "freq_min_hz": r.freq_min_hz, "freq_max_hz": r.freq_max_hz,
                                             "direction": r.direction, "paths": sorted(r.paths), "overlap_hz": r.overlap_hz,
                                             "uncovered_hz": r.uncovered_hz,
                                             "finland_named_provisions": r.finland_named_provisions},
            "lanes": [] if r is None else lanes_for(r.matched_subband_ids, bands, r.freq_min_hz, r.freq_max_hz),
            "geo": {"relevance": g.relevance if g else "unknown", "method": g.method if g else "none",
                    "note": g.note if g else "", "detail": json.loads(json.dumps(detail, default=str))},
            "rule": s.rule if s else None, "score": s.score if s else None,
            "factors": s.factors if s else {},
            "stations": [] if r is None else station_context(r),
            # every located earth station of the notice, for the overview map (geo.detail keeps only the nearest)
            "earth_stations": map_layers.earth_stations(n.notice_id, [g.group_id for g in n.groups], geo),
        }
    finding_by_notice = {f.notice_id: f.id for f in run.result.findings}
    concern = {f.id: f.concern for f in run.result.findings}
    return {"result": json.loads(run.result.model_dump_json()), "context": ctx, "overview": {"gso_arc": gso_arc()},
            "map": {"special_interest": map_layers.special_interest(
                SI.stations(), map_layers.reached_by_groups(run.rows, finding_by_notice), concern)}}


def gso_arc(step_deg: int = 1) -> list[dict]:
    """For every GSO longitude: the highest elevation from any Finnish reference point and where (radar.pipeline.geography).
    Drawn behind the flagged GSO filings on the Overview tab; computed here so the screen never computes geometry."""
    out = []
    for lon in range(-180, 181, step_deg):
        g = G.gso_result(float(lon))
        out.append({"lon": lon, "max_elevation_deg": g.detail["max_elevation_deg"], "point": g.detail["max_elevation_point"]})
    return out


def station_context(r) -> list[dict]:
    """The lead group's special-interest stations for the map: position, protected channel, reach (geography)."""
    from radar.adapters import special_interest as SI
    by_number = {}
    for st in SI.stations():
        by_number.setdefault(st.station_number, st)
    out = []
    for number in r.matched_station_numbers:
        st = by_number.get(number)
        if st is not None:
            out.append({"number": number, "class": st.licence_class, "lat": st.lat, "lon": st.lon, "centre_hz": st.centre_hz,
                        "bandwidth_hz": st.bandwidth_hz, "row": st.source_row, "reach": r.station_reach.get(number, {})})
    return sorted(out, key=lambda s: (s["reach"].get("elevation_deg", 0), s["reach"].get("distance_km", 0), s["number"]))


def terrestrial(issue: int) -> dict:
    run = TR.run(issue)
    bands = traficom_table.subbands()
    bmap = {b.id: b for b in bands}
    by_id = {n.notice_id: n for n in run.ingest.notices}
    ctx = {}
    for f in run.result.findings:
        if f.concern == "none":
            continue
        n = by_id[f.notice_id]
        c = run.calcs[f.notice_id]
        e = run.ingest.extra[f.notice_id]
        lo = (n.freq_hz or 0) - (n.bandwidth_hz or 0) // 2
        hi = (n.freq_hz or 0) + (n.bandwidth_hz or 0) // 2
        ids = [b.id for b, _ in traficom_table.overlapping(lo, max(hi, lo + 1), bands)] if n.freq_hz else []
        ctx[f.id] = {
            "title": f"{n.administration} {n.site_name or ''}".strip(),
            "notice": {"administration": n.administration, "site_name": n.site_name, "change": n.change,
                       "station_class": n.station_class, "notice_type": e.notice_type, "freq_hz": n.freq_hz,
                       "bandwidth_hz": n.bandwidth_hz, "erp_dbw": n.erp_dbw, "antenna_height_m": n.antenna_height_m,
                       "azimuth_deg": n.azimuth_deg, "lat": n.lat, "lon": n.lon},
            "group": None if not n.freq_hz else {"freq_min_hz": lo, "freq_max_hz": hi, "direction": n.change},
            "lanes": lanes_for(ids, bmap, lo, hi),
            "geo": {"relevance": f.geo_relevance, "method": "border_distance" if c.status == "computed" else "none",
                    "note": (f"{c.distance_km:g} km from the nearest point of the Finnish border; path "
                             + ", ".join(f"{d:g} km {'land' if k == 'Land' else 'sea'}" for d, k in c.segments)
                             if c.status == "computed" else c.reason), "detail": {
                        "distance_km": c.distance_km, "nearest": None if not c.nearest else {"lat": c.nearest[0], "lon": c.nearest[1]},
                        "segments": [{"km": d, "zone": k} for d, k in c.segments],
                        "e_dbuv_m": c.e_dbuv_m, "free_space_dbuv_m": c.free_space_dbuv_m}},
            "rule": None, "score": None, "factors": {},
            "stations": [{"number": s["number"], "class": s["class"], "lat": s["lat"], "lon": s["lon"], "centre_hz": s["centre_hz"],
                          "row": s["row"], "reach": {"distance_km": s["distance_km"], "e_dbuv_m": s["e_dbuv_m"],
                                                     "margin_db": s["margin_db"], "h2_m": s["h2_m"]}} for s in c.stations],
        }
    result = json.loads(run.result.model_dump_json())
    result["findings"] = [f for f in result["findings"] if f["concern"] != "none"]
    reached: dict[str, set[str]] = {}
    for f in run.result.findings:
        c = run.calcs.get(f.notice_id)
        for s in (c.stations if c else ()):
            reached.setdefault(s["number"], set()).add(f.id)
    concern = {f.id: f.concern for f in run.result.findings}
    return {"result": result, "context": ctx,
            # all located notices (raised or not) and every special-interest station, for the overview map
            "map": {"terrestrial": map_layers.terrestrial(run.ingest.notices, run.result.findings, run.ingest.extra),
                    "special_interest": map_layers.special_interest(SI.stations(), reached, concern)},
            "omitted": {"not_raised": run.result.screened - len(result["findings"]),
                        "note": f"they are listed in results/terrestrial_{issue}.csv"}}


def main() -> int:
    out = settings.data_dir / "cache"
    out.mkdir(parents=True, exist_ok=True)
    for kind, issue, fn in (("space", 3074, space), ("terrestrial", 3076, terrestrial)):
        data = fn(issue)
        p = out / f"{kind}_{issue}.json"
        p.write_text(json.dumps(data, separators=(",", ":"), sort_keys=True), encoding="utf-8")
        r = data["result"]
        print(f"{p}: {r['screened']} screened, {r['flagged']} flagged, {len(data['context'])} contexts, {p.stat().st_size / 1e6:.2f} MB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
