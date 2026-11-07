"""Print the Python test files affected by the changes on this branch (used by `make test-changed`).

A change counts if it is committed since the merge base with BASE (default main), staged, unstaged or untracked.
A test file is affected when it changed itself, or when it imports (directly or through other repo modules) a
module that changed. A changed data, prompt or config file counts as a change to every module that names it.
When a change cannot be traced to modules (a shared contract, the pytest config, a file nobody names), every
test is printed: running too many is safe, running too few is not.

The file list goes to stdout, the reasons to stderr. `make test` before a commit stays the rule.
"""
from __future__ import annotations

import argparse
import ast
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALL = ["tests", "scoring/tests"]
# Roots that put modules on the import path (pyproject: pythonpath = ["backend", "."]).
SOURCE_ROOTS = [ROOT / "backend", ROOT]
CODE_DIRS = ["backend/radar", "scoring", "scripts", "tests"]
# Changing any of these can move every test; run them all.
RUN_ALL = {"pyproject.toml", "uv.lock", "backend/radar/models.py", "backend/radar/config.py",
           "tests/conftest.py", "scripts/changed_tests.py"}
# Changes here never reach a Python test.
IGNORED_PREFIXES = ("frontend/", "docs/", "pm_pack/", "research/", "solutions/", "design/", "reports/", ".claude/",
                    "results/proof/", ".github/")
IGNORED_SUFFIXES = (".md", ".pdf", ".png", ".jpg", ".svg", ".html")
IGNORED_FILES = {"Makefile", "Dockerfile", "cloudbuild.yaml", "LICENSE", ".gitignore", ".dockerignore", ".gcloudignore"}


def git(*args: str) -> list[str]:
    out = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return [line for line in out.splitlines() if line]


def changed_files(base: str) -> set[str]:
    merge_base = git("merge-base", "HEAD", base)[0]
    files = set(git("diff", "--name-only", merge_base))           # committed on the branch plus the working tree
    files |= set(git("ls-files", "--others", "--exclude-standard"))  # new files not yet added
    return files


def module_name(path: Path) -> str | None:
    for root in SOURCE_ROOTS:
        try:
            rel = path.relative_to(root)
        except ValueError:
            continue
        if root == ROOT and rel.parts[0] == "backend":
            continue
        parts = list(rel.with_suffix("").parts)
        if parts[-1] == "__init__":
            parts.pop()
        return ".".join(parts)
    return None


def repo_modules() -> dict[str, Path]:
    mods: dict[str, Path] = {}
    for d in CODE_DIRS:
        for p in (ROOT / d).rglob("*.py"):
            name = module_name(p)
            if name:
                mods[name] = p
    return mods


def imports_of(path: Path, mods: dict[str, Path]) -> set[str]:
    """Repo modules imported by one file. `from a.b import c` counts a.b.c when c is a module, else a.b."""
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return set()
    own = module_name(path) or ""
    found: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names = [a.name for a in node.names]
        elif isinstance(node, ast.ImportFrom):
            base = node.module or ""
            if node.level:
                pkg = own.split(".")
                if not path.name == "__init__.py":
                    pkg = pkg[:-1]
                pkg = pkg[: len(pkg) - (node.level - 1)] if node.level > 1 else pkg
                base = ".".join([*pkg, base] if base else pkg)
            names = [f"{base}.{a.name}" for a in node.names] + [base]
        else:
            continue
        for name in names:
            # the module itself and every parent package it runs on import
            parts = name.split(".")
            for i in range(1, len(parts) + 1):
                cand = ".".join(parts[:i])
                if cand in mods:
                    found.add(cand)
    return found


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", default="main")
    ap.add_argument("files", nargs="*", help="repo-relative paths to treat as changed instead of asking git")
    args = ap.parse_args()

    def say(msg: str) -> None:
        print(msg, file=sys.stderr)

    try:
        changes = set(args.files) or changed_files(args.base)
    except (subprocess.CalledProcessError, IndexError):
        say(f"cannot compare with {args.base}; running every test")
        print(" ".join(ALL))
        return 0

    mods = repo_modules()
    by_path = {p.relative_to(ROOT).as_posix(): m for m, p in mods.items()}
    graph = {m: imports_of(p, mods) for m, p in mods.items()}
    texts = {m: p.read_text(encoding="utf-8", errors="ignore") for m, p in mods.items()}

    touched: set[str] = set()
    for f in sorted(changes):
        if f in RUN_ALL:
            say(f"{f} is shared by everything; running every test")
            print(" ".join(ALL))
            return 0
        loaded_by_code = f.startswith(("prompts/", "data/", "backend/", "scoring/", "tests/"))
        if f in IGNORED_FILES or f.startswith(IGNORED_PREFIXES) or (f.endswith(IGNORED_SUFFIXES) and not loaded_by_code):
            continue
        if f in by_path:
            touched.add(by_path[f])
            continue
        if f.endswith(".py"):
            continue  # deleted module: whatever imported it changed too, or fails to import under make test
        # data, prompt or config file: every module that names it
        name = Path(f).name
        users = {m for m, t in texts.items() if name in t}
        if not users:
            say(f"{f} is not named by any module; running every test")
            print(" ".join(ALL))
            return 0
        touched |= users

    # every module that reaches a touched module through imports
    affected = set(touched)
    grew = True
    while grew:
        grew = False
        for m, deps in graph.items():
            if m not in affected and deps & affected:
                affected.add(m)
                grew = True

    tests = sorted(
        p.relative_to(ROOT).as_posix() for m, p in mods.items()
        if m in affected and p.name.startswith("test_") and (p.parent.name == "tests")
    )
    if touched:
        say("changed modules: " + ", ".join(sorted(touched)))
    say(f"{len(tests)} test file(s) affected" if tests else "no Python test is affected by these changes")
    print(" ".join(tests))
    return 0


if __name__ == "__main__":
    sys.exit(main())
