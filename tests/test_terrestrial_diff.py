"""Step C2 of pm_pack/08: terrestrial adapter and the issue-to-issue diff."""
from __future__ import annotations

import duckdb
import pytest

from radar.adapters import terrestrial_ific as T
from radar.pipeline import diff as D

needs_db = pytest.mark.skipif(not (T.db_path(3075).exists() and T.db_path(3076).exists()), reason="run make convert first")


@pytest.mark.parametrize("hz, label", [(30_000_000, "29.7-47 MHz"), (153_075_000, "108-380 MHz"), (425_825_000, "400-470 MHz"),
                                       (793_500_000, "790-960 MHz"), (415_000, "below 29.7 MHz"), (None, "unknown")])
def test_band_labels(hz, label):
    assert D.band_label(hz) == label


def test_intent_mapping():
    assert T.CHANGE == {"ADD": "new", "MODIFY": "modified", "SUPPRESS": "withdrawn", "RECORDED": "unchanged"}


@pytest.fixture(scope="module")
def issues():
    return T.load(3076), T.load(3075)


@needs_db
def test_counts_match_the_bureau_intents(issues):
    cur, prev = issues
    from collections import Counter
    assert Counter(n.change for n in cur.notices) == {"new": 2905, "modified": 163, "withdrawn": 413, "unchanged": 576}
    assert len(prev.notices) == 8373
    assert cur.stats["land_mobile"] == 1878


@needs_db
def test_every_notice_cites_its_row_and_units_are_sane(issues):
    cur, _ = issues
    for n in cur.notices:
        assert n.source_ref == f"fxm_terra.terrakey={n.notice_id}"
        if n.lat is not None:
            assert -90 <= n.lat <= 90 and -180 <= n.lon <= 180
        if n.freq_hz is not None:
            assert 9_000 <= n.freq_hz <= 300e9


@needs_db
def test_eirp_is_converted_to_erp(issues):
    cur, _ = issues
    with duckdb.connect(str(T.db_path(3076)), read_only=True) as con:
        tk, pwr = con.execute("""SELECT CAST(terrakey AS VARCHAR), max(pwr_dbw) FROM fxm_ant
                                 WHERE pwr_eiv = 'I' AND tx_rx = 'TX' GROUP BY 1 HAVING count(*) = 1 LIMIT 1""").fetchone()
    n = next(n for n in cur.notices if n.notice_id == tk)
    assert n.erp_dbw == pytest.approx(pwr - 2.15, abs=1e-6)


@needs_db
def test_diff_is_a_trend_because_extracts_are_change_sets(issues):
    d = D.compare(*issues)
    assert d.shared_notice_ids == 0 and d.targets_in_previous == 0
    assert sum(c for _, _, c in d.adm_compare) == 4057 and sum(p for _, p, _ in d.adm_compare) == 8373
    assert sum(d.neighbours["RUS"].values()) == 313
    assert d.change["new"] < len(issues[0].notices)          # not every notice classed new


@needs_db
def test_russian_800_mhz_base_stations_near_the_border(issues):
    """Ruskeala and Sortavala FB stations at 793.5 MHz lie within about 15 km of Finland (golden case for C3)."""
    from radar.pipeline.geography import distance_to_finland_km
    cur, _ = issues
    near = [n for n in cur.notices if n.administration == "RUS" and n.station_class == "FB" and n.freq_hz == 793_500_000
            and n.lat is not None and distance_to_finland_km(round(n.lat, 4), round(n.lon, 4)) < 20]
    assert {n.site_name for n in near} >= {"KRL RUSKEALA", "KRL SORTAVALA"}
