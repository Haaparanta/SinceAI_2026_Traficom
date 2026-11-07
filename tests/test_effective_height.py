"""P.1546 h1 from the notice's own filed effective heights (fxm_ant_hgt per azimuth, fxm_ant.eff_hgtmax)."""
from __future__ import annotations

import pytest

from radar.adapters import terrestrial_ific as T
from radar.models import TerrestrialNotice
from radar.pipeline import terrestrial as TR

needs_db = pytest.mark.skipif(not T.db_path(3076).exists(), reason="run make convert first")
RING = tuple((float(az), float(az) / 10.0) for az in range(0, 360, 10))       # height = azimuth / 10


def notice(agl=30.0, cls="FB"):
    return TerrestrialNotice(issue=3076, notice_id="N1", administration="RUS", change="new", station_class=cls,
                             lat=60.0, lon=30.0, freq_hz=415_825_000, bandwidth_hz=25_000, erp_dbw=20.0,
                             antenna_height_m=agl, source_ref="t")


def extra(**kw):
    return T.NoticeExtra(intent="ADD", notice_type="T12", geo_type="POINT", country="RUS", power_dbw_filed=20.0,
                         power_quantity="E", directivity="ND", received=None, target=None, land_mobile=True, **kw)


def test_interpolation_between_filed_azimuths():
    assert TR.interpolate_azimuth(RING, 20.0) == (2.0, (20.0,))
    h, used = TR.interpolate_azimuth(RING, 25.0)
    assert h == pytest.approx(2.5) and used == (20.0, 30.0)


def test_interpolation_wraps_around_north():
    ring = ((0.0, 10.0), (350.0, 30.0)) + tuple((float(a), 0.0) for a in range(10, 350, 10))
    h, used = TR.interpolate_azimuth(ring, 355.0)
    assert h == pytest.approx(20.0) and used == (350.0, 0.0)


def test_h1_prefers_the_filed_height_towards_the_receiver():
    # due west of (60 N, 30 E) is bearing about 270 deg -> 27 m from the ring
    h = TR.h1_for(notice(), extra(eff_heights=RING, eff_height_max_m=80.0), 60.0, 29.0, sea_in_path=False)
    assert h.value_m == pytest.approx(27.0, abs=0.5) and h.source.startswith("filed effective height towards the receiver")
    assert h.azimuths and 260.0 <= h.azimuths[0] <= 280.0


def test_h1_falls_back_to_maximum_then_above_ground_then_default():
    assert TR.h1_for(notice(), extra(eff_height_max_m=80.0), 60.0, 29.0, False).value_m == 80.0
    h = TR.h1_for(notice(agl=30.0), extra(), 60.0, 29.0, False)
    assert h.value_m == 30.0 and "hgt_agl" in h.source
    h = TR.h1_for(notice(agl=None, cls="ML"), extra(), 60.0, 29.0, False)
    assert h.value_m == 1.5 and "[hypothesis]" in h.source


def test_negative_effective_height_kept_on_land_and_raised_to_1_m_over_sea():
    ring = tuple((float(a), -15.0) for a in range(0, 360, 10))
    assert TR.h1_for(notice(), extra(eff_heights=ring), 60.0, 29.0, sea_in_path=False).value_m == -15.0
    h = TR.h1_for(notice(), extra(eff_heights=ring), 60.0, 29.0, sea_in_path=True)
    assert h.value_m == 1.0 and "Annex 5 section 4.2" in h.source


@needs_db
def test_3076_notices_with_filed_heights_use_them():
    ing = T.load(3076)
    filed = [n for n in ing.notices if ing.extra[n.notice_id].eff_heights]
    assert len(filed) == 32 and all(len(ing.extra[n.notice_id].eff_heights) == 36 for n in filed)
    computed = [(n, c) for n in filed if (c := TR.evaluate(n, ing.extra[n.notice_id])).status == "computed"]
    assert computed and all(c.heff_source.startswith("filed effective height") for _, c in computed)


def test_short_land_path_blends_ha_and_heff_like_the_engine():
    from radar.calc.p1546 import field_strength, short_path_h1

    assert short_path_h1(2.0, 11.6, 36.0) == 36.0
    assert short_path_h1(9.0, 12.0, 36.0) == pytest.approx(24.0)
    assert short_path_h1(20.0, 12.0, 36.0) == 12.0
    # the engine with (heff, ha) equals the engine with h1 already blended
    blended = field_strength(415.0, [(9.0, "Land")], 24.0, 10.0)
    engine = field_strength(415.0, [(9.0, "Land")], 12.0, 10.0, ha_m=36.0)
    assert engine.e_dbuv_m == pytest.approx(blended.e_dbuv_m, abs=0.01)
    assert any("Annex 5 section 3.1.1" in n for n in engine.notes)
