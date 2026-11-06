#!/usr/bin/env bash
#
# download_data.sh - fetch the Since AI 2026 / Traficom challenge datasets into data/raw/ (git-ignored).
#
# Usage:
#   scripts/download_data.sh                      # everything that is missing (about 720 MB on the first run)
#   scripts/fetch_data.sh                         # quick start: graded issues, M4 and the Finnish table only (wrapper, about 75 MB)
#   FORCE=1 scripts/download_data.sh              # re-download files that already exist
#   SPACE_IFICS="3084" scripts/download_data.sh   # only these Space IFIC issues (default: 3062-3083, all of 2026)
#   TERR_IFICS="3076" scripts/download_data.sh    # only these Terrestrial IFIC issues (default: 3074-3083)
#   UNZIP="ific3074 brific3076" ...               # archives to extract to data/raw/<name>/ (default: the graded issues and the
#                                                 # previous terrestrial issue); UNZIP=all extracts every IFIC zip (several GB)
#   SKIP_OPTIONAL=1 scripts/download_data.sh      # skip M15, the Radio Regulations, the CEPT exports and the station registers
#   DATA_DIR=/elsewhere scripts/download_data.sh  # custom destination (default: <repo>/data/raw)
#   PARALLEL=8 scripts/download_data.sh           # concurrent downloads (default: 4)
#
# Layout of data/raw/ (sources, dates and columns: data/SOURCES.md):
#   ific<NNNN>.zip, ific<NNNN>/ific<NNNN>.mdb          ITU BR IFIC (Space services) database of one issue
#   brific<NNNN>.zip, brific<NNNN>/brific<NNNN>.mdb    ITU BR IFIC (Terrestrial services) MDB extract of one issue
#   ific<NNNN>_article11.pdf, ReadMe_<NNNN>.pdf        terrestrial Article 11 index and issue notes
#   PREFACE_EN.pdf, BR_IFIC_and_other_BR_tools.pdf, SRSDiagramV9_1.pdf      ITU reference documents
#   taajuusjakotaulukko[_fin|_swe].json, traficom_swagger_v13.json, traficom_metadata_v13.xml,
#   radioasematiedot.json, tvasematiedot.json          Traficom open data API
#   finlex_m4/, finlex_m15/                            Traficom regulations M4 and M15 (PDF, fi/en/sv + explanatory notes)
#   itu_rr/, cept/                                     ITU Radio Regulations 2024, CEPT ECO exports (optional)
#   special_interest.xlsx                              NOT fetched: copy it by hand from the Since AI platform
#
# Already-present files are skipped, so the script is safe to re-run. New IFIC issues appear every
# second Tuesday; pass their numbers in SPACE_IFICS / TERR_IFICS or extend the defaults below.
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DATA_DIR="${DATA_DIR:-$ROOT/data/raw}"
MANIFEST="${MANIFEST:-$(dirname "$DATA_DIR")/MANIFEST.sha256}"
SPACE_IFICS="${SPACE_IFICS:-$(seq 3062 3083 | tr '\n' ' ')}"
TERR_IFICS="${TERR_IFICS:-$(seq 3074 3083 | tr '\n' ' ')}"
UNZIP="${UNZIP:-ific3074 brific3075 brific3076}"
PARALLEL="${PARALLEL:-4}"
FORCE="${FORCE:-0}"
SKIP_OPTIONAL="${SKIP_OPTIONAL:-0}"
export DATA_DIR FORCE

# fetch <dest> <url> : download one file atomically (dest.part -> dest); skip if present.
fetch() {
  local dest="$1" url="$2" tmp rel bad=0
  rel="${dest#"$DATA_DIR"/}"
  mkdir -p "$(dirname "$dest")"
  if [ -s "$dest" ] && [ "$FORCE" != "1" ]; then
    printf 'skip    %s\n' "$rel"
    return 0
  fi
  tmp="$dest.part"
  if ! curl -fsSL --retry 3 --retry-delay 3 --connect-timeout 30 -o "$tmp" "$url"; then
    rm -f "$tmp"
    printf 'FAILED  %s  <-  %s\n' "$rel" "$url" >&2
    return 1
  fi
  # Some servers answer with an HTML error page and HTTP 200. Keep a .zip/.pdf only if it is one.
  case "$dest" in
    *.zip) [ "$(head -c 2 "$tmp")" = "PK" ]   || bad=1 ;;
    *.pdf) [ "$(head -c 4 "$tmp")" = "%PDF" ] || bad=1 ;;
  esac
  if [ "$bad" = "1" ]; then
    printf 'FAILED  %s  (server sent "%s" instead of the file)  <-  %s\n' "$rel" "$(file -b "$tmp" | cut -d, -f1)" "$url" >&2
    rm -f "$tmp"
    return 1
  fi
  mv "$tmp" "$dest"
  printf 'ok      %-60s %6s\n' "$rel" "$(du -h "$dest" | cut -f1)"
}
export -f fetch

