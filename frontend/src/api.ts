import type { AnalysisBundle, IssueInfo, Kind, RefPoint, Region } from "./types";

async function get<T>(path: string): Promise<T> {
  const r = await fetch(`/api${path}`);
  if (!r.ok) throw new Error(`${path}: ${r.status} ${await r.text()}`);
  return r.json() as Promise<T>;
}

export const api = {
  issues: () => get<IssueInfo[]>("/issues"),
  analysis: (kind: Kind, issue: number) => get<AnalysisBundle>(`/analysis/${kind}/${issue}`),
  region: () => get<Region>("/reference/region"),
  points: () => get<RefPoint[]>("/reference/points"),
  exportUrl: (kind: Kind, issue: number) => `/api/export/${issue}?kind=${kind}`,
};

export function fmtHz(hz: number | null | undefined): string {
  if (hz == null) return "unknown";
  for (const [u, d] of [["GHz", 1e9], ["MHz", 1e6], ["kHz", 1e3]] as const) {
    if (Math.abs(hz) >= d) return `${+(hz / d).toPrecision(6)} ${u}`;
  }
  return `${hz} Hz`;
}

export const CONCERN_LABEL: Record<string, string> = { high: "High", medium: "Medium", review: "Review", low: "Low", none: "Not raised" };
