import { expect, test, type Page, type TestInfo } from "@playwright/test";

// Screenshots for pull requests (docs/screenshots/<step>/). Runs only on demand, one step at a time:
//   SCREENSHOTS=d2 npm --prefix frontend run e2e -- screenshots
// Each step has its own scene below; each project (desktop dark, desktop light, phone) writes its own files.
const step = process.env.SCREENSHOTS;
test.skip(!step, "set SCREENSHOTS=<step> to capture screenshots");

// Dark is the default (PR #41): the desktop-light project opts into light the way a user would, before the first paint.
test.beforeEach(async ({ page }, info) => {
  if (info.project.use.colorScheme === "light") {
    await page.addInitScript(() => { try { localStorage.setItem("filing-radar.theme", "light"); } catch { /* no storage */ } });
  }
});

async function shot(page: Page, info: TestInfo, name: string, phoneRegion?: string) {
  const path = `../docs/screenshots/${step}/${name}-${info.project.name}.png`;
  // On the phone the page is very long: capture the part that changed instead of the whole page.
  if (info.project.name === "phone" && phoneRegion) await page.getByRole("region", { name: phoneRegion, exact: true }).screenshot({ path });
  else await page.screenshot({ path });
}

async function open(page: Page) {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Filing Radar" })).toBeVisible();
}

test("d3: decision and audit log", async ({ page }, info) => {
  test.skip(step !== "d3");
  await open(page);
  await page.getByLabel("Reviewer").fill("Aino Virtanen");
  const panel = page.getByRole("region", { name: "Decision" });
  await panel.getByLabel(/Note/).fill("Steerable beam can reach Finland: ask CHN for the pfd mask over 18.7-19.2 GHz.");
  await panel.getByRole("button", { name: "Investigate" }).click();
  await expect(panel.getByRole("status")).toContainText("Decision saved");
  await shot(page, info, "1-decision", "Decision");
  await page.getByRole("list", { name: "Ranked findings" }).getByRole("button").nth(1).click();
  await panel.getByLabel(/Note/).fill("Same operator and band as F-3074-0001; handled in one letter.");
  await panel.getByRole("button", { name: "Approve" }).click();
  await expect(panel.getByRole("status")).toContainText("Decision saved");
  await page.getByRole("tab", { name: "Audit log" }).click();
  await expect(page.getByRole("status").filter({ hasText: "Audit chain verified" })).toBeVisible();
  if (info.project.name === "phone") {
    await page.getByRole("list", { name: "Audit log entries" }).locator("xpath=ancestor::section[1]")
      .screenshot({ path: `../docs/screenshots/${step}/2-audit-log-${info.project.name}.png` });
  } else await shot(page, info, "2-audit-log");
});

test("d2: explanation and letter draft", async ({ page }, info) => {
  test.skip(step !== "d2");
  await open(page);
  await page.getByRole("button", { name: "Explain in plain language" }).click();
  const explanation = page.getByRole("region", { name: "Explanation", exact: true });
  await expect(explanation).toContainText("checked:");
  await explanation.getByLabel("Cited evidence").getByRole("button").first().click();
  await explanation.scrollIntoViewIfNeeded();
  await shot(page, info, "1-explanation", "Explanation");
  await page.getByRole("button", { name: "Draft letter" }).click();
  const letter = page.getByRole("region", { name: "Letter draft" });
  await expect(letter.getByLabel("Letter text")).toHaveValue(/DRAFT for expert review/);
  await letter.scrollIntoViewIfNeeded();
  await shot(page, info, "2-letter", "Letter draft");
});

test("e: offline demo, accuracy and proof pack", async ({ page }, info) => {
  test.skip(step !== "e");
  await open(page);
  await expect(page.getByRole("status", { name: "Data source" })).toHaveText(/Offline demo/);
  await shot(page, info, "1-demo-mode");
  const proof = new URL("../../results/proof/", import.meta.url).href;
  await page.goto(`${proof}freeze/e2_golden.html`);
  await expect(page.getByRole("heading", { name: /Case recognition accuracy/ })).toBeVisible();
  await shot(page, info, "2-accuracy");
  await page.goto(`${proof}index.html`);
  await expect(page.getByRole("heading", { name: "Filing Radar: stage reports" })).toBeVisible();
  await page.screenshot({ path: `../docs/screenshots/${step}/3-proof-pack-${info.project.name}.png`, fullPage: info.project.name !== "phone" });
});

