import unittest

from demo_features.showcase.showcase_feature import (
    apply_category_visibility,
    category_for_row,
)
from gui_do.features.feature_lifecycle import PlacedControl


class _DummyNode:
    def __init__(self):
        self.visible = True
        self.enabled = True


class TestCategoryForRow(unittest.TestCase):
    def test_category_for_row_thresholds(self):
        self.assertEqual("basics", category_for_row(0))
        self.assertEqual("basics", category_for_row(59))
        self.assertEqual("data", category_for_row(60))
        self.assertEqual("advanced", category_for_row(100))
        self.assertEqual("extended", category_for_row(140))

    def test_category_for_row_extended_above_boundary(self):
        self.assertEqual("extended", category_for_row(200))
        self.assertEqual("extended", category_for_row(999))

    def test_category_for_row_advanced_range(self):
        self.assertEqual("advanced", category_for_row(100))
        self.assertEqual("advanced", category_for_row(139))


class TestApplyCategoryVisibility(unittest.TestCase):
    def _make_placed(self, control, label, name, row_index):
        return PlacedControl(control, label, name, 0, row_index)

    def test_basics_active_shows_basics_hides_others(self):
        basics_control = _DummyNode()
        basics_label = _DummyNode()
        data_control = _DummyNode()
        data_label = _DummyNode()
        orphan_label = _DummyNode()

        placed_controls = [
            self._make_placed(basics_control, basics_label, "button", 0),
            self._make_placed(data_control, data_label, "list_view", 70),
        ]
        control_labels = [basics_label, data_label, orphan_label]

        apply_category_visibility(
            active_key="basics",
            placed_controls=placed_controls,
            control_labels=control_labels,
        )

        self.assertTrue(basics_control.visible)
        self.assertTrue(basics_control.enabled)
        self.assertTrue(basics_label.visible)
        self.assertTrue(basics_label.enabled)

        self.assertFalse(data_control.visible)
        self.assertFalse(data_control.enabled)
        self.assertFalse(data_label.visible)
        self.assertFalse(data_label.enabled)

        self.assertFalse(orphan_label.visible)
        self.assertFalse(orphan_label.enabled)

    def test_data_active_shows_data_hides_basics(self):
        data_control = _DummyNode()
        data_label = _DummyNode()
        basics_control = _DummyNode()
        basics_label = _DummyNode()

        placed_controls = [
            self._make_placed(data_control, data_label, "list_view", 70),
            self._make_placed(basics_control, basics_label, "button", 4),
        ]
        control_labels = [data_label, basics_label]

        apply_category_visibility(
            active_key="data",
            placed_controls=placed_controls,
            control_labels=control_labels,
        )

        self.assertTrue(data_control.visible)
        self.assertTrue(data_label.visible)
        self.assertFalse(basics_control.visible)
        self.assertFalse(basics_label.visible)

    def test_control_without_label_handled(self):
        control = _DummyNode()
        placed = PlacedControl(control, None, "canvas", 0, 67)

        apply_category_visibility(
            active_key="data",
            placed_controls=[placed],
            control_labels=[],
        )

        self.assertTrue(control.visible)
        self.assertTrue(control.enabled)

    def test_advanced_and_extended_boundaries(self):
        adv_control = _DummyNode()
        adv_label = _DummyNode()
        ext_control = _DummyNode()
        ext_label = _DummyNode()

        placed_controls = [
            self._make_placed(adv_control, adv_label, "spinner", 100),
            self._make_placed(ext_control, ext_label, "toolbar", 140),
        ]
        control_labels = [adv_label, ext_label]

        apply_category_visibility(
            active_key="advanced",
            placed_controls=placed_controls,
            control_labels=control_labels,
        )

        self.assertTrue(adv_control.visible)
        self.assertTrue(adv_label.visible)
        self.assertFalse(ext_control.visible)
        self.assertFalse(ext_label.visible)

    def test_all_labels_show_when_all_belong_to_active_category(self):
        controls = [_DummyNode() for _ in range(3)]
        labels = [_DummyNode() for _ in range(3)]
        placed = [
            self._make_placed(controls[i], labels[i], f"ctrl_{i}", i)
            for i in range(3)
        ]

        apply_category_visibility(
            active_key="basics",
            placed_controls=placed,
            control_labels=labels,
        )

        for c, l in zip(controls, labels):
            self.assertTrue(c.visible)
            self.assertTrue(l.visible)


if __name__ == "__main__":
    unittest.main()
