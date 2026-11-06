# 05 — Execution Roadmap and Milestones (EET)

Four-hour sprints from Fri 19:30 to Sun 10:00, five binary gates, tonight's first 90 minutes and the Sunday run-sheet.

> [!NOTE]
> **Grounding.** Stand and specialist hours are from the challenge brief section 08 `[SOURCE DATA]`. The build window Fri 19:30 to Sun 10:00 and the Sunday deadline come from the user's prompt, not from the brief `[GAP - ASK PARTNER: Q18]`. Requirement IDs are from `02_Requirements_Management_PRD.md`, question IDs from `01_Partner_Briefing_Questions.md`. Owners are role placeholders (PM, BE, AI, FE); the plan assumes four people. Written Fri 6 Nov 2026 at 20:20, so Sprint 1 is already running.

---

## 1. Fixed times

| When | What | Source |
|---|---|---|
| Fri 19:30 | Build starts | user prompt |
| Sat 09:00-12:00, 14:30-18:00 | Traficom Q&A stand (or as requested and agreed) | brief 08 |
| Sat 10:00-11:00, 17:00-18:00 | Space IFIC specialists | brief 08 |
| Sat 11:00-12:00, 16:00-17:00 | Terrestrial IFIC specialists | brief 08 |
| Sun 09:15 | Internal FINAL | this plan |
| Sun 10:00 | Hard deadline | user prompt `[GAP - ASK PARTNER: Q18]` |
| Tue 10 Nov | IFIC 3084 published; after the hackathon, used only as the watcher example (C2) | ITU schedule |

Discord `traficomsinceai2026` is the preferred channel for anything outside the slots `[SOURCE DATA: brief 08]`.

---

## 2. Sprints

| Sprint | Time | Focus | Key outputs (requirement IDs) |
|---|---|---|---|
| Sprint 1 | Fri 19:30-23:30 | Fetch, convert, skeleton | Data fetched and converted (M1), Traficom table cached (M2), UI skeleton with three sample buttons (M6), briefing card on phones. **Gate 1 at 23:30** |
| Sprint 2 | Fri 23:30-Sat 03:30 | Ugly end to end on 3074 | Frequency relevance (M3), geographic relevance (M4), evidence rule (M7), first results export (M8); FE wires the finding card |
| Sleep A | Sat 03:30-07:30 | BE and AI sleep. PM and FE continue on the UI and on sample selection | Three samples chosen from real 3074 rows, cached payloads drafted |
| Sprint 3 | Sat 07:30-11:30 | Partner demo and the first calculations | 07:30 all up, rehearse. **Gate 2 at 09:00** at the stand. Space slot 10-11: validate M5 inputs (Q2, Q7, Q8). AI starts worst-case pfd (M5) |
| Sprint 4 | Sat 11:30-15:30 | Terrestrial side quest, time-boxed | Terrestrial slot 11-12: Q11, Q12, Q13. BE: 3075 to 3076 diff and border filter (S1). AI: P.1546 (S1). PM and FE sleep 12:00-15:00, then FE on decisions and audit log (S4) |
| Sprint 5 | Sat 15:30-19:30 | Lock the differentiators | **Gate 3 at 16:00.** Terrestrial slot 16-17 validates one field-strength result. Space slot 17-18 validates the results format (Q3, Q16). Letter draft (S2), grounded explanations (S3), proof metrics (S5) |
| Sprint 6 | Sat 19:30-23:30 | Robustness and story | Trends panel (S6), unit tests for M5 and S1, results files regenerated for both issues, video script written, deck outline |
| Sprint 7 | Sat 23:30-Sun 03:30 | Freeze | **Gate 4 at 02:00.** Demo cache built and validated, setup README, COULD items only if green (C1, C2, C5). Everyone sleeps from 02:30 |
| Sleep B | Sun 02:30-06:00 | All sleep; PM alarm at 06:00 for the script | |
| Sprint 8 | Sun 06:00-10:00 | Ship | 06:30 record the video in demo mode. **Gate 5 at 08:00.** Submission package, FINAL at 09:15, buffer until 10:00 |

---

## 3. Binary kill or pivot gates

### Gate 1, Fri 23:30
- [ ] `ific3074.zip`, `brific3076.zip`, `brific3075.zip` downloaded and converted; row counts per table logged (M1)
- [ ] Traficom table cached as Parquet, 5 917 rows, lookup by Hz works (M2)
- [ ] One-screen skeleton runs locally with the three sample buttons (M6)
- [ ] Briefing card open on every phone, Q14 and Q15 posted on Discord
- **Fail:** if the `.mdb` files do not convert, move to rung 2 or 3 of the data fallback ladder in `04_Risk_Register_and_Mitigation.md` and keep the adapter interface unchanged.

### Gate 2, Sat 09:00
- [ ] Ugly end-to-end run on the three 3074 samples: ranked list, finding card, evidence links (M3, M4, M7)
- [ ] First `results/space_3074.csv` written (M8)
- [ ] Shown live to the partner when the stand opens; Q1, Q3, Q4, Q5 asked and typed into the card
- **Fail or lukewarm partner:** pivot to Wedge 2 "Finland Filter" by Sat 11:30, reusing the data layer and the export; drop M5 to a COULD.

### Gate 3, Sat 16:00
- [ ] pfd calculation trace on screen with inputs, formula, limit and margin (M5)
- [ ] Evidence on every finding, grounded explanation (M7, S3)
- [ ] Letter draft for a High finding (S2)
- [ ] Terrestrial diff counts and border filter running on 3075 to 3076 (S1), validated with the terrestrial specialists at 16-17 and the results format with the space specialists at 17-18
- **Fail:** cut S6 and every COULD; if P.1546 is not ready, ship the diff and the distance filter with the "no propagation model" label (R5).

