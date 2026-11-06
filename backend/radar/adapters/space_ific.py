"""Step B1 of pm_pack/08: Space IFIC DuckDB -> Notice and FrequencyGroup objects.

Every ITU name comes from schema_map.yaml. Missing values stay None (rule 3: unknown stays unknown).

Scope: by default only groups published in this issue (grp.wic_no == issue) are screened, plus any earlier group of
a notice in this issue where the Bureau lists Finland as an affected administration (provn.adm = 'FIN'): the Bureau's
own finding is never left out (3074: SECOMSAT-5-78E, CR/C 6344, has its Finland-affecting UHF groups in IFIC 3060).
Other groups published in earlier issues are returned in `excluded` with the reason, so nothing disappears silently.

Direction: grp.emi_rcp describes the notified station. For space-station notices (G, N) E means space-to-Earth;
for earth-station notices (S) E means Earth-to-space. Checked on 3074 against the usual satellite bands
(see schema_map.yaml, direction_rule).

    uv run python -m radar.adapters.space_ific 3074
"""
from __future__ import annotations

import math
import sys
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path

import duckdb

from radar import schema_map
from radar.config import settings
from radar.models import FrequencyGroup, Notice

KIND = "space"
# Main special section for each notification reason; the others published with it are companions.
MAIN_SECTION_FOR_REASON = {"A": "API/A", "C": "CR/C", "U": "RES49"}
PART_NAMES = {"1": "Part I-S", "2": "Part II-S", "3": "Part III-S"}


@dataclass
class Excluded:
    group_id: str
    notice_id: str
    reason: str


@dataclass
class Anomaly:
    """A value kept exactly as filed but implausible; downstream calculations must not use it silently."""
    group_id: str
    notice_id: str
    field: str
    value: float
    reason: str
    cross_check: str
    source_ref: str


@dataclass
class IngestResult:
    issue: int
    notices: list[Notice]
    excluded: list[Excluded]
    special_sections: dict[str, list[str]] = field(default_factory=dict)   # notice_id -> every section published
    anomalies: list[Anomaly] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


def db_path(issue: int) -> Path:
    return settings.derived_dir / f"space_{issue}.duckdb"


# Plausible range for a declared maximum power density at the antenna input [HYPOTHESIS: wide on purpose,
# 3074 has -103.2 to -3 dBW/Hz apart from one +73]. Outside it, the value is kept as filed and flagged.
PD_PLAUSIBLE_DBW_HZ = (-120.0, 20.0)
_BW_UNITS = {"H": 1.0, "K": 1e3, "M": 1e6, "G": 1e9}


def necessary_bandwidth_hz(designation: str | None) -> float | None:
    """Necessary bandwidth from an ITU emission designation such as 8M00G2D-- (8 MHz) or 2K40 (2.4 kHz)."""
    if not designation or len(designation) < 4:
        return None
    code = designation[:4]
    for i, ch in enumerate(code):
        if ch in _BW_UNITS:
            try:
                return float(code[:i] + "." + code[i + 1:]) * _BW_UNITS[ch]
            except ValueError:
                return None
    return None


def _fmt_bw(hz: float) -> str:
    for unit, div in (("GHz", 1e9), ("MHz", 1e6), ("kHz", 1e3)):
        if hz >= div:
            return f"{hz / div:g} {unit}"
    return f"{hz:g} Hz"


def mhz_to_hz(v: float | None) -> int | None:
    return None if v is None else int(round(v * 1_000_000))


def direction(emi_rcp: str | None, ntc_type: str | None, M: schema_map.SchemaMap) -> str:
    rule = M.setting(KIND, "direction_rule")
    if emi_rcp not in ("E", "R"):
        return "unknown"
    if ntc_type in rule["space_station_types"]:
        return "space_to_earth" if emi_rcp == "E" else "earth_to_space"
    if ntc_type in rule["earth_station_types"]:
        return "earth_to_space" if emi_rcp == "E" else "space_to_earth"
    return "unknown"


def _as_date(v) -> date | None:
    if v is None:
        return None
    return v.date() if isinstance(v, datetime) else v


