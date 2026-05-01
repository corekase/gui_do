import unittest

import pygame

from gui_do import ButtonControl, LabelControl
from demo_features.systems_demo_feature import SystemsDemoFeature


class _StubWindow:
    def __init__(self):
        self.added = []

    def add(self, control):
        self.added.append(control)
        return control


class TestSystemsDemoFeatureAbstractions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def _make_feature(self) -> SystemsDemoFeature:
        feature = SystemsDemoFeature()
        feature.window = _StubWindow()
        return feature

    def test_add_tab_control_adds_to_window_and_list(self):
        feature = self._make_feature()
        controls = []
        label = LabelControl("label_id", pygame.Rect(0, 0, 120, 20), "Label", align="left")

        added = feature._add_tab_control(controls, label)

        self.assertIs(label, added)
        self.assertEqual([label], controls)
        self.assertEqual([label], feature.window.added)

    def test_add_tab_label_creates_left_aligned_label(self):
        feature = self._make_feature()
        controls = []

        label = feature._add_tab_label(
            controls,
            "test_label",
            pygame.Rect(10, 20, 240, 22),
            "Hello",
        )

        self.assertIsInstance(label, LabelControl)
        self.assertEqual("test_label", label.control_id)
        self.assertEqual("Hello", label.text)
        self.assertEqual("left", label.align)
        self.assertEqual([label], controls)
        self.assertEqual([label], feature.window.added)

    def test_add_tab_button_creates_button_and_tracks_it(self):
        feature = self._make_feature()
        controls = []

        def on_click():
            return None

        button = feature._add_tab_button(
            controls,
            "test_button",
            pygame.Rect(8, 12, 140, 28),
            "Run",
            on_click,
        )

        self.assertIsInstance(button, ButtonControl)
        self.assertEqual("test_button", button.control_id)
        self.assertEqual("Run", button.text)
        self.assertEqual([button], controls)
        self.assertEqual([button], feature.window.added)


if __name__ == "__main__":
    unittest.main()
