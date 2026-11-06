# PM pack — Filing Radar

Plan, questions and agent context for the Traficom challenge at Since AI 2026 (Turku, 6 to 8 Nov 2026). Locked wedge: Filing Radar.

> [!NOTE]
> Rebuilt on Fri 6 Nov 2026 from the full source data: the Traficom challenge brief (PDF in the repo root), `README.md`, the ITU space and terrestrial BR IFIC pages, the Finlex page for Regulation M4 and the Traficom frequency table API. Tags: `[SOURCE DATA]` stated by the partner or a linked page, `[HYPOTHESIS]` our assumption until verified, `[GAP - ASK PARTNER: Qn]` open question, `[PARTNER CONFIRMED]` answered at the stand.

| File | Use it when |
|---|---|
| [01_Partner_Briefing_Questions.md](01_Partner_Briefing_Questions.md) | Preparing for the Q&A stand and the specialist slots. Eighteen numbered questions, the top five, the slot plan, three pitches, the pivot red flags. |
| [01b_Partner_Briefing_Card.html](01b_Partner_Briefing_Card.html) | At the stand, on a phone. Pitches to read aloud, ten answer boxes, one button that copies the answers as a Claude update prompt. Answers stay on the phone. |
| [02_Requirements_Management_PRD.md](02_Requirements_Management_PRD.md) | Deciding what to build. Persona, the one screen, MoSCoW with acceptance tests and hours, traceability to the brief and the judging weights. |
| [03_Strategic_SWOT_and_Competitor_Matrix.md](03_Strategic_SWOT_and_Competitor_Matrix.md) | Writing the pitch and checking we are not building what everyone else builds. |
| [04_Risk_Register_and_Mitigation.md](04_Risk_Register_and_Mitigation.md) | At every gate. Scored risks with triggers, Cached Demo Mode, the data fallback ladder, the pre-mortem. |
| [05_Execution_Roadmap_and_Milestones.md](05_Execution_Roadmap_and_Milestones.md) | Running the weekend. Sprints, gates, the first 90 minutes, the Sunday run-sheet. |
| [06_AGENTS_Master_Context.md](06_AGENTS_Master_Context.md) | Before any coding agent touches the repo. Stack, folder tree, contracts, calculations, LLM rules, agent ownership. Symlinked as `AGENTS.md`, `CLAUDE.md` and `.cursorrules` in the repo root. |

## How the pack stays current

1. Ask the questions at the stand and type the answers into the phone card.
2. Tap "Copy Partner Answers as Claude Update Prompt" and paste it into Claude. It replaces the matching `[GAP]` and `[HYPOTHESIS]` tags, marks them `[PARTNER CONFIRMED]`, rescores the risks and lists architecture changes.
3. The PM updates the tags before engineers change behaviour (rule 7 in file 06).

## First actions tonight

```bash
scripts/fetch_data.sh                       # IFIC 3074, 3075, 3076, the ReadMe and SRS diagram PDFs, the Traficom table
python3 scripts/inspect_mdb.py data/raw/ific3074/*.mdb   # real table and column names; then fill backend/radar/schema_map.yaml
```

The special-interest XLS is on the Since AI platform and must be downloaded by a logged-in team member into `data/raw/special_interest.xlsx`.

## Assumptions baked in until corrected

- Team members appear as four role placeholders (PM, BE, AI, FE); no team details were given.
- The partner track is the primary goal; peer voting is handled in the Sunday run-sheet.
- The Sunday 10:00 deadline comes from the planning prompt, not from the brief (Q18).
- Every ITU table and field name is a hypothesis until `scripts/inspect_mdb.py` has run on the real database.
- The Claude client defaults to `claude-opus-5-5`; `LLM_MODEL` switches it and `LLM_DISABLED=1` runs the pipeline without any model.

## Open questions

| Q | Topic | Ask in slot | Status |
|---|---|---|---|
| Q1 | Relevance rule for Finland | Sat 9:00 stand | open |
| Q2 | pfd limits and method | Space 10-11 | open |
| Q3 | Correct result and file format for 3074 and 3076 | Sat 9:00 stand, Space 17-18 | open |
| Q4 | Special-interest XLS columns and availability | Sat 9:00 stand | open |
| Q5 | The one thing on screen that wins Sunday | Sat 9:00 stand | open |
| Q6 | Notices per IFIC and time per issue today | any | open |
| Q7 | Non-GSO depth, bands that hurt | Space 10-11 | open |
| Q8 | Finnish satellite systems to protect | Space 10-11 | open |
| Q9 | M15 and additional tables | any | open |
| Q10 | Correspondence template | Space 10-11 | open |
| Q11 | Terrestrial neighbours, distance, station classes | Terrestrial 11-12 | open |
| Q12 | T/R 25-08 threshold and P.1546 parameters | Terrestrial 11-12, 16-17 | open |
| Q13 | Reading the .mdb files, CSV extracts | Terrestrial 11-12 | open |
| Q14 | Cloud LLM and Discord sharing | Discord tonight | open |
| Q15 | Exact input files | Discord tonight | open |
| Q16 | How accuracy is scored | Space 17-18 | open |
| Q17 | pfd polish or terrestrial switch for Sunday | Sat 9:00 stand | open |
| Q18 | Deadline, submission channel, demo format, peer voting | Sat 9:00 stand | open |
