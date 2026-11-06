import { defineConfig, devices } from "@playwright/test";

// End-to-end tests of the one screen against the real API and the committed data/cache files.
// Both servers start automatically; locally an already running `make api` / `make frontend` is reused.
// The HTML report lands in reports/playwright/ so it shows up on the stage-report index (make index).
export default defineConfig({
  testDir: "./e2e",
  timeout: 30_000,
  expect: { timeout: 10_000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"], ["html", { outputFolder: "../reports/playwright", open: "never" }]],
  outputDir: "../reports/playwright-artifacts",
  use: {
    baseURL: "http://127.0.0.1:5173",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [
    { name: "desktop-dark", use: { ...devices["Desktop Chrome"], viewport: { width: 1500, height: 950 }, colorScheme: "dark" } },
    { name: "desktop-light", use: { ...devices["Desktop Chrome"], viewport: { width: 1500, height: 950 }, colorScheme: "light" } },
    { name: "phone", use: { ...devices["Pixel 7"], colorScheme: "light" } },
  ],
  webServer: [
    {
      command: "uv run uvicorn radar.main:app --app-dir backend --host 127.0.0.1 --port 8000",
      cwd: "..",
      url: "http://127.0.0.1:8000/issues",
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
    {
      command: "npm run dev -- --host 127.0.0.1 --port 5173 --strictPort",
      url: "http://127.0.0.1:5173",
      reuseExistingServer: !process.env.CI,
      timeout: 60_000,
    },
  ],
});
