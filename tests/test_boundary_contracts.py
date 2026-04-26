import ast
import unittest
from pathlib import Path
from unittest import mock

from tests.contract_test_catalog import DEMO_CONTRACTS_ENABLED
from tests.contract_test_catalog import ACTIVE_DEMO_ENTRYPOINT_GLOB
from tests.contract_test_catalog import ACTIVE_DEMO_ENTRYPOINTS
from tests.contract_test_catalog import PUBLIC_API_EXPORT_ORDER


class BoundaryContractsTests(unittest.TestCase):
    def _require_demo_contracts(self) -> None:
        if not DEMO_CONTRACTS_ENABLED:
            self.skipTest("demo contracts disabled")

    def _parse_python_file(self, py_file: Path) -> ast.AST:
        text = py_file.read_text(encoding="utf-8")
        try:
            return ast.parse(text, filename=str(py_file))
        except SyntaxError as exc:
            location = "unknown"
            if exc.lineno is not None and exc.offset is not None:
                location = f"line {exc.lineno}, column {exc.offset}"
            self.fail(
                f"Failed to parse {py_file} during boundary import inspection: "
                f"{exc.msg} ({location})"
            )

    def _imported_top_levels_from_file(self, py_file: Path) -> set[str]:
        tree = self._parse_python_file(py_file)
        imported: set[str] = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imported.add(alias.name.split(".")[0])
            elif isinstance(node, ast.ImportFrom) and node.module:
                imported.add(node.module.split(".")[0])

        return imported

    def _collect_import_offenders(self, root: Path, start: Path, blocked_packages: list[str]) -> list[str]:
        offenders = []
        for py_file in start.rglob("*.py"):
            imported = self._imported_top_levels_from_file(py_file)
            if any(package in imported for package in blocked_packages):
                offenders.append(str(py_file.relative_to(root)))
        return sorted(offenders)

    def _active_demo_entrypoints(self, root: Path) -> list[Path]:
        return sorted(
            root.glob(ACTIVE_DEMO_ENTRYPOINT_GLOB),
            key=lambda path: path.name,
        )

    def test_gui_package_does_not_depend_on_demo_features(self) -> None:
        root = Path(__file__).resolve().parents[1]
        gui_root = root / "gui_do"
        offenders = self._collect_import_offenders(root, gui_root, ["demo_features"])

        self.assertEqual(offenders, [], f"gui_do package must not import demo_features; found: {offenders}")

    def test_demo_features_do_not_import_gui_do_internals(self) -> None:
        root = Path(__file__).resolve().parents[1]
        demo_features_root = root / "demo_features"
        if not demo_features_root.exists():
            self.assertFalse(DEMO_CONTRACTS_ENABLED)
            return
        offenders = []
        for py_file in demo_features_root.rglob("*.py"):
            tree = self._parse_python_file(py_file)
            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("gui_do."):
                    offenders.append(f"{py_file.name}: {node.module}")

        self.assertEqual(
            sorted(set(offenders)),
            [],
            "demo_features must only import from the gui_do public root, not internal submodules; "
            f"found: {sorted(set(offenders))}",
        )

    def test_parse_failure_reports_explicit_boundary_message(self) -> None:
        with mock.patch("ast.parse", side_effect=SyntaxError("invalid syntax", ("x.py", 7, 3, "x"))):
            with self.assertRaises(AssertionError) as context:
                self._imported_top_levels_from_file(Path(__file__))

        message = str(context.exception)
        self.assertIn("Failed to parse", message)
        self.assertIn("boundary import inspection", message)

    def test_demo_entrypoints_use_public_gui_api_only(self) -> None:
        self._require_demo_contracts()
        root = Path(__file__).resolve().parents[1]
        offenders = []

        for demo_file in self._active_demo_entrypoints(root):
            tree = self._parse_python_file(demo_file)

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("gui_do."):
                    offenders.append(f"{demo_file.name}: {node.module}")

        self.assertEqual(
            sorted(set(offenders)),
            [],
            "demo entrypoints must import gui_do symbols from package root only; "
            f"found internal imports: {sorted(set(offenders))}",
        )

    def test_demo_entrypoints_do_not_import_gui_submodules_via_import_statement(self) -> None:
        self._require_demo_contracts()
        root = Path(__file__).resolve().parents[1]
        offenders = []

        for demo_file in self._active_demo_entrypoints(root):
            tree = self._parse_python_file(demo_file)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith("gui_do."):
                            offenders.append(f"{demo_file.name}: {alias.name}")

        self.assertEqual(
            sorted(set(offenders)),
            [],
            "demo entrypoints must not import gui_do submodules via import statements; "
            f"found submodule imports: {sorted(set(offenders))}",
        )

    def test_demo_entrypoints_import_only_named_public_gui_exports(self) -> None:
        self._require_demo_contracts()
        root = Path(__file__).resolve().parents[1]
        wildcard_offenders = []
        non_public_offenders = []
        canonical_public_exports = set(PUBLIC_API_EXPORT_ORDER)

        for demo_file in self._active_demo_entrypoints(root):
            tree = self._parse_python_file(demo_file)

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == "gui_do":
                    for alias in node.names:
                        if alias.name == "*":
                            wildcard_offenders.append(f"{demo_file.name}: from gui_do import *")
                        elif alias.name not in canonical_public_exports:
                            non_public_offenders.append(f"{demo_file.name}: {alias.name}")

        self.assertEqual(
            sorted(set(wildcard_offenders)),
            [],
            "demo entrypoints must not use wildcard imports from gui_do root; "
            f"found wildcard imports: {sorted(set(wildcard_offenders))}",
        )
        self.assertEqual(
            sorted(set(non_public_offenders)),
            [],
            "demo entrypoints must import only canonical public gui_do exports; "
            f"found non-public imports: {sorted(set(non_public_offenders))}",
        )

    def test_demo_entrypoints_gui_root_import_names_follow_canonical_order(self) -> None:
        self._require_demo_contracts()
        root = Path(__file__).resolve().parents[1]
        ordering_offenders = []
        canonical_index = {name: idx for idx, name in enumerate(PUBLIC_API_EXPORT_ORDER)}

        for demo_file in self._active_demo_entrypoints(root):
            tree = self._parse_python_file(demo_file)

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == "gui_do":
                    imported_names = [alias.name for alias in node.names if alias.name != "*"]
                    imported_indices = [canonical_index[name] for name in imported_names if name in canonical_index]
                    if imported_indices != sorted(imported_indices):
                        ordering_offenders.append(f"{demo_file.name}: {imported_names}")

        self.assertEqual(
            sorted(set(ordering_offenders)),
            [],
            "demo entrypoints should keep gui_do root imports in canonical public export order; "
            f"found ordering violations: {sorted(set(ordering_offenders))}",
        )

    def test_demo_entrypoints_do_not_alias_gui_root_imports(self) -> None:
        self._require_demo_contracts()
        root = Path(__file__).resolve().parents[1]
        alias_offenders = []

        for demo_file in self._active_demo_entrypoints(root):
            tree = self._parse_python_file(demo_file)

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module == "gui_do":
                    for alias in node.names:
                        if alias.asname is not None:
                            alias_offenders.append(f"{demo_file.name}: {alias.name} as {alias.asname}")

        self.assertEqual(
            sorted(set(alias_offenders)),
            [],
            "demo entrypoints should import gui_do root names without aliases; "
            f"found aliased imports: {sorted(set(alias_offenders))}",
        )

    def test_demo_entrypoints_use_single_gui_root_import_block(self) -> None:
        self._require_demo_contracts()
        root = Path(__file__).resolve().parents[1]
        offenders = []

        for demo_file in self._active_demo_entrypoints(root):
            tree = self._parse_python_file(demo_file)
            gui_root_import_count = sum(
                1
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module == "gui_do"
            )
            if gui_root_import_count != 1:
                offenders.append(f"{demo_file.name}: gui_do root import blocks={gui_root_import_count}")

        self.assertEqual(
            sorted(set(offenders)),
            [],
            "active demo entrypoints should use a single from gui_do import (...) block; "
            f"found violations: {sorted(set(offenders))}",
        )

    def test_active_demo_entrypoints_include_current_demo_set(self) -> None:
        self._require_demo_contracts()
        root = Path(__file__).resolve().parents[1]
        entrypoint_names = [path.name for path in self._active_demo_entrypoints(root)]

        self.assertIn("gui_do_demo.py", entrypoint_names)

    def test_active_demo_entrypoints_match_expected_contract_set(self) -> None:
        root = Path(__file__).resolve().parents[1]
        entrypoint_names = tuple(path.name for path in self._active_demo_entrypoints(root))

        self.assertEqual(entrypoint_names, ACTIVE_DEMO_ENTRYPOINTS)


if __name__ == "__main__":
    unittest.main()
