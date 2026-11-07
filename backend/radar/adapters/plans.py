"""Space plan databases: Appendix 30/30A (SPS_ALL_IFIC<n>.mdb) and Appendix 30B (30B_<n>.mdb) -> Finnish plan entries,
the Bureau's examination results against them, and the plan notices an IFIC issue published.

Why a separate adapter: the IFIC database leaves every plan table empty (no notice has a plan_id in ific3074.mdb).
The brief names AP30, AP30A and AP30B among the sections to watch; their data is only in the two plan databases on
the ITU Plans pages, which ITU replaces with every issue (only the latest snapshot stays online).

What it reads [SOURCE DATA, checked on snapshot 3083]:

* Finnish plan entries (notice.adm = FIN): FIN10300 and FIN10400 at 22.8 E in the AP30 downlink Plan (11.7-12.5 GHz)
  and the AP30A feeder-link Plan (17.3-18.1 GHz); the AP30B allotment FIN00000 at 46.8 E (4.5-4.8, 6.725-7.025,
  10.70-10.95, 11.20-11.45 and 12.75-13.25 GHz). Each group is clipped to the plan bands of data/reference/plan_arcs.csv.
* Bureau examination results naming a Finnish entry as the affected one: sps_results (pfd excess and equivalent
  protection margin degradation) and ap30b_tr_res (aggregate degradation and pfd excess).
* Plan notices whose record was published in a given issue (notice.wic_no = issue). Caveat: the snapshot holds the
  latest record of each network, so a plan section of an older issue that was later modified carries the later wic_no.

Evidence locators carry the database tag before the table, e.g. SPS_ALL_IFIC3083:grp.grp_id=3412, so the resolver
(radar.evidence_check) opens the right file.

    uv run python -m radar.adapters.plans 3074      # Finnish entries, Bureau results, plan notices of 3074
"""
from __future__ import annotations

import csv
import re
import sys
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

import duckdb

from radar import schema_map
from radar.config import ROOT, settings
from radar.evidence import locator, row_excerpt

KIND = "plans"
DBS = ("AP30", "AP30B")                                  # database keys; AP30 holds both the AP30 and AP30A Plans
PREFIX = {"AP30": "ap30", "AP30B": "ap30b"}              # data/derived/<prefix>_<snapshot>.duckdb
TAG = {"AP30": "SPS_ALL_IFIC{n}", "AP30B": "30B_{n}"}    # ITU file name without .mdb, also the locator prefix
ARCS_FILE = ROOT / "data" / "reference" / "plan_arcs.csv"
FINLAND = "FIN"


# ---- files ---------------------------------------------------------------------------------------------------------

def snapshots(derived: Path | None = None) -> dict[str, int]:
    """Database key -> newest converted snapshot in data/derived (missing keys: not converted yet)."""
    derived = derived or settings.derived_dir
    out = {}
    for db, prefix in PREFIX.items():
        nums = [int(m.group(1)) for p in derived.glob(f"{prefix}_*.duckdb")
                if (m := re.fullmatch(rf"{prefix}_(\d+)\.duckdb", p.name))]
        if nums:
            out[db] = max(nums)
    return out


def db_path(db: str, snapshot: int) -> Path:
    return settings.derived_dir / f"{PREFIX[db]}_{snapshot}.duckdb"


def tag(db: str, snapshot: int) -> str:
    return TAG[db].format(n=snapshot)


def source(db: str, snapshot: int) -> str:
    return f"{tag(db, snapshot)}.mdb (data/derived/{PREFIX[db]}_{snapshot}.duckdb)"


def connect(db: str, snapshot: int) -> duckdb.DuckDBPyConnection:
    return duckdb.connect(str(db_path(db, snapshot)), read_only=True)


def tagged(db: str, snapshot: int, loc: str) -> str:
    return f"{tag(db, snapshot)}:{loc}"


def db_for_tag(t: str) -> tuple[str, int] | None:
    """Inverse of tag(): 'SPS_ALL_IFIC3083' -> ('AP30', 3083)."""
    for db, pattern in TAG.items():
        m = re.fullmatch(pattern.replace("{n}", r"(\d+)"), t)
        if m:
            return db, int(m.group(1))
    return None


