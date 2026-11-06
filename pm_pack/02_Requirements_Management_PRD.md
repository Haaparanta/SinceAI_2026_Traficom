# 02 — Requirements and PRD: Filing Radar (Wedge 1)

One screen that turns an ITU BR IFIC issue into a ranked, cited, expert-reviewable list of concerns for Finland, on space data first and terrestrial land-mobile data second.

> [!NOTE]
> **Grounding.** Built from the challenge brief (sections 02 to 07), `README.md` and the live ITU, Finlex and Traficom sources checked on Fri 6 Nov 2026. Tags: `[SOURCE DATA]`, `[HYPOTHESIS]`, `[GAP - ASK PARTNER: Qn]` where Qn points to `01_Partner_Briefing_Questions.md`.
> Owners are role placeholders (PM, BE, AI, FE). Hour estimates assume four people and about 30 productive hours each between Fri 20:00 and Sun 09:15. Numbers in the before/after workflow are `[HYPOTHESIS]` until Q6 is answered. Requirement IDs M1 to M8, S1 to S6 and C1 to C5 are MoSCoW items; the Finnish regulation is always written "Regulation M4".

---

## 1. Persona and the Tuesday-morning workflow

**Persona:** "Aino", spectrum specialist, Traficom Spectrum and Space department `[SOURCE DATA: partner; name is a placeholder]`.

BR IFICs are published every second Tuesday `[SOURCE DATA: ITU schedule; 3084 lands 10 Nov 2026]`. On that morning Aino must find the notices that may affect Finnish use, assess technical concerns, and prepare correspondence to the other administration, either to solve the situation before it happens or to preserve Finland's right to claim protection `[SOURCE DATA: brief 02]`.

| Step | Before (manual) `[HYPOTHESIS]` | After (Filing Radar) |
|---|---|---|
| Notice the new issue | Check itu.int, download the zip, open in Windows tools | Watcher shows "3084 available", one click to ingest `[COULD]` |
| Find notices relevant to Finland | Query the database by band, read special sections one by one, about a day per issue | Every notice screened against the M4 table and the special-interest stations in minutes; ranked list with reasons |
| Assess technical concern | Manual pfd check with ITU tools for a handful of networks | Worst-case pfd per matched group with inputs, formula, limit and margin on screen, labelled indicative |
| Connect the evidence | Notes in a document, references typed by hand | Every finding carries SRS table and row references, Regulation M4 table row IDs and the RR provision |
| Draft the letter | Written from scratch | Draft addressed to the notifying administration, grounded in the evidence, edited by Aino |
| Decide | Aino | **Still Aino**: approve, dismiss or investigate, with an audit log |
| Terrestrial issue | Separate process | Same screen, same engine, P.1546 field strength instead of pfd |

**Proof metrics on screen:** (1) notices screened versus flagged for the selected issue, (2) provenance coverage: share of findings with a complete evidence chain, target 100 %. Once Q3 and Q16 are answered, add (3) precision and recall on the partner's reference answers for 3074 and 3076.

---

## 2. The one-screen product

```
+----------------------------------------------------------------------------------+
| INPUT  [Issue: Space 3074 v] [Terrestrial 3076]   [Sample 1] [Sample 2] [Sample 3] |
|        [Demo mode: on]                                      Screened 0 / Flagged 0 |
+----------------------------------+-----------------------------------------------+
| CENTRAL VIEW                     | ACTIONABLE OUTPUT                             |
| Tabs: Spectrum | Map | Calculation| Finding card for the selected notice           |
|                                  |   Concern: High . Band 10.95-11.2 GHz          |
| Spectrum: notice groups as bars  |   Reason (2 lines, cites evidence IDs)         |
|   over Finnish sub-bands from    |   Evidence: notice row, grp rows, Traficom rows|
|   the Traficom table             |             RR 21.16 limit row                 |
| Map: Finland outline, GSO        |   [Draft correspondence] [Export row]          |
|   elevation contours or station  |   [Approve] [Dismiss] [Investigate]            |
|   position and border distance   |                                               |
| Calculation: inputs -> formula   | Ranked list of all flagged notices (sortable)  |
|   -> result -> limit -> margin   |                                               |
+----------------------------------+-----------------------------------------------+
| PROOF METRICS  Screened 412 . Flagged 17 . Provenance coverage 100 %              |
+----------------------------------------------------------------------------------+
```

