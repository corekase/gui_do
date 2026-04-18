import unittest

import pygame
from pygame.locals import KEYDOWN, KEYUP, MOUSEBUTTONDOWN, MOUSEBUTTONUP, MOUSEMOTION, QUIT

from gui.utility.events import Event
from gui.utility.input_actions import InputAction
from gui.utility.input_emitter import InputEventEmitter


class _GuiEventStub:
    def __init__(self, event_type: Event, **kwargs: object) -> None:
        self.type = event_type
        for key, value in kwargs.items():
            setattr(self, key, value)


class _GuiStub:
    def event(self, event_type: Event, **kwargs: object) -> _GuiEventStub:
        return _GuiEventStub(event_type, **kwargs)


class InputEventEmitterContractsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.gui = _GuiStub()
        self.emitter = InputEventEmitter(self.gui)

    def test_emit_action_prefers_builder(self) -> None:
        built = _GuiEventStub(Event.Widget, widget_id="built")
        action = InputAction.from_builder(lambda: built)

        result = self.emitter.emit_action(action)

        self.assertIs(result, built)

    def test_emit_action_with_none_event_type_returns_pass(self) -> None:
        action = InputAction(event_type=None)

        result = self.emitter.emit_action(action)

        self.assertEqual(result.type, Event.Pass)

    def test_emit_action_emits_event_with_kwargs(self) -> None:
        action = InputAction.emit(Event.Widget, widget_id="w-1", task_panel=True)

        result = self.emitter.emit_action(action)

        self.assertEqual(result.type, Event.Widget)
        self.assertEqual(result.widget_id, "w-1")
        self.assertTrue(result.task_panel)

    def test_base_mouse_event_mappings(self) -> None:
        up = self.emitter.base_mouse_event(pygame.event.Event(MOUSEBUTTONUP, {"button": 3}))
        down = self.emitter.base_mouse_event(pygame.event.Event(MOUSEBUTTONDOWN, {"button": 1}))
        motion = self.emitter.base_mouse_event(pygame.event.Event(MOUSEMOTION, {"rel": (4, -2)}))

        self.assertEqual(up.type, Event.MouseButtonUp)
        self.assertEqual(up.button, 3)
        self.assertEqual(down.type, Event.MouseButtonDown)
        self.assertEqual(down.button, 1)
        self.assertEqual(motion.type, Event.MouseMotion)
        self.assertEqual(motion.rel, (4, -2))

    def test_base_mouse_event_defaults_and_fallback(self) -> None:
        default_up = self.emitter.base_mouse_event(pygame.event.Event(MOUSEBUTTONUP, {}))
        default_down = self.emitter.base_mouse_event(pygame.event.Event(MOUSEBUTTONDOWN, {}))
        default_motion = self.emitter.base_mouse_event(pygame.event.Event(MOUSEMOTION, {}))
        fallback = self.emitter.base_mouse_event(pygame.event.Event(KEYDOWN, {"key": 7}))

        self.assertIsNone(default_up.button)
        self.assertIsNone(default_down.button)
        self.assertEqual(default_motion.rel, (0, 0))
        self.assertEqual(fallback.type, Event.Pass)

    def test_system_event_mappings(self) -> None:
        quit_event = self.emitter.system_event(pygame.event.Event(QUIT, {}))
        key_up = self.emitter.system_event(pygame.event.Event(KEYUP, {"key": 42}))
        key_down = self.emitter.system_event(pygame.event.Event(KEYDOWN, {"key": 84}))

        self.assertEqual(quit_event.type, Event.Quit)
        self.assertEqual(key_up.type, Event.KeyUp)
        self.assertEqual(key_up.key, 42)
        self.assertEqual(key_down.type, Event.KeyDown)
        self.assertEqual(key_down.key, 84)

    def test_system_event_defaults_and_fallback(self) -> None:
        key_up = self.emitter.system_event(pygame.event.Event(KEYUP, {}))
        key_down = self.emitter.system_event(pygame.event.Event(KEYDOWN, {}))
        fallback = self.emitter.system_event(pygame.event.Event(MOUSEMOTION, {}))

        self.assertIsNone(key_up.key)
        self.assertIsNone(key_down.key)
        self.assertEqual(fallback.type, Event.Pass)

    def test_widget_event_kwargs_shape(self) -> None:
        with_widget = self.emitter.widget_event("widget-1")
        with_window = self.emitter.widget_event("widget-2", window="win")
        task_panel_only = self.emitter.widget_event(task_panel=True)

        self.assertEqual(with_widget.type, Event.Widget)
        self.assertEqual(with_widget.widget_id, "widget-1")
        self.assertEqual(with_window.window, "win")
        self.assertTrue(task_panel_only.task_panel)
        self.assertFalse(hasattr(task_panel_only, "widget_id"))

    def test_pass_event(self) -> None:
        result = self.emitter.pass_event()
        self.assertEqual(result.type, Event.Pass)


if __name__ == "__main__":
    unittest.main()
