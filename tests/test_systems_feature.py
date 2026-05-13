import unittest

import pygame
from pygame import Rect

from demo_features.systems.systems_feature import SystemsFeature


class _HostStub:
    def __init__(self):
        self.screen_rect = Rect(0, 0, 1000, 800)


class TestSystemsFeature(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()
        if pygame.display.get_surface() is None:
            pygame.display.set_mode((1, 1))

    def _make_feature(self) -> SystemsFeature:
        feature = SystemsFeature()
        self.addCleanup(feature._task_scheduler.shutdown)
        return feature

    def test_tab_definitions_include_new_runtime_tabs(self):
        self.assertEqual(
            [
                "data",
                "validation",
                "history",
                "theme",
                "state",
                "infrastructure",
                "scheduling",
                "motion",
                "persistence",
                "graphics",
                "text",
            ],
            [key for key, _label in SystemsFeature.TAB_DEFINITIONS],
        )

    def test_window_spec_uses_eighty_percent_screen_size(self):
        feature = self._make_feature()

        spec = feature._make_window_spec(_HostStub())

        self.assertEqual((800, 640), spec.size)
        self.assertEqual("center", spec.anchor)

    def test_workspace_state_serializes_registered_settings(self):
        feature = self._make_feature()
        feature._apply_production_profile()

        state = feature._build_workspace_state()

        self.assertEqual("production", state.metadata["profile"])
        self.assertEqual("production", state.settings_blocks["systems"]["systems"]["profile"])
        self.assertEqual(4, state.settings_blocks["systems"]["systems"]["parallel_checks"])

    def test_graphics_demo_burst_creates_particles(self):
        feature = self._make_feature()
        feature.build_graphics_panel(Rect(0, 0, 640, 360))

        feature._trigger_particle_burst()
        feature._advance_graphics_demo(0.1)

        self.assertEqual(2, feature._particle_layer.particle_system.emitter_count)
        self.assertGreater(feature._particle_layer.particle_system.active_particle_count, 0)

    def test_graphics_runtime_updates_tile_map_status(self):
        feature = self._make_feature()
        feature.build_graphics_panel(Rect(0, 0, 640, 420))

        feature._advance_graphics_runtime()

        self.assertIsNotNone(feature.graphics_tile_map_label)
        self.assertIn("TileMap camera=", feature.graphics_tile_map_label.text)
        self.assertIn("visible_tiles=", feature.graphics_tile_map_label.text)
        self.assertIsNotNone(feature.graphics_tile_preview_canvas)
        preview_surface = feature.graphics_tile_preview_canvas.get_canvas_surface()
        sampled = preview_surface.get_at((4, 4))
        self.assertNotEqual((0, 0, 0, 0), tuple(sampled))

    def test_graphics_tile_preview_is_right_aligned_and_pans(self):
        feature = self._make_feature()
        panel = feature.build_graphics_panel(Rect(0, 0, 700, 420))

        self.assertIsNotNone(feature.graphics_tile_preview_canvas)
        preview_rect = feature.graphics_tile_preview_canvas.rect
        self.assertGreaterEqual(preview_rect.left, panel.rect.width // 2)
        self.assertLessEqual(preview_rect.right, panel.rect.width - feature.PANEL_PADDING_X)

        start = feature._graphics_tile_camera.topleft
        feature._pan_tile_camera(24, 24)
        self.assertNotEqual(start, feature._graphics_tile_camera.topleft)

        feature._pan_tile_camera(10_000, 10_000)
        max_x = max(0, feature._graphics_tile_map.pixel_width - feature._graphics_tile_camera.width)
        max_y = max(0, feature._graphics_tile_map.pixel_height - feature._graphics_tile_camera.height)
        self.assertEqual((max_x, max_y), feature._graphics_tile_camera.topleft)

        nav_ids = {
            "systems_graphics_nav_left",
            "systems_graphics_nav_up",
            "systems_graphics_nav_down",
            "systems_graphics_nav_right",
        }
        panel_child_ids = {child.control_id for child in panel.children}
        self.assertIn("systems_graphics_tile_nav_cluster", panel_child_ids)

        nav_cluster = next(child for child in panel.children if child.control_id == "systems_graphics_tile_nav_cluster")
        nav_child_ids = {child.control_id for child in nav_cluster.children}
        self.assertTrue(nav_ids.issubset(nav_child_ids))
        self.assertGreaterEqual(nav_cluster.rect.left, panel.rect.left)
        self.assertLessEqual(nav_cluster.rect.right, panel.rect.right)
        self.assertLess(nav_cluster.rect.right, preview_rect.left)
        for child in nav_cluster.children:
            self.assertTrue(nav_cluster.rect.contains(child.rect))

        start_x = feature._graphics_tile_camera.x
        right_arrow = next(child for child in nav_cluster.children if child.control_id == "systems_graphics_nav_right")
        right_arrow._invoke_click()
        self.assertGreaterEqual(feature._graphics_tile_camera.x, start_x)

    def test_scheduling_rate_limiter_simulation_updates_status(self):
        feature = self._make_feature()
        feature.build_scheduling_panel(Rect(0, 0, 640, 360))

        feature._simulate_rate_limited_input()
        self.assertIn("Burst queued", feature._rate_limiter_status)
        self.assertTrue(feature._debouncer.is_pending)
        self.assertTrue(feature._throttler.is_locked)

        feature._timers.update(0.13)
        self.assertGreaterEqual(feature._throttle_event_count, 1)
        self.assertIn("Throttler sampled value", feature._rate_limiter_status)

        feature._timers.update(0.25)
        self.assertGreaterEqual(feature._debounce_commit_count, 1)
        self.assertIn("Debouncer committed", feature._rate_limiter_status)
        self.assertIsNotNone(feature.scheduling_rate_limiter_label)
        self.assertIn("debounced_commits=", feature.scheduling_rate_limiter_label.text)

    def test_motion_panel_initializes_animation_state_machine_lazily(self):
        feature = self._make_feature()

        self.assertIsNone(feature._motion_animation_state_machine.current_state)
        panel = feature.build_motion_panel(Rect(0, 0, 640, 360))

        self.assertEqual("idle", feature._motion_animation_state_machine.current_state)
        panel_child_ids = {child.control_id for child in panel.children}
        self.assertIn("systems_motion_transition", panel_child_ids)
        self.assertIn("systems_motion_asm", panel_child_ids)

    def test_motion_transition_toggle_updates_phase_and_value(self):
        feature = self._make_feature()
        feature.build_motion_panel(Rect(0, 0, 640, 360))

        feature._toggle_motion_transition()
        self.assertEqual("Show", feature._motion_transition_phase)
        feature._motion_tweens.update(0.3)
        self.assertGreater(feature._motion_transition_value, 0.0)

        feature._toggle_motion_transition()
        self.assertEqual("Hide", feature._motion_transition_phase)

    def test_motion_animation_state_cycle_changes_state(self):
        feature = self._make_feature()
        feature.build_motion_panel(Rect(0, 0, 640, 360))

        self.assertEqual("idle", feature._motion_animation_state)
        feature._cycle_motion_animation_state()
        self.assertEqual("hover", feature._motion_animation_state)
        feature._cycle_motion_animation_state()
        self.assertEqual("press", feature._motion_animation_state)

    def test_text_panel_localization_and_search_updates_labels(self):
        feature = self._make_feature()
        panel = feature.build_text_panel(Rect(0, 0, 640, 360))

        panel_child_ids = {child.control_id for child in panel.children}
        self.assertIn("systems_text_preview", panel_child_ids)
        self.assertIn("systems_text_search", panel_child_ids)

        feature._on_text_locale_changed("es")
        feature._on_text_query_changed("despliegue")
        feature._run_text_search()

        self.assertIsNotNone(feature.text_search_status_label)
        self.assertIn("active=ES", feature.text_search_status_label.text)
        self.assertIsNotNone(feature.text_search_match_label)
        self.assertIn("TextSearcher", feature.text_search_match_label.text)


if __name__ == "__main__":
    unittest.main()
