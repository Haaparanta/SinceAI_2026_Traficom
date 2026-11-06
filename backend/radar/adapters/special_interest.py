"""Special-interest stations: Traficom_SinceAI_Frequencies_of_interest_v05112026.xlsx -> SpecialInterestStation.

The brief (section 05) makes this table mandatory: synthetic Finnish stations whose frequencies are "in special
interest to be protected". Saved by hand as data/raw/special_interest.xlsx (git-ignored; SPECIAL_INTEREST_XLSX
overrides the path). Read with the standard library (the file is Office Open XML), so no extra dependency.

Columns are found by their English header text (row "Station number ... Directivity"), not by letter, so a reordered
or extended sheet still reads. Rules, every one recorded as a quality flag on the station (rule 3: never invent):

* Protected channel: the RX frequency (the station receives there) +- half the channel bandwidth. When RX is
  missing (58 rows, all at FM or TV frequencies) the TX frequency is used: broadcast listeners receive on it.
* No TX and no RX frequency: the row is excluded, with the reason.
* Channel bandwidth missing: the transmission bandwidth column ("300k", "7,6k", "8M00") is used instead.
* Antenna height above ground below 1 m: raised to 1 m, as the sheet's own note suggests.
* Implausible values kept as filed and flagged: antenna above sea level below the ground, gain above 60 dB,
  position outside Finland (with the distance).
* An exact duplicate row is read once; a repeated station number with different data is kept, flagged.
* Radiated power: value x unit (W, kW, mW) in W; no unit means unknown (None), never a guess.

    uv run python -m radar.adapters.special_interest        # summary of the file
"""
from __future__ import annotations

import os
import re
import sys
import xml.etree.ElementTree as ET
import zipfile
from collections import Counter
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path

from radar.config import settings
from radar.models import SpecialInterestStation

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"
HEADER_MARK = "Station number"
UNIT_HZ = {"Hz": 1.0, "kHz": 1e3, "MHz": 1e6, "GHz": 1e9}
BW_SUFFIX = {"k": 1e3, "M": 1e6, "G": 1e9}             # ITU necessary-bandwidth style: 300k, 7,6k, 8M00, 0,1G
POWER_W = {"W": 1.0, "kW": 1e3, "mW": 1e-3}
MIN_ANTENNA_AGL_M = 1.0
MAX_PLAUSIBLE_GAIN_DB = 60.0

# English header text in the sheet -> our field. Two spellings in the source are kept as printed ("Radioation").
COLUMNS = {
    "Station number": "station", "Class of licence": "licence", "Longitude": "lon", "Latitude": "lat",
    "Ground height (m)": "ground", "Mast height (m)": "mast", "Channel bandwidth": "chan_bw",
    "TX frequency": "tx", "RX frequency": "rx", "Ant height AGL (m)": "agl", "Ant height ASL (m)": "asl",
    "Ant gain (dB)": "gain", "Class of transmission": "emission", "Transmission bandwidth": "tx_bw",
    "Radiation direction (°)": "direction", "Polarisation": "polarisation", "Radioation power": "power",
    "Radioation power (ITU)": "power_kind", "Radiation power unit": "power_unit", "Directivity": "directivity",
}


def path() -> Path:
    return Path(os.environ.get("SPECIAL_INTEREST_XLSX", settings.data_dir / "raw" / "special_interest.xlsx"))


@dataclass
class Excluded:
    row: int
    station_number: str
    reason: str


@dataclass
class StationsResult:
    source: str
    stations: list[SpecialInterestStation]
    excluded: list[Excluded] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


# ---- parsing helpers ---------------------------------------------------------------------------------------------

def _num(text) -> float | None:
    if text is None:
        return None
    t = str(text).strip().replace(",", ".")
    try:
        return float(t)
    except ValueError:
        return None


def parse_hz(text) -> int | None:
    """'87.900 MHz', '5 MHz', '0.1 GHz', '7.6 kHz' -> Hz. None when empty or unreadable."""
    m = re.fullmatch(r"\s*([\d.,]+)\s*(Hz|kHz|MHz|GHz)\s*", str(text or ""))
    if not m:
        return None
    return round(float(m.group(1).replace(",", ".")) * UNIT_HZ[m.group(2)])


