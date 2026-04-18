import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pygame
from pygame import Rect
from pygame.locals import MOUSEBUTTONDOWN, MOUSEBUTTONUP

from gui.utility.events import ButtonStyle, GuiError, InteractiveState
from gui.widgets.arrowbox import ArrowBox
from gui.widgets.button import Button
from gui.widgets.frame import Frame
from gui.widgets.image import Image


class TimersSpy:
    def __init__(self) -> None:
        self.add_calls = []
        self.remove_calls = []

    def add_timer(self, timer_id, repeat_ms, callback):
        self.add_calls.append((timer_id, repeat_ms, callback))

    def remove_timer(self, timer_id):
        self.remove_calls.append(timer_id)


class SurfaceSpy:
    def __init__(self) -> None:
        self.blit_calls = []

    def blit(self, bitmap, pos):
        self.blit_calls.append((bitmap, pos))


def build_interactive_gui_stub():
    gui = SimpleNamespace()
    gui.get_mouse_pos = lambda: (5, 5)
    gui.convert_to_window = lambda point, _window: point
    gui.timers = TimersSpy()
    gui.graphics_factory = SimpleNamespace()
    return gui


class WidgetConstructorAndStateContractTests(unittest.TestCase):
    def test_arrowbox_rejects_invalid_repeat_interval(self) -> None:
        gui = build_interactive_gui_stub()
        gui.graphics_factory.draw_arrow_state_bitmaps = lambda rect, direction: (object(), object(), object())

        with self.assertRaises(GuiError):
            ArrowBox(gui, "a", Rect(0, 0, 10, 10), 0, repeat_activation_ms="bad")  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            ArrowBox(gui, "a", Rect(0, 0, 10, 10), 0, repeat_activation_ms=0)

    def test_arrowbox_press_adds_repeat_timer_and_release_clears_it(self) -> None:
        gui = build_interactive_gui_stub()
        gui.graphics_factory.draw_arrow_state_bitmaps = lambda rect, direction: (object(), object(), object())
        activated = []

        arrow = ArrowBox(gui, "arrow", Rect(0, 0, 10, 10), 0, on_activate=lambda: activated.append(True), repeat_activation_ms=50)

        down = pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1})
        result_down = arrow.handle_event(down, None)

        self.assertTrue(result_down)
        self.assertEqual(arrow.state, InteractiveState.Armed)
        self.assertEqual(len(gui.timers.add_calls), 1)
        self.assertEqual(gui.timers.add_calls[0][0], "arrow.timer")
        self.assertEqual(gui.timers.add_calls[0][1], 50)

        up = pygame.event.Event(MOUSEBUTTONUP, {"button": 1})
        result_up = arrow.handle_event(up, None)

        self.assertFalse(result_up)
        self.assertEqual(arrow.state, InteractiveState.Hover)
        self.assertEqual(gui.timers.remove_calls, ["arrow.timer"])
        self.assertEqual(activated, [])

    def test_arrowbox_destructor_tolerates_partial_initialization(self) -> None:
        # Simulate constructor failure before attributes like _timer_id are assigned.
        arrow = ArrowBox.__new__(ArrowBox)

        ArrowBox.__del__(arrow)

    def test_button_state_machine_and_activation_contract(self) -> None:
        gui = build_interactive_gui_stub()
        gui.graphics_factory.build_interactive_visuals = lambda style, text, rect: SimpleNamespace(
            idle=object(), hover=object(), armed=object(), hit_rect=Rect(rect)
        )

        button = Button(gui, "b", Rect(0, 0, 20, 10), ButtonStyle.Box, "txt", on_activate=None)

        down = pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1})
        up = pygame.event.Event(MOUSEBUTTONUP, {"button": 1})

        self.assertFalse(button.handle_event(down, None))
        self.assertEqual(button.state, InteractiveState.Armed)
        self.assertTrue(button.handle_event(up, None))
        self.assertEqual(button.state, InteractiveState.Hover)

        callback_button = Button(gui, "b2", Rect(0, 0, 20, 10), ButtonStyle.Box, "txt", on_activate=lambda: None)
        callback_button.handle_event(down, None)
        self.assertFalse(callback_button.handle_event(up, None))

    def test_image_rejects_empty_name_and_wraps_load_failure(self) -> None:
        gui = SimpleNamespace()
        gui.graphics_factory = SimpleNamespace(file_resource=lambda *parts: "D:/Code/gui_do/data/images/missing.png")

        with self.assertRaises(GuiError):
            Image(gui, "img", Rect(0, 0, 10, 10), "")

        with patch("pygame.image.load", side_effect=RuntimeError("boom")):
            with self.assertRaises(GuiError) as ctx:
                Image(gui, "img", Rect(0, 0, 10, 10), "missing.png", scale=False)

        self.assertIn("failed to load widget image", str(ctx.exception))

    def test_frame_draw_uses_bitmap_for_current_state(self) -> None:
        idle = object()
        hover = object()
        armed = object()

        gui = SimpleNamespace()
        gui.graphics_factory = SimpleNamespace(
            build_frame_visuals=lambda rect: SimpleNamespace(idle=idle, hover=hover, armed=armed, hit_rect=Rect(rect))
        )

        frame = Frame(gui, "frame", Rect(1, 2, 10, 10))
        frame.surface = SurfaceSpy()

        frame.state = InteractiveState.Idle
        frame.draw()
        frame.state = InteractiveState.Hover
        frame.draw()
        frame.state = InteractiveState.Armed
        frame.draw()

        self.assertEqual(
            frame.surface.blit_calls,
            [
                (idle, (1, 2)),
                (hover, (1, 2)),
                (armed, (1, 2)),
            ],
        )


if __name__ == "__main__":
    unittest.main()
