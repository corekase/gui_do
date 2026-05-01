"""Tests for GridLayout, ConstraintLayout/Builder, and ResponsiveLayout."""
import unittest
from types import SimpleNamespace

import pygame
from pygame import Rect

from gui_do.layout.grid_layout import GridLayout, GridTrack, GridPlacement
from gui_do.layout.constraint_layout import (
    AnchorConstraint, ConstraintLayout, ConstraintBuilder,
)
from gui_do.layout.responsive_layout import Breakpoint, ResponsiveLayout

pygame.init()   # Rect requires pygame initialisation


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _node(w: int, h: int, x: int = 0, y: int = 0) -> SimpleNamespace:
    return SimpleNamespace(rect=Rect(x, y, w, h))


# ===========================================================================
# GridTrack validation
# ===========================================================================


class TestGridTrack(unittest.TestCase):
    def test_fixed_int_ok(self):
        t = GridTrack(100)
        self.assertEqual(100, t.size)

    def test_auto_str_ok(self):
        t = GridTrack("auto")
        self.assertEqual("auto", t.size)

    def test_fr_str_ok(self):
        t = GridTrack("1fr")
        self.assertEqual("1fr", t.size)

    def test_fr_float_str_ok(self):
        t = GridTrack("2.5fr")
        self.assertEqual("2.5fr", t.size)

    def test_negative_int_raises(self):
        with self.assertRaises(ValueError):
            GridTrack(-1)

    def test_bad_str_raises(self):
        with self.assertRaises(ValueError):
            GridTrack("100%")

    def test_bad_type_raises(self):
        with self.assertRaises(TypeError):
            GridTrack(3.14)

    def test_min_size_stored(self):
        t = GridTrack("1fr", min_size=20)
        self.assertEqual(20, t.min_size)


# ===========================================================================
# GridPlacement validation
# ===========================================================================


class TestGridPlacement(unittest.TestCase):
    def test_default_span(self):
        p = GridPlacement(row=0, col=0)
        self.assertEqual(1, p.rowspan)
        self.assertEqual(1, p.colspan)

    def test_negative_row_raises(self):
        with self.assertRaises(ValueError):
            GridPlacement(row=-1, col=0)

    def test_negative_col_raises(self):
        with self.assertRaises(ValueError):
            GridPlacement(row=0, col=-1)

    def test_rowspan_zero_raises(self):
        with self.assertRaises(ValueError):
            GridPlacement(row=0, col=0, rowspan=0)

    def test_bad_align_x_raises(self):
        with self.assertRaises(ValueError):
            GridPlacement(row=0, col=0, align_x="left")

    def test_bad_align_y_raises(self):
        with self.assertRaises(ValueError):
            GridPlacement(row=0, col=0, align_y="top")


# ===========================================================================
# GridLayout — placement management
# ===========================================================================


class TestGridLayoutManagement(unittest.TestCase):
    def _make(self):
        return GridLayout(
            row_tracks=[GridTrack(100), GridTrack(100)],
            col_tracks=[GridTrack(100), GridTrack(100)],
        )

    def test_place_and_nodes(self):
        layout = self._make()
        n = _node(50, 50)
        layout.place(n, GridPlacement(row=0, col=0))
        self.assertIn(n, layout.nodes())

    def test_place_replaces_existing(self):
        layout = self._make()
        n = _node(50, 50)
        layout.place(n, GridPlacement(row=0, col=0))
        layout.place(n, GridPlacement(row=1, col=1))
        self.assertEqual(1, len(layout.nodes()))

    def test_remove_returns_true(self):
        layout = self._make()
        n = _node(50, 50)
        layout.place(n, GridPlacement(row=0, col=0))
        self.assertTrue(layout.remove(n))
        self.assertNotIn(n, layout.nodes())

    def test_remove_missing_returns_false(self):
        layout = self._make()
        self.assertFalse(layout.remove(_node(50, 50)))


# ===========================================================================
# GridLayout — apply: fixed tracks
# ===========================================================================


