"""Step C2 of pm_pack/08: what changed in a Terrestrial IFIC, and how it compares with the previous issue.

Each extract is already a change set (radar.adapters.terrestrial_ific), so the per-notice change comes from the
Bureau's intent. The comparison with the previous issue is therefore about trends, not about matching rows:
counts per administration, band and station class, with the difference. A key-based cross-check confirms that
no notice of the current issue refers to a notice of the previous extract (MODIFY and SUPPRESS point into the
Master Register instead), so a row-level diff would find nothing and is not used.
"""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from radar.adapters.terrestrial_ific import TerrestrialIngest

# Land-mobile bands of interest; the first five are the T/R 25-08 Annex 1 bands [SOURCE DATA: T/R 25-08].
BANDS_MHZ = [(29.7, 47), (47, 108), (108, 380), (380, 400), (400, 470), (470, 790), (790, 960), (960, 3000), (3000, 100000)]
NEIGHBOURS = ("S", "NOR", "EST", "RUS")       # ITU symbols of Finland's neighbours [HYPOTHESIS until Q11]


def band_label(freq_hz: int | None) -> str:
    if freq_hz is None:
        return "unknown"
    f = freq_hz / 1e6
    for lo, hi in BANDS_MHZ:
        if lo <= f < hi:
            return f"{lo:g}-{hi:g} MHz"
    return "below 29.7 MHz"


@dataclass
class IssueDiff:
    current: int
    previous: int
    change: Counter                     # change -> count (current issue)
    by_adm: dict[str, Counter]          # adm -> change -> count (current)
    adm_compare: list[tuple[str, int, int]]            # (adm, previous count, current count)
    band_class_compare: list[tuple[str, str, int, int]]  # (band, station class, previous, current), land mobile
    shared_notice_ids: int
    targets_in_previous: int
    neighbours: dict[str, Counter]      # neighbour adm -> change -> count (current)


def compare(cur: TerrestrialIngest, prev: TerrestrialIngest) -> IssueDiff:
    by_adm: dict[str, Counter] = {}
    for n in cur.notices:
        by_adm.setdefault(n.administration, Counter())[n.change] += 1
    prev_adm = Counter(n.administration for n in prev.notices)
    cur_adm = Counter(n.administration for n in cur.notices)
    adms = sorted(set(prev_adm) | set(cur_adm), key=lambda a: -(cur_adm[a] + prev_adm[a]))
    bc_prev = Counter((band_label(n.freq_hz), n.station_class) for n in prev.notices if prev.extra[n.notice_id].land_mobile)
    bc_cur = Counter((band_label(n.freq_hz), n.station_class) for n in cur.notices if cur.extra[n.notice_id].land_mobile)
    keys = sorted(set(bc_prev) | set(bc_cur), key=lambda k: (k[0], k[1] or ""))
    prev_ids = {n.notice_id for n in prev.notices}
    return IssueDiff(
        current=cur.issue, previous=prev.issue, change=Counter(n.change for n in cur.notices), by_adm=by_adm,
        adm_compare=[(a, prev_adm[a], cur_adm[a]) for a in adms],
        band_class_compare=[(b, c or "", bc_prev[(b, c)], bc_cur[(b, c)]) for b, c in keys],
        shared_notice_ids=sum(1 for n in cur.notices if n.notice_id in prev_ids),
        targets_in_previous=sum(1 for e in cur.extra.values() if e.target and e.target in prev_ids),
        neighbours={a: by_adm.get(a, Counter()) for a in NEIGHBOURS},
    )
