import json
import os
import tempfile
import unittest
from datetime import date

from scoring import cli
from scoring.adapters import (groups_from_srs, notice_from_t12, protected_stations_from_json, space_groups_from_json,
                              terrestrial_notices_from_json, finnish_networks_from_json)
from scoring.config import load_config
from scoring.evaluate import priority_agreement, ranking_quality, threshold_sweep
from scoring.finnish_table import FinnishTable
from scoring.models import OrbitInfo, SpaceGroup
from scoring.space_scoring import SpaceContext, aggregate_by_notice, normalise_section, rank_groups, score_group
from scoring.terrestrial_scoring import TerrestrialContext, diff_notices, rank_notices, trends

EX = os.path.join(os.path.dirname(os.path.dirname(__file__)), "examples")


class SpaceScoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_config()
        cls.groups = space_groups_from_json(os.path.join(EX, "space_groups_example.json"))
        cls.ctx = SpaceContext(FinnishTable.load(), cls.cfg, finnish_networks_from_json(os.path.join(EX, "finnish_space_networks_example.json")))
        cls.scored = {s.subject_id: s for s in rank_groups(cls.groups, cls.ctx)}

    def test_section_normalisation(self):
        self.assertEqual(normalise_section("CR/C/4321"), "CR/C")
        self.assertEqual(normalise_section("api/a/1"), "API/A")
        self.assertEqual(normalise_section("Part I-S"), "PART-I-S")
        self.assertEqual(normalise_section("AP30B/A6A/123"), "AP30B/A6A")
        self.assertEqual(normalise_section(None), "unknown")

    def test_clear_conflict_is_priority_a(self):
        s = self.scored["126001001-1"]
        self.assertEqual(s.status, "active")
        self.assertEqual(s.priority, "A", s.summary)
        top = s.findings[0]
        self.assertIn("FIXED SATELLITE (SPACE-TO-EARTH)", top.target_label)
        self.assertTrue(top.indicative)
        self.assertEqual(top.deadline, "2026-10-23")
        names = {f.name for f in top.factors}
        self.assertEqual(names, {"freq_overlap", "geography", "direction", "pfd_margin", "finnish_sensitivity", "finnish_status", "bandwidth", "stage", "deadline", "finland_listed", "novelty"})
        for f in top.factors:
            self.assertTrue(0.0 <= f.value <= 1.0, f.name)

    def test_finland_listed_crc_passive_adjacent_is_high(self):
        s = self.scored["126001007-1"]
        self.assertEqual(s.status, "active")
        self.assertIn(s.priority, ("A", "B"), s.summary)
        listed = next(f for f in s.findings[0].factors if f.name == "finland_listed")
        self.assertEqual(listed.value, 1.0)
        self.assertTrue(any("RADIO ASTRONOMY" in f.target_label for f in s.findings))

    def test_irrelevant_cases_are_screened_out(self):
        self.assertEqual(self.scored["126001004-1"].status, "screened_out")   # low inclination never reaches Finland
        self.assertEqual(self.scored["126001005-1"].status, "screened_out")   # GSO below the horizon
        self.assertEqual(self.scored["126001004-1"].score, 0)
        self.assertEqual(self.scored["126001008-1"].status, "withdrawn")      # suppression

    def test_borderline_between(self):
        a = self.scored["126001001-1"].score
        b = self.scored["126001003-1"].score
        self.assertTrue(0 < b < a, (a, b))
        self.assertEqual(self.scored["126001003-1"].status, "active")

    def test_uplink_scores_below_downlink(self):
        self.assertLess(self.scored["126001001-2"].score, self.scored["126001001-1"].score)

    def test_finnish_network_raises_uplink_relevance(self):
        s = self.scored["126001009-1"]
        d = next(f for f in s.findings[0].factors if f.name == "direction")
        self.assertGreaterEqual(d.value, 0.8)
        self.assertIn("FIN-LEO-OBS", d.reason)

    def test_every_active_finding_has_evidence_and_explanation(self):
        for s in self.scored.values():
            for f in s.findings:
                self.assertTrue(f.explanation)
                self.assertTrue(any(x.evidence for x in f.factors), f.finding_id)
                self.assertTrue(0 <= f.score <= 100)

    def test_deterministic(self):
        a = [s.to_dict() for s in rank_groups(self.groups, self.ctx)]
        b = [s.to_dict() for s in rank_groups(self.groups, self.ctx)]
        self.assertEqual(json.dumps(a, sort_keys=True), json.dumps(b, sort_keys=True))

    def test_as_of_after_deadline_lowers_urgency(self):
        ctx_late = SpaceContext(self.ctx.table, self.cfg, as_of=date(2026, 12, 1))
        late = score_group(self.groups[0], ctx_late)
        self.assertLess(late.score, self.scored["126001001-1"].score)

    def test_aggregate_by_notice(self):
        agg = aggregate_by_notice(list(self.scored.values()), self.groups)
        k = {n["ntc_id"]: n for n in agg}
        self.assertEqual(k["126001001"]["groups_scored"], 2)
        self.assertEqual(k["126001001"]["top_group"], "126001001-1")

    def test_missing_inputs_lower_confidence(self):
        g = SpaceGroup("x", "x-1", "NOPOWER", "D", "G", "E", 10950, 11200, "CR/C", 3074, date(2026, 6, 23), "A",
                       orbit=OrbitInfo("GSO", 13.0), srv_area=["FIN"])
        s = score_group(g, self.ctx)
        self.assertLess(s.confidence, 1.0)
        self.assertIn("pfd_margin", s.findings[0].missing_inputs)

    def test_weight_override_changes_score(self):
        cfg2 = load_config(overrides={"score": {"severity_weight": 0.2, "urgency_weight": 0.8}})
        s2 = score_group(self.groups[0], SpaceContext(self.ctx.table, cfg2))
        self.assertNotEqual(s2.score, self.scored["126001001-1"].score)


class TerrestrialScoringTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cfg = load_config()
        cls.notices = terrestrial_notices_from_json(os.path.join(EX, "terrestrial_notices_example.json"))
        cls.previous = terrestrial_notices_from_json(os.path.join(EX, "terrestrial_notices_previous_example.json"))
        cls.diff = diff_notices(cls.previous, cls.notices, cls.cfg["terrestrial"]["technical_fields"])
        cls.ctx = TerrestrialContext(FinnishTable.load(), cls.cfg, protected=protected_stations_from_json(os.path.join(EX, "protected_stations_example.json")))
        cls.scored = {s.subject_id: s for s in rank_notices(cls.notices, cls.ctx)}

    def test_diff(self):
        by = {n.notice_id: n for n in self.notices}
        self.assertEqual(by["S-2026-0003"].change_status, "modified")
        self.assertIn("erp_dbw", by["S-2026-0003"].changed_fields)
        self.assertEqual(by["RUS-2026-0004"].change_status, "unchanged")
        self.assertEqual(by["RUS-2026-0001"].change_status, "new")
        self.assertEqual([n.notice_id for n in self.diff["withdrawn"]], ["RUS-2026-0010"])
        self.assertEqual(self.diff["counts"]["withdrawn"], 2)   # one SUPPRESS in the current IFIC + one that disappeared

    def test_ranking_makes_sense(self):
        spb = self.scored["RUS-2026-0008"]      # 390.5 MHz, 100 m, pointing at Finland, VIRVE band
        petro = self.scored["RUS-2026-0004"]    # 270 km away
        riga = self.scored["LVA-2026-0007"]
        tallinn = self.scored["EST-2026-0002"]
        self.assertEqual(spb.status, "active")
        self.assertGreater(spb.score, petro.score)
        self.assertGreater(tallinn.score, riga.score)
        self.assertEqual(self.scored["EST-2026-0006"].status, "withdrawn")
        self.assertGreater(spb.score, riga.score)
        self.assertIn(spb.priority, ("A", "B", "C"), spb.summary)   # free-space screening only: a P.1546 run decides
        self.assertIn("VIRVE", spb.findings[0].target_label)

    def test_protected_station_target_appears(self):
        s = self.scored["RUS-2026-0008"]
        self.assertTrue(any(f.target_id == "FI-0003" for f in s.findings))

    def test_agreement_notice_has_deadline(self):
        s = self.scored["RUS-2026-0001"]
        self.assertEqual(s.deadline, "2026-11-13")

    def test_outside_tr2508_not_evaluated(self):
        s = self.scored["RUS-2026-0009"]
        fs = next(f for f in s.findings[0].factors if f.name == "field_strength_margin")
        self.assertFalse(fs.available)
        self.assertIn("outside the T/R 25-08 range", fs.reason)

    def test_free_space_screening_marks_needs_p1546(self):
        s = self.scored["EST-2026-0002"]
        fs = next(f for f in s.findings[0].factors if f.name == "field_strength_margin")
        self.assertTrue(fs.indicative)
        self.assertIn("P.1546", fs.reason)

    def test_trends(self):
        items = trends(self.notices, [self.previous, self.previous], self.cfg, self.ctx.region)
        self.assertTrue(items)
        self.assertTrue(any(i["note"] == "stations within 50 km of Finnish territory" for i in items))
        self.assertTrue(all("adm" in i and "count" in i for i in items))


