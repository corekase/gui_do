"""Tests for DragDropManager (Feature 10)."""
import unittest
from unittest.mock import MagicMock, patch

import pygame
from pygame import Rect

from gui_do.core.drag_drop_manager import DragDropManager, DragPayload
from gui_do.core.ui_node import UiNode
from gui_do.core.gui_event import EventType, GuiEvent


def _app():
    app = MagicMock()
    app.invalidation = MagicMock()
    return app


def _scene(*nodes):
    scene = MagicMock()
    scene._nodes = list(nodes)
    return scene


def _node_at(x, y, w=60, h=40) -> UiNode:
    return UiNode("n", Rect(x, y, w, h))


def _mouse_down(x, y) -> GuiEvent:
    return GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0, pos=(x, y), button=1)


def _mouse_up(x, y) -> GuiEvent:
    return GuiEvent(kind=EventType.MOUSE_BUTTON_UP, type=0, pos=(x, y), button=1)


def _mouse_motion(x, y) -> GuiEvent:
    return GuiEvent(kind=EventType.MOUSE_MOTION, type=0, pos=(x, y))


class TestDefaultNoDrag(unittest.TestCase):
    def test_is_active_false_initially(self) -> None:
        mgr = DragDropManager()
        self.assertFalse(mgr.is_active)

    def test_active_payload_none_initially(self) -> None:
        mgr = DragDropManager()
        self.assertIsNone(mgr.active_payload)


class TestMouseDownOnNonDraggableDoesNotStartSession(unittest.TestCase):
    def test_mouse_down_on_non_draggable_returns_false(self) -> None:
        mgr = DragDropManager()
        node = _node_at(0, 0)
        result = mgr.route_event(_mouse_down(10, 10), _scene(node), _app())
        self.assertFalse(result)
        self.assertFalse(mgr.is_active)


class TestDragStartsAfterThreshold(unittest.TestCase):
    def test_drag_active_after_threshold_motion(self) -> None:
        mgr = DragDropManager(drag_threshold=5)
        node = _node_at(0, 0)
        payload = DragPayload("item", data=42)
        node.on_drag_start = lambda evt: payload

        mgr.route_event(_mouse_down(10, 10), _scene(node), _app())
        # Not yet active (threshold not met)
        self.assertFalse(mgr.is_active)
        # Move past threshold
        mgr.route_event(_mouse_motion(20, 10), _scene(node), _app())
        self.assertTrue(mgr.is_active)
        self.assertIs(mgr.active_payload, payload)


class TestDragNotActiveBeforeThreshold(unittest.TestCase):
    def test_drag_not_active_before_threshold(self) -> None:
        mgr = DragDropManager(drag_threshold=20)
        node = _node_at(0, 0)
        node.on_drag_start = lambda evt: DragPayload("x")

        mgr.route_event(_mouse_down(10, 10), _scene(node), _app())
        mgr.route_event(_mouse_motion(12, 10), _scene(node), _app())
        self.assertFalse(mgr.is_active)


class TestMouseUpDropsPayload(unittest.TestCase):
    def test_mouse_up_calls_on_drop_and_on_drag_end(self) -> None:
        mgr = DragDropManager(drag_threshold=5)
        source = _node_at(0, 0)
        payload = DragPayload("p")
        source.on_drag_start = lambda evt: payload
        ended = []
        source.on_drag_end = lambda accepted: ended.append(accepted)

        target = _node_at(100, 0)
        dropped = []
        target.accepts_drop = lambda p: True
        target.on_drop = lambda p, pos: dropped.append(True) or True

        app = _app()
        scene = _scene(source, target)
        mgr.route_event(_mouse_down(10, 10), scene, app)
        mgr.route_event(_mouse_motion(110, 10), scene, app)
        mgr.route_event(_mouse_up(110, 10), scene, app)

        self.assertEqual(dropped, [True])
        self.assertEqual(ended, [True])


class TestMouseUpWithoutThresholdNotConsumed(unittest.TestCase):
    def test_mouse_up_without_threshold_not_consumed(self) -> None:
        mgr = DragDropManager(drag_threshold=50)
        node = _node_at(0, 0)
        node.on_drag_start = lambda evt: DragPayload("x")
        app = _app()
        scene = _scene(node)
        mgr.route_event(_mouse_down(10, 10), scene, app)
        result = mgr.route_event(_mouse_up(11, 10), scene, app)
        self.assertFalse(result)


class TestCancelEndsDrag(unittest.TestCase):
    def test_cancel_ends_drag_and_calls_on_drag_end(self) -> None:
        mgr = DragDropManager(drag_threshold=5)
        node = _node_at(0, 0)
        payload = DragPayload("c")
        node.on_drag_start = lambda evt: payload
        ended = []
        node.on_drag_end = lambda accepted: ended.append(accepted)

        app = _app()
        scene = _scene(node)
        mgr.route_event(_mouse_down(10, 10), scene, app)
        mgr.route_event(_mouse_motion(20, 10), scene, app)
        self.assertTrue(mgr.is_active)
        mgr.cancel(app)
        self.assertFalse(mgr.is_active)
        self.assertEqual(ended, [False])


class TestDragEnterLeaveCallbacks(unittest.TestCase):
    def test_drag_enter_called_when_entering_target(self) -> None:
        mgr = DragDropManager(drag_threshold=5)
        source = _node_at(0, 0)
        payload = DragPayload("e")
        source.on_drag_start = lambda evt: payload

        target = _node_at(100, 0)
        target.accepts_drop = lambda p: True
        entered = []
        target.on_drag_enter = lambda p: entered.append(1)

        app = _app()
        scene = _scene(source, target)
        mgr.route_event(_mouse_down(10, 10), scene, app)
        mgr.route_event(_mouse_motion(110, 10), scene, app)
        self.assertGreater(len(entered), 0)


class TestAcceptsDropDefaultFalse(unittest.TestCase):
    def test_accepts_drop_returns_false_by_default(self) -> None:
        node = _node_at(0, 0)
        self.assertFalse(node.accepts_drop(DragPayload("x")))


class TestOnDragStartReturnsNoneByDefault(unittest.TestCase):
    def test_on_drag_start_returns_none_by_default(self) -> None:
        node = _node_at(0, 0)
        result = node.on_drag_start(GuiEvent(kind=EventType.MOUSE_BUTTON_DOWN, type=0, pos=(0, 0), button=1))
        self.assertIsNone(result)


class TestDrawDoesNothingWhenNotActive(unittest.TestCase):
    def test_draw_does_nothing_when_not_active(self) -> None:
        import pygame
        pygame.init()
        surface = pygame.Surface((100, 100))
        theme = MagicMock()
        mgr = DragDropManager()
        mgr.draw(surface, theme)  # Should not raise


if __name__ == "__main__":
    unittest.main()
