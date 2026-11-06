import { expect, test, type Page, type TestInfo } from "@playwright/test";

// Screenshots for pull requests (docs/screenshots/<step>/). Runs only on demand, one step at a time:
//   SCREENSHOTS=d2 npm --prefix frontend run e2e -- screenshots
// Each step has its own scene below; each project (desktop dark, desktop light, phone) writes its own files.
const step = process.env.SCREENSHOTS;
test.skip(!step, "set SCREENSHOTS=<step> to capture screenshots");

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
