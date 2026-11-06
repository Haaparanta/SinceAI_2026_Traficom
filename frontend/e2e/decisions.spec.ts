import { expect, test } from "@playwright/test";

// Step D3: a reviewer decides, the decision lands in the hash-chained audit log, the computed concern does not change,
// and the export carries the decision. The API under test writes to a throwaway log (playwright.config.ts).

test.beforeEach(async ({ page }) => {
  await page.goto("/");
  await expect(page.getByRole("heading", { name: "Filing Radar" })).toBeVisible();
});

test("decision buttons stay disabled until there is a reviewer and a note", async ({ page }) => {
  await page.getByLabel("Reviewer").fill("");
  const panel = page.getByRole("region", { name: "Decision" });
  await expect(panel.getByRole("button", { name: "Investigate" })).toBeDisabled();
  await expect(panel).toContainText("Enter your name as reviewer");
  await page.getByLabel("Reviewer").fill("E2E Reviewer");
  await expect(panel).toContainText("Write a short note");
  await panel.getByLabel(/Note/).fill("ok");
  await expect(panel.getByRole("button", { name: "Approve" })).toBeDisabled();
});

test("a decision is saved, shown, logged with a verified chain, and exported; the concern stays", async ({ page }, info) => {
  const firstRow = page.getByRole("list", { name: "Ranked findings" }).getByRole("button").first();
  const concernBefore = await firstRow.locator("[data-concern]").getAttribute("data-concern");
  const id = (await firstRow.innerText()).match(/F-\d{4}-\d{4}/)![0];
  const note = `Playwright ${info.project.name}: ask the notifying administration`;

  await page.getByLabel("Reviewer").fill("E2E Reviewer");
  const panel = page.getByRole("region", { name: "Decision" });
  await panel.getByLabel(/Note/).fill(note);
  await panel.getByRole("button", { name: "Investigate" }).click();

  await expect(panel.getByRole("status")).toContainText("Decision saved: Investigate. Logged at");
  await expect(panel.getByRole("list", { name: "Decision history" })).toContainText(note);
  await expect(firstRow).toContainText("Investigate");
  await expect(firstRow.locator("[data-concern]")).toHaveAttribute("data-concern", concernBefore!);

  await page.getByRole("tab", { name: "Audit log" }).click();
  await expect(page.getByRole("status").filter({ hasText: "Audit chain verified" })).toBeVisible();
  const auditLog = info.project.name === "phone"
    ? page.getByRole("list", { name: "Audit log entries" }) : page.getByRole("table", { name: "Audit log" });
  await expect(auditLog).toContainText(note);

  const finding = await (await page.request.get(`/api/findings/${id}`)).json();
  expect(finding.finding.concern).toBe(concernBefore);
  const csv = await (await page.request.get("/api/export/3074?kind=space")).text();
  const row = csv.split("\n").find((l) => l.split(",")[2] === finding.finding.notice_id)!;
  expect(row).toContain("investigate by E2E Reviewer at");
});

test("the reviewer name is remembered across reloads", async ({ page }) => {
  await page.getByLabel("Reviewer").fill("Aino Reviewer");
  await page.reload();
  await expect(page.getByLabel("Reviewer")).toHaveValue("Aino Reviewer");
});
