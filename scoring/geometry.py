"""Geometry: great-circle distances, Finland polygon tests, GSO/NGSO visibility and coverage.

All functions are pure. Polygons come from reference/finland_region.geojson
(Natural Earth 1:50m, public domain). Distances to polygon edges use a local
equirectangular projection around the query point, accurate to about 1 % for
the few-hundred-kilometre distances that matter for cross-border analysis.
"""
from __future__ import annotations

import json
import math
import os
from functools import lru_cache
from typing import Optional

EARTH_RADIUS_KM = 6371.0
GSO_ALTITUDE_KM = 35786.0
KM_PER_DEG = math.pi * EARTH_RADIUS_KM / 180.0   # 111.19 km

# Finland's latitude span (mainland and Aland), used for NGSO coverage fractions.
FINLAND_LAT_MIN = 59.8
FINLAND_LAT_MAX = 70.1

# Reference points spread over Finnish territory for satellite visibility checks.
FINLAND_REFERENCE_POINTS: list[tuple[str, float, float]] = [
    ("Mariehamn", 60.10, 19.94),
    ("Helsinki", 60.17, 24.94),
    ("Turku", 60.45, 22.27),
    ("Joensuu", 62.60, 29.76),
    ("Vaasa", 63.10, 21.62),
    ("Oulu", 65.01, 25.47),
    ("Rovaniemi", 66.50, 25.73),
    ("Kilpisjarvi", 69.05, 20.79),
    ("Utsjoki", 69.91, 27.03),
]

REFERENCE_DIR = os.path.join(os.path.dirname(__file__), "reference")
REGION_FILE = os.path.join(REFERENCE_DIR, "finland_region.geojson")


# ----------------------------------------------------------------------------- basic spherical maths

def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = p2 - p1
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * EARTH_RADIUS_KM * math.asin(math.sqrt(a))