class AdapterTests(unittest.TestCase):
    def test_srs_join(self):
        tables = {
            "notice": [{"ntc_id": 1, "ntc_type": "G", "adm": "RUS", "sat_name": "TEST-1", "ntf_rsn": "C", "act_code": "A", "wic_no": 3074, "d_wic": "20260623"}],
            "geo": [{"ntc_id": 1, "long_nom": 36.0, "f_pfd_limit": "N"}],
            "grp": [{"grp_id": 11, "ntc_id": 1, "emi_rcp": "E", "beam_name": "NRD", "bdwdth": 36000, "act_code": "A"}],
            "freq": [{"grp_id": 11, "freq_min": 10950.0, "freq_max": 11200.0}],
            "s_beam": [{"ntc_id": 1, "emi_rcp": "E", "beam_name": "NRD", "gain": 38.0}],
            "emiss": [{"grp_id": 11, "pwr_ds_max": -62.0, "pep_max": 13.0}],
            "srv_area": [{"grp_id": 11, "ctry": "FIN"}, {"grp_id": 11, "ctry": "RUS"}],
            "srv_cls": [{"grp_id": 11, "stn_cls": "EC", "nat_srv": "CP"}],
            "provn": [{"grp_id": 11, "coord_prov": "9.7", "adm": "S"}, {"grp_id": 11, "coord_prov": "9.7", "adm": "FIN"}],
            "pub_ssn": [{"ntc_id": 1, "ssn_ref": "CR/C", "ssn_no": 4321}],
        }
        groups = groups_from_srs(tables, source_file="test.mdb")
        self.assertEqual(len(groups), 1)
        g = groups[0]
        self.assertEqual((g.freq_min_mhz, g.freq_max_mhz), (10950.0, 11200.0))
        self.assertEqual(g.orbit.kind, "GSO")
        self.assertEqual(g.orbit.long_nom_deg, 36.0)
        self.assertEqual(g.gain_dbi, 38.0)
        self.assertEqual(g.pwr_ds_max_dbw_hz, -62.0)
        self.assertEqual(g.srv_area, ["FIN", "RUS"])
        self.assertEqual(g.affected_adms, ["FIN", "S"])
        self.assertEqual(g.special_section, "CR/C")
        self.assertEqual(g.ific_date, date(2026, 6, 23))
        self.assertFalse(g.f_pfd_limit_commit)
        s = score_group(g, SpaceContext(FinnishTable.load(), load_config()))
        self.assertEqual(s.priority, "A")

    def test_t12_mapping(self):
        n = notice_from_t12({"t_adm": "EST", "t_ctry": "EST", "t_action": "ADD", "t_freq_assgn": "453.5", "t_lat": "+592624", "t_long": "+0244500",
                             "t_stn_cls": "FB", "t_bdwdth_cde": "16K0", "t_emi_cls": "16K0F3E", "t_pwr_dbw": "17", "t_pwr_eiv": "I",
                             "t_ant_dir": "D", "t_azm_max_e": "10", "t_bmwdth": "60", "t_gain_max": "6", "t_gain_type": "D", "t_hgt_agl": "90",
                             "t_fragment": "Req_agrt", "t_prov": "RR9.21", "t_adm_ref_id": "EST-1"}, ific_date=date(2026, 7, 14))
        self.assertAlmostEqual(n.lat, 59.44, places=2)
        self.assertAlmostEqual(n.lon, 24.75, places=2)
        self.assertEqual(n.bandwidth_khz, 16.0)
        self.assertAlmostEqual(n.erp_dbw, 14.85)
        self.assertAlmostEqual(n.gain_dbi, 8.15)
        self.assertEqual(n.notice_id, "EST-1")
        self.assertEqual(n.fragment, "Req_agrt")


class EvaluateAndCliTests(unittest.TestCase):
    def test_evaluation_metrics(self):
        groups = space_groups_from_json(os.path.join(EX, "space_groups_example.json"))
        scored = rank_groups(groups, SpaceContext(FinnishTable.load(), load_config()))
        with open(os.path.join(EX, "labels_example.json"), encoding="utf-8") as fh:
            labels = {k: v for k, v in json.load(fh).items() if not k.startswith("_")}
        sweep = threshold_sweep(scored, labels)
        self.assertEqual(sweep["labelled"], 10)
        self.assertGreaterEqual(sweep["best"]["f1"], 0.8, sweep["best"])
        rq = ranking_quality(scored, labels)
        self.assertEqual(rq["relevant"], 4)
        self.assertIsNotNone(priority_agreement(scored, labels))

    def test_cli_space_and_terrestrial(self):
        with tempfile.TemporaryDirectory() as tmp:
            out = os.path.join(tmp, "space.json")
            md = os.path.join(tmp, "space.md")
            self.assertEqual(cli.main(["space", os.path.join(EX, "space_groups_example.json"), "--out", out, "--markdown", md,
                                       "--finnish-networks", os.path.join(EX, "finnish_space_networks_example.json")]), 0)
            with open(out, encoding="utf-8") as fh:
                data = json.load(fh)
            self.assertEqual(len(data["subjects"]), 10)
            self.assertTrue(os.path.getsize(md) > 1000)
            out2 = os.path.join(tmp, "terr.json")
            self.assertEqual(cli.main(["terrestrial", os.path.join(EX, "terrestrial_notices_example.json"), "--previous", os.path.join(EX, "terrestrial_notices_previous_example.json"),
                                       "--stations", os.path.join(EX, "protected_stations_example.json"), "--out", out2]), 0)
            with open(out2, encoding="utf-8") as fh:
                data2 = json.load(fh)
            self.assertEqual(data2["meta"]["diff"]["new"], 6)
            self.assertIn("withdrawn_since_previous", data2)
            ev = os.path.join(tmp, "eval.json")
            self.assertEqual(cli.main(["evaluate", out, os.path.join(EX, "labels_example.json"), "--out", ev]), 0)


if __name__ == "__main__":
    unittest.main()
