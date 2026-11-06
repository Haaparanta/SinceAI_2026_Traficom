# Results: Space IFIC 3074

The separate results files the challenge brief asks for (section 07). The terrestrial file for IFIC 3076 follows with build steps C2 and C3.

> [!IMPORTANT]
> **Status on Fri 6 Nov 2026.** Frequency screening, geography, evidence and ranking are complete. The worst-case power flux-density (pfd) check (build step C1) is **not yet evaluated**: `calc_method` is `none` in every row. Until C1 lands, the 104 "medium" notices cannot be told apart by power, only by allocation and geography. Every rule below is a hypothesis until the partner answers questions Q1 to Q3 (`pm_pack/01_Partner_Briefing_Questions.md`).

## Files

| File | Rows | What one row is |
|---|---|---|
| `space_3074.csv` | 196 | One screened notice: every notice in the issue, including the ones not raised, each with its reason |
| `space_3074.json` | 196 | The same rows as JSON (a list of `ResultRow` objects, `backend/radar/models.py`) |
| `space_3074_groups.csv` | 8 954 | Detail: one candidate frequency group (the ITU `grp` row) after frequency and geography screening. Kept because the partner has not yet said whether accuracy is judged per notice or per group (Q3) |

Notice-level counts: **18 high, 104 medium, 1 review, 12 low, 61 not raised** (135 flagged of 196).

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
| `calc_method`, `calc_value`, `calc_unit`, `limit_value`, `margin_db` | pfd trace; empty until step C1 |
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
7. **Order inside a level.** `score = 100 x relevance x (0.65 severity + 0.35 urgency)` with the factors and weights of `scoring/weights.json`; the pfd factor is fixed at the neutral 0.5 until C1.

## Known source-data issue

Group 126662625 (IND, network LVI, 2.2 to 2.29 GHz) files `pwr_ds_max = +73 dBW/Hz`. Its own peak power of -4 dBW over 8 MHz implies about -73 dBW/Hz. The value is kept as filed and flagged; the pfd step must not use it without a reviewer.

## Reproduce

```bash
make convert                                   # .mdb -> DuckDB (about 25 s)
make subbands                                  # Traficom table -> Parquet
uv run python -m radar.export --issue 3074 --kind space
make check-evidence ISSUE=3074                 # reopens every citation, exit 1 on any mismatch
```

Two runs on the same inputs produce byte-identical files (`tests/test_export.py`). The visual proof for every step is in `reports/3074/` (`make ingest relevance geography findings ISSUE=3074`).
