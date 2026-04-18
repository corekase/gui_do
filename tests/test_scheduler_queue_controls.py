import unittest

from gui.utility.events import GuiError
from gui.utility.scheduler import Scheduler, Task


class SchedulerGuiStub:
    pass


class SchedulerQueueControlTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scheduler = Scheduler(SchedulerGuiStub())

    def tearDown(self) -> None:
        self.scheduler.shutdown()

    def test_ingest_limit_drains_messages_across_updates(self) -> None:
        observed = []

        def on_message(payload: object) -> None:
            observed.append(payload)

        self.scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=on_message,
            generation=1,
        )
        self.scheduler._task_generation["task"] = 1
        self.scheduler.set_message_ingest_limit(1)

        self.scheduler.send_message("task", "one")
        self.scheduler.send_message("task", "two")

        self.scheduler._drain_incoming_task_messages()
        self.scheduler._dispatch_task_messages()

        self.assertEqual(observed, ["one"])
        self.assertEqual(self.scheduler._task_message_counts.get("task"), 1)

        self.scheduler._drain_incoming_task_messages()
        self.scheduler._dispatch_task_messages()

        self.assertEqual(observed, ["one", "two"])
        self.assertIsNone(self.scheduler._task_message_counts.get("task"))

    def test_dispatch_limit_batches_callback_delivery(self) -> None:
        observed = []

        def on_message(payload: object) -> None:
            observed.append(payload)

        self.scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=on_message,
            generation=1,
        )
        self.scheduler._task_generation["task"] = 1
        self.scheduler.set_message_dispatch_limit(1)

        self.scheduler.send_message("task", "a")
        self.scheduler.send_message("task", "b")

        self.scheduler._drain_incoming_task_messages()
        self.scheduler._dispatch_task_messages()
        self.assertEqual(observed, ["a"])

        self.scheduler._dispatch_task_messages()
        self.assertEqual(observed, ["a", "b"])

    def test_tasks_busy_reflects_queued_message_counts(self) -> None:
        self.assertFalse(self.scheduler.tasks_busy())

        self.scheduler._task_message_counts["task"] = 1

        self.assertTrue(self.scheduler.tasks_busy())
        self.assertTrue(self.scheduler.tasks_busy_match_any("task"))

    def test_setters_reject_invalid_limit_values(self) -> None:
        with self.assertRaises(GuiError):
            self.scheduler.set_message_ingest_limit(0)
        with self.assertRaises(GuiError):
            self.scheduler.set_message_dispatch_limit(0)
        with self.assertRaises(GuiError):
            self.scheduler.set_max_queued_messages_per_task(0)

    def test_remove_tasks_clears_queued_dispatch_messages(self) -> None:
        observed = []

        def on_message(payload: object) -> None:
            observed.append(payload)

        self.scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=on_message,
            generation=1,
        )
        self.scheduler._task_generation["task"] = 1

        self.scheduler.send_message("task", "msg")
        self.scheduler._drain_incoming_task_messages()
        self.assertEqual(len(self.scheduler._task_messages), 1)

        self.scheduler.remove_tasks("task")
        self.assertEqual(len(self.scheduler._task_messages), 0)

        self.scheduler._dispatch_task_messages()
        self.assertEqual(observed, [])


if __name__ == "__main__":
    unittest.main()
