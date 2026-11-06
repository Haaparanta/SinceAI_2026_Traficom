"""Step B1 of pm_pack/08: the space adapter. Data tests skip when data/derived/space_3074.duckdb is absent."""
from __future__ import annotations

import duckdb
import pytest

from radar import schema_map
from radar.adapters import space_ific as S

DB = S.db_path(3074)
needs_db = pytest.mark.skipif(not DB.exists(), reason="run make convert first")


# ---- pure logic ---------------------------------------------------------------------------------------------

@pytest.mark.parametrize("emi_rcp, ntc_type, expected", [
    ("E", "G", "space_to_earth"), ("R", "G", "earth_to_space"),
    ("E", "N", "space_to_earth"), ("R", "N", "earth_to_space"),
    ("E", "S", "earth_to_space"), ("R", "S", "space_to_earth"),   # earth-station notices flip [CHECKED 3074]
    ("X", "G", "unknown"), (None, "G", "unknown"), ("E", "R", "unknown"),
])
def test_direction_depends_on_the_notified_station(emi_rcp, ntc_type, expected):
    assert S.direction(emi_rcp, ntc_type, schema_map.load()) == expected


@pytest.mark.parametrize("designation, hz", [
    ("8M00G2D--", 8e6), ("14M0F2D--", 14e6), ("2K40J3E", 2.4e3), ("100HA1A", 100.0), ("1G20", 1.2e9),
    ("", None), (None, None), ("ABCD", None),
])
def test_necessary_bandwidth_from_emission_designation(designation, hz):
    assert S.necessary_bandwidth_hz(designation) == hz


def test_mhz_to_hz_is_exact_for_filed_values():
    assert S.mhz_to_hz(6011.5) == 6_011_500_000
    assert S.mhz_to_hz(137.03) == 137_030_000
    assert S.mhz_to_hz(None) is None


def test_every_name_used_exists_in_schema_map():
    M = schema_map.load()
    for entity in ("notice", "special_section", "gso", "non_gso", "earth_station_notice", "group", "emission",
                   "beam", "earth_antenna", "service_area"):
        assert M.table("space", entity)


# ---- real data ----------------------------------------------------------------------------------------------

@pytest.fixture(scope="module")
def result():
    return S.load(3074)


@needs_db
def test_counts_reconcile_with_the_database(result):
    st = result.stats
    assert st["notices"] == 196
    assert st["groups_in_db"] == 34365
    assert st["groups_kept"] == 25127   # 25 105 published in 3074 + 22 earlier groups the Bureau names Finland in
    assert st["groups_kept"] + st["groups_excluded"] == st["groups_in_db"]


@needs_db
def test_every_group_is_valid_and_cites_its_row(result):
    for n in result.notices:
        assert n.source_ref == f"notice.ntc_id={n.notice_id}"
        for g in n.groups:
            assert g.freq_min_hz <= g.freq_max_hz
            assert g.source_ref == f"grp.grp_id={g.group_id}"
            assert g.direction != "unknown"


@needs_db
def test_power_density_is_never_invented(result):
    """Groups with no pd in our objects must be exactly the groups whose emissions have no pd in the file."""
    ours = {g.group_id for n in result.notices for g in n.groups if g.power_density_dbw_hz is None}
    with duckdb.connect(str(DB), read_only=True) as con:
        theirs = {str(r[0]) for r in con.execute("""
            SELECT g.grp_id FROM grp g LEFT JOIN emiss e USING (grp_id)
            WHERE g.wic_no = 3074 GROUP BY 1 HAVING max(e.pwr_ds_max) IS NULL""").fetchall()}
    assert ours == theirs


@needs_db
def test_implausible_source_value_is_kept_and_flagged(result):
    """IND network LVI files +73 dBW/Hz; pep -4 dBW over 8 MHz implies about -73. Keep as filed, flag it."""
    [a] = [a for a in result.anomalies if a.group_id == "126662625"]
    assert a.value == 73.0
    assert "-73.0 dBW/Hz" in a.cross_check
    g = next(g for n in result.notices for g in n.groups if g.group_id == "126662625")
    assert g.power_density_dbw_hz == 73.0


@needs_db
def test_special_sections_follow_the_notification_reason(result):
    by_id = {n.notice_id: n for n in result.notices}
    assert by_id["113520154"].special_section == "CR/C 3407 M2"       # published with CR/D 5360
    assert result.special_sections["113520154"] == ["CR/D 5360", "CR/C 3407 M2"]
    sections = {n.special_section.split(" ")[0] for n in result.notices if n.special_section and n.special_section[0] != "P"}
    assert sections == {"CR/C", "API/A", "RES49"}


@needs_db
def test_gso_longitudes_and_west_sign(result):
    gso = [n for n in result.notices if n.orbit == "GSO" and n.longitude_deg is not None]
    assert gso and all(-180 <= n.longitude_deg <= 180 for n in gso)
    assert any(n.longitude_deg < 0 for n in gso)
