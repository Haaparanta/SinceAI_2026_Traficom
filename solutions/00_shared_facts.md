# Shared facts and evidence base

> [!NOTE]
> Written on 6 November 2026, before any partner data from the Since AI platform was seen. This file is the common evidence base for the five solution plans in this folder. Tag convention: `[BRIEF]` = stated in the official challenge brief (`00_challenge_brief_text.md`); `[README]` = repo README; `[FACTS]` = verified in an earlier session on this repo, with the source URL; `[HYPOTHESIS]` = reasoned from general knowledge of the ITU and CEPT processes but not verified for this challenge; `[GAP - ASK PARTNER]` = must be asked at the Q&A stand. Replace hypotheses with verified facts as answers arrive, and keep the URL.

---

## 1. The brief in one checklist

**Mandatory inputs** `[BRIEF]`

| Input | Where | What must be true |
|---|---|---|
| ITU Space BR IFIC | https://www.itu.int/en/ITU-R/space/brific/Pages/default.aspx and https://www.itu.int/sns/wic/demowic.html | All existing and forthcoming IFICs must be evaluable; **Space IFIC 3074** must be analysed, concerns raised, results submitted as a separate file (accuracy evaluation) |
| ITU Terrestrial BR IFIC | https://www.itu.int/en/ITU-R/terrestrial/brific/Pages/default.aspx | All existing and forthcoming IFICs evaluable; **Terrestrial IFIC 3076** analysed, concerns raised, results in a separate file |
| Regulation 4 (M4), Finnish table of frequencies | https://www.finlex.fi/fi/viranomaiset/maarayskokoelmat/traficom-viestinta/2026/3 and the API https://opendata.traficom.fi/api/v13/Taajuusjakotaulukko | Used for every comparison and interference recognition |
| Synthetic table of frequencies of special interest (XLS) | Since AI platform | Station number, frequency range (bandwidth and centre), coordinates, antenna height, direction, directivity and more |

