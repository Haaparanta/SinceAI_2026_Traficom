import { expect, test } from "@playwright/test";

// Step D2: explanation and letter draft. The API under test runs with DEMO_MODE=1 (playwright.config.ts), so the
// drafts come from the deterministic template and the same grounding check applies; no network call is made.

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Filing Radar" })).toBeVisible();
});

test("the explanation is grounded and its citations open the evidence", async ({ page }) => {
  await page.getByRole("button", { name: "Explain in plain language" }).click();
  const region = page.getByRole("region", { name: "Explanation", exact: true });
  await expect(region).toContainText("was rated high by the screening rules");
  await expect(region).toContainText("Template from the evidence");
  await expect(region).toContainText("checked:");
  const cite = region.getByLabel("Cited evidence").getByRole("button").first();
  const id = (await cite.innerText()).trim();
  await cite.click();
  await expect(page.getByRole("list", { name: "Evidence" }).locator(`[data-evidence-id="${id}"]`)).toHaveAttribute("aria-current", "true");
});

test("the letter is a draft to the notifying administration that can be edited and downloaded, never sent", async ({ page }) => {
  const finding = await (await page.request.get("/api/findings/F-3074-0001")).json();
  await page.getByRole("button", { name: "Draft letter" }).click();
  const region = page.getByRole("region", { name: "Letter draft" });
  await expect(region.getByRole("heading")).toHaveText(`Letter draft to ${finding.context.notice.administration}`);
  await expect(region).toContainText("Filing Radar never sends anything");
  const text = region.getByLabel("Letter text");
  await expect(text).toHaveValue(/^\*DRAFT for expert review/);
  await expect(text).toHaveValue(new RegExp(`notice ${finding.finding.notice_id}`));
  await text.fill("Edited by the specialist.");
  const download = page.waitForEvent("download");
  await region.getByRole("button", { name: "Download .md" }).click();
  expect((await download).suggestedFilename()).toBe("letter-F-3074-0001.md");
  await expect(page.getByRole("button", { name: /send/i })).toHaveCount(0);
});

test("drafts reset when another finding is selected", async ({ page }) => {
  await page.getByRole("button", { name: "Explain in plain language" }).click();
  await expect(page.getByRole("region", { name: "Explanation", exact: true })).toBeVisible();
  await page.getByRole("list", { name: "Ranked findings" }).getByRole("button").nth(1).click();
  await expect(page.getByRole("region", { name: "Explanation", exact: true })).toHaveCount(0);
});
