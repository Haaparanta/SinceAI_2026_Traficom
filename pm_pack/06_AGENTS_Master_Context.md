# AGENTS.md — Master Context: Filing Radar

Shared context for every coding agent on the team (Claude Code, Cursor, Codex, Antigravity). Read fully before touching code.

> [!NOTE]
> **Grounding.** Designed on Fri 6 Nov 2026 from the Traficom challenge brief, `README.md`, and the live ITU, Finlex and Traficom sources. Tags: `[SOURCE DATA]` stated by the partner or a linked page, `[HYPOTHESIS]` our assumption until verified, `[GAP - ASK PARTNER: Qn]` open question in `pm_pack/01_Partner_Briefing_Questions.md`.
> The ITU database table and field names below come from the ITU's schema documentation (see `pm_pack/07_Solution_Catalogue.md`, section 2) but have not yet been checked against the files inside the 3074 and 3076 zips. The first engineering task is to print the real schema and fill `backend/radar/schema_map.yaml`; nothing else may hard-code a table or column name.
>
> To use: `ln -s pm_pack/06_AGENTS_Master_Context.md AGENTS.md` and the same for `CLAUDE.md` and `.cursorrules`.

---

## Mission

Turn an ITU BR IFIC issue into a ranked, cited, expert-reviewable list of notices that may affect radio frequency use in Finland, with an indicative technical check and a draft letter to the notifying administration. Space services first (Space IFIC 3074 is the graded set), the same engine on terrestrial land-mobile notices (Terrestrial IFIC 3076 is the graded set). `[SOURCE DATA: brief 02, 03, 07]`

**Rules that never change**

1. The tool suggests; a human decides. No automatic sending, rejecting or dismissing.
2. No finding without evidence. Every `Finding` carries at least one `Evidence` item that points to a file, table, row and field, or to a regulation section.
3. Unknown stays unknown. Parsers never invent a missing value; they return `null` and the UI shows "unknown".
4. Deterministic first. Screening, geometry, pfd and field strength are plain code with unit tests. The language model only explains, drafts and summarises, and may cite only evidence IDs that exist.
5. Every calculated number is shown with its inputs, their sources, the formula, the limit used and the margin, and is labelled `indicative` unless a specialist has confirmed the method `[GAP: Q2, Q12]`.
6. The judging weights decide priorities: A technical analysis and reproducibility 25 %, B extensibility and terrestrial side quest 25 %, C workflow usefulness and output quality 20 %, D case recognition accuracy 15 %, E auditability and evidence 15 % `[SOURCE DATA: brief 06]`.

---

## Source data map `[SOURCE DATA unless tagged]`

| Source | Where | Format | We take |
|---|---|---|---|
| Space IFIC 3074 (graded) | `https://www.itu.int/sns/ific10/ific3074.zip` | zip, 60.8 MB, "Version 10" Access `.mdb` databases | notices in Parts I-S, II-S, III-S and Special Sections API/A, CR/C; AP30/30A/30B are separate ITU databases (C3) |
| Any other Space IFIC | `https://www.itu.int/sns/ific10/ific<NNNN>.zip`; list at `https://www.itu.int/sns/wic/demowic26.html` | same | "all existing and forthcoming IFICs shall be able to be evaluated": the adapter takes an issue number, nothing else |
| Terrestrial IFIC 3076 (graded) and 3075 | `https://www.itu.int/en/ITU-R/terrestrial/brific/BRIFIC/MDB/brific3076.zip` (2.4 MB), `brific3075.zip` (3.4 MB), `ReadMe/ReadMe_3076.pdf` (145 KB), `Article11-Index/ific3076.pdf` (1.9 MB) | zip with an `.mdb` extract | Article 11 notices; diff between consecutive issues |
| Finnish frequency allocation table | `https://opendata.traficom.fi/api/v13/Taajuusjakotaulukko` (OData, CC BY 4.0) | JSON, 5 917 rows, 24 fields | sub-band limits in Hz, `Services_in_Finland`, `Sub_band_usage`, `Class_of_station`, `Direction`, powers, `Comment` |
| Regulation M4 | `https://www.finlex.fi/fi/viranomaiset/maarayskokoelmat/traficom-viestinta/2026/3` | Radiotaajuusmääräys 4 AG/2026M, PDF plus memo | citation target for every Finnish-table match |
| Special-interest stations (mandatory) | Since AI platform, XLS, fetched by a human | station number, centre frequency, bandwidth, coordinates, antenna height, direction, directivity `[GAP: Q4 for exact columns]` | point targets for geography and limits |
| Schema documentation | `https://www.itu.int/en/ITU-R/space/Documents/SRSDiagramV9_1.pdf` (50 KB), `legend_E.pdf` from the "Data items description" page, terrestrial `ReadMe_3076.pdf` and Preface | PDF | the real table and field names |
| Limits and criteria | ITU Radio Regulations (Article 21 pfd tables), ECC T/R 25-08, ITU-R P.1546, CEPT docdb CSV exports | documents | values go into reviewed CSVs in `data/reference/` with a `source` column |

