# Solution plans: five ways to build the Traficom IFIC analysis workflow

> [!NOTE]
> Five deliberately different architectures for the same brief, each written as a complete plan (requirements map, architecture, data ingestion, relevance rules, calculations, AI guardrails, evidence model, terrestrial side quest, deliverables, UI, stack, hour-by-hour build plan, risks, self-assessment, demo script). They exist so the team can pick one, or a hybrid, after the Friday briefing and the Saturday Q&A instead of arguing from scratch. Written on 6 Nov 2026 before any partner data from the Since AI platform was seen. The verified facts behind all five are in `00_shared_facts.md`; the official brief is in `00_challenge_brief_text.md`.

## Folder map

| File | What it is |
|---|---|
| `00_challenge_brief_text.md` | Verbatim text of the official PDF brief, for search and quotation |
| `00_shared_facts.md` | Evidence base: data formats, schema names, limits, formulas, tools, open questions; section 7a carries the facts verified on `main` |
| `01_deterministic_pipeline.md` | Deterministic Screening Pipeline: ETL, SQL views, rules and calculators; LLM only explains and drafts |
| `02_agentic_workflow.md` | Agentic Analyst Workflow: LLM agents that call deterministic tools and leave an evidence ledger |
| `03_knowledge_graph.md` | Spectrum Knowledge Graph: every source integrated into one typed graph with provenance; findings are graph queries |
| `04_itu_toolchain_wrapper.md` | ITU Toolchain Automation: the ITU's own Windows tools as the calculation engine, AI as the analyst layer |
| `05_geospatial_interference_twin.md` | Geospatial Interference Twin: pfd and field-strength rasters over a grid of Finland, map-first review |

## The five approaches at a glance

| # | Thesis | Where the computation lives | Where the AI lives | Primary artifact | Biggest risk |
|---|---|---|---|---|---|
| 01 Deterministic pipeline | Parse both IFIC databases, express every rule and calculation as tested code, re-run with one command | Python, DuckDB or SQLite views, numpy | Edges only: summaries, explanations, letter drafts grounded in computed facts | Reproducible run producing the 3074 and 3076 result files | Looks like a plain script unless prioritisation and output quality are excellent |
| 02 Agentic workflow | Specialist agents plan the analysis and call tools; every tool call is evidence | Inside tools (SQL, pfd, P.1546, M4 lookup, diff) | At the core: orchestration, reasoning, drafting; numbers only from tools | Replayable run transcript plus structured findings | Reproducibility and latency; a run that cannot be replayed loses criterion A |
| 03 Knowledge graph | Integrate administrations, networks, groups, Finnish allocations, stations and regulations into one graph with provenance edges | Graph queries and computed nodes | Extraction of regulation text into nodes, rendering why-chains to prose | Browsable graph with path-based evidence | Build time; a graph that only demonstrates a database |
| 04 ITU toolchain wrapper | Use SpaceQry, GIBC, SpaceCom and TerRaQ as the engine and automate around them | ITU Windows tools, outputs parsed | Triage, cross-comparison with M4, explanation, correspondence | Analysis package whose numbers come from the regulator's own tools | Windows-only GUI tools with no documented batch mode; `pm_pack/07` judges them not scriptable in 48 h |
| 05 Geospatial twin | Compute pfd and field strength on a grid over Finland and rank exceedances per cell and per protected station | Vectorised geometry and propagation per cell | Narration of exceedances and letter drafts | Interactive interference maps and exceedance tables | False precision and compute cost; worst-case assumptions must be labelled |

## How they differ

- **Determinism versus orchestration.** 01, 03 and 05 run a fixed program; 02 lets a model decide the order of steps within guardrails; 04 delegates the numbers to external software.
- **Data model.** 01 and 04 keep relational tables; 03 keeps a graph; 05 keeps rasters and station tables; 02 keeps whatever the tools return plus a ledger.
- **Calculation engine.** 01, 02, 03 and 05 implement pfd and P.1546 in Python (with `Py1546` where possible); 04 reads them from GIBC and the ITU tools and falls back to Python.
- **Centre of gravity of the UI.** 01 a ranked list with traces; 02 a transcript and findings; 03 a graph browser; 04 a memo per IFIC; 05 a map with a time slider across issues.

## Comparison against the evaluation criteria

Each plan carries its own self-assessment in section 15 (A 25, B 25, C 20, D 15, E 15). The index-level view, judged against `pm_pack/07_Solution_Catalogue.md` and the verified facts:

