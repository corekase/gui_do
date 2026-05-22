import unittest

import pygame
from pygame import Rect

from gui_do.controls.input.window_toggle_button_control import WindowToggleButtonControl
from gui_do.events.gui_event import EventType, GuiEvent


pygame.init()


class _UnresolvedPresentation:
    def __init__(self):
        self.show_calls = []
        self.set_visible_calls = []

    @staticmethod
    def get_window(_key: str):
        # Simulate temporary resolution gap in presentation model.
        return None

    def show(self, key: str):
        self.show_calls.append(str(key))

    def set_visible(self, key: str, visible: bool, *, from_toggle: bool = False):
        self.set_visible_calls.append((str(key), bool(visible), bool(from_toggle)))


class _StubApp:
    def __init__(self, window_presentation):
        self.window_presentation = window_presentation


class _Window:
    def __init__(self, *, visible: bool):
        self.visible = bool(visible)


class _ResolvedPresentation:
    def __init__(self, window):
        self._window = window
        self.show_calls = []
        self.set_visible_calls = []

    def get_window(self, _key: str):
        return self._window

    def show(self, key: str):
        self.show_calls.append(str(key))

    def set_visible(self, key: str, visible: bool, *, from_toggle: bool = False):
        self.set_visible_calls.append((str(key), bool(visible), bool(from_toggle)))


class TestWindowToggleButtonControl(unittest.TestCase):
    def test_open_button_prefers_show_over_set_visible_when_window_resolution_is_missing(self):
        presentation = _UnresolvedPresentation()
        app = _StubApp(presentation)

        on_toggle_calls = []
        button = WindowToggleButtonControl(
            "show_life",
            Rect(10, 10, 120, 30),
            "life",
            "Life",
            pushed=True,
            on_toggle=lambda pushed: on_toggle_calls.append(bool(pushed)),
            on_show=lambda: presentation.show("life"),
        )

        click = GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0, pos=(20, 20), button=1)
        consumed = button.handle_event(click, app)

        self.assertTrue(consumed)
        self.assertEqual(["life"], presentation.show_calls)
        self.assertEqual([], presentation.set_visible_calls)
        self.assertEqual([], on_toggle_calls)

    def test_hidden_window_with_stale_pushed_opens_via_set_visible_not_show(self):
        presentation = _ResolvedPresentation(_Window(visible=False))
        app = _StubApp(presentation)

        on_toggle_calls = []
        button = WindowToggleButtonControl(
            "show_life",
            Rect(10, 10, 120, 30),
            "life",
            "Life",
            pushed=True,
            on_toggle=lambda pushed: on_toggle_calls.append(bool(pushed)),
            on_show=lambda: presentation.show("life"),
        )

        click = GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0, pos=(20, 20), button=1)
        consumed = button.handle_event(click, app)

        self.assertTrue(consumed)
        self.assertEqual([], presentation.show_calls)
        self.assertEqual([("life", True, True)], presentation.set_visible_calls)
        self.assertEqual([True], on_toggle_calls)


if __name__ == "__main__":
    unittest.main()
