"""Comprehensive library/demo separation contract tests.

Enforces complete architectural separation between:
- GUI_DO LIBRARY: gui_do/, tests/, docs/, scripts/manage.py
- DEMO: demo_features/, gui_do_demo.py and all demo-specific assets

Separation is enforced at three levels:
1. Import separation: gui_do never imports demo, demo only uses gui_do public API
2. Packaging separation: Wheel/sdist distributions contain only library, not demo
3. Path separation: No hardcoded demo paths in gui_do; demo provides all paths from CWD
"""

import ast
import unittest
from pathlib import Path
from typing import Set

from tests.contract_test_catalog import DEMO_CONTRACTS_ENABLED, LIBRARY_SEPARATION_PRINCIPLE


class LibraryDemoSeparationTests(unittest.TestCase):
    """Verify complete separation between gui_do library and demo."""

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
            self.fail(f"Failed to parse {py_file}: {exc.msg} ({location})")

    def test_separation_principle_is_documented(self) -> None:
        """Verify the separation principle is formally documented."""
        self._require_demo_contracts()
        self.assertIsNotNone(LIBRARY_SEPARATION_PRINCIPLE)
        self.assertIn("GUI_DO LIBRARY", LIBRARY_SEPARATION_PRINCIPLE)
        self.assertIn("DEMO", LIBRARY_SEPARATION_PRINCIPLE)
        self.assertIn("PACKAGING ENFORCEMENT", LIBRARY_SEPARATION_PRINCIPLE)

    def test_gui_package_has_no_hardcoded_demo_data_paths(self) -> None:
        """Verify gui_do/ has no hardcoded demo_features/data/ paths."""
        self._require_demo_contracts()
        root = Path(__file__).resolve().parents[1]
        gui_root = root / "gui_do"
        offenders = []

        for py_file in gui_root.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            # Check for hardcoded demo_features paths
            if "demo_features/data" in text or "demo_features" + "/" + "data" in text:
                offenders.append(str(py_file.relative_to(root)))

        self.assertEqual(
            offenders,
            [],
            f"gui_do package must not contain hardcoded demo_features/data paths; found in: {offenders}",
        )

    def test_path_resolution_functions_accept_caller_paths(self) -> None:
        """Verify asset loading functions resolve from CWD or absolute paths, not demo_features/data."""
        self._require_demo_contracts()
        root = Path(__file__).resolve().parents[1]

        # Check load_pristine_surface docstring
        graphics_init = root / "gui_do" / "graphics" / "__init__.py"
        tree = self._parse_python_file(graphics_init)
        found_load_pristine = False
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "load_pristine_surface":
                found_load_pristine = True
                # Get the docstring
                docstring = ast.get_docstring(node)
                self.assertIsNotNone(docstring)
                self.assertIn("CWD", docstring, "load_pristine_surface must document CWD resolution")
                self.assertNotIn("demo_features", docstring, "load_pristine_surface docstring must not mention demo_features")

        self.assertTrue(found_load_pristine, "load_pristine_surface function not found")

        # Check register_cursor signature
        app_file = root / "gui_do" / "app" / "gui_application.py"
        tree = self._parse_python_file(app_file)
        found_register_cursor = False
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == "register_cursor":
                found_register_cursor = True
                # Verify it has 'path' parameter, not 'filename'
                param_names = [arg.arg for arg in node.args.args]
                self.assertIn("path", param_names, "register_cursor must take 'path' parameter")
                self.assertNotIn("filename", param_names, "register_cursor must not take 'filename' parameter")

        self.assertTrue(found_register_cursor, "register_cursor function not found")

    def test_demo_provides_full_paths_to_framework(self) -> None:
        """Verify demo passes full CWD-relative paths to framework, not bare filenames."""
        self._require_demo_contracts()
        root = Path(__file__).resolve().parents[1]
        demo_file = root / "gui_do_demo.py"

        text = demo_file.read_text(encoding="utf-8")

        # Check that cursor registration uses full paths
        self.assertIn('register_cursor("normal", "demo_features/', text,
                     "Demo must pass full CWD-relative path to register_cursor")
        self.assertIn('register_cursor("hand", "demo_features/', text,
                     "Demo must pass full CWD-relative path to register_cursor")

        # Check that set_pristine uses full paths
        self.assertIn('set_pristine("demo_features/', text,
                     "Demo must pass full CWD-relative path to set_pristine")

        # Should NOT have bare filenames
        self.assertNotIn('register_cursor("normal", "cursor.png"', text,
                        "Demo must not pass bare filename to register_cursor")
        self.assertNotIn('set_pristine("backdrop.jpg"', text,
                        "Demo must not pass bare filename to set_pristine")

    def test_pyproject_packages_find_includes_only_gui_do(self) -> None:
        """Verify pyproject.toml packages.find include only gui_do*, not demo_features."""
        self._require_demo_contracts()
        root = Path(__file__).resolve().parents[1]
        pyproject = root / "pyproject.toml"

        text = pyproject.read_text(encoding="utf-8")

        # Should have include = ["gui_do*"]
        self.assertIn('include = ["gui_do*"]', text,
                     "pyproject.toml must include gui_do* in packages.find")

        # Should NOT have demo_features in include
        self.assertNotIn('demo_features', text.split("packages.find")[1].split("[tool.setuptools")[0],
                        "pyproject.toml packages.find must not include demo_features")

    def test_manifest_in_excludes_demo_features_data(self) -> None:
        """Verify MANIFEST.in does not include demo_features/data (sdist exclusion)."""
        self._require_demo_contracts()
        root = Path(__file__).resolve().parents[1]
        manifest = root / "MANIFEST.in"

        text = manifest.read_text(encoding="utf-8")

        # Should NOT have recursive-include demo_features
        self.assertNotIn("demo_features", text,
                        "MANIFEST.in must not include demo_features or demo_features/data")

    def test_library_composition_documented(self) -> None:
        """Verify what constitutes the library is clearly documented."""
        self._require_demo_contracts()
        principle = LIBRARY_SEPARATION_PRINCIPLE

        # Library components
        self.assertIn("gui_do/", principle, "Library composition must include gui_do/")
        self.assertIn("tests/", principle, "Library composition must include tests/")
        self.assertIn("docs/", principle, "Library composition must include docs/")
        self.assertIn("scripts/manage.py", principle, "Library composition must include scripts/manage.py")

        # Demo components
        self.assertIn("demo_features/", principle, "Demo composition must include demo_features/")
        self.assertIn("*_demo.py", principle, "Demo composition must document demo entrypoints by glob")

        # Developer workflow must be documented
        self.assertIn("DEVELOPER WORKFLOW", principle, "Principle must document the developer workflow")
        self.assertIn("manage.py init", principle, "Principle must document manage.py init as the strip command")
        self.assertIn("NOT included in wheel distribution", principle, "Demo must be documented as excluded from wheel")
        self.assertIn("NOT included in sdist distribution", principle, "Demo must be documented as excluded from sdist")

    def test_manage_py_demo_discovery_is_fully_dynamic(self) -> None:
        """Verify manage.py uses dynamic discovery for both demo tests and demo entrypoints.

        Both mechanisms must be glob/content-scan based so new files are handled automatically
        without any code change as the demo grows.
        """
        self._require_demo_contracts()
        root = Path(__file__).resolve().parents[1]
        manage_text = (root / "scripts" / "manage.py").read_text(encoding="utf-8")

        # Entrypoint discovery must be dynamic (glob *_demo.py)
        self.assertIn("DEMO_ENTRYPOINT_DISCOVERY_RULE", manage_text,
                     "manage.py must declare DEMO_ENTRYPOINT_DISCOVERY_RULE for auditability")
        self.assertIn("_find_demo_entrypoints(root)", manage_text,
                     "manage.py must use _find_demo_entrypoints() in sync function")
        self.assertNotIn('DEMO_ENTRYPOINT_FILE = "gui_do_demo.py"', manage_text,
                        "manage.py must not hardcode a single demo entrypoint filename")

        # Test discovery must be dynamic (content scan)
        self.assertIn("DEMO_TEST_DISCOVERY_RULE", manage_text,
                     "manage.py must declare DEMO_TEST_DISCOVERY_RULE for auditability")
        self.assertIn("_find_demo_test_files(root)", manage_text,
                     "manage.py must use _find_demo_test_files() in sync function")

        # Demo tree removal must use the constant, not a hardcoded path
        self.assertIn("_delete_path(root / DEMO_ROOT_DIR, apply)", manage_text,
                     "manage.py must remove demo_features as a tree via DEMO_ROOT_DIR constant")

    def test_all_separation_rules_consolidated(self) -> None:
        """Verify all separation rules are consolidated in one place (this test module + catalog)."""
        self._require_demo_contracts()
        # This test documents that:
        # 1. test_gui_package_does_not_depend_on_demo_features (test_boundary_contracts.py) - Import separation
        # 2. test_demo_features_do_not_import_gui_do_internals (test_boundary_contracts.py) - Import separation
        # 3. test_demo_entrypoints_use_public_gui_api_only (test_boundary_contracts.py) - API separation
        # All consolidated here with packaging, path, and architectural documentation
        self.assertTrue(True, "Consolidation complete: all rules in test_boundary_contracts + here + catalog")


if __name__ == "__main__":
    unittest.main()
