"""Tests for SnapGrid, AlignmentGuide, SnapComposer, and Viewport.

All modules are pure-logic and require only pygame.Rect — no display needed.
"""
import unittest

import pygame
from pygame import Rect

from gui_do.layout.snap_grid import SnapGrid, AlignmentGuide, SnapComposer
from gui_do.layout.viewport import Viewport

pygame.init()


# ===========================================================================
# SnapGrid
# ===========================================================================


class TestSnapGridSnapPoint(unittest.TestCase):
    def setUp(self):
        self.grid = SnapGrid(16, 16)

    def test_origin_snaps_to_zero(self):
        self.assertEqual((0, 0), self.grid.snap_point(0, 0))

    def test_exact_grid_intersection_unchanged(self):
        self.assertEqual((32, 48), self.grid.snap_point(32, 48))

    def test_rounds_up_past_midpoint(self):
        sx, sy = self.grid.snap_point(9, 9)
        self.assertEqual(16, sx)
        self.assertEqual(16, sy)

    def test_rounds_down_before_midpoint(self):
        sx, sy = self.grid.snap_point(7, 7)
        self.assertEqual(0, sx)
        self.assertEqual(0, sy)

    def test_offset_shifts_grid_origin(self):
        grid = SnapGrid(16, 16, offset_x=4, offset_y=4)
        sx, sy = grid.snap_point(4, 4)
        self.assertEqual(4, sx)
        self.assertEqual(4, sy)

    def test_non_square_cells(self):
        grid = SnapGrid(20, 10)
        sx, sy = grid.snap_point(11, 6)
        self.assertEqual(20, sx)
        self.assertEqual(10, sy)


class TestSnapGridSnapRect(unittest.TestCase):
    def setUp(self):
        self.grid = SnapGrid(16, 16)

    def test_snaps_topleft(self):
        r = Rect(7, 7, 50, 30)
        snapped = self.grid.snap_rect(r)
        self.assertEqual(0, snapped.x)
        self.assertEqual(0, snapped.y)

    def test_preserves_size(self):
        r = Rect(7, 7, 50, 30)
        snapped = self.grid.snap_rect(r)
        self.assertEqual(50, snapped.width)
        self.assertEqual(30, snapped.height)

    def test_already_aligned_unchanged(self):
        r = Rect(32, 64, 10, 10)
        snapped = self.grid.snap_rect(r)
        self.assertEqual(Rect(32, 64, 10, 10), snapped)


class TestSnapGridNearestCell(unittest.TestCase):
    def test_origin(self):
        grid = SnapGrid(16, 16)
        self.assertEqual((0, 0), grid.nearest_cell(0, 0))

    def test_positive_coords(self):
        grid = SnapGrid(16, 16)
        self.assertEqual((1, 2), grid.nearest_cell(20, 33))

    def test_with_offset(self):
        grid = SnapGrid(16, 16, offset_x=8, offset_y=8)
        col, row = grid.nearest_cell(8, 8)
        self.assertEqual(0, col)
        self.assertEqual(0, row)


# ===========================================================================
# AlignmentGuide
# ===========================================================================


class TestAlignmentGuide(unittest.TestCase):
    def setUp(self):
        self.cand = Rect(100, 100, 80, 60)
        self.guide = AlignmentGuide([self.cand])

    def test_no_snap_when_far(self):
        dragged = Rect(0, 0, 40, 40)
        targets = self.guide.find_snap_targets(dragged, threshold_px=8)
        self.assertEqual([], targets)

    def test_left_left_snap(self):
        # dragged.left is close to cand.left (100)
        dragged = Rect(103, 50, 40, 40)
        targets = self.guide.find_snap_targets(dragged, threshold_px=8)
        self.assertTrue(any(t.label == "left-left" for t in targets))

    def test_top_top_snap(self):
        # dragged.top close to cand.top (100)
        dragged = Rect(50, 97, 40, 40)
        targets = self.guide.find_snap_targets(dragged, threshold_px=8)
        self.assertTrue(any(t.label == "top-top" for t in targets))

    def test_sorted_by_distance_ascending(self):
        dragged = Rect(103, 97, 40, 40)
        targets = self.guide.find_snap_targets(dragged, threshold_px=8)
        dists = [t.distance for t in targets]
        self.assertEqual(sorted(dists), dists)

    def test_update_candidates_replaces(self):
        self.guide.update_candidates([])
        dragged = Rect(103, 100, 40, 40)
        self.assertEqual([], self.guide.find_snap_targets(dragged, threshold_px=8))

    def test_center_x_snap(self):
        # dragged.centerx close to cand.centerx (140)
        dragged = Rect(103, 0, 40, 40)  # centerx = 123 → dist=17 → no snap at 8
        targets = self.guide.find_snap_targets(dragged, threshold_px=20)
        cx_targets = [t for t in targets if t.label == "center-x"]
        self.assertTrue(len(cx_targets) > 0)


