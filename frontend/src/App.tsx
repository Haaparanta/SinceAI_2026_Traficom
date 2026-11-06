import { useEffect, useState } from "react";
import { api } from "./api";
import { AuditLogView } from "./components/AuditLogView";
import { CalcTraceView } from "./components/CalcTraceView";
import { DecisionPanel } from "./components/DecisionPanel";
import { DraftsPanel } from "./components/DraftsPanel";
import { FindingCard } from "./components/FindingCard";
import { MapView } from "./components/MapView";
import { RankedList } from "./components/RankedList";
import { SpectrumView } from "./components/SpectrumView";
import { Card, Empty, Segmented, Stat } from "./components/ui";
import type { AnalysisBundle, AuditEntry, IssueInfo, Kind, RefPoint, Region } from "./types";

type Tab = "spectrum" | "map" | "calculation" | "audit";
const REVIEWER_KEY = "filing-radar.reviewer";

function storedReviewer(): string {
  try { return localStorage.getItem(REVIEWER_KEY) ?? ""; } catch { return ""; }
}

export default function App() {
  const [issues, setIssues] = useState<IssueInfo[]>([]);
  const [current, setCurrent] = useState<{ kind: Kind; issue: number } | null>(null);
  const [bundle, setBundle] = useState<AnalysisBundle | null>(null);
  const [selected, setSelected] = useState<string | null>(null);
  const [tab, setTab] = useState<Tab>("spectrum");
  const [highlight, setHighlight] = useState<string | null>(null);
  const [region, setRegion] = useState<Region | null>(null);
  const [points, setPoints] = useState<RefPoint[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [reviewer, setReviewer] = useState<string>(storedReviewer);
  const [auditVersion, setAuditVersion] = useState(0);

  useEffect(() => {
    try { localStorage.setItem(REVIEWER_KEY, reviewer); } catch { /* storage unavailable: name lasts for this visit */ }
  }, [reviewer]);

  const onDecided = (e: AuditEntry) => {
    setBundle((b) => (b ? { ...b, decisions: { ...b.decisions, [e.finding_id]: e } } : b));
    setAuditVersion((v) => v + 1);
  };

  useEffect(() => {
    // Default to the first issue only if the user has not chosen one yet: a late response must not undo a click.
    api.issues().then((xs) => {
      setIssues(xs);
      if (xs.length) setCurrent((c) => c ?? { kind: xs[0].kind, issue: xs[0].issue });
    }).catch((e) => setError(String(e)));
    api.region().then(setRegion).catch(() => undefined);
    api.points().then(setPoints).catch(() => undefined);
  }, []);

  useEffect(() => {
    if (!current) return;
    let stale = false;            // ignore a response for an issue that is no longer selected
    setBundle(null);
    api.analysis(current.kind, current.issue).then((b) => {
      if (stale) return;
      setBundle(b);
      const first = b.result.findings.find((f) => f.concern !== "none") ?? b.result.findings[0];
      setSelected(first?.id ?? null);
      setTab(first?.calc.method !== "none" ? "calculation" : "spectrum");
    }).catch((e) => { if (!stale) setError(String(e)); });
    return () => { stale = true; };
  }, [current]);

  const finding = bundle?.result.findings.find((f) => f.id === selected) ?? null;
  const ctx = finding ? bundle?.context[finding.id] : undefined;
  const r = bundle?.result;
  const showEvidence = (id: string) => { setHighlight(id); setTimeout(() => setHighlight(null), 2500); };

  return (
    <div className="bg-sigil min-h-screen">
      <div className="mx-auto max-w-[1600px] px-4 py-4 flex flex-col gap-4 lg:h-screen">
        <header className="flex flex-wrap items-end gap-4">
          <div className="mr-auto">
            <h1 className="font-display text-2xl font-bold tracking-tight text-foreground">Filing Radar</h1>
            <p className="text-sm text-secondary-foreground">ITU BR IFIC notices that may affect radio frequency use in Finland. The tool suggests; a specialist decides.</p>
          </div>
          <label className="flex flex-col text-xs text-secondary-foreground">
            Reviewer
            <input value={reviewer} onChange={(e) => setReviewer(e.target.value)} placeholder="Your name" aria-label="Reviewer"
              className="mt-1 w-44 rounded-xl border border-input bg-card px-3 py-2 text-sm text-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2" />
          </label>
          {issues.length > 0 && current && (
            <Segmented label="Issue" value={`${current.kind}:${current.issue}`}
              options={issues.map((i) => ({ value: `${i.kind}:${i.issue}`, label: `${i.kind === "space" ? "Space" : "Terrestrial"} ${i.issue}` }))}
              onChange={(v) => { const [k, n] = v.split(":"); setCurrent({ kind: k as Kind, issue: Number(n) }); }} />
          )}
          {r && (
            <div className="flex flex-wrap gap-2" aria-label="Proof metrics">
              <Stat value={r.screened.toLocaleString("en")} label="notices screened" />
              <Stat value={r.flagged.toLocaleString("en")} label="flagged" />
              <Stat value={`${r.provenance_coverage_pct} %`} label="provenance coverage" />
              <a href={api.exportUrl(r.kind, r.issue)} className="self-center rounded-full bg-primary text-primary-foreground px-4 py-2 text-sm font-semibold min-h-11 inline-flex items-center">
                Export results
              </a>
            </div>
          )}
        </header>

        {error && <Card className="p-4 text-sm"><b>Could not load data.</b> Start the API (make api) and build the cache (scripts/build_cache.py). {error}</Card>}

        {bundle && (
          <main className="grid gap-4 flex-1 min-h-0 grid-cols-1 lg:grid-cols-[340px_minmax(0,1fr)_420px]">
            <Card className="min-h-0 overflow-hidden flex flex-col max-h-[70vh] lg:max-h-none">
              <RankedList bundle={bundle} selected={selected} onSelect={(id) => { setSelected(id); }} />
              {bundle.omitted && <p className="text-xs text-muted-foreground p-3 border-t border-border">{bundle.omitted.not_raised.toLocaleString("en")} notices not raised; {bundle.omitted.note}.</p>}
            </Card>
            <Card className="min-h-0 overflow-y-auto">
              <div className="p-3 border-b border-border flex items-center gap-3">
                <Segmented label="Central view" value={tab} onChange={setTab}
                  options={[{ value: "spectrum", label: "Spectrum" }, { value: "map", label: "Map" }, { value: "calculation", label: "Calculation" }, { value: "audit", label: "Audit log" }]} />
              </div>
              {tab === "audit" ? <AuditLogView kind={bundle.result.kind} issue={bundle.result.issue} version={auditVersion} onSelect={setSelected} />
                : !finding || !ctx ? <Empty>Select a finding.</Empty>
                : tab === "spectrum" ? <SpectrumView ctx={ctx} />
                : tab === "map" ? <MapView ctx={ctx} region={region} points={points} />
                : <CalcTraceView calc={finding.calc} onEvidence={showEvidence} />}
            </Card>
            <Card className="min-h-0 overflow-y-auto">
              {finding ? (
                <FindingCard finding={finding} ctx={ctx} highlight={highlight}
                  drafts={<DraftsPanel findingId={finding.id} onEvidence={showEvidence} />}
                  decision={<DecisionPanel findingId={finding.id} reviewer={reviewer} onDecided={onDecided} />} />
              ) : <Empty>Select a finding.</Empty>}
            </Card>
          </main>
        )}
        {!bundle && !error && <Empty>Loading the analysis.</Empty>}
      </div>
    </div>
  );
}
