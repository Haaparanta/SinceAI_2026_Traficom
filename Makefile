# Filing Radar. Step IDs refer to pm_pack/08_Build_Plan_Step_by_Step.md.
.PHONY: doctor check-data checksums schema convert convert-plans plans subbands special-interest ingest relevance geography findings check-evidence results pfd diff field-strength results-terrestrial explanations determinism golden proof freeze status api-demo index cache frontend frontend-build e2e screenshots test api

doctor:        ## A1: tools on PATH, native arm64
	python3 scripts/doctor.py tools

check-data:    ## A2: graded databases, Finnish table, special-interest XLS
	python3 scripts/doctor.py data

checksums:     ## A2: every downloaded file against data/MANIFEST.sha256
	cd data && shasum -a 256 -c MANIFEST.sha256 | grep -v ': OK$$' || echo "all files OK"

schema:        ## A4: real tables and columns of each database, plus the HTML report
	python3 -I scripts/inspect_mdb.py data/raw/ific3074/ific3074.mdb --out data/derived/schema_ific3074.json > data/derived/schema_ific3074.txt
	python3 -I scripts/inspect_mdb.py data/raw/brific3075/brific3075.mdb --out data/derived/schema_brific3075.json > data/derived/schema_brific3075.txt
	python3 -I scripts/inspect_mdb.py data/raw/brific3076/brific3076.mdb --out data/derived/schema_brific3076.json > data/derived/schema_brific3076.txt
	python3 -I scripts/schema_report.py data/derived/schema_ific3074.json --kind space --out reports/schema/schema_ific3074.html
	python3 -I scripts/schema_report.py data/derived/schema_brific3075.json --kind terrestrial --out reports/schema/schema_brific3075.html
	python3 -I scripts/schema_report.py data/derived/schema_brific3076.json --kind terrestrial --out reports/schema/schema_brific3076.html

convert:       ## A5: .mdb -> DuckDB with row-count check and report (about 25 s in total)
	uv run python scripts/mdb_to_duckdb.py data/raw/ific3074/ific3074.mdb data/derived/space_3074.duckdb
	uv run python scripts/mdb_to_duckdb.py data/raw/brific3075/brific3075.mdb data/derived/terrestrial_3075.duckdb
	uv run python scripts/mdb_to_duckdb.py data/raw/brific3076/brific3076.mdb data/derived/terrestrial_3076.duckdb

PLAN ?= $(shell ls -d data/raw/30B_*/ 2>/dev/null | grep -oE '[0-9]{4}/$$' | tr -d / | sort -n | tail -1)

convert-plans: ## AP30/30A and AP30B plan databases -> DuckDB (latest snapshot in data/raw, about 90 s); make convert-plans PLAN=3083
	uv run python scripts/mdb_to_duckdb.py data/raw/SPS_ALL_IFIC$(PLAN)/SPS_ALL_IFIC$(PLAN).mdb data/derived/ap30_$(PLAN).duckdb
	uv run python scripts/mdb_to_duckdb.py data/raw/30B_$(PLAN)/30B_$(PLAN).mdb data/derived/ap30b_$(PLAN).duckdb

plans:         ## C1b: Finnish AP30/30A/30B plan entries against $(ISSUE), report reports/$(ISSUE)/08_plans.html
	PYTHONPATH=backend uv run python -m radar.adapters.plans $(ISSUE)
	uv run python scripts/plans_report.py $(ISSUE)

subbands:      ## A6: Finnish table -> Parquet, spectrum strip report
	PYTHONPATH=backend uv run python -m radar.adapters.traficom_table
	uv run python scripts/subbands_report.py

ISSUE ?= 3074

ingest:        ## B1: space notices and groups, report reports/$(ISSUE)/01_ingest.html (fails on unflagged red flags)
	uv run python scripts/ingest_report.py $(ISSUE)

relevance:     ## B2: frequency relevance, report reports/$(ISSUE)/02_relevance.html
	uv run python scripts/relevance_report.py $(ISSUE)

