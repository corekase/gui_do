import unittest
from pathlib import Path


class CoreOnlyBootstrapContractsTests(unittest.TestCase):
    def _repo_root(self) -> Path:
        return Path(__file__).resolve().parents[1]

    def test_bootstrap_and_upgrade_wrappers_exist(self) -> None:
        root = self._repo_root()
        required = (
            "scripts/bootstrap_new_project.py",
            "scripts/bootstrap_new_project.bat",
            "scripts/bootstrap_new_project.sh",
            "scripts/upgrade_existing_project.bat",
            "scripts/upgrade_existing_project.sh",
        )

        for relative_path in required:
            self.assertTrue((root / relative_path).exists(), f"missing required script: {relative_path}")

    def test_wrapper_scripts_call_bootstrap_entrypoint(self) -> None:
        root = self._repo_root()

        win_bootstrap = (root / "scripts" / "bootstrap_new_project.bat").read_text(encoding="utf-8")
        win_upgrade = (root / "scripts" / "upgrade_existing_project.bat").read_text(encoding="utf-8")
        sh_bootstrap = (root / "scripts" / "bootstrap_new_project.sh").read_text(encoding="utf-8")
        sh_upgrade = (root / "scripts" / "upgrade_existing_project.sh").read_text(encoding="utf-8")

        self.assertIn("bootstrap_new_project.py", win_bootstrap)
        self.assertIn(" new ", win_bootstrap)
        self.assertIn("--scaffold", win_bootstrap)
        self.assertIn("--verify", win_bootstrap)
        self.assertIn("bootstrap_new_project.py", win_upgrade)
        self.assertIn(" upgrade ", win_upgrade)
        self.assertIn("--verify", win_upgrade)
        self.assertIn("bootstrap_new_project.py", sh_bootstrap)
        self.assertIn(" new ", sh_bootstrap)
        self.assertIn("--scaffold", sh_bootstrap)
        self.assertIn("--verify", sh_bootstrap)
        self.assertIn("bootstrap_new_project.py", sh_upgrade)
        self.assertIn(" upgrade ", sh_upgrade)
        self.assertIn("--verify", sh_upgrade)

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
        self.assertEqual(namespace["README_PUBLIC_API_REQUIRED_DEMO_IMPORTS"], ())

    def test_bootstrap_script_declares_required_sync_targets(self) -> None:
        root = self._repo_root()
        bootstrap = (root / "scripts" / "bootstrap_new_project.py").read_text(encoding="utf-8")

        required_markers = (
            "DEMO_CONTRACTS_ENABLED",
            "README.md",
            "architecture_boundary_spec.md",
            "public_api_spec.md",
            ".github/workflows/unittest.yml",
            "## Run Boundary Contract Tests",
            "## Current Demo Boundary Assets",
            "## Current Active Demo Entrypoints",
            "## Enforcement",
            "new",
            "upgrade",
            "check",
            "verify",
            "--skip-doc-sync",
            "--skip-workflow-sync",
            "--scaffold",
            "--verify",
        )

        for marker in required_markers:
            self.assertIn(marker, bootstrap, f"bootstrap script missing required sync marker: {marker}")


if __name__ == "__main__":
    unittest.main()
