import threading
import time
import unittest

from gui.utility.scheduler import Scheduler, Task


class SchedulerGuiStub:
    pass


class SchedulerAsyncBackpressureBatchTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scheduler = Scheduler(SchedulerGuiStub())

    def tearDown(self) -> None:
        self.scheduler.shutdown()

    def test_add_task_passes_parameters_and_stores_result(self) -> None:
        def logic(task_id, parameters):
            return (task_id, parameters["value"])

        self.scheduler.add_task("task", logic, parameters={"value": 7})

        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            self.scheduler.update()
            if "task" in self.scheduler.get_finished_tasks():
                break
            time.sleep(0.005)

        self.assertIn("task", self.scheduler.get_finished_tasks())
        self.assertEqual(self.scheduler.pop_result("task"), ("task", 7))

    def test_add_task_supports_async_callable_result(self) -> None:
        async def logic(task_id):
            return f"{task_id}-done"

        self.scheduler.add_task("async", logic)

        deadline = time.monotonic() + 1.0
        while time.monotonic() < deadline:
            self.scheduler.update()
            if "async" in self.scheduler.get_finished_tasks():
                break
            time.sleep(0.005)

        self.assertIn("async", self.scheduler.get_finished_tasks())
        self.assertEqual(self.scheduler.pop_result("async"), "async-done")

    def test_send_message_backpressure_waits_until_slot_is_freed(self) -> None:
        observed = []

        def on_message(payload):
            observed.append(payload)

        self.scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=on_message,
            generation=1,
        )
        self.scheduler._task_generation["task"] = 1
        self.scheduler.set_max_queued_messages_per_task(1)

        self.scheduler.send_message("task", "first")

        started = threading.Event()
        completed = threading.Event()

        def producer() -> None:
            started.set()
            self.scheduler.send_message("task", "second")
            completed.set()

        worker = threading.Thread(target=producer)
        worker.start()

        self.assertTrue(started.wait(timeout=1.0))
        self.assertFalse(completed.wait(timeout=0.05))

        self.scheduler._drain_incoming_task_messages()
        self.scheduler._dispatch_task_messages()

        self.assertTrue(completed.wait(timeout=1.0))
        worker.join(timeout=1.0)

        self.scheduler._drain_incoming_task_messages()
        self.scheduler._dispatch_task_messages()

        self.assertEqual(observed, ["first", "second"])

    def test_none_max_queued_messages_allows_unbounded_enqueue(self) -> None:
        observed = []

        def on_message(payload):
            observed.append(payload)

        self.scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=on_message,
            generation=1,
        )
        self.scheduler._task_generation["task"] = 1
        self.scheduler.set_max_queued_messages_per_task(None)

        for i in range(50):
            self.scheduler.send_message("task", i)

        self.scheduler._drain_incoming_task_messages()
        self.scheduler._dispatch_task_messages()

        self.assertEqual(observed, list(range(50)))
        self.assertIsNone(self.scheduler._task_message_counts.get("task"))


if __name__ == "__main__":
    unittest.main()
