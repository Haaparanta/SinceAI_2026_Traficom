# Filing Radar. Step IDs refer to pm_pack/08_Build_Plan_Step_by_Step.md.
.PHONY: doctor check-data checksums schema convert subbands test api

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

test:          ## all unit tests
	uv run pytest -q

api:           ## local API on http://127.0.0.1:8000/docs
	uv run uvicorn radar.main:app --app-dir backend --reload
