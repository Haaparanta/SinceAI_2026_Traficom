import { Fragment, useEffect, useState } from "react";
import { api, CONCERN_LABEL, DECISION_LABEL, fmtTime } from "../api";
import type { AuditLog, Kind } from "../types";
import { Empty } from "./ui";

/** Every decision for the issue, newest first, with the result of re-checking the hash chain on the server. */
export function AuditLogView({ kind, issue, version, onSelect }: {
  kind: Kind; issue: number; version: number; onSelect: (id: string) => void;
}) {
  const [log, setLog] = useState<AuditLog | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    let stale = false;
    setError(null);
    api.audit(kind, issue).then((l) => { if (!stale) setLog(l); })
      .catch((e) => { if (!stale) setError(String(e)); });
    return () => { stale = true; };
  }, [kind, issue, version]);

  if (error && !log) return <p role="alert" className="p-6 text-sm text-destructive">The audit log could not be loaded. {error}</p>;
  if (!log) return <Empty>Loading the audit log.</Empty>;
  return (
    <div className="p-4 space-y-3">
      <p role="status" className={`rounded-xl px-3 py-2 text-sm ${log.chain.ok ? "bg-risk-low text-risk-low-foreground" : "bg-risk-high text-risk-high-foreground"}`}>
        {log.chain.ok
          ? `Audit chain verified: ${log.chain.entries} ${log.chain.entries === 1 ? "entry" : "entries"}, each linked to the previous one by its SHA-256 hash.`
          : `Audit chain broken at entry ${log.chain.first_bad_seq}: the log was edited outside the tool. New decisions are refused until it is restored.`}
      </p>
      {log.entries.length === 0 ? <Empty>No decisions yet for this issue.</Empty> : (
        <>
        <ol className="sm:hidden space-y-2" aria-label="Audit log entries">
          {log.entries.map((e) => (
            <li key={e.seq} className="rounded-xl border border-border p-2.5 text-sm">
              <div className="flex flex-wrap items-baseline gap-x-2">
                <span className="num text-xs text-muted-foreground">#{e.seq}</span>
                <span className="font-semibold">{DECISION_LABEL[e.decision]}</span>
                <button type="button" onClick={() => onSelect(e.finding_id)} className="num text-primary underline underline-offset-2">{e.finding_id}</button>
              </div>
              <div className="text-xs text-muted-foreground">{e.reviewer} · <span className="num">{fmtTime(e.at)}</span> · concern then {CONCERN_LABEL[e.concern_at_decision]}</div>
              {e.note && <div className="mt-1">{e.note}</div>}
              <div className="num text-[11px] text-muted-foreground mt-1 break-all">hash {e.hash.slice(0, 16)}</div>
            </li>
          ))}
        </ol>
        <div className="hidden sm:block overflow-x-auto"><table className="w-full text-sm" aria-label="Audit log">
          <thead><tr className="text-left text-xs text-muted-foreground [&>th]:py-1 [&>th]:pr-3 [&>th]:whitespace-nowrap">
            <th>Entry</th><th>Time</th><th>Finding</th><th>Decision</th><th>Reviewer</th><th>Concern then</th><th>Hash</th>
          </tr></thead>
          <tbody>
            {log.entries.map((e) => (
              <Fragment key={e.seq}>
                <tr className="border-t border-border align-top whitespace-nowrap [&>td]:pt-2 [&>td]:pr-3">
                  <td className="num">{e.seq}</td>
                  <td className="num">{fmtTime(e.at)}</td>
                  <td><button type="button" onClick={() => onSelect(e.finding_id)} className="num text-primary underline underline-offset-2">{e.finding_id}</button></td>
                  <td className="font-semibold">{DECISION_LABEL[e.decision]}</td>
                  <td>{e.reviewer}</td>
                  <td>{CONCERN_LABEL[e.concern_at_decision]}</td>
                  <td className="num text-xs text-muted-foreground" title={e.hash}>{e.hash.slice(0, 12)}</td>
                </tr>
                <tr><td colSpan={7} className="pb-2 pt-0.5 text-muted-foreground">{e.note}</td></tr>
              </Fragment>
            ))}
          </tbody>
        </table></div>
        </>
      )}
    </div>
  );
}
