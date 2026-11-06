"""Step B3 of pm_pack/08: can the station in a filing reach Finland?

* GSO space stations: elevation and slant range from the Finnish reference points
  (data/reference/fi_reference_points.csv) with the pm_pack/06 formula, R = 6378.137 km, h = 35 786 km.
  visible: highest elevation >= 10 deg; low_elevation: 0 to 10 deg; not_visible: below the horizon everywhere.
* Non-GSO space stations: for each orbit, the highest latitude from which a satellite can be seen at 0 and
  10 deg elevation (circular-orbit coverage at the apogee, the largest footprint), compared with Finland's
  southernmost latitude. Orbits around another body (Moon, Sun, Jupiter) are not_visible.
* Earth stations (uplink groups, earth-station notices): distance from the station to Finland (Natural Earth
  polygon via scoring.geometry.Region); near_border within NEAR_BORDER_KM, otherwise far; typical earth
  stations have no location and stay unknown.

Every result keeps its inputs so the report and the evidence can show them [HYPOTHESIS thresholds, Q1].
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import duckdb

from radar import schema_map
from radar.config import ROOT
from radar.models import Notice
from scoring.geometry import Region

R_EARTH_KM = 6378.137          # pm_pack/06, equatorial radius
GSO_ALT_KM = 35786.0
LOW_ELEVATION_DEG = 10.0       # pm_pack/06
NEAR_BORDER_KM = 500.0         # [HYPOTHESIS] order of the largest earth-station coordination distances (RR App. 7)
FINLAND_LAT_MIN = 59.8         # Hanko, southernmost reference point
POINTS_FILE = ROOT / "data" / "reference" / "fi_reference_points.csv"

GeoRelevance = str  # visible | low_elevation | not_visible | near_border | far | unknown


@lru_cache(maxsize=1)
def reference_points() -> tuple[tuple[str, float, float], ...]:
    with POINTS_FILE.open(encoding="utf-8") as fh:
        return tuple((r["name"], float(r["lat_deg"]), float(r["lon_deg"])) for r in csv.DictReader(fh))


def gso_look(lat_deg: float, lon_deg: float, sat_lon_deg: float) -> tuple[float, float]:
    """(elevation_deg, slant_range_km) from a ground point to a GSO satellite. pm_pack/06 formula."""
    phi, dl = math.radians(lat_deg), math.radians(sat_lon_deg - lon_deg)
    cos_g = max(-1.0, min(1.0, math.cos(phi) * math.cos(dl)))
    sin_g = math.sqrt(1.0 - cos_g * cos_g)
    rs = R_EARTH_KM + GSO_ALT_KM
    elevation = math.degrees(math.atan2(cos_g - R_EARTH_KM / rs, sin_g)) if sin_g > 0 else 90.0
    slant = math.sqrt(R_EARTH_KM ** 2 + rs ** 2 - 2 * R_EARTH_KM * rs * cos_g)
    return elevation, slant


def coverage_lat_limit(inclination_deg: float, altitude_km: float, min_elev_deg: float) -> float:
    """Highest latitude that sees a satellite of this inclination and altitude at >= min_elev_deg."""
    i_eff = inclination_deg if inclination_deg <= 90 else 180.0 - inclination_deg
    e = math.radians(min_elev_deg)
    lam = math.acos(R_EARTH_KM / (R_EARTH_KM + altitude_km) * math.cos(e)) - e
    return min(90.0, i_eff + math.degrees(lam))


def dms_to_deg(deg, minutes, seconds, hemisphere) -> float | None:
    if deg is None:
        return None
    v = float(deg) + float(minutes or 0) / 60 + float(seconds or 0) / 3600
    return -v if (hemisphere or "").upper() in ("W", "S") else v


@lru_cache(maxsize=4096)
def distance_to_finland_km(lat: float, lon: float) -> float:
    return Region.load().distance_to_country_km("FIN", lat, lon)[0]


def classify_distance(d_km: float | None) -> GeoRelevance:
    if d_km is None:
        return "unknown"
    return "near_border" if d_km <= NEAR_BORDER_KM else "far"


@dataclass
class GeoResult:
    relevance: GeoRelevance
    method: str                                   # gso_elevation | ngso_coverage | earth_station_distance | none
    detail: dict = field(default_factory=dict)    # inputs and intermediate values for the trace
    note: str = ""


def gso_result(sat_lon: float | None) -> GeoResult:
    if sat_lon is None:
        return GeoResult("unknown", "none", note="GSO longitude not filed")
    pts = []
    for name, lat, lon in reference_points():
        el, d = gso_look(lat, lon, sat_lon)
        pts.append({"point": name, "lat": lat, "lon": lon, "elevation_deg": round(el, 3), "slant_range_km": round(d, 1)})
    best = max(pts, key=lambda p: p["elevation_deg"])
    visible = [p for p in pts if p["elevation_deg"] > 0]
    lowest = min(visible, key=lambda p: p["elevation_deg"]) if visible else None
    if best["elevation_deg"] >= LOW_ELEVATION_DEG:
        rel = "visible"
    elif best["elevation_deg"] > 0:
        rel = "low_elevation"
    else:
        rel = "not_visible"
    return GeoResult(rel, "gso_elevation", {
        "satellite_longitude_deg": sat_lon, "points": pts,
        "max_elevation_deg": best["elevation_deg"], "max_elevation_point": best["point"],
        "lowest_visible": lowest,
    }, note=f"highest elevation {best['elevation_deg']:.1f} deg at {best['point']}")


def ngso_result(reference_body: str | None, orbits: list[tuple[float, float, float]]) -> GeoResult:
    """orbits: (inclination_deg, apogee_km, perigee_km)."""
    if reference_body and reference_body != "T":
        body = {"L": "the Moon", "S": "the Sun", "J": "Jupiter"}.get(reference_body, reference_body)
        return GeoResult("not_visible", "none", {"reference_body": reference_body}, note=f"orbits {body}")
    if not orbits:
        return GeoResult("unknown", "none", {"reference_body": reference_body}, note="no orbit filed")
    best0 = best10 = -90.0
    best_orbit = None
    for inc, apo, per in orbits:
        if inc is None or apo is None:
            continue
        l0, l10 = coverage_lat_limit(inc, apo, 0.0), coverage_lat_limit(inc, apo, LOW_ELEVATION_DEG)
        if l10 > best10 or (l10 == best10 and l0 > best0):
            best_orbit = {"inclination_deg": round(float(inc), 4), "apogee_km": round(float(apo), 3),
                          "perigee_km": None if per is None else round(float(per), 3)}
        best0, best10 = max(best0, l0), max(best10, l10)
    if best_orbit is None:
        return GeoResult("unknown", "none", note="orbit parameters missing")
    rel = "visible" if best10 >= FINLAND_LAT_MIN else "low_elevation" if best0 >= FINLAND_LAT_MIN else "not_visible"
    return GeoResult(rel, "ngso_coverage", {
        "orbits": len(orbits), "best_orbit": best_orbit,
        "lat_limit_0deg": round(best0, 2), "lat_limit_10deg": round(best10, 2), "finland_lat_min": FINLAND_LAT_MIN,
    }, note=f"seen up to {best10:.1f} N at 10 deg elevation (Finland from {FINLAND_LAT_MIN} N)")


def earth_station_result(stations: list[dict]) -> GeoResult:
    """stations: dicts with name, country, lat, lon (None when the station is typical)."""
    located = [s for s in stations if s.get("lat") is not None and s.get("lon") is not None]
    if not located:
        return GeoResult("unknown", "none", {"stations": len(stations)}, note="typical earth station, no location filed")
    for s in located:
        s["distance_km"] = round(distance_to_finland_km(round(s["lat"], 4), round(s["lon"], 4)), 1)
    nearest = min(located, key=lambda s: s["distance_km"])
    rel = classify_distance(nearest["distance_km"])
    return GeoResult(rel, "earth_station_distance", {
        "stations": len(stations), "located": len(located), "nearest": nearest, "near_border_km": NEAR_BORDER_KM,
    }, note=(f"earth station {nearest['name']} ({nearest['country']}) is inside Finland" if nearest["distance_km"] == 0
             else f"nearest earth station {nearest['name']} ({nearest['country']}) {nearest['distance_km']:.0f} km from Finland"))


# ---------------------------------------------------------------------------------------------------------------

@dataclass
class IssueGeography:
    by_notice: dict[str, GeoResult]                 # space-station visibility, or earth-station notice location
    by_group: dict[str, GeoResult]                  # earth-station location for uplink groups of space notices


def for_issue(notices: list[Notice], con: duckdb.DuckDBPyConnection) -> IssueGeography:
    M = schema_map.load()
    q = lambda e, c, a=None: M.q("space", e, c, a)  # noqa: E731
    ids = [n.notice_id for n in notices]
    types = dict(con.execute(f"SELECT CAST({q('notice','notice_id')} AS VARCHAR), {q('notice','orbit_code')} "
                             f"FROM {M.t('space','notice')}").fetchall())
    ref_body = dict(con.execute(f"SELECT CAST({q('non_gso','notice_id')} AS VARCHAR), {q('non_gso','reference_body')} "
                                f"FROM {M.t('space','non_gso')}").fetchall())
    orbits: dict[str, list] = {}
    for nid, inc, apo, per in con.execute(
            f"SELECT CAST({q('orbit','notice_id')} AS VARCHAR), {q('orbit','inclination_deg')}, {q('orbit','apogee_km')}, "
            f"{q('orbit','perigee_km')} FROM {M.t('space','orbit')}").fetchall():
        orbits.setdefault(nid, []).append((inc, apo, per))
    es_notice = {}
    for row in con.execute(
            f"SELECT CAST({q('earth_station_notice','notice_id')} AS VARCHAR), {q('earth_station_notice','station_name')}, "
            + ", ".join(q('earth_station_notice', c) for c in ("lon_deg", "lon_min", "lon_sec", "lon_hemisphere",
                                                              "lat_deg", "lat_min", "lat_sec", "lat_hemisphere"))
            + f" FROM {M.t('space','earth_station_notice')}").fetchall():
        nid, name, lo_d, lo_m, lo_s, lo_h, la_d, la_m, la_s, la_h = row
        es_notice[nid] = {"name": name, "country": None, "lat": dms_to_deg(la_d, la_m, la_s, la_h),
                          "lon": dms_to_deg(lo_d, lo_m, lo_s, lo_h)}
    group_stations: dict[str, list[dict]] = {}
    for gid, seq, name, stype, ctry, lat, lon in con.execute(
            f"SELECT CAST({q('earth_station','group_id')} AS VARCHAR), {q('earth_station','seq_no')}, {q('earth_station','station_name')}, "
            f"{q('earth_station','station_type')}, {q('earth_station','country')}, {q('earth_station','lat_deg')}, "
            f"{q('earth_station','lon_deg')} FROM {M.t('space','earth_station')}").fetchall():
        group_stations.setdefault(gid, []).append({"name": name, "seq_no": seq, "type": stype, "country": ctry,
                                                   "lat": None if lat is None else float(lat),
                                                   "lon": None if lon is None else float(lon)})

    by_notice: dict[str, GeoResult] = {}
    by_group: dict[str, GeoResult] = {}
    for n in notices:
        t = types.get(n.notice_id)
        if t == "G":
            by_notice[n.notice_id] = gso_result(n.longitude_deg)
        elif t == "N":
            by_notice[n.notice_id] = ngso_result(ref_body.get(n.notice_id), orbits.get(n.notice_id, []))
        elif t == "S":
            st = es_notice.get(n.notice_id)
            if st and st["lat"] is not None:
                st = {**st, "country": n.administration}
            by_notice[n.notice_id] = earth_station_result([st] if st else [])
        else:
            by_notice[n.notice_id] = GeoResult("unknown", "none", note=f"notice type {t!r}")
        if t in ("G", "N"):
            for g in n.groups:
                if g.direction == "earth_to_space":
                    by_group[g.group_id] = earth_station_result(group_stations.get(g.group_id, []))
    return IssueGeography(by_notice, by_group)


def group_relevance(geo: IssueGeography, notice_id: str, group_id: str, direction: str) -> GeoResult:
    """The geography that matters for one group: the earth station for uplinks of space notices,
    otherwise the notice's own station."""
    return geo.by_group.get(group_id) or geo.by_notice.get(notice_id) or GeoResult("unknown", "none")


