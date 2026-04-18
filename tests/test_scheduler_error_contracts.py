import unittest

from gui.utility.events import GuiError
from gui.utility.scheduler import Scheduler, Task, TaskKind


class SchedulerGuiStub:
    pass


class SchedulerErrorContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.scheduler = Scheduler(SchedulerGuiStub())

    def tearDown(self) -> None:
        self.scheduler.shutdown()

    def test_send_message_rejects_unknown_task_id(self) -> None:
        with self.assertRaises(GuiError):
            self.scheduler.send_message("missing", "payload")

    def test_send_message_rejects_task_without_message_handler(self) -> None:
        self.scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method=None,
            generation=1,
        )

        with self.assertRaises(GuiError):
            self.scheduler.send_message("task", "payload")

    def test_send_message_rejects_non_callable_message_handler(self) -> None:
        self.scheduler.tasks["task"] = Task(
            id="task",
            run_callable=lambda: None,
            message_method="not-callable",  # type: ignore[arg-type]
            generation=1,
        )

        with self.assertRaises(GuiError):
            self.scheduler.send_message("task", "payload")

    def test_limit_setters_reject_non_int_non_none_values(self) -> None:
        with self.assertRaises(GuiError):
            self.scheduler.set_message_ingest_limit("1")  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            self.scheduler.set_message_dispatch_limit("1")  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            self.scheduler.set_max_queued_messages_per_task("1")  # type: ignore[arg-type]

    def test_event_rejects_unhashable_task_id_when_provided(self) -> None:
        with self.assertRaises(GuiError):
            self.scheduler.event(operation=TaskKind.Finished, item1=[])  # type: ignore[arg-type]

    def test_add_task_rejects_invalid_message_method(self) -> None:
        with self.assertRaises(GuiError):
            self.scheduler.add_task("t", lambda task_id: None, message_method="bad")  # type: ignore[arg-type]

    def test_remove_tasks_rejects_unhashable_id(self) -> None:
        with self.assertRaises(GuiError):
            self.scheduler.remove_tasks([])  # type: ignore[arg-type]


if __name__ == "__main__":
    unittest.main()
