import { useMemo, useState } from "react";
import { CONCERN_LABEL, DECISION_LABEL, fmtHz } from "../api";
import type { AnalysisBundle, Concern, DecisionKind, FindingContext, Region } from "../types";
import { ConcernBadge } from "./ui";

// Every located datapoint of one analysis on one map: terrestrial notified stations (raised or not), every earth
// station of the space filings, and every special-interest station (bundle.map, backend/radar/map_layers.py). Cache
// files built before those layers existed still work: the map then shows what the findings carry. Each marker carries its type (shape and label)
// and its state (concern level, reviewer decision, change for terrestrial notices); colour is never the only signal.

type PointType = "terrestrial" | "earth_station" | "special_interest";
type ReviewState = DecisionKind | "open";

interface MapPoint {
  key: string;
  type: PointType;
  name: string;
  typeLabel: string;          // "Base station (FB), form T12", "Earth station, specific", ...
  administration: string | null;
  lat: number;
  lon: number;
  concern: Concern;           // the finding's concern; for a special-interest station, the highest among the findings that reach it
  review: ReviewState;
  change: string | null;      // terrestrial: new, modified, unchanged
  findingIds: string[];
  facts: string[];            // short plain-language lines for the detail box and the tooltip
}

const TYPE_LABEL: Record<PointType, string> = {
  terrestrial: "Terrestrial station",
  earth_station: "Earth station",
  special_interest: "Special-interest station",
};
const TYPES: PointType[] = ["terrestrial", "earth_station", "special_interest"];
const LEVELS: Concern[] = ["high", "medium", "review", "low", "none"];
const REVIEW_STATES: ReviewState[] = ["open", "investigate", "approve", "dismiss"];
const REVIEW_LABEL: Record<ReviewState, string> = { open: "Not reviewed", ...DECISION_LABEL };
const STATION_CLASS: Record<string, string> = { FB: "Base station", FL: "Land station", ML: "Land mobile", MO: "Mobile" };
const EARTH_STATION_TYPE: Record<string, string> = { S: "specific", T: "typical" };
const CONCERN_FILL: Record<Concern, string> = {
  high: "var(--risk-high-foreground)",
  medium: "var(--risk-medium-foreground)",
  review: "var(--secondary-foreground)",
  low: "var(--risk-low-foreground)",
  none: "var(--muted-foreground)",
};

// The map always shows Finland with a margin, and grows to take in points as far as the region outline reaches
// (scoring/reference/finland_region.geojson). Points beyond that are listed as outside the map.
const BASE = { lon0: 14, lon1: 38, lat0: 57.5, lat1: 71 };
const PAD = 1;

function regionExtent(region: Region | null) {
  if (!region?.features.length) return BASE;
  let lon0 = Infinity, lon1 = -Infinity, lat0 = Infinity, lat1 = -Infinity;
  for (const f of region.features) for (const poly of f.geometry.coordinates) for (const [lo, la] of poly[0]) {
    lon0 = Math.min(lon0, lo); lon1 = Math.max(lon1, lo); lat0 = Math.min(lat0, la); lat1 = Math.max(lat1, la);
  }
  return { lon0, lon1, lat0, lat1 };
}

const rank = (c: Concern) => LEVELS.indexOf(c);

/** Why a finding has no point on the map, in plain words: what the filing is, then what geography found. */
function whereText(ctx: FindingContext | undefined): string {
  if (!ctx) return "no context for this finding";
  const n = ctx.notice ?? {};
  const what = n.orbit === "GSO" && n.longitude_deg != null
    ? `geostationary satellite at ${Math.abs(n.longitude_deg)} ${n.longitude_deg < 0 ? "W" : "E"}`
    : n.orbit === "GSO" ? "geostationary satellite" : n.orbit === "NGSO" ? "non-geostationary satellite" : "no position filed";
  return ctx.geo?.note ? `${what}; ${ctx.geo.note}` : what;
}
const fmtLatLon = (lat: number, lon: number, digits: number) =>
  `${Math.abs(lat).toFixed(digits)} ${lat < 0 ? "S" : "N"}, ${Math.abs(lon).toFixed(digits)} ${lon < 0 ? "W" : "E"}`;

