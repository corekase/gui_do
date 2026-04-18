import unittest

from gui.utility.scheduler import Scheduler, Task


class SchedulerGuiStub:
    pass


class SchedulerMessageInterleavingsBatch11Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.scheduler = Scheduler(SchedulerGuiStub())

    def tearDown(self) -> None:
        self.scheduler.shutdown()

    def test_stale_and_fresh_messages_reconcile_message_count_in_one_cycle(self) -> None:
        observed = []
        old_handler = lambda _payload: None
        new_handler = lambda payload: observed.append(payload)

        self.scheduler.tasks["task"] = Task(id="task", run_callable=lambda: None, message_method=old_handler, generation=1)
        self.scheduler._task_generation["task"] = 1
        self.scheduler.send_message("task", "old-1")
        self.scheduler.send_message("task", "old-2")

        self.scheduler.tasks["task"] = Task(id="task", run_callable=lambda: None, message_method=new_handler, generation=2)
        self.scheduler._task_generation["task"] = 2
        self.scheduler.send_message("task", "new-1")
        self.scheduler.send_message("task", "new-2")

        self.scheduler._drain_incoming_task_messages()
        self.scheduler._dispatch_task_messages()

        self.assertEqual(observed, ["new-1", "new-2"])
        self.assertIsNone(self.scheduler._task_message_counts.get("task"))

    def test_ingest_limited_interleaving_preserves_fresh_delivery_and_counts(self) -> None:
        observed = []
        old_handler = lambda _payload: None
        new_handler = lambda payload: observed.append(payload)

        self.scheduler.tasks["task"] = Task(id="task", run_callable=lambda: None, message_method=old_handler, generation=1)
        self.scheduler._task_generation["task"] = 1
        self.scheduler.send_message("task", "old-1")
        self.scheduler.send_message("task", "old-2")

        self.scheduler.tasks["task"] = Task(id="task", run_callable=lambda: None, message_method=new_handler, generation=2)
        self.scheduler._task_generation["task"] = 2
        self.scheduler.send_message("task", "new-1")
        self.scheduler.send_message("task", "new-2")

        self.scheduler.set_message_ingest_limit(3)
        self.scheduler._drain_incoming_task_messages()
        self.scheduler._dispatch_task_messages()

        self.assertEqual(observed, ["new-1"])
        self.assertEqual(self.scheduler._task_message_counts.get("task"), 1)

        self.scheduler._drain_incoming_task_messages()
        self.scheduler._dispatch_task_messages()

        self.assertEqual(observed, ["new-1", "new-2"])
        self.assertIsNone(self.scheduler._task_message_counts.get("task"))


if __name__ == "__main__":
    unittest.main()
