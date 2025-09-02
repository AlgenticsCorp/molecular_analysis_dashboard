#!/usr/bin/env python3
"""Render code relationship graphs for a Python repo.

Outputs two SVGs under docs/atlas/ by default:
  - calls.svg    : approximate function-level call graph (via pyan3)
  - imports.svg  : module/package import dependency graph (via AST)

Usage (from repo root):
    python tools/render_graphs.py \
        --src src \
        --out docs/atlas \
        --repo-url https://github.com/your-org/your-repo/blob/main

Notes:
  * Requires Graphviz `dot` in PATH for DOT→SVG rendering.
  * `pyan3` generates an approximate call graph from source.
  * Import graph focuses on *in-repo* modules (filters external imports).
"""
from __future__ import annotations

import argparse
import ast
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Dict, Iterable, List, Set, Tuple

# ----------------------------- CLI ----------------------------- #


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Render call and import graphs as SVGs.")
    p.add_argument("--src", default="src", help="Source directory to scan (default: src)")
    p.add_argument(
        "--out", default="docs/atlas", help="Output directory for graphs (default: docs/atlas)"
    )
    p.add_argument(
        "--repo-url",
        default=None,
        help=(
            "Optional repository web URL prefix to hyperlink nodes, e.g. "
            "https://github.com/org/repo/blob/main"
        ),
    )
    p.add_argument(
        "--exclude",
        action="append",
        default=["**/tests/**", "**/.venv/**"],
        help="Glob(s) to exclude (can pass multiple)",
    )
    p.add_argument("--no-calls", action="store_true", help="Skip generating calls.svg")
    p.add_argument("--no-imports", action="store_true", help="Skip generating imports.svg")
    return p.parse_args()


# ------------------------ Common helpers ----------------------- #


def ensure_tool(name: str) -> None:
    if shutil.which(name) is None:
        print(f"ERROR: required tool '{name}' not found in PATH", file=sys.stderr)
        sys.exit(2)


def gather_py_files(root: Path, excludes: Iterable[str]) -> List[Path]:
    # naive glob traversal + exclude filtering
    files = [p for p in root.rglob("*.py")]
    excluded: Set[Path] = set()
    for pattern in excludes:
        excluded.update(
            set(root.rglob(pattern.replace("**/", "")))
            if pattern.startswith("**/")
            else set(root.rglob(pattern))
        )

    # Filter out any path that matches an exclude pattern substring
    def is_excluded(p: Path) -> bool:
        for pattern in excludes:
            if p.match(pattern):
                return True
        return False

    return [p for p in files if not is_excluded(p)]


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


# ---------------------- Calls graph (pyan3) -------------------- #


def render_calls_svg(py_files: List[Path], out_dir: Path) -> Path:
    dot_path = out_dir / "calls.dot"
    svg_path = out_dir / "calls.svg"

    if not py_files:
        print("No Python files to analyze for call graph; skipping.")
        return svg_path

    # Build DOT with pyan3
    cmd = [
        "pyan3",
        *[str(p) for p in py_files],
        "--dot",
        "--grouped",
        "--colours",
        "-o",
        str(dot_path),
    ]
    subprocess.check_call(cmd)

    # dot -> svg
    subprocess.check_call(["dot", "-Tsvg", str(dot_path), "-o", str(svg_path)])
    print(f"Wrote {svg_path}")
    return svg_path


# ---------------------- Import graph (AST) --------------------- #


def module_name_from_path(src_root: Path, file_path: Path) -> str:
    rel = file_path.relative_to(src_root)
    return ".".join(rel.with_suffix("").parts)


def build_internal_module_set(src_root: Path, py_files: List[Path]) -> Set[str]:
    return {module_name_from_path(src_root, f) for f in py_files}


