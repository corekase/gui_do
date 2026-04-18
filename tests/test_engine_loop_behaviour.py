import unittest

from gui.utility.events import Event
from gui.utility.engine import Engine
from gui.utility.state_manager import StateManager


class DummyEvent:
    def __init__(self, event_type: Event, **kwargs: object) -> None:
        self.type = event_type
        for key, value in kwargs.items():
            setattr(self, key, value)


class RecordingClock:
    def __init__(self) -> None:
        self.calls = []

    def tick(self, fps: int) -> None:
        self.calls.append(fps)


class DummyTimers:
    def __init__(self, calls) -> None:
        self.calls = calls

    def timer_updates(self, now_time: int) -> None:
        self.calls.append(("timers", now_time))


class DummyScheduler:
    def __init__(self, calls) -> None:
        self.calls = calls

    def update(self):
        self.calls.append("scheduler.update")
        return ["task-ok"]

    def event(self, kind, task_id, error_message=None):
        self.calls.append(("scheduler.event", kind.name, task_id, error_message))
        if kind.name == "Finished":
            return DummyEvent(Event.Task, id=task_id, operation=kind)
        return DummyEvent(Event.Task, id=task_id, operation=kind, error=error_message)

    def get_failed_tasks(self):
        self.calls.append("scheduler.get_failed_tasks")
        return [("task-bad", "failure")]


class DummyGui:
    def __init__(self, calls) -> None:
        self.calls = calls
        self.scheduler = DummyScheduler(calls)
        self.timers = DummyTimers(calls)
        self.buffered = True

    def run_preamble(self) -> None:
        self.calls.append("gui.run_preamble")

    def events(self):
        self.calls.append("gui.events")
        return [
            DummyEvent(Event.KeyDown, key=1),
            DummyEvent(Event.KeyUp, key=1),
        ]

    def dispatch_event(self, event) -> None:
        if event.type == Event.Task:
            op = getattr(event, "operation", None)
            op_name = getattr(op, "name", "") if op is not None else ""
            self.calls.append(("gui.dispatch_event", "Task", getattr(event, "id", None), op_name, getattr(event, "error", None)))
            return
        self.calls.append(("gui.dispatch_event", event.type.name))

    def run_postamble(self) -> None:
        self.calls.append("gui.run_postamble")

    def draw_gui(self) -> None:
        self.calls.append("gui.draw_gui")

    def undraw_gui(self) -> None:
        self.calls.append("gui.undraw_gui")


class SingleFrameStateManager(StateManager):
    def __init__(self, gui) -> None:
        super().__init__(mouse_pos_provider=lambda: (0, 0))
        self.gui = gui
        self._entered = False

    def get_active_gui(self):
        if self._entered:
            # Stop after one frame.
            self.is_running = False
            return None
        self._entered = True
        return self.gui


class EngineLoopBehaviourTests(unittest.TestCase):
    def test_single_frame_orders_callbacks_and_dispatches_task_events(self) -> None:
        calls = []
        gui = DummyGui(calls)
        state = SingleFrameStateManager(gui)
        clock = RecordingClock()
        flips = []
        quits = []
        exits = []

        engine = Engine(
            state,
            fps=144,
            clock=clock,
            ticks_provider=lambda: 321,
            display_flip=lambda: flips.append(True),
            quit_callable=lambda: quits.append(True),
            exit_callable=lambda code: exits.append(code),
            exit_on_finish=False,
        )

        engine.run()

        self.assertEqual(quits, [True])
        self.assertEqual(exits, [])
        self.assertEqual(flips, [True])
        self.assertEqual(clock.calls, [144])

        expected_order = [
            "gui.run_preamble",
            ("timers", 321),
            "gui.events",
            ("gui.dispatch_event", "KeyDown"),
            ("gui.dispatch_event", "KeyUp"),
            "scheduler.update",
            ("scheduler.event", "Finished", "task-ok", None),
            ("gui.dispatch_event", "Task", "task-ok", "Finished", None),
            "scheduler.get_failed_tasks",
            ("scheduler.event", "Failed", "task-bad", "failure"),
            ("gui.dispatch_event", "Task", "task-bad", "Failed", "failure"),
            "gui.run_postamble",
            "gui.draw_gui",
            "gui.undraw_gui",
        ]
        self.assertEqual(calls, expected_order)


if __name__ == "__main__":
    unittest.main()
