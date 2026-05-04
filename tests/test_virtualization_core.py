"""Tests for gui_do.controls.data.virtualization_core."""
from __future__ import annotations

import unittest

from gui_do.controls.data.virtualization_core import (
    MeasureMode,
    MeasurePolicy,
    RecyclePool,
    VirtualizationCore,
    VirtualizedWindow,
)


class TestMeasurePolicy(unittest.TestCase):
    def test_uniform_height(self):
        mp = MeasurePolicy(item_height=40)
        self.assertEqual(mp.get_height(0), 40)
        self.assertEqual(mp.get_height(99), 40)

    def test_variable_height(self):
        mp = MeasurePolicy(mode=MeasureMode.VARIABLE, height_fn=lambda i: 20 + i * 5)
        self.assertEqual(mp.get_height(0), 20)
        self.assertEqual(mp.get_height(2), 30)

    def test_total_height_uniform(self):
        mp = MeasurePolicy(item_height=30)
        self.assertEqual(mp.total_height(10), 300)

    def test_total_height_variable(self):
        mp = MeasurePolicy(mode=MeasureMode.VARIABLE, height_fn=lambda i: 10 * (i + 1))
        # heights: 10, 20, 30 = 60
        self.assertEqual(mp.total_height(3), 60)

    def test_item_at_offset_uniform(self):
        mp = MeasurePolicy(item_height=30)
        self.assertEqual(mp.item_at_offset(0, 10), 0)
        self.assertEqual(mp.item_at_offset(29, 10), 0)
        self.assertEqual(mp.item_at_offset(30, 10), 1)

    def test_item_at_offset_variable(self):
        mp = MeasurePolicy(mode=MeasureMode.VARIABLE, height_fn=lambda i: 10 * (i + 1))
        # offsets: item 0: 0-9, item 1: 10-29, item 2: 30-59
        self.assertEqual(mp.item_at_offset(0, 5), 0)
        self.assertEqual(mp.item_at_offset(15, 5), 1)
        self.assertEqual(mp.item_at_offset(35, 5), 2)

    def test_offset_of_item_uniform(self):
        mp = MeasurePolicy(item_height=30)
        self.assertEqual(mp.offset_of_item(0), 0)
        self.assertEqual(mp.offset_of_item(3), 90)

    def test_offset_of_item_variable(self):
        mp = MeasurePolicy(mode=MeasureMode.VARIABLE, height_fn=lambda i: 10 * (i + 1))
        self.assertEqual(mp.offset_of_item(0), 0)
        self.assertEqual(mp.offset_of_item(2), 30)  # 10 + 20

    def test_item_at_offset_clamped(self):
        mp = MeasurePolicy(item_height=30)
        self.assertEqual(mp.item_at_offset(10000, 5), 4)

    def test_item_at_offset_empty(self):
        mp = MeasurePolicy(item_height=30)
        self.assertEqual(mp.item_at_offset(0, 0), 0)


class TestVirtualizedWindow(unittest.TestCase):
    def test_empty_range(self):
        win = VirtualizedWindow(viewport_height=200, overscan=0)
        win.update(scroll_offset=0, item_count=0)
        first, last = win.visible_range()
        self.assertLess(last, first)
        self.assertEqual(win.visible_count, 0)

    def test_basic_visible_range(self):
        mp = MeasurePolicy(item_height=30)
        win = VirtualizedWindow(viewport_height=90, overscan=0, policy=mp)
        win.update(scroll_offset=0, item_count=20)
        first, last = win.visible_range()
        self.assertEqual(first, 0)
        # 90px / 30px = 3 items visible → indices 0, 1, 2 → last offset item at 90 = item 3
        self.assertGreaterEqual(last, 2)

    def test_scroll_updates_range(self):
        mp = MeasurePolicy(item_height=30)
        win = VirtualizedWindow(viewport_height=60, overscan=0, policy=mp)
        win.update(scroll_offset=60, item_count=20)
        first, last = win.visible_range()
        self.assertEqual(first, 2)

    def test_overscan_extends_range(self):
        mp = MeasurePolicy(item_height=30)
        win = VirtualizedWindow(viewport_height=30, overscan=2, policy=mp)
        win.update(scroll_offset=0, item_count=20)
        first, last = win.visible_range()
        self.assertEqual(first, 0)
        self.assertGreaterEqual(last, 2)  # at least overscan extra

    def test_range_clamped_to_item_count(self):
        mp = MeasurePolicy(item_height=30)
        win = VirtualizedWindow(viewport_height=200, overscan=5, policy=mp)
        win.update(scroll_offset=0, item_count=3)
        first, last = win.visible_range()
        self.assertEqual(first, 0)
        self.assertEqual(last, 2)


