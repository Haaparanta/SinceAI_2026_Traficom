# 07 — Solution Catalogue: more solutions, what each needs, what is fast enough, and where logic beats AI

> [!IMPORTANT]
> **Verified schema and solution reference.** This catalogue complements docs 01–06. Doc 06 stays the master context for agents, doc 02 the scope, doc 05 the schedule. This document adds three things they do not cover in depth: the ITU table and column names checked against the ITU's own schema documentation (section 2), a wider menu of solutions with what each needs (section 4), and per-stage speed budgets (section 3).
> Sources: the official challenge brief (`Since_AI_Traficom_Challenge_Brief_FINAL_04112026.pdf`) and public ITU, CEPT and Traficom documents checked on 6 Nov 2026.
> Labels: `[VERIFIED]` = checked against the named source. `[ESTIMATE]` = our own calculation or assumption. `[GAP]` = unknown; ask Traficom at the Q&A or check on the data. Question numbers Q1–Q18 refer to doc 01.
> Doc 06's table list has been updated from section 2. Names still go through `schema_map.yaml` until `scripts/inspect_mdb.py` has run on the real files.

---

## 1. What the official brief changes

The brief is far more specific than the README. Three things matter for solution choice:

1. **The workflow is prescribed.** Ingest national tables; detect, retrieve and ingest new BR IFICs (API/A, CR/C, AP30/30A/30B); use SpaceCom or GIBC *or direct database and calculation logic*; summarise what affects Finland; cross-compare with M4, M15 and the extra tables; calculate pfd where appropriate; identify the counterparty administration; draft correspondence for expert review. `[VERIFIED brief p. 2]`
2. **The terrestrial side quest is worth as much as the technical core (25 % each).** It asks for: diff of consecutive terrestrial IFICs (new, modified, withdrawn); filter of foreign assignments relevant to Finland; applicable ITU, CEPT/ECC and national framework; criterion such as ECC T/R 25-08; deterministic field-strength calculation with ITU-R P.1546; expert-reviewable findings with model parameters; plus a few trends or anomalies in neighbouring administrations' notices. `[VERIFIED brief p. 2]`
3. **The scoring rewards logic.** Weights: A technical analysis and reproducibility 25 %, B extensibility and terrestrial side quest 25 %, C workflow usefulness and innovation 20 %, D case recognition accuracy 15 %, E auditability and evidence 15 %. `[VERIFIED brief p. 4–5]` Four of the five criteria (80 %) are about deterministic, reproducible, accurate and auditable analysis. The brief says it outright: "technical correctness, traceability and expert reviewability are more important than the choice of model."

**Submission:** a demo, the ability to process IFIC files with Finnish usage information, the processed Space IFIC 3074 and Terrestrial IFIC 3076 as separate files for accuracy evaluation, input/output documentation and the repository. `[VERIFIED brief p. 5]`

**Consequence for the product:** the PRD's Filing Radar (doc 02) stays the user-facing shape, but the engine underneath must be a deterministic rules-and-calculations pipeline with an LLM only on top. The catalogue below is organised that way.

---

## 2. Data and tool reality check

### 2.1 Summary table

| # | Source | What it is | Format and size | Access | Parse route | Status |
|---|---|---|---|---|---|---|
| 1 | Space BR IFIC circular database, issue 3074 | The notices published in that IFIC (Parts I-S, II-S, III-S, Special Sections API/A and CR/C) in SNS format | Zip, 60.8 MB for 3074 (dated 23 Jun 2026); 19.0 MB for 3083 (27 Oct 2026). URL pattern `https://www.itu.int/sns/ific10/ific<NNNN>.zip` | No login seen; the 2026 list page offers 3062–3083 | Unzip, then `mdbtools` (`mdb-tables`, `mdb-export`) to CSV, then SQLite or DuckDB | `[VERIFIED]` sizes by HTTP HEAD; file list inside the zip `[GAP: unzip and check]` |
| 2 | Full SRS snapshot (`SRS_IFIC<NNNN>.mdb`, split into `_part1of2` and `_part2of2` because of the 2 GB Access limit) | Every recorded and pending satellite network and earth station (needed for "Finnish satellites already in use" and for affected-network lists) | Microsoft Access, more than 2 GB | ISO image or BR IFIC online, registered users only | As above, slower (minutes) | `[VERIFIED]` existence and split; `[GAP]` ask Traficom for the file or a SpaceQry export |
| 3 | Preface to the BR IFIC (Space Services), edition October 2026, 387 pages | Section III Chapter 1 defines every SNS table and column (see 2.2) | PDF, 11.2 MB, `https://www.itu.int/en/ITU-R/space/Preface/preface_e.pdf` | Public | Text extraction with `pypdf` | `[VERIFIED]` |
| 4 | Terrestrial BR IFIC "MDB extract", issue 3076 | Assignments published in that issue (Article 11 Parts I–III and Plan Special Sections) | Zip, 2.4 MB for 3076 (21 Jul 2026), 3.4 MB for 3075. URL pattern `https://www.itu.int/en/ITU-R/terrestrial/brific/BRIFIC/MDB/brific<NNNN>.zip`; issues 3074–3083 on the first page of the list | No login seen | Unzip; if `.mdb` use `mdbtools`, if `.db3` open directly with `sqlite3` | `[VERIFIED]` sizes; inner format `[GAP: unzip]` |
| 5 | Terrestrial IFIC 3076 information note | Counts: Part I 2 415, Part II 1 051, Part III 44 (total 3 510); GE84/365 472 notices; GE06L/167 16 notices; Special Section RR9.21/C/1116 as PDF | PDF | Public | Read | `[VERIFIED ReadMe_3076.pdf]` |
| 6 | Full TerRaBase (`BRIFIC_<NNNN>.db3`) | The complete terrestrial database; each IFIC replaces the previous one; no history kept | SQLite, single file | Full BR IFIC package | `sqlite3` directly | `[VERIFIED terrasys docs]`; size `[GAP]` |
| 7 | Preface to the BR IFIC (Terrestrial Services), edition 3083, 396 pages | Field definitions, notice forms, class-of-station codes, administration codes | PDF, 3 MB | Public | `pypdf` | `[VERIFIED]` |
| 8 | Traficom frequency allocation table API v13 | Finnish table of frequencies, one row per sub-band usage | OData JSON, 5 917 rows, 4.4 MB, about 2 s to fetch | Public, no key | `requests` + `pandas` | `[VERIFIED 6 Nov 2026]` |
| 9 | Regulation M4 (Finlex 2026/3) and M15 (2025/51209) | Regulation text behind the table | HTML on Finlex | Public | Cite by section; the table itself comes from the API | `[brief]` |
| 10 | Synthetic "frequencies of special interest" dataset | Station number, centre frequency and bandwidth, coordinates, antenna height, direction, directivity | XLS on the Since AI platform | Platform login | `openpyxl` | `[brief]`; exact columns and whether a protection limit is included `[GAP]` |
| 11 | ECC Recommendation T/R 25-08 (amended 28 Sep 2018) | Land-mobile coordination thresholds 29.7–470 MHz | DOCX from `docdb.cept.org/download/2543` | Public | Values transcribed in 2.4 | `[VERIFIED]` |
| 12 | ITU-R P.1546-6 | Point-to-area field-strength prediction 30–4 000 MHz | `Py1546` (GitHub `eeveetza/Py1546`), Python port of the ITU-R WP 3K reference MATLAB code, with validation examples | pip install from git | Import | `[VERIFIED search]`; runtime per path `[ESTIMATE]` |
| 13 | Radio Regulations Article 21, Table 21-4 | pfd hard limits at the Earth's surface by band and angle of arrival (0–5°, 5–25°, 25–90°) in 4 kHz or 1 MHz | RR 2024 edition PDF | Public | Transcribe to CSV by hand, two people check | `[GAP: transcribe]` |
| 14 | ITU BR space software (SpaceCap, SpaceQry, GIBC, SpaceCom, GIMS) | GUI tools for filings, queries, pfd examinations and comments | 400 MB installer, Windows 10 and 11 only, no command line documented | Public | Not scriptable in 48 h; use "direct logic" as the brief allows | `[VERIFIED ITU software pages]` |
| 15 | Finnish border and coastline geometry | Needed for distance, azimuth and land/sea path fractions | Natural Earth 10 m boundaries (public domain) or Maanmittauslaitos | Public | `shapely`, `pyproj` | `[ESTIMATE]` |

