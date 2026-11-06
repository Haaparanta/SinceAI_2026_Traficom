#!/usr/bin/env bash
# Fetch the public inputs for Filing Radar into data/raw/ (git-ignored).
# Sources and sizes verified on Fri 6 Nov 2026; see pm_pack/06_AGENTS_Master_Context.md.
set -euo pipefail
cd "$(dirname "$0")/.."
mkdir -p data/raw
cd data/raw

fetch() {  # fetch <local name> <url>
  local name="$1" url="$2"
  if [ -s "$name" ]; then
    echo "skip   $name (exists, $(du -h "$name" | cut -f1))"
  else
    echo "fetch  $name"
    curl -L --fail --progress-bar -o "$name" "$url"
    echo "done   $name ($(du -h "$name" | cut -f1))"
  fi
}

fetch ific3074.zip            "https://www.itu.int/sns/ific10/ific3074.zip"                                      # Space IFIC 3074, 60.8 MB, graded
fetch brific3076.zip          "https://www.itu.int/en/ITU-R/terrestrial/brific/BRIFIC/MDB/brific3076.zip"        # Terrestrial 3076 MDB extract, 2.4 MB, graded
fetch brific3075.zip          "https://www.itu.int/en/ITU-R/terrestrial/brific/BRIFIC/MDB/brific3075.zip"        # Terrestrial 3075, 3.4 MB, for the diff
fetch ReadMe_3076.pdf         "https://www.itu.int/en/ITU-R/terrestrial/brific/BRIFIC/ReadMe/ReadMe_3076.pdf"    # MDB extract structure, 145 KB
fetch ific3076_article11.pdf  "https://www.itu.int/en/ITU-R/terrestrial/brific/BRIFIC/Article11-Index/ific3076.pdf" # Article 11 index, 1.9 MB
fetch SRSDiagramV9_1.pdf      "https://www.itu.int/en/ITU-R/space/Documents/SRSDiagramV9_1.pdf"                  # SRS table diagram, 50 KB
fetch taajuusjakotaulukko.json "https://opendata.traficom.fi/api/v13/Taajuusjakotaulukko"                         # Finnish table, 5 917 rows, 4.4 MB

for z in ific3074 brific3076 brific3075; do
  if [ ! -d "$z" ]; then
    echo "unzip  $z.zip"
    mkdir -p "$z" && unzip -q -o "$z.zip" -d "$z"
  fi
done

echo
echo "Database files found:"
find . -iname '*.mdb' -o -iname '*.accdb' | sort
echo
echo "Still needed by hand: the special-interest XLS from the Since AI platform -> data/raw/special_interest.xlsx"
echo "Next: python3 scripts/inspect_mdb.py data/raw/ific3074/*.mdb"
