# Filing Radar. Step IDs refer to pm_pack/08_Build_Plan_Step_by_Step.md.
.PHONY: doctor check-data checksums schema convert subbands ingest relevance geography findings check-evidence results pfd test api

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

test:          ## all unit tests
	uv run pytest -q

api:           ## local API on http://127.0.0.1:8000/docs
	uv run uvicorn radar.main:app --app-dir backend --reload