---

## Provisional tech stack `[HYPOTHESIS]`

- **Backend:** Python 3.12, `uv`, FastAPI, Pydantic v2, DuckDB (SQL over the converted tables, Parquet caches), pandas, pyarrow, NumPy, Shapely, pytest.
- **Database conversion:** `mdbtools` (`brew install mdbtools`; `mdb-tables -1`, `mdb-export`). Fallback: a Windows machine with Access or the ITU tools exporting CSV `[GAP: Q13]`.
- **AI:** Anthropic Python SDK (`pip install anthropic`), model `claude-opus-5-5` by default with adaptive thinking and the server-side refusal fallback enabled; `LLM_MODEL` in `.env` switches the model; `LLM_DISABLED=1` makes every LLM function return a deterministic placeholder so the pipeline runs offline.
- **Frontend:** React 19, Vite, TypeScript, Tailwind CSS v4, shadcn/ui, MapLibre GL with a committed Finland GeoJSON, Recharts.
- **Design system:** Girlypop theme v2. Import `design/girlypop.css` into `frontend/src/globals.css` and follow `design/girlypop-theme.md`: tokens only, risk badges always with a text label, `bg-sigil` on the page root only, no emoji anywhere, plain language on findings, decisions and exports.
- **Storage:** files only. `data/derived/*.duckdb`, `data/reference/*.csv`, `data/cache/*.json`, `results/*.csv|json`.

---

## Folder tree

```
.
├── AGENTS.md -> pm_pack/06_AGENTS_Master_Context.md
├── Makefile                      # data, convert, screen, export, test, run
├── backend/
│   └── radar/
│       ├── main.py               # FastAPI routes
│       ├── config.py             # DATA_DIR, DEMO_MODE, LLM_MODEL, LLM_DISABLED
│       ├── models.py             # Pydantic contracts (FROZEN after Gate 1)
│       ├── schema_map.yaml       # real ITU table and field names -> our names
│       ├── adapters/
│       │   ├── base.py           # IssueAdapter protocol
│       │   ├── space_ific.py     # zip -> mdb -> DuckDB -> Notice, FrequencyGroup
│       │   ├── terrestrial_ific.py
│       │   ├── traficom_table.py # API -> FinnishSubBand (Parquet cache)
│       │   └── special_interest.py # XLS -> SpecialInterestStation
│       ├── pipeline/
│       │   ├── relevance.py      # frequency overlap, direction rules
│       │   ├── geography.py      # GSO elevation, service areas, border distance
│       │   ├── diff.py           # terrestrial new / modified / withdrawn
│       │   ├── assemble.py       # overlaps + geometry + calc -> Finding
│       │   └── rank.py           # concern level and ordering
│       ├── calc/
│       │   ├── pfd.py            # GSO worst-case pfd and limit lookup
│       │   ├── p1546.py          # field strength at the border
│       │   └── trace.py          # CalcTrace builder
│       ├── llm/
│       │   ├── client.py         # one Anthropic client, structured outputs
│       │   ├── explain.py        # grounded explanation
│       │   └── letter.py         # correspondence draft
│       ├── export/results.py     # results/space_3074.csv, terrestrial_3076.csv
│       └── demo_cache.py         # DEMO_MODE
├── frontend/src/
│   ├── types.ts                  # mirrors models.py
│   ├── App.tsx                   # the one screen
│   └── components/{IssueBar,SpectrumStrip,MapView,CalcTrace,FindingCard,RankedList,Metrics}.tsx
├── data/
│   ├── raw/                      # downloads, GIT-IGNORED
│   ├── derived/                  # DuckDB and Parquet, GIT-IGNORED
│   ├── reference/                # finland.geojson, fi_reference_points.csv, pfd_limits.csv, tr2508_thresholds.csv (committed, each row has a source)
│   └── cache/                    # sample_1.json, sample_2.json, sample_3.json (committed)
├── results/                      # the graded output files (committed at the end)
├── prompts/                      # explain.md, letter.md
├── scripts/
│   ├── fetch_data.sh
│   ├── inspect_mdb.py            # prints every table and column of an .mdb
│   ├── mdb_to_duckdb.py
│   └── build_cache.py
└── tests/
```

