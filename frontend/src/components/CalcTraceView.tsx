import type { CalcTrace } from "../types";
import { Empty } from "./ui";

const METHOD: Record<string, string> = {
  pfd_gso_worst_case: "Worst-case power flux-density at the Finnish surface (RR Article 21)",
  pfd_ngso_worst_case: "Worst-case power flux-density at the Finnish surface from one non-GSO satellite (RR Article 21)",
  p1546_field_strength: "Field strength at the Finnish border (ITU-R P.1546-6, T/R 25-08)",
};

/** Inputs with their evidence, the formula, the result, the limit and the margin (pm_pack/06 rule 5). */
export function CalcTraceView({ calc, onEvidence }: { calc: CalcTrace; onEvidence: (id: string) => void }) {
  if (calc.method === "none") {
    return (
      <div className="p-4">
        <Empty>No calculation applies to this finding.</Empty>
        <ul className="px-6 text-sm text-muted-foreground list-disc space-y-1">{calc.notes.map((n, i) => <li key={i}>{n}</li>)}</ul>
      </div>
    );
  }
  const exceeds = calc.margin_db != null && calc.margin_db < 0;
  return (
    <div className="p-4 space-y-4">
      <div className="flex flex-wrap items-center gap-2">
        <h2 className="font-display text-lg font-semibold tracking-tight">{METHOD[calc.method]}</h2>
        <span className="rounded-full bg-accent text-accent-foreground px-2.5 py-0.5 text-xs font-semibold">{calc.label === "indicative" ? "Indicative" : "Confirmed"}</span>
      </div>
      {calc.result_value != null ? (
        <div className="grid gap-3 grid-cols-[repeat(auto-fit,minmax(9.5rem,1fr))]">
          <Big label="Result" value={calc.result_value} unit={calc.result_unit} />
          <Big label="Limit" value={calc.limit_value} unit={calc.limit_value != null ? calc.result_unit.split(" in ")[0] : "no criterion"} />
          <div className={`rounded-xl p-3 ${calc.margin_db == null ? "bg-muted" : exceeds ? "bg-risk-high text-risk-high-foreground" : "bg-risk-low text-risk-low-foreground"}`}>
            <div className="text-xs">Margin (limit minus result)</div>
            <div className="num text-2xl font-semibold">{calc.margin_db == null ? "n/a" : `${calc.margin_db.toFixed(2)} dB`}</div>
            <div className="text-xs">{calc.margin_db == null ? "" : exceeds ? "Exceeds the limit" : "Below the limit"}</div>
          </div>
        </div>
      ) : <Empty>Not computed: {calc.notes[0]}</Empty>}
      <div>
        <div className="text-xs text-muted-foreground mb-1">Formula</div>
        <code className="block num text-sm bg-muted rounded-xl p-3 whitespace-pre-wrap">{calc.formula}</code>
      </div>
      {calc.inputs.length > 0 && (
        <table className="w-full text-sm">
          <thead><tr className="text-left text-xs text-muted-foreground"><th className="py-1">Input</th><th className="text-right">Value</th><th>Unit</th><th>Evidence</th></tr></thead>
          <tbody>
            {calc.inputs.map((i, k) => (
              <tr key={k} className="border-t border-border odd:bg-muted/40">
                <td className="py-1.5 pr-2">{i.name}</td>
                <td className="num text-right pr-2">{typeof i.value === "number" ? +i.value.toPrecision(8) : i.value}</td>
                <td className="text-muted-foreground">{i.unit}</td>
                <td><button type="button" onClick={() => onEvidence(i.evidence_id)} className="num text-primary underline underline-offset-2">{i.evidence_id}</button></td>
              </tr>
            ))}
            {calc.limit_evidence_id && (
              <tr className="border-t border-border"><td className="py-1.5">Limit</td><td className="num text-right pr-2">{calc.limit_value}</td><td /><td>
                <button type="button" onClick={() => onEvidence(calc.limit_evidence_id!)} className="num text-primary underline underline-offset-2">{calc.limit_evidence_id}</button></td></tr>
            )}
          </tbody>
        </table>
      )}
      <ul className="text-xs text-muted-foreground list-disc pl-5 space-y-1">{calc.notes.map((n, i) => <li key={i}>{n}</li>)}</ul>
    </div>
  );
}

function Big({ label, value, unit }: { label: string; value: number | null; unit: string }) {
  return (
    <div className="rounded-xl bg-muted p-3">
      <div className="text-xs text-muted-foreground">{label}</div>
      <div className="num text-2xl font-semibold">{value == null ? "n/a" : value.toFixed(2)}</div>
      <div className="text-xs text-muted-foreground">{unit}</div>
    </div>
  );
}
