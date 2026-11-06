"""Filing Radar backend.

The geometry and reference data of the `scoring` package (repository root) are reused here; make the root importable
however the app is started (uvicorn --app-dir backend, pytest, scripts).
"""
import sys
from pathlib import Path

_ROOT = str(Path(__file__).resolve().parents[2])
if _ROOT not in sys.path:
    sys.path.append(_ROOT)
