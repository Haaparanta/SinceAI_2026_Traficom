import { fmtHz } from "../api";
import type { FindingContext } from "../types";
import { Empty } from "./ui";

const LANE_FILL: Record<string, string> = {
  terrestrial: "var(--chart-4)", space: "var(--chart-2)", passive: "var(--chart-3)", not_allocated: "var(--muted-foreground)",
};
const LANE_LABEL: Record<string, string> = {
  terrestrial: "Finnish terrestrial use", space: "Finnish space use", passive: "Passive (radio astronomy, EESS)", not_allocated: "Not allocated",
};

/** The lead group against the Finnish rows under it, on a linear axis padded by 15 %. */
export function SpectrumView({ ctx }: { ctx: FindingContext }) {
  const g = ctx.group;
  if (!g) return <Empty>This notice has no frequency group in this issue.</Empty>;
  const width = Math.max(g.freq_max_hz - g.freq_min_hz, 1);
  const pad = Math.max(width * 0.15, 5000);
  const lo = g.freq_min_hz - pad, hi = g.freq_max_hz + pad;
  const W = 960, L = 300, lane = 18, gap = 8;
  const pw = W - L - 16;
  const x = (hz: number) => L + ((Math.min(Math.max(hz, lo), hi) - lo) / (hi - lo)) * pw;
  const H = (ctx.lanes.length + 2) * (lane + gap) + 30;
  const cats = [...new Set(ctx.lanes.map((l) => l.category))];

  return (
    <div className="p-4">
      <p className="text-sm text-muted-foreground mb-3">
        Lead group {g.group_id ?? ""} against the rows of the Finnish frequency table it overlaps. Faded rows are secondary
        allocations. Hover a bar for the Traficom row.
      </p>
      <div className="flex flex-wrap gap-4 text-xs mb-2">
        <span className="flex items-center gap-1.5"><i className="inline-block w-3 h-3 rounded-sm" style={{ background: "var(--primary)" }} />The filing</span>
        {cats.map((c) => (
          <span key={c} className="flex items-center gap-1.5"><i className="inline-block w-3 h-3 rounded-sm" style={{ background: LANE_FILL[c] }} />{LANE_LABEL[c]}</span>
        ))}
      </div>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Spectrum overlap">
        <text x={L - 10} y={lane - 4} textAnchor="end" className="fill-foreground text-[12px] font-semibold">
          {g.direction?.replace(/_/g, " ")}
        </text>
        <rect x={x(g.freq_min_hz)} y={0} width={Math.max(x(g.freq_max_hz) - x(g.freq_min_hz), 2)} height={lane} rx={5} fill="var(--primary)">
          <title>{`${fmtHz(g.freq_min_hz)} to ${fmtHz(g.freq_max_hz)}`}</title>
        </rect>
        {ctx.lanes.map((l, i) => {
          const y = (i + 1) * (lane + gap);
          const ids = l.ids.length > 1 ? `IDs ${l.ids[0]}-${l.ids[l.ids.length - 1]}` : `ID ${l.ids[0]}`;
          return (
            <g key={i}>
              <text x={L - 10} y={y + lane - 5} textAnchor="end" className="fill-muted-foreground text-[11px]">
                {`${ids}: ${l.services.slice(0, 30)}`}
              </text>
              <rect x={x(l.lower_hz)} y={y} width={Math.max(x(l.upper_hz) - x(l.lower_hz), 2)} height={lane} rx={5}
                fill={LANE_FILL[l.category]} opacity={l.primary ? 1 : 0.5}>
                <title>{`Taajuusjakotaulukko ${ids}: ${fmtHz(l.lower_hz)} to ${fmtHz(l.upper_hz)}; ${l.services}; ${l.usage}${l.primary ? "" : " (secondary)"}`}</title>
              </rect>
            </g>
          );
        })}
        {[0, 0.5, 1].map((t) => {
          const hz = g.freq_min_hz + t * (g.freq_max_hz - g.freq_min_hz);
          return (
            <text key={t} x={x(hz)} y={H - 8} textAnchor={t === 0 ? "start" : t === 1 ? "end" : "middle"} className="num fill-muted-foreground text-[11px]">
              {fmtHz(hz)}
            </text>
          );
        })}
      </svg>
      {ctx.lanes.length === 0 && <Empty>No Finnish table row overlaps this group (a gap in the table: reported as unknown, not as no concern).</Empty>}
    </div>
  );
}
