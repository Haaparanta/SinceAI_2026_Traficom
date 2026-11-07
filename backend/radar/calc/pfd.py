"""Step C1 of pm_pack/08: indicative worst-case pfd of a satellite downlink at the Finnish surface (GSO and non-GSO).

Formula (pm_pack/06):   pfd = P_d + G + 10 log10(B) - 10 log10(4 pi d^2)       [dB(W/m2) in B]
    P_d  maximum power density at the antenna input, dBW/Hz        (emiss.pwr_ds_max)
    G    maximum gain of the transmitting beam, dBi                (s_beam.gain)
    B    min(reference bandwidth of the limit, necessary bandwidth of the emission), Hz
    d    slant range from the reference point to the satellite, m  (radar.pipeline.geography)

The pfd is evaluated at every Finnish reference point that sees the satellite, against every applicable
RR Article 21 Table 21-4 row (data/reference/pfd_limits.csv) at that point's angle of arrival; the reported
case is the smallest margin. margin_db = limit - pfd; negative means the limit is exceeded.

Worst case on purpose: free-space propagation, no atmospheric or polarisation loss, maximum beam gain assumed
towards Finland (gain contours are not read). The result is therefore an upper bound and always 'indicative'.

Non-GSO (worst_case_ngso): one satellite at the orbit's lowest altitude (the perigee; an upper bound for eccentric
orbits), seen from the Finnish reference point that sees it highest. The highest elevation follows from the
inclination: a satellite reaches latitudes up to min(i, 180 - i), so a point at latitude phi sees it at a central
angle of at least max(0, phi - i_eff). Every elevation from 0 deg to that maximum is scanned (0.25 deg steps plus
the limit's segment edges) with d(delta) = sqrt((R + h)^2 - (R cos delta)^2) - R sin delta. Table 21-4 rows for
non-GSO: the 'any' and 'NGSO' rows; for highly inclined orbits (apogee over 18 000 km, inclination 35 to 145 deg)
the footnote-16 row replaces the footnote-13 row in 17.7-19.7 GHz. Footnote 13: X from the constellation size N
(orbit.nbr_sat_pl summed); for N of 1 000 or more X also needs Nv, which is not filed, so its lower bound 20.3 dB is
used (the least strict limit: an exceedance is certain, a pass is not conclusive). Footnote 11 rows apply only to
systems with 99 satellites or fewer.
"""
from __future__ import annotations

import csv
import math
from dataclasses import dataclass, field
from functools import lru_cache

from radar.config import ROOT
from radar.pipeline import geography as G

LIMITS_FILE = ROOT / "data" / "reference" / "pfd_limits.csv"
FORMULA = "pfd = P_d + G + 10*log10(B) - 10*log10(4*pi*d^2); B = min(B_ref, B_emission); margin = limit(delta) - pfd"
FORMULA_NGSO = (FORMULA + "; d(delta) = sqrt((R+h)^2 - (R cos delta)^2) - R sin delta at the perigee altitude h, "
                "delta from 0 to the highest elevation Finland sees")
R_EARTH_KM = 6378.137
HEO_APOGEE_KM = 18000.0           # RR footnotes 15 and 16 (21.16.6B, 21.16.6C)
HEO_INCLINATION = (35.0, 145.0)
X_LOWER_BOUND_DB = 20.3           # RR footnote 13 (21.16.6): X = max(20.3, 10 log10 Nv) for 1 000 <= N <= 6 000


