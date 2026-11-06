# Filing Radar. Step IDs refer to pm_pack/08_Build_Plan_Step_by_Step.md.
.PHONY: doctor check-data checksums schema

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
