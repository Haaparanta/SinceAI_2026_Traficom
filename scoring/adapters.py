"""Adapters from ITU data shapes to the scoring input models.

* groups_from_srs(tables)   : SRS/BR IFIC MDB tables (lists of dict rows) -> SpaceGroup list
* notice_from_t12(items)    : T11/T12 electronic-notice item keys -> TerrestrialNotice
* notices_from_rows(rows)   : TerRaBase-like rows (t_ prefix optional) -> TerrestrialNotice list
* *_from_json(path)         : plain JSON files in the examples/ shape

Readers for .mdb / .db3 files are deliberately not included: export the tables with
mdbtools, pyodbc or sqlite3 and pass the rows in as dicts.
"""
from __future__ import annotations

import json
from datetime import date
from typing import Any, Iterable, Optional

from .models import (FinnishSpaceNetwork, OrbitInfo, ProtectedStation, SpaceGroup, TerrestrialNotice,
                     bandwidth_code_to_khz, dms_to_decimal, parse_date)
from .propagation import erp_dbw_from_notified


def _g(row: dict, *names: str, default: Any = None) -> Any:
    """Tolerant getter: tries each name as given, lower-case and upper-case."""
    for n in names:
        for k in (n, n.lower(), n.upper()):
            if k in row and row[k] not in (None, ""):
                return row[k]
    return default


def _f(x: Any) -> Optional[float]:
    try:
        return None if x in (None, "") else float(x)
    except (TypeError, ValueError):
        return None


NTF_RSN_TO_SECTION = {"A": "API/A", "C": "CR/C", "D": "CR/C", "N": "PART-I-S", "B": "AP30/E", "P": "AP30B/A6A", "U": "RES49"}


