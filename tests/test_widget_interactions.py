import unittest
from types import SimpleNamespace
from unittest.mock import patch

import pygame
from pygame import Rect
from pygame.locals import MOUSEBUTTONDOWN
from pygame.locals import MOUSEBUTTONUP
from pygame.locals import MOUSEMOTION

from gui.utility.events import ButtonStyle, InteractiveState
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


class FailingTimersSpy(TimersSpy):
    def remove_timer(self, timer_id):
        super().remove_timer(timer_id)
        raise RuntimeError("remove failed")


def build_interactive_gui_stub():
    gui = SimpleNamespace()
    gui.get_mouse_pos = lambda: (5, 5)
    gui._get_mouse_pos = lambda: (5, 5)
    gui.convert_to_window = lambda point, _window: point
    gui._convert_to_window = lambda point, _window: point
    gui.timers = TimersSpy()
    gui.graphics_factory = SimpleNamespace(
        build_arrow_visuals=lambda rect, _direction: SimpleNamespace(
            idle=object(),
            hover=object(),
            armed=object(),
            disabled=object(),
            hit_rect=Rect(rect),
        )
    )
    return gui


def build_interactive_gui_stub_with_failing_timers():
    gui = SimpleNamespace()
    gui.get_mouse_pos = lambda: (5, 5)
    gui._get_mouse_pos = lambda: (5, 5)
    gui.convert_to_window = lambda point, _window: point
    gui._convert_to_window = lambda point, _window: point
    gui.timers = FailingTimersSpy()
    gui.graphics_factory = SimpleNamespace(
        build_arrow_visuals=lambda rect, _direction: SimpleNamespace(
            idle=object(),
            hover=object(),
            armed=object(),
            disabled=object(),
            hit_rect=Rect(rect),
        )
    )
    return gui


