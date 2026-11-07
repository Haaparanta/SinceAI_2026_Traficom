"""Step C3 of pm_pack/08: terrestrial screening of one issue, from notice to ranked Finding.

For every located land-mobile notice of another administration within MAX_DISTANCE_KM of Finland:
  1. nearest point of the Finland polygon and the distance (scoring.geometry.Region, Natural Earth 1:50m)
  2. the path from the station to that point split into land and sea zones (1 km samples against the country
     polygons; sea = outside every loaded country, treated as 'Cold' sea for P.1546: Baltic, Gulf of Finland)
  3. field strength at the border with ITU-R P.1546-6 (radar.calc.p1546) for the notified e.r.p., 10 % time,
     50 % locations, 10 m receiving height. h1, the transmitting antenna's effective height, is the notice's own
     filed value in the direction of the receiver when it files one (fxm_ant_hgt, every 10 deg, interpolated to the
     bearing), else its filed maximum effective height, else the antenna height above ground (no terrain profile)
  4. the ECC/ERC T/R 25-08 Annex 1 trigger for the band plus 10 log10(channel / 25 kHz); margin = trigger - E

Special-interest stations (Traficom XLS): for a computed notice, every station whose protected channel (RX
frequency +- half the bandwidth) overlaps the notice's channel and lies within MAX_DISTANCE_KM gets its own P.1546
field strength, over the path from the transmitter to the station and at the station's antenna height above ground,
against the same trigger. The concern is the worse of the border check and the worst station; the trace shows the
calculation that decided it.

Concern [HYPOTHESIS rules until Q11, Q12]:
  new or modified notice, E above the trigger -> high; within 6 dB below -> medium; further below -> low
  recorded (unchanged) notice, E above the trigger -> medium; otherwise low
  no T/R 25-08 trigger for the band (e.g. 790-862 MHz LTE) -> review within 100 km, low beyond; field strength reported
  withdrawn, Finnish, not land mobile, beyond MAX_DISTANCE_KM -> none, with the reason
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from functools import lru_cache

from radar import schema_map
from radar.adapters import terrestrial_ific as T
from radar.config import ROOT
from radar.evidence import locator, row_excerpt
from radar.models import AnalysisResult, CalcInput, CalcTrace, Evidence, Finding, TerrestrialNotice
from scoring.geometry import Region

MAX_DISTANCE_KM = 1000.0         # P.1546 validity limit
MAX_STATION_EVIDENCE = 5          # stations cited per finding; all of them are in the results file
P1546_MIN_H2_SEA_M = 3.0         # P.1546-6: receiving antenna below 3 m adjacent to sea is outside the method
STATION_DEFAULT_H2_M = 10.0     # receiving height when the sheet gives none (the T/R 25-08 reference height)
NO_CRITERION_REVIEW_KM = 100.0   # [HYPOTHESIS] without a criterion, only stations this close go to review (Q12)
WITHIN_DB_MEDIUM = 6.0           # [HYPOTHESIS] within 6 dB of the trigger is still worth a look (Q12)
DEFAULT_HEIGHT = {"ML": 1.5, "MO": 1.5}   # [HYPOTHESIS] vehicle or handheld height when none is filed
DEFAULT_HEIGHT_OTHER = 10.0
P1546_MIN_H1_SEA_M = 1.0         # P.1546-6 Annex 5 section 4.2: for a sea path h1 should not be less than 1 m
THRESHOLDS_FILE = ROOT / "data" / "reference" / "tr2508_thresholds.csv"
CONCERN_ORDER = {"high": 4, "medium": 3, "review": 2, "low": 1, "none": 0}


@dataclass(frozen=True)
class Threshold:
    id: str
    f_min_mhz: float
    f_max_mhz: float
    threshold_dbuv_m: float
    ref_bw_khz: float
    source: str
    review: str

    def excerpt(self) -> str:
        return f"{self.f_min_mhz:g}-{self.f_max_mhz:g} MHz: {self.threshold_dbuv_m:g} dB(uV/m) per {self.ref_bw_khz:g} kHz at 10 m, 10 % time"


@lru_cache(maxsize=1)
def thresholds() -> tuple[Threshold, ...]:
    with THRESHOLDS_FILE.open(encoding="utf-8") as fh:
        return tuple(Threshold(r["id"], float(r["f_min_mhz"]), float(r["f_max_mhz"]), float(r["threshold_dbuv_m"]),
                               float(r["ref_bw_khz"]), r["source"], r["review"]) for r in csv.DictReader(fh))


def threshold_for(freq_hz: int | None, bandwidth_hz: int | None) -> tuple[Threshold | None, float]:
    """(row, bandwidth correction dB). Correction = 10 log10(channel / 25 kHz) for channels wider than 25 kHz."""
    if freq_hz is None:
        return None, 0.0
    f = freq_hz / 1e6
    # T/R 25-08 A1.2.3 ranges share their edges ("between 47 and 108 MHz", "between 108 and 380 MHz"): a frequency on
    # an edge belongs to both, so the stricter (lower) trigger applies. Signed off 7 Nov 2026, data/reference/review.
    matches = [t for t in thresholds() if t.f_min_mhz <= f <= t.f_max_mhz]
    row = min(matches, key=lambda t: t.threshold_dbuv_m) if matches else None
    if row is None:
        return None, 0.0
    bc = 10 * math.log10(bandwidth_hz / (row.ref_bw_khz * 1000)) if bandwidth_hz and bandwidth_hz > row.ref_bw_khz * 1000 else 0.0
    return row, round(bc, 2)


# ---- geography -----------------------------------------------------------------------------------------------

@lru_cache(maxsize=8192)
def border(lat: float, lon: float) -> tuple[float, float, float]:
    """(distance_km, nearest Finnish lat, lon)."""
    return Region.load().distance_to_country_km("FIN", lat, lon)


@lru_cache(maxsize=8192)
def path_segments(lat1: float, lon1: float, lat2: float, lon2: float, d_km: float) -> tuple[tuple[float, str], ...]:
    """Split the straight path into consecutive land and sea zones from 1 km samples (at least 20 samples)."""
    region = Region.load()
    n = max(20, int(math.ceil(d_km)))
    kinds = []
    for i in range(n):
        t = (i + 0.5) / n
        lat, lon = lat1 + (lat2 - lat1) * t, lon1 + (lon2 - lon1) * t
        kinds.append("Land" if region.country_at(lat, lon) is not None else "Cold")
    segs: list[list] = []
    for k in kinds:
        if segs and segs[-1][1] == k:
            segs[-1][0] += 1
        else:
            segs.append([1, k])
    return tuple((round(d_km * c / n, 4), k) for c, k in segs)


# ---- transmitting antenna height h1 ----------------------------------------------------------------------------

@dataclass(frozen=True)
class H1:
    value_m: float
    source: str
    azimuths: tuple[float, ...] = ()      # fxm_ant_hgt rows used (for the evidence)
    bearing_deg: float | None = None


def interpolate_azimuth(heights: tuple[tuple[float, float], ...], bearing: float) -> tuple[float, tuple[float, ...]]:
    """Linear interpolation between the two filed azimuths around the bearing (circular)."""
    pts = sorted((az % 360.0, h) for az, h in heights)
    b = bearing % 360.0
    for az, h in pts:
        if abs(az - b) < 1e-9:
            return h, (az,)
    after = next(((az, h) for az, h in pts if az > b), (pts[0][0] + 360.0, pts[0][1]))
    before = next(((az, h) for az, h in reversed(pts) if az < b), (pts[-1][0] - 360.0, pts[-1][1]))
    t = (b - before[0]) / (after[0] - before[0])
    return before[1] + t * (after[1] - before[1]), (before[0] % 360.0, after[0] % 360.0)


def h1_for(n: TerrestrialNotice, extra: T.NoticeExtra, lat2: float, lon2: float, sea_in_path: bool) -> H1:
    """h1 towards (lat2, lon2): the filed effective height first, then the filed maximum, then above ground, then a default."""
    from scoring.geometry import initial_bearing_deg

    if extra.eff_heights:
        b = round(initial_bearing_deg(n.lat, n.lon, lat2, lon2), 1)
        h, used = interpolate_azimuth(extra.eff_heights, b)
        h = round(h, 1)
        between = f"filed at {used[0]:g} deg" if len(used) == 1 else f"interpolated between {used[0]:g} and {used[1]:g} deg"
        out = H1(h, f"filed effective height towards the receiver, bearing {b:g} deg ({between}, fxm_ant_hgt.eff_hgt)", used, b)
    elif extra.eff_height_max_m is not None:
        out = H1(extra.eff_height_max_m, "filed maximum effective height (fxm_ant.eff_hgtmax); no value per azimuth, "
                                         "so the highest one is used (conservative)")
    elif n.antenna_height_m:
        out = H1(n.antenna_height_m, "antenna height above ground (fxm_ant.hgt_agl): no effective height filed, no terrain profile")
    else:
        h = DEFAULT_HEIGHT.get(n.station_class or "", DEFAULT_HEIGHT_OTHER)
        out = H1(h, f"not filed; {h:g} m assumed for class {n.station_class} [hypothesis]")
    if sea_in_path and out.value_m < P1546_MIN_H1_SEA_M:
        out = H1(P1546_MIN_H1_SEA_M, f"{out.source}; {out.value_m:g} m raised to {P1546_MIN_H1_SEA_M:g} m: P.1546-6 Annex 5 "
                                     f"section 4.2, h1 should not be less than 1 m on a sea path", out.azimuths, out.bearing_deg)
    return out


def _has_sea(segs) -> bool:
    return any(k != "Land" for _, k in segs)


# ---- one notice ------------------------------------------------------------------------------------------------

@dataclass
class TerrestrialCalc:
    status: str                          # computed | not_applicable | no_input
    reason: str
    distance_km: float | None = None
    nearest: tuple[float, float] | None = None
    segments: tuple = ()
    heff_m: float | None = None
    heff_source: str = ""
    e_dbuv_m: float | None = None
    free_space_dbuv_m: float | None = None
    threshold: Threshold | None = None
    bc_db: float = 0.0
    trigger_dbuv_m: float | None = None
    margin_db: float | None = None
    notes: list[str] = field(default_factory=list)
    stations: list[dict] = field(default_factory=list)     # co-channel special-interest stations, worst first
    heff_azimuths: tuple[float, ...] = ()   # fxm_ant_hgt azimuths behind h1 (empty when not per azimuth)


def evaluate(n: TerrestrialNotice, extra: T.NoticeExtra) -> TerrestrialCalc:
    if n.administration == "FIN":
        return TerrestrialCalc("not_applicable", "Finnish notice (own administration)")
    if n.change == "withdrawn":
        return TerrestrialCalc("not_applicable", "withdrawn by the notifying administration (SUPPRESS)")
    if not extra.land_mobile:
        return TerrestrialCalc("not_applicable", f"station class {n.station_class}: not land mobile (outside the T/R 25-08 side quest)")
    if n.lat is None:
        if extra.geo_type == "ZONE" and extra.zone_id:
            region = Region.load()
            if extra.zone_id not in region.polygons:
                return TerrestrialCalc("not_applicable", f"area notice for the whole territory of {extra.zone_id}, "
                                                         "not Finland or a neighbour")
            return TerrestrialCalc("no_input", f"area notice for the territory of {extra.zone_id}: no point to compute from")
        return TerrestrialCalc("no_input", f"no point location (site type {extra.geo_type})")
    d, nlat, nlon = border(round(n.lat, 5), round(n.lon, 5))
    if d > MAX_DISTANCE_KM:
        return TerrestrialCalc("not_applicable", f"{d:.0f} km from Finland, beyond the {MAX_DISTANCE_KM:.0f} km limit of P.1546", distance_km=round(d, 1))
    if n.freq_hz is None or not 30e6 <= n.freq_hz <= 4000e6:
        return TerrestrialCalc("no_input", "frequency outside 30-4000 MHz (P.1546 range)", distance_km=round(d, 1))
    if n.erp_dbw is None:
        return TerrestrialCalc("no_input", "e.r.p. not filed", distance_km=round(d, 1))
    from radar.calc.p1546 import field_strength

    segs = path_segments(round(n.lat, 5), round(n.lon, 5), round(nlat, 5), round(nlon, 5), round(max(d, 0.04), 3))
    h1 = h1_for(n, extra, nlat, nlon, _has_sea(segs))
    fs = field_strength(n.freq_hz / 1e6, list(segs), h1.value_m, n.erp_dbw, ha_m=n.antenna_height_m)
    row, bc = threshold_for(n.freq_hz, n.bandwidth_hz)
    c = TerrestrialCalc("computed", "", round(d, 1), (nlat, nlon), segs, h1.value_m, h1.source, fs.e_dbuv_m, fs.free_space_dbuv_m,
                        row, bc, notes=fs.notes, heff_azimuths=h1.azimuths)
    if row is not None:
        c.trigger_dbuv_m = round(row.threshold_dbuv_m + bc, 2)
        c.margin_db = round(c.trigger_dbuv_m - fs.e_dbuv_m, 2)
    if extra.directivity == "D" and n.azimuth_deg is not None:
        c.notes.append(f"directional antenna, maximum radiation at {n.azimuth_deg:g} deg; no pattern applied (conservative)")
    c.stations = station_checks(n, extra, c.trigger_dbuv_m)
    return c


def co_channel_stations(n: TerrestrialNotice) -> list:
    from radar.adapters import special_interest as SI
    half = (n.bandwidth_hz or 0) // 2
    lo, hi = n.freq_hz - half, n.freq_hz + half
    out = []
    for s in SI.stations():
        s_lo, s_hi = s.centre_hz - s.bandwidth_hz // 2, s.centre_hz + s.bandwidth_hz // 2
        if (min(hi, s_hi) - max(lo, s_lo) > 0) or (lo == hi and s_lo <= lo < s_hi):
            out.append(s)
    return out


def station_checks(n: TerrestrialNotice, extra: T.NoticeExtra, trigger: float | None) -> list[dict]:
    """P.1546 field strength at every co-channel special-interest station within MAX_DISTANCE_KM, worst first."""
    from radar.calc.p1546 import field_strength
    from scoring.geometry import haversine_km

    out = []
    for s in co_channel_stations(n):
        d = haversine_km(n.lat, n.lon, s.lat, s.lon)
        if d > MAX_DISTANCE_KM:
            continue
        h2 = max(s.antenna_height_m or STATION_DEFAULT_H2_M, 1.0)
        h2_source = "antenna height above ground (sheet)" if s.antenna_height_m else f"not filed; {STATION_DEFAULT_H2_M:g} m assumed"
        segs = path_segments(round(n.lat, 5), round(n.lon, 5), round(s.lat, 5), round(s.lon, 5), round(max(d, 0.04), 3))
        if segs[-1][1] != "Land" and h2 < P1546_MIN_H2_SEA_M:
            h2_source = f"{h2:g} m raised to {P1546_MIN_H2_SEA_M:g} m: P.1546 is not valid below that next to sea"
            h2 = P1546_MIN_H2_SEA_M
        h1 = h1_for(n, extra, s.lat, s.lon, _has_sea(segs))
        fs = field_strength(n.freq_hz / 1e6, list(segs), h1.value_m, n.erp_dbw, rx_height_m=h2, ha_m=n.antenna_height_m)
        out.append({"number": s.station_number, "row": s.source_row, "class": s.licence_class, "lat": s.lat, "lon": s.lon,
                    "centre_hz": s.centre_hz, "distance_km": round(d, 1), "h2_m": h2,
                    "h1_m": h1.value_m, "h1_source": h1.source, "h1_azimuths": h1.azimuths,
                    "h2_source": h2_source,
                    "segments": segs, "e_dbuv_m": fs.e_dbuv_m,
                    "margin_db": None if trigger is None else round(trigger - fs.e_dbuv_m, 2)})
    return sorted(out, key=lambda r: (-r["e_dbuv_m"], r["distance_km"], r["number"]))


def station_excerpt(s: dict) -> str:
    return f"E {s['e_dbuv_m']:.2f} dB(uV/m) at station {s['number']}, {s['distance_km']:g} km, h1 {s['h1_m']:g} m, h2 {s['h2_m']:g} m"


def _level(n: TerrestrialNotice, margin: float | None, distance_km: float) -> str:
    if margin is None:
        return "review" if distance_km <= NO_CRITERION_REVIEW_KM else "low"
    over = margin < 0
    if n.change in ("new", "modified"):
        return "high" if over else ("medium" if margin < WITHIN_DB_MEDIUM else "low")
    return "medium" if over else "low"


def concern(n: TerrestrialNotice, c: TerrestrialCalc) -> tuple[str, str]:
    """The worse of the border check and the worst co-channel special-interest station (decides the trace too)."""
    level, text = border_concern(n, c)
    if c.status != "computed" or not c.stations:
        return level, text
    w = c.stations[0]
    s_level = _level(n, w["margin_db"], w["distance_km"])
    k = len(c.stations)
    who = f"special-interest station {w['number']}" if k == 1 else f"{k} co-channel special-interest stations, worst {w['number']}"
    at = (f"{who}: {w['distance_km']:g} km, field strength {w['e_dbuv_m']:g} dB(uV/m) at {w['h2_m']:g} m"
          + ("" if w["margin_db"] is None else
             f", {'exceeds the trigger by ' + format(-w['margin_db'], 'g') + ' dB' if w['margin_db'] < 0 else format(w['margin_db'], 'g') + ' dB below the trigger'}"))
    if CONCERN_ORDER[s_level] > CONCERN_ORDER[level]:
        return s_level, f"{text}; {at} (decides)"
    return level, f"{text}; {at}"


def station_decides(n: TerrestrialNotice, c: TerrestrialCalc) -> bool:
    if c.status != "computed" or not c.stations:
        return False
    w = c.stations[0]
    return CONCERN_ORDER[_level(n, w["margin_db"], w["distance_km"])] > CONCERN_ORDER[border_concern(n, c)[0]]


def border_concern(n: TerrestrialNotice, c: TerrestrialCalc) -> tuple[str, str]:
    if c.status == "not_applicable":
        return "none", c.reason
    if c.status == "no_input":
        return "review", f"cannot compute: {c.reason}"
    where = f"{c.distance_km:g} km from Finland"
    if c.threshold is None:
        level = "review" if c.distance_km <= NO_CRITERION_REVIEW_KM else "low"
        return level, (f"{where}; field strength at the border {c.e_dbuv_m:g} dB(uV/m) (P.1546); no T/R 25-08 trigger "
                       f"for {n.freq_hz / 1e6:g} MHz, criterion needed (Q12)")
    over = c.margin_db < 0
    text = (f"{where}; field strength at the border {c.e_dbuv_m:g} dB(uV/m) (P.1546, 10 % time) against the T/R 25-08 "
            f"trigger {c.trigger_dbuv_m:g} dB(uV/m): " + (f"exceeds by {-c.margin_db:g} dB" if over else f"{c.margin_db:g} dB below"))
    if n.change in ("new", "modified"):
        if over:
            return "high", f"{n.change} land-mobile notice; {text}"
        return ("medium" if c.margin_db < WITHIN_DB_MEDIUM else "low"), f"{n.change} land-mobile notice; {text}"
    return ("medium" if over else "low"), f"recorded land-mobile notice; {text}"


# ---- the issue ----------------------------------------------------------------------------------------------------

@dataclass
class TerrestrialRun:
    result: AnalysisResult
    calcs: dict[str, TerrestrialCalc]
    ingest: T.TerrestrialIngest


def run(issue: int) -> TerrestrialRun:
    import duckdb

    M = schema_map.load()
    C = lambda e, c: M.col("terrestrial", e, c)  # noqa: E731
    Tb = lambda e: M.table("terrestrial", e)  # noqa: E731
    ing = T.load(issue)
    con = duckdb.connect(str(T.db_path(issue)), read_only=True)
    source = f"brific{issue}.mdb (data/derived/terrestrial_{issue}.duckdb)"
    geo_keys = dict(con.execute(f'SELECT CAST("{C("notice", "notice_id")}" AS VARCHAR), "{C("notice", "geo_key")}" '
                                f'FROM "{Tb("notice")}"').fetchall())
    calcs, findings = {}, []
    for n in ing.notices:
        e = ing.extra[n.notice_id]
        c = evaluate(n, e)
        calcs[n.notice_id] = c
        level, reason = concern(n, c)
        ev: list[Evidence] = []

        def add(kind, src, loc, excerpt):
            ev.append(Evidence(id=f"E-{len(ev) + 1:03d}", kind=kind, source=src, locator=loc, excerpt=excerpt))
            return ev[-1].id

        k = {C("notice", "notice_id"): n.notice_id}
        n_ev = add("itu_row", source, locator(Tb("notice"), **k), row_excerpt(con, Tb("notice"), k, [
            C("notice", x) for x in ("administration", "intent", "notice_type", "station_class", "freq_mhz", "bandwidth_khz")]))
        trace = CalcTrace(method="none", inputs=[], formula="", result_value=None, result_unit="", limit_value=None,
                          limit_evidence_id=None, margin_db=None, notes=[c.reason] if c.reason else [])
        geo = "unknown"
        if c.status == "computed":
            gk = {C("site", "geo_key"): geo_keys[n.notice_id]}
            s_ev = add("itu_row", source, locator(Tb("site"), **gk), row_excerpt(con, Tb("site"), gk, [
                C("site", x) for x in ("country", "site_name", "lat_deg", "lon_deg")]))
            ak = {C("antenna", "notice_id"): n.notice_id, C("antenna", "antenna_key"): e.antenna_key}
            a_ev = add("itu_row", source, locator(Tb("antenna"), **ak), row_excerpt(con, Tb("antenna"), ak, [
                C("antenna", x) for x in ("power_dbw", "power_quantity", "height_agl_m", "max_effective_height_m", "directivity")]))

            def h_ev(azimuths) -> str:
                """Evidence for h1: the fxm_ant_hgt rows used, or the antenna row."""
                ids = []
                for az in azimuths:
                    hk = {C("antenna_height", "notice_id"): n.notice_id, C("antenna_height", "antenna_key"): e.antenna_key,
                          C("antenna_height", "azimuth_deg"): f"{az:.1f}"}
                    ids.append(add("itu_row", source, locator(Tb("antenna_height"), **hk), row_excerpt(
                        con, Tb("antenna_height"), hk, [C("antenna_height", "azimuth_deg"), C("antenna_height", "effective_height_m")])))
                return ids[0] if ids else a_ev
            h1_ev = h_ev(c.heff_azimuths)
            b_ev = add("calculation", "radar.pipeline.terrestrial (Natural Earth 1:50m polygons)",
                       f"border(notice_id={n.notice_id})", border_excerpt(c))
            p_ev = add("calculation", "radar.calc.p1546 (ITU-R P.1546-6 reference implementation)",
                       f"p1546(notice_id={n.notice_id})", f"E {c.e_dbuv_m:.2f} dB(uV/m); free space {c.free_space_dbuv_m:.2f}")
            t_ev = None
            if c.threshold is not None:
                t_ev = add("regulation", f"{c.threshold.source} (data/reference/tr2508_thresholds.csv)",
                           f"tr2508_thresholds.csv id={c.threshold.id}", c.threshold.excerpt())
            trace = CalcTrace(
                method="p1546_field_strength",
                inputs=[CalcInput(name="f frequency", value=n.freq_hz / 1e6, unit="MHz", evidence_id=n_ev),
                        CalcInput(name="e.r.p.", value=n.erp_dbw, unit="dBW", evidence_id=a_ev),
                        CalcInput(name="h1 transmitting antenna effective height", value=c.heff_m, unit="m", evidence_id=h1_ev),
                        CalcInput(name="ha antenna height above ground (sets h1 on land paths under 15 km)",
                                  value=n.antenna_height_m if n.antenna_height_m is not None else "not filed", unit="m",
                                  evidence_id=a_ev),
                        CalcInput(name="d distance to the Finnish border", value=c.distance_km, unit="km", evidence_id=b_ev),
                        CalcInput(name="path zones", value="; ".join(f"{d:g} km {k}" for d, k in c.segments), unit="", evidence_id=b_ev),
                        CalcInput(name="time percentage", value=10.0, unit="%", evidence_id=p_ev),
                        CalcInput(name="h2 receiving height", value=10.0, unit="m", evidence_id=p_ev),
                        CalcInput(name="bandwidth correction 10 log10(B/25 kHz)", value=c.bc_db, unit="dB",
                                  evidence_id=t_ev or n_ev)],
                formula="E = P.1546-6(f, t = 10 %, h1, h2 = 10 m, path zones) scaled to the e.r.p.; margin = (trigger + BC) - E",
                result_value=c.e_dbuv_m, result_unit="dB(uV/m)", limit_value=c.trigger_dbuv_m, limit_evidence_id=t_ev,
                margin_db=c.margin_db, label="indicative",
                notes=[f"h1: {c.heff_source}", "no antenna pattern applied (conservative)"] + c.notes)
            if c.stations:
                from radar.adapters import special_interest as SI
                rows = SI.by_row()
                st_ev = {}
                for st in c.stations[:MAX_STATION_EVIDENCE]:
                    e_st = SI.evidence(rows[st["row"]], f"E-{len(ev) + 1:03d}")
                    ev.append(e_st)
                    st_ev[st["number"]] = e_st.id
                w = c.stations[0]
                ws_ev = add("calculation", "radar.calc.p1546 (ITU-R P.1546-6 reference implementation)",
                            f"p1546_station(notice_id={n.notice_id};station={w['number']})", station_excerpt(w))
                if station_decides(n, c):
                    w_h1_ev = h_ev(w["h1_azimuths"]) if w["h1_azimuths"] != c.heff_azimuths else h1_ev
                    trace = CalcTrace(
                        method="p1546_field_strength",
                        inputs=[CalcInput(name="f frequency", value=n.freq_hz / 1e6, unit="MHz", evidence_id=n_ev),
                                CalcInput(name="e.r.p.", value=n.erp_dbw, unit="dBW", evidence_id=a_ev),
                                CalcInput(name="h1 transmitting antenna effective height", value=w["h1_m"], unit="m",
                                          evidence_id=w_h1_ev),
                                CalcInput(name=f"d distance to special-interest station {w['number']}", value=w["distance_km"], unit="km",
                                          evidence_id=st_ev[w["number"]]),
                                CalcInput(name="path zones", value="; ".join(f"{d:g} km {k}" for d, k in w["segments"]), unit="",
                                          evidence_id=ws_ev),
                                CalcInput(name="time percentage", value=10.0, unit="%", evidence_id=ws_ev),
                                CalcInput(name="h2 receiving height (station antenna)", value=w["h2_m"], unit="m",
                                          evidence_id=st_ev[w["number"]]),
                                CalcInput(name="bandwidth correction 10 log10(B/25 kHz)", value=c.bc_db, unit="dB",
                                          evidence_id=t_ev or n_ev)],
                        formula="E = P.1546-6(f, t = 10 %, h1, h2 = station antenna height, path zones to the station) scaled to the "
                                "e.r.p.; margin = (trigger + BC) - E",
                        result_value=w["e_dbuv_m"], result_unit="dB(uV/m)", limit_value=c.trigger_dbuv_m, limit_evidence_id=t_ev,
                        margin_db=w["margin_db"], label="indicative",
                        notes=[f"computed at special-interest station {w['number']} (decides the concern); at the border: "
                               f"E {c.e_dbuv_m:g} dB(uV/m), {c.distance_km:g} km",
                               f"h2: {w['h2_source']}", f"h1: {w['h1_source']}", "no antenna pattern applied (conservative)",
                               "the T/R 25-08 trigger is defined at the border line; applying it at a station inside Finland is "
                               "an indicative protection check [hypothesis]"] + c.notes)
                else:
                    trace.notes.append(f"{len(c.stations)} co-channel special-interest station(s); worst {station_excerpt(w)} "
                                       f"(evidence {ws_ev}); the border check decides")
            geo = "near_border" if c.distance_km <= 300 else "far"
            del s_ev
        elif c.distance_km is not None:
            geo = "near_border" if c.distance_km <= 300 else "far"
        findings.append(Finding(id="", kind="terrestrial", issue=issue, notice_id=n.notice_id, group_id=None,
                                matched_station_numbers=[st["number"] for st in c.stations],
                                geo_relevance=geo, calc=trace, concern=level, reason=reason, evidence=ev))
    con.close()
    order = sorted(findings, key=lambda f: (-CONCERN_ORDER[f.concern],
                                            calcs[f.notice_id].margin_db if calcs[f.notice_id].margin_db is not None else 999,
                                            calcs[f.notice_id].distance_km or 99999, f.notice_id))
    for i, f in enumerate(order, start=1):
        f.id = f"F-{issue}-{i:04d}"
    complete = sum(1 for f in order if all(e.excerpt for e in f.evidence))
    res = AnalysisResult(issue=issue, kind="terrestrial", screened=len(order),
                         flagged=sum(1 for f in order if f.concern != "none"),
                         provenance_coverage_pct=round(100 * complete / max(len(order), 1), 1), findings=order)
    return TerrestrialRun(res, calcs, ing)


def border_excerpt(c: TerrestrialCalc) -> str:
    return (f"{c.distance_km:g} km to {c.nearest[0]:.4f} N {c.nearest[1]:.4f} E; zones "
            + "; ".join(f"{d:g} km {k}" for d, k in c.segments))
