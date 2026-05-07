import unittest

from pygame import Rect

from demo_features.mandelbrot.mandelbrot_logic import MandelbrotLogicFeature


class _StubScheduler:
    def __init__(self):
        self.messages = []

    def send_message(self, task_id, payload):
        self.messages.append((task_id, payload))


class MandelbrotLogicSliceBudgetTests(unittest.TestCase):
    def test_iterative_task_emits_chunked_payloads(self):
        logic = MandelbrotLogicFeature()
        logic.ITERATIVE_MIN_CHUNK = 8
        logic.ITERATIVE_MAX_CHUNK = 8
        scheduler = _StubScheduler()

        logic.run_iterative_task(
            scheduler,
            "iter",
            {"size": (24, 1), "center": -0.7 + 0.0j, "scale": 0.01},
        )

        payloads = [payload for task_id, payload in scheduler.messages if task_id == "iter"]
        self.assertEqual(3, len(payloads))
        self.assertEqual((0, 0), payloads[0][:2])
        self.assertEqual((0, 8), payloads[1][:2])
        self.assertEqual((0, 16), payloads[2][:2])
        self.assertEqual(8, len(payloads[0][2]))

    def test_recursive_leaf_sends_scalar_for_uniform_tile(self):
        logic = MandelbrotLogicFeature()
        scheduler = _StubScheduler()

        logic.run_recursive_task(
            scheduler,
            "recu",
            {
                "size": (8, 8),
                "center": 3.0 + 3.0j,
                "scale": 0.05,
                "rect": Rect(0, 0, 8, 8),
            },
        )

        self.assertEqual(1, len(scheduler.messages))
        payload = scheduler.messages[0][1]
        self.assertEqual((0, 0, 8, 8), payload[:4])
        self.assertIsInstance(payload[4], int)


if __name__ == "__main__":
    unittest.main()
