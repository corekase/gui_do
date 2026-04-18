import unittest

import pygame

from gui_manager_test_factory import build_state_manager_stub
from gui.utility.constants import Event
from gui.utility.guimanager import GuiManager
from gui.utility.statemanager import StateManager


class DummyBitmapFactory:
    def load_font(self, name: str, filename: str, size: int) -> None:
        return None


class DummyScheduler:
    def shutdown(self) -> None:
        return None


def make_minimal_gui_stub(mouse_position=(0, 0)):
    gui = build_state_manager_stub()
    gui._scheduler = DummyScheduler()
    gui._mouse_pos = mouse_position
    return gui


class InputProviderAbstractionTests(unittest.TestCase):
    def test_state_manager_uses_injected_mouse_provider(self) -> None:
        provider_calls = []

        def provider():
            provider_calls.append(True)
            return (9, 7)

        state = StateManager(mouse_pos_provider=provider)
        old_gui = make_minimal_gui_stub(mouse_position=(1, 2))
        new_gui = make_minimal_gui_stub(mouse_position=(0, 0))

        state.register_context("old", old_gui, replace=False)
        state.switch_context("old")
        # Simulate no active context on next switch so provider is used.
        state._active_context_name = None

        state.register_context("new", new_gui, replace=False)
        state.switch_context("new")

        self.assertEqual(provider_calls, [True, True])
        self.assertEqual(new_gui._mouse_pos, (9, 7))

    def test_gui_manager_uses_injected_input_providers(self) -> None:
        visible_calls = []
        mouse_set_calls = []

        queue = [object(), object()]

        def event_getter():
            return list(queue)

        gui = GuiManager(
            surface=pygame.Surface((100, 80)),
            fonts=[("normal", "ignored.ttf", 12)],
            bitmap_factory=DummyBitmapFactory(),
            task_panel_enabled=False,
            event_getter=event_getter,
            mouse_get_pos=lambda: (11, 13),
            mouse_set_pos=lambda pos: mouse_set_calls.append(pos),
            mouse_set_visible=lambda visible: visible_calls.append(visible),
        )

        self.assertEqual(gui.mouse_pos, (11, 13))
        self.assertEqual(visible_calls, [False])

        calls = []

        def fake_handle_event(_event):
            calls.append(True)
            if len(calls) == 1:
                return gui.event(Event.Pass)
            return gui.event(Event.KeyDown, key=3)

        gui.handle_event = fake_handle_event  # type: ignore[assignment]

        events = list(gui.events())

        self.assertEqual(len(events), 1)
        self.assertEqual(events[0].type, Event.KeyDown)

        gui._set_physical_mouse_pos((4, 5))
        self.assertEqual(mouse_set_calls, [(4, 5)])


if __name__ == "__main__":
    unittest.main()
