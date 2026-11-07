"""Step C1 of pm_pack/08: indicative worst-case pfd of a GSO downlink at the Finnish surface.

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

    def limit(self, delta_deg: float) -> float:
        for lo, hi, base, slope, ref in self.segments:
            if lo <= delta_deg <= hi:
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
                                 r["review"], r["notes"]))
    return tuple(rows)


def applicable_limits(freq_min_hz: int, freq_max_hz: int, orbit: str = "GSO") -> list[LimitRow]:
    lo, hi = freq_min_hz / 1e6, freq_max_hz / 1e6
    return [r for r in limits() if r.applies_to_finland and r.orbit in (orbit, "any")
            and min(hi, r.band_max_mhz) - max(lo, r.band_min_mhz) > 0]


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
