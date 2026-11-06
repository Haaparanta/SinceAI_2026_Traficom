import { defineConfig, devices } from "@playwright/test";

// End-to-end tests of the one screen against the real API and the committed data/cache files.
// The tests start their own API (port 8100) and dev server (port 5180), so they never reuse a server you are
// working with, and the API writes reviewer decisions to a throwaway folder (reports/e2e-decisions, emptied first).
// The HTML report lands in reports/playwright/ and is linked from the stage-report index (make index).
const API_PORT = 8100;
const WEB_PORT = 5180;

export default defineConfig({
  testDir: "./e2e",
  globalSetup: "./e2e/global-setup.ts",
  timeout: 30_000,
  expect: { timeout: 10_000 },
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 1 : 0,
  reporter: [["list"], ["html", { outputFolder: "../reports/playwright", open: "never" }]],
  outputDir: "../reports/playwright-artifacts",
  use: {
    baseURL: `http://127.0.0.1:${WEB_PORT}`,
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
      command: `uv run uvicorn radar.main:app --app-dir backend --host 127.0.0.1 --port ${API_PORT}`,
      cwd: "..",
      env: { DECISIONS_DIR: "reports/e2e-decisions", LLM_DISABLED: "1" },
      url: `http://127.0.0.1:${API_PORT}/issues`,
      reuseExistingServer: false,
      timeout: 60_000,
    },
    {
      command: `npm run dev -- --host 127.0.0.1 --port ${WEB_PORT} --strictPort`,
      env: { API_PORT: String(API_PORT) },
      url: `http://127.0.0.1:${WEB_PORT}`,
      reuseExistingServer: false,
      timeout: 60_000,
    },
  ],
});
