# 🌸 05 — Execution Roadmap & Milestones (EET)

> [!WARNING]
> 🍒 **Draft — based on missing data**
> The schedule assumes ~4 people (team size not provided) and that partner data may be missing. Gate 1 explicitly accepts **synthetic data** so the plan works either way. Re-plan sprint owners once `{TEAM_SIZE}` and `{ROLES_AND_STRENGTHS}` are known.

**Fixed times:** Build starts **Fri 19:30** · Partner Q&A **Sat morning/afternoon** · Internal FINAL **Sun 09:15** · Hard deadline **Sun 10:00**.

---

## Sprints

| Sprint | Time | Focus | Key outputs |
|---|---|---|---|
| S1 | Fri 19:30 – 23:30 | Briefing + foundations | Briefing answers in card; pack updated; repo skeleton; data adapter; synthetic generator; UI skeleton → **Gate 1 at 22:30** |
| S2 | Fri 23:30 – Sat 03:30 | Ugly end-to-end | Extraction → matching → scoring → UI for 3 samples |
| — | Sat 03:30 – 07:30 | Sleep rotation (2 sleep, 2 on bug-fix/data) | — |
| S3 | Sat 07:30 – 11:30 | Partner demo | **Gate 2 at 09:00**: live demo to partner; capture feedback |
| S4 | Sat 11:30 – 15:30 | AI differentiator | Grounded explanations, evidence links, decision buttons, metrics |
| S5 | Sat 15:30 – 19:30 | Lock | **Gate 3 at 16:00**; batch ranking; real data swap if available |
| S6 | Sat 19:30 – 23:30 | Robustness | Tests on golden cases; video script; deck draft |
| S7 | Sat 23:30 – Sun 03:30 | Freeze | **Gate 4 at 02:00**; Demo Mode cache; setup README |
| — | Sun 03:30 – 06:30 | Sleep rotation | — |
| S8 | Sun 06:30 – 10:00 | Ship | **Gate 5 at 08:00**; video, deck PDF, FINAL by 09:15 |

---

## Binary Kill / Pivot Gates

### Gate 1 — Fri 22:30
- [ ] Briefing answers pasted into the pack (or marked "still GAP")
- [ ] Real **or** synthetic seed data loads through the adapter
- [ ] One-Screen UI skeleton runs locally
- **Fail →** drop real-data parsing for tonight; go 100 % Branch B.

### Gate 2 — Sat 09:00
- [ ] Working (ugly) end-to-end pipeline on 3 samples
- [ ] Demoed live to the partner at the Saturday Q&A
- **Fail / lukewarm partner →** pivot to Wedge 2 by 11:30 (reuse data layer + extraction).

### Gate 3 — Sat 16:00
- [ ] Partner feedback written into `02_…PRD.md`
- [ ] Primary differentiator works: cited, grounded explanation per finding + human decision buttons
- **Fail →** cut S4/S5 and C-items; polish what works.

### Gate 4 — Sun 02:00
- [ ] Feature freeze (only bug fixes after this)
- [ ] Deterministic Demo Mode cache filled for all 3 samples
- [ ] Repo `README.md` has <5-minute setup instructions
- **Fail →** demo and video only in Demo Mode.

### Gate 5 — Sun 08:00
- [ ] Video under 2:00 rendered
- [ ] Deck exported as PDF
- [ ] Submission marked **FINAL by 09:15**
- **Fail →** submit whatever exists at 09:15; never miss 10:00.

---

## 2:00 Video Outline (draft)

| Time | Shot |
|---|---|
| 0:00 – 0:15 | Problem: crowded orbits, Finland's systems, experts drowning in filings |
| 0:15 – 0:45 | Load Sample 1 → parameters extracted → footprint over Finland |
| 0:45 – 1:15 | Ranked circular; click top flag → exact evidence |
| 1:15 – 1:35 | Expert approves; audit log; memo export |
| 1:35 – 1:50 | Proof metrics: minutes saved, evidence coverage |
| 1:50 – 2:00 | One-line pitch + team |
