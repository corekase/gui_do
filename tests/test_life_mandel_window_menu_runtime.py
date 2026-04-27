import unittest
from types import SimpleNamespace

from demo_features.life_demo_feature import LifeSimulationFeature
from demo_features.mandelbrot_demo_feature import MandelbrotRenderFeature


class LifeWindowMenuRuntimeTests(unittest.TestCase):
    def test_life_menu_contains_minimize(self) -> None:
        feature = LifeSimulationFeature()

        entries = feature._menu_entries()

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].label, "File")
        self.assertEqual(entries[0].items[0].label, "Minimize")

    def test_life_minimize_updates_host_visibility(self) -> None:
        called = {"count": 0}
        feature = LifeSimulationFeature()
        feature.window = SimpleNamespace(visible=True)
        feature.demo = SimpleNamespace(
            set_life_window_visible=lambda _value: called.__setitem__("count", called["count"] + 1),
            life_toggle_window=SimpleNamespace(pushed=True),
        )

        feature._minimize_window()

        self.assertFalse(feature.window.visible)
        self.assertEqual(called["count"], 1)


class MandelWindowMenuRuntimeTests(unittest.TestCase):
    def test_mandel_menu_contains_minimize(self) -> None:
        feature = MandelbrotRenderFeature()

        entries = feature._menu_entries()

        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].label, "File")
        self.assertEqual(entries[0].items[0].label, "Minimize")

    def test_mandel_minimize_updates_host_visibility(self) -> None:
        called = {"count": 0}
        feature = MandelbrotRenderFeature()
        feature.window = SimpleNamespace(visible=True)
        feature.demo = SimpleNamespace(
            set_mandel_window_visible=lambda _value: called.__setitem__("count", called["count"] + 1),
            mandel_toggle_window=SimpleNamespace(pushed=True),
        )

        feature._minimize_window()

        self.assertFalse(feature.window.visible)
        self.assertEqual(called["count"], 1)


if __name__ == "__main__":
    unittest.main()