# ---- the orbital-arc criteria (RR Appendix 30 Annex 1, 30A Annex 1, 30B Annex 4) ---------------------------------

@dataclass(frozen=True)
class Arc:
    id: str
    plan: str              # AP30 | AP30A | AP30B
    lo_hz: int
    hi_hz: int
    direction: str         # space_to_earth | earth_to_space
    arc_deg: float
    comparison: str        # lt (strictly less than) | le (equal to or less than)
    source: str
    page: str
    excerpt_text: str

    def within(self, separation_deg: float) -> bool:
        return separation_deg < self.arc_deg if self.comparison == "lt" else separation_deg <= self.arc_deg

    def rule_text(self) -> str:
        return f"{'less than' if self.comparison == 'lt' else 'equal to or less than'} {self.arc_deg:g} deg"

    def excerpt(self) -> str:
        return (f"{self.plan} {self.lo_hz / 1e6:g}-{self.hi_hz / 1e6:g} MHz {self.direction}: affected if orbital spacing "
                f"{self.rule_text()} ({self.source}, page {self.page})")


@lru_cache(maxsize=1)
def arcs(path: str = str(ARCS_FILE)) -> tuple[Arc, ...]:
    with open(path, encoding="utf-8", newline="") as fh:
        return tuple(Arc(r["id"], r["plan"], int(round(float(r["band_min_mhz"]) * 1e6)), int(round(float(r["band_max_mhz"]) * 1e6)),
                         r["direction"], float(r["arc_deg"]), r["comparison"], r["source"], r["page"], r["excerpt"])
                     for r in csv.DictReader(fh))


def arc_by_id(arc_id: str) -> Arc | None:
    return next((a for a in arcs() if a.id == arc_id), None)


# ---- Finnish plan entries ------------------------------------------------------------------------------------------

@dataclass
class PlanEntry:
    """One group of a Finnish plan notice, clipped to one plan band."""
    plan: str               # AP30 | AP30A | AP30B
    db: str                 # AP30 | AP30B
    snapshot: int
    notice_id: str
    group_id: str
    satellite: str
    longitude_deg: float
    tol_east_deg: float | None
    tol_west_deg: float | None
    direction: str
    lo_hz: int
    hi_hz: int
    beam_name: str | None
    gain_dbi: float | None
    arc: Arc
    group_locator: str = ""
    group_excerpt: str = ""
    gso_locator: str = ""
    gso_excerpt: str = ""

    def label(self) -> str:
        return f"{self.plan} {self.satellite} ({self.longitude_deg:g} E, {self.lo_hz / 1e6:g}-{self.hi_hz / 1e6:g} MHz)"


def _q(e: str, c: str, a: str | None = None) -> str:
    return schema_map.load().q(KIND, e, c, a)


def _t(e: str) -> str:
    return schema_map.load().t(KIND, e)


def _c(e: str, c: str) -> str:
    return schema_map.load().col(KIND, e, c)


def _direction(code: str | None) -> str:
    # every plan notice is a space-station notice: E = space-to-Earth, R = Earth-to-space (schema_map direction_rule)
    return {"E": "space_to_earth", "R": "earth_to_space"}.get(code or "", "unknown")


