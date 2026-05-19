import unittest
from unittest.mock import patch

from pygame import Rect

from gui_do.layout.window_layout_handler import WindowLayoutHandler


class _Surface:
    def __init__(self, rect: Rect):
        self._rect = Rect(rect)

    def get_rect(self) -> Rect:
        return Rect(self._rect)


class _Scene:
    def __init__(self, nodes):
        self.nodes = list(nodes)


class _WindowNode:
    def __init__(self, x: int, y: int, w: int, h: int, *, visible: bool = True):
        self.rect = Rect(x, y, w, h)
        self.visible = bool(visible)
        self.children = []
        self.parent = None

    def is_window(self) -> bool:
        return True

    def is_task_panel(self) -> bool:
        return False

    def move_by(self, dx: int, dy: int) -> None:
        self.rect = self.rect.move(int(dx), int(dy))


class _App:
    def __init__(self, surface_rect: Rect, scene):
        self.surface = _Surface(surface_rect)
        self.scene = scene


class TestWindowLayoutHandlerSingleWindowAnimation(unittest.TestCase):
    def test_single_window_standard_relayout_uses_animation(self):
        window = _WindowNode(0, 0, 120, 90, visible=True)
        scene = _Scene([window])
        app = _App(Rect(0, 0, 400, 300), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        with patch.object(handler, "_animate_window_to") as animate_mock:
            handler.arrange_windows()

        animate_mock.assert_called_once()

    def test_single_window_immediate_relayout_moves_without_animation(self):
        window = _WindowNode(0, 0, 120, 90, visible=True)
        scene = _Scene([window])
        app = _App(Rect(0, 0, 400, 300), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        with patch.object(handler, "_animate_window_to") as animate_mock:
            handler.arrange_windows(include_hidden=True, immediate=True)

        animate_mock.assert_not_called()
        self.assertNotEqual((window.rect.x, window.rect.y), (0, 0))

    def test_multi_window_vertical_intent_keeps_below_relationship_when_space_allows(self):
        top = _WindowNode(80, 40, 120, 90, visible=True)
        bottom = _WindowNode(84, 180, 120, 90, visible=True)
        scene = _Scene([top, bottom])
        app = _App(Rect(0, 0, 520, 420), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        handler.arrange_windows(immediate=True)

        self.assertLess(top.rect.y, bottom.rect.y)

    def test_multi_window_horizontal_intent_keeps_left_right_relationship(self):
        left = _WindowNode(40, 120, 120, 90, visible=True)
        right = _WindowNode(220, 124, 120, 90, visible=True)
        scene = _Scene([left, right])
        app = _App(Rect(0, 0, 520, 420), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        handler.arrange_windows(immediate=True)

        self.assertLess(left.rect.x, right.rect.x)

    def test_row_titlebars_align_and_next_row_uses_tallest_row_height_plus_gap(self):
        w1 = _WindowNode(30, 30, 170, 90, visible=True)
        w2 = _WindowNode(240, 34, 170, 140, visible=True)
        w3 = _WindowNode(26, 220, 170, 80, visible=True)
        w4 = _WindowNode(244, 226, 170, 70, visible=True)
        scene = _Scene([w1, w2, w3, w4])
        app = _App(Rect(0, 0, 420, 420), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        handler.arrange_windows(immediate=True)

        placed = sorted([w1, w2, w3, w4], key=lambda w: (w.rect.y, w.rect.x))
        top_row = placed[:2]
        bottom_row = placed[2:]

        self.assertEqual(top_row[0].rect.y, top_row[1].rect.y)
        self.assertEqual(bottom_row[0].rect.y, bottom_row[1].rect.y)

        expected_next_row_top = top_row[0].rect.y + max(top_row[0].rect.height, top_row[1].rect.height) + handler.gap
        self.assertEqual(expected_next_row_top, bottom_row[0].rect.y)

    def test_large_overflow_window_falls_back_to_screen_center(self):
        small = _WindowNode(20, 20, 120, 90, visible=True)
        large = _WindowNode(200, 60, 360, 280, visible=True)
        scene = _Scene([small, large])
        app = _App(Rect(0, 0, 400, 300), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        handler.arrange_windows(immediate=True)

        self.assertEqual(app.surface.get_rect().center, large.rect.center)

    def test_visibility_change_retiles_windows_out_of_previous_cascade(self):
        w1 = _WindowNode(20, 20, 170, 150, visible=True)
        w2 = _WindowNode(210, 28, 170, 150, visible=True)
        w3 = _WindowNode(24, 196, 170, 150, visible=True)
        scene = _Scene([w1, w2, w3])
        app = _App(Rect(0, 0, 420, 300), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        # Initial layout overflows height and places one window in cascade.
        handler.arrange_windows(immediate=True)

        # Hide one window so remaining windows can fit a regular tiled row.
        w3.visible = False
        handler.arrange_windows(immediate=True)

        self.assertEqual(w1.rect.y, w2.rect.y)
        self.assertNotEqual(w1.rect.x, w2.rect.x)


if __name__ == "__main__":
    unittest.main()