def parse_itu_bandwidth(text) -> int | None:
    """ITU necessary-bandwidth notation: '300k' 300 kHz, '7,6k' 7.6 kHz, '8M00' 8 MHz, '0,1G' 100 MHz."""
    m = re.fullmatch(r"\s*(\d*)[.,]?(\d*)([kMG])(\d*)\s*", str(text or ""))
    if not m or not (m.group(1) or m.group(2)):
        return None
    whole, frac_before, unit, frac_after = m.groups()
    frac = frac_before or frac_after
    value = float(f"{whole or 0}.{frac or 0}")
    return round(value * BW_SUFFIX[unit])


FLAG_KINDS = [  # (text the flag starts with or contains, name in summaries)
    ("position outside Finland", "position outside Finland (kept as filed)"),
    ("RX frequency missing", "RX frequency missing: TX frequency protected"),
    ("channel bandwidth missing", "channel bandwidth missing: transmission bandwidth used"),
    ("above ground raised", "antenna below 1 m above ground: raised to 1 m"),
    ("above sea level is below the ground", "antenna above sea level below the ground (kept as filed)"),
    ("antenna gain", "implausible antenna gain over 60 dB (kept as filed)"),
    ("has no unit", "radiated power without a unit: unknown"),
    ("radiated power type", "radiated power not given as e.r.p."),
    ("repeated with different data", "station number repeated with different data"),
]


def flag_kind(flag: str) -> str:
    return next((name for key, name in FLAG_KINDS if key in flag), flag)


def _read_sheet(xlsx: Path) -> list[tuple[int, dict[str, str | None]]]:
    """(row number, {column letter: text}) for every row of the first sheet."""
    with zipfile.ZipFile(xlsx) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(f"{NS}si"):
                shared.append("".join(t.text or "" for t in si.iter(f"{NS}t")))
        sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml")).find(f"{NS}sheetData")
    rows = []
    for r in sheet:
        cells = {}
        for c in r:
            col = re.match(r"[A-Z]+", c.get("r")).group()
            v, inline = c.find(f"{NS}v"), c.find(f"{NS}is")
            if inline is not None:
                cells[col] = "".join(t.text or "" for t in inline.iter(f"{NS}t"))
            elif v is not None:
                cells[col] = shared[int(v.text)] if c.get("t") == "s" else v.text
            else:
                cells[col] = None
        rows.append((int(r.get("r")), cells))
    return rows


def _header(rows) -> tuple[int, dict[str, str]]:
    for n, cells in rows:
        if any((v or "").strip() == HEADER_MARK for v in cells.values()):
            letters = {(v or "").strip(): col for col, v in cells.items()}
            missing = [h for h in ("Station number", "Longitude", "Latitude", "TX frequency", "RX frequency") if h not in letters]
            if missing:
                raise ValueError(f"special-interest sheet: header row {n} lacks {missing}")
            return n, {COLUMNS[h]: col for h, col in letters.items() if h in COLUMNS}
    raise ValueError(f"special-interest sheet: no header row with '{HEADER_MARK}'")


# ---- the reader --------------------------------------------------------------------------------------------------