# ---------------------------------------------------------------------------------------------------------------
# Applying geography to the frequency screen (B2 -> B3)

def station_reach(direction: str, gres: GeoResult, notice_type: str | None,
                  stations: list) -> tuple[list[str], dict[str, dict], list[str]]:
    """Which matched special-interest stations the group can actually reach, from each station's own position.

    * GSO space station, downlink: the station sees the satellite above the horizon (elevation > 0 deg).
    * Non-GSO space station, downlink: the station's latitude is inside the orbit's coverage at 0 deg.
    * Earth station (an uplink, or a receiving earth-station notice): within NEAR_BORDER_KM of the station.
    * Downlink with unknown geography: kept, as for Finland as a whole (unknown is never treated as safe). An uplink
      from an earth station with no location (a typical station) is not promoted, as for Finland.
    Returns (kept station numbers, geometry per kept station, reasons for the dropped ones).
    """
    kept, detail, dropped = [], {}, []
    for s in stations:
        if gres.method == "gso_elevation" and direction == "space_to_earth":
            el, d = gso_look(s.lat, s.lon, gres.detail["satellite_longitude_deg"])
            if el > 0:
                kept.append(s.station_number)
                detail[s.station_number] = {"elevation_deg": round(el, 3), "slant_range_km": round(d, 1)}
            else:
                dropped.append(f"{s.station_number}: satellite {el:.1f} deg below its horizon")
        elif gres.method == "ngso_coverage" and direction == "space_to_earth":
            if s.lat <= gres.detail["lat_limit_0deg"]:
                kept.append(s.station_number)
                detail[s.station_number] = {"coverage_lat_limit_deg": gres.detail["lat_limit_0deg"]}
            else:
                dropped.append(f"{s.station_number}: at {s.lat:.2f} N, beyond the orbit's coverage")
        elif gres.method == "earth_station_distance":
            es = gres.detail["nearest"]
            d = _haversine_km(es["lat"], es["lon"], s.lat, s.lon)
            if d <= NEAR_BORDER_KM:
                kept.append(s.station_number)
                detail[s.station_number] = {"earth_station": es["name"], "distance_km": round(d, 1)}
            else:
                dropped.append(f"{s.station_number}: earth station {es['name']} {d:.0f} km away")
        elif gres.relevance == "unknown" and direction == "space_to_earth":
            kept.append(s.station_number)
            detail[s.station_number] = {"note": "geography unknown"}
        elif gres.relevance == "unknown":
            dropped.append(f"{s.station_number}: earth station location not filed ({gres.note})")
        else:
            dropped.append(f"{s.station_number}: {gres.relevance}")
    return kept, detail, dropped


