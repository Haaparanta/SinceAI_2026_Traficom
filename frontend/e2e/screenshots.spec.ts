import { expect, test } from "@playwright/test";

// Screenshots for pull requests (docs/screenshots/<step>/). Runs only on demand:
//   SCREENSHOTS=d3 npm --prefix frontend run e2e -- screenshots
// Each project (desktop dark, desktop light, phone) writes its own files.
const step = process.env.SCREENSHOTS;
test.skip(!step, "set SCREENSHOTS=<step> to capture screenshots");

const out = (name: string, project: string) => `../docs/screenshots/${step}/${name}-${project}.png`;

test("decision and audit log", async ({ page }, info) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Filing Radar" })).toBeVisible();
  await page.getByLabel("Reviewer").fill("Aino Virtanen");
  const panel = page.getByRole("region", { name: "Decision" });
  await panel.getByLabel(/Note/).fill("Steerable beam can reach Finland: ask CHN for the pfd mask over 18.7-19.2 GHz.");
  await panel.getByRole("button", { name: "Investigate" }).click();
  await expect(panel.getByRole("status")).toContainText("Decision saved");
  // On the phone, the page is very long: capture the part that changed instead of the whole page.
  if (info.project.name === "phone") await panel.screenshot({ path: out("1-decision", info.project.name) });
  else await page.screenshot({ path: out("1-decision", info.project.name) });

  const second = page.getByRole("list", { name: "Ranked findings" }).getByRole("button").nth(1);
  await second.click();
  await panel.getByLabel(/Note/).fill("Same operator and band as F-3074-0001; handled in one letter.");
  await panel.getByRole("button", { name: "Approve" }).click();
  await expect(panel.getByRole("status")).toContainText("Decision saved");

  await page.getByRole("tab", { name: "Audit log" }).click();
  await expect(page.getByRole("status").filter({ hasText: "Audit chain verified" })).toBeVisible();
  if (info.project.name === "phone") {
    await page.getByRole("list", { name: "Audit log entries" }).locator("xpath=ancestor::section[1]").screenshot({ path: out("2-audit-log", info.project.name) });
  } else await page.screenshot({ path: out("2-audit-log", info.project.name) });
});
