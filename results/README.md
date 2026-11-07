# Results: Space IFIC 3074 and Terrestrial IFIC 3076

The separate results files the challenge brief asks for (section 07). Space first; the terrestrial side quest is at the end.

> [!IMPORTANT]
> **Status on Sat 7 Nov 2026: frozen (build steps E1 to E4).** Two full runs give byte-identical files, every stage report passes, and the proof pack is in [`proof/`](proof/index.html). Frequency screening, geography, evidence, ranking and the worst-case power flux-density (pfd) check for GSO downlinks (build step C1) are complete. pfd is **indicative**: free-space propagation and the beam's peak gain towards Finland, so it is an upper bound. Non-GSO pfd is not evaluated yet, which is why 87 of the 99 "medium" notices are non-GSO. The partner questions were not asked: every rule marked *hypothesis* below is the team's final choice for this submission, with the reason in [`pm_pack/01_Partner_Briefing_Questions.md`](../pm_pack/01_Partner_Briefing_Questions.md#final-status-7-nov-2026-questions-not-asked).

## Files

| File | Rows | What one row is |
|---|---|---|
| `space_3074.csv` | 199 | One screened notice: the 196 notices of the IFIC database plus the 3 AP30B sections of the issue from the AP30B plan database, including the ones not raised, each with its reason |
| `space_3074.json` | 199 | The same rows as JSON (a list of `ResultRow` objects, `backend/radar/models.py`) |
| `plans_finland.csv` | 30 | Finland's own plan entries (9 plan bands of FIN10300, FIN10400 and FIN00000) and the 21 Bureau examination rows in which another network affects one of them (11 networks). Not tied to one issue: a watch list for the expert |
| `space_3074_groups.csv` | 8 976 | Detail: one candidate frequency group (the ITU `grp` row) after frequency and geography screening. Kept because the partner has not yet said whether accuracy is judged per notice or per group (Q3) |

Notice-level counts: **23 high, 99 medium, 1 review, 12 low, 64 not raised** (135 flagged of 199; the three AP30B sections are not raised, see "Space plans" below). The two SECOMSAT-5-78E notices (CR/C 6344) are high because the Bureau names Finland in their UHF groups first published in IFIC 3060; until E2 those groups were outside the scope and the notices were low. The pfd check moved five notices: CHINASAT-H-60.5E (two notices, 6.3 dB over) and INSAT-KA68ER (3.1 dB over) to high, BUL-TTC-1.9E (two notices, 28 dB under) to low.

## Columns

| Column | Meaning |
|---|---|
| `issue`, `kind` | 3074, `space` |
| `notice_id` | ITU `notice.ntc_id` |
| `special_section` | Main special section for the notification reason (API/A, CR/C, RES49), e.g. `CR/C 3407 M2`; otherwise `Part I-S`, `Part II-S` or `Part III-S` |
| `administration` | ITU symbol of the notifying administration (the addressee of any letter) |
| `network_or_station` | Satellite name (`geo`, `non_geo`) or earth station name (`e_stn`) |
| `freq_min_mhz`, `freq_max_mhz`, `direction` | The lead group: the notice's group with the highest concern, then the highest score |
| `finnish_match` | Finnish services and Traficom table row IDs overlapping the lead group (up to six distinct rows, terrestrial first) |
| `special_interest_station_ids` | Empty: the special-interest XLS has not been loaded yet |
| `overlap_mhz` | Width of the lead group covered by Finnish rows (union of rows, not their sum) |
| `geo_relevance` | `visible`, `low_elevation`, `not_visible`, `near_border`, `far` or `unknown` |
| `calc_method`, `calc_value`, `calc_unit`, `limit_value`, `margin_db` | Worst-case pfd of the lead group (`pfd_gso_worst_case`), its unit and reference bandwidth, the RR Article 21 limit at the angle of arrival, and `limit - pfd` (negative = exceeds). Filled for 13 notice rows and 568 group rows; empty where pfd does not apply (uplinks, non-GSO, no limit in the band) |
| `concern` | `high`, `medium`, `review`, `low` or `none` |
| `reason` | Template sentence naming the rule that set the concern; no language model |
| `evidence_refs` | Semicolon-separated locators, each reopened by `make check-evidence` (`table.col=value`, `Taajuusjakotaulukko.ID=n`, `geography(...)`) |
| `decision` | Empty in the committed file. The screen's export (`GET /export/<issue>`) fills it with the latest reviewer decision for the notice, for example `investigate by Aino at 2026-11-06T23:47:00Z: ask CHN for the pfd mask`; every decision stays in the audit log `data/decisions/<kind>_<issue>.jsonl` |

## Inputs

| Input | Version | SHA-256 |
|---|---|---|
| ITU Space IFIC 3074 database, `ific3074.mdb` from `https://www.itu.int/sns/ific10/ific3074.zip` | published 23 Jun 2026 | `a9755213b6cdb7a26a1ca1dcf95ba69a362d3bcc2cb088e91b6b8e01e4790e31` |
| Finnish table of frequency allocations, Traficom API v13 `Taajuusjakotaulukko` (CC BY 4.0), 5 917 rows | snapshot 6 Nov 2026 | `41ffdd0ed84a40c19fd4bb3771699a63c879b1ad4f2201dcb1cd3c37524871fb` |
| Finnish reference points, `data/reference/fi_reference_points.csv` (seven points, approximate town coordinates) | this repository | `e2083112e3e1111c0b766e7a30c37d94a3ac330dede87519264c5cab17671ba6` |
| RR Article 21 Table 21-4 limits, `data/reference/pfd_limits.csv`, transcribed from ITU Radio Regulations 2024 Vol. 1 (Rev.WRC-23) with the page per row | 38 rows; second check on 7 Nov 2026 against an independent transcription of the page images: all values agree, two page numbers corrected; signed off by Claude (AI agent) at the project owner's request, no human specialist available ([review](../data/reference/review/README.md)) | |
| ITU Space Plans System, `SPS_ALL_IFIC3083.mdb` from `https://www.itu.int/en/ITU-R/space/plans/Documents/SPS_ALL_IFIC3083.zip` | snapshot 3083, last export 16 Sep 2026 | `0d82d067b6feaf082d330b9b048ab1bdcbe5a2717603e78bd6b65101dd23c85d` |
| ITU Appendix 30B Plan database, `30B_3083.mdb` from `https://www.itu.int/en/ITU-R/space/plans/Documents/30B_3083.zip` | snapshot 3083, last export 24 Sep 2026 | `0b58f258c5ebd8ce8829b88f211dad3ddbc5729e057fdee27d2d137f5625cf95` |
| Plan orbital arcs, `data/reference/plan_arcs.csv`, typed from RR 2024 Vol. 2 (Appendix 30 Annex 1, 30A Annex 1, 30B Annex 4) with the page per row | 8 rows, 7 Nov 2026 | |
| Scoring weights, `scoring/weights.json` | version 2026-11-06 | `183bf176a7b1de045dc6a9910e28f87f0cc35b6aa287b3c739205b5d0c4513b7` |
| Finland and neighbour borders, `scoring/reference/finland_region.geojson` | Natural Earth 1:50m, public domain. Åland (Natural Earth `ALD`, sovereign Finland) merged into Finland on 7 Nov 2026: distances to Finland now reach Åland; no concern level changed | |

The special-interest station table (XLS from the Since AI platform) is a mandatory input that is not yet loaded.

## Method and parameters

1. **Scope.** Groups published in this issue (`grp.wic_no = 3074`, 25 105 of 34 365), plus the 22 earlier groups of 3074 notices in which the Bureau names Finland (SECOMSAT-5-78E, CR/C 6344, first published in IFIC 3060): 25 127 screened. The other 9 238 are earlier records of the same notices.
2. **Direction.** `grp.emi_rcp = E` is space-to-Earth for space-station notices (G, N) and Earth-to-space for earth-station notices (S). Checked against the satellite bands in 3074.
3. **Frequency.** Every group is joined with every Finnish row it overlaps (Hz integers). Finnish rows are classified as terrestrial, space (downlink, uplink or both), passive or not allocated; CAPITALS mean primary. A part of a group with no Finnish row is reported as `uncovered`, never as "no concern".
4. **Bureau signal.** Groups for which the Radiocommunication Bureau lists Finland as an affected administration (`provn.adm = 'FIN'`): 18 notices, 220 groups.
5. **Geography.**
   - GSO: elevation from the seven reference points with R = 6 378.137 km, h = 35 786 km; visible at 10 degrees or more, low elevation from 0 to 10 degrees.
   - Non-GSO: highest latitude that sees the satellite at 0 and 10 degrees (coverage at apogee); orbits around the Moon, the Sun or Jupiter are not visible.
   - Earth stations: distance to the Finland polygon; near border within **500 km** [hypothesis]; typical earth stations have no location and stay unknown.
6. **Concern rules** (first match wins): Bureau names Finland, high; uplink from an earth station inside Finland, high; special-interest station, near-border uplink, or downlink over a Finnish primary terrestrial or passive allocation (visible or low elevation), medium; secondary allocation or satellite-only overlap, low; table gap or unknown geography, review; otherwise none.
7. **Worst-case pfd (GSO downlinks over Finnish terrestrial or passive rows, visible from Finland).** `pfd = P_d + G + 10 log10(B) - 10 log10(4 pi d^2)` with `P_d` = `emiss.pwr_ds_max`, `G` = `s_beam.gain`, `B` = min(reference bandwidth, necessary bandwidth of the emission), `d` = slant range; evaluated at every visible reference point against every applicable Table 21-4 row at that point's angle of arrival; the smallest margin is reported. A margin below zero raises the notice to high when the beam is steerable (it can be pointed at Finland) and to review when it is fixed (the IFIC database has no boresight or gain contours). A margin of 15 dB or more lowers it to low [hypothesis, Q2].
8. **Order inside a level.** `score = 100 x relevance x (0.65 severity + 0.35 urgency)` with the factors and weights of `scoring/weights.json`; the pfd factor uses the scoring package's margin bins, neutral 0.5 where pfd is not evaluated.

## Space plans (AP30, AP30A, AP30B)

The IFIC database has no plan data (every plan table is empty), so the plan check reads the two ITU plan databases
(`SPS_ALL_IFIC3083.mdb`, `30B_3083.mdb`; [data/SOURCES.md section 1b](../data/SOURCES.md)).

1. **Finnish plan entries.** FIN10300 and FIN10400 at 22.8 E (AP30 downlink 12.1-12.5 GHz, AP30A feeder link 17.7-18.1 GHz) and the AP30B allotment FIN00000 at 46.8 E, each clipped to the plan bands of [`data/reference/plan_arcs.csv`](../data/reference/plan_arcs.csv).
2. **Bureau examination.** A network whose examination rows (`sps_results`, `ap30b_tr_res`) name a Finnish entry as affected is high. None of them is in 3074; the 11 such networks are listed in `plans_finland.csv` (for example ITALY_BSS_24.8E, pfd excess 27 dB on FIN10300; EUROPESTAR-FSS-47.5E, 41.5 dB on FIN00000).
3. **Orbital-arc pre-screen** [hypothesis: applied to every co-frequency GSO network, not only to Plan modifications]. A GSO group in the same band and direction as a Finnish entry, with a worst-case orbital spacing (nominal minus the facing station-keeping tolerances) inside the arc of RR Appendix 30 Annex 1 section 1 or Appendix 30A Annex 1 section 4 (less than 9 deg) or Appendix 30B Annex 4 section 1 (7 deg C band, 6 deg Ku band), is medium. No 3074 notice is inside an arc; the closest is CHINASAT-G-33.5E at 10.5 deg from FIN10300. EUROPESTAR-47.5E-A at 0.7 deg from FIN00000 uses 10.95-11.20 GHz, which is not an AP30B band.
4. **Plan sections of the issue.** The AP30B database holds three notices published in 3074 (AP30B/A6A 760 MEASAT-91.5E-30B-E, AP30B/A6B 235 HISPASAT-93A, AP30B/A6B 239 F-SAT-30B-139W). All three are outside every Finnish arc (44.6 deg and more) and the Bureau's examination of MEASAT names no Finnish entry, so they are not raised, with the reason. The AP30/30A database holds no notice published in 3074.

Caveat: ITU keeps only the latest plan snapshot online (3083). It holds the latest record of each network, so a plan section of 3074 that was modified later carries the later issue number and is not counted here. The exact 3074 snapshot is on the issue's BR IFIC DVD.

## Known source-data issue

Group 126662625 (IND, network LVI, 2.2 to 2.29 GHz) files `pwr_ds_max = +73 dBW/Hz`. Its own peak power of -4 dBW over 8 MHz implies about -73 dBW/Hz. The value is kept as filed and flagged; the pfd step leaves flagged emissions out and marks the group for review if nothing usable remains.

## Reproduce

```bash
make convert                                   # .mdb -> DuckDB (about 25 s)
make convert-plans                             # AP30/30A and AP30B plan databases -> DuckDB (about 90 s)
make subbands                                  # Traficom table -> Parquet
uv run python -m radar.export --issue 3074 --kind space
make check-evidence ISSUE=3074                 # reopens every citation (ITU rows, Finnish rows, RR limit rows, pfd and geography recomputed)
```

Two runs on the same inputs produce byte-identical files (`tests/test_export.py`). The visual proof for every step is in `reports/3074/` (`make ingest relevance geography findings ISSUE=3074`).

## Proof pack

[`proof/index.html`](proof/index.html) links every stage report with its status, copied from `reports/` when the files were frozen (`make freeze`). Open it from disk; the reports are self-contained.

| Check | Report | Result |
|---|---|---|
| E1 determinism | `proof/freeze/e1_determinism.html` | The whole pipeline (findings, space and terrestrial export, screen cache) run twice from DuckDB: all 7 output files identical to each other and to the committed files |
| E2 case recognition | `proof/freeze/e2_golden.html`, `proof/accuracy.csv` | 10 of 10 golden cases; 220 of 220 groups in which the Bureau names Finland are candidates with concern high; precision on reviewer decisions waits for decisions |
| E3 offline demo | `proof/playwright/index.html`, `tests/test_demo_mode.py` | With `DEMO_MODE=1` and the network cut, every endpoint and the whole screen work; no request leaves the machine and no Claude client is built |
| Evidence | `proof/3074/04_findings.html` | 1 659 citations reopened, 0 mismatches |

How to read the accuracy table: the golden cases are first-pass labels by the coding agent (a regression guard, not a specialist judgement); the Bureau list is also a rule input, so a hit shows the rule is wired through; reviewer decisions in the screen (approve or investigate = relevant, dismiss = not relevant) are the labels that measure precision, and the table fills in as soon as they exist.

---

# Terrestrial IFIC 3076

| File | Rows | What one row is |
|---|---|---|
| `terrestrial_3076.csv`, `terrestrial_3076.json` | 4 057 | One notice of the issue, each with its concern and reason |

Counts: **6 high, 1 medium, 6 review, 52 low, 3 992 not raised.** Field strength computed for 65 land-mobile notices.

| Column | Terrestrial meaning |
|---|---|
| `special_section` | ITU notice type (T11, T12, T13, T14, G12) |
| `network_or_station` | Site name (or `zone <country>` for an area notice) |
| `freq_min_mhz`, `freq_max_mhz` | Assigned frequency plus and minus half the bandwidth |
| `direction` | The change in this issue: `new` (ADD), `modified` (MODIFY), `withdrawn` (SUPPRESS), `unchanged` (RECORDED) |
| `geo_relevance` | `near_border` within 300 km of Finland, otherwise `far` |
| `calc_method`, `calc_value`, `calc_unit` | `p1546_field_strength`: field strength at the nearest Finnish border point, dB(uV/m) |
| `limit_value`, `margin_db` | T/R 25-08 trigger plus bandwidth correction; `trigger - E` (negative = trigger exceeded) |

**Inputs.** `brific3076.mdb` (ITU Terrestrial BR IFIC, published 21 Jul 2026); `data/reference/tr2508_thresholds.csv` (ECC/ERC Recommendation T/R 25-08, 6 June 2025, Annex 1; second check on 7 Nov 2026: all 5 values agree with page 6, [review](../data/reference/review/README.md); signed off by Claude at the project owner's request); Finland and neighbour borders from Natural Earth 1:50m.

**Method.**
1. Each extract is the change set of its issue (no 3076 notice is in 3075; MODIFY and SUPPRESS point into the Master Register), so the change comes from the Bureau's intent. The comparison with 3075 is a trend per administration, band and station class (`reports/3076/01_diff.html`).
2. Land-mobile notices (station classes FB, FL, ML, MO) of other administrations, with a point location, within 1 000 km of Finland.
3. Distance to the nearest point of the Finland polygon; the straight path split into land and sea zones (sea = outside every country polygon, treated as cold sea).
4. Field strength with the **ITU-R P.1546-6 reference implementation** (Py1546 6.1, pinned to commit e2356290; its 52 ITU validation cases reproduce to 0.0 dB in `tests/test_p1546.py`): 10 % of time, 50 % of locations, receiving antenna 10 m, rural receiver, no terrain profile (transmitting antenna height above ground as effective height; 1.5 m assumed for mobiles without a filed height), notified e.r.p. (e.i.r.p. minus 2.15 dB), no antenna pattern (conservative).
5. Concern [hypothesis until Q11, Q12]: new or modified notice above the trigger, high; within 6 dB below, medium; further below, low. Recorded notice above the trigger, medium; otherwise low. No T/R 25-08 trigger for the band (for example 790-862 MHz), review within 100 km and low beyond, field strength reported. Withdrawn, Finnish, non-land-mobile and area notices for distant territories are not raised, with the reason.

**Highest cases.** New Russian VHF base stations at Kostomuksha (152 MHz, 31.5 km from Finland, 13 dB above the trigger), Lyaskelya (42 km, 9 dB above) and Vyborg (30 km, 8 dB above). Review: Russian 800 MHz base stations at Ruskeala and Sortavala, 12 to 14 km from Finland, where T/R 25-08 has no trigger.

**Reproduce.**

```bash
uv run python -m radar.export --issue 3076 --kind terrestrial
uv run python scripts/field_strength_report.py 3076      # reports/3076/02_field_strength.html
```

