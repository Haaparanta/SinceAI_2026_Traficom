"""python -m radar.export --issue 3074 --kind space"""
from __future__ import annotations

import argparse

from radar.export.results import export_space


def main() -> int:
    ap = argparse.ArgumentParser(description="Write the graded results files for one IFIC issue.")
    ap.add_argument("--issue", type=int, required=True)
    ap.add_argument("--kind", choices=["space", "terrestrial"], required=True)
    args = ap.parse_args()
    if args.kind == "terrestrial":
        from radar.export.results import export_terrestrial
        t = export_terrestrial(args.issue)
        print(f"{t['paths']['csv']}: {t['rows']} rows {t['concern']}")
        return 0
    s = export_space(args.issue)
    print(f"{s['paths']['csv']}: {s['rows']} rows {s['concern']}")
    print(f"{s['paths']['groups_csv']}: {s['group_rows']} candidate group rows {s['group_concern']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