- **One input:** the issue selector plus three preloaded samples (cached, offline). Sample patterns `[HYPOTHESIS until 3074 is parsed tonight]`: (1) a GSO network whose downlink overlaps a Finnish fixed or FSS sub-band at low elevation, expected High; (2) a non-GSO API/A network overlapping a Finnish band but with a pfd mask, expected Review; (3) a terrestrial 3076 land-mobile notice from a neighbour within 100 km of the border, expected Medium with a field-strength trace.
- **One central view:** spectrum overlap strip, map, calculation trace.
- **One actionable output:** the finding card with evidence, decision buttons, letter draft and results-row export.
- **Two proof metrics:** screened versus flagged, provenance coverage.

---

## 3. MoSCoW requirements

### MUST, done by Gate 2 (Sat 09:00)

| ID | Requirement | Acceptance test | Owner | Est. h |
|---|---|---|---|---|
| M1 | **Ingest Space IFIC 3074.** Download the ITU zip, convert the `.mdb` databases to DuckDB or SQLite, keep table and row identifiers `[SOURCE DATA: zip 60.8 MB, Version 10 databases]` `[HYPOTHESIS: mdbtools can read them]` | `make data` ends with `data/derived/ific3074.duckdb`; row counts per table logged; `notice`, `grp`, `assgn`, `emiss`, `s_beam`, `srv_area`, `geo`, `orbit` present or an equivalent named mapping documented `[SOURCE DATA: Space Preface Section III; see 07_Solution_Catalogue.md section 2]` | BE | 5 |
| M2 | **Finnish reference data.** Cache the Traficom table (5 917 rows) as Parquet; load the special-interest XLS once available `[SOURCE DATA: API fields; XLS columns from brief 05]` `[GAP: Q4]` | `GET /reference/subbands?hz=11000000000` returns the matching rows with `Services_in_Finland` and `Comment`; XLS loader validates station number, centre frequency, bandwidth, coordinates, antenna height, direction, directivity | BE | 2 |
| M3 | **Frequency relevance.** For every group in the issue, compute overlap in MHz with Finnish sub-bands and with special-interest stations, direction-aware (space-to-Earth against terrestrial use; Earth-to-space against Finnish space use) `[HYPOTHESIS rule]` `[GAP: Q1]` | Full 3074 screened in under 5 minutes on a laptop; Sample 3 pattern yields no space overlap; every overlap row references the SRS group row and the Traficom row ID | BE | 5 |
| M4 | **Geographic relevance.** GSO: elevation angle from four Finnish reference points to the nominal longitude; visible if above 0 degrees, low-elevation flag below 10 degrees. Non-GSO: relevant unless the service area excludes Finland. Service area codes containing FIN or a region including Finland count `[HYPOTHESIS]` `[GAP: Q1]` | Elevation table for Samples 1 and 2 matches a hand calculation within 0.5 degrees | AI | 3 |
| M5 | **Indicative pfd, GSO worst case.** pfd = power density + max beam gain + 10 log10(reference bandwidth) minus spreading loss at the slant range of the lowest Finnish elevation; compare with a reviewed limits table (RR Article 21, Table 21-4 rows for the bands we hit) `[SOURCE DATA: brief asks for pfd; RR listed as a source]` `[HYPOTHESIS formula and table values]` `[GAP: Q2]` | Calculation trace shows every input with its source row, the formula, the result, the limit row and the margin; a unit test reproduces a hand-worked case; result labelled "indicative, worst case" | AI | 5 |
| M6 | **One-screen UI** as in section 2, Girlypop theme v2 | All three samples run end to end in the browser; selecting a notice updates spectrum, map, calculation and finding card | FE | 8 |
| M7 | **Evidence rule.** A finding without at least one evidence item cannot be created or rendered | Pydantic validator and a UI test; evidence item has `source` (file or URL), `locator` (table, row, field or section), `excerpt` | AI | 2 |
| M8 | **Results file for 3074.** One row per screened notice with concern level, reason, matched Finnish service, overlap, pfd estimate, limit, margin, evidence refs; CSV and JSON `[SOURCE DATA: brief 07 "separate file(s)"]` `[GAP: Q3 for the schema]` | `python -m radar.export --issue 3074` writes `results/space_3074.csv` and `.json`; both validate against the `ResultRow` contract | BE | 2 |

### SHOULD, done by Gate 3 (Sat 16:00)