def initial_bearing_deg(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Bearing from point 1 to point 2, degrees clockwise from true north."""
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    return (math.degrees(math.atan2(x, y)) + 360.0) % 360.0


def angular_difference_deg(a: float, b: float) -> float:
    """Smallest absolute difference between two azimuths, 0..180."""
    d = abs((a - b + 180.0) % 360.0 - 180.0)
    return d


# ----------------------------------------------------------------------------- polygons

def _point_in_ring(lat: float, lon: float, ring: list[list[float]]) -> bool:
    """Ray casting in lon/lat space. ring = [[lon, lat], ...]."""
    inside = False
    n = len(ring)
    j = n - 1
    for i in range(n):
        xi, yi = ring[i][0], ring[i][1]
        xj, yj = ring[j][0], ring[j][1]
        if (yi > lat) != (yj > lat):
            x_cross = (xj - xi) * (lat - yi) / (yj - yi) + xi
            if lon < x_cross:
                inside = not inside
        j = i
    return inside


def _point_in_polygon(lat: float, lon: float, polygon: list[list[list[float]]]) -> bool:
    """polygon = [outer_ring, hole1, hole2, ...]."""
    if not polygon or not _point_in_ring(lat, lon, polygon[0]):
        return False
    for hole in polygon[1:]:
        if _point_in_ring(lat, lon, hole):
            return False
    return True


def _segment_nearest_km(lat: float, lon: float, a: list[float], b: list[float]) -> tuple[float, float, float]:
    """Distance (km) from (lat, lon) to segment a-b (each [lon, lat]) and the nearest point."""
    k = math.cos(math.radians(lat)) * KM_PER_DEG
    ax, ay = (a[0] - lon) * k, (a[1] - lat) * KM_PER_DEG
    bx, by = (b[0] - lon) * k, (b[1] - lat) * KM_PER_DEG
    dx, dy = bx - ax, by - ay
    seg2 = dx * dx + dy * dy
    t = 0.0 if seg2 == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / seg2))
    nx, ny = ax + t * dx, ay + t * dy
    n_lon = lon + nx / k if k else lon
    n_lat = lat + ny / KM_PER_DEG
    return math.hypot(nx, ny), n_lat, n_lon


class Region:
    """Finland and its neighbours as ITU-coded multipolygons."""

    def __init__(self, geojson: dict):
        self.polygons: dict[str, list[list[list[list[float]]]]] = {}
        self.names: dict[str, str] = {}
        self.source = geojson.get("source", "")
        for f in geojson["features"]:
            code = f["properties"]["itu"]
            self.polygons[code] = f["geometry"]["coordinates"]
            self.names[code] = f["properties"].get("name", code)

    @classmethod
    @lru_cache(maxsize=1)
    def load(cls, path: Optional[str] = None) -> "Region":
        with open(path or REGION_FILE, encoding="utf-8") as fh:
            return cls(json.load(fh))

    def contains(self, code: str, lat: float, lon: float) -> bool:
        return any(_point_in_polygon(lat, lon, poly) for poly in self.polygons.get(code, []))

    def country_at(self, lat: float, lon: float) -> Optional[str]:
        for code in self.polygons:
            if self.contains(code, lat, lon):
                return code
        return None

    def distance_to_country_km(self, code: str, lat: float, lon: float) -> tuple[float, float, float]:
        """(distance_km, nearest_lat, nearest_lon). Distance is 0 when the point is inside."""
        if self.contains(code, lat, lon):
            return 0.0, lat, lon
        best = (float("inf"), lat, lon)
        for poly in self.polygons.get(code, []):
            outer = poly[0]
            for i in range(len(outer) - 1):
                d, nlat, nlon = _segment_nearest_km(lat, lon, outer[i], outer[i + 1])
                if d < best[0]:
                    best = (d, nlat, nlon)
        return best

    def path_profile(self, lat1: float, lon1: float, lat2: float, lon2: float, samples: int = 40) -> dict:
        """Classify the great-circle path by land/sea using the loaded country polygons.

        A sample point inside any loaded country polygon is land; otherwise sea.
        Returns land_fraction, sea_fraction and path_type (land | sea | mixed).
        """
        land = 0
        for i in range(samples + 1):
            t = i / samples
            lat = lat1 + (lat2 - lat1) * t
            lon = lon1 + (lon2 - lon1) * t
            if self.country_at(lat, lon) is not None:
                land += 1
        land_fraction = land / (samples + 1)
        if land_fraction >= 0.95:
            path_type = "land"
        elif land_fraction <= 0.15:
            path_type = "sea"
        else:
            path_type = "mixed"
        return {"land_fraction": round(land_fraction, 3), "sea_fraction": round(1 - land_fraction, 3), "path_type": path_type}


def distance_to_finland_km(lat: float, lon: float) -> tuple[float, float, float]:
    return Region.load().distance_to_country_km("FIN", lat, lon)


# ----------------------------------------------------------------------------- GSO geometry

def gso_geometry(lat: float, lon: float, sat_lon: float) -> dict:
    """Elevation angle, slant range and central angle from a ground point to a GSO satellite."""
    phi = math.radians(lat)
    dl = math.radians(sat_lon - lon)
    cos_gamma = math.cos(phi) * math.cos(dl)
    gamma = math.acos(max(-1.0, min(1.0, cos_gamma)))
    r = (EARTH_RADIUS_KM + GSO_ALTITUDE_KM) / EARTH_RADIUS_KM
    elev = math.degrees(math.atan2(cos_gamma - 1.0 / r, math.sin(gamma))) if gamma > 0 else 90.0
    slant = EARTH_RADIUS_KM * math.sqrt(1.0 + r * r - 2.0 * r * cos_gamma)
    return {"elevation_deg": elev, "slant_range_km": slant, "central_angle_deg": math.degrees(gamma)}


def gso_visibility_from_finland(sat_lon: float) -> dict:
    """Best (highest elevation) and lowest-elevation visible reference points for a GSO longitude."""
    pts = []
    for name, lat, lon in FINLAND_REFERENCE_POINTS:
        g = gso_geometry(lat, lon, sat_lon)
        pts.append({"name": name, "lat": lat, "lon": lon, **g})
    pts.sort(key=lambda p: p["elevation_deg"], reverse=True)
    visible = [p for p in pts if p["elevation_deg"] > 0]
    return {"best": pts[0], "lowest_visible": visible[-1] if visible else None, "visible_points": len(visible), "points": pts}


# ----------------------------------------------------------------------------- NGSO geometry

def slant_range_km(altitude_km: float, elev_deg: float) -> float:
    e = math.radians(elev_deg)
    re, h = EARTH_RADIUS_KM, altitude_km
    return math.sqrt((re + h) ** 2 - (re * math.cos(e)) ** 2) - re * math.sin(e)


def ngso_coverage(inclination_deg: float, altitude_km: float, min_elev_deg: float = 0.0) -> dict:
    """Highest latitude a satellite in a circular orbit can see at >= min elevation, and the
    fraction of Finland's latitude span that lies below that limit."""
    i_eff = inclination_deg if inclination_deg <= 90 else 180.0 - inclination_deg
    e = math.radians(min_elev_deg)
    gamma = math.acos((EARTH_RADIUS_KM / (EARTH_RADIUS_KM + altitude_km)) * math.cos(e)) - e
    lat_limit = min(90.0, i_eff + math.degrees(gamma))
    frac = (lat_limit - FINLAND_LAT_MIN) / (FINLAND_LAT_MAX - FINLAND_LAT_MIN)
    return {"lat_limit_deg": lat_limit, "finland_fraction": max(0.0, min(1.0, frac)), "earth_central_angle_deg": math.degrees(gamma)}
