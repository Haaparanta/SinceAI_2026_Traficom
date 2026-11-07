import type { KeyboardEvent } from "react";
import { CONCERN_LABEL } from "../api";
import type { AnalysisBundle, Concern, Region } from "../types";

// Whole-issue view: every flagged finding at once. Colour encodes the concern level (status), always with a legend and a
// text label on hover and focus; clicking or pressing Enter on a mark selects that finding. Every position comes from
// the cache (the GSO arc is computed by radar.pipeline.geography in scripts/build_cache.py), never from the screen.

const ORDER: Concern[] = ["high", "medium", "review", "low"];
const FILL: Record<Concern, string> = {
  high: "var(--risk-high-foreground)", medium: "var(--risk-medium-foreground)", review: "var(--chart-2)",
  low: "var(--risk-low-foreground)", none: "var(--muted-foreground)",
};

type Mark = { id: string; title: string; concern: Concern };

function activate(onSelect: (id: string) => void, id: string) {
  return {
    role: "button", tabIndex: 0, "aria-label": id, onClick: () => onSelect(id),
    onKeyDown: (e: KeyboardEvent) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); onSelect(id); } },
    style: { cursor: "pointer" },
  } as const;
}

function Legend({ counts }: { counts: Record<string, number> }) {
  return (
    <div className="flex flex-wrap gap-x-4 gap-y-1 text-xs text-muted-foreground" aria-label="Legend">
      {ORDER.filter((c) => counts[c]).map((c) => (
        <span key={c} className="inline-flex items-center gap-1.5">
          <svg width="10" height="10" aria-hidden="true"><circle cx="5" cy="5" r="4.5" fill={FILL[c]} /></svg>
          {`${CONCERN_LABEL[c]} (${counts[c]})`}
        </span>
      ))}
    </div>
  );
}

function fmtHz(hz: number): string {
  return hz >= 1e9 ? `${+(hz / 1e9).toPrecision(4)} GHz` : `${+(hz / 1e6).toPrecision(4)} MHz`;
}

/** Flagged findings on a log-frequency axis, one lane per concern level. */
function SpectrumOverview({ marks, selected, onSelect }: { marks: (Mark & { lo: number; hi: number })[]; selected: string | null; onSelect: (id: string) => void }) {
  const W = 640, lane = 30, top = 8, left = 64, right = 30;
  const lanes = ORDER.filter((c) => marks.some((m) => m.concern === c));
  const H = top + lane * lanes.length + 30;
  const lo = Math.floor(Math.log10(Math.min(...marks.map((m) => m.lo))));
  const hi = Math.ceil(Math.log10(Math.max(...marks.map((m) => m.hi))));
  const x = (hz: number) => left + ((Math.log10(hz) - lo) / Math.max(hi - lo, 1)) * (W - left - right);
  const ticks: number[] = [];
  for (let d = lo; d <= hi; d++) for (const k of [1, 3]) if (d + Math.log10(k) <= hi) ticks.push(k * 10 ** d);
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Flagged findings by frequency and concern">
      {ticks.map((t) => (
        <g key={t}>
          <line x1={x(t)} x2={x(t)} y1={top} y2={H - 24} stroke="var(--border)" />
          <text x={x(t)} y={H - 8} textAnchor="middle" className="fill-muted-foreground text-[11px]">{fmtHz(t)}</text>
        </g>
      ))}
      {lanes.map((c, i) => (
        <g key={c}>
          <text x={left - 8} y={top + i * lane + lane / 2 + 4} textAnchor="end" className="fill-foreground text-[11px]">{CONCERN_LABEL[c]}</text>
          {marks.filter((m) => m.concern === c).map((m) => {
            const w = Math.max(3, x(m.hi) - x(m.lo));
            const on = m.id === selected;
            return (
              <rect key={m.id} x={x(m.lo)} y={top + i * lane + 6} width={w} height={lane - 12} rx={2} fill={FILL[c]}
                fillOpacity={on ? 1 : 0.7} stroke={on ? "var(--foreground)" : "var(--card)"} strokeWidth={on ? 2 : 1}
                data-finding={m.id} {...activate(onSelect, m.id)}>
                <title>{`${m.id} ${m.title}: ${fmtHz(m.lo)} to ${fmtHz(m.hi)}, ${CONCERN_LABEL[c]}`}</title>
              </rect>
            );
          })}
        </g>
      ))}
    </svg>
  );
}

