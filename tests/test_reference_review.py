"""Second review of the hand-typed limit tables (pm_pack/06 rule 5; build plan C1 and C3).

data/reference/review/ holds two transcriptions made independently of the CSVs, from the rendered page images of the
sources (RR 2024 Vol. 1 Table 21-4; T/R 25-08 edition of 6 June 2025). These tests fail if a limit or threshold in
the CSVs ever differs from them, so a later edit cannot slip through unreviewed. Method and findings:
data/reference/review/README.md.
"""
from __future__ import annotations

import csv
import json
import math
import re
from pathlib import Path

import pytest

REF = Path(__file__).resolve().parents[1] / "data" / "reference"
RR = json.loads((REF / "review" / "rr_table21_4_transcription.json").read_text())["rows"]
TR = json.loads((REF / "review" / "tr2508_transcription.json").read_text())["values"]
PFD = list(csv.DictReader((REF / "pfd_limits.csv").open(encoding="utf-8")))
THR = list(csv.DictReader((REF / "tr2508_thresholds.csv").open(encoding="utf-8")))
GRID = [i / 4 for i in range(361)]          # 0 to 90 degrees in quarter-degree steps


def _expr(text: str):
    """A printed limit such as '−154 + 0.5(δ − 5)' or '−127 + (4/3)(δ − 5)' as a function of the angle."""
    s = text.split("[")[0].split("(value")[0].replace("−", "-").replace("δ", "d").strip()
    s = re.sub(r"(\d)\s*\(", r"\1*(", s)
    s = re.sub(r"\)\s*\(", ")*(", s)
    s = re.sub(r"(\d)d", r"\1*d", s)
    return lambda d: eval(s, {"math": math, "Y": 0}, {"d": d})   # noqa: S307 (fixed, committed input)


def _angles(a: str) -> tuple[float, float]:
    n = [float(x) for x in re.findall(r"\d+(?:\.\d+)?", a)]
    return (0.0, 90.0) if "single" in a else (n[0], n[1])


def _rr(row: dict, which: int):
    segs = [(*_angles(lim["angle_range"]), _expr(lim["limit"].split(" and ")[which] if " and " in lim["limit"] else lim["limit"]))
            for lim in row["limits"]]
    return lambda d: next(e(d) for lo, hi, e in segs if lo <= d <= hi)


def _ours(row: dict):
    segs = [tuple(float(x) for x in s.split("|")) for s in row["segments"].split(";")]
    return lambda d: next(b + k * (d - r) for lo, hi, b, k, r in segs if lo <= d <= hi)


def _bw(text: str) -> int:
    return 4000 if "4 kHz" in text else 1_500_000 if "1.5 MHz" in text else 1_000_000


def _candidates(row: dict) -> list[tuple[dict, int]]:
    """RR entries of the same orbit and reference bandwidth that overlap the CSV band."""
    lo, hi, orbit, bw = float(row["band_min_mhz"]), float(row["band_max_mhz"]), row["orbit"], int(row["ref_bw_hz"])
    out = []
    for r in RR:
        if min(hi, r["band_max_mhz"]) - max(lo, r["band_min_mhz"]) <= 0:
            continue
        q = (r["service_qualifier"] or "") + r["service"]
        if (orbit == "GSO" and "non-geostationary" in q) or (orbit == "NGSO" and "(geostationary" in q):
            continue
        both = " and " in r["reference_bandwidth"]
        if not both and _bw(r["reference_bandwidth"]) != bw:
            continue
        out.append((r, (1 if bw == 1_000_000 else 0) if both else 0))
    return out


@pytest.mark.parametrize("row", PFD, ids=[r["id"] for r in PFD])
def test_pfd_limit_equals_the_independent_transcription(row):
    ours = _ours(row)
    cands = _candidates(row)
    # the CSV band must be covered by RR entries whose limits agree at every angle
    agreeing = [(r, w) for r, w in cands if max(abs(ours(d) - _rr(r, w)(d)) for d in GRID) < 1e-6]
    assert agreeing, f"{row['id']}: no RR entry with the same limit"
    lo, hi = float(row["band_min_mhz"]), float(row["band_max_mhz"])
    edges = sorted({lo, hi} | {e for r, _ in agreeing for e in (r["band_min_mhz"], r["band_max_mhz"]) if lo < e < hi})
    covered = all(any(r["band_min_mhz"] <= a and b <= r["band_max_mhz"] for r, _ in agreeing) for a, b in zip(edges, edges[1:]))
    assert covered, f"{row['id']}: part of {lo}-{hi} MHz has no agreeing RR entry"
    pages = {int(r["printed_page"].split()[0]) for r, _ in agreeing}
    assert int(row["page"]) in pages, f"{row['id']}: page {row['page']} but the row is printed on {sorted(pages)}"


def test_every_tr2508_threshold_equals_annex_1():
    annex1 = {(v["freq_min_mhz"], v["freq_max_mhz"]): v for v in TR if v["section"].startswith("Annex 1")}
    assert len(annex1) == len(THR) == 5
    for t in THR:
        v = annex1[(float(t["f_min_mhz"]), float(t["f_max_mhz"]))]
        assert float(t["threshold_dbuv_m"]) == float(v["field_strength"])
        assert (float(t["h_rx_m"]), float(t["time_pct"]), float(t["location_pct"])) == (v["receiver_height_m"], v["time_pct"], v["locations_pct"])
        assert "25 kHz" in v["reference_bandwidth"] and float(t["ref_bw_khz"]) == 25 and v["distance_km"] == 0
