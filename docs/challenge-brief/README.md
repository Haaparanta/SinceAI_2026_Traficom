# Challenge brief: Saving Earth from Space Interferers Using Radio Frequencies

What Traficom's official brief for the Since AI Hackathon 2026 asks teams to build, which data is mandatory, how entries are scored, what to submit and whom to ask.

| Item | Value |
|---|---|
| File | [Since_AI_Traficom_Challenge_Brief_FINAL_04112026.pdf](../../Since_AI_Traficom_Challenge_Brief_FINAL_04112026.pdf) in the repository root |
| Size | 281,800 bytes (about 275 KiB), 5 pages |
| Version | Final, dated 4 November 2026 in the file name (FINAL_04112026); the PDF's embedded creation timestamp is 6 November 2026 17:01 (+02:00) |
| Filled in by | Liikenne- ja viestintävirasto (Transport and Communications Agency) Traficom, Spectrum and Space department, the challenge partner |
| Template by | Since AI ry, Espoo, organiser of the Since AI Hackathon 2026 (6-8 November 2026, Turku) |
| Language | English |
| Checked | 6 November 2026 |

> [!NOTE]
> This page was written on 6 November 2026 from the PDF in this repository, using a text extraction of its five pages. It summarises the brief rather than replacing it. If this page and the PDF differ, the PDF is authoritative.

## What the document is

The PDF is Since AI's "Challenge Brief" template for challenge partners, filled in by Traficom's Spectrum and Space department. The template asks each partner to fill in eight numbered sections, and the partner's answers define the challenge teams work on during the hackathon. The page footer names Since AI ry (business ID 3593920-2, Haukilahdenkatu 1 A 89, 02200 Espoo) as the organiser. Questions about the template itself go to Riku Lauttia (riku.lauttia@sinceai.fi; the phone number is in the PDF).

| Section | Title in the brief | Pages | What Traficom filled in |
|---|---|---|---|
| 01 | Challenge Title | 1 | The title and a one-sentence aim |
| 02 | Problem Statement | 1-2 | Context, today's manual process, a possible end-to-end workflow and the terrestrial side quest |
| 03 | Guiding Question | 3 | One question, plus the Finnish data the comparison must rest on |
| 04 | Recommended AI Approaches (marked optional) | 3 | Candidate techniques and a statement that no architecture is required |
| 05 | Dataset or API Provided | 3-4 | Four mandatory and four optional data sources, with URLs for all but the XLS file |
| 06 | Evaluation Criteria | 4-5 | Five weighted criteria summing to 100 % |
| 07 | Submission Format | 5 | Six expected deliverables |
| 08 | Point of Contact | 5 | Discord-first contacts, Q&A stand hours and senior-specialist slots |

## Why it matters

The brief is the only authoritative statement of the task. It fixes four mandatory data sources, names the two International Frequency Information Circular (IFIC) issues used to measure accuracy (Space IFIC 3074 and Terrestrial IFIC 3076), sets the scoring weights and lists the deliverables. Criterion B (25 %) is scored on extensibility and the terrestrial side quest, so skipping the side quest puts up to a quarter of the score at risk. Every design choice in this repository should trace back to a sentence in the brief.

## Section 01: challenge title

The title is "Saving Earth from Space Interferers Using Radio Frequencies". The aim in one sentence: develop an analysis tool that protects national radio frequency use from planned space and terrestrial usage, so that potential harmful interference is prevented.

## Section 02: problem statement

### Why the problem exists

Using radio frequencies (spectrum) requires preliminary planning and obeying the rules of the International Telecommunication Union (ITU), the Radio Regulations. Usage differs between countries and regions. Satellites make the problem global: the brief's example is that Australian terrestrial usage does not interfere with Finnish usage, but an Australian satellite orbiting the Earth may interfere with Finnish terrestrial usage in the same or an adjacent frequency range.

For this reason the ITU's Radiocommunication Bureau (BR; the brief calls it the Radio Bureau) publishes the International Frequency Information Circular (IFIC). The brief describes the publications as separate series for space and terrestrial use, "containing bi-monthly update on both pdf and database format". The ITU's own pages say the circular is published once every two weeks (see the caveats below).

### What specialists do today

