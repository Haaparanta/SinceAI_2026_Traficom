"""Evidence helpers shared by the assembler (which writes excerpts) and the resolver (which checks them).

Locator grammar for ITU rows:  <table>.<col>=<value>[&<col>=<value>...]   e.g. provn.grp_id=95600334&adm=FIN
Excerpt grammar for ITU rows:  <col>=<value>[; <col>=<value>...]          values formatted by fmt()
Calculation locators:          geography(notice_id=<id>) | geography(group_id=<id>)
Finnish table rows:            Taajuusjakotaulukko.ID=<id>, excerpt from radar.adapters.traficom_table.evidence()

The resolver (radar.evidence_check) reopens every locator and requires the excerpt to match exactly.
"""
from __future__ import annotations

from datetime import date, datetime

import duckdb


def fmt(v) -> str:
    if v is None:
        return "NULL"
    if isinstance(v, datetime):
        return v.date().isoformat() if v.time() == datetime.min.time() else v.isoformat(sep=" ")
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, float):
        return f"{v:.6g}"
    return str(v)


def locator(table: str, **keys) -> str:
    return table + "." + "&".join(f"{k}={v}" for k, v in keys.items())


def parse_locator(loc: str) -> tuple[str, dict[str, str]]:
    table, rest = loc.split(".", 1)
    return table, dict(part.split("=", 1) for part in rest.split("&"))


def row_excerpt(con: duckdb.DuckDBPyConnection, table: str, keys: dict, fields: list[str]) -> str | None:
    """Excerpt for the first row matching keys (string comparison on the key columns), or None."""
    where = " AND ".join(f'CAST("{k}" AS VARCHAR) = ?' for k in keys)
    row = con.execute(f'SELECT {", ".join(f"{chr(34)}{f}{chr(34)}" for f in fields)} FROM "{table}" WHERE {where} '
                      f'ORDER BY "_row" LIMIT 1', [str(v) for v in keys.values()]).fetchone()
    if row is None:
        return None
    return "; ".join(f"{f}={fmt(v)}" for f, v in zip(fields, row))


def parse_excerpt(excerpt: str) -> list[str]:
    return [p.split("=", 1)[0] for p in excerpt.split("; ")]
