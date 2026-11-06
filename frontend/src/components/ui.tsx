import type { ReactNode } from "react";
import { CONCERN_LABEL } from "../api";
import type { Concern } from "../types";

// Risk badges always carry a text label; colour is never the only signal (design/girlypop-theme.md section 3).
const CONCERN_CLASS: Record<Concern, string> = {
  high: "bg-risk-high text-risk-high-foreground",
  medium: "bg-risk-medium text-risk-medium-foreground",
  review: "bg-secondary text-secondary-foreground",
  low: "bg-risk-low text-risk-low-foreground",
  none: "bg-muted text-muted-foreground",
};

export function ConcernBadge({ concern }: { concern: Concern }) {
  return (
    <span data-concern={concern} className={`inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-semibold ${CONCERN_CLASS[concern]}`}>
      {CONCERN_LABEL[concern]}
    </span>
  );
}

export function Card({ children, className = "" }: { children: ReactNode; className?: string }) {
  return <section className={`bg-card text-card-foreground rounded-2xl shadow-soft border border-border ${className}`}>{children}</section>;
}

export function Segmented<T extends string>({ value, options, onChange, label }: {
  value: T; options: { value: T; label: string }[]; onChange: (v: T) => void; label: string;
}) {
  return (
    <div role="tablist" aria-label={label} className="inline-flex max-w-full overflow-x-auto rounded-full bg-muted p-1 gap-1">
      {options.map((o) => (
        <button key={o.value} role="tab" aria-selected={value === o.value} onClick={() => onChange(o.value)}
          className={`min-h-9 shrink-0 whitespace-nowrap rounded-full px-4 text-sm font-medium transition-colors ${value === o.value
            ? "bg-card text-foreground shadow-soft" : "text-muted-foreground hover:text-foreground"}`}>
          {o.label}
        </button>
      ))}
    </div>
  );
}

export function Stat({ value, label }: { value: ReactNode; label: string }) {
  return (
    <div className="rounded-xl bg-card/80 border border-border px-4 py-2">
      <div className="num text-lg font-semibold text-foreground">{value}</div>
      <div className="text-xs text-muted-foreground">{label}</div>
    </div>
  );
}

export function Empty({ children }: { children: ReactNode }) {
  return <p className="text-sm text-muted-foreground p-6">{children}</p>;
}
