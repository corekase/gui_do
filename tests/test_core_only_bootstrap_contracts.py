import unittest
from pathlib import Path
import re


class CoreOnlyBootstrapContractsTests(unittest.TestCase):
    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def test_single_user_facing_script_exists(self) -> None:
        root = self._repo_root()
        required = ("scripts/manage.py",)

        for relative_path in required:
            self.assertTrue((root / relative_path).exists(), f"missing required script: {relative_path}")

    def test_contract_catalog_core_only_mode_is_well_formed(self) -> None:
        root = self._repo_root()
        catalog_path = root / "tests" / "contract_test_catalog.py"
        source = catalog_path.read_text(encoding="utf-8-sig")
        self.assertIn("DEMO_CONTRACTS_ENABLED = True", source)

        core_only_source = source.replace("DEMO_CONTRACTS_ENABLED = True", "DEMO_CONTRACTS_ENABLED = False", 1)
        namespace: dict[str, object] = {}
        exec(compile(core_only_source, str(catalog_path), "exec"), namespace)

        modules = namespace["CONTRACT_TEST_MODULES"]
        core_modules = namespace["CORE_CONTRACT_TEST_MODULES"]

        self.assertEqual(modules, core_modules)
        self.assertNotIn("tests.test_mandel_event_schema_exports", modules)
        self.assertEqual(namespace["ACTIVE_DEMO_ENTRYPOINTS"], ())
        self.assertEqual(namespace["BOUNDARY_ASSET_PATHS"], ())
        self.assertEqual(namespace["DEMO_FEATURES_EXPORT_ORDER"], ())
        self.assertEqual(namespace["PACKAGE_PUBLIC_API_REQUIRED_DEMO_IMPORTS"], ())

    def test_bootstrap_script_declares_required_sync_targets(self) -> None:
        root = self._repo_root()
        bootstrap = (root / "scripts" / "manage.py").read_text(encoding="utf-8")

        required_markers = (
            "DEMO_CONTRACTS_ENABLED",
            "package_contracts.md",
            "architecture_boundary_spec.md",
            "public_api_spec.md",
            ".github/workflows/unittest.yml",
            "## Run Boundary Contract Tests",
            "## Current Demo Boundary Assets",
            "## Current Active Demo Entrypoints",
            "## Enforcement",
            "init",
            "apply",
            "verify",
            "check",
            "update",
            "--target",
            "--skip-doc-sync",
            "--skip-workflow-sync",
            "--scaffold",
            "--verify",
        )

        for marker in required_markers:
            self.assertIn(marker, bootstrap, f"bootstrap script missing required sync marker: {marker}")

    def test_manage_script_is_declared_in_manifest(self) -> None:
        root = self._repo_root()
        manifest = (root / "MANIFEST.in").read_text(encoding="utf-8")
        self.assertIn("scripts/manage.py", manifest, "MANIFEST.in must declare scripts/manage.py so it ships in source distributions")

    def test_init_removes_demo_tests_by_content_scan_not_hardcoded_list(self) -> None:
        """The init command must discover demo tests dynamically, not from a hardcoded filename list.

        As demo_features/ and demo tests grow over time, manage.py must not require manual
        updates to pick up new files. The canonical discovery rule is: any test file in tests/
        that imports from demo_features is a demo test and must be removed by init.
        """
        root = self._repo_root()
        bootstrap = (root / "scripts" / "manage.py").read_text(encoding="utf-8")

        # The script must not contain the old hardcoded tuple constant.
        self.assertNotIn(
            "DEMO_TEST_FILES = (\n",
            bootstrap,
            "manage.py must not use a hardcoded DEMO_TEST_FILES tuple — use dynamic discovery instead",
        )

        # The script must declare the discovery rule constant so it is auditable.
        self.assertIn(
            "DEMO_TEST_DISCOVERY_RULE",
            bootstrap,
            "manage.py must declare DEMO_TEST_DISCOVERY_RULE to document how demo tests are found",
        )

        # The discovery mechanism must scan file content for demo_features imports.
        self.assertIn(
                "demo_features",
            bootstrap,
            "manage.py must scan for 'demo_features' to identify demo test files dynamically",
        )

        # Verify the catalog also carries the discovery rule so it is a first-class contract.
        catalog_path = root / "tests" / "contract_test_catalog.py"
        catalog_text = catalog_path.read_text(encoding="utf-8")
        self.assertIn(
            "DEMO_TEST_DISCOVERY_RULE",
            catalog_text,
            "contract_test_catalog.py must declare DEMO_TEST_DISCOVERY_RULE as a first-class package contract",
        )

    def test_init_demo_test_discovery_finds_all_current_demo_tests(self) -> None:
        """The dynamic discovery function must find all test files that import from demo_features."""
        root = self._repo_root()
        tests_dir = root / "tests"
        discovered = []
        for test_file in sorted(tests_dir.glob("test_*.py")):
            try:
                text = test_file.read_text(encoding="utf-8", errors="ignore")
            except OSError:
                continue
            if re.search(r"^(?:from|import) demo_features\b", text, re.MULTILINE):
                discovered.append(test_file.name)

        # Every discovered file must actually be a demo test (sanity check: core tests must not appear).
        core_test_names = {
            "test_boundary_contracts.py",
            "test_public_api_exports.py",
            "test_public_api_docs_contracts.py",
            "test_architecture_boundary_docs_contracts.py",
            "test_contract_command_parity.py",
            "test_core_only_bootstrap_contracts.py",
            "test_contract_catalog_consistency.py",
            "test_contract_docs_helpers.py",
        }
        for name in discovered:
            self.assertNotIn(
                name,
                core_test_names,
                f"Core contract test '{name}' must not import from demo_features",
            )

        # Discovery must find at least the known set of demo tests.
        known_demo_tests = {
            "test_bouncing_shapes_demo_feature.py",
            "test_controls_demo_feature.py",
            "test_demo_features_gui_portability.py",
            "test_feature_lifecycle_host_parameter_contracts.py",
            "test_gui_do_demo_life_runtime.py",
            "test_gui_do_demo_presentation_model.py",
            "test_mandel_event_schema_exports.py",
            "test_mandel_logic_feature_runtime.py",
            "test_styles_demo_feature.py",
        }
        discovered_set = set(discovered)
        for name in known_demo_tests:
            self.assertIn(
                name,
                discovered_set,
                f"Dynamic demo-test discovery must find '{name}' (it imports from demo_features)",
            )


if __name__ == "__main__":
    unittest.main()
