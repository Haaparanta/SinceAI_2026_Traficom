"""Data contracts for the scoring package.

Input objects mirror the ITU field names (SRS database for space, T12 notice item keys
for terrestrial) so that an adapter is a plain rename, not a re-modelling.
Unknown values are None. The scorer never invents a value; a missing input lowers
`confidence` and is listed in `missing_inputs`.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import date
from typing import Any, Optional


# ----------------------------------------------------------------------------- outputs

@dataclass
class Evidence:
    """One traceable source for a factor value."""
    kind: str        # filing | finnish_table | regulation | calculation | geometry | asset | history
    source: str      # where to look: table.column=value, M4 row ID, RR article, formula name
    excerpt: str     # the values actually used, as text

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass
class Factor:
    """One scored consideration. value is always in [0, 1]."""
    name: str
    group: str                 # relevance | severity | urgency
    value: float
    weight: float              # weight inside its group (relevance factors multiply, weight 1.0)
    available: bool            # False when the inputs were missing and a neutral value was used
    reason: str                # one deterministic sentence
    evidence: list[Evidence] = field(default_factory=list)
    indicative: bool = False   # True when the value rests on a calculation with assumptions

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["value"] = round(self.value, 3)
        return d


@dataclass
class Finding:
    """A (notice item x Finnish target) pair with its score and full audit trail."""
    finding_id: str
    subject_id: str            # grp_id (space) or notice id (terrestrial)
    subject_label: str
    target_id: str             # Finnish allocation unit id or protected station id
    target_label: str
    score: int
    priority: str              # A | B | C | D
    relevance: float
    severity: float
    urgency: float
    confidence: float
    factors: list[Factor]
    screened_out_reason: Optional[str] = None
    indicative: bool = False
    missing_inputs: list[str] = field(default_factory=list)
    explanation: str = ""
    deadline: Optional[str] = None   # ISO date of the comment/agreement window end, when known

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["factors"] = [f.to_dict() for f in self.factors]
        for k in ("relevance", "severity", "urgency", "confidence"):
            d[k] = round(getattr(self, k), 3)
        return d


@dataclass
class ScoredSubject:
    """Notice-level roll-up: one satellite network group or one terrestrial notice."""
    subject_id: str
    subject_label: str
    score: int
    priority: str
    confidence: float
    breadth: int                      # number of distinct Finnish services/targets with a finding
    findings: list[Finding]           # sorted by score desc, screened-out ones last
    summary: str = ""
    status: str = "active"            # active | withdrawn | screened_out
    deadline: Optional[str] = None

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["findings"] = [f.to_dict() for f in self.findings]
        d["confidence"] = round(self.confidence, 3)
        return d


# ----------------------------------------------------------------------------- space inputs

@dataclass
class OrbitInfo:
    kind: str = "unknown"                       # GSO | NGSO | unknown
    long_nom_deg: Optional[float] = None        # geo.long_nom (East positive)
    inclination_deg: Optional[float] = None     # orbit.inclin_ang
    apogee_km: Optional[float] = None           # orbit.apog
    perigee_km: Optional[float] = None          # orbit.perig
    n_planes: Optional[int] = None              # non_geo.nbr_plane
    sats_per_plane: Optional[int] = None        # orbit.nbr_sat_pl

    @property
    def altitude_km(self) -> Optional[float]:
        vals = [v for v in (self.apogee_km, self.perigee_km) if v is not None]
        if not vals:
            return None
        return sum(vals) / len(vals)


@dataclass
class SpaceGroup:
    """One frequency group of one satellite-network notice (SRS tables notice + grp + freq + ...)."""
    ntc_id: str
    grp_id: str
    sat_name: str
    adm: str                                    # notifying administration symbol, e.g. "RUS"
    ntc_type: str                               # G (GSO) | N (NGSO) | S/T (earth station) | R (radio astronomy)
    emi_rcp: str                                # E = space station transmits (downlink); R = receives (uplink)
    freq_min_mhz: float
    freq_max_mhz: float
    special_section: str = "unknown"            # CR/C, API/A, AP30/E, AP30A/E, AP30B/A6A, PART-I-S, ...
    ific_no: Optional[int] = None
    ific_date: Optional[date] = None
    act_code: str = "A"                         # A add | M modify | S suppress (SRS act_code)
    ntf_occurs: Optional[str] = None            # F first submission | R resubmission
    beam_name: str = ""
    gain_dbi: Optional[float] = None            # s_beam.gain (max isotropic gain)
    pwr_ds_max_dbw_hz: Optional[float] = None   # emiss.pwr_ds_max
    pep_max_dbw: Optional[float] = None         # emiss.pep_max
    bandwidth_khz: Optional[float] = None       # grp.bdwdth or freq.bdwdth
    orbit: OrbitInfo = field(default_factory=OrbitInfo)
    srv_area: list[str] = field(default_factory=list)     # srv_area.ctry symbols
    stn_cls: list[str] = field(default_factory=list)      # srv_cls.stn_cls
    nat_srv: list[str] = field(default_factory=list)      # srv_cls.nat_srv
    affected_adms: list[str] = field(default_factory=list)  # provn / tr_aff_ntw adm symbols
    coord_provisions: list[str] = field(default_factory=list)  # provn.coord_prov e.g. 9.7, 9.11A, 9.14, 9.21
    f_pfd_limit_commit: Optional[bool] = None   # geo/non_geo.f_pfd_limit
    earth_station_ctry: list[str] = field(default_factory=list)  # e_as_stn.ctry / e_stn.ctry
    earth_station_lat: Optional[float] = None
    earth_station_lon: Optional[float] = None
    source_ref: str = ""                        # file + table + key, for the evidence trail

    @property
    def label(self) -> str:
        return f"{self.sat_name} ({self.adm}) {self.special_section} grp {self.grp_id} {self.emi_rcp} {self.freq_min_mhz:g}-{self.freq_max_mhz:g} MHz"


@dataclass
class FinnishSpaceNetwork:
    """A Finnish (adm FIN) satellite network already filed/in use, to protect from new systems."""
    sat_name: str
    freq_min_mhz: float
    freq_max_mhz: float
    emi_rcp: str                                # E or R, as seen from the Finnish space station
    orbit_kind: str = "unknown"
    source_ref: str = ""


# ----------------------------------------------------------------------------- terrestrial inputs

@dataclass
class TerrestrialNotice:
    """One terrestrial notice (T11/T12 item keys; TerRaBase fxm_* columns map onto these)."""
    notice_id: str
    adm: str                                    # t_adm
    ctry: str                                   # t_ctry
    action: str                                 # ADD | MODIFY | SUPPRESS | WITHDRAW
    freq_assgn_mhz: float                       # t_freq_assgn
    lat: float                                  # decimal degrees (from t_lat +DDMMSS)
    lon: float                                  # decimal degrees (from t_long +DDDMMSS)
    adm_ref_id: str = ""                        # t_adm_ref_id (unique id given by the administration)
    stn_cls: str = ""                           # t_stn_cls: FB base, ML land mobile, FX fixed, ...
    nat_srv: list[str] = field(default_factory=list)   # t_nat_srv
    fragment: str = "NTFD_RR"                   # t_fragment: NTFD_RR | Req_agrt
    prov: str = "RR11.2"                        # t_prov: RR11.2 | RR9.21
    ific_no: Optional[int] = None
    ific_date: Optional[date] = None
    notice_type: str = "T12"                    # T11 | T12 | ...
    bandwidth_khz: Optional[float] = None       # decoded t_bdwdth_cde (e.g. 16K0 -> 16.0)
    emi_cls: str = ""                           # t_emi_cls
    site_name: str = ""
    site_alt_m: Optional[float] = None          # t_site_alt
    erp_dbw: Optional[float] = None             # radiated power converted to e.r.p. (dBW)
    pwr_type: str = ""                          # E e.r.p. | I e.i.r.p. | V e.m.r.p. (as notified)
    ant_dir: str = "ND"                         # t_ant_dir: D | ND
    azm_max_deg: Optional[float] = None         # t_azm_max_e
    beamwidth_deg: Optional[float] = None       # t_bmwdth
    gain_dbi: Optional[float] = None            # t_gain_max (converted to dBi)
    hgt_agl_m: Optional[float] = None           # t_hgt_agl
    elev_deg: Optional[float] = None            # t_elev
    d_inuse: Optional[date] = None
    change_status: str = "unknown"              # new | modified | unchanged | withdrawn | unknown (from the IFIC diff)
    changed_fields: list[str] = field(default_factory=list)
    source_ref: str = ""

    @property
    def label(self) -> str:
        return f"{self.adm} {self.stn_cls} {self.freq_assgn_mhz:g} MHz {self.site_name or ''} ({self.action})".strip()

    def identity_key(self) -> tuple:
        """Identifying elements of a T12 notice (freq, site, class, emission, bandwidth)."""
        return (self.adm, round(self.freq_assgn_mhz, 6), round(self.lat, 4), round(self.lon, 4),
                self.stn_cls, self.emi_cls, self.bandwidth_khz)


@dataclass
class ProtectedStation:
    """A Finnish station of special interest (the synthetic XLS dataset shape)."""
    station_id: str
    name: str
    lat: float
    lon: float
    f_center_mhz: float
    bandwidth_khz: float
    service: str = ""
    antenna_height_m: Optional[float] = None
    antenna_azimuth_deg: Optional[float] = None
    antenna_directivity: str = "ND"             # D | ND
    gain_dbi: Optional[float] = None
    protection_field_strength_dbuv_m: Optional[float] = None   # if a specific criterion is known
    pfd_limit_dbw_m2: Optional[float] = None                   # for space-side checks, if given
    source_ref: str = ""

    @property
    def f_min_mhz(self) -> float:
        return self.f_center_mhz - self.bandwidth_khz / 2000.0

    @property
    def f_max_mhz(self) -> float:
        return self.f_center_mhz + self.bandwidth_khz / 2000.0


# ----------------------------------------------------------------------------- helpers

def parse_date(value: Any) -> Optional[date]:
    """Accept date, 'YYYY-MM-DD', 'YYYYMMDD' or None."""
    if value is None or value == "":
        return None
    if isinstance(value, date):
        return value
    s = str(value).strip()
    if len(s) == 8 and s.isdigit():
        return date(int(s[:4]), int(s[4:6]), int(s[6:]))
    return date.fromisoformat(s[:10])


def dms_to_decimal(value: Any) -> Optional[float]:
    """ITU +DDDMMSS / +DDMMSS strings (or ints) to decimal degrees."""
    if value is None or value == "":
        return None
    s = str(value).strip()
    sign = -1.0 if s.startswith("-") else 1.0
    digits = s.lstrip("+-")
    if not digits.isdigit():
        return float(s)
    ss = int(digits[-2:]); mm = int(digits[-4:-2]); dd = int(digits[:-4] or 0)
    return sign * (dd + mm / 60.0 + ss / 3600.0)


_BW_UNITS = {"H": 1e-3, "K": 1.0, "M": 1e3, "G": 1e6}


def bandwidth_code_to_khz(code: Optional[str]) -> Optional[float]:
    """ITU necessary-bandwidth code (e.g. 16K0, 1M25, 500H) to kHz."""
    if not code:
        return None
    code = code.strip().upper()
    for unit, mult in _BW_UNITS.items():
        if unit in code:
            a, _, b = code.partition(unit)
            try:
                return (float(a or 0) + (float("0." + b) if b else 0.0)) * mult
            except ValueError:
                return None
    try:
        return float(code)
    except ValueError:
        return None
