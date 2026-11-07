"""Broadcasting extension of the terrestrial screening: FM (GE84) and TV (GE06) notices of a Terrestrial BR IFIC
against Finland and the special-interest stations of the Traficom table.

Same engine as the land-mobile side quest (radar.pipeline.terrestrial): the notices become TerrestrialNotice objects,
h1 is the filed effective height towards the receiver, the path is split into land and sea, and the field strength
comes from the ITU-R P.1546-6 reference implementation. What differs for broadcasting:

* reception is protected at 10 m above ground (the planning height of GE84 and GE06), also around a protected
  broadcasting station, whose own antenna height says nothing about where its listeners are;
* interference is evaluated for 1 % of time (tropospheric propagation) [HYPOTHESIS until confirmed in the Final Acts];
* the trigger comes from data/reference/ge_triggers.csv (GE84 and GE06), with its page; when no trigger applies,
  the field strength is reported and the concern follows the no-criterion rule of the land-mobile step.

For every notice of another administration with a point location: the field strength at the nearest point of the
Finnish border and at every special-interest station on the same channel within MAX_DISTANCE_KM. The concern is the
worse of the two; the trace shows the calculation that decided it. Output: results/broadcasting_<issue>.csv|json
(ResultRow), kept apart from the graded land-mobile file.
"""
from __future__ import annotations

import csv
from dataclasses import dataclass, field
from functools import lru_cache

from radar import schema_map
from radar.adapters import special_interest as SI
from radar.adapters import terrestrial_ific as T
from radar.config import ROOT
from radar.evidence import locator, row_excerpt
from radar.models import AnalysisResult, CalcInput, CalcTrace, Evidence, Finding, TerrestrialNotice
from radar.pipeline import terrestrial as TR

TIME_PCT = 1.0                  # [HYPOTHESIS] interference to broadcasting: 1 % of time
RX_HEIGHT_M = 10.0              # GE84 / GE06 planning height of the receiving antenna
TRIGGERS_FILE = ROOT / "data" / "reference" / "ge_triggers.csv"
BROADCAST_CLASSES = ("BC", "BT")


@dataclass(frozen=True)
class Trigger:
    id: str
    f_min_mhz: float
    f_max_mhz: float
    system: str                  # fm | dvbt
    trigger_dbuv_m: float
    time_pct: float
    h_rx_m: float
    source: str
    page: str
    review: str
    notes: str

    def excerpt(self) -> str:
        return (f"{self.f_min_mhz:g}-{self.f_max_mhz:g} MHz {self.system}: {self.trigger_dbuv_m:g} dB(uV/m) at {self.h_rx_m:g} m, "
                f"{self.time_pct:g} % time; page {self.page}")


@lru_cache(maxsize=1)
def triggers() -> tuple[Trigger, ...]:
    if not TRIGGERS_FILE.exists():
        return ()
    with TRIGGERS_FILE.open(encoding="utf-8", newline="") as fh:
        return tuple(Trigger(r["id"], float(r["f_min_mhz"]), float(r["f_max_mhz"]), r["system"], float(r["trigger_dbuv_m"]),
                             float(r["time_pct"]), float(r["h_rx_m"]), r["source"], r["page"], r["review"], r.get("notes", ""))
                     for r in csv.DictReader(fh))


def system_of(n: TerrestrialNotice, digital: bool | None) -> str:
    """fm (GE84), dvbt or atv (GE06 Table A.1.1 rows), other (T-DAB, digital sound: no trigger loaded)."""
    if n.station_class == "BC":
        return "fm" if not digital else "other"
    if n.station_class == "BT":
        return "dvbt" if digital else "atv" if digital is False else "other"
    return "other"


def trigger_for(n: TerrestrialNotice, digital: bool | None) -> Trigger | None:
    f = (n.freq_hz or 0) / 1e6
    sysname = system_of(n, digital)
    matches = [t for t in triggers() if t.system == sysname and t.f_min_mhz <= f <= t.f_max_mhz]
    return min(matches, key=lambda t: t.trigger_dbuv_m) if matches else None


# ---- reading ------------------------------------------------------------------------------------------------------

@dataclass
class BroadcastIngest:
    issue: int
    notices: list[TerrestrialNotice]
    extra: dict[str, T.NoticeExtra]
    digital: dict[str, bool | None]
    stats: dict = field(default_factory=dict)


