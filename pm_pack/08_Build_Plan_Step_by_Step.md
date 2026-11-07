# 08 — Build Plan, Step by Step (with visual proof)

How we build Filing Radar from an empty `backend/` to the two graded results files, one step at a time. Every step says what to do, what we should see, what we must not see, and which picture proves it worked.

> [!NOTE]
> **Grounding.** Written Fri 6 Nov 2026 after checking the machine and the data. Facts checked today `[CHECKED]`: the data download finished in the worktree `data-download-27f5bc` (1.0 GB in `data/raw/`, 69 entries) and already holds the extracted `ific3074/ific3074.mdb` (287 MB), `brific3075/brific3075.mdb` (33 MB) and `brific3076/brific3076.mdb` (25 MB). The terrestrial extracts are Access `.mdb` files, not SQLite `.db3`, so solution plan 01 section 4 is wrong on that point and both sides use the same reader. `special_interest.xlsx` is **not** downloaded yet. On this Mac: `uv`, Python, Node, `sqlite3`, `gh` and Homebrew are installed; `mdbtools` and `duckdb` are **missing**. The Mac is a MacBook Pro M1, 8 cores, 8 GB RAM, 80 GB free.
> Everything else follows `06_AGENTS_Master_Context.md` (contracts, folders, owners) and `05_Execution_Roadmap_and_Milestones.md` (gates and times). Tags as in the rest of the pack.

---

## Status (Fri 6 Nov 2026, late evening)