**Optional inputs** `[BRIEF]`: ITU space software (https://www.itu.int/en/ITU-R/software/Pages/space-network-software.aspx), Regulation 15 (M15, licence-exempt), CEPT implementation status (https://docdb.cept.org/implementation/overview), ITU Radio Regulations (https://www.itu.int/pub/r-reg-rr).

**Space workflow steps** `[BRIEF]`: ingest national frequency information; detect, retrieve and ingest new IFICs (API/A, CR/C, AP30 incl. AP30A and AP30B); identify interesting satellite systems (SpaceCom or direct database logic); calculate pfd (GIBC or direct calculation); summarise relevant content and frequency ranges affecting Finland; cross-compare with M4, M15 and the additional tables; identify items that may concern Finland; detect and explain concerns with calculations; identify the counterparty administration and draft correspondence for expert review.

**Terrestrial side quest** `[BRIEF]`: consecutive terrestrial IFICs, identify new, modified and withdrawn; filter foreign land-mobile assignments relevant to Finland; determine the ITU, CEPT/ECC and national framework; identify the criterion (for example ECC T/R 25-08); deterministic field-strength calculation with ITU-R P.1546; expert-reviewable findings with source notice, field strengths, model parameters, assumptions and citations; plus a small number of trends or anomalies in neighbouring administrations' notices (band, geography, station class, bandwidth).

**Evaluation weights** `[BRIEF]`: A technical analysis and reproducibility 25; B extensibility and terrestrial side quest 25; C workflow usefulness, innovation and output quality 20; D case recognition accuracy and relevance 15; E auditability and evidence quality 15.

**Submission** `[BRIEF]`: a demo, the ability to process IFIC files into relevant output using the Finnish usage information, the processed Space IFIC 3074 and Terrestrial IFIC 3076 as separate files, information on input and output, the code repository, other documentation.

**Timeline** `[README pm_pack]`: build starts Fri 6 Nov 19:30; internal FINAL Sun 8 Nov 09:15; hard deadline Sun 10:00. Q&A stand Sat 09:00-12:00 and 14:30-18:00; senior space IFIC specialists Sat 10-11 and 17-18; terrestrial Sat 11-12 and 16-17; Discord preferred `[BRIEF]`.

---

## 2. Space BR IFIC

| Fact | Tag |
|---|---|
| Space BR IFIC 3074, the accuracy-evaluation issue, was published on 2026-06-23. | `[FACTS]` |
| Comment windows are four months from publication: RR No. 9.3 for API/A, RR No. 9.52 for CR/C, AP30 Article 4.1.5 for the plan sections. For items published in IFIC 3074 the windows closed around 2026-10-23, so the 3074 deliverable is an accuracy exercise, not a live deadline. | `[FACTS]` for the windows; the derived date is arithmetic |
| The Space IFIC ships the SRS-format Microsoft Access database. Tables: `notice`, `grp`, `freq`, `s_beam`, `emiss`, `geo`, `orbit`, `non_geo`, `srv_area`, `srv_cls`, `provn`, `pub_ssn`. Description: https://www.itu.int/en/ITU-R/software/Documents/spaceqry/srs_dbv6.pdf | `[FACTS]` |
| Likely roles of those tables: `notice` one row per notice (notice id, administration, satellite name, notification reason, nominal longitude for GSO, date received); `grp` frequency groups per beam (group id, notice id, beam name, emission or reception, min and max frequency, noise temperature); `freq` assigned frequencies per group; `s_beam` satellite beams (beam name, direction, maximum gain); `emiss` emissions per group (designation of emission, maximum power density per Hz, peak and total power); `geo` and `srv_area` geographical areas and service areas by ITU area codes; `orbit` GSO orbital data; `non_geo` NGSO orbital planes (altitude, inclination, number of satellites); `srv_cls` class of station and nature of service; `provn` the RR provisions under which the notice was submitted (for example 9.1, 9.6, 11.2, AP30); `pub_ssn` the special-section references under which the notice was published (for example API/A, CR/C, AP30/E). Field names must be taken from the srs_dbv6.pdf document, not from memory. | `[HYPOTHESIS]` |
| Special sections of interest: API/A (advance publication, RR 9.1), CR/C (coordination request, RR 9.6), AP30/E and AP30A/E (BSS Plan and feeder-link Plan, Regions 1 and 3), AP30B (FSS Plan). The meaning and relevance of CR/D, CR/E and CR/F sections is an open item from the earlier scoring work. | `[HYPOTHESIS]`, `[GAP - ASK PARTNER]` |
| The BR IFIC is published every two weeks (the brief says "bi-monthly"; ITU's own description is fortnightly). | `[HYPOTHESIS]` |
| Where the list of administrations identified as affected for a CR/C notice sits in the SRS database is not yet known. | `[GAP - ASK PARTNER]` |
| Which ITU geographical-area codes cover Finland (country symbol FIN, regional codes, "Region 1", worldwide) is not yet known. | `[GAP - ASK PARTNER]` |
| ITU space tools (Windows applications shipped with the IFIC): SpaceQry (query the SRS database), SpacePub (browse publications), SpaceCom (prepare and submit comments on API/A and CR/C special sections under 9.3 and 9.52), GIBC (Graphical Interference Batch Calculation: Appendix 7 contours, Appendix 8 examinations, pfd examinations under Article 21, AP30/30A/30B examinations), SpaceCap (capture notices), SpaceVal (validate), GIMS (graphical data such as service areas and antenna gain contours). Whether batch or command-line modes exist is unverified. | `[HYPOTHESIS]`; page https://www.itu.int/en/ITU-R/software/Pages/space-network-software.aspx `[BRIEF]` |
| What the demowic.html page offers (full IFIC with database, sample only, TIES login, download size) is unverified. | `[GAP - ASK PARTNER]`, check on Friday night |

---

## 3. Terrestrial BR IFIC

| Fact | Tag |
|---|---|
| Since IFIC 3042 (2025-03-18) the Terrestrial BR IFIC database is SQLite: `BRIFIC_nnnn.db3` (TerRaBase). The FXM domain tables are `fxm_terra`, `fxm_ant`, `fxm_tx`, `fxm_rx`, `fxm_geo`. Documentation: https://www.itu.int/ITU-R/terrasys/docs/db/structure | `[FACTS]` |
| Land-mobile notices use the T12 item keys, for example `t_freq_assgn`, `t_lat` (format +DDMMSS), `t_pwr_dbw` with `t_pwr_eiv`, `t_hgt_agl`, `t_azm_max_e`. | `[FACTS]` |
| Terrestrial IFIC 3076 publication date: not verified. If the fortnightly cadence held from 3042 (2025-03-18), 3076 would fall in July 2026, give or take two weeks because the Bureau skips issues around holidays. | `[HYPOTHESIS]` |
| Parts of a terrestrial IFIC: notices received (Part I), assignments recorded with favourable finding (Part II), unfavourable findings (Part III), plus special sections for the regional plans (GE06 and others). Action codes (add, modify, suppress) and the notice status field identify what is new, modified or withdrawn between issues. | `[HYPOTHESIS]` |
| Neighbouring administrations for Finland and their ITU symbols: Sweden S, Norway NOR, Estonia EST, Russian Federation RUS; also relevant across the Baltic: Latvia LVA, Lithuania LTU, Denmark DNK, Germany D, Poland POL. Finland is FIN. | `[HYPOTHESIS]`, symbols are standard ITU usage |
| Terrestrial tools: TerRaQ (query), TerRaNotices (prepare notices), TerRaNV (validation), eTerrestrial (web). Batch modes unverified. | `[HYPOTHESIS]` |
| Reading the terrestrial database needs only Python's standard `sqlite3` module. | `[FACTS]` (SQLite format) |

---

## 4. Finnish and European regulatory sources

| Fact | Tag |
|---|---|
| The Finnish table API https://opendata.traficom.fi/api/v13/Taajuusjakotaulukko returns 5,917 rows as OData with `$top` and `$skip` paging. In the `Services_in_Finland` field, services written in capitals are primary, lower case are secondary (ITU convention). A snapshot taken on 2026-11-06 lives on branch `claude/folder-scoring-system-a430c2` at `scoring/reference/taajuusjakutaulukko_2026-11-06.json.gz` (check the exact file name on that branch). | `[FACTS]` |
| Other likely fields: lower and upper frequency, the ITU Region 1 allocation, Finnish usage or application, footnotes, remarks in Finnish, Swedish and English. Confirm against the Swagger page https://opendata.traficom.fi/swagger/ui/index#/Taajuusjakotaulukko. | `[HYPOTHESIS]` |
| Finland is in ITU Region 1; the Finnish table follows the RR Article 5 allocation table with national footnotes. | well-known `[HYPOTHESIS]` |
| Regulation 15 (M15) covers collective frequencies for licence-exempt transmitters; the brief marks it as less relevant. | `[BRIEF]` |
| ECC/ERC Recommendation T/R 25-08, edition of June 2025, https://docdb.cept.org/download/4789. Annex 1 coordination trigger field strengths at 10 m above ground, 10 percent of time, referred to 25 kHz: 0 dBuV/m for 29.7-47 MHz, 6 dBuV/m for 47-108 MHz, 12 dBuV/m for 108-380 MHz, 18 dBuV/m for 380-400 MHz, 20 dBuV/m for 400-470 MHz, each increased by 10 log10(channel bandwidth / 25 kHz). | `[FACTS]` |
| T/R 25-08 is titled "Planning criteria and coordination of frequencies in the land mobile service in the range 29.7-921 MHz"; the trigger values above 470 MHz and the exact reference geometry (field strength at the border line versus at a distance inside the neighbouring country, 50 percent of locations) must be read from the document. | `[HYPOTHESIS]` |
| Bilateral agreements between Finland and Sweden, Norway, Estonia or Russia may override T/R 25-08 for specific bands. | `[GAP - ASK PARTNER]` |
| CEPT docdb implementation overview lists, per ECC Decision and Recommendation, each country's implementation status; useful for the "applicable CEPT/ECC framework" step of the side quest. Export or API availability is unverified. | `[BRIEF]`, `[HYPOTHESIS]` |

---

## 5. Calculation methods

### 5.1 pfd from a satellite filing (textbook, no URL needed)

pfd at the Earth's surface in dB(W/m2) per reference bandwidth:

```
pfd = EIRP_density_dBW_per_refBW - 10 * log10(4 * pi * d^2)
```

where `d` is the slant range in metres and the EIRP density per reference bandwidth comes from the filed maximum power density per Hz (`emiss`, dBW/Hz, `[HYPOTHESIS]` field) plus the beam gain in the direction of the point (`s_beam` maximum gain as the worst case) plus 10 log10(reference bandwidth in Hz). Spreading loss at the GSO nadir distance of 35,786 km is 162.1 dB(m2); it grows to about 163.3 dB at the horizon (slant range 41,679 km).

GSO geometry for a ground point at latitude `lat`, longitude `lon` and a satellite at nominal longitude `lon_s`, with `R_e = 6371 km` and `r_gso = 42164 km`:

```
cos(gamma) = cos(lat) * cos(lon - lon_s)              # central angle
d          = sqrt(R_e^2 + r_gso^2 - 2 * R_e * r_gso * cos(gamma))
elevation  = atan2(cos(gamma) - R_e / r_gso, sin(gamma))
```

A GSO satellite is below the horizon (elevation below 0) for points with `gamma` greater than about 81.3 degrees. From southern Finland (60 N) the maximum elevation towards a GSO satellite at the same longitude is roughly 23 degrees, and from Utsjoki (70 N) roughly 12 degrees; GSO filings are therefore evaluated mostly in the low-elevation rows of the pfd tables. `[HYPOTHESIS]` for the exact numbers, arithmetic from the formulas above.

NGSO: the filing gives orbital planes, altitude and inclination (`non_geo`, `[HYPOTHESIS]`); a worst-case screening uses the minimum slant range at the minimum operating elevation declared in the filing, or the altitude itself if nothing else is given, and labels the result "worst case".

### 5.2 Limits compared against

| Limit | Tag |
|---|---|
| RR Article 21, Table 21-4: pfd limits for space stations in bands shared with terrestrial services as a function of the angle of arrival (0-5, 5-25, 25-90 degrees) and a reference bandwidth (4 kHz or 1 MHz). Example often quoted: 3400-4200 MHz, -152 dB(W/m2) per 4 kHz for 0-5 degrees, rising linearly to -142 at 25 degrees. Rows in the earlier scoring reference file are partly marked `verified: false`; every row used must be checked against the RR text. | `[HYPOTHESIS]`, https://www.itu.int/pub/r-reg-rr `[BRIEF]` |
| Appendix 30 (BSS Plan, Regions 1 and 3) and Appendix 30A (feeder links) carry their own pfd and power limits in their annexes; Appendix 30B is the FSS Plan (4500-4800, 6725-7025, 10.70-10.95, 11.20-11.45, 12.75-13.25 MHz bands). | `[HYPOTHESIS]` |
| Article 22 epfd limits apply to NGSO FSS systems and are time-statistical; out of scope for a deterministic hackathon screening unless the specialists ask for it. | `[HYPOTHESIS]` |
| Appendix 5 coordination thresholds (for example delta T/T 6 percent under RR 9.7, pfd thresholds under 9.11, 9.14 and 9.21) decide whether an administration is "affected". | `[HYPOTHESIS]` |

### 5.3 ITU-R P.1546 for the terrestrial side quest

| Fact | Tag |
|---|---|
| P.1546 is the ITU-R point-to-area prediction method for terrestrial services from 30 MHz to 4 GHz, distances 1 to 1,000 km, giving field strength in dB(uV/m) for 1 kW e.r.p. at a receiving antenna height of 10 m as a function of distance, frequency (curves at 100, 600 and 2,000 MHz with interpolation), transmitting antenna effective height `h1`, time percentage (1, 10, 50 percent) and path type (land, cold sea, warm sea), with corrections for receiver height, location variability and mixed paths. | `[HYPOTHESIS]`, verify against the current edition at https://www.itu.int/rec/R-REC-P.1546 |
| Reference implementations by the ITU-R Study Group 3 contributor Ivica Stevanovic exist on GitHub (MATLAB P1546 and a Python port, repository names of the form `eeveetza/Py1546`), with ITU validation examples. Verify the URL and licence before use. | `[HYPOTHESIS]` |
| Scaling: `E = E_1kW + 10 log10(e.r.p. in kW)`; the field strength to pfd relation is `pfd dB(W/m2) = E dB(uV/m) - 145.8`. | textbook |
| T/R 25-08 inputs needed per notice: frequency, e.r.p. (from `t_pwr_dbw` with `t_pwr_eiv`), antenna height above ground (`t_hgt_agl`) and terrain for `h1`, azimuth of maximum radiation (`t_azm_max_e`), coordinates (`t_lat`, longitude), channel bandwidth from the emission designator. | `[FACTS]` for the keys, `[HYPOTHESIS]` for the mapping |

---

## 6. Expert process

| Fact | Tag |
|---|---|
| Article 9 stages for space networks: advance publication (RR 9.1-9.3, comments within four months, API/A special section), coordination (RR 9.6 and following, CR/C special section, requests to be included under 9.41/9.42, comments and disagreement under 9.52 within four months), notification and recording (Article 11, Parts I-S, II-S, III-S). Plan sections follow AP30, AP30A and AP30B Article 4 procedures. | `[FACTS]` for the four-month windows, `[HYPOTHESIS]` for the rest |
| A CR/C special section lists, per RR provision, the administrations the Bureau identified as affected; Finland appearing in that list is a strong relevance signal, Finland missing from it despite a pfd exceedance is a finding worth a letter. | `[HYPOTHESIS]`, `[GAP - ASK PARTNER]` |
| Typical content of correspondence to another administration: the network name and administration, the special-section reference and IFIC number, the frequency bands and beams concerned, the Finnish assignments or usage affected with the M4 reference, the calculated pfd or field strength versus the applicable limit with the assumptions, the request (inclusion in coordination under 9.41, a 9.52 comment, a technical modification, or a reservation of rights), the contact details and the deadline. | `[HYPOTHESIS]` |
| Finnish satellite networks and operators that may need protection (ICEYE, Kuva Space, Aalto University small satellites; networks may be filed through other administrations) and Finnish terrestrial services sensitive to space interference (Metsähovi radio observatory near 60.22 N 24.39 E, FMI weather radars, Virve PPDR at 380-400 MHz, mobile broadband bands including 3400-3800 MHz and 26 GHz, broadcasting, GNSS, defence). | `[HYPOTHESIS]`, `[GAP - ASK PARTNER]` for the authoritative list |
| An existing scoring package on branch `claude/folder-scoring-system-a430c2` (worktree `.claude/worktrees/folder-scoring-system-a430c2`): `score = 100 x relevance x (0.65 severity + 0.35 urgency)`, `relevance = freq_overlap x geography x direction` (multiplicative gates), priority A at 70 and above, B at 45, C at 20; weights in `scoring/weights.json`, reasoning in `scoring/DESIGN.md`, 52 unit tests, no P.1546 implementation yet; the terrestrial field-strength factor is screening-only. | `[FACTS]` |

---

## 7. Libraries and tooling

| Need | Option | Tag |
|---|---|---|
| Read the SRS Access database on macOS or Linux | `mdbtools` (`brew install mdbtools`; `mdb-tables`, `mdb-export` to CSV), `pandas-access` as a wrapper, `access-parser` (pure Python, read-only), UCanAccess (Java JDBC) | `[HYPOTHESIS]` |
| Read the terrestrial database | Python `sqlite3` | `[FACTS]` |
| Analytics store | DuckDB (reads CSV, Parquet and SQLite directly, spatial extension) or SQLite | `[HYPOTHESIS]` |
| Geospatial | GeoPandas, Shapely, pyproj, H3; Finland boundary from Natural Earth admin-0 or GADM; Finnish NLS open data for higher detail | `[HYPOTHESIS]` |
| Propagation | A P.1546 port (see 5.3); for checks, `pycraf` implements P.452 | `[HYPOTHESIS]` |
| Excel | `openpyxl` or `pandas.read_excel` | standard |
| LLM | Claude API with structured outputs (`claude-sonnet-5-5`, `claude-opus-5-5`); keep a provider-agnostic client so a local open-weight model can replace it if the partner requires | `[README pm_pack]` |
| Map UI | MapLibre GL with the design tokens in `design/girlypop.css`; or a Python-side Folium or pydeck export | `[README design]` |

---

## 7a. Verified updates from the main branch (supersede the hypotheses above where they differ)

After this file was first written, the branch was synced with `main`, which now carries `pm_pack/07_Solution_Catalogue.md` (schema names checked against the ITU Preface), `data/SOURCES.md` (every dataset downloaded on 6 Nov 2026 with URLs, sizes and dates), `pm_pack/06_AGENTS_Master_Context.md` (rules and contracts) and `scoring/` (the deterministic scorer). Facts below are `[FACTS: pm_pack/07]` or `[FACTS: data/SOURCES.md]` and override sections 2 to 5 and 7 where they differ.

| Topic | Verified fact |
|---|---|
| Issue numbering and dates | Space and terrestrial IFICs share the issue number and date: 3074 = 23 Jun 2026 (space graded issue), 3076 = 21 Jul 2026 (terrestrial graded issue), 3075 = 7 Jul 2026, 3083 = 27 Oct 2026 (latest at download). Fortnightly, Tuesdays. |
| Space download | `https://www.itu.int/sns/ific10/ific<NNNN>.zip` (no login seen; 2026 list at `demowic26.html`, issues 3062-3083). 3074 is 60.8 MB zipped and unpacks to one `ific3074.mdb` of 287 MB (Access, SNS schema v10, used since 7 Jan 2025). It is the circular database (Parts I-S, II-S, III-S plus special sections), not the full SRS; the full `SRS_IFIC<NNNN>.mdb` (over 2 GB, two parts) needs registered access. |
| Space tables (SNS v10) | `notice` (`ntc_id`, `adm`, `ntwk_org`, `ntc_type` G/N/S/T/R, `ntf_rsn`, `prov`, `act_code`, `d_rcv`, `wic_no`, `wic_part`, `d_wic`), `geo` (`sat_name`, `long_nom`), `non_geo`, `orbit` (`nbr_sat_pl`, `inclin_ang`, `apog_km`, `perig_km`), `phase`, `s_beam` (`beam_name`, `emi_rcp`, `gain`), `grp` (`grp_id`, `freq_min`, `freq_max`, `bdwdth`, `emi_rcp`), `assgn` (assigned frequency, declared `pfd`), `emiss` (`design_emi`, `pep_max`, `pwr_ds_max` dBW/Hz), `srv_area` (`ctry`), `srv_cls`, `e_as_stn`, `e_ant`, `mask_info`, `provn`, `all_aff_ntw`, `tr_aff_ntw`, `pub_ssn`. `com_el` and `freq` are marked BR-internal: do not build on them. Part I-S action symbols: A new, M modification, N non-basic change, R resubmission, S suppression, W withdrawn. All names still go through `backend/radar/schema_map.yaml` until `scripts/inspect_mdb.py` has printed the real schema. |
| Terrestrial download | `https://www.itu.int/en/ITU-R/terrestrial/brific/BRIFIC/MDB/brific<NNNN>.zip` (2.4 MB for 3076, 3.4 MB for 3075; ten latest issues listed, 3074-3083 downloaded). Each zip holds one `brific<NNNN>.mdb` (Access, 25-33 MB) with the Article 11 notices of Parts 1 to 3. The full TerRaBase (`BRIFIC_<NNNN>.db3`, SQLite) is not in the free extract. 3076 counts: Part I 2,415, Part II 1,051, Part III 44. |
| Terrestrial tables (FXM) | `fxm_terra` (`terrakey`, `fragment`, `adm`, `freq_assgn`, `freq_min`, `freq_max`, `bdwdth`, `emi_cls`, `stn_cls`, `notice_typ`, `intent` = ADD, MODIFY, SUPPRESS, WITHDRAW, `d_rcv`, `geo_key`, `assgn_id`, `adm_ref_id`), `fxm_geo` and `fxm_geo_pt` (`ctry`, `site_name`, `long_dec`, `lat_dec`, `site_alt`), `fxm_ant` (`pwr_ant`, `gain_max`, `gain_type`, `ant_dir`, `azm_max_e`, `hgt_agl`, `eff_hgtmax`, `polar`), `fxm_ant_hgt` (`azm`, `eff_hgt`: the P.1546 input), `fxm_ant_diag`, `fxm_coord`, `fxm_pub_hist`. Notice forms T11 fixed, T12 other transmitting stations (land-mobile base stations), T13 receiving land station, T14 typical station, T17 adaptive. Station classes FB, FL, ML, MO, FX. |
| Finnish table API | 24 columns incl. `ID`, `Sub_band_lower_limit__Hz_`, `Sub_band_upper_limit__Hz_`, `Services_in_Finland`, `Sub_band_usage`, `Class_of_station`, `Direction`, `Radiated_power`, `Channel_spacing`, `Bandwidth`, `Comment`; 5,917 rows, 4.4 MB, CC BY 4.0; OData `$filter`, `$top`, `$skip` work. M4 is Regulation 4 AG/2026 M of 26 Mar 2026 (table dated 31 Mar 2026). |
| T/R 25-08 | Verified from docdb 2543 (2018 amendment) in `pm_pack/07` section 2.4: thresholds as in section 4 above; co-channel, 50 percent locations, 10 percent time, 10 m receiving height, 25 kHz, evaluated at the border line; preferential regimes 20 dBuV/m per 25 kHz at 40 or 50 km inside the neighbour; wideband 410-430 and 450-470 MHz FDD systems: 55 dBuV/m per 5 MHz at the border and 37 at 10 km inside, at 3 m. Finland is not an HCM Agreement party. |
| Article 21 | Two illustrative rows (to verify before use): 3400-4200 MHz FSS -152 / -152 + 0.75 (delta - 5) / -137 dB(W/m2) per 4 kHz; 10.7-11.7 GHz FSS -150 / -150 + 0.5 (delta - 5) / -140 per 4 kHz. GIBC examines hard limits (Nos. 9.35, 11.31) and triggers (9.11, 9.14, 9.21). |
| ITU tools | SpaceCap, SpaceQry, GIBC, SpaceCom, GIMS: Windows 10/11 GUI applications, 400 MB installer, no documented command line. The catalogue's verdict: not scriptable in 48 hours; use direct calculation logic, which the brief allows, and treat a specialist-run GIBC report as a golden test. |
| P.1546 | `Py1546` (GitHub `eeveetza/Py1546`), Python port of the ITU-R reference MATLAB code with validation examples. |
| Local data | `scripts/fetch_data.sh` and `scripts/download_data.sh` put everything under `data/raw/` (git-ignored); `data/reference/fi_reference_points.csv` has six Finnish reference points; `scoring/` ranks groups and notices with evidence. |
| Rule 8 of the master context | When a task is done: commit, push the branch and open a pull request against `main`; never commit straight to `main`. |

## 8. Contradictions and how they are resolved

- The brief says the IFICs are "bi-monthly"; ITU publishes them every two weeks. The plans assume fortnightly and tag it `[HYPOTHESIS]`.
- The brief says "database format"; the space side is Microsoft Access (SRS) while the terrestrial side has been SQLite since 2025. Both facts are `[FACTS]` above; the plans must handle both formats.
- The repo's PM pack assumed a single-screen product ("Filing Radar") built from the README alone. The brief adds mandatory datasets, calculations and the terrestrial side quest; the plans here supersede the PM pack where they differ.

---

## 9. Open questions for the Q&A stand

**Space IFIC specialists (Sat 10-11 and 17-18)**

1. Which special sections matter most for Finland in practice: API/A, CR/C, AP30/E, AP30A/E, AP30B? What do CR/D, CR/E and CR/F contain?
2. Where in the SRS database are the affected administrations per CR/C notice (table and field)? Which geographical-area codes include Finland?
3. For the pfd check, do you use GIBC or your own calculation? Which reference bandwidth, elevation assumption and Table 21-4 rows do you apply, and how do you treat NGSO systems?
4. Which Finnish satellite networks, earth stations and terrestrial services must be protected? Is there a list we can load?
5. What should the Space IFIC 3074 result file contain: one row per network, per group or per band? Which columns, and in which format (CSV, Excel, PDF memo)?
6. Does the demowic.html download contain the full IFIC with the SRS database, and is a TIES account needed?
7. Can filing data and the synthetic XLS go to a cloud LLM API, or must models run locally?

**Terrestrial IFIC specialists (Sat 11-12 and 16-17)**

1. Which notice types and station classes count as land mobile for the side quest (T12 keys; FB, ML, MO classes)?
2. Which neighbouring administrations matter, and do bilateral agreements with Sweden, Norway, Estonia or Russia override T/R 25-08 in some bands?
3. Where in the db3 are the action codes and notice versions that identify new, modified and withdrawn assignments between two issues?
4. Which P.1546 parameters do you use: time percentage, `h1` definition, land or sea path, receiver height, location percentage?
5. What should the Terrestrial IFIC 3076 result file contain?

**Both**

1. Columns and units of the special-interest XLS, and whether the coordinates are WGS84.
2. One anonymised past example of a concern that led to correspondence, to use as a golden test case.
3. On Sunday, which single output on screen separates first place from second?