def load(issue: int, con=None) -> BroadcastIngest:
    import duckdb

    M = schema_map.load()
    q = lambda c: M.q("terrestrial", "broadcast", c)  # noqa: E731
    own = con is None
    con = con or duckdb.connect(str(T.db_path(issue)), read_only=True)
    cols = ("notice_id", "administration", "country", "intent", "station_class", "notice_type", "freq_mhz", "bandwidth_khz",
            "digital", "site_name", "lat_deg", "lon_deg", "height_agl_m", "max_effective_height_m", "erp_dbw", "directivity")
    rows = con.execute(f"SELECT {', '.join(q(c) for c in cols)} FROM {M.t('terrestrial', 'broadcast')} "
                       f"WHERE {q('station_class')} IN ('BC', 'BT') ORDER BY 1").fetchall()
    heights: dict[str, list[tuple[float, float]]] = {}
    for nid, az, h in con.execute(
            f"SELECT CAST({M.q('terrestrial', 'broadcast_antenna_height', 'notice_id')} AS VARCHAR), "
            f"{M.q('terrestrial', 'broadcast_antenna_height', 'azimuth_deg')}, "
            f"{M.q('terrestrial', 'broadcast_antenna_height', 'effective_height_m')} "
            f"FROM {M.t('terrestrial', 'broadcast_antenna_height')}").fetchall():
        if az is not None and h is not None:
            heights.setdefault(nid, []).append((float(az), float(h)))
    if own:
        con.close()
    notices, extra, digital = [], {}, {}
    for (nid, adm, ctry, intent, cls, ntype, f, bw, dig, site, lat, lon, hagl, heff, erp, adir) in rows:
        nid = str(nid)
        notices.append(TerrestrialNotice(
            issue=issue, notice_id=nid, administration=adm or "unknown", change=T.CHANGE.get(intent, "unchanged"),
            station_class=cls, site_name=site, lat=None if lat is None else float(lat), lon=None if lon is None else float(lon),
            freq_hz=None if f is None else round(float(f) * 1e6), bandwidth_hz=None if bw is None else round(float(bw) * 1e3),
            erp_dbw=None if erp is None else float(erp), antenna_height_m=None if hagl is None else float(hagl),
            source_ref=f"fmtv_terra.terrakey={nid}"))
        extra[nid] = T.NoticeExtra(intent=intent, notice_type=ntype, geo_type="POINT" if lat is not None else None, country=ctry,
                                   power_dbw_filed=None if erp is None else float(erp), power_quantity="E", directivity=adir,
                                   received=None, target=None, eff_height_max_m=None if heff is None else float(heff),
                                   eff_heights=tuple(sorted(heights.get(nid, []))))
        digital[nid] = None if dig is None else str(dig).upper() in ("TRUE", "1", "Y", "YES")
    return BroadcastIngest(issue, notices, extra, digital, {"notices": len(notices)})


# ---- one notice ---------------------------------------------------------------------------------------------------

@dataclass
class Point:
    kind: str                        # border | station
    name: str
    lat: float
    lon: float
    distance_km: float
    segments: tuple
    h1: TR.H1
    e_dbuv_m: float
    margin_db: float | None
    station: object | None = None


@dataclass
class BroadcastCalc:
    status: str                      # computed | not_applicable | no_input
    reason: str
    trigger: Trigger | None = None
    border: Point | None = None
    stations: list[Point] = field(default_factory=list)
    notes: list[str] = field(default_factory=list)


def _point(n: TerrestrialNotice, e: T.NoticeExtra, kind: str, name: str, lat: float, lon: float, d: float,
           trigger: Trigger | None, station=None) -> Point:
    from radar.calc.p1546 import field_strength

    segs = TR.path_segments(round(n.lat, 5), round(n.lon, 5), round(lat, 5), round(lon, 5), round(max(d, 0.04), 3))
    h1 = TR.h1_for(n, e, lat, lon, TR._has_sea(segs))
    fs = field_strength(n.freq_hz / 1e6, list(segs), h1.value_m, n.erp_dbw, time_pct=TIME_PCT, rx_height_m=RX_HEIGHT_M,
                        ha_m=n.antenna_height_m)
    return Point(kind, name, lat, lon, round(d, 1), segs, h1, fs.e_dbuv_m,
                 None if trigger is None else round(trigger.trigger_dbuv_m - fs.e_dbuv_m, 2), station)