- Identify the items in each IFIC that may be relevant to Finland.
- Compare them with other frequency information, especially the Finnish table of frequencies, but also the list of frequencies of special interest.
- When a possible problem is found, assess the technical concerns.
- Prepare follow-up correspondence to the administration planning the usage, either to solve the situation technically before it happens or to preserve the right to claim protection if harmful interference occurs.

### What the challenge asks for

An AI-assisted workflow that reduces manual effort, enhances analysis coverage and increases the quality of analysis, while keeping the analysis transparent and technically reviewable. A first demonstrator may focus on the space-services side, but it should be designed so that the same architecture can later be extended to terrestrial frequency-planning workflows.

### A possible end-to-end workflow

The brief lists nine steps (condensed here):

1. Ingest the relevant national information on frequency usage: regulations and the additional frequency tables provided.
2. Detect, retrieve and ingest new ITU BR IFIC publications, especially the special sections API/A, CR/C and AP30 (including AP30A and AP30B). Background, not from the brief: API/A publishes advance publication information for satellite networks, CR/C publishes coordination requests, and AP30, AP30A and AP30B are Appendices 30, 30A and 30B of the Radio Regulations, which hold the satellite Plans.
3. Possibly use the ITU SpaceCom tool, or direct database logic, to identify interesting satellite systems.
4. Possibly use the ITU GIBC tool (Graphical Interface for Batch Calculations), or direct calculation logic, to calculate power flux density (pfd) values of the satellite systems.
5. Summarise the relevant content and the frequency ranges affecting Finland or Finnish usage.
6. Cross-compare the findings with the national regulations (M4, M15) and the additional frequency tables.
7. Identify items that may concern Finland, based on both previous public material and possible synthetic data on frequencies, pfd limits and geographical locations.
8. Detect and explain potential concerns, including technical calculations such as pfd where appropriate.
9. Identify the relevant counterparty (administration) and draft a correspondence template, for expert review, that describes the possible interference concern.

### Side quest: terrestrial land-mobile notices

The side quest demonstrates the same architecture on terrestrial BR IFIC data, limited to land-mobile notices. It should show that the workflow, with the additions, modifications or simplifications below, supports a different context without turning the submission into a second full challenge.

1. Use consecutive terrestrial BR IFIC issues and identify what is new, modified or withdrawn.
2. Filter foreign assignments that may be relevant to Finland using the notice data.
3. Determine the applicable ITU, CEPT/ECC and national regulatory framework. Background, not from the brief: CEPT is the European Conference of Postal and Telecommunications Administrations and ECC its Electronic Communications Committee.
4. Based on that framework, identify the applicable coordination or protection criterion, such as ECC T/R 25-08 (background: a CEPT/ECC recommendation on planning criteria and cross-border frequency coordination for the land mobile service).
5. Using the criterion, calculate the field strengths caused by the notified station with a deterministic method, using the ITU-R P.1546 propagation model (background: a Recommendation of the ITU Radiocommunication Sector, ITU-R, for point-to-area field-strength prediction for terrestrial services).
6. Produce expert-reviewable findings that show the source notice, the calculated field strengths, the model parameters, the assumptions and the source citations.

In addition, the brief asks teams to surface a small number of trends or anomalies in neighbouring administrations' notices, such as new activity by band, geography, station class or bandwidth.

## Section 03: guiding question

The brief's one-sentence question: "How might we build an auditable AI-assisted workflow that automatically monitors ITU BR IFIC information, identifies cases relevant to Finland, supports technical (frequency and radio frequency power level) analysis, and prepares expert-reviewable draft correspondence?"

The supporting paragraph adds four points.

- Power flux densities of geostationary-satellite orbit (GSO) and non-GSO satellites are of special interest for recognising possibly interfering usage.
- Understanding trends and the planned usage of new satellite systems matters too, because they may interfere with Finnish satellites already in use.
- Identifying these issues from the huge mass of IFIC API/A, CR/C and AP30 (AP30A and AP30B) information is essential, and that is where an AI solution might help.
- The comparison must take into account the available information on Finnish radio frequency usage: Regulation M4 and the additional frequency tables of special interest provided on the challenge platform. Additional data may be used, for example the harmonised use of radio frequencies in Europe or other public sources, to raise further notes and concerns on the IFIC information.

## Section 04: recommended AI approaches

The section is marked optional in the template. The brief lists possible approaches:

