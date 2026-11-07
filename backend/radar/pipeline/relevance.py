"""Step B2 of pm_pack/08: frequency relevance of every frequency group against the Finnish table.

Rules from pm_pack/06 "Relevance rules" [HYPOTHESIS until partner question Q1 is answered]:

| Group direction | Finnish row class          | Path                       | Candidate? |
|-----------------|----------------------------|----------------------------|------------|
| space-to-Earth  | terrestrial                | pfd_terrestrial (main)     | yes        |
| space-to-Earth  | passive (radio astronomy)  | passive_service            | yes        |
| space-to-Earth  | space, downlink or both    | space_cofrequency          | yes (coordination review, no pfd limit, Q8) |
| space-to-Earth  | no Finnish row (table gap) | uncovered                  | yes (unknown, never "no concern") |
| Earth-to-space  | terrestrial / space / passive | uplink_*                | informational; geography decides later |
| any             | special-interest station   | special_interest           | yes, at least medium (XLS still WAITING) |
| GSO, same sense | Finnish AP30/30A/30B plan entry inside the Annex orbital arc | plan_finnish (set by pipeline.plans) | yes, medium |

Overlap is computed on Hz integers with the formula max(0, min(g.hi, s.hi) - max(g.lo, s.lo)) per row, and the
group total is the union of matched rows (several Finnish rows often describe one band), never their sum.
Finnish rows are classified from Services_in_Finland: CAPITALS mean primary, normal case secondary [SOURCE DATA:
the M4 table convention, checked on the 2026-11-06 snapshot].
"""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field

import duckdb
import pyarrow as pa

from radar.adapters import traficom_table
from radar.models import FinnishSubBand, FrequencyGroup, Notice, SpecialInterestStation

CANDIDATE_PATHS = ("special_interest", "pfd_terrestrial", "passive_service", "space_cofrequency", "uncovered",
                   "uplink_near_finland", "uplink_near_station", "plan_finnish")
INFORMATIONAL_PATHS = ("uplink_terrestrial", "uplink_space", "uplink_passive", "uplink_uncovered")


@dataclass(frozen=True)
class RowClass:
    category: str          # terrestrial | space | passive | not_allocated
    space_direction: str | None   # downlink | uplink | both | None
    primary: bool


def classify(services: str) -> RowClass:
    s = services.strip()
    u = s.upper()
    primary = s == u
    if "NOT ALLOCATED" in u:
        return RowClass("not_allocated", None, False)
    if "RADIO ASTRONOMY" in u or "(PASSIVE)" in u:
        return RowClass("passive", None, primary)
    if any(k in u for k in ("SATELLITE", "SPACE RESEARCH", "SPACE OPERATION")):
        down, up = "SPACE-TO-EARTH" in u, "EARTH-TO-SPACE" in u
        direction = "downlink" if down and not up else "uplink" if up and not down else "both"
        return RowClass("space", direction, primary)
    return RowClass("terrestrial", None, primary)


def path_for(direction: str, rc: RowClass) -> str | None:
    if direction == "space_to_earth":
        if rc.category == "terrestrial":
            return "pfd_terrestrial"
        if rc.category == "passive":
            return "passive_service"
        if rc.category == "space" and rc.space_direction in ("downlink", "both"):
            return "space_cofrequency"
        return None   # s2e over a Finnish uplink-only or not-allocated row: no co-directional victim
    if direction == "earth_to_space":
        if rc.category == "terrestrial":
            return "uplink_terrestrial"
        if rc.category == "space":
            return "uplink_space"
        if rc.category == "passive":
            return "uplink_passive"
    return None


