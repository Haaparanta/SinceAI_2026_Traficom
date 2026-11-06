# Filing Radar

Turns an ITU BR IFIC issue into a ranked, cited, expert-reviewable list of notices that may affect radio frequency use in Finland. Built for the Traficom challenge at Since AI 2026. The tool suggests; a specialist decides.

**Live demo:** https://filingradar.click (fallback https://filing-radar-ga6ca37kma-lz.a.run.app), hosted on Cloud Run in Finland and redeployed on every merge to `main`. See [docs/HOSTING.md](docs/HOSTING.md).

> [!NOTE]
> **Status on Fri 6 Nov 2026.** The space pipeline (Space IFIC 3074) and the terrestrial side quest (Terrestrial IFIC 3076) run end to end, the graded results files are in [`results/`](results/README.md), and the one-screen UI runs on the cached analyses. Every finding carries evidence that a script re-opens and checks. Reviewers approve, investigate or dismiss findings into a hash-chained audit log (D3). Each finding can be explained in plain language and turned into a letter draft to the notifying administration (D2): Claude writes them when credentials are present, a deterministic template otherwise, and a validator rejects any text that cites an evidence ID outside the finding or writes a number that is not in it. Still to come: demo packaging (E). All thresholds marked *hypothesis* wait for the partner's answers ([questions](pm_pack/01_Partner_Briefing_Questions.md)).

## What it finds

| Issue | Screened | Flagged | High | Medium | Review | Low | File |
|---|---|---|---|---|---|---|---|
| Space IFIC 3074 | 196 notices (25 105 frequency groups) | 135 | 21 | 99 | 1 | 14 | [`space_3074.csv`](results/space_3074.csv) |
| Terrestrial IFIC 3076 | 4 057 notices | 65 | 6 | 1 | 6 | 52 | [`terrestrial_3076.csv`](results/terrestrial_3076.csv) |

- **Space.** 16 notices where the Radiocommunication Bureau itself lists Finland as affected (RR 9.11, 9.14, 9.21, 11.31, AP30A); worst-case pfd above the RR Article 21 limit with a steerable beam for CHINASAT-H-60.5E (6.3 dB), CHINASAT-G-33.5E and INSAT; foreign networks with earth stations inside Finland (Tampere, Muonio).
- **Terrestrial.** New Russian VHF base stations above the ECC/ERC T/R 25-08 trigger at the Finnish border: Kostomuksha (13 dB over), Lyaskelya (9 dB), Vyborg (8 dB), with ITU-R P.1546-6 field strength. Russian 800 MHz base stations 12 to 14 km from Finland go to review (no T/R 25-08 criterion above 470 MHz).
- **Data quality.** One filing (IND network LVI) declares +73 dBW/Hz where its own peak power implies about -73: kept as filed, flagged, never used silently.

## Quick start

