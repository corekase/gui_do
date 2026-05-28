import unittest
from types import SimpleNamespace

import pygame
from pygame import Rect

from gui_do.controls.chrome.menu_bar_control import MenuStripControl
from gui_do.graphics.shear_window import ShearWindowController
from gui_do.graphics.window_effect_scratch_pad import WindowEffectScratchPad
from gui_do.graphics.window_visibility_transition import WindowVisibilityTransitionController
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
        self.raise_calls = []
        self.lower_calls = []
        self.surface = _StubSurface((800, 600))
        self._tiling_enabled = bool(tiling_enabled)
        self.window_tiling = _StubWindowTiling(self.surface)

    def find(self, control_id: str):
        return self._nodes.get(str(control_id))

    def tile_windows(self, *args, **kwargs) -> None:
        self.tile_windows_calls.append((args, kwargs))

    def is_window_tiling_enabled(self, scene_name=None) -> bool:
        return self._tiling_enabled

    def raise_window(self, window, *, relayout: bool = True, scene_name=None) -> bool:
        _ = scene_name
        self.raise_calls.append({"window": window, "relayout": bool(relayout)})
        parent = getattr(window, "parent", None)
        raise_window = getattr(parent, "_raise_window", None)
        if callable(raise_window):
            raise_window(window)
        return True

    def lower_window(self, window, *, relayout: bool = True, scene_name=None) -> bool:
        _ = scene_name
        self.lower_calls.append({"window": window, "relayout": bool(relayout)})
        parent = getattr(window, "parent", None)
        lower_window = getattr(parent, "_lower_window", None)
        if callable(lower_window):
            lower_window(window)
        return True


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


class _StubFocus:
    def __init__(self):
        self.clear_calls = 0

    def clear_focus(self):
        self.clear_calls += 1


class _StubWindow:
    def __init__(self):
        self.visible = False


class _ScratchPadStubWindow:
    def __init__(self):
        self.rect = Rect(10, 10, 120, 80)
        self.visible = True


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


class _RaiseParentStub:
    def __init__(self):
        self.raised = []

    def _raise_window(self, window):
        self.raised.append(window)

    def _on_window_visibility_changed(self, _window, _old_visible: bool, _new_visible: bool) -> None:
        return None