class TestGridLayoutFixedTracks(unittest.TestCase):
    def test_fixed_col_positions(self):
        layout = GridLayout(
            row_tracks=[GridTrack(200)],
            col_tracks=[GridTrack(100), GridTrack(200)],
            gap=0,
        )
        a = _node(0, 0)
        b = _node(0, 0)
        layout.place(a, GridPlacement(row=0, col=0))
        layout.place(b, GridPlacement(row=0, col=1))
        layout.apply(Rect(0, 0, 400, 200))
        self.assertEqual(0, a.node.rect.x if hasattr(a, 'node') else a.rect.x)
        self.assertEqual(100, b.rect.x)

    def test_fixed_col_width(self):
        layout = GridLayout(
            row_tracks=[GridTrack(200)],
            col_tracks=[GridTrack(100), GridTrack(200)],
            gap=0,
        )
        a = _node(0, 0)
        layout.place(a, GridPlacement(row=0, col=0))
        layout.apply(Rect(0, 0, 400, 200))
        self.assertEqual(200, a.rect.height)  # row is 200
        self.assertEqual(100, a.rect.width)   # first col fixed at 100

    def test_col_gap_offsets_second_column(self):
        layout = GridLayout(
            row_tracks=[GridTrack(200)],
            col_tracks=[GridTrack(100), GridTrack(100)],
            gap=10,
        )
        a = _node(0, 0)
        b = _node(0, 0)
        layout.place(a, GridPlacement(row=0, col=0))
        layout.place(b, GridPlacement(row=0, col=1))
        layout.apply(Rect(0, 0, 400, 200))
        self.assertEqual(110, b.rect.x)   # 100 + 10

    def test_row_gap_offsets_second_row(self):
        layout = GridLayout(
            row_tracks=[GridTrack(50), GridTrack(50)],
            col_tracks=[GridTrack(200)],
            gap=8,
        )
        a = _node(0, 0)
        b = _node(0, 0)
        layout.place(a, GridPlacement(row=0, col=0))
        layout.place(b, GridPlacement(row=1, col=0))
        layout.apply(Rect(0, 0, 200, 200))
        self.assertEqual(0, a.rect.y)
        self.assertEqual(58, b.rect.y)   # 50 + 8

    def test_out_of_range_placement_skipped(self):
        layout = GridLayout(
            row_tracks=[GridTrack(100)],
            col_tracks=[GridTrack(100)],
        )
        n = _node(50, 50)
        layout.place(n, GridPlacement(row=5, col=0))
        layout.apply(Rect(0, 0, 400, 400))   # should not raise; rect unchanged
        self.assertEqual(50, n.rect.width)


# ===========================================================================
# GridLayout — apply: fr tracks
# ===========================================================================


class TestGridLayoutFrTracks(unittest.TestCase):
    def test_equal_fr_splits_space(self):
        layout = GridLayout(
            row_tracks=[GridTrack(200)],
            col_tracks=[GridTrack("1fr"), GridTrack("1fr")],
            gap=0,
        )
        a = _node(0, 0)
        b = _node(0, 0)
        layout.place(a, GridPlacement(row=0, col=0))
        layout.place(b, GridPlacement(row=0, col=1))
        layout.apply(Rect(0, 0, 400, 200))
        self.assertEqual(200, a.rect.width)
        self.assertEqual(200, b.rect.width)
        self.assertEqual(200, b.rect.x)

    def test_proportional_fr(self):
        layout = GridLayout(
            row_tracks=[GridTrack(200)],
            col_tracks=[GridTrack("1fr"), GridTrack("3fr")],
            gap=0,
        )
        a = _node(0, 0)
        b = _node(0, 0)
        layout.place(a, GridPlacement(row=0, col=0))
        layout.place(b, GridPlacement(row=0, col=1))
        layout.apply(Rect(0, 0, 400, 200))
        self.assertEqual(100, a.rect.width)
        self.assertEqual(300, b.rect.width)


# ===========================================================================
# GridLayout — apply: auto tracks
# ===========================================================================


class TestGridLayoutAutoTracks(unittest.TestCase):
    def test_auto_track_sizes_to_content(self):
        layout = GridLayout(
            row_tracks=[GridTrack(200)],
            col_tracks=[GridTrack("auto"), GridTrack("1fr")],
            gap=0,
        )
        # Node pre-layout width is 60 → auto col should become 60
        a = _node(60, 20)
        b = _node(0, 0)
        layout.place(a, GridPlacement(row=0, col=0))
        layout.place(b, GridPlacement(row=0, col=1))
        layout.apply(Rect(0, 0, 400, 200))
        self.assertEqual(60, a.rect.width)
        self.assertEqual(340, b.rect.width)  # remainder


# ===========================================================================
# GridLayout — colspan/rowspan
# ===========================================================================


