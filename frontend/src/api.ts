import type { AnalysisBundle, AuditEntry, AuditLog, DecisionKind, DraftResult, Explanation, IssueInfo, Kind, Letter, LLMStatus, RefPoint, Region } from "./types";

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`/api${path}`);
  if (!r.ok) throw new Error(`${path}: ${r.status} ${await r.text()}`);
  return r.json() as Promise<T>;
}

async function post<T>(path: string): Promise<T> {
  const r = await fetch(`/api${path}`, { method: "POST" });
  if (!r.ok) throw new Error(`${path}: ${r.status} ${await r.text()}`);
  return r.json() as Promise<T>;
}

const seg = encodeURIComponent;   // path segments come from data files: encode them

export const api = {
  issues: () => get<IssueInfo[]>("/issues"),
  analysis: (kind: Kind, issue: number) => get<AnalysisBundle>(`/analysis/${seg(kind)}/${seg(issue)}`),
  region: () => get<Region>("/reference/region"),
  points: () => get<RefPoint[]>("/reference/points"),
  exportUrl: (kind: Kind, issue: number) => `/api/export/${seg(issue)}?kind=${seg(kind)}`,
  audit: (kind: Kind, issue: number) => get<AuditLog>(`/audit?issue=${seg(issue)}&kind=${seg(kind)}`),
  findingDecisions: (id: string) => get<AuditEntry[]>(`/findings/${seg(id)}/decisions`),
  llmStatus: () => get<LLMStatus>("/llm/status"),
  explain: (id: string) => post<DraftResult<Explanation>>(`/findings/${seg(id)}/explanation`),
  letter: (id: string) => post<DraftResult<Letter>>(`/findings/${seg(id)}/letter`),
  decide: async (id: string, body: { decision: DecisionKind; reviewer: string; note: string }): Promise<AuditEntry> => {
    const r = await fetch(`/api/findings/${seg(id)}/decision`, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body),
    });
    if (!r.ok) throw new Error(`${r.status}: ${await r.text()}`);
    return r.json() as Promise<AuditEntry>;
  },
};

export const DECISION_LABEL: Record<DecisionKind, string> = { approve: "Approved", dismiss: "Dismissed", investigate: "Investigate" };

export function fmtTime(iso: string): string {
  const d = new Date(iso);
  return `${d.toLocaleDateString("en-GB")} ${d.toLocaleTimeString("en-GB", { hour: "2-digit", minute: "2-digit" })}`;
}

export function fmtHz(hz: number | null | undefined): string {
  if (hz == null) return "unknown";
  for (const [u, d] of [["GHz", 1e9], ["MHz", 1e6], ["kHz", 1e3]] as const) {
    if (Math.abs(hz) >= d) return `${+(hz / d).toPrecision(6)} ${u}`;
  }
  return `${hz} Hz`;
}

export const CONCERN_LABEL: Record<string, string> = { high: "High", medium: "Medium", review: "Review", low: "Low", none: "Not raised" };