- document and structured-data ingestion directly from the public source;
- information extraction;
- retrieval-augmented generation (RAG);
- rule-based or deterministic calculation components;
- agentic workflows;
- anomaly detection;
- ranking and prioritisation;
- auditable citation or provenance mechanisms.

Teams are not required to use any specific AI architecture. The brief states that technical correctness, traceability and expert reviewability are more important than the choice of model.

## Section 05: datasets and resources

The brief notes that Since AI challenges can be built with synthetic, anonymised or public data, and that no personal data is required. Datasets marked with `**` in the brief are mandatory; all other data may be used, whether listed in the brief or taken from other sources.

| Resource | Status | What the brief says | Docs page |
|---|---|---|---|
| ITU Space IFIC | Mandatory | BR IFIC (Space services) page and downloadable Space IFIC databases | [itu-space-brific](../links/itu-space-brific/README.md), [itu-space-ific-databases](../links/itu-space-ific-databases/README.md) |
| ITU Terrestrial IFIC | Mandatory | BR IFIC (Terrestrial services) page and downloadable extract | [itu-terrestrial-brific](../links/itu-terrestrial-brific/README.md) |
| Regulation 4, "M4" | Mandatory | Finnish Radio Frequency Regulation, including the table of frequencies in Finland; the table can also be downloaded from the Traficom open data API | [finlex-regulation-m4](../links/finlex-regulation-m4/README.md), [traficom-opendata-swagger](../links/traficom-opendata-swagger/README.md), [traficom-frequency-table-api](../links/traficom-frequency-table-api/README.md) |
| Additional XLS dataset | Mandatory | Synthetic table of frequencies of special interest, available on the SinceAI platform only | none (not in this repository) |
| ITU tools | Optional | Software that can be used to handle and analyse IFIC datasets | [itu-space-software](../links/itu-space-software/README.md) |
| Regulation 15, "M15" | Optional | Collective Frequencies for Licence-exempt Radio Transmitters and Their Use; the brief notes it is "not necessarily as relevant as previous one" | [finlex-regulation-m15](../links/finlex-regulation-m15/README.md) |
| CEPT implementation status | Optional | Harmonised radio frequency use in Europe, including Finland, with technical harmonisation parameters | [cept-docdb-implementation](../links/cept-docdb-implementation/README.md) |
| ITU Radio Regulations | Optional | The international agreement on radio frequency usage, with limits for cross-border power levels and for satellites using frequencies above another country | [itu-radio-regulations](../links/itu-radio-regulations/README.md) |

### URLs as printed in the brief

All URLs answered HTTP 200 on 6 November 2026 (see the commands below).

| Resource | URL |
|---|---|
| ITU Space IFIC, page | https://www.itu.int/en/ITU-R/space/brific/Pages/default.aspx |
| ITU Space IFIC, downloadable databases | https://www.itu.int/sns/wic/demowic.html |
| ITU Terrestrial IFIC, page and "downloadable extract" | https://www.itu.int/en/ITU-R/terrestrial/brific/Pages/default.aspx |
| Regulation 4 (M4), Finlex | https://www.finlex.fi/fi/viranomaiset/maarayskokoelmat/traficom-viestinta/2026/3 |
| Frequency table API, Swagger UI | https://opendata.traficom.fi/swagger/ui/index#/Taajuusjakotaulukko |
| Frequency table API, endpoint | https://opendata.traficom.fi/api/v13/Taajuusjakotaulukko |
| ITU tools | https://www.itu.int/en/ITU-R/software/Pages/space-network-software.aspx |
| Regulation 15 (M15), Finlex | https://www.finlex.fi/fi/viranomaiset/maarayskokoelmat/traficom-viestinta/2025/51209 |
| CEPT implementation status | https://docdb.cept.org/implementation/overview |
| ITU Radio Regulations | https://www.itu.int/pub/r-reg-rr |

### Requirements attached to the mandatory datasets