class TestGridLayoutSpanning(unittest.TestCase):
    def test_colspan_2_gets_combined_width(self):
        layout = GridLayout(
            row_tracks=[GridTrack(100), GridTrack(100)],
            col_tracks=[GridTrack(80), GridTrack(120)],
            gap=0,
        )
        header = _node(0, 0)
        layout.place(header, GridPlacement(row=0, col=0, colspan=2))
        layout.apply(Rect(0, 0, 400, 200))
        self.assertEqual(200, header.rect.width)  # 80 + 120

    def test_rowspan_2_gets_combined_height(self):
        layout = GridLayout(
            row_tracks=[GridTrack(60), GridTrack(80)],
            col_tracks=[GridTrack(200)],
            gap=0,
        )
        tall = _node(0, 0)
        layout.place(tall, GridPlacement(row=0, col=0, rowspan=2))
        layout.apply(Rect(0, 0, 200, 200))
        self.assertEqual(140, tall.rect.height)   # 60 + 80


# ===========================================================================
# GridLayout — alignment
# ===========================================================================


class TestGridLayoutAlignment(unittest.TestCase):
    def _make_single_node(self, align_x="stretch", align_y="stretch"):
        layout = GridLayout(
            row_tracks=[GridTrack(200)],
            col_tracks=[GridTrack(200)],
            gap=0,
        )
        n = _node(80, 40)
        layout.place(n, GridPlacement(row=0, col=0, align_x=align_x, align_y=align_y))
        layout.apply(Rect(0, 0, 200, 200))
        return n

    def test_align_stretch_fills_cell(self):
        n = self._make_single_node()
        self.assertEqual(200, n.rect.width)
        self.assertEqual(200, n.rect.height)

    def test_align_x_start(self):
        n = self._make_single_node(align_x="start")
        self.assertEqual(0, n.rect.x)
        self.assertEqual(80, n.rect.width)

    def test_align_x_end(self):
        n = self._make_single_node(align_x="end")
        self.assertEqual(120, n.rect.x)   # 200 - 80

    def test_align_x_center(self):
        n = self._make_single_node(align_x="center")
        self.assertEqual(60, n.rect.x)   # (200 - 80) // 2

    def test_align_y_end(self):
        n = self._make_single_node(align_y="end")
        self.assertEqual(160, n.rect.y)  # 200 - 40


# ===========================================================================
# AnchorConstraint — horizontal
# ===========================================================================


class TestAnchorConstraintHorizontal(unittest.TestCase):
    PARENT = Rect(0, 0, 400, 300)

    def test_left_pin(self):
        c = AnchorConstraint(left=10)
        r = c.apply(Rect(0, 0, 80, 40), self.PARENT)
        self.assertEqual(10, r.left)
        self.assertEqual(80, r.width)  # width preserved

    def test_right_pin(self):
        c = AnchorConstraint(right=20)
        r = c.apply(Rect(0, 0, 80, 40), self.PARENT)
        self.assertEqual(380, r.right)  # 400 - 20
        self.assertEqual(80, r.width)

    def test_left_and_right_fill_width(self):
        c = AnchorConstraint(left=10, right=10)
        r = c.apply(Rect(0, 0, 0, 40), self.PARENT)
        self.assertEqual(10, r.left)
        self.assertEqual(390, r.right)
        self.assertEqual(380, r.width)

    def test_left_frac(self):
        c = AnchorConstraint(left_frac=0.25)
        r = c.apply(Rect(0, 0, 80, 40), self.PARENT)
        self.assertEqual(100, r.left)  # 400 * 0.25

    def test_right_frac(self):
        c = AnchorConstraint(right_frac=0.5)
        r = c.apply(Rect(0, 0, 80, 40), self.PARENT)
        self.assertEqual(200, r.right)  # 400 - 400*0.5

    def test_min_width_clamped(self):
        c = AnchorConstraint(left=0, right=350, min_width=100)
        r = c.apply(Rect(0, 0, 0, 40), self.PARENT)
        self.assertGreaterEqual(r.width, 100)

    def test_max_width_clamped(self):
        c = AnchorConstraint(left=0, right=0, max_width=50)
        r = c.apply(Rect(0, 0, 0, 40), self.PARENT)
        self.assertLessEqual(r.width, 50)


# ===========================================================================
# AnchorConstraint — vertical
# ===========================================================================


