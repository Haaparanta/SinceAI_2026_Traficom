"""Step C2 of pm_pack/08: Terrestrial IFIC DuckDB -> TerrestrialNotice objects.

Each terrestrial extract is the change set of one issue (checked on 3075 and 3076): every notice carries the
Bureau's intent, which maps to our change field:
    ADD -> new, MODIFY -> modified, SUPPRESS -> withdrawn, RECORDED -> unchanged (recorded in the Master Register)

Site from fxm_geo (POINT or ZONE); antenna from fxm_ant, the transmitting antenna with the highest power.
Power is normalised to e.r.p.: e.i.r.p. (pwr_eiv = I) minus 2.15 dB. Every ITU name comes from schema_map.yaml.

Effective antenna height, the P.1546 h1 input: the notice may file it per azimuth (fxm_ant_hgt, 36 values every
10 deg in 3076, the height above the average terrain 3 to 15 km out in that direction) and as a maximum
(fxm_ant.eff_hgtmax). Both are carried for the chosen antenna; radar.pipeline.terrestrial picks the azimuth.

    uv run python -m radar.adapters.terrestrial_ific 3076
"""
from __future__ import annotations

import sys
from dataclasses import dataclass, field
from pathlib import Path

import duckdb

from radar import schema_map
from radar.config import settings
from radar.models import TerrestrialNotice

KIND = "terrestrial"
CHANGE = {"ADD": "new", "MODIFY": "modified", "SUPPRESS": "withdrawn", "RECORDED": "unchanged"}
EIRP_TO_ERP_DB = 2.15


@dataclass
class NoticeExtra:
    """Fields we need for screening and the report that the frozen TerrestrialNotice contract does not carry."""
    intent: str | None
    notice_type: str | None
    geo_type: str | None
    country: str | None
    power_dbw_filed: float | None
    power_quantity: str | None          # E e.r.p., I e.i.r.p.
    directivity: str | None
    received: str | None
    target: str | None                  # Master Register record a MODIFY or SUPPRESS refers to
    land_mobile: bool = False
    antenna_key: int | None = None
    zone_id: str | None = None          # for ZONE sites: the territory the notice covers
    eff_height_max_m: float | None = None                      # fxm_ant.eff_hgtmax of the chosen antenna
    eff_heights: tuple[tuple[float, float], ...] = ()          # (azimuth deg, effective height m), fxm_ant_hgt


@dataclass
class TerrestrialIngest:
    issue: int
    notices: list[TerrestrialNotice]
    extra: dict[str, NoticeExtra]
    stats: dict = field(default_factory=dict)


def db_path(issue: int) -> Path:
    return settings.derived_dir / f"terrestrial_{issue}.duckdb"


