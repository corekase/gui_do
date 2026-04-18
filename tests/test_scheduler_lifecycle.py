import unittest
from concurrent.futures import Future

from gui.utility.scheduler import Scheduler, Task


class SchedulerGuiStub:
    pass


class SchedulerLifecycleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scheduler = Scheduler(SchedulerGuiStub())

    def tearDown(self) -> None:
        self.scheduler.shutdown()

    def test_collect_finished_task_stores_result(self) -> None:
        future: Future[object] = Future()
        future.set_result({"ok": True})

        self.scheduler.tasks["done"] = Task(
            id="done",
            run_callable=lambda: None,
            message_method=None,
            future=future,
            generation=1,
        )
        self.scheduler._task_generation["done"] = 1
        self.scheduler._running.add("done")

        self.scheduler._enqueue_task_completion("done", 1, future)
        self.scheduler._collect_finished_tasks()

        self.assertEqual(self.scheduler.get_finished_tasks(), ["done"])
        self.assertEqual(self.scheduler.pop_result("done"), {"ok": True})
        self.assertNotIn("done", self.scheduler.tasks)

    def test_collect_task_exception_records_failure(self) -> None:
        future: Future[object] = Future()
        future.set_exception(ValueError("bad"))

        self.scheduler.tasks["fail"] = Task(
            id="fail",
            run_callable=lambda: None,
            message_method=None,
            future=future,
            generation=1,
        )
        self.scheduler._task_generation["fail"] = 1
        self.scheduler._running.add("fail")

        self.scheduler._enqueue_task_completion("fail", 1, future)
        self.scheduler._collect_finished_tasks()
        self.scheduler._drain_incoming_task_failures()

        failed = self.scheduler.get_failed_tasks()
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0][0], "fail")
        self.assertIn("ValueError: bad", failed[0][1])

    def test_message_callback_failure_is_reported(self) -> None:
        def broken_callback(_payload: object) -> None:
            raise RuntimeError("callback broke")

        self.scheduler.tasks["msg"] = Task(
            id="msg",
            run_callable=lambda: None,
            message_method=broken_callback,
            generation=1,
        )
        self.scheduler._task_generation["msg"] = 1

        self.scheduler.send_message("msg", {"progress": 1})
        self.scheduler._drain_incoming_task_messages()
        self.scheduler._dispatch_task_messages()
        self.scheduler._drain_incoming_task_failures()

        failed = self.scheduler.get_failed_tasks()
        self.assertEqual(len(failed), 1)
        self.assertEqual(failed[0][0], "msg")
        self.assertIn("Task message callback failed: RuntimeError: callback broke", failed[0][1])


if __name__ == "__main__":
    unittest.main()
