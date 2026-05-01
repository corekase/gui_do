import unittest
import ast
from pathlib import Path


def _python_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.py") if p.is_file())


def _imported_modules(path: Path) -> list[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.append(node.module)
    return modules


class TestBoundaryContracts(unittest.TestCase):
    def test_gui_package_does_not_import_demo_features(self):
        root = Path(__file__).resolve().parents[1]
        gui_root = root / "gui_do"

        violations = []
        for path in _python_files(gui_root):
            for module in _imported_modules(path):
                if module == "demo_features" or module.startswith("demo_features."):
                    violations.append(path.relative_to(root).as_posix())

        self.assertEqual([], violations, msg=f"gui_do imports demo_features in: {violations}")

    def test_demo_entrypoint_uses_gui_root_import(self):
        root = Path(__file__).resolve().parents[1]
        entrypoint = root / "gui_do_demo.py"
        tree = ast.parse(entrypoint.read_text(encoding="utf-8"), filename=str(entrypoint))

        gui_imports = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module is not None and node.module.startswith("gui_do"):
                gui_imports.append(node.module)

        self.assertIn("gui_do", gui_imports)
        self.assertNotIn("gui_do.features", gui_imports)
        self.assertNotIn("gui_do.app", gui_imports)