def groups_from_srs(tables: dict[str, list[dict]], ific_no: Optional[int] = None, ific_date: Optional[date] = None,
                    source_file: str = "") -> list[SpaceGroup]:
    """Join SRS tables into one SpaceGroup per grp row.

    Expected keys (any subset): notice, grp, freq, s_beam, emiss, geo, orbit, non_geo, srv_area, srv_cls,
    provn, e_as_stn, e_stn, pub_ssn. Column names follow the SRS database description.
    """
    notices = {str(_g(r, "ntc_id")): r for r in tables.get("notice", [])}
    geo = {str(_g(r, "ntc_id")): r for r in tables.get("geo", [])}
    non_geo = {str(_g(r, "ntc_id")): r for r in tables.get("non_geo", [])}
    orbits: dict[str, list[dict]] = {}
    for r in tables.get("orbit", []):
        orbits.setdefault(str(_g(r, "ntc_id")), []).append(r)
    beams = {(str(_g(r, "ntc_id")), str(_g(r, "emi_rcp")), str(_g(r, "beam_name"))): r for r in tables.get("s_beam", [])}
    by_grp = lambda name: _group_by(tables.get(name, []), "grp_id")  # noqa: E731
    freq, emiss, srv_area, srv_cls, provn, e_as = (by_grp(n) for n in ("freq", "emiss", "srv_area", "srv_cls", "provn", "e_as_stn"))
    pub = {str(_g(r, "ntc_id")): r for r in tables.get("pub_ssn", [])}
    e_stn = {str(_g(r, "ntc_id")): r for r in tables.get("e_stn", [])}

    out: list[SpaceGroup] = []
    for g in tables.get("grp", []):
        ntc_id, grp_id = str(_g(g, "ntc_id")), str(_g(g, "grp_id"))
        n = notices.get(ntc_id, {})
        emi = str(_g(g, "emi_rcp", default="E"))
        beam = str(_g(g, "beam_name", default=""))
        fr = freq.get(grp_id, [])
        fmins = [_f(_g(r, "freq_min")) for r in fr]
        fmaxs = [_f(_g(r, "freq_max")) for r in fr]
        fmins = [x for x in fmins if x is not None]
        fmaxs = [x for x in fmaxs if x is not None]
        bw_khz = _f(_g(g, "bdwdth")) or (max((_f(_g(r, "bdwdth")) or 0 for r in fr), default=None))
        if fmins and fmaxs:
            f_min, f_max = min(fmins), max(fmaxs)
        else:
            fa = [_f(_g(r, "freq_mhz", "freq_assgn")) for r in fr]
            fa = [x for x in fa if x is not None]
            if not fa:
                continue
            half = (bw_khz or 0) / 2000.0
            f_min, f_max = min(fa) - half, max(fa) + half
        ntc_type = str(_g(n, "ntc_type", default=_g(g, "ntc_type", default="")))
        orbit = OrbitInfo(kind="unknown")
        if ntc_type == "G" or ntc_id in geo:
            orbit = OrbitInfo(kind="GSO", long_nom_deg=_f(_g(geo.get(ntc_id, {}), "long_nom")))
        elif ntc_type == "N" or ntc_id in non_geo or ntc_id in orbits:
            ob = orbits.get(ntc_id, [])
            incs = [_f(_g(r, "inclin_ang")) for r in ob]
            apos = [_f(_g(r, "apog")) for r in ob]
            pers = [_f(_g(r, "perig", "perigee", "op_ht")) for r in ob]
            orbit = OrbitInfo(kind="NGSO", inclination_deg=max((x for x in incs if x is not None), default=None),
                              apogee_km=max((x for x in apos if x is not None), default=None),
                              perigee_km=min((x for x in pers if x is not None), default=None),
                              n_planes=int(_g(non_geo.get(ntc_id, {}), "nbr_plane", default=0) or 0) or None,
                              sats_per_plane=max((int(_g(r, "nbr_sat_pl", default=0) or 0) for r in ob), default=None))
        b = beams.get((ntc_id, emi, beam), {})
        em = emiss.get(grp_id, [])
        pds = [_f(_g(r, "pwr_ds_max")) for r in em]
        peps = [_f(_g(r, "pep_max")) for r in em]
        section = _g(pub.get(ntc_id, {}), "ssn_ref") or NTF_RSN_TO_SECTION.get(str(_g(n, "ntf_rsn", default="")), "unknown")
        affected = sorted({str(_g(r, "adm", "ctry")) for r in provn.get(grp_id, []) if _g(r, "adm", "ctry")})
        provs = sorted({str(_g(r, "coord_prov")) for r in provn.get(grp_id, []) if _g(r, "coord_prov")})
        es = e_as.get(grp_id, [])
        es_ctry = sorted({str(_g(r, "ctry")) for r in es if _g(r, "ctry")})
        es_row = e_stn.get(ntc_id, {})
        pfd_commit = _g(geo.get(ntc_id, {}), "f_pfd_limit") or _g(non_geo.get(ntc_id, {}), "f_pfd_limit")
        out.append(SpaceGroup(
            ntc_id=ntc_id, grp_id=grp_id, sat_name=str(_g(n, "sat_name", default=_g(geo.get(ntc_id, {}), "sat_name", default=""))),
            adm=str(_g(n, "adm", default="")), ntc_type=ntc_type or orbit.kind[:1], emi_rcp=emi, freq_min_mhz=f_min, freq_max_mhz=f_max,
            special_section=str(section), ific_no=ific_no or (int(_g(n, "wic_no")) if _g(n, "wic_no") else None),
            ific_date=ific_date or parse_date(_g(n, "d_wic")), act_code=str(_g(g, "act_code", default=_g(n, "act_code", default="A"))),
            ntf_occurs=_g(n, "ntf_occurs"), beam_name=beam, gain_dbi=_f(_g(b, "gain")),
            pwr_ds_max_dbw_hz=max((x for x in pds if x is not None), default=None), pep_max_dbw=max((x for x in peps if x is not None), default=None),
            bandwidth_khz=bw_khz, orbit=orbit, srv_area=sorted({str(_g(r, "ctry")) for r in srv_area.get(grp_id, []) if _g(r, "ctry")}),
            stn_cls=sorted({str(_g(r, "stn_cls")) for r in srv_cls.get(grp_id, []) if _g(r, "stn_cls")}),
            nat_srv=sorted({str(_g(r, "nat_srv")) for r in srv_cls.get(grp_id, []) if _g(r, "nat_srv")}),
            affected_adms=affected, coord_provisions=provs,
            f_pfd_limit_commit=(str(pfd_commit).upper() == "Y") if pfd_commit else None,
            earth_station_ctry=es_ctry or ([str(_g(es_row, "ctry"))] if _g(es_row, "ctry") else []),
            earth_station_lat=_f(_g(es_row, "lat_dec")), earth_station_lon=_f(_g(es_row, "long_dec")),
            source_ref=f"{source_file or 'SRS'} notice.ntc_id={ntc_id} grp.grp_id={grp_id}"))
    return out


