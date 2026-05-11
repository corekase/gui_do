import unittest

import pygame
from pygame import Rect

from gui_do.app.scene import Scene
from gui_do.controls.input.chip_input_control import ChipInputControl
from gui_do.events.gui_event import EventType, GuiEvent
from gui_do.focus.focus_manager import FocusManager


pygame.init()


class _StubApp:
    def __init__(self, scene=None):
        self.scene = Scene() if scene is None else scene
        self.theme = None


class TestChipInputControlKeyboard(unittest.TestCase):
    def _focused_chip_input(self) -> ChipInputControl:
        control = ChipInputControl("chips", Rect(0, 0, 300, 36))
        control._focused = True
        return control

    def test_text_input_not_doubled_after_keydown(self):
        control = self._focused_chip_input()
        app = _StubApp()

        keydown = GuiEvent(
            kind=EventType.KEY_DOWN,
            type=pygame.KEYDOWN,
            key=pygame.K_a,
            mod=0,
        )
        keydown.source_event = type("_Source", (), {"unicode": "a"})()
        text_input = GuiEvent(
            kind=EventType.TEXT_INPUT,
            type=pygame.TEXTINPUT,
            text="a",
        )

        self.assertFalse(control.handle_event(keydown, app))
        self.assertTrue(control.handle_event(text_input, app))
        self.assertEqual("a", control.edit_text)

    def test_focus_manager_routes_main_enter_to_chip_input(self):
        scene = Scene()
        control = ChipInputControl("chips", Rect(0, 0, 300, 36))
        scene.add(control)
        control._edit_text = "alpha"

        app = _StubApp(scene=scene)
        focus = FocusManager()
        app.focus = focus
        focus.set_focus(control)

        event = GuiEvent(
            kind=EventType.KEY_DOWN,
            type=pygame.KEYDOWN,
            key=pygame.K_RETURN,
            mod=0,
        )

        self.assertTrue(focus.route_key_event(event, app))
        self.assertEqual(["alpha"], control.values)
        self.assertEqual("", control.edit_text)

    def test_main_enter_commits_edit_text(self):
        control = self._focused_chip_input()
        app = _StubApp()
        control._edit_text = "alpha"

        event = GuiEvent(
            kind=EventType.KEY_DOWN,
            type=pygame.KEYDOWN,
            key=pygame.K_RETURN,
            mod=0,
        )

        self.assertTrue(control.handle_event(event, app))
        self.assertEqual(["alpha"], control.values)
        self.assertEqual("", control.edit_text)

    def test_numpad_enter_commits_edit_text(self):
        control = self._focused_chip_input()
        app = _StubApp()
        control._edit_text = "beta"

        event = GuiEvent(
            kind=EventType.KEY_DOWN,
            type=pygame.KEYDOWN,
            key=pygame.K_KP_ENTER,
            mod=0,
        )

        self.assertTrue(control.handle_event(event, app))
        self.assertEqual(["beta"], control.values)
        self.assertEqual("", control.edit_text)


if __name__ == "__main__":
    unittest.main()
