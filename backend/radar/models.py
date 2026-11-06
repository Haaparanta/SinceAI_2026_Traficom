"""Data contracts, copied one to one from pm_pack/06_AGENTS_Master_Context.md.

FROZEN after Gate 1 (Fri 23:30): a new field needs the PM and lands here and in frontend/src/types.ts in one commit.
"""
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


class SpecialInterestStation(BaseModel):      # one row of Traficom_SinceAI_Frequencies_of_interest_v05112026.xlsx
    station_number: str
    centre_hz: int                            # RX frequency: the channel the station receives on, which is protected
    bandwidth_hz: int
    lat: float
    lon: float
    antenna_height_m: float | None = None     # above ground level
    antenna_direction_deg: float | None = None
    antenna_directivity: str | None = None    # "D" directional, "ND" non-directional
    limit_value: float | None = None          # the XLS gives no limits; kept for a future table
    limit_unit: str | None = None
    # Added 7 Nov 2026 with the PM's approval (the XLS has TX and RX frequencies and more antenna data):
    tx_hz: int | None = None
    licence_class: str | None = None          # BC, BT, FX, MVV, MUUT or None as filed
    erp_w: float | None = None                # radiated power in W when the unit is given; unknown otherwise
    antenna_gain_db: float | None = None      # as filed ("Ant gain (dB)"), reference not stated
    ground_height_m: float | None = None
    source_row: int | None = None             # spreadsheet row number, for evidence
    quality_flags: list[str] = []             # what the reader noticed and did (rule 3: values are never invented)


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
