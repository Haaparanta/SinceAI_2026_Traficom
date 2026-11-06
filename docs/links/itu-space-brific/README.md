# ITU BR IFIC (Space services)

The Radiocommunication Bureau's fortnightly circular of frequency assignments and allotments to space services, which the challenge brief lists as a mandatory dataset.

| Source | Detail |
|---|---|
| Link | [https://www.itu.int/en/ITU-R/space/brific/Pages/default.aspx](https://www.itu.int/en/ITU-R/space/brific/Pages/default.aspx) |
| Publisher | International Telecommunication Union (ITU), Radiocommunication Bureau (BR), Space Services Department (SSD) |
| Language | English; the page also exists in French and Spanish |
| Access | The page and its description files are free; the online application, the ISO download and the online queries need a TIES (ITU Telecommunication Information Exchange Service) account or a paid subscription; the zipped IFIC databases are free |
| Format | SharePoint web page linking PDF documents, web applications and zipped Microsoft Access databases |
| Checked | 6 November 2026 |

> [!NOTE]
> Written on 6 November 2026 from the live page, its subpages and the documents they link. It summarises rather than replaces the source; if this page and the source differ, the source is authoritative.

## What it is

The page defines the BR International Frequency Information Circular (Space services), short BR IFIC, as "a service document containing particulars of frequency allotments and assignments to space services". It is published once every two weeks by the Radiocommunication Bureau in accordance with provisions Nos. 20.2 to 20.6 and No. 20.15 of the Radio Regulations (RR), and it is distributed through an online application, web-based distribution of an ISO disc image, and DVD-ROM.

The slide deck linked from the page (the Bureau's WRS-24 presentation; WRS stands for World Radiocommunication Seminar, background, not from the page) adds the operational facts: the circular carries the assignments and allotments that administrations submit for updating the Master International Frequency Register (MIFR) and the Plans; it appears in the six ITU languages; the publication date is always a Tuesday; there are generally 25 issues a year; and the four-month time limit for regulatory comments under various provisions runs from the publication date.

Contacts printed on the page: the helpdesk spacehelp@itu.int for general and technical questions, and ITU Sales sales@itu.int for subscriptions.

### What one issue contains

From slides 12 to 15 of the presentation:

| Part of an issue | Content |
|---|---|
| Regulatory publications | Special Sections and Parts I-S, II-S and III-S as PDF files, in six languages |
| Technical data | Transaction summary (TSUM), Appendix 8 results, EPFD input, results and summary, AP30/30A and AP30B examination results, interference analysis |
| Databases | IFIC, SRS, GIMS, AP30/30A, AP30B, RES35 |
| Preface | Contents and layout of the circular, four sections |
| BR space software | The Bureau's Windows applications |

Part I-S holds the characteristics of a notified satellite network, earth station or radio astronomy station and is the acknowledgement of receipt; Part II-S holds assignments recorded in the MIFR; Part III-S holds assignments returned to the administrations. Slide 13 lists the Special Section families: API/A, API/B, API/C; CR/C, CR/F, CR/D, CR/E; AP30/E, AP30A/E, AP30-30A/E; AP30-30A/F/C, AP30-30A/F/D; AP30B/A6A, AP30B/A6B, AP30B/A7; RES4, RES35, RES49, RES552. API stands for advance publication information and CR for coordination request (expansions are background, not from the page); AP30, AP30A and AP30B are Appendices 30, 30A and 30B of the RR, which the Space Services home page calls the BSS Plan (Appendices 30 and 30A) and the FSS Plan (Appendix 30B); BSS and FSS are the broadcasting-satellite and fixed-satellite services (background, not from the page).

Slide 15 describes the databases: the BRIFIC MDB holds the Appendix 4 (AP4) data of non-planned space services published in the current issue; the SRS MDB (Space Radiocommunication Stations) holds the AP4 data of all satellite networks, earth stations and radio astronomy stations; AP30_30A and AP30B hold the Plan, List and pending-network data; the GIMS reference database (Graphical Interference Management System, REFDB) holds graphical data; the SRS-RES35 MDB holds Resolution 35 information. Slide 9 states that the only official regulatory reference for coordination between administrations is the PDF Part or Special Section in the circular, and that the SRS reference database (SRSxxxx.mdb) and the GIMS data (GREFxxxx.mdb) are distributed only in the BR IFIC.

## Why it matters for the challenge

- The official brief marks the ITU Space IFIC as mandatory. All existing and forthcoming IFICs must be evaluable, and Space IFIC no. 3074 must be analysed with its results submitted as a separate file, because it is used to evaluate accuracy. See [the challenge brief](../../challenge-brief/README.md).
- The brief names the Special Sections to watch: API/A, CR/C and AP30 including AP30A and AP30B. It singles out the power flux-density (pfd) of geostationary-satellite orbit (GSO) and non-geostationary (non-GSO or NGSO) systems as the quantity of special interest.
- Three evaluation criteria depend directly on reading this circular correctly: case recognition accuracy and relevance (15 %), technical analysis and reproducibility (25 %) and auditability and evidence quality (15 %).

### The procedure behind the Special Sections

Slide 5 of the presentation quotes the Article 9 provisions that the Special Sections implement. In summary:

| Step | Provision | What happens |
|---|---|---|
| Advance publication | No. 9.1 | The administration sends the Bureau a general description of the network for advance publication in the BR IFIC |
| Advance publication | No. 9.1A | On receipt of the complete information under No. 9.30, the Bureau publishes a general description in a Special Section using the basic characteristics of the coordination request |
| Advance publication | No. 9.2B | The Bureau publishes the complete information sent under Nos. 9.1 and 9.2 in a Special Section within two months |
| Comments | No. 9.3 | An administration that believes unacceptable interference may be caused to its existing or planned networks sends its comments to the publishing administration within four months of the publication date |
| Coordination | No. 9.38 | The Bureau publishes the complete coordination information in the BR IFIC within four months |
| Coordination | No. 9.40 | The Bureau informs the administrations concerned and communicates its calculation results, drawing attention to the relevant BR IFIC |
| Coordination | No. 9.41 | An administration that believes it, or one of its networks not identified, should have been included informs the initiating administration and the Bureau within four months of the publication date |
| Agreement | Nos. 9.51 and 9.52 | Within four months of the publication under No. 9.38 the administration either informs the requesting administration and the Bureau of its agreement or of its disagreement |

Slide 10 restates the rule: the four-month time limit for regulatory comments starts from the publication date of the circular. That window is what the expert-reviewable draft correspondence requested by the brief serves. For Space IFIC 3074, published on 23 June 2026, four months end on 23 October 2026 (computed from the rule on slide 10), so the graded issue is a retrospective exercise during the hackathon of 6 to 8 November 2026.

Slide 6 lists what the circular publishes for regulatory purposes: the characteristics required by Annex 2 of Appendix 4, the list of administrations with which coordination may need to be carried out, the Bureau's findings, comments received from administrations in response to a BR IFIC, bringing into use, suspension, and Resolution 35 deployment information. The list of administrations is the field that says whether Finland has been identified as affected. Slide 22 summarises the affected administration's work on an issue: check whether it is identified as affected, analyse, comment and send its decision within four months, using IFIC.mdb, SRS.mdb, GREF.mdb, SPS_ALL.mdb and RES35.mdb with SpaceCap, BRSIS/SpaceQry and GIMS.

## Map of the page

The page has a header link, eight link blocks and a sidebar. Every URL below is resolved from the href in the page HTML as captured on 6 November 2026.

### Header

| Link text | URL | Notes |
|---|---|---|
| Log into the BRIFIC (Space services) online | https://www.itu.int/epublications/brific-space | Login required |

### BR IFIC information

| Link text | URL | Notes |
|---|---|---|
| Presentation of the BR IFIC (Space services) | https://www.itu.int/en/ITU-R/space/Documents/BR%20IFIC%20%28Space%20services%29.pdf | WRS-24 slides, 35 pages, 1,832,283 bytes (1.7 MiB) |
| Schedule of publication | https://www.itu.int/en/ITU-R/space/brific/Pages/brificSchedule.aspx | Tables for 2026, 2025, 2024 and 2023 |
| Preface to the BR IFIC | https://www.itu.int/ITU-R/go/space-preface/en | Contents and layout of the circular |
| Frequently asked questions | https://www.itu.int/en/ITU-R/space/Pages/FAQspace.aspx#BRIFIC | BR IFIC section of the space FAQ |

### Access and distribution

| Link text | URL | Notes |
|---|---|---|
| Access rights to the BR IFIC | https://www.itu.int/en/ITU-R/space/brific/Pages/brificAccess.aspx | Who gets access and how |
| BR IFIC online, and its Explanation link | https://www.itu.int/en/ITU-R/space/brific/Pages/brificOnline.aspx | Both links go to the same page |
| Web-based distribution of the ISO file | https://www.itu.int/pub/R-SP-LN.IS | ITU publications catalogue, sign-in needed to download |
| Explanation (of the ISO file) | https://www.itu.int/en/ITU-R/space/Documents/BR-IFIC-%28Space%29-ISO-image_2021.pdf | 3 pages, 418,155 bytes (408 KiB) |
| To order the BR IFIC | https://www.itu.int/pub/R-SP-LN/e | ITU publications catalogue entry |
| To order the annual collection | https://www.itu.int/pub/R-SP-LN.IW | ITU publications catalogue entry for the annual collection |

### Description files

| Link text | URL | Notes |
|---|---|---|
| BR IFIC user guide | https://www.itu.int/en/ITU-R/space/Documents/brificSpaceServicesOnlineUserGuide.pdf | 10 pages, version of 8 February 2024, 667,607 bytes (652 KiB) |
| Data items description in publication | https://www.itu.int/en/ITU-R/space/brific/Pages/pubLegend.aspx | Legends for the PDF Parts and Special Sections in six languages; English file https://www.itu.int/en/ITU-R/space/publicationLegend/legend_E.pdf, 211,924 bytes (207 KiB) |
| SNS V9.1 | https://www.itu.int/en/ITU-R/space/Documents/sns_dbv91.pdf | Data items of the Space Network Systems (SNS) database, 30 pages, 853,162 bytes (833 KiB) |
| SNS V9.1 diagram | https://www.itu.int/en/ITU-R/space/Documents/SRSDiagramV9_1.pdf | Entity diagram, 1 page, 49,510 bytes (48 KiB) |
| How to consult exceedingly large notices | https://www.itu.int/en/ITU-R/space/Documents/Viewing%20exceedingly%20large%20notices.pdf | 611,409 bytes (597 KiB), not summarised here |

### News

| Link text | URL | Notes |
|---|---|---|
| BR IFIC 3013: BR IFIC online | https://www.itu.int/en/ITU-R/space/BRIFICnewsDVD/News_1_E_3013.pdf | 23 January 2024, release of the online application and the new desktop application, 83,289 bytes (81 KiB) |
| BR IFIC 3012: BR IFIC online | https://www.itu.int/en/ITU-R/space/BRIFICnewsDVD/News_1_E_3012.pdf | 9 January 2024, availability announcement, 83,478 bytes (82 KiB) |
| BR IFIC 3009: Correction to BR IFIC 2999 | https://www.itu.int/en/ITU-R/space/BRIFICnewsDVD/Correction_IFIC3009.pdf | 14 November 2023, 222,932 bytes (218 KiB) |
| BR IFIC 3006: Update of e-Submission system | https://www.itu.int/en/ITU-R/space/BRIFICnewsDVD/News_1_E_3006.pdf | 3 October 2023, introduction of e-Examination for pfd and EIRP limits, 105,149 bytes (103 KiB) |
| All news | https://www.itu.int/en/ITU-R/space/brific/Pages/brificNews.aspx | 30 items from 3013 back to 2918 of 14 April 2020 |

The news list also records the database history: SNS version 9.0 with BR IFIC 2926 (4 August 2020), the three-part SRS database format with 2951 (27 July 2021), the SNS 9.1 beta with 2982 (18 October 2022) and SNS 9.1 itself with 2985 (29 November 2022).

### Publications online

| Link text | URL | Notes |
|---|---|---|
| Table of contents (Space station) | https://www.itu.int/itu-r/space/apps/public/spaceexplorer/list-redirect?entity=ss&src=sp&geo=1&nongeo=1&plan=1&nonplan=1&wic_latest_only=1 | Space Explorer list (parameter wic_latest_only=1), JavaScript application |
| Table of contents (Earth station) | https://www.itu.int/itu-r/space/apps/public/spaceexplorer/list-redirect?entity=es&src=sp&specific=1&typical=1&wic_latest_only=1 | Same application, earth stations |
| RES 32 publications | https://www.itu.int/net/ITU-R/space/snl/bresult/radvance.asp?res32=Y | Explanation link: https://www.itu.int/en/ITU-R/space/support/nonGSO/RES32/Pages/default.aspx |
| RES 35 publications | https://www.itu.int/net/ITU-R/space/snl/bresult/radvance.asp?sel_type=RES35 | Explanation link: https://www.itu.int/en/ITU-R/space/Pages/res35main.aspx |
| API/C publications | https://www.itu.int/net4/ITU-R/SpaceWISC/apipub/IFIC/Apic | API/C Special Sections |

### Database online

| Link text | URL | Notes |
|---|---|---|
| BR IFIC database | https://www.itu.int/sns/wic/demowic.html | Free zipped IFIC databases per year; see [ITU Space IFIC databases](../itu-space-ific-databases/README.md) |
| AP30/30A database | https://www.itu.int/en/ITU-R/space/plans/Pages/AP30-30A.aspx | Appendices 30 and 30A Plan data |
| AP30B database | https://www.itu.int/en/ITU-R/space/plans/Pages/AP30B.aspx | Appendix 30B Plan data |
| Information "As received" | https://www.itu.int/ITU-R/go/space/snl/en | Redirects to https://www.itu.int/space-networks-hub/ |
| RES35 database | https://www.itu.int/net/ITU-R/space/documents/RES35/db/srs_res35.zip | 378,981 bytes (370 KiB), server last-modified 19 December 2024 |

### Additional information

| Link text | URL | Notes |
|---|---|---|
| EPFD data and EPFD examination results | https://www.itu.int/ITU-R/go/space-epfd-data | Redirects to https://www.itu.int/net/ITU-R/space/epfd/index.html; EPFD is equivalent power flux-density |
| Additional information related to the spectrum masks | https://www.itu.int/en/ITU-R/space/brific/Pages/brificMask.aspx | Spectrum mask information |
| Additional information related to the orientation angles | https://www.itu.int/en/ITU-R/space/brific/Pages/brificOrientationAngle.aspx | Orientation angle information |
| Additional information related to N-GSO satellite networks | https://www.itu.int/en/ITU-R/space/brific/Pages/brificAdditionalInformation.aspx | Non-GSO additional information |

### Special publications

| Link text | URL | Notes |
|---|---|---|
| Resolution 609 (Rev. WRC-07) Consultation meeting | https://www.itu.int/en/ITU-R/space/Pages/res609.aspx | Consultation meeting pages |
| Resolution 900 (WRC-03) | https://www.itu.int/net/ITU-R/space/res900/index.asp | Resolution 900 publications |
| Change of notifying administration | https://www.itu.int/en/ITU-R/space/brific/Pages/brificChangeAdm.aspx | Notices whose notifying administration changed |

The sidebar links the Space Services Department home (https://www.itu.int/ITU-R/go/space/en), Space Support (https://www.itu.int/en/ITU-R/space/support/Pages/default.aspx) and Space Explorer (https://www.itu.int/en/ITU-R/space/ITUSpaceExplorer/Pages/default.aspx). The support page carries the EPFD material (XML format of EIRP/pfd masks, EPFD software and validation support), the filing FAQ and the BR Circular Letters.

## Access and distribution

### Who gets in

The access page states that the circular is delivered to administrations and paying subscribers through the web-based ISO file, the online application and DVD-ROM. Member State administrations have unlimited free access to the BR IFIC Online and to the ISO distribution through all TIES accounts of the administration (the TIES expansion above is background, not from the page). Users who are not from a Member State administration and hold a paid subscription nominate a designated user per subscription through ITU Sales (sales@itu.int); that user is granted the online application and the ISO download. The user guide calls the BR IFIC "a paying service" and says earlier issues than 2987 are available only on DVD-ROM or ISO through the Sales Department.

### The ISO disc image

Administrations and subscribers download the ISO file at https://www.itu.int/pub/R-SP-LN.IS with their designated user's login: select the year, then click the folder logo. The ISO is the exact copy of the DVD-ROM, is made available on the publication date, and is described in Circular Letter CR/360 of 13 March 2014 (https://www.itu.int/md/R00-CR-CIR-0360/en). It can also be downloaded from the online application. The 2021 explanation PDF adds that each edition has two files, a zip of the ISO image and a SHA-1 checksum file, that the uncompressed image is close to 3 GB, and that it can be mounted as a virtual DVD drive. The user guide says the desktop application on the ISO is started with brific-space.exe and lists the disc layout: br_soft (BR software), databases (technical data and databases), ific_publications (Parts and Special Sections) and Support_documents (the Preface).

Fetched without a login on 6 November 2026, the ISO page is a catalogue entry titled "BR International Frequency Information Circular (BR IFIC) - Space Service" with a Sign In link, year entries for 2026, 2025 back to 2015, 2014 and 2010, and a "Publication Notice with Order Form". Its text also states that the Terrestrial services DVD is published at the same time and that the SRS database formerly sold separately is now available only in this product.

### The online application

The online page says the Bureau's web application at https://www.itu.int/epublications/brific-space has been available to registered users since 23 January 2024 and covers every issue from BR IFIC 2987 of 10 January 2023. It offers:

| Feature | What the page and the user guide say |
|---|---|
| Publications | All Special Sections and Parts as PDF, including notes from administrations and from the Bureau; list exportable as CSV; publication cards; zip download structured as Brific-space-xxxx with Ific_publications and Databases |
| Technical data | TSUM, Appendix 8 results, EPFD input, results and summary, AP30/30A and AP30B results, interference analysis; not every publication has technical data |
| Specific queries | Affected administrations by a coordination request; affected networks by a coordination request; networks potentially interfering with networks of my administration |
| Databases | SRS, SPS (Space Plans Systems), Appendix 30B, GIMS, BRIFIC and SRS-RES35, downloadable with size shown; the full SRS and GIMS databases exist only in the BRIFIC |
| Other data | List of technical data, the SNS-removal list and the SpaceCom draft database |
| Mobile | Only the PDF publications |

The user guide restricts the queries: they are online only (the desktop application lacks them, use BRSIS-SpaceQry locally), limited to the non-planned bands and to the data published in the selected issue, consider only modified data for modifications, and ignore general publications such as bringing into use, suspension or suppression that do not change the interference situation. User support: spacehelp@itu.int for feedback, sales@itu.int for access.

### DVD-ROM

From 1 January 2025 the main means of distribution are the ISO file and the online application; the physical DVD-ROM is discontinued except for administrations and subscribers who explicitly ask ITU Sales to keep it (the page prints the Sales telephone and fax numbers). Slide 8 gives the history: weekly circulars on paper, microfiche and floppy disk before 2000, CD-ROM from issue 2410 (11 January 2000), DVD-ROM from 2710 (10 January 2012), web-based ISO from 2014, dual-layer DVD from 2833 (22 November 2016) and the online application from 23 January 2024; the slide refers to Circular Letter CR/508 for the distribution arrangements.

> [!IMPORTANT]
> A hackathon team without a TIES account or a paid subscription cannot open the online application, its three queries or the ISO download. The free route is the zipped IFIC database of each issue on the "BR IFIC database" page, documented in [ITU Space IFIC databases](../itu-space-ific-databases/README.md). That page states that the free databases hold the SNS data of Parts I-S, II-S and III-S and of the Special Sections API/A and CR/C when they appear in the issue's table of contents; the Plan data have their own pages listed above (AP30/30A database, AP30B database).

What an anonymous visitor gets from the application entry point:

```bash
curl -sS -L --max-time 60 -A "Mozilla/5.0 (Macintosh) AppleWebKit/537.36 Chrome/124 Safari/537.36" \
  -o brific_space.html -w "%{http_code} %{url_effective}\n" "https://www.itu.int/epublications/brific-space"
```

```text
200 https://www.itu.int/epublications/brific-space
```

The saved file is a 3,404-byte application shell titled "BR IFIC Space services: Home page"; the content is loaded by scripts and the shell holds no publication data.

## Publication schedule

The schedule page lists the 2026 issues as follows (dates in the page's own dd.mm.yyyy form).

| No. | Date | No. | Date |
|---|---|---|---|
| 3062 | 06.01.2026 | 3075 | 07.07.2026 |
| 3063 | 20.01.2026 | 3076 | 21.07.2026 |
| 3064 | 03.02.2026 | 3077 | 04.08.2026 |
| 3065 | 17.02.2026 | 3078 | 18.08.2026 |
| 3066 | 03.03.2026 | 3079 | 01.09.2026 |
| 3067 | 17.03.2026 | 3080 | 15.09.2026 |
| 3068 | 31.03.2026 | 3081 | 29.09.2026 |
| 3069 | 14.04.2026 | 3082 | 13.10.2026 |
| 3070 | 28.04.2026 | 3083 | 27.10.2026 |
| 3071 | 12.05.2026 | 3084 | 10.11.2026 |
| 3072 | 26.05.2026 | 3085 | 24.11.2026 |
| 3073 | 09.06.2026 | 3086 | 08.12.2026 |
| 3074 | 23.06.2026 | 3087 | 05.01.2027 |

- Space IFIC 3074, the graded issue, was published on 23 June 2026. Issue 3076 was published on 21 July 2026; the Terrestrial IFIC 3076 that the brief grades carries the same number and date on the terrestrial page, see [ITU BR IFIC (Terrestrial services)](../itu-terrestrial-brific/README.md). Both dates are Tuesdays, as slide 10 says.
- The page also holds the 2025 table (3037 of 7 January 2025 to 3061 of 9 December 2025, followed by 3062), and the 2024 and 2023 tables (3012 to 3036, and 2987 to 3011).

> [!TIP]
> At the time of checking, the latest issue with a published database was 3083 of 27 October 2026. The next issue, 3084, is due on 10 November 2026, two days after the hackathon; the brief's "forthcoming IFICs shall be able to be evaluated" requirement can be demonstrated on it.

## Database structure

### The SNS V9.1 data-items description

The PDF is titled "Details relating to the contents of the SNS data items published in Part I-S, II-S, III-S and the Special Sections of the BR IFIC". It has 30 pages, server last-modified 17 January 2024. Each row gives the table name, data item, the Appendix 4 item it carries, the format, flags for the AP4 annexes (4/2 space stations, 4/3 earth stations, Plans), a description and a comment such as PK (primary key), FK (foreign key), "derived data" or "BR internal data". Formats are picture strings: 9(9) is a nine-digit integer, X(3) a three-character text, S9(3).9(2) a signed decimal, and dates are yyyymmdd.

The tables appear alphabetically within each section, starting with adm_assoc (administrations "on behalf of" which a notice was submitted), assgn (assigned frequency, with freq_assgn and the derived freq_mhz), c_pfd (compliance with pfd limits: freq_min, freq_max, pfd in dB(W/m²), bdwdth), carrier_fr (carrier frequencies), the cmr_* tables (Resolution 49 and 552 commercial system data), coord_agree_ntw (network-level coordination agreements), diag_grp, the e_* tables (earth station antenna, elevation, associated earth station, service class, earth station) and emiss (designation of emission, peak envelope power, power density). Page 28 starts the reference tables and page 29 the BR internal data; the last table, srs_ooak, records the database version and creation date.

Tables that matter most for finding cases relevant to Finland:

| Table | Columns to know | Use |
|---|---|---|
| notice | ntc_id, adm, ntwk_org, ntf_rsn, ntc_type (G, N, S, T or R), d_rcv, wic_no, wic_part, d_wic, tgt_ntc_id | One row per notice; which issue and part published it, which administration filed it, geostationary or not |
| geo, non_geo, orbit, phase | sat_name, long_nom (geo); orbital planes and initial phase angles of a non-geostationary satellite (orbit, phase) | Satellite identity, nominal longitude and orbit |
| grp | grp_id, ntc_id, beam_name, emi_rcp (E or R), freq_min, freq_max, bdwdth, d_inuse, fdg_reg, fdg_plan, fdg_tex, wic_no, d_wic | Frequency groups per beam; the derived freq_min and freq_max give the band in MHz |
| assgn, emiss | freq_assgn, freq_mhz; design_emi, pep_max, pwr_ds_max | Assigned frequencies and emission power densities |
| c_pfd | freq_min, freq_max, pfd, bdwdth | Declared pfd compliance values |
| provn, tr_provn | coord_prov, agree_st (O obtained, R requested), adm | Coordination provisions and the administrations involved |
| all_aff_ntw, tr_aff_ntw | aff_ntc_id, coord_prov, adm, sat_name, long_nom, f_cause, f_rec, wic_no | Affected or affecting networks per group and per transaction |
| gpub, pub_ssn | pub_ref, pub_no, ssn_ref, ssn_no, ssn_rev, wic_no, d_wic | Which Part or Special Section published a group or notice |

The country symbol in adm is the three-letter ITU symbol listed in Table 1A of the Preface; the terrestrial BR IFIC 3076 Article 11 index captured for this repository uses FIN for Finnish notices.

### The diagram

The one-page SNS V9.1 diagram was generated on 23 February 2023 with DbSchema. It draws the tables with their column types (INTEGER, SMALLINT, VARCHAR, NUMERIC, DOUBLE, TIMESTAMP) and their key relations, grouped into the main tables, BR internal data, the C/I tables for the Plans and AP30B, and the reference tables. It includes the res35_* and scraft_cmr_* tables that the data-items PDF only partly lists.

> [!WARNING]
> The databases page states that from 7 January 2025 all Space IFIC databases are published in the new restructured Space Network System database version 10. The V9.1 description linked here is the latest description published on this page. Checked against the table catalogue of ific3074.mdb recorded for [ITU Space IFIC databases](../itu-space-ific-databases/README.md): the file has 88 user tables, of which 13 are described neither in the V9.1 PDF nor in the diagram (aesim_param, epfd_freq, epfd_param, es_ctry, interf_poc, isl_param, ngeo_diag_grp, ntc_tmp, orbit_set, ras_ant_type, res35_sp_stn_deploy, res8_sp_stn, srvlnk_sat), while diag_grp, res35_notice and res35_ntc_lnk from the V9.1 documents are absent from the file. Treat the V9.1 documents as a guide to column meanings, and read the current Preface for the version 10 layout.

The legend PDFs on the "Data items description in publication" page explain the data items as printed in the PDF Parts and Special Sections rather than the database columns; the page lists the English legend at 212 KB.

## How to use it for the challenge

1. Pick the issue from the schedule table above; for the graded case it is 3074 of 23 June 2026.
2. Get its database from the free databases page (https://www.itu.int/sns/wic/demowic26.html for 2026). The 3074 file is https://www.itu.int/sns/ific10/ific3074.zip, 60,837,631 bytes (58.0 MiB), server last-modified 23 June 2026 06:25:33 GMT; it unzips to ific3074.mdb, 286,654,464 bytes (273.4 MiB), a Microsoft Access file. The sibling page documents the download and how the catalogue was read on macOS with the pure-Python access-parser library. Check the file without downloading it again:

   ```bash
   curl -sS -o /dev/null -I -L --max-time 60 -A "Mozilla/5.0 (Macintosh) AppleWebKit/537.36 Chrome/124 Safari/537.36" \
     -w "%{http_code} %{content_type} %{url_effective}\n" "https://www.itu.int/sns/ific10/ific3074.zip"
   ```

   ```text
   200 application/zip https://www.itu.int/sns/ific10/ific3074.zip
   ```

3. Read the Preface (https://www.itu.int/ITU-R/go/space-preface/en) for the layout of the issue. Slide 16 says it has four sections (General; description of the BR IFIC and SRS database information; description of the SNS; reference tables), that it is to be used when consulting the IFIC and SRS data, and that the edition and new changes should always be checked.
4. See which Special Sections the issue contains through the Space Explorer tables of contents linked under "Publications online". The older table-of-contents query at https://www.itu.int/sns/ific.html (Space Network Systems Online, covering issues from WIC 1418 onwards) leads to the SNL (Space Network List) query page, which carries a notice dated 28 September 2026 that the SNL technology is obsolete and that Space Explorer (https://www.itu.int/go/ITUSpaceExplorer) should be used instead.
5. Use the data-items PDF and the diagram for table semantics, then filter: notices in the issue by wic_no and wic_part, publication references in gpub or pub_ssn for the API/A, CR/C and AP30 families, administrations in all_aff_ntw, tr_aff_ntw and provn, and frequency bands from grp.freq_min and grp.freq_max against the Finnish Frequency Allocation Table ([Regulation 4](../finlex-regulation-m4/README.md) and the [Traficom frequency table API](../traficom-frequency-table-api/README.md)).
6. For the pfd and EPFD side, the declared values sit in c_pfd and emiss, the Bureau's EPFD inputs and results are linked under "Additional information", and the limits are in the [Radio Regulations](../itu-radio-regulations/README.md).
7. The Bureau's own tools (SpaceQry, SpaceCom, GIBC, GIMS) are Windows-only desktop applications; see [ITU space software](../itu-space-software/README.md). The user guide's advanced queries (affected administrations, affected networks, interfering networks) exist only behind the login.

Checking any description file without downloading it, as run on 6 November 2026:

```bash
curl -sS -I -L --max-time 60 -A "Mozilla/5.0 (Macintosh) AppleWebKit/537.36 Chrome/124 Safari/537.36" \
  "https://www.itu.int/en/ITU-R/space/Documents/sns_dbv91.pdf" | grep -iE "^(HTTP|content-length|last-modified)"
```

```text
HTTP/1.1 200 OK
Content-Length: 853162
Last-Modified: Wed, 17 Jan 2024 15:54:55 GMT
```

## Key facts for the team

| Fact | Value | Source |
|---|---|---|
| Cadence | Every two weeks, always a Tuesday, generally 25 issues a year | Page; slide 10 |
| Legal basis | RR Nos. 20.2 to 20.6 and 20.15 | Page |
| Graded space issue | 3074, published 23 June 2026 | Schedule page; brief |
| Graded terrestrial issue | 3076, published 21 July 2026 | Schedule page; terrestrial page; brief |
| Next issue after the hackathon | 3084, 10 November 2026 | Schedule page |
| Free database for 3074 | ific3074.zip, 60,837,631 bytes (58.0 MiB), ific3074.mdb 286,654,464 bytes (273.4 MiB), 88 user tables | Databases page; sources recorded for this repository |
| ISO image | Close to 3 GB uncompressed, zip plus SHA-1 checksum per edition | ISO explanation PDF |
| Online application | Since 23 January 2024, issues from 2987 (10 January 2023), login required | Online page; user guide |
| Comment window | Four months from the publication date | Slides 5 and 10 |
| Database version | V9.1 described on the page; databases in version 10 since 7 January 2025 | Page; databases page |
| Special Sections named by the brief | API/A, CR/C, AP30, AP30A, AP30B | Brief; slide 13 |

## Related pages

- [Documentation index](../../README.md)
- [Challenge brief](../../challenge-brief/README.md): the mandatory datasets, the graded issues and the evaluation weights
- [ITU Space IFIC databases](../itu-space-ific-databases/README.md): the free zipped databases, including ific3074.zip and its table catalogue
- [ITU BR IFIC (Terrestrial services)](../itu-terrestrial-brific/README.md): the terrestrial circular and the graded issue 3076
- [ITU space software](../itu-space-software/README.md): SpaceQry, SpaceCom, GIBC and GIMS
- [ITU Radio Regulations](../itu-radio-regulations/README.md): Articles 9, 11 and 22, Appendix 4 and the Plans
- [Regulation 4 (M4)](../finlex-regulation-m4/README.md) and the [Traficom frequency table API](../traficom-frequency-table-api/README.md): the Finnish side of the comparison
- [PM pack](../../pm-pack/README.md): the planning documents and what the brief has answered since they were drafted

## Caveats

- The page is a SharePoint site whose link targets change; the "go" short links redirect (space/snl/en to the Space Networks Hub, space-epfd-data to the EPFD index page) and the news page warns that some links to documents within the BR IFIC may not work.
- The news page links its PDFs with http URLs; the https forms listed above returned 200 on 6 November 2026.
- The Space Explorer tables of contents are a JavaScript application: curl returns the application shell titled "ITU Space Explorer", so a scraper needs a browser or the application's own data endpoints. The SNL table-of-contents query is marked obsolete since 28 September 2026.
- "Log into the BRIFIC (Space services) online", the ISO download and the three online queries require a TIES or subscriber login.
- The desktop application (brific-space.exe) and the BR software are Windows programs; the software page says only Windows 10 and 11 are supported.
- The data-items description and diagram describe SNS version 9.1; the databases of 2025 and 2026 use version 10, see the warning above. The ific3074.mdb table list in this repository shows the differences.
- The access page and the user guide describe the BR IFIC as a paying service outside Member State administrations; the free zipped databases are described on their page as "a free service on a trial basis until further notice".
- Dates on the ITU pages use dd.mm.yyyy; the brief uses the same issue numbers for the space and terrestrial circulars, so always state which circular a number refers to.