---

## Data acquisition

`scripts/fetch_data.sh` (run by a human; everything lands in `data/raw/`, which is git-ignored) fetches the graded issues and
extracts their databases: `ific3074.zip` -> `ific3074/ific3074.mdb`, `brific3076.zip` -> `brific3076/brific3076.mdb`,
`brific3075.zip` -> `brific3075/brific3075.mdb` (previous issue, for the diff), plus `ReadMe_3076.pdf`, `ific3076_article11.pdf`,
`PREFACE_EN.pdf`, `SRSDiagramV9_1.pdf`, the M4 PDFs in `finlex_m4/` and `taajuusjakotaulukko.json` (about 75 MB).

`scripts/download_data.sh` is the full version it wraps: every 2026 Space IFIC (3062-3083), terrestrial issues 3074-3083 with their
Article 11 indexes and ReadMes, M15, the ITU Radio Regulations 2024, the CEPT ECO exports and the Traficom station registers
(about 720 MB). `SPACE_IFICS="3084" scripts/download_data.sh` adds a new issue; `UNZIP="ific3083" ...` extracts another database.
Every URL, issue date, column list and licence is in `data/SOURCES.md`; checksums land in `data/MANIFEST.sha256`.

The special-interest XLS comes from the Since AI platform: save it as `data/raw/special_interest.xlsx`.

Then `python scripts/inspect_mdb.py data/raw/ific3074/*.mdb` and fill `schema_map.yaml`. Only after that may `space_ific.py` be written.

### ITU tables we expect `[SOURCE DATA: Space Preface Oct 2026, Section III Ch. 1; terrestrial FXM diagram and Preface ed. 3083. Confirm with scripts/inspect_mdb.py]`

Names below are taken from the ITU's own schema documentation; full column lists and sources are in `pm_pack/07_Solution_Catalogue.md`, section 2. They still go through `schema_map.yaml`, because the files inside the 3074 zip have not been opened yet.