Local environment today: macOS, Python 3.15, no `mdbtools` and no `poppler` installed yet (`brew install mdbtools poppler`). `[VERIFIED]`

### 2.2 Space side: the SNS v10 tables that matter

SNS schema v10 applies from IFIC 3037 (7 Jan 2025); v9.1 from IFIC 2985 (Nov 2022); v9 from IFIC 2926 (Aug 2020). `[VERIFIED WRS-24 slides]` The 2026 download page notes that older-year databases are "no longer supported on this webpage", so "all existing IFICs" in practice means: v10 natively, v9.1 by column mapping, older issues only if Traficom supplies them. `[VERIFIED demowic26]`

Table names and the columns the solutions use, from Section III Chapter 1 of the October 2026 Preface `[VERIFIED]`:

| Table | Meaning | Columns we rely on |
|---|---|---|
| `notice` | One row per filing | `ntc_id`, `adm` (notifying administration), `ntwk_org`, `ntc_type` (G geostationary, N non-geostationary, S specific earth station, T typical earth station, R radio astronomy), `ntf_rsn` (9.1 = API, 9.6 = coordination, 11.2 = notification, AP30B codes, Res49), `prov`, `act_code`, `d_rcv`, `wic_no`, `wic_part`, `d_wic`, `tgt_ntc_id` |
| `geo` | GSO space station | `ntc_id`, `sat_name`, `long_nom` (nominal longitude, minus for West) |
| `non_geo` | NGSO space station | `ntc_id`, `sat_name`, `ref_body` |
| `orbit` | Orbital planes of an NGSO system | `ntc_id`, `orb_id`, `nbr_sat_pl`, `inclin_ang`, `apog_km`, `perig_km`, `right_asc`, `perig_arg`, `orbit_set_id` |
| `phase` | Initial phase angles per plane | per-satellite positions |
| `s_beam` | Satellite antenna beam | `ntc_id`, `beam_name`, `emi_rcp` (E transmit, R receive), `gain` (max isotropic gain, dBi), `f_steer` |
| `grp` | Group of assigned frequencies | `grp_id`, `ntc_id`, `beam_name`, `emi_rcp`, `freq_min`, `freq_max` (MHz, derived), `bdwdth` (kHz), `d_inuse`, `adm_resp`, `op_agcy`, `prov`, `wic_no`, `wic_part`, `d_wic` |
| `assgn` | Assigned frequencies of a group | assigned frequency, `pfd` (declared pfd, where given) and `bdwdth` |
| `emiss` | Emission | `grp_id`, `design_emi` (emission designator), `pep_max` (dBW), `pwr_ds_max` (max power density, dBW/Hz), `pwr_ds_nbw` |
| `srv_area` | Service area | `grp_id`, `ctry` (country or geographical-area symbol), `f_excl_api` |
| `srv_cls` | Nature of service and class of station per group | service codes |
| `e_as_stn`, `e_ant` | Associated earth stations and their antennas | `ctry`, `gain`, location |
| `mask_info`, `mask_lnk1`–`mask_lnk3` | NGSO pfd and epfd masks | `freq_min`, `freq_max`, mask data |
| `provn`, `all_aff_ntw`, `tr_aff_ntw` | Coordination provisions and affected or affecting networks | administrations and networks identified by the Bureau |
| `pub_ssn` | Publication information for a notice | special-section reference |

Part I-S action symbols: A new, M modification, N non-basic change, R resubmission, S suppression, W withdrawn. `[VERIFIED Preface Section II]`

### 2.3 Terrestrial side: the FXM tables (fixed, mobile and other services)

The terrestrial database has three domains: FM/TV, LF/MF and FXM. Land-mobile notices live in FXM. `[VERIFIED Preface Chapter II Section 6]`

