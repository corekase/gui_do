import unittest

from gui.utility.scheduler import Scheduler


class SchedulerGuiStub:
    pass


class SchedulerSuspendResumeTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scheduler = Scheduler(SchedulerGuiStub())

    def tearDown(self) -> None:
        self.scheduler.shutdown()

    def _add_simple_tasks(self) -> None:
        logic = lambda task_id: task_id
        self.scheduler.add_task("a", logic)
        self.scheduler.add_task("b", logic)
        self.scheduler.add_task("c", logic)

    def test_suspend_tasks_moves_selected_pending_tasks(self) -> None:
        self._add_simple_tasks()

        self.scheduler.suspend_tasks("b", "c")

        self.assertEqual(list(self.scheduler._pending), ["a"])
        self.assertEqual(self.scheduler.read_suspended(), ["b", "c"])
        self.assertTrue("b" in self.scheduler._suspended_set)
        self.assertTrue("c" in self.scheduler._suspended_set)

    def test_resume_tasks_restores_selected_suspended_tasks(self) -> None:
        self._add_simple_tasks()
        self.scheduler.suspend_tasks("b", "c")

        self.scheduler.resume_tasks("c")

        self.assertEqual(list(self.scheduler._pending), ["a", "c"])
        self.assertEqual(self.scheduler.read_suspended(), ["b"])
        self.assertTrue("c" not in self.scheduler._suspended_set)

    def test_suspend_all_then_resume_all_restores_order(self) -> None:
        self._add_simple_tasks()

        self.scheduler.suspend_all()
        self.assertEqual(list(self.scheduler._pending), [])
        self.assertEqual(self.scheduler.read_suspended(), ["a", "b", "c"])

        self.scheduler.resume_all()

        self.assertEqual(list(self.scheduler._pending), ["a", "b", "c"])
        self.assertEqual(self.scheduler.read_suspended(), [])

    def test_resume_tasks_ignores_non_suspended_ids(self) -> None:
        self._add_simple_tasks()
        self.scheduler.suspend_tasks("b")

        self.scheduler.resume_tasks("a", "c")

        self.assertEqual(list(self.scheduler._pending), ["a", "c"])
        self.assertEqual(self.scheduler.read_suspended(), ["b"])

    def test_suspend_tasks_ignores_non_pending_ids(self) -> None:
        self._add_simple_tasks()
        self.scheduler.suspend_tasks("b")

        self.scheduler.suspend_tasks("b", "missing")

        self.assertEqual(list(self.scheduler._pending), ["a", "c"])
        self.assertEqual(self.scheduler.read_suspended(), ["b"])


if __name__ == "__main__":
    unittest.main()
