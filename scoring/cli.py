"""Command-line entry points.

  python -m scoring space INPUT.json [--out OUT.json] [--markdown OUT.md] [--as-of YYYY-MM-DD] [--finnish-networks F.json] [--config W.json] [--top N]
  python -m scoring terrestrial INPUT.json [--previous PREV.json] [--stations S.json] [--model auto|free-space|p1546] [--out OUT.json] [--markdown OUT.md] [--top N]
  python -m scoring evaluate SCORED.json LABELS.json
  python -m scoring explain SCORED.json [--id SUBJECT_ID]
"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import date

from . import __version__
from .adapters import (finnish_networks_from_json, protected_stations_from_json, space_groups_from_json, terrestrial_notices_from_json)
from .config import load_config
from .evaluate import priority_agreement, ranking_quality, threshold_sweep
from .explain import evidence_lines
from .finnish_table import FinnishTable
from .models import ScoredSubject
from .propagation import FreeSpaceModel, get_model
from .space_scoring import SpaceContext, aggregate_by_notice, rank_groups
from .terrestrial_scoring import TerrestrialContext, diff_notices, rank_notices, trends


def to_markdown(subjects: list[ScoredSubject], cfg: dict, title: str, top: int = 20) -> str:
    lines = [f"# {title}", "", f"Scoring model {cfg['version']} (scoring package {__version__}). Score = 100 x relevance x ({cfg['score']['severity_weight']} x severity + {cfg['score']['urgency_weight']} x urgency).", "",
             "| Rank | Score | Priority | Subject | Top Finnish target | Confidence | Deadline |", "|---|---|---|---|---|---|---|"]
    shown = [s for s in subjects if s.status == "active"][:top]
    for i, s in enumerate(shown, start=1):
        t = s.findings[0].target_label if s.findings else ""
        lines.append(f"| {i} | {s.score} | {s.priority} | {s.subject_label} | {t} | {s.confidence:.0%} | {s.deadline or ''} |")
    n_screen = sum(1 for s in subjects if s.status == "screened_out")
    n_wd = sum(1 for s in subjects if s.status == "withdrawn")
    lines += ["", f"{len(subjects)} subjects scored: {len([s for s in subjects if s.status == 'active'])} active, {n_screen} screened out, {n_wd} withdrawn/suppressed.", ""]
    for i, s in enumerate(shown, start=1):
        f = s.findings[0]
        lines += [f"## {i}. {s.subject_label}", "", s.summary, "", "```", f.explanation, "```", "", "Evidence:", ""]
        lines += [f"- {e}" for e in evidence_lines(f)]
        lines.append("")
    return "\n".join(lines)


def _write(obj, path: str | None) -> None:
    text = json.dumps(obj, indent=2, ensure_ascii=False, default=str)
    if path:
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
        print(f"wrote {path}")
    else:
        print(text)


def cmd_space(a: argparse.Namespace) -> int:
    cfg = load_config(a.config)
    groups = space_groups_from_json(a.input)
    ctx = SpaceContext(FinnishTable.load(), cfg, finnish_networks_from_json(a.finnish_networks) if a.finnish_networks else [],
                       as_of=date.fromisoformat(a.as_of) if a.as_of else None)
    scored = rank_groups(groups, ctx)
    out = {"meta": {"side": "space", "config_version": cfg["version"], "as_of": a.as_of, "groups": len(groups), "finnish_table": ctx.table.meta},
           "notices": aggregate_by_notice(scored, groups), "subjects": [s.to_dict() for s in scored]}
    _write(out, a.out)
    if a.markdown:
        with open(a.markdown, "w", encoding="utf-8") as fh:
            fh.write(to_markdown(scored, cfg, "Space IFIC findings for Finland", a.top))
        print(f"wrote {a.markdown}")
    for s in scored[: a.top]:
        print(f"{s.score:3d} {s.priority} {s.subject_label}  <- {s.findings[0].target_label if s.findings else ''}")
    return 0


def cmd_terrestrial(a: argparse.Namespace) -> int:
    cfg = load_config(a.config)
    notices = terrestrial_notices_from_json(a.input)
    diff = None
    if a.previous:
        diff = diff_notices(terrestrial_notices_from_json(a.previous), notices, cfg["terrestrial"]["technical_fields"])
    model = FreeSpaceModel() if a.model == "free-space" else get_model(a.model)
    ctx = TerrestrialContext(FinnishTable.load(), cfg, protected=protected_stations_from_json(a.stations) if a.stations else [], model=model,
                             as_of=date.fromisoformat(a.as_of) if a.as_of else None)
    scored = rank_notices(notices, ctx)
    out = {"meta": {"side": "terrestrial", "config_version": cfg["version"], "propagation_model": getattr(model, "name", str(model)), "notices": len(notices),
                    "diff": diff["counts"] if diff else None},
           "trends": trends(notices, [], cfg, ctx.region), "subjects": [s.to_dict() for s in scored]}
    if diff:
        out["withdrawn_since_previous"] = [n.label for n in diff["withdrawn"]]
    _write(out, a.out)
    if a.markdown:
        with open(a.markdown, "w", encoding="utf-8") as fh:
            fh.write(to_markdown(scored, cfg, "Terrestrial IFIC land-mobile findings for Finland", a.top))
        print(f"wrote {a.markdown}")
    for s in scored[: a.top]:
        print(f"{s.score:3d} {s.priority} {s.subject_label}  <- {s.findings[0].target_label if s.findings else ''}")
    return 0


def cmd_evaluate(a: argparse.Namespace) -> int:
    with open(a.scored, encoding="utf-8") as fh:
        data = json.load(fh)
    with open(a.labels, encoding="utf-8") as fh:
        labels = json.load(fh)
    subjects = [ScoredSubject(d["subject_id"], d["subject_label"], d["score"], d["priority"], d["confidence"], d["breadth"], [], d.get("summary", ""), d.get("status", "active"), d.get("deadline"))
                for d in data["subjects"]]
    res = {"sweep": threshold_sweep(subjects, labels), "ranking": ranking_quality(subjects, labels), "priority_agreement": priority_agreement(subjects, labels)}
    _write(res, a.out)
    return 0


def cmd_explain(a: argparse.Namespace) -> int:
    with open(a.scored, encoding="utf-8") as fh:
        data = json.load(fh)
    for d in data["subjects"]:
        if a.id and d["subject_id"] != a.id:
            continue
        print("=" * 100)
        print(d.get("summary") or d["subject_label"])
        for f in d["findings"][: a.top]:
            print("-" * 100)
            print(f["explanation"])
    return 0


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="python -m scoring", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("space"); s.add_argument("input"); s.add_argument("--out"); s.add_argument("--markdown"); s.add_argument("--as-of"); s.add_argument("--finnish-networks"); s.add_argument("--config"); s.add_argument("--top", type=int, default=20); s.set_defaults(fn=cmd_space)
    t = sub.add_parser("terrestrial"); t.add_argument("input"); t.add_argument("--previous"); t.add_argument("--stations"); t.add_argument("--model", default="auto"); t.add_argument("--out"); t.add_argument("--markdown"); t.add_argument("--as-of"); t.add_argument("--config"); t.add_argument("--top", type=int, default=20); t.set_defaults(fn=cmd_terrestrial)
    e = sub.add_parser("evaluate"); e.add_argument("scored"); e.add_argument("labels"); e.add_argument("--out"); e.set_defaults(fn=cmd_evaluate)
    x = sub.add_parser("explain"); x.add_argument("scored"); x.add_argument("--id"); x.add_argument("--top", type=int, default=3); x.set_defaults(fn=cmd_explain)
    a = p.parse_args(argv)
    return a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