@dataclass(frozen=True)
class LimitRow:
    id: str
    band_min_mhz: float
    band_max_mhz: float
    orbit: str
    service: str
    ref_bw_hz: float
    segments: tuple[tuple[float, float, float, float, float], ...]   # (from, to, base, slope, ref)
    applies_to_finland: bool
    source: str
    page: str
    review: str
    notes: str
    x_footnote: str = ""                 # "13": the limit depends on X(N) (17.7-19.3 GHz non-GSO FSS)
    max_satellites: int | None = None    # footnote 11: the row applies to systems of at most this many satellites

    def limit(self, delta_deg: float, x_db: float = 0.0) -> float:
        """With x_db (footnote 13): -115 - X up to 5 deg, -115 - X + ((10 + X)/20)(delta - 5) to 25 deg, unchanged above."""
        for k, (lo, hi, base, slope, ref) in enumerate(self.segments):
            if lo <= delta_deg <= hi:
                if self.x_footnote == "13" and x_db and k < len(self.segments) - 1:
                    return base - x_db + ((10 + x_db) / 20 if k == 1 else 0.0) * (delta_deg - ref)
                return base + slope * (delta_deg - ref)
        raise ValueError(f"angle {delta_deg} outside the segments of {self.id}")

    def excerpt(self) -> str:
        return (f"{self.band_min_mhz:g}-{self.band_max_mhz:g} MHz {self.orbit}; ref bw {fmt_bw(self.ref_bw_hz)}; "
                f"segments {self.segments_text()}; page {self.page}")

    def segments_text(self) -> str:
        return "; ".join(f"{lo:g}-{hi:g} deg: {base:g}{'' if slope == 0 else f' {slope:+g}*(d-{ref:g})'}"
                         for lo, hi, base, slope, ref in self.segments)