def load(xlsx: Path | None = None) -> StationsResult:
    from scoring.geometry import Region

    xlsx = Path(xlsx or path())
    rows = _read_sheet(xlsx)
    header_row, col = _header(rows)
    get = lambda cells, key: (cells.get(col[key]) if key in col else None)  # noqa: E731
    region = Region.load()
    # the local-language header sits right under the English one
    data = [(n, c) for n, c in rows if n > header_row + 1 and (get(c, "station") or "").strip()]

    stations: list[SpecialInterestStation] = []
    excluded: list[Excluded] = []
    seen_rows: set[tuple] = set()
    seen_numbers: Counter = Counter()
    for n, cells in data:
        number = str(get(cells, "station")).strip()
        fingerprint = tuple(sorted((k, v) for k, v in cells.items() if v not in (None, "")))
        if fingerprint in seen_rows:
            excluded.append(Excluded(n, number, "exact duplicate of an earlier row"))
            continue
        seen_rows.add(fingerprint)
        flags: list[str] = []

        tx, rx = parse_hz(get(cells, "tx")), parse_hz(get(cells, "rx"))
        if rx is None and tx is None:
            excluded.append(Excluded(n, number, "no TX and no RX frequency"))
            continue
        if rx is None:
            rx = tx
            flags.append("RX frequency missing: protected channel taken from the TX frequency")
        bw = parse_hz(get(cells, "chan_bw"))
        if bw is None:
            bw = parse_itu_bandwidth(get(cells, "tx_bw"))
            if bw is None:
                excluded.append(Excluded(n, number, "no channel or transmission bandwidth"))
                continue
            flags.append(f"channel bandwidth missing: transmission bandwidth {get(cells, 'tx_bw')} used")

        lat, lon = _num(get(cells, "lat")), _num(get(cells, "lon"))
        if lat is None or lon is None:
            excluded.append(Excluded(n, number, "no coordinates"))
            continue
        if not region.contains("FIN", lat, lon):
            d_km = region.distance_to_country_km("FIN", lat, lon)[0]
            flags.append(f"position outside Finland ({d_km:.1f} km from the border; kept as filed)")

        agl, asl, ground = _num(get(cells, "agl")), _num(get(cells, "asl")), _num(get(cells, "ground"))
        if agl is not None and agl < MIN_ANTENNA_AGL_M:
            flags.append(f"antenna height {agl:g} m above ground raised to {MIN_ANTENNA_AGL_M:g} m (sheet note)")
            agl = MIN_ANTENNA_AGL_M
        if asl is not None and ground is not None and asl < ground:
            flags.append(f"antenna {asl:g} m above sea level is below the ground at {ground:g} m (kept as filed)")

        gain = _num(get(cells, "gain"))
        if gain is not None and gain > MAX_PLAUSIBLE_GAIN_DB:
            flags.append(f"antenna gain {gain:g} dB is implausible (kept as filed)")

        power, unit = _num(get(cells, "power")), (get(cells, "power_unit") or "").strip()
        erp_w = power * POWER_W[unit] if power is not None and unit in POWER_W else None
        if power is not None and erp_w is None:
            flags.append(f"radiated power {power:g} has no unit: unknown")
        kind = (get(cells, "power_kind") or "").strip()
        if erp_w is not None and kind and kind != "E":
            flags.append(f"radiated power type '{kind}' is not e.r.p. (E)")

        seen_numbers[number] += 1
        if seen_numbers[number] > 1:
            flags.append(f"station number {number} repeated with different data (row {n})")

        stations.append(SpecialInterestStation(
            station_number=number, centre_hz=rx, bandwidth_hz=bw, lat=lat, lon=lon,
            antenna_height_m=agl, antenna_direction_deg=_num(get(cells, "direction")),
            antenna_directivity=(get(cells, "directivity") or None), tx_hz=tx,
            licence_class=(get(cells, "licence") or None), erp_w=erp_w, antenna_gain_db=gain,
            ground_height_m=ground, source_row=n, quality_flags=flags))

    by_class = Counter(s.licence_class or "none given" for s in stations)
    flag_kinds = Counter(flag_kind(f) for s in stations for f in s.quality_flags)
    stats = {"rows": len(data), "stations": len(stations), "excluded": len(excluded), "header_row": header_row,
             "by_class": dict(by_class.most_common()), "flagged_stations": sum(1 for s in stations if s.quality_flags),
             "flags": dict(flag_kinds.most_common()),
             "freq_range_hz": [min(s.centre_hz for s in stations), max(s.centre_hz for s in stations)]}
    return StationsResult(source=xlsx.name, stations=stations, excluded=excluded, stats=stats)


@lru_cache(maxsize=1)
def stations() -> tuple[SpecialInterestStation, ...]:
    """The stations, or () when the file is not there (the pipeline then reports the table as missing)."""
    p = path()
    return tuple(load(p).stations) if p.exists() else ()


def locator(s: SpecialInterestStation) -> str:
    return f"special_interest.xlsx row {s.source_row} (Station number={s.station_number})"


if __name__ == "__main__":
    res = load(Path(sys.argv[1]) if len(sys.argv) > 1 else None)
    print(res.source, res.stats)
    for e in res.excluded:
        print(f"  excluded row {e.row} station {e.station_number}: {e.reason}")
