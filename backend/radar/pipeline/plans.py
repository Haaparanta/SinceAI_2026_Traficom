"""Space plans (AP30, AP30A, AP30B): screen an issue against Finland's own plan entries.

Two checks, both deterministic and both citing the plan database rows they rely on:

1. **Bureau examination.** The plan databases hold the Bureau's examination results (sps_results, ap30b_tr_res). A
   network whose results name a Finnish entry as affected is high, with the pfd excess and the degradation as filed.
2. **Orbital-arc pre-screen** [HYPOTHESIS: applied to every co-frequency GSO network, not only to Plan modifications].
   A GSO group co-frequency and co-directional with a Finnish plan entry, whose worst-case orbital spacing to the
   Finnish position is inside the arc of RR Appendix 30 Annex 1 section 1 (less than 9 deg), Appendix 30A Annex 1
   section 4 (less than 9 deg) or Appendix 30B Annex 4 section 1 (7 deg C band, 6 deg Ku band), is medium. The Annex
   pfd test that can clear such a case is not run: the database has no test-point pfd for a non-plan network.

Worst-case spacing = nominal spacing minus the facing East-West station-keeping tolerances of the two satellites
(geo.tol_east / tol_west); a missing tolerance counts as 0 and is said so in the excerpt.

Plan notices whose record the issue published (the AP30B Part A and Part B sections of 3074, for example) become
findings of their own, with the same two checks.
"""
from __future__ import annotations

from dataclasses import dataclass

import duckdb

from radar import schema_map
from radar.adapters import plans as P
from radar.models import CalcTrace, Evidence, Finding, FrequencyGroup, Notice
from radar.pipeline import geography as G

PLAN_PATH = "plan_finnish"


@dataclass
class PlanHit:
    entry: P.PlanEntry
    nominal_deg: float
    worst_deg: float
    lo_hz: int
    hi_hz: int
    tolerance_note: str

    def text(self) -> str:
        a = self.entry.arc
        return (f"co-frequency with the Finnish {self.entry.plan} plan entry {self.entry.satellite} at "
                f"{self.entry.longitude_deg:g} E, worst-case orbital spacing {self.worst_deg:.2f} deg, inside the "
                f"{a.plan} arc ({a.rule_text()}, {a.source})")


def separation(fin_lon: float, fin_te, fin_tw, lon: float, te, tw) -> tuple[float, float, str]:
    """(nominal, worst-case, note). East of the Finnish satellite the facing tolerances are Finnish east and other west."""
    d = ((lon - fin_lon + 180.0) % 360.0) - 180.0
    a, b = (fin_te, tw) if d >= 0 else (fin_tw, te)
    missing = [n for n, v in (("Finnish", a), ("other", b)) if v is None]
    worst = max(0.0, abs(d) - (a or 0.0) - (b or 0.0))
    note = f"tolerance not filed for {' and '.join(missing)} satellite, counted as 0" if missing else "filed tolerances"
    return round(abs(d), 4), round(worst, 4), note


def hits_for(direction: str, lo: int, hi: int, lon: float | None, te, tw, entries: list[P.PlanEntry]) -> list[PlanHit]:
    if lon is None:
        return []
    out = []
    for e in entries:
        if e.direction != direction:
            continue
        olo, ohi = max(lo, e.lo_hz), min(hi, e.hi_hz)
        if ohi <= olo and not (lo == hi and e.lo_hz <= lo < e.hi_hz):
            continue
        nominal, worst, note = separation(e.longitude_deg, e.tol_east_deg, e.tol_west_deg, lon, te, tw)
        if e.arc.within(worst):
            out.append(PlanHit(e, nominal, worst, olo, max(ohi, olo), note))
    return sorted(out, key=lambda h: (h.worst_deg, h.entry.plan, h.entry.group_id))


def nearest_cofrequency(direction: str, lo: int, hi: int, lon: float | None, te, tw,
                        entries: list[P.PlanEntry]) -> tuple[P.PlanEntry, float, float, str] | None:
    """The co-frequency, co-directional Finnish entry with the smallest worst-case spacing, inside the arc or not."""
    best = None
    if lon is None:
        return None
    for e in entries:
        if e.direction != direction or min(hi, e.hi_hz) <= max(lo, e.lo_hz):
            continue
        nominal, worst, note = separation(e.longitude_deg, e.tol_east_deg, e.tol_west_deg, lon, te, tw)
        if best is None or worst < best[2]:
            best = (e, nominal, worst, note)
    return best


