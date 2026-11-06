#!/usr/bin/env python3
"""Step A4 visual proof: one HTML page per database showing what scripts/inspect_mdb.py found.

    python3 scripts/schema_report.py data/derived/schema_ific3074.json --kind space \
        --out reports/schema/schema_ific3074.html

Expected tables and columns are the ones named in pm_pack/06_AGENTS_Master_Context.md ("ITU tables we
expect"). Each is marked FOUND or MISSING, with a text label as well as a colour. The page also lists every
other table with its row count and three sample rows, so a person can check the data by eye.
Writes a JSON summary next to the HTML (same name, .summary.json) for tests.
"""
from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

# From pm_pack/06 section "ITU tables we expect" [HYPOTHESIS until this report says FOUND].
EXPECTED = {
    "space": {
        "notice": ["ntc_id", "adm", "ntwk_org", "ntc_type", "ntf_rsn", "prov", "act_code", "d_rcv",
                   "wic_no", "wic_part", "d_wic", "tgt_ntc_id"],
        "geo": ["ntc_id", "sat_name", "long_nom"],
        "non_geo": ["ntc_id", "sat_name", "ref_body"],
        "grp": ["grp_id", "ntc_id", "beam_name", "emi_rcp", "freq_min", "freq_max", "bdwdth", "d_inuse",
                "adm_resp", "op_agcy"],
        "assgn": ["grp_id", "seq_no", "freq_mhz"],
        "emiss": ["grp_id", "seq_no", "design_emi", "pep_max", "pwr_ds_max", "pwr_ds_nbw"],
        "s_beam": ["ntc_id", "emi_rcp", "beam_name", "gain", "f_steer"],
        "srv_area": ["grp_id", "ctry", "f_excl_api"],
        "srv_cls": ["grp_id", "stn_cls", "nat_srv"],
        "orbit": ["ntc_id", "orb_id", "nbr_sat_pl", "inclin_ang", "apog_km", "perig_km", "right_asc", "perig_arg"],
        "phase": ["ntc_id", "orb_id"],
        "mask_info": [],
        "e_as_stn": ["grp_id", "stn_name", "long_dec", "lat_dec", "gain"],  # links via grp_id, not ntc_id [CHECKED 3074]
        "e_ant": ["ntc_id", "gain"],
        "provn": [],
        "all_aff_ntw": [],
        "tr_aff_ntw": [],
        "pub_ssn": ["ntc_id", "ssn_ref", "ssn_no"],
    },
    "terrestrial": {
        "fxm_terra": ["terrakey", "adm", "fragment", "freq_assgn", "freq_min", "freq_max", "bdwdth", "emi_cls",
                      "stn_cls", "notice_typ", "intent", "d_rcv", "geo_key"],
        "fxm_geo": ["geo_key", "ctry", "site_name", "long_dec", "lat_dec", "site_alt"],  # site_alt lives here [CHECKED 3076]
        "fxm_geo_pt": ["geo_key", "long_dec", "lat_dec"],
        "fxm_tx": ["terrakey", "ant_key", "geo_key"],
        "fxm_ant": ["pwr_ant", "gain_max", "gain_type", "ant_dir", "azm_max_e", "hgt_agl", "eff_hgtmax", "polar"],
        "fxm_ant_hgt": [],
    },
}

CSS = """
:root { --bg:#fbf8fa; --fg:#221a20; --muted:#6f6470; --line:#e6dde3; --ok:#1f7a4d; --okbg:#e3f4ea;
        --bad:#a32035; --badbg:#fbe4e8; --warn:#8a5a00; --warnbg:#fdf1d8; --card:#ffffff; }
@media (prefers-color-scheme: dark) { :root { --bg:#17131a; --fg:#efe7ee; --muted:#a99fab; --line:#3a3140;
        --ok:#7fd8a6; --okbg:#173326; --bad:#ff9aa9; --badbg:#3a1820; --warn:#f2c46b; --warnbg:#382a10; --card:#201a24; } }
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
.cols code { display:inline-block; margin:1px 3px 1px 0; padding:0 4px; border-radius:4px; background:var(--bg); }
.cols code.miss { background:var(--badbg); color:var(--bad); }
details { margin:4px 0; } summary { cursor:pointer; }
.scroll { overflow-x:auto; }
"""


def esc(v: object) -> str:
    return html.escape(str(v))


def badge(ok: bool, yes: str = "FOUND", no: str = "MISSING") -> str:
    return f'<span class="badge {"ok" if ok else "bad"}">{yes if ok else no}</span>'


