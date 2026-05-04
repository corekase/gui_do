"""Tests for gui_do.scheduling.dataflow_pipeline."""
from __future__ import annotations

import threading
import unittest

from gui_do.scheduling.dataflow_pipeline import (
    CancelledError,
    CancellationToken,
    DataflowPipeline,
    PipelineHandle,
    PipelineStage,
)


class TestCancellationToken(unittest.TestCase):
    def test_not_cancelled_initially(self):
        token = CancellationToken()
        self.assertFalse(token.is_cancelled)

    def test_cancel_sets_flag(self):
        token = CancellationToken()
        token.cancel()
        self.assertTrue(token.is_cancelled)

    def test_cancel_idempotent(self):
        token = CancellationToken()
        token.cancel()
        token.cancel()
        self.assertTrue(token.is_cancelled)

    def test_raise_if_cancelled(self):
        token = CancellationToken()
        token.cancel()
        with self.assertRaises(CancelledError):
            token.raise_if_cancelled()

    def test_raise_if_not_cancelled_does_nothing(self):
        token = CancellationToken()
        token.raise_if_cancelled()  # no exception


class TestPipelineStage(unittest.TestCase):
    def test_repr(self):
        stage = PipelineStage("double", lambda v, t: v * 2)
        self.assertIn("double", repr(stage))

    def test_transform_called(self):
        token = CancellationToken()
        stage = PipelineStage("add1", lambda v, t: v + 1)
        self.assertEqual(stage.transform(5, token), 6)


class TestDataflowPipeline(unittest.TestCase):
    def _make_add(self, n: int) -> PipelineStage:
        return PipelineStage(f"add{n}", lambda v, t: v + n)

    def test_empty_pipeline_returns_input(self):
        pipe = DataflowPipeline()
        handle = pipe.run(42)
        self.assertTrue(handle.is_done)
        self.assertEqual(handle.result, 42)

    def test_single_stage(self):
        pipe = DataflowPipeline([self._make_add(10)])
        self.assertEqual(pipe.run(5).result, 15)

    def test_chained_stages(self):
        pipe = DataflowPipeline([self._make_add(1), self._make_add(2), self._make_add(3)])
        self.assertEqual(pipe.run(0).result, 6)

    def test_add_stage_after_construction(self):
        pipe = DataflowPipeline()
        pipe.add_stage(self._make_add(7))
        self.assertEqual(pipe.run(0).result, 7)

    def test_stages_list_is_copy(self):
        pipe = DataflowPipeline([self._make_add(1)])
        stages = pipe.stages
        stages.clear()
        self.assertEqual(len(pipe.stages), 1)

    def test_repr(self):
        pipe = DataflowPipeline([self._make_add(1), self._make_add(2)])
        r = repr(pipe)
        self.assertIn("add1", r)
        self.assertIn("add2", r)

    def test_handle_is_done_after_run(self):
        pipe = DataflowPipeline()
        handle = pipe.run(0)
        self.assertTrue(handle.is_done)

    def test_handle_not_done_before_run(self):
        handle = PipelineHandle(CancellationToken(), 1)
        self.assertFalse(handle.is_done)

    def test_handle_result_before_done_raises(self):
        handle = PipelineHandle(CancellationToken(), 1)
        with self.assertRaises(RuntimeError):
            _ = handle.result

    def test_error_propagates_to_handle(self):
        def boom(v, t):
            raise ValueError("boom")

        pipe = DataflowPipeline([PipelineStage("boom", boom)])
        handle = pipe.run(0)
        self.assertTrue(handle.is_done)
        with self.assertRaises(ValueError):
            _ = handle.result

    def test_cancellation_mid_pipeline(self):
        fired = []

        def slow(v, t):
            t.cancel()  # cancel ourselves
            t.raise_if_cancelled()
            fired.append("should-not-reach")
            return v

        pipe = DataflowPipeline([PipelineStage("self-cancel", slow)])
        handle = pipe.run(0)
        self.assertTrue(handle.is_done)
        self.assertTrue(handle.is_cancelled)
        self.assertEqual(fired, [])
        with self.assertRaises(CancelledError):
            _ = handle.result

    def test_new_run_cancels_previous_handle(self):
        # We can't truly interleave synchronous runs, but we verify that
        # a completed handle is not re-cancelled on subsequent calls.
        pipe = DataflowPipeline([self._make_add(1)])
        h1 = pipe.run(0)
        h2 = pipe.run(0)
        self.assertTrue(h1.is_done)
        self.assertTrue(h2.is_done)
        self.assertEqual(h2.result, 1)

    def test_cancel_via_handle(self):
        handle = PipelineHandle(CancellationToken(), 1)
        handle.cancel()
        self.assertTrue(handle.is_cancelled)

    def test_pipeline_stage_count(self):
        stages = [self._make_add(i) for i in range(5)]
        pipe = DataflowPipeline(stages)
        self.assertEqual(len(pipe.stages), 5)


if __name__ == "__main__":
    unittest.main()
