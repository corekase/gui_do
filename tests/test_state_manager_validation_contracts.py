import unittest

from gui.utility.guimanager import GuiManager
from gui.utility.statemanager import StateManager


class SchedulerNoopStub:
    def shutdown(self) -> None:
        return None


def build_gui_stub() -> GuiManager:
    gui = GuiManager.__new__(GuiManager)
    gui._scheduler = SchedulerNoopStub()
    gui._mouse_pos = (0, 0)

    def get_mouse_pos():
        return gui._mouse_pos

    def set_mouse_pos(pos, _update_physical_coords=True):
        gui._mouse_pos = pos

    gui.get_mouse_pos = get_mouse_pos
    gui.set_mouse_pos = set_mouse_pos
    return gui


class StateManagerValidationContractTests(unittest.TestCase):
    def test_init_rejects_non_callable_mouse_provider(self) -> None:
        with self.assertRaises(TypeError):
            StateManager(mouse_pos_provider=123)  # type: ignore[arg-type]

    def test_register_context_rejects_invalid_names(self) -> None:
        manager = StateManager(mouse_pos_provider=lambda: (0, 0))
        gui = build_gui_stub()

        with self.assertRaises(ValueError):
            manager.register_context("", gui)
        with self.assertRaises(ValueError):
            manager.register_context(1, gui)  # type: ignore[arg-type]

    def test_register_context_rejects_non_gui_instance(self) -> None:
        manager = StateManager(mouse_pos_provider=lambda: (0, 0))

        with self.assertRaises(TypeError):
            manager.register_context("bad", object())  # type: ignore[arg-type]

    def test_register_context_duplicate_requires_replace_flag(self) -> None:
        manager = StateManager(mouse_pos_provider=lambda: (0, 0))
        gui1 = build_gui_stub()
        gui2 = build_gui_stub()

        manager.register_context("ctx", gui1)
        with self.assertRaises(KeyError):
            manager.register_context("ctx", gui2)

        manager.register_context("ctx", gui2, replace=True)
        manager.switch_context("ctx")
        self.assertIs(manager.get_active_gui(), gui2)

    def test_switch_context_rejects_invalid_and_unknown_names(self) -> None:
        manager = StateManager(mouse_pos_provider=lambda: (0, 0))
        manager.register_context("ctx", build_gui_stub())

        with self.assertRaises(ValueError):
            manager.switch_context(1)  # type: ignore[arg-type]
        with self.assertRaises(ValueError):
            manager.switch_context("")
        with self.assertRaises(KeyError):
            manager.switch_context("missing")

    def test_set_running_rejects_non_bool_values(self) -> None:
        manager = StateManager(mouse_pos_provider=lambda: (0, 0))

        with self.assertRaises(TypeError):
            manager.set_running("yes")  # type: ignore[arg-type]

    def test_get_active_gui_returns_none_for_missing_active_name(self) -> None:
        manager = StateManager(mouse_pos_provider=lambda: (0, 0))
        manager._active_context_name = "missing"

        self.assertIsNone(manager.get_active_gui())

    def test_exit_with_no_contexts_still_sets_not_running(self) -> None:
        manager = StateManager(mouse_pos_provider=lambda: (0, 0))
        manager.__enter__()

        manager.__exit__(None, None, None)

        self.assertFalse(manager.is_running)


if __name__ == "__main__":
    unittest.main()
