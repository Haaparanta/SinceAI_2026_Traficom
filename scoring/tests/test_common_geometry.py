import math
import unittest

from scoring import common, geometry
from scoring.config import load_config


class CommonTests(unittest.TestCase):
    def test_overlap_and_gap(self):
        self.assertEqual(common.overlap_mhz(100, 200, 150, 250), 50)
        self.assertEqual(common.overlap_mhz(100, 200, 200, 250), 0)
        self.assertEqual(common.gap_mhz(100, 200, 210, 250), 10)
        self.assertEqual(common.gap_mhz(100, 200, 150, 250), 0)

    def test_bin_lookup(self):
        bins = [[0, 1.0], [6, 0.8], [15, 0.5], [None, 0.05]]
        self.assertEqual(common.bin_lookup(-3, bins), 1.0)
        self.assertEqual(common.bin_lookup(0, bins), 1.0)
        self.assertEqual(common.bin_lookup(5.9, bins), 0.8)
        self.assertEqual(common.bin_lookup(100, bins), 0.05)

    def test_combine_and_priority(self):
        cfg = load_config()
        self.assertEqual(common.combine_score(1, 1, 1, cfg), 100)
        self.assertEqual(common.combine_score(0, 1, 1, cfg), 0)
        self.assertEqual(common.combine_score(0.5, 1, 1, cfg), 50)
        self.assertEqual(common.priority_from_score(70, cfg), "A")
        self.assertEqual(common.priority_from_score(69, cfg), "B")
        self.assertEqual(common.priority_from_score(19, cfg), "D")

    def test_ramp(self):
        self.assertEqual(common.ramp(5, 0, 10), 0.5)
        self.assertEqual(common.ramp(-1, 0, 10), 0.0)
        self.assertEqual(common.ramp(20, 0, 10), 1.0)


class GeometryTests(unittest.TestCase):
    def test_haversine_helsinki_tallinn(self):
        d = geometry.haversine_km(60.17, 24.94, 59.44, 24.75)
        self.assertTrue(75 < d < 90, d)

    def test_gso_elevation_helsinki_13e(self):
        g = geometry.gso_geometry(60.17, 24.94, 13.0)
        self.assertAlmostEqual(g["elevation_deg"], 21.0, delta=0.5)
        self.assertTrue(39000 < g["slant_range_km"] < 40000)

    def test_gso_not_visible_far_east(self):
        vis = geometry.gso_visibility_from_finland(128.0)
        self.assertEqual(vis["visible_points"], 0)

    def test_ngso_coverage(self):
        self.assertEqual(geometry.ngso_coverage(53, 550)["finland_fraction"], 1.0)
        self.assertEqual(geometry.ngso_coverage(30, 500)["finland_fraction"], 0.0)
        part = geometry.ngso_coverage(42, 550)["finland_fraction"]
        self.assertTrue(0 < part < 1, part)
        self.assertEqual(geometry.ngso_coverage(98, 550)["finland_fraction"], 1.0)

    def test_slant_range(self):
        self.assertAlmostEqual(geometry.slant_range_km(550, 90), 550, delta=0.01)
        self.assertTrue(geometry.slant_range_km(550, 5) > 1500)

    def test_distance_to_finland(self):
        d, lat, lon = geometry.distance_to_finland_km(59.44, 24.75)   # Tallinn
        self.assertTrue(50 < d < 90, d)
        d0, _, _ = geometry.distance_to_finland_km(60.17, 24.94)      # Helsinki
        self.assertEqual(d0, 0.0)
        d2, _, _ = geometry.distance_to_finland_km(60.71, 28.75)      # Vyborg
        self.assertTrue(10 < d2 < 45, d2)

    def test_region_country_at(self):
        r = geometry.Region.load()
        self.assertEqual(r.country_at(60.17, 24.94), "FIN")
        self.assertEqual(r.country_at(59.93, 30.33), "RUS")
        self.assertEqual(r.country_at(58.38, 26.72), "EST")
        self.assertEqual(r.country_at(59.86, 17.64), "S")

    def test_path_profile_sea(self):
        r = geometry.Region.load()
        p = r.path_profile(59.44, 24.75, 60.02, 24.45)
        self.assertEqual(p["path_type"], "sea")

    def test_bearing(self):
        b = geometry.initial_bearing_deg(59.93, 30.33, 60.17, 24.94)   # St Petersburg -> Helsinki, roughly west-north-west
        self.assertTrue(260 < b < 300, b)
        self.assertEqual(geometry.angular_difference_deg(350, 10), 20)


if __name__ == "__main__":
    unittest.main()
