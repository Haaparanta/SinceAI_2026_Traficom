import { useEffect, useState } from "react";
import { chooseTheme, currentTheme, onSystemThemeChange, type Theme } from "../theme";

// Line icons (lucide "sun" and "moon" shapes), drawn inline: no icon font and no emoji (design/girlypop-theme.md).
function Sun() {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2v2M12 20v2M4.93 4.93l1.41 1.41M17.66 17.66l1.41 1.41M2 12h2M20 12h2M6.34 17.66l-1.41 1.41M19.07 4.93l-1.41 1.41" />
    </svg>
  );
}

function Moon() {
  return (
    <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">
      <path d="M12 3a6 6 0 0 0 9 9 9 9 0 1 1-9-9Z" />
    </svg>
  );
}

const OPTIONS: { value: Theme; label: string; icon: () => React.JSX.Element }[] = [
  { value: "light", label: "Light", icon: Sun },
  { value: "dark", label: "Dark", icon: Moon },
];

export function ThemeSwitch() {
  const [theme, setTheme] = useState<Theme>(currentTheme);
  useEffect(() => onSystemThemeChange(setTheme), []);

  return (
    <div role="radiogroup" aria-label="Colour theme" className="inline-flex rounded-full bg-muted p-1 gap-1 self-end">
      {OPTIONS.map(({ value, label, icon: Icon }) => {
        const on = theme === value;
        return (
          <button key={value} type="button" role="radio" aria-checked={on}
            onClick={() => { chooseTheme(value); setTheme(value); }}
            className={`min-h-9 inline-flex items-center gap-1.5 rounded-full px-3 text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-ring ${on
              ? "bg-card text-foreground shadow-soft" : "text-muted-foreground hover:text-foreground"}`}>
            <Icon />
            {label}
          </button>
        );
      })}
    </div>
  );
}
