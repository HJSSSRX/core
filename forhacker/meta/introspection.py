import ast
from dataclasses import dataclass
from pathlib import Path


@dataclass
class CodeIssue:
    file: str
    line: int
    severity: str  # LOW | MEDIUM | HIGH
    category: str  # unused_code | missing_test | complexity | security
    description: str


class IntrospectionAgent:
    """Scans the codebase for code quality issues and improvement opportunities."""

    def scan(self, root: Path) -> list[CodeIssue]:
        issues: list[CodeIssue] = []
        for py_file in root.rglob("*.py"):
            if "__pycache__" in str(py_file):
                continue
            issues.extend(self._analyze_file(py_file, root))
        return issues

    def _analyze_file(self, path: Path, root: Path) -> list[CodeIssue]:
        issues: list[CodeIssue] = []
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (SyntaxError, UnicodeDecodeError):
            return [CodeIssue(
                file=str(path.relative_to(root)), line=1, severity="HIGH",
                category="security", description=f"Cannot parse {path.name} — possible syntax error",
            )]

        rel = str(path.relative_to(root))
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name.startswith("_"):
                used = self._is_used(tree, node.name)
                if not used:
                    issues.append(CodeIssue(
                        file=rel, line=node.lineno, severity="LOW",
                        category="unused_code",
                        description=f"Private function '{node.name}' may be unused",
                    ))
        return issues

    def _is_used(self, tree: ast.AST, name: str) -> bool:
        for node in ast.walk(tree):
            if isinstance(node, ast.Name) and node.id == name:
                return True
            if isinstance(node, ast.Attribute) and node.attr == name:
                return True
        return False