class TestAnchorConstraintVertical(unittest.TestCase):
    PARENT = Rect(0, 0, 400, 300)

    def test_top_pin(self):
        c = AnchorConstraint(top=5)
        r = c.apply(Rect(0, 0, 80, 40), self.PARENT)
        self.assertEqual(5, r.top)
        self.assertEqual(40, r.height)

    def test_bottom_pin(self):
        c = AnchorConstraint(bottom=10)
        r = c.apply(Rect(0, 0, 80, 40), self.PARENT)
        self.assertEqual(290, r.bottom)  # 300 - 10

    def test_top_and_bottom_fill_height(self):
        c = AnchorConstraint(top=20, bottom=20)
        r = c.apply(Rect(0, 0, 80, 0), self.PARENT)
        self.assertEqual(20, r.top)
        self.assertEqual(280, r.bottom)
        self.assertEqual(260, r.height)

    def test_top_frac(self):
        c = AnchorConstraint(top_frac=0.5)
        r = c.apply(Rect(0, 0, 80, 40), self.PARENT)
        self.assertEqual(150, r.top)  # 300 * 0.5

    def test_bottom_frac(self):
        c = AnchorConstraint(bottom_frac=0.25)
        r = c.apply(Rect(0, 0, 80, 40), self.PARENT)
        self.assertEqual(225, r.bottom)  # 300 - 300*0.25

    def test_no_constraint_preserves_rect(self):
        c = AnchorConstraint()
        original = Rect(10, 20, 80, 40)
        r = c.apply(original, self.PARENT)
        self.assertEqual(original, r)


# ===========================================================================
# ConstraintLayout
# ===========================================================================


class TestConstraintLayout(unittest.TestCase):
    PARENT = Rect(0, 0, 400, 300)

    def test_add_and_has(self):
        layout = ConstraintLayout()
        n = _node(80, 40)
        layout.add(n, AnchorConstraint(left=0))
        self.assertTrue(layout.has(n))

    def test_has_false_for_unknown(self):
        layout = ConstraintLayout()
        self.assertFalse(layout.has(_node(10, 10)))

    def test_node_count(self):
        layout = ConstraintLayout()
        layout.add(_node(10, 10), AnchorConstraint())
        layout.add(_node(10, 10), AnchorConstraint())
        self.assertEqual(2, layout.node_count())

    def test_remove_returns_true(self):
        layout = ConstraintLayout()
        n = _node(80, 40)
        layout.add(n, AnchorConstraint())
        self.assertTrue(layout.remove(n))
        self.assertFalse(layout.has(n))

    def test_remove_missing_returns_false(self):
        layout = ConstraintLayout()
        self.assertFalse(layout.remove(_node(10, 10)))

    def test_add_replaces_constraint(self):
        layout = ConstraintLayout()
        n = _node(80, 40)
        layout.add(n, AnchorConstraint(left=0))
        layout.add(n, AnchorConstraint(left=50))
        self.assertEqual(1, layout.node_count())

    def test_apply_mutates_node_rect(self):
        layout = ConstraintLayout()
        n = _node(0, 40)
        layout.add(n, AnchorConstraint(left=10, right=10))
        layout.apply(self.PARENT)
        self.assertEqual(10, n.rect.left)
        self.assertEqual(390, n.rect.right)

    def test_apply_to_returns_rect_without_mutating(self):
        layout = ConstraintLayout()
        n = _node(80, 40)
        layout.add(n, AnchorConstraint(left=20))
        result = layout.apply_to(n, self.PARENT)
        self.assertEqual(20, result.left)
        self.assertEqual(0, n.rect.left)  # original unchanged

    def test_apply_to_unknown_returns_copy(self):
        layout = ConstraintLayout()
        n = _node(80, 40)
        result = layout.apply_to(n, self.PARENT)
        self.assertEqual(Rect(0, 0, 80, 40), result)


# ===========================================================================
# ConstraintBuilder
# ===========================================================================