def finnish_entries(adm: str = FINLAND, snaps: dict[str, int] | None = None) -> list[PlanEntry]:
    snaps = snaps if snaps is not None else snapshots()
    out: list[PlanEntry] = []
    for db, n in sorted(snaps.items()):
        con = connect(db, n)
        rows = con.execute(f"""
            SELECT {_q('group','group_id','g')}, {_q('group','notice_id','g')}, {_q('group','direction','g')},
                   {_q('group','beam_name','g')}, {_q('group','freq_min_mhz','g')}, {_q('group','freq_max_mhz','g')},
                   {_q('gso','satellite_name','s')}, {_q('gso','longitude_deg','s')},
                   {_q('gso','tolerance_east_deg','s')}, {_q('gso','tolerance_west_deg','s')}, {_q('beam','max_gain_dbi','b')}
            FROM {_t('group')} g
            JOIN {_t('notice')} n ON {_q('notice','notice_id','n')} = {_q('group','notice_id','g')}
            JOIN {_t('gso')} s ON {_q('gso','notice_id','s')} = {_q('group','notice_id','g')}
            LEFT JOIN {_t('beam')} b ON {_q('beam','notice_id','b')} = {_q('group','notice_id','g')}
                 AND {_q('beam','direction','b')} = {_q('group','direction','g')} AND {_q('beam','beam_name','b')} = {_q('group','beam_name','g')}
            WHERE {_q('notice','administration','n')} = ?
            ORDER BY 1""", [adm]).fetchall()
        for gid, nid, code, beam, fmin, fmax, sat, lon, te, tw, gain in rows:
            if fmin is None or fmax is None or lon is None:
                continue
            lo, hi, d = int(round(fmin * 1e6)), int(round(fmax * 1e6)), _direction(code)
            gkey = {_c('group', 'group_id'): gid}
            skey = {_c('gso', 'notice_id'): nid}
            g_loc, s_loc = tagged(db, n, locator(schema_map.load().table(KIND, 'group'), **gkey)), \
                tagged(db, n, locator(schema_map.load().table(KIND, 'gso'), **skey))
            g_ex = row_excerpt(con, schema_map.load().table(KIND, 'group'), gkey,
                               [_c('group', c) for c in ('notice_id', 'direction', 'beam_name', 'freq_min_mhz', 'freq_max_mhz')])
            s_ex = row_excerpt(con, schema_map.load().table(KIND, 'gso'), skey,
                               [_c('gso', c) for c in ('satellite_name', 'longitude_deg', 'tolerance_east_deg', 'tolerance_west_deg')])
            for a in arcs():
                plan_ok = (a.plan == "AP30B") == (db == "AP30B")
                if not plan_ok or a.direction != d or min(hi, a.hi_hz) <= max(lo, a.lo_hz):
                    continue
                out.append(PlanEntry(
                    plan=a.plan, db=db, snapshot=n, notice_id=str(nid), group_id=str(gid), satellite=sat,
                    longitude_deg=round(float(lon), 4), tol_east_deg=te, tol_west_deg=tw, direction=d,
                    lo_hz=max(lo, a.lo_hz), hi_hz=min(hi, a.hi_hz), beam_name=beam,
                    gain_dbi=None if gain is None else round(float(gain), 4), arc=a,
                    group_locator=g_loc, group_excerpt=g_ex or "", gso_locator=s_loc, gso_excerpt=s_ex or ""))
        con.close()
    return out


# ---- Bureau examination results naming a Finnish entry --------------------------------------------------------------

@dataclass
class BureauEffect:
    db: str
    snapshot: int
    notice_id: str                  # the network the Bureau examined
    administration: str
    satellite: str | None
    longitude_deg: float | None
    provision: str | None
    ific_no: int | None             # issue that published this network's record
    finnish_notice_id: str
    finnish_satellite: str | None
    freq_band: str | None
    pfd_excess_db: float | None     # max pfd excess over the Annex criterion (positive = over)
    degradation_db: float | None    # EPM / C/I degradation (AP30) or aggregate degradation (AP30B)
    locator: str = ""
    excerpt: str = ""

    def summary(self) -> str:
        bits = []
        if self.pfd_excess_db is not None:
            bits.append(f"pfd excess {self.pfd_excess_db:.2f} dB")
        if self.degradation_db is not None:
            bits.append(f"degradation {self.degradation_db:.2f} dB")
        return ", ".join(bits) or "affected"