geography:     ## B3: GSO elevation, NGSO coverage, earth stations, report reports/$(ISSUE)/03_geography.html
	uv run python scripts/geography_report.py $(ISSUE)

findings:      ## B4: ranked findings with evidence, report reports/$(ISSUE)/04_findings.html
	uv run python scripts/findings_report.py $(ISSUE)

check-evidence: ## B4: reopen every citation of data/derived/findings_space_$(ISSUE).json
	PYTHONPATH=backend:. uv run python -m radar.evidence_check $(ISSUE)

results:       ## B5: results/space_$(ISSUE).csv|json + groups detail, reconciliation reports/$(ISSUE)/05_results.html
	PYTHONPATH=backend:. uv run python -m radar.export --issue $(ISSUE) --kind space
	uv run python scripts/results_report.py $(ISSUE)

pfd:           ## C1: worst-case pfd report reports/$(ISSUE)/06_pfd.html
	uv run python scripts/pfd_report.py $(ISSUE)

PREV ?= 3075

diff:          ## C2: terrestrial change set and trend, report reports/$(ISSUE)/01_diff.html (make diff ISSUE=3076)
	uv run python scripts/diff_report.py $(ISSUE) $(PREV)

field-strength: ## C3: P.1546 at the border, report reports/$(ISSUE)/02_field_strength.html (make field-strength ISSUE=3076)
	uv run python scripts/field_strength_report.py $(ISSUE)

results-terrestrial: ## C3: results/terrestrial_$(ISSUE).csv|json
	PYTHONPATH=backend:. uv run python -m radar.export --issue $(ISSUE) --kind terrestrial

special-interest: ## A3: read data/raw/special_interest.xlsx, report reports/reference/special_interest.html
	uv run python scripts/special_interest_report.py

explanations:  ## D2: grounded explanations and letters for 20 findings, report reports/$(ISSUE)/07_explanations.html
	uv run python scripts/explanations_report.py $(ISSUE)

determinism:   ## E1: run the whole 3074 and 3076 pipeline twice; every output identical and equal to git, reports/freeze/e1_determinism.html
	uv run python scripts/determinism_check.py

golden:        ## E2: precision and recall by label source, reports/freeze/e2_golden.html and results/proof/accuracy.csv
	uv run python scripts/golden_report.py

proof:         ## E4: copy every stage report into results/proof/ with an index page (committed)
	uv run python scripts/proof_pack.py

freeze:        ## E1 to E4 in one go: determinism, accuracy, e2e (incl. the offline demo), proof pack
	$(MAKE) determinism golden e2e index proof

status:        ## one line per build step: PASS, FAIL or WAITING (pm_pack/08 section 4); also rebuilds reports/index.html
	uv run python scripts/status.py

index:         ## reports/index.html: every stage report with its status
	uv run python scripts/reports_index.py

cache:         ## D1: data/cache/space_3074.json and terrestrial_3076.json for the screen (about 20 s)
	uv run python scripts/build_cache.py

frontend:      ## D1: the one screen on http://127.0.0.1:5173 (run make api in another terminal)
	npm --prefix frontend run dev

frontend-build: ## D1: type-check, lint and build the screen
	npm --prefix frontend run build && npx --prefix frontend eslint frontend/src

e2e:           ## D1: Playwright end-to-end tests of the screen (starts API and dev server if needed); report in reports/playwright/
	npm --prefix frontend run e2e

STEP ?= e

screenshots:   ## PR pictures: Playwright captures the changed views into docs/screenshots/$(STEP)/ (one run per project)
	for p in desktop-light desktop-dark phone; do SCREENSHOTS=$(STEP) npm --prefix frontend run e2e -- screenshots --project $$p || exit 1; done

test:          ## all unit tests
	uv run pytest -q

api-demo:      ## E3: the API in demo mode: cached analyses only, no network and no language-model calls
	DEMO_MODE=1 $(MAKE) api

api:           ## local API on http://127.0.0.1:8000/docs
	uv run uvicorn radar.main:app --app-dir backend --reload