def _group_by(rows: Iterable[dict], key: str) -> dict[str, list[dict]]:
    out: dict[str, list[dict]] = {}
    for r in rows:
        out.setdefault(str(_g(r, key)), []).append(r)
    return out


# ----------------------------------------------------------------------------- terrestrial

def notice_from_t12(items: dict, notice_id: Optional[str] = None, ific_no: Optional[int] = None,
                    ific_date: Optional[date] = None, source_ref: str = "") -> TerrestrialNotice:
    """Build a TerrestrialNotice from T11/T12 item keys (t_ prefix optional, case-insensitive)."""
    def k(*names, default=None):
        return _g(items, *[n for base in names for n in (f"t_{base}", base)], default=default)

    lat = _f(k("lat_dec")) if k("lat_dec") is not None else dms_to_decimal(k("lat"))
    lon = _f(k("long_dec")) if k("long_dec") is not None else dms_to_decimal(k("long"))
    pwr_dbw = _f(k("pwr_dbw"))
    pwr_type = str(k("pwr_eiv", default="E"))
    erp, _ = erp_dbw_from_notified(pwr_dbw, pwr_type)
    gain = _f(k("gain_max"))
    gain_type = str(k("gain_type", default="D")).upper()
    gain_dbi = None if gain is None else (gain if gain_type == "I" else gain + 2.15)
    if erp is None and _f(k("pwr_ant")) is not None and gain is not None:
        erp = _f(k("pwr_ant")) + (gain if gain_type == "D" else gain - 2.15)
        pwr_type = "E (from power to antenna + gain)"
    bw = _f(k("bdwdth_khz")) or bandwidth_code_to_khz(k("bdwdth_cde"))
    nat = k("nat_srv", default=[])
    return TerrestrialNotice(
        notice_id=notice_id or str(k("adm_ref_id", "notice_id", default=f"{k('adm')}-{k('freq_assgn')}-{k('site_name', default='')}")),
        adm=str(k("adm", default="")), ctry=str(k("ctry", default=k("adm", default=""))), action=str(k("action", default="ADD")).upper(),
        freq_assgn_mhz=float(k("freq_assgn")), lat=lat, lon=lon, adm_ref_id=str(k("adm_ref_id", default="")),
        stn_cls=str(k("stn_cls", default="")), nat_srv=list(nat) if isinstance(nat, (list, tuple)) else [str(nat)],
        fragment=str(k("fragment", default="NTFD_RR")), prov=str(k("prov", default="RR11.2")), ific_no=ific_no, ific_date=ific_date,
        notice_type=str(k("notice_type", default="T12")), bandwidth_khz=bw, emi_cls=str(k("emi_cls", default="")),
        site_name=str(k("site_name", default="")), site_alt_m=_f(k("site_alt")), erp_dbw=erp, pwr_type=pwr_type,
        ant_dir=str(k("ant_dir", default="ND")).upper(), azm_max_deg=_f(k("azm_max_e", "azm_max")), beamwidth_deg=_f(k("bmwdth")),
        gain_dbi=gain_dbi, hgt_agl_m=_f(k("hgt_agl")), elev_deg=_f(k("elev")), d_inuse=parse_date(k("d_inuse")),
        change_status=str(k("change_status", default="unknown")), source_ref=source_ref or str(k("source_ref", default="")))


