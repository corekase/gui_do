import unittest
from types import SimpleNamespace

from gui.utility.constants import GuiError
from gui.utility.scheduler import Scheduler, Task, TaskFailure


class SchedulerGuiStub:
    pass


class SchedulerInternalHelpersBatch2Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.scheduler = Scheduler(SchedulerGuiStub())

    def tearDown(self) -> None:
        self.scheduler.shutdown()

    def test_remove_from_pending_clears_deque_and_set(self) -> None:
        self.scheduler._pending.extend(["a", "b"])
        self.scheduler._pending_set.update(["a", "b"])

        self.scheduler._remove_from_pending("a")

        self.assertEqual(list(self.scheduler._pending), ["b"])
        self.assertEqual(self.scheduler._pending_set, {"b"})

    def test_remove_from_suspended_clears_list_and_set(self) -> None:
        self.scheduler._suspended.extend(["x", "y"])
        self.scheduler._suspended_set.update(["x", "y"])

        self.scheduler._remove_from_suspended("x")

        self.assertEqual(self.scheduler.read_suspended(), ["y"])
        self.assertEqual(self.scheduler._suspended_set, {"y"})

    def test_decrement_message_count_locked_removes_at_zero(self) -> None:
        self.scheduler._task_message_counts["task"] = 2

        with self.scheduler._lock:
            self.scheduler._decrement_message_count_locked("task")
        self.assertEqual(self.scheduler._task_message_counts["task"], 1)

        with self.scheduler._lock:
            self.scheduler._decrement_message_count_locked("task")
        self.assertNotIn("task", self.scheduler._task_message_counts)

    def test_drain_incoming_task_failures_ignores_stale_generations(self) -> None:
        self.scheduler._task_generation["task"] = 2
        self.scheduler._incoming_task_failures.put(TaskFailure(id="task", generation=1, error="stale"))
        self.scheduler._incoming_task_failures.put(TaskFailure(id="task", generation=2, error="fresh"))

        self.scheduler._drain_incoming_task_failures()

        self.assertEqual(self.scheduler.get_failed_tasks(), [("task", "fresh")])

    def test_build_task_callable_supports_with_and_without_parameters(self) -> None:
        no_params = self.scheduler._build_task_callable("a", lambda task_id: task_id + "-ok", None)
        with_params = self.scheduler._build_task_callable("b", lambda task_id, p: f"{task_id}-{p}", "ok")

        self.assertEqual(no_params(), "a-ok")
        self.assertEqual(with_params(), "b-ok")

    def test_validate_task_id_rejects_unhashable(self) -> None:
        with self.assertRaises(GuiError):
            self.scheduler._validate_task_id([])  # type: ignore[arg-type]

    def test_remove_task_internal_cancels_running_future(self) -> None:
        cancelled = {"value": False}

        def cancel() -> None:
            cancelled["value"] = True

        task = Task(
            id="task",
            run_callable=lambda: None,
            message_method=None,
            future=SimpleNamespace(cancel=cancel),  # type: ignore[arg-type]
            generation=1,
        )
        self.scheduler.tasks["task"] = task
        self.scheduler._running.add("task")
        self.scheduler._task_message_counts["task"] = 1

        with self.scheduler._lock:
            self.scheduler._remove_task_internal("task")

        self.assertNotIn("task", self.scheduler.tasks)
        self.assertNotIn("task", self.scheduler._running)
        self.assertTrue(cancelled["value"])

    def test_submit_ready_tasks_skips_missing_task_entries(self) -> None:
        self.scheduler._pending.append("missing")
        self.scheduler._pending_set.add("missing")

        self.scheduler._submit_ready_tasks()

        self.assertEqual(list(self.scheduler._pending), [])
        self.assertEqual(self.scheduler._pending_set, set())


if __name__ == "__main__":
    unittest.main()
