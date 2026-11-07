import { useEffect, useState } from "react";
import { api, DECISION_LABEL, fmtTime } from "../api";
import type { AuditEntry, DecisionKind } from "../types";

const OPTIONS: { value: DecisionKind; label: string; className: string }[] = [
  { value: "approve", label: "Approve", className: "bg-primary text-primary-foreground" },
  { value: "investigate", label: "Investigate", className: "bg-secondary text-secondary-foreground" },
  { value: "dismiss", label: "Dismiss", className: "border border-border text-foreground hover:bg-muted" },
];

/** Approve, investigate or dismiss with a required note. Plain language only (design rule 8, serious context).
 *  The decision is appended to the audit log; the computed concern never changes. */
export function DecisionPanel({ findingId, reviewer, onDecided }: {
  findingId: string; reviewer: string; onDecided: (e: AuditEntry) => void;
}) {
  const [note, setNote] = useState("");
  const [history, setHistory] = useState<AuditEntry[]>([]);
  const [status, setStatus] = useState<{ ok: boolean; text: string } | null>(null);
  const [busy, setBusy] = useState(false);

  useEffect(() => {
    let stale = false;
    setNote(""); setStatus(null);
    api.findingDecisions(findingId).then((h) => { if (!stale) setHistory(h); }).catch(() => undefined);
    return () => { stale = true; };
  }, [findingId]);

  const missing = !reviewer.trim() ? "Enter your name as reviewer at the top of the page." : note.trim().length < 3 ? "Write a short note on why." : null;

  async function decide(decision: DecisionKind) {
    if (missing) return;
    setBusy(true);
    try {
      const e = await api.decide(findingId, { decision, reviewer: reviewer.trim(), note: note.trim() });
      setHistory((h) => [...h, e]);
      setNote("");
      setStatus({ ok: true, text: `Decision saved: ${DECISION_LABEL[e.decision]}. Logged at ${fmtTime(e.at)} as entry ${e.seq}.` });
      onDecided(e);
    } catch (err) {
      setStatus({ ok: false, text: `The decision was not saved. ${String(err)}` });
    } finally {
      setBusy(false);
    }
  }

  return (
    <section aria-label="Decision" className="rounded-2xl border border-border p-3 space-y-3">
      <h3 className="text-sm font-semibold">Decision</h3>
      <label className="block text-xs text-muted-foreground" htmlFor={`note-${findingId}`}>Note (required, kept in the audit log)</label>
      <textarea id={`note-${findingId}`} value={note} onChange={(e) => setNote(e.target.value)} rows={2} maxLength={500}
        className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2" />
      <div className="flex flex-wrap gap-2">
        {OPTIONS.map((o) => (
          <button key={o.value} type="button" onClick={() => decide(o.value)} disabled={!!missing || busy}
            className={`min-h-11 rounded-full px-4 text-sm font-semibold transition active:scale-[0.97] disabled:opacity-40 disabled:cursor-not-allowed ${o.className}`}>
            {o.label}
          </button>
        ))}
      </div>
      {missing && <p className="text-xs text-muted-foreground">{missing}</p>}
      {status && <p role="status" className={`text-sm ${status.ok ? "text-success" : "text-destructive"}`}>{status.text}</p>}
      {history.length > 0 && (
        <ol aria-label="Decision history" className="space-y-1.5 border-t border-border pt-2">
          {[...history].reverse().map((e) => (
            <li key={e.seq} className="text-xs">
              <span className="font-semibold">{DECISION_LABEL[e.decision]}</span> by {e.reviewer}
              <span className="num text-muted-foreground whitespace-nowrap"> · {fmtTime(e.at)} · entry {e.seq}</span>
              {e.note && <div className="text-muted-foreground">{e.note}</div>}
            </li>
          ))}
        </ol>
      )}
    </section>
  );
}
