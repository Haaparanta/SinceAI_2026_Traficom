# AGENTS.md — Master Context (Filing Radar)

> [!WARNING]
> **Draft — based on missing data**
> This architecture was designed from `README.md` alone. The data schemas below are **our own `[HYPOTHESIS]` model**, not ITU or Traficom formats. Do not treat any field name as an official spec. When real partner data arrives, change **only** the adapter (`backend/app/adapters/partner.py`) and, if needed, add fields to the models. See "Final Verification" at the end.
>
> To use: `ln -s pm_pack/06_AGENTS_Master_Context.md AGENTS.md` (and the same for `CLAUDE.md` / `.cursorrules`).

---

## Mission
Help Traficom spectrum experts discover international satellite filings that may affect systems operating in Finland, explain why with cited evidence, and let the expert decide. `[README]`

**Rules that never change**
1. The tool suggests; a human decides. No automatic sending, rejecting or dismissing.
2. No finding without evidence. Every `Finding` has ≥1 `Evidence`.
3. Unknown stays unknown. Extraction never invents a missing value; it returns `null` and the UI shows "unknown".
4. Technical calculations beyond simple overlap are labelled `indicative`.

---

## Provisional Tech Stack `[HYPOTHESIS]`
- **Backend:** Python 3.12, FastAPI, Pydantic v2, Shapely (geometry), pytest
- **AI:** Claude API (`claude-sonnet-5-5`) with structured output for extraction and explanations. If the NDA forbids cloud models `[GAP]`, swap to a local open-weight model behind the same `LLMClient` interface.
- **Frontend:** React + Vite + TypeScript, shadcn/ui + Tailwind CSS v4, MapLibre GL (map), Recharts (frequency chart)
- **Design system:** Girlypop theme v2. Import `design/girlypop.css` into `frontend/src/globals.css` and follow `design/girlypop-theme.md`. Use only theme tokens (no hex codes); risk badges use `risk-*` tokens with a text label; put `bg-sigil` on the app's `<body>` for the hand-drawn cybersigilism mosaic background (see `design/sigils/preview.html`), and keep text that sits directly on it in `foreground` or `secondary-foreground`; no emoji anywhere in the UI or docs, and no playful copy on findings, decisions or exports.
- **Storage:** JSON files in `/data` (no database needed for the hackathon)

## Folder Tree
```
.
├── AGENTS.md -> pm_pack/06_AGENTS_Master_Context.md
├── backend/
│   └── app/
│       ├── main.py              # FastAPI routes
│       ├── models.py            # Pydantic contracts (FROZEN, see below)
│       ├── config.py            # DATA_SOURCE, DEMO_MODE, LLM settings
│       ├── adapters/
│       │   ├── base.py          # DataAdapter interface
│       │   ├── synthetic.py     # Branch B
│       │   └── partner.py       # Branch A (stub until data arrives)
│       ├── pipeline/
│       │   ├── extract.py       # raw filing -> Filing
│       │   ├── match.py         # Filing x ProtectedAsset -> overlaps
│       │   ├── score.py         # overlaps -> RiskScore
│       │   └── explain.py       # LLM explanation grounded in Evidence
│       ├── llm.py               # LLMClient interface
│       └── cache.py             # Demo Mode
├── frontend/src/
│   ├── types.ts                 # mirrors models.py
│   ├── App.tsx                  # One-Screen layout
│   └── components/{InputBar,MapView,BandChart,FindingsList,Metrics}.tsx
├── data/
│   ├── seed/                    # synthetic, committed
│   ├── partner/                 # real data, GIT-IGNORED
│   └── cache/                   # Demo Mode JSON, committed
├── scripts/generate_synthetic.py
└── tests/
```

---

## Data Contracts (Pydantic) `[HYPOTHESIS schema]`

