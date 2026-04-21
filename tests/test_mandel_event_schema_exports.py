import unittest

from demo_parts.mandel_events import MANDEL_KIND_COMPLETE
from demo_parts.mandel_events import MANDEL_KIND_FAILED
from demo_parts.mandel_events import MANDEL_KIND_STATUS
from demo_parts.mandel_events import MANDEL_STATUS_SCOPE
from demo_parts.mandel_events import MANDEL_STATUS_TOPIC
from demo_parts.mandel_events import MandelStatusEvent


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


if __name__ == "__main__":
    unittest.main()