def bureau_effects(adm: str = FINLAND, snaps: dict[str, int] | None = None) -> list[BureauEffect]:
    snaps = snaps if snaps is not None else snapshots()
    out: list[BureauEffect] = []
    M = schema_map.load()
    for db, n in sorted(snaps.items()):
        con = connect(db, n)
        ent = "ap30_results" if db == "AP30" else "ap30b_results"
        tbl = M.table(KIND, ent)
        pfd_cols = ["pfd_excess_max_db"] if db == "AP30" else ["pfd_excess_down_max_db", "pfd_excess_up_max_db"]
        deg_col = "epm_degradation_max_db" if db == "AP30" else "aggregate_degradation_max_db"
        r = lambda c: _q(ent, c, "r")  # noqa: E731
        rows = con.execute(f"""
            SELECT {r('notice_id')}, {r('affected_notice_id')}, {r('freq_band')},
                   {', '.join(r(c) for c in pfd_cols)}, {r(deg_col)},
                   {_q('notice','administration','n')}, {_q('notice','provision','n')}, {_q('notice','ific_no','n')},
                   {_q('gso','satellite_name','s')}, {_q('gso','longitude_deg','s')}, {_q('gso','satellite_name','fs')}
            FROM "{tbl}" r
            JOIN {_t('notice')} n ON {_q('notice','notice_id','n')} = {r('notice_id')}
            LEFT JOIN {_t('gso')} s ON {_q('gso','notice_id','s')} = {r('notice_id')}
            LEFT JOIN {_t('gso')} fs ON {_q('gso','notice_id','fs')} = {r('affected_notice_id')}
            WHERE {r('affected_notice_id')} IN
                  (SELECT {_q('notice','notice_id')} FROM {_t('notice')} WHERE {_q('notice','administration')} = ?)
            ORDER BY 1, 2, r."_row" """, [adm]).fetchall()
        for row in rows:
            nid, fid, band = row[0], row[1], row[2]
            pfds = [v for v in row[3:3 + len(pfd_cols)] if v is not None]
            deg, a, prov, wic, sat, lon, fsat = row[3 + len(pfd_cols):]
            key = {M.col(KIND, ent, 'notice_id'): nid, M.col(KIND, ent, 'affected_notice_id'): fid}
            if band is not None:
                key[M.col(KIND, ent, 'freq_band')] = band
            fields = [M.col(KIND, ent, c) for c in ['freq_band'] + pfd_cols + [deg_col]]
            out.append(BureauEffect(
                db=db, snapshot=n, notice_id=str(nid), administration=a, satellite=sat,
                longitude_deg=None if lon is None else round(float(lon), 4), provision=prov, ific_no=wic,
                finnish_notice_id=str(fid), finnish_satellite=fsat, freq_band=band,
                pfd_excess_db=round(float(max(pfds)), 3) if pfds else None,
                degradation_db=None if deg is None else round(float(deg), 3),
                locator=tagged(db, n, locator(tbl, **key)), excerpt=row_excerpt(con, tbl, key, fields) or ""))
        con.close()
    return out


# ---- plan notices published in an issue ----------------------------------------------------------------------------

@dataclass
class PlanGroup:
    group_id: str
    direction: str
    lo_hz: int
    hi_hz: int
    beam_name: str | None


@dataclass
class PlanNotice:
    db: str
    snapshot: int
    notice_id: str
    administration: str
    satellite: str | None
    longitude_deg: float | None
    tol_east_deg: float | None
    tol_west_deg: float | None
    provision: str | None
    reason: str | None
    ific_no: int
    sections: list[str] = field(default_factory=list)       # e.g. AP30B/A6A 760
    groups: list[PlanGroup] = field(default_factory=list)
    examined: bool = False                                   # the Bureau has examination rows for this network
    notice_locator: str = ""
    notice_excerpt: str = ""
    gso_locator: str = ""
    gso_excerpt: str = ""