// One map point can stand for several findings (an earth station or special-interest station named by more than one
// filing): it takes the highest concern among them, and the most urgent review state (open before decided).
function merge(points: Map<string, MapPoint>, p: MapPoint) {
  const q = points.get(p.key);
  if (!q) { points.set(p.key, p); return; }
  for (const id of p.findingIds) if (!q.findingIds.includes(id)) q.findingIds.push(id);
  if (rank(p.concern) < rank(q.concern)) q.concern = p.concern;
}

function collectPoints(bundle: AnalysisBundle): { points: MapPoint[]; unlocated: string[] } {
  const layers = bundle.map ?? {};
  const known = (id: string | null | undefined): id is string => id != null && bundle.context[id] != null;
  const csv = `results/${bundle.result.kind}_${bundle.result.issue}.csv`;
  const points = new Map<string, MapPoint>();
  const located = new Set<string>();

  // Terrestrial notified stations: every located notice of the issue when the cache has the layer, raised or not.
  const terrestrial = layers.terrestrial ?? bundle.result.findings.flatMap((f) => {
    const n = bundle.context[f.id]?.notice ?? {};
    return n.lat != null && n.lon != null ? [{ notice_id: f.notice_id, finding_id: f.id, concern: f.concern, administration: n.administration,
      site_name: n.site_name ?? null, station_class: n.station_class ?? null, notice_type: n.notice_type ?? null, change: n.change,
      freq_hz: n.freq_hz ?? null, erp_dbw: n.erp_dbw ?? null, lat: n.lat, lon: n.lon }] : [];
  });
  for (const t of terrestrial) {
    const fid = known(t.finding_id) ? t.finding_id : null;
    const ctx = fid ? bundle.context[fid] : undefined;
    const cls = t.station_class;
    if (fid) located.add(fid);
    merge(points, {
      key: `T-${t.notice_id}`, type: "terrestrial", name: t.site_name ?? ctx?.title ?? `Notice ${t.notice_id}`, administration: t.administration ?? null,
      typeLabel: `${cls ? `${STATION_CLASS[cls] ?? "Station"} (${cls})` : "Station, class unknown"}${t.notice_type ? `, form ${t.notice_type}` : ""}`,
      lat: t.lat, lon: t.lon, concern: t.concern, review: "open", change: t.change ?? null, findingIds: fid ? [fid] : [],
      facts: [
        fid ? `${fid}, notice ${t.notice_id}` : `notice ${t.notice_id}, not raised: listed in ${csv}`,
        t.freq_hz != null ? `${fmtHz(t.freq_hz)}${t.erp_dbw != null ? `, ERP ${t.erp_dbw} dBW` : ""}` : "frequency unknown",
        ctx?.geo?.note ?? "",
      ].filter(Boolean),
    });
  }

  // Earth stations of space filings: every located station of the notice when the cache has it, else the nearest one.
  for (const f of bundle.result.findings) {
    const ctx = bundle.context[f.id];
    if (!ctx || ctx.notice?.lat != null) continue;
    const d = ctx.geo?.detail ?? {};
    const stations = ctx.earth_stations
      ?? (d.nearest?.lat != null && d.nearest?.lon != null && d.nearest?.name ? [{ ...d.nearest, group_ids: [] }] : []);
    for (const es of stations) {
      located.add(f.id);
      merge(points, {
        key: `E-${es.name}-${es.lat}-${es.lon}`, type: "earth_station", name: es.name ?? "Earth station, no name filed",
        administration: es.country ?? ctx.notice?.administration ?? null,
        typeLabel: `Earth station${es.type ? `, ${EARTH_STATION_TYPE[es.type] ?? es.type}` : ""}`,
        lat: es.lat, lon: es.lon, concern: f.concern, review: "open", change: null, findingIds: [f.id],
        facts: [es.distance_km != null ? `${es.distance_km} km from Finland` : ""].filter(Boolean),
      });
    }
  }

  // Special-interest stations: the whole sheet when the cache has it, else the stations the lead groups reach.
  const special = layers.special_interest ?? bundle.result.findings.flatMap((f) =>
    (bundle.context[f.id]?.stations ?? []).map((s) => ({ ...s, finding_ids: [f.id], concern: f.concern })));
  for (const s of special) {
    const ids = s.finding_ids.filter(known);
    merge(points, {
      key: `S-${s.number}`, type: "special_interest", name: `Station ${s.number}`, administration: "FIN",
      typeLabel: `Special-interest station${s.class ? ` (${s.class})` : ""}`,
      lat: s.lat, lon: s.lon, concern: s.concern ?? "none", review: "open", change: null, findingIds: ids,
      facts: [`receives ${fmtHz(s.centre_hz)}, bandwidth ${fmtHz(s.bandwidth_hz)}`, s.row != null ? `sheet row ${s.row}` : "",
        s.finding_ids.length ? "" : "no filing in this issue reaches it"].filter(Boolean),
    });
  }

  const out = [...points.values()];
  for (const p of out) {
    const states: ReviewState[] = p.findingIds.map((id) => bundle.decisions?.[id]?.decision ?? "open");
    p.review = REVIEW_STATES.find((s) => states.includes(s)) ?? "open";
    if (p.type !== "special_interest" && p.findingIds.length > 1) p.facts.unshift(`named by ${p.findingIds.length} findings`);
    else if (p.type === "earth_station" && p.findingIds.length === 1) p.facts.unshift(`${p.findingIds[0]}, ${bundle.context[p.findingIds[0]]?.title ?? ""}`);
  }
  const unlocated = bundle.result.findings.filter((f) => !located.has(f.id)).map((f) => f.id);
  return { points: out, unlocated };
}

