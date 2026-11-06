import { expect, test } from "@playwright/test";

// Step E3: the demo runs with Wi-Fi off. The API under test runs with DEMO_MODE=1 (playwright.config.ts). Every
// request to a host other than this machine is aborted and recorded; walking the whole screen must record none.
const LOCAL = /^https?:\/\/(localhost|127\.0\.0\.1|\[::1\])(:\d+)?\//;

test("the whole screen works offline in demo mode", async ({ page }) => {
  const external: string[] = [];
  await page.route("**/*", (route) => {
    const url = route.request().url();
    if (LOCAL.test(url) || url.startsWith("data:") || url.startsWith("blob:")) return route.continue();
    external.push(url);
    return route.abort("internetdisconnected");
  });

  await page.goto("/");
  await expect(page.getByRole("status", { name: "Data source" })).toHaveText(/Offline demo: cached analysis/);
  for (const issue of ["Space 3074", "Terrestrial 3076"]) {
    await page.getByRole("tab", { name: issue }).click();
    await expect(page.getByRole("list", { name: "Ranked findings" }).getByRole("button").first()).toBeVisible();
    for (const tab of ["Spectrum", "Map", "Calculation", "Audit log"]) {
      await page.getByRole("tab", { name: tab }).click();
      await expect(page.getByRole("tab", { name: tab })).toHaveAttribute("aria-selected", "true");
    }
    await page.getByRole("button", { name: "Explain in plain language" }).click();
    await expect(page.getByRole("region", { name: "Explanation", exact: true })).toContainText("DEMO_MODE=1");
    await page.getByRole("button", { name: "Draft letter" }).click();
    await expect(page.getByRole("region", { name: "Letter draft" }).getByLabel("Letter text")).toHaveValue(/DRAFT for expert review/);
  }
  expect(external, "requests that left this machine").toEqual([]);
});
