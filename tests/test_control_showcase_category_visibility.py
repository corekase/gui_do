import unittest

from gui_do import apply_category_visibility
from demo_features.showcase.showcase_helpers import category_for_row
from gui_do.features.feature_lifecycle import PlacedControl


class _DummyNode:
    def __init__(self):
        self.visible = True
        self.enabled = True


class TestCategoryForRow(unittest.TestCase):
    def test_category_for_row_thresholds(self):
        self.assertEqual("display", category_for_row(0))
        self.assertEqual("input", category_for_row(9))
        self.assertEqual("input", category_for_row(12))
        self.assertEqual("data_bound", category_for_row(60))
        self.assertEqual("composite", category_for_row(100))
        self.assertEqual("chrome", category_for_row(140))

    def test_category_for_row_extended_above_boundary(self):
        self.assertEqual("display", category_for_row(200))
        self.assertEqual("display", category_for_row(999))

    def test_category_for_row_advanced_range(self):
        self.assertEqual("composite", category_for_row(100))
        self.assertEqual("composite", category_for_row(139))


class TestApplyCategoryVisibility(unittest.TestCase):
    def _make_placed(self, control, label, name, row_index):
        return PlacedControl(control, label, name, 0, row_index)

    def test_input_active_shows_input_hides_others(self):
        basics_control = _DummyNode()
        basics_label = _DummyNode()
        data_control = _DummyNode()
        data_label = _DummyNode()
        orphan_label = _DummyNode()

        placed_controls = [
            self._make_placed(basics_control, basics_label, "button", 1),
            self._make_placed(data_control, data_label, "list_view", 70),
        ]
        control_labels = [basics_label, data_label, orphan_label]

        apply_category_visibility(
            active_key="input",
            placed_controls=placed_controls,
            control_labels=control_labels,
            category_fn=category_for_row,
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

    def test_data_bound_active_shows_data_hides_input(self):
        data_control = _DummyNode()
        data_label = _DummyNode()
        basics_control = _DummyNode()
        basics_label = _DummyNode()

        placed_controls = [
            self._make_placed(data_control, data_label, "list_view", 70),
            self._make_placed(basics_control, basics_label, "button", 1),
        ]
        control_labels = [data_label, basics_label]

        apply_category_visibility(
            active_key="data_bound",
            placed_controls=placed_controls,
            control_labels=control_labels,
            category_fn=category_for_row,
        )

        self.assertTrue(data_control.visible)
        self.assertTrue(data_label.visible)
        self.assertFalse(basics_control.visible)
        self.assertFalse(basics_label.visible)

    def test_control_without_label_handled(self):
        control = _DummyNode()
        placed = PlacedControl(control, None, "canvas", 0, 16)

        apply_category_visibility(
            active_key="display",
            placed_controls=[placed],
            control_labels=[],
            category_fn=category_for_row,
        )

        self.assertTrue(control.visible)
        self.assertTrue(control.enabled)

    def test_composite_and_chrome_boundaries(self):
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
            active_key="composite",
            placed_controls=placed_controls,
            control_labels=control_labels,
            category_fn=category_for_row,
        )

        self.assertTrue(adv_control.visible)
        self.assertTrue(adv_label.visible)
        self.assertFalse(ext_control.visible)
        self.assertFalse(ext_label.visible)

    def test_all_labels_show_when_all_belong_to_active_category(self):
        controls = [_DummyNode() for _ in range(3)]
        labels = [_DummyNode() for _ in range(3)]
        placed = [
            self._make_placed(controls[0], labels[0], "ctrl_0", 0),
            self._make_placed(controls[1], labels[1], "ctrl_1", 10),
            self._make_placed(controls[2], labels[2], "ctrl_2", 11),
        ]

        apply_category_visibility(
            active_key="display",
            placed_controls=placed,
            control_labels=labels,
            category_fn=category_for_row,
        )

        for c, l in zip(controls, labels):
            self.assertTrue(c.visible)
            self.assertTrue(l.visible)


if __name__ == "__main__":
    unittest.main()