- Space IFIC: all existing and forthcoming IFICs shall be able to be evaluated. Space IFIC no. 3074 needs to be analysed and possible concerns raised from it; 3074 is used to evaluate accuracy, and the results from it shall be submitted separately.
- Terrestrial IFIC: the same two requirements, with Terrestrial IFIC no. 3076 as the accuracy issue. The brief prints the same URL for the terrestrial page and for the downloadable extract.
- Regulation 4 (M4): the radio frequency table can be downloaded from the Traficom open data API; the Swagger UI and the endpoint are both printed. Taajuusjakotaulukko (frequency allocation table) is the API resource name.
- Additional XLS dataset: a synthetic table of frequencies of special interest with station number, frequency range (bandwidth and centre frequency), terrestrial coordinates and technical information (antenna height, antenna direction, antenna directivity, etc.). It is published on the SinceAI platform and is not in this repository.

## Section 06: evaluation criteria

| Criterion | Weight | Sub-points |
|---|---|---|
| A. Technical analysis and reproducibility | 25 % | Technically credible calculations and reasoning; deterministic and reproducible components where appropriate; assumptions and model parameters are visible |
| B. Extensibility and terrestrial side quest | 25 % | Demonstrates reuse of the core architecture; shows a credible extension from space services to terrestrial land-mobile notices |
| C. Workflow usefulness, innovation and output quality | 20 % | Prioritisation of findings is useful to an expert; outputs are understandable, reviewable and well documentable; innovation adds useful new ideas while remaining realistically implementable |
| D. Case recognition accuracy and relevance | 15 % | Correctly identifies cases relevant to Finland and Finnish terrestrial use; minimises material false positives and false negatives |
| E. Auditability and evidence quality | 15 % | Clear source provenance; citations and references to source notices, regulations or standards; an expert can understand why a conclusion was reached |
| Total | 100 % | |

## Section 07: submission format

The brief expects six deliverables:

1. A demo of the solution, preferably with some working functionality.
2. The ability to process IFIC files and generate relevant output, using the Finnish usage information.
3. Processed Space IFIC 3074 and Terrestrial IFIC 3076 for accuracy evaluation, provided as separate file(s).
4. Information on the input and output leading to the solution.
5. The code repository of the solution.
6. Other clarifying documentation; suggested, because it helps to evaluate the solution.

## Section 08: point of contact

Discord is the preferred contact method. The brief prints phone numbers for the two specialists; they are not reproduced here.

| Role | Name | Email | Discord |
|---|---|---|---|
| Q&A stand | Traficom SinceAI 2026 | Traficom.sinceai.2026@gmail.com | traficomsinceai2026 |
| Specialist on the challenge | Pekka Pussinen | pekka.pussinen@traficom.fi | pekkatraficom_83563 |
| Specialist on the challenge | Otto Julkunen | otto.julkunen@traficom.fi | ottoj0436_45333 |

The brief gives the times as "Sat"; the hackathon's Saturday is 7 November 2026.

| Who | When | Note |
|---|---|---|
| Q&A stand | Sat 9.00-12.00 and 14.30-18.00 | or as requested and agreed |
| Senior specialist, Space IFIC | Sat 10-11 and 17-18 | only if the named specialists cannot answer |
| Senior specialist, Terrestrial IFIC | Sat 11-12 and 16-17 | only if the named specialists cannot answer |

## What the repository README covers and what only the brief has

The [repository README](../../README.md) has a general description of the challenge and a "Datasets and APIs Provided" section that lists the three mandatory sources with URLs: ITU Space IFIC (with the 3074 requirement), ITU Terrestrial IFIC (with the 3076 requirement) and Regulation 4 "M4" (Finlex page, Swagger UI and API endpoint). Only the brief has:

- the mandatory XLS dataset on the SinceAI platform and the four optional resources (ITU tools, M15, CEPT docdb, Radio Regulations);
- the problem statement with the nine-step workflow;
- the terrestrial land-mobile side quest;
- the guiding question;
- the recommended AI approaches;
- the evaluation criteria and their weights;
- the submission format;
- the points of contact and the Q&A hours.

## Deliverables checklist

Derived from sections 05-07 only.

- [ ] ITU Space IFIC used; any existing or forthcoming issue can be evaluated.
- [ ] ITU Terrestrial IFIC used; any existing or forthcoming issue can be evaluated.
- [ ] Regulation M4 (Finnish table of frequencies, via Finlex or the Traficom API) used in the comparisons.
- [ ] Additional XLS table of frequencies of special interest (SinceAI platform) used in the comparisons.
- [ ] Space IFIC 3074 processed, concerns raised, results in a separate file.
- [ ] Terrestrial IFIC 3076 processed, concerns raised, results in a separate file.
- [ ] Demo, preferably with working functionality.
- [ ] The solution processes IFIC files and produces relevant output using the Finnish usage information.
- [ ] Documentation of the input and output leading to the solution.
- [ ] Code repository.
- [ ] Other clarifying documentation.