class TestConstraintBuilder(unittest.TestCase):
    PARENT = Rect(0, 0, 400, 300)

    def _builder(self, n=None):
        layout = ConstraintLayout()
        if n is None:
            n = _node(80, 40)
        return ConstraintBuilder(n, layout), layout, n

    def test_left_pin(self):
        builder, layout, n = self._builder()
        builder.left(15).commit()
        layout.apply(self.PARENT)
        self.assertEqual(15, n.rect.left)

    def test_right_pin(self):
        builder, layout, n = self._builder()
        builder.right(15).commit()
        layout.apply(self.PARENT)
        self.assertEqual(385, n.rect.right)

    def test_fill_width(self):
        builder, layout, n = self._builder()
        builder.fill_width(10, 10).commit()
        layout.apply(self.PARENT)
        self.assertEqual(380, n.rect.width)

    def test_fill_height(self):
        builder, layout, n = self._builder()
        builder.fill_height(5, 5).commit()
        layout.apply(self.PARENT)
        self.assertEqual(290, n.rect.height)

    def test_top_pin(self):
        builder, layout, n = self._builder()
        builder.top(10).commit()
        layout.apply(self.PARENT)
        self.assertEqual(10, n.rect.top)

    def test_bottom_pin(self):
        builder, layout, n = self._builder()
        builder.bottom(10).commit()
        layout.apply(self.PARENT)
        self.assertEqual(290, n.rect.bottom)

    def test_min_max_width(self):
        builder, layout, n = self._builder()
        builder.fill_width().min_width(100).max_width(200).commit()
        layout.apply(Rect(0, 0, 50, 300))  # too narrow → clamped
        self.assertGreaterEqual(n.rect.width, 100)


# ===========================================================================
# ResponsiveLayout
# ===========================================================================


class TestResponsiveLayoutInitial(unittest.TestCase):
    def test_default_active_breakpoint_name(self):
        r = ResponsiveLayout()
        self.assertEqual("default", r.active_breakpoint.value)

    def test_default_active_layout(self):
        obj = object()
        r = ResponsiveLayout(default_layout=obj)
        self.assertIs(obj, r.active_layout)

    def test_current_width_zero(self):
        r = ResponsiveLayout()
        self.assertEqual(0, r.current_width)

    def test_breakpoints_initially_empty(self):
        r = ResponsiveLayout()
        self.assertEqual([], r.breakpoints)


class TestResponsiveLayoutBreakpoints(unittest.TestCase):
    def _make(self):
        narrow = object()
        wide = object()
        r = ResponsiveLayout(default_layout=narrow)
        r.add_breakpoint(Breakpoint("wide", min_width=640, layout=wide))
        r.add_breakpoint(Breakpoint("narrow", min_width=0, layout=narrow))
        return r, narrow, wide

    def test_add_breakpoint_sorted_widest_first(self):
        r, _, _ = self._make()
        names = [bp.name for bp in r.breakpoints]
        self.assertEqual(["wide", "narrow"], names)

    def test_add_non_breakpoint_raises(self):
        r = ResponsiveLayout()
        with self.assertRaises(TypeError):
            r.add_breakpoint("not a breakpoint")

    def test_update_switches_to_wide(self):
        r, narrow, wide = self._make()
        changed = r.update(800)
        self.assertTrue(changed)
        self.assertIs(wide, r.active_layout)
        self.assertEqual("wide", r.active_breakpoint.value)

    def test_update_stays_narrow_below_wide(self):
        r, narrow, wide = self._make()
        r.update(400)
        self.assertIs(narrow, r.active_layout)
        self.assertEqual("narrow", r.active_breakpoint.value)

    def test_update_no_change_returns_false(self):
        r, _, _ = self._make()
        r.update(800)
        changed = r.update(900)   # still "wide"
        self.assertFalse(changed)

    def test_current_width_updated(self):
        r, _, _ = self._make()
        r.update(750)
        self.assertEqual(750, r.current_width)

    def test_subscriber_notified_on_change(self):
        r, _, _ = self._make()
        received = []
        r.active_breakpoint.subscribe(lambda v: received.append(v))
        r.update(800)
        self.assertEqual(["wide"], received)

    def test_subscriber_not_notified_without_change(self):
        r, _, _ = self._make()
        r.update(800)
        received = []
        r.active_breakpoint.subscribe(lambda v: received.append(v))
        r.update(900)   # still wide, no change
        self.assertEqual([], received)

    def test_set_default_layout(self):
        r = ResponsiveLayout()
        new_default = object()
        r.set_default_layout(new_default)
        self.assertIs(new_default, r.active_layout)

    def test_fallback_to_default_when_width_below_all_breakpoints(self):
        default = object()
        wide = object()
        r = ResponsiveLayout(default_layout=default)
        r.add_breakpoint(Breakpoint("wide", min_width=800, layout=wide))
        r.update(100)   # below 800, no match → default
        self.assertIs(default, r.active_layout)
        self.assertEqual("default", r.active_breakpoint.value)


if __name__ == "__main__":
    unittest.main()