function Marker({ p, cx, cy, active }: { p: MapPoint; cx: number; cy: number; active: boolean }) {
  const s = active ? 8 : 5.5;
  const common = { fill: CONCERN_FILL[p.concern], stroke: "var(--card)", strokeWidth: 1.4 };
  const shape = p.type === "terrestrial" ? <circle cx={cx} cy={cy} r={s} {...common} />
    : p.type === "earth_station" ? <rect x={cx - s} y={cy - s} width={2 * s} height={2 * s} transform={`rotate(45 ${cx} ${cy})`} {...common} />
    : <polygon points={`${cx},${cy - s * 1.15} ${cx + s},${cy + s * 0.75} ${cx - s},${cy + s * 0.75}`} {...common} />;
  return (
    <>
      {p.review !== "open" && <circle cx={cx} cy={cy} r={s + 3.5} fill="none" stroke="var(--foreground)" strokeWidth={1.4} />}
      {active && <circle cx={cx} cy={cy} r={s + 7} fill="none" stroke="var(--primary)" strokeWidth={2} />}
      {shape}
    </>
  );
}

function Chips<T extends string>({ label, values, shown, counts, text, onToggle }: {
  label: string; values: T[]; shown: Set<T>; counts: Record<string, number>; text: (v: T) => string; onToggle: (v: T) => void;
}) {
  const present = values.filter((v) => counts[v]);
  if (!present.length) return null;
  return (
    <div role="group" aria-label={label} className="space-y-1">
      <div className="text-muted-foreground text-xs">{label}</div>
      <div className="flex flex-wrap gap-1.5">
        {present.map((v) => (
          <button key={v} type="button" onClick={() => onToggle(v)} aria-pressed={shown.has(v)}
            className={`rounded-full border px-2.5 py-1 text-xs transition-colors ${shown.has(v) ? "border-ring bg-card text-foreground" : "border-dashed border-border text-muted-foreground"}`}>
            {text(v)} <span className="num ml-1">{counts[v]}</span>
          </button>
        ))}
      </div>
    </div>
  );
}

function toggler<T>(set: (f: (s: Set<T>) => Set<T>) => void) {
  return (v: T) => set((s) => { const n = new Set(s); if (n.has(v)) n.delete(v); else n.add(v); return n; });
}

function count<T extends string>(points: MapPoint[], key: (p: MapPoint) => T) {
  const c: Record<string, number> = {};
  for (const p of points) c[key(p)] = (c[key(p)] ?? 0) + 1;
  return c;
}

