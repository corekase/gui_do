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


class MenuStripControl:
    def __init__(self, rect: Rect, *, visible: bool = True, enabled: bool = True):
        self.rect = Rect(rect)
        self.visible = bool(visible)
        self.enabled = bool(enabled)
        self.children = []

    def is_window(self) -> bool:
        return False

    def is_task_panel(self) -> bool:
        return False


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

        self.assertEqual(app.surface.get_rect().centerx, large.rect.centerx)
        self.assertGreaterEqual(large.rect.top, app.surface.get_rect().top)

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

    def test_overflow_uses_repeated_tiled_layers_not_diagonal_cascade(self):
        w1 = _WindowNode(20, 20, 150, 120, visible=True)
        w2 = _WindowNode(210, 20, 150, 120, visible=True)
        w3 = _WindowNode(20, 160, 150, 120, visible=True)
        w4 = _WindowNode(210, 160, 150, 120, visible=True)
        w5 = _WindowNode(20, 300, 150, 120, visible=True)
        scene = _Scene([w1, w2, w3, w4, w5])
        app = _App(Rect(0, 0, 420, 260), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        handler.arrange_windows(immediate=True)

        # Overflow layer 1 fills both base row slots at the same y.
        self.assertEqual(w3.rect.y, w4.rect.y)
        self.assertLess(w3.rect.x, w4.rect.x)

        # Overflow layer 2 (single-window layer) is centered for that layer.
        self.assertEqual(app.surface.get_rect().centerx, w5.rect.centerx)

    def test_multiple_overflow_layers_keep_row_titlebar_alignment(self):
        windows = [
            _WindowNode(20 + (i % 2) * 190, 20 + (i // 2) * 120, 150, 100, visible=True)
            for i in range(8)
        ]
        scene = _Scene(windows)
        app = _App(Rect(0, 0, 420, 320), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        handler.arrange_windows(immediate=True)

        # Base layer provides two row slots; each additional layer should keep
        # those same row-top alignments as it repeats with layer offsets.
        y_values = sorted({w.rect.y for w in windows})
        counts = {y: 0 for y in y_values}
        for w in windows:
            counts[w.rect.y] += 1

        # Per-layer centering means repeated full layers reuse the same aligned
        # row tops, so each distinct row y appears once per layer.
        self.assertEqual(2, len(y_values))
        self.assertTrue(all(counts[y] == 4 for y in y_values))

    def test_large_centered_overflow_does_not_shift_next_overflow_row_slots(self):
        base_a = _WindowNode(20, 20, 170, 110, visible=True)
        base_b = _WindowNode(210, 20, 170, 110, visible=True)
        systems = _WindowNode(260, 20, 360, 250, visible=True)
        life = _WindowNode(270, 20, 170, 110, visible=True)
        mandel = _WindowNode(280, 20, 170, 110, visible=True)
        scene = _Scene([base_a, base_b, systems, life, mandel])
        app = _App(Rect(0, 0, 420, 230), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        handler.arrange_windows(immediate=True)

        self.assertEqual(app.surface.get_rect().centerx, systems.rect.centerx)
        self.assertGreaterEqual(systems.rect.top, app.surface.get_rect().top)
        self.assertEqual(life.rect.y, mandel.rect.y)
        self.assertLess(life.rect.x, mandel.rect.x)

    def test_visibility_order_life_mandel_system_does_not_overlap_menu_strip(self):
        menu = MenuStripControl(Rect(0, 0, 420, 32), visible=True, enabled=True)
        life = _WindowNode(20, 20, 170, 110, visible=True)
        mandel = _WindowNode(210, 20, 170, 110, visible=True)
        systems = _WindowNode(260, 20, 360, 250, visible=True)
        # Match reported visibility order.
        scene = _Scene([menu, life, mandel, systems])
        app = _App(Rect(0, 0, 420, 230), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        handler.arrange_windows(immediate=True)

        menu_bottom = menu.rect.bottom
        self.assertGreaterEqual(life.rect.top, menu_bottom)
        self.assertGreaterEqual(mandel.rect.top, menu_bottom)
        self.assertGreaterEqual(systems.rect.top, menu_bottom)


if __name__ == "__main__":
    unittest.main()