| Our name | SNS v10 table | Fields we need |
|---|---|---|
| notice | `notice` | `ntc_id`, `adm`, `ntwk_org`, `ntc_type` (G GSO, N non-GSO, S specific earth station, T typical earth station, R radio astronomy), `ntf_rsn` (A API, C coordination, N notification), `prov`, `act_code`, `d_rcv`, `wic_no`, `wic_part`, `d_wic`, `tgt_ntc_id` |
| GSO station | `geo` | `ntc_id`, `sat_name`, `long_nom` (minus = West) |
| non-GSO station | `non_geo` | `ntc_id`, `sat_name`, `ref_body` |
| group | `grp` | `grp_id`, `ntc_id`, `beam_name`, `emi_rcp` (E = space station emits, R = receives), `freq_min`, `freq_max` (MHz), `bdwdth` (kHz), `d_inuse`, `adm_resp`, `op_agcy` |
| frequency | `assgn` | assigned frequency; `pfd` and its `bdwdth` where declared |
| emission | `emiss` | `grp_id`, `seq_no`, `design_emi`, `pep_max` (dBW), `pwr_ds_max` (dBW/Hz), `pwr_ds_nbw` |
| beam | `s_beam` | `ntc_id`, `emi_rcp`, `beam_name`, `gain` (max dBi), `f_steer` |
| service area | `srv_area` | `grp_id`, `ctry` (country or area symbol), `f_excl_api` |
| service class | `srv_cls` | `grp_id`, nature of service, class of station |
| orbit (non-GSO) | `orbit`, `phase` | `ntc_id`, `orb_id`, `nbr_sat_pl`, `inclin_ang`, `apog_km`, `perig_km`, `right_asc`, `perig_arg` |
| pfd mask (non-GSO) | `mask_info`, `mask_lnk1`–`mask_lnk3` | presence and frequency range (C1) |
| earth station | `e_as_stn`, `e_ant` | `ntc_id`, `ctry`, antenna `gain` |
| affected networks | `provn`, `all_aff_ntw`, `tr_aff_ntw` | administrations and networks the Bureau identified |
| publication | `pub_ssn` | special section reference |

`com_el` and `freq` exist but are marked "BR internal use"; do not build on them. Part I-S action symbols: A new, M modification, N non-basic change, R resubmission, S suppression, W withdrawn.

Terrestrial MDB extract: land-mobile notices are in the FXM domain, spread over several tables, not one. `fxm_terra` (`terrakey`, `adm`, `fragment`, `freq_assgn`, `freq_min`, `freq_max`, `bdwdth`, `emi_cls`, `stn_cls`, `notice_typ`, `intent` = ADD, MODIFY, SUPPRESS or WITHDRAW, `d_rcv`, `geo_key`), `fxm_geo` and `fxm_geo_pt` (`ctry`, `site_name`, `long_dec`, `lat_dec`, `site_alt`), `fxm_ant` (`pwr_ant` dBW, `gain_max`, `gain_type`, `ant_dir`, `azm_max_e`, `hgt_agl`, `eff_hgtmax`, `polar`) and `fxm_ant_hgt` (effective height per azimuth, the P.1546 input). Land-mobile notice forms: T12 transmitting stations, T13 receiving land stations, T14 typical stations. Station classes: FB base, FL land, ML land mobile, MO mobile. The full TerRaBase is SQLite (`BRIFIC_<NNNN>.db3`); the per-issue extract format is still to be confirmed by unzipping.

---

## Pipeline

```
issue number
  -> adapter: download or reuse zip -> mdb -> DuckDB (data/derived/<kind>_<issue>.duckdb)
  -> normalise: Notice + FrequencyGroup rows (space) | TerrestrialNotice rows (terrestrial, with diff against the previous issue)
  -> relevance.py: overlap with FinnishSubBand rows and SpecialInterestStation rows, direction rules
  -> geography.py: GSO elevation from Finnish reference points | non-GSO visibility | border distance for terrestrial
  -> calc: pfd.py (space) | p1546.py (terrestrial) -> CalcTrace
  -> assemble.py: Finding with Evidence; rank.py: concern level
  -> llm/explain.py (optional, grounded) ; llm/letter.py (on request)
  -> export/results.py ; API ; one screen
```

### Relevance rules `[HYPOTHESIS until Q1 is answered]`

| Group direction | Finnish table match | Concern path |
|---|---|---|
| space-to-Earth (`emi_rcp = E`) | sub-band allocated to terrestrial services (FIXED, MOBILE, BROADCASTING, RADIOLOCATION and similar) | pfd at the Finnish surface versus the limits table: this is the main path |
| space-to-Earth | sub-band allocated to a space service in Finland (text contains "(space-to-Earth)") | co-frequency with Finnish satellite downlinks or earth stations: flag for coordination review, no pfd limit `[GAP: Q8]` |
| Earth-to-space (`emi_rcp = R`) | any Finnish terrestrial allocation | low unless the associated earth station is in a neighbouring country; otherwise informational |
| any | special-interest station within the group's frequency range | always at least Medium, with the station as evidence |

