# Documentation

Reference pages for every document in this repository and for every external resource named in the README and in the challenge brief.

> [!NOTE]
> Written on 6 November 2026 from the files in this repository and from the live pages on that date. Each page summarises its source and links to it. If a page and its source differ, the source is authoritative.

## Documents in this repository

| Page | Source | What it covers |
|---|---|---|
| [Challenge brief](challenge-brief/README.md) | [Since_AI_Traficom_Challenge_Brief_FINAL_04112026.pdf](../Since_AI_Traficom_Challenge_Brief_FINAL_04112026.pdf) | The official Traficom brief: problem statement, end-to-end workflow, terrestrial side quest, datasets, evaluation criteria, submission format, contacts |
| [PM pack](pm-pack/README.md) | [pm_pack/](../pm_pack/) | The six planning documents and the briefing card, and what the official brief has answered since they were drafted |
| [Design theme](design-theme/README.md) | [design/](../design/) | Girlypop theme v2: tokens, typography, sigil backgrounds, component rules and the document rules these pages follow |

## Mandatory datasets

Listed in the README and marked mandatory in the brief.

| Page | Link | Why it matters |
|---|---|---|
| [ITU BR IFIC (Space services)](links/itu-space-brific/README.md) | https://www.itu.int/en/ITU-R/space/brific/Pages/default.aspx | What the space circular is, the 2026 schedule, access rules, database descriptions; Space IFIC 3074 is the graded issue |
| [ITU Space IFIC databases](links/itu-space-ific-databases/README.md) | https://www.itu.int/sns/wic/demowic.html | Free zipped Access databases for every Space IFIC, including ific3074.zip, and what is inside them |
| [ITU BR IFIC (Terrestrial services)](links/itu-terrestrial-brific/README.md) | https://www.itu.int/en/ITU-R/terrestrial/brific/Pages/default.aspx | Terrestrial issues with MDB extracts, ReadMe notes and special sections; Terrestrial IFIC 3076 is the graded issue |
| [Regulation 4 (M4)](links/finlex-regulation-m4/README.md) | https://www.finlex.fi/fi/viranomaiset/maarayskokoelmat/traficom-viestinta/2026/3 | The Finnish Radio Frequency Regulation 4 AG/2026M and its Frequency Allocation Table |
| [Traficom API: Swagger UI](links/traficom-opendata-swagger/README.md) | https://opendata.traficom.fi/swagger/ui/index#/Taajuusjakotaulukko | The open data API specification: operations, query parameters, field definitions, licence |
| [Traficom API: frequency table endpoint](links/traficom-frequency-table-api/README.md) | https://opendata.traficom.fi/api/v13/Taajuusjakotaulukko | The allocation table as JSON: record structure, statistics, tested queries and an overlap recipe |

## Additional resources

Named in the brief only.

| Page | Link | Why it matters |
|---|---|---|
| [ITU space software](links/itu-space-software/README.md) | https://www.itu.int/en/ITU-R/software/Pages/space-network-software.aspx | SpaceCom, GIBC and the other Radiocommunication Bureau tools, Windows only |
| [Regulation 15 (M15)](links/finlex-regulation-m15/README.md) | https://www.finlex.fi/fi/viranomaiset/maarayskokoelmat/traficom-viestinta/2025/51209 | Licence-exempt transmitters, including satellite terminals; a newer 2026 edition exists |
| [CEPT ECO docdb](links/cept-docdb-implementation/README.md) | https://docdb.cept.org/implementation/overview | Implementation status of ECC Decisions and Recommendations per country, with CSV downloads |
| [ITU Radio Regulations](links/itu-radio-regulations/README.md) | https://www.itu.int/pub/r-reg-rr | The treaty text behind the IFIC procedures, pfd limits and the plans |

## How the pages are built

Every page follows the document rules of the [design theme](design-theme/README.md): one title, a one-line subtitle, a Source table on link pages, GitHub alerts for callouts, tables for structured facts and fenced code blocks only for commands that were actually run. Link pages record the date they were checked.
