"""Tests for FrameTimer, WindowRelativeRect, PlacedControl, FeatureMessage."""
import unittest
import time
import pygame
from pygame import Rect

from gui_do.features.feature_lifecycle import (
    ControlPlacementSpec,
    FeatureMessage,
    FrameTimer,
    PlacedControl,
    WindowRelativeRect,
    place_control,
    place_control_specs,
    place_control_unlabeled,
)

pygame.init()


# ===========================================================================
# FrameTimer
# ===========================================================================


class TestFrameTimer(unittest.TestCase):
    def test_first_tick_returns_zero(self):
        timer = FrameTimer()
        dt = timer.tick()
        self.assertEqual(0.0, dt)

    def test_second_tick_returns_positive(self):
        timer = FrameTimer()
        timer.tick()  # first call
        time.sleep(0.005)
        dt = timer.tick()
        self.assertGreater(dt, 0.0)

    def test_reset_causes_next_tick_to_return_zero(self):
        timer = FrameTimer()
        timer.tick()  # arm
        time.sleep(0.005)
        timer.reset()
        dt = timer.tick()
        self.assertEqual(0.0, dt)


# ===========================================================================
# PlacedControl
# ===========================================================================


class TestPlacedControl(unittest.TestCase):
    def test_fields_stored(self):
        control = object()
        label = object()
        pc = PlacedControl(
            control=control,
            label=label,
            name="my_control",
            column_index=1,
            row_index=2,
        )
        self.assertIs(control, pc.control)
        self.assertIs(label, pc.label)
        self.assertEqual("my_control", pc.name)
        self.assertEqual(1, pc.column_index)
        self.assertEqual(2, pc.row_index)

    def test_label_can_be_none(self):
        pc = PlacedControl(control=object(), label=None, name="x", column_index=0, row_index=0)
        self.assertIsNone(pc.label)


# ===========================================================================
# WindowRelativeRect
# ===========================================================================


class _MockWindow:
    def __init__(self, x, y):
        self.rect = Rect(x, y, 400, 300)


class TestWindowRelativeRect(unittest.TestCase):
    def test_resolve_at_same_position(self):
        win = _MockWindow(100, 200)
        child_rect = Rect(110, 220, 50, 30)
        wrr = WindowRelativeRect(win, child_rect)
        resolved = wrr.resolve()
        self.assertEqual(Rect(110, 220, 50, 30), resolved)

    def test_resolve_after_window_move(self):
        win = _MockWindow(100, 200)
        child_rect = Rect(110, 220, 50, 30)
        wrr = WindowRelativeRect(win, child_rect)
        win.rect = Rect(50, 100, 400, 300)  # move window
        resolved = wrr.resolve()
        self.assertEqual(Rect(60, 120, 50, 30), resolved)

    def test_relative_offsets_stored(self):
        win = _MockWindow(100, 200)
        child_rect = Rect(110, 230, 50, 30)
        wrr = WindowRelativeRect(win, child_rect)
        self.assertEqual(10, wrr.rel_x)
        self.assertEqual(30, wrr.rel_y)

    def test_width_height_properties(self):
        win = _MockWindow(0, 0)
        wrr = WindowRelativeRect(win, Rect(0, 0, 75, 40))
        self.assertEqual(75, wrr.width)
        self.assertEqual(40, wrr.height)


# ===========================================================================
# FeatureMessage
# ===========================================================================


