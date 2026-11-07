import { expect, test } from "@playwright/test";

// The terrestrial overview draws and lists about 4 000 datapoints: single tests take 29-33 s on an M1 when the whole
// suite runs in parallel, at the default 30 s limit, so this file gets 60 s per test.
test.describe.configure({ timeout: 60_000 });

// "All on map": every located datapoint of the issue over Finland and its neighbours, with its type and state.
// Expected counts come from the API bundle, not typed in here.
type Bundle = {
  result: { findings: { id: string; concern: string }[] };
  context: Record<string, { title: string; notice: { lat?: number | null; site_name?: string } }>;
  map?: { terrestrial?: { notice_id: string; finding_id: string | null; site_name: string | null }[] };
};

test("terrestrial 3076: every located notice is on the map, and a raised one selects its finding", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("tablist", { name: "Issue" }).getByRole("tab", { name: "Terrestrial 3076" }).click();
  await page.getByRole("tab", { name: "All on map" }).click();
  const b: Bundle = await (await page.request.get("/api/analysis/terrestrial/3076")).json();
  const located = b.result.findings.filter((f) => b.context[f.id].notice.lat != null);
  expect(located.length).toBeGreaterThan(0);
  // The cache carries every located notice of the issue (raised or not) under map.terrestrial; older caches only the findings.
  const notices = b.map?.terrestrial ?? located.map((f) => ({ notice_id: f.id, finding_id: f.id, site_name: b.context[f.id].notice.site_name ?? null }));
  expect(notices.length).toBeGreaterThanOrEqual(located.length);

  // Type and state are written out in the list, not only drawn; the list holds every datapoint, on the map or outside it.
  const list = page.getByRole("list", { name: "Map datapoints" });
  const stations = list.getByRole("button").filter({ hasText: "Terrestrial station" });
  await expect(stations).toHaveCount(notices.length);
  await expect(stations.first()).toContainText(/Not reviewed|Investigate|Approved|Dismissed/);   // decisions from other tests may exist
  const map = page.locator("svg[aria-label^='Map of Finland and its neighbours']");
  const counts = page.getByLabel("Map counts").locator("dd");
  const drawn = await map.locator("[data-point]").count();
  await expect(counts.nth(0)).toHaveText(String(drawn));
  expect(drawn + Number(await counts.nth(1).innerText())).toBe(await list.getByRole("button").count());

  // Clicking a raised notice selects its finding in the side panel (a site whose name only that notice uses).
  const names = new Map<string, number>();
  for (const n of notices) names.set(n.site_name ?? "", (names.get(n.site_name ?? "") ?? 0) + 1);
  const target = located.find((f) => names.get(b.context[f.id].notice.site_name ?? "") === 1) ?? located[0];
  const site = b.context[target.id].notice.site_name ?? "";
  await list.getByRole("button").filter({ hasText: site }).first().click();
  await expect(page.getByLabel("Selected datapoint")).toContainText(site);
  if (names.get(site) === 1) await expect(page.getByRole("heading", { level: 2 })).toHaveText(b.context[target.id].title);

  // Filters hide the points of a type.
  await page.getByRole("group", { name: "Type" }).getByRole("button", { name: /Terrestrial station/ }).click();
  await expect(map.locator("[data-point='terrestrial']")).toHaveCount(0);
});

test("space 3074: earth stations and special-interest stations are drawn by type", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("tab", { name: "All on map" }).click();
  const map = page.locator("svg[aria-label^='Map of Finland and its neighbours']");
  await expect(map.locator("[data-point='special_interest']").first()).toBeVisible();
  await expect(map.locator("[data-point='earth_station']").first()).toBeVisible();
  await expect(page.getByLabel("Map counts")).toContainText("Findings without a location");
});

test("a reviewer decision shows as the datapoint's state", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("tablist", { name: "Issue" }).getByRole("tab", { name: "Terrestrial 3076" }).click();
  await page.getByLabel("Reviewer").fill("Map Tester");
  const panel = page.getByRole("region", { name: "Decision" });
  await panel.getByLabel(/Note/).fill("Checked on the overview map.");
  await panel.getByRole("button", { name: "Investigate" }).click();
  await expect(panel.getByRole("status")).toContainText("Decision saved");
  await page.getByRole("tab", { name: "All on map" }).click();
  await expect(page.getByLabel("Selected datapoint")).toContainText("Investigate");
  await expect(page.locator("svg[aria-label^='Map of Finland and its neighbours'] [data-review='investigate']").first()).toBeVisible();
});

