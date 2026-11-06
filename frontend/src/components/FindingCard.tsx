import { useEffect, useRef } from "react";
import type { Finding, FindingContext } from "../types";
import { ConcernBadge } from "./ui";

const KIND_LABEL: Record<string, string> = {
  itu_row: "ITU database row", finnish_table_row: "Finnish frequency table", special_interest_row: "Special-interest station",
  regulation: "Regulation", calculation: "Calculation",
};

/** The actionable output: concern, reason, every piece of evidence. Plain language only (serious-context rule). */
export function FindingCard({ finding, ctx, highlight }: { finding: Finding; ctx: FindingContext | undefined; highlight: string | null }) {
  const refs = useRef<Record<string, HTMLLIElement | null>>({});
  useEffect(() => {
    if (highlight) refs.current[highlight]?.scrollIntoView({ behavior: "smooth", block: "center" });
  }, [highlight]);
  const n = ctx?.notice ?? {};
  return (
    <div className="p-4 space-y-4">
      <header className="space-y-1">
        <div className="flex items-center gap-2">
          <ConcernBadge concern={finding.concern} />
          <span className="num text-xs text-muted-foreground">{finding.id}</span>
        </div>
        <h2 className="font-display text-xl font-semibold tracking-tight">{ctx?.title ?? finding.notice_id}</h2>
        <p className="text-xs text-muted-foreground num">
          Notice {finding.notice_id}{n.special_section ? ` · ${n.special_section}` : ""}{n.orbit ? ` · ${n.orbit}` : ""}
          {n.change ? ` · ${n.change}` : ""}{n.station_class ? ` · ${n.station_class}` : ""}
        </p>
      </header>
      <p className="text-[15px] leading-6">{finding.reason}</p>
      {n.all_sections?.length > 1 && (
        <p className="text-xs text-muted-foreground">Published with: {(n.all_sections as string[]).join(", ")}</p>
      )}
      <section>
        <h3 className="text-sm font-semibold mb-2">Evidence ({finding.evidence.length})</h3>
        <ol className="space-y-2" aria-label="Evidence">
          {finding.evidence.map((e) => (
            <li key={e.id} ref={(el) => { refs.current[e.id] = el; }} data-evidence-id={e.id}
              aria-current={highlight === e.id ? "true" : undefined}
              className={`rounded-xl border p-2.5 text-sm transition-colors ${highlight === e.id ? "border-ring bg-secondary" : "border-border"}`}>
              <div className="flex items-center gap-2 text-xs text-muted-foreground">
                <span className="num font-semibold text-foreground">{e.id}</span><span>{KIND_LABEL[e.kind]}</span>
              </div>
              <code className="num block text-xs mt-1 break-all">{e.locator}</code>
              <div className="mt-1 break-words">{e.excerpt}</div>
              <div className="text-[11px] text-muted-foreground mt-0.5">{e.source}</div>
            </li>
          ))}
        </ol>
      </section>
      {ctx?.factors && Object.keys(ctx.factors).length > 0 && (
        <details className="text-sm">
          <summary className="cursor-pointer font-semibold">How the rank was scored{ctx.score != null ? ` (${ctx.score})` : ""}</summary>
          <table className="w-full mt-2 text-xs">
            <tbody>
              {Object.entries(ctx.factors).map(([k, v]) => (
                <tr key={k} className="border-t border-border"><td className="py-1 pr-2 text-muted-foreground">{k.replace(/_/g, " ")}</td>
                  <td className="num">{Array.isArray(v) ? `${v[0]} (${v[1]})` : String(v)}</td></tr>
              ))}
            </tbody>
          </table>
        </details>
      )}
    </div>
  );
}
