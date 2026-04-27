"""Tests for ListViewControl (Feature 8)."""
import unittest
from unittest.mock import MagicMock

import pygame
from pygame import Rect

from gui_do.controls.list_view_control import ListItem, ListViewControl
from gui_do.core.gui_event import EventType, GuiEvent


def _items(n: int = 5) -> list:
    return [ListItem(label=f"Item {i}", value=i) for i in range(n)]


def _ctrl(n: int = 5, **kwargs) -> ListViewControl:
    return ListViewControl("lst", Rect(0, 0, 200, 120), _items(n), **kwargs)


def _app():
    return MagicMock()


def _click(y: int) -> GuiEvent:
    return GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0, pos=(10, y), button=1)


def _key(k: int) -> GuiEvent:
    return GuiEvent(kind=EventType.KEY_DOWN, type=0, key=k, mod=0)


def _wheel(delta: int) -> GuiEvent:
    e = GuiEvent(kind=EventType.MOUSE_WHEEL, type=0)
    e.y = delta
    return e


class TestClickSelectsItem(unittest.TestCase):
    def test_click_selects_item(self) -> None:
        ctrl = _ctrl(row_height=24)
        ctrl.handle_event(_click(10), _app())
        self.assertEqual(ctrl.selected_index, 0)


class TestClickSecondRow(unittest.TestCase):
    def test_click_second_row(self) -> None:
        ctrl = _ctrl(row_height=24)
        ctrl.handle_event(_click(25), _app())
        self.assertEqual(ctrl.selected_index, 1)


class TestOnSelectCallback(unittest.TestCase):
    def test_on_select_callback_fires(self) -> None:
        calls = []
        ctrl = _ctrl(row_height=24, on_select=lambda idx, item: calls.append((idx, item.label)))
        ctrl.handle_event(_click(10), _app())
        self.assertEqual(calls[0][0], 0)


class TestKeyboardNavigationDown(unittest.TestCase):
    def test_keyboard_down_selects_next(self) -> None:
        ctrl = _ctrl(row_height=24)
        ctrl._selected_indices = [0]
        ctrl._focused = True
        ctrl.handle_event(_key(pygame.K_DOWN), _app())
        self.assertEqual(ctrl.selected_index, 1)


class TestKeyboardNavigationUp(unittest.TestCase):
    def test_keyboard_up_selects_prev(self) -> None:
        ctrl = _ctrl(row_height=24)
        ctrl._selected_indices = [2]
        ctrl._focused = True
        ctrl.handle_event(_key(pygame.K_UP), _app())
        self.assertEqual(ctrl.selected_index, 1)


class TestKeyboardHomeEnd(unittest.TestCase):
    def test_keyboard_home_jumps_to_first(self) -> None:
        ctrl = _ctrl(row_height=24)
        ctrl._selected_indices = [3]
        ctrl._focused = True
        ctrl.handle_event(_key(pygame.K_HOME), _app())
        self.assertEqual(ctrl.selected_index, 0)

    def test_keyboard_end_jumps_to_last(self) -> None:
        ctrl = _ctrl(row_height=24)
        ctrl._focused = True
        ctrl.handle_event(_key(pygame.K_END), _app())
        self.assertEqual(ctrl.selected_index, 4)


class TestSetItemsClearsSelection(unittest.TestCase):
    def test_set_items_clears_selection(self) -> None:
        ctrl = _ctrl(row_height=24)
        ctrl._selected_indices = [1]
        ctrl.set_items([ListItem("x")])
        self.assertEqual(ctrl.selected_index, -1)


class TestAppendItem(unittest.TestCase):
    def test_append_item_increases_count(self) -> None:
        ctrl = _ctrl(3, row_height=24)
        ctrl.append_item(ListItem("new"))
        self.assertEqual(ctrl.item_count(), 4)


class TestRemoveItemShiftsSelection(unittest.TestCase):
    def test_remove_item_before_selected_shifts_index(self) -> None:
        ctrl = _ctrl(5, row_height=24)
        ctrl._selected_indices = [3]
        ctrl.remove_item(1)
        self.assertEqual(ctrl.selected_index, 2)


class TestDisabledItemSkipped(unittest.TestCase):
    def test_disabled_item_not_selectable_via_click(self) -> None:
        items = [ListItem("a"), ListItem("b", enabled=False), ListItem("c")]
        ctrl = ListViewControl("lst", Rect(0, 0, 200, 120), items, row_height=24)
        ctrl.handle_event(_click(25), _app())  # row 1 = disabled
        self.assertEqual(ctrl.selected_index, -1)


class TestWheelScrolls(unittest.TestCase):
    def test_mouse_wheel_scrolls(self) -> None:
        ctrl = _ctrl(20, row_height=24)  # tall content
        initial_scroll = ctrl.scroll_offset
        ctrl.handle_event(_wheel(-1), _app())
        self.assertGreater(ctrl.scroll_offset, initial_scroll)


class TestScrollToItem(unittest.TestCase):
    def test_scroll_to_item_brings_into_view(self) -> None:
        ctrl = _ctrl(20, row_height=24)
        ctrl.scroll_to_item(15)
        self.assertGreater(ctrl.scroll_offset, 0)


class TestMultiSelectSpaceToggle(unittest.TestCase):
    def test_multi_select_space_toggles_selection(self) -> None:
        ctrl = _ctrl(5, multi_select=True, row_height=24)
        ctrl._selected_indices = [2]
        ctrl._focused = True
        ctrl.handle_event(_key(pygame.K_SPACE), _app())
        self.assertNotIn(2, ctrl.selected_indices)


class TestGuardDisabled(unittest.TestCase):
    def test_guard_disabled_returns_false(self) -> None:
        ctrl = _ctrl(row_height=24)
        ctrl.enabled = False
        self.assertFalse(ctrl.handle_event(_click(10), _app()))


class TestSelectedItemProperty(unittest.TestCase):
    def test_selected_item_returns_correct_item(self) -> None:
        ctrl = _ctrl(5, row_height=24)
        ctrl._selected_indices = [2]
        item = ctrl.selected_item
        self.assertIsNotNone(item)
        self.assertEqual(item.label, "Item 2")


if __name__ == "__main__":
    unittest.main()