Frequency overlap is computed on Hz integers: `max(0, min(g.freq_max, s.upper) - max(g.freq_min, s.lower))`.

### Geometry `[HYPOTHESIS: standard formulas; coordinates approximate]`

Finnish reference points in `data/reference/fi_reference_points.csv`: Hanko 59.82 N 22.97 E, Helsinki 60.17 N 24.94 E, Vaasa 63.10 N 21.62 E, Ilomantsi 62.67 N 30.93 E, Oulu 65.01 N 25.47 E, Utsjoki 69.91 N 27.03 E.

For a GSO satellite at longitude `L` and a site at latitude `phi`, longitude `lam`, with `R = 6378.137 km` and `h = 35786 km`:
`cos(gamma) = cos(phi) * cos(L - lam)`;
`elevation = atan2(cos(gamma) - R / (R + h), sin(gamma))`;
`slant_range = sqrt(R^2 + (R + h)^2 - 2 * R * (R + h) * cos(gamma))`.
Visible if elevation is above 0 degrees; low-elevation flag below 10 degrees. Finland sees GSO satellites at low elevation, so the strict low-angle pfd limits usually apply.

Terrestrial: distance from the notified station to the nearest point of the Finland polygon (`data/reference/finland.geojson`), path type land, sea or mixed from the line crossing the polygon and the sea mask.

### Calculations

**pfd (space, GSO worst case):** with `P_d` the maximum power density at the antenna input in dBW/Hz (`emiss.pwr_ds_max`), `G` the maximum beam gain in dBi (`s_beam.gain`), `d` the slant range in metres at the Finnish point with the lowest elevation, and `B_ref` the reference bandwidth of the limit in Hz:
`pfd_dbw_m2 = P_d + G + 10 log10(B_ref) - 10 log10(4 * pi * d^2)`.
Limit lookup from `data/reference/pfd_limits.csv` (`band_min_mhz, band_max_mhz, service, ref_bw_hz, limit_le5deg, slope_per_deg, limit_ge25deg, source`): `limit = limit_le5deg` for elevation at or below 5 degrees, linear between 5 and 25 degrees, `limit_ge25deg` above `[HYPOTHESIS shape; values typed from RR Article 21 and reviewed by two people]`. `margin_db = limit - pfd`. Worst case ignores atmospheric loss and beam roll-off, which makes it conservative; say so in the trace. Non-GSO: report mask presence only (C1) `[GAP: Q7]`.

**Field strength (terrestrial):** inputs frequency MHz, distance km, time percentage, transmitting effective height, receiving height 10 m, path type, ERP. Prefer an official ITU-R Study Group 3 reference implementation of P.1546 if one can be installed in under an hour; otherwise implement the curve interpolation for the frequency and distance ranges we hit, keep `tests/p1546_vectors.md` with hand-checked values, and label the method in the trace. `E = E_curve(1 kW) + ERP_dBW - 30`. Threshold from `data/reference/tr2508_thresholds.csv` `[HYPOTHESIS values]` `[GAP: Q12]`. `margin_db = threshold - E`.

Every calculation returns a `CalcTrace` and never a bare number.

---

## Data contracts (Pydantic, `backend/radar/models.py`)