| Step | State | Proof | PR |
|---|---|---|---|
| A1, A2 tools and data | done | `make doctor check-data checksums` | #16 |
| A3 special-interest XLS | done 7 Nov 2026; `Traficom_SinceAI_Frequencies_of_interest_v05112026.xlsx`: 874 rows, 870 stations, 4 excluded with reasons, 131 flagged; read by `adapters/special_interest.py` | `make special-interest`, `reports/reference/special_interest.html` | #40 |
| A3+ stations in the space screening | done 7 Nov 2026; protected RX channel joined with every group, reach from each station's own position, pfd also at matched stations, station floor after the pfd rules; 52 notices cite stations, no concern change in 3074 | `reports/3074/04_findings.html`, `docs/screenshots/stations/` | #43 |
| A3+ stations in the terrestrial screening | done 7 Nov 2026; P.1546 at every co-channel station within 1 000 km at its antenna height; concern = worse of border and station; 24 notices in 3076 have stations, none decides | `reports/3076/02_field_strength.html`, `docs/screenshots/terrestrial-stations/` | #45 |
| Overview charts | done 7 Nov 2026; Overview tab: geostationary arc seen from Finland with the flagged GSO filings (space), flagged foreign stations and the special-interest stations they reach (terrestrial), flagged findings across the spectrum by concern (both); every mark opens its finding | `make e2e` (e2e/overview.spec.ts), `docs/screenshots/overview/` | this PR |
| A4 schema | done; all expected tables found | `reports/schema/*.html` | #17 |
| A5 DuckDB, A6 Finnish table | done; row counts match, 5 917 rows | `reports/convert/*.html`, `reports/reference/fi_subbands.html` | #18 |
| B1 to B5 space 3074 | done; 196 notices, 135 flagged, results files written | `reports/3074/01-05_*.html`, `results/space_3074.*` | #19 to #23 |
| C1 worst-case pfd | done; limits re-transcribed from RR 2024, second check against an independent transcription on 7 Nov 2026 (38 of 38 agree); signed off by Claude at the project owner's request | `reports/3074/06_pfd.html` | #24 |
| C2 terrestrial diff | done; each extract is a change set | `reports/3076/01_diff.html` | #25 |
| C3 P.1546 at the border | done; ITU reference code, 52 validation cases at 0.0 dB | `reports/3076/02_field_strength.html`, `results/terrestrial_3076.*` | #26 |
| D1 one screen | done (built by Claude Code at the user's request; file 06 gives `frontend/` to Cursor) | `make frontend`, Playwright `make e2e` | #27, #28 |
| D2 explanation and letter | done; Claude (claude-opus-5-5, refusal fallback on) when credentials exist, else a grounded template; validator rejects unknown IDs and new numbers; letters are drafts, never sent | `make explanations`, `reports/3074/07_explanations.html`, `docs/screenshots/d2/` | #31 |
| D3 decisions and audit log | done; append-only log with a SHA-256 chain, export carries the decision, concern never changes | `make e2e`, `docs/screenshots/d3/` | #29 |
| E1 to E4 freeze | done; two full runs identical to git (E1); 10 of 10 golden cases and 220 of 220 Bureau-named groups, which found and fixed SECOMSAT-5-78E (E2); demo mode offline with no external request (E3); proof pack in `results/proof/` (E4) | `make freeze`, `make status`, `results/proof/index.html` | this PR |
| E5 video and submission | run-sheet checked against the screen (file 05, section 5); recording and submission are for the team | | |

Facts the real files changed (also recorded in file 06 and `backend/radar/schema_map.yaml`):

- The terrestrial extracts are Access `.mdb`, not SQLite, and each is the **change set** of its issue: the diff uses the Bureau's intent (ADD, MODIFY, SUPPRESS, RECORDED), the comparison with the previous issue is a trend.
- `grp.wic_no` marks the issue that published a group (25 105 of 34 365 groups in 3074); `grp.emi_rcp` flips meaning for earth-station notices.
- `e_as_stn` links through `grp_id`; `site_alt` is in `fxm_geo`.
- `provn.adm = 'FIN'` is the Bureau's own list of notices affecting Finland (16 in 3074), the strongest relevance signal.
- The IFIC database has no beam boresight or gain contours: pfd exceedances count as high only for steerable beams.
- Mariehamn was added to the reference points (westernmost point decides visibility of western GSO satellites).
- Solution plan 01 had a 36 dB slip in its pfd example (corrected in C1).

## 0. How to read this plan

Each step has the same five parts:

| Part | Meaning |
|---|---|
| **Do** | The commands or the code to write, and who owns it (BE, AI, FE, PM as in file 06) |
| **Should see** | The output that means the step worked. Numbers we do not know yet are written as "a count", never guessed |
| **Must not see** | Red flags. If one appears, stop and fix before the next step |
| **Visual proof** | The picture we open to check it with our own eyes, and that we keep for the demo |
| **Done when** | A check that a script can run (`make check-<step>`), so "done" is not an opinion |

A step is finished only when its check passes and its proof file exists. One step is one branch (`feat/<area>-<thing>`) and one pull request.

---

## 1. Hardware: what the M1 can and cannot do

Nothing in this project needs a GPU or a cloud server. The biggest file is the 287 MB Space database; converted to DuckDB and Parquet it is a few hundred MB on disk and fits in memory many times over. The language model runs on Anthropic's servers through the API.

| Work | Where it runs | Why it is fine on 8 GB |
|---|---|---|
| `.mdb` to CSV to DuckDB | Laptop | Streams one table at a time; set DuckDB `memory_limit = '3GB'` and `threads = 4` so the browser and editor stay responsive |
| Screening, geometry, pfd, P.1546 | Laptop | Interval joins and arithmetic on tens of thousands of rows; seconds, not minutes |
| Maps and charts | Laptop browser | Finland GeoJSON is small; we draw dozens of points, not millions |
| Explanations and letters | Anthropic API (cloud) | Only text goes out; cached results mean the demo runs offline |
| Fallback conversion if `mdbtools` fails | A Linux GitHub Codespace or a teammate's Windows laptop with Access | Only needed for rung 2 of the data ladder in file 04 |

**Rules for the laptop.** Close Docker if it is running (it reserves memory). Never load a whole `.mdb` export into pandas at once; let DuckDB read the CSV. Run long conversions in the background and keep working. Keep only 3074, 3075 and 3076 extracted; leave the other zips zipped.

---

## 2. Visual debugging toolkit

We use four kinds of picture, from raw data up to the finished product. Each one answers a different "is this right?" question.

| Tool | Answers | How to open |
|---|---|---|
| **DuckDB UI** (raw and derived tables) | "What is actually in this table, row by row?" | `duckdb -ui data/derived/space_3074.duckdb` opens a SQL notebook in the browser. Fallback: `uvx datasette data/derived/space_3074.sqlite` |
| **Stage reports** (one HTML page per pipeline step) | "Did this step do what it should, in bulk?" Counts, missing values, histograms, a funnel, ten random rows | `make report STEP=ingest ISSUE=3074` writes `reports/3074/01_ingest.html`; open it in the browser pane |
| **Evidence resolver** | "Does every citation point at a real row with the same value?" | `make check-evidence ISSUE=3074` re-opens every `Evidence.locator` in DuckDB or the Traficom cache and compares the `excerpt`; it prints a table and fails on any mismatch |
| **The product screen** | "Would an expert trust this finding?" | `make run`, then the Spectrum, Map and Calculation tabs |

**Stage reports are the core of the visual proof.** They are plain HTML (one file, no server), generated by `scripts/stage_report.py` from a small JSON summary that each stage writes next to its output. The tests read the same JSON, so the picture and the test can never disagree. `reports/` is git-ignored while we work; at Gate 4 the final reports for 3074 and 3076 are copied to `results/proof/` and committed as part of the submission.

Every stage report has the same four blocks:

1. **Counts in and out**: rows read, rows kept, rows dropped, with the reason for every drop.
2. **Field health**: for each field we use, the share of rows where it is missing and its minimum and maximum, with the expected range shown next to it in red if outside.
3. **One chart** that fits the stage (listed per step below).
4. **Ten random rows and the five extremes**, each with its source locator, so a person can check them by hand.

---

## 3. The steps

Times refer to the sprints and gates in file 05. Owners follow the agent table in file 06.

### Phase A — Workstation and data (Sprint 1, before Gate 1)

#### Step A1. Install the missing tools · BE · 15 min

**Do**
```bash
brew install mdbtools duckdb
uv --version && node --version && mdb-ver --help >/dev/null && duckdb --version
```

**Should see** version lines for `uv`, `node`, `duckdb`; `mdb-ver` runs without "command not found".

**Must not see** a Rosetta or x86 warning from Homebrew (it should be the arm64 build under `/opt/homebrew`).

**Visual proof** none needed; the next step proves it.

**Done when** `make doctor` (a 10-line script) prints PASS for each tool.

#### Step A2. Point this worktree at the downloaded data · BE · 10 min

The data already exists in the worktree `data-download-27f5bc`. Do not download 1 GB again. Move it to one shared place outside every worktree and link to it, so every branch sees the same files.

**Do**
```bash
mkdir -p ~/Desktop/SinceAI_2026_Traficom/_data
mv ~/Desktop/SinceAI_2026_Traficom/.claude/worktrees/data-download-27f5bc/data/raw ~/Desktop/SinceAI_2026_Traficom/_data/raw
ln -s ~/Desktop/SinceAI_2026_Traficom/_data/raw data/raw
cd data && shasum -a 256 -c MANIFEST.sha256 | grep -v ': OK' ; cd ..
```
Add `data/raw` (without the trailing slash) to `.gitignore` in the same commit: the current pattern `data/raw/` matches only real folders, so git would try to commit the symlink.

**Should see** no output from the checksum line (every file OK); `git status` clean.

**Must not see** `FAILED` lines; `data/raw` listed by `git status`.

**Done when** `make check-data` confirms the three `.mdb` files exist with the sizes above and `taajuusjakotaulukko.json` parses.

#### Step A3. Fetch the special-interest XLS · PM · 10 min

**Do** log in to the Since AI platform, download the synthetic table, save it as `data/raw/special_interest.xlsx`.

**Should see** a sheet with station number, centre frequency, bandwidth, coordinates, antenna height, direction and directivity `[SOURCE DATA: brief 05]`.

**Must not see** a file that needs macros, or coordinates in a format we have never seen (write the format down for Q4).

**Visual proof** a screenshot of the first rows pasted into the team channel, so BE knows the real column names.

#### Step A4. Read the real schema · BE · 30 min, runs in the background

**Do**
```bash
python3 scripts/inspect_mdb.py data/raw/ific3074/ific3074.mdb   --out data/derived/schema_3074.json
python3 scripts/inspect_mdb.py data/raw/brific3076/brific3076.mdb --out data/derived/schema_3076.json
python3 scripts/inspect_mdb.py data/raw/brific3075/brific3075.mdb --out data/derived/schema_3075.json
```
Then fill `backend/radar/schema_map.yaml` from what was printed, table by table, and mark every name we expected but did not find.

**Should see** the tables named in file 06 (`notice`, `grp`, `emiss`, `s_beam`, `srv_area`, `geo`, `non_geo`, `orbit`, `pub_ssn`, ... for space; `fxm_*` tables for terrestrial), each with a row count above zero.

**Must not see** zero tables (mdbtools cannot read the file: go to rung 2 of the data ladder in file 04); a large table with 0 rows; column names that are numbers or empty (a broken header).

**Visual proof** `reports/schema/schema_3074.html`: one row per table with its row count and columns, expected tables highlighted green when found and red when missing.

**Done when** `schema_map.yaml` has an entry for every table in file 06, each either mapped or marked `missing`.

#### Step A5. Convert to DuckDB · BE · 45 min

**Do** `scripts/mdb_to_duckdb.py` exports each table with `mdb-export -D '%Y-%m-%d' -b strip` to a temporary CSV and loads it with `read_csv` into `data/derived/space_3074.duckdb` (and `terrestrial_3075.duckdb`, `terrestrial_3076.duckdb`). Keep the original table and column names; renaming happens later through `schema_map.yaml`.

**Should see** the same row count per table in DuckDB as in `schema_3074.json`.

**Must not see** a row-count mismatch (quoting or line-break problems in a text field); dates as numbers; frequencies stored as text.

**Visual proof** open `duckdb -ui data/derived/space_3074.duckdb` and run `SELECT * FROM notice LIMIT 20` and `SUMMARIZE grp`. Screenshot `SUMMARIZE grp` for the team.

**Done when** `make check-convert` compares row counts table by table and prints PASS.

#### Step A6. Finnish frequency table · AI · 30 min

**Do** `adapters/traficom_table.py` reads `data/raw/taajuusjakotaulukko.json` into `FinnishSubBand` rows (Hz integers) and writes `data/derived/fi_subbands.parquet`. Expose `GET /reference/subbands?hz=`.

**Should see** 5 917 rows `[SOURCE DATA]`; every row with `lower_hz < upper_hz`; the rows covering about 9 kHz to 3 000 GHz without large holes.

**Must not see** negative or zero widths; frequencies that look like MHz where Hz was expected (values under 10 000 for an upper limit); duplicate IDs.

**Visual proof** `reports/reference/fi_subbands.html` with a **spectrum strip**: a horizontal log-scale bar from 9 kHz to 300 GHz, one coloured segment per sub-band, gaps in red. Click three random segments and compare them by eye with the Traficom web version of the table.

**Done when** the API returns rows for 11 GHz and the gap list is empty or explained.

**Gate 1 (Fri 23:30)** = A1 to A6 PASS. The UI skeleton (FE) runs in parallel from file 05.

---

### Phase B — Space end to end on 3074 (Sprint 2, before Gate 2)

#### Step B1. Normalise notices and frequency groups · BE · 2 h

**Do** `adapters/space_ific.py` builds `Notice` and `FrequencyGroup` objects from DuckDB through `schema_map.yaml`: MHz to Hz integers, `emi_rcp` E/R to `space_to_earth`/`earth_to_space`, orbit type from `ntc_type`, special section from `pub_ssn`. Missing values stay `None`.

**Should see** one `Notice` per row of `notice` that belongs to this issue; group counts equal to `grp`; every object with a `source_ref` such as `grp.grp_id=1234`.

**Must not see** a group with `freq_min_hz > freq_max_hz`; frequencies below 1 MHz or above 300 GHz for a space group (unit error); direction `unknown` for more than a small share; a value filled in where the database had nothing.

**Visual proof** `reports/3074/01_ingest.html`: counts by special section (API/A, CR/C, ...) and by administration, a histogram of group frequencies on a log axis (expect peaks near the usual satellite bands such as C, Ku and Ka), the null share for power density and gain (these drive the pfd later, so we need to know early how many are missing).

**Done when** `make check-ingest ISSUE=3074` passes and the null shares are written into the report.

#### Step B2. Frequency relevance · AI · 2 h

**Do** `pipeline/relevance.py`: interval join of groups against Finnish sub-bands and special-interest stations, overlap in Hz, direction rules from file 06.

**Should see** a **funnel**: all groups, groups overlapping any Finnish sub-band, groups that pass the direction rule, groups hitting a special-interest station.

**Must not see** almost every group kept (the join ignores the direction or the bounds), or none kept (units wrong on one side); an overlap larger than the group width.

**Visual proof** `reports/3074/02_relevance.html`: the funnel chart, and for five random kept groups and five random dropped groups the spectrum strip zoomed to the group with the Finnish sub-bands under it. A person reads the ten pictures and agrees or disagrees with each.

**Done when** the ten hand checks are written into `tests/golden/space_3074.yaml` as expected outcomes and pass.

#### Step B3. Geography · AI · 1.5 h

**Do** `pipeline/geography.py` with the GSO formula in file 06 for the six points in `data/reference/fi_reference_points.csv`; non-GSO by inclination and service area.

**Should see** test vectors pass: a satellite on the meridian of a site at 60 N gives about 22 degrees elevation, at 70 N about 11.5 degrees, and a satellite more than about 72 degrees of longitude away from a site at 60 N is below the horizon (about 64 degrees at 70 N). Slant ranges between 35 786 km and about 41 700 km.

**Must not see** elevation above 23 degrees from anywhere in Finland (impossible for GSO at these latitudes); sign errors that make West longitudes visible from the wrong side.

**Visual proof** `reports/3074/03_geography.html`: a chart of nominal longitude (x) against lowest Finnish elevation (y), one dot per GSO notice, with the 0 and 10 degree lines drawn. Expected shape: a hump peaking near 11 degrees above about 27 E (Utsjoki is the lowest point) and crossing zero about 64 degrees either side; a second line for the highest elevation (Hanko) peaks near 22 degrees and crosses zero about 72 degrees either side. Plus a small Finland map with the six points.

**Done when** `uv run pytest tests/test_geometry.py` passes and the hump looks right.

#### Step B4. Assemble findings, evidence and ranking · AI · 2 h

**Do** `pipeline/assemble.py` builds `Finding` objects with `Evidence` items; `pipeline/rank.py` sets the concern level, reusing the `scoring/` package. `reason` is a template sentence, no language model yet.

**Should see** every finding with at least one evidence item (the Pydantic rule enforces it); provenance coverage 100 %; a few High, more Medium, many Low.

**Must not see** all findings at one level; a finding citing an evidence ID it does not contain; the word "unknown" replaced by a number anywhere.

**Visual proof** `reports/3074/04_findings.html`: a bar per concern level, the top 20 table, and the evidence resolver result. Run `make check-evidence ISSUE=3074`: every locator reopened, every excerpt equal.

**Done when** both checks pass.

#### Step B5. Results file · BE · 1 h

**Do** `python -m radar.export --issue 3074 --kind space` writes `results/space_3074.csv` and `.json` (`ResultRow`).

**Should see** one row per screened notice or group, the same totals as the funnel, and the concern counts equal to the bars in B4.

**Must not see** a count that differs between the report, the screen and the file; numbers with no unit column.

**Visual proof** the CSV opened in the DuckDB UI, sorted by concern and margin.

**Gate 2 (Sat 09:00)** = B1 to B5 PASS, three samples chosen from real rows, shown to the partner. Ask Q1, Q3, Q4, Q5.

---

### Phase C — Calculations (Sprint 3 and 4)

#### Step C1. Worst-case pfd for GSO downlinks · AI · 3 h

**Do** `calc/pfd.py` and `calc/trace.py` with the formula in file 06, limits from `data/reference/pfd_limits.csv` (seeded from `scoring/reference/rr_article21_table21-4.json`, each row with its source and a `verified` flag). Validate inputs and limits at the space specialist slot (Sat 10 to 11, Q2, Q7, Q8).

**Should see** a hand-worked example in `tests/test_pfd.py` reproduced to 0.1 dB; computed pfd values in the range of roughly −180 to −100 dBW/m² in the reference bandwidth; the spreading term near 162.6 dB at 38 000 km.

**Must not see** pfd values above −80 or below −250 dBW/m² (unit or bandwidth error); a margin with no limit row; a result without the label `indicative`.

**Visual proof** `reports/3074/05_pfd.html`: histogram of margins with zero marked, the ten worst cases with their full `CalcTrace` (inputs with evidence IDs, formula, result, limit, margin), and the share of groups where power or gain was missing.

**Done when** the unit test passes and the specialist has seen one trace.

#### Step C2. Terrestrial diff 3075 to 3076 · BE · 2 h

**Do** `adapters/terrestrial_ific.py` and `pipeline/diff.py`: use the notice intent field (ADD, MODIFY, SUPPRESS, WITHDRAW) where it exists, otherwise match by key and compare fields.

**Should see** counts of new, modified and withdrawn per administration; neighbours (S, NOR, EST, RUS) listed first.

**Must not see** every notice classed as new (the key is wrong), or the counts not adding up to the totals of both issues.

**Visual proof** `reports/3076/01_diff.html`: a stacked bar per administration and a map with new stations green, modified amber, withdrawn grey, and the Finnish border drawn.

#### Step C3. Border distance and P.1546 · AI · 3 h

**Do** `pipeline/geography.py` (distance to the Finland polygon, path type) and `calc/p1546.py` (reference implementation if it installs in an hour, otherwise curve interpolation with `tests/p1546_vectors.md`). Thresholds from `tr2508_thresholds.csv` with the bandwidth correction. Validate at the terrestrial slot (Sat 11 to 12 and 16 to 17, Q11, Q12).

**Should see** field strength falling with distance; a station at the border far above the trigger, one 300 km away far below.

**Must not see** field strength rising with distance; distances of zero for stations clearly outside Finland.

**Visual proof** `reports/3076/02_field_strength.html`: the P.1546 curve we use plotted against distance for one frequency with our test vectors as dots; a map with a line from each flagged station to its nearest border point, labelled with distance and margin.

**Done when** the test vectors pass and `results/terrestrial_3076.csv` is written.

**Gate 3 (Sat 16:00)** = C1 to C3 PASS, a pfd trace and a field-strength trace on screen.

---

### Phase D — The product (Sprint 5 and 6)

#### Step D1. One screen wired to real data · FE · runs from Sprint 1

**Should see** the screen in file 02 section 2; Spectrum, Map and Calculation tabs change when a finding is selected; every number on screen also exists in the stage report or results file.

**Must not see** a literal number typed into the UI; a risk badge without a text label; emoji.

**Visual proof** screenshots of the three tabs for each of the three samples, taken with the browser pane, saved in `results/proof/screens/`.

#### Step D2. Grounded explanation and letter · AI · 3 h

**Do** `llm/explain.py`, `llm/letter.py`, prompts in `prompts/`, validator as in file 06.

**Should see** explanations that cite only evidence IDs of their finding and contain no number missing from the inputs; `LLM_DISABLED=1` still runs the whole pipeline.

**Must not see** a new number in the text; a letter that says it was sent.

**Visual proof** `reports/3074/07_explanations.html` (06 is the pfd report): for 20 findings the explanation beside the evidence table, with every cited ID and every number highlighted green when it matches and red when it does not.

#### Step D3. Decisions and audit log · FE and BE · 1.5 h

**Should see** approve, dismiss and investigate each write a line with reviewer, note and time; the results file shows the decision column.

**Must not see** a decision that changes the concern level computed by the pipeline.

---

### Phase E — Freeze and ship (Sprint 7 and 8)

| Step | Do | Proof |
|---|---|---|
| E1 Determinism | Run the whole 3074 and 3076 pipeline twice; `diff` the CSVs | Empty diff, shown in the video |
| E2 Golden cases | `scoring/evaluate.py` on `tests/golden/*.yaml`, updated with every specialist answer | Precision and recall table in `results/proof/` |
| E3 Demo cache | `scripts/build_cache.py` builds `data/cache/sample_1..3.json`, validated against `AnalysisResult` | UI in demo mode with Wi-Fi off |
| E4 Proof pack | Copy the final stage reports to `results/proof/`, write `results/README.md` (inputs, parameters, assumptions) | One index page linking every report |
| E5 Video and submission | Run-sheet in file 05 section 5 | Video under 2:00 |

**Gate 4 (Sun 02:00)** = E1 to E4. **Gate 5 (Sun 08:00)** = E5.

---

## 4. The check runner

One command shows where we are, so nobody has to ask:

```bash
make status
```

It runs every `check-*` target that has its inputs available and prints one line per step: PASS, FAIL with the first failing assertion, or WAITING with the missing input (for example `A3 special_interest.xlsx WAITING: file not found`). It also writes `reports/index.html` linking every stage report that exists. Open that page in the browser pane at every stand-up.

---

## 5. What we build first, in order

1. A1 and A2 now (tools and data link): 25 minutes, unblocks everything.
2. A4 in the background while writing `scripts/stage_report.py` and `make status` (the debugging tools are built before the pipeline, so every later step gets its picture for free).
3. A5 and A6, then Gate 1.
4. Phase B in order; FE builds the screen against `data/cache/` in parallel.

The special-interest XLS (A3) is the only step a person must do by hand; ask the PM to do it first.

---

## 6. Open points this plan depends on

| Point | Affects | Resolved by |
|---|---|---|
| mdbtools reads Version 10 `.mdb` files `[HYPOTHESIS]` | A4, A5 | Running A4; fallback ladder in file 04 |
| Real XLS columns `[GAP: Q4]` | A3, B2 | Opening the file |
| Relevance rule `[GAP: Q1]` | B2, B4 | Sat 09:00 stand |
| pfd limits and method `[GAP: Q2]` | C1 | Space slot Sat 10 to 11 |
| P.1546 and T/R 25-08 parameters `[GAP: Q12]` | C3 | Terrestrial slots Sat 11 to 12, 16 to 17 |
| Results file format `[GAP: Q3]` | B5, C3 | Before Gate 4 |
