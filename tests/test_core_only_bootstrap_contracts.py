import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
