import unittest
from types import SimpleNamespace

from pygame import Rect

from gui_do.controls.chrome.menu_bar_control import MenuStripControl
from gui_do.controls.chrome.window_control import WindowControl
from gui_do.features.feature_lifecycle import FeatureWindowPresentationModel, set_window_visible_state
from gui_do.overlays.command_palette_manager import CommandPaletteManager


class _StubToggle:
    def __init__(self, pushed: bool = False):
        self.pushed = bool(pushed)


class _StubNode:
    def __init__(self, rect: Rect):
        self.rect = Rect(rect)


class _StubApp:
    def __init__(self, *, tiling_enabled: bool = True):
        self._nodes = {}
        self.tile_windows_calls = []
        self.surface = _StubSurface((800, 600))
        self._tiling_enabled = bool(tiling_enabled)
        self.window_tiling = _StubWindowTiling(self.surface)

    def find(self, control_id: str):
        return self._nodes.get(str(control_id))

    def tile_windows(self, *args, **kwargs) -> None:
        self.tile_windows_calls.append((args, kwargs))

    def is_window_tiling_enabled(self, scene_name=None) -> bool:
        return self._tiling_enabled


class _StubSurface:
    def __init__(self, size):
        self._size = tuple(size)

    def get_size(self):
        return self._size

    def get_rect(self):
        return Rect(0, 0, int(self._size[0]), int(self._size[1]))


