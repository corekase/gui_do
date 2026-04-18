import unittest

from gui.utility.scheduler import Timers
from gui.utility.statemanager import StateManager
from gui.utility.guimanager import GuiManager


class SchedulerStub:
    def __init__(self, fail: bool = False) -> None:
        self.fail = fail
        self.shutdown_calls = 0

    def shutdown(self) -> None:
        self.shutdown_calls += 1
        if self.fail:
            raise RuntimeError("shutdown failed")


class GuiStubFactory:
    @staticmethod
    def build(mouse_pos=(0, 0), fail_shutdown: bool = False):
        gui = GuiManager.__new__(GuiManager)
        gui._scheduler = SchedulerStub(fail=fail_shutdown)
        gui._mouse_pos = mouse_pos
        gui.set_calls = []

        def get_mouse_pos():
            return gui._mouse_pos

        def set_mouse_pos(pos, update_physical_coords=True):
            gui._mouse_pos = pos
            gui.set_calls.append((pos, update_physical_coords))

        gui.get_mouse_pos = get_mouse_pos
        gui.set_mouse_pos = set_mouse_pos
        return gui


class TimersTests(unittest.TestCase):
    def test_timer_accumulates_elapsed_before_firing(self) -> None:
        timers = Timers()
        fired = []

        timers.add_timer("tick", 10, lambda: fired.append(True))
        timers.timer_updates(100)
        timers.timer_updates(105)
        timers.timer_updates(116)

        self.assertEqual(len(fired), 1)

    def test_timer_can_fire_multiple_times_in_one_update(self) -> None:
        timers = Timers()
        fired = []

        timers.add_timer("tick", 10, lambda: fired.append(True))
        timers.timer_updates(0)
        timers.timer_updates(35)

        self.assertEqual(len(fired), 3)

    def test_timer_callback_can_remove_own_timer(self) -> None:
        timers = Timers()
        fired = []

        def callback() -> None:
            fired.append(True)
            timers.remove_timer("self")

        timers.add_timer("self", 10, callback)
        timers.timer_updates(0)
        timers.timer_updates(25)

        self.assertEqual(len(fired), 1)
        self.assertNotIn("self", timers.timers)


class StateManagerLifecycleTests(unittest.TestCase):
    def test_switch_context_carries_mouse_from_previous_context(self) -> None:
        manager = StateManager(mouse_pos_provider=lambda: (99, 88))
        old_gui = GuiStubFactory.build(mouse_pos=(12, 34))
        new_gui = GuiStubFactory.build(mouse_pos=(0, 0))

        manager.register_context("old", old_gui)
        manager.register_context("new", new_gui)

        manager.switch_context("old")
        old_gui._mouse_pos = (12, 34)
        manager.switch_context("new")

        self.assertEqual(new_gui._mouse_pos, (12, 34))
        self.assertEqual(new_gui.set_calls[-1], ((12, 34), True))

    def test_exit_shuts_down_all_contexts_even_if_one_fails(self) -> None:
        manager = StateManager(mouse_pos_provider=lambda: (0, 0))
        gui_ok = GuiStubFactory.build(fail_shutdown=False)
        gui_fail = GuiStubFactory.build(fail_shutdown=True)

        manager.register_context("ok", gui_ok)
        manager.register_context("fail", gui_fail)

        with self.assertLogs("gui.utility.statemanager", level="WARNING") as captured:
            manager.__exit__(None, None, None)

        self.assertEqual(gui_ok._scheduler.shutdown_calls, 1)
        self.assertEqual(gui_fail._scheduler.shutdown_calls, 1)
        self.assertEqual(manager.is_running, False)
        self.assertTrue(any('context "fail"' in message for message in captured.output))
        self.assertTrue(any('shutdown failed' in message for message in captured.output))


if __name__ == "__main__":
    unittest.main()
