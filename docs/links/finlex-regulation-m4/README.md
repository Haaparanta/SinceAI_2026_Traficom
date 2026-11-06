# Regulation 4 (M4): Radio Frequency Regulation 4 AG/2026M on Finlex

Traficom's Radiotaajuusmääräys (Radio Frequency Regulation) 4 AG/2026M, with the Finnish Frequency Allocation Table as its annex, is the mandatory national baseline against which the challenge compares ITU BR IFIC publications.

| Field | Value |
|---|---|
| Link | [https://www.finlex.fi/fi/viranomaiset/maarayskokoelmat/traficom-viestinta/2026/3](https://www.finlex.fi/fi/viranomaiset/maarayskokoelmat/traficom-viestinta/2026/3) |
| Publisher | Finlex (Ministry of Justice legal database, maintained by the Legal Register Centre); regulation issued by Liikenne- ja viestintävirasto Traficom (Finnish Transport and Communications Agency) |
| Language | Page and regulation in Finnish, Swedish and English; Appendix 2 of the regulation is trilingual |
| Access | Free, no login |
| Format | Client-rendered web page with metadata; the regulation and its explanatory notes are PDF downloads |
| Checked | 6 November 2026 |

> [!NOTE]
> This page was written on 6 November 2026 from the live Finlex page (Finnish and English views), the four PDFs it links to, the Traficom open-data API and the challenge brief. It summarises rather than replaces the source. If this page and the source differ, the source is authoritative.

## What it is

Regulation 4 is Traficom's Radiotaajuusmääräys (Radio Frequency Regulation). The current edition is numbered 4 AG/2026M. It was issued on 26 March 2026, entered into force on 31 March 2026 and is valid until further notice. It repeals the previous edition 4 AF/2025M of 27 March 2025. Each edition carries the full text, so the 2026 PDF is the only one you need.

The regulation itself is two pages. Its substance is the annexed Taajuusjakotaulukko (Frequency Allocation Table), which lists every frequency band from 100 Hz to 400 GHz, the radio services allocated to it in Finland, and the sub-bands, station classes, powers, channel widths and duplex arrangements that apply. The challenge brief calls this document "M4" and lists it as a mandatory dataset.

Key identifiers from the Finlex page and the PDF:

| Field (Finlex) | Value |
|---|---|
| Viranomainen (authority) | Liikenne- ja viestintävirasto (Traficom): Viestintä (Communications) |
| Tyyppi (type) | Määräys (Regulation; the English page says "Ordinance") |
| Määräyskokoelman numero (collection number) | 4 AG/2026M |
| Antopäivä (date of issue) | 26.3.2026 |
| Voimaantulo (entry into force) | 31.3.2026 |
| Voimassa (validity, from the PDF) | Until further notice |
| Diaarinumero (register number) | TRAFICOM/265115/03.04.05.00/2025 |
| Asiasanat (keywords) | radiotaajuus, radiotaajuusmääräys (radio frequency, radio frequency regulation) |
| Säädösperusta (legal basis) | Sections 96(1) and 97(2) of the Act on Electronic Communications Services (917/2014) |
| Sanctions (from the PDF) | Section 348(1) of the same Act |
| EU-säädöksen täytäntöönpano (EU implementation) | None listed on the page; the PDF says the regulation is notified to the European Commission under Directive (EU) 2015/1535 |
| Muutostiedot (change information) | Repeals Regulation 4 AF/2025M of 27 March 2025 |
| Saatavissa (available from) | Traficom, PL/PB 320, 00059 TRAFICOM (switchboard number printed on the page) |
| Signed by | Jarkko Saarimäki, Director-General, and Emil Asp, Deputy Director-General, Helsinki, 26 March 2026 |

Drafting history, from the explanatory notes: stakeholder consultation ran from 22 August to 22 September 2025 on Lausuntopalvelu.fi (the Finnish government consultation service; comments are published there in Finnish), after which the Ministry of Economic Affairs and Employment notified the European Commission between 4 December 2025 and 5 March 2026 under Directive (EU) 2015/1535.

### Language versions

| Language | Finlex page | Regulation PDF | Explanatory document |
|---|---|---|---|
| Finnish | [fi/.../2026/3](https://www.finlex.fi/fi/viranomaiset/maarayskokoelmat/traficom-viestinta/2026/3) | [main.pdf (1070975)](https://www.finlex.fi/api/media/authority-regulation/1070975/mainPdf/main.pdf?typeDiscriminator=traficom-communications&timestamp=2026-06-11T18%3A09%3A49.000Z) | [Perustelumuistio (explanatory memorandum)](https://www.finlex.fi/api/media/authority-regulation/1070975/media/Perustelumuistio%20Radiotaajuusm%C3%A4%C3%A4r%C3%A4ys%204AG2026M.pdf?typeDiscriminator=traficom-communications&timestamp=2026-06-11T18%3A10%3A25.000Z) |
| Swedish | [sv/.../2026/3](https://www.finlex.fi/sv/myndigheter/foreskriftssamlingar/traficom-viestinta/2026/3) | Linked from the Swedish page (not captured here) | Not captured here |
| English | [en/.../2026/3](https://www.finlex.fi/en/authorities/regulations/traficom-viestinta/2026/3) | [main.pdf (1070976)](https://www.finlex.fi/api/media/authority-regulation/1070976/mainPdf/main.pdf?typeDiscriminator=traficom-communications&timestamp=2026-06-11T18%3A09%3A49.000Z) | [Explanatory notes](https://www.finlex.fi/api/media/authority-regulation/1070976/media/Explanatory%20notes%20Radio%20Frequency%20Regulation%204AG2026M.pdf?typeDiscriminator=traficom-communications&timestamp=2026-06-11T18%3A10%3A28.000Z) |

The Finnish text is the one Traficom issued; the English edition is the agency's own translation of the same regulation and carries the same number and dates. Use the English PDF for reading and the API (below) for data.

## Why it matters for the challenge

The brief asks for a workflow that monitors International Telecommunication Union (ITU) Radiocommunication Bureau (BR) International Frequency Information Circular (IFIC) publications and identifies cases relevant to Finland. Its guidance is that a successful solution must take into account the Finnish radio frequency usage, "i.e. Regulation 'M4' and additional frequency tables of special interest provided on the challenge platform", and use them for comparisons and interference recognition. In practice this means:

- Every satellite network or terrestrial assignment found in Space IFIC 3074 or Terrestrial IFIC 3076 has a frequency range; M4 tells you which Finnish service is allocated there, whether it is primary or secondary, and what station classes and powers are in use. A notice that overlaps a Finnish primary allocation is a candidate case.
- The brief's evaluation criteria reward case recognition accuracy (15 %) and auditability (15 %). Citing the M4 row (band, service, sub-band, comment) that a finding rests on is the simplest way to make a finding expert-reviewable.
- The brief also mentions the "list of frequencies of special interest", a synthetic XLS on the SinceAI platform (not in this repository). It complements M4 with specific Finnish stations, positions and power flux density (pfd) limits; M4 remains the regulatory baseline.
- The 2026 amendments (below) include a new primary Earth exploration-satellite allocation and GNSS-protection notes, both of which bear directly on satellite analysis.

See [the challenge brief notes](../../challenge-brief/README.md) for the full task description.

## What the PDF contains

The English edition has 258 pages, the Finnish edition 239 (the Finnish table is typeset more compactly; the content is the same). Structure of the English PDF:

| Part | Pages (EN) | Content |
|---|---|---|
| Regulation text | 1-2 | Header data, sections 1-4, signatures, list of enclosures |
| Annex: amendments | 3-4 | "Amendments made to the Radio Frequency Regulation 4 AF/2025M since 31 March 2025", by service |
| Annex: equipment conditions | 5-9 | Inductive equipment, NMR equipment, UWB, WAS/RLAN 57-71 GHz, security scanners, amateur transmitters |
| Frequency Allocation Table | 10-239 | The table itself, 8.3 kHz to 400 GHz |
| Appendix 1 | 240-242 | Definitions of the table's columns and terms |
| Appendix 2 | 243-244 | List of abbreviations (Finnish, Swedish, English) |
| Appendix 3 | 245-246 | Standards for PMR (Professional/Private Mobile Radio) equipment |
| Appendix 4 | 247-258 | Maritime HF channel tables (4 to 25 MHz bands) |

Files and sizes, as served on 6 November 2026:

| File | Bytes | Approx. |
|---|---|---|
| Finnish regulation (main.pdf, id 1070975) | 1,564,006 | 1.49 MiB |
| English regulation (main.pdf, id 1070976) | 1,425,953 | 1.36 MiB |
| Finnish Perustelumuistio (explanatory memorandum), 3 pages | 76,799 | 75.0 KiB |
| English Explanatory notes, 3 pages | 97,084 | 94.8 KiB |

### The regulation text (sections 1-4)

- Section 1, Scope of application: the regulation applies to the radio frequency spectrum 100 Hz to 400 GHz. Radio transmitters must meet its requirements for transmitting and receiving frequencies, channel spacing, bandwidth of transmission, duplex separation, transmitted powers and other corresponding radio characteristics, which the regulation calls radio interfaces. Industrial, scientific and medical (ISM) equipment may only be used on the frequencies and conditions the regulation sets.
- Section 2, Objective: fair availability and efficient, appropriate and sufficiently interference-free use of radio frequencies.
- Section 3, Definitions: the allocation of frequencies, bands and sub-bands to purposes of use, the radio interface requirements and the ISM bands and conditions are all in the annexed Frequency Allocation Table. There is no separate definitions section in the regulation body; the definitions are Appendix 1 of the table.
- Section 4, Entry into force: 31 March 2026, in force until further notice; repeals 4 AF/2025M of 27 March 2025.

### The equipment annex (pages 5-9)

A five-page annex gives conditions for licence-exempt or special equipment classes, mostly by reference to European Conference of Postal and Telecommunications Administrations (CEPT) Electronic Communications Committee (ECC) decisions, European Commission implementing decisions and ETSI standards: inductive equipment (ERC/REC 70-03, Decision 2006/771/EC as supplemented by (EU) 2025/105), enclosed NMR equipment at 9 kHz to 130 MHz, generic and vehicular ultra-wideband (UWB) at 3.1-4.8 GHz and 6.0-9.0 GHz (ECC/DEC/(06)04, (EU) 2019/785 and 2024/1467), tank and level probing radars, ground and wall probing radar, wide-band data transmission (WAS/RLAN) at 57-71 GHz, indoor security scanners at 69.8-79.9 GHz and 76.5-80.5 GHz, and a clause allowing amateur licences to permit higher power than the table states. Each entry refers to Regulation 15 for the licence-exempt conditions.

### The Frequency Allocation Table (pages 10-239)

The explanatory notes describe the table as containing "provisions on the allocation of different radio frequencies, frequency bands and sub-bands for different purposes of use" together with the requirements on transmitting and receiving frequencies, channel spacing, bandwidth, duplex separation and transmitted powers. The table takes the ITU Radio Regulations into account; the notes state that the Radio Regulations were implemented in Finland by Decree 12/2000. Traficom publishes the table (the "radio frequency utilisation plan") so that equipment manufacturers and users know how frequencies are used and what protection frequency planning gives to radio networks, and so that manufacturers can meet their information duties under Article 10 of the Radio Equipment Directive 2014/53/EU.

Each row of the table pairs a frequency band and its service(s) with one or more sub-bands and their usage. The columns, as defined in Appendix 1:

| Column | Meaning (per Appendix 1) |
|---|---|
| Frequency band, services in Finland | Band and services in use or intended in Finland; based on the Radio Regulations (RR) and ERC Report 25 (the European Common Allocation table) |
| Sub-band, width, usage | Sub-bands and their intended use; in mobile and fixed services the limits are the centre frequencies of the extreme channels |
| Mode of traffic | Simplex (one frequency) or duplex (two frequencies) |
| Class of station | Based on the RR; the example given is FB for a land mobile base station |
| Direction | TX, RX or TXRX |
| Channel width | Separation between centre frequencies of adjacent channels |
| Bandwidth | Necessary bandwidth allowed for a transmission |
| Class of emission | Modulation and information type |
| Duplex separation and paired band | Distance (+ or -) to the paired band |
| Standard type | Properties of radio link equipment, for example DRS 34/18000 |
| Radiated power | Transmitter power plus antenna gain minus line loss, stated in W ERP (dipole reference) or W EIRP (isotropic reference) |

Primary and secondary allocations: Appendix 1 states that in the table "primary services are written with upper case letters (e.g. MOBILE) and secondary services with lower case letters (e.g. Mobile)". That is the whole explanation given; the regulation does not restate the ITU priority rules between primary and secondary services (those are in the Radio Regulations, see [ITU Radio Regulations](../itu-radio-regulations/README.md)). The same convention carries over into the API, where `Services_in_Finland` is upper case for primary (for example `EARTH EXPLORATION-SATELLITE`) and mixed case for secondary (`Amateur`).

Class-of-station codes: Appendix 1 says only that the class of station is based on the Radio Regulations and gives FB as an example. The codes appear in the table as a name plus code, for instance "Space station (EW) TX" and "Earth station (TW) RX" on the 8025-8400 MHz row. Appendix 2 expands a handful of them (LR, Radiolocation Land Station) but is not a full code list; the API's `Class_of_station` field uses 39 distinct values on 6 November 2026, including Earth station (TC/TE/TM/TT/TW/UE/UV/UY), Space station (EC/EE/EG/EI/EM/EN), Fixed station (FX), Base station (FB), Ship station (MS) and Amateur station (AT).

Other Appendix 1 definitions worth knowing: data transmission (anything other than real-time person-to-person communication), duty cycle (maximum "on" time per hour), radio transmitters with a high risk of interference (broadcasting transmitters, high-power radars and R&D licences, which may require Traficom inspection before commissioning under section 42 of the Act), and the status of standard references, which are informative only and always mean the latest version published in the Official Journal of the EU.

### Appendices 2-4

Appendix 2 is a two-page trilingual list of abbreviations (ADS-B to VOR), including ECA (European Common Allocation), HEST and LEST (high and low EIRP satellite terminals), HDFSS (high density fixed satellite service), RR AP30B (Appendix 30B of the Radio Regulations), SRD, UWB and VIRVE (the Finnish public authority network). Appendix 3 lists the ETSI standards assumed for PMR radiotelephones and telemetry equipment by channel spacing. Appendix 4 holds the maritime HF channel tables: paired radiotelephony channels in the 4, 6, 8, 16 and 22 MHz bands, unpaired frequencies, paired telex (NBDP) frequencies and data transmission channels, with the distress and safety calling channels marked.

## Amendments in the 2026 edition

The annex on pages 3-4 lists every change since 31 March 2025; the explanatory notes summarise the main ones. Condensed by service:

| Service | Change |
|---|---|
| Satellite | A primary "Earth Exploration-Satellite" allocation added in the sub-band 8025-8400 MHz |
| Satellite / GNSS | References to ECC/DEC/(25)01 and Recommendation ITU-R M.2164 on the protection of GNSS added to the comments for 1240-1300 MHz |
| Government | 738-753 MHz allocated to use by public authorities; the usage plan is still under review |
| Military | The "Mobile" allocation corresponding to military use at 230-240 MHz changed from secondary to primary |
| Broadcasting | The primary "Broadcasting" allocation at 230-267 MHz removed |
| Short-range devices | Wide-band data transmission extended to 916.4-919.4 MHz and non-specific SRDs to 916.1-919.4 MHz, per Commission Implementing Decision (EU) 2025/650; reference to (EU) 2025/913 added for WAS/RLAN at 5945-6425 MHz |
| Fixed (radio links) | 8 GHz: 56 MHz channel plan extended from three to five channels, mobile programme links ended; 15 GHz: "No new licences" on 14 MHz channels with 308 MHz duplex separation; 23 GHz: 56 MHz channel plan extended from two to nine channels; 38 GHz: 3.5, 7 and 14 MHz channel plans removed |
| Land mobile | Sub-band usage names simplified (for example "PMR" became "Radiotelephony for business activities"); simplex allowed at 78.100-80.000 MHz; several split sub-bands merged; "Mobile" replaced by "Land mobile" for three sub-bands in 154-174 MHz |
| Aeronautical mobile | The national common frequency use removed from 119.700 MHz |
| Amateur | 433/434 MHz sub-bands with 1.6 MHz duplex separation removed; FM calling-frequency comments added at 29.600, 51.510, 145.500 and 433.500 MHz |

> [!IMPORTANT]
> For satellite and space analysis the two rows to remember are 8025-8400 MHz, now EARTH EXPLORATION-SATELLITE (SPACE-TO-EARTH) as a primary service with a comment pointing to RR footnote 5.462A and an earth station at Sodankylä Tähtelä noted in the neighbouring 7700-8500 MHz fixed-service entry, and 1240-1300 MHz, where the comments now cite ECC/DEC/(25)01 and ITU-R M.2164 on GNSS protection. Both can be pulled from the API by filtering on `Sub_band_lower_limit__Hz_`.

## Relation to the Traficom open-data API

The same Frequency Allocation Table is served as JSON by Traficom's open-data service, which the brief and the repository README link next to the Finlex page:

| Resource | URL |
|---|---|
| Swagger UI (Taajuusjakotaulukko section) | [https://opendata.traficom.fi/swagger/ui/index#/Taajuusjakotaulukko](https://opendata.traficom.fi/swagger/ui/index#/Taajuusjakotaulukko) |
| Swagger 2.0 spec | [https://opendata.traficom.fi/swagger/docs/v13](https://opendata.traficom.fi/swagger/docs/v13) |
| English table | [https://opendata.traficom.fi/api/v13/Taajuusjakotaulukko](https://opendata.traficom.fi/api/v13/Taajuusjakotaulukko) |
| Finnish table | [https://opendata.traficom.fi/api/v13/Taajuusjakotaulukko_fin](https://opendata.traficom.fi/api/v13/Taajuusjakotaulukko_fin) |
| Swedish table | [https://opendata.traficom.fi/api/v13/Taajuusjakotaulukko_swe](https://opendata.traficom.fi/api/v13/Taajuusjakotaulukko_swe) |

On 6 November 2026 the English endpoint returned 5917 rows (4,359,860 bytes), with the OData (Open Data Protocol) query options `$filter`, `$select`, `$orderby`, `$top`, `$skip` and `$count`. The field names mirror the PDF columns (`Frequency_band_lower_limit`, `Services_in_Finland`, `Sub_band_usage`, `Class_of_station`, `Direction`, `Radiated_power`, `Comment`, and so on) and add integer `Sub_band_lower_limit__Hz_` and `Sub_band_upper_limit__Hz_` fields that make range queries easy. 856 of the rows have "SATELLITE" in the service name. The API is licensed under Creative Commons BY 4.0 according to the spec.

The PDF on Finlex is the legally binding text; the API is a convenience copy. Neither the API nor the spec states which regulation edition the data reflects, so record the download date with any extract. The field-level details are on [the frequency table endpoint page](../traficom-frequency-table-api/README.md) and the service as a whole on [the Swagger UI page](../traficom-opendata-swagger/README.md).

## Relation to Regulation 15

The explanatory notes say that the use of radio transmitter frequencies is also governed by Traficom's Regulation 15 on collective frequencies for licence-exempt radio transmitters, and that "Regulations 4 and 15 are updated simultaneously". The 2026 edition of Regulation 15, 15 AW/2026M, was issued on 26 March 2026 and entered into force on 31 March 2026, at [https://www.finlex.fi/fi/viranomaiset/maarayskokoelmat/traficom-viestinta/2026/4](https://www.finlex.fi/fi/viranomaiset/maarayskokoelmat/traficom-viestinta/2026/4). The challenge brief links the older 15 AV/2025M edition instead. Both are covered on [the Regulation 15 page](../finlex-regulation-m15/README.md). The M4 equipment annex refers to Regulation 15 for every licence-exempt class it lists.

## How to get it

> [!WARNING]
> The Finlex page is a client-rendered Next.js application. The readable text that curl returns is only the site chrome; the metadata and PDF links are present but embedded, escaped, inside a script payload. Use a browser to read the page, or go straight to the PDF URLs above.

The following commands were run on 6 November 2026. The PDF URLs carry a `timestamp` query parameter that Finlex may change when a file is re-uploaded; the same URL without the parameter also returned the file (HTTP 200, same size), but the captured form is the one the page links.

```bash
# The page itself: 200, about 190 kB of HTML, but the metadata is only inside a script payload
curl -sS -o /dev/null -L --max-time 60 -A "Mozilla/5.0" -w "%{http_code} %{size_download}\n" \
  "https://www.finlex.fi/fi/viranomaiset/maarayskokoelmat/traficom-viestinta/2026/3"

# Recover the PDF link from the raw HTML (it is escaped, so grep the path fragment)
curl -sS -L --max-time 60 -A "Mozilla/5.0" \
  "https://www.finlex.fi/fi/viranomaiset/maarayskokoelmat/traficom-viestinta/2026/3" \
  | grep -o 'mainPdf[^"]\{0,120\}' | head -1

# English regulation PDF (1,425,953 bytes)
curl -sS -L --max-time 60 -A "Mozilla/5.0" -o m4_en_main.pdf \
  "https://www.finlex.fi/api/media/authority-regulation/1070976/mainPdf/main.pdf?typeDiscriminator=traficom-communications&timestamp=2026-06-11T18%3A09%3A49.000Z"

# Finnish regulation PDF (1,564,006 bytes)
curl -sS -L --max-time 60 -A "Mozilla/5.0" -o m4_main.pdf \
  "https://www.finlex.fi/api/media/authority-regulation/1070975/mainPdf/main.pdf?typeDiscriminator=traficom-communications&timestamp=2026-06-11T18%3A09%3A49.000Z"

# Row count of the API copy of the table (the reply starts with a UTF-8 byte order mark)
curl -sS -L --max-time 60 -A "Mozilla/5.0" 'https://opendata.traficom.fi/api/v13/Taajuusjakotaulukko/$count'
```

Sample output of the last command:

```text
5917
```

### Extracting text from the PDF

pypdf (tested with version 7.0.0 in a virtual environment) reads the file without errors and reports 258 pages. Page 1 extracts cleanly; the regulation text, the amendment annex and Appendices 1-3 are usable as plain text.

```bash
python3 -m venv venv-m4 && venv-m4/bin/pip install -q pypdf
venv-m4/bin/python -I m4_extract.py m4_en_main.pdf
```

```python
# m4_extract.py
import sys
from pypdf import PdfReader
r = PdfReader(sys.argv[1])
print("pages", len(r.pages))
for i in (0, 2):
    print("--- page", i + 1)
    print(r.pages[i].extract_text()[:300])
```

```text
pages 258
--- page 1
 1 (2)
Finnish Transport and Communications Agency Traficom ...
Issued: 26.3.2026
Enters into force: 31.3.2026
```

> [!TIP]
> Pages 10-239 (the table) extract as one cell per line, with band limits, units and parentheses on separate lines and the column headings repeated between rows, so reconstructing rows from PDF text is error-prone. Take the table data from the API and use the PDF to cite page numbers and to read the Appendices.

## Caveats

- The Finlex HTML is not usable as a data source without a browser or a Next.js-payload parser; treat the PDF and the API as the sources.
- The PDF `timestamp` query parameters (2026-06-11T18:09:49Z for both main PDFs) are later than the issue date; they reflect the upload, not the regulation. They may change.
- The English Finlex page labels the document type "Ordinance" while the PDF and the Finnish page say Määräys / Regulation; the number 4 AG/2026M is the stable identifier.
- The English page lists no EU implementation measure, but the regulation text and the annex cite several Commission implementing decisions ((EU) 2025/650, 2025/913, 2025/105, 2019/785, 2024/1467). Check the annex rather than the page metadata.
- The regulation is updated roughly yearly (4 AF/2025M of 27 March 2025, 4 AG/2026M of 26 March 2026), and the Finlex year listing at [https://www.finlex.fi/fi/viranomaiset/maarayskokoelmat/traficom-viestinta/2026](https://www.finlex.fi/fi/viranomaiset/maarayskokoelmat/traficom-viestinta/2026) is where a newer edition would appear.
- The header pages of the PDFs print Traficom's switchboard number; no personal contact data is involved.

## Related pages

- [Documentation index](../../README.md) and [repository README](../../../README.md)
- [Challenge brief](../../challenge-brief/README.md): why M4 is mandatory and how it is used in comparisons
- [Traficom frequency table API endpoint](../traficom-frequency-table-api/README.md) and [Traficom open-data Swagger UI](../traficom-opendata-swagger/README.md): the JSON copy of the table
- [Regulation 15 (M15)](../finlex-regulation-m15/README.md): licence-exempt collective frequencies, updated together with M4
- [ITU Radio Regulations](../itu-radio-regulations/README.md): the international allocation table and footnotes (for example 5.462A) that M4 builds on
- [CEPT docdb implementation](../cept-docdb-implementation/README.md): the ECC decisions and recommendations M4 cites, with national implementation status
- [ITU Space BR IFIC](../itu-space-brific/README.md) and [ITU Terrestrial BR IFIC](../itu-terrestrial-brific/README.md): the publications whose notices are compared against this table
