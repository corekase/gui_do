import ast
import unittest
from pathlib import Path
from unittest import mock


class BoundaryContractsTests(unittest.TestCase):
    def _imported_top_levels_from_file(self, py_file: Path) -> set[str]:
        text = py_file.read_text(encoding="utf-8")
        try:
            tree = ast.parse(text, filename=str(py_file))
        except SyntaxError as exc:
            location = "unknown"
            if exc.lineno is not None and exc.offset is not None:
                location = f"line {exc.lineno}, column {exc.offset}"
            self.fail(
                f"Failed to parse {py_file} during boundary import inspection: "
                f"{exc.msg} ({location})"
            )
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

    def test_demo_entrypoint_uses_public_gui_api_only(self) -> None:
        root = Path(__file__).resolve().parents[1]
        demo_file = root / "gui_do_demo.py"
        text = demo_file.read_text(encoding="utf-8")
        tree = ast.parse(text, filename=str(demo_file))
        offenders = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module and node.module.startswith("gui."):
                offenders.append(node.module)

        self.assertEqual(
            sorted(set(offenders)),
            [],
            f"demo entrypoint must import gui symbols from package root only; found internal imports: {sorted(set(offenders))}",
        )


if __name__ == "__main__":
    unittest.main()