| Table | Columns we rely on `[VERIFIED FXM diagram and Preface Chapter III]` |
|---|---|
| `fxm_terra` | `terrakey`, `fragment` (NTFD_RR for Article 11 notices), `adm`, `freq_assgn`, `freq_carr`, `freq_min`, `freq_max`, `bdwdth`, `emi_cls` (emission designator), `stn_cls` (class of station), `stn_type`, `notice_typ`, `intent` (ADD, MODIFY, SUPPRESS, WITHDRAW), `stage`, `d_rcv`, `d_adm_ntc`, `d_inuse`, `pub_no`, `assgn_id`, `adm_ref_id`, `geo_key` |
| `fxm_geo`, `fxm_geo_pt` | `geo_key`, `ctry`, `site_name`, `long_dec`, `lat_dec`, `site_alt`, `radius`, `zone_id` |
| `fxm_ant` | `ant_key`, `pwr_ant` (power to the antenna, dBW), `pwr_dbw`, `pwr_dens`, `pwr_xyz` (power type), `gain_max`, `gain_type`, `ant_dir` (D or ND), `azm_max_e`, `elev`, `bmwdth`, `polar`, `hgt_agl`, `eff_hgtmax`, `gain_max_horizon`, `tx_rx` |
| `fxm_ant_hgt` | Effective antenna height per azimuth (`azm`, `eff_hgt`), the exact input P.1546 wants |
| `fxm_ant_diag`, `fxm_rot` | Antenna attenuation pattern by azimuth; rotation sectors |
| `fxm_pub_hist`, `fxm_history`, `fxm_status`, `fxm_fdg` | Publication history (`pub_no`, `pub_part`), status, findings |
| `fxm_coord` | Coordination with other administrations (`adm`, `coord_prov`, `coord_st`) |

Notice forms for FXM: T11 fixed-service transmitter, T12 other transmitting stations (this is where land-mobile base stations go), T13 receiving land station, T14 typical transmitting station, T17 adaptive systems. Class-of-station codes: FB base station (land mobile), FL land station (mobile service), ML land mobile receiving station, MO mobile receiving station, FX fixed station. `[VERIFIED Preface Chapter III Section 2 and Chapter IV Section 6]`

Parts of the terrestrial circular: Part I = notices received (ADD, MODIFY, SUPPRESS, WITHDRAWN), Part II = recorded in the Master Register with findings, Part III = returned with unfavourable findings. `[VERIFIED]`

### 2.4 Rules and models (values to code as data, with citations)

**T/R 25-08 (2018) coordination thresholds** `[VERIFIED docdb 2543, Annex 1]`: co-channel, 50 % locations, 10 % time, 10 m receiving height, 25 kHz reference bandwidth, evaluated at the border line.

| Band | Threshold |
|---|---|
| 29.7–47 MHz | 0 dBµV/m |
| 47–108 MHz | 6 dBµV/m |
| 108–380 MHz | 12 dBµV/m |
| 380–400 MHz | 18 dBµV/m |
| 400–470 MHz | 20 dBµV/m |

Bandwidth correction for channels wider than 25 kHz with uniform spectral density: add `10·log10(channel spacing / 25 kHz)`; otherwise apply the threshold within every 25 kHz. Preferential regimes in the 400 MHz range: 20 dBµV/m per 25 kHz at 40 km (regime a) or 50 km (regime b) inside the neighbouring country; non-preferential: at the border line. Wideband (> 1 MHz) FDD systems in 410–430 and 450–470 MHz: 55 dBµV/m per 5 MHz at the border and 37 dBµV/m per 5 MHz at 10 km inside, at 3 m height (Annex 4). A 10 dB correction from 10 m to 3 m height "may be used"; P.1546 gives 10.3 dB. P.1546 is the propagation reference cited by the Recommendation. Finland is a "type 1" country for PCI and code sharing; Finland is not among the HCM Agreement parties listed, so HCM is not the applicable bilateral framework. `[VERIFIED]`

**RR Article 21, Table 21-4** `[GAP: transcribe from the RR 2024 edition]`: rows are band × service × angle-of-arrival class with a reference bandwidth. Two classic rows, shown only to illustrate the shape and to be verified before use: 3 400–4 200 MHz FSS: −152 / −152 + 0.75(δ − 5) / −137 dB(W/m²) in 4 kHz; 10.7–11.7 GHz FSS: −150 / −150 + 0.5(δ − 5) / −140 dB(W/m²) in 4 kHz. GIBC examines both "hard limits" (Nos. 9.35 and 11.31, unfavourable finding when exceeded) and "triggers" (Nos. 9.11, 9.14, 9.21/C, coordination when exceeded). `[VERIFIED WRS-24 NGSO Article 21 slides]` Our calculator reproduces the single-entry pfd part of that examination.

**Deadlines** `[RR; verify provision numbers]`: comments on an API/A are due within four months of the IFIC date (No. 9.3); disagreement with a CR/C within four months (No. 9.52). Both follow from `notice.d_wic` or the IFIC date.

### 2.5 Tools we cannot script

GIBC, SpaceCom, SpaceQry and GIMS are Windows-only GUI applications with a 400 MB installer and no documented batch interface. `[VERIFIED]` They remain useful in one way: if a Traficom specialist can run GIBC on one network from IFIC 3074 and share the report, it becomes a golden test for our pfd calculator (P4).

---

## 3. What is fast enough

The IFIC cadence is one issue every two weeks for both circulars, and both are published on the same day with the same number (Space 3074 and Terrestrial 3074 on 23 Jun 2026; 3076 on 21 Jul 2026). `[VERIFIED schedule pages]` Nothing in the evaluation rewards raw speed; it rewards reproducibility, accuracy and auditability. Speed matters in two places only: the batch must be re-runnable before the Sunday submission, and the demo must feel instant.

