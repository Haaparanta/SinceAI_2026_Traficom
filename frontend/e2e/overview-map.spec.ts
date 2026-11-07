import { expect, test } from "@playwright/test";

// "All on map": every located datapoint of the issue over Finland and its neighbours, with its type and state.
// Expected counts come from the API bundle, not typed in here.
type Bundle = {
  result: { findings: { id: string; concern: string }[] };
  context: Record<string, { title: string; notice: { lat?: number | null; site_name?: string } }>;
};

test("terrestrial 3076: every notified station is on the map and selects its finding", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("tablist", { name: "Issue" }).getByRole("tab", { name: "Terrestrial 3076" }).click();
  await page.getByRole("tab", { name: "All on map" }).click();
  const b: Bundle = await (await page.request.get("/api/analysis/terrestrial/3076")).json();
  const located = b.result.findings.filter((f) => b.context[f.id].notice.lat != null);
  expect(located.length).toBeGreaterThan(0);

  const map = page.locator("svg[aria-label^='Map of Finland and its neighbours']");
  await expect(map.locator("[data-point='terrestrial']")).toHaveCount(located.length);
  const drawn = await map.locator("[data-point]").count();
  await expect(page.getByLabel("Map counts").locator("dd").first()).toHaveText(String(drawn));

  // Type and state are written out in the list, not only drawn.
  const list = page.getByRole("list", { name: "Map datapoints" });
  const stations = list.getByRole("button").filter({ hasText: "Terrestrial station" });
  await expect(stations).toHaveCount(located.length);
  await expect(stations.first()).toContainText(/Not reviewed|Investigate|Approved|Dismissed/);   // decisions from other tests may exist

  // Clicking a datapoint selects its finding in the side panel.
  const target = located[located.length - 1];
  await list.getByRole("button").filter({ hasText: b.context[target.id].notice.site_name ?? "" }).first().click();
  await expect(page.getByLabel("Selected datapoint")).toContainText(b.context[target.id].notice.site_name ?? "");
  await expect(page.getByRole("heading", { level: 2 })).toHaveText(b.context[target.id].title);

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