def sample_table(columns: list[str], rows: list[list[str]]) -> str:
    if not rows:
        return '<p class="sub">No rows.</p>'
    head = "".join(f"<th><code>{esc(c)}</code></th>" for c in columns)
    body = "".join("<tr>" + "".join(f"<td><code>{esc(v[:80])}</code></td>" for v in r) + "</tr>" for r in rows)
    return f'<div class="scroll"><table><tr>{head}</tr>{body}</table></div>'


def build(schema: dict, kind: str) -> tuple[str, dict]:
    tables = schema["tables"]
    lower = {t.lower(): t for t in tables}
    expected = EXPECTED[kind]
    found_tables, missing_tables, missing_columns = [], [], {}
    rows_html = []
    for name, cols in expected.items():
        actual = lower.get(name.lower())
        if not actual:
            missing_tables.append(name)
            rows_html.append(f"<tr><td><code>{esc(name)}</code></td><td>{badge(False)}</td><td class='num'>-</td>"
                             f"<td class='cols'>{''.join(f'<code class=miss>{esc(c)}</code>' for c in cols)}</td></tr>")
            continue
        found_tables.append(name)
        meta = tables[actual]
        have = {c.lower() for c in meta["columns"]}
        miss = [c for c in cols if c.lower() not in have]
        if miss:
            missing_columns[name] = miss
        chips = "".join(f'<code class="{"miss" if c in miss else ""}">{esc(c)}</code>' for c in cols)
        empty = meta["rows"] == 0
        status = badge(True) if not empty else '<span class="badge warn">EMPTY</span>'
        rows_html.append(f"<tr><td><code>{esc(actual)}</code></td><td>{status}</td>"
                         f"<td class='num'>{meta['rows']:,}</td><td class='cols'>{chips or '<span class=sub>no columns required</span>'}"
                         f"{'<br><b>missing: ' + esc(', '.join(miss)) + '</b>' if miss else ''}</td></tr>")

    all_rows = []
    for name, meta in sorted(tables.items(), key=lambda kv: -kv[1]["rows"]):
        exp = name.lower() in expected
        all_rows.append(
            f"<details><summary><code>{esc(name)}</code> &middot; {meta['rows']:,} rows &middot; "
            f"{len(meta['columns'])} columns{' &middot; <span class=\"badge ok\">EXPECTED</span>' if exp else ''}</summary>"
            f"<p class='cols'>{''.join(f'<code>{esc(c)}</code>' for c in meta['columns'])}</p>"
            f"{sample_table(meta['columns'], meta.get('sample', []))}</details>")

    summary = {
        "file": schema["file"], "kind": kind, "tables": len(tables),
        "total_rows": sum(m["rows"] for m in tables.values()),
        "empty_tables": sorted(n for n, m in tables.items() if m["rows"] == 0),
        "expected_found": found_tables, "expected_missing": missing_tables,
        "expected_columns_missing": missing_columns,
    }
    ok_all = not missing_tables and not missing_columns
    page = f"""<!doctype html><html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1"><title>Schema {esc(Path(schema['file']).name)}</title>
<style>{CSS}</style></head><body><main>
<h1>Schema of {esc(Path(schema['file']).name)}</h1>
<p class="sub">Step A4 of pm_pack/08. Read with mdbtools; expected names from pm_pack/06. {badge(ok_all, 'ALL EXPECTED NAMES FOUND', 'SOME EXPECTED NAMES MISSING')}</p>
<div class="tiles">
<div class="tile"><b>{summary['tables']}</b><span>tables</span></div>
<div class="tile"><b>{summary['total_rows']:,}</b><span>rows in all tables</span></div>
<div class="tile"><b>{len(found_tables)} / {len(expected)}</b><span>expected tables found</span></div>
<div class="tile"><b>{sum(len(v) for v in missing_columns.values())}</b><span>expected columns missing</span></div>
<div class="tile"><b>{len(summary['empty_tables'])}</b><span>empty tables</span></div>
</div>
<h2>Expected tables</h2>
<table><tr><th>Table</th><th>Status</th><th>Rows</th><th>Columns we need (red = not in the file)</th></tr>{''.join(rows_html)}</table>
<h2>Every table in the file, largest first</h2>
<p class="sub">Click a table to see its columns and the first three rows.</p>
{''.join(all_rows)}
</main></body></html>"""
    return page, summary


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("schema", type=Path)
    ap.add_argument("--kind", choices=EXPECTED, required=True)
    ap.add_argument("--out", type=Path, required=True)
    args = ap.parse_args()
    listing = json.loads(args.schema.read_text(encoding="utf-8"))
    page, summary = build(listing[0], args.kind)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(page, encoding="utf-8")
    args.out.with_suffix(".summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"written {args.out}: {len(summary['expected_found'])} expected tables found, "
          f"missing {summary['expected_missing'] or 'none'}, columns missing {summary['expected_columns_missing'] or 'none'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
