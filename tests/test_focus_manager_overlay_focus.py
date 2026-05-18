import unittest

import pygame

from gui_do.events.gui_event import EventType, GuiEvent
from gui_do.focus.focus_manager import FocusManager


class _OverlayStub:
    def __init__(self, *, palette_open: bool):
        self._palette_open = bool(palette_open)

    def has_overlay(self, owner_id: str) -> bool:
        return self._palette_open and str(owner_id) == "__command_palette__"


class _AppStub:
    def __init__(self, *, palette_open: bool):
        self.overlay = _OverlayStub(palette_open=palette_open)
        self.scene = type("_Scene", (), {"nodes": []})()
        self.theme = object()


class _OverlayFocusNode:
    def __init__(self, control_id: str):
        self.control_id = str(control_id)
        self.visible = True
        self.enabled = True
        self.parent = None
        self.clear_calls = []

    def _set_focused(self, is_focused: bool) -> None:
        self.clear_calls.append(bool(is_focused))


class TestFocusManagerOverlayFocus(unittest.TestCase):
    def test_route_key_event_preserves_command_palette_overlay_focus(self):
        focus = FocusManager()
        target = _OverlayFocusNode("__command_palette___list")
        app = _AppStub(palette_open=True)
        focus.set_focus(target)

        consumed = focus.route_key_event(
            GuiEvent(kind=EventType.KEY_UP, type=pygame.KEYUP, key=pygame.K_F5),
            app,
        )

        self.assertFalse(consumed)
        self.assertIs(focus.focused_node, target)

    def test_route_key_event_clears_missing_scene_focus_when_palette_not_open(self):
        focus = FocusManager()
        target = _OverlayFocusNode("__command_palette___list")
        app = _AppStub(palette_open=False)
        focus.set_focus(target)

        consumed = focus.route_key_event(
            GuiEvent(kind=EventType.KEY_UP, type=pygame.KEYUP, key=pygame.K_F5),
            app,
        )

        self.assertFalse(consumed)
        self.assertIsNone(focus.focused_node)

    def test_revalidate_focus_preserves_command_palette_overlay_focus(self):
        focus = FocusManager()
        target = _OverlayFocusNode("__command_palette___list")
        app = _AppStub(palette_open=True)
        focus.set_focus(target)

        focus.revalidate_focus(app.scene, app=app)

        self.assertIs(focus.focused_node, target)

    def test_revalidate_focus_clears_command_palette_overlay_focus_when_palette_closed(self):
        focus = FocusManager()
        target = _OverlayFocusNode("__command_palette___list")
        app = _AppStub(palette_open=False)
        focus.set_focus(target)

        focus.revalidate_focus(app.scene, app=app)

        self.assertIsNone(focus.focused_node)


if __name__ == "__main__":
    unittest.main()
