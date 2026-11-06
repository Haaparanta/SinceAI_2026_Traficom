# ITU Space IFIC databases (SNS Online downloads)

Free zipped Microsoft Access databases for every Space IFIC issue, including ific3074.zip, and what is inside them.

| Field | Value |
|---|---|
| Link | [https://www.itu.int/sns/wic/demowic.html](https://www.itu.int/sns/wic/demowic.html) |
| Publisher | International Telecommunication Union (ITU), Radiocommunication Bureau (BR); contact Space Applications Software Division, brsas@itu.int |
| Language | English |
| Access | Free, no login; "a free service on a trial basis until further notice" |
| Format | Static HTML pages linking to .zip files; each zip holds one Microsoft Access .mdb database |
| Checked | 6 November 2026 |

> [!NOTE]
> Written on 6 November 2026 from the live page, its 2026 year page and a download of ific3074.zip made the same day. It summarises rather than replaces the source. If this page and the source differ, the source is authoritative.

## What it is

The page is the "Space Network Systems Online" (SNS Online) service of the ITU Radiocommunication Bureau (BR), titled "Space International Frequency Information Circular Databases Online". It gives the databases of the Space International Frequency Information Circular (IFIC), and of its predecessor the Weekly Circular (WIC), as downloadable zip files, one per issue, for further processing. The service is "a free service on a trial basis until further notice".

What the page says about the data:

- The databases "presently contain SNS data of Part-IS, Part-IIS, Part-IIIS and Special Sections API/A and CR/C if they are present in the Table of Contents of the BR IFIC (Space Services)". In the BR IFIC, Part I-S carries the characteristics of notified satellite networks, earth stations and radio astronomy stations (and acknowledges receipt of the notice), Part II-S the frequency assignments recorded in the Master International Frequency Register (MIFR) and Part III-S the assignments returned to administrations; API/A is the special section for advance publication of information (API) and CR/C the special section for coordination requests (CR) (these Part and special-section descriptions come from the BR's WRS-24 presentation, not from the page).
- Advance publication data has been included since 5 March 2002 (IFIC 2464).
- The data of an IFIC "should be read with the corresponding publications, Preface, Appendix 4 and other parts of the Radio Regulations, and database structure definitions that exist on the date of release of the BRIFIC".
- IFIC .mdb files from previous years are no longer supported on the page; for those, contact ITU sales for the relevant BR IFIC DVD.
- Questions about the content go to the Space Applications Software Division, brsas@itu.int (the 2026 page names the same address as the Space Administrative Software Division).

The page also advertises the "Space Query System" for querying the databases. That link, `https://www.itu.int/en/ITU-R/software/Pages/spaceqry.aspx`, returned HTTP 404 on 6 November 2026. The current query tool is BRSIS-Query (Space Query and Extract System) on the [BR space software page](https://www.itu.int/en/ITU-R/software/Pages/space-network-software.aspx), described there as the software that "provides access to the Radiocommunication Bureau's Space Radiocommunication Stations database"; see [ITU space software](../itu-space-software/README.md). It is Windows-only.

## Why it matters for the challenge

- The brief lists this page as the download location of the mandatory ITU Space IFIC dataset ("Downloadable Space IFIC") and requires that "all existing IFICs and forthcoming IFICs shall be able to be evaluated".
- Space IFIC 3074 must be analysed and its results submitted separately; it is the issue used to evaluate accuracy (criterion D, case recognition accuracy and relevance, 15 %). The 3074 database is [ific3074.zip](https://www.itu.int/sns/ific10/ific3074.zip).
- The brief's workflow ingests new IFIC publications, "especially API/A, CR/C and AP30 (including AP30A and AP30B)", and allows "direct database logic" instead of the BR's SpaceCom tool and "direct calculation logic" instead of GIBC for power flux-density (pfd). These zips are the only no-login, machine-readable form of that content; the full BR IFIC needs a TIES account of a Member State administration or a paid subscription (see [ITU BR IFIC (Space services)](../itu-space-brific/README.md)).
- The notice tables carry the notifying administration and the service-area country symbols, which is what the brief needs for "identifying the relevant counterparty (administration)" and for the Finland filter. Keeping the raw rows next to each finding serves criterion E (auditability and evidence quality, 15 %) and the reproducibility part of criterion A (25 %).

## How the site is organised

### Year pages

The landing page links one page per year, 1998 to 2026, named `demowicYY.html` with a two-digit year (`demowic98.html` ... `demowic26.html`). Each year page repeats the year links and lists the issues of that year with a publication date, a link to the zip and a "View" link to the table of contents.

| What | URL pattern | Example |
|---|---|---|
| Landing page | https://www.itu.int/sns/wic/demowic.html | - |
| Year page | https://www.itu.int/sns/wic/demowicYY.html | https://www.itu.int/sns/wic/demowic26.html |
| Database zip, 2025 onward (version 10) | `https://www.itu.int/sns/ific10/ific<NUMBER>.zip` | https://www.itu.int/sns/ific10/ific3074.zip |
| Database zip, older years | `https://www.itu.int/sns/<folder>/ific<NUMBER>.zip`, several folders per issue | https://www.itu.int/sns/converted-to-v10/ific3036.zip |
| Table of contents ("View") | `https://www.itu.int/net/ITU-R/space/snl/bresult/radvance.asp?sel_ific=<NUMBER>&ie=y` | obsolete, see below |
| Table of contents query form | https://www.itu.int/sns/ific.html | obsolete, see below |

The year pages are plain HTML (no JavaScript needed); the zip links are relative (`../ific10/ific3074.zip`).

### The 2026 list

The 2026 page lists 22 entries under the heading "Version 10 Databases", with the note "As from 7 January 2025 all Space IFIC databases are published in the new restructured Space Network System database version 10". The dates agree with the BR IFIC schedule page.

| Published | IFIC | Download |
|---|---|---|
| 06.01.2026 | 3062 | https://www.itu.int/sns/ific10/ific3062.zip |
| 20.01.2026 | 3063 | https://www.itu.int/sns/ific10/ific3063.zip |
| 03.02.2026 | 3064 | https://www.itu.int/sns/ific10/ific3064.zip |
| 17.02.2026 | 3065 | https://www.itu.int/sns/ific10/ific3065.zip |
| 03.03.2026 | 3066 | https://www.itu.int/sns/ific10/ific3066.zip |
| 17.03.2026 | 3067 | https://www.itu.int/sns/ific10/ific3067.zip |
| 31.03.2026 | 3068 | https://www.itu.int/sns/ific10/ific3068.zip |
| 14.04.2026 | 3069 | https://www.itu.int/sns/ific10/ific3069.zip |
| 28.04.2026 | 3070-Correction | https://www.itu.int/sns/ific10/ific3070.zip |
| 12.05.2026 | 3071 | https://www.itu.int/sns/ific10/ific3071.zip |
| 26.05.2026 | 3072 | https://www.itu.int/sns/ific10/ific3072.zip |
| 09.06.2026 | 3073 | https://www.itu.int/sns/ific10/ific3073.zip |
| 23.06.2026 | 3074 | https://www.itu.int/sns/ific10/ific3074.zip |
| 07.07.2026 | 3075 | https://www.itu.int/sns/ific10/ific3075.zip |
| 21.07.2026 | 3076 | https://www.itu.int/sns/ific10/ific3076.zip |
| 04.08.2026 | 3077 | https://www.itu.int/sns/ific10/ific3077.zip |
| 18.08.2026 | 3078 | https://www.itu.int/sns/ific10/ific3078.zip |
| 01.09.2026 | 3079 | https://www.itu.int/sns/ific10/ific3079.zip |
| 15.09.2026 | 3080 | https://www.itu.int/sns/ific10/ific3080.zip |
| 29.09.2026 | 3081 | https://www.itu.int/sns/ific10/ific3081.zip |
| 13.10.2026 | 3082 | https://www.itu.int/sns/ific10/ific3082.zip |
| 27.10.2026 | 3083 | https://www.itu.int/sns/ific10/ific3083.zip |

The "3070-Correction" entry links to the ordinary file name `ific3070.zip`, so a correction replaces the file rather than adding a second one; the HTTP `Last-Modified` header is the only way to see that a file changed.

### Table-of-contents links are obsolete

Every "View" link (`radvance.asp?sel_ific=<NUMBER>&ie=y`) and the [query form](https://www.itu.int/sns/ific.html) lead to the Space Network List (SNL) application. On 6 November 2026 the `radvance.asp` page for 3074 returned HTTP 200 with no table of contents, only a notice dated 28.09.2026 saying that the technology behind the SNL application is obsolete and that some features could not be maintained, and pointing to the Space Explorer application at [https://www.itu.int/go/ITUSpaceExplorer](https://www.itu.int/go/ITUSpaceExplorer) (HTTP 301 to [https://www.itu.int/itu-r/space/apps/public/spaceexplorer/](https://www.itu.int/itu-r/space/apps/public/spaceexplorer/)). The form page still states that table-of-contents information exists from WIC 1418 onward. Which special sections an issue contains is therefore best read from the database itself (table `pub_ssn`, below) or from the BR IFIC online application (login required).

## Space IFIC 3074

Checked and downloaded on 6 November 2026.

| Item | Value |
|---|---|
| IFIC number | 3074 |
| Publication date | 23 June 2026 (SNS 2026 page and BR IFIC schedule) |
| Download | [https://www.itu.int/sns/ific10/ific3074.zip](https://www.itu.int/sns/ific10/ific3074.zip) (HTTP 200, `Content-Type: application/zip`) |
| Zip size | 60,837,631 bytes (58.0 MiB) |
| HTTP Last-Modified | Tue, 23 Jun 2026 06:25:33 GMT |
| Zip contents | one file, `ific3074.mdb`, 286,654,464 bytes (273.4 MiB), dated 11 June 2026 18:20 in the archive |
| Database format | Microsoft Access (.mdb) |
| Structure version | SNS v10.0: table `srs_ooak` holds version_no 10, version_no_sub 0, d_create 2026-06-11 18:19:24, comment `ific3074` |
| Tables | 95 catalog entries, of which 7 are `MSys*` system tables and 88 are data tables |
| Table of contents link | https://www.itu.int/net/ITU-R/space/snl/bresult/radvance.asp?sel_ific=3074&ie=y (obsolescence notice only) |

### What the 3074 database holds

Row counts and value distributions below were read with the Python package access-parser 0.0.6 on 6 November 2026 (commands in the next section). The code meanings are quoted from the SNS v9.1 data-items PDF.

| Table | Rows | Content |
|---|---|---|
| notice | 196 | General information for the notice; every row has wic_no 3074 and d_wic 2026-06-23 |
| com_el | 146 | Common elements per notice: notifying administration (adm), satellite name, nominal longitude |
| pub_ssn | 225 | Publication information for a notice: special section symbol (ssn_ref) and number (ssn_no) |
| grp | 34,365 | Common data for a group of assigned frequencies |
| freq | 95,865 | Frequency rows: assigned frequency, band limits in MHz, bandwidth |
| emiss | 216,455 | Emission: peak power, power density, carrier-to-noise |
| gpub | 70,681 | Publication information per group, including earlier issues (for example 3059, 3060, 3063) |
| c_pfd | 119 | Compliance with pfd limits (A.17): band limits, pfd in dB(W/m2), bandwidth |
| epfd_param | 34 | Equivalent pfd (epfd) scenario parameters for non-GSO systems |
| geo | 72 | Geostationary (GSO) space station: nominal longitude and tolerances |
| non_geo | 112 | Non-geostationary (NGSO) space station: number of planes and satellites per plane |
| e_stn | 12 | Earth station (A.7): coordinates, horizon and elevation data |
| srv_area | 930 | Service area: country symbol per group |

Profile of the 196 notices:

- ntc_type: N (non-geostationary satellite) 112, G (geostationary satellite) 72, S (specific earth station) 12.
- ntf_rsn (notification reason): C 76, N 65, A 50, U 5. In the data-items PDF, A is advance publication under No. 9.1, C covers coordination under Nos. 9.6, 9.7A and 9.21, N covers notification under Nos. 11.2 and 11.12 and U is Resolution 49.
- Special sections referenced in `pub_ssn.ssn_ref`: CR/C 76, CR/D 58, API/A 50, API/B 22, CR/E 14, RES49 5.
- Notifying administrations in `com_el.adm` (25 distinct): CHN 38, USA 29, RUS 13, KOR 10, D 7, E 6, G 5, F 5, J 5, IND 4, I 4, KAZ 3, then INS, S, TUR, GRC with 2 and ISR, QAT, B, BUL with 1. Four notices carry an intergovernmental organisation (ntwk_org EUM 2, ESA 1, ARB 1). No notice is filed by FIN.
- `srv_area.ctry` has 47 distinct symbols; FIN appears in 2 rows. The most frequent symbols are XAA 310, CHN 226, ARG 71 and XR3 37.

> [!IMPORTANT]
> access-parser is a pure-Python reader of the Access file format and can misread pages or data types. Before a number from it goes into a submitted finding, confirm it with a second reader (mdbtools or Microsoft Access).

### Tables in ific3074.mdb

All 88 data tables, grouped by what they describe. The descriptions are shortened from the SNS v9.1 data-items PDF, [sns_dbv91.pdf](https://www.itu.int/en/ITU-R/space/Documents/sns_dbv91.pdf) (853,162 bytes, 833 KiB, 30 pages, "Details relating to the contents of the SNS data items published in Part I-S, II-S, III-S and the Special Sections of the BR IFIC"), which is linked from the BR IFIC page together with the [SNS v9.1 diagram](https://www.itu.int/en/ITU-R/space/Documents/SRSDiagramV9_1.pdf). The PDF describes version 9.1 while the file is version 10; tables marked "not in the v9.1 PDF" have no entry there.

Notice, station and antenna level:

| Table | Content |
|---|---|
| notice | General information for the notice |
| com_el | Common elements (BR internal use) |
| adm_assoc | Administrations "on behalf of" which the notice was submitted |
| ntc_commit | Commitments |
| ntc_lnk | Notice link |
| ntc_lnk_ref | Notice link reference |
| ntc_memo | Comments and remarks (Resolution 49 and API only) |
| ntc_tmp | not in the v9.1 PDF |
| geo | Geostationary space station |
| non_geo | Non-geostationary space station |
| orbit | Orbital plane of a non-geostationary satellite |
| orbit_lnk | Link between a non-geostationary space station antenna and the orbital plane |
| orbit_set | not in the v9.1 PDF |
| phase | Initial phase angle of a non-geostationary satellite in an orbital plane |
| sat_lnk | Link between a non-geostationary space station antenna and the satellite |
| sat_oper | Non-geostationary satellites with overlapping frequencies |
| s_as_stn | Space associated station |
| s_beam | Satellite antenna beam |
| beam_tr | Beam information SNS/SPS to Plans |
| e_stn | Earth station (A.7) |
| e_ant | Earth station antenna |
| e_ant_elev | Earth antenna elevation |
| e_as_stn | Associated earth station |
| e_srvcls | Nature of service and class of station for an associated earth station |
| hor_elev | Horizon elevation diagram |
| isl_param | not in the v9.1 PDF |
| srvlnk_sat | not in the v9.1 PDF |
| ngeo_diag_grp | not in the v9.1 PDF |
| aesim_param | not in the v9.1 PDF |

Group, frequency and emission level:

| Table | Content |
|---|---|
| grp | Common data for a group of assigned frequencies |
| grp_lnk | Group link |
| grp_aff_rec | Link between an incoming group and an affected or affecting network |
| ex_op_grp | Exclusive operation group |
| freq | Frequency (BR internal use) |
| assgn | Assigned frequency |
| emiss | Emission |
| carrier_fr | Carrier frequency of the emissions |
| mod_char | General characteristics of the emission |
| pwr_ctrl | Power control information |
| strap | Connection between uplink and downlink beams and frequencies (D.1) |
| ngma | Link-noise and transmission gain for one or more straps |
| srv_area | Service area |
| srv_cls | Nature of service and class of station for the group |
| fdg_ref | Finding reference |
| all_aff_ntw | Affected and affecting networks at group level |
| tr_aff_ntw | Affected and affecting networks for the transaction |
| coord_agree_ntw | Network-level coordination agreements (A5/A6) |
| interf_poc | not in the v9.1 PDF |
| es_ctry | not in the v9.1 PDF |

pfd, epfd and masks:

| Table | Content |
|---|---|
| c_pfd | Compliance with pfd limits (A.17) |
| epfd_freq | not in the v9.1 PDF |
| epfd_param | not in the v9.1 PDF |
| mask_info | Mask information |
| mask_lnk1 | Link between mask, group and satellite of a non-geostationary system |
| mask_lnk2 | Link between mask, associated earth station and satellite of a non-geostationary system |
| mask_lnk3 | System operating parameters identification for Recommendation ITU-R S.1503-3 |

Plans (Appendices 30, 30A and 30B of the Radio Regulations):

| Table | Content |
|---|---|
| ap30b_ref_agg | Reference aggregate C/I values |
| ap30b_ref_se | Reference single-entry C/I values |
| ap30b_tr_res | AP30B Annex 4 findings at the notice level |
| pl_strap | Connection between uplink and downlink beams and frequencies (plans) |
| plan_pub | Publication information for plan notices |
| sps_results | Space plan results |
| link_epm | Equivalent protection margin (link), Appendix 30/30A Regions 1 and 3 |
| ovrl_epm | Overall equivalent protection margin, Appendix 30/30A Region 2 |
| sat_sys_provn | Coordination information for AP30/30A Article 4 notices of the same cluster in Region 2 |

Resolutions 35, 49, 552 and 8:

| Table | Content |
|---|---|
| grp_res35 | Information for a group of assigned frequencies under Resolution 35 |
| res35_freq | Resolution 35 space station frequency characteristics |
| res35_sp_stn | Resolution 35 space station characteristics |
| res35_launch | Resolution 35 launch information |
| res35_deploy | Resolution 35 deployment summary |
| res35_sp_stn_deploy | not in the v9.1 PDF |
| res49_sel | Resolution 49 download table |
| cmr_syst | Commercial satellite system submitted under Resolution 49 |
| cmr_grp_lnk | Link between cmr_syst and grp |
| cmr_notice | Link between a Resolution 552 submission and the ITU spacecraft identifier |
| cmr_history | Spacecraft history |
| scraft_cmr_freq | Frequency bands present on board the spacecraft |
| scraft_cmr_syst | Spacecraft under Resolution 552 |
| res8_sp_stn | not in the v9.1 PDF |

Publication, coordination provisions and history:

| Table | Content |
|---|---|
| gpub | Publication information for a group of assigned frequencies (A.13) |
| pub_ssn | Publication information for a notice |
| provn | Coordination information |
| tr_provn | Coordination information for the transaction |
| history | Transaction history data (BR internal use) |

Reference and system tables:

| Table | Content |
|---|---|
| ant_type | Antenna type information |
| ras_ant_type | not in the v9.1 PDF |
| alloc_id | Identifier allocation (BR internal use) |
| srs_ooak | Database system information: version, creation date, comment |

## How to download and open the database

### Download and unzip

The download is 58 MiB and took a while on 6 November 2026; check the headers first, then fetch with a long timeout. The zip holds one .mdb file.

```bash
curl -sS -I -L --max-time 60 -A "Mozilla/5.0" https://www.itu.int/sns/ific10/ific3074.zip
mkdir -p ific_downloads
curl -sS -L --max-time 900 -A "Mozilla/5.0" -o ific_downloads/ific3074.zip https://www.itu.int/sns/ific10/ific3074.zip
unzip -l ific_downloads/ific3074.zip
unzip -d ific_downloads ific_downloads/ific3074.zip
```

```text
HTTP/1.1 200 OK
Last-Modified: Tue, 23 Jun 2026 06:25:33 GMT
Content-Length: 60837631
Content-Type: application/zip

Archive:  ific_downloads/ific3074.zip
  Length      Date    Time    Name
---------  ---------- -----   ----
286654464  06-11-2026 18:20   ific3074.mdb
```

### Read it without Windows: access-parser

[access-parser](https://pypi.org/project/access-parser/) is a pure-Python reader; version 0.0.6 was used here in a virtual environment. `AccessParser(path).catalog` maps table names to their catalog entries and `parse_table(name)` returns a dict of column name to list of values. Run Python with `-I` and pass the path as an argument, because the file is downloaded data.

```bash
python3 -m venv venv
venv/bin/pip install access-parser
venv/bin/python3 -I - ific_downloads/ific3074.mdb <<'EOF'
import sys
from access_parser import AccessParser
db = AccessParser(sys.argv[1])
names = sorted(db.catalog)
user = [n for n in names if not n.startswith('MSys')]
print(len(names), 'catalog entries;', len(user), 'non-system tables')
ooak = db.parse_table('srs_ooak')
print(ooak['version_no'], ooak['version_no_sub'], ooak['d_create'], ooak['comment'])
notice = db.parse_table('notice')
print(len(notice['ntc_id']), 'notices; wic_no values:', sorted(set(notice['wic_no'])))
EOF
```

```text
95 catalog entries; 88 non-system tables
[10] [0] ['2026-06-11 18:19:24'] ['ific3074']
196 notices; wic_no values: [3074]
```

Reading the catalog took about 3 seconds; parsing `emiss` (216,455 rows) took about 8 seconds.

### Other readers

| Reader | Platform | How | Tested here |
|---|---|---|---|
| [mdbtools](https://github.com/mdbtools/mdbtools) | macOS (Homebrew), Linux | `mdb-tables -1 ific3074.mdb` lists tables; `mdb-export ific3074.mdb notice > notice.csv` exports one table to CSV | No (not installed on the machine used) |
| Microsoft Access or an ODBC driver | Windows | Open the .mdb directly, or query it through ODBC | No |
| BRSIS-Query | Windows 10 and 11 only | The BR's own query and extract tool, part of BR Space Application software v10 | No |

## Processing all existing and forthcoming issues

### Enumerate the year pages

Each year page lists its zips as relative `href` values. Fetch the page, collect the hrefs and resolve them against `https://www.itu.int/sns/wic/`. This command was run on 6 November 2026:

```bash
curl -sS -L --max-time 60 -A "Mozilla/5.0" https://www.itu.int/sns/wic/demowic26.html | grep -oE 'href="[^"]*\.zip"' | head -3
```

```text
href="../ific10/ific3083.zip"
href="../ific10/ific3082.zip"
href="../ific10/ific3081.zip"
```

The publication date sits in the same table row as the link, so parse the rows rather than only the hrefs. The IFIC number is the digits in the file name; the "3070-Correction" label appears only in the link text.

### Older years and database versions

Older year pages list one issue several times, once per database structure: the folder of the original version plus "converted-to-vX" folders. Sampled on 6 November 2026:

| Year page | Folders used | Note on the page |
|---|---|---|
| demowic26.html, demowic25.html | ific10 | version 10 from 7 January 2025 |
| demowic24.html, demowic23.html | ific91 and converted-to-v10 | version 9.1 from 29 November 2022 |
| demowic20.html | ific8, ific9, converted-to-v9, converted-to-v9.1, converted-to-v10 | - |
| demowic15.html | ific61, converted-to-v8, converted-to-v9, converted-to-v9.1 (2 entries) | - |
| demowic98.html | wic2 (files named `swic<NUMBER>.zip`), converted-to-v8, converted-to-v9, converted-to-v9.1 | - |

For a uniform pipeline, prefer the `converted-to-v10` copy where it exists and fall back to the newest conversion otherwise; the oldest years have no version 10 copy. Column semantics may still differ between versions, so record the structure version from `srs_ooak` with every result.

### Forthcoming issues

The SNS page has no schedule of its own. The BR IFIC schedule page (documented in [ITU BR IFIC (Space services)](../itu-space-brific/README.md)) lists the remaining 2026 issues: 3084 on 10 November 2026, 3085 on 24 November 2026, 3086 on 8 December 2026 and 3087 on 5 January 2027. To pick up a new issue, re-fetch `demowic26.html` (and `demowic27.html` from January 2027) on or after the publication date, diff the set of zip hrefs against the previous run, and send a HEAD request for each new or changed file; `Last-Modified` also reveals a replaced file such as a correction.

## Caveats

- The service is free "on a trial basis until further notice"; the terms may change without notice.
- The table-of-contents links and query form are obsolete (notice dated 28 September 2026); use Space Explorer or the `pub_ssn` table instead.
- The files are large: 3074 is 60,837,631 bytes zipped and 286,654,464 bytes unpacked; the space IFIC 3076 zip, [ific3076.zip](https://www.itu.int/sns/ific10/ific3076.zip), is 22,079,898 bytes (21.1 MiB, Last-Modified 21 July 2026), so sizes vary a lot between issues. Keep downloads out of the repository.
- Each database is the set of notices published in that issue (all 196 notice rows in 3074 have wic_no 3074), with the publication history of their groups, not the full Space Radiocommunication Stations (SRS) database. The BR IFIC online page says that the full SRS and GIMS (Graphical Interference Management) databases are only available in the BR IFIC, which is distributed as an ISO file at [https://www.itu.int/pub/R-SP-LN.IS](https://www.itu.int/pub/R-SP-LN.IS) and through [https://www.itu.int/epublications/brific-space](https://www.itu.int/epublications/brific-space) to TIES (Telecommunication Information Exchange Service; expansion is background, not from the page) accounts of Member State administrations and to paid subscribers (sales@itu.int).
- The .mdb format needs a reader. access-parser works on macOS and Linux but is unofficial; the BR's own tools run on Windows 10 and 11 only.
- The column documentation is for SNS v9.1 while the 2025 and 2026 files are v10; 18 of the 88 tables in 3074 have no entry in the v9.1 PDF.
- Older issues are published in older structures or as converted copies, and files older than the years listed are only available on DVD from ITU sales.
- A correction replaces the original file under the same name; keep the `Last-Modified` value and a checksum with each download.

## Related pages

- [ITU BR IFIC (Space services)](../itu-space-brific/README.md): what the circular is, the 2026 schedule, access rules and the SNS description files.
- [ITU space software](../itu-space-software/README.md): BRSIS-Query, SpaceCom, GIBC and the other BR tools, Windows only.
- [ITU BR IFIC (Terrestrial services)](../itu-terrestrial-brific/README.md): the terrestrial counterpart with its own MDB extracts, including 3076.
- [ITU Radio Regulations](../itu-radio-regulations/README.md): the Preface, Appendix 4 and the Article 9 and 11 provisions the notice codes refer to.
- [Regulation 4 (M4)](../finlex-regulation-m4/README.md) and [Traficom frequency table endpoint](../traficom-frequency-table-api/README.md): the Finnish allocation table the IFIC frequencies are compared with.
- [Challenge brief](../../challenge-brief/README.md): the mandatory-dataset wording and the evaluation criteria.
- [Documentation index](../../README.md) and the [repository README](../../../README.md).
