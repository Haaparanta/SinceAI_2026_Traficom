"""Shared building blocks for the stage reports (pm_pack/08 section 2).

Every stage report is one self-contained HTML file plus a .summary.json that the tests read, so the picture
and the test can never disagree. Status always carries a text label, never colour alone.
"""
from __future__ import annotations

import html
import json
from pathlib import Path

CSS = """
:root { --bg:#fbf8fa; --fg:#221a20; --muted:#6f6470; --line:#e6dde3; --ok:#1f7a4d; --okbg:#e3f4ea;
        --bad:#a32035; --badbg:#fbe4e8; --warn:#8a5a00; --warnbg:#fdf1d8; --card:#ffffff; --accent:#b0407a; }
@media (prefers-color-scheme: dark) { :root { --bg:#17131a; --fg:#efe7ee; --muted:#a99fab; --line:#3a3140;
        --ok:#7fd8a6; --okbg:#173326; --bad:#ff9aa9; --badbg:#3a1820; --warn:#f2c46b; --warnbg:#382a10;
        --card:#201a24; --accent:#f08cc0; } }
body { margin:0; background:var(--bg); color:var(--fg); font:14px/1.45 -apple-system, system-ui, sans-serif; }
main { max-width:1200px; margin:0 auto; padding:24px 16px 64px; }
h1 { font-size:22px; margin:0 0 4px; } h2 { font-size:17px; margin:32px 0 8px; }
.sub { color:var(--muted); margin:0 0 16px; }
.tiles { display:flex; gap:12px; flex-wrap:wrap; margin:16px 0; }
.tile { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:10px 14px; min-width:140px; }
.tile b { display:block; font-size:22px; } .tile span { color:var(--muted); font-size:12px; }
table { border-collapse:collapse; width:100%; background:var(--card); border:1px solid var(--line); }
th, td { text-align:left; padding:6px 8px; border-bottom:1px solid var(--line); vertical-align:top; }
th { font-size:12px; color:var(--muted); font-weight:600; }
td.num { text-align:right; font-variant-numeric:tabular-nums; }
.badge { display:inline-block; padding:1px 7px; border-radius:999px; font-size:11px; font-weight:700; letter-spacing:.02em; }
.ok { background:var(--okbg); color:var(--ok); } .bad { background:var(--badbg); color:var(--bad); }
.warn { background:var(--warnbg); color:var(--warn); }
code { font:12px ui-monospace, Menlo, monospace; }
.scroll { overflow-x:auto; }
details { margin:4px 0; } summary { cursor:pointer; }
"""


def esc(v: object) -> str:
    return html.escape("" if v is None else str(v))


def badge(status: str) -> str:
    cls = {"PASS": "ok", "FOUND": "ok", "FAIL": "bad", "MISSING": "bad"}.get(status, "warn")
    return f'<span class="badge {cls}">{esc(status)}</span>'


def tiles(items: list[tuple[str, str]]) -> str:
    return '<div class="tiles">' + "".join(
        f'<div class="tile"><b>{esc(v)}</b><span>{esc(k)}</span></div>' for k, v in items) + "</div>"


def table(headers: list[str], rows: list[list[str]], raw: bool = False) -> str:
    """rows are HTML when raw=True, otherwise escaped text."""
    head = "".join(f"<th>{esc(h)}</th>" for h in headers)
    body = "".join("<tr>" + "".join(f"<td>{c if raw else esc(c)}</td>" for c in r) + "</tr>" for r in rows)
    return f'<div class="scroll"><table><tr>{head}</tr>{body}</table></div>'


def page(title: str, subtitle: str, body: str, extra_css: str = "") -> str:
    return (f'<!doctype html><html lang="en"><head><meta charset="utf-8">'
            f'<meta name="viewport" content="width=device-width, initial-scale=1"><title>{esc(title)}</title>'
            f"<style>{CSS}{extra_css}</style></head><body><main><h1>{esc(title)}</h1>"
            f'<p class="sub">{subtitle}</p>{body}</main></body></html>')


def write(out: Path, html_text: str, summary: dict) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html_text, encoding="utf-8")
    out.with_suffix(".summary.json").write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
