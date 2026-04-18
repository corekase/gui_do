import unittest
from types import SimpleNamespace

from gui.utility.engine import Engine
from gui.utility.scheduler import TaskKind
from gui.utility.statemanager import StateManager


class TimersStub:
    def __init__(self, log, owner_name: str) -> None:
        self.log = log
        self.owner_name = owner_name

    def timer_updates(self, ticks: int) -> None:
        self.log.append((self.owner_name, "timers", ticks))


class SchedulerStub:
    def __init__(self, owner_name: str, finished_ids=None, failed_items=None, log=None) -> None:
        self.owner_name = owner_name
        self.finished_ids = [] if finished_ids is None else list(finished_ids)
        self.failed_items = [] if failed_items is None else list(failed_items)
        self.log = [] if log is None else log

    def update(self):
        self.log.append((self.owner_name, "scheduler.update"))
        values = list(self.finished_ids)
        self.finished_ids.clear()
        return values

    def get_failed_tasks(self):
        self.log.append((self.owner_name, "scheduler.failed"))
        values = list(self.failed_items)
        self.failed_items.clear()
        return values

    def event(self, kind, task_id, error_message=None):
        return SimpleNamespace(type="Task", kind=kind, id=task_id, error=error_message)


class ScriptedGui:
    def __init__(self, name: str, state_manager, log, events, scheduler: SchedulerStub) -> None:
        self.name = name
        self.state_manager = state_manager
        self.log = log
        self._events = list(events)
        self.scheduler = scheduler
        self.timers = TimersStub(log, name)
        self.buffered = True

    def run_preamble(self):
        self.log.append((self.name, "preamble"))

    def events(self):
        self.log.append((self.name, "events"))
        events = list(self._events)
        self._events.clear()
        return events

    def dispatch_event(self, event):
        self.log.append((self.name, "dispatch", getattr(event, "type", None), getattr(event, "id", None)))
        if getattr(event, "type", None) == "Switch":
            self.state_manager.set_active("second")
        if getattr(event, "type", None) == "Quit":
            self.state_manager.set_running(False)

    def run_postamble(self):
        self.log.append((self.name, "postamble"))

    def draw_gui(self):
        self.log.append((self.name, "draw"))

    def undraw_gui(self):
        self.log.append((self.name, "undraw"))


class ScriptedStateManager(StateManager):
    def __init__(self):
        super().__init__(mouse_pos_provider=lambda: (0, 0))
        self._guis = {}
        self._active_key = None

    def add_gui(self, key: str, gui) -> None:
        self._guis[key] = gui

    def set_active(self, key: str) -> None:
        self._active_key = key

    def get_active_gui(self):
        if self._active_key is None:
            return None
        return self._guis[self._active_key]


class IntegrationFrameSequenceTests(unittest.TestCase):
    def test_engine_processes_two_contexts_via_runtime_switch(self) -> None:
        log = []
        state = ScriptedStateManager()

        first_scheduler = SchedulerStub("first", log=log)
        second_scheduler = SchedulerStub("second", log=log)

        first_gui = ScriptedGui(
            name="first",
            state_manager=state,
            log=log,
            events=[SimpleNamespace(type="Switch")],
            scheduler=first_scheduler,
        )
        second_gui = ScriptedGui(
            name="second",
            state_manager=state,
            log=log,
            events=[SimpleNamespace(type="Quit")],
            scheduler=second_scheduler,
        )

        state.add_gui("first", first_gui)
        state.add_gui("second", second_gui)
        state.set_active("first")

        flips = []
        ticks = [100, 200]

        engine = Engine(
            state,
            fps=60,
            clock=SimpleNamespace(tick=lambda fps: log.append(("engine", "tick", fps))),
            ticks_provider=lambda: ticks.pop(0),
            display_flip=lambda: flips.append(True),
            quit_callable=lambda: log.append(("engine", "quit")),
            exit_callable=lambda code: log.append(("engine", "exit", code)),
            exit_on_finish=False,
        )

        engine.run()

        self.assertEqual(len(flips), 2)
        self.assertIn(("first", "dispatch", "Switch", None), log)
        self.assertIn(("second", "dispatch", "Quit", None), log)
        self.assertIn(("engine", "quit"), log)

    def test_engine_dispatches_scheduler_finished_and_failed_events(self) -> None:
        log = []
        state = ScriptedStateManager()

        scheduler = SchedulerStub(
            "main",
            finished_ids=["done-task"],
            failed_items=[("failed-task", "boom")],
            log=log,
        )
        gui = ScriptedGui(
            name="main",
            state_manager=state,
            log=log,
            events=[SimpleNamespace(type="Quit")],
            scheduler=scheduler,
        )

        state.add_gui("main", gui)
        state.set_active("main")

        engine = Engine(
            state,
            clock=SimpleNamespace(tick=lambda fps: None),
            ticks_provider=lambda: 123,
            display_flip=lambda: None,
            quit_callable=lambda: None,
            exit_on_finish=False,
        )

        engine.run()

        self.assertIn(("main", "dispatch", "Task", "done-task"), log)
        self.assertIn(("main", "dispatch", "Task", "failed-task"), log)


if __name__ == "__main__":
    unittest.main()