| Criterion | 01 | 02 | 03 | 04 | 05 |
|---|---|---|---|---|---|
| A technical analysis and reproducibility (25) | strong | medium, needs replay and temperature 0 | strong if computed nodes carry parameters | strongest if the tools run, weak if they do not | strong, as long as worst-case labels are kept |
| B extensibility and side quest (25) | strong: same stages, two adapters | strong: same agents, different toolset | strong: schema extension | medium: a second tool family to automate | strong: same grid, different propagation |
| C usefulness, innovation, output quality (20) | medium | strong | medium to strong | medium | strong |
| D case recognition accuracy (15) | strong | medium to strong | medium | strong if tools run | strong |
| E auditability and evidence (15) | strong | strong (ledger) | strongest (provenance by construction) | medium (tool outputs as black boxes) | medium to strong |

## Recommendation

Start with **01 Deterministic Screening Pipeline**. Four of the five criteria (80 percent of the score) reward deterministic, reproducible, accurate and auditable analysis, and the brief says outright that technical correctness, traceability and expert reviewability matter more than the choice of model. It also reuses the most of what already exists on `main`: the download scripts, the verified schema notes, the `scoring/` package and the data contracts in `pm_pack/06`.

Keep **05 Geospatial Interference Twin** as the pivot and as the demo layer: its per-cell pfd and field-strength rasters are the same calculations as 01, presented on a map, which is the strongest answer to criterion C and the most convincing two-minute video. If the pipeline is running by Saturday 09:00, the map is the Saturday afternoon differentiator.

Graft from the others:

- From 02: the evidence ledger (every tool call recorded with inputs, outputs and a hash) and the human checkpoint before any letter is finalised.
- From 03: why-chain explanations (notice, group, Finnish sub-band, regulation, calculation) rendered as a path, and the IFIC-to-IFIC diff as a comparison of two issue snapshots.
- From 04: a specialist-run GIBC report on one 3074 network as a golden test for the pfd calculator, and a SpaceCom-compatible comment as one of the correspondence outputs.

## Decision rules for Saturday

- If `mdbtools` reads `ific3074.mdb` and `brific3076.mdb` on Friday night: stay with 01. If it does not, ask the partner for CSV extracts (question Q13 in `pm_pack/01`) and keep 01 with a CSV adapter; 04 does not rescue this case because its tools need the same files on Windows.
- If a team member has a Windows laptop with the ITU tools installed and a specialist agrees to run GIBC on one network: use the output as a test for 01, not as the engine (04 in test-only form).
- If the special-interest XLS carries protection limits per station: 05's per-station comparison becomes the main ranking signal; if it carries only locations and antenna data, rank by pfd margin against Article 21 and distance.
- If the space specialists say Finland's relevance is decided mostly by the affected-administration lists in CR/C sections: raise rule R0 (Finland named in `provn`, `tr_aff_ntw`, `all_aff_ntw`) to the top of the ranking and report "named but no overlap" and "overlap but not named" as separate finding classes.
- If the terrestrial specialists confirm T/R 25-08 at the border line with 10 percent time and 10 m: 01's P.1546 engine is sufficient; if bilateral agreements override it for some bands, add rows to the framework table rather than code.
- If the partner forbids cloud models: every plan degrades to templates for explanations and drafts; 02 loses the most, 01 the least.

## Shared non-negotiables

Whatever the choice, the submission must contain: the Space IFIC 3074 and Terrestrial IFIC 3076 result files as separate files with one row per finding and the "evaluated, no concern" list; the cross-comparison with the M4 table from the Traficom API with row IDs cited; pfd and P.1546 calculations with every input, formula, limit and margin visible and labelled indicative until a specialist confirms the method; provenance on every finding (file, table, row, field, or regulation clause); human review before any correspondence leaves the tool; the same architecture demonstrated on terrestrial land-mobile notices including the diff of consecutive issues and a few trends or anomalies; no emoji and no playful copy on findings, decisions or exports.

## How to use these plans

1. Read `00_shared_facts.md` section 7a first; it lists what is verified and what is still a hypothesis.
2. Pick the plan after the Friday briefing (or default to 01) and copy its section 13 build plan into `pm_pack/05_Execution_Roadmap_and_Milestones.md`, replacing the sprint table.
3. Update `pm_pack/02_Requirements_Management_PRD.md` MoSCoW items from the plan's section 2 requirements map.
4. Record every Q&A answer in `00_shared_facts.md` (replace the `[HYPOTHESIS]` or `[GAP - ASK PARTNER]` tag with the answer and the specialist's name) and in the `[GAP]` tags of `pm_pack/06`.
5. Keep the other four plans: their sections 5 to 9 are reusable designs for the pivot and for the post-hackathon roadmap.
