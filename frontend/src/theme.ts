// Dark is the default; light is opt-in through ThemeSwitch and the choice is remembered.
// index.html applies the same rule in an inline script before the first paint, so the page never flashes.
export type Theme = "light" | "dark";

const KEY = "filing-radar.theme";
const BAR: Record<Theme, string> = { light: "#fff9fd", dark: "#170a16" };   // --background of each theme

export function currentTheme(): Theme {
  try {
    return localStorage.getItem(KEY) === "light" ? "light" : "dark";
  } catch {
    return "dark";
  }
}

export function applyTheme(t: Theme): void {
  const root = document.documentElement;
  root.classList.toggle("dark", t === "dark");
  root.style.colorScheme = t;
  document.querySelectorAll('meta[name="theme-color"]').forEach((m) => m.setAttribute("content", BAR[t]));
}

export function chooseTheme(t: Theme): void {
  try { localStorage.setItem(KEY, t); } catch { /* storage unavailable: the choice lasts for this visit */ }
  const root = document.documentElement;
  root.classList.add("theme-anim");            // fade colours only during a switch (index.css)
  applyTheme(t);
  window.setTimeout(() => root.classList.remove("theme-anim"), 300);
}