```python
from datetime import date, datetime
from typing import Literal
from pydantic import BaseModel, Field

Kind = Literal["space", "terrestrial"]
Concern = Literal["none", "low", "medium", "high", "review"]

class Evidence(BaseModel):
    id: str                                   # "E-0001"
    kind: Literal["itu_row", "finnish_table_row", "special_interest_row", "regulation", "calculation"]
    source: str                               # file name, URL or document title
    locator: str                              # "notice.ntc_id=123456789" | "Taajuusjakotaulukko.ID=4123" | "RR Art. 21 Table 21-4"
    excerpt: str                              # the value or sentence as found

class FrequencyGroup(BaseModel):
    group_id: str
    notice_id: str
    freq_min_hz: int
    freq_max_hz: int
    direction: Literal["space_to_earth", "earth_to_space", "unknown"]
    beam_name: str | None = None
    power_density_dbw_hz: float | None = None
    max_gain_dbi: float | None = None
    service_area_codes: list[str] = []
    source_ref: str                           # table.row locator

class Notice(BaseModel):
    kind: Kind = "space"
    issue: int                                # 3074
    notice_id: str
    administration: str                       # ITU symbol, e.g. "FIN"
    network_name: str
    special_section: str | None = None        # "API/A", "CR/C", ...
    orbit: Literal["GSO", "NGSO", "unknown"]
    longitude_deg: float | None = None
    received: date | None = None
    groups: list[FrequencyGroup]
    source_ref: str

class TerrestrialNotice(BaseModel):
    kind: Kind = "terrestrial"
    issue: int                                # 3076
    notice_id: str
    administration: str
    change: Literal["new", "modified", "withdrawn", "unchanged"]
    station_class: str | None = None
    site_name: str | None = None
    lat: float | None = None
    lon: float | None = None
    freq_hz: int | None = None
    bandwidth_hz: int | None = None
    erp_dbw: float | None = None
    antenna_height_m: float | None = None
    azimuth_deg: float | None = None
    source_ref: str

class FinnishSubBand(BaseModel):              # one Traficom API row
    id: int
    lower_hz: int
    upper_hz: int
    services_in_finland: str
    sub_band_usage: str
    class_of_station: str | None = None
    direction: str | None = None
    comment: str | None = None

class SpecialInterestStation(BaseModel):      # one XLS row, columns per brief 05 [GAP: Q4]
    station_number: str
    centre_hz: int
    bandwidth_hz: int
    lat: float
    lon: float
    antenna_height_m: float | None = None
    antenna_direction_deg: float | None = None
    antenna_directivity: str | None = None
    limit_value: float | None = None
    limit_unit: str | None = None

class CalcInput(BaseModel):
    name: str
    value: float | str
    unit: str
    evidence_id: str

class CalcTrace(BaseModel):
    method: Literal["pfd_gso_worst_case", "p1546_field_strength", "none"]
    inputs: list[CalcInput]
    formula: str
    result_value: float | None
    result_unit: str
    limit_value: float | None
    limit_evidence_id: str | None
    margin_db: float | None
    label: Literal["indicative", "confirmed"] = "indicative"
    notes: list[str] = []

class Finding(BaseModel):
    id: str                                   # "F-3074-0001"
    kind: Kind
    issue: int
    notice_id: str
    group_id: str | None = None
    matched_subband_ids: list[int] = []
    matched_station_numbers: list[str] = []
    overlap_hz: int = 0
    geo_relevance: Literal["visible", "low_elevation", "not_visible", "near_border", "far", "unknown"]
    calc: CalcTrace
    concern: Concern
    reason: str                               # deterministic, template-based
    explanation: str | None = None            # LLM, cites evidence IDs only
    evidence: list[Evidence] = Field(min_length=1)

class AnalysisResult(BaseModel):
    issue: int
    kind: Kind
    screened: int
    flagged: int
    provenance_coverage_pct: float
    findings: list[Finding]
    from_cache: bool = False

class ReviewDecision(BaseModel):
    finding_id: str
    decision: Literal["approve", "dismiss", "investigate"]
    reviewer: str
    note: str | None = None
    at: datetime

class Letter(BaseModel):
    finding_id: str
    to_administration: str
    subject: str
    body_markdown: str
    cited_evidence_ids: list[str]

class ResultRow(BaseModel):                   # one line of the graded results file
    issue: int
    kind: Kind
    notice_id: str
    special_section: str | None
    administration: str
    network_or_station: str
    freq_min_mhz: float | None
    freq_max_mhz: float | None
    direction: str | None
    finnish_match: str | None                 # services and sub-band IDs
    special_interest_station_ids: str | None
    overlap_mhz: float | None
    geo_relevance: str
    calc_method: str
    calc_value: float | None
    calc_unit: str | None
    limit_value: float | None
    margin_db: float | None
    concern: Concern
    reason: str
    evidence_refs: str                        # semicolon-separated locators
    decision: str | None = None
```