@lru_cache(maxsize=1)
def limits() -> tuple[LimitRow, ...]:
    rows = []
    with LIMITS_FILE.open(encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            segs = tuple(tuple(float(x) for x in s.split("|")) for s in r["segments"].split(";"))
            rows.append(LimitRow(r["id"], float(r["band_min_mhz"]), float(r["band_max_mhz"]), r["orbit"], r["service"],
                                 float(r["ref_bw_hz"]), segs, r["applies_to_finland"] == "yes", r["source"], r["page"],
                                 r["review"], r["notes"], (r.get("x_footnote") or "").strip(),
                                 int(r["max_satellites"]) if (r.get("max_satellites") or "").strip() else None))
    return tuple(rows)


def applicable_limits(freq_min_hz: int, freq_max_hz: int, orbit: str = "GSO", n_sats: int | None = None) -> list[LimitRow]:
    """orbit: GSO, NGSO or HEO (a non-GSO highly inclined orbit). n_sats: constellation size, for footnote 11."""
    lo, hi = freq_min_hz / 1e6, freq_max_hz / 1e6
    allowed = {"GSO": ("GSO", "any"), "NGSO": ("NGSO", "any"), "HEO": ("NGSO", "HEO", "any")}[orbit]
    rows = [r for r in limits() if r.applies_to_finland and r.orbit in allowed
            and min(hi, r.band_max_mhz) - max(lo, r.band_min_mhz) > 0]
    if orbit == "HEO" and any(r.orbit == "HEO" for r in rows):       # footnote 16 replaces footnote 13 for these orbits
        rows = [r for r in rows if r.x_footnote != "13"]
    return [r for r in rows if r.max_satellites is None or n_sats is None or n_sats <= r.max_satellites]


def x_db(n_sats: int | None) -> tuple[float, str]:
    """RR footnote 13 (21.16.6): X in dB from the number of satellites N."""
    if n_sats is None:
        return 0.0, "N not filed: X = 0 dB (the least strict value)"
    if n_sats <= 50:
        return 0.0, f"N = {n_sats}: X = 0 dB"
    if n_sats <= 288:
        return round(5 / 119 * (n_sats - 50), 3), f"N = {n_sats}: X = (5/119)(N - 50)"
    if n_sats <= 999:
        return round((n_sats + 402) / 69, 3), f"N = {n_sats}: X = (1/69)(N + 402)"
    return X_LOWER_BOUND_DB, (f"N = {n_sats}: X depends on Nv, which is not filed; its lower bound {X_LOWER_BOUND_DB:g} dB is used "
                              "(least strict: an exceedance is certain, a pass is not conclusive)")


def orbit_class(orbits: list["OrbitIn"]) -> str:
    """HEO when any orbit has apogee over 18 000 km and inclination 35-145 deg (RR footnotes 15, 16), else NGSO."""
    for o in orbits:
        if o.apogee_km and o.apogee_km > HEO_APOGEE_KM and o.inclination_deg is not None \
                and HEO_INCLINATION[0] <= o.inclination_deg <= HEO_INCLINATION[1]:
            return "HEO"
    return "NGSO"


def fmt_bw(hz: float) -> str:
    for unit, div in (("GHz", 1e9), ("MHz", 1e6), ("kHz", 1e3)):
        if hz >= div:
            return f"{hz / div:g} {unit}"
    return f"{hz:g} Hz"


def spreading_loss_db(d_m: float) -> float:
    return 10 * math.log10(4 * math.pi * d_m ** 2)


def pfd_db(p_d_dbw_hz: float, gain_dbi: float, bandwidth_hz: float, d_m: float) -> float:
    return p_d_dbw_hz + gain_dbi + 10 * math.log10(bandwidth_hz) - spreading_loss_db(d_m)


@dataclass
class Emission:
    seq_no: int
    designation: str | None
    p_d_dbw_hz: float | None
    necessary_bw_hz: float | None
    flagged: bool = False


@dataclass
class PfdResult:
    status: str                         # computed | no_limit | no_input | not_visible | flagged_input
    pfd_db: float | None = None
    limit_db: float | None = None
    margin_db: float | None = None
    worst: dict = field(default_factory=dict)       # inputs of the worst case
    cases: int = 0
    notes: list[str] = field(default_factory=list)
    orbit: str = "GSO"                  # GSO | NGSO | HEO

    @property
    def method(self) -> str:
        return "pfd_gso_worst_case" if self.orbit == "GSO" else "pfd_ngso_worst_case"


def worst_case(freq_min_hz: int, freq_max_hz: int, sat_lon_deg: float, emissions: list[Emission],
               gain_dbi: float | None, steerable: bool | None = None,
               extra_points: list[tuple[str, float, float]] | None = None) -> PfdResult:
    """extra_points: (name, lat, lon) evaluated next to the reference points, e.g. matched special-interest stations."""
    rows = applicable_limits(freq_min_hz, freq_max_hz, "GSO")
    if not rows:
        return PfdResult("no_limit", notes=["no RR Article 21 Table 21-4 limit applies to this band in Finland"])
    usable = [e for e in emissions if e.p_d_dbw_hz is not None and not e.flagged]
    flagged = [e for e in emissions if e.flagged]
    if gain_dbi is None or not usable:
        status = "flagged_input" if flagged and not usable else "no_input"
        miss = "beam gain" if gain_dbi is None else "power density"
        return PfdResult(status, notes=[f"{miss} not filed or not usable; pfd not computed"]
                         + ([f"{len(flagged)} emission(s) with an implausible filed value left out"] if flagged else []))
    points = []
    for name, lat, lon in list(G.reference_points()) + list(extra_points or []):
        el, d_km = G.gso_look(lat, lon, sat_lon_deg)
        if el > 0:
            points.append((name, lat, lon, el, d_km))
    if not points:
        return PfdResult("not_visible", notes=["satellite below the horizon at every reference point and matched station"])

    best: PfdResult | None = None
    cases = 0
    for row in rows:
        for e in usable:
            b = min(row.ref_bw_hz, e.necessary_bw_hz) if e.necessary_bw_hz else row.ref_bw_hz
            for name, lat, lon, el, d_km in points:
                cases += 1
                p = pfd_db(e.p_d_dbw_hz, gain_dbi, b, d_km * 1000)
                lim = row.limit(el)
                m = lim - p
                if best is None or m < best.margin_db:
                    best = PfdResult("computed", round(p, 2), round(lim, 2), round(m, 2), {
                        "point": name, "lat": lat, "lon": lon, "elevation_deg": round(el, 3), "slant_range_km": round(d_km, 1),
                        "p_d_dbw_hz": e.p_d_dbw_hz, "emission_seq_no": e.seq_no, "designation": e.designation,
                        "gain_dbi": gain_dbi, "bandwidth_hz": b, "ref_bw_hz": row.ref_bw_hz,
                        "spreading_loss_db": round(spreading_loss_db(d_km * 1000), 2), "limit_row": row,
                    })
    best.cases = cases
    best.worst["steerable"] = steerable
    pointing = ("the beam is steerable, so its peak can be pointed at Finland" if steerable else
                "beam pointing unknown: the IFIC database has no boresight or gain contours (GIMS); peak gain assumed"
                if steerable is not None else "peak gain assumed towards Finland")
    best.notes = [
        "free-space propagation, no atmospheric loss, maximum beam gain towards Finland: an upper bound",
        pointing,
        f"worst of {cases} cases ({len(usable)} emission(s) x {len(points)} visible point(s) x {len(rows)} limit row(s))"
        + (f"; points include {len(extra_points)} special-interest station(s)" if extra_points else ""),
        f"limit row {best.worst['limit_row'].id}: {best.worst['limit_row'].review}",
    ] + ([f"{len(flagged)} emission(s) with an implausible filed value left out"] if flagged else [])
    return best


# ---- non-GSO ----------------------------------------------------------------------------------------------------

@dataclass(frozen=True)
class OrbitIn:
    orbit_id: int
    inclination_deg: float | None
    apogee_km: float | None
    perigee_km: float | None
    satellites: int | None


def elevation_deg(central_angle_deg: float, altitude_km: float) -> float:
    g = math.radians(central_angle_deg)
    return math.degrees(math.atan2(math.cos(g) - R_EARTH_KM / (R_EARTH_KM + altitude_km), math.sin(g)))


def slant_range_km(altitude_km: float, elev_deg: float) -> float:
    e = math.radians(elev_deg)
    return math.sqrt((R_EARTH_KM + altitude_km) ** 2 - (R_EARTH_KM * math.cos(e)) ** 2) - R_EARTH_KM * math.sin(e)


def highest_elevation(inclination_deg: float, altitude_km: float) -> tuple[str, float]:
    """(reference point, highest elevation in deg) of a satellite of this inclination and altitude over Finland."""
    i_eff = min(inclination_deg % 180, 180 - inclination_deg % 180)
    best = None
    for name, lat, _ in G.reference_points():
        el = elevation_deg(max(0.0, lat - i_eff), altitude_km)
        if best is None or el > best[1]:
            best = (name, el)
    return best


def worst_case_ngso(freq_min_hz: int, freq_max_hz: int, orbits: list[OrbitIn], emissions: list[Emission],
                    gain_dbi: float | None, steerable: bool | None = None) -> PfdResult:
    n_sats = sum(o.satellites or 0 for o in orbits) or None
    oclass = orbit_class(orbits)
    rows = applicable_limits(freq_min_hz, freq_max_hz, oclass, n_sats)
    dropped = [r for r in applicable_limits(freq_min_hz, freq_max_hz, oclass) if r not in rows]
    fn11 = [f"footnote 11 rows left out: {', '.join(r.id for r in dropped)} apply to 99 satellites or fewer, this system has {n_sats}"] if dropped else []
    if not rows:
        return PfdResult("no_limit", notes=["no RR Article 21 Table 21-4 limit applies to this band for this orbit in Finland"] + fn11,
                         orbit=oclass)
    usable = [e for e in emissions if e.p_d_dbw_hz is not None and not e.flagged]
    flagged = [e for e in emissions if e.flagged]
    if gain_dbi is None or not usable:
        status = "flagged_input" if flagged and not usable else "no_input"
        miss = "beam gain" if gain_dbi is None else "power density"
        return PfdResult(status, notes=[f"{miss} not filed or not usable; pfd not computed"], orbit=oclass)
    geoms = {}
    for o in orbits:
        h = o.perigee_km if o.perigee_km is not None else o.apogee_km
        if h is None or o.inclination_deg is None or h <= 0:
            continue
        key = (round(o.inclination_deg, 4), round(h, 3))
        if key not in geoms:
            point, top = highest_elevation(o.inclination_deg, h)
            if top > 0:
                geoms[key] = (o, h, point, top)
    if not geoms:
        return PfdResult("not_visible", notes=["no orbit reaches above the horizon of the Finnish reference points"], orbit=oclass)
    xv, xnote = x_db(n_sats)
    best: PfdResult | None = None
    tops: dict[tuple, list] = {}         # per orbit geometry: [highest elevation, smallest margin there]
    cases = 0
    for o, h, point, top in geoms.values():
        for row in rows:
            edges = {lo for lo, *_ in row.segments} | {hi for _, hi, *_ in row.segments}
            angles = sorted({round(k * 0.25, 2) for k in range(int(top / 0.25) + 1)} | {e for e in edges if e <= top} | {round(top, 3)})
            x_use = xv if row.x_footnote == "13" else 0.0
            for e in usable:
                b = min(row.ref_bw_hz, e.necessary_bw_hz) if e.necessary_bw_hz else row.ref_bw_hz
                for el in angles:
                    cases += 1
                    d_km = slant_range_km(h, el)
                    p = pfd_db(e.p_d_dbw_hz, gain_dbi, b, d_km * 1000)
                    lim = row.limit(el, x_use)
                    m = lim - p
                    if el == round(top, 3):
                        t = tops.setdefault((o.inclination_deg, h), [round(top, 2), None])
                        t[1] = round(m, 2) if t[1] is None else min(t[1], round(m, 2))
                    if best is None or m < best.margin_db:
                        best = PfdResult("computed", round(p, 2), round(lim, 2), round(m, 2), {
                            "point": point, "elevation_deg": round(el, 3), "slant_range_km": round(d_km, 1),
                            "max_elevation_deg": round(top, 2), "orbit_id": o.orbit_id, "inclination_deg": o.inclination_deg,
                            "altitude_km": h, "apogee_km": o.apogee_km, "perigee_km": o.perigee_km,
                            "p_d_dbw_hz": e.p_d_dbw_hz, "emission_seq_no": e.seq_no, "designation": e.designation,
                            "gain_dbi": gain_dbi, "bandwidth_hz": b, "ref_bw_hz": row.ref_bw_hz,
                            "spreading_loss_db": round(spreading_loss_db(d_km * 1000), 2), "limit_row": row,
                            "x_db": x_use, "n_sats": n_sats, "orbit_class": oclass,
                        })
    best.cases = cases
    best.orbit = oclass
    best.worst["steerable"] = steerable
    best.worst["tops"] = sorted((tuple(t) for t in tops.values()), key=lambda t: (-t[0], t[1]))
    top_el, top_margin = best.worst["tops"][0]          # the geometry that rises highest over Finland
    best.worst["top_margin_db"], best.worst["top_elevation_deg"] = top_margin, top_el
    best.worst["x_lower_bound"] = best.worst["limit_row"].x_footnote == "13" and (n_sats or 0) >= 1000
    best.worst["y_assumed"] = "Y = 0 assumed" in best.worst["limit_row"].notes     # footnote 22: Y is not filed
    w = best.worst
    best.notes = [
        "one satellite at the perigee altitude (the lowest; an upper bound for an eccentric orbit), free-space propagation, "
        "maximum beam gain towards Finland: an upper bound",
        f"orbit {w['orbit_id']}: inclination {w['inclination_deg']:g} deg, altitude {w['altitude_km']:g} km; seen up to "
        f"{w['max_elevation_deg']:g} deg from {w['point']}; worst at {w['elevation_deg']:g} deg",
        "margin with the satellite at its highest over Finland, per orbit: "
        + "; ".join(f"{el:g} deg: {m:.2f} dB" for el, m in w["tops"]),
        "the beam is steerable, so its peak can be pointed at Finland" if steerable else
        "beam pointing unknown: the IFIC database has no boresight or gain contours (GIMS); peak gain assumed",
        f"worst of {cases} cases ({len(usable)} emission(s) x {len(geoms)} orbit geometry(ies) x elevation scan x {len(rows)} limit row(s))",
        f"limit row {w['limit_row'].id}: {w['limit_row'].review}",
    ] + ([f"footnote 13: {xnote}"] if w["limit_row"].x_footnote == "13" else []) \
      + (["footnote 22: Y (co-frequency satellites per hemisphere) is not filed; Y = 0, the least strict value"] if w["y_assumed"] else []) + fn11 \
      + ([f"{len(flagged)} emission(s) with an implausible filed value left out"] if flagged else [])
    return best


def load_orbits(con, notice_ids: list[str]) -> dict[str, list[OrbitIn]]:
    from radar import schema_map

    M = schema_map.load()
    q = lambda c: M.q("space", "orbit", c)  # noqa: E731
    out: dict[str, list[OrbitIn]] = {}
    wanted = set(notice_ids)
    for nid, oid, inc, apo, per, n in con.execute(
            f"SELECT CAST({q('notice_id')} AS VARCHAR), {q('orbit_id')}, {q('inclination_deg')}, {q('apogee_km')}, "
            f"{q('perigee_km')}, {q('satellites_per_plane')} FROM {M.t('space','orbit')} ORDER BY 1, 2").fetchall():
        if nid in wanted:
            out.setdefault(nid, []).append(OrbitIn(int(oid), None if inc is None else float(inc), None if apo is None else float(apo),
                                                   None if per is None else float(per), None if n is None else int(n)))
    return out


def margin_factor(margin_db: float | None, weights: dict) -> tuple[float, str]:
    """Severity factor from the scoring package bins (scoring/DESIGN.md section 3)."""
    if margin_db is None:
        return 0.5, "not evaluated"
    if margin_db < 0:
        return 1.0, f"exceeds the limit by {-margin_db:.1f} dB"
    for k, (limit, value) in enumerate(((6, 0.8), (15, 0.5), (30, 0.2))):
        if margin_db < limit:
            return value, f"within {limit} dB of the limit"
    return 0.05, f"{margin_db:.1f} dB below the limit"


# ---------------------------------------------------------------------------------------------------------------
# Inputs from the IFIC database (names via schema_map.yaml)

@dataclass
class GroupInputs:
    group_id: str
    notice_id: str
    beam_name: str | None
    direction_code: str | None
    gain_dbi: float | None
    emissions: list[Emission]
    steerable: bool = False         # s_beam.f_steer = 'Y': the beam can be pointed anywhere, including Finland


def load_inputs(con, group_ids: list[str], flagged_groups: set[str] | None = None) -> dict[str, GroupInputs]:
    """Emissions and beam gain of the given groups. flagged_groups: anomalies from the adapter (left out)."""
    from radar import schema_map
    from radar.adapters.space_ific import PD_PLAUSIBLE_DBW_HZ, necessary_bandwidth_hz

    if not group_ids:
        return {}
    M = schema_map.load()
    q = lambda e, c, a=None: M.q("space", e, c, a)  # noqa: E731
    con.execute("CREATE OR REPLACE TEMP TABLE _gids(gid VARCHAR)")
    con.executemany("INSERT INTO _gids VALUES (?)", [[g] for g in group_ids])
    out: dict[str, GroupInputs] = {}
    for gid, nid, beam, emi_rcp, gain, steer in con.execute(f"""
            SELECT CAST({q('group','group_id','g')} AS VARCHAR), CAST({q('group','notice_id','g')} AS VARCHAR),
                   {q('group','beam_name','g')}, {q('group','direction','g')}, {q('beam','max_gain_dbi','b')}, {q('beam','steerable','b')}
            FROM {M.t('space','group')} g JOIN _gids ON _gids.gid = CAST({q('group','group_id','g')} AS VARCHAR)
            LEFT JOIN {M.t('space','beam')} b ON {q('beam','notice_id','b')} = {q('group','notice_id','g')}
                 AND {q('beam','direction','b')} = {q('group','direction','g')} AND {q('beam','beam_name','b')} = {q('group','beam_name','g')}
            """).fetchall():
        out[gid] = GroupInputs(gid, nid, beam, emi_rcp, None if gain is None else round(float(gain), 4), [],
                               steerable=(steer or "").upper() == "Y")
    for gid, seq, design, pd in con.execute(f"""
            SELECT CAST({q('emission','group_id','e')} AS VARCHAR), "seq_no", {q('emission','designation','e')},
                   {q('emission','max_power_density_dbw_hz','e')}
            FROM {M.t('space','emission')} e JOIN _gids ON _gids.gid = CAST({q('emission','group_id','e')} AS VARCHAR)
            ORDER BY 1, 2""").fetchall():
        if gid not in out:
            continue
        pdv = None if pd is None else round(float(pd), 4)
        bad = pdv is not None and not PD_PLAUSIBLE_DBW_HZ[0] <= pdv <= PD_PLAUSIBLE_DBW_HZ[1]
        out[gid].emissions.append(Emission(seq, design, pdv, necessary_bandwidth_hz(design), flagged=bad))
    return out
