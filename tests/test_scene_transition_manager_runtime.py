"""Tests for SceneTransitionManager and SceneTransitionStyle."""
import unittest
from unittest.mock import MagicMock, call, patch
from pygame import Rect

import pygame
pygame.init()
pygame.display.set_mode((1, 1), pygame.NOFRAME)

from gui_do.core.scene_transition_manager import (
    SceneTransitionManager,
    SceneTransitionStyle,
)


def _make_app() -> MagicMock:
    app = MagicMock()
    app.surface = pygame.Surface((200, 100))
    tweens = MagicMock()
    app.tweens = tweens
    return app


class TestSceneTransitionStyle(unittest.TestCase):

    def test_enum_members_exist(self):
        self.assertIsInstance(SceneTransitionStyle.NONE, SceneTransitionStyle)
        self.assertIsInstance(SceneTransitionStyle.FADE, SceneTransitionStyle)
        self.assertIsInstance(SceneTransitionStyle.SLIDE_LEFT, SceneTransitionStyle)
        self.assertIsInstance(SceneTransitionStyle.SLIDE_RIGHT, SceneTransitionStyle)
        self.assertIsInstance(SceneTransitionStyle.SLIDE_UP, SceneTransitionStyle)
        self.assertIsInstance(SceneTransitionStyle.SLIDE_DOWN, SceneTransitionStyle)


class TestSceneTransitionManagerDefaults(unittest.TestCase):

    def test_default_style_is_fade(self):
        app = _make_app()
        mgr = SceneTransitionManager(app)
        self.assertIs(mgr._default_style, SceneTransitionStyle.FADE)

    def test_set_default_changes_style(self):
        app = _make_app()
        mgr = SceneTransitionManager(app)
        mgr.set_default(SceneTransitionStyle.SLIDE_LEFT, duration=0.5)
        self.assertIs(mgr._default_style, SceneTransitionStyle.SLIDE_LEFT)
        self.assertAlmostEqual(mgr._default_duration, 0.5)

    def test_set_style_override(self):
        app = _make_app()
        mgr = SceneTransitionManager(app)
        mgr.set_style("editor", SceneTransitionStyle.SLIDE_RIGHT, duration=0.2)
        style, dur = mgr._overrides["editor"]
        self.assertIs(style, SceneTransitionStyle.SLIDE_RIGHT)
        self.assertAlmostEqual(dur, 0.2)


class TestSceneTransitionManagerGo(unittest.TestCase):

    def test_none_style_calls_switch_scene_directly(self):
        app = _make_app()
        mgr = SceneTransitionManager(app, default_style=SceneTransitionStyle.NONE)
        mgr.go("home")
        app.switch_scene.assert_called_once_with("home")
        app.tweens.tween_fn.assert_not_called()

    def test_zero_duration_calls_switch_scene_directly(self):
        app = _make_app()
        mgr = SceneTransitionManager(app, default_duration=0.0)
        mgr.go("home")
        app.switch_scene.assert_called_once_with("home")
        app.tweens.tween_fn.assert_not_called()

    def test_fade_registers_tween(self):
        app = _make_app()
        mgr = SceneTransitionManager(
            app, default_style=SceneTransitionStyle.FADE, default_duration=0.3
        )
        mgr.go("home")
        app.switch_scene.assert_called_once_with("home")
        app.tweens.tween_fn.assert_called_once()

    def test_slide_left_registers_tween(self):
        app = _make_app()
        mgr = SceneTransitionManager(
            app, default_style=SceneTransitionStyle.SLIDE_LEFT, default_duration=0.3
        )
        mgr.go("home")
        app.tweens.tween_fn.assert_called_once()

    def test_on_complete_callback_wired(self):
        app = _make_app()
        mgr = SceneTransitionManager(
            app, default_style=SceneTransitionStyle.NONE
        )
        completed = []
        mgr.go("home", on_complete=lambda: completed.append(True))
        self.assertEqual(completed, [True])

    def test_is_animating_false_after_none_style(self):
        app = _make_app()
        mgr = SceneTransitionManager(app, default_style=SceneTransitionStyle.NONE)
        mgr.go("home")
        self.assertFalse(mgr.is_animating)

    def test_is_animating_true_during_fade(self):
        app = _make_app()
        mgr = SceneTransitionManager(
            app, default_style=SceneTransitionStyle.FADE, default_duration=0.3
        )
        mgr.go("home")
        # Animation starts immediately; is_animating should be True
        # (tween_fn hasn't called _done yet because it's mocked)
        self.assertTrue(mgr.is_animating)

    def test_per_scene_override_used(self):
        app = _make_app()
        mgr = SceneTransitionManager(app, default_style=SceneTransitionStyle.FADE)
        mgr.set_style("special", SceneTransitionStyle.NONE)
        mgr.go("special")
        # NONE style means switch directly without tween
        app.tweens.tween_fn.assert_not_called()

    def test_explicit_style_overrides_all(self):
        app = _make_app()
        mgr = SceneTransitionManager(app, default_style=SceneTransitionStyle.FADE)
        mgr.set_style("scene_a", SceneTransitionStyle.SLIDE_LEFT)
        mgr.go("scene_a", style=SceneTransitionStyle.NONE)
        app.tweens.tween_fn.assert_not_called()


if __name__ == "__main__":
    unittest.main()
