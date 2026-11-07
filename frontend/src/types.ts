// Mirrors backend/radar/models.py one to one (pm_pack/06). FROZEN after Gate 1: change both files in one commit.
export type Kind = "space" | "terrestrial";
export type Concern = "none" | "low" | "medium" | "high" | "review";
export interface Evidence { id: string; kind: "itu_row" | "finnish_table_row" | "special_interest_row" | "regulation" | "calculation"; source: string; locator: string; excerpt: string; }
export interface CalcInput { name: string; value: number | string; unit: string; evidence_id: string; }
export interface CalcTrace { method: "pfd_gso_worst_case" | "pfd_ngso_worst_case" | "p1546_field_strength" | "none"; inputs: CalcInput[]; formula: string; result_value: number | null; result_unit: string; limit_value: number | null; limit_evidence_id: string | null; margin_db: number | null; label: "indicative" | "confirmed"; notes: string[]; }
export interface Finding { id: string; kind: Kind; issue: number; notice_id: string; group_id: string | null; matched_subband_ids: number[]; matched_station_numbers: string[]; overlap_hz: number; geo_relevance: "visible" | "low_elevation" | "not_visible" | "near_border" | "far" | "unknown"; calc: CalcTrace; concern: Concern; reason: string; explanation: string | null; evidence: Evidence[]; }
export interface AnalysisResult { issue: number; kind: Kind; screened: number; flagged: number; provenance_coverage_pct: number; findings: Finding[]; from_cache: boolean; }

// Screen context written by scripts/build_cache.py (not part of the frozen contract). Its notice, geometry and factor
// fields are free-form JSON that differs between space and terrestrial findings, so they are typed loosely on purpose.
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type Json = Record<string, any>;
export interface Lane { ids: number[]; lower_hz: number; upper_hz: number; services: string; usage: string; category: "terrestrial" | "space" | "passive" | "not_allocated"; space_direction: string | null; primary: boolean; }
export interface StationContext { number: string; class: string | null; lat: number; lon: number; centre_hz: number; bandwidth_hz: number; row: number; reach: Json; }
export interface GeoContext { relevance: string; method: string; note: string; detail: Json; }
export interface FindingContext {
  title: string;
  notice: Json;
  group: (Json & { freq_min_hz: number; freq_max_hz: number; direction: string }) | null;
  lanes: Lane[];
  geo: GeoContext;
  rule: string | null;
  score: number | null;
  factors: Json;
  stations?: StationContext[];
}
export type DecisionKind = "approve" | "dismiss" | "investigate";
// One line of the audit log: a ReviewDecision (models.py) plus where it applies and the hash chain.
export interface AuditEntry { seq: number; kind: Kind; issue: number; finding_id: string; notice_id: string; concern_at_decision: Concern; decision: DecisionKind; reviewer: string; note: string | null; at: string; prev_hash: string; hash: string; }
export interface AuditLog { chain: { ok: boolean; entries: number; first_bad_seq: number | null; head?: string }; entries: AuditEntry[]; }
export interface AnalysisBundle { result: AnalysisResult; context: Record<string, FindingContext>; decisions: Record<string, AuditEntry>; omitted?: { not_raised: number; note: string }; }
// Step D2: grounded explanation and letter draft (backend/radar/llm/drafts.py).
export interface SpecialInterestStation { station_number: string; centre_hz: number; bandwidth_hz: number; lat: number; lon: number; antenna_height_m: number | null; antenna_direction_deg: number | null; antenna_directivity: string | null; limit_value: number | null; limit_unit: string | null; tx_hz: number | null; licence_class: string | null; erp_w: number | null; antenna_gain_db: number | null; ground_height_m: number | null; source_row: number | null; quality_flags: string[]; }
export interface Explanation { text: string; cited_evidence_ids: string[]; }
export interface Letter { finding_id: string; to_administration: string; subject: string; body_markdown: string; cited_evidence_ids: string[]; }
export interface DraftResult<T> { output: T; source: string; check: string; notes: string[]; }
export interface LLMStatus { available: boolean; model: string; reason: string; demo_mode: boolean; }
export interface IssueInfo { kind: Kind; issue: number; screened: number; flagged: number; provenance_coverage_pct: number; }
export interface RefPoint { name: string; lat: number; lon: number; }
export interface Region { features: { properties: { itu: string; name: string }; geometry: { coordinates: number[][][][] } }[]; }
