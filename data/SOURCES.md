# Data sources

Everything in this folder was fetched on **2026-11-06** with [`scripts/download_data.sh`](../scripts/download_data.sh).
SHA-256 checksums of every file are in [`MANIFEST.sha256`](MANIFEST.sha256) (`cd data && shasum -a 256 -c MANIFEST.sha256`).
The raw files are git-ignored (see `.gitignore`); re-create them with the script.
"Mandatory" below follows the challenge brief (`Since_AI_Traficom_Challenge_Brief_FINAL_04112026.pdf`, section 05).
Total on disk: about 720 MB in 78 files (space IFICs 532 MB, terrestrial IFICs 73 MB, Radio Regulations 80 MB, the rest 33 MB).

| Folder | What | Mandatory | Origin |
|---|---|---|---|
| `itu_space_ific/` | ITU BR IFIC (Space services) databases, issues 3062-3083 (all 2026 issues) | yes, issue **3074** is the evaluation issue | ITU-R SNS Online |
| `itu_terrestrial_ific/` | ITU BR IFIC (Terrestrial services) MDB extracts, Article 11 indexes and ReadMe notes, issues 3074-3083 | yes, issue **3076** is the evaluation issue | ITU-R terrestrial BR IFIC page |
| `finlex_m4/` | Traficom Regulation 4 "M4", Radio Frequency Regulation 4 AG/2026 M (fi/en/sv + explanatory notes) | yes | Finlex |
| `traficom_opendata/` | Finnish table of frequency allocations (API), en/fi/sv, plus API schema; radio and TV station registers | yes (frequency table) | Traficom open data API v13 |
| `finlex_m15/` | Traficom Regulation 15 "M15", licence-exempt collective frequencies 15 AV/2025 M | no | Finlex |
| `itu_radio_regulations/` | ITU Radio Regulations, 2024 edition, English PDFs (zip) | no | ITU publications |
| `cept_ecc/` | CEPT/ECO implementation status exports and ECC document list with frequency ranges | no | ECO documentation database |
| *(not here)* | Synthetic XLS "table of frequencies of special interest" (station number, centre frequency, bandwidth, coordinates, antenna data) | yes | **SinceAI platform only**, download it by hand into `data/sinceai_platform/` |

## 1. ITU BR IFIC (Space services) - `itu_space_ific/`

* Landing page: <https://www.itu.int/en/ITU-R/space/brific/Pages/default.aspx>
* Download service ("Space Circular Databases Online"): <https://www.itu.int/sns/wic/demowic.html>, yearly listings at
  `https://www.itu.int/sns/wic/demowic<YY>.html` (`demowic26.html` = 2026, `demowic25.html` = 2025).
* File URL pattern: `https://www.itu.int/sns/ific10/ific<NNNN>.zip` (the `ific10` path = Space Network System database **version 10**,
  used for every issue since 7 January 2025).
* Each zip contains exactly one file, `ific<NNNN>.mdb` (Microsoft Access / Jet database; 3074 unpacks to 287 MB, most issues
  70-150 MB). It is the SNS/SRS database published with that issue: Part-IS, Part-IIS, Part-IIIS and the
  special sections (API/A, CR/C, AP30/30A/30B ...) listed in the issue's table of contents. The database must be read together with
  the Preface, Appendix 4 of the Radio Regulations and the SNS database structure definitions valid on the release date.
* Only the current and previous year are kept on the web page; older issues come on the BR IFIC DVD (ITU sales).
* Issues downloaded (publication date, ITU numbering is shared with the terrestrial IFIC, the two are different publications):

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
* Reading `.mdb` files without Windows/Access: `brew install mdbtools` then `mdb-tables file.mdb`, `mdb-export file.mdb <table>`;
  or Python `pandas_access`; or Java `jackcess`.

## 2. ITU BR IFIC (Terrestrial services) - `itu_terrestrial_ific/`

* Landing page (also the download page): <https://www.itu.int/en/ITU-R/terrestrial/brific/Pages/default.aspx>
* File URL patterns, `<NNNN>` = issue number:
  * MDB extract: `https://www.itu.int/en/ITU-R/terrestrial/brific/BRIFIC/MDB/brific<NNNN>.zip` -> `mdb/`
  * Article 11 index (PDF): `https://www.itu.int/en/ITU-R/terrestrial/brific/BRIFIC/Article11-Index/ific<NNNN>.pdf` -> `article11_index/`
  * Issue notes: `https://www.itu.int/en/ITU-R/terrestrial/brific/BRIFIC/ReadMe/ReadMe_<NNNN>.pdf` -> `readme/`
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
  the Article 11 notices (Parts 1, 2 and 3) published in that issue, which is where the land-mobile notices for
  the terrestrial side quest live. The plan-related special sections published alongside (GE06, GE06L, GE75, GE84, GE85, GE89, RJ81,
  ST61, RR 9.21) are broadcasting/maritime plan modifications and were not downloaded; they are linked from the landing page.
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
* The regulation's annex is the Finnish table of frequency allocations; the same table is available as data from the Traficom API (next section).

