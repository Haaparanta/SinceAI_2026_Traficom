"""Special-interest stations in the terrestrial screening: co-channel match, P.1546 at the station, concern."""
from __future__ import annotations

import json

import pytest

from radar.adapters import special_interest as SI
from radar.config import settings
from radar.models import SpecialInterestStation, TerrestrialNotice
from radar.pipeline import terrestrial as TR


def notice(freq=415_825_000, bw=25_000, change="new", lat=60.0, lon=28.8, erp=20.0):
    return TerrestrialNotice(issue=3076, notice_id="N1", administration="RUS", change=change, station_class="FB",
                             lat=lat, lon=lon, freq_hz=freq, bandwidth_hz=bw, erp_dbw=erp, antenna_height_m=30.0, source_ref="t")


def station(number, centre, bw=25_000, lat=60.47, lon=26.95, h=30.0):
    return SpecialInterestStation(station_number=number, centre_hz=centre, bandwidth_hz=bw, lat=lat, lon=lon,
                                  antenna_height_m=h, source_row=100)


@pytest.fixture
def stations(monkeypatch):
    def use(items):
        monkeypatch.setattr(SI, "stations", lambda: tuple(items))
    return use


def test_co_channel_means_overlapping_channels(stations):
    stations([station("A", 415_825_000), station("B", 415_850_000), station("C", 415_840_000, bw=10_000)])
    assert [s.station_number for s in TR.co_channel_stations(notice())] == ["A", "C"]


def test_field_strength_at_the_station_uses_its_antenna_height(stations):
    inland = dict(lat=61.0, lon=27.5)
    stations([station("LOW", 415_825_000, h=2.0, **inland), station("HIGH", 415_825_000, h=60.0, **inland)])
    res = {s["number"]: s for s in TR.station_checks(notice(), 30.0, 20.0)}
    assert res["HIGH"]["e_dbuv_m"] > res["LOW"]["e_dbuv_m"] and res["HIGH"]["h2_m"] == 60.0
    assert res["LOW"]["margin_db"] == pytest.approx(20.0 - res["LOW"]["e_dbuv_m"], abs=0.01)


def test_a_low_antenna_next_to_sea_is_raised_to_the_p1546_minimum(stations):
    stations([station("SEA", 415_825_000, h=2.0, lat=60.2, lon=27.4)])          # Gulf of Finland, off Kotka
    [r] = TR.station_checks(notice(), 30.0, 20.0)
    assert r["h2_m"] == 3.0 and "raised to 3 m" in r["h2_source"] and r["segments"][-1][1] != "Land"


def test_stations_beyond_the_p1546_limit_are_left_out(stations):
    stations([station("FAR", 415_825_000, lat=69.9, lon=27.0)])
    assert TR.station_checks(notice(lat=50.0, lon=30.0), 30.0, 20.0) == []


def test_a_station_over_the_trigger_decides_the_concern():
    n = notice()
    c = TR.TerrestrialCalc("computed", "", distance_km=40.0, e_dbuv_m=10.0, trigger_dbuv_m=20.0, margin_db=10.0,
                           threshold=TR.thresholds()[4])
    c.stations = [{"number": "A", "distance_km": 120.0, "e_dbuv_m": 25.0, "margin_db": -5.0, "h2_m": 30.0}]
    level, reason = TR.concern(n, c)
    assert level == "high" and "(decides)" in reason and TR.station_decides(n, c)
    c.stations[0].update(e_dbuv_m=5.0, margin_db=15.0)
    level, reason = TR.concern(n, c)
    assert level == "low" and "(decides)" not in reason and "15 dB below the trigger" in reason


CACHE = settings.data_dir / "cache" / "terrestrial_3076.json"
needs = pytest.mark.skipif(not (CACHE.exists() and SI.path().exists()), reason="needs the cache and the XLS")


@needs
def test_3076_station_evidence():
    b = json.loads(CACHE.read_text())
    rows = SI.by_row()
    with_st = [f for f in b["result"]["findings"] if f["matched_station_numbers"]]
    assert len(with_st) == 24
    for f in with_st:
        cited = [e for e in f["evidence"] if e["kind"] == "special_interest_row"]
        assert 1 <= len(cited) <= 5 and all(e["excerpt"] == SI.excerpt(rows[int(e["locator"].split("=")[1])]) for e in cited)
        assert any(e["locator"].startswith("p1546_station(") for e in f["evidence"])
        assert len(b["context"][f["id"]]["stations"]) == len(f["matched_station_numbers"])
