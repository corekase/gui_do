import unittest
import importlib
import sys
import demo_parts

from demo_parts.mandel_events import MANDEL_KIND_COMPLETE
from demo_parts.mandel_events import MANDEL_KIND_CLEARED
from demo_parts.mandel_events import MANDEL_KIND_FAILED
from demo_parts.mandel_events import MANDEL_KIND_IDLE
from demo_parts.mandel_events import MANDEL_KIND_RUNNING_FOUR_SPLIT
from demo_parts.mandel_events import MANDEL_KIND_RUNNING_ITERATIVE
from demo_parts.mandel_events import MANDEL_KIND_RUNNING_ONE_SPLIT
from demo_parts.mandel_events import MANDEL_KIND_RUNNING_RECURSIVE
from demo_parts.mandel_events import MANDEL_KIND_STATUS
from demo_parts.mandel_events import MANDEL_STATUS_SCOPE
from demo_parts.mandel_events import MANDEL_STATUS_TOPIC
from demo_parts.mandel_events import MandelStatusEvent
from demo_parts import __all__ as demo_parts_all
from demo_parts import MandelStatusEvent as PackageMandelStatusEvent
from tests.contract_test_catalog import DEMO_PARTS_EXPORT_ORDER


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

    def test_demo_parts_schema_module_importable(self) -> None:
        module = importlib.import_module("demo_parts.mandel_events")

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

    def test_demo_parts_package_reexports_dataclass(self) -> None:
        self.assertIs(PackageMandelStatusEvent, MandelStatusEvent)

    def test_demo_parts_all_matches_expected_schema_surface_and_order(self) -> None:
        self.assertEqual(tuple(demo_parts_all), DEMO_PARTS_EXPORT_ORDER)
        self.assertEqual(set(demo_parts_all), set(DEMO_PARTS_EXPORT_ORDER))

    def test_demo_parts_all_has_no_duplicates(self) -> None:
        self.assertEqual(len(demo_parts_all), len(set(demo_parts_all)))

    def test_demo_parts_all_names_are_resolvable_attributes(self) -> None:
        for export_name in demo_parts_all:
            self.assertTrue(hasattr(demo_parts, export_name), f"demo_parts missing attribute for __all__ export: {export_name}")


if __name__ == "__main__":
    unittest.main()
