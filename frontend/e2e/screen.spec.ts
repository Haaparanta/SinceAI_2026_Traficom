import { expect, test, type Page } from "@playwright/test";

// What the screen shows must equal what the API serves: expected values are read from the API, not typed in here.
type Metrics = { screened: number; flagged: number; provenance_coverage_pct: number; concern: Record<string, number> };
type Bundle = {
  result: { findings: { id: string; concern: string; calc: { method: string; margin_db: number | null; result_value: number | null } }[] };
  context: Record<string, { title: string }>;
};

const consoleErrors = new WeakMap<Page, string[]>();

test.beforeEach(async ({ page }) => {
  const errors: string[] = [];
  consoleErrors.set(page, errors);
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Filing Radar" })).toBeVisible();
});

test.afterEach(async ({ page }) => {
  expect(consoleErrors.get(page), "no console errors or failed requests").toEqual([]);
});

async function metrics(page: Page, kind: string, issue: number): Promise<Metrics> {
  return (await page.request.get(`/api/metrics?issue=${issue}&kind=${kind}`)).json();
}
async function bundle(page: Page, kind: string, issue: number): Promise<Bundle> {
  return (await page.request.get(`/api/analysis/${kind}/${issue}`)).json();
}
function list(page: Page) {
  return page.getByRole("list", { name: "Ranked findings" });
}
async function chooseIssue(page: Page, label: string) {
  await page.getByRole("tablist", { name: "Issue" }).getByRole("tab", { name: label }).click();
  await expect(page.getByRole("tablist", { name: "Issue" }).getByRole("tab", { name: label })).toHaveAttribute("aria-selected", "true");
}

test("proof metrics match the API for Space 3074", async ({ page }) => {
  const m = await metrics(page, "space", 3074);
  const bar = page.getByLabel("Proof metrics");
  await expect(bar).toContainText(m.screened.toLocaleString("en"));
  await expect(bar).toContainText(String(m.flagged));
  await expect(bar).toContainText(`${m.provenance_coverage_pct} %`);
});

test("the ranked list starts with the API's first finding and every badge has a text label", async ({ page }) => {
  const b = await bundle(page, "space", 3074);
  const first = b.result.findings[0];
  const firstRow = list(page).getByRole("button").first();
  await expect(firstRow).toContainText(b.context[first.id].title);
  await expect(firstRow).toContainText(first.id);
  const badges = list(page).locator("[data-concern]");
  const n = await badges.count();
  expect(n).toBeGreaterThan(10);
  // textContent, not innerText: rows below the fold use content-visibility: auto, so the browser skips their layout
  for (const text of await badges.allTextContents()) expect(["High", "Medium", "Review", "Low", "Not raised"]).toContain(text.trim());
});

test("calculation tab shows result, limit, margin and the indicative label from the trace", async ({ page }) => {
  const b = await bundle(page, "space", 3074);
  const calc = b.result.findings[0].calc;
  await page.getByRole("tab", { name: "Calculation" }).click();
  await expect(page.getByText("Worst-case power flux-density at the Finnish surface")).toBeVisible();
  await expect(page.getByText("Indicative", { exact: true })).toBeVisible();
  await expect(page.getByText(calc.result_value!.toFixed(2), { exact: true })).toBeVisible();
  await expect(page.getByText(`${calc.margin_db!.toFixed(2)} dB`, { exact: true })).toBeVisible();
  await expect(page.getByText(calc.margin_db! < 0 ? "Exceeds the limit" : "Below the limit", { exact: true })).toBeVisible();
});

test("an evidence link in the trace highlights that evidence item", async ({ page }) => {
  await page.getByRole("tab", { name: "Calculation" }).click();
  const link = page.getByRole("button", { name: /^E-\d{3}$/ }).first();
  const id = (await link.innerText()).trim();
  await link.click();
  const item = page.getByRole("list", { name: "Evidence" }).locator(`[data-evidence-id="${id}"]`);
  await expect(item).toHaveAttribute("aria-current", "true");
  await expect(item).toBeInViewport();
});

