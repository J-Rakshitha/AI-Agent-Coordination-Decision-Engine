"""AST-based Python code analysis — shared by Discovery, Semantic, and Quality agents."""
from __future__ import annotations

import ast
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

logger = logging.getLogger("code_parser")

BACKEND_ROOT = Path(__file__).resolve().parents[2]
PROJECT_ROOT = BACKEND_ROOT.parent
DEFAULT_SCAN_ROOTS = [
    PROJECT_ROOT / "backend" / "app",
    PROJECT_ROOT / "frontend" / "src",
]


@dataclass
class SymbolInfo:
    file_path: str
    symbol_type: str  # function | class | import
    name: str
    line_start: int
    line_end: int
    dependencies: list[str] = field(default_factory=list)
    complexity: int = 1
    source_snippet: str = ""


def _rel_path(path: Path) -> str:
    try:
        return str(path.relative_to(PROJECT_ROOT)).replace("\\", "/")
    except ValueError:
        return str(path).replace("\\", "/")


def _complexity(node: ast.AST) -> int:
    """McCabe-style branch count (stdlib only)."""
    score = 1
    for child in ast.walk(node):
        if isinstance(child, (ast.If, ast.For, ast.While, ast.Try, ast.With, ast.BoolOp)):
            score += 1
    return score


def parse_python_file(path: Path) -> list[SymbolInfo]:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError as exc:
        logger.warning("Cannot read %s: %s", path, exc)
        return []

    rel = _rel_path(path)
    try:
        tree = ast.parse(source, filename=rel)
    except SyntaxError as exc:
        logger.warning("Syntax error in %s: %s", rel, exc)
        return []

    lines = source.splitlines()
    symbols: list[SymbolInfo] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef | ast.AsyncFunctionDef):
            deps = sorted(
                {
                    getattr(n, "id", getattr(n, "attr", ""))
                    for n in ast.walk(node)
                    if isinstance(n, ast.Name) and isinstance(n.ctx, ast.Load)
                }
            )
            snippet = "\n".join(lines[node.lineno - 1 : node.end_lineno or node.lineno])
            symbols.append(
                SymbolInfo(
                    file_path=rel,
                    symbol_type="function",
                    name=node.name,
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    dependencies=deps[:30],
                    complexity=_complexity(node),
                    source_snippet=snippet[:4000],
                )
            )
        elif isinstance(node, ast.ClassDef):
            deps = sorted(
                {b.id for b in node.bases if isinstance(b, ast.Name)}
            )
            snippet = "\n".join(lines[node.lineno - 1 : node.end_lineno or node.lineno])
            symbols.append(
                SymbolInfo(
                    file_path=rel,
                    symbol_type="class",
                    name=node.name,
                    line_start=node.lineno,
                    line_end=node.end_lineno or node.lineno,
                    dependencies=deps,
                    complexity=_complexity(node),
                    source_snippet=snippet[:4000],
                )
            )
        elif isinstance(node, ast.Import):
            for alias in node.names:
                symbols.append(
                    SymbolInfo(
                        file_path=rel,
                        symbol_type="import",
                        name=alias.name,
                        line_start=node.lineno,
                        line_end=node.lineno,
                        dependencies=[alias.name],
                    )
                )
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ""
            for alias in node.names:
                symbols.append(
                    SymbolInfo(
                        file_path=rel,
                        symbol_type="import",
                        name=f"{module}.{alias.name}" if module else alias.name,
                        line_start=node.lineno,
                        line_end=node.lineno,
                        dependencies=[module or alias.name],
                    )
                )

    return symbols


def scan_local_repository(roots: list[Path] | None = None, max_files: int = 120) -> list[SymbolInfo]:
    roots = roots or DEFAULT_SCAN_ROOTS
    symbols: list[SymbolInfo] = []
    count = 0
    for root in roots:
        if not root.exists():
            continue
        for path in root.rglob("*.py"):
            if count >= max_files:
                break
            if any(part in path.parts for part in ("venv", ".venv", "__pycache__", "alembic")):
                continue
            symbols.extend(parse_python_file(path))
            count += 1
    return symbols


def find_symbol(symbols: list[SymbolInfo], file_path: str, function_name: str | None) -> SymbolInfo | None:
    normalized = file_path.replace("\\", "/")
    for sym in symbols:
        if sym.file_path.endswith(normalized) or normalized.endswith(sym.file_path):
            if function_name and sym.symbol_type == "function" and sym.name == function_name:
                return sym
            if not function_name and sym.symbol_type == "function":
                return sym
    for sym in symbols:
        if sym.file_path.endswith(normalized) or normalized in sym.file_path:
            if function_name and sym.name == function_name:
                return sym
    return None


def ast_diff_summary(source_a: str, source_b: str) -> dict[str, Any]:
    """Compare two Python source strings at AST level."""
    try:
        tree_a = ast.parse(source_a or "pass")
        tree_b = ast.parse(source_b or "pass")
    except SyntaxError:
        return {"comparable": False, "reason": "syntax_error"}

    names_a = {n.name for n in ast.walk(tree_a) if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)}
    names_b = {n.name for n in ast.walk(tree_b) if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef)}
    args_a = []
    args_b = []
    for n in ast.walk(tree_a):
        if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef):
            args_a = [a.arg for a in n.args.args]
            break
    for n in ast.walk(tree_b):
        if isinstance(n, ast.FunctionDef | ast.AsyncFunctionDef):
            args_b = [a.arg for a in n.args.args]
            break

    return {
        "comparable": True,
        "functions_added": sorted(names_b - names_a),
        "functions_removed": sorted(names_a - names_b),
        "signature_changed": args_a != args_b,
        "args_before": args_a,
        "args_after": args_b,
        "complexity_a": _complexity(tree_a),
        "complexity_b": _complexity(tree_b),
    }


def symbol_to_dict(sym: SymbolInfo) -> dict:
    return {
        "file_path": sym.file_path,
        "symbol_type": sym.symbol_type,
        "name": sym.name,
        "line_start": sym.line_start,
        "line_end": sym.line_end,
        "dependencies": sym.dependencies,
        "complexity": sym.complexity,
        "source_snippet": sym.source_snippet[:2000],
    }


def symbols_to_json(symbols: list[SymbolInfo]) -> str:
    return json.dumps([symbol_to_dict(s) for s in symbols[:500]])