## 4. Traficom open data API v13 - `traficom_opendata/`

* Swagger UI: <https://opendata.traficom.fi/swagger/ui/index#/Taajuusjakotaulukko>; OData v4 base `https://opendata.traficom.fi/api/v13/`.
  Licence: Creative Commons BY 4.0 (stated in the API description).
* `Taajuusjakotaulukko_en.json` = `GET /api/v13/Taajuusjakotaulukko` (English column values), `_fin.json` and `_swe.json` are the
  Finnish and Swedish variants of the same 5 917 rows. One full response each (no server-side paging was applied); OData query
  options `$filter`, `$select`, `$top`, `$skip`, `$count` work on the endpoint.
  Columns: `ID, Frequency_band_lower_limit, Frequency_band_upper_limit, Services_in_Finland, Additional_information,
  Sub_band_lower_limit, Sub_band_upper_limit, Sub_band_lower_limit__Hz_, Sub_band_upper_limit__Hz_, Sub_band_width, Sub_band_usage,
  Mode_of_traffic, Class_of_station, Direction, Radiated_power, Transmitter_power, Channel_spacing, Bandwidth, Duplex_separation,
  Duplex_band_lower_limit, Duplex_band_upper_limit, Class_of_emission, Standard_type, Comment`
  (`Sub_band_*__Hz_` are integers in Hz, the other limits are display strings such as `"8.3 kHz"`).
* `swagger_v13.json` and `metadata_v13.xml` describe every entity set of the API (also `RadiomikrofonitVapaatTaajuudet`,
  `RadioamatoorienKutsumerkit`, `Meriradionumerot` ...).
* Extras, useful as public Finnish station data on the terrestrial side:
  `Radioasematiedot.json` (2 382 sound-broadcasting stations) and `TVAsematiedot.json` (1 066 TV stations), both with
  `Municipality, StationName, Frequency (Hz), TransmissionPower (W), AntennaHeight, MaxEffectiveHeight, Polarisation, Latitude,
  Longitude (DDMMSS strings such as "62N5005" / "23E5608"), LicenseNumber, LicenseOwner, Directivity, RadiatedPowerAttenuation_<deg>`.

## 5. Optional sources

### Regulation 15 "M15" - `finlex_m15/`
<https://www.finlex.fi/fi/viranomaiset/maarayskokoelmat/traficom-viestinta/2025/51209>: "Luvasta vapaiden radiolähettimien
yhteistaajuudet ja käyttö" / Collective Frequencies for Licence-exempt Radio Transmitters and Their Use, **15 AV/2025 M**, 27.3.2025.
Finlex media ids 535594 (fi), 687387 (en), 535595 (sv). Same file naming scheme as M4.

### ITU Radio Regulations 2024 - `itu_radio_regulations/`
<https://www.itu.int/pub/r-reg-rr> -> electronic edition <https://www.itu.int/pub/publications.aspx?lang=en&media=electronic&parent=R-REG-RR-2024>.
`R-REG-RR-2024-ZPF-E.zip` is the free English zip of PDFs, 69.6 MB: `RR-Vol 1` (Articles), `Vol 2` (Appendices), `Vol 3`
(Resolutions and Recommendations), `Vol 4` (ITU-R Recommendations incorporated by reference) and `Appendix 27 Maps_2024.zip`.
Other languages: replace `-E` with `-A`, `-C`, `-F`, `-R`, `-S`; `-ZIP-` instead of `-ZPF-` gives the Word version.

### CEPT / ECO documentation database - `cept_ecc/`
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
scripts/download_data.sh                          # fetch whatever is missing (existing files are skipped)
SPACE_IFICS="3084 3085" scripts/download_data.sh  # add new Space IFIC issues as ITU publishes them (every two weeks, Tuesdays)
TERR_IFICS="3084" scripts/download_data.sh        # same for the terrestrial IFIC
SKIP_OPTIONAL=1 scripts/download_data.sh          # mandatory sources only
```

Notes on fetching: the ITU site sits behind a web application firewall that answers some clients with an HTML "Request Rejected"
page and HTTP 200. Plain `curl` (its default user agent) is accepted; the script verifies that every `.zip`/`.pdf` really is one and
reports a FAILED line otherwise.
