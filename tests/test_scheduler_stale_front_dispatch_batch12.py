import unittest

from gui.utility.scheduler import Scheduler, Task


class SchedulerGuiStub:
    pass


class SchedulerStaleFrontDispatchBatch12Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.scheduler = Scheduler(SchedulerGuiStub())

    def tearDown(self) -> None:
        self.scheduler.shutdown()

    def test_dispatch_limit_delivers_fresh_after_stale_filtered_in_drain(self) -> None:
        observed = []

        self.scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=lambda payload: observed.append(payload),
            generation=1,
        )
        self.scheduler._task_generation["task"] = 1
        self.scheduler.send_message("task", "old")

        self.scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=lambda payload: observed.append(payload),
            generation=2,
        )
        self.scheduler._task_generation["task"] = 2
        self.scheduler.send_message("task", "new")

        self.scheduler.set_message_dispatch_limit(1)
        self.scheduler._drain_incoming_task_messages()
        self.scheduler._dispatch_task_messages()

        self.assertEqual(observed, ["new"])
        self.assertIsNone(self.scheduler._task_message_counts.get("task"))

        self.scheduler._dispatch_task_messages()

        self.assertEqual(observed, ["new"])
        self.assertIsNone(self.scheduler._task_message_counts.get("task"))

    def test_unbounded_ingest_with_mixed_stale_messages_clears_counts(self) -> None:
        observed = []

        self.scheduler.tasks["task"] = Task(id="task", run_callable=lambda: None, message_method=lambda _p: None, generation=1)
        self.scheduler._task_generation["task"] = 1
        self.scheduler.send_message("task", "old-1")
        self.scheduler.send_message("task", "old-2")

        self.scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=lambda payload: observed.append(payload),
            generation=2,
        )
        self.scheduler._task_generation["task"] = 2
        self.scheduler.send_message("task", "new-1")

        self.scheduler.set_message_ingest_limit(None)
        self.scheduler._drain_incoming_task_messages()
        self.scheduler._dispatch_task_messages()

        self.assertEqual(observed, ["new-1"])
        self.assertIsNone(self.scheduler._task_message_counts.get("task"))


if __name__ == "__main__":
    unittest.main()
