import unittest

import pygame

from gui_do import ButtonControl, LabelControl, TabLayoutContext
from gui_do.persistence.scene_snapshot import SceneSnapshot
from demo_features.systems import SystemsDemoFeature


class _StubWindow:
    def __init__(self):
        self.added = []

    def add(self, control):
        self.added.append(control)
        return control


class _StubStatusLabel:
    def __init__(self):
        self.text = ""


class _StubSnapshotWindow:
    def __init__(self):
        self.control_id = "systems_window"
        self.rect = pygame.Rect(0, 0, 320, 240)


class TestSystemsDemoFeatureAbstractions(unittest.TestCase):
    """Tests for TabLayoutContext — the cursor-tracking tab content builder.

    These replaced the old _add_tab_control / _add_tab_label / _add_tab_button /
    _add_tab_button_row presenter wrapper methods, which were removed once all
    tab build methods were migrated to use TabLayoutContext directly.
    """

    @classmethod
    def setUpClass(cls):
        pygame.init()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def _make_ctx(self, left=10, top=20, width=400, height=300, *, pad=8):
        window = _StubWindow()
        rect = pygame.Rect(left, top, width, height)
        return TabLayoutContext(window, rect, pad=pad), window

    def test_add_control_adds_to_window_and_returns_control(self):
        ctx, window = self._make_ctx()
        label = LabelControl("label_id", pygame.Rect(0, 0, 120, 20), "Label", align="left")

        added = ctx.add_control(label)

        self.assertIs(label, added)
        self.assertEqual([label], ctx.build())
        self.assertEqual([label], window.added)

    def test_add_label_creates_left_aligned_label(self):
        ctx, window = self._make_ctx(left=10, top=20)

        label = ctx.add_label("test_label", 22, "Hello")

        self.assertIsInstance(label, LabelControl)
        self.assertEqual("test_label", label.control_id)
        self.assertEqual("Hello", label.text)
        self.assertEqual("left", label.align)
        self.assertEqual([label], ctx.build())
        self.assertEqual([label], window.added)

    def test_add_button_creates_button_and_tracks_it(self):
        ctx, window = self._make_ctx()

        def on_click():
            return None

        button = ctx.add_button("test_button", 140, 28, "Run", on_click)

        self.assertIsInstance(button, ButtonControl)
        self.assertEqual("test_button", button.control_id)
        self.assertEqual("Run", button.text)
        self.assertEqual([button], ctx.build())
        self.assertEqual([button], window.added)

    def test_add_button_row_places_buttons_with_consistent_gap(self):
        ctx, window = self._make_ctx(left=10, top=20, pad=0)

        def first():
            return None

        def second():
            return None

        buttons = ctx.add_button_row(
            height=30,
            gap=8,
            width=100,
            specs=(
                ("btn_one", "One", first),
                ("btn_two", "Two", second),
            ),
        )

        self.assertEqual(2, len(buttons))
        self.assertEqual("btn_one", buttons[0].control_id)
        self.assertEqual("btn_two", buttons[1].control_id)
        # With pad=0, ctx.x = left = 10
        self.assertEqual(10, buttons[0].rect.left)
        self.assertEqual(10 + 100 + 8, buttons[1].rect.left)
        self.assertEqual([buttons[0], buttons[1]], ctx.build())
        self.assertEqual([buttons[0], buttons[1]], window.added)

    def test_restore_snapshot_uses_rect_topleft_for_status_text(self):
        feature = SystemsDemoFeature()
        window = _StubSnapshotWindow()
        feature.window = window
        feature._snapshot_label = _StubStatusLabel()
        feature._snapshot = SceneSnapshot.from_nodes([window])

        window.rect.topleft = (150, 160)

        feature._restore_snapshot()

        self.assertEqual((0, 0), window.rect.topleft)
        self.assertEqual("Restored: window moved to (0, 0)", feature._snapshot_label.text)


if __name__ == "__main__":
    unittest.main()