class _StubWindowTiling:
    def __init__(self, surface: _StubSurface):
        self._surface = surface
        self.center_windows_calls = []

    def center_windows(self, windows):
        items = tuple(windows)
        self.center_windows_calls.append(items)
        bounds = self._surface.get_rect()
        for window in items:
            rect = getattr(window, "rect", None)
            move_by = getattr(window, "move_by", None)
            if rect is None or not callable(move_by):
                continue
            target_x = int(bounds.centerx - (int(rect.width) // 2))
            target_y = int(bounds.centery - (int(rect.height) // 2))
            dx = int(target_x - int(rect.x))
            dy = int(target_y - int(rect.y))
            if dx != 0 or dy != 0:
                move_by(dx, dy)


class _StubBinding:
    def __init__(self, button_id: str):
        self.task_panel_toggle_button_id = str(button_id)


class _StubWindow:
    def __init__(self):
        self.visible = False


class _ShowTileStubWindow(WindowControl):
    def __init__(self):
        super().__init__("demo_window", (180, 120), "Demo")
        self.window_effects = {"hide_show_enabled": True}


class _GrowShrinkStubWindow(WindowControl):
    def __init__(self):
        super().__init__("demo_window", (180, 120), "Demo")
        self.window_effects = {"grow_shrink_enabled": True}


class _PresentationStub:
    def __init__(self, *, return_value: bool = True):
        self.return_value = bool(return_value)
        self.calls = []

    def toggle_window(self, window):
        self.calls.append(window)
        return self.return_value


class _OverlayStub:
    def has_overlay(self, _owner_id):
        return False

    def hide(self, _owner_id):
        return None


class TestWindowVisibilityTransitionAndWindowListRouting(unittest.TestCase):
    def test_visibility_setter_uses_app_tile_windows_when_callback_not_supplied(self):
        app = _StubApp()
        window = WindowControl("demo_window", (180, 120), "Demo")
        window.window_effects = {}
        window.visible = False

        set_window_visible_state(
            window,
            True,
            app=app,
            binding=None,
        )

        self.assertTrue(window.visible)
        self.assertEqual(1, len(app.tile_windows_calls))

    def test_defaults_disable_visibility_transition_when_not_configured(self):
        app = _StubApp()
        window = WindowControl("demo_window", (180, 120), "Demo")
        window.window_effects = {}
        window.visible = True

        set_window_visible_state(
            window,
            False,
            tile_windows=app.tile_windows,
            app=app,
            binding=None,
        )

        self.assertIsNone(window.visibility_transition_controller)
        self.assertFalse(window.visible)
        self.assertEqual(1, len(app.tile_windows_calls))

    def test_hide_then_reverse_show_finishes_in_original_remaining_time(self):
        app = _StubApp()
        app._nodes["show_demo"] = _StubNode(Rect(20, 20, 48, 22))
        binding = _StubBinding("show_demo")
        toggle = _StubToggle(True)

        window = WindowControl("demo_window", (180, 120), "Demo")
        window.window_effects = {"hide_show_enabled": True}
        window.rect.topleft = (240, 180)
        window.visible = True

        set_window_visible_state(
            window,
            False,
            toggle=toggle,
            tile_windows=app.tile_windows,
            app=app,
            binding=binding,
        )

        controller = window.visibility_transition_controller
        self.assertIsNotNone(controller)
        self.assertFalse(window.visible)
        self.assertTrue(controller.is_active())
        self.assertTrue(window.is_visibility_transition_renderable())
        self.assertFalse(toggle.pushed)
        self.assertEqual(1, len(app.tile_windows_calls))
        self.assertEqual((44.0, 600.0), controller._target_center)

        half = controller.base_duration_seconds / 2.0
        window.update(half)
        mid_progress = controller.progress()

        self.assertGreater(mid_progress, 0.0)
        self.assertLess(mid_progress, 1.0)

        set_window_visible_state(
            window,
            True,
            toggle=toggle,
            tile_windows=app.tile_windows,
            app=app,
            binding=binding,
        )

        self.assertTrue(window.visible)
        self.assertTrue(controller.is_active())

        window.update(half * 0.99)
        self.assertTrue(controller.is_active())

        window.update(half * 0.01)
        self.assertFalse(controller.is_active())
        self.assertAlmostEqual(1.0, controller.progress(), places=4)
        self.assertGreaterEqual(len(app.tile_windows_calls), 2)

    def test_show_transition_targets_solved_tile_position_and_tracks_relayout(self):
        app = _StubApp()
        app._nodes["show_demo"] = _StubNode(Rect(20, 20, 48, 22))
        binding = _StubBinding("show_demo")
        toggle = _StubToggle(False)
        window = _ShowTileStubWindow()
        window.visible = False
        window.rect.topleft = (300, 220)

        def _tile_windows(*args, **kwargs):
            window._window_tiling_target_rect = Rect(120, 140, window.rect.width, window.rect.height)

        set_window_visible_state(
            window,
            True,
            toggle=toggle,
            tile_windows=_tile_windows,
            app=app,
            binding=binding,
        )

        controller = window.visibility_transition_controller
        self.assertIsNotNone(controller)
        self.assertEqual((210.0, 212.0), controller._resolved_target_center())

        window.update(controller.base_duration_seconds / 2.0)
        mid_center_before = controller._current_center()

        window._window_tiling_target_rect = Rect(200, 260, window.rect.width, window.rect.height)
        mid_center_after = controller._current_center()

        self.assertGreater(mid_center_after[0], mid_center_before[0])
        self.assertGreater(mid_center_after[1], mid_center_before[1])

    def test_near_complete_reverse_uses_elapsed_time_not_remaining_time(self):
        app = _StubApp()
        app._nodes["show_demo"] = _StubNode(Rect(20, 20, 48, 22))
        binding = _StubBinding("show_demo")
        window = _ShowTileStubWindow()
        window.visible = False
        window.rect.topleft = (300, 220)

        def _tile_windows(*args, **kwargs):
            window._window_tiling_target_rect = Rect(120, 140, window.rect.width, window.rect.height)

        set_window_visible_state(
            window,
            True,
            tile_windows=_tile_windows,
            app=app,
            binding=binding,
        )

        controller = window.visibility_transition_controller
        self.assertIsNotNone(controller)
        duration = controller.base_duration_seconds

        # Advance close to completion of show.
        window.update(duration * 0.9)
        self.assertTrue(controller.is_active())

        # Reverse to hide: reverse leg should use elapsed time (0.9 * duration),
        # not remaining time (0.1 * duration).
        set_window_visible_state(
            window,
            False,
            tile_windows=_tile_windows,
            app=app,
            binding=binding,
        )
        self.assertTrue(controller.is_active())

        # If remaining-time logic were used, this would have already finished.
        window.update(duration * 0.2)
        self.assertTrue(controller.is_active())

        # Finish the reverse leg.
        window.update(duration * 0.7)
        self.assertFalse(controller.is_active())

    def test_grow_shrink_hides_from_window_center_without_anchor_drift(self):
        app = _StubApp()
        app._nodes["show_demo"] = _StubNode(Rect(20, 20, 48, 22))
        binding = _StubBinding("show_demo")
        window = _GrowShrinkStubWindow()
        window.visible = True
        window.rect.topleft = (300, 220)
        starting_center = tuple(map(float, window.rect.center))

        set_window_visible_state(
            window,
            False,
            tile_windows=app.tile_windows,
            app=app,
            binding=binding,
        )

        controller = window.visibility_transition_controller
        self.assertIsNotNone(controller)
        self.assertEqual(starting_center, controller._target_center)

    def test_register_feature_window_rejects_conflicting_transition_modes(self):
        model = FeatureWindowPresentationModel(SimpleNamespace(app=None), tile_windows=None)

        with self.assertRaises(ValueError):
            model.register_feature_window(
                "demo",
                feature_attribute_name="_demo_feature",
                window_effects={
                    "hide_show_enabled": True,
                    "grow_shrink_enabled": True,
                },
            )

    def test_show_when_tiling_disabled_centers_only_target_window_and_skips_tile_solve(self):
        app = _StubApp(tiling_enabled=False)
        window = _ShowTileStubWindow()
        other = _ShowTileStubWindow()
        window.visible = False
        other.visible = True
        window.rect.topleft = (12, 18)
        other.rect.topleft = (66, 72)
        other_start = Rect(other.rect)

        set_window_visible_state(
            window,
            True,
            tile_windows=app.tile_windows,
            app=app,
            binding=None,
        )

        self.assertEqual(0, len(app.tile_windows_calls))
        self.assertEqual(1, len(app.window_tiling.center_windows_calls))
        centered_windows = app.window_tiling.center_windows_calls[0]
        self.assertEqual((window,), centered_windows)
        self.assertEqual(app.surface.get_rect().center, window.rect.center)
        self.assertEqual(other_start.topleft, other.rect.topleft)

    def test_menu_bar_window_list_routes_through_window_presentation(self):
        presentation = _PresentationStub(return_value=True)
        window = _StubWindow()
        menu = MenuStripControl(
            "menu",
            app=None,
            window_presentation=presentation,
        )

        menu._toggle_window(window)

        self.assertEqual([window], presentation.calls)
        self.assertFalse(window.visible)

    def test_command_palette_window_list_routes_through_window_presentation(self):
        presentation = _PresentationStub(return_value=True)
        window = _StubWindow()
        manager = CommandPaletteManager(_OverlayStub())
        manager._window_presentation = presentation

        manager._toggle_builtin_window(_StubApp(), window)

        self.assertEqual([window], presentation.calls)
        self.assertFalse(window.visible)


if __name__ == "__main__":
    unittest.main()
