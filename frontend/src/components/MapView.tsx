import type { FindingContext, RefPoint, Region } from "../types";

const VIEW = { lon0: 14, lon1: 38, lat0: 57.5, lat1: 71 };

/** Finland and its neighbours with what the geography step computed for this finding. */
export function MapView({ ctx, region, points }: { ctx: FindingContext; region: Region | null; points: RefPoint[] }) {
  const W = 560;
  const k = Math.cos((64 * Math.PI) / 180);
  const H = Math.round((W * (VIEW.lat1 - VIEW.lat0)) / ((VIEW.lon1 - VIEW.lon0) * k));
  const x = (lon: number) => ((lon - VIEW.lon0) / (VIEW.lon1 - VIEW.lon0)) * W;
  const y = (lat: number) => ((VIEW.lat1 - lat) / (VIEW.lat1 - VIEW.lat0)) * H;
  const geo = ctx.geo;
  const d = geo.detail ?? {};
  const elevations: Record<string, number> = {};
  for (const p of (d.points ?? []) as { point: string; elevation_deg: number }[]) elevations[p.point] = p.elevation_deg;
  const station = ctx.notice.lat != null ? { lat: ctx.notice.lat as number, lon: ctx.notice.lon as number }
    : d.nearest?.lat != null && d.nearest?.name ? { lat: d.nearest.lat, lon: d.nearest.lon } : null;
  const border = d.nearest?.lat != null && ctx.notice.lat != null ? d.nearest : null;
  const latLimit = d.lat_limit_10deg as number | undefined;

  return (
    <div className="p-4 grid gap-4 lg:grid-cols-[minmax(0,1fr)_260px]">
      <svg viewBox={`0 0 ${W} ${H}`} width="100%" role="img" aria-label="Map of Finland with the geography of this finding"
        className="rounded-2xl" style={{ background: "var(--card)" }}>
        {region?.features.map((f) => f.geometry.coordinates.map((poly, i) => (
          <polygon key={`${f.properties.itu}-${i}`}
            points={poly[0].map(([lo, la]) => `${x(lo).toFixed(1)},${y(la).toFixed(1)}`).join(" ")}
            fill={f.properties.itu === "FIN" ? "var(--map-footprint)" : "var(--map-land)"}
            stroke={f.properties.itu === "FIN" ? "var(--map-focus-outline)" : "var(--muted-foreground)"}
            strokeOpacity={f.properties.itu === "FIN" ? 1 : 0.45} strokeWidth={f.properties.itu === "FIN" ? 1.5 : 0.8}>
            <title>{f.properties.name}</title>
          </polygon>
        )))}
        {latLimit != null && latLimit < VIEW.lat1 && latLimit > VIEW.lat0 && (
          <g>
            <line x1={0} x2={W} y1={y(latLimit)} y2={y(latLimit)} stroke="var(--primary)" strokeDasharray="6 4" strokeWidth={1.5} />
            <text x={6} y={y(latLimit) - 6} className="fill-foreground text-[13px]">{`seen up to ${latLimit.toFixed(1)} N at 10 deg`}</text>
          </g>
        )}
        {geo.method === "gso_elevation" && points.map((p) => {
          const el = elevations[p.name];
          const seen = el != null && el > 0;
          return (
            <g key={p.name}>
              <circle cx={x(p.lon)} cy={y(p.lat)} r={6} fill={seen ? "var(--primary)" : "var(--muted-foreground)"} stroke="var(--card)" strokeWidth={2} />
              <text x={x(p.lon) + 9} y={y(p.lat) + 4} className="num fill-foreground text-[13px] font-medium">{`${p.name} ${el != null ? el.toFixed(1) : "?"} deg`}</text>
            </g>
          );
        })}
        {station && (
          <g>
            {border && <line x1={x(station.lon)} y1={y(station.lat)} x2={x(border.lon)} y2={y(border.lat)} stroke="var(--primary)" strokeWidth={2} strokeDasharray="4 3" />}
            <rect x={x(station.lon) - 6} y={y(station.lat) - 6} width={12} height={12} rx={2} fill="var(--primary)" stroke="var(--card)" strokeWidth={2} />
            {border && <circle cx={x(border.lon)} cy={y(border.lat)} r={4} fill="var(--map-focus-outline)" />}
          </g>
        )}
      </svg>
      <dl className="text-sm space-y-2">
        <div><dt className="text-muted-foreground text-xs">Geography</dt><dd className="font-semibold">{geo.relevance.replace("_", " ")}</dd></div>
        <div><dt className="text-muted-foreground text-xs">How it was decided</dt><dd>{geo.note || geo.method}</dd></div>
        {d.satellite_longitude_deg != null && <div><dt className="text-muted-foreground text-xs">Satellite</dt><dd className="num">{`${Math.abs(d.satellite_longitude_deg)} ${d.satellite_longitude_deg < 0 ? "W" : "E"}`}</dd></div>}
        {d.distance_km != null && <div><dt className="text-muted-foreground text-xs">Distance to Finland</dt><dd className="num">{`${d.distance_km} km`}</dd></div>}
        {d.segments?.length > 0 && <div><dt className="text-muted-foreground text-xs">Path</dt><dd className="num">{(d.segments as { km: number; zone: string }[]).map((s) => `${s.km} km ${s.zone === "Land" ? "land" : "sea"}`).join(", ")}</dd></div>}
        {d.nearest?.name && <div><dt className="text-muted-foreground text-xs">Nearest earth station</dt><dd>{`${d.nearest.name} (${d.nearest.country}), ${d.nearest.distance_km} km`}</dd></div>}
        <p className="text-xs text-muted-foreground pt-2">Markers: squares are stations, circles are Finnish reference points (pink = sees the satellite).</p>
      </dl>
    </div>
  );
}