def arc_excerpt(e: P.PlanEntry, lon: float, te, tw) -> str:
    nominal, worst, note = separation(e.longitude_deg, e.tol_east_deg, e.tol_west_deg, lon, te, tw)
    inside = e.arc.within(worst)
    return (f"{e.satellite} {e.longitude_deg:g} E vs {lon:g} E: nominal {nominal:.2f} deg, worst case {worst:.2f} deg "
            f"({note}); {e.arc.id} arc {e.arc.rule_text()}: {'inside' if inside else 'outside'}")


def arc_locator(origin: str, notice_id: str, e: P.PlanEntry) -> str:
    """origin: 'ific<issue>' for an IFIC notice, or a plan database tag for a plan notice."""
    return f"plan_arc({origin}:notice_id={notice_id}&entry={P.tag(e.db, e.snapshot)}:{e.group_id}&arc={e.arc.id})"


def tolerances(con: duckdb.DuckDBPyConnection) -> dict[str, tuple]:
    """IFIC notice_id -> (tol_east, tol_west) from the GSO table."""
    M = schema_map.load()
    rows = con.execute(f"SELECT CAST({M.q('space','gso','notice_id')} AS VARCHAR), {M.q('space','gso','tolerance_east_deg')}, "
                       f"{M.q('space','gso','tolerance_west_deg')} FROM {M.t('space','gso')}").fetchall()
    return {n: (te, tw) for n, te, tw in rows}


def apply(rows, notices_by_id: dict, tol: dict[str, tuple], entries: list[P.PlanEntry],
          effects: list[P.BureauEffect]) -> None:
    """Set plan_hits and plan_bureau on every group of an IFIC issue; a hit makes the group a candidate."""
    by_network: dict[str, list[P.BureauEffect]] = {}
    for b in effects:
        by_network.setdefault(b.notice_id, []).append(b)
    for r in rows:
        n = notices_by_id[r.notice_id]
        r.plan_bureau = by_network.get(r.notice_id, [])
        if r.notice_id not in tol or n.longitude_deg is None:   # GSO space stations only (the geo table)
            continue
        te, tw = tol[r.notice_id]
        r.plan_hits = hits_for(r.direction, r.freq_min_hz, r.freq_max_hz, n.longitude_deg, te, tw, entries)
        if r.plan_hits or r.plan_bureau:
            r.paths.setdefault(PLAN_PATH, [])
            r.candidate, r.drop_reason = True, None


def add_entry_evidence(add, e: P.PlanEntry) -> None:
    src = P.source(e.db, e.snapshot)
    add("itu_row", src, e.gso_locator, e.gso_excerpt)
    add("itu_row", src, e.group_locator, e.group_excerpt)
    add("regulation", f"{e.arc.source}, page {e.arc.page} (data/reference/plan_arcs.csv)", f"plan_arcs.csv id={e.arc.id}", e.arc.excerpt())


def add_effect_evidence(add, b: P.BureauEffect) -> None:
    add("itu_row", P.source(b.db, b.snapshot), b.locator, b.excerpt)


# ---- plan notices published in the issue ---------------------------------------------------------------------------

def as_notice(issue: int, pn: P.PlanNotice) -> Notice:
    """A plan notice in the shape of an IFIC Notice, so reports, the screen and the export read it the same way."""
    return Notice(issue=issue, notice_id=pn.notice_id, administration=pn.administration,
                  network_name=pn.satellite or "unknown",
                  special_section=", ".join(pn.sections) or f"{pn.db} {pn.provision or ''}".strip(),
                  orbit="GSO" if pn.longitude_deg is not None else "unknown", longitude_deg=pn.longitude_deg,
                  groups=[FrequencyGroup(group_id=g.group_id, notice_id=pn.notice_id, freq_min_hz=g.lo_hz, freq_max_hz=g.hi_hz,
                                         direction=g.direction, beam_name=g.beam_name,
                                         source_ref=f"{P.tag(pn.db, pn.snapshot)}:grp.grp_id={g.group_id}") for g in pn.groups],
                  source_ref=pn.notice_locator)


