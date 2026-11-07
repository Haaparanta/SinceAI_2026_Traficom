import { expect, test } from "@playwright/test";

// Special-interest stations in the space screening: the Map tab draws every station in reach of the lead group,
// and the side panel counts the same number.
test("map shows the special-interest stations in reach", async ({ page }) => {
  await page.goto("/");
  await page.getByRole("list", { name: "Ranked findings" }).getByRole("button").first().click();
  await page.getByRole("tab", { name: "Map" }).click();
  const panel = page.getByLabel("Special-interest stations in reach");
  await expect(panel).toContainText("Special-interest stations in the band and in reach");
  const count = Number(await panel.locator("dd").first().innerText());
  expect(count).toBeGreaterThan(0);
  await expect(page.locator("svg[aria-label^='Map of Finland'] [data-station]")).toHaveCount(count);
  await expect(panel).toContainText(/sees the satellite at [\d.]+ deg/);
});
