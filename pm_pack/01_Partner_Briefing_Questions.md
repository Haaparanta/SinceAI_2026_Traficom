# 01 — Partner Briefing Questions (Traficom, Since AI 2026)

Interrogation script for the Traficom stand and the specialist call slots. Locked wedge: **Filing Radar** (Wedge 1).

> [!NOTE]
> **Generated Fri 6 Nov 2026, 20:10 EET from the full source data:** the five-page challenge brief (PDF), `README.md`, the ITU space and terrestrial BR IFIC pages, the Finlex page for M4 and the Traficom frequency table API.
> - `[SOURCE DATA]` = stated in the brief, the README or a linked page. `[HYPOTHESIS]` = our domain assumption, unverified. `[GAP - ASK PARTNER]` = unknown; must be asked.
> - Team size and roles were not provided. Owners are role placeholders: **PM** (product and analysis), **BE** (data and pipeline), **AI** (calculations, LLM, drafting), **FE** (one-screen UI).
> - Stand hours `[SOURCE DATA]`: Q&A stand **Sat 9:00-12:00 and 14:30-18:00**. Space IFIC specialists **Sat 10-11 and 17-18**. Terrestrial IFIC specialists **Sat 11-12 and 16-17**. Discord is the preferred channel: `traficomsinceai2026`. Named contacts: Pekka Pussinen, Otto Julkunen.

## Final status, 7 Nov 2026: questions not asked

The team did not get to ask the partner, and it is now too late to do so. Every open question is closed with the assumption the code already uses; that assumption is the final choice for the submission, and the results say so (`[HYPOTHESIS]` and `indicative` labels stay on every affected number). A partner answer received later changes the constant or rule named here, and `make freeze` re-runs every check.

