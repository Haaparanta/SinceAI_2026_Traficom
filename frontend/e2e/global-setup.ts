import { rmSync } from "node:fs";
import { fileURLToPath } from "node:url";

// Start every run with an empty decision log, so the audit chain the tests check is their own.
export default function globalSetup() {
  rmSync(fileURLToPath(new URL("../../reports/e2e-decisions", import.meta.url)), { recursive: true, force: true });
}