### Gate 4, Sun 02:00
- [ ] Feature freeze; only bug fixes after this
- [ ] `data/cache/sample_1.json` to `sample_3.json` built by `scripts/build_cache.py` and validated against `AnalysisResult`
- [ ] `results/space_3074.csv` and `.json`, `results/terrestrial_3076.csv` and `.json` written and spot-checked
- [ ] Setup README: install, fetch data, run, under five minutes
- **Fail:** demo and video in demo mode only; results files are shipped as they are, with the threshold documented.

### Gate 5, Sun 08:00
- [ ] Video under 2:00 recorded and exported
- [ ] Deck exported as PDF
- [ ] Submission package assembled (section 5)
- **Fail:** submit whatever exists at 09:15; never miss 10:00.

---

## 4. First 90 minutes, Fri 20:20 to 21:50

| Who | Do | Done when |
|---|---|---|
| BE | Fetch the data below into a git-ignored `data/raw/`; install `mdbtools`; list tables; convert to DuckDB or SQLite; log row counts | Row counts for 3074, 3075, 3076 in the channel |
| AI | Cache the Traficom table JSON to Parquet; start the reviewed limits CSV for RR Article 21 with the table reference per row; read the pfd bullets in the brief again | `GET /reference/subbands` returns rows (M2); limits CSV has its first rows |
| PM | Log in to the Since AI platform and download the special-interest XLS (a human must do this); read `ReadMe_3076.pdf`; post Q14 and Q15 on Discord; replace the owner placeholders in `02_Requirements_Management_PRD.md` with names; open the briefing card on every phone | XLS in `data/raw/`, questions posted, names in the PRD |
| FE | Scaffold the frontend with `design/girlypop.css`, the three-panel layout and the three sample buttons reading `data/cache/` | Skeleton renders with placeholder payloads |
| All | 21:50 stand-up: confirm Gate 1 criteria and who sleeps when | |

Data to fetch tonight (sizes verified on Fri 6 Nov). `scripts/fetch_data.sh` runs exactly these commands and `scripts/inspect_mdb.py` prints the real table names afterwards:

```bash
mkdir -p data/raw && cd data/raw
curl -LO https://www.itu.int/sns/ific10/ific3074.zip                                          # Space IFIC 3074, 60.8 MB
curl -LO https://www.itu.int/en/ITU-R/terrestrial/brific/BRIFIC/MDB/brific3076.zip            # Terrestrial 3076 MDB extract, 2.4 MB
curl -LO https://www.itu.int/en/ITU-R/terrestrial/brific/BRIFIC/MDB/brific3075.zip            # Terrestrial 3075, 3.4 MB, for the diff
curl -LO https://www.itu.int/en/ITU-R/terrestrial/brific/BRIFIC/ReadMe/ReadMe_3076.pdf        # MDB extract structure, 145 KB
curl -LO https://www.itu.int/en/ITU-R/space/Documents/SRSDiagramV9_1.pdf                      # SRS table diagram, 50 KB
curl -L "https://opendata.traficom.fi/api/v13/Taajuusjakotaulukko" -o taajuusjakotaulukko.json # 5 917 rows, 4.4 MB
```

The synthetic special-interest XLS is on the Since AI platform and must be downloaded by a logged-in team member `[SOURCE DATA: brief 05]`.

---

## 5. Sunday run-sheet: video, submission and peer voting

### 2-minute video, recorded 06:30 to 07:15 in demo mode

PM narrates, FE drives the screen, BE and AI watch for errors. One take per shot, no editing beyond cuts.

| Time | Shot | Requirement |
|---|---|---|
| 0:00-0:10 | Title, one sentence of the problem in the brief's words | |
| 0:10-0:30 | Select Space 3074; the Finnish table loads, 5 917 rows, every row keeps its ID | M1, M2 |
| 0:30-0:50 | Ranked list appears; counter shows screened versus flagged | M3, M4, S5 |
| 0:50-1:05 | Calculation tab: inputs, formula, limit, margin | M5 |
| 1:05-1:20 | Click evidence: the SRS row and the Traficom table row open | M7, S3 |
| 1:20-1:30 | Draft letter to the administration, edit one line | S2 |
| 1:30-1:40 | Approve, audit log line | S4 |
| 1:40-1:55 | Switch to Terrestrial 3076: diff counts, field-strength trace at the border | S1, S6 |
| 1:55-2:00 | Results files written; one-line pitch | M8 |

### Submission package, 07:15 to 09:15

| Deliverable `[SOURCE DATA: brief 07]` | Where it lives |
|---|---|
| Demo of the solution | Video file plus the live app in demo mode |
| Ability to process IFIC files | Repository, setup README, `make data` and `make run` |
| Processed Space IFIC 3074 and Terrestrial IFIC 3076 | `results/space_3074.csv`, `results/space_3074.json`, `results/terrestrial_3076.csv`, `results/terrestrial_3076.json` |
| Information on the input and output | "Inputs and outputs" section of the README, including the relevance rule, limits table source and model parameters |
| Code repository | Link in the submission form |
| Other clarifying documentation | This `pm_pack/` folder and the deck PDF |

Where and how to submit, and whether the demo is live or video `[GAP - ASK PARTNER: Q18]`: ask at the Saturday stand and write the answer here.

### Peer voting

- Mechanics (who votes, when, on what) `[GAP - ASK PARTNER: Q18]`.
- Table setup: one laptop in demo mode on the 3074 ranked list, one phone showing the video on loop, the two results files printed as one page each.
- 60-second stand pitch: the 30-second pitch from `03_Strategic_SWOT_and_Competitor_Matrix.md`, then "pick any notice" and open its evidence live.
- Rotation: two people at the table, two visiting other teams, swap every 30 minutes.