def evaluate(n: TerrestrialNotice, e: T.NoticeExtra, digital: bool | None) -> BroadcastCalc:
    from scoring.geometry import haversine_km

    if n.administration == "FIN":
        return BroadcastCalc("not_applicable", "Finnish notice (own administration)")
    if n.change == "withdrawn":
        return BroadcastCalc("not_applicable", "withdrawn by the notifying administration (SUPPRESS)")
    if n.lat is None or n.lon is None:
        return BroadcastCalc("no_input", "no point location (allotment or area notice)")
    d, blat, blon = TR.border(round(n.lat, 5), round(n.lon, 5))
    if d > TR.MAX_DISTANCE_KM:
        return BroadcastCalc("not_applicable", f"{d:.0f} km from Finland, beyond the {TR.MAX_DISTANCE_KM:.0f} km limit of P.1546")
    if n.freq_hz is None or not 30e6 <= n.freq_hz <= 4000e6:
        return BroadcastCalc("no_input", "frequency outside 30-4000 MHz (P.1546 range)")
    if n.erp_dbw is None:
        return BroadcastCalc("no_input", "e.r.p. not filed")
    trig = trigger_for(n, digital)
    c = BroadcastCalc("computed", "", trig)
    c.border = _point(n, e, "border", "nearest Finnish border point", blat, blon, d, trig)
    for s in TR.co_channel_stations(n):
        ds = haversine_km(n.lat, n.lon, s.lat, s.lon)
        if ds <= TR.MAX_DISTANCE_KM:
            c.stations.append(_point(n, e, "station", s.station_number, s.lat, s.lon, ds, trig, s))
    c.stations.sort(key=lambda p: (-p.e_dbuv_m, p.distance_km, p.name))
    if trig is None:
        c.notes.append(f"no GE84/GE06 trigger in data/reference/ge_triggers.csv for {system_of(n, digital)} at "
                       f"{n.freq_hz / 1e6:g} MHz: field strength reported, criterion needed")
    return c


def deciding(n: TerrestrialNotice, c: BroadcastCalc) -> Point | None:
    pts = ([c.border] if c.border else []) + c.stations
    if not pts:
        return None
    return max(pts, key=lambda p: (TR.CONCERN_ORDER[TR._level(n, p.margin_db, p.distance_km)], p.e_dbuv_m))


def concern(n: TerrestrialNotice, c: BroadcastCalc) -> tuple[str, str]:
    if c.status == "not_applicable":
        return "none", c.reason
    if c.status == "no_input":
        return "review" if n.change in ("new", "modified") else "none", f"cannot compute: {c.reason}"
    w = deciding(n, c)
    level = TR._level(n, w.margin_db, w.distance_km)
    where = "at the nearest Finnish border point" if w.kind == "border" else f"at special-interest station {w.name}"
    crit = ("no GE84/GE06 trigger, criterion needed" if w.margin_db is None else
            f"exceeds the {c.trigger.id} trigger {c.trigger.trigger_dbuv_m:g} dB(uV/m) by {-w.margin_db:g} dB" if w.margin_db < 0 else
            f"{w.margin_db:g} dB below the {c.trigger.id} trigger {c.trigger.trigger_dbuv_m:g} dB(uV/m)")
    st = f"; {len(c.stations)} co-channel special-interest station(s) within {TR.MAX_DISTANCE_KM:.0f} km" if c.stations else \
        "; no special-interest station on this channel within reach"
    return level, (f"{n.change} {'FM' if n.station_class == 'BC' else 'TV'} broadcasting notice, {c.border.distance_km:g} km from "
                   f"Finland; field strength {w.e_dbuv_m:g} dB(uV/m) {where} ({w.distance_km:g} km, P.1546, {TIME_PCT:g} % time, "
                   f"{RX_HEIGHT_M:g} m): {crit}{st}")


def point_excerpt(p: Point) -> str:
    return f"E {p.e_dbuv_m:.2f} dB(uV/m) at {p.name}, {p.distance_km:g} km, h1 {p.h1.value_m:g} m, h2 {RX_HEIGHT_M:g} m, t {TIME_PCT:g} %"


# ---- the issue ----------------------------------------------------------------------------------------------------

@dataclass
class BroadcastRun:
    result: AnalysisResult
    calcs: dict[str, BroadcastCalc]
    ingest: BroadcastIngest


