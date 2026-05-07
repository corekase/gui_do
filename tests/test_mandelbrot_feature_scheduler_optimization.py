import unittest

import pygame

from demo_features.mandelbrot.mandelbrot_feature import MandelbrotFeature


class _StubScheduler:
    def __init__(self):
        self.dispatch_limit = 77
        self.ingest_limit = 155
        self.dispatch_set_calls = []
        self.ingest_set_calls = []

    def get_message_dispatch_limit(self):
        return self.dispatch_limit

    def get_message_ingest_limit(self):
        return self.ingest_limit

    def set_message_dispatch_limit(self, value):
        self.dispatch_limit = value
        self.dispatch_set_calls.append(value)

    def set_message_ingest_limit(self, value):
        self.ingest_limit = value
        self.ingest_set_calls.append(value)


class _CanvasNode:
    def __init__(self, width: int, height: int):
        self.canvas = pygame.Surface((int(width), int(height)))


class MandelbrotFeatureSchedulerOptimizationTests(unittest.TestCase):
    def test_set_busy_uses_and_restores_scheduler_baseline_limits(self):
        feature = MandelbrotFeature()
        scheduler = _StubScheduler()
        feature.scheduler = scheduler
        feature._idle_dispatch_limit = scheduler.get_message_dispatch_limit()
        feature._idle_ingest_limit = scheduler.get_message_ingest_limit()

        feature._set_busy(True)
        self.assertEqual(77, scheduler.dispatch_limit)
        self.assertEqual(256, scheduler.ingest_limit)

        feature._set_busy(False)
        self.assertEqual(77, scheduler.dispatch_limit)
        self.assertEqual(155, scheduler.ingest_limit)

    def test_iterative_apply_result_uses_cached_color_table(self):
        feature = MandelbrotFeature()
        feature.primary_canvas = _CanvasNode(3, 1)
        feature.split_canvases = {}
        feature._color_table = ((10, 0, 0), (20, 0, 0), (30, 0, 0), (0, 0, 0))

        feature._apply_result("iter", (0, [0, 1, 2]))

        surface = feature.primary_canvas.canvas
        self.assertEqual((10, 0, 0), surface.get_at((0, 0))[:3])
        self.assertEqual((20, 0, 0), surface.get_at((1, 0))[:3])
        self.assertEqual((30, 0, 0), surface.get_at((2, 0))[:3])

    def test_iterative_apply_result_supports_chunked_row_payload(self):
        feature = MandelbrotFeature()
        feature.primary_canvas = _CanvasNode(4, 1)
        feature.split_canvases = {}
        feature._color_table = ((10, 0, 0), (20, 0, 0), (30, 0, 0), (40, 0, 0), (0, 0, 0))

        feature._apply_result("iter", (0, 2, [1, 2]))

        surface = feature.primary_canvas.canvas
        self.assertEqual((0, 0, 0), surface.get_at((0, 0))[:3])
        self.assertEqual((0, 0, 0), surface.get_at((1, 0))[:3])
        self.assertEqual((20, 0, 0), surface.get_at((2, 0))[:3])
        self.assertEqual((30, 0, 0), surface.get_at((3, 0))[:3])

    def test_queue_staged_tasks_enqueues_one_and_defers_rest(self):
        feature = MandelbrotFeature()
        queued = []

        def _queue_task(host, task_id, logic_alias, runnable, params):
            queued.append((task_id, logic_alias, runnable, params))

        feature._queue_task = _queue_task
        tasks = [
            ("1", "primary", "recursive_task", {"k": 1}),
            ("2", "primary", "recursive_task", {"k": 2}),
            ("3", "primary", "recursive_task", {"k": 3}),
        ]

        feature._queue_staged_tasks(object(), tasks)

        self.assertEqual([("1", "primary", "recursive_task", {"k": 1})], queued)
        self.assertEqual([
            ("2", "primary", "recursive_task", {"k": 2}),
            ("3", "primary", "recursive_task", {"k": 3}),
        ], feature._pending_launches)


if __name__ == "__main__":
    unittest.main()