LIST="$(mktemp)"
trap 'rm -f "$LIST"' EXIT
add() { printf '%s\t%s\n' "$1" "$2" >> "$LIST"; }   # add <path relative to DATA_DIR> <url>

# ---------------------------------------------------------------- 1. ITU BR IFIC (Space services)
# One zip per issue holding ific<NNNN>.mdb: the SNS (v10) Access database published with that issue, with
# Part-IS/IIS/IIIS and the API/A, CR/C, AP30/30A/30B special sections.
for n in $SPACE_IFICS; do
  add "ific${n}.zip" "https://www.itu.int/sns/ific10/ific${n}.zip"
done
add "SRSDiagramV9_1.pdf" "https://www.itu.int/en/ITU-R/space/Documents/SRSDiagramV9_1.pdf"   # SRS/SNS table diagram

# ---------------------------------------------------------------- 2. ITU BR IFIC (Terrestrial services)
TERR=https://www.itu.int/en/ITU-R/terrestrial/brific/BRIFIC
for n in $TERR_IFICS; do
  add "brific${n}.zip"           "$TERR/MDB/brific${n}.zip"             # MDB extract: brific<NNNN>.mdb with the Article 11 notices
  add "ific${n}_article11.pdf"   "$TERR/Article11-Index/ific${n}.pdf"   # Article 11 index of the issue
  add "ReadMe_${n}.pdf"          "$TERR/ReadMe/ReadMe_${n}.pdf"         # issue notes, MDB extract structure
done
add "PREFACE_EN.pdf"                 "$TERR/Preface/PREFACE_EN.pdf"       # how to read the BR IFIC (Terrestrial)
add "BR_IFIC_and_other_BR_tools.pdf" "$TERR/BR_IFIC_and_other_BR_tools.pdf"

# ---------------------------------------------------------------- 3. Regulation 4 "M4" (Finlex)
# Traficom Radio Frequency Regulation 4 AG/2026 M, issued 26.3.2026. Finlex ids: 1070975 fi, 1070976 en, 1070974 sv.
FINLEX=https://www.finlex.fi/api/media/authority-regulation
Q='?typeDiscriminator=traficom-communications'
add "finlex_m4/M4_radiotaajuusmaarays_4AG2026M_fi.pdf"          "$FINLEX/1070975/mainPdf/main.pdf$Q"
add "finlex_m4/M4_radio_frequency_regulation_4AG2026M_en.pdf"   "$FINLEX/1070976/mainPdf/main.pdf$Q"
add "finlex_m4/M4_radiofrekvensforeskrift_4AG2026M_sv.pdf"      "$FINLEX/1070974/mainPdf/main.pdf$Q"
add "finlex_m4/M4_perustelumuistio_4AG2026M_fi.pdf"             "$FINLEX/1070975/media/Perustelumuistio%20Radiotaajuusm%C3%A4%C3%A4r%C3%A4ys%204AG2026M.pdf$Q"
add "finlex_m4/M4_explanatory_notes_4AG2026M_en.pdf"            "$FINLEX/1070976/media/Explanatory%20notes%20Radio%20Frequency%20Regulation%204AG2026M.pdf$Q"
add "finlex_m4/M4_motiveringspromemoria_4AG2026M_sv.pdf"        "$FINLEX/1070974/media/Motiveringspromemoria%20Radiofrekvensf%C3%B6reskrift%204AG2026M.pdf$Q"

# ---------------------------------------------------------------- 4. Traficom open data API v13 (OData, JSON)
# Taajuusjakotaulukko = table of frequency allocations in Finland (the M4 annex as data; 5917 sub-bands).
TRAFICOM=https://opendata.traficom.fi/api/v13
add "taajuusjakotaulukko.json"       "$TRAFICOM/Taajuusjakotaulukko"        # English column values
add "taajuusjakotaulukko_fin.json"   "$TRAFICOM/Taajuusjakotaulukko_fin"
add "taajuusjakotaulukko_swe.json"   "$TRAFICOM/Taajuusjakotaulukko_swe"
add "traficom_swagger_v13.json"      "https://opendata.traficom.fi/swagger/docs/v13"
add "traficom_metadata_v13.xml"      "$TRAFICOM/%24metadata"

