# Hackathon PM pack (pm_pack/)

The six planning documents and the interactive briefing card in pm_pack/, what each one contains, how the team is meant to use them, and what the official challenge brief has settled since they were drafted.

> [!NOTE]
> Written on 6 November 2026 from the files in this repository: the seven files in [pm_pack/](../../pm_pack/), the repository [README.md](../../README.md) and the official challenge brief PDF. It summarises the pack rather than replacing it. If this page and a pack file differ, the pack file is authoritative; if the pack and the official brief differ, the brief is.

## What the pack is

- Six numbered Markdown documents plus one interactive HTML briefing card, 254,060 bytes (248.1 KiB) in total, of which the card is 220,002 bytes (214.8 KiB).
- Every document was drafted from the repository README alone (about 180 words at the time, according to the pack itself), before the official brief, any data or any team details existed. Each document opens with a `> [!WARNING]` callout headed "Draft — based on missing data" that says so.
- Tag convention used throughout: `[README]` means stated in the README; `[HYPOTHESIS]` means the pack's own domain guess, unverified; `[GAP - ASK PARTNER]` means unknown and must be asked. The briefing card's Copy prompt adds a fourth tag, `[PARTNER CONFIRMED]`, for answers received at the briefing.
- Owners are role placeholders because team size and roles (`{TEAM_SIZE}`, `{ROLES_AND_STRENGTHS}`) were not provided: PM, BE (backend and data), AI and FE (frontend). Hour estimates assume about four people.
- Default product choice: Wedge 1, "Filing Radar", which document 01 says was recommended in "Step 0" and is to be re-checked after the briefing. The alternatives are Wedge 2, "Circular Triage Agent" (data-light), and Wedge 3, "Interference Screening Pipeline" (data-heavy).

## Why it matters for the challenge

The official brief (see [the challenge brief page](../challenge-brief/README.md)) asks for an auditable AI-assisted workflow that monitors the International Telecommunication Union (ITU) Radiocommunication Bureau (BR) International Frequency Information Circular (IFIC), identifies cases relevant to Finland, supports technical analysis of frequencies and power levels, and prepares expert-reviewable draft correspondence. The pack's four unchanging rules in 06 (the tool suggests and a human decides; no finding without evidence; unknown stays unknown; calculations beyond simple overlap are labelled indicative) line up with evaluation criterion E, auditability and evidence quality (15 %), and criterion C, workflow usefulness (20 %).

