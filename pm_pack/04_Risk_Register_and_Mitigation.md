# 04 — Risk Register & Mitigation

> ⚠️ **DRAFT — BASED ON MISSING DATA**
> Likelihood (L) and impact (I) scores are our estimates from `README.md` alone. The single biggest risk is the missing data itself (R1, R2, R5). Rescore every row after the Friday 19:30 briefing. Owners are role placeholders (**PM, BE, AI, FE**).

Score = L × I. Act on anything ≥ 12 before Gate 1.

| ID | Risk | L | I | Score | Trigger | Owner | Hard fallback |
|---|---|---|---|---|---|---|---|
| R1 | **Zero partner data at 19:30** | 4 | 5 | **20** | No files or access by 20:30 | BE | Run `scripts/generate_synthetic.py` (see below). Build everything on Branch B; keep Branch A adapter as a stub. |
| R2 | **Dirty / unparseable data** (PDF-only, SRS `.mdb`, GXT) | 4 | 4 | **16** | Parser fails on >30 % of sample after 2 h | AI | Extract only the 6 fields we need via LLM from text; mark the rest "unknown". Fall back to synthetic for the demo. |
| R3 | **README misinterpretation** (we build the wrong tool) | 3 | 5 | **15** | Partner reaction at Sat 09:00 is lukewarm or confused | PM | **Mandatory live prototype check with the partner at Sat 09:00.** Pre-agreed pivot to Wedge 2 (same data layer, different UI). |
| R4 | **Live demo / API failure** | 3 | 5 | **15** | Any LLM call >10 s or errors in rehearsal | AI | **Cached Demo Mode toggle**: precomputed JSON for the 3 samples in `/data/cache/`. Video recorded in Demo Mode. |
| R5 | **NDA forbids cloud LLMs** | 2 | 4 | 8 | Partner says data must stay local | AI | Local open-weight model for extraction; cloud LLM only on synthetic data. Keep prompts provider-agnostic. |
| R6 | **Wrong technical maths** (interference/PFD) | 3 | 4 | 12 | Partner or mentor questions a number | AI | Show only overlap (frequency + area) as fact; label any power calculation "indicative" with formula visible. |
| R7 | **Scope creep** | 4 | 3 | 12 | New feature proposed after Gate 3 | PM | WON'T list in `02_…PRD.md` is binding. Anything new goes to a "post-hackathon" list. |
| R8 | **Fatigue / single point of failure** | 3 | 3 | 9 | Someone awake >20 h | PM | Sleep rotation (see `05_…Roadmap.md`). Every module has a README and a second person who has run it. |
| R9 | **Video or deck not finished** | 2 | 5 | 10 | No video draft by Sun 06:00 | PM | Script written Sat evening; screen-record in Demo Mode; no fancy editing. |
| R10 | **Map / chart library trouble** | 2 | 3 | 6 | Map not rendering by Gate 1 | FE | Static SVG of Finland + circles for footprints. |

---

## R1 Fallback: Synthetic Data in 15 Minutes `[HYPOTHESIS schema]`

The schema below is our guess at what matters. It is **not** an ITU format. Replace with real fields as soon as data arrives.

1. **Filings (≥50):** network name, administration (random country), orbit (GSO longitude or NGSO altitude/inclination), filing stage (advance publication / coordination / notification), publication date, frequency assignments (min–max MHz, up/down link), service area (centre lat/lon + radius km, or polygon), max power indicator.
2. **Finnish protected assets (≥15):** name, lat/lon, band (min–max MHz), service type, protection threshold (indicative).
   Examples to model `[HYPOTHESIS]`: a radio-astronomy site in southern Finland, GNSS receivers, mobile network bands, satellite earth stations in Lapland.
3. **Plant 3 golden cases:** one clear overlap (Sample 1), one borderline (Sample 2), one irrelevant (Sample 3). These become the demo samples and the tests.
4. Fixed random seed so the data is the same on every machine.

---

## Sunday 10:00 Pre-Mortem: Top 3 Ways Teams Lose on This README

1. **They build a chatbot.** A RAG bot over the Radio Regulations answers questions but does not "discover", "connect" or "identify" anything. The evaluators see the same demo as every other team.
2. **They automate the decision.** A tool that says "reject this filing" ignores "human experts firmly in control" and loses trust instantly. Ours suggests; the expert decides.
3. **They wait for data.** Teams that spend Friday night waiting for the partner's files have nothing to show at the Saturday Q&A. We build on synthetic data from minute one and swap later.
