import unittest

from pygame import Rect

from demo_features.systems.systems_feature import SystemsFeature


class _HostStub:
    def __init__(self):
        self.screen_rect = Rect(0, 0, 1000, 800)


class TestSystemsFeature(unittest.TestCase):
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
                "persistence",
                "graphics",
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


if __name__ == "__main__":
    unittest.main()
