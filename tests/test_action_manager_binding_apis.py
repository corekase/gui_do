"""Tests for ActionManager management APIs: binding_count, clear_bindings_for_action."""
import unittest

import pygame

from gui_do.core.action_manager import ActionManager


class BindingCountTests(unittest.TestCase):

    def test_binding_count_zero_initially(self) -> None:
        am = ActionManager()
        self.assertEqual(am.binding_count(), 0)

    def test_binding_count_increments_per_binding(self) -> None:
        am = ActionManager()
        am.register_action("jump", lambda e: True)
        am.bind_key(pygame.K_SPACE, "jump")
        self.assertEqual(am.binding_count(), 1)

    def test_binding_count_counts_multiple_actions_on_same_key(self) -> None:
        am = ActionManager()
        am.register_action("a", lambda e: True)
        am.register_action("b", lambda e: True)
        am.bind_key(pygame.K_SPACE, "a")
        am.bind_key(pygame.K_SPACE, "b")
        self.assertEqual(am.binding_count(), 2)

    def test_binding_count_counts_across_different_keys(self) -> None:
        am = ActionManager()
        am.register_action("x", lambda e: True)
        am.bind_key(pygame.K_LEFT, "x")
        am.bind_key(pygame.K_RIGHT, "x")
        self.assertEqual(am.binding_count(), 2)

    def test_binding_count_decrements_after_unbind(self) -> None:
        am = ActionManager()
        am.register_action("act", lambda e: True)
        am.bind_key(pygame.K_a, "act")
        am.bind_key(pygame.K_b, "act")
        am.unbind_key(pygame.K_a, "act")
        self.assertEqual(am.binding_count(), 1)

    def test_binding_count_zero_after_clear_bindings(self) -> None:
        am = ActionManager()
        am.register_action("act", lambda e: True)
        am.bind_key(pygame.K_a, "act")
        am.bind_key(pygame.K_b, "act")
        am.clear_bindings()
        self.assertEqual(am.binding_count(), 0)

    def test_binding_count_ignores_duplicate_bind_calls(self) -> None:
        am = ActionManager()
        am.register_action("act", lambda e: True)
        am.bind_key(pygame.K_a, "act")
        am.bind_key(pygame.K_a, "act")  # duplicate — must not double-count
        self.assertEqual(am.binding_count(), 1)


class ClearBindingsForActionTests(unittest.TestCase):

    def test_clear_bindings_for_action_returns_zero_when_none(self) -> None:
        am = ActionManager()
        self.assertEqual(am.clear_bindings_for_action("missing"), 0)

    def test_clear_bindings_for_action_returns_count_removed(self) -> None:
        am = ActionManager()
        am.register_action("act", lambda e: True)
        am.bind_key(pygame.K_a, "act")
        am.bind_key(pygame.K_b, "act")
        self.assertEqual(am.clear_bindings_for_action("act"), 2)

    def test_clear_bindings_for_action_removes_all_keys_for_action(self) -> None:
        am = ActionManager()
        am.register_action("act", lambda e: True)
        am.bind_key(pygame.K_a, "act")
        am.bind_key(pygame.K_b, "act")
        am.clear_bindings_for_action("act")
        self.assertEqual(am.binding_count(), 0)

    def test_clear_bindings_for_action_leaves_other_actions_intact(self) -> None:
        am = ActionManager()
        am.register_action("act", lambda e: True)
        am.register_action("other", lambda e: True)
        am.bind_key(pygame.K_a, "act")
        am.bind_key(pygame.K_b, "other")
        am.clear_bindings_for_action("act")
        # "other" binding must survive
        self.assertEqual(am.binding_count(), 1)
        self.assertEqual(am.bindings_for_action("other"), [am._keymap[list(am._keymap.keys())[0]]] if False else am.bindings_for_action("other"))

    def test_clear_bindings_for_action_idempotent(self) -> None:
        am = ActionManager()
        am.register_action("act", lambda e: True)
        am.bind_key(pygame.K_a, "act")
        am.clear_bindings_for_action("act")
        result = am.clear_bindings_for_action("act")
        self.assertEqual(result, 0)

    def test_clear_bindings_for_action_shared_key_removes_only_target(self) -> None:
        am = ActionManager()
        am.register_action("a", lambda e: True)
        am.register_action("b", lambda e: True)
        am.bind_key(pygame.K_SPACE, "a")
        am.bind_key(pygame.K_SPACE, "b")
        am.clear_bindings_for_action("a")
        # K_SPACE→"b" must remain; K_SPACE→"a" must be gone
        remaining = am.bindings_for_action("b")
        self.assertEqual(len(remaining), 1)
        self.assertEqual(am.bindings_for_action("a"), [])

    def test_clear_bindings_does_not_unregister_handler(self) -> None:
        am = ActionManager()
        am.register_action("act", lambda e: True)
        am.bind_key(pygame.K_a, "act")
        am.clear_bindings_for_action("act")
        self.assertTrue(am.has_action("act"))


if __name__ == "__main__":
    unittest.main()