class TestFeatureMessage(unittest.TestCase):
    def _msg(self, payload=None):
        return FeatureMessage(sender="feat_a", target="feat_b", payload=payload or {})

    def test_fields_stored(self):
        msg = FeatureMessage(sender="a", target="b", payload={"key": "val"})
        self.assertEqual("a", msg.sender)
        self.assertEqual("b", msg.target)
        self.assertEqual({"key": "val"}, msg.payload)

    def test_getitem(self):
        msg = FeatureMessage(sender="a", target="b", payload={"x": 42})
        self.assertEqual(42, msg["x"])

    def test_get_existing(self):
        msg = FeatureMessage(sender="a", target="b", payload={"y": 99})
        self.assertEqual(99, msg.get("y"))

    def test_get_missing_default(self):
        msg = self._msg()
        self.assertIsNone(msg.get("missing"))

    def test_get_missing_custom_default(self):
        msg = self._msg()
        self.assertEqual("fallback", msg.get("missing", "fallback"))

    def test_topic_property(self):
        msg = FeatureMessage(sender="a", target="b", payload={"topic": "refresh"})
        self.assertEqual("refresh", msg.topic)

    def test_topic_missing_returns_none(self):
        msg = self._msg()
        self.assertIsNone(msg.topic)

    def test_command_property(self):
        msg = FeatureMessage(sender="a", target="b", payload={"command": "stop"})
        self.assertEqual("stop", msg.command)

    def test_event_property(self):
        msg = FeatureMessage(sender="a", target="b", payload={"event": "loaded"})
        self.assertEqual("loaded", msg.event)

    def test_from_payload(self):
        msg = FeatureMessage.from_payload("s", "t", {"k": "v"})
        self.assertEqual("s", msg.sender)
        self.assertEqual("t", msg.target)
        self.assertEqual({"k": "v"}, msg.payload)

    def test_from_payload_copies_dict(self):
        source = {"k": "v"}
        msg = FeatureMessage.from_payload("s", "t", source)
        source["k"] = "changed"
        self.assertEqual("v", msg.payload["k"])


class _StubControl:
    def __init__(self):
        self.rect = Rect(0, 0, 1, 1)
        self.tab_index = -1
        self.enabled = False
        self.accessibility = None

    def set_rect(self, rect):
        self.rect = Rect(rect)

    def set_tab_index(self, tab_index):
        self.tab_index = int(tab_index)

    def set_accessibility(self, *, role, label):
        self.accessibility = (role, label)


class _StubContainer:
    def __init__(self):
        self.children = []

    def add(self, control):
        self.children.append(control)
        return control


class TestPlacementHelpers(unittest.TestCase):
    def test_place_control_adds_label_and_control_once_each(self):
        container = _StubContainer()
        control = _StubControl()
        labels = []
        controls = []
        placed = []

        place_control(
            container,
            "alpha",
            "Alpha",
            control,
            Rect(10, 20, 100, 40),
            focusable=True,
            placed_controls=placed,
            control_labels=labels,
            controls=controls,
        )

        self.assertEqual(2, len(container.children))
        self.assertEqual(1, len(labels))
        self.assertEqual(1, len(controls))
        self.assertEqual(1, len(placed))
        self.assertEqual(Rect(10, 42, 100, 18), control.rect)
        self.assertEqual(0, control.tab_index)

    def test_place_control_focusable_preserves_existing_non_negative_tab_index(self):
        container = _StubContainer()
        control = _StubControl()
        control.set_tab_index(7)

        place_control(
            container,
            "alpha",
            "Alpha",
            control,
            Rect(10, 20, 100, 40),
            focusable=True,
        )

        self.assertEqual(7, control.tab_index)

    def test_place_control_unlabeled_disables_non_focusable(self):
        container = _StubContainer()
        control = _StubControl()

        place_control_unlabeled(
            container,
            "beta",
            control,
            Rect(0, 0, 20, 20),
            focusable=False,
        )

        self.assertEqual(-1, control.tab_index)
        self.assertEqual(1, len(container.children))

    def test_place_control_specs_mixes_labeled_and_unlabeled(self):
        container = _StubContainer()
        labeled = _StubControl()
        unlabeled = _StubControl()
        placed = []

        specs = (
            ControlPlacementSpec(
                name="labeled",
                label_text="Labeled",
                control=labeled,
                control_rect=Rect(0, 0, 100, 32),
                focusable=True,
                labeled=True,
            ),
            ControlPlacementSpec(
                name="unlabeled",
                control=unlabeled,
                control_rect=Rect(0, 0, 80, 24),
                focusable=False,
                labeled=False,
            ),
        )

        place_control_specs(
            container,
            specs,
            placed_controls=placed,
        )

        self.assertEqual(3, len(container.children))
        self.assertEqual(2, len(placed))
        self.assertEqual("labeled", placed[0].name)
        self.assertEqual("unlabeled", placed[1].name)
        self.assertEqual(0, labeled.tab_index)
        self.assertEqual(-1, unlabeled.tab_index)


if __name__ == "__main__":
    unittest.main()