class TestRecyclePool(unittest.TestCase):
    def test_factory_called_when_empty(self):
        count = [0]

        def factory():
            count[0] += 1
            return object()

        pool = RecyclePool(factory)
        pool.acquire()
        self.assertEqual(count[0], 1)

    def test_acquire_from_pool(self):
        obj = object()
        pool = RecyclePool(object)
        pool.release(obj)
        self.assertIs(pool.acquire(), obj)

    def test_pool_size_tracks(self):
        pool = RecyclePool(object)
        pool.release(object())
        pool.release(object())
        self.assertEqual(pool.pool_size, 2)
        pool.acquire()
        self.assertEqual(pool.pool_size, 1)

    def test_reset_fn_called_on_release(self):
        called = []

        class Cell:
            pass

        pool = RecyclePool(Cell, reset_fn=lambda c: called.append(True))
        cell = pool.acquire()
        pool.release(cell)
        self.assertEqual(called, [True])

    def test_no_reset_fn(self):
        pool = RecyclePool(object)
        obj = object()
        pool.release(obj)  # no error
        self.assertEqual(pool.pool_size, 1)


class TestVirtualizationCore(unittest.TestCase):
    def _setup(self, viewport_height=90, overscan=0, item_height=30):
        mp = MeasurePolicy(item_height=item_height)
        win = VirtualizedWindow(viewport_height=viewport_height, overscan=overscan, policy=mp)

        class Cell:
            def __init__(self):
                self.index = -1

        pool = RecyclePool(Cell)
        bound = {}

        def bind(cell, idx):
            cell.index = idx
            bound[idx] = cell

        core = VirtualizationCore(win, pool, bind)
        return core, bound

    def test_refresh_binds_visible_cells(self):
        core, bound = self._setup()
        pairs = core.refresh(scroll_offset=0, item_count=5)
        indices = [idx for idx, _ in pairs]
        self.assertIn(0, indices)
        self.assertIn(1, indices)
        self.assertIn(2, indices)

    def test_cells_recycled_on_scroll(self):
        core, bound = self._setup()
        core.refresh(scroll_offset=0, item_count=10)
        # Scroll down past first 3 items
        pairs_after = core.refresh(scroll_offset=90, item_count=10)
        visible_indices = [idx for idx, _ in pairs_after]
        self.assertNotIn(0, visible_indices)

    def test_empty_item_count(self):
        core, bound = self._setup()
        pairs = core.refresh(scroll_offset=0, item_count=0)
        self.assertEqual(pairs, [])

    def test_pool_reuses_cells(self):
        mp = MeasurePolicy(item_height=30)
        win = VirtualizedWindow(viewport_height=60, overscan=0, policy=mp)

        created = [0]

        class Cell:
            pass

        def factory():
            created[0] += 1
            return Cell()

        pool = RecyclePool(factory)
        core = VirtualizationCore(win, pool, lambda c, i: None)

        core.refresh(scroll_offset=0, item_count=10)
        initial_created = created[0]
        # Scroll so items recycle into pool, then scroll back
        core.refresh(scroll_offset=300, item_count=10)
        core.refresh(scroll_offset=0, item_count=10)
        # Should reuse pooled cells, not create all new ones
        self.assertLessEqual(created[0], initial_created + 2 + 2)


if __name__ == "__main__":
    unittest.main()
