# Results: Space IFIC 3074 and Terrestrial IFIC 3076

The separate results files the challenge brief asks for (section 07). Space first; the terrestrial side quest is at the end.

> [!IMPORTANT]
> **Status on Fri 6 Nov 2026.** Frequency screening, geography, evidence, ranking and the worst-case power flux-density (pfd) check for GSO downlinks (build step C1) are complete. pfd is **indicative**: free-space propagation and the beam's peak gain towards Finland, so it is an upper bound. Non-GSO pfd is not evaluated yet, which is why 87 of the 99 "medium" notices are non-GSO. Every rule below is a hypothesis until the partner answers questions Q1 to Q3 (`pm_pack/01_Partner_Briefing_Questions.md`).

## Files

| File | Rows | What one row is |
|---|---|---|
| `space_3074.csv` | 196 | One screened notice: every notice in the issue, including the ones not raised, each with its reason |
| `space_3074.json` | 196 | The same rows as JSON (a list of `ResultRow` objects, `backend/radar/models.py`) |
| `space_3074_groups.csv` | 8 954 | Detail: one candidate frequency group (the ITU `grp` row) after frequency and geography screening. Kept because the partner has not yet said whether accuracy is judged per notice or per group (Q3) |

Notice-level counts: **21 high, 99 medium, 1 review, 14 low, 61 not raised** (135 flagged of 196). The pfd check moved five notices: CHINASAT-H-60.5E (two notices, 6.3 dB over) and INSAT-KA68ER (3.1 dB over) to high, BUL-TTC-1.9E (two notices, 28 dB under) to low.

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
| `decision` | Empty; filled by the reviewer (approve, dismiss, investigate) |

## Inputs

| Input | Version | SHA-256 |
|---|---|---|
| ITU Space IFIC 3074 database, `ific3074.mdb` from `https://www.itu.int/sns/ific10/ific3074.zip` | published 23 Jun 2026 | `a9755213b6cdb7a26a1ca1dcf95ba69a362d3bcc2cb088e91b6b8e01e4790e31` |
| Finnish table of frequency allocations, Traficom API v13 `Taajuusjakotaulukko` (CC BY 4.0), 5 917 rows | snapshot 6 Nov 2026 | `41ffdd0ed84a40c19fd4bb3771699a63c879b1ad4f2201dcb1cd3c37524871fb` |
| Finnish reference points, `data/reference/fi_reference_points.csv` (seven points, approximate town coordinates) | this repository | `e2083112e3e1111c0b766e7a30c37d94a3ac330dede87519264c5cab17671ba6` |
| RR Article 21 Table 21-4 limits, `data/reference/pfd_limits.csv`, transcribed from ITU Radio Regulations 2024 Vol. 1 (Rev.WRC-23) with the page per row | 38 rows, each checked once; a second reviewer is pending | |
| Scoring weights, `scoring/weights.json` | version 2026-11-06 | `183bf176a7b1de045dc6a9910e28f87f0cc35b6aa287b3c739205b5d0c4513b7` |
| Finland and neighbour borders, `scoring/reference/finland_region.geojson` | Natural Earth 1:50m, public domain | |

The special-interest station table (XLS from the Since AI platform) is a mandatory input that is not yet loaded.

## Method and parameters

1. **Scope.** Only groups published in this issue (`grp.wic_no = 3074`): 25 105 of 34 365 groups. The other 9 260 are earlier records of the same notices.
2. **Direction.** `grp.emi_rcp = E` is space-to-Earth for space-station notices (G, N) and Earth-to-space for earth-station notices (S). Checked against the satellite bands in 3074.
3. **Frequency.** Every group is joined with every Finnish row it overlaps (Hz integers). Finnish rows are classified as terrestrial, space (downlink, uplink or both), passive or not allocated; CAPITALS mean primary. A part of a group with no Finnish row is reported as `uncovered`, never as "no concern".
4. **Bureau signal.** Groups for which the Radiocommunication Bureau lists Finland as an affected administration (`provn.adm = 'FIN'`): 16 notices, 198 groups.
5. **Geography.**
   - GSO: elevation from the seven reference points with R = 6 378.137 km, h = 35 786 km; visible at 10 degrees or more, low elevation from 0 to 10 degrees.
   - Non-GSO: highest latitude that sees the satellite at 0 and 10 degrees (coverage at apogee); orbits around the Moon, the Sun or Jupiter are not visible.
   - Earth stations: distance to the Finland polygon; near border within **500 km** [hypothesis]; typical earth stations have no location and stay unknown.
6. **Concern rules** (first match wins): Bureau names Finland, high; uplink from an earth station inside Finland, high; special-interest station, near-border uplink, or downlink over a Finnish primary terrestrial or passive allocation (visible or low elevation), medium; secondary allocation or satellite-only overlap, low; table gap or unknown geography, review; otherwise none.
7. **Worst-case pfd (GSO downlinks over Finnish terrestrial or passive rows, visible from Finland).** `pfd = P_d + G + 10 log10(B) - 10 log10(4 pi d^2)` with `P_d` = `emiss.pwr_ds_max`, `G` = `s_beam.gain`, `B` = min(reference bandwidth, necessary bandwidth of the emission), `d` = slant range; evaluated at every visible reference point against every applicable Table 21-4 row at that point's angle of arrival; the smallest margin is reported. A margin below zero raises the notice to high when the beam is steerable (it can be pointed at Finland) and to review when it is fixed (the IFIC database has no boresight or gain contours). A margin of 15 dB or more lowers it to low [hypothesis, Q2].
8. **Order inside a level.** `score = 100 x relevance x (0.65 severity + 0.35 urgency)` with the factors and weights of `scoring/weights.json`; the pfd factor uses the scoring package's margin bins, neutral 0.5 where pfd is not evaluated.

## Known source-data issue

Group 126662625 (IND, network LVI, 2.2 to 2.29 GHz) files `pwr_ds_max = +73 dBW/Hz`. Its own peak power of -4 dBW over 8 MHz implies about -73 dBW/Hz. The value is kept as filed and flagged; the pfd step leaves flagged emissions out and marks the group for review if nothing usable remains.

## Reproduce

```bash
make convert                                   # .mdb -> DuckDB (about 25 s)
make subbands                                  # Traficom table -> Parquet
uv run python -m radar.export --issue 3074 --kind space
make check-evidence ISSUE=3074                 # reopens every citation (ITU rows, Finnish rows, RR limit rows, pfd and geography recomputed)
```

Two runs on the same inputs produce byte-identical files (`tests/test_export.py`). The visual proof for every step is in `reports/3074/` (`make ingest relevance geography findings ISSUE=3074`).

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

**Inputs.** `brific3076.mdb` (ITU Terrestrial BR IFIC, published 21 Jul 2026); `data/reference/tr2508_thresholds.csv` (ECC/ERC Recommendation T/R 25-08, 6 June 2025, Annex 1; second reviewer pending); Finland and neighbour borders from Natural Earth 1:50m.

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