| Q | Final decision | Where it lives |
|---|---|---|
| Q1 relevance rule | A group is a candidate when its frequencies overlap a row of the Finnish allocation table **and** it can reach Finland: GSO elevation above 0 degrees from at least one of seven Finnish reference points, a non-GSO orbit that covers Finland's latitudes, or an earth station within 500 km. The Bureau naming Finland (`provn`) or an earth station inside Finland is always high. All special sections are screened. | `pipeline/relevance.py`, `pipeline/geography.py`, `pipeline/rank.py` |
| Q2 pfd limits and method | RR Article 21 Table 21-4 (signed off, `data/reference/review/`), worst-case GSO pfd (peak gain towards Finland, free space, lowest elevation), labelled indicative. Non-GSO: not evaluated, reported as "medium, non-GSO pfd not evaluated". A margin of 15 dB or more lowers a notice to low. | `calc/pfd.py`, `data/reference/pfd_limits.csv`, `rank.PFD_LOW_MARGIN_DB` |
| Q3 results format | One row per notice in CSV and JSON (`ResultRow`), every notice included with its reason, plus a per-group detail file for space. | `results/`, `results/README.md` |
| Q4 special-interest XLS | Fetched by the team from the Since AI platform. The matching rule (a station inside a group's frequency range is at least medium) is in `relevance.screen`; the XLS reader that feeds it is not built yet. | `pipeline/relevance.py` |
| Q5, Q17 demo focus | Both: the pfd calculation with every input on screen, and the same screen switching from Space 3074 to Terrestrial 3076. | `pm_pack/05` section 5 |
| Q6 scope | Every notice of the issue is screened (196 in 3074, 4 057 in 3076). | results files |
| Q7 non-GSO | No epfd (Article 22); non-GSO is flagged for review. | `calc/pfd.py` |
| Q8 Finnish satellite systems | Protected through the Finnish table: a downlink over Finnish space-service rows raises a coordination-review path (concern low). FIN filings in the SRS are not used as a second target. | `pipeline/relevance.py` |
| Q9 M15 | Not used; M4 (the Finnish allocation table) is the national reference. | |
| Q10 letter | Formal English draft to the notifying administration, citing the special section, the frequency range, the Finnish use and the indicative calculation; placeholder signature; never sent. | `prompts/letter.md`, `llm/drafts.py` |
| Q11 neighbours and distance | Any administration other than FIN; land-mobile notices up to 1 000 km (P.1546's limit); without a T/R 25-08 trigger, review within 100 km. | `pipeline/terrestrial.py` |
| Q12 P.1546 and T/R 25-08 | T/R 25-08 Annex 1 co-channel trigger at the border line (signed off), ITU-R P.1546-6 through the ITU reference code, 10 % time, 50 % locations, 10 m receiving height; within 6 dB below the trigger is medium. | `calc/p1546.py`, `data/reference/tr2508_thresholds.csv` |
| Q13 database access | `mdbtools` and DuckDB read every issue; no ITU software needed. | `scripts/mdb_to_duckdb.py` |
| Q14 cloud language model | Optional; the screen, results and demo run without it. | `llm/client.py` |
| Q15 input files | The full Space IFIC zip; the terrestrial MDB extract with the previous issue for the trend. | `scripts/fetch_data.sh` |
| Q16 scoring | Unknown; the ranking favours recall (every notice is listed with its reason, nothing is dropped silently). | `results/README.md` |
| Q18 logistics | Handled by the team on submission day. | |

---

## Top 5: the "3-minute stand" shortlist

Ask these first, in this order. Each answer changes code the same day.

| # | Question | Why we ask, and what changes in our code |
|---|---|---|
| Q1 | **What makes a notice "relevant to Finland" in your daily practice?** Frequency overlap with the Regulation M4 table only, overlap with the special-interest station table, service area or beam over Finland, GSO visibility from Finland, or all of these? Which Special Sections matter most: API/A, CR/C, AP30, AP30A, AP30B? | The relevance rule is the core of criterion D (15 %). Sets the filter order in `pipeline/relevance.py` and which SRS tables we read first. Today we assume: frequency overlap AND (service area includes Finland OR GSO elevation from Finland above 0 degrees) `[HYPOTHESIS]`. |
| Q2 | **Which pfd limits should a credible first pass compare against?** RR Article 21 Table 21-4 per band, the limits in the synthetic special-interest table, or both? For GSO, do you accept a worst-case pfd (max beam gain, lowest Finnish elevation)? For non-GSO, is "mask present / not assessed" acceptable at hackathon depth? | Criterion A (25 %). Decides the limits table we load into `calc/pfd.py` and how we label results. Today: worst-case GSO pfd labelled "indicative", non-GSO flagged for review `[HYPOTHESIS]`. |
| Q3 | **What does a correct result for Space IFIC 3074 and Terrestrial IFIC 3076 look like, and in what file format do you want it?** One row per notice with concern level and reason? CSV, Excel, JSON? Roughly how many true concerns exist in 3074? | Submission format `[SOURCE DATA: brief 07 says "separate file(s)"]` but the schema is open. Fixes `export/results.py` and lets us size precision and recall. |
| Q4 | **Can we get the synthetic special-interest XLS tonight, and what are its exact columns, units and coordinate system?** Does it contain pfd or field-strength limits per station? | The brief marks it mandatory `[SOURCE DATA: brief 05]` but it lives on the Since AI platform. Defines `adapters/special_interest.py` and whether geography is point-based. |
| Q5 | **On Sunday, what single thing on screen separates first place from second?** A ranked list with sources, a pfd number with visible maths, a draft letter, or the terrestrial reuse? | Becomes the first 30 seconds of the demo and the main number on the screen. Moves hours between M5, S1 and S2 in the PRD. |

---

## Unpacking ambiguities in the brief

| # | Brief wording `[SOURCE DATA]` | Question | What changes in our code |
|---|---|---|---|
| Q6 | "identify items that may be relevant to Finland" (02) | Do you screen every notice in an IFIC, or only bands with Finnish systems of special interest? Roughly how many notices per IFIC does a specialist open today, and how long does one IFIC take? | Baseline for the proof metric "specialist minutes per IFIC". We will count 3074 ourselves tonight `[HYPOTHESIS: hundreds of notices per issue]`. |
| Q7 | "GSO and non-GSO satellite power flux densities are in special interest" (03) | For non-GSO, is a pfd mask check enough, or do you expect epfd per RR Article 22? Which bands are the pain today: Ku, Ka, C, L? | Decides whether C1 (NGSO mask) is promoted to SHOULD and which bands our three samples come from. |
| Q8 | "new satellites systems which may interfere Finnish satellites already in use" (03) | Which Finnish satellite networks and earth stations should we protect: all filings notified by administration FIN in the SRS, or a shorter list? | Adds a second matching target next to the M4 table. `[HYPOTHESIS: filter SRS by adm = FIN]`. |
| Q9 | "cross-comparing the findings with information on national regulations ('M4', 'M15')" (02) | Is M15 (licence-exempt collective frequencies) needed for a winning result, or only M4 plus the special-interest table? Are there "additional frequency tables" beyond the XLS? | Keeps M15 in COULD or moves it to SHOULD. |
| Q10 | "identifying the relevant counterparty (administration) and drafting relevant correspondence template" (02) | What does a real letter look like today: language, structure, tone, what it asks for, who signs? Can you share one anonymised example? | Shapes the letter template in `prompts/correspondence.md`. `[HYPOTHESIS: formal English letter citing the special section reference and the RR provision]`. |
| Q11 | "filter foreign assignments that may be relevant to Finland using notice data" (side quest) | Which neighbours count: Sweden, Norway, Russia, Estonia, others? Distance from the border that matters? Which station classes count as land-mobile? | Sets the terrestrial filter constants. `[HYPOTHESIS: 100 km from the border, base and mobile station classes]`. |
| Q12 | "coordination or protection criterion such as ECC T/R 25-08" and "ITU-R P.1546" (side quest) | Which T/R 25-08 threshold and at what point (border line, inside Finland at a distance)? P.1546 parameters: time percentage, receiving height 10 m, land or sea path, how effective antenna height is derived? Do you use an official ITU-R reference implementation we should match? | Fixes `calc/p1546.py` parameters and the acceptance test. `[HYPOTHESIS: 10 % time, 10 m receiving height, worst case path]`. |

---

## Data and NDA reality check

What we verified tonight without the partner, and what only they can unlock.

| # | Question | Status |
|---|---|---|
| Q13 | **Is reading the IFIC `.mdb` databases with open-source tools acceptable, or do you expect ITU software?** Could you hand over CSV extracts of 3074 and 3076 if our parser fails? | `[SOURCE DATA]` ITU tools are Windows 10/11 only, 400 MB installer. The brief allows "direct database logic". We plan `mdbtools` plus DuckDB `[HYPOTHESIS]`. |
| Q14 | **Are cloud LLM APIs acceptable for every input we use?** All sources are public, but confirm. May we post interim results on Discord? | `[SOURCE DATA]` Since AI states no personal data is required; the brief lists only public sources. |
| Q15 | **Which exact files should we treat as the IFIC input?** The full Space IFIC zip (3074 is 60.8 MB, Version 10 databases) or only the API/A and CR/C parts? For terrestrial, the MDB extract (3076 is 2.4 MB) plus the previous issue 3075 (3.4 MB)? | `[SOURCE DATA]` Verified URLs and sizes on itu.int tonight. The IFIC zip is the only bulk source for 3074; the SpaceWISC batch downloads stop at IFIC 2847. |
| Q16 | **How are the 3074 and 3076 results scored?** By notice ID match? Is a near miss (right band, wrong reason) partial credit? | Decides whether we bias toward recall or precision in the ranking threshold. |

---

## The Sunday evaluator question

| # | Question | Why we ask |
|---|---|---|
| Q17 | *"Your criteria put 25 % on reproducible technical analysis and 25 % on the terrestrial extension. If we can only perfect one live moment for Sunday, should it be a pfd calculation with every parameter on screen, or the same engine switching from Space 3074 to Terrestrial 3076 in one click?"* | The answer sets the order of Saturday afternoon. Either way, both must exist; the question decides which one gets polish. |

## Logistics

| # | Question | What changes |
|---|---|---|
| Q18 | **Logistics.** The Sunday 10:00 deadline is in our plan, not in the brief. Confirm the submission deadline and channel, whether the Sunday demo is live or a video, where the 3074 and 3076 results files go, and how peer voting works at Since AI. | Fixes Gate 5 in `05_Execution_Roadmap_and_Milestones.md` and the Sunday run-sheet. `[HYPOTHESIS: deadline Sun 10:00]` |

---

## Three 2-sentence pitch scripts (read aloud, watch the reaction)

**Wedge 1, Filing Radar (locked):**
"You pick an IFIC issue, and Filing Radar screens every notice against the Finnish frequency table and your special-interest stations, then ranks the ones that touch Finland with a worst-case pfd and the limit it was checked against. Every flag shows the SRS rows and the regulation it came from, and the same engine runs the terrestrial 3076 notices with a P.1546 field strength at the border, so your expert reviews a short, cited list instead of a circular."

**Wedge 2, Finland Filter (fallback if the maths stalls):**
"We take each IFIC and apply a deterministic filter: frequency overlap with the Regulation M4 table, service area over Finland, neighbour notices near the border, and nothing else. The output is a reviewable shortlist with sources for every row, and the language model only writes the explanation and the letter draft, never the decision."

**Wedge 3, pfd Lab (if your specialists value the calculation above all):**
"We built transparent calculators for GSO pfd and P.1546 field strength where every parameter is visible and editable, validated against worked examples, and ranked by margin to the limit. The circular becomes a list of margins your expert can audit line by line."

---

## Opening line at the stand (20 seconds)

"We are building Filing Radar. It reads the IFIC database, screens every notice against the Finnish frequency table and your stations of special interest, and gives the specialist a ranked, cited shortlist with a worst-case pfd and a draft letter. We have 3074 and 3076 loaded. Can we check three things with you?" Then Q1, Q3 and Q5, in that order.

## Red flags that trigger the pivot at Gate 2

| If the partner says | It means | We do |
|---|---|---|
| "Relevance is mostly about the special-interest stations and their limits, not the allocation table" | Station geometry and station limits lead; band overlap is secondary | Promote the XLS loader and station geometry (M2, M4); take limits from the station rows `[GAP: Q2, Q4]` |
| "A pfd from the maximum gain means nothing to us" | Worst case is not credible to the expert | Keep the trace, rank by overlap and geography, move M5 to COULD, spend the hours on S1 and S2 |
| "The screening we do with the ITU tools; we need the summary and the letter" | Output quality beats screening | Pivot to Wedge 2 "Finland Filter" with S2 and S3 first; the data layer stays |
| "Terrestrial is where we lose the most time" | The side quest weight is real for them too | Start S1 right after the stand instead of at 11:30 |
| "Do not send this to cloud models" | Provider restriction | `LLM_DISABLED=1` for the stand demo; swap the client later (R9 in `04_Risk_Register_and_Mitigation.md`) |

---

## Top 10 for the phone card

These ten are the text inputs in `01b_Partner_Briefing_Card.html`, in this order: Q1, Q2, Q3, Q4, Q5, Q12, Q10, Q13, Q8, Q16. The others, Q6, Q7, Q9, Q11, Q14, Q15, Q17 and Q18, sit under "Also asked" with one notes box.

## When to ask what `[SOURCE DATA: brief 08]`

| Slot | Who | Ask |
|---|---|---|
| Sat 9:00 | Q&A stand opens | Q1, Q3, Q4, Q5, Q14, Q15, Q18. Show the Gate 2 prototype. |
| Sat 10-11 | Space IFIC specialists | Q2, Q7, Q8, Q10. Show the pfd trace on one 3074 notice. |
| Sat 11-12 | Terrestrial IFIC specialists | Q11, Q12, Q13. Show the 3075 to 3076 diff counts. |
| Sat 16-17 | Terrestrial specialists | Validate one field-strength result and the threshold. |
| Sat 17-18 | Space specialists | Validate the results file format for 3074 (Q3, Q16). |

> [!TIP]
> After each slot: type the answers into the card, tap **Copy Partner Answers as Claude Update Prompt**, paste into Claude. Every `[GAP - ASK PARTNER]` in this pack is keyed by its Q number.