The pack predates the brief, so two of its assumptions no longer hold: it does not cover the terrestrial side quest, which carries 25 % under criterion B, and it treats power calculations as "indicative" even though criterion A (25 %) rewards credible, reproducible calculations with visible parameters. The section [What the challenge brief has answered since the pack was written](#what-the-challenge-brief-has-answered-since-the-pack-was-written) maps every open question to the brief.

## Files

| File | Size | Purpose | Key content | When to use it |
|---|---|---|---|---|
| [01_Partner_Briefing_Questions.md](../../pm_pack/01_Partner_Briefing_Questions.md) | 5,743 B (5.6 KiB) | Questions for the partner briefing | Top-5 questions, README-wording questions, data and NDA check, evaluator question, three wedge pitches | Friday 19:30 briefing and the Saturday Q&A stand |
| [01b_Partner_Briefing_Card.html](../../pm_pack/01b_Partner_Briefing_Card.html) | 220,002 B (214.8 KiB) | Phone-sized answer form | Wedge picker, top-10 questions with text boxes, Copy button that builds a Claude update prompt | While the partner answers, then to update the pack |
| [02_Requirements_Management_PRD.md](../../pm_pack/02_Requirements_Management_PRD.md) | 7,783 B (7.6 KiB) | Product requirements for Filing Radar | Persona, before/after table, one-screen UI spec, MoSCoW lists with gates, WON'T list, traceability matrix | Scope decisions and gate checks |
| [03_Strategic_SWOT_and_Competitor_Matrix.md](../../pm_pack/03_Strategic_SWOT_and_Competitor_Matrix.md) | 4,170 B (4.1 KiB) | Positioning | SWOT, competitor matrix, unfair-advantage sentence, 30-second pitch | Pitch, video script, Saturday re-check |
| [04_Risk_Register_and_Mitigation.md](../../pm_pack/04_Risk_Register_and_Mitigation.md) | 4,191 B (4.1 KiB) | Risk register | R1-R10 with scores and hard fallbacks, 15-minute synthetic-data recipe, pre-mortem | Rescoring after the briefing, and whenever a trigger fires |
| [05_Execution_Roadmap_and_Milestones.md](../../pm_pack/05_Execution_Roadmap_and_Milestones.md) | 3,287 B (3.2 KiB) | Schedule in EET | Fixed times, sprints S1-S8, five binary gates, 2:00 video outline | Every sprint boundary and gate |
| [06_AGENTS_Master_Context.md](../../pm_pack/06_AGENTS_Master_Context.md) | 8,884 B (8.7 KiB) | Shared context for coding agents | Mission, four rules, provisional stack, folder tree, data contracts, adapter rule, demo-mode contract, agent division, top-5 gaps | Symlinked as AGENTS.md before any coding |

The pack's weekday times refer to the hackathon days: Friday 6, Saturday 7 and Sunday 8 November 2026. EET is Eastern European Time.

## Document essentials

### 01 Partner briefing questions

The "if we only get 3 minutes" top five, each with the code it changes:

| # | Question | What the answer changes |
|---|---|---|
| 1 | What data can we have tonight: real ITU filings (SRS database, .mdb or GXT files, BR IFIC PDFs), a sample, or nothing? | Branch A (real-data adapter, `adapters/partner.py`) versus Branch B (synthetic generator, `adapters/synthetic.py`) |
| 2 | What are we protecting: a list of Finnish assignments, earth stations or protected services to match filings against? | The `ProtectedAsset` schema and the seed data |
| 3 | May the data go to cloud LLM APIs, or must it stay on local or open-weight models? | The LLM provider in `pipeline/extract.py`, possibly the hosting plan |
| 4 | What does an expert produce today after reviewing a filing (memo, ITU comment or objection, coordination request, nothing)? | The actionable-output panel of the one screen |
| 5 | On Sunday morning, which single live action or metric on screen separates first place from second? | The demo script and the proof metrics shown |

SRS is the ITU Space Radiocommunication Stations database; LLM means large language model. GXT is a file format named in the pack without expansion.

Questions 6-11 each unpack one README phrase:

| # | README phrase | Question | What it changes |
|---|---|---|---|
| 6 | "A new transmission planned far away" | Which filing stages matter most: advance publication, coordination requests, notifications? Tagged `[HYPOTHESIS: ITU API/CR/N stages]` | The `filing_stage` field and urgency weights |
| 7 | "Discover relevant filings" | How many filings arrive per circular, and how many get a close look? | The baseline for the time-saved metric and the pipeline scale target |
| 8 | "Understand their implications" | Which parameters decide whether a filing matters (band, service area, power, orbit)? | Extractor fields and risk-score factors |
| 9 | "Connect evidence across sources" | Which sources do experts cross-check (Radio Regulations, Finnish frequency plan, earlier correspondence, other databases)? | Evidence-panel sources and what gets indexed |
| 10 | "Identify situations worth investigating" | What makes a case worth investigating; can one past real example be shared, anonymised? | The golden demo sample and its test |
| 11 | "Keeping human experts firmly in control" | What must the tool never do on its own (send anything to ITU, dismiss a filing silently)? | Guard rails: approve and dismiss buttons, audit log, no auto-send |

Data and NDA (non-disclosure agreement) reality check, questions 12-14: whether any files are under NDA and may appear in a public repository or video (decides whether `/data/partner/` is git-ignored and whether the demo is synthetic-only); which tools the experts use today (ITU software, spreadsheets, GIS) and whether output should import into them (decides the export format: CSV, PDF memo or JSON); and whether each filing carries a deadline such as a comment window, tagged `[HYPOTHESIS: ~4 months for API comments under RR No. 9.3 — verify]` (adds a deadline factor and countdown).

Question 15, the Sunday 10:00 evaluator question, asks which single live action or metric on screen on Sunday morning separates first place from second; the answer is meant to become the first 30 seconds of the video and the main number on screen.

The three two-sentence pitches, to be read aloud while watching the partner's reaction:

| Wedge | Pitch in one line | Data need |
|---|---|---|
| 1 Filing Radar (recommended) | Load a filing and see within seconds where its frequencies and coverage overlap Finland's protected systems, ranked by a "worth investigating" score; every flag links to the filing line and the rule, and the expert approves or dismisses | Medium |
| 2 Circular Triage Agent | An assistant reads each new ITU circular, triages every filing against the Radio Regulations and the Finnish frequency plan, tracks comment deadlines and drafts a reviewer memo with evidence links for sign-off | Light |
| 3 Interference Screening Pipeline | Ingest full filing data including coverage and antenna diagrams, project each footprint over Finland and run first-pass interference screening against regulatory limits, giving experts an explained risk queue | Heavy |

### 01b Partner briefing card

A single self-contained HTML file (178 lines) titled "Traficom Briefing Card", meant to be opened in a phone browser during the briefing. No server or build step is needed.

- Pick the wedge: three buttons for the wedges above; Wedge 1 is pre-selected and tagged "Recommended".
- Top 10 questions: questions 1-5 and 7-11 from document 01, reworded, each with a hint and a text box. Questions 6 and 12-14 are not on the card.
- Answers and the chosen wedge are saved in the browser's `localStorage` under the key `traficom-briefing-v1`; the card says "Answers are saved on this phone only". Nothing is sent anywhere.
- The Copy button, labelled "Copy Partner Answers as Claude Update Prompt", builds a prompt that names the locked wedge, lists each question with its answer (unanswered ones become "[no answer — keep as GAP - ASK PARTNER]") and instructs Claude to update every file in `./pm_pack/`: replace each matching `[GAP - ASK PARTNER]` and `[HYPOTHESIS]` with the confirmed answer, mark it `[PARTNER CONFIRMED]`, remove the missing-data warning only where every gap in that file is resolved, and list architecture changes needed in 06. The text goes to the clipboard, with a fallback for browsers without the clipboard API.
- Styling: a subset of the Girlypop theme v2 tokens from [design/girlypop.css](../../design/girlypop.css) is inlined, with light and dark schemes, and the hand-drawn cybersigilism mosaic from [design/sigils/mosaic.svg](../../design/sigils/mosaic.svg) is inlined as a background mask; that inlined SVG is why the file is 220 kB. Reduced-motion, reduced-transparency, high-contrast and print fallbacks are included. See [the design theme page](../design-theme/README.md).

### 02 Requirements and PRD

PRD stands for product requirements document. All figures in the before/after table are `[HYPOTHESIS]` placeholders until question 7 is answered.

Persona: "Aino", a spectrum engineer in Traficom's satellite coordination team (`[HYPOTHESIS]`). On a Monday morning a new international circular (`[HYPOTHESIS: ITU BR IFIC]`) lists many new satellite filings from other countries; she must find the few that could affect systems operating in Finland, check them against international filings and national rules, and decide what is worth investigating. She is accountable for the decision; the tool may suggest, never decide.

| Step | Before (manual today) | After (Filing Radar) |
|---|---|---|
| Find relevant filings in a circular | Scan every filing by hand, about 1-2 days | Auto-ranked list, minutes |
| Extract technical parameters | Read filing data per network, about 20-40 min each | Extracted and shown with source references, about 1 min each |
| Cross-check bands and coverage against Finnish systems | Manual lookups across sources | Automatic overlap check, visual |
| Explain why a filing matters | Written from scratch by the expert | Draft explanation with cited evidence, edited by the expert |
| Decision | Expert | Still the expert: approve, dismiss or investigate |

Two proof metrics on screen: estimated expert minutes saved per circular, and the share of flags with complete source evidence (target 100 %).

The one-screen product:

| Area | Content |
|---|---|
| Input bar | Upload filing; Sample 1 (clear conflict), Sample 2 (borderline), Sample 3 (irrelevant, should score low); Demo Mode toggle |
| Central view | Map of the filing footprint against Finland and its protected assets; frequency chart of filing bands against Finnish bands; step-by-step reasoning trace |
| Actionable output | Risk score 0-100 with a label; ranked findings, each with a plain-language reason, evidence links (filing line, rule) and Approve, Dismiss and Investigate buttons; Export memo |
| Proof metrics | Minutes saved; evidence coverage % |

MoSCoW requirements (Must, Should, Could, Won't), with the gate each tier must pass:

| ID | Tier and gate | Requirement | Acceptance test | Owner | h |
|---|---|---|---|---|---|
| M1 | Must, Gate 2 Sat 09:00 | Data adapter with Branch A (partner) and Branch B (synthetic) | `DATA_SOURCE=synthetic` or `partner` switches data with no other code edits | BE | 3 |
| M2 | Must, Gate 2 | Synthetic generator: at least 50 filings and 15 protected assets | `python scripts/generate_synthetic.py` writes valid JSON in under 1 min | BE | 2 |
| M3 | Must, Gate 2 | Extraction of a filing into a structured `Filing` (bands, orbit, service area, power, stage, dates) | 3 samples parse; missing fields shown as "unknown", never invented | AI | 4 |
| M4 | Must, Gate 2 | Matching: frequency and geographic overlap against protected assets | Sample 1 flags at least 1 asset; Sample 3 flags none | BE | 4 |
| M5 | Must, Gate 2 | Score 0-100 with a per-factor breakdown | Each factor's contribution is shown | AI | 2 |
| M6 | Must, Gate 2 | One-screen UI: input, map, frequency chart, findings list | All 3 samples run end to end in the browser | FE | 6 |
| M7 | Must, Gate 2 | Every finding carries at least 1 evidence item (source and location) | No finding renders without evidence (test) | AI | 2 |
| S1 | Should, Gate 3 Sat 16:00 | LLM explanation per finding, grounded only in cited evidence | Text references only evidence IDs present in the finding | AI | 4 |
| S2 | Should, Gate 3 | Decision buttons and audit log (who, what, when) | Decisions persist and show in the log | FE/BE | 3 |
| S3 | Should, Gate 3 | Proof metrics: minutes saved, evidence coverage % | Metrics update per run | FE | 2 |
| S4 | Should, Gate 3 | Batch mode: rank a whole circular | 50 synthetic filings ranked in under 60 s | BE | 3 |
| S5 | Should, Gate 3 | Deadline and urgency factor `[HYPOTHESIS: comment window]` | Countdown shown per filing | BE | 1 |
| C1 | Could, Gate 4 Sun 02:00 | Export a reviewer memo (Markdown or PDF) | Memo opens with findings and evidence | FE | 2 |
| C2 | Could, Gate 4 | Simple pfd or interference indicator `[HYPOTHESIS]`, labelled "indicative" | Value shown with formula and inputs | AI | 3 |
| C3 | Could, Gate 4 | Ask-a-question box scoped to the current filing | Answers cite evidence | AI | 3 |
| C4 | Could, Gate 4 | Visual polish, dark mode, 3D orbit view | None | FE | 3 |

pfd is power-flux density. The WON'T list (anti-scope): login or auth screens and user management; settings pages; multi-page CRUD (create, read, update, delete); automatic sending of anything to ITU or other administrations; a general "chat with the Radio Regulations" bot.

The traceability matrix links requirement IDs to README phrases, to the judging criteria the pack guessed (production viability, business impact, innovation and wow, innovation and trust) and to moments in the two-minute video: 0:15 one-switch data source (M1, M2), 0:30 parameters appear (M3), 0:45 footprint over Finland (M4), 1:00 ranked circular (M5, S4), 1:15 click a flag to see the source (M7, S1), 1:30 Approve updates the audit log (S2), 1:45 minutes-saved counter (S3), 1:55 memo exported (C1). The guessed criteria are superseded by the brief's five weighted criteria (see below).

### 03 Strategic SWOT and competitor matrix

Competitor entries are predictions (`[HYPOTHESIS]`), to be re-checked after the Friday briefing and the Saturday Q&A.

| Quadrant | Points |
|---|---|
| Strengths | Narrow, specific product instead of a generic assistant; data adapter demos on synthetic data and switches to real data with one file edit; every flag is cited; human approve/dismiss loop |
| Weaknesses | No spectrum-regulation expert on the team (`[HYPOTHESIS]`); real ITU formats (SRS .mdb, GXT) may be slow to parse (`[GAP - ASK PARTNER]`); interference maths is easy to get wrong, so it must be labelled "indicative"; team size unknown |
| Opportunities | The narrow README is the biggest advantage, since most teams will build a generic chatbot; Saturday partner Q&A validates early; public sources (Radio Regulations, Finnish frequency plan) exist even with zero partner data (`[HYPOTHESIS]`) |
| Threats | Partner gives only PDFs or nothing at 19:30; an NDA forbids cloud LLMs; evaluators value something unguessed (a different user, policy analysis); a team with real spectrum expertise |

The competitor matrix scores Filing Radar against three "lazy README interpretations": A, a "chat with the Radio Regulations" RAG chatbot (retrieval-augmented generation); B, a filing PDF summariser; C, a pretty 3D satellite visualiser.

| Dimension | Filing Radar | A: RAG chatbot | B: PDF summariser | C: 3D visualiser |
|---|---|---|---|---|
| Discover relevant filings | Yes, ranks a whole circular | No, user must know what to ask | Partly, one file at a time | No |
| Understand implications for Finland | Yes, overlap against Finnish assets | Partly, generic answers | Partly, generic summary | Partly, visual only |
| Connect evidence across sources | Yes, cited filing, rule and asset | Partly, citations to rules only | No | No |
| Identify situations worth investigating | Yes, score and reasons | No | No | No |
| Human in control | Yes, approve, dismiss, audit log | Partly, implicit | Partly, implicit | Not applicable |
| 15-second wow | Yes, footprint lights up, click to source | Partly, looks like every chatbot | No, text wall | Yes, but no substance |
| Works with zero partner data | Yes, synthetic Branch B | Yes | Partly, needs PDFs | Yes |

Where they win: C looks prettier and A is faster to build. The pack's answer is to borrow C's visual hook (the map), keep A's citations, and attach both to a real decision.

The unfair-advantage sentence says the team is the only one likely to turn "a new transmission planned far away" into a ranked, cited, Finland-specific shortlist that a Traficom expert can approve in one click. The 30-second pitch tells the story in order: a new circular every few weeks with many filings; experts must find the few that could interfere with Finnish systems before the comment deadline; today that is manual reading and cross-checking; Filing Radar does the first pass (extract parameters, check frequencies and coverage against protected systems, rank); every flag links to its source and the expert makes every decision; same experts, same control, minutes instead of days for the first pass. The figures "every few weeks" and "minutes instead of days" are `[HYPOTHESIS]` and must be replaced with partner numbers before the video.

### 04 Risk register and mitigation

Score is likelihood (L) times impact (I); anything scoring 12 or more is acted on before Gate 1. The pack calls the missing data itself the single biggest risk (R1, R2, R5) and asks for every row to be rescored after the Friday 19:30 briefing.

| ID | Risk | L | I | Score | Owner | Hard fallback |
|---|---|---|---|---|---|---|
| R1 | Zero partner data at 19:30 | 4 | 5 | 20 | BE | Run `scripts/generate_synthetic.py`; build everything on Branch B; keep the Branch A adapter as a stub |
| R2 | Dirty or unparseable data (PDF-only, SRS .mdb, GXT) | 4 | 4 | 16 | AI | Extract only the 6 needed fields from text with the LLM; mark the rest "unknown"; synthetic data for the demo |
| R3 | README misinterpretation (wrong tool built) | 3 | 5 | 15 | PM | Mandatory live prototype check with the partner Sat 09:00; pre-agreed pivot to Wedge 2 (same data layer, different UI) |
| R4 | Live demo or API failure | 3 | 5 | 15 | AI | Cached Demo Mode toggle with precomputed JSON for the 3 samples in `/data/cache/`; video recorded in Demo Mode |
| R5 | NDA forbids cloud LLMs | 2 | 4 | 8 | AI | Local open-weight model for extraction; cloud LLM only on synthetic data; provider-agnostic prompts |
| R6 | Wrong technical maths (interference, pfd) | 3 | 4 | 12 | AI | Show only frequency and area overlap as fact; label any power calculation "indicative" with the formula visible |
| R7 | Scope creep | 4 | 3 | 12 | PM | The WON'T list in 02 is binding; new ideas go to a post-hackathon list |
| R8 | Fatigue, single point of failure | 3 | 3 | 9 | PM | Sleep rotation per 05; every module has a README and a second person who has run it |
| R9 | Video or deck not finished | 2 | 5 | 10 | PM | Script written Saturday evening; screen-record in Demo Mode; no fancy editing |
| R10 | Map or chart library trouble | 2 | 3 | 6 | FE | Static SVG of Finland with circles for footprints |

The four risks scoring 15 or more are R1, R2, R3 and R4; their triggers are, in order, no files or access by 20:30, a parser failing on more than 30 % of the sample after two hours, a lukewarm or confused partner reaction at Saturday 09:00, and any LLM call over 10 s or an error in rehearsal.

The R1 fallback, "synthetic data in 15 minutes" (`[HYPOTHESIS schema]`, explicitly not an ITU format): generate at least 50 filings (network name, administration, orbit as GSO longitude or NGSO altitude and inclination, filing stage, publication date, frequency assignments as min-max MHz with link direction, service area as centre and radius or polygon, maximum power indicator); at least 15 Finnish protected assets (name, latitude and longitude, band, service type, indicative protection threshold), modelled on examples such as a radio-astronomy site in southern Finland, GNSS receivers, mobile network bands and satellite earth stations in Lapland; plant three golden cases (clear overlap, borderline, irrelevant) that become the demo samples and the tests; and fix the random seed so every machine gets the same data. GSO and NGSO mean geostationary and non-geostationary satellite orbit; GNSS is global navigation satellite system.

The Sunday 10:00 pre-mortem names three ways teams lose on this README: they build a chatbot (which answers questions but does not discover, connect or identify anything); they automate the decision (losing the trust that "human experts firmly in control" demands); they wait for data instead of building on synthetic data from minute one.

### 05 Execution roadmap and milestones

Fixed times (EET): build starts Friday 19:30; partner Q&A on Saturday morning and afternoon; internal FINAL on Sunday 09:15; hard deadline Sunday 10:00. The schedule assumes about four people, and Gate 1 explicitly accepts synthetic data so the plan works with or without partner data.

| Sprint | Time | Focus | Key outputs |
|---|---|---|---|
| S1 | Fri 19:30-23:30 | Briefing and foundations | Briefing answers in the card; pack updated; repo skeleton; data adapter; synthetic generator; UI skeleton; Gate 1 at 22:30 |
| S2 | Fri 23:30-Sat 03:30 | Ugly end-to-end | Extraction, matching, scoring and UI for 3 samples |
| Rest | Sat 03:30-07:30 | Sleep rotation | 2 sleep, 2 on bug-fix and data |
| S3 | Sat 07:30-11:30 | Partner demo | Gate 2 at 09:00: live demo to the partner; feedback captured |
| S4 | Sat 11:30-15:30 | AI differentiator | Grounded explanations, evidence links, decision buttons, metrics |
| S5 | Sat 15:30-19:30 | Lock | Gate 3 at 16:00; batch ranking; real-data swap if available |
| S6 | Sat 19:30-23:30 | Robustness | Tests on golden cases; video script; deck draft |
| S7 | Sat 23:30-Sun 03:30 | Freeze | Gate 4 at 02:00; Demo Mode cache; setup README |
| Rest | Sun 03:30-06:30 | Sleep rotation | None |
| S8 | Sun 06:30-10:00 | Ship | Gate 5 at 08:00; video, deck PDF, FINAL by 09:15 |

The five binary kill or pivot gates:

| Gate | Time | Checklist | On failure |
|---|---|---|---|
| 1 | Fri 22:30 | Briefing answers pasted into the pack or marked "still GAP"; real or synthetic seed data loads through the adapter; one-screen UI skeleton runs locally | Drop real-data parsing for the night; go 100 % Branch B |
| 2 | Sat 09:00 | Working (ugly) end-to-end pipeline on 3 samples; demoed live to the partner at the Saturday Q&A | On failure or a lukewarm partner, pivot to Wedge 2 by 11:30, reusing the data layer and extraction |
| 3 | Sat 16:00 | Partner feedback written into 02; primary differentiator works (cited, grounded explanation per finding plus decision buttons) | Cut S4 and S5 work and the Could items; polish what works |
| 4 | Sun 02:00 | Feature freeze (bug fixes only); deterministic Demo Mode cache filled for all 3 samples; repository README has under-5-minute setup instructions | Demo and video only in Demo Mode |
| 5 | Sun 08:00 | Video under 2:00 rendered; deck exported as PDF; submission marked FINAL by 09:15 | Submit whatever exists at 09:15; never miss 10:00 |

The draft 2:00 video outline:

| Time | Shot |
|---|---|
| 0:00-0:15 | Problem: crowded orbits, Finland's systems, experts drowning in filings |
| 0:15-0:45 | Load Sample 1; parameters extracted; footprint over Finland |
| 0:45-1:15 | Ranked circular; click the top flag to see exact evidence |
| 1:15-1:35 | Expert approves; audit log; memo export |
| 1:35-1:50 | Proof metrics: minutes saved, evidence coverage |
| 1:50-2:00 | One-line pitch and team |

### 06 Master context for agents (AGENTS.md)

Mission: help Traficom spectrum experts discover international satellite filings that may affect systems operating in Finland, explain why with cited evidence, and let the expert decide (`[README]`). The architecture and the schemas are the pack's own `[HYPOTHESIS]` model, not ITU or Traficom formats; no field name is an official specification.

The four rules that never change:

1. The tool suggests; a human decides. No automatic sending, rejecting or dismissing.
2. No finding without evidence. Every `Finding` has at least one `Evidence`.
3. Unknown stays unknown. Extraction never invents a missing value; it returns `null` and the UI shows "unknown".
4. Technical calculations beyond simple overlap are labelled `indicative`.

Provisional stack (`[HYPOTHESIS]`):

| Layer | Components |
|---|---|
| Backend | Python 3.12, FastAPI, Pydantic v2, Shapely (geometry), pytest |
| AI | Claude API (`claude-sonnet-5-5`) with structured output for extraction and explanations; if the NDA forbids cloud models (`[GAP]`), a local open-weight model behind the same `LLMClient` interface |
| Frontend | React, Vite, TypeScript, shadcn/ui, Tailwind CSS v4, MapLibre GL (map), Recharts (frequency chart) |
| Design system | Girlypop theme v2: import `design/girlypop.css` into `frontend/src/globals.css`, follow `design/girlypop-theme.md`, theme tokens only (no hex codes), `risk-*` tokens with a text label for risk badges, `bg-sigil` on the app `<body>`, text on the mosaic in `foreground` or `secondary-foreground`, no emoji, no playful copy on findings, decisions or exports |
| Storage | JSON files in `/data`; no database |

Folder tree in brief: `AGENTS.md` is a symlink to this file; `backend/app/` holds `main.py` (FastAPI routes), `models.py` (Pydantic contracts, frozen), `config.py` (`DATA_SOURCE`, `DEMO_MODE`, LLM settings), `adapters/` (`base.py`, `synthetic.py` for Branch B, `partner.py` for Branch A), `pipeline/` (`extract.py`, `match.py`, `score.py`, `explain.py`), `llm.py` and `cache.py`; `frontend/src/` holds `types.ts`, `App.tsx` and the components `InputBar`, `MapView`, `BandChart`, `FindingsList` and `Metrics`; `data/` has `seed/` (synthetic, committed), `partner/` (real data, git-ignored) and `cache/` (Demo Mode JSON, committed); plus `scripts/generate_synthetic.py` and `tests/`.

Data contracts (`[HYPOTHESIS schema]`, Pydantic): `FilingStage`, `FrequencyRange`, `ServiceArea`, `Orbit`, `Filing`, `ProtectedAsset`, `Evidence`, `Finding`, `AnalysisResult` and `ReviewDecision`. `frontend/src/types.ts` mirrors them one to one. `models.py` is frozen after Gate 1; changes go through the PM and are applied to both files in the same commit.

Branch A / Branch B adapter rule: a `DataAdapter` protocol with `list_filings()`, `get_filing(filing_id)` and `list_assets()`. `DATA_SOURCE=synthetic` selects `adapters/synthetic.py` (reads `data/seed/`); `DATA_SOURCE=partner` selects `adapters/partner.py` (reads `data/partner/`). Swapping synthetic for real data must be one file edit, `partner.py`; the pipeline, API and UI never import an adapter directly but get it from `config.get_adapter()`.

Deterministic Demo Mode contract: with `DEMO_MODE=1` or the UI toggle, `POST /analyze` for `sample_1`, `sample_2` or `sample_3` returns `data/cache/<sample_id>.json` with `from_cache=true` and makes no network calls; `scripts/build_cache.py` regenerates the cache from a live run and the output is committed; the cached JSON must validate against `AnalysisResult`, checked by a test; the video and the Sunday demo are recorded in Demo Mode.

Multi-agent division:

| Agent | Owns | Must not touch |
|---|---|---|
| Claude Code | `backend/app/pipeline/`, `llm.py`, prompts, `models.py` (with PM approval) | `frontend/` |
| Cursor | `frontend/` | `backend/app/pipeline/` |
| Codex | `scripts/`, `tests/`, `adapters/` | UI components, prompts |
| Antigravity | Visual polish, map styling, video and deck assets | Contracts, pipeline |

Shared rules: one agent per folder at a time, small commits, one feature per branch; contracts first, so an agent that needs a new field stops and asks the PM; every agent runs `pytest` (backend) or `npm run build` (frontend) before committing; no secrets or partner data in commits, with `data/partner/` and `.env` git-ignored.

Top-5 gaps that could change the architecture (`[GAP - ASK PARTNER]`): the real data format (rewrites `adapters/partner.py` and maybe `extract.py`); the protected-asset list (changes `ProtectedAsset` and the matching logic); whether cloud LLMs are allowed (swaps `LLMClient` to a local model); the expert's actual output (changes `ReviewDecision` and the export); what the evaluators judge on Sunday (moves effort between batch ranking, explanations and interference maths).

## How to use the pack

1. Make 06 the shared context before any coding. The instruction in 06 is a symlink from the repository root; the command below was run in a scratch copy of the folder while writing this page, not in the repository, which has no `AGENTS.md` yet.

   ```bash
   ln -s pm_pack/06_AGENTS_Master_Context.md AGENTS.md
   ln -s pm_pack/06_AGENTS_Master_Context.md CLAUDE.md
   readlink AGENTS.md CLAUDE.md
   ```

   ```text
   pm_pack/06_AGENTS_Master_Context.md
   pm_pack/06_AGENTS_Master_Context.md
   ```

   06 asks for the same for `.cursorrules`.
2. At the briefing, open `01b_Partner_Briefing_Card.html` on a phone, pick the wedge, type the partner's answers, tap Copy and paste the prompt into Claude. The prompt tells Claude to update every pack file, replace resolved `[GAP - ASK PARTNER]` and `[HYPOTHESIS]` tags with `[PARTNER CONFIRMED]`, and list architecture changes in 06. Gate 1 (Friday 22:30) expects the answers to be in the pack or marked "still GAP".
3. Freeze `models.py` after Gate 1. Later changes go through the PM and land in `models.py` and `frontend/src/types.ts` in one commit.
4. Rescore the risk register and re-check the competitor matrix after the briefing and again after the Saturday Q&A, and write partner feedback into 02 before Gate 3.
5. The stack and the card depend on the design system in [design/](../../design/): [girlypop.css](../../design/girlypop.css), [girlypop-theme.md](../../design/girlypop-theme.md) and the sigil tiles with their [preview](../../design/sigils/preview.html). The theme's serious-context rule (plain, precise language on findings, decisions and exports; no emoji) applies to everything the product shows an expert. See [the design theme page](../design-theme/README.md).

## What the challenge brief has answered since the pack was written

> [!IMPORTANT]
> Cross-reference added on 6 November 2026. It is not part of the pack. It maps the pack's open questions and hypotheses to the official brief, [Since_AI_Traficom_Challenge_Brief_FINAL_04112026.pdf](../../Since_AI_Traficom_Challenge_Brief_FINAL_04112026.pdf) (281,800 bytes, 275.2 KiB, five pages), without changing the pack's recommendations. "Section" refers to the brief's numbered sections 01-08; the brief is summarised on [the challenge brief page](../challenge-brief/README.md).

### Answered by the brief

| Pack item | Pack position | What the brief says | Section |
|---|---|---|---|
| Q1, R1, R2, gap 1: data | Feared zero data or PDF-only data; Branch B synthetic fallback | The ITU BR IFIC publications are public and mandatory. Space IFIC: source page [BR IFIC (Space services)](https://www.itu.int/en/ITU-R/space/brific/Pages/default.aspx), downloads from the [Space IFIC databases page](https://www.itu.int/sns/wic/demowic.html) as zipped MS Access databases, one per circular. Terrestrial IFIC: [BR IFIC (Terrestrial services)](https://www.itu.int/en/ITU-R/terrestrial/brific/Pages/default.aspx), with an MDB extract per issue. All existing and forthcoming IFICs must be evaluable | 05 |
| Mandatory test issues | Not foreseen | Space IFIC no. 3074 and Terrestrial IFIC no. 3076 must each be analysed, with concerns raised and results submitted separately; they are used to evaluate accuracy | 05, 07 |
| Q2, gap 2: what to compare against | `ProtectedAsset` list unknown; synthetic assets modelled on guesses | Regulation 4 "M4" (Radiotaajuusmääräys, Radio Frequency Regulation, 4 AG/2026M of 26 March 2026) including the table of frequencies in Finland (Taajuusjakotaulukko, frequency allocation table), on [Finlex](https://www.finlex.fi/fi/viranomaiset/maarayskokoelmat/traficom-viestinta/2026/3) and through the Traficom open-data API ([Swagger](https://opendata.traficom.fi/swagger/ui/index#/Taajuusjakotaulukko), [endpoint](https://opendata.traficom.fi/api/v13/Taajuusjakotaulukko)); plus a synthetic XLS table of frequencies of special interest on the SinceAI platform (station number, frequency range with bandwidth and centre frequency, terrestrial coordinates, antenna height, direction and directivity). Optional: Regulation 15 "M15", the CEPT implementation database and the ITU Radio Regulations | 03, 05 |
| Q6: filing stages | `[HYPOTHESIS: ITU API/CR/N stages]`; `FilingStage` enum of advance publication, coordination, notification | The publications of interest are the special sections API/A (Advance Publication of Information), CR/C (Coordination Request) and AP30 including AP30A and AP30B. GSO and non-GSO power-flux densities are of special interest | 02, 03 |
| Q4, gap 4: expert output | Memo export (C1), approve, dismiss, investigate | Summaries of relevant content and frequency ranges affecting Finland; detected and explained concerns including technical calculations such as pfd where appropriate; identification of the counterpart administration and a draft correspondence template for expert review | 02, 03 |
| Q8: deciding parameters | Band, service area, power, orbit guessed | Frequency ranges, pfd and field strength, geographical locations, and GSO and non-GSO pfd; terrestrial notices add station class, bandwidth and geography | 02, 03 |
| Q9: sources to cross-check | Radio Regulations and Finnish frequency plan guessed | M4, M15, the additional frequency tables, CEPT harmonisation data and the ITU Radio Regulations, plus other public spectrum sources | 03, 05 |
| Q13: expert tools | Unknown; export format open | ITU SpaceCom (comments on special sections) or direct database logic to identify systems of interest; ITU GIBC (Graphical Interface for Batch Calculations) or direct calculation logic for pfd; the [ITU space network software page](https://www.itu.int/en/ITU-R/software/Pages/space-network-software.aspx) | 02, 05 |
| Q11: guard rails | No auto-send, no silent dismissal, audit log | Analysis must stay transparent and technically reviewable; correspondence is a draft for expert review; criterion E requires that an expert can understand why a conclusion was reached | 02, 06 |
| Q5, Q15, gap 5: what is judged | One single metric sought; traceability matrix guessed criteria | Five weighted criteria: A technical analysis and reproducibility 25 %; B extensibility and terrestrial side quest 25 %; C workflow usefulness, innovation and output quality 20 %; D case recognition accuracy and relevance 15 %; E auditability and evidence quality 15 % | 06 |
| R6, rule 4, C2: calculations | Anything beyond overlap labelled "indicative"; pfd indicator only a Could item | Criterion A rewards technically credible calculations and reasoning, deterministic and reproducible components, and visible assumptions and model parameters; the brief names pfd calculations for space and ITU-R P.1546 field-strength calculations for terrestrial. The "indicative only" stance should be revisited | 02, 03, 06 |
| Terrestrial side quest | Not covered at all | Use consecutive terrestrial BR IFIC issues to identify new, modified or withdrawn land-mobile notices; filter foreign assignments relevant to Finland; determine the applicable ITU, CEPT/ECC and national framework; identify a coordination or protection criterion such as ECC T/R 25-08; calculate field strengths deterministically with the ITU-R P.1546 propagation model; produce expert-reviewable findings with the source notice, field strengths, parameters, assumptions and citations; surface trends or anomalies in neighbouring administrations' notices. Carries 25 % under criterion B | 02, 06 |
| Gate 5 deliverables | Video, deck PDF, FINAL by 09:15 | Demo; the ability to process IFIC files into relevant output using the Finnish usage information; processed Space IFIC 3074 and Terrestrial IFIC 3076 as separate files; information on input and output; the code repository; other clarifying documentation | 07 |
| Gate 2 partner contact | "Partner Q&A Sat morning/afternoon" | Discord is the preferred channel. Q&A stand Saturday 9.00-12.00 and 14.30-18.00; senior specialists on Space IFIC Saturday 10-11 and 17-18, on Terrestrial IFIC Saturday 11-12 and 16-17. Contacts: Traficom.sinceai.2026@gmail.com (Discord traficomsinceai2026), pekka.pussinen@traficom.fi (Discord pekkatraficom_83563), otto.julkunen@traficom.fi (Discord ottoj0436_45333); phone numbers are in the PDF | 08 |
| Q7: volume | Filings per circular unknown | No counts. The brief describes bi-monthly space and terrestrial publications in PDF and database form and a "huge mass" of API/A, CR/C and AP30 information; the ITU page says the space BR IFIC appears once every two weeks | 02, 03 |
| 03 threat "evaluators value something unguessed" | Policy analysis feared | Section 04 lists ingestion, information extraction, RAG, rule-based or deterministic components, agentic workflows, anomaly detection, ranking and prioritisation, and auditable citation or provenance; no architecture is required, and technical correctness, traceability and expert reviewability outrank model choice | 04 |

CEPT is the European Conference of Postal and Telecommunications Administrations and ECC its Electronic Communications Committee. AP30, AP30A and AP30B refer to Appendices 30, 30A and 30B of the Radio Regulations (background, not from the brief). Regulation 15 "M15" is Luvasta vapaiden radiolähettimien yhteistaajuudet ja käyttö (Collective Frequencies for Licence-exempt Radio Transmitters and Their Use), on [Finlex](https://www.finlex.fi/fi/viranomaiset/maarayskokoelmat/traficom-viestinta/2025/51209); the CEPT data is at [docdb.cept.org](https://docdb.cept.org/implementation/overview) and the Radio Regulations at [itu.int/pub/r-reg-rr](https://www.itu.int/pub/r-reg-rr).

The mandatory files, as checked on 6 November 2026 (sizes from the captured source inventory, confirmed with the HEAD request below):

| File | URL | Published | Size |
|---|---|---|---|
| Space IFIC 3074 database | [ific3074.zip](https://www.itu.int/sns/ific10/ific3074.zip) | 23.06.2026 | 60,837,631 B (58.0 MiB); contains ific3074.mdb, 286,654,464 B (273.4 MiB) |
| Terrestrial BR IFIC 3076 MDB extract | [brific3076.zip](https://www.itu.int/en/ITU-R/terrestrial/brific/BRIFIC/MDB/brific3076.zip) | 21.07.2026 | 2,406,450 B (2.3 MiB); contains brific3076.mdb, 25,145,344 B (24.0 MiB) |

```bash
curl -sS -I -L --max-time 60 -A "Mozilla/5.0 (Macintosh) AppleWebKit/537.36 Chrome/124 Safari/537.36" "https://www.itu.int/sns/ific10/ific3074.zip" | grep -i -E '^HTTP|^content-length|^last-modified'
```

```text
HTTP/1.1 200 OK
Last-Modified: Tue, 23 Jun 2026 06:25:33 GMT
Content-Length: 60837631
```

Both databases are MS Access files; the space one has 95 catalog entries (tables such as `notice`, `freq`, `geo` and `non_geo`), which the pack's `[HYPOTHESIS]` schema does not resemble. Details are on [the Space IFIC databases page](../links/itu-space-ific-databases/README.md) and [the terrestrial BR IFIC page](../links/itu-terrestrial-brific/README.md).

### Not answered by the brief

| Pack item | Status on 6 November 2026 |
|---|---|
| Q3, R5, gap 3: cloud LLM policy | Not mentioned. The brief says challenges can be built with synthetic, anonymised or public data and that no personal data is required (section 05), but says nothing about where models may run |
| Q12: NDA | Not mentioned. Every listed dataset is public ITU, Finlex or Traficom material, except the synthetic XLS on the SinceAI platform; the brief contains no NDA clause |
| Q14, S5: comment deadlines | Not mentioned. ITU's own WRS-24 presentation, linked from the BR IFIC (Space services) page as [Presentation of the BR IFIC (Space services)](https://www.itu.int/en/ITU-R/space/Documents/BR%20IFIC%20%28Space%20services%29.pdf), quotes Radio Regulations No. 9.3: an administration that expects unacceptable interference communicates its comments within four months of the BR IFIC publication date; the same four-month limit appears under Nos. 9.41, 9.51 and 9.52. See [the ITU space BR IFIC page](../links/itu-space-brific/README.md) |
| Q5, Q15: the single Sunday metric | No single metric; the brief gives the five weighted criteria instead |
| Team size and roles | Not a brief matter; the role placeholders stay until the team fills them in |

## Key facts for the team

| Item | Value |
|---|---|
| Pack files | 6 Markdown documents and 1 HTML card, 705 lines, 254,060 B (248.1 KiB) |
| Pack basis | README only, before the brief; every file carries the missing-data warning |
| Default wedge | Wedge 1, Filing Radar |
| Model string in 06 | `claude-sonnet-5-5` (quoted as written; provisional) |
| Fixed times | Build Fri 19:30; Gate 1 Fri 22:30; Gate 2 Sat 09:00; Gate 3 Sat 16:00; Gate 4 Sun 02:00; Gate 5 Sun 08:00; FINAL Sun 09:15; deadline Sun 10:00 |
| Brief evaluation weights | A 25 %, B 25 %, C 20 %, D 15 %, E 15 % |
| Mandatory issues | Space IFIC 3074 (23.06.2026) and Terrestrial IFIC 3076 (21.07.2026), results submitted separately |
| Q&A stand | Sat 9.00-12.00 and 14.30-18.00, Discord preferred |

## Related pages

- [Documentation index](../README.md)
- [Challenge brief](../challenge-brief/README.md)
- [Design theme](../design-theme/README.md)
- [ITU space BR IFIC](../links/itu-space-brific/README.md), [Space IFIC databases](../links/itu-space-ific-databases/README.md), [ITU terrestrial BR IFIC](../links/itu-terrestrial-brific/README.md), [ITU space software](../links/itu-space-software/README.md), [ITU Radio Regulations](../links/itu-radio-regulations/README.md)
- [Regulation 4 (M4) on Finlex](../links/finlex-regulation-m4/README.md), [Traficom open-data Swagger](../links/traficom-opendata-swagger/README.md), [Traficom frequency table API](../links/traficom-frequency-table-api/README.md), [Regulation 15 (M15) on Finlex](../links/finlex-regulation-m15/README.md), [CEPT implementation database](../links/cept-docdb-implementation/README.md)

## Caveats

- Everything tagged `[HYPOTHESIS]` or `[GAP - ASK PARTNER]` is unverified until the card's prompt or a manual edit replaces it; the cross-reference above records what the brief settles but does not edit the pack.
- The card keeps answers only in one phone's browser storage; nothing is synced or committed, so copy the prompt out before the briefing ends.
- The pack's data contracts, folder tree and stack are provisional designs; the real IFIC data is MS Access databases with their own table structure, and the pack's `partner.py` adapter is the only place where that is meant to be absorbed.
- The pack's judging criteria, time figures and filing volumes were guesses; use the brief's criteria and the ITU publication facts above instead.
- The HTML card is 220 kB because the sigil mosaic is inlined; open it directly in a browser rather than reading it in an editor.
