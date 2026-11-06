"""Step C3 of pm_pack/08: terrestrial screening of one issue, from notice to ranked Finding.

For every located land-mobile notice of another administration within MAX_DISTANCE_KM of Finland:
  1. nearest point of the Finland polygon and the distance (scoring.geometry.Region, Natural Earth 1:50m)
  2. the path from the station to that point split into land and sea zones (1 km samples against the country
     polygons; sea = outside every loaded country, treated as 'Cold' sea for P.1546: Baltic, Gulf of Finland)
  3. field strength at the border with ITU-R P.1546-6 (radar.calc.p1546) for the notified e.r.p., 10 % time,
     50 % locations, 10 m receiving height
  4. the ECC/ERC T/R 25-08 Annex 1 trigger for the band plus 10 log10(channel / 25 kHz); margin = trigger - E

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
NO_CRITERION_REVIEW_KM = 100.0   # [HYPOTHESIS] without a criterion, only stations this close go to review (Q12)
WITHIN_DB_MEDIUM = 6.0           # [HYPOTHESIS] within 6 dB of the trigger is still worth a look (Q12)
DEFAULT_HEIGHT = {"ML": 1.5, "MO": 1.5}   # [HYPOTHESIS] vehicle or handheld height when none is filed
DEFAULT_HEIGHT_OTHER = 10.0
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
    row = next((t for t in thresholds() if t.f_min_mhz <= f < t.f_max_mhz), None)
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
    if n.antenna_height_m:
        heff, src = n.antenna_height_m, "antenna height above ground (fxm_ant.hgt_agl), no terrain profile"
    else:
        heff = DEFAULT_HEIGHT.get(n.station_class or "", DEFAULT_HEIGHT_OTHER)
        src = f"not filed; {heff:g} m assumed for class {n.station_class} [hypothesis]"
    from radar.calc.p1546 import field_strength

    segs = path_segments(round(n.lat, 5), round(n.lon, 5), round(nlat, 5), round(nlon, 5), round(max(d, 0.04), 3))
    fs = field_strength(n.freq_hz / 1e6, list(segs), heff, n.erp_dbw)
    row, bc = threshold_for(n.freq_hz, n.bandwidth_hz)
    c = TerrestrialCalc("computed", "", round(d, 1), (nlat, nlon), segs, heff, src, fs.e_dbuv_m, fs.free_space_dbuv_m,
                        row, bc, notes=fs.notes)
    if row is not None:
        c.trigger_dbuv_m = round(row.threshold_dbuv_m + bc, 2)
        c.margin_db = round(c.trigger_dbuv_m - fs.e_dbuv_m, 2)
    if extra.directivity == "D" and n.azimuth_deg is not None:
        c.notes.append(f"directional antenna, maximum radiation at {n.azimuth_deg:g} deg; no pattern applied (conservative)")
    return c


def concern(n: TerrestrialNotice, c: TerrestrialCalc) -> tuple[str, str]:
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
                C("antenna", x) for x in ("power_dbw", "power_quantity", "height_agl_m", "directivity")]))
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
                        CalcInput(name="h1 transmitting antenna height", value=c.heff_m, unit="m", evidence_id=a_ev),
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
            geo = "near_border" if c.distance_km <= 300 else "far"
            del s_ev
        elif c.distance_km is not None:
            geo = "near_border" if c.distance_km <= 300 else "far"
        findings.append(Finding(id="", kind="terrestrial", issue=issue, notice_id=n.notice_id, group_id=None,
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
