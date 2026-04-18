import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pygame
from pygame import Rect
from pygame.locals import MOUSEBUTTONDOWN

from gui.utility.constants import ButtonStyle, InteractiveState
from gui.widgets.arrowbox import ArrowBox
from gui.widgets.button import Button
from gui.widgets.image import Image


class TimersSpy:
    def __init__(self) -> None:
        self.add_calls = []
        self.remove_calls = []

    def add_timer(self, timer_id, repeat_ms, callback):
        self.add_calls.append((timer_id, repeat_ms, callback))

    def remove_timer(self, timer_id):
        self.remove_calls.append(timer_id)


def build_interactive_gui_stub():
    gui = SimpleNamespace()
    gui.get_mouse_pos = lambda: (5, 5)
    gui.convert_to_window = lambda point, _window: point
    gui.timers = TimersSpy()
    gui.bitmap_factory = SimpleNamespace()
    return gui


class WidgetInteractionsBatch3Tests(unittest.TestCase):
    def test_arrowbox_leave_clears_timer_and_resets_idle(self) -> None:
        gui = build_interactive_gui_stub()
        gui.bitmap_factory.draw_arrow_state_bitmaps = lambda rect, direction: (object(), object(), object())
        arrow = ArrowBox(gui, "arrow", Rect(0, 0, 10, 10), 0, on_activate=lambda: None, repeat_activation_ms=50)

        down = pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1})
        self.assertTrue(arrow.handle_event(down, None))
        self.assertEqual(arrow.state, InteractiveState.Armed)

        arrow.leave()

        self.assertEqual(arrow.state, InteractiveState.Idle)
        self.assertEqual(gui.timers.remove_calls, ["arrow.timer"])

    def test_arrowbox_invoke_on_activate_noop_without_callback(self) -> None:
        gui = build_interactive_gui_stub()
        gui.bitmap_factory.draw_arrow_state_bitmaps = lambda rect, direction: (object(), object(), object())
        arrow = ArrowBox(gui, "arrow", Rect(0, 0, 10, 10), 0, on_activate=None, repeat_activation_ms=50)

        arrow._invoke_on_activate()

        self.assertEqual(gui.timers.add_calls, [])

    def test_button_leave_resets_state_to_idle(self) -> None:
        gui = build_interactive_gui_stub()
        gui.bitmap_factory.get_styled_bitmaps = lambda style, text, rect: ((object(), object(), object()), Rect(rect))
        button = Button(gui, "b", Rect(0, 0, 20, 10), ButtonStyle.Box, "txt", on_activate=None)
        button.state = InteractiveState.Armed

        button.leave()

        self.assertEqual(button.state, InteractiveState.Idle)

    def test_buttongroup_select_resets_previous_selection(self) -> None:
        previous = SimpleNamespace(state=InteractiveState.Armed)
        selected = {"value": previous}

        mediator = SimpleNamespace(
            get_selection=lambda _group: selected["value"],
            select=lambda _group, button: selected.__setitem__("value", button),
        )

        button = SimpleNamespace(
            group="grp",
            state=InteractiveState.Idle,
            gui=SimpleNamespace(button_group_mediator=mediator),
        )

        from gui.widgets.buttongroup import ButtonGroup

        ButtonGroup.select(button)

        self.assertEqual(previous.state, InteractiveState.Idle)
        self.assertEqual(button.state, InteractiveState.Armed)
        self.assertIs(selected["value"], button)

    def test_image_scales_when_enabled_and_skips_when_disabled(self) -> None:
        gui = SimpleNamespace()
        gui.bitmap_factory = SimpleNamespace(file_resource=lambda *parts: "D:/Code/gui_do/data/images/test.png")
        base_surface = pygame.Surface((4, 4))

        with patch("pygame.image.load", return_value=base_surface), patch(
            "pygame.transform.smoothscale", return_value=pygame.Surface((10, 8))
        ) as smoothscale:
            image = Image(gui, "img", Rect(0, 0, 10, 8), "test.png", scale=True)
            self.assertEqual(image._image.get_size(), (10, 8))
            smoothscale.assert_called_once()

        with patch("pygame.image.load", return_value=base_surface), patch(
            "pygame.transform.smoothscale", return_value=pygame.Surface((10, 8))
        ) as smoothscale:
            image = Image(gui, "img2", Rect(0, 0, 10, 8), "test.png", scale=False)
            self.assertEqual(image._image.get_size(), (4, 4))
            smoothscale.assert_not_called()


if __name__ == "__main__":
    unittest.main()
