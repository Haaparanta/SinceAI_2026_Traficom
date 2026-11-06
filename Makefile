# Filing Radar. Step IDs refer to pm_pack/08_Build_Plan_Step_by_Step.md.
.PHONY: doctor check-data checksums

doctor:        ## A1: tools on PATH, native arm64
	python3 scripts/doctor.py tools

check-data:    ## A2: graded databases, Finnish table, special-interest XLS
	python3 scripts/doctor.py data

checksums:     ## A2: every downloaded file against data/MANIFEST.sha256
	cd data && shasum -a 256 -c MANIFEST.sha256 | grep -v ': OK$$' || echo "all files OK"
