"""Behavioral tests for the level-oriented shelf-packing WindowLayoutHandler.

These tests target the *observable contract* of the layout handler rather than
its private packing internals:

* single window centers in the work area and tweens (or snaps when immediate);
* multiple windows pack into centered, non-overlapping rows with aligned
  titlebars, wrapping to new rows by width and to new z-stacked *pages* (layers)
  by height;
* z-order intent (raise / lower / visibility) only re-layers windows, never the
  geometric packing;
* drop / drag insertion re-flows the layout like a sortable grid;
* the ``immediate_windows`` bridge keeps an appearing window stationary so its
  hide/show (fade/grow) transition plays in the correct spot;
* menu strip and task panel regions are avoided.

The design is independent of any specific window set -- it scales with the
actual number and sizes of the windows present.
"""

from __future__ import annotations

import unittest

from pygame import Rect

from gui_do.layout.window_layout_handler import (
    WINDOW_TILING_ANIMATION_DURATION_SECONDS,
    WindowLayoutHandler,
)


SCREEN_SIZE = (0, 0, 1920, 1080)
SCREEN_CENTER = (960, 540)


# ----------------------------------------------------------------------
# Lightweight scene-graph stubs
# ----------------------------------------------------------------------
class _Surface:
    def __init__(self, rect):
        self._rect = Rect(rect)

    def get_rect(self):
        return Rect(self._rect)


class _Scene:
    def __init__(self, nodes):
        self.nodes = list(nodes)


class _WindowNode:
    def __init__(self, x, y, w, h, *, visible=True):
        self.rect = Rect(int(x), int(y), int(w), int(h))
        self.visible = bool(visible)
        self.children = []
        self.parent = None

    def is_window(self):
        return True

    def is_task_panel(self):
        return False

    def move_by(self, dx, dy):
        self.rect.move_ip(int(dx), int(dy))


class _ParentNode:
    def __init__(self, children):
        self.children = list(children)
        for child in self.children:
            child.parent = self
        self.visible = True
        self.rect = Rect(0, 0, 0, 0)

    def is_window(self):
        return False

    def is_task_panel(self):
        return False


class MenuStripControl:
    """Stub whose class name is detected by the handler's menu-strip probe."""

    def __init__(self, rect, *, visible=True, enabled=True):
        self.rect = Rect(rect)
        self.visible = bool(visible)
        self.enabled = bool(enabled)
        self.children = []
        self.parent = None

    def is_window(self):
        return False

    def is_task_panel(self):
        return False


class _TaskPanelNode:
    def __init__(self, rect):
        self.rect = Rect(rect)
        self.visible = True
        self.children = []
        self.parent = None

    def is_window(self):
        return False

    def is_task_panel(self):
        return True


# ----------------------------------------------------------------------
# Tween scheduler stubs
# ----------------------------------------------------------------------
class _Tween:
    def __init__(self, apply_fn, on_complete):
        self._apply = apply_fn
        self._on_complete = on_complete
        self.is_complete = False

    def finish(self):
        self._apply(1.0)
        self.is_complete = True
        if self._on_complete is not None:
            self._on_complete()


class _RecordingTweens:
    """Captures scheduled tweens so tests can assert animation behaviour."""

    def __init__(self):
        self.scheduled = []  # list[tuple[tag, _Tween]]
        self.cancelled = []

    def tween_fn(self, duration, apply_fn, *, easing=None, on_complete=None, tag=None):
        tween = _Tween(apply_fn, on_complete)
        self.scheduled.append((tag, tween))
        return tween

    def cancel_all_for_tag(self, tag):
        self.cancelled.append(tag)
        self.scheduled = [(t, tw) for (t, tw) in self.scheduled if t != tag]

    def tags(self):
        return [tag for tag, _ in self.scheduled]

    def finish_all(self):
        for _tag, tween in list(self.scheduled):
            tween.finish()


class _ImmediateTweens:
    """Applies tweens to completion immediately for deterministic layout."""

    def tween_fn(self, duration, apply_fn, *, easing=None, on_complete=None, tag=None):
        apply_fn(1.0)
        if on_complete is not None:
            on_complete()

        class _Handle:
            is_complete = True

        return _Handle()

    def cancel_all_for_tag(self, tag):
        return None