| Stage | Production "fast enough" | Demo target | Expected on a laptop `[ESTIMATE]` | How we keep it there |
|---|---|---|---|---|
| Detect a new IFIC | Within 24 h of publication (daily poll, bi-weekly cadence) | Manual trigger | HEAD requests, milliseconds | Poll the two ITU list pages once a day |
| Download | Minutes | Pre-downloaded | 61 MB + 2.4 MB, under 1 min | Cache by issue number |
| Convert Access to SQLite | Under 5 min per space issue; under 10 s per terrestrial extract | Pre-converted | `mdb-export` streams tens of MB/s; the 3074 archive may expand to several hundred MB of `.mdb` | Convert once, keep SQLite per issue |
| Deterministic screening (filters, overlaps, geometry) | Under 60 s per issue | Under 5 s | SQL and pandas on 10⁴–10⁵ rows | Interval index for band overlap; vectorised geometry |
| GSO and NGSO pfd | Under 10 s per issue | Instant | Closed form, under 1 ms per emission | Pure numpy |
| P.1546 field strength | Under 10 min per issue | Pre-computed | Tens to a few hundred candidate stations × about 200 border points = 10⁴–10⁵ paths at roughly 1–5 ms each, single-threaded | Pre-filter by distance; `multiprocessing`; measure on day one |
| LLM explanations and drafts | Under 5 min per issue | Cached | 5–20 s per call; cap at 30 findings and 10 drafts, 5 calls in parallel | Content-hash cache; `--max-llm-calls`; never on the critical path of a finding |
| Whole batch per issue | Under 15 min | n/a | | A `run_manifest.json` with input hashes, versions and timings |
| UI interaction | Under 200 ms | Under 200 ms | Reads precomputed JSON or SQLite | Demo Mode makes no network calls |

Rules that follow from the table:

- **Deterministic first, LLM last.** A finding exists and is ranked before any LLM call; the LLM only explains and drafts. If the LLM is slow or down, the finding still ships.
- **Same input, same output.** Thresholds and limits are versioned CSV files; library versions are pinned; LLM calls use temperature 0 and are cached by prompt hash; the prompt hash and model name are written into the output. Two consecutive runs of 3074 must produce identical finding files (P4 tests this).
- **Scale guard.** Every rule and calculation gets a per-issue budget; if P.1546 would exceed 10 min, the pre-filter radius is tightened and the change is logged, not silently applied.

---

## 4. Solution catalogue

Each entry: what it does, what it needs, how fast it must be, which criteria it serves (A–E from section 1), effort for one person, and risks. Effort assumes the data has been opened once (L2).

### 4.1 Logic-based solutions (deterministic, no LLM)

**L1 — IFIC watcher and fetcher**
- Does: polls the 2026 space list page and the terrestrial list page for new `ific<NNNN>.zip` and `brific<NNNN>.zip`, downloads new issues, records size, date and SHA-256 in a manifest. Accepts any issue number on the command line so "all existing and forthcoming IFICs" is a parameter, not a feature.
- Needs: `requests`, the two URL patterns in 2.1, a cron job or GitHub Action, retry and checksum logic.
- Fast enough: daily poll; a run is seconds.
- Criteria: C ("automatically monitors"), B. Effort: 2 h. Risk: ITU page layout changes; parse the `href` pattern, not the layout.

**L2 — Ingest and normalise (the riskiest step, do it first)**
- Does: unzips an issue, exports every table with `mdbtools` to CSV, loads into one SQLite file per issue, detects the schema version (v10 vs v9.1) from the table and column set, and maps both domains into one `Notice` model: identifier, administration, kind (space network, earth station, terrestrial station), action (ADD, MODIFY, SUPPRESS, WITHDRAW or the Part I-S symbols), frequency ranges, geometry (longitude, orbit, or site coordinates), power descriptors, publication part and date, source reference (file, table, primary key).
- Needs: `brew install mdbtools` (or `apt`), `pandas`, `sqlite3`, the table list in 2.2 and 2.3, a `partner.py`-style adapter per domain. For the split SRS files, export from whichever part physically holds the table (Access linked tables are only links). `[GAP]`
- Fast enough: under 5 min per space issue.
- Criteria: A, B. Effort: 4–6 h. Risk: the zip may hold `.accdb` or a different layout; `mdbtools` reads both JET4 and ACCDB, but check on Friday night.

**L3 — Finland-relevance filter for space notices**
- Does: scores every group in the issue against ordered rules and keeps the rule hits as evidence:
  - R0 Finland is named by the Bureau as affected (FIN in `provn`, `tr_aff_ntw` or `all_aff_ntw` for a CR/C). Highest confidence. `[column names GAP]`
  - R1 Frequency overlap of `grp.freq_min`–`freq_max` with Finnish sub-bands from the Traficom API, co-channel or adjacent (adjacent window is a parameter, default 1 MHz or 10 % of the group bandwidth).
  - R2 Service area includes Finland: `srv_area.ctry` is FIN, a Region 1 or world code, or empty with a global beam. `[area codes GAP: Preface Table 1B]`
  - R3 GSO visibility: elevation from Finnish reference points to `geo.long_nom` is at least 0° (formula in section 8). From Helsinki this admits longitudes roughly 47° W to 97° E; from Utsjoki 39° W to 89° E. `[ESTIMATE from the formula]`
  - R4 NGSO visibility: `inclin_ang + arccos(R / (R + apog_km))` at or above 59.8° (southern tip of Finland); otherwise the system never rises above the Finnish horizon.
  - R5 `notice.adm` is not FIN; direction matters: transmitting beams (`emi_rcp` = E) threaten Finnish terrestrial use, receiving beams (R) matter for Finnish satellites and earth stations.
  - R6 Procedure stage from `ntf_rsn` and the special section (API/A, CR/C, AP30/30A/30B, Part I-S), used for urgency and for which deadline applies.
- Needs: L2 output, the Traficom API table, Finnish reference points (Helsinki, Turku, Vaasa, Oulu, Rovaniemi, Utsjoki plus the special-interest stations), an interval index.
- Fast enough: under 10 s per issue.
- Criteria: D, A, E. Effort: 6 h. Risk: over-inclusion by R1 alone; that is why R0, R3 and R4 exist and why the score keeps each rule separate.

**L4 — GSO pfd calculator against Article 21**
- Does: for each transmitting emission of a relevant GSO group computes the free-space pfd at each Finnish reference point in the band's reference bandwidth, the angle of arrival (equal to the elevation), the applicable Table 21-4 limit and the margin in dB. Reports every input used (`emiss.pwr_ds_max`, `s_beam.gain`, `geo.long_nom`, distance, reference bandwidth) and labels the result "single entry, maximum gain, free space; no beam roll-off applied unless a contour is available".
- Needs: Table 21-4 as a verified CSV (band, service, three limits, reference bandwidth, orbit class, footnotes), `grp`, `emiss`, `s_beam`, `geo`, `srv_cls`. GIMS contours are optional refinement.
- Fast enough: milliseconds per emission.
- Criteria: A, D, E. Effort: 4 h plus 2 h to transcribe and cross-check the table. Risk: a wrong limit row. Mitigation: two people transcribe independently and a test compares the two files.