def station_points(numbers: list[str], sat_lon_deg: float, stations: list) -> list[tuple[str, float, float]]:
    """pfd points for matched stations that see a GSO satellite: (name, lat, lon). Shared by assemble and
    evidence_check so the recomputed pfd uses exactly the same points."""
    wanted = set(numbers)
    return [(f"station {s.station_number}", s.lat, s.lon) for s in stations
            if s.station_number in wanted and gso_look(s.lat, s.lon, sat_lon_deg)[0] > 0]


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    a = math.sin((p2 - p1) / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(math.radians(lon2 - lon1) / 2) ** 2
    return 2 * R_EARTH_KM * math.asin(math.sqrt(a))


def apply(rows, geo: IssueGeography, notice_types: dict[str, str], stations: list | None = None) -> None:
    """Set geo fields on relevance rows and update `candidate` [HYPOTHESIS rules until Q1]:

    * downlink of a space station: kept if visible, low_elevation or unknown; dropped if not_visible.
    * downlink received by an earth-station notice: kept if the station is near or inside Finland.
    * uplink (any): promoted to candidate when the transmitting earth station is near or inside Finland and the
      group overlaps a Finnish terrestrial or passive row; otherwise informational.
    * groups where the Bureau names Finland stay candidates whatever the geography.
    * special-interest stations: a match stays only if the group reaches that station (station_reach); an uplink
      from an earth station within NEAR_BORDER_KM of a matched station is a candidate (path uplink_near_station).
    """
    from radar.pipeline.relevance import CANDIDATE_PATHS

    by_number: dict[str, list] = {}
    for s in stations or []:
        by_number.setdefault(s.station_number, []).append(s)
    for r in rows:
        g = group_relevance(geo, r.notice_id, r.group_id, r.direction)
        r.geo_relevance, r.geo_note = g.relevance, g.note
        if r.matched_station_numbers:
            matched = [s for num in r.matched_station_numbers for s in by_number.get(num, [])]
            kept, detail, dropped = station_reach(r.direction, g, notice_types.get(r.notice_id), matched)
            r.matched_station_numbers, r.station_reach = list(dict.fromkeys(kept)), detail
            if not kept:
                r.paths.pop("special_interest", None)
                was = r.candidate
                r.candidate = any(p in r.paths for p in CANDIDATE_PATHS)
                if was and not r.candidate:
                    r.drop_reason = f"special-interest station(s) out of reach ({dropped[0]}{'; ...' if len(dropped) > 1 else ''})"
            elif r.direction == "earth_to_space":
                r.paths.pop("special_interest", None)
                r.paths.setdefault("uplink_near_station", [])
        if r.finland_named_provisions:
            r.candidate, r.drop_reason = True, None
            continue
        earth_station_notice = notice_types.get(r.notice_id) == "S"
        if r.direction == "space_to_earth":
            if not r.candidate:
                continue
            if earth_station_notice:
                ok = g.relevance == "near_border"
            else:
                # a protected station that sees the satellite keeps the group, even if no reference point does
                ok = g.relevance in ("visible", "low_elevation", "unknown") or bool(r.matched_station_numbers)
            if not ok:
                r.candidate, r.drop_reason = False, f"geography: {g.relevance} ({g.note})"
        elif r.direction == "earth_to_space":
            hits = any(p in r.paths for p in ("uplink_terrestrial", "uplink_passive", "uplink_uncovered"))
            if g.relevance == "near_border" and hits:
                r.candidate, r.drop_reason = True, None
                r.paths.setdefault("uplink_near_finland", [])
            elif r.drop_reason and r.drop_reason.startswith("Earth-to-space"):
                r.drop_reason = f"Earth-to-space, earth station {g.relevance} ({g.note})"
