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
        self.assertIsNotNone(
            re.search(r"^DEMO_CONTRACTS_ENABLED\s*=\s*(True|False)\s*$", source, re.MULTILINE)
        )

        core_only_source = re.sub(
            r"^DEMO_CONTRACTS_ENABLED\s*=\s*(True|False)\s*$",
            "DEMO_CONTRACTS_ENABLED = False",
            source,
            count=1,
            flags=re.MULTILINE,
        )
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

    def test_manage_script_describes_developer_bootstrap_purpose(self) -> None:
        """manage.py must document that its primary purpose is stripping demo for application developers."""
        root = self._repo_root()
        bootstrap = (root / "scripts" / "manage.py").read_text(encoding="utf-8")

        # Docstring must describe init as the demo-stripping command
        self.assertIn("strip", bootstrap,
                     "manage.py docstring must describe init as stripping demo content")
        self.assertIn("demo content", bootstrap,
                     "manage.py docstring must mention demo content removal")
        # init description must mention removal of content outside gui_do/
        self.assertIn("outside gui_do/", bootstrap,
                 "manage.py docstring must describe removal of consumer/demo content outside gui_do/")
        self.assertIn("*_demo.py", bootstrap,
                     "manage.py docstring must name *_demo.py as a removed artifact")

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

    def test_init_treats_entire_demo_features_tree_as_demo_owned(self) -> None:
        root = self._repo_root()
        bootstrap = (root / "scripts" / "manage.py").read_text(encoding="utf-8")

        self.assertIn(
            "DEMO_ROOT_DIR = \"demo_features\"",
            bootstrap,
            "manage.py must declare demo_features as the demo root directory contract",
        )
        self.assertIn(
            "_delete_path(root / DEMO_ROOT_DIR, apply)",
            bootstrap,
            "manage.py init/apply must remove demo_features as one tree, not per-file paths",
        )
        self.assertNotIn(
            "demo_features/data",
            bootstrap,
            "manage.py must not hardcode nested consumer/demo asset paths; whole-tree removal is the general rule",
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

        discovered_set = set(discovered)
        expected_demo_tests = {
            "test_bouncing_shapes_demo_feature.py",
            "test_controls_demo_feature.py",
            "test_demo_features_gui_portability.py",
            "test_feature_lifecycle_host_parameter_contracts.py",
            "test_gui_do_demo_life_runtime.py",
            "test_gui_do_demo_presentation_model.py",
            "test_mandel_event_schema_exports.py",
            "test_mandel_logic_feature_runtime.py",
        }

        existing_expected = {name for name in expected_demo_tests if (tests_dir / name).exists()}

        if existing_expected:
            for name in existing_expected:
                self.assertIn(
                    name,
                    discovered_set,
                    f"Dynamic demo-test discovery must find '{name}' when it exists",
                )
        else:
            self.assertEqual(
                discovered_set,
                set(),
                "Core-only initialized projects should not retain demo test files",
            )

    def test_init_removes_demo_entrypoints_by_glob_not_hardcoded_name(self) -> None:
        """The init command must discover demo entrypoints by glob pattern, not hardcoded filename.

        As new *_demo.py files are added to the repo root, they must be automatically
        picked up and removed during init without any code change.
        """
        root = self._repo_root()
        bootstrap = (root / "scripts" / "manage.py").read_text(encoding="utf-8")

        # Must not hardcode a specific demo entrypoint filename
        self.assertNotIn(
            'DEMO_ENTRYPOINT_FILE = "gui_do_demo.py"',
            bootstrap,
            "manage.py must not hardcode a single demo entrypoint filename — use dynamic discovery",
        )

        # Must declare the discovery rule constant
        self.assertIn(
            "DEMO_ENTRYPOINT_DISCOVERY_RULE",
            bootstrap,
            "manage.py must declare DEMO_ENTRYPOINT_DISCOVERY_RULE to document the glob pattern",
        )

        # Must use the discovery function, not a hardcoded path
        self.assertIn(
            "_find_demo_entrypoints(root)",
            bootstrap,
            "manage.py init/apply must use _find_demo_entrypoints() for dynamic entrypoint removal",
        )

        # Must use *_demo.py glob pattern
        self.assertIn(
            '"*_demo.py"',
            bootstrap,
            "manage.py must use *_demo.py glob pattern to discover demo entrypoints",
        )

    def test_init_entrypoint_discovery_finds_all_current_demo_entrypoints(self) -> None:
        """The dynamic discovery function must find all current *_demo.py files."""
        root = self._repo_root()
        discovered = [p.name for p in sorted(root.glob("*_demo.py")) if p.is_file()]

        existing_expected = [
            name for name in ["gui_do_demo.py"]
            if (root / name).exists()
        ]

        if existing_expected:
            for name in existing_expected:
                self.assertIn(
                    name,
                    discovered,
                    f"Dynamic entrypoint discovery must find '{name}' when it exists",
                )
        else:
            self.assertEqual(
                discovered,
                [],
                "Core-only initialized projects should not retain *_demo.py files",
            )

    def test_upgrade_sync_dirs_contain_only_library_content(self) -> None:
        """SYNC_DIRS must include all library dirs and must never include demo dirs.

        The update command copies SYNC_DIRS from a new source into a developer
        project. Including demo_features/ would silently overwrite the project
        with demo content on every upgrade.
        """
        root = self._repo_root()
        manage_path = root / "scripts" / "manage.py"

        # Load SYNC_DIRS from manage.py without importing it
        namespace: dict = {}
        exec(compile(manage_path.read_text(encoding="utf-8"), str(manage_path), "exec"), namespace)
        sync_dirs = namespace["SYNC_DIRS"]
        sync_files = namespace["SYNC_FILES"]

        # Required library dirs must all be present
        for required in ("gui_do", "scripts", "tests", "docs"):
            self.assertIn(required, sync_dirs,
                         f"SYNC_DIRS must include '{required}' (library content)")

        # Demo dir must never be in SYNC_DIRS
        self.assertNotIn("demo_features", sync_dirs,
                        "SYNC_DIRS must not include demo_features/ — upgrade must not pollute developer projects with demo content")

        # Demo entrypoints must not be in SYNC_FILES
        for item in sync_files:
            self.assertFalse(
                item.endswith("_demo.py"),
                f"SYNC_FILES must not include demo entrypoints; found: {item}",
            )

        # No demo data paths in SYNC_FILES
        for item in sync_files:
            self.assertNotIn("demo_features", item,
                            f"SYNC_FILES must not reference demo_features; found: {item}")

    def test_upgrade_path_documented_in_manage_script(self) -> None:
        """manage.py docstring must explicitly document the upgrade workflow."""
        root = self._repo_root()
        bootstrap = (root / "scripts" / "manage.py").read_text(encoding="utf-8")

        # Must document what update copies
        self.assertIn("gui_do/", bootstrap,
                     "manage.py docstring must name gui_do/ as an upgrade-synced dir")
        self.assertIn("scripts/", bootstrap,
                     "manage.py docstring must name scripts/ as an upgrade-synced dir")
        self.assertIn("tests/", bootstrap,
                     "manage.py docstring must name tests/ as an upgrade-synced dir")
        self.assertIn("docs/", bootstrap,
                     "manage.py docstring must name docs/ as an upgrade-synced dir")

        # Must name the upgrade source scenarios
        self.assertTrue(
            "git" in bootstrap or "zip" in bootstrap,
            "manage.py docstring must mention git clone or zip download as upgrade sources",
        )

        # Must document the --target flag
        self.assertIn("--target", bootstrap,
                     "manage.py must document --target flag for update/check commands")

        # update command must call apply on target (not copy demo then strip)
        self.assertIn("apply", bootstrap,
                     "manage.py must run apply on target after copying library dirs")


if __name__ == "__main__":
    unittest.main()
