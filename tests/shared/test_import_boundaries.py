from __future__ import annotations

import ast
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[2]
PRODUCTION_ROOTS = ("client", "server", "shared")
LEGACY_SURVIVE_TIMED_MODULES = (
    "client.gameplay.modes.survive_timed.contracts",
    "client.gameplay.modes.survive_timed.registry",
    "client.gameplay.modes.survive_timed.profiles",
)


def _iter_python_files(root_name: str) -> tuple[Path, ...]:
    root = PROJECT_ROOT / root_name
    return tuple(sorted(path for path in root.rglob("*.py") if path.is_file()))


def _collect_forbidden_imports(root_name: str, forbidden_roots: tuple[str, ...]) -> list[str]:
    violations: list[str] = []
    for path in _iter_python_files(root_name):
        tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
        relative_path = path.relative_to(PROJECT_ROOT).as_posix()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported_name = alias.name
                    if imported_name.split(".", 1)[0] in forbidden_roots:
                        violations.append(f"{relative_path}:{node.lineno} import {imported_name}")
            elif isinstance(node, ast.ImportFrom):
                imported_name = node.module or ""
                if imported_name.split(".", 1)[0] in forbidden_roots:
                    violations.append(f"{relative_path}:{node.lineno} from {imported_name}")
    return violations


def _collect_legacy_survive_timed_imports() -> list[str]:
    violations: list[str] = []
    for root_name in PRODUCTION_ROOTS:
        for path in _iter_python_files(root_name):
            tree = ast.parse(path.read_text(encoding="utf-8-sig"), filename=str(path))
            relative_path = path.relative_to(PROJECT_ROOT).as_posix()
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        imported_name = alias.name
                        if any(
                            imported_name == legacy_name or imported_name.startswith(f"{legacy_name}.")
                            for legacy_name in LEGACY_SURVIVE_TIMED_MODULES
                        ):
                            violations.append(f"{relative_path}:{node.lineno} import {imported_name}")
                elif isinstance(node, ast.ImportFrom):
                    imported_name = node.module or ""
                    if any(
                        imported_name == legacy_name or imported_name.startswith(f"{legacy_name}.")
                        for legacy_name in LEGACY_SURVIVE_TIMED_MODULES
                    ):
                        violations.append(f"{relative_path}:{node.lineno} from {imported_name}")
    return violations


def test_server_has_no_client_imports() -> None:
    violations = _collect_forbidden_imports("server", ("client",))
    assert not violations, "Forbidden imports found:\n" + "\n".join(violations)


def test_shared_has_no_client_imports() -> None:
    violations = _collect_forbidden_imports("shared", ("client",))
    assert not violations, "Forbidden imports found:\n" + "\n".join(violations)


def test_shared_has_no_server_imports() -> None:
    violations = _collect_forbidden_imports("shared", ("server",))
    assert not violations, "Forbidden imports found:\n" + "\n".join(violations)


def test_production_tree_has_no_legacy_survive_timed_imports() -> None:
    violations = _collect_legacy_survive_timed_imports()
    assert not violations, "Forbidden imports found:\n" + "\n".join(violations)