`frontend/src/types.ts` mirrors these one to one, for example:

```ts
export type Kind = "space" | "terrestrial";
export type Concern = "none" | "low" | "medium" | "high" | "review";
export interface Evidence { id: string; kind: "itu_row" | "finnish_table_row" | "special_interest_row" | "regulation" | "calculation"; source: string; locator: string; excerpt: string; }
export interface CalcInput { name: string; value: number | string; unit: string; evidence_id: string; }
export interface CalcTrace { method: "pfd_gso_worst_case" | "p1546_field_strength" | "none"; inputs: CalcInput[]; formula: string; result_value: number | null; result_unit: string; limit_value: number | null; limit_evidence_id: string | null; margin_db: number | null; label: "indicative" | "confirmed"; notes: string[]; }
export interface Finding { id: string; kind: Kind; issue: number; notice_id: string; group_id: string | null; matched_subband_ids: number[]; matched_station_numbers: string[]; overlap_hz: number; geo_relevance: "visible" | "low_elevation" | "not_visible" | "near_border" | "far" | "unknown"; calc: CalcTrace; concern: Concern; reason: string; explanation: string | null; evidence: Evidence[]; }
export interface AnalysisResult { issue: number; kind: Kind; screened: number; flagged: number; provenance_coverage_pct: number; findings: Finding[]; from_cache: boolean; }
```

**`models.py` and `types.ts` are frozen after Gate 1 (Fri 23:30).** A new field needs the PM and lands in both files in one commit.

---

## LLM contract (`backend/radar/llm/`)

- One client: `anthropic.Anthropic()` reads `ANTHROPIC_API_KEY` from `.env`. Model from `LLM_MODEL`, default `claude-opus-5-5`. `LLM_DISABLED=1` returns placeholders.
- Structured outputs through `client.messages.parse(...)` with a Pydantic class; the result is validated before use. Free text drafts go through `client.beta.messages.create(...)` with `fallbacks="default"` and `betas=["server-side-fallback-2026-07-01"]`, so a safety refusal falls back to another model instead of failing the demo. Check `stop_reason` before reading content.
- Prompts live in `prompts/*.md` and are loaded, never inlined. The system prompt is stable (cacheable); the finding JSON goes in the user message.
- The model receives only: the finding, its evidence items, and the matched Finnish rows. It must cite evidence IDs in `cited_evidence_ids`; a validator rejects any ID not in the finding and any new number not present in the inputs.

```python
# backend/radar/llm/explain.py
import anthropic
from pydantic import BaseModel
from radar.config import settings
from radar.models import Finding

class Explanation(BaseModel):
    text: str                      # two sentences, plain language
    cited_evidence_ids: list[str]

client = anthropic.Anthropic()

def explain(finding: Finding) -> Explanation:
    if settings.llm_disabled:
        return Explanation(text=finding.reason, cited_evidence_ids=[e.id for e in finding.evidence[:1]])
    response = client.messages.parse(
        model=settings.llm_model,                  # default "claude-opus-5-5"
        max_tokens=2000,
        thinking={"type": "adaptive"},
        output_config={"effort": "medium"},
        system=settings.prompt("explain"),         # prompts/explain.md, stable for caching
        messages=[{"role": "user", "content": finding.model_dump_json()}],
        output_format=Explanation,
    )
    if response.stop_reason == "refusal":
        return Explanation(text=finding.reason, cited_evidence_ids=[e.id for e in finding.evidence[:1]])
    out = response.parsed_output
    allowed = {e.id for e in finding.evidence}
    if not set(out.cited_evidence_ids) <= allowed:
        raise ValueError("explanation cites unknown evidence")
    return out
```

The letter draft uses the same shape with `effort: "high"`, `max_tokens=4000`, the `Letter` model, and `prompts/letter.md` (formal English, names the special section reference, the frequency range, the Finnish service, the RR provision, asks for coordination or for the technical parameters, signed by a placeholder) `[GAP: Q10]`.