@dataclass
class GroupRelevance:
    group_id: str
    notice_id: str
    direction: str
    freq_min_hz: int
    freq_max_hz: int
    matched_subband_ids: list[int]
    overlap_hz: int                       # union of matched Finnish rows inside the group
    uncovered_hz: int                     # part of the group no Finnish row covers
    paths: dict[str, list[int]]           # path -> sub-band IDs that produced it ([] for uncovered)
    primary_terrestrial: bool             # at least one primary terrestrial row on the pfd path
    matched_station_numbers: list[str] = field(default_factory=list)   # stations whose RX channel overlaps the group
    station_reach: dict[str, dict] = field(default_factory=dict)        # station number -> geometry (geography.apply)
    finland_named_provisions: list[str] = field(default_factory=list)   # Bureau lists FIN as affected (provn)
    plan_hits: list = field(default_factory=list)      # pipeline.plans.PlanHit: inside the arc of a Finnish plan entry
    plan_bureau: list = field(default_factory=list)    # adapters.plans.BureauEffect: Bureau finds a Finnish entry affected
    geo_relevance: str = "unknown"        # set by geography.apply (B3)
    geo_note: str = ""
    candidate: bool = False
    drop_reason: str | None = None


def _union_length(intervals: list[tuple[int, int]]) -> int:
    total, cur_lo, cur_hi = 0, None, None
    for lo, hi in sorted(intervals):
        if cur_hi is None or lo > cur_hi:
            if cur_hi is not None:
                total += cur_hi - cur_lo
            cur_lo, cur_hi = lo, hi
        else:
            cur_hi = max(cur_hi, hi)
    return total + (cur_hi - cur_lo if cur_hi is not None else 0)


def finland_named(con: duckdb.DuckDBPyConnection, administration: str = "FIN") -> dict[str, list[str]]:
    """group_id -> provisions under which the Bureau lists Finland as an affected administration (provn)."""
    from radar import schema_map

    M = schema_map.load()
    rows = con.execute(f"""
        SELECT {M.q('space','affected','group_id')}, list(DISTINCT {M.q('space','affected','provision')} ORDER BY 1)
        FROM {M.t('space','affected')} WHERE {M.q('space','affected','administration')} = ? GROUP BY 1""",
                       [administration]).fetchall()
    return {str(g): list(p) for g, p in rows}


