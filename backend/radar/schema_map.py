"""Access to schema_map.yaml: the only place ITU table and column names come from (pm_pack/06).

    M = schema_map.load()
    M.table("space", "group")                 -> 'grp'
    M.col("space", "group", "freq_min_mhz")   -> 'freq_min'
    M.q("space", "group", "freq_min_mhz")     -> '"grp"."freq_min"'  (quoted, for SQL)
"""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

PATH = Path(__file__).with_name("schema_map.yaml")


class SchemaMap:
    def __init__(self, data: dict):
        self.data = data

    def entity(self, kind: str, entity: str) -> dict:
        try:
            return self.data[kind][entity]
        except KeyError as exc:
            raise KeyError(f"schema_map.yaml has no {kind}.{entity}") from exc

    def table(self, kind: str, entity: str) -> str:
        return self.entity(kind, entity)["table"]

    def col(self, kind: str, entity: str, name: str) -> str:
        cols = self.entity(kind, entity).get("columns", {})
        if name not in cols:
            raise KeyError(f"schema_map.yaml has no column {kind}.{entity}.{name}")
        return cols[name]

    def q(self, kind: str, entity: str, name: str, alias: str | None = None) -> str:
        return f'"{alias or self.table(kind, entity)}"."{self.col(kind, entity, name)}"'

    def t(self, kind: str, entity: str) -> str:
        return f'"{self.table(kind, entity)}"'

    def setting(self, kind: str, key: str):
        return self.data[kind][key]


@lru_cache(maxsize=1)
def load(path: str = str(PATH)) -> SchemaMap:
    return SchemaMap(yaml.safe_load(Path(path).read_text(encoding="utf-8")))