| ID | Requirement | Acceptance test | Owner | Est. h |
|---|---|---|---|---|
| S1 | **Terrestrial side quest.** Ingest 3075 and 3076 MDB extracts, diff notices into new, modified, withdrawn; filter neighbour land-mobile notices within a border distance; compute P.1546 field strength at the nearest Finnish border point; compare with the T/R 25-08 threshold; emit the same `Finding` and a `results/terrestrial_3076.csv` `[SOURCE DATA: side quest bullets]` `[HYPOTHESIS: constants]` `[GAP: Q11, Q12]` | Diff counts shown per administration; Sample 3 shows a field-strength trace with time percentage, heights, distance, path type and the threshold row; results file written | BE, AI | 8 |
| S2 | **Correspondence draft.** Letter to the notifying administration per High finding, grounded only in evidence IDs, editable, exported as Markdown and DOCX `[SOURCE DATA: brief 02 last bullet]` `[GAP: Q10]` | Draft names the special section reference, the frequency range, the Finnish service and the RR provision; a test rejects drafts that cite unknown evidence IDs | AI | 3 |
| S3 | **Grounded explanation** per finding, two sentences, citing evidence IDs only | Validator rejects explanations that mention an ID not in the finding | AI | 3 |
| S4 | **Decisions and audit log.** Approve, dismiss, investigate; who, what, when; decisions flow into the results file | Decision persists across reload and appears in `results/*.csv` | FE, BE | 3 |
| S5 | **Proof metrics** on screen | Screened, flagged and provenance coverage update per issue | FE | 2 |
| S6 | **Trends and anomalies** for terrestrial: counts by band, administration, station class and bandwidth versus the previous issue `[SOURCE DATA: side quest last paragraph]` | Panel lists the top three changes with the rows behind each | BE | 2 |

### COULD, done by Gate 4 (Sun 02:00)

| ID | Requirement | Acceptance test | Owner | Est. h |
|---|---|---|---|---|
| C1 | Non-GSO pfd mask presence check; "not assessed" label when absent `[GAP: Q7]` | Sample 2 shows the mask status with its source row | AI | 3 |
| C2 | Forthcoming-issue watcher: poll the ITU schedule and zip URL for 3084 `[SOURCE DATA: schedule page]` | Banner appears when the URL returns 200 | BE | 2 |
| C3 | AP30, AP30A, AP30B database ingestion through the same adapter `[SOURCE DATA: separate ITU databases]` | Plan networks appear in the ranked list with their section | BE | 3 |
| C4 | M15 and CEPT harmonisation notes attached to matched bands `[SOURCE DATA: optional sources]` | Note shown with its source link | AI | 2 |
| C5 | Visual polish, dark mode, map contours | Shipping checklist in `design/girlypop-theme.md` passes | FE | 3 |

### WON'T (anti-scope)

- Integrating or automating the Windows-only ITU tools.
- Full epfd evaluation under RR Article 22 or beam-contour gain towards Finland from GIMS graphics; we use worst-case max gain and say so.
- Automatic sending of anything to the ITU or another administration.
- A general "chat with the Radio Regulations" bot, login, user management, settings pages.
- A second full terrestrial product; the side quest reuses the space pipeline `[SOURCE DATA: brief says it must not become a second challenge]`.
- Any number shown without its inputs and source.

---

## 4. Traceability

| Req ID | Source data reference | Judging criterion (weight) | 2-minute video moment |
|---|---|---|---|
| M1, M2 | Brief 02 "ingesting relevant national information" and "retrieving and ingesting ITU BR IFIC publications"; brief 05 mandatory datasets | A reproducibility (25 %), C usefulness (20 %) | 0:10 "3074 and the Finnish table load, 5 917 rows, every row keeps its ID" |
| M3, M4 | Brief 02 "summarising the relevant content and frequency ranges affecting Finland"; brief 03 "identifies cases relevant to Finland" | D accuracy (15 %) | 0:30 ranked list appears; counter shows screened versus flagged |
| M5 | Brief 02 "calculate pfd values"; brief 03 "power flux densities are in special interest" | A technical analysis (25 %) | 0:50 calculation tab: inputs, formula, limit, margin |
| M7, S3 | Brief 04 "auditable citation or provenance mechanisms"; criterion E | E auditability (15 %) | 1:05 click evidence, the SRS row and the Traficom table row open |
| S2 | Brief 02 "drafting relevant correspondence template for expert review" | C output quality (20 %) | 1:20 draft letter to the administration, expert edits one line |
| S4 | Brief 02 "expert-reviewable"; brief 04 "expert reviewability" | C, E | 1:30 Approve, audit log line |
| S1, S6 | Side quest bullets; criterion B | B extensibility (25 %) | 1:40 switch to Terrestrial 3076, diff counts, field-strength trace at the border |
| M8 | Brief 07 "Processed Space IFIC 3074 and Terrestrial IFIC 3076" | D, submission | 1:55 results files written, one line pitch |