test("spectrum and map tabs draw the lead group, the Finnish rows and the reference points", async ({ page }) => {
  await page.getByRole("tab", { name: "Spectrum" }).click();
  const spectrum = page.getByRole("img", { name: "Spectrum overlap" });
  await expect(spectrum).toBeVisible();
  expect(await spectrum.locator("rect").count()).toBeGreaterThan(1);
  await page.getByRole("tab", { name: "Map", exact: true }).click();
  const map = page.getByRole("img", { name: /Map of Finland/ });
  await expect(map).toBeVisible();
  const points = await (await page.request.get("/api/reference/points")).json();
  for (const p of points as { name: string }[]) await expect(map).toContainText(p.name);
});

test("concern filter and search narrow the list", async ({ page }) => {
  const m = await metrics(page, "space", 3074);
  const highChip = page.getByRole("group", { name: "Filter by concern" }).getByRole("button", { name: /High/ });
  await expect(highChip).toContainText(String(m.concern.high));
  await highChip.click();
  await expect(highChip).toHaveAttribute("aria-pressed", "false");
  await expect(list(page).getByText("High", { exact: true })).toHaveCount(0);
  await page.getByLabel("Search findings").fill("HISPASAT");
  for (const row of await list(page).getByRole("button").allInnerTexts()) expect(row).toMatch(/HISPASAT/);
});

test("Terrestrial 3076 shows the P.1546 trace of its first finding", async ({ page }) => {
  await chooseIssue(page, "Terrestrial 3076");
  const b = await bundle(page, "terrestrial", 3076);
  const first = b.result.findings[0];
  await expect(list(page).getByRole("button").first()).toContainText(b.context[first.id].title);
  await page.getByRole("tab", { name: "Calculation" }).click();
  await expect(page.getByText("Field strength at the Finnish border")).toBeVisible();
  await expect(page.getByText(`${first.calc.margin_db!.toFixed(2)} dB`, { exact: true })).toBeVisible();
  const m = await metrics(page, "terrestrial", 3076);
  await expect(page.getByLabel("Proof metrics")).toContainText(m.screened.toLocaleString("en"));
});

test("export downloads the results CSV for the selected issue", async ({ page }) => {
  const href = await page.getByRole("link", { name: "Export results" }).getAttribute("href");
  expect(href).toContain("/api/export/3074?kind=space");
  const r = await page.request.get(href!);
  expect(r.status()).toBe(200);
  expect((await r.text()).split("\n")[0]).toBe(
    "issue,kind,notice_id,special_section,administration,network_or_station,freq_min_mhz,freq_max_mhz,direction,finnish_match," +
    "special_interest_station_ids,overlap_mhz,geo_relevance,calc_method,calc_value,calc_unit,limit_value,margin_db,concern,reason,evidence_refs,decision");
});

test("dark by default, light when chosen and remembered; the page never scrolls sideways", async ({ page }) => {
  // PR #41: dark whatever the system setting; light is opt-in through the Colour theme switch
  await expect(page.locator("html")).toHaveClass(/dark/);
  await page.getByRole("radiogroup", { name: "Colour theme" }).getByRole("radio", { name: "Light" }).click();
  await expect(page.locator("html")).not.toHaveClass(/dark/);
  await page.reload();
  await expect(page.locator("html")).not.toHaveClass(/dark/);
  await page.getByRole("radiogroup", { name: "Colour theme" }).getByRole("radio", { name: "Dark" }).click();
  await expect(page.locator("html")).toHaveClass(/dark/);
  await expect(page.locator(".bg-sigil")).toHaveCount(1);
  const { scrollW, clientW } = await page.evaluate(() => ({
    scrollW: document.documentElement.scrollWidth, clientW: document.documentElement.clientWidth,
  }));
  expect(scrollW).toBeLessThanOrEqual(clientW);
});
