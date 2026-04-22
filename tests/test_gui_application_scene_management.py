"""Tests for GuiApplication scene management APIs: scene_names, has_scene, remove_scene."""
import unittest
from unittest.mock import MagicMock, patch

import pygame

from gui.app.gui_application import GuiApplication


def _make_app() -> GuiApplication:
    surface = MagicMock(spec=pygame.Surface)
    surface.get_rect.return_value = pygame.Rect(0, 0, 800, 600)
    surface.get_size.return_value = (800, 600)
    with patch("pygame.mouse.get_pos", return_value=(0, 0)), \
         patch("pygame.mouse.set_pos"):
        return GuiApplication.__new__(GuiApplication)


class GuiApplicationSceneManagementSetup(unittest.TestCase):
    """Base providing a minimal GuiApplication instance for scene tests."""

    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((200, 150))
        with patch("pygame.mouse.get_pos", return_value=(0, 0)):
            self.app = GuiApplication(self.surface)

    def tearDown(self) -> None:
        self.app.shutdown()
        pygame.quit()


class SceneNamesTests(GuiApplicationSceneManagementSetup):

    def test_scene_names_contains_default_on_init(self) -> None:
        self.assertIn("default", self.app.scene_names())

    def test_scene_names_returns_list(self) -> None:
        self.assertIsInstance(self.app.scene_names(), list)

    def test_scene_names_grows_after_create_scene(self) -> None:
        self.app.create_scene("extra")
        self.assertIn("extra", self.app.scene_names())

    def test_scene_names_contains_active_scene(self) -> None:
        self.assertIn(self.app.active_scene_name, self.app.scene_names())

    def test_scene_names_snapshot_is_independent(self) -> None:
        names = self.app.scene_names()
        self.app.create_scene("new_scene")
        # Original snapshot unchanged
        self.assertNotIn("new_scene", names)


class HasSceneTests(GuiApplicationSceneManagementSetup):

    def test_has_scene_true_for_default(self) -> None:
        self.assertTrue(self.app.has_scene("default"))

    def test_has_scene_false_for_unknown(self) -> None:
        self.assertFalse(self.app.has_scene("nonexistent"))

    def test_has_scene_true_after_create_scene(self) -> None:
        self.app.create_scene("fresh")
        self.assertTrue(self.app.has_scene("fresh"))

    def test_has_scene_false_after_remove_scene(self) -> None:
        self.app.create_scene("temp")
        self.app.remove_scene("temp")
        self.assertFalse(self.app.has_scene("temp"))


class RemoveSceneTests(GuiApplicationSceneManagementSetup):

    def test_remove_scene_returns_false_for_unknown(self) -> None:
        self.assertFalse(self.app.remove_scene("does_not_exist"))

    def test_remove_scene_returns_false_for_active_scene(self) -> None:
        # "default" is the active scene — must not be removable
        self.assertFalse(self.app.remove_scene(self.app.active_scene_name))

    def test_remove_scene_returns_true_for_inactive(self) -> None:
        self.app.create_scene("side")
        self.assertTrue(self.app.remove_scene("side"))

    def test_remove_scene_removes_from_scene_names(self) -> None:
        self.app.create_scene("gone")
        self.app.remove_scene("gone")
        self.assertNotIn("gone", self.app.scene_names())

    def test_remove_scene_active_remains_after_inactive_removed(self) -> None:
        self.app.create_scene("side")
        self.app.remove_scene("side")
        self.assertIn(self.app.active_scene_name, self.app.scene_names())

    def test_remove_scene_idempotent(self) -> None:
        self.app.create_scene("once")
        self.assertTrue(self.app.remove_scene("once"))
        self.assertFalse(self.app.remove_scene("once"))

    def test_remove_scene_does_not_affect_other_scenes(self) -> None:
        self.app.create_scene("keep")
        self.app.create_scene("drop")
        self.app.remove_scene("drop")
        self.assertTrue(self.app.has_scene("keep"))

    def test_removed_scene_cannot_be_switched_to(self) -> None:
        self.app.create_scene("away")
        self.app.remove_scene("away")
        with self.assertRaises(ValueError):
            self.app.switch_scene("away")


if __name__ == "__main__":
    unittest.main()
