#!/usr/bin/env python3
"""Schema extractor for Python repos.

Generates a machine-readable summary of modules, functions, and classes for
LLM agents and humans. Outputs JSON to docs/schema.json with:
- modules → imports, definitions
- functions → signature (args/types/defaults), returns, docstring/summary,
  dependencies (calls/imports), logical structure (branch counts),
  cyclomatic complexity (if radon installed)
- classes → docstring/summary, methods (same structure as functions)

Run:
    python tools/extract_schema.py
"""
from __future__ import annotations

import ast
import json
import sys
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Optional radon support for cyclomatic complexity
try:
    from radon.complexity import cc_visit  # type: ignore
except Exception:  # pragma: no cover - radon is optional
    cc_visit = None  # type: ignore

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC_DIR = PROJECT_ROOT / "src"
OUT_PATH = PROJECT_ROOT / "docs" / "schema.json"


# --------------------------- helpers --------------------------- #


def unparse(node: Optional[ast.AST]) -> Optional[str]:
    if node is None:
        return None
    try:
        return ast.unparse(node)  # py>=3.9
    except Exception:
        return None


def doc_summary(full: Optional[str]) -> Optional[str]:
    if not full:
        return None
    first = full.strip().splitlines()[0].strip()
    return first or None


def get_call_name(node: ast.AST) -> Optional[str]:
    """Extract dotted name from a Call.func expression if possible."""
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parts: List[str] = []
        cur: ast.AST = node
        while isinstance(cur, ast.Attribute):
            parts.append(cur.attr)
            cur = cur.value  # type: ignore[attr-defined]
        if isinstance(cur, ast.Name):
            parts.append(cur.id)
            return ".".join(reversed(parts))
    return None


def count_nodes(fn: ast.AST) -> Dict[str, int]:
    """Logical structure counters inside a function/method body."""
    counters = {
        "ifs": 0,
        "fors": 0,
        "whiles": 0,
        "trys": 0,
        "matches": 0,
        "withs": 0,
        "returns": 0,
        "assigns": 0,
    }
    for n in ast.walk(fn):
        if isinstance(n, ast.If):
            counters["ifs"] += 1
        elif isinstance(n, ast.For):
            counters["fors"] += 1
        elif isinstance(n, ast.While):
            counters["whiles"] += 1
        elif isinstance(n, ast.Try):
            counters["trys"] += 1
        elif isinstance(n, ast.Match):  # py3.10+
            counters["matches"] += 1
        elif isinstance(n, ast.With):
            counters["withs"] += 1
        elif isinstance(n, ast.Return):
            counters["returns"] += 1
        elif isinstance(n, ast.Assign):
            counters["assigns"] += 1
    return counters


def collect_calls(fn: ast.AST) -> List[str]:
    calls: List[str] = []
    for n in ast.walk(fn):
        if isinstance(n, ast.Call):
            name = get_call_name(n.func)
            if name:
                calls.append(name)
    # de-duplicate while preserving order
    seen = set()
    uniq: List[str] = []
    for c in calls:
        if c not in seen:
            seen.add(c)
            uniq.append(c)
    return uniq


def build_complexity_map(source: str) -> Dict[Tuple[str, int], int]:
    """Map (qualname, lineno) -> CC using radon if available."""
    result: Dict[Tuple[str, int], int] = {}
    if not cc_visit:
        return result
    try:
        for block in cc_visit(source):  # type: ignore[attr-defined]
            # block has .name, .lineno, .complexity
            key = (block.name, int(block.lineno))
            result[key] = int(block.complexity)
    except Exception:
        pass
    return result


def qualname(stack: List[str], name: str) -> str:
    return ".".join([*stack, name]) if stack else name


# --------------------------- dataclasses --------------------------- #


@dataclass
class Param:
    name: str
    annotation: Optional[str]
    default: Optional[str]


@dataclass
class FunctionInfo:
    name: str
    qualname: str
    lineno: int
    endlineno: Optional[int]
    summary: Optional[str]
    doc: Optional[str]
    returns: Optional[str]
    params: List[Param] = field(default_factory=list)
    calls: List[str] = field(default_factory=list)
    logical: Dict[str, int] = field(default_factory=dict)
    complexity: Optional[int] = None


@dataclass
class ClassInfo:
    name: str
    qualname: str
    lineno: int
    endlineno: Optional[int]
    summary: Optional[str]
    doc: Optional[str]
    methods: List[FunctionInfo] = field(default_factory=list)


@dataclass
class ModuleInfo:
    path: str
    module: str
    imports: List[str]
    functions: List[FunctionInfo] = field(default_factory=list)
    classes: List[ClassInfo] = field(default_factory=list)


# --------------------------- core extraction --------------------------- #


