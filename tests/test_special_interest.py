"""Special-interest station reader (brief section 05; adapters/special_interest.py)."""
from __future__ import annotations

import zipfile
from xml.sax.saxutils import escape

import pytest

from radar.adapters import special_interest as S

HEADER = ["Station number", "Class of licence", "Longitude", "Latitude", "Ground height (m)", "Mast height (m)",
          "Mast type", "Channel bandwidth", "TX frequency", "RX frequency", "Ant height AGL (m)", "Ant height ASL (m)",
          "Ant gain (dB)", "Class of transmission", "Transmission bandwidth", "Radiation direction (°)", "Polarisation",
          "Radioation power", "Radioation power (ITU)", "Radiation power unit", "Transmission line (dB)", "Directivity"]


def _col(i: int) -> str:
    s = ""
    i += 1
    while i:
        i, r = divmod(i - 1, 26)
        s = chr(65 + r) + s
    return s


def write_xlsx(path, rows: list[list], header=HEADER, start_row: int = 11):
    """A minimal workbook: a title line, then the English header, a local-language header and the data rows."""
    all_rows = [(1, ["Traficom / Since AI Hackathon 6.-8.11.2026"]), (start_row, header),
                (start_row + 1, ["Asemanro"] + [""] * (len(header) - 1))]
    all_rows += [(start_row + 2 + i, r) for i, r in enumerate(rows)]
    xml_rows = []
    for n, values in all_rows:
        cells = "".join(f'<c r="{_col(i)}{n}" t="inlineStr"><is><t>{escape(str(v))}</t></is></c>'
                        for i, v in enumerate(values) if v not in (None, ""))
        xml_rows.append(f'<row r="{n}">{cells}</row>')
    sheet = ('<?xml version="1.0" encoding="UTF-8"?><worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
             f'<sheetData>{"".join(xml_rows)}</sheetData></worksheet>')
    with zipfile.ZipFile(path, "w") as z:
        z.writestr("xl/worksheets/sheet1.xml", sheet)
    return path


def row(number, **kw):
    base = {"Station number": number, "Class of licence": "FX", "Longitude": "25.0", "Latitude": "62.0",
            "Ground height (m)": "100", "Channel bandwidth": "5.000 MHz", "TX frequency": "2050 MHz",
            "RX frequency": "2230 MHz", "Ant height AGL (m)": "30", "Ant height ASL (m)": "130",
            "Transmission bandwidth": "5000k", "Radioation power": "10", "Radioation power (ITU)": "E",
            "Radiation power unit": "W", "Directivity": "D"}
    base.update(kw)
    return [base.get(h, "") for h in HEADER]


# ---- unit parsing ------------------------------------------------------------------------------------------------

@pytest.mark.parametrize("text, hz", [("87.900 MHz", 87_900_000), ("5 MHz", 5_000_000), ("0.1 GHz", 100_000_000),
                                      ("7.6 kHz", 7_600), ("1485 kHz", 1_485_000), ("25.2 GHz", 25_200_000_000),
                                      ("", None), (None, None), ("abc", None)])
def test_parse_hz(text, hz):
    assert S.parse_hz(text) == hz


@pytest.mark.parametrize("text, hz", [("300k", 300_000), ("7,6k", 7_600), ("8M00", 8_000_000), ("0,1G", 100_000_000),
                                      ("5000k", 5_000_000), ("118600k", 118_600_000), ("", None), ("x", None)])
def test_parse_itu_bandwidth(text, hz):
    assert S.parse_itu_bandwidth(text) == hz


# ---- rules on a synthetic workbook -------------------------------------------------------------------------------

def test_rules(tmp_path):
    rows = [
        row("1"),                                                           # clean
        row("1"),                                                           # exact duplicate -> excluded
        row("2", **{"RX frequency": ""}),                                   # RX missing -> TX used
        row("3", **{"TX frequency": "", "RX frequency": ""}),               # no frequency -> excluded
        row("4", **{"Channel bandwidth": "", "Transmission bandwidth": "300k"}),
        row("5", **{"Ant height AGL (m)": "0.2"}),                          # raised to 1 m
        row("6", **{"Radiation power unit": ""}),                           # power unknown
        row("7", **{"Ant gain (dB)": "76"}),                                # implausible gain
        row("8", **{"Ant height ASL (m)": "50"}),                           # below ground (100 m)
        row("9", **{"Latitude": "59.0", "Longitude": "18.0"}),              # at sea, west of Aland
        row("2", **{"Class of licence": "BC"}),                             # number repeated, other data
    ]
    res = S.load(write_xlsx(tmp_path / "s.xlsx", rows))
    by = {}
    for s in res.stations:
        by.setdefault(s.station_number, []).append(s)
    assert res.stats["stations"] == 9 and {e.reason for e in res.excluded} == {"exact duplicate of an earlier row", "no TX and no RX frequency"}
    clean = by["1"][0]
    assert (clean.centre_hz, clean.tx_hz, clean.bandwidth_hz, clean.erp_w, clean.quality_flags) == (2_230_000_000, 2_050_000_000, 5_000_000, 10.0, [])
    assert by["2"][0].centre_hz == 2_050_000_000 and "TX frequency" in by["2"][0].quality_flags[0]
    assert by["4"][0].bandwidth_hz == 300_000 and "transmission bandwidth 300k" in by["4"][0].quality_flags[0]
    assert by["5"][0].antenna_height_m == 1.0
    assert by["6"][0].erp_w is None and "no unit" in by["6"][0].quality_flags[0]
    assert by["7"][0].antenna_gain_db == 76 and "implausible" in by["7"][0].quality_flags[0]
    assert "below the ground" in by["8"][0].quality_flags[0]
    assert "outside Finland" in by["9"][0].quality_flags[0]
    assert len(by["2"]) == 2 and "repeated" in by["2"][1].quality_flags[-1]
    assert all(s.source_row for s in res.stations)


def test_columns_are_found_by_header_text_not_position(tmp_path):
    header = list(reversed(HEADER))
    res = S.load(write_xlsx(tmp_path / "r.xlsx", [list(reversed(row("42")))], header=header, start_row=4))
    s = res.stations[0]
    assert (s.station_number, s.centre_hz, s.lat, s.lon) == ("42", 2_230_000_000, 62.0, 25.0)


def test_a_sheet_without_the_header_is_refused(tmp_path):
    p = tmp_path / "bad.xlsx"
    with zipfile.ZipFile(p, "w") as z:
        z.writestr("xl/worksheets/sheet1.xml", '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main"><sheetData/></worksheet>')
    with pytest.raises(ValueError, match="no header row"):
        S.load(p)


# ---- the real file -----------------------------------------------------------------------------------------------

needs_file = pytest.mark.skipif(not S.path().exists(), reason="save the XLS as data/raw/special_interest.xlsx")


@needs_file
def test_the_traficom_file():
    res = S.load()
    assert res.stats["rows"] == 874 and res.stats["stations"] == 870 and res.stats["excluded"] == 4
    assert res.stats["by_class"] == {"FX": 320, "none given": 294, "BC": 115, "MVV": 63, "BT": 56, "MUUT": 22}
    assert res.stats["freq_range_hz"] == [1_485_000, 27_500_000_000]
    # every value comes from the sheet: protected channel inside the TX/RX values filed, positive bandwidth
    assert all(s.bandwidth_hz > 0 and s.centre_hz > 0 and s.source_row > 12 for s in res.stations)
