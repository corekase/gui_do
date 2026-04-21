import ast
import unittest
from pathlib import Path
from unittest import mock

from contract_test_catalog import ACTIVE_DEMO_ENTRYPOINT_GLOB
from contract_test_catalog import PRE_REBASE_DEMO_PREFIX


class BoundaryContractsTests(unittest.TestCase):
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
            (
                path
                for path in root.glob(ACTIVE_DEMO_ENTRYPOINT_GLOB)
                if not path.name.startswith(PRE_REBASE_DEMO_PREFIX)
            ),
            key=lambda path: path.name,
        )

    def test_gui_package_does_not_depend_on_demo_parts(self) -> None:
        root = Path(__file__).resolve().parents[1]
        gui_root = root / "gui"
        offenders = self._collect_import_offenders(root, gui_root, ["demo_parts"])

        self.assertEqual(offenders, [], f"gui package must not import demo_parts; found: {offenders}")

    def test_demo_parts_does_not_depend_on_gui(self) -> None:
        root = Path(__file__).resolve().parents[1]
        demo_parts_root = root / "demo_parts"
        offenders = self._collect_import_offenders(root, demo_parts_root, ["gui"])

        self.assertEqual(offenders, [], f"demo_parts must remain gui-independent; found: {offenders}")

    def test_parse_failure_reports_explicit_boundary_message(self) -> None:
        with mock.patch("ast.parse", side_effect=SyntaxError("invalid syntax", ("x.py", 7, 3, "x"))):
            with self.assertRaises(AssertionError) as context:
                self._imported_top_levels_from_file(Path(__file__))

        message = str(context.exception)
        self.assertIn("Failed to parse", message)
        self.assertIn("boundary import inspection", message)

    def test_demo_entrypoints_use_public_gui_api_only(self) -> None:
        root = Path(__file__).resolve().parents[1]
        offenders = []

        for demo_file in self._active_demo_entrypoints(root):
            tree = self._parse_python_file(demo_file)

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("gui."):
                    offenders.append(f"{demo_file.name}: {node.module}")

        self.assertEqual(
            sorted(set(offenders)),
            [],
            "demo entrypoints must import gui symbols from package root only; "
            f"found internal imports: {sorted(set(offenders))}",
        )

    def test_demo_entrypoints_do_not_import_gui_submodules_via_import_statement(self) -> None:
        root = Path(__file__).resolve().parents[1]
        offenders = []

        for demo_file in self._active_demo_entrypoints(root):
            tree = self._parse_python_file(demo_file)

            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.name.startswith("gui."):
                            offenders.append(f"{demo_file.name}: {alias.name}")

        self.assertEqual(
            sorted(set(offenders)),
            [],
            "demo entrypoints must not import gui submodules via import statements; "
            f"found submodule imports: {sorted(set(offenders))}",
        )

    def test_active_demo_entrypoints_exclude_pre_rebase_archives(self) -> None:
        root = Path(__file__).resolve().parents[1]
        entrypoint_names = [path.name for path in self._active_demo_entrypoints(root)]

        self.assertIn("gui_do_demo.py", entrypoint_names)
        self.assertFalse(any(name.startswith(PRE_REBASE_DEMO_PREFIX) for name in entrypoint_names))


if __name__ == "__main__":
    unittest.main()