class WidgetInteractionsBatch3Tests(unittest.TestCase):
    def test_arrowbox_leave_clears_timer_and_resets_idle(self) -> None:
        gui = build_interactive_gui_stub()
        arrow = ArrowBox(gui, "arrow", Rect(0, 0, 10, 10), 0, on_activate=lambda: None, repeat_activation_ms=50)

        down = pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1})
        self.assertTrue(arrow.handle_event(down, None))
        self.assertEqual(arrow.state, InteractiveState.Armed)

        arrow.leave()

        self.assertEqual(arrow.state, InteractiveState.Idle)
        self.assertEqual(gui.timers.remove_calls, ["arrow.timer"])

    def test_arrowbox_invoke_on_activate_noop_without_callback(self) -> None:
        gui = build_interactive_gui_stub()
        arrow = ArrowBox(gui, "arrow", Rect(0, 0, 10, 10), 0, on_activate=None, repeat_activation_ms=50)

        arrow._invoke_on_activate()

        self.assertEqual(gui.timers.add_calls, [])

    def test_arrowbox_leave_logs_warning_when_timer_remove_fails(self) -> None:
        gui = build_interactive_gui_stub_with_failing_timers()
        arrow = ArrowBox(gui, "arrow", Rect(0, 0, 10, 10), 0, on_activate=lambda: None, repeat_activation_ms=50)

        down = pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1})
        self.assertTrue(arrow.handle_event(down, None))

        with self.assertLogs("gui.widgets.arrowbox", level="WARNING") as logs:
            arrow.leave()

        self.assertEqual(arrow.state, InteractiveState.Idle)
        self.assertIsNone(arrow._timer_id)
        self.assertTrue(any("timer cleanup failed" in line for line in logs.output))

    def test_arrowbox_ignores_non_mouse_events(self) -> None:
        gui = build_interactive_gui_stub()
        arrow = ArrowBox(gui, "arrow", Rect(0, 0, 10, 10), 0, on_activate=None, repeat_activation_ms=50)

        other = pygame.event.Event(pygame.USEREVENT, {})
        self.assertFalse(arrow.handle_event(other, None))

    def test_arrowbox_motion_outside_clears_repeat_timer(self) -> None:
        gui = build_interactive_gui_stub()
        arrow = ArrowBox(gui, "arrow", Rect(0, 0, 10, 10), 0, on_activate=lambda: None, repeat_activation_ms=50)

        down = pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1})
        self.assertTrue(arrow.handle_event(down, None))
        self.assertEqual(arrow.state, InteractiveState.Armed)

        gui.get_mouse_pos = lambda: (50, 50)
        gui._get_mouse_pos = gui.get_mouse_pos
        motion = pygame.event.Event(MOUSEMOTION, {"rel": (1, 1)})
        self.assertFalse(arrow.handle_event(motion, None))
        self.assertIsNone(arrow._timer_id)
        self.assertEqual(gui.timers.remove_calls, ["arrow.timer"])

    def test_arrowbox_press_without_callback_does_not_register_timer(self) -> None:
        gui = build_interactive_gui_stub()
        arrow = ArrowBox(gui, "arrow", Rect(0, 0, 10, 10), 0, on_activate=None, repeat_activation_ms=50)

        down = pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1})
        self.assertTrue(arrow.handle_event(down, None))
        self.assertEqual(gui.timers.add_calls, [])

    def test_arrowbox_outside_collision_and_callback_invoke_paths(self) -> None:
        gui = build_interactive_gui_stub()
        calls = []
        arrow = ArrowBox(gui, "arrow", Rect(0, 0, 10, 10), 0, on_activate=lambda: calls.append(True), repeat_activation_ms=50)

        self.assertFalse(arrow.should_handle_outside_collision())
        arrow.state = InteractiveState.Armed
        self.assertTrue(arrow.should_handle_outside_collision())
        arrow._invoke_on_activate()
        self.assertEqual(calls, [True])

    def test_arrowbox_clear_timer_is_noop_when_timers_absent(self) -> None:
        gui = build_interactive_gui_stub()
        arrow = ArrowBox(gui, "arrow", Rect(0, 0, 10, 10), 0, on_activate=None, repeat_activation_ms=50)
        arrow._timer_id = "arrow.timer"
        arrow.gui = SimpleNamespace(timers=None)

        arrow._clear_timer()

        self.assertIsNone(arrow._timer_id)

    def test_arrowbox_destructor_logs_debug_when_internal_cleanup_raises(self) -> None:
        arrow = ArrowBox.__new__(ArrowBox)

        def _raise() -> None:
            raise RuntimeError("cleanup boom")

        arrow._clear_timer = _raise  # type: ignore[method-assign]
        with self.assertLogs("gui.widgets.arrowbox", level="DEBUG") as logs:
            ArrowBox.__del__(arrow)

        self.assertTrue(any("destructor cleanup failed" in line for line in logs.output))

    def test_button_leave_resets_state_to_idle(self) -> None:
        gui = build_interactive_gui_stub()
        gui.graphics_factory.build_interactive_visuals = lambda style, text, rect: SimpleNamespace(
            idle=object(), hover=object(), armed=object(), disabled=object(), hit_rect=Rect(rect)
        )
        button = Button(gui, "b", Rect(0, 0, 20, 10), ButtonStyle.Box, "txt", on_activate=None)
        button.state = InteractiveState.Armed

        button.leave()

        self.assertEqual(button.state, InteractiveState.Idle)

    def test_button_non_left_click_does_not_arm_or_activate(self) -> None:
        gui = build_interactive_gui_stub()
        gui.graphics_factory.build_interactive_visuals = lambda style, text, rect: SimpleNamespace(
            idle=object(), hover=object(), armed=object(), disabled=object(), hit_rect=Rect(rect)
        )
        button = Button(gui, "b", Rect(0, 0, 20, 10), ButtonStyle.Box, "txt", on_activate=None)

        right_down = pygame.event.Event(MOUSEBUTTONDOWN, {"button": 3})
        right_up = pygame.event.Event(MOUSEBUTTONUP, {"button": 3})

        self.assertFalse(button.handle_event(right_down, None))
        self.assertEqual(button.state, InteractiveState.Hover)
        self.assertFalse(button.handle_event(right_up, None))
        self.assertEqual(button.state, InteractiveState.Hover)

    def test_button_returns_false_when_mouse_event_not_colliding(self) -> None:
        gui = build_interactive_gui_stub()
        gui.graphics_factory.build_interactive_visuals = lambda style, text, rect: SimpleNamespace(
            idle=object(), hover=object(), armed=object(), disabled=object(), hit_rect=Rect(rect)
        )
        gui.get_mouse_pos = lambda: (50, 50)
        gui._get_mouse_pos = gui.get_mouse_pos
        button = Button(gui, "b", Rect(0, 0, 20, 10), ButtonStyle.Box, "txt", on_activate=None)

        down = pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1})
        self.assertFalse(button.handle_event(down, None))

    def test_button_ignores_non_mouse_events(self) -> None:
        gui = build_interactive_gui_stub()
        gui.graphics_factory.build_interactive_visuals = lambda style, text, rect: SimpleNamespace(
            idle=object(), hover=object(), armed=object(), disabled=object(), hit_rect=Rect(rect)
        )
        button = Button(gui, "b", Rect(0, 0, 20, 10), ButtonStyle.Box, "txt", on_activate=None)

        other = pygame.event.Event(pygame.USEREVENT, {})
        self.assertFalse(button.handle_event(other, None))

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
        gui.graphics_factory = SimpleNamespace(file_resource=lambda *parts: "D:/Code/gui_do/data/images/test.png")
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