test("review: pfd report with the sign-off", async ({ page }, info) => {
  test.skip(step !== "review" && step !== "signoff");
  const proof = new URL("../../results/proof/", import.meta.url).href;
  await page.goto(`${proof}3074/06_pfd.html`);
  await expect(page.getByText(/Signed off on 7 Nov 2026/)).toBeVisible();
  await page.getByText(/Signed off on 7 Nov 2026/).scrollIntoViewIfNeeded();
  await page.screenshot({ path: `../docs/screenshots/${step}/1-pfd-report-${info.project.name}.png` });
});

test("a3: special-interest stations report", async ({ page }, info) => {
  test.skip(step !== "a3");
  const proof = new URL("../../results/proof/", import.meta.url).href;
  await page.goto(`${proof}reference/special_interest.html`);
  await expect(page.getByRole("heading", { name: "Special-interest stations" })).toBeVisible();
  await page.screenshot({ path: `../docs/screenshots/${step}/1-summary-${info.project.name}.png` });
  await page.getByRole("heading", { name: "Where they are and what they use" }).scrollIntoViewIfNeeded();
  await page.getByRole("heading", { name: "Where they are and what they use" }).evaluate((el) => el.scrollIntoView({ block: "start" }));
  await page.screenshot({ path: `../docs/screenshots/${step}/2-map-and-spectrum-${info.project.name}.png` });
});

test("stations: special-interest stations on the map", async ({ page }, info) => {
  test.skip(step !== "stations");
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Filing Radar" })).toBeVisible();
  await page.getByRole("tab", { name: "Map", exact: true }).click();
  const map = page.locator("svg[aria-label^='Map of Finland']");
  await expect(map.locator("[data-station]").first()).toBeVisible();
  await map.scrollIntoViewIfNeeded();
  await page.screenshot({ path: `../docs/screenshots/${step}/1-map-${info.project.name}.png` });
});

test("terrestrial-stations: field strength at a special-interest station", async ({ page }, info) => {
  test.skip(step !== "terrestrial-stations");
  await page.goto("/");
  await page.getByRole("tab", { name: "Terrestrial 3076" }).click();
  await page.getByPlaceholder(/Search/).fill("93075625");
  await page.getByRole("list", { name: "Ranked findings" }).getByRole("button").first().click();
  await page.getByRole("tab", { name: "Map", exact: true }).click();
  const map = page.locator("svg[aria-label^='Map of Finland']");
  await expect(map.locator("[data-station]")).toHaveCount(1);
  await map.scrollIntoViewIfNeeded();
  await page.screenshot({ path: `../docs/screenshots/${step}/1-map-${info.project.name}.png` });
});

test("overview: whole-issue charts", async ({ page }, info) => {
  test.skip(step !== "overview");
  await page.goto("/");
  await page.getByRole("tab", { name: "Overview" }).click();
  await expect(page.getByRole("tab", { name: "Overview" })).toHaveAttribute("aria-selected", "true");
  await page.waitForTimeout(400);                                   // the tab highlight fades in (transition-colors)
  await expect(page.locator("svg[aria-label^='Geostationary arc'] [data-finding]").first()).toBeVisible();
  await page.getByRole("region", { name: "Issue overview" }).scrollIntoViewIfNeeded();
  if (info.project.name === "phone") await page.getByRole("region", { name: "Issue overview" }).screenshot({ path: `../docs/screenshots/${step}/1-space-${info.project.name}.png` });
  else await page.screenshot({ path: `../docs/screenshots/${step}/1-space-${info.project.name}.png` });
  await page.getByRole("tab", { name: "Terrestrial 3076" }).click();
  await page.getByRole("tab", { name: "Overview" }).click();
  await expect(page.getByRole("tab", { name: "Overview" })).toHaveAttribute("aria-selected", "true");
  await page.waitForTimeout(400);                                   // the tab highlight fades in (transition-colors)
  await expect(page.locator("svg[aria-label='Flagged findings by frequency and concern'] [data-finding]").first()).toBeVisible();
  if (info.project.name === "phone") await page.getByRole("region", { name: "Issue overview" }).screenshot({ path: `../docs/screenshots/${step}/2-terrestrial-${info.project.name}.png` });
  else await page.screenshot({ path: `../docs/screenshots/${step}/2-terrestrial-${info.project.name}.png` });
});