def published_in(issue: int, snaps: dict[str, int] | None = None) -> list[PlanNotice]:
    snaps = snaps if snaps is not None else snapshots()
    M = schema_map.load()
    out: list[PlanNotice] = []
    for db, n in sorted(snaps.items()):
        con = connect(db, n)
        res_tbl = M.table(KIND, "ap30_results" if db == "AP30" else "ap30b_results")
        res_nid = M.col(KIND, "ap30_results" if db == "AP30" else "ap30b_results", "notice_id")
        rows = con.execute(f"""
            SELECT {_q('notice','notice_id','n')}, {_q('notice','administration','n')}, {_q('notice','provision','n')},
                   {_q('notice','reason','n')}, {_q('gso','satellite_name','s')}, {_q('gso','longitude_deg','s')},
                   {_q('gso','tolerance_east_deg','s')}, {_q('gso','tolerance_west_deg','s')},
                   EXISTS (SELECT 1 FROM "{res_tbl}" r WHERE r."{res_nid}" = {_q('notice','notice_id','n')})
            FROM {_t('notice')} n LEFT JOIN {_t('gso')} s ON {_q('gso','notice_id','s')} = {_q('notice','notice_id','n')}
            WHERE {_q('notice','ific_no','n')} = ? ORDER BY 1""", [issue]).fetchall()
        for nid, adm, prov, reason, sat, lon, te, tw, examined in rows:
            nkey = {_c('notice', 'notice_id'): nid}
            skey = {_c('gso', 'notice_id'): nid}
            secs = con.execute(f"""SELECT {_q('special_section','reference')}, {_q('special_section','number')}
                                   FROM {_t('special_section')} WHERE {_q('special_section','notice_id')} = ? ORDER BY "seq_no" """,
                               [nid]).fetchall()
            groups = con.execute(f"""SELECT {_q('group','group_id')}, {_q('group','direction')}, {_q('group','freq_min_mhz')},
                                            {_q('group','freq_max_mhz')}, {_q('group','beam_name')}
                                     FROM {_t('group')} WHERE {_q('group','notice_id')} = ? ORDER BY 1""", [nid]).fetchall()
            out.append(PlanNotice(
                db=db, snapshot=n, notice_id=str(nid), administration=adm or "unknown", satellite=sat,
                longitude_deg=None if lon is None else round(float(lon), 4), tol_east_deg=te, tol_west_deg=tw,
                provision=prov, reason=reason, ific_no=issue,
                sections=[f"{r} {num}" if num is not None else r for r, num in secs],
                groups=[PlanGroup(str(g), _direction(d), int(round(lo * 1e6)), int(round(hi * 1e6)), b)
                        for g, d, lo, hi, b in groups if lo is not None and hi is not None],
                examined=bool(examined),
                notice_locator=tagged(db, n, locator(M.table(KIND, 'notice'), **nkey)),
                notice_excerpt=row_excerpt(con, M.table(KIND, 'notice'), nkey,
                                           [_c('notice', c) for c in ('administration', 'plan_id', 'provision', 'reason', 'ific_no')]) or "",
                gso_locator=tagged(db, n, locator(M.table(KIND, 'gso'), **skey)) if sat else "",
                gso_excerpt=(row_excerpt(con, M.table(KIND, 'gso'), skey,
                                         [_c('gso', c) for c in ('satellite_name', 'longitude_deg', 'tolerance_east_deg', 'tolerance_west_deg')]) or "") if sat else "",
            ))
        con.close()
    return out


def main() -> int:
    issue = int(sys.argv[1]) if len(sys.argv) > 1 else 3074
    snaps = snapshots()
    if not snaps:
        print("no plan database converted: run make convert-plans")
        return 1
    print(f"snapshots: {', '.join(f'{tag(d, n)}' for d, n in sorted(snaps.items()))}")
    for e in finnish_entries(snaps=snaps):
        print(f"  Finnish entry {e.label()} beam {e.beam_name} gain {e.gain_dbi} dBi  [{e.group_locator}]")
    for b in bureau_effects(snaps=snaps):
        print(f"  Bureau: {b.administration} {b.satellite} ({b.longitude_deg} E, {b.provision}, IFIC {b.ific_no}) affects "
              f"{b.finnish_satellite}: {b.summary()}")
    for p in published_in(issue, snaps):
        print(f"  published in {issue}: {p.db} {p.administration} {p.satellite} ({p.longitude_deg} E) {p.provision} "
              f"{'; '.join(p.sections)}, {len(p.groups)} groups, examined={p.examined}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
