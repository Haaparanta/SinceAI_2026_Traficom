# 04 — Risk Register and Mitigation

Scored risks for the Filing Radar build, the Cached Demo Mode contract, the data fallback ladder and the Sunday pre-mortem.

> [!NOTE]
> **Grounding.** Built from the challenge brief, `README.md`, the live ITU, Finlex and Traficom checks of Fri 6 Nov 2026, and the IDs in `01_Partner_Briefing_Questions.md` (Q1 to Q18) and `02_Requirements_Management_PRD.md` (M1 to M8, S1 to S6, C1 to C5). Likelihood (L) and impact (I) are our estimates at 20:20 EET on Friday; rescore after the Saturday 09:00 stand and after each specialist slot. Owners are role placeholders (PM, BE, AI, FE). Score = L x I. Act on anything scoring 12 or more before Gate 1 (Fri 23:30, see `05_Execution_Roadmap_and_Milestones.md`).

---

## 1. Risk table

| ID | Risk | L | I | Score | Trigger | Owner | Hard fallback |
|---|---|---|---|---|---|---|---|
| R1 | **The 60.8 MB Space IFIC 3074 zip or its `.mdb` files do not parse with open-source tools** `[HYPOTHESIS: mdbtools reads Version 10 databases]` | 3 | 5 | **15** | `mdb-tables` fails, exports are empty or truncated, or no row counts by Fri 22:00 | BE | Try a second reader (a Java bridge such as Jackcess or UCanAccess) before 22:30. Then the data fallback ladder below: partner CSV extracts `[GAP - ASK PARTNER: Q13]`, reduced subset, synthetic last. |
| R2 | **Version 10 SRS table or field names differ from our assumptions** (`com_el`, `grp`, `freq`, `emiss`, `s_beam`, `geo`, `orbit`) `[HYPOTHESIS]` | 4 | 3 | **12** | Expected tables missing after conversion | BE | Read `SRSDiagramV9_1.pdf` and the ITU data-item legend; keep one named mapping in the SRS adapter (M1 acceptance test) so renames are a mapping change, never a pipeline change. |
| R3 | **Synthetic special-interest XLS unavailable or in an unexpected shape** `[SOURCE DATA: brief 05 says it is on the Since AI platform]` | 3 | 4 | **12** | Not downloaded by Sat 09:30, or columns differ from the brief's list | PM | Build the loader from the brief's column list (M2); run geography on the Finnish bounding box and the M4 table only until the file arrives; ask Q4 at the 09:00 stand. |
| R4 | **pfd formula or limits table wrong** `[HYPOTHESIS: formula and RR Article 21 values]` | 3 | 5 | **15** | Specialists dispute the number at Sat 10-11, or the unit test against a hand-worked case fails | AI | Overlap stays a fact; pfd stays "indicative, worst case" with every parameter and its source row on screen (M5). Limits load only from a reviewed CSV with the RR table reference per row. If disputed, change the constant, keep the trace `[GAP - ASK PARTNER: Q2]`. |
| R5 | **P.1546 implementation takes too long** | 4 | 4 | **16** | No field-strength number for Sample 3 by Sat 14:00 | AI | Check first for an official ITU-R Study Group 3 reference implementation to match `[HYPOTHESIS]`. If none fits in time: free-space loss plus a documented P.1546 land-path correction at the brief's time percentage for the three reference frequencies, interpolated, labelled as such. Last rung: rank by distance to the border, labelled "no propagation model" `[GAP - ASK PARTNER: Q12]`. |
| R6 | **We misread "relevant to Finland"** and build a confident wrong list | 3 | 5 | **15** | Lukewarm or confused reaction at the Sat 09:00 stand (Gate 2) | PM | The relevance rule is a configuration object in `pipeline/relevance.py` (M3, M4); change the rule, rerun the issue, re-export. If the product itself is wrong: pivot to Wedge 2 "Finland Filter" on the same data layer by Sat 11:30 `[GAP - ASK PARTNER: Q1]`. |
| R7 | **Results file format rejected** | 3 | 3 | 9 | Q3 answer differs from our `ResultRow` schema | BE | `export/results.py` writes from one contract (M8); renaming or adding a column is a mapping edit. Keep CSV and JSON side by side `[GAP - ASK PARTNER: Q3]`. |
| R8 | **Terrestrial side quest starved of time** (25 % of the score) | 4 | 5 | **20** | S1 not started by Sat 11:30, or no diff counts by Sat 15:30 | BE | Hard time box Sat 11:30 to 15:30 for S1 owned by BE with AI on P.1546. The diff and the border-distance filter ship even if the propagation model is reduced (R5). S6 trends panel is two hours and ships last. |
| R9 | **Cloud LLM or Discord sharing restrictions** | 2 | 3 | 6 | Partner objects at the stand | AI | All inputs are public `[SOURCE DATA: brief 05]`. The LLM is used only for explanations (S3) and the letter draft (S2) behind a provider-agnostic client; a local model can replace it. Keep interim results off Discord until Q14 is answered `[GAP - ASK PARTNER: Q14]`. |
| R10 | **Live demo or API failure** | 3 | 5 | **15** | Any request over 10 seconds or any error during the Saturday rehearsal | AI | Cached Demo Mode (section 2). The video and the Sunday demo run in demo mode. |
| R11 | **Specialists unavailable outside their slots** | 4 | 3 | **12** | A blocking question appears outside Sat 9-12 and 14:30-18 | PM | Batch questions into the slots per "When to ask what" in `01_Partner_Briefing_Questions.md`; post the rest on Discord `[SOURCE DATA: preferred channel]`; decide with a labelled assumption and record it in the finding trace. |
| R12 | **Fatigue, single point of failure** | 3 | 4 | **12** | Anyone awake more than 20 hours; a module only one person can run | PM | Sleep rotation in `05_Execution_Roadmap_and_Milestones.md`. Every module has a README and a second person who has run it before Gate 3. |
| R13 | **Video, deck or submission not finished** | 2 | 5 | 10 | No video script by Sat 23:30, no recording by Sun 07:15 | PM | Script written in Sprint 6; recorded in demo mode Sunday 06:30; FINAL at 09:15, never past 10:00 (deadline from the user's prompt, not the brief `[GAP - ASK PARTNER: Q18]`). |
| R14 | **Scoring bias unknown** (recall versus precision) | 3 | 3 | 9 | Q16 unanswered by Sat 18:00 | AI | Export concern levels High, Medium, Review, None for every screened notice so an evaluator can pick a threshold; document the default threshold in the results README `[GAP - ASK PARTNER: Q16]`. |

**Note, not a risk:** Space and Terrestrial IFIC 3084 are scheduled for Tue 10 Nov 2026 `[SOURCE DATA: ITU schedule page]`, after the hackathon. It is the dated example for the watcher (C2) and for the "forthcoming IFICs" line in the pitch.

---

## 2. Cached Demo Mode toggle

- **Switch:** environment variable `DEMO_MODE=1`, mirrored by a switch in the input bar of the one screen (M6). Either one is enough; the UI shows "Demo mode: on" whenever it is active.
- **Content:** `data/cache/sample_1.json`, `data/cache/sample_2.json`, `data/cache/sample_3.json`, each a precomputed `AnalysisResult` payload for the three sample patterns in `02_Requirements_Management_PRD.md` section 2 (GSO downlink overlap at low elevation, non-GSO API/A network with a pfd mask, terrestrial 3076 land-mobile notice near the border).
- **No network calls** in demo mode: no ITU fetch, no LLM call, no API call to Traficom. The explanation and the letter draft are read from the cached payload.
- **Regeneration:** `scripts/build_cache.py` runs the live pipeline for the three samples and writes the files. The output is committed.
- **Validation:** a test loads each cached file and validates it against the Pydantic `AnalysisResult` contract in `06_AGENTS_Master_Context.md`; the build fails if the contract and the cache drift.
- **Use:** the 2-minute video and the Sunday demo run in demo mode. The live mode is shown only if a specialist asks and the rehearsal passed.

---

## 3. Data fallback ladder (missing or dirty partner data)

Climb down one rung at a time; every rung is labelled in the UI and in the results files.

| Rung | Source | Label shown |
|---|---|---|
| 1 | Full IFIC zip converted from `.mdb` to DuckDB or SQLite (M1) | "Source: ITU BR IFIC 3074 database" |
| 2 | CSV extracts handed over by the partner `[GAP - ASK PARTNER: Q13]` | "Source: partner extract of IFIC 3074" |
| 3 | Reduced subset: API/A and CR/C special sections only, parsed from whatever table or PDF loads | "Partial coverage: API/A and CR/C only" |
| 4 | Synthetic generator shaped like the SRS tables, fixed random seed, three planted golden cases | "Synthetic data, not ITU data" |

---

## 4. Sunday 10:00 pre-mortem: top three ways teams lose on this brief

1. **They build a chatbot.** A RAG assistant over the Radio Regulations answers questions but screens nothing, computes nothing and produces no 3074 or 3076 results file. Criteria A, D and E all suffer at once.
2. **They skip or rush the terrestrial side quest.** It is 25 % of the score `[SOURCE DATA: brief 06]` and it is explicitly a reuse test. A space-only demo caps the team at three quarters of the available points.
3. **They show numbers without inputs and sources.** The brief rewards "assumptions and model parameters are visible" and "clear source provenance". A pfd value with no trace reads as a guess, and an expert cannot review it.
