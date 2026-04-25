"""Tests for ActionManager runtime binding management APIs."""
import unittest
from types import SimpleNamespace

import pygame

from gui.core.action_manager import ActionManager, KeyBinding
from gui.core.gui_event import EventType, GuiEvent, EventPhase


def _key_down_event(key: int) -> GuiEvent:
    return GuiEvent(
        kind=EventType.KEY_DOWN,
        type=pygame.KEYDOWN,
        key=key,
        phase=EventPhase.TARGET,
    )


def _app(scene_name="default", has_window=False):
    scene = SimpleNamespace(active_window=lambda: object() if has_window else None)
    return SimpleNamespace(active_scene_name=scene_name, scene=scene)


class ActionManagerHasActionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = ActionManager()

    def test_has_action_false_when_empty(self) -> None:
        self.assertFalse(self.manager.has_action("quit"))

    def test_has_action_true_after_register(self) -> None:
        self.manager.register_action("quit", lambda e: True)
        self.assertTrue(self.manager.has_action("quit"))

    def test_has_action_false_after_unregister(self) -> None:
        self.manager.register_action("quit", lambda e: True)
        self.manager.unregister_action("quit")
        self.assertFalse(self.manager.has_action("quit"))


class ActionManagerRegisteredActionsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.manager = ActionManager()

    def test_registered_actions_empty_by_default(self) -> None:
        self.assertEqual(self.manager.registered_actions(), [])

    def test_registered_actions_returns_sorted_names(self) -> None:
        self.manager.register_action("zoom_in", lambda e: True)
        self.manager.register_action("quit", lambda e: True)
        self.manager.register_action("help", lambda e: True)
        self.assertEqual(self.manager.registered_actions(), ["help", "quit", "zoom_in"])

    def test_registered_actions_excludes_unregistered(self) -> None:
        self.manager.register_action("a", lambda e: True)
        self.manager.register_action("b", lambda e: True)
        self.manager.unregister_action("a")
        self.assertEqual(self.manager.registered_actions(), ["b"])


class ActionManagerUnbindKeyTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.manager = ActionManager()
        self.manager.register_action("save", lambda e: True)
        self.manager.register_action("save_as", lambda e: True)
        self.manager.bind_key(pygame.K_s, "save")
        self.manager.bind_key(pygame.K_s, "save_as", scene="editor")

    def test_unbind_key_returns_true_when_binding_exists(self) -> None:
        result = self.manager.unbind_key(pygame.K_s, "save")
        self.assertTrue(result)

    def test_unbind_key_returns_false_when_binding_missing(self) -> None:
        result = self.manager.unbind_key(pygame.K_s, "nonexistent")
        self.assertFalse(result)

    def test_unbind_key_stops_action_from_triggering(self) -> None:
        app = _app()
        event = _key_down_event(pygame.K_s)
        # save triggers before unbind
        self.assertTrue(self.manager.trigger_from_event(event, app))
        self.manager.unbind_key(pygame.K_s, "save")
        # After unbind: global "save" removed; only scene-scoped "save_as" remains
        # With scene_name="default" and no scene="editor" match → no trigger
        self.assertFalse(self.manager.trigger_from_event(event, app))

    def test_unbind_key_removes_only_specified_action(self) -> None:
        self.manager.unbind_key(pygame.K_s, "save")
        # save_as (scene="editor") binding must survive
        app = _app(scene_name="editor")
        event = _key_down_event(pygame.K_s)
        self.assertTrue(self.manager.trigger_from_event(event, app))

    def test_unbind_key_with_scene_arg_removes_only_scoped_binding(self) -> None:
        self.manager.unbind_key(pygame.K_s, "save_as", scene="editor")
        # Global "save" binding must still work
        app = _app()
        event = _key_down_event(pygame.K_s)
        self.assertTrue(self.manager.trigger_from_event(event, app))

    def test_unbind_key_cleans_up_empty_binding_entry(self) -> None:
        # Bind a solo action then unbind it; the keymap entry should be gone
        self.manager.register_action("solo", lambda e: True)
        self.manager.bind_key(pygame.K_z, "solo")
        self.manager.unbind_key(pygame.K_z, "solo")
        # Internal cleanup: binding key should not exist in keymap
        binding = KeyBinding(pygame.K_z, scene=None, window_only=False)
        self.assertNotIn(binding, self.manager._keymap)

    def test_unbind_key_idempotent_second_call_returns_false(self) -> None:
        self.manager.unbind_key(pygame.K_s, "save")
        second = self.manager.unbind_key(pygame.K_s, "save")
        self.assertFalse(second)


class ActionManagerBindingsForActionTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.manager = ActionManager()
        self.manager.register_action("zoom", lambda e: True)

    def test_bindings_for_action_empty_when_none_registered(self) -> None:
        self.assertEqual(self.manager.bindings_for_action("zoom"), [])

    def test_bindings_for_action_returns_all_bindings(self) -> None:
        self.manager.bind_key(pygame.K_PLUS, "zoom")
        self.manager.bind_key(pygame.K_EQUALS, "zoom", scene="canvas")
        bindings = self.manager.bindings_for_action("zoom")
        keys = {b.key for b in bindings}
        self.assertIn(pygame.K_PLUS, keys)
        self.assertIn(pygame.K_EQUALS, keys)
        self.assertEqual(len(bindings), 2)

    def test_bindings_for_action_does_not_include_other_actions(self) -> None:
        self.manager.register_action("quit", lambda e: True)
        self.manager.bind_key(pygame.K_q, "quit")
        self.manager.bind_key(pygame.K_z, "zoom")
        bindings = self.manager.bindings_for_action("zoom")
        keys = {b.key for b in bindings}
        self.assertNotIn(pygame.K_q, keys)
        self.assertIn(pygame.K_z, keys)

    def test_bindings_for_action_reflects_unbind(self) -> None:
        self.manager.bind_key(pygame.K_PLUS, "zoom")
        self.manager.bind_key(pygame.K_EQUALS, "zoom")
        self.manager.unbind_key(pygame.K_PLUS, "zoom")
        bindings = self.manager.bindings_for_action("zoom")
        keys = {b.key for b in bindings}
        self.assertNotIn(pygame.K_PLUS, keys)
        self.assertIn(pygame.K_EQUALS, keys)


if __name__ == "__main__":
    unittest.main()
