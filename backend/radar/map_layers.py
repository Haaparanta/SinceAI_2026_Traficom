"""Map layers for the screen's "All on map" tab: every located datapoint, not only the lead group's.

The findings carry the lead group's geometry (map tab of one finding). The overview map also needs what the
findings leave out, so that all provided data is on screen:

* earth_stations(...):   every located earth station of a space notice, over all its groups in the issue
                         (geography keeps only the nearest one per group).
* special_interest(...): every station of the special-interest sheet, with the findings that reach it through
                         any of their groups (after geography), not only through the lead group.
* terrestrial(...):      every located terrestrial notice of the issue, including the ones not raised.

Pure functions over the pipeline's outputs; scripts/build_cache.py writes the result into data/cache/*.json under
the bundle key "map" (screen context, not part of the frozen contract). Output is deterministic.
"""
from __future__ import annotations

from collections.abc import Iterable

from radar.pipeline import geography as G

CONCERN_ORDER = {"high": 4, "medium": 3, "review": 2, "low": 1, "none": 0}


def _located(s: dict | None) -> bool:
    return bool(s) and s.get("lat") is not None and s.get("lon") is not None


def earth_stations(notice_id: str, group_ids: Iterable[str], geo: G.IssueGeography) -> list[dict]:
    """Every located earth station of one space notice: the station of an S notice, and the stations of each group.

    One entry per distinct station (name and position), with the groups that name it, nearest to Finland first.
    """
    out: dict[tuple, dict] = {}

    def add(s: dict, group_id: str | None) -> None:
        if not _located(s):
            return
        lat, lon = round(float(s["lat"]), 6), round(float(s["lon"]), 6)
        key = (s.get("name"), lat, lon)
        e = out.get(key)
        if e is None:
            d = s.get("distance_km")
            e = out[key] = {"name": s.get("name"), "country": s.get("country"), "type": s.get("type"), "lat": lat, "lon": lon,
                            "distance_km": d if d is not None else round(G.distance_to_finland_km(round(lat, 4), round(lon, 4)), 1),
                            "group_ids": []}
        if group_id is not None and group_id not in e["group_ids"]:
            e["group_ids"].append(group_id)

    add(geo.notice_stations.get(notice_id), None)
    for gid in group_ids:
        for s in geo.group_stations.get(gid, []):
            add(s, gid)
    for e in out.values():
        e["group_ids"].sort()
    return sorted(out.values(), key=lambda e: (e["distance_km"], e["name"] or "", e["lat"], e["lon"]))


def special_interest(stations: Iterable, reached_by: dict[str, set[str]], concern: dict[str, str]) -> list[dict]:
    """Every special-interest station with the findings that reach it.

    stations:   SpecialInterestStation rows as read from the sheet (a number can repeat; one entry per number, first row)
    reached_by: station number -> finding ids whose groups match and reach it (after geography)
    concern:    finding id -> concern, to give each station the highest concern of the findings that reach it
    """
    out, seen = [], set()
    for s in stations:
        if s.station_number in seen:
            continue
        seen.add(s.station_number)
        ids = sorted(reached_by.get(s.station_number, ()))
        top = max((concern.get(i, "none") for i in ids), key=lambda c: CONCERN_ORDER.get(c, 0), default=None)
        out.append({"number": s.station_number, "class": s.licence_class, "lat": s.lat, "lon": s.lon,
                    "centre_hz": s.centre_hz, "bandwidth_hz": s.bandwidth_hz, "row": s.source_row,
                    "finding_ids": ids, "concern": top})
    return sorted(out, key=lambda e: e["number"])


def reached_by_groups(rows: Iterable, finding_by_notice: dict[str, str]) -> dict[str, set[str]]:
    """Station number -> finding ids, from every screened group's matched stations (space: one finding per notice)."""
    out: dict[str, set[str]] = {}
    for r in rows:
        fid = finding_by_notice.get(r.notice_id)
        if fid is None:
            continue
        for number in r.matched_station_numbers:
            out.setdefault(number, set()).add(fid)
    return out


def terrestrial(notices: Iterable, findings: Iterable, extra: dict) -> list[dict]:
    """Every located terrestrial notice with its finding id, concern, type and change, raised or not."""
    by_notice = {f.notice_id: f for f in findings}
    out = []
    for n in notices:
        if n.lat is None or n.lon is None:
            continue
        f = by_notice.get(n.notice_id)
        e = extra.get(n.notice_id)
        out.append({"notice_id": n.notice_id, "finding_id": f.id if f else None, "concern": f.concern if f else "none",
                    "administration": n.administration, "site_name": n.site_name, "station_class": n.station_class,
                    "notice_type": getattr(e, "notice_type", None), "change": n.change, "freq_hz": n.freq_hz,
                    "erp_dbw": n.erp_dbw, "lat": n.lat, "lon": n.lon})
    return sorted(out, key=lambda e: e["notice_id"])
