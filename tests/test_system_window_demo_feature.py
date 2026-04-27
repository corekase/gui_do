import os
import unittest
from types import SimpleNamespace

os.environ.setdefault("SDL_VIDEODRIVER", "dummy")

import pygame

from demo_features.system_window_demo_feature import SystemWindowDemoFeature
from gui_do import GuiApplication, PanelControl


class _Host(SimpleNamespace):
    pass


class SystemWindowDemoFeatureTests(unittest.TestCase):
    def setUp(self) -> None:
        pygame.init()
        self.surface = pygame.display.set_mode((1280, 720))

    def tearDown(self) -> None:
        pygame.quit()

    def _build_feature(self):
        app = GuiApplication(self.surface)
        app.create_scene("main")
        root = app.add(PanelControl("main_root", pygame.Rect(0, 0, 1280, 720), draw_background=False), scene_name="main")
        host = _Host(
            app=app,
            root=root,
            screen_rect=pygame.Rect(0, 0, 1280, 720),
            go_to_main=lambda: app.switch_scene("main"),
            go_to_control_showcase=lambda: app.switch_scene("main"),
            set_system_window_visible=lambda _value: None,
        )
        feature = SystemWindowDemoFeature()
        feature.build(host)
        return app, host, feature

    def test_build_creates_window_and_primary_controls(self) -> None:
        _app, _host, feature = self._build_feature()

        self.assertIsNotNone(feature.window)
        self.assertIsNotNone(feature.menu_bar)
        self.assertIsNotNone(feature.tree)
        self.assertIsNotNone(feature.log_area)
        self.assertEqual(len(feature._toolbar_buttons), 4)

    def test_publish_test_notification_updates_center_and_log(self) -> None:
        _app, _host, feature = self._build_feature()

        before = len(feature.notification_center.all_records)
        feature.publish_test_notification()

        self.assertEqual(len(feature.notification_center.all_records), before + 1)
        self.assertIn("Notification:", feature.log_area.value)

    def test_show_notifications_panel_adds_overlay(self) -> None:
        app, _host, feature = self._build_feature()

        feature.show_notifications_panel()

        self.assertTrue(app.overlay.has_overlay("system_notification_panel"))

    def test_open_and_save_result_callbacks_update_log(self) -> None:
        _app, _host, feature = self._build_feature()

        feature._on_open_result(["demo.txt"])
        feature._on_save_result(["out.txt"])

        self.assertIn("Open: demo.txt", feature.log_area.value)
        self.assertIn("Save: out.txt", feature.log_area.value)

    def test_minimize_window_hides_window(self) -> None:
        _app, host, feature = self._build_feature()
        called = {"count": 0}
        host.set_system_window_visible = lambda _value: called.__setitem__("count", called["count"] + 1)

        feature.minimize_window()

        self.assertFalse(feature.window.visible)
        self.assertEqual(called["count"], 1)


if __name__ == "__main__":
    unittest.main()