## Key facts for the team

| Fact | Value | Where it comes from |
|---|---|---|
| Hackathon | Since AI Hackathon 2026, 6-8 November 2026, Turku | brief header |
| Accuracy issue, space | Space IFIC no. 3074, published 23.06.2026 | brief; ITU schedule page |
| Space IFIC 3074 database | https://www.itu.int/sns/ific10/ific3074.zip, 60,837,631 bytes (about 58.0 MiB); contains ific3074.mdb, 286,654,464 bytes (about 273.4 MiB) | curl HEAD, 6 November 2026; zip listing |
| Space database format | Microsoft Access .mdb, Space Network Systems (SNS) database version 10 since 7 January 2025; 95 catalogue entries including system tables | ITU download page; table catalogue |
| Accuracy issue, terrestrial | Terrestrial IFIC no. 3076, published 21.07.2026 | brief; ITU terrestrial page |
| Terrestrial IFIC 3076 extract | https://www.itu.int/en/ITU-R/terrestrial/brific/BRIFIC/MDB/brific3076.zip, 2,406,450 bytes (about 2.3 MiB); contains brific3076.mdb, 25,145,344 bytes (about 24.0 MiB), 143 catalogue entries | curl HEAD; zip listing; table catalogue |
| Article 11 notices in 3076 | Part I 2415, Part II 1051, Part III 44, total 3510 | ITU information note ReadMe_3076.pdf |
| Previous terrestrial issue | No. 3075, published 07.07.2026; brific3075.zip 3,427,636 bytes (about 3.3 MiB) | ITU terrestrial page; curl HEAD |
| M4 in force | Radiotaajuusmääräys (Radio Frequency Regulation) 4 AG/2026M, issued 26.3.2026, in force 31.3.2026, repeals 4 AF/2025M | Finlex page |
| Frequency table API | 5,917 rows; full JSON 4,359,860 bytes (about 4.2 MiB) | API response captured 6 November 2026 |
| M15 as linked | Regulation 15 AV/2025M, issued 27.3.2025; Finlex also lists a newer 15 AW/2026M issued 26.3.2026 | Finlex pages |
| Q&A stand | Saturday 7 November 2026, 9.00-12.00 and 14.30-18.00 | brief |

## How to use the brief

1. Read the PDF once in full; it is five pages.
2. Use the dataset table above to open the docs page for each source; the link pages hold the download URLs, formats and access notes.
3. Keep the deliverables checklist and the criteria table next to the project plan in the [PM pack](../pm-pack/README.md).
4. Re-check the printed URLs before submission with the commands below.

The commands below were run on 6 November 2026 from the repository root.

```bash
# Size of the brief
ls -l Since_AI_Traficom_Challenge_Brief_FINAL_04112026.pdf

# Every URL printed in the brief (all returned 200 on 6 November 2026)
for u in \
  "https://www.itu.int/en/ITU-R/space/brific/Pages/default.aspx" \
  "https://www.itu.int/sns/wic/demowic.html" \
  "https://www.itu.int/en/ITU-R/terrestrial/brific/Pages/default.aspx" \
  "https://www.finlex.fi/fi/viranomaiset/maarayskokoelmat/traficom-viestinta/2026/3" \
  "https://opendata.traficom.fi/swagger/ui/index#/Taajuusjakotaulukko" \
  "https://opendata.traficom.fi/api/v13/Taajuusjakotaulukko" \
  "https://www.itu.int/en/ITU-R/software/Pages/space-network-software.aspx" \
  "https://www.finlex.fi/fi/viranomaiset/maarayskokoelmat/traficom-viestinta/2025/51209" \
  "https://docdb.cept.org/implementation/overview" \
  "https://www.itu.int/pub/r-reg-rr"; do
  curl -sS -o /dev/null -L --max-time 60 -A "Mozilla/5.0" -w "%{http_code} %{url_effective}\n" "$u"
done

# Size and date of the two accuracy-evaluation database files, without downloading them
curl -sSI -L --max-time 60 -A "Mozilla/5.0" "https://www.itu.int/sns/ific10/ific3074.zip" | grep -iE "^(HTTP|content-length|last-modified)"
curl -sSI -L --max-time 60 -A "Mozilla/5.0" "https://www.itu.int/en/ITU-R/terrestrial/brific/BRIFIC/MDB/brific3076.zip" | grep -iE "^(HTTP|content-length|last-modified)"
```

