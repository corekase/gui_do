import unittest
import importlib
import sys

import demo_features.mandelbrot_demo_feature as mandel_module
from demo_features.mandelbrot_demo_feature import MANDEL_KIND_COMPLETE
from demo_features.mandelbrot_demo_feature import MANDEL_KIND_CLEARED
from demo_features.mandelbrot_demo_feature import MANDEL_KIND_FAILED
from demo_features.mandelbrot_demo_feature import MANDEL_KIND_IDLE
from demo_features.mandelbrot_demo_feature import MANDEL_KIND_RUNNING_FOUR_SPLIT
from demo_features.mandelbrot_demo_feature import MANDEL_KIND_RUNNING_ITERATIVE
from demo_features.mandelbrot_demo_feature import MANDEL_KIND_RUNNING_ONE_SPLIT
from demo_features.mandelbrot_demo_feature import MANDEL_KIND_RUNNING_RECURSIVE
from demo_features.mandelbrot_demo_feature import MANDEL_KIND_STATUS
from demo_features.mandelbrot_demo_feature import MANDEL_STATUS_SCOPE
from demo_features.mandelbrot_demo_feature import MANDEL_STATUS_TOPIC
from demo_features.mandelbrot_demo_feature import MandelStatusEvent
from demo_features.mandelbrot_demo_feature import __all__ as mandel_module_all
from demo_features.mandelbrot_demo_feature import MandelStatusEvent as ModuleMandelStatusEvent
from tests.contract_test_catalog import DEMO_FEATURES_EXPORT_ORDER


class MandelEventSchemaExportTests(unittest.TestCase):
    def test_schema_exports_are_available(self) -> None:
        self.assertEqual(MANDEL_STATUS_TOPIC, "demo.mandel.status")
        self.assertEqual(MANDEL_STATUS_SCOPE, "main")
        self.assertEqual(MANDEL_KIND_IDLE, "idle")
        self.assertEqual(MANDEL_KIND_CLEARED, "cleared")
        self.assertEqual(MANDEL_KIND_RUNNING_ITERATIVE, "running_iterative")
        self.assertEqual(MANDEL_KIND_RUNNING_RECURSIVE, "running_recursive")
        self.assertEqual(MANDEL_KIND_RUNNING_ONE_SPLIT, "running_one_split")
        self.assertEqual(MANDEL_KIND_RUNNING_FOUR_SPLIT, "running_four_split")
        self.assertEqual(MANDEL_KIND_STATUS, "status")
        self.assertEqual(MANDEL_KIND_FAILED, "failed")
        self.assertEqual(MANDEL_KIND_COMPLETE, "complete")

    def test_exported_dataclass_payload_conversion(self) -> None:
        event = MandelStatusEvent(kind=MANDEL_KIND_STATUS, detail="ok")

        payload = event.to_payload()
        restored = MandelStatusEvent.from_payload(payload)

        self.assertEqual(restored, event)

    def test_demo_features_schema_module_importable(self) -> None:
        module = importlib.import_module("demo_features.mandelbrot_demo_feature")

        self.assertTrue(hasattr(module, "MandelStatusEvent"))

    def test_old_gui_core_mandel_module_removed(self) -> None:
        with self.assertRaises(ModuleNotFoundError):
            importlib.import_module("gui.core.mandel_events")

    def test_old_gui_core_mandel_module_remains_unimportable_after_cache_resets(self) -> None:
        sys.modules.pop("gui.core.mandel_events", None)
        importlib.invalidate_caches()

        with self.assertRaises(ModuleNotFoundError):
            importlib.import_module("gui.core.mandel_events")

        sys.modules.pop("gui", None)
        sys.modules.pop("gui.core", None)
        importlib.invalidate_caches()

        with self.assertRaises(ModuleNotFoundError):
            importlib.import_module("gui.core.mandel_events")

    def test_mandel_module_exports_dataclass(self) -> None:
        self.assertIs(ModuleMandelStatusEvent, MandelStatusEvent)

    def test_mandel_module_all_matches_expected_schema_surface_and_order(self) -> None:
        self.assertEqual(tuple(mandel_module_all), DEMO_FEATURES_EXPORT_ORDER)
        self.assertEqual(set(mandel_module_all), set(DEMO_FEATURES_EXPORT_ORDER))

    def test_mandel_module_all_has_no_duplicates(self) -> None:
        self.assertEqual(len(mandel_module_all), len(set(mandel_module_all)))

    def test_mandel_module_all_names_are_resolvable_attributes(self) -> None:
        for export_name in mandel_module_all:
            self.assertTrue(hasattr(mandel_module, export_name), f"mandelbrot_demo_part missing attribute for __all__ export: {export_name}")


if __name__ == "__main__":
    unittest.main()
