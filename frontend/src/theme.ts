// Light or dark: the user's choice wins and is remembered; without a choice the operating system setting decides.
// index.html applies the same rule in an inline script before the first paint, so the page never flashes.
export type Theme = "light" | "dark";

const KEY = "filing-radar.theme";
const BAR: Record<Theme, string> = { light: "#fff9fd", dark: "#170a16" };   // --background of each theme
const media = window.matchMedia("(prefers-color-scheme: dark)");

export function storedTheme(): Theme | null {
  try {
    const v = localStorage.getItem(KEY);
    return v === "light" || v === "dark" ? v : null;
  } catch {
    return null;
  }
}

export function systemTheme(): Theme {
  return media.matches ? "dark" : "light";
}

export function currentTheme(): Theme {
  return storedTheme() ?? systemTheme();
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

/** Follow operating-system changes while the user has not picked a theme. */
export function onSystemThemeChange(cb: (t: Theme) => void): () => void {
  const handler = () => {
    if (storedTheme()) return;
    applyTheme(systemTheme());
    cb(systemTheme());
  };
  media.addEventListener("change", handler);
  return () => media.removeEventListener("change", handler);
}