def run(issue: int) -> BroadcastRun:
    import duckdb

    M = schema_map.load()
    con = duckdb.connect(str(T.db_path(issue)), read_only=True)
    ing = load(issue, con)
    source = f"brific{issue}.mdb (data/derived/terrestrial_{issue}.duckdb)"
    table = M.table("terrestrial", "broadcast")
    key = M.col("terrestrial", "broadcast", "notice_id")
    show = [M.col("terrestrial", "broadcast", c) for c in ("administration", "intent", "station_class", "freq_mhz", "bandwidth_khz",
                                                           "erp_dbw", "height_agl_m", "max_effective_height_m", "lat_deg", "lon_deg")]
    calcs, findings = {}, []
    rows = SI.by_row() if SI.path().exists() else {}
    for n in ing.notices:
        e = ing.extra[n.notice_id]
        c = evaluate(n, e, ing.digital[n.notice_id])
        calcs[n.notice_id] = c
        level, reason = concern(n, c)
        ev: list[Evidence] = []

        def add(kind, src, loc, excerpt):
            ev.append(Evidence(id=f"E-{len(ev) + 1:03d}", kind=kind, source=src, locator=loc, excerpt=excerpt))
            return ev[-1].id

        n_ev = add("itu_row", source, locator(table, **{key: n.notice_id}), row_excerpt(con, table, {key: n.notice_id}, show))
        trace = CalcTrace(method="none", inputs=[], formula="", result_value=None, result_unit="", limit_value=None,
                          limit_evidence_id=None, margin_db=None, notes=[c.reason] if c.reason else [])
        geo = "unknown"
        if c.status == "computed":
            t_ev = None if c.trigger is None else add("regulation", f"{c.trigger.source} (data/reference/ge_triggers.csv)",
                                                      f"ge_triggers.csv id={c.trigger.id}", c.trigger.excerpt())
            st_ev = {}
            for p in c.stations[:TR.MAX_STATION_EVIDENCE]:
                if p.station is not None and p.station.source_row in rows:
                    e_st = SI.evidence(rows[p.station.source_row], f"E-{len(ev) + 1:03d}")
                    ev.append(e_st)
                    st_ev[p.name] = e_st.id
            b_ev = add("calculation", "radar.pipeline.broadcasting (ITU-R P.1546-6 reference implementation)",
                       f"broadcast_border(notice_id={n.notice_id})", point_excerpt(c.border))
            for p in c.stations[:1]:
                add("calculation", "radar.pipeline.broadcasting (ITU-R P.1546-6 reference implementation)",
                    f"broadcast_station(notice_id={n.notice_id};station={p.name})", point_excerpt(p))
            w = deciding(n, c)
            w_ev = b_ev if w.kind == "border" else st_ev.get(w.name, b_ev)
            trace = CalcTrace(
                method="p1546_field_strength",
                inputs=[CalcInput(name="f frequency", value=n.freq_hz / 1e6, unit="MHz", evidence_id=n_ev),
                        CalcInput(name="e.r.p.", value=n.erp_dbw, unit="dBW", evidence_id=n_ev),
                        CalcInput(name="h1 transmitting effective height", value=w.h1.value_m, unit="m", evidence_id=n_ev),
                        CalcInput(name=f"d distance to {w.name}", value=w.distance_km, unit="km", evidence_id=w_ev),
                        CalcInput(name="path zones", value="; ".join(f"{d:g} km {k}" for d, k in w.segments), unit="", evidence_id=b_ev),
                        CalcInput(name="time percentage", value=TIME_PCT, unit="%", evidence_id=b_ev),
                        CalcInput(name="h2 receiving height", value=RX_HEIGHT_M, unit="m", evidence_id=t_ev or b_ev)],
                formula="E = P.1546-6(f, t = 1 %, h1, h2 = 10 m, path zones) scaled to the e.r.p.; margin = trigger - E",
                result_value=w.e_dbuv_m, result_unit="dB(uV/m)", limit_value=None if c.trigger is None else c.trigger.trigger_dbuv_m,
                limit_evidence_id=t_ev, margin_db=w.margin_db, label="indicative",
                notes=[f"computed {'at the nearest Finnish border point' if w.kind == 'border' else 'at special-interest station ' + w.name}"
                       " (decides the concern)", f"h1: {w.h1.source}", "no antenna pattern applied (conservative)",
                       f"{TIME_PCT:g} % time for interference to broadcasting [hypothesis]"] + c.notes)
            geo = "near_border" if c.border.distance_km <= 300 else "far"
        findings.append(Finding(id="", kind="terrestrial", issue=issue, notice_id=n.notice_id,
                                matched_station_numbers=[p.name for p in c.stations], geo_relevance=geo, calc=trace,
                                concern=level, reason=reason, evidence=ev))
    con.close()
    order = sorted(findings, key=lambda f: (-TR.CONCERN_ORDER[f.concern], f.notice_id))
    for i, f in enumerate(order, start=1):
        f.id = f"B-{issue}-{i:04d}"
    res = AnalysisResult(issue=issue, kind="terrestrial", screened=len(order), flagged=sum(1 for f in order if f.concern != "none"),
                         provenance_coverage_pct=round(100 * sum(1 for f in order if all(x.excerpt for x in f.evidence)) / max(len(order), 1), 1),
                         findings=order)
    return BroadcastRun(res, calcs, ing)