def parse_params(args: ast.arguments) -> List[Param]:
    params: List[Param] = []
    all_args: List[Tuple[str, Optional[ast.AST], Optional[ast.AST]]] = []

    # Positional-only (py3.8+)
    for a in getattr(args, "posonlyargs", []):
        all_args.append((a.arg, a.annotation, None))

    # Positional / keyword
    for a in args.args:
        all_args.append((a.arg, a.annotation, None))

    # Vararg *args
    if args.vararg:
        all_args.append(("*" + args.vararg.arg, args.vararg.annotation, None))

    # Keyword-only
    for a in args.kwonlyargs:
        all_args.append((a.arg, a.annotation, None))

    # Kwarg **kwargs
    if args.kwarg:
        all_args.append(("**" + args.kwarg.arg, args.kwarg.annotation, None))

    # Attach defaults to the rightmost args
    defaults = list(args.defaults or [])
    kw_defaults = list(args.kw_defaults or [])
    # Map defaults for positional/kw args (ignore posonly count for simplicity)
    idx = len([a for a in args.args]) - len(defaults)
    for i, d in enumerate(defaults):
        name, ann, _ = all_args[idx + i]
        all_args[idx + i] = (name, ann, d)
    for i, d in enumerate(kw_defaults):
        if d is None:
            continue
        # kwonlyargs defaults are aligned
        kname = args.kwonlyargs[i].arg if i < len(args.kwonlyargs) else None
        if kname:
            # find the tuple and update default
            for j, (nm, an, df) in enumerate(all_args):
                if nm == kname:
                    all_args[j] = (nm, an, d)
                    break

    for name, ann, d in all_args:
        params.append(Param(name=name, annotation=unparse(ann), default=unparse(d)))
    return params


def extract_functions(
    tree: ast.AST, source: str, module_stack: List[str]
) -> Tuple[List[FunctionInfo], List[ClassInfo]]:
    funcs: List[FunctionInfo] = []
    classes: List[ClassInfo] = []

    # Build complexity map once per module
    cc_map = build_complexity_map(source)

    class Visitor(ast.NodeVisitor):
        def __init__(self) -> None:
            self.class_stack: List[str] = []

        def visit_FunctionDef(self, node: ast.FunctionDef) -> Any:
            q = qualname([*module_stack, *self.class_stack], node.name)
            f = FunctionInfo(
                name=node.name,
                qualname=q,
                lineno=node.lineno,
                endlineno=getattr(node, "end_lineno", None),
                summary=doc_summary(ast.get_docstring(node)),
                doc=ast.get_docstring(node),
                returns=unparse(node.returns),
                params=parse_params(node.args),
                calls=collect_calls(node),
                logical=count_nodes(node),
                complexity=cc_map.get((node.name, node.lineno)),
            )
            if self.class_stack:
                if classes and classes[-1].name == self.class_stack[-1]:
                    classes[-1].methods.append(f)
                else:
                    # Defensive: find last matching class
                    for c in reversed(classes):
                        if c.name == self.class_stack[-1]:
                            c.methods.append(f)
                            break
            else:
                funcs.append(f)
            # Continue traversal
            self.generic_visit(node)

        def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> Any:  # treat similar
            self.visit_FunctionDef(node)  # type: ignore[arg-type]

        def visit_ClassDef(self, node: ast.ClassDef) -> Any:
            q = qualname([*module_stack], node.name)
            c = ClassInfo(
                name=node.name,
                qualname=q,
                lineno=node.lineno,
                endlineno=getattr(node, "end_lineno", None),
                summary=doc_summary(ast.get_docstring(node)),
                doc=ast.get_docstring(node),
                methods=[],
            )
            classes.append(c)
            self.class_stack.append(node.name)
            self.generic_visit(node)
            self.class_stack.pop()

    Visitor().visit(tree)
    return funcs, classes


def extract_module(py_path: Path) -> ModuleInfo:
    source = py_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    # module name from src-relative path
    rel = py_path.relative_to(SRC_DIR)
    module_name = ".".join(list(rel.with_suffix("").parts))

    imports: List[str] = []
    for n in ast.walk(tree):
        if isinstance(n, ast.Import):
            for a in n.names:
                imports.append(a.name)
        elif isinstance(n, ast.ImportFrom):
            mod = n.module or ""
            imports.append(mod)

    # de-dup imports while preserving order
    seen = set()
    uniq_imports: List[str] = []
    for imp in imports:
        if imp not in seen:
            seen.add(imp)
            uniq_imports.append(imp)

    funcs, classes = extract_functions(tree, source, module_stack=[module_name])

    return ModuleInfo(
        path=str(py_path.relative_to(PROJECT_ROOT)),
        module=module_name,
        imports=uniq_imports,
        functions=funcs,
        classes=classes,
    )


# --------------------------- entrypoint --------------------------- #


def main() -> int:
    if not SRC_DIR.exists():
        print(f"ERROR: src directory not found at {SRC_DIR}", file=sys.stderr)
        return 2

    modules: List[ModuleInfo] = []
    for py in SRC_DIR.rglob("*.py"):
        if py.name == "__init__.py":
            # include package-level file only for imports; skip functions/methods
            # to avoid clutter unless users want otherwise.
            # Still capture imports for __init__ if desired later.
            pass
        try:
            info = extract_module(py)
            modules.append(info)
        except SyntaxError as e:
            print(f"WARN: Skipping {py} due to SyntaxError: {e}")
        except Exception as e:
            print(f"WARN: Failed to parse {py}: {e}")

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "project_root": str(PROJECT_ROOT),
        "src": str(SRC_DIR),
        "modules": [
            {
                **asdict(m),
                "functions": [asdict(f) for f in m.functions],
                "classes": [
                    {**asdict(c), "methods": [asdict(mm) for mm in c.methods]} for c in m.classes
                ],
            }
            for m in modules
        ],
    }
    OUT_PATH.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    print(f"Wrote {OUT_PATH.relative_to(PROJECT_ROOT)} with {len(modules)} modules")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
