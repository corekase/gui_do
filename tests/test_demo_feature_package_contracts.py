import importlib
import unittest
from pathlib import Path


DEMO_FEATURES_ROOT = Path(__file__).resolve().parents[1] / "demo_features"


def _iter_feature_scene_package_names() -> list[str]:
    names: list[str] = []
    for child in sorted(DEMO_FEATURES_ROOT.iterdir()):
        if not child.is_dir():
            continue
        if child.name in {"data", "__pycache__"}:
            continue
        if (child / "__init__.py").exists():
            names.append(child.name)
    return names


def _package_python_file_names(package_name: str) -> set[str]:
    package_dir = DEMO_FEATURES_ROOT / package_name
    return {
        child.name
        for child in package_dir.iterdir()
        if child.is_file() and child.suffix == ".py"
    }


class TestDemoFeaturePackageContracts(unittest.TestCase):
    def test_feature_scene_folders_are_python_packages(self):
        package_names = _iter_feature_scene_package_names()
        self.assertTrue(package_names, msg="No demo feature/scene packages discovered")

        for package_name in package_names:
            init_path = DEMO_FEATURES_ROOT / package_name / "__init__.py"
            self.assertTrue(
                init_path.exists(),
                msg=f"Missing package boundary file for demo_features.{package_name}",
            )

    def test_feature_scene_packages_define_clean_canonical_exports(self):
        package_names = _iter_feature_scene_package_names()

        for package_name in package_names:
            module = importlib.import_module(f"demo_features.{package_name}")

            exports = getattr(module, "__all__", None)
            self.assertIsInstance(
                exports,
                list,
                msg=f"demo_features.{package_name} should expose a list __all__",
            )
            self.assertTrue(exports, msg=f"demo_features.{package_name} has empty __all__")

            for exported_name in exports:
                self.assertFalse(
                    str(exported_name).startswith("_"),
                    msg=f"demo_features.{package_name} exports private symbol {exported_name!r}",
                )
                self.assertTrue(
                    hasattr(module, exported_name),
                    msg=f"demo_features.{package_name} missing exported attribute {exported_name!r}",
                )

            self.assertIn(
                "FEATURE_PACKAGE_INFO",
                exports,
                msg=f"demo_features.{package_name} should export FEATURE_PACKAGE_INFO metadata",
            )

            feature_exports = [name for name in exports if str(name).endswith("Feature")]
            self.assertFalse(
                feature_exports,
                msg=(
                    f"demo_features.{package_name} should not re-export *Feature symbols "
                    "from package __init__.py; import concrete modules directly"
                ),
            )

            file_names = _package_python_file_names(package_name)
            feature_modules = [name for name in file_names if name.endswith("_feature.py")]
            self.assertTrue(
                feature_modules,
                msg=f"demo_features.{package_name} should define feature classes in *_feature.py modules",
            )

    def test_feature_scene_packages_require_kind_files_by_default(self):
        """Kind-file layout is a required default for all demo feature/scene packages."""
        package_names = _iter_feature_scene_package_names()

        for package_name in package_names:
            file_names = _package_python_file_names(package_name)

            self.assertIn(
                "__init__.py",
                file_names,
                msg=f"demo_features.{package_name} must include __init__.py",
            )

            has_feature_file = any(name.endswith("_feature.py") for name in file_names)
            self.assertTrue(
                has_feature_file,
                msg=f"demo_features.{package_name} must include at least one *_feature.py module",
            )

            has_specs_file = any(name.endswith("_specs.py") for name in file_names)
            self.assertTrue(
                has_specs_file,
                msg=f"demo_features.{package_name} must include at least one *_specs.py module",
            )

    def test_feature_package_info_is_optional_and_non_runtime(self):
        """If present, FEATURE_PACKAGE_INFO is treated as metadata only."""
        package_names = _iter_feature_scene_package_names()

        for package_name in package_names:
            module = importlib.import_module(f"demo_features.{package_name}")
            info = getattr(module, "FEATURE_PACKAGE_INFO", None)
            if info is None:
                continue
            self.assertIsInstance(
                info,
                dict,
                msg=f"demo_features.{package_name} FEATURE_PACKAGE_INFO must be a dict when present",
            )
            feature_name = info.get("feature_name")
            if feature_name is not None:
                self.assertEqual(
                    package_name,
                    str(feature_name),
                    msg=f"demo_features.{package_name} FEATURE_PACKAGE_INFO.feature_name should match package name",
                )