Needs macOS or Linux, Python 3.12 via [`uv`](https://docs.astral.sh/uv/), Node 20+, `mdbtools` and `duckdb` (`brew install mdbtools duckdb`).

```bash
uv sync                              # Python dependencies, including the pinned P.1546 reference code
npm --prefix frontend install        # the screen
make api                             # API on http://127.0.0.1:8000, serving data/cache/*.json
make frontend                        # the screen on http://127.0.0.1:5173
```

The screen runs from the committed `data/cache/` files; no database is needed to look at the results. To recompute everything from the ITU files:

```bash
scripts/fetch_data.sh                # graded issues, Regulation M4, Finnish frequency table into data/raw/ (git-ignored)
make doctor check-data checksums     # tools, files, SHA-256 against data/MANIFEST.sha256
make convert subbands                # .mdb -> DuckDB (about 25 s), Finnish table -> Parquet
make results ISSUE=3074              # results/space_3074.csv|json and the per-group detail
make results-terrestrial ISSUE=3076  # results/terrestrial_3076.csv|json
make cache                           # data/cache/*.json for the screen
make check-evidence ISSUE=3074       # re-open every citation; exit 1 on any mismatch
```

Explanations and letter drafts use Claude (`claude-opus-5-5`, with the server-side refusal fallback) when `ANTHROPIC_API_KEY` is set in `.env`; `LLM_MODEL` changes the model and `LLM_DISABLED=1` switches it off. Without a key the same buttons give a deterministic template built from the evidence, and the screen says which one you are reading. Accepted model texts are cached in `data/cache/llm/`, so a rerun or the demo makes no call.

The special-interest station table (XLS from the Since AI platform) goes to `data/raw/special_interest.xlsx` by hand; the station rule is built and waits for the file.

## How it works

```
issue number
  -> mdbtools + DuckDB          every table, typed from the Access schema, row counts checked     (A4, A5)
  -> schema_map.yaml            the only place ITU table and column names live                    (A4)
  -> adapters                   Notice / FrequencyGroup (space), TerrestrialNotice (terrestrial)   (B1, C2)
  -> relevance                  Hz overlap with the Finnish table, direction rules, Bureau list    (B2)
  -> geography                  GSO elevation, non-GSO reach, earth station and border distance   (B3, C3)
  -> calc                       worst-case pfd vs RR Art. 21 | ITU-R P.1546-6 vs T/R 25-08         (C1, C3)
  -> assemble + rank            Finding with Evidence and CalcTrace, concern rules, score         (B4)
  -> export, cache, API, UI     results/*.csv|json, data/cache/*.json, FastAPI, React             (B5, D1)
```

| Principle | How it is enforced |
|---|---|
| No finding without evidence | `Finding.evidence` has a minimum length of 1; [`radar.evidence_check`](backend/radar/evidence_check.py) re-opens all 6 001 citations of both issues (ITU rows, Finnish rows, RR and T/R 25-08 rows, recomputed pfd, geometry and P.1546) and requires an exact match |
| Unknown stays unknown | Missing values stay `None`; a gap in the Finnish table is "uncovered", never "no concern"; implausible filed values are flagged, not corrected |
| Deterministic first | Plain code with tests; two runs give byte-identical results files |
| Every number shows its working | `CalcTrace`: inputs with evidence IDs, formula, result, limit, margin, label `indicative` |
| The language model explains, it never decides | It sees only the finding and its evidence; output must cite IDs of that finding and contain no number missing from it, otherwise the template is shown with the reason; it never sets the concern; letters are drafts with a banner, edited and copied by a person, never sent |
| The tool suggests, a person decides | No automatic sending or dismissing; a reviewer approves, investigates or dismisses with a required note; the decision goes to an append-only, SHA-256-chained audit log (`data/decisions/`, git-ignored) and never changes the computed concern; the export carries the latest decision |

Methods and every parameter are listed in [`results/README.md`](results/README.md). Reference data with a source per row: [`pfd_limits.csv`](data/reference/pfd_limits.csv) (RR 2024 Table 21-4, 38 rows with page numbers), [`tr2508_thresholds.csv`](data/reference/tr2508_thresholds.csv), [`fi_reference_points.csv`](data/reference/fi_reference_points.csv).

## Proof that it works

| Check | Command | What it shows |
|---|---|---|
| Unit and data tests | `make test` | 257 Python tests: formulas against hand-worked values, golden cases, contracts, invariants on 3074 and 3076 |
| P.1546 engine | part of `make test` | the ITU validation suite (52 reference cases) reproduces to 0.0 dB |
| Evidence | `make check-evidence ISSUE=3074` | every citation re-opened; tamper tests prove a changed excerpt fails |
| Stage reports | `make index`, then open `reports/index.html` (or the `reports` entry in `.claude/launch.json`) | one HTML page per build step: counts in and out, charts, maps, ten random rows, PASS or FAIL |
| End-to-end UI | `make e2e` | Playwright drives the real screen and API in Chromium: both issues, all tabs, evidence links, filters, decisions and the audit chain, explanation and letter draft (no send button), export, dark and light, phone width |
| Explanations and letters | `make explanations ISSUE=3074` | 20 explanations beside their evidence, every cited ID and number green or red, a planted invented number rejected, no letter that says it was sent |
| Screenshots | `make screenshots STEP=d2` | the views a pull request changes, in `docs/screenshots/<step>/` |

## Repository

| Path | What |
|---|---|
| [`backend/radar/`](backend/radar/) | Pipeline: `adapters/`, `pipeline/`, `calc/`, `export/`, `models.py` (contracts), `schema_map.yaml`, `main.py` (API) |
| [`frontend/`](frontend/README.md) | The one screen (React, Vite, Tailwind v4, Girlypop tokens) and its Playwright tests |
| [`results/`](results/README.md) | The graded results files and their documentation |
| [`data/`](data/SOURCES.md) | `reference/` (committed, sourced), `cache/` (committed, for the screen), `raw/` and `derived/` (git-ignored) |
| [`scripts/`](scripts/) | Data download, conversion, cache, and one report script per build step |
| [`tests/`](tests/) | Python tests, golden cases, the vendored P.1546 validation suite |
| [`scoring/`](scoring/README.md) | The ranking model whose weights the pipeline uses |
| [`pm_pack/`](pm_pack/README.md) | Plan, requirements, risks, partner questions, agent context, [step-by-step build plan](pm_pack/08_Build_Plan_Step_by_Step.md) |
| [`docs/`](docs/README.md) | One page per document and external source |
| [`design/`](design/girlypop-theme.md) | Girlypop theme v2 |

## The challenge

Traficom asks for AI-assisted support to find the international filings that may affect Finland, explain why, and prepare the response, with experts in control of every decision. Full brief: [PDF](Since_AI_Traficom_Challenge_Brief_FINAL_04112026.pdf), [summary](docs/challenge-brief/README.md).

| Dataset | Mandatory | Used as | Notes |
|---|---|---|---|
| [ITU Space IFIC](https://www.itu.int/en/ITU-R/space/brific/Pages/default.aspx), issue 3074 graded | yes | `ific3074.mdb` | [notes](docs/links/itu-space-brific/README.md), [databases](docs/links/itu-space-ific-databases/README.md) |
| [ITU Terrestrial IFIC](https://www.itu.int/en/ITU-R/terrestrial/brific/Pages/default.aspx), issue 3076 graded | yes | `brific3076.mdb`, `brific3075.mdb` for the trend | [notes](docs/links/itu-terrestrial-brific/README.md) |
| [Regulation 4 (M4)](https://www.finlex.fi/fi/viranomaiset/maarayskokoelmat/traficom-viestinta/2026/3) and the [frequency table API](https://opendata.traficom.fi/api/v13/Taajuusjakotaulukko) | yes | 5 917 rows, snapshot 6 Nov 2026 | [M4](docs/links/finlex-regulation-m4/README.md), [API](docs/links/traficom-frequency-table-api/README.md) |
| Special-interest stations (XLS, Since AI platform) | yes | waiting for the file | |
| [ITU Radio Regulations 2024](https://www.itu.int/pub/r-reg-rr) | no | Article 21 Table 21-4 | [notes](docs/links/itu-radio-regulations/README.md) |
| ECC/ERC T/R 25-08, ITU-R P.1546-6 | no | terrestrial trigger and propagation | |
| [M15](https://www.finlex.fi/fi/viranomaiset/maarayskokoelmat/traficom-viestinta/2025/51209), [CEPT docdb](https://docdb.cept.org/implementation/overview), [ITU space software](https://www.itu.int/en/ITU-R/software/Pages/space-network-software.aspx) | no | not used yet | [M15](docs/links/finlex-regulation-m15/README.md), [CEPT](docs/links/cept-docdb-implementation/README.md), [software](docs/links/itu-space-software/README.md) |

## Credits

ITU-R P.1546-6 field strength: [Py1546](https://github.com/eeveetza/Py1546) by Ivica Stevanovic (OFCOM/BAKOM), the reference implementation approved by ITU-R Working Party 3K, pinned to commit `e2356290`. Borders: Natural Earth (public domain). Finnish frequency table: Traficom open data, CC BY 4.0.
