"""Paths and switches. Values come from the environment so the same code runs live and in demo mode."""
from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


class Settings:
    data_dir: Path = Path(os.environ.get("DATA_DIR", ROOT / "data"))
    reports_dir: Path = Path(os.environ.get("REPORTS_DIR", ROOT / "reports"))
    demo_mode: bool = os.environ.get("DEMO_MODE", "0") == "1"
    llm_model: str = os.environ.get("LLM_MODEL", "claude-opus-5-5")
    llm_disabled: bool = os.environ.get("LLM_DISABLED", "0") == "1"
    # Keep the M1 responsive: DuckDB gets at most 3 GB and 4 threads (pm_pack/08 section 1).
    duckdb_memory_limit: str = os.environ.get("DUCKDB_MEMORY_LIMIT", "3GB")
    duckdb_threads: int = int(os.environ.get("DUCKDB_THREADS", "4"))

    @property
    def raw_dir(self) -> Path:
        return self.data_dir / "raw"

    @property
    def derived_dir(self) -> Path:
        return self.data_dir / "derived"

    def prompt(self, name: str) -> str:
        return (ROOT / "prompts" / f"{name}.md").read_text(encoding="utf-8")


settings = Settings()