# ===========================================================================
# SnapComposer
# ===========================================================================


class TestSnapComposerGridOnly(unittest.TestCase):
    def setUp(self):
        self.grid = SnapGrid(16, 16)
        self.composer = SnapComposer(grid=self.grid)

    def test_snap_aligns_to_grid(self):
        r = Rect(7, 7, 50, 30)
        snapped = self.composer.snap(r)
        self.assertEqual(0, snapped.x)
        self.assertEqual(0, snapped.y)

    def test_size_preserved(self):
        r = Rect(7, 7, 50, 30)
        snapped = self.composer.snap(r)
        self.assertEqual(50, snapped.width)
        self.assertEqual(30, snapped.height)


class TestSnapComposerGuideOverridesGrid(unittest.TestCase):
    def test_guide_wins_over_grid(self):
        # Place candidate at x=100; grid would snap to 96 (nearest 16 multiple)
        cand = Rect(100, 0, 80, 60)
        grid = SnapGrid(16, 16)
        guide = AlignmentGuide([cand])
        composer = SnapComposer(grid=grid, guides=guide)

        # dragged.left=103 → dist from cand.left=3, well within threshold
        dragged = Rect(103, 5, 40, 40)
        snapped = composer.snap(dragged, threshold_px=8)
        self.assertEqual(100, snapped.x)  # guide won, not grid (96)


# ===========================================================================
# Viewport
# ===========================================================================


class TestViewportInitialState(unittest.TestCase):
    def setUp(self):
        self.vp = Viewport(content_size=(2000, 1500), viewport_size=(800, 600))

    def test_scroll_starts_at_zero(self):
        self.assertEqual((0.0, 0.0), self.vp.scroll_offset)

    def test_zoom_starts_at_one(self):
        self.assertAlmostEqual(1.0, self.vp.zoom)

    def test_content_size(self):
        self.assertEqual((2000, 1500), self.vp.content_size)

    def test_viewport_size(self):
        self.assertEqual((800, 600), self.vp.viewport_size)


class TestViewportScrollTo(unittest.TestCase):
    def setUp(self):
        self.vp = Viewport(content_size=(2000, 1500), viewport_size=(800, 600))

    def test_scroll_to_moves_offset(self):
        self.vp.scroll_to(100, 200)
        self.assertAlmostEqual(100.0, self.vp.scroll_x)
        self.assertAlmostEqual(200.0, self.vp.scroll_y)

    def test_scroll_clamped_at_zero(self):
        self.vp.scroll_to(-100, -100)
        self.assertAlmostEqual(0.0, self.vp.scroll_x)
        self.assertAlmostEqual(0.0, self.vp.scroll_y)

    def test_scroll_clamped_at_max(self):
        self.vp.scroll_to(9999, 9999)
        self.assertLessEqual(self.vp.scroll_x, 2000)
        self.assertLessEqual(self.vp.scroll_y, 1500)

    def test_scroll_by_accumulates(self):
        self.vp.scroll_to(100, 100)
        self.vp.scroll_by(50, 25)
        self.assertAlmostEqual(150.0, self.vp.scroll_x)
        self.assertAlmostEqual(125.0, self.vp.scroll_y)

    def test_scroll_fires_subscriber(self):
        events = []
        self.vp.subscribe(lambda: events.append(1))
        self.vp.scroll_to(100, 0)
        self.assertEqual(1, len(events))

    def test_no_event_when_scroll_unchanged(self):
        events = []
        self.vp.scroll_to(0, 0)  # already at 0,0
        self.vp.subscribe(lambda: events.append(1))
        self.vp.scroll_to(0, 0)
        self.assertEqual(0, len(events))


class TestViewportScrollToItem(unittest.TestCase):
    def setUp(self):
        self.vp = Viewport(content_size=(2000, 1500), viewport_size=(800, 600))

    def test_item_already_visible_no_scroll(self):
        self.vp.scroll_to(0, 0)
        item = Rect(100, 100, 50, 50)
        self.vp.scroll_to_item(item)
        self.assertAlmostEqual(0.0, self.vp.scroll_x)
        self.assertAlmostEqual(0.0, self.vp.scroll_y)

    def test_item_right_of_viewport_scrolls(self):
        self.vp.scroll_to(0, 0)
        item = Rect(900, 100, 50, 50)  # right=950 > viewport_w=800
        self.vp.scroll_to_item(item)
        self.assertGreater(self.vp.scroll_x, 0)


