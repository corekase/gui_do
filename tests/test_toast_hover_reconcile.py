import unittest

import pygame
from pygame import Rect

from gui_do.app.gui_application import GuiApplication
from gui_do.controls.input.button_control import ButtonControl
from gui_do.events.gui_event import EventType, GuiEvent


pygame.init()


class _StubToastFont:
    point_size = 18

    @staticmethod
    def text_size(text):
        return (max(8, len(str(text)) * 8), 18)


class _StubToastFonts:
    def font_instance(self, *_args, **_kwargs):
        return _StubToastFont()


class _StubToastTheme:
    fonts = _StubToastFonts()


class TestToastHoverReconcile(unittest.TestCase):
    def test_entering_toast_clears_underlying_hover_state(self):
        app = GuiApplication(pygame.Surface((320, 240)))
        app.theme = _StubToastTheme()
        button = ButtonControl("btn", Rect(0, 0, 320, 240), "Hover")
        app.scene.add(button)
        app.toasts.show_persistent("toast")

        move_over_control = GuiEvent(
            kind=EventType.MOUSE_MOTION,
            type=pygame.MOUSEMOTION,
            pos=(8, 8),
            rel=(0, 0),
        )
        app.process_event(move_over_control)
        self.assertTrue(button.hovered)

        move_into_toast = GuiEvent(
            kind=EventType.MOUSE_MOTION,
            type=pygame.MOUSEMOTION,
            pos=(300, 220),
            rel=(0, 0),
        )
        consumed = app.process_event(move_into_toast)

        self.assertTrue(consumed)
        self.assertFalse(button.hovered)


if __name__ == "__main__":
    unittest.main()
