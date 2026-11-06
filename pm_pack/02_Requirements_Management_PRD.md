# 📋 02 — Requirements & PRD: "Filing Radar" (Wedge 1)

> [!WARNING]
> 🍒 **Draft — based on missing data**
> Written from `README.md` only. No real filings, protected-asset lists, user interviews or evaluation criteria were available.
> - All numbers in the before/after workflow are **`[HYPOTHESIS]` placeholders** and must be replaced with partner figures (see Q7 in `01_Partner_Briefing_Questions.md`).
> - Owners are role placeholders (**PM, BE, AI, FE**) because team size and roles were not provided. Hour estimates assume ~4 people.
> - If the partner picks Wedge 2 or 3, the MUST list stays mostly valid; SHOULD/COULD change.

---

## 1. Persona: Monday Morning

**Name:** "Aino", spectrum engineer, satellite coordination team, Traficom `[HYPOTHESIS]`

- A new international circular has been published `[HYPOTHESIS: ITU BR IFIC]`. It contains many new satellite filings from other countries `[README: "new transmission planned far away"]`.
- She must find the few that could affect systems operating in Finland `[README]`, check them against international filings and national rules `[README]`, and decide what is worth investigating `[README]`.
- She is accountable for the decision. The tool may suggest, never decide `[README: "human experts firmly in control"]`.

### Before / After (all figures are `[HYPOTHESIS]` until Q7 is answered)

| Step | Before (today, manual) | After (Filing Radar) |
|---|---|---|
| Find relevant filings in a circular | Scan every filing by hand, ~1–2 days | Auto-ranked list, ~minutes |
| Extract technical parameters | Read filing data per network, ~20–40 min each | Extracted and shown with source references, ~1 min each |
| Cross-check bands and coverage vs Finnish systems | Manual lookups across sources | Automatic overlap check, visual |
| Explain why a filing matters | Written by the expert from scratch | Draft explanation with cited evidence, edited by expert |
| Decision | Expert | **Still the expert** (approve / dismiss / investigate) |

**Proof metrics on screen:** ① estimated expert minutes saved per circular, ② share of flags with complete source evidence (target 100 %).

---

## 2. The One-Screen Product (UI spec)

```
┌───────────────────────────────────────────────────────────────────────┐
│ INPUT: [Upload filing] [Sample 1] [Sample 2] [Sample 3]  ⚙ Demo Mode ◉ │
├───────────────────────────────┬───────────────────────────────────────┤
│ CENTRAL VIEW                  │ ACTIONABLE OUTPUT                      │
│  • Map: filing footprint vs   │  Risk score 0–100 + label              │
│    Finland + protected assets │  Ranked findings, each with:           │
│  • Frequency chart: filing    │   - plain-language reason              │
│    bands vs Finnish bands     │   - evidence links (filing line, rule) │
│  • Reasoning trace (steps)    │   - [Approve] [Dismiss] [Investigate]  │
│                               │  [Export memo]                         │
├───────────────────────────────┴───────────────────────────────────────┤
│ PROOF METRICS: ⏱ minutes saved  ·  📎 evidence coverage %              │
└───────────────────────────────────────────────────────────────────────┘
```

- **1 input:** upload or 3 preloaded samples: (1) clear conflict, (2) borderline case, (3) irrelevant filing that should score low. `[HYPOTHESIS]`
- **1 central view:** map + frequency overlap chart + step-by-step reasoning.
- **1 actionable output:** ranked findings with human decision buttons and memo export.
- **2 proof metrics** as above.

---

## 3. MoSCoW Requirements

### MUST — Gate 2 (Sat 09:00)

| ID | Requirement | Acceptance test | Owner | Est. h |
|---|---|---|---|---|
| M1 | Data adapter interface with **Branch A** (partner data) and **Branch B** (synthetic) implementations | Switching `DATA_SOURCE=synthetic\|partner` changes data with no other code edits | BE | 3 |
| M2 | Synthetic generator: ≥50 filings + ≥15 Finnish protected assets `[HYPOTHESIS schema]` | `python scripts/generate_synthetic.py` writes valid JSON in <1 min | BE | 2 |
| M3 | Extraction: filing → structured `Filing` (bands, orbit, service area, power, stage, dates) | 3 sample filings parse with all required fields; missing fields shown as "unknown", never invented | AI | 4 |
| M4 | Matching: frequency overlap + geographic overlap vs protected assets | Sample 1 flags ≥1 asset; Sample 3 flags none | BE | 4 |
| M5 | Scoring 0–100 with per-factor breakdown | Score shown with each factor's contribution | AI | 2 |
| M6 | One-Screen UI: input, map, frequency chart, findings list | All 3 samples run end-to-end in the browser | FE | 6 |
| M7 | Every finding carries ≥1 evidence item (source + location) | No finding renders without evidence (test) | AI | 2 |

### SHOULD — Gate 3 (Sat 16:00)

| ID | Requirement | Acceptance test | Owner | Est. h |
|---|---|---|---|---|
| S1 | LLM explanation per finding, grounded only in cited evidence | Explanation text references only evidence IDs present in the finding | AI | 4 |
| S2 | Human decision buttons + audit log (who, what, when) | Decisions persist and show in log | FE/BE | 3 |
| S3 | Proof metrics: minutes saved, evidence coverage % | Metrics update per run | FE | 2 |
| S4 | Batch mode: rank a whole circular | 50 synthetic filings ranked in <60 s | BE | 3 |
| S5 | Deadline/urgency factor `[HYPOTHESIS: comment window]` | Countdown shown per filing | BE | 1 |

### COULD — Gate 4 (Sun 02:00)

| ID | Requirement | Acceptance test | Owner | Est. h |
|---|---|---|---|---|
| C1 | Export reviewer memo (Markdown/PDF) | Memo opens with findings + evidence | FE | 2 |
| C2 | Simple PFD/interference indicator `[HYPOTHESIS]`, clearly labelled "indicative" | Value shown with formula and inputs | AI | 3 |
| C3 | Ask-a-question box scoped to the current filing | Answers cite evidence | AI | 3 |
| C4 | Visual polish, dark mode, 3D orbit view | — | FE | 3 |

### WON'T (Anti-Scope)

- Login / auth screens, user management
- Settings pages
- Multi-page CRUD
- Automatic sending of anything to ITU or other administrations
- A general "chat with the Radio Regulations" bot

---

## 4. Traceability Matrix

| Req ID | README phrase | Judging criterion | 2-min video moment |
|---|---|---|---|
| M1, M2 | "large amounts of complicated information" | Production viability | 0:15 — "runs on real or synthetic data, one switch" |
| M3 | "understand their implications" | Production viability | 0:30 — filing loads, parameters appear |
| M4 | "discover relevant filings" / "systems operating in Finland" | Business impact | 0:45 — footprint lights up over Finland |
| M5, S4 | "identify situations worth investigating" | Business impact | 1:00 — ranked circular, top 3 stand out |
| M7, S1 | "connect evidence across sources" / "explainable AI" | Innovation / wow | 1:15 — click a flag, see the exact source |
| S2 | "human experts firmly in control" | Innovation / trust | 1:30 — expert clicks Approve, audit log updates |
| S3 | "more transparent and efficient" | Business impact | 1:45 — minutes-saved counter |
| C1 | "consequential decisions" | Production viability | 1:55 — memo exported |
