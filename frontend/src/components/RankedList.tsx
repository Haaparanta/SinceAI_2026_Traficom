import { useMemo, useState } from "react";
import { DECISION_LABEL, fmtHz } from "../api";
import type { AnalysisBundle, Concern, Finding } from "../types";
import { ConcernBadge } from "./ui";

const LEVELS: Concern[] = ["high", "medium", "review", "low", "none"];

function keyNumber(f: Finding): string {
  if (f.calc.margin_db != null) return `${f.calc.margin_db > 0 ? "+" : ""}${f.calc.margin_db.toFixed(1)} dB`;
  return "";
}

export function RankedList({ bundle, selected, onSelect }: {
  bundle: AnalysisBundle; selected: string | null; onSelect: (id: string) => void;
}) {
  const [levels, setLevels] = useState<Set<Concern>>(new Set(["high", "medium", "review", "low"]));
  const [q, setQ] = useState("");
  const counts = useMemo(() => {
    const c: Record<string, number> = {};
    for (const f of bundle.result.findings) c[f.concern] = (c[f.concern] ?? 0) + 1;
    return c;
  }, [bundle]);
  const rows = bundle.result.findings.filter((f) => {
    if (!levels.has(f.concern)) return false;
    if (!q) return true;
    const ctx = bundle.context[f.id];
    return `${f.id} ${f.notice_id} ${ctx?.title ?? ""} ${f.reason}`.toLowerCase().includes(q.toLowerCase());
  });
  const toggle = (l: Concern) => setLevels((s) => {
    const n = new Set(s);
    if (n.has(l)) n.delete(l); else n.add(l);
    return n;
  });

  return (
    <div className="flex flex-col min-h-0 h-full">
      <div className="p-3 border-b border-border space-y-2">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Search network, station, notice"
          aria-label="Search findings"
          className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2" />
        <div className="flex flex-wrap gap-1.5" role="group" aria-label="Filter by concern">
          {LEVELS.filter((l) => counts[l]).map((l) => (
            <button key={l} type="button" onClick={() => toggle(l)} aria-pressed={levels.has(l)}
              title={levels.has(l) ? "Shown: click to hide" : "Hidden: click to show"}
              className={`rounded-full border px-2.5 py-1 text-xs transition-colors ${levels.has(l) ? "border-ring bg-card" : "border-dashed border-border bg-transparent [&>[data-concern]]:grayscale"}`}>
              <ConcernBadge concern={l} /> <span className="num ml-1">{counts[l]}</span>
            </button>
          ))}
        </div>
      </div>
      <ol className="overflow-y-auto flex-1" aria-label="Ranked findings">
        {rows.map((f) => {
          const ctx = bundle.context[f.id];
          const g = ctx?.group;
          const d = bundle.decisions?.[f.id];
          return (
            <li key={f.id} className="row-lazy">
              <button type="button" onClick={() => onSelect(f.id)} aria-current={selected === f.id}
                className={`w-full text-left px-3 py-2.5 border-b border-border transition-colors ${selected === f.id ? "bg-secondary" : "hover:bg-muted"}`}>
                <div className="flex items-center gap-2">
                  <ConcernBadge concern={f.concern} />
                  <span className="text-sm font-medium truncate">{ctx?.title ?? f.notice_id}</span>
                  {d && <span className="shrink-0 rounded-full border border-border px-2 py-0.5 text-[11px] text-secondary-foreground" title={`${d.reviewer}: ${d.note ?? ""}`}>{DECISION_LABEL[d.decision]}</span>}
                  <span className="num ml-auto shrink-0 whitespace-nowrap text-xs text-muted-foreground">{keyNumber(f)}</span>
                </div>
                <div className="num text-xs text-muted-foreground mt-0.5 truncate">
                  {f.id} · {g ? `${fmtHz(g.freq_min_hz)} to ${fmtHz(g.freq_max_hz)}` : "no group"} · {f.geo_relevance.replace("_", " ")}
                </div>
              </button>
            </li>
          );
        })}
        {rows.length === 0 && <li className="p-4 text-sm text-muted-foreground">No findings match these filters.</li>}
      </ol>
    </div>
  );
}
