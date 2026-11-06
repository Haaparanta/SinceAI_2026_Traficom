import math
import unittest

from scoring import pfd, propagation
from scoring.config import load_config
from scoring.finnish_table import FinnishTable


class FinnishTableTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.t = FinnishTable.load()
        cls.cfg = load_config()

    def test_loaded(self):
        self.assertGreater(len(self.t.rows), 5000)
        self.assertGreater(len(self.t.units), 1000)
        self.assertLess(len(self.t.units), len(self.t.rows))

    def test_overlap_ku_band(self):
        hits = self.t.overlapping(10950, 11200)
        self.assertTrue(hits)
        for u, ov in hits:
            self.assertEqual(ov, 250)
            self.assertIn("FIXED SATELLITE (SPACE-TO-EARTH)", u.service)
            self.assertTrue(u.primary)
            self.assertTrue(u.is_space_to_earth)

    def test_primary_secondary_convention(self):
        caps = [u for u in self.t.units if u.service == "MOBILE"][0]
        mixed = [u for u in self.t.units if u.service == "Mobile"][0]
        self.assertTrue(caps.primary and not caps.secondary)
        self.assertTrue(mixed.secondary and not mixed.primary)

    def test_sensitivity_rules(self):
        ras = [u for u in self.t.units if "RADIO ASTRONOMY" in u.service][0]
        self.assertEqual(self.t.sensitivity(ras, self.cfg)[0], 1.0)
        am = [u for u in self.t.units if u.service == "Amateur"][0]
        self.assertEqual(self.t.sensitivity(am, self.cfg)[0], 0.3)
        virve = [u for u in self.t.units if "VIRVE" in u.usage][0]
        self.assertEqual(self.t.sensitivity(virve, self.cfg)[0], 1.0)

    def test_adjacent(self):
        adj = self.t.adjacent(1427, 1432, 0.5)
        self.assertTrue(any("RADIO ASTRONOMY" in u.service for u, g in adj))


class PfdTests(unittest.TestCase):
    def test_spreading_loss(self):
        self.assertAlmostEqual(pfd.spreading_loss_db(1.0), 10 * math.log10(4 * math.pi * 1e6), places=6)

    def test_limit_segments(self):
        row = next(r for r in pfd.Article21Table.load().rows if r["id"] == "10700-11700_gso")
        self.assertEqual(pfd.Article21Table.limit_db(row, 3), -150)
        self.assertEqual(pfd.Article21Table.limit_db(row, 5), -150)
        self.assertEqual(pfd.Article21Table.limit_db(row, 15), -145)
        self.assertEqual(pfd.Article21Table.limit_db(row, 30), -140)

    def test_find_rows(self):
        t = pfd.Article21Table.load()
        self.assertTrue(any(r["id"] == "10700-11700_gso" for r in t.find(10950, 11200, "GSO")))
        self.assertTrue(any(r["id"] == "10700-11700_ngso" for r in t.find(10950, 11200, "NGSO")))
        self.assertFalse(t.find(10950, 11200, "GSO")[0]["id"].endswith("ngso"))
        self.assertFalse(t.find(5000, 5010, "GSO"))

    def test_gso_assessment_worst_case_point(self):
        cfg = load_config()
        a = pfd.assess_gso(-62.0, 38.0, 36.0, 10950, 11200, 36e6, cfg)
        self.assertIsNotNone(a)
        self.assertEqual(a.ref_bw_hz, 4000)
        self.assertIsNotNone(a.margin_db)
        self.assertTrue(a.limit_verified)
        self.assertIn("pfd =", a.formula)

    def test_gso_not_visible(self):
        cfg = load_config()
        self.assertIsNone(pfd.assess_gso(-62.0, 38.0, 128.0, 10950, 11200, 36e6, cfg))

    def test_power_density_fallback(self):
        v, src = pfd.power_density_dbw_hz(None, 10.0, 1000.0)
        self.assertAlmostEqual(v, 10.0 - 60.0)
        self.assertIn("pep_max", src)


class PropagationTests(unittest.TestCase):
    def test_free_space(self):
        self.assertAlmostEqual(propagation.free_space_dbuv_m(30.0, 1.0), 106.9, places=6)
        self.assertAlmostEqual(propagation.free_space_dbuv_m(10.0, 80.0), 48.8, delta=0.05)

    def test_erp_conversion(self):
        self.assertEqual(propagation.erp_dbw_from_notified(10.0, "E")[0], 10.0)
        self.assertAlmostEqual(propagation.erp_dbw_from_notified(10.0, "I")[0], 7.85)
        self.assertAlmostEqual(propagation.erp_dbw_from_notified(10.0, "V")[0], 12.62)
        self.assertIsNone(propagation.erp_dbw_from_notified(None, "E")[0])

    def test_tr2508(self):
        self.assertEqual(propagation.tr2508_threshold(162.5, 12.5)["threshold_dbuv_m"], 12.0)
        self.assertEqual(propagation.tr2508_threshold(390.0, 25.0)["threshold_dbuv_m"], 18.0)
        wide = propagation.tr2508_threshold(455.0, 200.0)
        self.assertAlmostEqual(wide["threshold_dbuv_m"], 20 + 10 * math.log10(8), places=6)
        self.assertIsNone(propagation.tr2508_threshold(2602.5, 20000.0))
        self.assertIsNone(propagation.tr2508_threshold(20.0, 10.0))

    def test_model_selection(self):
        m = propagation.get_model("auto")
        self.assertTrue(getattr(m, "upper_bound", False))
        with self.assertRaises(propagation.ModelUnavailable):
            propagation.get_model("p1546")


if __name__ == "__main__":
    unittest.main()
