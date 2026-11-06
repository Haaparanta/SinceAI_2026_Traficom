# 01 — Partner Briefing Questions (Traficom)

> [!WARNING]
> **Draft — based on missing data**
> This pack was generated from `README.md` alone (~180 words). There were **no datasets, sample filings, API docs, evaluation criteria or team details** available.
> - `[README]` = stated in the README. `[HYPOTHESIS]` = our domain guess, **unverified**. `[GAP - ASK PARTNER]` = unknown; must be asked.
> - Team size and roles (`{TEAM_SIZE}`, `{ROLES_AND_STRENGTHS}`) were not provided, so owners are role placeholders: **PM, BE** (backend/data), **AI**, **FE** (frontend).
> - Default product choice: **Wedge 1 "Filing Radar"** (recommended in Step 0). Re-check after the briefing.

---

## Top 5: "If We Only Get 3 Minutes"

| # | Question | Why we ask → How the answer changes our code |
|---|----------|-----------------------------------------------|
| 1 | **What data can we have tonight?** Real ITU filings (SRS database, `.mdb`/GXT files, BR IFIC PDFs), a sample, or nothing? | Decides **Branch A (real data adapter)** vs **Branch B (synthetic generator)**. Changes `adapters/partner.py` vs `adapters/synthetic.py`. |
| 2 | **What are we protecting?** Is there a list of Finnish assignments, earth stations or protected services (e.g. radio astronomy, GNSS, mobile bands) we can match filings against? | Without a protected-asset list the matching step has nothing to compare to. Changes the `ProtectedAsset` schema and seed data. |
| 3 | **Can this data go to cloud LLM APIs**, or must it stay on local/open-weight models? | Changes the LLM provider in `pipeline/extract.py` and possibly the hosting plan. |
| 4 | **What does an expert produce today** after reviewing a filing (memo, ITU comment/objection, coordination request, nothing)? | Defines the "Actionable Output" panel on the one screen. |
| 5 | **On Sunday morning, what single live action or metric on screen separates 1st place from 2nd?** | Defines the demo script and which proof metrics we show. |

---

## Unpacking the README Wording

| # | README phrase `[README]` | Question | Why we ask → How it changes our code |
|---|---|---|---|
| 6 | "A new transmission planned far away" | Which filing stages matter most to you: advance publication, coordination requests, notifications? `[HYPOTHESIS: ITU API/CR/N stages]` | Sets the `filing_stage` field and which stages get a higher urgency weight. |
| 7 | "Discover relevant filings" | Roughly how many filings arrive per circular, and how many does an expert actually look at closely? | Gives the baseline for our ROI metric (time saved per circular). Sets the scale target for the pipeline. |
| 8 | "Understand their implications" | Which technical parameters decide whether a filing matters (frequency band, service area, power, orbit)? | Defines the fields the extractor must pull out and the factors in the risk score. |
| 9 | "Connect evidence across sources" | Which sources do experts cross-check today (Radio Regulations, Finnish frequency plan, earlier correspondence, other databases)? | Decides which sources the evidence panel links to and what we index. |
| 10 | "Identify situations worth investigating" | What makes a case "worth investigating" in practice? Can you share one past real example (anonymised is fine)? | One real case becomes our golden demo sample and our test. |
| 11 | "Keeping human experts firmly in control" | What must the tool **never** do on its own (e.g. send anything to ITU, dismiss a filing silently)? | Defines guard rails: approve/dismiss buttons, audit log, no auto-send. |

## Data & NDA Reality Check

| # | Question | Why we ask → How it changes our code |
|---|---|---|
| 12 | Are any files under NDA, and may they appear in a public repo or video? | Decides whether `/data/partner/` is git-ignored and whether the demo must use synthetic data only. |
| 13 | What tools do your experts use today (ITU software, spreadsheets, GIS)? Should our output import into any of them? | Decides export format (CSV, PDF memo, JSON). |
| 14 | Are there deadlines tied to each filing (e.g. a comment window)? `[HYPOTHESIS: ~4 months for API comments under RR No. 9.3 — verify]` | Adds a deadline/urgency factor and countdown in the UI. |

## The Sunday 10:00 Evaluator Question

| # | Question | Why we ask → How it changes our code |
|---|---|---|
| 15 | *"Since the README leaves the exact format open, what single live action or metric on screen on Sunday morning separates 1st place from 2nd place?"* | Becomes the first 30 seconds of our video and the main number on screen. |

---

## Three 2-Sentence Pitch Scripts (read aloud, watch their reaction)

**Wedge 1 — Filing Radar (recommended):**
"You load a new satellite filing and in seconds see where its frequencies and coverage overlap Finland's protected systems, with a ranked 'worth investigating' score. Every flag links back to the exact line in the filing and the rule behind it, and your expert approves or dismisses it."

**Wedge 2 — Circular Triage Agent (data-light):**
"An assistant reads each new ITU circular, triages every filing against the Radio Regulations and the Finnish frequency plan, and tracks the comment deadlines. It drafts a reviewer memo with evidence links that your expert signs off before anything leaves the building."

**Wedge 3 — Interference Screening Pipeline (data-heavy):**
"We ingest the full filing data, including coverage and antenna diagrams, project each footprint over Finland and run first-pass interference screening against regulatory limits. Your experts get an explained risk queue instead of starting from raw data."

> [!TIP]
> After the briefing: paste answers into `01b_Partner_Briefing_Card.html` and tap **Copy** to get a ready update prompt for Claude.