def load(issue: int, include_earlier_groups: bool = False, con: duckdb.DuckDBPyConnection | None = None) -> IngestResult:
    M = schema_map.load()
    own = con is None
    con = con or duckdb.connect(str(db_path(issue)), read_only=True)
    q = lambda e, c, a=None: M.q(KIND, e, c, a)  # noqa: E731

    # --- notices with their orbit, name and longitude ---------------------------------------------------------
    notices_sql = f"""
        SELECT {q('notice','notice_id','n')}, {q('notice','administration','n')}, {q('notice','orbit_code','n')},
               {q('notice','reason','n')}, {q('notice','ific_part','n')}, {q('notice','received','n')},
               {q('gso','satellite_name','g')}, {q('gso','longitude_deg','g')},
               {q('non_gso','satellite_name','ng')},
               {q('earth_station_notice','station_name','es')}, {q('earth_station_notice','satellite_name','es')},
               {q('earth_station_notice','satellite_longitude_deg','es')}
        FROM {M.t(KIND,'notice')} n
        LEFT JOIN {M.t(KIND,'gso')} g ON {q('gso','notice_id','g')} = {q('notice','notice_id','n')}
        LEFT JOIN {M.t(KIND,'non_gso')} ng ON {q('non_gso','notice_id','ng')} = {q('notice','notice_id','n')}
        LEFT JOIN {M.t(KIND,'earth_station_notice')} es ON {q('earth_station_notice','notice_id','es')} = {q('notice','notice_id','n')}
        ORDER BY 1
    """
    notice_rows = con.execute(notices_sql).fetchall()

    # --- special sections per notice ----------------------------------------------------------------------------
    sections: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for ntc, ref, no, rev, rev_no in con.execute(f"""
        SELECT {q('special_section','notice_id')}, {q('special_section','reference')}, {q('special_section','number')},
               {q('special_section','revision')}, {q('special_section','revision_no')}
        FROM {M.t(KIND,'special_section')} ORDER BY 1, "seq_no" """).fetchall():
        label = f"{ref} {no}" + (f" {rev}{rev_no or ''}" if rev else "")
        sections[str(ntc)].append((ref, label))

    # --- groups with max power density and the beam gain -------------------------------------------------------
    groups_sql = f"""
        WITH pd AS (
            SELECT {q('emission','group_id')} AS gid, max({q('emission','max_power_density_dbw_hz')}) AS pd,
                   arg_max({q('emission','peak_power_dbw')}, {q('emission','max_power_density_dbw_hz')}) AS pep,
                   arg_max({q('emission','designation')}, {q('emission','max_power_density_dbw_hz')}) AS emi
            FROM {M.t(KIND,'emission')} GROUP BY 1),
        sa AS (
            SELECT {q('service_area','group_id')} AS gid, list(DISTINCT {q('service_area','country')} ORDER BY 1) AS areas
            FROM {M.t(KIND,'service_area')} GROUP BY 1)
        SELECT {q('group','group_id','gr')}, {q('group','notice_id','gr')}, {q('group','direction','gr')},
               {q('group','beam_name','gr')}, {q('group','freq_min_mhz','gr')}, {q('group','freq_max_mhz','gr')},
               {q('group','ific_no','gr')}, pd.pd, coalesce({q('beam','max_gain_dbi','b')}, {q('earth_antenna','max_gain_dbi','ea')}),
               sa.areas, gr."_row", pd.pep, pd.emi
        FROM {M.t(KIND,'group')} gr
        LEFT JOIN pd ON pd.gid = {q('group','group_id','gr')}
        LEFT JOIN sa ON sa.gid = {q('group','group_id','gr')}
        LEFT JOIN {M.t(KIND,'beam')} b ON {q('beam','notice_id','b')} = {q('group','notice_id','gr')}
             AND {q('beam','direction','b')} = {q('group','direction','gr')} AND {q('beam','beam_name','b')} = {q('group','beam_name','gr')}
        LEFT JOIN {M.t(KIND,'earth_antenna')} ea ON {q('earth_antenna','notice_id','ea')} = {q('group','notice_id','gr')}
             AND {q('earth_antenna','direction','ea')} = {q('group','direction','gr')} AND {q('earth_antenna','beam_name','ea')} = {q('group','beam_name','gr')}
        ORDER BY 2, 1
    """
    group_rows = con.execute(groups_sql).fetchall()
    from radar.pipeline.relevance import finland_named
    bureau_named = set(finland_named(con))
    if own:
        con.close()

    ntc_type = {str(r[0]): r[2] for r in notice_rows}
    t_group, c_gid = M.table(KIND, "group"), M.col(KIND, "group", "group_id")
    groups_by_notice: dict[str, list[FrequencyGroup]] = defaultdict(list)
    excluded: list[Excluded] = []
    anomalies: list[Anomaly] = []
    t_emiss, c_pd = M.table(KIND, "emission"), M.col(KIND, "emission", "max_power_density_dbw_hz")
    for gid, nid, emi_rcp, beam, fmin, fmax, wic_no, pd, gain, areas, _row, pep, emi in group_rows:
        gid, nid = str(gid), str(nid)
        if not include_earlier_groups and wic_no != issue and gid not in bureau_named:
            excluded.append(Excluded(gid, nid, f"published in an earlier issue (wic_no={wic_no})"))
            continue
        lo, hi = mhz_to_hz(fmin), mhz_to_hz(fmax)
        if lo is None or hi is None:
            excluded.append(Excluded(gid, nid, "frequency range missing"))
            continue
        if lo > hi:
            excluded.append(Excluded(gid, nid, f"freq_min above freq_max ({fmin} > {fmax} MHz)"))
            continue
        if pd is not None and not PD_PLAUSIBLE_DBW_HZ[0] <= pd <= PD_PLAUSIBLE_DBW_HZ[1]:
            bw = necessary_bandwidth_hz(emi)
            implied = None if pep is None or not bw else pep - 10 * math.log10(bw)
            anomalies.append(Anomaly(
                group_id=gid, notice_id=nid, field="power_density_dbw_hz", value=round(float(pd), 4),
                reason=f"outside the plausible range {PD_PLAUSIBLE_DBW_HZ[0]:g} to {PD_PLAUSIBLE_DBW_HZ[1]:g} dBW/Hz",
                cross_check=(f"peak power {pep:g} dBW over the necessary bandwidth of {emi} ({_fmt_bw(bw)}) implies about "
                             f"{implied:.1f} dBW/Hz" if implied is not None else "no peak power or bandwidth to cross-check"),
                source_ref=f"{t_emiss}.{M.col(KIND, 'emission', 'group_id')}={gid} ({c_pd})",
            ))
        groups_by_notice[nid].append(FrequencyGroup(
            group_id=gid, notice_id=nid, freq_min_hz=lo, freq_max_hz=hi,
            direction=direction(emi_rcp, ntc_type.get(nid), M),
            beam_name=beam, power_density_dbw_hz=None if pd is None else round(float(pd), 4),
            max_gain_dbi=None if gain is None else round(float(gain), 4),
            service_area_codes=list(areas or []),
            source_ref=f"{t_group}.{c_gid}={gid}",
        ))

    t_notice, c_nid = M.table(KIND, "notice"), M.col(KIND, "notice", "notice_id")
    notices: list[Notice] = []
    all_sections: dict[str, list[str]] = {}
    for (nid, adm, otype, reason, part, received, gso_name, gso_long, ngso_name, es_name, es_sat, es_long) in notice_rows:
        nid = str(nid)
        secs = sections.get(nid, [])
        all_sections[nid] = [label for _, label in secs]
        main = MAIN_SECTION_FOR_REASON.get(reason or "")
        special = next((label for ref, label in secs if ref == main), secs[0][1] if secs else PART_NAMES.get(part or ""))
        if otype == "G":
            orbit, longitude, name = "GSO", gso_long, gso_name
        elif otype == "N":
            orbit, longitude, name = "NGSO", None, ngso_name
        elif otype == "S":
            orbit, longitude = ("GSO", es_long) if es_long is not None else ("unknown", None)
            name = f"{es_name} (earth station for {es_sat})" if es_name and es_sat else es_name
        else:
            orbit, longitude, name = "unknown", None, None
        notices.append(Notice(
            issue=issue, notice_id=nid, administration=adm or "unknown", network_name=name or "unknown",
            special_section=special, orbit=orbit,
            longitude_deg=None if longitude is None else round(float(longitude), 4),
            received=_as_date(received), groups=groups_by_notice.get(nid, []),
            source_ref=f"{t_notice}.{c_nid}={nid}",
        ))

    kept = sum(len(n.groups) for n in notices)
    return IngestResult(issue=issue, notices=notices, excluded=excluded, special_sections=all_sections,
                        anomalies=anomalies, stats={
        "notices": len(notices), "notices_in_db": len(notice_rows),
        "groups_in_db": len(group_rows), "groups_kept": kept, "groups_excluded": len(excluded),
        "include_earlier_groups": include_earlier_groups, "anomalies": len(anomalies),
    })


def main() -> int:
    issue = int(sys.argv[1]) if len(sys.argv) > 1 else 3074
    r = load(issue)
    print(f"space {issue}: {r.stats}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