def plan_notice_findings(issue: int, notices: list[P.PlanNotice], entries: list[P.PlanEntry],
                         effects: list[P.BureauEffect]) -> list[Finding]:
    by_network: dict[str, list[P.BureauEffect]] = {}
    for b in effects:
        by_network.setdefault(b.notice_id, []).append(b)
    out = []
    for pn in notices:
        ev: list[Evidence] = []

        def add(kind, src, loc, excerpt):
            ev.append(Evidence(id=f"E-{len(ev) + 1:03d}", kind=kind, source=src, locator=loc, excerpt=excerpt))
            return ev[-1].id

        src = P.source(pn.db, pn.snapshot)
        add("itu_row", src, pn.notice_locator, pn.notice_excerpt)
        if pn.gso_locator:
            add("itu_row", src, pn.gso_locator, pn.gso_excerpt)
        mine = by_network.get(pn.notice_id, [])
        hits, near = [], None
        for g in pn.groups:
            hits += [(g, h) for h in hits_for(g.direction, g.lo_hz, g.hi_hz, pn.longitude_deg, pn.tol_east_deg, pn.tol_west_deg, entries)]
            c = nearest_cofrequency(g.direction, g.lo_hz, g.hi_hz, pn.longitude_deg, pn.tol_east_deg, pn.tol_west_deg, entries)
            if c and (near is None or c[2] < near[2]):
                near = c
        geo = G.gso_result(pn.longitude_deg)
        label = f"{pn.db} {', '.join(pn.sections) or pn.provision or ''}".strip()
        if mine:
            for b in mine[:4]:
                add_effect_evidence(add, b)
            b = max(mine, key=lambda x: (x.pfd_excess_db or -999, x.degradation_db or -999))
            concern = "high"
            reason = (f"The Bureau's {pn.db} examination finds the Finnish plan entry {b.finnish_satellite} affected "
                      f"({b.summary()}).")
        elif hits:
            g, h = hits[0]
            add_entry_evidence(add, h.entry)
            add("calculation", "radar.pipeline.plans", arc_locator(P.tag(pn.db, pn.snapshot), pn.notice_id, h.entry),
                arc_excerpt(h.entry, pn.longitude_deg, pn.tol_east_deg, pn.tol_west_deg))
            concern = "medium"
            reason = f"{h.text()[0].upper()}{h.text()[1:]}; the Annex pfd test was not run."
        else:
            concern = "none"
            if near is not None:
                e, nominal, worst, note = near
                add_entry_evidence(add, e)
                add("calculation", "radar.pipeline.plans", arc_locator(P.tag(pn.db, pn.snapshot), pn.notice_id, e),
                    arc_excerpt(e, pn.longitude_deg, pn.tol_east_deg, pn.tol_west_deg))
                why = (f"the nearest co-frequency Finnish plan entry, {e.satellite} at {e.longitude_deg:g} E, is "
                       f"{worst:.2f} deg away, outside the {e.arc.plan} arc ({e.arc.rule_text()})")
            else:
                why = "no group is co-frequency and co-directional with a Finnish plan entry"
            exam = ("; the Bureau's examination of this network names no Finnish entry" if pn.examined
                    else "; no Bureau examination result for this network in the snapshot")
            reason = f"Not raised: {why}{exam}."
        lo = min((g.lo_hz for g in pn.groups), default=None)
        hi = max((g.hi_hz for g in pn.groups), default=None)
        add("calculation", "radar.pipeline.geography", f"geography(plan:{P.tag(pn.db, pn.snapshot)}:notice_id={pn.notice_id})",
            f"{geo.relevance}: {geo.note}")
        out.append(Finding(
            id="", kind="space", issue=issue, notice_id=pn.notice_id, group_id=None,
            overlap_hz=0, geo_relevance=geo.relevance if geo.relevance in ("visible", "low_elevation", "not_visible") else "unknown",
            calc=CalcTrace(method="none", inputs=[], formula="", result_value=None, result_unit="", limit_value=None,
                           limit_evidence_id=None, margin_db=None,
                           notes=[f"{label}: plan section published in IFIC {issue}, read from {P.tag(pn.db, pn.snapshot)}.mdb",
                                  f"frequency span {lo / 1e6:g}-{hi / 1e6:g} MHz over {len(pn.groups)} groups" if lo is not None else "no groups",
                                  "orbital-arc pre-screen only; the Annex pfd and C/I tests are the Bureau's (sps_results, ap30b_tr_res)"]),
            concern=concern, reason=reason, evidence=ev))
    return out