def notices_from_rows(rows: Iterable[dict], ific_no: Optional[int] = None, ific_date: Optional[date] = None, source_file: str = "") -> list[TerrestrialNotice]:
    out = []
    for i, r in enumerate(rows):
        out.append(notice_from_t12(r, ific_no=ific_no, ific_date=ific_date, source_ref=f"{source_file or 'terrestrial'} row {i}"))
    return out


# ----------------------------------------------------------------------------- JSON files

def space_groups_from_json(path: str) -> list[SpaceGroup]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    items = data["groups"] if isinstance(data, dict) else data
    out = []
    for d in items:
        d = dict(d)
        d["orbit"] = OrbitInfo(**d.get("orbit", {}))
        d["ific_date"] = parse_date(d.get("ific_date"))
        out.append(SpaceGroup(**d))
    return out


def finnish_networks_from_json(path: str) -> list[FinnishSpaceNetwork]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return [FinnishSpaceNetwork(**d) for d in (data["networks"] if isinstance(data, dict) else data)]


def terrestrial_notices_from_json(path: str) -> list[TerrestrialNotice]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    items = data["notices"] if isinstance(data, dict) else data
    meta = data if isinstance(data, dict) else {}
    out = []
    for d in items:
        d = dict(d)
        if "lat" in d and "freq_assgn_mhz" in d and "t_freq_assgn" not in d:
            d["ific_date"] = parse_date(d.get("ific_date") or meta.get("ific_date"))
            d.setdefault("ific_no", meta.get("ific_no"))
            d["d_inuse"] = parse_date(d.get("d_inuse"))
            out.append(TerrestrialNotice(**d))
        else:
            out.append(notice_from_t12(d, ific_no=meta.get("ific_no"), ific_date=parse_date(meta.get("ific_date")), source_ref=d.get("source_ref", path)))
    return out


def protected_stations_from_json(path: str) -> list[ProtectedStation]:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return [ProtectedStation(**d) for d in (data["stations"] if isinstance(data, dict) else data)]


def protected_stations_from_rows(rows: Iterable[dict], source_ref: str = "special-interest XLS") -> list[ProtectedStation]:
    """Map the synthetic 'frequencies of special interest' sheet (column names are guessed and tolerant)."""
    out = []
    for i, r in enumerate(rows):
        f_c = _f(_g(r, "f_center_mhz", "center_frequency_mhz", "centre_frequency_mhz", "frequency_mhz", "freq_mhz"))
        bw = _f(_g(r, "bandwidth_khz", "bw_khz")) or (_f(_g(r, "bandwidth_mhz")) or 0.025) * 1000.0
        if f_c is None:
            continue
        out.append(ProtectedStation(
            station_id=str(_g(r, "station_id", "station_number", "id", default=f"ST{i + 1}")), name=str(_g(r, "name", "station_name", default=f"station {i + 1}")),
            lat=float(_g(r, "lat", "latitude")), lon=float(_g(r, "lon", "longitude", "long")), f_center_mhz=f_c, bandwidth_khz=bw,
            service=str(_g(r, "service", "usage", default="")), antenna_height_m=_f(_g(r, "antenna_height_m", "antenna_height", "height_m")),
            antenna_azimuth_deg=_f(_g(r, "antenna_azimuth_deg", "antenna_direction", "azimuth")),
            antenna_directivity=str(_g(r, "antenna_directivity", "directivity", default="ND")).upper()[:2].replace("DI", "D"),
            gain_dbi=_f(_g(r, "gain_dbi", "gain")), protection_field_strength_dbuv_m=_f(_g(r, "protection_field_strength_dbuv_m")),
            pfd_limit_dbw_m2=_f(_g(r, "pfd_limit_dbw_m2", "pfd_limit")), source_ref=f"{source_ref} row {i + 1}"))
    return out
