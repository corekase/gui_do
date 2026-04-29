"""Tests for ListViewControl (Feature 8)."""
import unittest
from unittest.mock import MagicMock
from unittest.mock import patch

import pygame
from pygame import Rect

from gui_do.controls.data.list_view_control import ListItem, ListViewControl
from gui_do.controls.composite.scroll_view_control import ScrollViewControl
from gui_do.events.gui_event import EventType, GuiEvent
from gui_do.events.pointer_capture import PointerCapture


def _items(n: int = 5) -> list:
    return [ListItem(label=f"Item {i}", value=i) for i in range(n)]


def _ctrl(n: int = 5, **kwargs) -> ListViewControl:
    return ListViewControl("lst", Rect(0, 0, 200, 120), _items(n), **kwargs)


def _app():
    class _AppStub:
        def __init__(self):
            self.logical_pointer_pos = (0, 0)
            self.pointer_capture = PointerCapture()
            self.synced_pointer_pos = None

        def set_logical_pointer_position(self, pos, apply_constraints=True):
            self.logical_pointer_pos = (int(pos[0]), int(pos[1]))

        def sync_pointer_to_logical_position(self, pos):
            self.synced_pointer_pos = (int(pos[0]), int(pos[1]))

    return _AppStub()


def _click(y: int) -> GuiEvent:
    return GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0, pos=(10, y), button=1)


def _click_at(x: int, y: int) -> GuiEvent:
    return GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0, pos=(x, y), button=1)


def _key(k: int) -> GuiEvent:
    return GuiEvent(kind=EventType.KEY_DOWN, type=0, key=k, mod=0)


def _wheel(delta: int, *, pos=(10, 10)) -> GuiEvent:
    e = GuiEvent(kind=EventType.MOUSE_WHEEL, type=0)
    e.y = delta
    e.wheel_y = delta
    e.pos = pos
    return e


def _motion(pos: tuple[int, int]) -> GuiEvent:
    return GuiEvent(kind=EventType.MOUSE_MOTION, type=0, pos=pos)


def _mouse_up(pos: tuple[int, int]) -> GuiEvent:
    return GuiEvent(kind=EventType.MOUSE_BUTTON_UP, type=0, pos=pos, button=1)


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


class TestClickOutsideHorizontalBounds(unittest.TestCase):
    def test_click_left_of_rect_does_not_select(self) -> None:
        ctrl = _ctrl(row_height=24)
        handled = ctrl.handle_event(_click_at(-1, 25), _app())
        self.assertFalse(handled)
        self.assertEqual(ctrl.selected_index, 0)

    def test_click_right_of_rect_does_not_select(self) -> None:
        ctrl = _ctrl(row_height=24)
        handled = ctrl.handle_event(_click_at(205, 25), _app())
        self.assertFalse(handled)
        self.assertEqual(ctrl.selected_index, 0)


class TestDefaultSelectionOnCreation(unittest.TestCase):
    def test_defaults_to_first_item_when_unspecified(self) -> None:
        ctrl = _ctrl(row_height=24)
        self.assertEqual(ctrl.selected_index, 0)


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
        self.assertEqual(ctrl.selected_index, 0)


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
        self.assertEqual(ctrl.selected_index, 0)


class TestWheelScrolls(unittest.TestCase):
    def test_mouse_wheel_scrolls(self) -> None:
        ctrl = _ctrl(20, row_height=24)  # tall content
        initial_scroll = ctrl.scroll_offset
        ctrl.handle_event(_wheel(-1), _app())
        self.assertGreater(ctrl.scroll_offset, initial_scroll)

    def test_mouse_wheel_outside_bounds_does_not_scroll(self) -> None:
        ctrl = _ctrl(20, row_height=24)
        initial_scroll = ctrl.scroll_offset
        handled = ctrl.handle_event(_wheel(-1, pos=(500, 500)), _app())
        self.assertFalse(handled)
        self.assertEqual(ctrl.scroll_offset, initial_scroll)

    def test_mouse_wheel_uses_wheel_delta_field(self) -> None:
        ctrl = _ctrl(20, row_height=24)
        event = GuiEvent(kind=EventType.MOUSE_WHEEL, type=0, pos=(10, 10), wheel_y=-1)
        initial_scroll = ctrl.scroll_offset
        handled = ctrl.handle_event(event, _app())
        self.assertTrue(handled)
        self.assertGreater(ctrl.scroll_offset, initial_scroll)


class TestScrollbarDrag(unittest.TestCase):
    def test_dragging_scrollbar_handle_scrolls_content(self) -> None:
        ctrl = _ctrl(30, row_height=24)
        app = _app()
        handle = ctrl._scrollbar_handle_rect()
        self.assertIsNotNone(handle)
        assert handle is not None
        start = (handle.centerx, handle.centery)

        consumed_down = ctrl.handle_event(GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0, pos=start, button=1), app)
        self.assertTrue(consumed_down)
        self.assertTrue(app.pointer_capture.is_owned_by("lst"))

        app.logical_pointer_pos = (start[0], start[1] + 40)
        consumed_motion = ctrl.handle_event(_motion(app.logical_pointer_pos), app)
        self.assertTrue(consumed_motion)
        self.assertGreater(ctrl.scroll_offset, 0)

        consumed_up = ctrl.handle_event(_mouse_up(app.logical_pointer_pos), app)
        self.assertTrue(consumed_up)
        self.assertFalse(app.pointer_capture.is_owned_by("lst"))


class TestEmbeddedInScrollViewRendering(unittest.TestCase):
    def test_embedded_list_draws_last_item_label(self) -> None:
        scroll = ScrollViewControl(
            "sv",
            Rect(0, 0, 200, 120),
            content_width=180,
            content_height=24 * 8,
            scroll_y=True,
        )
        lst = ListViewControl(
            "lst",
            Rect(0, 0, 180, 24 * 8),
            [ListItem(label=f"Item {i}", value=i) for i in range(8)],
            row_height=24,
            show_scrollbar=False,
        )
        scroll.add(lst, content_x=4, content_y=0)
        scroll.set_scroll(y=24 * 3)

        rendered_labels: list[str] = []

        class _StubFont:
            def render(self, text, _aa, _color):
                rendered_labels.append(text)
                return pygame.Surface((8, 8))

            def get_height(self):
                return 8

        surface = pygame.Surface((240, 180))
        theme = MagicMock()
        theme.background = (30, 30, 30)
        theme.text = (220, 220, 220)
        theme.highlight = (0, 100, 200)

        with patch("gui_do.controls.data.list_view_control.pygame.font.SysFont", return_value=_StubFont()):
            lst.draw(surface, theme)

        self.assertIn("Item 7", rendered_labels)


class TestScrollToItem(unittest.TestCase):
    def test_scroll_to_item_brings_into_view(self) -> None:
        ctrl = _ctrl(20, row_height=24)
        ctrl.scroll_to_item(15)
        self.assertGreater(ctrl.scroll_offset, 0)


class TestMultiSelectSpaceToggle(unittest.TestCase):
    def test_multi_select_space_toggles_selection(self) -> None:
        ctrl = _ctrl(5, multi_select=True, row_height=24)
        ctrl._selected_indices = [2, 3]
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