def screen(notices: list[Notice], bands: tuple[FinnishSubBand, ...] | None = None,
           stations: list[SpecialInterestStation] | None = None,
           named: dict[str, list[str]] | None = None) -> list[GroupRelevance]:
    """named: output of finland_named(); groups where the Bureau names Finland are always candidates."""
    bands = bands or traficom_table.subbands()
    stations = stations or []
    named = named or {}
    groups: list[FrequencyGroup] = [g for n in notices for g in n.groups]
    by_id = {b.id: b for b in bands}
    classes = {b.id: classify(b.services_in_finland) for b in bands}

    # Interval join in DuckDB (IEJoin): 25 k groups x 6 k rows in well under a second on the M1.
    con = duckdb.connect()
    con.register("g", pa.table({"gid": [g.group_id for g in groups], "lo": [g.freq_min_hz for g in groups],
                                "hi": [g.freq_max_hz for g in groups]}))
    con.register("b", pa.table({"bid": [b.id for b in bands], "lo": [b.lower_hz for b in bands],
                                "hi": [b.upper_hz for b in bands]}))
    pairs = con.execute("""
        SELECT g.gid, b.bid FROM g JOIN b
          ON (g.lo < b.hi AND g.hi > b.lo) OR (g.lo = g.hi AND g.lo >= b.lo AND g.lo < b.hi)""").fetchall()
    con.close()
    hits: dict[str, list[int]] = defaultdict(list)
    for gid, bid in pairs:
        hits[gid].append(bid)
    # Special-interest stations: the protected channel is the RX frequency +- half the channel bandwidth.
    station_hits: dict[str, list[str]] = defaultdict(list)
    if stations:
        con = duckdb.connect()
        con.register("g", pa.table({"gid": [g.group_id for g in groups], "lo": [g.freq_min_hz for g in groups],
                                    "hi": [g.freq_max_hz for g in groups]}))
        con.register("s", pa.table({"k": list(range(len(stations))),
                                    "lo": [s.centre_hz - s.bandwidth_hz // 2 for s in stations],
                                    "hi": [s.centre_hz + s.bandwidth_hz // 2 for s in stations]}))
        for gid, k in con.execute("""
                SELECT g.gid, s.k FROM g JOIN s
                  ON (g.lo < s.hi AND g.hi > s.lo) OR (g.lo = g.hi AND g.lo >= s.lo AND g.lo < s.hi)
                ORDER BY g.gid, s.k""").fetchall():
            station_hits[gid].append(stations[k].station_number)
        con.close()

    out = []
    for g in groups:
        ids = sorted(hits.get(g.group_id, []))
        width = g.freq_max_hz - g.freq_min_hz
        clipped = [(max(g.freq_min_hz, by_id[i].lower_hz), min(g.freq_max_hz, by_id[i].upper_hz)) for i in ids]
        covered = _union_length(clipped) if width else (1 if ids else 0)
        uncovered = max(width - covered, 0) if width else (0 if ids else 1)
        paths: dict[str, list[int]] = defaultdict(list)
        for i in ids:
            p = path_for(g.direction, classes[i])
            if p:
                paths[p].append(i)
        if uncovered > 0:
            paths["uncovered" if g.direction == "space_to_earth" else "uplink_uncovered"] = []
        st = list(dict.fromkeys(station_hits.get(g.group_id, [])))
        if st:
            paths["special_interest"] = []
        r = GroupRelevance(
            group_id=g.group_id, notice_id=g.notice_id, direction=g.direction,
            freq_min_hz=g.freq_min_hz, freq_max_hz=g.freq_max_hz, matched_subband_ids=ids,
            overlap_hz=covered if width else 0, uncovered_hz=uncovered, paths=dict(paths),
            primary_terrestrial=any(classes[i].primary for i in paths.get("pfd_terrestrial", [])),
            matched_station_numbers=st, finland_named_provisions=named.get(g.group_id, []),
        )
        r.candidate = any(p in r.paths for p in CANDIDATE_PATHS) or bool(r.finland_named_provisions)
        if not r.candidate:
            if g.direction == "unknown":
                r.drop_reason = "direction unknown"
            elif g.direction == "earth_to_space":
                r.drop_reason = "Earth-to-space: informational until geography (B3)"
            else:
                r.drop_reason = "space-to-Earth over Finnish uplink-only or unallocated rows"
        out.append(r)
    return out


def funnel(rows: list[GroupRelevance], by: str = "group",
           station_hits: dict[str, list[str]] | None = None) -> list[tuple[str, int]]:
    """Counts per stage, by group or by notice (a notice counts once if any of its groups qualifies).

    station_hits: group_id -> special-interest stations the group overlaps in frequency, from a screen with the
    stations (the B2 report screens without them so its funnel and hand-check cases stay frequency-only)."""
    hits = station_hits if station_hits is not None else {r.group_id: r.matched_station_numbers for r in rows}

    def n(pred) -> int:
        if by == "group":
            return sum(1 for r in rows if pred(r))
        return len({r.notice_id for r in rows if pred(r)})

    return [
        ("Screened", n(lambda r: True)),
        ("Overlap a Finnish sub-band or a table gap", n(lambda r: r.matched_subband_ids or r.uncovered_hz)),
        ("Space-to-Earth (reaches Finnish receivers)", n(lambda r: r.direction == "space_to_earth")),
        ("Candidate (space-to-Earth concern path, or Bureau names Finland)", n(lambda r: r.candidate)),
        ("  over a Finnish terrestrial row (pfd path)", n(lambda r: "pfd_terrestrial" in r.paths)),
        ("  over a primary terrestrial row", n(lambda r: r.primary_terrestrial)),
        ("  Bureau names Finland as affected (provn)", n(lambda r: r.finland_named_provisions)),
        ("  overlap a special-interest station (frequency, before geography)", n(lambda r: hits.get(r.group_id))),
    ]