class TestViewportZoom(unittest.TestCase):
    def setUp(self):
        self.vp = Viewport(content_size=(2000, 1500), viewport_size=(800, 600))

    def test_set_zoom_changes_factor(self):
        self.vp.set_zoom(2.0)
        self.assertAlmostEqual(2.0, self.vp.zoom)

    def test_zoom_clamped_at_min(self):
        self.vp.set_zoom(0.001)
        self.assertGreaterEqual(self.vp.zoom, 0.1)

    def test_zoom_clamped_at_max(self):
        self.vp.set_zoom(999.0)
        self.assertLessEqual(self.vp.zoom, 32.0)

    def test_adjust_zoom_multiplies(self):
        self.vp.set_zoom(2.0)
        self.vp.adjust_zoom(1.5)
        self.assertAlmostEqual(3.0, self.vp.zoom)

    def test_zoom_fires_subscriber(self):
        events = []
        self.vp.subscribe(lambda: events.append(1))
        self.vp.set_zoom(2.0)
        self.assertEqual(1, len(events))

    def test_same_zoom_no_event(self):
        events = []
        self.vp.set_zoom(1.0)  # already 1.0
        self.vp.subscribe(lambda: events.append(1))
        self.vp.set_zoom(1.0)
        self.assertEqual(0, len(events))


class TestViewportCoordinateTransforms(unittest.TestCase):
    def setUp(self):
        self.vp = Viewport(content_size=(2000, 1500), viewport_size=(800, 600), zoom=2.0)

    def test_screen_to_local_at_origin(self):
        lx, ly = self.vp.screen_to_local((0, 0))
        self.assertAlmostEqual(0.0, lx)
        self.assertAlmostEqual(0.0, ly)

    def test_screen_to_local_with_zoom(self):
        # zoom=2: screen(100,100) → local(50,50)
        lx, ly = self.vp.screen_to_local((100, 100))
        self.assertAlmostEqual(50.0, lx)
        self.assertAlmostEqual(50.0, ly)

    def test_local_to_screen_round_trip(self):
        local = (300.0, 200.0)
        screen = self.vp.local_to_screen(local)
        back = self.vp.screen_to_local(screen)
        self.assertAlmostEqual(local[0], back[0], places=5)
        self.assertAlmostEqual(local[1], back[1], places=5)

    def test_visible_rect_with_zoom(self):
        # zoom=2, viewport 800x600 → visible 400x300 in content coords
        vis = self.vp.visible_rect()
        self.assertEqual(400, vis.width)
        self.assertEqual(300, vis.height)


class TestViewportSizing(unittest.TestCase):
    def setUp(self):
        self.vp = Viewport(content_size=(1000, 800), viewport_size=(400, 300))

    def test_set_content_size(self):
        self.vp.set_content_size(2000, 1600)
        self.assertEqual((2000, 1600), self.vp.content_size)

    def test_set_viewport_size(self):
        self.vp.set_viewport_size(800, 600)
        self.assertEqual((800, 600), self.vp.viewport_size)

    def test_set_content_fires_subscriber(self):
        events = []
        self.vp.subscribe(lambda: events.append(1))
        self.vp.set_content_size(5000, 4000)
        self.assertEqual(1, len(events))

    def test_set_viewport_fires_subscriber(self):
        events = []
        self.vp.subscribe(lambda: events.append(1))
        self.vp.set_viewport_size(1200, 900)
        self.assertEqual(1, len(events))


class TestViewportSubscription(unittest.TestCase):
    def test_unsubscribe_stops_events(self):
        vp = Viewport(content_size=(2000, 1500), viewport_size=(800, 600))
        events = []
        unsub = vp.subscribe(lambda: events.append(1))
        vp.scroll_to(100, 0)
        unsub()
        vp.scroll_to(200, 0)
        self.assertEqual(1, len(events))

    def test_multiple_subscribers(self):
        vp = Viewport(content_size=(2000, 1500), viewport_size=(800, 600))
        a, b = [], []
        vp.subscribe(lambda: a.append(1))
        vp.subscribe(lambda: b.append(1))
        vp.scroll_to(100, 0)
        self.assertEqual(1, len(a))
        self.assertEqual(1, len(b))


if __name__ == "__main__":
    unittest.main()
