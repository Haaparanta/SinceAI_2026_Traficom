import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { DraftResult, Explanation, Letter } from "../types";

function SourceNote({ d }: { d: DraftResult<unknown> }) {
  const fromModel = d.source !== "template";
  return (
    <div className="text-xs text-muted-foreground space-y-0.5">
      <div>
        <span className={`rounded-full px-2 py-0.5 font-semibold ${fromModel ? "bg-secondary text-secondary-foreground" : "bg-muted text-foreground"}`}>
          {fromModel ? `Written by ${d.source.replace("cache: ", "")}${d.source.startsWith("cache") ? " (cached)" : ""}` : "Template from the evidence"}
        </span>{" "}
        <span>{d.check}</span>
      </div>
      {d.notes.map((n, i) => <div key={i}>{n}</div>)}
    </div>
  );
}

function Cited({ ids, onEvidence }: { ids: string[]; onEvidence: (id: string) => void }) {
  return (
    <div className="flex flex-wrap gap-1.5 text-xs" aria-label="Cited evidence">
      <span className="text-muted-foreground">Cites</span>
      {ids.map((id) => (
        <button key={id} type="button" onClick={() => onEvidence(id)} className="num text-primary underline underline-offset-2">{id}</button>
      ))}
    </div>
  );
}

/** Explanation and correspondence draft. Grounded in the finding's evidence; never sent, never decides. */
export function DraftsPanel({ findingId, onEvidence }: { findingId: string; onEvidence: (id: string) => void }) {
  const [explanation, setExplanation] = useState<DraftResult<Explanation> | null>(null);
  const [letter, setLetter] = useState<DraftResult<Letter> | null>(null);
  const [body, setBody] = useState("");
  const [busy, setBusy] = useState<"explain" | "letter" | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [copied, setCopied] = useState(false);

  // The finding on screen now: a draft that arrives after the reviewer moved on is dropped, not shown on the wrong finding.
  const current = useRef(findingId);
  useEffect(() => {
    current.current = findingId;
    setExplanation(null); setLetter(null); setBody(""); setError(null); setBusy(null);
  }, [findingId]);
  const copiedTimer = useRef<number | undefined>(undefined);
  useEffect(() => () => window.clearTimeout(copiedTimer.current), []);

  async function run(task: "explain" | "letter") {
    const id = findingId;
    setBusy(task); setError(null);
    try {
      if (task === "explain") {
        const x = await api.explain(id);
        if (current.current === id) setExplanation(x);
      } else {
        const l = await api.letter(id);
        if (current.current === id) { setLetter(l); setBody(l.output.body_markdown); }
      }
    } catch (e) {
      if (current.current === id) setError(`Could not prepare the ${task === "explain" ? "explanation" : "letter"}. ${String(e)}`);
    } finally {
      if (current.current === id) setBusy(null);
    }
  }

  async function copy() {
    try {
      await navigator.clipboard.writeText(body);
      setCopied(true);
      window.clearTimeout(copiedTimer.current);
      copiedTimer.current = window.setTimeout(() => setCopied(false), 2000);
    } catch { setCopied(false); }
  }
  const download = () => {
    if (!letter) return;
    const blob = new Blob([`# ${letter.output.subject}\n\n${body}\n`], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `letter-${findingId}.md`;
    document.body.appendChild(a);   // Firefox needs the link in the document
    a.click();
    a.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);   // revoking at once can cancel the download in Safari
  };

  return (
    <section aria-label="Explanation and letter" className="rounded-2xl border border-border p-3 space-y-3">
      <div className="flex flex-wrap gap-2">
        <button type="button" onClick={() => run("explain")} disabled={busy !== null}
          className="min-h-11 rounded-full bg-secondary text-secondary-foreground px-4 text-sm font-semibold disabled:opacity-40">
          {busy === "explain" ? "Preparing explanation" : "Explain in plain language"}
        </button>
        <button type="button" onClick={() => run("letter")} disabled={busy !== null}
          className="min-h-11 rounded-full border border-border px-4 text-sm font-semibold hover:bg-muted disabled:opacity-40">
          {busy === "letter" ? "Preparing letter" : "Draft letter"}
        </button>
      </div>
      {error && <p role="alert" className="text-sm text-destructive">{error}</p>}

      {explanation && (
        <div aria-label="Explanation" role="region" className="space-y-2">
          <h3 className="text-sm font-semibold">Explanation</h3>
          <p className="text-[15px] leading-6">{explanation.output.text}</p>
          <Cited ids={explanation.output.cited_evidence_ids} onEvidence={onEvidence} />
          <SourceNote d={explanation} />
        </div>
      )}

      {letter && (
        <div aria-label="Letter draft" role="region" className="space-y-2 border-t border-border pt-3">
          <h3 className="text-sm font-semibold">Letter draft to {letter.output.to_administration}</h3>
          <p className="rounded-xl bg-accent text-accent-foreground px-3 py-2 text-xs">
            Draft for expert review. Edit it here; Filing Radar never sends anything.
          </p>
          <div className="text-sm"><span className="text-muted-foreground">Subject: </span>{letter.output.subject}</div>
          <label htmlFor={`letter-${findingId}`} className="sr-only">Letter text</label>
          <textarea id={`letter-${findingId}`} value={body} onChange={(e) => setBody(e.target.value)} rows={14}
            className="w-full rounded-xl border border-input bg-background px-3 py-2 text-sm num leading-5 focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2" />
          <div className="flex flex-wrap gap-2">
            <button type="button" onClick={copy} className="min-h-11 rounded-full border border-border px-4 text-sm font-semibold hover:bg-muted">
              {copied ? "Copied" : "Copy text"}
            </button>
            <span className="sr-only" role="status">{copied ? "Letter text copied" : ""}</span>
            <button type="button" onClick={download} className="min-h-11 rounded-full border border-border px-4 text-sm font-semibold hover:bg-muted">
              Download .md
            </button>
          </div>
          <Cited ids={letter.output.cited_evidence_ids} onEvidence={onEvidence} />
          <SourceNote d={letter} />
        </div>
      )}
    </section>
  );
}