def collect_import_edges(
    src_root: Path, py_files: List[Path], internal_modules: Set[str]
) -> Set[Tuple[str, str]]:
    edges: Set[Tuple[str, str]] = set()
    for f in py_files:
        mod = module_name_from_path(src_root, f)
        try:
            tree = ast.parse(f.read_text(encoding="utf-8"))
        except SyntaxError as e:
            print(f"WARN: skipping {f} (SyntaxError: {e})")
            continue
        imports: Set[str] = set()
        for n in ast.walk(tree):
            if isinstance(n, ast.ImportFrom):
                if n.module:
                    imports.add(n.module)
            elif isinstance(n, ast.Import):
                for a in n.names:
                    imports.add(a.name)
        # keep only edges that point to internal modules (or their parent packages)
        for imp in imports:
            # try to match import prefix to an internal module
            parts = imp.split(".")
            while parts:
                candidate = ".".join(parts)
                if any(m == candidate or m.startswith(candidate + ".") for m in internal_modules):
                    edges.add((mod, candidate))
                    break
                parts.pop()
    return edges


def build_imports_dot(
    internal_modules: Set[str], edges: Set[Tuple[str, str]], repo_url: str | None, src_root: Path
) -> str:
    # Cluster by top-level package
    packages: Dict[str, List[str]] = {}
    for m in sorted(internal_modules):
        top = m.split(".")[0]
        packages.setdefault(top, []).append(m)

    lines: List[str] = [
        "digraph imports {",
        "  rankdir=LR;",
        "  graph [fontsize=10];",
        "  node  [shape=box, fontsize=10];",
        "  edge  [fontsize=9, arrowsize=0.7];",
    ]

    # clusters
    for i, (pkg, mods) in enumerate(sorted(packages.items())):
        lines.append(
            f'  subgraph cluster_{i} {{ label="{pkg}"; fontsize=12; style=rounded; color=gray50;'
        )
        for m in mods:
            url_attr = ""
            if repo_url:
                file_path = src_root / Path(*m.split("."))
                # Try .py and __init__.py
                if (file_path.with_suffix(".py")).exists():
                    repo_link = f"{repo_url}/src/{'/'.join(m.split('.'))}.py"
                elif (file_path / "__init__.py").exists():
                    repo_link = f"{repo_url}/src/{'/'.join(m.split('.'))}/__init__.py"
                else:
                    repo_link = f"{repo_url}"
                url_attr = f', URL="{repo_link}", target="_blank"'
            lines.append(f'    "{m}" [shape=box{url_attr}];')
        lines.append("  }")

    # edges
    for a, b in sorted(edges):
        if a == b:
            continue
        lines.append(f'  "{a}" -> "{b}";')

    lines.append("}")
    return "\n".join(lines)


def render_imports_svg(
    src_root: Path, py_files: List[Path], out_dir: Path, repo_url: str | None
) -> Path:
    internal = build_internal_module_set(src_root, py_files)
    edges = collect_import_edges(src_root, py_files, internal)
    dot_text = build_imports_dot(internal, edges, repo_url, src_root)

    dot_path = out_dir / "imports.dot"
    svg_path = out_dir / "imports.svg"
    write_text(dot_path, dot_text)
    subprocess.check_call(["dot", "-Tsvg", str(dot_path), "-o", str(svg_path)])
    print(f"Wrote {svg_path}")
    return svg_path


# ----------------------------- Main ---------------------------- #


def main() -> int:
    args = parse_args()

    src_root = Path(args.src).resolve()
    out_dir = Path(args.out).resolve()

    if not src_root.exists():
        print(f"ERROR: src dir not found: {src_root}", file=sys.stderr)
        return 2

    # required tools
    ensure_tool("dot")
    if not args.no_calls:
        ensure_tool("pyan3")  # pyan3 is a console_script provided by the pyan3 package

    py_files = gather_py_files(src_root, args.exclude)
    if not py_files:
        print("WARN: No Python files found under src; nothing to do.")
        out_dir.mkdir(parents=True, exist_ok=True)
        return 0

    out_dir.mkdir(parents=True, exist_ok=True)

    if not args.no_calls:
        try:
            render_calls_svg(py_files, out_dir)
        except subprocess.CalledProcessError as e:
            print(f"ERROR generating calls.svg: {e}", file=sys.stderr)

    if not args.no_imports:
        try:
            render_imports_svg(src_root, py_files, out_dir, args.repo_url)
        except subprocess.CalledProcessError as e:
            print(f"ERROR generating imports.svg: {e}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
