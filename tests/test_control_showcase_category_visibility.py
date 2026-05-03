import unittest

from pygame import Rect

from demo_features.controls_demo_feature import (
    apply_category_visibility,
    category_for_row,
)
from gui_do.features.feature_lifecycle import PlacedControl


class _DummyNode:
    def __init__(self):
        self.visible = True
        self.enabled = True
        self.rect = Rect(0, 0, 10, 10)

    def set_rect(self, rect):
        self.rect = Rect(rect)


class _DummyGalleryLayout:
    def __init__(self):
        self.basics_calls = 0
        self.grid_calls = []

    def relayout_basics(self, bounds, items, *, ensure_aux_label):
        self.basics_calls += 1

    def relayout_grid_items(self, category_key, bounds, items):
        self.grid_calls.append((category_key, len(items)))


class TestControlShowcaseCategoryVisibility(unittest.TestCase):
    def test_category_for_row_thresholds(self):
        self.assertEqual("basics", category_for_row(0))
        self.assertEqual("basics", category_for_row(59))
        self.assertEqual("data", category_for_row(60))
        self.assertEqual("advanced", category_for_row(100))
        self.assertEqual("extended", category_for_row(140))

    def test_apply_basics_visibility_suppresses_duplicate_labels(self):
        gallery = _DummyGalleryLayout()

        basic_control = _DummyNode()
        basic_label = _DummyNode()
        suppressed_control = _DummyNode()
        suppressed_label = _DummyNode()
        data_control = _DummyNode()
        data_label = _DummyNode()
        aux_label = _DummyNode()
        orphan_label = _DummyNode()

        placed_controls = [
            PlacedControl(basic_control, basic_label, "button", 0, 0),
            PlacedControl(suppressed_control, suppressed_label, "button_2", 0, 1),
            PlacedControl(data_control, data_label, "list_view", 0, 70),
        ]
        control_labels = [basic_label, suppressed_label, data_label, aux_label, orphan_label]

        apply_category_visibility(
            active_key="basics",
            category_content_bounds=Rect(0, 0, 300, 200),
            placed_controls=placed_controls,
            control_labels=control_labels,
            basics_aux_labels={"vertical_scrollbar": aux_label},
            gallery_layout=gallery,
            ensure_basics_aux_label=lambda _name: aux_label,
            basics_suppressed_label_names=frozenset({"button_2"}),
        )

        self.assertEqual(1, gallery.basics_calls)
        self.assertEqual([], gallery.grid_calls)

        self.assertTrue(basic_control.visible)
        self.assertTrue(basic_control.enabled)
        self.assertTrue(basic_label.visible)

        self.assertTrue(suppressed_control.visible)
        self.assertFalse(suppressed_label.visible)

        self.assertFalse(data_control.visible)
        self.assertFalse(data_label.visible)

        self.assertTrue(aux_label.visible)
        self.assertFalse(orphan_label.visible)

    def test_apply_non_basics_hides_aux_labels_and_uses_grid_relayout(self):
        gallery = _DummyGalleryLayout()

        data_control = _DummyNode()
        data_label = _DummyNode()
        basics_control = _DummyNode()
        basics_label = _DummyNode()
        aux_label = _DummyNode()

        placed_controls = [
            PlacedControl(data_control, data_label, "list_view", 0, 70),
            PlacedControl(basics_control, basics_label, "button", 0, 0),
        ]
        control_labels = [data_label, basics_label, aux_label]

        apply_category_visibility(
            active_key="data",
            category_content_bounds=Rect(0, 0, 300, 200),
            placed_controls=placed_controls,
            control_labels=control_labels,
            basics_aux_labels={"vertical_scrollbar": aux_label},
            gallery_layout=gallery,
            ensure_basics_aux_label=lambda _name: aux_label,
            basics_suppressed_label_names=frozenset({"button_2"}),
        )

        self.assertEqual(0, gallery.basics_calls)
        self.assertEqual([("data", 1)], gallery.grid_calls)

        self.assertTrue(data_control.visible)
        self.assertTrue(data_label.visible)
        self.assertFalse(basics_control.visible)
        self.assertFalse(basics_label.visible)
        self.assertFalse(aux_label.visible)


if __name__ == "__main__":
    unittest.main()
