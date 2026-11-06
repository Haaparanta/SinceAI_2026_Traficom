#!/usr/bin/env bash
# Quick start: fetch only the graded issues (Space IFIC 3074, Terrestrial IFIC 3076 plus 3075 for the diff),
# the M4 regulation and the Finnish frequency table into data/raw/ (git-ignored), about 75 MB, and extract the
# three databases to data/raw/ific3074/, data/raw/brific3076/ and data/raw/brific3075/.
# For every 2026 issue and the optional sources (M15, Radio Regulations, CEPT exports, station registers)
# run scripts/download_data.sh instead. Sources, sizes and layout: data/SOURCES.md.
set -euo pipefail
export SPACE_IFICS="${SPACE_IFICS:-3074}"
export TERR_IFICS="${TERR_IFICS:-3075 3076}"
export SKIP_OPTIONAL="${SKIP_OPTIONAL:-1}"
exec "$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)/download_data.sh" "$@"