**L5 — NGSO worst-case pfd**
- Does: when a pfd mask exists in `mask_info` for the group, uses it directly. Otherwise computes the single-satellite worst case at the perigee altitude: nadir distance `perig_km`, and the distance at the minimum elevation declared or at 5°, with maximum power density and maximum beam gain, then compares with the NGSO rows of Table 21-4. Reports constellation size (`nbr_sat_pl` × planes) as context but does not aggregate, and says so.
- Needs: `orbit`, `non_geo`, `emiss`, `s_beam`, `mask_info`, Table 21-4 CSV.
- Fast enough: under 1 s per system.
- Criteria: A, D. Effort: 4 h. Risk: Article 21 NGSO rows carry conditions (number of satellites, bands). Keep the label "indicative, single entry" and cite the row.

**L6 — Finnish satellite protection (SRS self-join)**
- Does: extracts every network with `notice.adm` = FIN (or a Finnish `ntwk_org`) from the full SRS and checks each new foreign filing for: frequency overlap of opposite-direction beams, GSO orbital separation (`|Δ long_nom|` below the coordination-arc threshold for the band), NGSO overlap of altitude shells and inclinations (in-line event potential, indicative). Produces "new filing X may affect Finnish network Y" findings with both filings' identifiers as evidence.
- Needs: the full SRS or a SpaceQry export of FIN networks plus all networks in the bands of interest `[GAP, ask Traficom]`; Appendix 5 coordination-arc values per band `[GAP]`. Fallback without SRS: Finnish networks that appear in Part II-S of the 2026 issues (3062–3083), which is partial.
- Fast enough: seconds.
- Criteria: D, C (the brief's "Finnish satellites already in use"). Effort: 4 h.

**L7 — Special-interest station screening**
- Does: for each Finnish station in the XLS (coordinates, frequency, bandwidth, antenna height, azimuth, directivity) and each relevant space emission: pfd at the station (L4 or L5), elevation and azimuth to the satellite, antenna discrimination from a reference pattern (omni for mobile; a standard fixed-service pattern otherwise), received interference density, and comparison with the station's limit if the XLS has one, else with Table 21-4. Ranks station × filing pairs.
- Needs: the XLS schema `[GAP]`, reference antenna patterns, L4 and L5.
- Fast enough: seconds.
- Criteria: D, A, C. Effort: 5 h. Risk: the XLS is synthetic; keep the station-limit logic data-driven.

**L8 — Terrestrial diff engine (consecutive issues)**
- Does: loads `fxm_terra`, `fxm_geo`, `fxm_ant` from issues N−1, N and N+1 (3075, 3076, 3077 are all downloadable), keys on `terrakey` with `assgn_id` and `adm` + `stn_id` + `freq_assgn` as fallbacks, and classifies each notice as new, modified, suppressed or withdrawn from `intent`, then adds derived states the field does not give: first seen, changed technical fields (hash of frequency, power, site, antenna columns), moved from Part I to Part II or III, disappeared.
- Needs: three extracts, L2.
- Fast enough: seconds (3 510 Article 11 notices in 3076).
- Criteria: B. Effort: 3 h. Risk: identifiers differ between extracts; the fallback key handles it and the report says which key matched.

**L9 — Terrestrial Finland-relevance filter**
- Does: keeps foreign notices where `adm` is a neighbour (S, NOR, RUS, EST; extended set LVA, LTU, DNK, POL, D for long sea paths), `stn_cls` is FB, FL, ML or MO and `notice_typ` is T12, T13, T14 or T17 (T11 fixed only if Traficom asks), the assigned frequency is in 29.7–470 MHz or overlaps Finnish land-mobile usage in the Traficom table, and the site (`fxm_geo.long_dec`, `lat_dec`) is within a pre-filter distance of the Finnish border (parameters: 200 km land, 300 km sea, derived from what 1 kW e.r.p. at 10 % time can reach `[ESTIMATE]`). Records every rule hit.
- Needs: L2, L8, border geometry (source 15), administration codes from the Preface Chapter IV Section 1.
- Fast enough: seconds.
- Criteria: B, D. Effort: 3 h.

**L10 — Regulatory framework resolver**
- Does: a rule table that maps band, service, station class and administration to the applicable framework and returns a criterion record: threshold, reference bandwidth, receiving height, time and location percentages, where it is evaluated (border line, 10 km, 40 or 50 km inside), propagation model, and the citation. Rows: RR Article 5 allocation and footnotes for Region 1; T/R 25-08 Annex 1 for 29.7–470 MHz land mobile (values in 2.4); T/R 25-08 Annex 3 and 4 for wideband 400 MHz systems; ECC/REC/(16)03 for 698–791 MHz BB-PPDR `[VERIFIED document exists; values GAP]`; M4 rows from the API; bilateral FIN–SWE, FIN–NOR, FIN–RUS, FIN–EST agreements `[GAP]`. States explicitly when no criterion applies.
- Needs: the rule table as CSV with a source column, L9 output.
- Fast enough: instant.
- Criteria: B, E. Effort: 4 h, mostly reading and transcribing.

**L11 — P.1546 field-strength engine**
- Does: for each candidate station computes the field strength at sampled Finnish border points (every 5 km within the pre-filter radius) with `Py1546`: frequency = `freq_assgn`; e.r.p. from `pwr_ant` + `gain_max` − 2.15 dB (dBi to dBd; check `gain_type`); transmitter effective height from `fxm_ant_hgt.eff_hgt` at the path azimuth, else `eff_hgtmax`, else `hgt_agl` + `site_alt` minus a terrain estimate (flagged); receiving height 10 m; 10 % time; 50 % locations; land, sea or mixed path from the coastline polygon. Normalises to 25 kHz with the bandwidth rule, applies antenna pattern attenuation from `fxm_ant_diag` at the azimuth where available, compares with the L10 criterion and reports the maximum field strength, the point where it occurs, the distance and the margin. Every parameter and every fallback is printed in the finding.
- Needs: `Py1546` (validate against its bundled examples on day one), `shapely`, `pyproj`, border and coastline polygons, the emission designator parser for necessary bandwidth (first four characters, e.g. `16K0` = 16.0 kHz) with `bdwdth` as the primary source.
- Fast enough: under 10 min per issue single-threaded; parallelise if the timing test says otherwise.
- Criteria: A, B, E. Effort: 6 h including validation. Risk: the sea-border question (coastline versus maritime boundary) `[GAP, ask Traficom]`; make the border layer a parameter.

**L12 — Trend and anomaly detector**
- Does: per issue and per neighbouring administration counts notices by band (Finnish sub-band or 10 MHz bins), station class, bandwidth class (up to 25 kHz, up to 200 kHz, above 1 MHz), region (grid cell or nearest Finnish region) and new sites (first-seen `geo_key`), compares with the trailing six issues (3070–3075 are downloadable) and flags `|z| ≥ 2` or a category seen for the first time. Surfaces the top five with the counts behind them.
- Needs: seven consecutive extracts, L8, L9.
- Fast enough: seconds.
- Criteria: B, C. Effort: 3 h. Risk: small counts; show the raw numbers next to every flag.

**L13 — Counterparty and correspondence data resolver**
- Does: maps `adm` to the administration name and contact from the Preface's Administrations table, pulls the special-section reference (`pub_ssn`, `wic_no`, API/A or CR/C number), network name (`sat_name`), operator (`op_agcy`), the regulatory basis (No. 9.3 comment on an API/A, No. 9.52 disagreement with a CR/C, T/R 25-08 coordination request on the terrestrial side) and the deadline date, and fills a correspondence template with placeholders left where data is missing.
- Needs: Preface Chapter IV Section 1 as CSV, L3 or L9 output.
- Fast enough: instant.
- Criteria: C, E. Effort: 2 h.

**L14 — Provenance ledger and submission exporter**
- Does: every finding is a record with `finding_id`, `rule_id`, inputs as (file, table, primary key, value), formula, parameters, result, margin, citations (RR article or table, T/R 25-08 section, M4 row ID, Traficom API row ID), concern level and the list of rules that did not fire. Exports `findings_space_3074.csv/json`, `findings_terrestrial_3076.csv/json`, a Markdown report and `run_manifest.json`. Also exports the "evaluated, no concern" list with the reason, which is how false positives and coverage become visible to the evaluators.
- Needs: nothing beyond the pipeline.
- Fast enough: instant.
- Criteria: A, E and the submission itself. Effort: 3 h.

**L15 — Deadline tracker**
- Does: derives the comment or disagreement deadline per finding from the IFIC date and the procedure (section 2.4), sorts the queue by days left, and marks items past the deadline.
- Needs: `notice.d_wic` or the issue date, provision numbers confirmed with Traficom.
- Fast enough: instant.
- Criteria: C. Effort: 1 h.

### 4.2 AI-assisted solutions (LLM on top of logic)

**A1 — Grounded finding explainer**
- Does: writes a three-to-five sentence explanation per finding citing only evidence IDs from L14; a validator rejects any sentence that cites nothing or cites an unknown ID. Capped at the top 30 findings per issue.
- Needs: Claude API (`claude-sonnet-5-5` for volume, `claude-opus-5-5` for the drafts), structured output, the cache from section 3.
- Fast enough: 5–15 s per call, five in parallel.
- Criteria: C, E. Effort: 4 h.

**A2 — Correspondence drafter**
- Does: fills a fixed template (reference to the special section, network or station, frequencies, Finnish usage affected with M4 rows or stations, calculated pfd or field strength with parameters, requested action, regulatory basis, deadline) and lets the LLM write only the connective prose; everything numeric comes from L13 and L14. Output as Markdown and `.docx` for expert review; never sent anywhere.
- Needs: L13, a template agreed with Traficom `[GAP: what do they send today?]`.
- Fast enough: 10–20 s per draft, ten drafts per issue maximum.
- Criteria: C. Effort: 4 h.

**A3 — Special-section PDF reader**
- Does: for content only published as PDF (for example the RR9.21/C special section in terrestrial 3076, or CR/C narrative), extracts the needed fields with page-level citations. Used only when the database has no field for the item.
- Needs: `pypdf` text, LLM extraction with a strict schema, page references in the evidence.
- Fast enough: 10–30 s per document.
- Criteria: E, C. Effort: 4 h.

**A4 — Regulation interpreter (one-off, reviewed)**
- Does: turns free-text columns (Traficom `Additional_information` and `Comment`, RR footnotes relevant to the matched bands) into structured flags such as "passive system", "no new assignments", "radio astronomy protected", reviewed once by a human and cached; the flags feed L3 and L10.
- Needs: the API table, footnote text, a review pass.
- Fast enough: minutes once.
- Criteria: D, E. Effort: 3 h.

**A5 — Expert-feedback ranking (no LLM)**
- Does: the concern score is a weighted sum of rule hits and margins (overlap width, pfd or field-strength margin, visibility, stage urgency, Finnish-asset hit). Approve and dismiss decisions are logged; after about 30 decisions a logistic regression re-fits the weights and the UI shows old and new weights side by side. `[ESTIMATE on the 30]`
- Needs: P2 decision log.
- Fast enough: instant.
- Criteria: C. Effort: 3 h.

**A6 — Scoped question box**
- Does: answers questions about one finding using only its evidence, the cited regulation snippets and the calculation record; refuses outside that scope.
- Criteria: C. Effort: 3 h.

**A7 — Neighbourhood digest**
- Does: turns L12 output into a short narrative per issue, each sentence linked to the count behind it.
- Criteria: C, B. Effort: 1 h.

### 4.3 Workflow and product solutions

**P1 — Command-line batch processor** (`ific process --space 3074 --terrestrial 3076 --out results/`): the core deliverable, runs L1–L15 and the capped AI steps, produces the submission files. Effort: 3 h of glue.

**P2 — Review console**: the One-Screen UI from doc 02 (map, band chart, ranked findings, approve, dismiss, investigate, audit log, memo export) reading P1 output. Effort: as in doc 02.

**P3 — Watch mode and digest**: L1 on a schedule plus a Discord or e-mail digest of new findings; demonstrates "automatically monitors". Effort: 2 h.

**P4 — Validation harness**: P.1546 against the reference examples bundled with `Py1546`; pfd against a hand calculation and, if obtainable, a GIBC report for one 3074 network; a reproducibility test (two runs, identical hashes); golden cases from the Saturday Q&A. Effort: 4 h.

**P5 — Submission pack**: the two findings files, a data dictionary of every column used, the formula sheet (section 8), parameter tables, and a page describing input and output. Effort: 3 h.

### 4.4 Summary matrix

| ID | Solution | Type | A | B | C | D | E | Effort | Priority |
|---|---|---|---|---|---|---|---|---|---|
| L2 | Ingest and normalise | Logic | x | x | | | | 4–6 h | Must |
| L3 | Space relevance filter | Logic | x | | | x | x | 6 h | Must |
| L9 | Terrestrial relevance filter | Logic | | x | | x | | 3 h | Must |
| L8 | Terrestrial diff engine | Logic | | x | | | | 3 h | Must |
| L14 | Provenance and exporter | Logic | x | | | | x | 3 h | Must |
| P1 | CLI batch processor | Product | x | x | | | | 3 h | Must |
| L4 | GSO pfd calculator | Logic | x | | | x | x | 6 h | Should |
| L11 | P.1546 engine | Logic | x | x | | | x | 6 h | Should |
| L10 | Framework resolver | Logic | | x | | | x | 4 h | Should |
| A1 | Grounded explainer | AI | | | x | | x | 4 h | Should |
| P2 | Review console | Product | | | x | | x | per doc 02 | Should |
| P4 | Validation harness | Product | x | | | | | 4 h | Should |
| L13 | Counterparty resolver | Logic | | | x | | x | 2 h | Should |
| L15 | Deadline tracker | Logic | | | x | | | 1 h | Should |
| L5 | NGSO worst-case pfd | Logic | x | | | x | | 4 h | Could |
| L7 | Special-interest screening | Logic | x | | x | x | | 5 h | Could |
| L12 | Trend and anomaly detector | Logic | | x | x | | | 3 h | Could |
| A2 | Correspondence drafter | AI | | | x | | | 4 h | Could |
| L1 | IFIC watcher | Logic | | x | x | | | 2 h | Could |
| P3 | Watch mode and digest | Product | | | x | | | 2 h | Could |
| L6 | Finnish satellite protection | Logic | | | x | x | | 4 h | Could (needs SRS) |
| A3 | Special-section PDF reader | AI | | | x | | x | 4 h | Could |
| A4 | Regulation interpreter | AI | | | | x | x | 3 h | Stretch |
| A5 | Feedback ranking | Logic | | | x | | | 3 h | Stretch |
| A6 | Scoped question box | AI | | | x | | | 3 h | Stretch |
| A7 | Neighbourhood digest | AI | | x | x | | | 1 h | Stretch |
| P5 | Submission pack | Product | x | | | | x | 3 h | Must (Sunday) |

---

## 5. One architecture for space and terrestrial (criterion B)

The side quest must "show that the same workflow can support a different context". The pipeline has the same stages in both domains; only two stages have domain-specific implementations.

| Stage | Space | Terrestrial | Shared code |
|---|---|---|---|
| Fetch | `ific<NNNN>.zip` | `brific<NNNN>.zip` | L1 |
| Ingest | SNS tables (2.2) | FXM tables (2.3) | L2 adapter interface, SQLite per issue |
| Normalise | `Notice` from `notice`, `grp`, `emiss`, `geo`, `orbit` | `Notice` from `fxm_terra`, `fxm_geo`, `fxm_ant` | One model, one provenance scheme |
| What changed | Part I-S symbols A, M, N, R, S, W | `intent` plus the diff of consecutive issues | L8 generalised: both are "compare issue N with N−1" |
| Relevance | L3 (band overlap, service area, visibility, affected list) | L9 (band overlap, neighbour, station class, distance) | Interval index, geometry helpers, Traficom API client |
| Framework | RR Article 21 and Article 5, M4 | T/R 25-08, ECC recommendations, M4, bilateral | L10 rule table with a `domain` column |
| Technical calculation | pfd (L4, L5) | P.1546 field strength (L11) | Same "calculation record" structure: inputs, formula, parameters, result |
| Criterion | Table 21-4 limit and margin | Threshold at the border and margin | Same margin semantics |
| Findings and provenance | | | L14 |
| Trends | By administration, band, orbit class | By administration, band, station class, geography | L12 with different dimensions |
| Explain, draft, review | | | A1, A2, L13, L15, P2 |

Extension to a third context later (for example terrestrial fixed links or broadcasting under GE06) means a new relevance rule set and a new calculation module; everything else is reused.

---

## 6. Recommended build order for the 48 hours

Doc 05 owns the schedule and gate times. This section only says which catalogue items fit each gate.

Friday night to Saturday 09:00 (Gate 2): L2 on both zips, L3 and L9 with the Traficom table, L8, L14, P1. Outcome: the tool processes 3074 and 3076 end-to-end and prints ranked candidates with evidence, no calculations yet. Show this at the Q&A and ask the questions in section 7.

Saturday 09:00 to 16:00 (Gate 3): L4 with the transcribed Table 21-4, L11 with `Py1546` validated, L10, A1, P2, P4. Outcome: findings carry pfd or field-strength margins with parameters and citations.

Saturday 16:00 to Sunday 02:00 (Gate 4): L13, L15, L5, L12, A2, L1, P3; L6 and L7 if the SRS and the XLS are available. Freeze.

Sunday: P5, re-run both issues from scratch, check the hashes match, record the video in Demo Mode.

Roles (four people): BE takes L2, L8, L9, L1; AI takes L4, L5, L11, A1, A2; FE takes P2, P3; PM takes L10, L13, Table 21-4 transcription, P4, P5 and the Q&A.

---

## 7. New questions for the Saturday Q&A

Doc 01 holds the master list (Q1–Q18). The items below sharpen existing questions or add new ones; the doc 01 number each belongs to is in brackets.

1. [Q8, new detail] Can you give us `SRS_IFIC3074.mdb` (both parts) or a SpaceQry export of all Finnish networks and of all networks in the bands you care about? Without it, L6 runs on Part II-S of 2026 only.
2. [Q2, new detail] Which Radio Regulations edition should Table 21-4 be taken from (we assume the 2024 edition), and do you apply any national pfd or field-strength limits beyond it (for example from the special-interest list)?
3. [Q12, new detail] For T/R 25-08 at sea borders: coastline or maritime boundary, and do your bilateral agreements with Sweden, Norway, Russia and Estonia change the thresholds, time percentage (10 %) or receiving height (10 m)?
4. [Q11, new detail] Which notice types count as "land-mobile notices" for the 3076 evaluation: T12 base stations only, or also T13 receiving stations and T14 typical stations?
5. [Q3, already covered] What should the separate results file for 3074 and 3076 look like: one row per notice, or one row per finding, and which columns do you need to score accuracy?
6. [Q4, already covered] The XLS: exact columns, and does each station carry a protection threshold or do you expect us to derive one?
7. [Q1 and Q10, already covered] Which special sections matter most to you in practice: API/A, CR/C, AP30B, or Part I-S notifications? And what does a specialist actually send after review (comment under No. 9.3, disagreement under No. 9.52, informal letter)?

---

## 8. Formula sheet (deterministic components)

All constants and formulas live in code with these names so that the finding records can cite them.

**Geometry, GSO.** Earth radius R = 6 378 km, GSO radius r = 42 164 km. For a ground point at latitude φ and longitude λ and a satellite at longitude L:

```
cos γ   = cos φ · cos(L − λ)                      # central angle
el      = atan2(cos γ − R/r, sin γ)                # elevation; visible when el ≥ 0
d       = sqrt(R² + r² − 2·R·r·cos γ)              # slant range
```

Worked example `[ESTIMATE]`: Helsinki (60.17° N, 24.94° E), satellite at 25° E: γ = 60.17°, el = 21.7°, d = 39 382 km. Spreading loss 10·log10(4π·d²) with d in metres = 162.9 dB.

**pfd, single entry, free space.**

```
pfd[dBW/m²/B_ref] = pwr_ds_max[dBW/Hz] + 10·log10(B_ref[Hz]) + gain[dBi] − 10·log10(4π·d²[m²])
limit(δ)          = L0                       for 0° ≤ δ < 5°
                  = L0 + k·(δ − 5)           for 5° ≤ δ < 25°      # k = 0.5 or 0.75 per row
                  = L25                      for 25° ≤ δ ≤ 90°
margin            = limit(δ) − pfd           # negative means the limit is exceeded
```

Worked example `[ESTIMATE, limit row to verify]`: `pwr_ds_max` = −55 dBW/Hz, gain 36 dBi, B_ref = 4 kHz, d = 39 382 km gives pfd = −145.9 dB(W/m²) per 4 kHz; at δ = 21.7° the 10.7–11.7 GHz row gives −141.6, so the margin is +4.3 dB (compliant).

**NGSO visibility.** A satellite at apogee altitude h and inclination i can be above the horizon of latitude φ only if `i + arccos(R / (R + h)) ≥ φ`. Example: h = 550 km gives 23.0°, so i = 53° reaches 76.0° N and covers Finland; i = 30° at the same altitude reaches 53.0° N and never does.

**NGSO worst-case distance.** `d_nadir = perig_km`; at elevation el: `d = sqrt(R² + (R + perig)² − 2·R·(R + perig)·cos γ)` with γ from `el` by inverting the elevation formula.

**P.1546 inputs from a terrestrial notice.**

```
erp[dBW]   = pwr_ant[dBW] + gain_max[dBi] − 2.15          # if gain_type is dBd, drop the −2.15
E[dBµV/m]  = E_P1546(f, d, h1, h2 = 10 m, t = 10 %, q = 50 %, path) + (erp[dBW] − 30)   # curves are for 1 kW e.r.p.
E_25       = E − 10·log10(B / 25 kHz)   if B > 25 kHz and the spectrum is uniform, else E
margin     = threshold(band) − E_25     # thresholds in section 2.4; negative means coordination needed
```

`h1` is `eff_hgt` at the path azimuth from `fxm_ant_hgt`, else `eff_hgtmax`, else a flagged fallback. Necessary bandwidth B comes from `bdwdth`, else from the emission designator (`16K0F3E` = 16.0 kHz).

**Distance and azimuth** on the WGS-84 ellipsoid with `pyproj.Geod.inv`; border points sampled every 5 km along the Finnish boundary layer chosen in L11.

---

## 9. Assumption and decision log

| # | Assumption or decision | Basis | Revisit when |
|---|---|---|---|
| 1 | The free space zip holds the circular database, not the full SRS | ITU demowic page: "Space circular databases ... contain SNS data of Part-IS, Part-IIS, Part-IIIS and Special Sections API/A and CR/C"; full SRS "only available in the BRIFIC" | After unzipping 3074 |
| 2 | `mdbtools` can read the files on macOS and Linux | Access JET4 format is standard; the SRS note says Access 2000 format | Friday night smoke test |
| 3 | Direct calculation logic instead of GIBC | Brief allows "or direct calculation logic"; ITU tools are Windows GUI only | If Traficom can run GIBC for a golden case, use it as a test, not as the engine |
| 4 | 10 % time, 50 % locations, 10 m height, 25 kHz, border line | T/R 25-08 Annex 1 defaults | Q&A question 3 |
| 5 | Pre-filter radii 200 km land, 300 km sea | Order of magnitude from P.1546 1 kW curves | After the first full L11 run; log the change |
| 6 | Table 21-4 from the RR 2024 edition | Latest edition | Q&A question 2 |
| 7 | LLM output is cached and reproduced from cache during the demo | Reproducibility criterion | Never for the demo |
| 8 | Schema versions: v10 native, v9.1 mapped, older unsupported unless supplied | ITU version history | If Traficom supplies pre-2025 issues |