class _NoopTweens:
    """Simulates a scheduler that never queues anything (returns None)."""

    def tween_fn(self, *args, **kwargs):
        return None

    def cancel_all_for_tag(self, tag):
        return None


class _App:
    def __init__(self, surface_rect, scene, *, tweens=None):
        self.surface = _Surface(surface_rect)
        self.scene = scene
        self.tweens = tweens


def _make_handler(nodes, *, tweens=None, surface=SCREEN_SIZE, enabled=True):
    scene = _Scene(nodes)
    app = _App(surface, scene, tweens=tweens if tweens is not None else _ImmediateTweens())
    handler = WindowLayoutHandler(app, scene=scene)
    handler.enabled = bool(enabled)
    return handler, app, scene


class TestWindowLayoutHandlerSingleWindowAnimation(unittest.TestCase):
    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _rects_overlap(a: Rect, b: Rect) -> bool:
        return bool(a.colliderect(b))

    def _assert_no_overlaps(self, windows):
        for i in range(len(windows)):
            for j in range(i + 1, len(windows)):
                self.assertFalse(
                    self._rects_overlap(windows[i].rect, windows[j].rect),
                    msg=f"windows {i} and {j} overlap: {windows[i].rect} {windows[j].rect}",
                )

    # ------------------------------------------------------------------
    # Single window
    # ------------------------------------------------------------------
    def test_single_window_centers_in_work_area(self):
        window = _WindowNode(0, 0, 400, 300)
        handler, _app, _scene = _make_handler([window])
        handler.arrange_windows(immediate=True)
        self.assertEqual(window.rect.center, SCREEN_CENTER)

    def test_single_window_standard_relayout_uses_animation(self):
        window = _WindowNode(0, 0, 400, 300)
        tweens = _RecordingTweens()
        handler, _app, _scene = _make_handler([window], tweens=tweens)
        handler.arrange_windows(immediate=False)
        # A tween was scheduled for the window and it is flagged as animating.
        self.assertIn(f"window_tiling:{id(window)}", tweens.tags())
        self.assertTrue(getattr(window, "_window_tiling_animating", False))
        # The final target rect metadata is set even before the tween completes.
        self.assertEqual(window._window_tiling_target_rect.center, SCREEN_CENTER)
        # Driving the tween to completion lands the window on target.
        tweens.finish_all()
        self.assertEqual(window.rect.center, SCREEN_CENTER)
        self.assertFalse(getattr(window, "_window_tiling_animating", True))

    def test_single_window_immediate_relayout_moves_without_animation(self):
        window = _WindowNode(0, 0, 400, 300)
        tweens = _RecordingTweens()
        handler, _app, _scene = _make_handler([window], tweens=tweens)
        handler.arrange_windows(immediate=True)
        self.assertEqual(tweens.scheduled, [])
        self.assertEqual(window.rect.center, SCREEN_CENTER)
        self.assertFalse(getattr(window, "_window_tiling_animating", True))

    def test_relayout_falls_back_to_immediate_when_scheduler_does_not_queue(self):
        window = _WindowNode(0, 0, 400, 300)
        handler, _app, _scene = _make_handler([window], tweens=_NoopTweens())
        handler.arrange_windows(immediate=False)
        # Scheduler returned None -> handler moves the window immediately.
        self.assertEqual(window.rect.center, SCREEN_CENTER)
        self.assertFalse(getattr(window, "_window_tiling_animating", True))

    def test_single_window_immediate_windows_snaps_for_visibility_transition(self):
        # A window appearing with a hide/show transition is placed immediately
        # (via immediate_windows) so the fade/grow plays at the final spot.
        window = _WindowNode(0, 0, 400, 300)
        tweens = _RecordingTweens()
        handler, _app, _scene = _make_handler([window], tweens=tweens)
        handler.arrange_windows(immediate=False, immediate_windows=(window,))
        self.assertEqual(tweens.scheduled, [])
        self.assertEqual(window.rect.center, SCREEN_CENTER)
        self.assertFalse(getattr(window, "_window_tiling_animating", True))

    # ------------------------------------------------------------------
    # Visible-window snapshot / registration order
    # ------------------------------------------------------------------
    def test_visible_windows_snapshot_keeps_registration_order(self):
        a = _WindowNode(0, 0, 200, 150)
        b = _WindowNode(0, 0, 200, 150, visible=False)
        c = _WindowNode(0, 0, 200, 150)
        handler, _app, _scene = _make_handler([a, b, c])
        self.assertEqual(handler.visible_windows_snapshot(), (a, c))

    # ------------------------------------------------------------------
    # Multi-window shelf packing
    # ------------------------------------------------------------------
    def test_row_is_centered_with_aligned_titlebars_and_no_overlap(self):
        windows = [_WindowNode(0, 0, 400, 300) for _ in range(3)]
        handler, _app, _scene = _make_handler(list(windows))
        handler.arrange_windows(immediate=True)
        self._assert_no_overlaps(windows)
        tops = {w.rect.top for w in windows}
        self.assertEqual(len(tops), 1, "row titlebars should align")
        left = min(w.rect.left for w in windows)
        right = max(w.rect.right for w in windows)
        self.assertAlmostEqual((left + right) / 2.0, SCREEN_CENTER[0], delta=1)
        row_center_y = (min(w.rect.top for w in windows) + max(w.rect.bottom for w in windows)) / 2.0
        self.assertAlmostEqual(row_center_y, SCREEN_CENTER[1], delta=1)

    def test_windows_wrap_to_new_row_by_width(self):
        # Three 700-wide windows: two fit a row, the third wraps below.
        windows = [_WindowNode(0, 0, 700, 300) for _ in range(3)]
        handler, _app, _scene = _make_handler(list(windows))
        handler.arrange_windows(immediate=True)
        self._assert_no_overlaps(windows)
        tops = sorted({w.rect.top for w in windows})
        self.assertEqual(len(tops), 2, "windows should occupy two rows")

    def test_next_row_uses_tallest_row_height_plus_gap(self):
        tall = _WindowNode(0, 0, 700, 500)
        short = _WindowNode(0, 0, 700, 300)
        wrapped = _WindowNode(0, 0, 700, 300)
        handler, _app, _scene = _make_handler([tall, short, wrapped])
        handler.arrange_windows(immediate=True)
        first_row_top = tall.rect.top
        self.assertEqual(short.rect.top, first_row_top)
        second_row_top = wrapped.rect.top
        self.assertEqual(second_row_top - first_row_top, 500 + handler.gap)

    def test_general_uniform_windows_pack_into_centered_rows(self):
        windows = [_WindowNode(0, 0, 200, 150) for _ in range(12)]
        handler, _app, _scene = _make_handler(list(windows))
        handler.arrange_windows(immediate=True)
        self._assert_no_overlaps(windows)
        tops = sorted({w.rect.top for w in windows})
        self.assertGreaterEqual(len(tops), 2, "uniform windows should fill multiple rows")
        # Each row is horizontally centered about the screen center.
        for top in tops:
            row = [w for w in windows if w.rect.top == top]
            left = min(w.rect.left for w in row)
            right = max(w.rect.right for w in row)
            self.assertAlmostEqual((left + right) / 2.0, SCREEN_CENTER[0], delta=1)

    # ------------------------------------------------------------------
    # Overflow -> stacked pages (layers)
    # ------------------------------------------------------------------
    def test_height_overflow_creates_stacked_pages(self):
        # Four 600x600 windows: a row of three fills the page width, the fourth
        # plus the second row exceeds the work height -> a second stacked page.
        windows = [_WindowNode(0, 0, 600, 600) for _ in range(4)]
        handler, _app, _scene = _make_handler(list(windows))
        handler.arrange_windows(immediate=True)
        self.assertIsNotNone(handler._last_solve_layers)
        self.assertEqual(len(handler._last_solve_layers), 2, "overflow should stack two pages")
        # Windows sharing a page must not overlap each other.
        for page in handler._last_solve_layers:
            self._assert_no_overlaps(page)

    def test_pages_are_centered_and_stacked_in_z_order(self):
        windows = [_WindowNode(0, 0, 600, 600) for _ in range(4)]
        handler, _app, scene = _make_handler(list(windows))
        handler.arrange_windows(immediate=True)
        layers = handler._last_solve_layers
        # Back-to-front page flattening matches scene node z-order.
        desired = [w for page in layers for w in page]
        scene_windows = [n for n in scene.nodes if getattr(n, "is_window", lambda: False)()]
        self.assertEqual(scene_windows, desired)

    def test_too_wide_window_is_flagged_as_center_fallback(self):
        wide = _WindowNode(0, 0, 2400, 300)
        handler, _app, _scene = _make_handler([wide])
        work = handler._work_area_rect(handler._scene_layout_snapshot())
        rects = {wide: handler._full_window_rect(wide)}
        _pages, fallback = handler._pack_pages([wide], rects, work)
        self.assertIn(wide, fallback)

    # ------------------------------------------------------------------
    # immediate_windows bridge (hide/show animation preservation)
    # ------------------------------------------------------------------
    def test_immediate_window_snaps_while_peers_animate(self):
        appearing = _WindowNode(0, 0, 400, 300)
        peer = _WindowNode(0, 0, 400, 300)
        tweens = _RecordingTweens()
        handler, _app, _scene = _make_handler([appearing, peer], tweens=tweens)
        handler.arrange_windows(
            newly_visible=(appearing,),
            immediate=False,
            immediate_windows=(appearing,),
        )
        # Appearing window snapped (no tween) so its visibility effect plays put.
        self.assertNotIn(f"window_tiling:{id(appearing)}", tweens.tags())
        self.assertFalse(getattr(appearing, "_window_tiling_animating", True))
        self.assertNotEqual(appearing.rect.topleft, (0, 0))
        # Its peer still tweens into place.
        self.assertIn(f"window_tiling:{id(peer)}", tweens.tags())
        self.assertTrue(getattr(peer, "_window_tiling_animating", False))

    # ------------------------------------------------------------------
    # Z-order intent only re-layers (never re-packs)
    # ------------------------------------------------------------------
    def test_raised_window_is_promoted_to_front_of_scene_order(self):
        a = _WindowNode(0, 0, 300, 200)
        b = _WindowNode(0, 0, 300, 200)
        c = _WindowNode(0, 0, 300, 200)
        handler, _app, scene = _make_handler([a, b, c])
        handler.arrange_windows(raised_windows=(a,), immediate=True)
        self.assertIs(scene.nodes[-1], a)

    def test_lowered_window_is_demoted_to_back_of_scene_order(self):
        a = _WindowNode(0, 0, 300, 200)
        b = _WindowNode(0, 0, 300, 200)
        c = _WindowNode(0, 0, 300, 200)
        handler, _app, scene = _make_handler([a, b, c])
        handler.arrange_windows(demoted_windows=(c,), immediate=True)
        self.assertIs(scene.nodes[0], c)

    def test_z_intent_does_not_change_geometric_packing(self):
        windows = [_WindowNode(0, 0, 400, 300) for _ in range(3)]
        handler, _app, _scene = _make_handler(list(windows))
        handler.arrange_windows(immediate=True)
        baseline = [Rect(w.rect) for w in windows]
        handler.arrange_windows(raised_windows=(windows[0],), immediate=True)
        for window, original in zip(windows, baseline):
            self.assertEqual(window.rect, original, "raising must not move packing slots")

    # ------------------------------------------------------------------
    # Drop / drag insertion ordering
    # ------------------------------------------------------------------
    def _drop_plan(self, handler, moving, others, drop_point, z_rank=None):
        layout_rects = {w: handler._full_window_rect(w) for w in [moving, *others]}
        return handler._insertion_plan_for_drop(moving, drop_point, others, layout_rects, z_rank)

    def _drop_order(self, handler, moving, others, drop_point, z_rank=None):
        order, _force = self._drop_plan(handler, moving, others, drop_point, z_rank)
        return order

    def test_drop_far_left_inserts_window_first(self):
        a = _WindowNode(0, 100, 400, 300)
        b = _WindowNode(500, 100, 400, 300)
        moving = _WindowNode(0, 0, 400, 300)
        handler, _app, _scene = _make_handler([a, b, moving])
        order = self._drop_order(handler, moving, [a, b], (-10, 150))
        self.assertEqual(order, [moving, a, b])

    def test_drop_between_inserts_window_in_the_middle(self):
        a = _WindowNode(0, 100, 400, 300)
        b = _WindowNode(500, 100, 400, 300)
        moving = _WindowNode(0, 0, 400, 300)
        handler, _app, _scene = _make_handler([a, b, moving])
        order = self._drop_order(handler, moving, [a, b], (450, 150))
        self.assertEqual(order, [a, moving, b])

    def test_drop_far_right_inserts_window_last(self):
        a = _WindowNode(0, 100, 400, 300)
        b = _WindowNode(500, 100, 400, 300)
        moving = _WindowNode(0, 0, 400, 300)
        handler, _app, _scene = _make_handler([a, b, moving])
        order = self._drop_order(handler, moving, [a, b], (1200, 150))
        self.assertEqual(order, [a, b, moving])

    def test_drop_below_all_rows_appends_window(self):
        a = _WindowNode(0, 100, 400, 300)
        b = _WindowNode(500, 100, 400, 300)
        moving = _WindowNode(0, 0, 400, 300)
        handler, _app, _scene = _make_handler([a, b, moving])
        order = self._drop_order(handler, moving, [a, b], (450, 900))
        self.assertEqual(order, [a, b, moving])

    def test_drop_below_all_rows_forces_a_new_row(self):
        # A drop in the empty space below every row must start its own row.
        a = _WindowNode(0, 100, 400, 300)
        b = _WindowNode(500, 100, 400, 300)
        moving = _WindowNode(0, 0, 400, 300)
        handler, _app, _scene = _make_handler([a, b, moving])
        order, force = self._drop_plan(handler, moving, [a, b], (450, 900))
        self.assertEqual(order, [a, b, moving])
        self.assertIn(moving, force)

    def test_drop_above_all_rows_forces_a_new_row(self):
        # A drop in the empty space above every row must start its own row,
        # and the previous top row must break so it does not merge upward.
        a = _WindowNode(0, 200, 400, 300)
        b = _WindowNode(500, 200, 400, 300)
        moving = _WindowNode(0, 0, 400, 300)
        handler, _app, _scene = _make_handler([a, b, moving])
        order, force = self._drop_plan(handler, moving, [a, b], (450, 20))
        self.assertEqual(order, [moving, a, b])
        self.assertIn(moving, force)
        self.assertIn(a, force)

    def test_drop_above_below_create_distinct_stacked_rows(self):
        # Dropping below produces a new row stacked under the existing one.
        a = _WindowNode(0, 100, 300, 200)
        b = _WindowNode(400, 100, 300, 200)
        moving = _WindowNode(0, 0, 300, 200)
        handler, _app, _scene = _make_handler([a, b, moving])
        handler.arrange_windows_for_drop(moving, (450, 1000), immediate=True)
        self._assert_no_overlaps([a, b, moving])
        # moving forms its own row below the a/b row.
        self.assertGreater(moving.rect.top, a.rect.top)
        self.assertEqual(a.rect.top, b.rect.top)

    def test_drop_between_foreground_windows_ignores_enveloping_backdrop(self):
        # A large backdrop window sits behind two foreground windows. Dropping
        # between the foreground pair must insert there, not next to the
        # backdrop whose vertical band envelops the whole row.
        backdrop = _WindowNode(0, 0, 1536, 864)
        left = _WindowNode(0, 0, 620, 656)
        right = _WindowNode(0, 0, 676, 644)
        moving = _WindowNode(0, 0, 300, 200)
        handler, _app, _scene = _make_handler([backdrop, left, right, moving])
        handler.arrange_windows(demoted_windows=(backdrop,), immediate=True)
        others = [backdrop, left, right]
        snap = handler._scene_layout_snapshot()
        z_rank = handler._drop_z_rank(snap)
        # Backdrop is behind (lower z) than the foreground pair.
        self.assertLess(z_rank[backdrop], z_rank[left])
        self.assertLess(z_rank[backdrop], z_rank[right])
        drop_x = (left.rect.right + right.rect.left) // 2
        drop_y = (left.rect.top + left.rect.bottom) // 2
        order, _force = self._drop_plan(handler, moving, others, (drop_x, drop_y), z_rank)
        # moving lands directly between the foreground pair, not by the backdrop.
        self.assertEqual(order.index(moving), order.index(left) + 1)
        self.assertEqual(order.index(right), order.index(moving) + 1)
        self.assertIs(order[0], backdrop)

    def test_arrange_windows_for_drop_produces_no_overlap(self):
        a = _WindowNode(0, 100, 400, 300)
        b = _WindowNode(500, 100, 400, 300)
        moving = _WindowNode(50, 50, 400, 300)
        handler, _app, _scene = _make_handler([a, b, moving])
        handler.arrange_windows_for_drop(moving, (450, 150), immediate=True)
        self._assert_no_overlaps([a, b, moving])

    def test_arrange_windows_for_drop_promotes_dropped_window(self):
        a = _WindowNode(0, 100, 300, 200)
        b = _WindowNode(400, 100, 300, 200)
        moving = _WindowNode(50, 50, 300, 200)
        handler, _app, scene = _make_handler([a, b, moving])
        handler.arrange_windows_for_drop(moving, (450, 150), immediate=True, promoted_windows=(moving,))
        self.assertIs(scene.nodes[-1], moving)

    # ------------------------------------------------------------------
    # Drag preview
    # ------------------------------------------------------------------
    def test_drag_preview_skips_dragged_window_and_reflows_others(self):
        a = _WindowNode(10, 10, 400, 300)
        b = _WindowNode(20, 20, 400, 300)
        c = _WindowNode(30, 30, 400, 300)
        handler, _app, _scene = _make_handler([a, b, c])
        dragged_rect_before = Rect(b.rect)
        handler.arrange_windows_during_drag(b, (450, 150))
        # The dragged window keeps following the cursor (handler leaves it put).
        self.assertEqual(b.rect, dragged_rect_before)
        # The remaining windows reflow without overlapping each other.
        self.assertFalse(self._rects_overlap(a.rect, c.rect))

    # ------------------------------------------------------------------
    # Region avoidance
    # ------------------------------------------------------------------
    def test_windows_stay_below_menu_strip(self):
        menu = MenuStripControl(Rect(0, 0, 1920, 50))
        windows = [_WindowNode(0, 0, 300, 200) for _ in range(3)]
        handler, _app, _scene = _make_handler([menu, *windows])
        handler.arrange_windows(immediate=True)
        for window in windows:
            self.assertGreaterEqual(window.rect.top, menu.rect.bottom)

    def test_windows_stay_above_task_panel(self):
        panel = _TaskPanelNode(Rect(0, 1000, 1920, 80))
        windows = [_WindowNode(0, 0, 300, 200) for _ in range(3)]
        handler, _app, _scene = _make_handler([*windows, panel])
        handler.arrange_windows(immediate=True)
        for window in windows:
            self.assertLessEqual(window.rect.bottom, panel.rect.top)

    # ------------------------------------------------------------------
    # Enable gating
    # ------------------------------------------------------------------
    def test_disabled_handler_does_not_move_windows(self):
        window = _WindowNode(100, 100, 400, 300)
        handler, _app, _scene = _make_handler([window], enabled=False)
        handler.arrange_windows(immediate=True)
        self.assertEqual(window.rect.topleft, (100, 100))

    def test_disabled_handler_still_arranges_when_forced(self):
        window = _WindowNode(100, 100, 400, 300)
        handler, _app, _scene = _make_handler([window], enabled=False)
        handler.arrange_windows(immediate=True, force=True)
        self.assertEqual(window.rect.center, SCREEN_CENTER)

    # ------------------------------------------------------------------
    # Helper contracts used by other subsystems
    # ------------------------------------------------------------------
    def test_layout_reference_rect_prefers_stable_target(self):
        window = _WindowNode(100, 100, 400, 300)
        # No target metadata -> reports the live rect.
        ref = WindowLayoutHandler._layout_reference_rect(window)
        self.assertEqual(ref.topleft, (100, 100))
        # Stable target with the window settled on it -> reports the target.
        window._window_tiling_target_rect = Rect(100, 100, 400, 300)
        window._window_tiling_animating = False
        ref = WindowLayoutHandler._layout_reference_rect(window)
        self.assertEqual(ref.topleft, (100, 100))

    def test_spatial_rows_group_by_top_alignment(self):
        a = _WindowNode(0, 100, 300, 200)
        b = _WindowNode(400, 104, 300, 200)
        c = _WindowNode(0, 500, 300, 200)
        handler, _app, _scene = _make_handler([a, b, c])
        rects = {w: handler._full_window_rect(w) for w in (a, b, c)}
        rows = handler._spatial_rows([a, b, c], rects)
        self.assertEqual(len(rows), 2)
        self.assertEqual(set(rows[0]), {a, b})
        self.assertEqual(set(rows[1]), {c})

    def test_animation_duration_constant_is_positive(self):
        self.assertGreater(WINDOW_TILING_ANIMATION_DURATION_SECONDS, 0.0)


if __name__ == "__main__":
    unittest.main()
