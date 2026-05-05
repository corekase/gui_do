import unittest

from pygame import Rect

from demo_features.showcase.control_gallery_layout_manager import ControlGalleryLayoutManager


class _StubControl:
    def __init__(self, rect: Rect):
        self.rect = Rect(rect)

    def set_rect(self, rect: Rect):
        self.rect = Rect(rect)


class _StubLabel:
    def __init__(self):
        self.rect = Rect(0, 0, 1, 1)
        self.visible = False
        self.enabled = False
        self.text = ""

    def set_rect(self, rect: Rect):
        self.rect = Rect(rect)


class _Placed:
    def __init__(self, name: str, control: _StubControl, label=None, row_index=0, column_index=0):
        self.name = name
        self.control = control
        self.label = label
        self.row_index = row_index
        self.column_index = column_index


class TestControlGalleryLayoutManager(unittest.TestCase):
    def setUp(self):
        self.layout = ControlGalleryLayoutManager(inner_gap=4, label_height=18, label_gap=4)

    def test_target_control_size_basics_text_input(self):
        placed = _Placed("text_input", _StubControl(Rect(0, 0, 10, 10)))
        width, height = self.layout.target_control_size("basics", placed, 220)
        self.assertEqual(220, width)
        self.assertEqual(32, height)

    def test_target_control_size_non_basics_uses_current_height(self):
        placed = _Placed("any", _StubControl(Rect(0, 0, 10, 77)))
        width, height = self.layout.target_control_size("data", placed, 200)
        self.assertEqual(200, width)
        self.assertEqual(77, height)

    def test_relayout_grid_items_updates_label_and_control_rect(self):
        label = _StubLabel()
        placed = _Placed("text_input", _StubControl(Rect(0, 0, 10, 10)), label=label)
        end_y = self.layout.relayout_grid_items("data", Rect(10, 20, 500, 240), [placed])

        self.assertTrue(label.visible)
        self.assertTrue(label.enabled)
        self.assertEqual(10, label.rect.left)
        self.assertEqual(20, label.rect.top)
        self.assertEqual(18, label.rect.height)
        self.assertEqual(42, placed.control.rect.top)
        self.assertGreater(end_y, 20)


if __name__ == "__main__":
    unittest.main()