def load(issue: int, con: duckdb.DuckDBPyConnection | None = None) -> TerrestrialIngest:
    M = schema_map.load()
    q = lambda e, c, a=None: M.q(KIND, e, c, a)  # noqa: E731
    own = con is None
    con = con or duckdb.connect(str(db_path(issue)), read_only=True)
    land_mobile = set(M.setting(KIND, "land_mobile_station_classes"))
    rows = con.execute(f"""
        WITH ant AS (
            SELECT {q('antenna','notice_id')} AS tk,
                   arg_max({q('antenna','power_dbw')}, coalesce({q('antenna','power_dbw')}, -999)) AS pwr,
                   arg_max({q('antenna','power_quantity')}, coalesce({q('antenna','power_dbw')}, -999)) AS eiv,
                   arg_max({q('antenna','height_agl_m')}, coalesce({q('antenna','power_dbw')}, -999)) AS hgt,
                   arg_max({q('antenna','azimuth_max_deg')}, coalesce({q('antenna','power_dbw')}, -999)) AS azm,
                   arg_max({q('antenna','directivity')}, coalesce({q('antenna','power_dbw')}, -999)) AS dir,
                   arg_max({q('antenna','antenna_key')}, coalesce({q('antenna','power_dbw')}, -999)) AS akey,
                   arg_max({q('antenna','max_effective_height_m')}, coalesce({q('antenna','power_dbw')}, -999)) AS heffmax
            FROM {M.t(KIND,'antenna')}
            WHERE coalesce({q('antenna','tx_rx')}, 'TX') = 'TX'
            GROUP BY 1),
        tg AS (SELECT {q('target','notice_id')} AS tk, min(CAST({q('target','target')} AS VARCHAR)) AS target
               FROM {M.t(KIND,'target')} GROUP BY 1)
        SELECT CAST({q('notice','notice_id','t')} AS VARCHAR), {q('notice','administration','t')}, {q('notice','intent','t')},
               {q('notice','station_class','t')}, {q('notice','notice_type','t')}, {q('notice','freq_mhz','t')},
               {q('notice','bandwidth_khz','t')}, {q('notice','received','t')},
               {q('site','geo_type','g')}, {q('site','country','g')}, {q('site','site_name','g')}, {q('site','zone_id','g')},
               {q('site','lat_deg','g')}, {q('site','lon_deg','g')},
               ant.pwr, ant.eiv, ant.hgt, ant.azm, ant.dir, tg.target, ant.akey, ant.heffmax
        FROM {M.t(KIND,'notice')} t
        LEFT JOIN {M.t(KIND,'site')} g ON {q('site','geo_key','g')} = {q('notice','geo_key','t')}
        LEFT JOIN ant ON ant.tk = {q('notice','notice_id','t')}
        LEFT JOIN tg ON tg.tk = {q('notice','notice_id','t')}
        ORDER BY 1""").fetchall()
    heights: dict[tuple[str, int], list[tuple[float, float]]] = {}
    for tk, ak, az, h in con.execute(f"""
            SELECT CAST({q('antenna_height','notice_id')} AS VARCHAR), {q('antenna_height','antenna_key')},
                   {q('antenna_height','azimuth_deg')}, {q('antenna_height','effective_height_m')}
            FROM {M.t(KIND,'antenna_height')}
            WHERE {q('antenna_height','azimuth_deg')} IS NOT NULL AND {q('antenna_height','effective_height_m')} IS NOT NULL
            ORDER BY 1, 2, 3""").fetchall():
        heights.setdefault((tk, ak), []).append((float(az), float(h)))
    if own:
        con.close()

    t_notice, c_id = M.table(KIND, "notice"), M.col(KIND, "notice", "notice_id")
    notices, extra = [], {}
    for (tk, adm, intent, cls, ntype, f_mhz, bw_khz, rcv, gtype, ctry, site, zone, lat, lon,
         pwr, eiv, hgt, azm, ant_dir, target, akey, heffmax) in rows:
        erp = None
        if pwr is not None and eiv in ("E", "I"):
            erp = round(float(pwr) - (EIRP_TO_ERP_DB if eiv == "I" else 0.0), 3)
        point = gtype == "POINT"
        notices.append(TerrestrialNotice(
            issue=issue, notice_id=tk, administration=adm or "unknown", change=CHANGE.get(intent, "unchanged"),
            station_class=cls, site_name=site, lat=float(lat) if point and lat is not None else None,
            lon=float(lon) if point and lon is not None else None,
            freq_hz=None if f_mhz is None else int(round(f_mhz * 1e6)),
            bandwidth_hz=None if bw_khz is None else int(round(bw_khz * 1e3)),
            erp_dbw=erp, antenna_height_m=None if hgt is None else float(hgt),
            azimuth_deg=None if azm is None else float(azm), source_ref=f"{t_notice}.{c_id}={tk}",
        ))
        extra[tk] = NoticeExtra(intent, ntype, gtype, ctry, None if pwr is None else float(pwr), eiv, ant_dir,
                                None if rcv is None else str(rcv)[:10], target, land_mobile=cls in land_mobile,
                                antenna_key=akey, zone_id=zone,
                                eff_height_max_m=None if heffmax is None else float(heffmax),
                                eff_heights=tuple(heights.get((tk, akey), ())))
    return TerrestrialIngest(issue, notices, extra, {
        "notices": len(notices), "located": sum(1 for n in notices if n.lat is not None),
        "with_erp": sum(1 for n in notices if n.erp_dbw is not None),
        "land_mobile": sum(1 for e in extra.values() if e.land_mobile),
        "with_effective_heights": sum(1 for e in extra.values() if e.eff_heights),
    })


def main() -> int:
    issue = int(sys.argv[1]) if len(sys.argv) > 1 else 3076
    r = load(issue)
    from collections import Counter
    print(f"terrestrial {issue}: {r.stats}; change {dict(Counter(n.change for n in r.notices))}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
