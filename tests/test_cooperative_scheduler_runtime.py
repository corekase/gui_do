"""Tests for CooperativeScheduler, CoroutineHandle, and yield tokens."""
import unittest
from unittest.mock import MagicMock

from gui_do.scheduling.cooperative_scheduler import (
    CooperativeScheduler,
    CoroutineHandle,
    Pause,
    Sleep,
    WaitUntil,
    WaitForAll,
    WaitForEvent,
    WaitForSignal,
)


# ---------------------------------------------------------------------------
# Yield token dataclasses
# ---------------------------------------------------------------------------

class TestPauseToken(unittest.TestCase):
    def test_instantiates(self) -> None:
        p = Pause()
        self.assertIsInstance(p, Pause)


class TestSleepToken(unittest.TestCase):
    def test_stores_seconds(self) -> None:
        s = Sleep(1.5)
        self.assertAlmostEqual(s.seconds, 1.5)

    def test_negative_seconds_raises(self) -> None:
        with self.assertRaises(ValueError):
            Sleep(-0.1)


class TestWaitUntilToken(unittest.TestCase):
    def test_stores_predicate(self) -> None:
        pred = lambda: True
        w = WaitUntil(pred)
        self.assertIs(w.predicate, pred)


class TestWaitForAllToken(unittest.TestCase):
    def test_stores_handles(self) -> None:
        h1 = MagicMock(spec=CoroutineHandle)
        h2 = MagicMock(spec=CoroutineHandle)
        w = WaitForAll([h1, h2])
        self.assertEqual(len(w.handles), 2)


# ---------------------------------------------------------------------------
# CooperativeScheduler basic lifecycle
# ---------------------------------------------------------------------------

class TestSchedulerInitial(unittest.TestCase):
    def test_coroutine_count_zero(self) -> None:
        s = CooperativeScheduler()
        self.assertEqual(s.coroutine_count, 0)


class TestCoroutineStartAndRun(unittest.TestCase):
    def test_start_returns_handle(self) -> None:
        s = CooperativeScheduler()
        def gen():
            yield Pause()
        h = s.start(gen())
        self.assertIsInstance(h, CoroutineHandle)

    def test_handle_is_running_initially(self) -> None:
        s = CooperativeScheduler()
        def gen():
            yield Pause()
        h = s.start(gen())
        self.assertTrue(h.is_running)
        self.assertFalse(h.is_complete)
        self.assertFalse(h.is_cancelled)

    def test_coroutine_count_increments(self) -> None:
        s = CooperativeScheduler()
        def gen():
            yield Pause()
        s.start(gen())
        s.start(gen())
        self.assertEqual(s.coroutine_count, 2)


class TestCoroutineCompletesImmediately(unittest.TestCase):
    def test_empty_generator_completes_on_first_update(self) -> None:
        s = CooperativeScheduler()
        def gen():
            return
            yield  # make it a generator
        h = s.start(gen())
        s.update(0.016)
        self.assertTrue(h.is_complete)
        self.assertFalse(h.is_running)

    def test_completed_removed_from_count(self) -> None:
        s = CooperativeScheduler()
        def gen():
            return
            yield
        s.start(gen())
        s.update(0.016)
        self.assertEqual(s.coroutine_count, 0)


class TestPauseWaitsOneFrame(unittest.TestCase):
    def test_pause_delays_one_frame(self) -> None:
        s = CooperativeScheduler()
        log = []
        def gen():
            log.append("before")
            yield Pause()
            log.append("after")
        # start() runs to first yield — "before" is logged, Pause is set
        s.start(gen())
        self.assertIn("before", log)
        self.assertNotIn("after", log)
        # First update: Pause resumes, "after" is logged
        s.update(0.016)
        self.assertIn("after", log)


class TestSleepWaits(unittest.TestCase):
    def test_sleep_does_not_resume_early(self) -> None:
        s = CooperativeScheduler()
        log = []
        def gen():
            log.append("start")
            yield Sleep(0.5)
            log.append("done")
        s.start(gen())
        s.update(0.016)   # runs to Sleep
        s.update(0.1)     # partial sleep
        self.assertNotIn("done", log)
        s.update(0.5)     # enough time elapsed
        self.assertIn("done", log)


class TestCancel(unittest.TestCase):
    def test_cancel_marks_handle_cancelled(self) -> None:
        s = CooperativeScheduler()
        def gen():
            yield Pause()
            yield Pause()
        h = s.start(gen())
        s.update(0.016)   # advance to first Pause
        h.cancel()
        self.assertTrue(h.is_cancelled)
        self.assertFalse(h.is_running)

    def test_cancelled_coroutine_removed_from_scheduler(self) -> None:
        s = CooperativeScheduler()
        def gen():
            yield Pause()
        h = s.start(gen())
        h.cancel()
        s.update(0.016)
        self.assertEqual(s.coroutine_count, 0)


class TestCancelAll(unittest.TestCase):
    def test_cancel_all_clears_scheduler(self) -> None:
        s = CooperativeScheduler()
        def gen():
            yield Pause()
        s.start(gen())
        s.start(gen())
        s.cancel_all()
        self.assertEqual(s.coroutine_count, 0)


class TestWaitUntil(unittest.TestCase):
    def test_resumes_when_predicate_true(self) -> None:
        s = CooperativeScheduler()
        flag = [False]
        log = []
        def gen():
            yield WaitUntil(lambda: flag[0])
            log.append("resumed")
        s.start(gen())
        s.update(0.016)   # starts, suspends on WaitUntil
        s.update(0.016)   # still False
        self.assertNotIn("resumed", log)
        flag[0] = True
        s.update(0.016)   # predicate now True
        self.assertIn("resumed", log)


class TestWaitForAll(unittest.TestCase):
    def test_resumes_when_all_handles_complete(self) -> None:
        s = CooperativeScheduler()
        log = []
        def child():
            yield Pause()
        def parent():
            h1 = s.start(child())
            h2 = s.start(child())
            yield WaitForAll([h1, h2])
            log.append("parent_done")
        s.start(parent())
        # Advance enough frames for children to complete
        for _ in range(5):
            s.update(0.016)
        self.assertIn("parent_done", log)
