import unittest
from types import SimpleNamespace

import pygame
from pygame import Rect
from pygame.locals import KEYDOWN, MOUSEMOTION

from gui.utility.events import InteractiveState
from gui.widgets.label import Label
from gui.widgets.toggle import Toggle


class _FakeBitmap:
    def __init__(self, width: int, height: int):
        self._rect = Rect(0, 0, width, height)

    def get_rect(self):
        return Rect(self._rect)

    def copy(self):
        return _FakeBitmap(self._rect.width, self._rect.height)

    def fill(self, *_args, **_kwargs):
        return None


class LabelToggleRoiBatch8Tests(unittest.TestCase):
    def test_label_init_with_point_and_rect_positioning_paths(self) -> None:
        factory = SimpleNamespace(
            get_current_font_name=lambda: "main",
            render_text=lambda text, *_args: _FakeBitmap(len(text) + 3, 7),
            centre=lambda bigger, smaller: int((bigger - smaller) / 2),
        )
        gui = SimpleNamespace(graphics_factory=factory)

        label_point = Label(gui, "l1", (10, 20), "abc", shadow=False)
        self.assertEqual(label_point.draw_rect.topleft, (10, 20))
        self.assertEqual(label_point.draw_rect.size, (6, 7))

        label_rect = Label(gui, "l2", (100, 50, 40, 20), "xy", shadow=False)
        # width=5, height=7 -> centered inside 40x20 at (117,56)
        self.assertEqual(label_rect.draw_rect.topleft, (117, 56))

    def test_label_set_label_with_and_without_bound_font(self) -> None:
        calls = []

        def render_text(text, *_args):
            calls.append(("render", text))
            return _FakeBitmap(8, 6)

        factory = SimpleNamespace(
            get_current_font_name=lambda: "main",
            render_text=render_text,
            set_font=lambda name: calls.append(("set_font", name)),
            set_last_font=lambda: calls.append(("set_last_font", None)),
            centre=lambda bigger, smaller: int((bigger - smaller) / 2),
        )
        gui = SimpleNamespace(graphics_factory=factory)

        label = Label(gui, "l1", (0, 0), "start")
        calls.clear()
        label._font = "main"
        label.set_label("next")
        self.assertEqual(calls, [("set_font", "main"), ("render", "next"), ("set_last_font", None)])

        calls.clear()
        label._font = None
        label.set_label("raw")
        self.assertEqual(calls, [("render", "raw")])

    def test_label_draw_and_handle_event_paths(self) -> None:
        factory = SimpleNamespace(
            get_current_font_name=lambda: "main",
            render_text=lambda text, *_args: _FakeBitmap(len(text) + 2, 5),
            centre=lambda bigger, smaller: int((bigger - smaller) / 2),
        )
        blits = []
        gui = SimpleNamespace(graphics_factory=factory)

        label = Label(gui, "l1", (4, 6), "go")
        label.surface = SimpleNamespace(blit=lambda bmp, pos: blits.append((bmp, pos)))

        self.assertFalse(label.handle_event(pygame.event.Event(MOUSEMOTION, {}), None))
        label.draw()
        self.assertEqual(len(blits), 1)
        self.assertEqual(blits[0][1], (4, 6))

    def test_label_render_shadow_and_plain_paths(self) -> None:
        shadow_calls = []

        def render_text(text, *args):
            shadow_calls.append((text, args))
            return _FakeBitmap(5, 4)

        factory = SimpleNamespace(
            get_current_font_name=lambda: "main",
            render_text=render_text,
            centre=lambda bigger, smaller: int((bigger - smaller) / 2),
        )
        gui = SimpleNamespace(graphics_factory=factory)

        Label(gui, "plain", (0, 0), "p", shadow=False)
        Label(gui, "shadow", (0, 0), "s", shadow=True)

        self.assertEqual(len(shadow_calls), 2)
        self.assertEqual(shadow_calls[0][0], "p")
        self.assertEqual(shadow_calls[1], ("s", ((255, 255, 255), True)))

    def test_toggle_init_hit_rect_selects_larger_variant(self) -> None:
        calls = []

        def build_toggle_visuals(_style, pressed_text, raised_text, _rect):
            calls.extend([pressed_text, raised_text])
            return SimpleNamespace(idle="idle", hover="hover", armed="armed", disabled="disabled", hit_rect=Rect(0, 0, 14, 8))

        gui = SimpleNamespace(graphics_factory=SimpleNamespace(build_toggle_visuals=build_toggle_visuals))
        toggle = Toggle(gui, "t1", Rect(0, 0, 20, 10), object(), False, "pressed", "raised")

        self.assertEqual(calls, ["pressed", "raised"])
        self.assertEqual(toggle.hit_rect.size, (14, 8))
        self.assertEqual(toggle.armed, "armed")
        self.assertEqual(toggle.idle, "idle")
        self.assertEqual(toggle.hover, "hover")

    def test_toggle_init_defaults_raised_text_to_pressed_text(self) -> None:
        calls = []

        def build_toggle_visuals(_style, pressed_text, raised_text, _rect):
            calls.extend([pressed_text, raised_text])
            return SimpleNamespace(idle="i", hover="h", armed="a", disabled="d", hit_rect=Rect(0, 0, 9, 7))

        gui = SimpleNamespace(graphics_factory=SimpleNamespace(build_toggle_visuals=build_toggle_visuals))
        Toggle(gui, "t2", Rect(0, 0, 20, 10), object(), False, "same")

        self.assertEqual(calls, ["same", None])

    def test_toggle_pushed_property_and_handle_non_hover_branch(self) -> None:
        toggle = Toggle.__new__(Toggle)
        toggle._pushed = False
        toggle._disabled = False

        toggle.pushed = True
        self.assertTrue(toggle.pushed)

        toggle.state = InteractiveState.Idle
        toggle.handle_event = Toggle.handle_event.__get__(toggle, Toggle)
        # Force BaseInteractive.handle_event path success but non-hover branch.
        import gui.widgets.toggle as toggle_module

        original = toggle_module.BaseInteractive.handle_event
        try:
            toggle_module.BaseInteractive.handle_event = lambda _self, _event, _window: True
            event = pygame.event.Event(MOUSEMOTION, {})
            self.assertFalse(toggle.handle_event(event, None))
        finally:
            toggle_module.BaseInteractive.handle_event = original

    def test_toggle_draw_armed_and_raised_paths(self) -> None:
        blits = []
        toggle = Toggle.__new__(Toggle)
        toggle._pushed = True
        toggle._disabled = False
        toggle.armed = "armed-bitmap"
        toggle.draw_rect = Rect(2, 3, 10, 6)
        toggle.surface = SimpleNamespace(blit=lambda bmp, pos: blits.append((bmp, pos)))
        toggle.auto_restore_pristine = False
        toggle.gui = SimpleNamespace(restore_pristine=lambda *_args, **_kwargs: None)

        import gui.widgets.toggle as toggle_module

        widget_draw_calls = []
        base_draw_calls = []
        original_widget_draw = toggle_module.Widget.draw
        original_base_draw = toggle_module.BaseInteractive.draw
        try:
            toggle_module.Widget.draw = lambda _self: widget_draw_calls.append(True)
            toggle_module.BaseInteractive.draw = lambda _self: base_draw_calls.append(True)

            toggle.draw()
            self.assertEqual(widget_draw_calls, [True])
            self.assertEqual(base_draw_calls, [])
            self.assertEqual(blits, [("armed-bitmap", Rect(2, 3, 10, 6))])

            blits.clear()
            toggle._pushed = False
            toggle.draw()
            self.assertEqual(base_draw_calls, [True])
            self.assertEqual(blits, [])
        finally:
            toggle_module.Widget.draw = original_widget_draw
            toggle_module.BaseInteractive.draw = original_base_draw

    def test_toggle_handle_event_returns_false_when_base_handler_rejects(self) -> None:
        toggle = Toggle.__new__(Toggle)
        toggle._pushed = False
        toggle._disabled = False
        toggle.state = InteractiveState.Idle

        import gui.widgets.toggle as toggle_module

        original = toggle_module.BaseInteractive.handle_event
        try:
            toggle_module.BaseInteractive.handle_event = lambda _self, _event, _window: False
            event = pygame.event.Event(MOUSEMOTION, {})
            self.assertFalse(Toggle.handle_event(toggle, event, None))
        finally:
            toggle_module.BaseInteractive.handle_event = original

    def test_toggle_handle_event_returns_false_for_hover_non_activating_input(self) -> None:
        toggle = Toggle.__new__(Toggle)
        toggle._pushed = False
        toggle._disabled = False
        toggle.state = InteractiveState.Hover

        import gui.widgets.toggle as toggle_module

        original = toggle_module.BaseInteractive.handle_event
        try:
            toggle_module.BaseInteractive.handle_event = lambda _self, _event, _window: True
            event = pygame.event.Event(MOUSEMOTION, {})
            self.assertFalse(Toggle.handle_event(toggle, event, None))
        finally:
            toggle_module.BaseInteractive.handle_event = original

    def test_toggle_handle_event_rejects_non_mouse_events(self) -> None:
        toggle = Toggle.__new__(Toggle)
        toggle._pushed = False
        toggle._disabled = False
        toggle.state = InteractiveState.Idle

        event = pygame.event.Event(KEYDOWN, {"key": 32})
        self.assertFalse(Toggle.handle_event(toggle, event, None))


if __name__ == "__main__":
    unittest.main()
