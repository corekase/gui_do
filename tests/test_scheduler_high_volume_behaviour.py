import unittest

from gui.utility.scheduler import Scheduler, Task


class SchedulerGuiStub:
    pass


class SchedulerHighVolumeBehaviourTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scheduler = Scheduler(SchedulerGuiStub())

    def tearDown(self) -> None:
        self.scheduler.shutdown()

    def test_large_backlog_preserves_order_across_limited_updates(self) -> None:
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
        self.scheduler.set_message_ingest_limit(17)
        self.scheduler.set_message_dispatch_limit(13)

        for value in range(200):
            self.scheduler.send_message("task", value)

        for _ in range(100):
            self.scheduler._drain_incoming_task_messages()
            self.scheduler._dispatch_task_messages()
            if self.scheduler._task_message_counts.get("task") is None:
                break

        self.assertEqual(observed, list(range(200)))
        self.assertIsNone(self.scheduler._task_message_counts.get("task"))

    def test_callback_failure_does_not_block_backlog_progress(self) -> None:
        observed = []

        def on_message(payload: object) -> None:
            if payload == 57:
                raise RuntimeError("boom")
            observed.append(payload)

        self.scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=on_message,
            generation=1,
        )
        self.scheduler._task_generation["task"] = 1
        self.scheduler.set_message_ingest_limit(23)
        self.scheduler.set_message_dispatch_limit(11)

        for value in range(120):
            self.scheduler.send_message("task", value)

        for _ in range(100):
            self.scheduler._drain_incoming_task_messages()
            self.scheduler._dispatch_task_messages()
            self.scheduler._drain_incoming_task_failures()
            if self.scheduler._task_message_counts.get("task") is None:
                break

        self.assertEqual(observed, [value for value in range(120) if value != 57])
        failed = self.scheduler.get_failed_tasks()
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0][0], "task")
        self.assertIn("Task message callback failed", failed[0][1])

    def test_large_stale_generation_backlog_is_discarded(self) -> None:
        observed_new = []

        def on_message(payload: object) -> None:
            observed_new.append(payload)

        self.scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=lambda payload: None,
            generation=1,
        )
        self.scheduler._task_generation["task"] = 1
        for value in range(150):
            self.scheduler.send_message("task", value)

        self.scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=on_message,
            generation=2,
        )
        self.scheduler._task_generation["task"] = 2

        for value in range(10):
            self.scheduler.send_message("task", f"new-{value}")

        self.scheduler.set_message_ingest_limit(32)
        self.scheduler.set_message_dispatch_limit(32)

        for _ in range(20):
            self.scheduler._drain_incoming_task_messages()
            self.scheduler._dispatch_task_messages()
            if self.scheduler._task_message_counts.get("task") is None:
                break

        self.assertEqual(observed_new, [f"new-{value}" for value in range(10)])
        self.assertIsNone(self.scheduler._task_message_counts.get("task"))


if __name__ == "__main__":
    unittest.main()
