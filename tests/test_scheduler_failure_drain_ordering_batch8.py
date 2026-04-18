import unittest

from gui.utility.scheduler import Scheduler


class SchedulerGuiStub:
    pass


class SchedulerFailureDrainOrderingBatch8Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.scheduler = Scheduler(SchedulerGuiStub())

    def tearDown(self) -> None:
        self.scheduler.shutdown()

    def test_preloaded_matching_failure_is_reported_in_update_cycle(self) -> None:
        self.scheduler._task_generation["task"] = 1
        self.scheduler._enqueue_task_failure("task", 1, "boom")

        finished = self.scheduler.update()

        self.assertEqual(finished, [])
        self.assertEqual(self.scheduler.get_failed_tasks(), [("task", "boom")])

    def test_preloaded_stale_and_fresh_failures_only_keep_fresh(self) -> None:
        self.scheduler._task_generation["task"] = 3
        self.scheduler._enqueue_task_failure("task", 2, "stale")
        self.scheduler._enqueue_task_failure("task", 3, "fresh")

        self.scheduler.update()

        self.assertEqual(self.scheduler.get_failed_tasks(), [("task", "fresh")])

    def test_failed_list_clears_on_next_update_without_new_failures(self) -> None:
        self.scheduler._task_generation["task"] = 1
        self.scheduler._enqueue_task_failure("task", 1, "once")

        self.scheduler.update()
        self.assertEqual(self.scheduler.get_failed_tasks(), [("task", "once")])

        self.scheduler.update()
        self.assertEqual(self.scheduler.get_failed_tasks(), [])


if __name__ == "__main__":
    unittest.main()
