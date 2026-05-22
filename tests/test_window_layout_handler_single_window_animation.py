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


class _ParentNode:
    def __init__(self, children=None):
        self.children = list(children or [])
        self.visible = True
        self.enabled = True

    def is_window(self) -> bool:
        return False

    def is_task_panel(self) -> bool:
        return False


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


class _NoopTweens:
    def __init__(self):
        self._active_count = 0

    @property
    def active_count(self) -> int:
        return int(self._active_count)

    def cancel_all_for_tag(self, _tag: str) -> int:
        return 0

    def tween_fn(self, _duration, _fn, *, easing=None, on_complete=None, tag=None):
        _ = easing
        _ = on_complete
        _ = tag
        # Intentionally do nothing to simulate a scheduler that fails to queue.
        return None


class TestWindowLayoutHandlerSingleWindowAnimation(unittest.TestCase):
    @staticmethod
    def _rects_overlap(a: Rect, b: Rect) -> bool:
        return bool(a.colliderect(b))

    def test_single_window_standard_relayout_uses_animation(self):
        window = _WindowNode(0, 0, 120, 90, visible=True)
        scene = _Scene([window])
        app = _App(Rect(0, 0, 400, 300), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        with patch.object(handler, "_animate_window_to") as animate_mock:
            handler.arrange_windows()

        animate_mock.assert_called_once()

    def test_relayout_falls_back_to_immediate_when_tween_scheduler_does_not_queue(self):
        first = _WindowNode(20, 20, 120, 90, visible=True)
        second = _WindowNode(220, 20, 120, 90, visible=True)
        scene = _Scene([first, second])
        app = _App(Rect(0, 0, 520, 320), scene)
        app.tweens = _NoopTweens()
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        original_first = Rect(first.rect)
        original_second = Rect(second.rect)
        handler.arrange_windows(immediate=False)

        moved = (
            original_first.topleft != first.rect.topleft
            or original_second.topleft != second.rect.topleft
        )
        self.assertTrue(moved)

    def test_visible_windows_snapshot_includes_all_windows(self):
        first = _WindowNode(0, 0, 120, 90, visible=True)
        second = _WindowNode(180, 0, 120, 90, visible=True)
        scene = _Scene([first, second])
        app = _App(Rect(0, 0, 520, 320), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        snapshot = handler.visible_windows_snapshot()

        self.assertEqual((first, second), snapshot)

    def test_arrange_windows_repositions_all_windows(self):
        first = _WindowNode(20, 20, 120, 90, visible=True)
        second = _WindowNode(220, 20, 120, 90, visible=True)
        third = _WindowNode(370, 20, 120, 90, visible=True)
        scene = _Scene([first, second, third])
        app = _App(Rect(0, 0, 520, 320), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        original_third = Rect(third.rect)
        handler.arrange_windows(immediate=True)

        self.assertNotEqual(original_third, third.rect)

    def test_spatial_rows_ignore_tiny_outlier_when_grouping_normal_windows(self):
        normal_a = _WindowNode(20, 20, 220, 140, visible=True)
        normal_b = _WindowNode(260, 38, 220, 140, visible=True)
        tiny_outlier = _WindowNode(40, 280, 100, 30, visible=True)

        scene = _Scene([normal_a, normal_b, tiny_outlier])
        app = _App(Rect(0, 0, 700, 420), scene)
        handler = WindowLayoutHandler(app, scene=scene)

        window_rects = {
            normal_a: Rect(normal_a.rect),
            normal_b: Rect(normal_b.rect),
            tiny_outlier: Rect(tiny_outlier.rect),
        }

        rows = handler._spatial_rows([normal_a, normal_b, tiny_outlier], window_rects)

        normal_rows = [row for row in rows if normal_a in row or normal_b in row]
        self.assertEqual(1, len(normal_rows))
        self.assertIn(normal_a, normal_rows[0])
        self.assertIn(normal_b, normal_rows[0])

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

    def test_overflow_layer_pair_is_not_split_by_vertical_pair_cap(self):
        # Vertical intent baseline in primary layer: small above large.
        non_menu = _WindowNode(100, 40, 150, 56, visible=True)
        systems = _WindowNode(20, 160, 1536, 864, visible=True)
        life = _WindowNode(1216, 92, 620, 656, visible=True)
        mandel = _WindowNode(28, 92, 676, 644, visible=True)
        scene = _Scene([non_menu, systems, life, mandel])
        app = _App(Rect(0, 0, 1920, 1080), scene)
        app.bounded_area_rect = lambda scene_name=None: Rect(0, 28, 1920, 1002)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        handler.arrange_windows(immediate=True)

        self.assertFalse(self._rects_overlap(life.rect, mandel.rect))
        self.assertEqual(life.rect.y, mandel.rect.y)

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

    def test_multi_window_too_large_overflow_layer_retries_tiling_before_center_fallback(self):
        base_a = _WindowNode(20, 20, 170, 110, visible=True)
        base_b = _WindowNode(210, 20, 170, 110, visible=True)
        tall_a = _WindowNode(40, 170, 170, 250, visible=True)
        tall_b = _WindowNode(230, 170, 170, 250, visible=True)
        scene = _Scene([base_a, base_b, tall_a, tall_b])
        app = _App(Rect(0, 0, 420, 230), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        handler.arrange_windows(immediate=True)

        # Both tall windows exceed work-area height, but the overflow layer can
        # still tile them horizontally. They should not center-stack.
        self.assertNotEqual(tall_a.rect.x, tall_b.rect.x)
        self.assertEqual(tall_a.rect.y, tall_b.rect.y)

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

    def test_newly_visible_window_prefers_base_order_when_trailing_order_keeps_it_centered(self):
        non_menu = _WindowNode(100, 40, 150, 56, visible=True)
        systems = _WindowNode(20, 420, 600, 420, visible=True)
        life = _WindowNode(1216, 92, 620, 656, visible=True)
        scene = _Scene([non_menu, systems, life])
        app = _App(Rect(0, 0, 1920, 1080), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        # Tail-order solve path (forced + relaxed): newly visible Life remains centered.
        tail_targets = [
            (non_menu, 40, 120),
            (systems, 1500, 120),
            (life, 650, 201),
        ]
        # Base-order solve path (forced + relaxed): Life is not centered.
        base_targets = [
            (non_menu, 40, 120),
            (life, 740, 201),
            (systems, 1500, 120),
        ]

        with patch.object(
            handler,
            "_solve_layered_targets",
            side_effect=[
                (tail_targets, set(), 2),
                (tail_targets, set(), 2),
                (base_targets, set(), 2),
                (base_targets, set(), 2),
            ],
        ):
            with patch.object(
                handler,
                "_fit_pass_repack_layers",
                side_effect=lambda t, *_a, **_k: (t, set()),
            ):
                handler.arrange_windows(newly_visible=(life,), immediate=True)

        self.assertEqual(740, life.rect.x)

    def test_bounded_area_rect_is_used_as_window_placement_truth_source(self):
        window = _WindowNode(0, 0, 120, 90, visible=True)
        scene = _Scene([window])
        app = _App(Rect(0, 0, 400, 300), scene)
        app.bounded_area_rect = lambda scene_name=None: Rect(0, 40, 400, 220)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        handler.arrange_windows(immediate=True)

        bounded = app.bounded_area_rect()
        self.assertEqual(bounded.centerx, window.rect.centerx)
        self.assertGreaterEqual(window.rect.top, bounded.top)

    def test_arrange_windows_for_drop_reinserts_window_by_drop_position(self):
        left = _WindowNode(20, 20, 120, 90, visible=True)
        middle = _WindowNode(170, 20, 120, 90, visible=True)
        right = _WindowNode(320, 20, 120, 90, visible=True)
        scene = _Scene([left, middle, right])
        app = _App(Rect(0, 0, 480, 260), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        handler.arrange_windows(immediate=True)
        handler.arrange_windows_for_drop(middle, (10, left.rect.centery), immediate=True)

        self.assertLessEqual(middle.rect.x, left.rect.x)
        self.assertLessEqual(middle.rect.x, right.rect.x)

    def test_does_not_create_overlap_when_single_layer_has_room(self):
        w1 = _WindowNode(20, 20, 120, 90, visible=True)
        w2 = _WindowNode(170, 20, 120, 90, visible=True)
        w3 = _WindowNode(320, 20, 120, 90, visible=True)
        scene = _Scene([w1, w2, w3])
        app = _App(Rect(0, 0, 440, 140), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        handler.arrange_windows(immediate=True)

        self.assertFalse(self._rects_overlap(w1.rect, w2.rect))
        self.assertFalse(self._rects_overlap(w1.rect, w3.rect))
        self.assertFalse(self._rects_overlap(w2.rect, w3.rect))

    def test_drop_to_far_right_moves_dragged_window_to_rightmost_slot(self):
        left = _WindowNode(20, 20, 120, 90, visible=True)
        middle = _WindowNode(170, 20, 120, 90, visible=True)
        right = _WindowNode(320, 20, 120, 90, visible=True)
        scene = _Scene([left, middle, right])
        app = _App(Rect(0, 0, 520, 260), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        handler.arrange_windows(immediate=True)
        handler.arrange_windows_for_drop(middle, (500, right.rect.centery), immediate=True)

        self.assertGreaterEqual(middle.rect.x, left.rect.x)
        self.assertGreaterEqual(middle.rect.x, right.rect.x)

    def test_drop_inside_row_between_windows_places_window_between_neighbors(self):
        left = _WindowNode(20, 20, 120, 90, visible=True)
        moved = _WindowNode(170, 20, 120, 90, visible=True)
        right = _WindowNode(320, 20, 120, 90, visible=True)
        scene = _Scene([left, moved, right])
        app = _App(Rect(0, 0, 520, 260), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        handler.arrange_windows(immediate=True)
        between_x = int((left.rect.right + right.rect.left) // 2)
        handler.arrange_windows_for_drop(moved, (between_x, left.rect.centery), immediate=True)

        ordered = sorted([left, moved, right], key=lambda w: w.rect.x)
        self.assertIs(ordered[1], moved)

    def test_drop_to_different_vertical_row_moves_window_to_that_row(self):
        w1 = _WindowNode(20, 20, 120, 90, visible=True)
        moved = _WindowNode(170, 20, 120, 90, visible=True)
        w3 = _WindowNode(320, 20, 120, 90, visible=True)
        w4 = _WindowNode(20, 140, 120, 90, visible=True)
        w5 = _WindowNode(170, 140, 120, 90, visible=True)
        w6 = _WindowNode(320, 140, 120, 90, visible=True)
        scene = _Scene([w1, moved, w3, w4, w5, w6])
        app = _App(Rect(0, 0, 520, 320), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        handler.arrange_windows(immediate=True)
        top_row_y = min(w.rect.y for w in [w1, moved, w3, w4, w5, w6])
        bottom_row_y = max(w.rect.y for w in [w1, moved, w3, w4, w5, w6])
        self.assertLess(top_row_y, bottom_row_y)

        handler.arrange_windows_for_drop(moved, (w5.rect.centerx, bottom_row_y + 5), immediate=True)

        self.assertGreaterEqual(moved.rect.y, bottom_row_y)

    def test_drop_above_row_moves_window_to_top_row_band(self):
        w1 = _WindowNode(20, 20, 120, 90, visible=True)
        w2 = _WindowNode(170, 20, 120, 90, visible=True)
        w3 = _WindowNode(320, 20, 120, 90, visible=True)
        moved = _WindowNode(20, 140, 120, 90, visible=True)
        w5 = _WindowNode(170, 140, 120, 90, visible=True)
        w6 = _WindowNode(320, 140, 120, 90, visible=True)
        scene = _Scene([w1, w2, w3, moved, w5, w6])
        app = _App(Rect(0, 0, 520, 320), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        handler.arrange_windows(immediate=True)
        top_row_y = min(w.rect.y for w in [w1, w2, w3, moved, w5, w6])
        handler.arrange_windows_for_drop(moved, (w2.rect.centerx, top_row_y - 10), immediate=True)

        self.assertLessEqual(moved.rect.y, top_row_y)

    def test_drop_above_all_rows_creates_new_top_row(self):
        w1 = _WindowNode(20, 20, 120, 90, visible=True)
        w2 = _WindowNode(170, 20, 120, 90, visible=True)
        moved = _WindowNode(20, 140, 120, 90, visible=True)
        w4 = _WindowNode(170, 140, 120, 90, visible=True)
        scene = _Scene([w1, w2, moved, w4])
        app = _App(Rect(0, 0, 520, 360), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        handler.arrange_windows(immediate=True)
        prior_unique_rows = sorted({w.rect.y for w in [w1, w2, moved, w4]})
        self.assertEqual(2, len(prior_unique_rows))

        handler.arrange_windows_for_drop(moved, (moved.rect.centerx, prior_unique_rows[0] - 40), immediate=True)

        after_unique_rows = sorted({w.rect.y for w in [w1, w2, moved, w4]})
        self.assertGreaterEqual(len(after_unique_rows), 3)
        self.assertLess(moved.rect.y, min(w.rect.y for w in [w1, w2, w4]))

    def test_tile_now_preserves_spatial_row_column_order_after_manual_reposition(self):
        a = _WindowNode(20, 20, 120, 90, visible=True)
        b = _WindowNode(170, 20, 120, 90, visible=True)
        c = _WindowNode(320, 20, 120, 90, visible=True)
        d = _WindowNode(20, 140, 120, 90, visible=True)
        e = _WindowNode(170, 140, 120, 90, visible=True)
        f = _WindowNode(320, 140, 120, 90, visible=True)
        scene = _Scene([a, b, c, d, e, f])
        app = _App(Rect(0, 0, 520, 320), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        handler.arrange_windows(immediate=True)
        # Simulate user move to bottom row middle slot before tile-now.
        b.move_by(e.rect.x - b.rect.x, e.rect.y - b.rect.y)
        handler.arrange_windows(immediate=True)

        # Tile-now should preserve the moved window's row/column preference.
        self.assertGreaterEqual(b.rect.y, d.rect.y)

    def test_tile_now_prefers_live_rect_over_stale_target_for_ordering(self):
        a = _WindowNode(20, 20, 120, 90, visible=True)
        b = _WindowNode(170, 20, 120, 90, visible=True)
        c = _WindowNode(320, 20, 120, 90, visible=True)
        d = _WindowNode(20, 140, 120, 90, visible=True)
        e = _WindowNode(170, 140, 120, 90, visible=True)
        f = _WindowNode(320, 140, 120, 90, visible=True)
        scene = _Scene([a, b, c, d, e, f])
        app = _App(Rect(0, 0, 520, 320), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        handler.arrange_windows(immediate=True)

        # Simulate stale target metadata while user has manually moved b lower.
        b.move_by(e.rect.x - b.rect.x, e.rect.y - b.rect.y)
        stale_top = Rect(a.rect.x, a.rect.y, b.rect.width, b.rect.height)
        setattr(b, "_window_tiling_target_rect", stale_top)

        handler.arrange_windows(immediate=True)

        self.assertGreaterEqual(b.rect.y, d.rect.y)

    def test_layout_reference_rect_prefers_target_while_window_is_tiling_animating(self):
        window = _WindowNode(280, 210, 120, 90, visible=True)
        setattr(window, "_window_tiling_target_rect", Rect(300, 220, 120, 90))
        setattr(window, "_window_tiling_animating", True)

        ref = WindowLayoutHandler._layout_reference_rect(window)

        self.assertEqual((300, 220), (ref.x, ref.y))

    def test_layout_reference_rect_recovers_live_geometry_when_animating_marker_is_stale(self):
        window = _WindowNode(20, 20, 120, 90, visible=True)
        setattr(window, "_window_tiling_target_rect", Rect(300, 220, 120, 90))
        setattr(window, "_window_tiling_animating", True)

        # Simulate user drag / cancelled tween with large divergence.
        window.move_by(500, 300)
        ref = WindowLayoutHandler._layout_reference_rect(window)

        self.assertEqual((window.rect.x, window.rect.y), (ref.x, ref.y))
        self.assertFalse(bool(getattr(window, "_window_tiling_animating", False)))

    def test_tile_now_preserves_window_moved_to_new_row_membership(self):
        a = _WindowNode(20, 20, 120, 90, visible=True)
        b = _WindowNode(170, 20, 120, 90, visible=True)
        c = _WindowNode(320, 20, 120, 90, visible=True)
        d = _WindowNode(20, 140, 120, 90, visible=True)
        e = _WindowNode(170, 140, 120, 90, visible=True)
        scene = _Scene([a, b, c, d, e])
        app = _App(Rect(0, 0, 520, 360), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        handler.arrange_windows(immediate=True)
        lowest_row_y = max(w.rect.y for w in [a, b, c, d, e])

        # Simulate user placing b on a distinct new lower row before tile_now.
        b.move_by(0, (lowest_row_y + 120) - b.rect.y)
        handler.arrange_windows(immediate=True)

        self.assertGreaterEqual(b.rect.y, max(w.rect.y for w in [a, c, d, e]))

    def test_large_window_insert_into_existing_row_uses_pointer_x_position(self):
        top_left = _WindowNode(20, 20, 160, 120, visible=True)
        top_right = _WindowNode(260, 20, 160, 120, visible=True)
        moved_large = _WindowNode(20, 200, 170, 120, visible=True)
        bottom_right = _WindowNode(280, 200, 170, 120, visible=True)
        scene = _Scene([top_left, top_right, moved_large, bottom_right])
        app = _App(Rect(0, 0, 560, 380), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        handler.arrange_windows(immediate=True)
        # Drop into top row between the two top windows.
        between_x = int((top_left.rect.right + top_right.rect.left) // 2)
        handler.arrange_windows_for_drop(moved_large, (between_x, top_left.rect.centery), immediate=True)

        ordered = sorted([top_left, moved_large, top_right], key=lambda w: w.rect.x)
        self.assertIs(ordered[1], moved_large)

    def test_large_window_between_gap_uses_widened_logical_insertion_zone(self):
        left = _WindowNode(20, 20, 160, 120, visible=True)
        right = _WindowNode(260, 20, 160, 120, visible=True)
        moved = _WindowNode(20, 200, 160, 120, visible=True)
        scene = _Scene([left, right, moved])
        app = _App(Rect(0, 0, 560, 360), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        handler.arrange_windows(immediate=True)
        # Aim near (not exactly at) the between-window boundary; widened logical
        # insertion zone should still place moved between left/right.
        near_between_x = int(((left.rect.right + right.rect.left) // 2) + int(handler.gap * 1.5))
        handler.arrange_windows_for_drop(moved, (near_between_x, left.rect.centery), immediate=True)

        ordered = sorted([left, moved, right], key=lambda w: w.rect.x)
        self.assertIs(ordered[1], moved)

    def test_tile_now_keeps_explicit_new_row_membership_with_large_window_present(self):
        large = _WindowNode(20, 20, 300, 180, visible=True)
        a = _WindowNode(340, 20, 140, 100, visible=True)
        b = _WindowNode(340, 140, 140, 100, visible=True)
        moved = _WindowNode(20, 240, 140, 100, visible=True)
        scene = _Scene([large, a, b, moved])
        app = _App(Rect(0, 0, 560, 420), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        handler.arrange_windows(immediate=True)
        # Move window to a distinct lower row, then tile-now should preserve it.
        moved.move_by(0, 90)
        handler.arrange_windows(immediate=True)

        self.assertGreaterEqual(moved.rect.y, max(int(w.rect.y) for w in [large, a, b]))

    def test_arrange_windows_prefers_relaxed_solution_when_forced_overlaps(self):
        w1 = _WindowNode(20, 20, 120, 90, visible=True)
        w2 = _WindowNode(170, 20, 120, 90, visible=True)
        scene = _Scene([w1, w2])
        app = _App(Rect(0, 0, 520, 260), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        forced_targets = [(w1, 100, 80), (w2, 100, 80)]  # overlap
        relaxed_targets = [(w1, 80, 80), (w2, 240, 80)]  # non-overlap

        with patch.object(
            handler,
            "_solve_layered_targets",
            side_effect=[
                (forced_targets, set(), 2),
                (relaxed_targets, set(), 1),
            ],
        ):
            handler.arrange_windows(immediate=True)

        self.assertFalse(self._rects_overlap(w1.rect, w2.rect))

    def test_arrange_windows_prefers_relaxed_when_forced_has_more_centered_placements(self):
        w1 = _WindowNode(20, 20, 120, 90, visible=True)
        w2 = _WindowNode(220, 20, 120, 90, visible=True)
        scene = _Scene([w1, w2])
        app = _App(Rect(0, 0, 520, 320), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        # No overlap in either solution; forced keeps single-window centered
        # stacks, while relaxed tiles windows side-by-side.
        forced_targets = [(w1, 200, 80), (w2, 200, 190)]
        relaxed_targets = [(w1, 132, 115), (w2, 268, 115)]

        with patch.object(
            handler,
            "_solve_layered_targets",
            side_effect=[
                (forced_targets, set(), 2),
                (relaxed_targets, set(), 1),
            ],
        ):
            with patch.object(
                handler,
                "_fit_pass_repack_layers",
                side_effect=lambda t, *_a, **_k: (t, set()),
            ):
                handler.arrange_windows(immediate=True)

        self.assertEqual((132, 115), (w1.rect.x, w1.rect.y))
        self.assertEqual((268, 115), (w2.rect.x, w2.rect.y))

    def test_visibility_event_falls_back_to_registration_order_when_spatial_solution_overlaps(self):
        a = _WindowNode(20, 20, 120, 90, visible=True)
        b = _WindowNode(170, 20, 120, 90, visible=True)
        newly_visible = _WindowNode(320, 20, 120, 90, visible=True)
        scene = _Scene([a, b, newly_visible])
        app = _App(Rect(0, 0, 560, 320), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        # Spatial-order selected result still overlaps newly-visible with b.
        spatial_selected = [
            (a, 80, 80),
            (b, 240, 80),
            (newly_visible, 240, 80),
        ]
        # Registration-order fallback resolves overlap.
        registration_selected = [
            (a, 80, 80),
            (b, 240, 80),
            (newly_visible, 400, 80),
        ]

        with patch.object(
            handler,
            "_solve_layered_targets",
            side_effect=[
                (spatial_selected, set(), 2),
                (spatial_selected, set(), 2),
                (registration_selected, set(), 1),
                (registration_selected, set(), 1),
            ],
        ):
            with patch.object(
                handler,
                "_fit_pass_repack_layers",
                side_effect=lambda t, *_a, **_k: (t, set()),
            ):
                handler.arrange_windows(newly_visible=(newly_visible,), immediate=True)

        self.assertFalse(self._rects_overlap(b.rect, newly_visible.rect))

    def test_arrange_windows_for_drop_prefers_relaxed_when_forced_overlaps(self):
        w1 = _WindowNode(20, 20, 120, 90, visible=True)
        moved = _WindowNode(170, 20, 120, 90, visible=True)
        scene = _Scene([w1, moved])
        app = _App(Rect(0, 0, 520, 260), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        forced_targets = [(w1, 100, 80), (moved, 100, 80)]  # overlap
        relaxed_targets = [(w1, 80, 80), (moved, 240, 80)]  # non-overlap

        with patch.object(
            handler,
            "_solve_layered_targets",
            side_effect=[
                (forced_targets, set(), 2),
                (relaxed_targets, set(), 1),
            ],
        ):
            handler.arrange_windows_for_drop(moved, (240, 120), immediate=True)

        self.assertFalse(self._rects_overlap(w1.rect, moved.rect))

    def test_arrange_windows_for_drop_uses_live_z_order_for_top_to_back_layering(self):
        back = _WindowNode(20, 20, 140, 100, visible=True)
        z_mid_old = _WindowNode(20, 20, 140, 100, visible=True)
        z_mid_new = _WindowNode(20, 20, 140, 100, visible=True)
        dragged_top = _WindowNode(20, 20, 140, 100, visible=True)

        # Registration order: back, z_mid_old, z_mid_new, dragged_top.
        # Current z-order (children): back, z_mid_new, z_mid_old, dragged_top.
        # Drag-drop layering must follow live children z-order, not registration.
        parent = _ParentNode([back, z_mid_new, z_mid_old, dragged_top])
        back.parent = parent
        z_mid_old.parent = parent
        z_mid_new.parent = parent
        dragged_top.parent = parent

        scene = _Scene([parent])
        app = _App(Rect(0, 0, 560, 360), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        # Seed registration in a different order than current z-order.
        handler._registration_order = {
            back: 0,
            z_mid_old: 1,
            z_mid_new: 2,
            dragged_top: 3,
        }
        handler._next_order = 4

        captured_order = []

        def _capture_order(ordered_windows, _window_rects, _work, *, prefer_vertical, force_row_before=None):
            captured_order.append(list(ordered_windows))
            targets = [(w, 40 + (idx * 20), 80) for idx, w in enumerate(ordered_windows)]
            return (targets, set(), 1)

        with patch.object(handler, "_solve_layered_targets", side_effect=_capture_order):
            with patch.object(handler, "_fit_pass_repack_layers", side_effect=lambda t, *_a, **_k: (t, set())):
                handler.arrange_windows_for_drop(dragged_top, (200, 120), immediate=True)

        self.assertGreaterEqual(len(captured_order), 1)
        non_dragged = [w for w in captured_order[0] if w is not dragged_top]
        self.assertEqual([z_mid_old, z_mid_new, back], non_dragged)

    def test_arrange_windows_for_drop_depth_layers_use_layout_reference_rects(self):
        opt_out = _WindowNode(40, 30, 220, 110, visible=True)
        life = _WindowNode(40, 180, 220, 110, visible=True)
        mandelbrot = _WindowNode(300, 180, 220, 110, visible=True)

        # Simulate stale in-flight animation geometry: mandelbrot is still at
        # the top in live rects, but target metadata already places it on the
        # second row.
        mandelbrot.move_by(0, -150)
        setattr(opt_out, "_window_tiling_target_rect", Rect(40, 30, 220, 110))
        setattr(life, "_window_tiling_target_rect", Rect(40, 180, 220, 110))
        setattr(mandelbrot, "_window_tiling_target_rect", Rect(300, 180, 220, 110))

        scene = _Scene([opt_out, life, mandelbrot])
        app = _App(Rect(0, 0, 900, 640), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        captured_force_sets = []

        def _capture_order_and_forces(ordered_windows, _window_rects, _work, *, prefer_vertical, force_row_before=None):
            captured_force_sets.append(set(force_row_before or set()))
            targets = [(w, 80 + (idx * 160), 120) for idx, w in enumerate(ordered_windows)]
            return (targets, set(), 1)

        with patch.object(handler, "_solve_layered_targets", side_effect=_capture_order_and_forces):
            with patch.object(handler, "_fit_pass_repack_layers", side_effect=lambda t, *_a, **_k: (t, set())):
                handler.arrange_windows_for_drop(
                    life,
                    (life.rect.centerx, 200),
                    immediate=True,
                )

        self.assertGreaterEqual(len(captured_force_sets), 1)
        # Forced row breaks should only preserve top->second-row structure;
        # stale live overlap must not split mandelbrot into an extra row.
        self.assertEqual({life}, captured_force_sets[0])

    def test_drop_inside_lower_row_top_band_does_not_create_new_middle_row(self):
        opt_out = _WindowNode(40, 30, 200, 60, visible=True)
        life = _WindowNode(40, 180, 220, 110, visible=True)
        mandelbrot = _WindowNode(300, 180, 220, 110, visible=True)

        scene = _Scene([opt_out, life, mandelbrot])
        app = _App(Rect(0, 0, 900, 640), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        # Seed tiling targets so row inference mirrors active tiling state.
        for window in (opt_out, life, mandelbrot):
            setattr(window, "_window_tiling_target_rect", Rect(window.rect))

        captured_force_sets = []

        def _capture_order_and_forces(ordered_windows, _window_rects, _work, *, prefer_vertical, force_row_before=None):
            captured_force_sets.append(set(force_row_before or set()))
            targets = [(w, 80 + (idx * 160), 120) for idx, w in enumerate(ordered_windows)]
            return (targets, set(), 1)

        drop_y_near_top_of_lower_row = int(mandelbrot.rect.top + 2)
        with patch.object(handler, "_solve_layered_targets", side_effect=_capture_order_and_forces):
            with patch.object(handler, "_fit_pass_repack_layers", side_effect=lambda t, *_a, **_k: (t, set())):
                handler.arrange_windows_for_drop(
                    life,
                    (mandelbrot.rect.centerx, drop_y_near_top_of_lower_row),
                    immediate=True,
                )

        self.assertGreaterEqual(len(captured_force_sets), 1)
        # Expected rows are [opt_out], [life, mandelbrot] -> only one forced
        # row break before the lower row head (life).
        self.assertEqual({life}, captured_force_sets[0])

    def test_fit_pass_repacks_selected_overlapping_targets(self):
        w1 = _WindowNode(20, 20, 120, 90, visible=True)
        w2 = _WindowNode(170, 20, 120, 90, visible=True)
        scene = _Scene([w1, w2])
        app = _App(Rect(0, 0, 520, 260), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        overlapping_targets = [(w1, 100, 80), (w2, 100, 80)]

        with patch.object(
            handler,
            "_solve_layered_targets",
            side_effect=[
                (overlapping_targets, set(), 1),
                (overlapping_targets, set(), 1),
            ],
        ):
            handler.arrange_windows(immediate=True)

        self.assertFalse(self._rects_overlap(w1.rect, w2.rect))

    def test_arrange_windows_normalizes_parent_z_order_by_solved_layers(self):
        front_left = _WindowNode(20, 20, 120, 90, visible=True)
        back = _WindowNode(170, 20, 120, 90, visible=True)
        front_right = _WindowNode(320, 20, 120, 90, visible=True)

        parent = _ParentNode([front_left, back, front_right])
        front_left.parent = parent
        back.parent = parent
        front_right.parent = parent

        scene = _Scene([parent])
        app = _App(Rect(0, 0, 560, 320), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        # First layer: one back window.
        # Second layer: two non-overlapping front windows.
        solved_targets = [
            (back, 80, 80),
            (front_left, 80, 80),
            (front_right, 240, 80),
        ]

        with patch.object(
            handler,
            "_solve_layered_targets",
            side_effect=[
                (solved_targets, set(), 2),
                (solved_targets, set(), 2),
            ],
        ):
            with patch.object(
                handler,
                "_fit_pass_repack_layers",
                return_value=(solved_targets, set()),
            ):
                handler.arrange_windows(immediate=True)

        # Back layer should occupy lower z slots than the front layer.
        self.assertIs(parent.children[0], back)

    def test_arrange_windows_z_slices_layer_determines_overall_within_layer_existing_z_order(self):
        # Initial children: [w1(z=0), back(z=1), w2(z=2)].
        # Solver puts w2 and w1 in back layer, back in overflow front layer.
        # Within the back layer the existing z-order (w1 behind w2) should be
        # preserved, and the front layer (back) should be rendered in front of
        # all back-layer windows regardless of its original z-index.
        w1 = _WindowNode(20, 20, 120, 90, visible=True)
        w2 = _WindowNode(170, 20, 120, 90, visible=True)
        back = _WindowNode(320, 20, 120, 90, visible=True)

        parent = _ParentNode([w1, back, w2])
        w1.parent = parent
        w2.parent = parent
        back.parent = parent

        scene = _Scene([parent])
        app = _App(Rect(0, 0, 560, 320), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        # Back layer solve order is [w2, w1]; front layer is [back].
        solved_targets = [
            (w2, 80, 80),
            (w1, 240, 80),
            (back, 80, 80),
        ]

        with patch.object(
            handler,
            "_solve_layered_targets",
            side_effect=[
                (solved_targets, set(), 2),
                (solved_targets, set(), 2),
            ],
        ):
            with patch.object(
                handler,
                "_fit_pass_repack_layers",
                return_value=(solved_targets, set()),
            ):
                handler.arrange_windows(immediate=True)

        # Within back layer: w1 (z=0) behind w2 (z=2), preserving existing order.
        # Front layer: back on top of all back-layer windows.
        self.assertEqual([w1, w2, back], list(parent.children))

    def test_newly_visible_windows_are_appended_to_trailing_solve_segment(self):
        base_a = _WindowNode(20, 20, 120, 90, visible=True)
        base_b = _WindowNode(170, 20, 120, 90, visible=True)
        new_window = _WindowNode(320, 20, 120, 90, visible=True)
        scene = _Scene([base_a, base_b, new_window])
        app = _App(Rect(0, 0, 560, 320), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        captured_orders = []

        def _capture_order(ordered_windows, *_args, **_kwargs):
            captured_orders.append(list(ordered_windows))
            # Return a simple non-overlapping placement for whichever order we got.
            targets = [(w, 40 + (idx * 140), 80) for idx, w in enumerate(ordered_windows)]
            return (targets, set(), 1)

        with patch.object(handler, "_solve_layered_targets", side_effect=_capture_order):
            handler.arrange_windows(newly_visible=(new_window,), immediate=True)

        self.assertGreaterEqual(len(captured_orders), 1)
        self.assertIs(captured_orders[0][-1], new_window)

    def test_newly_visible_trailing_segment_does_not_force_row_break(self):
        base_a = _WindowNode(20, 20, 120, 90, visible=True)
        base_b = _WindowNode(170, 20, 120, 90, visible=True)
        new_window = _WindowNode(320, 20, 120, 90, visible=True)
        scene = _Scene([base_a, base_b, new_window])
        app = _App(Rect(0, 0, 560, 320), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        captured_force_sets = []

        def _capture_order_and_forces(ordered_windows, _window_rects, _work, *, prefer_vertical, force_row_before=None):
            captured_force_sets.append(set(force_row_before or set()))
            targets = [(w, 40 + (idx * 140), 80) for idx, w in enumerate(ordered_windows)]
            return (targets, set(), 1)

        with patch.object(handler, "_solve_layered_targets", side_effect=_capture_order_and_forces):
            handler.arrange_windows(newly_visible=(new_window,), immediate=True)

        self.assertGreaterEqual(len(captured_force_sets), 1)
        self.assertNotIn(new_window, captured_force_sets[0])

    def test_newly_visible_windows_are_last_drawn_within_their_layer(self):
        base_a = _WindowNode(20, 20, 120, 90, visible=True)
        new_window = _WindowNode(170, 20, 120, 90, visible=True)
        base_b = _WindowNode(320, 20, 120, 90, visible=True)

        parent = _ParentNode([base_a, new_window, base_b])
        base_a.parent = parent
        new_window.parent = parent
        base_b.parent = parent

        scene = _Scene([parent])
        app = _App(Rect(0, 0, 560, 320), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        solved_targets = [
            (base_a, 80, 80),
            (new_window, 240, 80),
            (base_b, 400, 80),
        ]

        with patch.object(
            handler,
            "_solve_layered_targets",
            side_effect=[
                (solved_targets, set(), 1),
                (solved_targets, set(), 1),
                (solved_targets, set(), 1),
                (solved_targets, set(), 1),
            ],
        ):
            with patch.object(
                handler,
                "_fit_pass_repack_layers",
                return_value=(solved_targets, set()),
            ):
                handler.arrange_windows(newly_visible=(new_window,), immediate=True)

        self.assertEqual([base_a, base_b, new_window], list(parent.children))

    def test_arrange_windows_excludes_newly_visible_from_forced_row_break_markers(self):
        non_menu = _WindowNode(100, 40, 150, 56, visible=True)
        systems = _WindowNode(20, 150, 1536, 864, visible=True)
        life = _WindowNode(620, 220, 620, 656, visible=True)
        newly_visible = _WindowNode(1240, 92, 676, 644, visible=True)
        scene = _Scene([non_menu, systems, life, newly_visible])
        app = _App(Rect(0, 0, 1920, 1080), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        captured_force_sets = []

        def _capture_order_and_forces(ordered_windows, _window_rects, _work, *, prefer_vertical, force_row_before=None):
            captured_force_sets.append(set(force_row_before or set()))
            targets = [(w, 80 + (idx * 40), 120) for idx, w in enumerate(ordered_windows)]
            return (targets, set(), 1)

        with patch.object(handler, "_solve_layered_targets", side_effect=_capture_order_and_forces):
            with patch.object(handler, "_fit_pass_repack_layers", side_effect=lambda t, *_a, **_k: (t, set())):
                handler.arrange_windows(newly_visible=(newly_visible,), immediate=True)

        self.assertGreaterEqual(len(captured_force_sets), 1)
        self.assertNotIn(newly_visible, captured_force_sets[0])

    def test_raised_window_is_promoted_alone_to_top_layer(self):
        back = _WindowNode(20, 20, 120, 90, visible=True)
        mid_peer = _WindowNode(170, 20, 120, 90, visible=True)
        raised = _WindowNode(320, 20, 120, 90, visible=True)
        front = _WindowNode(470, 20, 120, 90, visible=True)

        parent = _ParentNode([back, mid_peer, raised, front])
        back.parent = parent
        mid_peer.parent = parent
        raised.parent = parent
        front.parent = parent

        scene = _Scene([parent])
        app = _App(Rect(0, 0, 700, 360), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        # Layer 0: back
        # Layer 1: mid_peer, raised
        # Layer 2: front
        solved_targets = [
            (back, 80, 80),
            (mid_peer, 80, 80),
            (raised, 240, 80),
            (front, 80, 80),
        ]

        with patch.object(
            handler,
            "_solve_layered_targets",
            side_effect=[
                (solved_targets, set(), 3),
                (solved_targets, set(), 3),
            ],
        ):
            with patch.object(
                handler,
                "_fit_pass_repack_layers",
                return_value=(solved_targets, set()),
            ):
                handler.arrange_windows(raised_windows=(raised,), immediate=True)

        self.assertEqual([back, mid_peer, front, raised], list(parent.children))

    def test_arrange_windows_for_drop_demoted_window_is_forced_to_back(self):
        back = _WindowNode(20, 20, 120, 90, visible=True)
        mid = _WindowNode(170, 20, 120, 90, visible=True)
        lowered = _WindowNode(320, 20, 120, 90, visible=True)
        front = _WindowNode(470, 20, 120, 90, visible=True)

        parent = _ParentNode([back, mid, lowered, front])
        back.parent = parent
        mid.parent = parent
        lowered.parent = parent
        front.parent = parent

        scene = _Scene([parent])
        app = _App(Rect(0, 0, 700, 360), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        solved_targets = [
            (back, 80, 80),
            (mid, 240, 80),
            (lowered, 400, 80),
            (front, 560, 80),
        ]

        with patch.object(
            handler,
            "_solve_layered_targets",
            side_effect=[
                (solved_targets, set(), 1),
                (solved_targets, set(), 1),
            ],
        ):
            with patch.object(
                handler,
                "_fit_pass_repack_layers",
                return_value=(solved_targets, set()),
            ):
                handler.arrange_windows_for_drop(
                    lowered,
                    (lowered.rect.centerx, app.surface.get_rect().bottom + 40),
                    immediate=True,
                    demoted_windows=(lowered,),
                )

        self.assertIs(parent.children[0], lowered)

    def test_demotion_preserves_non_demoted_parent_z_order(self):
        back_a = _WindowNode(20, 20, 120, 90, visible=True)
        back_b = _WindowNode(170, 20, 120, 90, visible=True)
        top_a = _WindowNode(320, 20, 120, 90, visible=True)
        lowered = _WindowNode(470, 20, 120, 90, visible=True)
        top_b = _WindowNode(620, 20, 120, 90, visible=True)

        parent = _ParentNode([back_a, back_b, top_a, lowered, top_b])
        back_a.parent = parent
        back_b.parent = parent
        top_a.parent = parent
        lowered.parent = parent
        top_b.parent = parent

        scene = _Scene([parent])
        app = _App(Rect(0, 0, 900, 420), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        # Force solver order that differs from current parent order to ensure
        # demotion path preserves non-demoted z-order from parent.children.
        solved_targets = [
            (top_b, 80, 80),
            (top_a, 240, 80),
            (back_a, 400, 80),
            (back_b, 560, 80),
            (lowered, 720, 80),
        ]

        with patch.object(
            handler,
            "_solve_layered_targets",
            side_effect=[
                (solved_targets, set(), 2),
                (solved_targets, set(), 2),
            ],
        ):
            with patch.object(
                handler,
                "_fit_pass_repack_layers",
                return_value=(solved_targets, set()),
            ):
                handler.arrange_windows_for_drop(
                    lowered,
                    (lowered.rect.centerx, app.surface.get_rect().bottom + 40),
                    immediate=True,
                    demoted_windows=(lowered,),
                )

        self.assertEqual(
            [lowered, back_a, back_b, top_a, top_b],
            list(parent.children),
        )

    def test_arrange_windows_for_drop_promoted_window_is_forced_to_top(self):
        back = _WindowNode(20, 20, 120, 90, visible=True)
        mid = _WindowNode(170, 20, 120, 90, visible=True)
        front = _WindowNode(320, 20, 120, 90, visible=True)
        dragged = _WindowNode(470, 20, 120, 90, visible=True)

        parent = _ParentNode([back, mid, front, dragged])
        back.parent = parent
        mid.parent = parent
        front.parent = parent
        dragged.parent = parent

        scene = _Scene([parent])
        app = _App(Rect(0, 0, 800, 360), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        solved_targets = [
            (back, 80, 80),
            (mid, 240, 80),
            (front, 400, 80),
            (dragged, 560, 80),
        ]

        with patch.object(
            handler,
            "_solve_layered_targets",
            side_effect=[
                (solved_targets, set(), 1),
                (solved_targets, set(), 1),
            ],
        ):
            with patch.object(
                handler,
                "_fit_pass_repack_layers",
                return_value=(solved_targets, set()),
            ):
                handler.arrange_windows_for_drop(
                    dragged,
                    (dragged.rect.centerx, dragged.rect.centery),
                    immediate=True,
                    promoted_windows=(dragged,),
                )

        self.assertIs(parent.children[-1], dragged)

    def test_promotion_preserves_non_promoted_parent_z_order(self):
        back_a = _WindowNode(20, 20, 120, 90, visible=True)
        promoted = _WindowNode(170, 20, 120, 90, visible=True)
        back_b = _WindowNode(320, 20, 120, 90, visible=True)
        front_a = _WindowNode(470, 20, 120, 90, visible=True)
        front_b = _WindowNode(620, 20, 120, 90, visible=True)

        # Existing parent order should be preserved for non-promoted windows.
        parent = _ParentNode([back_a, promoted, back_b, front_a, front_b])
        back_a.parent = parent
        promoted.parent = parent
        back_b.parent = parent
        front_a.parent = parent
        front_b.parent = parent

        scene = _Scene([parent])
        app = _App(Rect(0, 0, 900, 420), scene)
        handler = WindowLayoutHandler(app, scene=scene)
        handler.enabled = True

        # Solver order intentionally differs from existing parent order.
        solved_targets = [
            (front_b, 80, 80),
            (front_a, 240, 80),
            (back_b, 400, 80),
            (back_a, 560, 80),
            (promoted, 720, 80),
        ]

        with patch.object(
            handler,
            "_solve_layered_targets",
            side_effect=[
                (solved_targets, set(), 2),
                (solved_targets, set(), 2),
            ],
        ):
            with patch.object(
                handler,
                "_fit_pass_repack_layers",
                return_value=(solved_targets, set()),
            ):
                handler.arrange_windows_for_drop(
                    promoted,
                    (promoted.rect.centerx, promoted.rect.centery),
                    immediate=True,
                    promoted_windows=(promoted,),
                )

        self.assertEqual(
            [back_a, back_b, front_a, front_b, promoted],
            list(parent.children),
        )


if __name__ == "__main__":
    unittest.main()
