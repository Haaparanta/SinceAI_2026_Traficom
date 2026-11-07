import { expect, test, type Page } from "@playwright/test";
import type { AnalysisBundle } from "../src/types";

// Step 4: the Overview tab shows the whole issue. Every mark is one flagged finding and opens it.
async function bundle(page: Page, kind: string, issue: number): Promise<AnalysisBundle> {
  const r = await page.request.get(`/api/analysis/${kind}/${issue}`);
  return r.json();
}

test("space: the arc holds every flagged GSO filing and a click opens it", async ({ page }) => {
  const b = await bundle(page, "space", 3074);
  const gso = b.result.findings.filter((f) => f.concern !== "none" && b.context[f.id].notice.orbit === "GSO"
    && b.context[f.id].notice.longitude_deg != null && b.context[f.id].geo.detail.max_elevation_deg != null);
  await page.goto("/");
  await page.getByRole("tab", { name: "Overview" }).click();
  const arc = page.locator("svg[aria-label^='Geostationary arc']");
  await expect(arc.locator("[data-finding]")).toHaveCount(gso.length);
  const bars = page.locator("svg[aria-label='Flagged findings by frequency and concern'] [data-finding]");
  await expect(bars).toHaveCount(b.result.findings.filter((f) => f.concern !== "none").length);
  const target = gso[gso.length - 1];
  await arc.locator(`[data-finding='${target.id}']`).click();
  await expect(page.locator("main").getByText(target.id, { exact: true }).first()).toBeVisible();
  await expect(page.getByRole("heading", { name: b.context[target.id].title }).first()).toBeVisible();
});

test("terrestrial: the map holds every located flagged station; Enter opens one", async ({ page }) => {
  const b = await bundle(page, "terrestrial", 3076);
  const located = b.result.findings.filter((f) => f.concern !== "none" && b.context[f.id].notice.lat != null);
  await page.goto("/");
  await page.getByRole("tab", { name: "Terrestrial 3076" }).click();
  await page.getByRole("tab", { name: "Overview" }).click();
  const map = page.locator("svg[aria-label='Flagged foreign stations around Finland']");
  await expect(map.locator("[data-finding]")).toHaveCount(located.length);
  const target = located.find((f) => f.concern === "high")!;
  await map.locator(`[data-finding='${target.id}']`).focus();
  await page.keyboard.press("Enter");
  await expect(page.getByRole("heading", { name: b.context[target.id].title }).first()).toBeVisible();
});

test("the legend counts match the concern counts", async ({ page }) => {
  const b = await bundle(page, "space", 3074);
  await page.goto("/");
  await page.getByRole("tab", { name: "Overview" }).click();
  const legend = page.getByLabel("Legend");
  for (const c of ["high", "medium", "review", "low"] as const) {
    const n = b.result.findings.filter((f) => f.concern === c).length;
    if (n) await expect(legend).toContainText(`(${n})`);
  }
});