// Cache files built by scripts/build_cache.py now carry every located datapoint under "map" (backend/radar/map_layers.py)
// and every earth station per finding. The committed cache predates them, so these tests add them to the served bundle.
test("with the full layers: unraised notices, every special-interest station and every earth station are drawn", async ({ page }) => {
  await page.route("**/api/analysis/terrestrial/3076", async (route) => {
    const res = await route.fetch();
    const b = await res.json();
    const raised = b.result.findings.map((f: { id: string; notice_id: string; concern: string }) => {
      const n = b.context[f.id].notice;
      return { notice_id: f.notice_id, finding_id: f.id, concern: f.concern, administration: n.administration, site_name: n.site_name,
        station_class: n.station_class, notice_type: n.notice_type, change: n.change, freq_hz: n.freq_hz, erp_dbw: n.erp_dbw, lat: n.lat, lon: n.lon };
    });
    b.map = {
      terrestrial: [...raised, { notice_id: "NOT-RAISED-1", finding_id: "F-3076-9999", concern: "none", administration: "EST", site_name: "UNRAISED SITE",
        station_class: "FX", notice_type: "T11", change: "new", freq_hz: 6_875_000_000, erp_dbw: 30, lat: 59.4, lon: 24.7 }],
      special_interest: [{ number: "LONELY-1", class: "FX", lat: 62.0, lon: 25.0, centre_hz: 3_500_000_000, bandwidth_hz: 1_000_000, row: 99,
        finding_ids: [], concern: null }],
    };
    await route.fulfill({ response: res, json: b });
  });
  await page.goto("/");
  await page.getByRole("tablist", { name: "Issue" }).getByRole("tab", { name: "Terrestrial 3076" }).click();
  await page.getByRole("tab", { name: "All on map" }).click();
  const map = page.locator("svg[aria-label^='Map of Finland and its neighbours']");
  const list = page.getByRole("list", { name: "Map datapoints" });
  const raisedCount = await page.getByRole("list", { name: "Ranked findings" }).getByRole("button").count();
  await expect(map.locator("[data-point='terrestrial']")).toHaveCount(raisedCount + 1);
  await expect(map.locator("[data-point='special_interest']")).toHaveCount(1);     // the layer replaces the lead-group stations

  await list.getByRole("button").filter({ hasText: "UNRAISED SITE" }).click();
  const detail = page.getByLabel("Selected datapoint");
  await expect(detail).toContainText("Not raised");
  await expect(detail).toContainText("not raised: listed in results/terrestrial_3076.csv");
  await list.getByRole("button").filter({ hasText: "Station LONELY-1" }).click();
  await expect(detail).toContainText("no filing in this issue reaches it");
});

test("with every earth station: a filing's stations are all drawn, and a shared station once", async ({ page }) => {
  let target = "";
  await page.route("**/api/analysis/space/3074", async (route) => {
    const res = await route.fetch();
    const b = await res.json();
    target = b.result.findings[0].id;
    const other = b.result.findings[1].id;
    const es = (name: string, lat: number, lon: number) => ({ name, country: "FIN", type: "S", lat, lon, distance_km: 0, group_ids: ["G1"] });
    for (const id of Object.keys(b.context)) b.context[id].earth_stations = [];
    b.context[target].earth_stations = [es("ALPHA", 61.5, 23.8), es("BRAVO", 65.0, 25.5), es("SHARED", 60.2, 24.9)];
    b.context[other].earth_stations = [es("SHARED", 60.2, 24.9)];
    await route.fulfill({ response: res, json: b });
  });
  await page.goto("/");
  await page.getByRole("tab", { name: "All on map" }).click();
  const map = page.locator("svg[aria-label^='Map of Finland and its neighbours']");
  await expect(map.locator("[data-point='earth_station']")).toHaveCount(3);
  await page.getByRole("list", { name: "Map datapoints" }).getByRole("button").filter({ hasText: "SHARED" }).click();
  await expect(page.getByLabel("Selected datapoint")).toContainText("Named by 2 findings");
  await expect(page.getByLabel("Selected datapoint").getByRole("button", { name: target })).toBeVisible();
});

test("space 3074: every finding without a ground position is listed with the reason, and selects its finding", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("tab", { name: "All on map" }).click();
  const counted = Number(await page.getByLabel("Map counts").locator("dd").nth(2).innerText());
  expect(counted).toBeGreaterThan(0);
  const rows = page.getByRole("list", { name: "Findings without a ground position" }).getByRole("button");
  await expect(rows).toHaveCount(counted);                                   // all filters on: every one is listed
  await expect(rows.filter({ hasText: /geostationary satellite at [\d.]+ [EW]/ }).first()).toBeVisible();
  const row = rows.first();
  const id = (await row.locator(".num").first().innerText()).trim();
  await row.click();
  await expect(page.locator("main").getByText(id, { exact: true }).first()).toBeVisible();
  await expect(row).toHaveAttribute("aria-current", "true");

  // The concern filter applies to this list too.
  await page.getByRole("group", { name: "Concern", exact: true }).getByRole("button", { name: /Not raised/ }).click();
  expect(await rows.count()).toBeLessThan(counted);
});
