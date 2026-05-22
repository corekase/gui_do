"""Tests for FrameTimer, WindowRelativeRect, PlacedControl, FeatureMessage."""
import unittest
import time
import pygame
from pygame import Rect

from gui_do.features.feature_lifecycle import (
    ControlPlacementSpec,
    FeatureWindowPresentationModel,
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


class _StubWindowFeature:
    def __init__(self, window):
        self.window = window


class _StubRaiseParent:
    def __init__(self, children):
        self.children = list(children)

    def _raise_window(self, window):
        if window in self.children:
            self.children.remove(window)
            self.children.append(window)


class _StubWindowNode:
    def __init__(self, control_id: str, *, visible: bool = True):
        self.control_id = str(control_id)
        self.visible = bool(visible)
        self.parent = None
        self.window_effects = {
            "shear_enabled": True,
            "hide_show_enabled": False,
            "grow_shrink_enabled": False,
        }


class _StubAppForRaiseRelayout:
    def __init__(self):
        self.calls = []

    @staticmethod
    def is_window_tiling_enabled() -> bool:
        return True

    def tile_windows(
        self,
        newly_visible=None,
        *,
        raised_windows=None,
        as_visibility_event: bool = False,
        force: bool = False,
    ):
        self.calls.append(
            {
                "newly_visible": newly_visible,
                "raised_windows": raised_windows,
                "as_visibility_event": bool(as_visibility_event),
                "force": bool(force),
            }
        )


class _StubAppForToggleOpenWithTilingDisabled:
    def __init__(self):
        self.calls = []
        self.window_tiling = object()

    @staticmethod
    def is_window_tiling_enabled() -> bool:
        return False

    def tile_windows(
        self,
        newly_visible=None,
        *,
        raised_windows=None,
        as_visibility_event: bool = False,
        force: bool = False,
    ):
        self.calls.append(
            {
                "newly_visible": newly_visible,
                "raised_windows": raised_windows,
                "as_visibility_event": bool(as_visibility_event),
                "force": bool(force),
            }
        )


class _StubHostForPresentation:
    def __init__(self, app, feature_attr_name: str, feature_obj):
        self.app = app
        setattr(self, feature_attr_name, feature_obj)


class TestFeatureWindowPresentationModelRaise(unittest.TestCase):
    def test_show_visible_window_raises_without_global_tile_relayout(self):
        app = _StubAppForRaiseRelayout()

        raised_window = _StubWindowNode("raised_window", visible=True)
        other_window = _StubWindowNode("other_window", visible=True)
        parent = _StubRaiseParent([raised_window, other_window])
        raised_window.parent = parent
        other_window.parent = parent

        host = _StubHostForPresentation(app, "life_feature", _StubWindowFeature(raised_window))
        model = FeatureWindowPresentationModel(host, tile_windows=app.tile_windows)
        model.register_feature_window("life", feature_attribute_name="life_feature")

        model.show("life")

        self.assertIs(parent.children[-1], raised_window)
        self.assertEqual([], app.calls)

    def test_get_window_marks_opt_out_window_as_unmanaged_for_tiling(self):
        app = _StubAppForRaiseRelayout()
        window = _StubWindowNode("opt_out_window", visible=True)
        host = _StubHostForPresentation(app, "opt_out_feature", _StubWindowFeature(window))
        model = FeatureWindowPresentationModel(host, tile_windows=app.tile_windows)
        model.register_feature_window(
            "opt_out",
            feature_attribute_name="opt_out_feature",
            window_management_opt_in=False,
        )

        resolved = model.get_window("opt_out")

        self.assertIs(resolved, window)
        self.assertFalse(bool(getattr(window, "_window_management_opt_in", True)))

    def test_set_visible_opt_out_binding_does_not_call_tile_windows(self):
        app = _StubAppForRaiseRelayout()
        window = _StubWindowNode("opt_out_window", visible=False)
        host = _StubHostForPresentation(app, "opt_out_feature", _StubWindowFeature(window))
        model = FeatureWindowPresentationModel(host, tile_windows=app.tile_windows)
        model.register_feature_window(
            "opt_out",
            feature_attribute_name="opt_out_feature",
            window_management_opt_in=False,
        )

        model.set_visible("opt_out", True)

        self.assertTrue(window.visible)
        self.assertEqual([], app.calls)

    def test_task_panel_toggle_open_forces_relayout_when_tiling_disabled(self):
        app = _StubAppForToggleOpenWithTilingDisabled()
        window = _StubWindowNode("life_window", visible=False)
        host = _StubHostForPresentation(app, "life_feature", _StubWindowFeature(window))
        model = FeatureWindowPresentationModel(host, tile_windows=app.tile_windows)
        model.register_feature_window("life", feature_attribute_name="life_feature")

        model.set_visible("life", True, from_toggle=True)

        self.assertTrue(window.visible)
        self.assertEqual(1, len(app.calls))
        self.assertTrue(bool(app.calls[0]["as_visibility_event"]))
        self.assertTrue(bool(app.calls[0]["force"]))


if __name__ == "__main__":
    unittest.main()
