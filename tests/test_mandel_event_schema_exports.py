import unittest

from demo_features.mandelbrot_demo_feature import (
    MANDEL_KIND_RUNNING_ITERATIVE,
    MANDEL_KIND_STATUS,
    MANDEL_STATUS_SCOPE,
    MANDEL_STATUS_TOPIC,
    MandelStatusEvent,
)


class TestMandelEventSchemaExports(unittest.TestCase):
    def test_status_topic_and_scope_are_strings(self):
        self.assertIsInstance(MANDEL_STATUS_TOPIC, str)
        self.assertIsInstance(MANDEL_STATUS_SCOPE, str)
        self.assertNotEqual("", MANDEL_STATUS_TOPIC)
        self.assertNotEqual("", MANDEL_STATUS_SCOPE)

    def test_status_event_payload_round_trip(self):
        event = MandelStatusEvent(kind=MANDEL_KIND_RUNNING_ITERATIVE, detail="ok")
        payload = event.to_payload()
        restored = MandelStatusEvent.from_payload(payload)

        self.assertEqual(event.kind, restored.kind)
        self.assertEqual(event.detail, restored.detail)

    def test_from_payload_uses_status_kind_for_non_dict_values(self):
        restored = MandelStatusEvent.from_payload("raw message")
        self.assertEqual(MANDEL_KIND_STATUS, restored.kind)
        self.assertEqual("raw message", restored.detail)