Sample output of the last two commands:

```text
HTTP/1.1 200 OK
Last-Modified: Tue, 23 Jun 2026 06:25:33 GMT
Content-Length: 60837631
HTTP/1.1 200 OK
Content-Length: 2406450
Last-Modified: Tue, 21 Jul 2026 06:18:20 GMT
```

`pdftotext` and `pdfinfo` are not installed on the authoring machine. The page count was confirmed by counting page objects in the file:

```bash
python3 -I -c 'import re,sys; d=open(sys.argv[1],"rb").read(); print(len(re.findall(rb"/Type\s*/Page[^s]", d)))' Since_AI_Traficom_Challenge_Brief_FINAL_04112026.pdf
```

## Related pages

- [Docs index](../README.md)
- [Repository README](../../README.md)
- [PM pack](../pm-pack/README.md): requirements, risk register and roadmap for the project
- [Design theme](../design-theme/README.md): the visual guide, including its serious-context rule for findings, evidence and exported memos
- Link pages for the brief's sources: [ITU Space BR IFIC](../links/itu-space-brific/README.md), [Space IFIC databases](../links/itu-space-ific-databases/README.md), [ITU Terrestrial BR IFIC](../links/itu-terrestrial-brific/README.md), [Regulation M4 on Finlex](../links/finlex-regulation-m4/README.md), [Traficom open data Swagger](../links/traficom-opendata-swagger/README.md), [Traficom frequency table API](../links/traficom-frequency-table-api/README.md), [ITU space software](../links/itu-space-software/README.md), [Regulation M15 on Finlex](../links/finlex-regulation-m15/README.md), [CEPT docdb implementation](../links/cept-docdb-implementation/README.md), [ITU Radio Regulations](../links/itu-radio-regulations/README.md)

## Caveats

- Publication cadence: the brief says "bi-monthly", but the ITU's BR IFIC (Space services) pages say the circular is published once every two weeks, and the terrestrial publication table shows the same fortnightly rhythm. The 2026 schedule lists 3074 on 23.06.2026, 3075 on 07.07.2026, 3076 on 21.07.2026 and 3077 on 04.08.2026; the space and terrestrial series share the numbering.
- Terrestrial extract URL: the brief prints the page URL twice. The actual database extracts are the zip files linked from the "MDB Extract" column of that page; for issue 3076 the file is https://www.itu.int/en/ITU-R/terrestrial/brific/BRIFIC/MDB/brific3076.zip, and the other issues follow the same pattern with their own number. The folder itself is not browsable without an ITU login (it answered 401 on 6 November 2026).
- Finlex pages are client-rendered: `curl` returns only an application shell. Open them in a browser, or use the direct PDF URLs recorded on the [M4](../links/finlex-regulation-m4/README.md) and [M15](../links/finlex-regulation-m15/README.md) link pages.
- M15 version: the brief links the 2025 regulation (15 AV/2025M). Finlex lists a newer Regulation 15 AW/2026M issued 26.3.2026 at https://www.finlex.fi/fi/viranomaiset/maarayskokoelmat/traficom-viestinta/2026/4. The brief's link is the one printed; which version to use is a question for the Q&A stand.
- ITU space software: the BR Space Application software (SpaceCom, GIBC and the other packages) supports only Windows 10 and 11; the offline installer is 400 MB. The ITU page describes SpaceCom as a tool for managing comments on the special sections CR/C, API/A, AP30-30A and AP30B, and GIBC as a tool for calculations that determine coordination requirements.
- Access: the BR IFIC online application and the ISO distribution need an ITU TIES account (Telecommunication Information Exchange Service; background) of a Member State administration or a paid subscription. The Space IFIC database downloads on demowic.html are described by the ITU as a free service "on a trial basis until further notice", and database files from previous years are no longer supported on that page.
- The XLS dataset of frequencies of special interest exists only on the SinceAI platform; nothing in this repository stands in for it.
- The two specialists' phone numbers are in the PDF only.
