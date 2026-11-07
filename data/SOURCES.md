# Data sources

Everything under `data/raw/` was fetched on **2026-11-06** with [`scripts/download_data.sh`](../scripts/download_data.sh)
([`scripts/fetch_data.sh`](../scripts/fetch_data.sh) is the quick-start wrapper that takes only the graded issues, M4 and the
Finnish table). `data/raw/` is git-ignored; re-create it with either script. SHA-256 checksums of every file are in
[`MANIFEST.sha256`](MANIFEST.sha256) (`cd data && shasum -a 256 -c MANIFEST.sha256`).
"Mandatory" below follows the challenge brief (`Since_AI_Traficom_Challenge_Brief_FINAL_04112026.pdf`, section 05).
Total on disk after the full run: about 720 MB downloaded in 79 files, plus about 340 MB for the three extracted databases.

| In `data/raw/` | What | Mandatory | Origin |
|---|---|---|---|
| `ific<NNNN>.zip`, `ific<NNNN>/ific<NNNN>.mdb` | ITU BR IFIC (Space services) databases, issues 3062-3083 (all 2026 issues) | yes, issue **3074** is the graded issue | ITU-R SNS Online |
| `brific<NNNN>.zip`, `brific<NNNN>/brific<NNNN>.mdb`, `ific<NNNN>_article11.pdf`, `ReadMe_<NNNN>.pdf` | ITU BR IFIC (Terrestrial services) MDB extracts, Article 11 indexes and issue notes, issues 3074-3083 | yes, issue **3076** is the graded issue | ITU-R terrestrial BR IFIC page |
| `SPS_ALL_IFIC<NNNN>.zip`, `SPS_ALL_IFIC<NNNN>/SPS_ALL_IFIC<NNNN>.mdb`, `30B_<NNNN>.zip`, `30B_<NNNN>/30B_<NNNN>.mdb` | ITU Space Plans System (Appendix 30/30A Plans and Lists) and Appendix 30B Plan databases, snapshot **3083** (the only one online), fetched 2026-11-07 | yes: the brief names AP30, AP30A and AP30B, and the IFIC database has no plan data | ITU-R Space Plans pages, [section 1b](#1b-itu-space-plan-databases-ap3030a-and-ap30b---sps_all_ificnnnnzip-30b_nnnnzip) |
| `PREFACE_EN.pdf`, `BR_IFIC_and_other_BR_tools.pdf`, `SRSDiagramV9_1.pdf` | How to read the BR IFIC (Terrestrial), BR tools overview, SRS/SNS table diagram | no | ITU-R |
| `finlex_m4/` | Traficom Regulation 4 "M4", Radio Frequency Regulation 4 AG/2026 M (fi/en/sv + explanatory notes) | yes | Finlex |
| `taajuusjakotaulukko.json` (+ `_fin`, `_swe`), `traficom_swagger_v13.json`, `traficom_metadata_v13.xml` | Finnish table of frequency allocations (API), en/fi/sv, plus the API schema | yes (frequency table) | Traficom open data API v13 |
| `radioasematiedot.json`, `tvasematiedot.json` | Finnish sound-broadcasting and TV station registers | no | Traficom open data API v13 |
| `finlex_m15/` | Traficom Regulation 15 "M15", licence-exempt collective frequencies 15 AV/2025 M | no | Finlex |
| `itu_rr/` | ITU Radio Regulations, 2024 edition, English PDFs (zip) | no | ITU publications |
| `cept/` | CEPT/ECO implementation status exports and ECC document list with frequency ranges | no | ECO documentation database |
| `special_interest.xlsx` | `Traficom_SinceAI_Frequencies_of_interest_v05112026.xlsx`, synthetic Finnish stations to protect, provided by Traficom on 5 Nov 2026 (874 rows; header on row 11: station number, class of licence, WGS84 longitude and latitude, ground and mast height, channel bandwidth, TX and RX frequency, antenna height AGL and ASL, gain, class of transmission, transmission bandwidth, direction, polarisation, radiated power and unit, directivity). SHA-256 `bb7f481f085fb6c457efc04b9b6bb8250c42ea81bab4b4a0e518c93834e03c8a` | yes | Since AI platform; copy it to this path by hand |

## 1. ITU BR IFIC (Space services) - `ific<NNNN>.zip`

* Landing page: <https://www.itu.int/en/ITU-R/space/brific/Pages/default.aspx>
* Download service ("Space Circular Databases Online"): <https://www.itu.int/sns/wic/demowic.html>, yearly listings at
  `https://www.itu.int/sns/wic/demowic<YY>.html` (`demowic26.html` = 2026, `demowic25.html` = 2025).
* File URL pattern: `https://www.itu.int/sns/ific10/ific<NNNN>.zip` (the `ific10` path = Space Network System database **version 10**,
  used for every issue since 7 January 2025).
* Each zip contains exactly one file, `ific<NNNN>.mdb` (Microsoft Access / Jet database; 3074 unpacks to 287 MB, most issues
  70-150 MB). It is the SNS/SRS database published with that issue: Part-IS, Part-IIS, Part-IIIS and the special sections
  (API/A, CR/C, AP30/30A/30B ...) listed in the issue's table of contents. The database must be read together with the Preface,
  Appendix 4 of the Radio Regulations and the SNS database structure definitions valid on the release date
  (`SRSDiagramV9_1.pdf` is the table diagram ITU publishes at <https://www.itu.int/en/ITU-R/space/Documents/SRSDiagramV9_1.pdf>).
* The script extracts `ific3074.zip` to `ific3074/ific3074.mdb` by default (`UNZIP=all` extracts every issue, several GB).
* Only the current and previous year are kept on the web page; older issues come on the BR IFIC DVD (ITU sales).
* Issues downloaded (publication date; ITU numbering is shared with the terrestrial IFIC, but the two are different publications):

| Issue | Date | Issue | Date | Issue | Date |
|---|---|---|---|---|---|
| 3062 | 06.01.2026 | 3070 | 28.04.2026 (corrected re-issue) | 3078 | 18.08.2026 |
| 3063 | 20.01.2026 | 3071 | 12.05.2026 | 3079 | 01.09.2026 |
| 3064 | 03.02.2026 | 3072 | 26.05.2026 | 3080 | 15.09.2026 |
| 3065 | 17.02.2026 | 3073 | 09.06.2026 | 3081 | 29.09.2026 |
| 3066 | 03.03.2026 | **3074** | **23.06.2026** | 3082 | 13.10.2026 |
| 3067 | 17.03.2026 | 3075 | 07.07.2026 | 3083 | 27.10.2026 (latest at download time) |
| 3068 | 31.03.2026 | 3076 | 21.07.2026 | | |
| 3069 | 14.04.2026 | 3077 | 04.08.2026 | | |

* Related ITU resources (not downloaded): space network software SpaceQry / SpaceCom / GIBC
  <https://www.itu.int/en/ITU-R/software/Pages/space-network-software.aspx>; BR IFIC (Space) online query
  <https://www.itu.int/en/ITU-R/space/brific/Pages/brificOnline.aspx>; advance publication (API/A) query per IFIC
  <https://www.itu.int/net4/ITU-R/SpaceWISC/apipub/IFIC/Apic>; publication schedule
  <https://www.itu.int/en/ITU-R/space/brific/Pages/brificSchedule.aspx>.
* Reading `.mdb` files without Windows/Access: `brew install mdbtools` then `python3 scripts/inspect_mdb.py data/raw/ific3074/*.mdb`
  (or `mdb-tables` / `mdb-export` directly); alternatives are Python `pandas_access` or Java `jackcess`.

## 1b. ITU space plan databases (AP30/30A and AP30B) - `SPS_ALL_IFIC<NNNN>.zip`, `30B_<NNNN>.zip`

* Why: in `ific3074.mdb` every plan table (`plan_pub`, `sps_results`, `ap30b_ref_*`, `ap30b_tr_res`) is empty and no notice
  has a `plan_id`. The Appendix 30/30A (broadcasting-satellite and feeder-link) and Appendix 30B (FSS) Plans, their Lists,
  the pending Article 4 / Article 6 networks and the Bureau's examination results are published in two separate SNS v10
  databases on the ITU Plans pages, replaced with every IFIC.
* Pages: <https://www.itu.int/en/ITU-R/space/plans/Pages/AP30-30A.aspx> and <https://www.itu.int/en/ITU-R/space/plans/Pages/AP30B.aspx>.
* Files (snapshot 3083, page dates 27/10/2026):
  * `https://www.itu.int/en/ITU-R/space/plans/Documents/SPS_ALL_IFIC3083.zip`, 72 764 638 bytes -> `SPS_ALL_IFIC3083.mdb`
    (387 MB, 88 tables, 1 770 notices, last export 2026-09-16).
  * `https://www.itu.int/en/ITU-R/space/plans/Documents/30B_3083.zip`, 22 002 409 bytes -> `30B_3083.mdb` (140 MB, 88 tables,
    918 notices, last export 2026-09-24).
* **Only the latest snapshot is online**: `SPS_ALL_IFIC3074.zip` and `30B_3074.zip` answer 404. The script reads the current
  file name from the two pages (`PLAN_IFIC=<n>` overrides it). The exact snapshot of an older issue comes with that issue's
  BR IFIC DVD or ISO (TIES account), so a request to Traficom is the route to the 3074 copy.
* What Finland has in them: FIN10300 and FIN10400 at 22.8 E (AP30 downlink 12.1-12.5 GHz, AP30A feeder link 17.7-18.1 GHz) and
  the AP30B allotment FIN00000 at 46.8 E (4.5-4.8, 6.725-7.025, 10.70-10.95, 11.20-11.45 and 12.75-13.25 GHz).
* Converted with `make convert-plans` to `data/derived/ap30_<n>.duckdb` and `ap30b_<n>.duckdb`; read by `backend/radar/adapters/plans.py`.
  Table and column names are in the `plans` section of `backend/radar/schema_map.yaml`.

## 2. ITU BR IFIC (Terrestrial services) - `brific<NNNN>.zip`, `ific<NNNN>_article11.pdf`, `ReadMe_<NNNN>.pdf`

* Landing page (also the download page): <https://www.itu.int/en/ITU-R/terrestrial/brific/Pages/default.aspx>
* File URL patterns, `<NNNN>` = issue number:
  * MDB extract: `https://www.itu.int/en/ITU-R/terrestrial/brific/BRIFIC/MDB/brific<NNNN>.zip` -> `brific<NNNN>.zip`
  * Article 11 index (PDF): `https://www.itu.int/en/ITU-R/terrestrial/brific/BRIFIC/Article11-Index/ific<NNNN>.pdf` -> `ific<NNNN>_article11.pdf`
  * Issue notes: `https://www.itu.int/en/ITU-R/terrestrial/brific/BRIFIC/ReadMe/ReadMe_<NNNN>.pdf` -> `ReadMe_<NNNN>.pdf`
  * Preface (how to read the BR IFIC): `.../BRIFIC/Preface/PREFACE_EN.pdf`; tool overview `.../BRIFIC/BR_IFIC_and_other_BR_tools.pdf`
* The web page only lists the ten most recent issues; all ten were taken:

| Issue | Date | Issue | Date |
|---|---|---|---|
| 3074 | 23.06.2026 | 3079 | 01.09.2026 |
| 3075 | 07.07.2026 | 3080 | 15.09.2026 |
| **3076** | **21.07.2026** | 3081 | 29.09.2026 |
| 3077 | 04.08.2026 | 3082 | 13.10.2026 |
| 3078 | 18.08.2026 | 3083 | 27.10.2026 (latest at download time) |

* Each MDB extract zip contains exactly one file, `brific<NNNN>.mdb` (Microsoft Access / Jet database, 25-33 MB unpacked). It holds
  the Article 11 notices (Parts 1, 2 and 3) published in that issue, which is where the land-mobile notices for the terrestrial
  side quest live. The script extracts `brific3076` (graded) and `brific3075` (previous issue, for the diff) by default.
* The plan-related special sections published alongside (GE06, GE06L, GE75, GE84, GE85, GE89, RJ81, ST61, RR 9.21) are
  broadcasting/maritime plan modifications and were not downloaded; they are linked from the landing page.
* The full BR IFIC (Terrestrial) ISO image with the complete MIFR requires the ITU TIES/subscription channel and is not included.

## 3. Regulation 4 "M4" - `finlex_m4/`

* Finlex record: <https://www.finlex.fi/fi/viranomaiset/maarayskokoelmat/traficom-viestinta/2026/3>
  (Radiotaajuusmääräys / Radio Frequency Regulation **4 AG/2026 M**, Liikenne- ja viestintävirasto Traficom, 26.3.2026).
* The Finlex page is a JavaScript application; the documents come from its media API
  `https://www.finlex.fi/api/media/authority-regulation/<id>/mainPdf/main.pdf?typeDiscriminator=traficom-communications`
  with id 1070975 (fi), 1070976 (en), 1070974 (sv); the explanatory memoranda are under `.../<id>/media/<file>.pdf`.
* Files: `M4_radiotaajuusmaarays_4AG2026M_fi.pdf`, `M4_radio_frequency_regulation_4AG2026M_en.pdf`,
  `M4_radiofrekvensforeskrift_4AG2026M_sv.pdf`, plus `M4_perustelumuistio_..._fi.pdf` / `M4_explanatory_notes_..._en.pdf` /
  `M4_motiveringspromemoria_..._sv.pdf`.
* The regulation's annex is the Finnish table of frequency allocations (dated 31.03.2026 in the English PDF); the same table is
  available as data from the Traficom API (next section).

## 4. Traficom open data API v13 - `taajuusjakotaulukko*.json`, `traficom_*`, `radioasematiedot.json`, `tvasematiedot.json`

* Swagger UI: <https://opendata.traficom.fi/swagger/ui/index#/Taajuusjakotaulukko>; OData v4 base `https://opendata.traficom.fi/api/v13/`.
  Licence: Creative Commons BY 4.0 (stated in the API description).
* `taajuusjakotaulukko.json` = `GET /api/v13/Taajuusjakotaulukko` (English column values), `taajuusjakotaulukko_fin.json` and
  `taajuusjakotaulukko_swe.json` are the Finnish and Swedish variants of the same 5 917 rows. One full response each (no
  server-side paging was applied); OData query options `$filter`, `$select`, `$top`, `$skip`, `$count` work on the endpoint.
  Columns: `ID, Frequency_band_lower_limit, Frequency_band_upper_limit, Services_in_Finland, Additional_information,
  Sub_band_lower_limit, Sub_band_upper_limit, Sub_band_lower_limit__Hz_, Sub_band_upper_limit__Hz_, Sub_band_width, Sub_band_usage,
  Mode_of_traffic, Class_of_station, Direction, Radiated_power, Transmitter_power, Channel_spacing, Bandwidth, Duplex_separation,
  Duplex_band_lower_limit, Duplex_band_upper_limit, Class_of_emission, Standard_type, Comment`
  (`Sub_band_*__Hz_` are integers in Hz, the other limits are display strings such as `"8.3 kHz"`).
* `traficom_swagger_v13.json` and `traficom_metadata_v13.xml` describe every entity set of the API (also
  `RadiomikrofonitVapaatTaajuudet`, `RadioamatoorienKutsumerkit`, `Meriradionumerot` ...).
* Extras, useful as public Finnish station data on the terrestrial side:
  `radioasematiedot.json` (2 382 sound-broadcasting stations) and `tvasematiedot.json` (1 066 TV stations), both with
  `Municipality, StationName, Frequency (Hz), TransmissionPower (W), AntennaHeight, MaxEffectiveHeight, Polarisation, Latitude,
  Longitude (DDMMSS strings such as "62N5005" / "23E5608"), LicenseNumber, LicenseOwner, Directivity, RadiatedPowerAttenuation_<deg>`.

## 4b. ITU regional broadcasting agreements - `itu_ge/`

| File | Source | Used for |
|---|---|---|
| `R-ACT-RRC.14-2006-PDF-E.pdf` | GE06 Final Acts (RRC-06), https://www.itu.int/dms_pub/itu-r/opb/act/R-ACT-RRC.14-2006-PDF-E.pdf | trigger field strengths, Annex 4 Section I Appendix 1 Table A.1.1 (`data/reference/ge_triggers.csv`) |
| `R-ACT-RRC.5-1984-PDF-E.pdf` | GE84 Final Acts (RRC-84), https://www.itu.int/dms_pub/itu-r/opb/act/R-ACT-RRC.5-1984-PDF-E.pdf | Annex 4 Chapter 1 basis of the FM coordination distances (derived FM trigger) |

## 5. Optional sources

### Regulation 15 "M15" - `finlex_m15/`
<https://www.finlex.fi/fi/viranomaiset/maarayskokoelmat/traficom-viestinta/2025/51209>: "Luvasta vapaiden radiolähettimien
yhteistaajuudet ja käyttö" / Collective Frequencies for Licence-exempt Radio Transmitters and Their Use, **15 AV/2025 M**, 27.3.2025.
Finlex media ids 535594 (fi), 687387 (en), 535595 (sv). Same file naming scheme as M4.

### ITU Radio Regulations 2024 - `itu_rr/`
<https://www.itu.int/pub/r-reg-rr> -> electronic edition <https://www.itu.int/pub/publications.aspx?lang=en&media=electronic&parent=R-REG-RR-2024>.
`R-REG-RR-2024-ZPF-E.zip` is the free English zip of PDFs, 69.6 MB: `RR-Vol 1` (Articles), `Vol 2` (Appendices), `Vol 3`
(Resolutions and Recommendations), `Vol 4` (ITU-R Recommendations incorporated by reference) and `Appendix 27 Maps_2024.zip`.
Other languages: replace `-E` with `-A`, `-C`, `-F`, `-R`, `-S`; `-ZIP-` instead of `-ZPF-` gives the Word version.

### CEPT / ECO documentation database - `cept/`
<https://docdb.cept.org/implementation/overview> (implementation status of ECC Decisions and Recommendations per CEPT country,
Finland included). Exports used:
* `Country_Implementations_Overview.xlsx` = `https://docdb.cept.org/implementation/download`
* `Country_Implementations_Decisions_Overview.xlsx` = `.../implementation/download?documentType=ECC_Decisions`
* `Country_Implementations_Recommendations_Overview.xlsx` = `.../implementation/download?documentType=ECC_Recommendations`
* `ECC_all_documents_with_frequencies.csv` = `https://docdb.cept.org/search/exportall?includeFrequencies=true&includeStandards=true`
  (about 5 800 rows, `;`-separated: `Type; Title; Group; Publish Date; Status; Description; pdf; Landing Page; Low; High; Unit; Application; Standard`,
  one row per document x frequency range, e.g. ECC/DEC/(25)02 862-870 MHz).

## Re-running and adding new IFIC issues

```bash
scripts/fetch_data.sh                             # quick start: graded issues 3074/3076 (+3075), M4, Finnish table, about 75 MB
scripts/download_data.sh                          # everything above (existing files are skipped), about 720 MB
SPACE_IFICS="3084 3085" scripts/download_data.sh  # add new Space IFIC issues as ITU publishes them (every two weeks, Tuesdays)
TERR_IFICS="3084" scripts/download_data.sh        # same for the terrestrial IFIC
UNZIP="ific3083" scripts/download_data.sh         # extract another issue to data/raw/ific3083/ific3083.mdb
PLAN_IFIC=3084 scripts/download_data.sh           # a specific AP30/30A and AP30B snapshot (default: the one the ITU Plans pages link)
```

Notes on fetching: the ITU site sits behind a web application firewall that answers some clients with an HTML "Request Rejected"
page and HTTP 200. Plain `curl` (its default user agent) is accepted; the script verifies that every `.zip`/`.pdf` really is one and
reports a FAILED line otherwise.