class TestWindowVisibilityTransitionAndWindowListRouting(unittest.TestCase):
    def test_visibility_transition_effect_uses_live_window_draw_each_frame(self):
        target = pygame.Surface((640, 480), pygame.SRCALPHA)

        for mode_name, effects in (
            ("hide_show", {"hide_show_enabled": True}),
            ("grow_shrink", {"grow_shrink_enabled": True}),
        ):
            with self.subTest(mode=mode_name):
                window = WindowControl(f"demo_window_{mode_name}", (180, 120), "Demo")
                window.window_effects = effects
                window.visible = True
                window.rect.topleft = (120, 80)
                center = tuple(map(int, window.rect.center))

                # Make the draw output obviously frame-varying so the transition
                # effect must sample fresh content each render.
                frame_color = [(220, 40, 40, 255)]

                def _draw_standard(surface, _theme, force_visible_visuals=False):
                    del force_visible_visuals
                    surface.fill(frame_color[0])

                window._draw_standard = _draw_standard
                window.begin_visibility_transition(False, app=None, binding=None)
                self.assertTrue(window.is_visibility_transition_renderable())

                target.fill((0, 0, 0, 0))
                window.draw(target, object())
                first_frame = target.get_at(center)

                frame_color[0] = (40, 200, 80, 255)
                target.fill((0, 0, 0, 0))
                window.draw(target, object())
                second_frame = target.get_at(center)

                self.assertNotEqual(first_frame, second_frame)
                self.assertEqual((40, 200, 80, 255), tuple(second_frame))

    def test_shear_and_visibility_share_common_window_effect_buffer_slot(self):
        WindowEffectScratchPad.dispose_all()
        shear = ShearWindowController(_ScratchPadStubWindow())
        visibility = WindowVisibilityTransitionController(_ScratchPadStubWindow())
        surface = pygame.Surface((400, 300), pygame.SRCALPHA)

        shear._refresh_buffer(surface, theme=object(), draw_window_standard=lambda _s, _t: None)
        shared = shear.buffer
        self.assertIsNotNone(shared)

        visibility._ensure_buffer_capacity((100, 60))
        self.assertIs(shared, visibility.buffer)

        visibility._ensure_buffer_capacity((220, 160))
        self.assertIsNot(shared, visibility.buffer)
        self.assertIs(visibility.buffer, shear.buffer)

        shear.dispose()
        visibility.dispose()

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
        self.assertEqual((44.0, 31.0), controller._target_center)

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

    def test_hide_and_show_anchor_use_button_center_for_varied_button_rects(self):
        for index, button_rect in enumerate(
            (
                Rect(4, 572, 40, 24),
                Rect(160, 560, 96, 32),
                Rect(420, 578, 120, 18),
                Rect(700, 548, 84, 44),
            )
        ):
            with self.subTest(case=index, button_rect=tuple(button_rect)):
                app = _StubApp()
                button_id = f"show_demo_{index}"
                app._nodes[button_id] = _StubNode(button_rect)
                binding = _StubBinding(button_id)

                hide_window = WindowControl(f"hide_demo_{index}", (180, 120), "Demo")
                hide_window.window_effects = {"hide_show_enabled": True}
                hide_window.rect.topleft = (240, 180)
                hide_window.visible = True
                set_window_visible_state(
                    hide_window,
                    False,
                    tile_windows=app.tile_windows,
                    app=app,
                    binding=binding,
                )
                hide_controller = hide_window.visibility_transition_controller
                self.assertIsNotNone(hide_controller)
                self.assertEqual(
                    (float(button_rect.centerx), float(button_rect.centery)),
                    hide_controller._target_center,
                )

                show_window = _ShowTileStubWindow()
                show_window.visible = False
                show_window.rect.topleft = (300, 220)

                def _tile_windows(*args, **kwargs):
                    show_window._window_tiling_target_rect = Rect(
                        120,
                        140,
                        show_window.rect.width,
                        show_window.rect.height,
                    )

                set_window_visible_state(
                    show_window,
                    True,
                    tile_windows=_tile_windows,
                    app=app,
                    binding=binding,
                )
                show_controller = show_window.visibility_transition_controller
                self.assertIsNotNone(show_controller)
                self.assertEqual(
                    (float(button_rect.centerx), float(button_rect.centery)),
                    show_controller._start_center,
                )

    def test_show_transition_freezes_solved_tile_target_during_animation(self):
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

        self.assertEqual(mid_center_before, mid_center_after)

    def test_show_transition_completion_uses_frozen_target_when_external_retile_changes_target(self):
        app = _StubApp()
        app._nodes["show_demo"] = _StubNode(Rect(20, 20, 48, 22))
        binding = _StubBinding("show_demo")
        window = _ShowTileStubWindow()
        window.visible = False
        window.rect.topleft = (300, 220)
        window.parent = _RaiseParentStub()

        initial_target = Rect(120, 140, window.rect.width, window.rect.height)
        external_target = Rect(260, 280, window.rect.width, window.rect.height)

        def _tile_windows(*args, **kwargs):
            app.tile_windows(*args, **kwargs)
            window._window_tiling_target_rect = Rect(initial_target)

        set_window_visible_state(
            window,
            True,
            tile_windows=_tile_windows,
            app=app,
            binding=binding,
        )

        controller = window.visibility_transition_controller
        self.assertIsNotNone(controller)
        self.assertEqual((float(initial_target.centerx), float(initial_target.centery)), controller._resolved_target_center())

        # Simulate a different window visibility relayout changing this window's
        # tiling target while the show transition is already in flight.
        window._window_tiling_target_rect = Rect(external_target)
        window.update(controller.base_duration_seconds)

        self.assertFalse(controller.is_active())
        self.assertEqual(initial_target.topleft, window.rect.topleft)
        self.assertEqual(initial_target.topleft, getattr(window, "_window_tiling_target_rect").topleft)

    def test_show_transition_completion_does_not_retile_and_only_re_raises(self):
        app = _StubApp()
        app._nodes["show_demo"] = _StubNode(Rect(20, 20, 48, 22))
        binding = _StubBinding("show_demo")
        window = _ShowTileStubWindow()
        window.visible = False
        window.rect.topleft = (300, 220)
        window.parent = _RaiseParentStub()

        def _tile_windows(*args, **kwargs):
            app.tile_windows(*args, **kwargs)
            window._window_tiling_target_rect = Rect(120, 140, window.rect.width, window.rect.height)

        set_window_visible_state(
            window,
            True,
            tile_windows=_tile_windows,
            app=app,
            binding=binding,
        )
        pre_completion_tile_count = len(app.tile_windows_calls)
        pre_completion_raise_count = len(window.parent.raised)

        controller = window.visibility_transition_controller
        self.assertIsNotNone(controller)
        window.update(controller.base_duration_seconds)

        self.assertFalse(controller.is_active())
        self.assertEqual(pre_completion_tile_count, len(app.tile_windows_calls))
        self.assertEqual(pre_completion_raise_count + 1, len(window.parent.raised))
        self.assertIs(window, window.parent.raised[-1])

    def test_show_transition_completion_snaps_live_window_to_solved_target(self):
        app = _StubApp()
        app._nodes["show_demo"] = _StubNode(Rect(20, 20, 48, 22))
        binding = _StubBinding("show_demo")
        window = _ShowTileStubWindow()
        window.visible = False
        window.rect.topleft = (300, 220)
        window.parent = _RaiseParentStub()

        solved_target = Rect(120, 140, window.rect.width, window.rect.height)

        def _tile_windows(*args, **kwargs):
            app.tile_windows(*args, **kwargs)
            window._window_tiling_target_rect = Rect(solved_target)

        set_window_visible_state(
            window,
            True,
            tile_windows=_tile_windows,
            app=app,
            binding=binding,
        )

        # Simulate lagging live geometry relative to solved target near completion.
        window.rect.topleft = (solved_target.x - 40, solved_target.y + 26)

        controller = window.visibility_transition_controller
        self.assertIsNotNone(controller)
        window.update(controller.base_duration_seconds)

        self.assertFalse(controller.is_active())
        self.assertEqual(solved_target.topleft, window.rect.topleft)

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

    def test_visibility_transition_clears_focus_on_entry(self):
        app = _StubApp()
        app.focus = _StubFocus()
        window = _GrowShrinkStubWindow()
        window.visible = True

        set_window_visible_state(
            window,
            False,
            tile_windows=app.tile_windows,
            app=app,
            binding=None,
        )

        self.assertEqual(1, app.focus.clear_calls)

    def test_hide_transition_completion_does_not_issue_additional_retile(self):
        app = _StubApp()
        window = _ShowTileStubWindow()
        window.visible = True

        set_window_visible_state(
            window,
            False,
            tile_windows=app.tile_windows,
            app=app,
            binding=None,
        )

        controller = window.visibility_transition_controller
        self.assertIsNotNone(controller)
        self.assertEqual(1, len(app.tile_windows_calls))

        window.update(controller.base_duration_seconds)

        self.assertFalse(controller.is_active())
        self.assertEqual(1, len(app.tile_windows_calls))

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

    def test_show_when_layout_disabled_skips_tile_solve_and_leaves_window_position_unchanged(self):
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
        self.assertEqual(0, len(app.window_tiling.center_windows_calls))
        self.assertEqual((12, 18), window.rect.topleft)
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

    def test_menu_bar_builtin_window_toggle_reorders_before_relayout(self):
        app = _StubApp()
        window = _StubWindow()
        menu = MenuStripControl("menu", app=app)

        menu._toggle_window(window)

        self.assertTrue(window.visible)
        self.assertEqual([{"window": window, "relayout": False}], app.raise_calls)
        self.assertEqual((window,), app.tile_windows_calls[0][1]["raised_windows"])

    def test_command_palette_window_list_routes_through_window_presentation(self):
        presentation = _PresentationStub(return_value=True)
        window = _StubWindow()
        manager = CommandPaletteManager(_OverlayStub())
        manager._window_presentation = presentation

        manager._toggle_builtin_window(_StubApp(), window)

        self.assertEqual([window], presentation.calls)
        self.assertFalse(window.visible)

    def test_command_palette_builtin_window_toggle_demotes_before_hide_relayout(self):
        app = _StubApp()
        window = _StubWindow()
        window.visible = True
        manager = CommandPaletteManager(_OverlayStub())

        manager._toggle_builtin_window(app, window)

        self.assertFalse(window.visible)
        self.assertEqual([{"window": window, "relayout": False}], app.lower_calls)
        self.assertEqual(1, len(app.tile_windows_calls))


if __name__ == "__main__":
    unittest.main()
