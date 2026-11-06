# 03 — Strategic SWOT and Competitor Matrix

How Filing Radar turns the public source data into an edge, and where the predictable readings of this brief fall short.

> [!NOTE]
> **Grounding.** Built from the challenge brief (sections 02 to 07), `README.md` and the live ITU, Finlex and Traficom checks of Fri 6 Nov 2026, plus the requirement IDs in `02_Requirements_Management_PRD.md` and the question IDs in `01_Partner_Briefing_Questions.md`. Competitor entries are predictions `[HYPOTHESIS]`, not observations; rescore after the Saturday stand. Tags: `[SOURCE DATA]`, `[HYPOTHESIS]`, `[GAP - ASK PARTNER: Qn]`.

---

## 1. SWOT

| | Helpful | Harmful |
|---|---|---|
| **Internal** | **Strengths**<br>• The partner wrote the workflow bullet by bullet (ingest, retrieve, identify, compute pfd, cross-compare, flag, draft a letter) `[SOURCE DATA: brief 02]`. We build that list, nothing else.<br>• Every bulk input is public and was verified tonight: Space IFIC 3074 zip (60.8 MB), terrestrial 3075 and 3076 extracts, the Traficom frequency table with 5 917 rows and Hz limits `[SOURCE DATA]`. We never wait for partner data; synthetic data is a last rung, not plan A.<br>• The evidence rule (M7) is a contract, not a feature: no finding exists without a source row. That maps straight onto criteria A and E, 40 % together `[SOURCE DATA: brief 06]`.<br>• One `Finding` model and one screen serve both space and terrestrial (S1), so the 25 % side quest reuses code instead of needing a second product `[SOURCE DATA: brief says it must not become a second challenge]`.<br>• Girlypop theme v2 and the one-screen layout already exist in `design/`; FE starts from a design system, not a blank page. | **Weaknesses**<br>• No spectrum engineer on the team as far as known `[HYPOTHESIS: team unknown]`; worst-case pfd (M5) and P.1546 (S1) are first implementations under time pressure.<br>• Reading Version 10 `.mdb` databases with open-source tools is unproven `[HYPOTHESIS]`; see R1 and R2 in `04_Risk_Register_and_Mitigation.md`.<br>• Four role placeholders. If the team is smaller, M5 and S1 compete for the same person.<br>• Mac and Linux stack only: the ITU tools are Windows 10 and 11 only `[SOURCE DATA: ITU software page]`, so we cannot cross-check our numbers against SpaceCom or GIBC ourselves. |
| **External** | **Opportunities**<br>• Most teams cannot run the ITU tools either (400 MB Windows installer). Teams that fall back to reading PDFs will have no numbers; a team that parses the databases and computes anything deterministic stands apart on criterion A `[HYPOTHESIS]`.<br>• The brief states that technical correctness, traceability and reviewability matter more than the model `[SOURCE DATA: brief 04]`: a small LLM footprint is a strength, not a gap.<br>• The processed 3074 and 3076 results are a scored deliverable `[SOURCE DATA: brief 07, criterion D]`. A team that hands in both files, even imperfect, beats a prettier demo with no file.<br>• Two validation rounds on Saturday: space specialists 10-11 and 17-18, terrestrial 11-12 and 16-17 `[SOURCE DATA: brief 08]`. Gate 2 and Gate 3 are timed to them.<br>• IFIC 3084 is scheduled for Tue 10 Nov `[SOURCE DATA: ITU schedule page]`: the "forthcoming IFICs" requirement becomes a dated demo of the watcher (C2). | **Threats**<br>• A misread relevance rule produces a confident, cited, wrong list `[GAP - ASK PARTNER: Q1]`. Gate 2 at the stand is the control.<br>• The limits table or the pfd method is contested by the specialists `[GAP - ASK PARTNER: Q2]`. Mitigation: label "indicative, worst case", show every parameter, change constants not pipeline.<br>• The special-interest XLS arrives late or in an unexpected shape `[GAP - ASK PARTNER: Q4]`, delaying station-level geography.<br>• A team with a real RF background does the pfd better. Our counter is coverage: both IFICs, both results files, letter draft, evidence on every row.<br>• Scoring mechanics for 3074 and 3076 are unknown `[GAP - ASK PARTNER: Q3, Q16]`; a recall-versus-precision bias could cost points either way. |

---

## 2. Competitor matrix: Filing Radar versus three lazy readings of the brief `[HYPOTHESIS]`

| Judging row | **Filing Radar (us)** | A: "Chat with the Radio Regulations" (RAG over RR and M4) | B: IFIC special-section PDF summariser | C: Satellite or map visualiser, no calculations |
|---|---|---|---|---|
| A. Technical analysis and reproducibility (25 %) | Yes: deterministic overlap, worst-case pfd and P.1546 field strength with inputs, formula, limit and margin on screen (M3, M5, S1) | No: answers vary with the prompt; nothing is computed | No: prose summaries, no numbers | Partly: geometry only, no power levels |
| B. Extensibility and terrestrial side quest (25 %) | Yes: same `Finding` model and screen on the 3075 to 3076 diff (S1, S6) | Partly: can index the terrestrial preface, cannot diff notices | Partly: can summarise 3076 PDFs, no field strength | No: no notice data at all |
| C. Workflow usefulness, innovation, output quality (20 %) | Yes: ranked list, letter draft, decisions and audit log (S2, S3, S4) | Partly: good for lookup, not for triage | Partly: a reading aid | Partly: good for a slide, not for a decision |
| D. Case recognition accuracy (15 %) | Yes: every notice in the issue is screened; results files for both issues (M3, M4, M8) | No: finds only what the user thinks to ask | Partly: one section at a time, by hand | No |
| E. Auditability and evidence quality (15 %) | Yes: evidence rule with table, row and field references (M7) | Partly: citations to rule text only | Partly: page references | No |
| Works offline for the demo | Yes: Cached Demo Mode (`04_Risk_Register_and_Mitigation.md`) | Partly: needs the model live | Partly | Yes |
| Produces the 3074 and 3076 results files | Yes (M8, S1) | No | No | No |

**Where they beat us:** C looks better in the first ten seconds. A is faster to build and answers any question. B needs no database parsing.

**What we borrow:** C's map as our second central tab (M6). A's citation habit on rule text, attached to matched bands (C4). B's section summary as the two-line reason in the finding card (S3).

---

## 3. Strategic verdict

**Unfair advantage, one sentence:**
We are the only team likely to screen every notice in Space IFIC 3074 and Terrestrial IFIC 3076 against the Finnish frequency table with a deterministic calculation and a row-level citation behind each flag, and to hand in the two results files the brief asks for.

**30-second elevator pitch** (words from the brief in quotation marks):
"Every second Tuesday the ITU publishes a circular with new satellite and terrestrial frequency notices. Traficom's specialists must 'identify items that may be relevant to Finland', check the power levels and 'prepare follow-up correspondence' before a planned transmission becomes a harmful interference case. Filing Radar does the first pass. It reads the circular's database, screens every notice against the Finnish frequency table and the stations of special interest, computes a worst-case power flux-density or a border field strength with 'assumptions and model parameters visible', and ranks what is worth a specialist's time. Each flag shows the source rows and the regulation it was checked against, and an 'expert-reviewable' draft letter to the other administration is ready. Same experts, same control, a cited shortlist instead of a circular."
