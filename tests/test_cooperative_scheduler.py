import unittest

from gui_do.scheduling.cooperative_scheduler import (
    CoroutineHandle,
    CooperativeScheduler,
    Pause,
    Sleep,
    WaitForAll,
    WaitUntil,
)


def _tick(scheduler: CooperativeScheduler, dt: float = 0.016, n: int = 1) -> None:
    for _ in range(n):
        scheduler.update(dt)


class TestCooperativeSchedulerBasics(unittest.TestCase):
    def test_coroutine_completes_immediately_when_no_yields(self):
        scheduler = CooperativeScheduler()
        ran = []

        def _gen():
            ran.append(True)
            return
            yield  # make it a generator

        handle = scheduler.start(_gen())

        self.assertTrue(handle.is_complete)
        self.assertFalse(handle.is_running)
        self.assertEqual([True], ran)

    def test_coroutine_runs_body_before_first_yield(self):
        scheduler = CooperativeScheduler()
        log = []

        def _gen():
            log.append("before")
            yield Pause()
            log.append("after")

        scheduler.start(_gen())

        self.assertEqual(["before"], log)

    def test_pause_resumes_after_one_tick(self):
        scheduler = CooperativeScheduler()
        log = []

        def _gen():
            log.append("a")
            yield Pause()
            log.append("b")

        scheduler.start(_gen())
        self.assertEqual(["a"], log)

        _tick(scheduler)
        self.assertEqual(["a", "b"], log)

    def test_sleep_resumes_after_elapsed_time(self):
        scheduler = CooperativeScheduler()
        log = []

        def _gen():
            log.append("start")
            yield Sleep(0.1)
            log.append("end")

        scheduler.start(_gen())
        self.assertEqual(["start"], log)

        _tick(scheduler, dt=0.05)
        self.assertEqual(["start"], log)  # not yet elapsed

        _tick(scheduler, dt=0.06)
        self.assertEqual(["start", "end"], log)

    def test_sleep_zero_resumes_next_tick(self):
        scheduler = CooperativeScheduler()
        log = []

        def _gen():
            log.append("a")
            yield Sleep(0.0)
            log.append("b")

        scheduler.start(_gen())
        _tick(scheduler, dt=0.0)
        self.assertEqual(["a", "b"], log)

    def test_sleep_negative_seconds_raises_value_error(self):
        with self.assertRaises(ValueError):
            Sleep(-0.1)

    def test_wait_until_resumes_when_predicate_true(self):
        scheduler = CooperativeScheduler()
        flag = [False]
        log = []

        def _gen():
            log.append("waiting")
            yield WaitUntil(lambda: flag[0])
            log.append("done")

        scheduler.start(_gen())
        _tick(scheduler)
        self.assertEqual(["waiting"], log)

        flag[0] = True
        _tick(scheduler)
        self.assertEqual(["waiting", "done"], log)

    def test_cancel_stops_running_coroutine(self):
        scheduler = CooperativeScheduler()
        log = []

        def _gen():
            log.append("a")
            yield Pause()
            log.append("b")  # should never run

        handle = scheduler.start(_gen())
        handle.cancel()
        _tick(scheduler)

        self.assertTrue(handle.is_cancelled)
        self.assertFalse(handle.is_running)
        self.assertEqual(["a"], log)

    def test_cancel_all_stops_all_coroutines(self):
        scheduler = CooperativeScheduler()

        def _long():
            while True:
                yield Pause()

        h1 = scheduler.start(_long())
        h2 = scheduler.start(_long())

        scheduler.cancel_all()

        self.assertTrue(h1.is_cancelled)
        self.assertTrue(h2.is_cancelled)
        self.assertEqual(0, scheduler.coroutine_count)

    def test_coroutine_count_reflects_running_coroutines(self):
        scheduler = CooperativeScheduler()

        def _one_pause():
            yield Pause()

        self.assertEqual(0, scheduler.coroutine_count)
        scheduler.start(_one_pause())
        self.assertEqual(1, scheduler.coroutine_count)
        _tick(scheduler)
        self.assertEqual(0, scheduler.coroutine_count)

    def test_completed_handles_are_purged_after_tick(self):
        scheduler = CooperativeScheduler()

        def _instant():
            return
            yield

        scheduler.start(_instant())
        _tick(scheduler)

        self.assertEqual(0, scheduler.coroutine_count)

    def test_multiple_coroutines_run_concurrently(self):
        scheduler = CooperativeScheduler()
        log = []

        def _a():
            log.append("a1")
            yield Pause()
            log.append("a2")

        def _b():
            log.append("b1")
            yield Pause()
            log.append("b2")

        scheduler.start(_a())
        scheduler.start(_b())
        _tick(scheduler)

        self.assertIn("a1", log)
        self.assertIn("b1", log)
        self.assertIn("a2", log)
        self.assertIn("b2", log)

    def test_wait_for_all_resumes_after_all_complete(self):
        scheduler = CooperativeScheduler()
        log = []

        def _child():
            yield Pause()

        def _parent(h1, h2):
            log.append("waiting")
            yield WaitForAll([h1, h2])
            log.append("all done")

        h1 = scheduler.start(_child())
        h2 = scheduler.start(_child())
        scheduler.start(_parent(h1, h2))

        _tick(scheduler)  # children complete, parent should resume
        self.assertIn("all done", log)

    def test_unknown_yield_token_treated_as_pause(self):
        scheduler = CooperativeScheduler()
        log = []

        def _gen():
            log.append("a")
            yield "not_a_token"
            log.append("b")

        scheduler.start(_gen())
        _tick(scheduler)
        self.assertEqual(["a", "b"], log)

    def test_cancel_on_already_completed_handle_is_noop(self):
        scheduler = CooperativeScheduler()

        def _instant():
            return
            yield

        handle = scheduler.start(_instant())
        self.assertTrue(handle.is_complete)
        handle.cancel()  # should not raise
        self.assertFalse(handle.is_cancelled)

    def test_coroutine_handle_is_running_only_while_active(self):
        scheduler = CooperativeScheduler()

        def _gen():
            yield Pause()

        handle = scheduler.start(_gen())
        self.assertTrue(handle.is_running)
        _tick(scheduler)
        self.assertFalse(handle.is_running)
        self.assertTrue(handle.is_complete)


if __name__ == "__main__":
    unittest.main()
