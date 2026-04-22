"""Tests for GuiApplication scene management APIs: scene_names, has_scene, remove_scene."""
import unittest
from unittest.mock import MagicMock, patch

import pygame

from gui.app.gui_application import GuiApplication
from gui.controls.window_control import WindowControl
from gui.controls.label_control import LabelControl
from gui.controls.button_control import ButtonControl
from gui.controls.canvas_control import CanvasControl
from gui.controls.slider_control import SliderControl
from gui.controls.toggle_control import ToggleControl
from gui.layout.layout_axis import LayoutAxis
from shared.part_lifecycle import Part


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


class _StubPart(Part):
    def __init__(self, name: str) -> None:
        super().__init__(name)
        self.host_seen = None

    def on_register(self, host) -> None:
        self.host_seen = host


class PartApiTests(GuiApplicationSceneManagementSetup):

    def test_register_and_get_part(self) -> None:
        part = _StubPart("alpha")
        self.app.register_part(part, host=self.app)
        self.assertIs(self.app.get_part("alpha"), part)
        self.assertIn("alpha", self.app.part_names())

    def test_unregister_part(self) -> None:
        self.app.register_part(_StubPart("alpha"), host=self.app)
        self.assertTrue(self.app.unregister_part("alpha"))
        self.assertIsNone(self.app.get_part("alpha"))

    def test_send_part_message(self) -> None:
        sender = _StubPart("sender")
        target = _StubPart("target")
        self.app.register_part(sender, host=self.app)
        self.app.register_part(target, host=self.app)
        sent = self.app.send_part_message("sender", "target", {"kind": "ping"})
        self.assertTrue(sent)
        self.assertTrue(target.has_messages())
        msg = target.pop_message()
        self.assertEqual("ping", msg["kind"])
        self.assertEqual("sender", msg["_from"])
        self.assertEqual("target", msg["_to"])

    def test_register_and_run_part_runnable(self) -> None:
        self.app.register_part(_StubPart("worker"), host=self.app)
        self.app.register_part_runnable("worker", "sum", lambda x, y: x + y)
        self.assertEqual(7, self.app.run_part_runnable("worker", "sum", 3, 4))

    def test_app_run_delegates_to_ui_engine(self) -> None:
        with patch("gui.loop.ui_engine.UiEngine.run", return_value=12) as run_mock:
            frames = self.app.run(target_fps=75, max_frames=3)

        self.assertEqual(12, frames)
        run_mock.assert_called_once_with(max_frames=3)


class PartUiTypesTests(GuiApplicationSceneManagementSetup):

    def test_read_part_ui_types_returns_same_instance(self) -> None:
        ui_types_a = self.app.read_part_ui_types()
        ui_types_b = self.app.read_part_ui_types()
        self.assertIs(ui_types_a, ui_types_b)

    def test_read_part_ui_types_contains_expected_bindings(self) -> None:
        ui_types = self.app.read_part_ui_types()
        self.assertIs(ui_types.window_control_cls, WindowControl)
        self.assertIs(ui_types.label_control_cls, LabelControl)
        self.assertIs(ui_types.button_control_cls, ButtonControl)
        self.assertIs(ui_types.canvas_control_cls, CanvasControl)
        self.assertIs(ui_types.slider_control_cls, SliderControl)
        self.assertIs(ui_types.toggle_control_cls, ToggleControl)
        self.assertIs(ui_types.layout_axis_cls, LayoutAxis)


if __name__ == "__main__":
    unittest.main()
