"""Terrestrial findings cite the Finnish table rows their channel overlaps, and Regulation M4 behind the first one.

Plain inputs only: these run without the raw databases.
"""
from __future__ import annotations

from types import SimpleNamespace

from radar.export import results as X
from radar.models import FinnishSubBand, TerrestrialNotice
from radar.pipeline import terrestrial as TR


def band(i, lo_mhz, hi_mhz, services="LAND MOBILE"):
    return FinnishSubBand(id=i, lower_hz=int(lo_mhz * 1e6), upper_hz=int(hi_mhz * 1e6), services_in_finland=services,
                          sub_band_usage="Mobile")


def notice(freq_mhz=152.025, bw_khz=16.8):
    return TerrestrialNotice(issue=3076, notice_id="1", administration="RUS", change="new", station_class="FB",
                             freq_hz=None if freq_mhz is None else int(freq_mhz * 1e6),
                             bandwidth_hz=None if bw_khz is None else int(bw_khz * 1e3), source_ref="x")


BANDS = (band(1, 146, 150), band(2, 150.05, 152.03), band(3, 152.03, 154), band(4, 152.03, 154),   # 4 repeats 3
         band(5, 152.0, 152.1, "FIXED"))


def test_rows_overlapping_the_channel_widest_first_one_per_service_and_limits():
    rows = TR.finnish_rows(notice(), BANDS)
    # channel 152.0166-152.0334 MHz: band 5 covers it all, band 2 the lower 13.4 kHz, band 3 the upper 3.4 kHz
    assert [b.id for b in rows] == [5, 2, 3]


def test_no_frequency_no_rows():
    assert TR.finnish_rows(notice(freq_mhz=None), BANDS) == []


def test_a_channel_without_bandwidth_still_matches_its_row():
    assert [b.id for b in TR.finnish_rows(notice(freq_mhz=148.0, bw_khz=None), BANDS)] == [1]


def test_at_most_six_rows():
    many = tuple(band(i, 152.0, 152.1, f"SERVICE {i}") for i in range(10))
    assert len(TR.finnish_rows(notice(), many)) == TR.MAX_FINNISH_ROWS


def test_results_row_names_the_finnish_match(monkeypatch):
    monkeypatch.setattr(X.traficom_table, "subbands", lambda: BANDS)
    n = notice()
    n.site_name, n.lat, n.lon = "KRL KOSTOMUKSHA", 64.6, 30.8
    calc = SimpleNamespace()
    f = SimpleNamespace(issue=3076, notice_id="1", matched_subband_ids=[5, 2], matched_station_numbers=[], geo_relevance="near_border",
                        calc=SimpleNamespace(method="none", result_value=None, result_unit="", limit_value=None, margin_db=None),
                        concern="low", reason="r", evidence=[SimpleNamespace(locator="fxm_terra.terrakey=1")])
    run = SimpleNamespace(ingest=SimpleNamespace(notices=[n], extra={"1": SimpleNamespace(notice_type="T12", zone_id=None)}),
                          calcs={"1": calc}, result=SimpleNamespace(findings=[f]))
    row = X.terrestrial_rows(run)[0]
    assert row.finnish_match == "FIXED; LAND MOBILE (IDs 5, 2)"
