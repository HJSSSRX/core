import ast
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class PluginInfo:
    name: str
    version: str
    domain: str
    tool_count: int


@dataclass
class CodeIssue:
    file: str
    line: int
    severity: str  # LOW | MEDIUM | HIGH
    category: str  # unused_code | missing_test | complexity | security
    description: str


class PlatformIntrospection(ABC):
    """Read-only introspection surface for the Platform Optimizer role."""

    @abstractmethod
    def list_registered_plugins(self) -> list[PluginInfo]: ...

    @abstractmethod
    def get_skill_configurations(self) -> dict[str, Any]: ...

    @abstractmethod
    def get_recent_metrics(self, window_seconds: float) -> dict[str, Any]: ...


class IntrospectionAgent(PlatformIntrospection):
    """Scans the codebase for code quality issues and collects platform state."""

    def __init__(self, root: Path | None = None) -> None:
        self._root = root or Path(__file__).resolve().parent.parent

    def list_registered_plugins(self) -> list[PluginInfo]:
        """Discover plugins by scanning the cells/ directory."""
        plugins: list[PluginInfo] = []
        cells_root = self._root.parent / "cells"
        if not cells_root.exists():
            return plugins
        for cell_dir in sorted(cells_root.iterdir()):
            if not cell_dir.is_dir() or cell_dir.name.startswith("_") or cell_dir.name.startswith("."):
                continue
            plugin_file = cell_dir / "plugin.py"
            if not plugin_file.exists():
                continue
            try:
                tree = ast.parse(plugin_file.read_text(encoding="utf-8"))
                tool_count = len(
                    [n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and not n.name.startswith("_")]
                )
                plugins.append(
                    PluginInfo(
                        name=cell_dir.name,
                        version="0.1.0",
                        domain=cell_dir.name.replace("_", "-"),
                        tool_count=tool_count,
                    )
                )
            except (SyntaxError, UnicodeDecodeError):
                continue
        return plugins

    def get_skill_configurations(self) -> dict[str, Any]:
        """Read skill configurations from the claude config directory."""
        config: dict[str, Any] = {"skills": [], "hooks": []}
        config_dirs = [
            Path.home() / ".claude",
            self._root.parent / ".claude",
        ]
        for base in config_dirs:
            skills_dir = base / "plugins"
            if skills_dir.exists():
                for plugin_dir in skills_dir.iterdir():
                    if plugin_dir.is_dir():
                        config["skills"].append(str(plugin_dir))
            hooks_file = base / "settings.json"
            if hooks_file.exists():
                try:
                    import json

                    settings = json.loads(hooks_file.read_text(encoding="utf-8"))
                    config["hooks"] = list(settings.get("hooks", {}).keys())
                except (json.JSONDecodeError, OSError):
                    pass
        return config

    def get_recent_metrics(self, window_seconds: float = 3600.0) -> dict[str, Any]:
        """Collect recent platform metrics from the filesystem."""
        metrics: dict[str, Any] = {"test_count": 0, "plugin_count": 0, "kb_entry_count": 0}
        tests_dir = self._root.parent / "tests"
        if tests_dir.exists():
            metrics["test_count"] = len(list(tests_dir.rglob("test_*.py")))

        cells_root = self._root.parent / "cells"
        if cells_root.exists():
            metrics["plugin_count"] = len(
                [d for d in cells_root.iterdir() if d.is_dir() and (d / "plugin.py").exists()]
            )

        kb_dir = Path("shared") / "kb"
        if kb_dir.exists():
            metrics["kb_entry_count"] = len(list(kb_dir.glob("*.md")))

        return metrics

    def scan(self, root: Path | None = None) -> list[CodeIssue]:
        """Scan Python files for code quality issues."""
        root = root or self._root
        issues: list[CodeIssue] = []
        for py_file in root.rglob("*.py"):
            if "__pycache__" in str(py_file) or "tests" in str(py_file):
                continue
            issues.extend(self._analyze_file(py_file, root))
        return issues

    def _analyze_file(self, path: Path, root: Path) -> list[CodeIssue]:
        issues: list[CodeIssue] = []
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            return [
                CodeIssue(
                    file=str(path.relative_to(root)),
                    line=1,
                    severity="HIGH",
                    category="security",
                    description=f"Cannot parse {path.name} — possible syntax error",
                )
            ]

        rel = str(path.relative_to(root))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("_") and not node.name.startswith("__"):
                if not self._is_used(tree, node.name) and not self._is_override_method(node.name):
                    issues.append(
                        CodeIssue(
                            file=rel,
                            line=node.lineno,
                            severity="LOW",
                            category="unused_code",
                            description=f"Private function '{node.name}' may be unused",
                        )
                    )
        return issues

    @staticmethod
    def _is_override_method(name: str) -> bool:
        """Filter out Python data-model methods that are called by the runtime, not user code."""
        return name in (
            "__init__",
            "__new__",
            "__del__",
            "__repr__",
            "__str__",
            "__hash__",
            "__eq__",
            "__ne__",
            "__lt__",
            "__le__",
            "__gt__",
            "__ge__",
            "__bool__",
            "__len__",
            "__iter__",
            "__next__",
            "__contains__",
            "__getitem__",
            "__setitem__",
            "__delitem__",
            "__enter__",
            "__exit__",
            "__aenter__",
            "__aexit__",
            "__await__",
            "__aiter__",
            "__anext__",
            "__call__",
            "__getattr__",
            "__setattr__",
            "__delattr__",
        )

    def _is_used(self, tree: ast.AST, name: str) -> bool:
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == name:
                return True
            if isinstance(node, ast.Attribute) and node.attr == name:
                return True
        return False
