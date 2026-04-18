import unittest

from gui.utility.constants import GuiError
from gui.utility.scheduler import Scheduler, TaskKind


class SchedulerGuiStub:
    pass


class SchedulerPublicContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scheduler = Scheduler(SchedulerGuiStub())

    def tearDown(self) -> None:
        self.scheduler.shutdown()

    def test_default_limits_and_limit_getters(self) -> None:
        self.assertEqual(self.scheduler.get_message_ingest_limit(), 256)
        self.assertIsNone(self.scheduler.get_message_dispatch_limit())
        self.assertEqual(self.scheduler.get_max_queued_messages_per_task(), 512)

        self.scheduler.set_message_ingest_limit(7)
        self.scheduler.set_message_dispatch_limit(9)
        self.scheduler.set_max_queued_messages_per_task(11)

        self.assertEqual(self.scheduler.get_message_ingest_limit(), 7)
        self.assertEqual(self.scheduler.get_message_dispatch_limit(), 9)
        self.assertEqual(self.scheduler.get_max_queued_messages_per_task(), 11)

    def test_clear_finished_and_failed_tasks(self) -> None:
        self.scheduler._tasks_finished.extend(["a", "b"])
        self.scheduler._tasks_failed.extend([("x", "bad"), ("y", "worse")])

        self.scheduler.clear_finished_tasks()
        self.scheduler.clear_failed_tasks()

        self.assertEqual(self.scheduler.get_finished_tasks(), [])
        self.assertEqual(self.scheduler.get_failed_tasks(), [])

    def test_event_factory_valid_operations(self) -> None:
        finished = self.scheduler.event(TaskKind.Finished, "task")
        failed = self.scheduler.event(TaskKind.Failed, "task", "boom")

        self.assertEqual(finished.operation, TaskKind.Finished)
        self.assertEqual(finished.id, "task")
        self.assertIsNone(finished.error)

        self.assertEqual(failed.operation, TaskKind.Failed)
        self.assertEqual(failed.id, "task")
        self.assertEqual(failed.error, "boom")

    def test_event_factory_rejects_unknown_operation(self) -> None:
        with self.assertRaises(GuiError):
            self.scheduler.event("bad", "task")  # type: ignore[arg-type]

    def test_tasks_active_match_all_and_any_reflect_pending_and_running(self) -> None:
        self.scheduler.add_task("a", lambda task_id: task_id)
        self.scheduler.add_task("b", lambda task_id: task_id)

        self.assertTrue(self.scheduler.tasks_active_match_all("a", "b"))
        self.assertTrue(self.scheduler.tasks_active_match_any("a"))
        self.assertFalse(self.scheduler.tasks_active_match_any("missing"))

        self.scheduler.update()
        self.assertTrue(self.scheduler.tasks_active_match_any("a", "b"))

    def test_tasks_busy_match_any_reflects_message_backlog(self) -> None:
        self.scheduler.add_task("t", lambda task_id: None, message_method=lambda _payload: None)
        self.scheduler.send_message("t", "payload")

        self.assertTrue(self.scheduler.tasks_busy_match_any("t"))
        self.assertFalse(self.scheduler.tasks_busy_match_any("other"))

    def test_match_helpers_validate_task_ids(self) -> None:
        with self.assertRaises(GuiError):
            self.scheduler.tasks_active_match_all([])  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            self.scheduler.tasks_active_match_any([])  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            self.scheduler.tasks_busy_match_any([])  # type: ignore[arg-type]

    def test_pop_result_returns_default_and_validates_id(self) -> None:
        self.assertEqual(self.scheduler.pop_result("missing", default="fallback"), "fallback")

        with self.assertRaises(GuiError):
            self.scheduler.pop_result([])  # type: ignore[arg-type]

    def test_remove_all_clears_pending_running_suspended_and_messages(self) -> None:
        self.scheduler.add_task("a", lambda task_id: task_id)
        self.scheduler.add_task("b", lambda task_id: task_id)
        self.scheduler.suspend_tasks("b")
        self.scheduler.add_task("m", lambda task_id: None, message_method=lambda _payload: None)
        self.scheduler.send_message("m", "x")
        self.scheduler._drain_incoming_task_messages()

        self.scheduler.remove_all()

        self.assertEqual(self.scheduler.tasks, {})
        self.assertEqual(list(self.scheduler._pending), [])
        self.assertEqual(self.scheduler.read_suspended(), [])
        self.assertEqual(len(self.scheduler._task_messages), 0)
        self.assertEqual(self.scheduler._task_message_counts, {})
        self.assertFalse(self.scheduler.tasks_active())
        self.assertFalse(self.scheduler.tasks_busy())


if __name__ == "__main__":
    unittest.main()
