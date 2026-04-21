import unittest
import importlib
import sys

from demo_parts.mandel_events import MANDEL_KIND_COMPLETE
from demo_parts.mandel_events import MANDEL_KIND_FAILED
from demo_parts.mandel_events import MANDEL_KIND_STATUS
from demo_parts.mandel_events import MANDEL_STATUS_SCOPE
from demo_parts.mandel_events import MANDEL_STATUS_TOPIC
from demo_parts.mandel_events import MandelStatusEvent
from demo_parts import __all__ as demo_parts_all
from demo_parts import MandelStatusEvent as PackageMandelStatusEvent


class MandelEventSchemaExportTests(unittest.TestCase):
    def test_schema_exports_are_available(self) -> None:
        self.assertEqual(MANDEL_STATUS_TOPIC, "demo.mandel.status")
        self.assertEqual(MANDEL_STATUS_SCOPE, "main")
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

    def test_demo_parts_all_contains_core_schema_names(self) -> None:
        self.assertIn("MandelStatusEvent", demo_parts_all)
        self.assertIn("MANDEL_STATUS_TOPIC", demo_parts_all)


if __name__ == "__main__":
    unittest.main()