---

## Demo mode and results export

- `DEMO_MODE=1` or the UI switch: `POST /issues/{issue}/screen` and `GET /findings` serve `data/cache/sample_<n>.json`, validated against `AnalysisResult`, `from_cache = true`, no network and no LLM calls. `scripts/build_cache.py` regenerates the cache from a live run. The video and the Sunday demo run in demo mode. Details in `pm_pack/04_Risk_Register_and_Mitigation.md`.
- `python -m radar.export --issue 3074 --kind space` writes `results/space_3074.csv` and `.json` (rows are `ResultRow`); the same for `--issue 3076 --kind terrestrial`. These are the files the brief asks to submit separately `[SOURCE DATA: brief 07]` `[GAP: Q3 for the partner's preferred schema]`. Commit them with a `results/README.md` that states inputs, parameters and assumptions.

## API (`backend/radar/main.py`)

| Method and path | Returns |
|---|---|
| `GET /issues` | known issues with status (downloaded, converted, screened) |
| `POST /issues/{issue}/screen?kind=space` | `AnalysisResult` (runs or returns the cached run) |
| `GET /findings?issue=3074&kind=space` | ranked `Finding[]` |
| `GET /findings/{id}` | one `Finding` with its evidence and trace |
| `POST /findings/{id}/decision` | stores a `ReviewDecision` |
| `POST /findings/{id}/letter` | `Letter` |
| `GET /reference/subbands?hz=11000000000` | matching `FinnishSubBand[]` |
| `GET /export/{issue}?kind=space` | the results CSV |
| `GET /metrics?issue=3074` | screened, flagged, provenance coverage |

---

## Multi-agent division rules

| Agent | Owns | Must not touch |
|---|---|---|
| **Claude Code** | `backend/radar/pipeline/`, `calc/`, `llm/`, `prompts/`, `models.py` (with PM approval) | `frontend/` |
| **Cursor** | `frontend/` | `backend/radar/pipeline/`, `calc/` |
| **Codex** | `scripts/`, `tests/`, `adapters/`, `schema_map.yaml`, `export/` | UI components, prompts, calculations |
| **Antigravity** | map styling, charts, `design/`, video and deck assets | contracts, pipeline, calculations |

Shared rules:

1. One agent per folder at a time. Small commits, one feature per branch, branch names `feat/<area>-<thing>`.
2. Contracts first: an agent that needs a new field stops and asks the PM; no local workarounds.
3. Before every commit: backend `uv run pytest -q`, frontend `npm run build`. A failing test is never committed.
4. No secrets, no `data/raw/`, no `data/derived/` in commits. `.env` stays local. `results/` and `data/cache/` are committed on purpose.
5. Every number on screen comes from a `CalcTrace` or a counted query. No agent writes a literal number into the UI.
6. The language model never decides concern level, never computes, never cites anything outside the finding.
7. Keep `pm_pack/` in sync: when a partner answer arrives, the PM updates the `[GAP]` tags before engineers change behaviour.
8. When a task is done: commit the work, push the branch to `origin` and open a pull request against `main` (`gh pr create`, short title, body that says what changed and why). Never commit straight to `main`; a person reviews and merges.

---

## Final verification: gaps that can change this architecture `[GAP - ASK PARTNER]`

1. **Q1 relevance rule.** Changes `relevance.py` ordering and may add beam or service-area geometry.
2. **Q2 pfd limits and method.** Changes `pfd_limits.csv` and whether non-GSO needs more than a mask check.
3. **Q3 results format.** Changes `ResultRow` and the export; do this before Gate 4.
4. **Q4 special-interest XLS columns.** Changes `SpecialInterestStation` and whether limits come from the XLS.
5. **Q12 P.1546 and T/R 25-08 parameters.** Changes `p1546.py` defaults and `tr2508_thresholds.csv`.
6. **Q13 database access.** If `mdbtools` fails, the adapter reads partner CSV extracts instead; nothing else changes.