/** The geostationary arc as seen from Finland, with every flagged GSO filing on it. */
function ArcOverview({ bundle, selected, onSelect }: { bundle: AnalysisBundle; selected: string | null; onSelect: (id: string) => void }) {
  const arc = bundle.overview?.gso_arc ?? [];
  const W = 640, H = 260, left = 40, right = 14, top = 12, bottom = 30;
  // The window: where Finland can see the arc, with room on both sides; below -15 deg the curve only says "not visible".
  const LON0 = -100, LON1 = 150, minEl = -15;
  const maxEl = Math.max(...arc.map((p) => p.max_elevation_deg), 25);
  const x = (lon: number) => left + ((lon - LON0) / (LON1 - LON0)) * (W - left - right);
  const y = (el: number) => top + ((maxEl - Math.max(el, minEl)) / (maxEl - minEl)) * (H - top - bottom);
  const path = arc.filter((p) => p.lon >= LON0 && p.lon <= LON1)
    .map((p, i) => `${i ? "L" : "M"}${x(p.lon).toFixed(1)},${y(p.max_elevation_deg).toFixed(1)}`).join(" ");
  const gso = bundle.result.findings.filter((f) => f.concern !== "none" && bundle.context[f.id]?.notice.orbit === "GSO"
    && bundle.context[f.id]?.notice.longitude_deg != null && bundle.context[f.id]?.geo.detail.max_elevation_deg != null);
  const outside = gso.filter((f) => { const l = bundle.context[f.id].notice.longitude_deg as number; return l < LON0 || l > LON1; }).length;
  const peak = arc.reduce((a, b) => (b.max_elevation_deg > a.max_elevation_deg ? b : a), arc[0]);
  return (
    <>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Geostationary arc seen from Finland with the flagged filings">
        {[-90, -60, -30, 0, 30, 60, 90, 120, 150].map((l) => (
          <g key={l}>
            <line x1={x(l)} x2={x(l)} y1={top} y2={H - bottom} stroke="var(--border)" />
            <text x={x(l)} y={H - 10} textAnchor="middle" className="fill-muted-foreground text-[11px]">{l === 0 ? "0" : `${Math.abs(l)} ${l < 0 ? "W" : "E"}`}</text>
          </g>
        ))}
        {[0, 10, 20].map((e) => (
          <g key={e}>
            <line x1={left} x2={W - right} y1={y(e)} y2={y(e)} stroke={e === 0 ? "var(--muted-foreground)" : "var(--border)"} strokeDasharray={e === 10 ? "4 3" : undefined} />
            <text x={left - 6} y={y(e) + 4} textAnchor="end" className="fill-muted-foreground text-[11px]">{`${e}°`}</text>
          </g>
        ))}
        <text x={left + 6} y={y(10) - 4} className="fill-muted-foreground text-[11px]">low elevation below 10°</text>
        <text x={W - right - 4} y={y(0) - 4} textAnchor="end" className="fill-muted-foreground text-[11px]">horizon: not visible below</text>
        <path d={path} fill="none" stroke="var(--primary)" strokeWidth={2} />
        {gso.filter((f) => { const l = bundle.context[f.id].notice.longitude_deg as number; return l >= LON0 && l <= LON1; }).map((f) => {
          const c = bundle.context[f.id];
          const lon = c.notice.longitude_deg as number;
          const el = c.geo.detail.max_elevation_deg as number;
          const on = f.id === selected;
          return (
            <circle key={f.id} cx={x(lon)} cy={y(el)} r={on ? 7 : 5} fill={FILL[f.concern]} stroke={on ? "var(--foreground)" : "var(--card)"}
              strokeWidth={on ? 2.5 : 2} data-finding={f.id} {...activate(onSelect, f.id)}>
              <title>{`${f.id} ${c.title}: ${Math.abs(lon)} ${lon < 0 ? "W" : "E"}, highest elevation ${el} deg (${c.geo.detail.max_elevation_point}), ${CONCERN_LABEL[f.concern]}`}</title>
            </circle>
          );
        })}
      </svg>
      <p className="text-xs text-muted-foreground">
        {`Line: highest elevation of the geostationary arc from any Finnish reference point; peak ${peak?.max_elevation_deg.toFixed(1)} deg at ${peak?.lon} E (${peak?.point}). Dots: the ${gso.length} flagged GSO filings at their filed longitude${outside ? `, ${outside} outside this window` : ""}. Non-GSO and earth-station filings are not on the arc.`}
      </p>
    </>
  );
}

