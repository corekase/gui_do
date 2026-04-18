import unittest

from gui.utility.scheduler import Scheduler


class SchedulerGuiStub:
    pass


class SchedulerRemoveResumeInterleavingsBatch5Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.scheduler = Scheduler(SchedulerGuiStub())

    def tearDown(self) -> None:
        self.scheduler.shutdown()

    def test_removed_suspended_task_is_not_restored_by_resume_all(self) -> None:
        logic = lambda task_id: task_id
        self.scheduler.add_task("a", logic)
        self.scheduler.add_task("b", logic)
        self.scheduler.add_task("c", logic)
        self.scheduler.suspend_tasks("b", "c")

        self.scheduler.remove_tasks("b")
        self.scheduler.resume_all()

        self.assertEqual(list(self.scheduler._pending), ["a", "c"])
        self.assertNotIn("b", self.scheduler.tasks)
        self.assertEqual(self.scheduler.read_suspended(), [])

    def test_remove_tasks_prunes_finished_and_failed_entries_for_removed_ids(self) -> None:
        self.scheduler._tasks_finished.extend(["keep", "drop"])
        self.scheduler._tasks_failed.extend([("drop", "bad"), ("keep", "still-bad")])

        self.scheduler.remove_tasks("drop")

        self.assertEqual(self.scheduler.get_finished_tasks(), ["keep"])
        self.assertEqual(self.scheduler.get_failed_tasks(), [("keep", "still-bad")])

    def test_remove_tasks_clears_pending_and_suspended_state_together(self) -> None:
        logic = lambda task_id: task_id
        self.scheduler.add_task("pending", logic)
        self.scheduler.add_task("suspended", logic)
        self.scheduler.suspend_tasks("suspended")

        self.scheduler.remove_tasks("pending", "suspended")

        self.assertEqual(list(self.scheduler._pending), [])
        self.assertEqual(self.scheduler.read_suspended(), [])
        self.assertEqual(self.scheduler.tasks, {})


if __name__ == "__main__":
    unittest.main()
