import unittest
from unittest.mock import patch

import pygame

from gui_do.app.gui_application import GuiApplication
from gui_do.controls.chrome.window_control import WindowControl


pygame.init()


class TestGuiApplicationWheelPointerSync(unittest.TestCase):
    def test_mouse_wheel_syncs_logical_pointer_from_hardware_when_unlocked(self):
        app = GuiApplication(pygame.Surface((320, 240)))
        app.set_logical_pointer_position((0, 0), apply_constraints=False)

        wheel = pygame.event.Event(pygame.MOUSEWHEEL, {"x": 0, "y": 1})
        with patch("gui_do.app.gui_application.pygame.mouse.get_pos", return_value=(123, 77)):
            app.process_event(wheel)

        self.assertEqual((123, 77), app.logical_pointer_pos)

    def test_visibility_event_centers_new_window_when_tiling_disabled(self):
        app = GuiApplication(pygame.Surface((320, 240)))
        window = WindowControl("w", (100, 80), "Window")
        window.visible = True
        app.scene.add(window)
        app.set_window_tiling_enabled(False, relayout=False)

        app.tile_windows(newly_visible=(window,), as_visibility_event=True)

        bounds = app.surface.get_rect()
        expected_left = int((bounds.width - window.rect.width) / 2)
        expected_top = int((bounds.height - window.rect.height) / 2)
        self.assertEqual((expected_left, expected_top), window.rect.topleft)

    def test_visibility_event_with_raised_windows_does_not_expand_newly_visible_snapshot(self):
        app = GuiApplication(pygame.Surface((320, 240)))
        raised = WindowControl("raised", (100, 80), "Raised")
        other = WindowControl("other", (100, 80), "Other")
        app.scene.add(raised)
        app.scene.add(other)

        with patch.object(app.window_tiling, "visible_windows_snapshot", return_value=(raised, other)):
            with patch.object(app.window_tiling, "arrange_windows") as arrange_mock:
                app.tile_windows(raised_windows=(raised,), as_visibility_event=True, force=True)

        arrange_mock.assert_called_once()
        kwargs = arrange_mock.call_args.kwargs
        self.assertIsNone(kwargs.get("newly_visible"))
        self.assertEqual((raised,), kwargs.get("raised_windows"))

    def test_force_tiling_does_not_snapshot_newly_visible_when_as_visibility_event(self):
        app = GuiApplication(pygame.Surface((320, 240)))
        first = WindowControl("first", (100, 80), "First")
        second = WindowControl("second", (100, 80), "Second")
        app.scene.add(first)
        app.scene.add(second)

        with patch.object(app.window_tiling, "visible_windows_snapshot", return_value=(first, second)):
            with patch.object(app.window_tiling, "arrange_windows") as arrange_mock:
                app.tile_windows(as_visibility_event=True, force=True)

        arrange_mock.assert_called_once()
        kwargs = arrange_mock.call_args.kwargs
        self.assertIsNone(kwargs.get("newly_visible"))


if __name__ == "__main__":
    unittest.main()