```python
from datetime import date, datetime
from enum import Enum
from typing import Literal
from pydantic import BaseModel, Field

class FilingStage(str, Enum):
    advance_publication = "advance_publication"
    coordination = "coordination"
    notification = "notification"
    unknown = "unknown"

class FrequencyRange(BaseModel):
    min_mhz: float
    max_mhz: float
    direction: Literal["uplink", "downlink", "unknown"] = "unknown"

class ServiceArea(BaseModel):
    center_lat: float | None = None
    center_lon: float | None = None
    radius_km: float | None = None
    polygon: list[tuple[float, float]] | None = None  # (lat, lon)

class Orbit(BaseModel):
    type: Literal["GSO", "NGSO", "unknown"]
    longitude_deg: float | None = None   # GSO
    altitude_km: float | None = None     # NGSO
    inclination_deg: float | None = None # NGSO

class Filing(BaseModel):
    id: str
    network_name: str
    administration: str | None = None
    stage: FilingStage = FilingStage.unknown
    published: date | None = None
    comment_deadline: date | None = None   # [HYPOTHESIS]
    orbit: Orbit
    frequencies: list[FrequencyRange]
    service_area: ServiceArea | None = None
    max_power_dbw: float | None = None     # indicative only
    source_ref: str                        # file + page/line

class ProtectedAsset(BaseModel):
    id: str
    name: str
    lat: float
    lon: float
    band: FrequencyRange
    service: str
    protection_threshold_db: float | None = None  # [HYPOTHESIS]
    source_ref: str

class Evidence(BaseModel):
    id: str
    kind: Literal["filing", "asset", "rule", "calculation"]
    source_ref: str
    excerpt: str

class Finding(BaseModel):
    id: str
    filing_id: str
    asset_id: str
    freq_overlap_mhz: float
    geo_overlap: bool
    factors: dict[str, float]           # factor name -> contribution 0..100
    score: int = Field(ge=0, le=100)
    explanation: str | None = None      # must only cite evidence IDs below
    evidence: list[Evidence] = Field(min_length=1)
    indicative: bool = False

class AnalysisResult(BaseModel):
    filing: Filing
    findings: list[Finding]
    overall_score: int = Field(ge=0, le=100)
    minutes_saved_estimate: float       # [HYPOTHESIS formula]
    evidence_coverage_pct: float
    from_cache: bool = False

class ReviewDecision(BaseModel):
    finding_id: str
    decision: Literal["approve", "dismiss", "investigate"]
    reviewer: str
    note: str | None = None
    at: datetime
```

`frontend/src/types.ts` mirrors these one-to-one. **`models.py` is frozen after Gate 1**; changes go through the PM and are applied to both files in the same commit.

---

## Branch A / Branch B Data Adapter Rule

```python
class DataAdapter(Protocol):
    def list_filings(self) -> list[Filing]: ...
    def get_filing(self, filing_id: str) -> Filing: ...
    def list_assets(self) -> list[ProtectedAsset]: ...
```

- `DATA_SOURCE=synthetic` → `adapters/synthetic.py` (reads `data/seed/`)
- `DATA_SOURCE=partner` → `adapters/partner.py` (reads `data/partner/`)
- **Swapping synthetic for real data must be one file edit: `partner.py`.** Pipeline, API and UI never import an adapter directly; they get it from `config.get_adapter()`.

## Deterministic Demo Mode Contract

- `DEMO_MODE=1` (or the UI toggle) → `POST /analyze` for `sample_1|sample_2|sample_3` returns `data/cache/<sample_id>.json` and sets `from_cache=true`. No network calls.
- `scripts/build_cache.py` regenerates the cache from a live run; commit the output.
- The cached JSON must validate against `AnalysisResult`. A test checks this.
- The video and the Sunday demo are recorded in Demo Mode.

---

## Multi-Agent Division Rules

| Agent | Owns | Must not touch |
|---|---|---|
| **Claude Code** | `backend/app/pipeline/`, `llm.py`, prompts, `models.py` (with PM approval) | `frontend/` |
| **Cursor** | `frontend/` | `backend/app/pipeline/` |
| **Codex** | `scripts/`, `tests/`, `adapters/` | UI components, prompts |
| **Antigravity** | Visual polish, map styling, video/deck assets | Contracts, pipeline |

Shared rules:
1. One agent per folder at a time. Small commits, one feature per branch.
2. Contracts first: if an agent needs a new field, it stops and asks the PM.
3. Every agent runs `pytest` (backend) or `npm run build` (frontend) before committing.
4. No secrets or partner data in commits. `data/partner/` and `.env` stay git-ignored.

---

## Final Verification: Top 5 Gaps That Could Change This Architecture `[GAP - ASK PARTNER]`

1. **Real data format** (SRS `.mdb`, GXT, PDF circulars, API?) → rewrites `adapters/partner.py` and maybe `extract.py`.
2. **Protected-asset list** (exists? shareable? format?) → changes `ProtectedAsset` and the matching logic.
3. **Cloud LLM allowed?** → swaps `LLMClient` to a local model; may change hosting.
4. **Expert's actual output** (memo, ITU comment, coordination request) → changes `ReviewDecision` and the export feature.
5. **What evaluators judge on Sunday** → may move effort between batch ranking, explanations and interference maths.
