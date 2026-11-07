"""Broadcasting extension (GE84 FM, GE06 TV): reading, reach, triggers, concern, evidence."""
from __future__ import annotations

import pytest

from radar.adapters import terrestrial_ific as T
from radar.models import TerrestrialNotice
from radar.pipeline import broadcasting as BR

needs_db = pytest.mark.skipif(not T.db_path(3076).exists(), reason="run make convert first")


def notice(cls="BC", freq=99_000_000, change="new", lat=60.0, lon=31.0, erp=40.0):
    return TerrestrialNotice(issue=3076, notice_id="N1", administration="RUS", change=change, station_class=cls, site_name="X",
                             lat=lat, lon=lon, freq_hz=freq, bandwidth_hz=300_000, erp_dbw=erp, antenna_height_m=150.0,
                             source_ref="t")


def extra():
    return T.NoticeExtra(intent="ADD", notice_type="T01", geo_type="POINT", country="RUS", power_dbw_filed=40.0,
                         power_quantity="E", directivity="ND", received=None, target=None, eff_height_max_m=200.0)


@pytest.fixture
def triggers(tmp_path, monkeypatch):
    def use(rows):
        p = tmp_path / "ge.csv"
        p.write_text("id,f_min_mhz,f_max_mhz,system,trigger_dbuv_m,time_pct,h_rx_m,source,page,review,notes\n"
                     + "".join(f"{r}\n" for r in rows))
        monkeypatch.setattr(BR, "TRIGGERS_FILE", p)
        BR.triggers.cache_clear()
    yield use
    BR.triggers.cache_clear()


def test_system_of():
    assert BR.system_of(notice("BC"), False) == "fm" and BR.system_of(notice("BT"), True) == "dvbt"
    assert BR.system_of(notice("BT"), False) == "atv" and BR.system_of(notice("BT"), None) == "other"


def test_trigger_lookup_by_system_and_band(triggers):
    triggers(["FM,87.5,108,fm,20,1,10,src,1,ok,", "TV,470,862,dvbt,25,1,10,src,2,ok,"])
    assert BR.trigger_for(notice("BC"), False).id == "FM"
    assert BR.trigger_for(notice("BT", 618_000_000), True).id == "TV"
    assert BR.trigger_for(notice("BT", 618_000_000), False) is None


def test_far_withdrawn_finnish_and_unlocated_notices_are_not_computed():
    assert BR.evaluate(notice(lat=46.4, lon=48.0), extra(), False).status == "not_applicable"
    assert BR.evaluate(notice(change="withdrawn"), extra(), False).status == "not_applicable"
    assert BR.evaluate(notice(lat=None, lon=None), extra(), False).status == "no_input"
    fin = notice()
    fin.administration = "FIN"
    assert BR.evaluate(fin, extra(), False).status == "not_applicable"


def test_near_notice_over_the_trigger_is_high(triggers):
    triggers(["FM,87.5,108,fm,0,1,10,src,1,ok,"])        # a deliberately low trigger: a 40 dBW FM station 30 km away exceeds it
    n = notice(lat=60.6, lon=28.6)                       # just across the border from south-east Finland
    c = BR.evaluate(n, extra(), False)
    level, reason = BR.concern(n, c)
    assert c.status == "computed" and c.border.margin_db < 0 and level == "high" and "exceeds the FM trigger" in reason


def test_without_a_trigger_the_field_strength_is_reported_and_nothing_is_invented(triggers):
    triggers([])
    n = notice(lat=60.6, lon=28.6)
    c = BR.evaluate(n, extra(), False)
    level, reason = BR.concern(n, c)
    assert c.trigger is None and c.border.margin_db is None and "criterion needed" in reason and level == "review"


@needs_db
def test_3076_reads_every_fm_and_tv_notice_and_every_citation_reopens():
    from radar import evidence_check as EC
    run = BR.run(3076)
    assert run.result.screened == 562 == len(run.ingest.notices)
    assert all(f.reason for f in run.result.findings)
    assert all(c.border is None or c.border.distance_km <= 1000 for c in run.calcs.values())
    assert all(c.status == "PASS" for c in EC.check_broadcasting(run.result))


def test_ge06_triggers_equal_the_transcription_of_table_a11():
    """data/reference/ge_triggers.csv against the independent transcription of GE06 Table A.1.1 (page image)."""
    import csv
    import json
    from pathlib import Path
    ref = Path(__file__).resolve().parents[1] / "data" / "reference"
    tr = json.loads((ref / "review" / "ge_triggers_transcription.json").read_text())["values"]
    a11 = [v for v in tr if v["agreement"] == "GE06" and "A.1.1" in v["table"]]
    rows = [r for r in csv.DictReader((ref / "ge_triggers.csv").open()) if r["id"].startswith("GE06_")]
    assert len(rows) == 8
    for r in rows:
        prefix = "Interferer = DVB-T" if r["system"] == "dvbt" else "Interferer = Analogue TV"
        band = [int(float(r["f_min_mhz"])), int(float(r["f_max_mhz"]))]
        match = [v for v in a11 if v["service_or_system"].startswith(prefix) and [int(x) for x in v["band_or_range_mhz"]] == band]
        assert len(match) == 1 and float(match[0]["trigger_dbuv_m"]) == float(r["trigger_dbuv_m"]), r["id"]
        assert float(r["time_pct"]) == 1 and float(r["h_rx_m"]) == 10
