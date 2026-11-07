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