if [ "$SKIP_OPTIONAL" != "1" ]; then
  # -------------------------------------------------------------- 5. Optional extras
  # Finnish broadcasting station registers (coordinates, power, antenna height): public station data for the terrestrial side.
  add "radioasematiedot.json"   "$TRAFICOM/Radioasematiedot"
  add "tvasematiedot.json"      "$TRAFICOM/TVAsematiedot"

  # Regulation 15 "M15" (licence-exempt collective frequencies), 15 AV/2025 M. Finlex ids: 535594 fi, 687387 en, 535595 sv.
  add "finlex_m15/M15_maarays_15AV2025M_fi.pdf"                 "$FINLEX/535594/mainPdf/main.pdf$Q"
  add "finlex_m15/M15_regulation_15AV2025M_en.pdf"              "$FINLEX/687387/mainPdf/main.pdf$Q"
  add "finlex_m15/M15_foreskrift_15AV2025M_sv.pdf"              "$FINLEX/535595/mainPdf/main.pdf$Q"
  add "finlex_m15/M15_perustelumuistio_15AV2025M_fi.pdf"        "$FINLEX/535594/media/Perustelumuistio%20M%C3%A4%C3%A4r%C3%A4ys%2015AV2025M.pdf$Q"
  add "finlex_m15/M15_explanatory_notes_15AV2025M_en.pdf"       "$FINLEX/687387/media/Explanatory%20notes%20Regulation%2015AV2025M.pdf$Q"
  add "finlex_m15/M15_motiveringspromemoria_15AV2025M_sv.pdf"   "$FINLEX/535595/media/Motiveringspromemoria%20F%C3%B6reskrift%2015AV2025M.pdf$Q"

  # ITU Radio Regulations, 2024 edition, English, zip of PDFs (free download).
  add "itu_rr/R-REG-RR-2024-ZPF-E.zip" "https://www.itu.int/dms_pub/itu-r/opb/reg/R-REG-RR-2024-ZPF-E.zip"

  # CEPT/ECO documentation database: implementation status of ECC Decisions/Recommendations per country,
  # and the full ECC document list with harmonised frequency ranges.
  CEPT=https://docdb.cept.org
  add "cept/Country_Implementations_Overview.xlsx"                 "$CEPT/implementation/download"
  add "cept/Country_Implementations_Decisions_Overview.xlsx"       "$CEPT/implementation/download?documentType=ECC_Decisions"
  add "cept/Country_Implementations_Recommendations_Overview.xlsx" "$CEPT/implementation/download?documentType=ECC_Recommendations"
  add "cept/ECC_all_documents_with_frequencies.csv"                "$CEPT/search/exportall?includeFrequencies=true&includeStandards=true"
fi

# ---------------------------------------------------------------- download
mkdir -p "$DATA_DIR"
echo "Fetching $(wc -l < "$LIST" | tr -d ' ') files into $DATA_DIR (PARALLEL=$PARALLEL) ..."
status=0
while IFS=$'\t' read -r rel url; do
  printf '%s\0%s\0' "$DATA_DIR/$rel" "$url"
done < "$LIST" | xargs -0 -n 2 -P "$PARALLEL" bash -c 'fetch "$0" "$1"' || status=1

# ---------------------------------------------------------------- extract the databases: <name>.zip -> <name>/<name>.mdb
if [ "$UNZIP" = "all" ]; then
  UNZIP="$(find "$DATA_DIR" -maxdepth 1 -name '*.zip' -exec basename {} .zip \; | sort | tr '\n' ' ')"
fi
for name in $UNZIP; do
  zip="$DATA_DIR/$name.zip"; dir="$DATA_DIR/$name"
  if [ ! -s "$zip" ]; then printf 'unzip   %s.zip is not downloaded, skipping\n' "$name"; continue; fi
  if [ -d "$dir" ] && [ "$FORCE" != "1" ]; then printf 'skip    %s/ (already extracted)\n' "$name"; continue; fi
  mkdir -p "$dir" && unzip -q -o "$zip" -d "$dir"
  printf 'unzip   %-60s %6s\n' "$name/" "$(du -sh "$dir" | cut -f1)"
done

# ---------------------------------------------------------------- checksums (paths relative to data/, so: cd data && shasum -a 256 -c MANIFEST.sha256)
echo "Writing $MANIFEST ..."
( cd "$(dirname "$DATA_DIR")" && find "$(basename "$DATA_DIR")" -type f ! -name '*.part' -print0 | sort -z | xargs -0 shasum -a 256 ) > "$MANIFEST"

echo
echo "Database files found:"
find "$DATA_DIR" -iname '*.mdb' | sort
echo
echo "Still needed by hand: the special-interest XLS from the Since AI platform -> $DATA_DIR/special_interest.xlsx"
echo "Next: python3 scripts/inspect_mdb.py data/raw/ific3074/*.mdb"
du -sh "$DATA_DIR" | awk '{print "Total in data/raw: " $1}'
if [ "$status" != "0" ]; then
  echo "Some downloads FAILED (see above). Re-run the script to retry the missing files." >&2
fi
exit "$status"