/** Every flagged foreign station around Finland, and the special-interest stations they share a channel with. */
function StationMap({ bundle, region, selected, onSelect }: { bundle: AnalysisBundle; region: Region | null; selected: string | null; onSelect: (id: string) => void }) {
  const V = { lon0: 8, lon1: 40, lat0: 52, lat1: 71.5 };      // east of 40 E the region file is clipped
  const W = 640;
  const H = Math.round((W * (V.lat1 - V.lat0)) / ((V.lon1 - V.lon0) * Math.cos((62 * Math.PI) / 180)));
  const x = (lon: number) => ((lon - V.lon0) / (V.lon1 - V.lon0)) * W;
  const y = (lat: number) => ((V.lat1 - lat) / (V.lat1 - V.lat0)) * H;
  const flagged = bundle.result.findings.filter((f) => f.concern !== "none" && bundle.context[f.id]?.notice.lat != null);
  const inView = flagged.filter((f) => { const n = bundle.context[f.id].notice; return n.lon >= V.lon0 && n.lon <= V.lon1 && n.lat >= V.lat0 && n.lat <= V.lat1; });
  const stations = new Map<string, { lat: number; lon: number }>();
  for (const f of flagged) for (const s of bundle.context[f.id].stations ?? []) stations.set(s.number, s);
  const tri = (cx: number, cy: number) => `${cx.toFixed(1)},${(cy - 5).toFixed(1)} ${(cx + 4.5).toFixed(1)},${(cy + 3.5).toFixed(1)} ${(cx - 4.5).toFixed(1)},${(cy + 3.5).toFixed(1)}`;
  const order = [...inView].sort((a, b) => ORDER.indexOf(b.concern) - ORDER.indexOf(a.concern));
  return (
    <>
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Flagged foreign stations around Finland">
        {region?.features.map((f) => f.geometry.coordinates.map((poly, i) => (
          <polygon key={`${f.properties.itu}-${i}`} points={poly[0].map(([lo, la]) => `${x(lo).toFixed(1)},${y(la).toFixed(1)}`).join(" ")}
            fill={f.properties.itu === "FIN" ? "var(--map-footprint)" : "var(--map-land)"}
            stroke={f.properties.itu === "FIN" ? "var(--map-focus-outline)" : "var(--muted-foreground)"}
            strokeOpacity={f.properties.itu === "FIN" ? 1 : 0.45} strokeWidth={f.properties.itu === "FIN" ? 1.2 : 0.6} />
        )))}
        {[...stations.entries()].map(([num, s]) => (
          <polygon key={num} points={tri(x(s.lon), y(s.lat))} fill="var(--chart-3)" stroke="var(--card)" strokeWidth={1}>
            <title>{`Special-interest station ${num}`}</title>
          </polygon>
        ))}
        {order.map((f) => {
          const n = bundle.context[f.id].notice;
          const on = f.id === selected;
          return (
            <circle key={f.id} cx={x(n.lon)} cy={y(n.lat)} r={on ? 6.5 : 4.5} fill={FILL[f.concern]} stroke={on ? "var(--foreground)" : "var(--card)"}
              strokeWidth={on ? 2.5 : 1.5} data-finding={f.id} {...activate(onSelect, f.id)}>
              <title>{`${f.id} ${bundle.context[f.id].title}: ${n.freq_hz ? fmtHz(n.freq_hz) : "frequency unknown"}, ${CONCERN_LABEL[f.concern]}`}</title>
            </circle>
          );
        })}
      </svg>
      <p className="text-xs text-muted-foreground">
        {`Dots: the ${inView.length} flagged stations in this window${flagged.length > inView.length ? ` (${flagged.length - inView.length} more outside it)` : ""}. Triangles: the ${stations.size} special-interest stations on their channels.`}
      </p>
    </>
  );
}

export function OverviewView({ bundle, region, selected, onSelect }: { bundle: AnalysisBundle; region: Region | null; selected: string | null; onSelect: (id: string) => void }) {
  const flagged = bundle.result.findings.filter((f) => f.concern !== "none");
  const counts: Record<string, number> = {};
  for (const f of flagged) counts[f.concern] = (counts[f.concern] ?? 0) + 1;
  const marks = flagged.flatMap((f) => {
    const g = bundle.context[f.id]?.group;
    return g && g.freq_min_hz > 0 ? [{ id: f.id, title: bundle.context[f.id].title, concern: f.concern, lo: g.freq_min_hz, hi: Math.max(g.freq_max_hz, g.freq_min_hz + 1) }] : [];
  });
  const space = bundle.result.kind === "space";
  return (
    <div className="p-4 space-y-6" aria-label="Issue overview" role="region">
      <Legend counts={counts} />
      <section aria-label={space ? "Geostationary arc" : "Station map"} className="space-y-2">
        <h3 className="text-sm font-semibold">{space ? "Geostationary arc seen from Finland" : "Flagged stations around Finland"}</h3>
        {space ? <ArcOverview bundle={bundle} selected={selected} onSelect={onSelect} />
          : <StationMap bundle={bundle} region={region} selected={selected} onSelect={onSelect} />}
      </section>
      <section aria-label="Frequencies" className="space-y-2">
        <h3 className="text-sm font-semibold">Where in the spectrum</h3>
        {marks.length ? <SpectrumOverview marks={marks} selected={selected} onSelect={onSelect} /> : <p className="text-sm text-muted-foreground">No frequency ranges.</p>}
        <p className="text-xs text-muted-foreground">{`${marks.length} flagged findings by the lead frequency range, log scale. Hover for details; click to open a finding.`}</p>
      </section>
    </div>
  );
}