/** All datapoints of the selected issue over Finland and its neighbours; clicking one selects its finding. */
export function OverviewMap({ bundle, region, selected, onSelect }: {
  bundle: AnalysisBundle; region: Region | null; selected: string | null; onSelect: (id: string) => void;
}) {
  const { points, unlocated } = useMemo(() => collectPoints(bundle), [bundle]);
  const [types, setTypes] = useState<Set<PointType>>(new Set(TYPES));
  const [levels, setLevels] = useState<Set<Concern>>(new Set(LEVELS));
  const [reviews, setReviews] = useState<Set<ReviewState>>(new Set(REVIEW_STATES));
  const [focus, setFocus] = useState<string | null>(null);

  const extent = useMemo(() => regionExtent(region), [region]);
  const inExtent = (p: MapPoint) => p.lon >= extent.lon0 && p.lon <= extent.lon1 && p.lat >= extent.lat0 && p.lat <= extent.lat1;
  const visible = points.filter((p) => types.has(p.type) && levels.has(p.concern) && reviews.has(p.review));
  const onMap = visible.filter(inExtent);
  const offMap = visible.filter((p) => !inExtent(p));

  // Grow the Finland view to take in every point shown, within the region outline.
  const view = { ...BASE };
  for (const p of onMap) {
    view.lon0 = Math.min(view.lon0, Math.max(extent.lon0, p.lon - PAD)); view.lon1 = Math.max(view.lon1, Math.min(extent.lon1, p.lon + PAD));
    view.lat0 = Math.min(view.lat0, Math.max(extent.lat0, p.lat - PAD)); view.lat1 = Math.max(view.lat1, Math.min(extent.lat1, p.lat + PAD));
  }
  const W = 640;
  const k = Math.cos((((view.lat0 + view.lat1) / 2) * Math.PI) / 180);
  const H = Math.round((W * (view.lat1 - view.lat0)) / ((view.lon1 - view.lon0) * k));
  const x = (lon: number) => ((lon - view.lon0) / (view.lon1 - view.lon0)) * W;
  const y = (lat: number) => ((view.lat1 - lat) / (view.lat1 - view.lat0)) * H;
  const grid = { lons: [] as number[], lats: [] as number[] };
  for (let lo = Math.ceil(view.lon0 / 5) * 5; lo <= view.lon1; lo += 5) grid.lons.push(lo);
  for (let la = Math.ceil(view.lat0 / 5) * 5; la <= view.lat1; la += 5) grid.lats.push(la);

  const isActive = (p: MapPoint) => p.key === focus || (selected != null && p.type !== "special_interest" && p.findingIds.includes(selected));
  // Draw low concern first so high concern sits on top; the active point last of all.
  const drawn = [...onMap].sort((a, b) => Number(isActive(a)) - Number(isActive(b)) || rank(b.concern) - rank(a.concern));
  const current = points.find((p) => p.key === focus) ?? points.find((p) => p.type !== "special_interest" && selected != null && p.findingIds.includes(selected)) ?? null;
  const pick = (p: MapPoint) => { setFocus(p.key); if (p.type !== "special_interest" && p.findingIds[0]) onSelect(p.findingIds[0]); };
  const byId = new Map(bundle.result.findings.map((f) => [f.id, f]));
  const unplaced = unlocated
    .map((id) => ({ id, concern: byId.get(id)?.concern ?? "none", review: (bundle.decisions?.[id]?.decision ?? "open") as ReviewState }))
    .filter((u) => levels.has(u.concern) && reviews.has(u.review))
    .sort((a, b) => rank(a.concern) - rank(b.concern) || a.id.localeCompare(b.id));
  const listed = [...visible].sort((a, b) => rank(a.concern) - rank(b.concern) || a.name.localeCompare(b.name));

  return (
    <div className="p-4 space-y-4">
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" className="rounded-2xl max-h-[75vh] mx-auto block" style={{ background: "var(--card)" }}
        aria-label={`Map of Finland and its neighbours with ${onMap.length} datapoints of ${bundle.result.kind} ${bundle.result.issue}`}>
        {grid.lons.map((lo) => <line key={`lo${lo}`} x1={x(lo)} x2={x(lo)} y1={0} y2={H} stroke="var(--border)" strokeWidth={0.8} />)}
        {grid.lats.map((la) => <line key={`la${la}`} x1={0} x2={W} y1={y(la)} y2={y(la)} stroke="var(--border)" strokeWidth={0.8} />)}
        {region?.features.map((f) => f.geometry.coordinates.map((poly, i) => (
          <polygon key={`${f.properties.itu}-${i}`}
            points={poly[0].map(([lo, la]) => `${x(lo).toFixed(1)},${y(la).toFixed(1)}`).join(" ")}
            fill={f.properties.itu === "FIN" ? "var(--map-footprint)" : "var(--map-land)"}
            stroke={f.properties.itu === "FIN" ? "var(--map-focus-outline)" : "var(--muted-foreground)"}
            strokeOpacity={f.properties.itu === "FIN" ? 1 : 0.7} strokeWidth={f.properties.itu === "FIN" ? 1.5 : 0.9}>
            <title>{f.properties.name}</title>
          </polygon>
        )))}
        {grid.lons.map((lo) => <text key={`tlo${lo}`} x={x(lo) + 3} y={H - 5} className="num fill-muted-foreground text-[11px]">{`${lo} E`}</text>)}
        {grid.lats.map((la) => <text key={`tla${la}`} x={4} y={y(la) - 4} className="num fill-muted-foreground text-[11px]">{`${la} N`}</text>)}
        {drawn.map((p) => (
          <g key={p.key} data-point={p.type} data-concern={p.concern} data-review={p.review} onClick={() => pick(p)} className="cursor-pointer">
            <Marker p={p} cx={x(p.lon)} cy={y(p.lat)} active={isActive(p)} />
            <title>{`${p.name}: ${p.typeLabel}${p.administration ? `, ${p.administration}` : ""}. Concern ${CONCERN_LABEL[p.concern]}, ${REVIEW_LABEL[p.review]}${p.change ? `, ${p.change} in this issue` : ""}. ${p.facts.join("; ")}`}</title>
          </g>
        ))}
      </svg>

      <div className="grid gap-4 text-sm sm:grid-cols-2">
        <div className="space-y-3">
          <dl className="grid grid-cols-2 gap-2" aria-label="Map counts">
            <div><dt className="text-muted-foreground text-xs">On the map</dt><dd className="num font-semibold">{onMap.length}</dd></div>
            <div><dt className="text-muted-foreground text-xs">Outside the map</dt><dd className="num font-semibold">{offMap.length}</dd></div>
            <div className="col-span-2"><dt className="text-muted-foreground text-xs">Findings without a location (satellites, orbits)</dt><dd className="num font-semibold">{unlocated.length}</dd></div>
          </dl>
          <Chips label="Type" values={TYPES} shown={types} counts={count(points, (p) => p.type)} text={(v) => TYPE_LABEL[v]} onToggle={toggler(setTypes)} />
          <Chips label="Concern" values={LEVELS} shown={levels} counts={count(points, (p) => p.concern)} text={(v) => CONCERN_LABEL[v]} onToggle={toggler(setLevels)} />
          <Chips label="Review state" values={REVIEW_STATES} shown={reviews} counts={count(points, (p) => p.review)} text={(v) => REVIEW_LABEL[v]} onToggle={toggler(setReviews)} />
        </div>
        <div className="space-y-3">
          {current ? (
            <div className="rounded-xl border border-border p-3 space-y-1" aria-label="Selected datapoint">
              <div className="flex items-center gap-2"><ConcernBadge concern={current.concern} /><span className="text-xs text-secondary-foreground">{REVIEW_LABEL[current.review]}</span></div>
              <div className="font-semibold">{current.name}</div>
              <div className="text-xs">{`${current.typeLabel}${current.administration ? `, ${current.administration}` : ""}`}</div>
              {current.change && <div className="text-xs">{`${current.change[0].toUpperCase()}${current.change.slice(1)} in this issue`}</div>}
              <div className="num text-xs text-muted-foreground">{fmtLatLon(current.lat, current.lon, 3)}</div>
              <ul className="text-xs text-muted-foreground space-y-0.5">{current.facts.map((t) => <li key={t}>{t}</li>)}</ul>
              {(current.type === "special_interest" ? current.findingIds.length > 0 : current.findingIds.length > 1) && (
                <div className="pt-1">
                  <div className="text-xs text-muted-foreground">{`${current.type === "special_interest" ? "Reached" : "Named"} by ${current.findingIds.length} finding${current.findingIds.length === 1 ? "" : "s"}`}</div>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {current.findingIds.slice(0, 8).map((id) => (
                      <button key={id} type="button" onClick={() => onSelect(id)}
                        className={`num rounded-full border px-2 py-0.5 text-[11px] ${id === selected ? "border-ring bg-secondary" : "border-border hover:bg-muted"}`}>{id}</button>
                    ))}
                    {current.findingIds.length > 8 && <span className="text-[11px] text-muted-foreground">{`and ${current.findingIds.length - 8} more`}</span>}
                  </div>
                </div>
              )}
            </div>
          ) : <p className="rounded-xl border border-dashed border-border p-3 text-xs text-muted-foreground">Select a datapoint on the map or in the list below.</p>}
          <p className="text-xs text-muted-foreground">
            Shape is the type: circle terrestrial station, diamond earth station, triangle special-interest station. Colour is the concern level,
            a ring around a marker means a reviewer decision is recorded. A station named by several findings takes the highest concern among them;
            a special-interest station no filing reaches, and a terrestrial notice that was not raised, show as Not raised.
          </p>
        </div>
      </div>

      <div>
        <h3 className="text-sm font-semibold mb-2">Datapoints</h3>
        <div className="max-h-80 overflow-y-auto rounded-xl border border-border">
          <ol aria-label="Map datapoints" className="text-sm">
            {listed.map((p) => (
              <li key={p.key} className="row-lazy">
                <button type="button" onClick={() => pick(p)} aria-current={isActive(p)}
                  className={`w-full text-left px-3 py-2 border-b border-border flex flex-wrap items-center gap-x-2 gap-y-0.5 ${isActive(p) ? "bg-secondary" : "hover:bg-muted"}`}>
                  <ConcernBadge concern={p.concern} />
                  <span className="font-medium">{p.name}</span>
                  <span className="text-xs text-muted-foreground">{TYPE_LABEL[p.type]}</span>
                  <span className="shrink-0 rounded-full border border-border px-2 py-0.5 text-[11px] text-secondary-foreground">{REVIEW_LABEL[p.review]}</span>
                  {p.change && <span className="text-[11px] text-muted-foreground">{p.change}</span>}
                  <span className="num ml-auto text-xs text-muted-foreground">{`${p.administration ?? "?"} · ${fmtLatLon(p.lat, p.lon, 2)}${inExtent(p) ? "" : " · outside the map"}`}</span>
                </button>
              </li>
            ))}
            {listed.length === 0 && <li className="p-4 text-sm text-muted-foreground">No datapoints match these filters.</li>}
          </ol>
        </div>
      </div>

      {unplaced.length > 0 && (
        <div>
          <h3 className="text-sm font-semibold mb-2">{`Findings without a ground position (${unplaced.length})`}</h3>
          <p className="text-xs text-muted-foreground mb-2">Satellites and orbits have no point on a map of the ground; their visibility from Finland is in each finding's Map tab.</p>
          <div className="max-h-80 overflow-y-auto rounded-xl border border-border">
            <ol aria-label="Findings without a ground position" className="text-sm">
              {unplaced.map(({ id, concern, review }) => (
                <li key={id} className="row-lazy">
                  <button type="button" onClick={() => onSelect(id)} aria-current={id === selected}
                    className={`w-full text-left px-3 py-2 border-b border-border flex flex-wrap items-center gap-x-2 gap-y-0.5 ${id === selected ? "bg-secondary" : "hover:bg-muted"}`}>
                    <ConcernBadge concern={concern} />
                    <span className="font-medium">{bundle.context[id]?.title ?? id}</span>
                    <span className="shrink-0 rounded-full border border-border px-2 py-0.5 text-[11px] text-secondary-foreground">{REVIEW_LABEL[review]}</span>
                    <span className="num text-xs text-muted-foreground">{id}</span>
                    <span className="basis-full text-xs text-muted-foreground">{whereText(bundle.context[id])}</span>
                  </button>
                </li>
              ))}
            </ol>
          </div>
        </div>
      )}
    </div>
  );
}
