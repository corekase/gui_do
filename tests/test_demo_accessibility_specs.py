import unittest

from gui_do import (
    build_host_main_tab_order,
    apply_host_main_accessibility,
    collect_window_toggle_controls,
)
from demo_features.demo_config import STATIC_ACCESSIBILITY_SPECS


class _StubControl:
    def __init__(self, name: str):
        self.name = str(name)
        self.tab_indices = []
        self.accessibility_calls = []

    def set_tab_index(self, index: int):
        self.tab_indices.append(int(index))

    def set_accessibility(self, *, role: str, label: str):
        self.accessibility_calls.append((str(role), str(label)))


class _StubBinding:
    def __init__(self, *, key, toggle_attr, accessibility_label, action_label, task_panel_slot_index, tab_before_showcase):
        self.key = str(key)
        self.toggle_attr = toggle_attr
        self.accessibility_label = accessibility_label
        self.action_label = action_label
        self.task_panel_slot_index = task_panel_slot_index
        self.tab_before_showcase = bool(tab_before_showcase)


class _StubWindowPresentation:
    def __init__(self, bindings):
        self._bindings = list(bindings)

    def bindings(self):
        return tuple(self._bindings)


class _StubHost:
    def __init__(self):
        self.exit_button = _StubControl("exit")
        self.showcase_button = _StubControl("showcase")
        self.systems_toggle_window = _StubControl("systems")
        self.life_toggle_window = _StubControl("life")
        self.mandel_toggle_window = _StubControl("mandel")
        self.window_presentation = _StubWindowPresentation([
            _StubBinding(key="systems", toggle_attr="systems_toggle_window", accessibility_label="Show Systems window",
                         action_label="Show Systems Window", task_panel_slot_index=1, tab_before_showcase=True),
            _StubBinding(key="life", toggle_attr="life_toggle_window", accessibility_label="Show Life window",
                         action_label="Show Life Window", task_panel_slot_index=3, tab_before_showcase=False),
            _StubBinding(key="mandel", toggle_attr="mandel_toggle_window", accessibility_label="Show Mandelbrot window",
                         action_label="Show Mandelbrot Window", task_panel_slot_index=4, tab_before_showcase=False),
        ])


class TestDemoAccessibilitySpecs(unittest.TestCase):
    def test_main_accessibility_order_places_showcase_after_first_toggle(self):
        host = _StubHost()
        toggles = collect_window_toggle_controls(host, host.window_presentation)
        self.assertEqual(["systems", "life", "mandel"], [b.key for b, _ in toggles])
        ordered = build_host_main_tab_order(host, toggles)
        self.assertEqual([host.exit_button, host.systems_toggle_window, host.showcase_button,
                          host.life_toggle_window, host.mandel_toggle_window], ordered)
        self.assertEqual([], host.exit_button.tab_indices)
        self.assertEqual([], host.systems_toggle_window.tab_indices)
        self.assertEqual([], host.showcase_button.tab_indices)
        self.assertEqual([], host.life_toggle_window.tab_indices)
        self.assertEqual([], host.mandel_toggle_window.tab_indices)

    def test_accessibility_applies_static_and_toggle_labels(self):
        host = _StubHost()
        ordered = [host.exit_button, host.systems_toggle_window, host.showcase_button]
        apply_host_main_accessibility(host, ordered, STATIC_ACCESSIBILITY_SPECS)
        self.assertEqual([("button", "Exit")], host.exit_button.accessibility_calls)
        self.assertEqual([("button", "Showcase")], host.showcase_button.accessibility_calls)
        self.assertEqual([("toggle", "Show Systems window")], host.systems_toggle_window.accessibility_calls)
        self.assertEqual([("toggle", "Show Life window")], host.life_toggle_window.accessibility_calls)
        self.assertEqual([("toggle", "Show Mandelbrot window")], host.mandel_toggle_window.accessibility_calls)


if __name__ == "__main__":
    unittest.main()
