import threading
import unittest

from gui.utility.events import GuiError
from gui.utility.scheduler import Scheduler, Task


class SchedulerGuiStub:
    pass


class SchedulerBackpressureInterleavingsBatch7Tests(unittest.TestCase):
    def setUp(self) -> None:
        self.scheduler = Scheduler(SchedulerGuiStub())

    def tearDown(self) -> None:
        self.scheduler.shutdown()

    def test_waiting_sender_wakes_and_fails_when_task_removed(self) -> None:
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
        finished = threading.Event()
        errors = []

        def producer() -> None:
            started.set()
            try:
                self.scheduler.send_message("task", "second")
            except Exception as exc:
                errors.append(exc)
            finally:
                finished.set()

        worker = threading.Thread(target=producer)
        worker.start()

        self.assertTrue(started.wait(timeout=1.0))
        self.assertFalse(finished.wait(timeout=0.05))

        self.scheduler.remove_tasks("task")

        self.assertTrue(finished.wait(timeout=1.0))
        worker.join(timeout=1.0)

        self.assertEqual(len(errors), 1)
        self.assertIsInstance(errors[0], GuiError)
        self.assertIn('unknown task id: task', str(errors[0]))

        self.scheduler._drain_incoming_task_messages()
        self.scheduler._dispatch_task_messages()
        self.assertEqual(observed, [])

    def test_waiting_sender_targets_new_generation_after_remove_and_readd(self) -> None:
        observed_new = []

        self.scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=lambda _payload: None,
            generation=1,
        )
        self.scheduler._task_generation["task"] = 1
        self.scheduler.set_max_queued_messages_per_task(1)
        self.scheduler.send_message("task", "old")

        started = threading.Event()
        finished = threading.Event()
        errors = []

        def producer() -> None:
            started.set()
            try:
                self.scheduler.send_message("task", "new")
            except Exception as exc:
                errors.append(exc)
            finally:
                finished.set()

        worker = threading.Thread(target=producer)
        worker.start()
        self.assertTrue(started.wait(timeout=1.0))
        self.assertFalse(finished.wait(timeout=0.05))

        with self.scheduler._lock:
            self.scheduler.remove_tasks("task")
            self.scheduler.add_task("task", lambda _task_id: None, message_method=lambda payload: observed_new.append(payload))

        self.assertTrue(finished.wait(timeout=1.0))
        worker.join(timeout=1.0)

        self.assertEqual(errors, [])

        self.scheduler._drain_incoming_task_messages()
        self.scheduler._dispatch_task_messages()

        self.assertEqual(observed_new, ["new"])
        self.assertIsNone(self.scheduler._task_message_counts.get("task"))


if __name__ == "__main__":
    unittest.main()
