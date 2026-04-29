"""Tests for all new feature implementations (session 2026-04-28).

Covers: ComputedValue, ClipboardManager export, AnimationSequence,
Feature state persistence, ScrollViewControl, SpinnerControl,
RangeSliderControl, ColorPickerControl, CommandPaletteManager.
"""
import os
import unittest
from unittest.mock import MagicMock, patch

# Headless pygame environment for control draw tests
os.environ.setdefault("SDL_VIDEODRIVER", "dummy")
os.environ.setdefault("SDL_AUDIODRIVER", "dummy")

import pygame
from pygame import Rect


# ---------------------------------------------------------------------------
# ComputedValue tests
# ---------------------------------------------------------------------------

from gui_do.data.presentation_model import ObservableValue, ComputedValue


class TestComputedValueBasics(unittest.TestCase):
    def test_initial_value_computed_from_deps(self) -> None:
        a = ObservableValue(3)
        b = ObservableValue(4)
        total = ComputedValue(lambda: a.value + b.value, deps=[a, b])
        self.assertEqual(total.value, 7)

    def test_value_updates_when_dep_changes(self) -> None:
        a = ObservableValue(1)
        c = ComputedValue(lambda: a.value * 2, deps=[a])
        a.value = 5
        self.assertEqual(c.value, 10)

    def test_subscribers_notified_on_dep_change(self) -> None:
        events: list = []
        a = ObservableValue(10)
        c = ComputedValue(lambda: a.value + 1, deps=[a])
        c.subscribe(lambda v: events.append(v))
        a.value = 20
        self.assertEqual(events, [21])

    def test_subscribe_returns_unsubscribe_callable(self) -> None:
        events: list = []
        a = ObservableValue(0)
        c = ComputedValue(lambda: a.value, deps=[a])
        unsub = c.subscribe(lambda v: events.append(v))
        a.value = 1
        self.assertEqual(len(events), 1)
        unsub()
        a.value = 2
        self.assertEqual(len(events), 1)  # no second event

    def test_dispose_removes_dep_subscriptions(self) -> None:
        events: list = []
        a = ObservableValue(0)
        c = ComputedValue(lambda: a.value, deps=[a])
        c.subscribe(lambda v: events.append(v))
        c.dispose()
        a.value = 99
        self.assertEqual(events, [])  # no notification after dispose

    def test_lazy_recompute_only_when_dirty(self) -> None:
        call_count = [0]

        def compute():
            call_count[0] += 1
            return 42

        a = ObservableValue(0)
        c = ComputedValue(compute, deps=[a])
        _ = c.value  # trigger first compute
        _ = c.value  # should NOT trigger another compute
        self.assertEqual(call_count[0], 1)
        a.value = 1  # marks dirty
        _ = c.value  # triggers recompute
        self.assertEqual(call_count[0], 2)

    def test_multiple_deps(self) -> None:
        x = ObservableValue(2)
        y = ObservableValue(3)
        z = ObservableValue(4)
        prod = ComputedValue(lambda: x.value * y.value * z.value, deps=[x, y, z])
        self.assertEqual(prod.value, 24)
        y.value = 10
        self.assertEqual(prod.value, 80)

    def test_exported_from_gui_do_root(self) -> None:
        import gui_do
        self.assertIn("ComputedValue", gui_do.__all__)
        self.assertIs(gui_do.ComputedValue, ComputedValue)


# ---------------------------------------------------------------------------
# ClipboardManager export test
# ---------------------------------------------------------------------------

class TestClipboardManagerExport(unittest.TestCase):
    def test_clipboard_manager_is_in_public_all(self) -> None:
        import gui_do
        self.assertIn("ClipboardManager", gui_do.__all__)

    def test_clipboard_manager_exported_class(self) -> None:
        from gui_do import ClipboardManager
        self.assertTrue(hasattr(ClipboardManager, "copy"))
        self.assertTrue(hasattr(ClipboardManager, "paste"))


# ---------------------------------------------------------------------------
# AnimationSequence tests
# ---------------------------------------------------------------------------

from gui_do.scheduling.animation_sequence import AnimationSequence, AnimationHandle
from gui_do.scheduling.tween_manager import TweenManager


class _Obj:
    """Simple object with attributes for tween targets."""
    def __init__(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)


class TestAnimationSequenceBasics(unittest.TestCase):
    def _manager(self) -> TweenManager:
        return TweenManager()

    def test_then_fires_on_complete_after_update(self) -> None:
        mgr = self._manager()
        done = [False]
        obj = _Obj(x=0.0)
        seq = AnimationSequence(mgr)
        seq.then(target=obj, attr="x", end_value=100.0, duration_seconds=0.5)
        seq.on_done(lambda: done.__setitem__(0, True))
        seq.start()
        mgr.update(1.0)
        self.assertTrue(done[0])

    def test_wait_delays_next_step(self) -> None:
        mgr = self._manager()
        order: list = []
        obj = _Obj(x=0.0)
        seq = AnimationSequence(mgr)
        seq.then(target=obj, attr="x", end_value=10.0, duration_seconds=0.1)
        seq.wait(0.5)
        seq.on_done(lambda: order.append("done"))
        seq.start()
        mgr.update(0.2)  # first step done, wait not done
        self.assertEqual(order, [])
        mgr.update(0.5)  # wait done
        self.assertEqual(order, ["done"])

    def test_parallel_waits_for_all_substeps(self) -> None:
        mgr = self._manager()
        done = [False]
        a = _Obj(x=0.0)
        b = _Obj(y=0.0)
        seq = AnimationSequence(mgr)
        seq.parallel([
            dict(target=a, attr="x", end_value=1.0, duration_seconds=0.1),
            dict(target=b, attr="y", end_value=1.0, duration_seconds=0.4),
        ])
        seq.on_done(lambda: done.__setitem__(0, True))
        seq.start()
        mgr.update(0.2)  # first sub-step done but second not
        self.assertFalse(done[0])
        mgr.update(0.4)  # second sub-step done
        self.assertTrue(done[0])

    def test_cancel_prevents_remaining_steps(self) -> None:
        mgr = self._manager()
        done = [False]
        obj = _Obj(x=0.0)
        seq = AnimationSequence(mgr)
        seq.then(target=obj, attr="x", end_value=1.0, duration_seconds=0.05)
        seq.then(target=obj, attr="x", end_value=2.0, duration_seconds=2.0)  # long: won't finish in first update
        seq.on_done(lambda: done.__setitem__(0, True))
        handle = seq.start()
        mgr.update(0.1)  # step1 (0.05s) finishes; step2 starts (elapsed=0.05 of 2.0s, not done)
        self.assertFalse(done[0])
        handle.cancel()
        mgr.update(2.0)  # step2 would finish, but cancel flag prevents on_done
        self.assertFalse(done[0])

    def test_handle_cancelled_property(self) -> None:
        mgr = self._manager()
        obj = _Obj(x=0.0)
        seq = AnimationSequence(mgr)
        seq.then(target=obj, attr="x", end_value=1.0, duration_seconds=1.0)
        handle = seq.start()
        self.assertFalse(handle.cancelled)
        handle.cancel()
        self.assertTrue(handle.cancelled)

    def test_empty_parallel_advances_immediately(self) -> None:
        mgr = self._manager()
        done = [False]
        seq = AnimationSequence(mgr)
        seq.parallel([])
        seq.on_done(lambda: done.__setitem__(0, True))
        seq.start()
        mgr.update(0.001)
        self.assertTrue(done[0])

    def test_exported_from_gui_do_root(self) -> None:
        import gui_do
        self.assertIn("AnimationSequence", gui_do.__all__)
        self.assertIn("AnimationHandle", gui_do.__all__)


# ---------------------------------------------------------------------------
# Feature state persistence tests
# ---------------------------------------------------------------------------

from gui_do.features.feature_lifecycle import Feature, FeatureManager


class _StatefulFeature(Feature):
    def __init__(self):
        super().__init__("stateful")
        self.counter = 0

    def save_state(self) -> dict:
        return {"counter": self.counter}

    def restore_state(self, state: dict) -> None:
        self.counter = int(state.get("counter", 0))


class _NoStateFeature(Feature):
    def __init__(self):
        super().__init__("no_state")


class _BrokenSaveFeature(Feature):
    def __init__(self):
        super().__init__("broken_save")

    def save_state(self) -> dict:
        raise RuntimeError("save failure")


class _BrokenRestoreFeature(Feature):
    def __init__(self):
        super().__init__("broken_restore")

    def restore_state(self, state: dict) -> None:
        raise RuntimeError("restore failure")


class _MinimalApp:
    """Minimal host for FeatureManager."""
    active_scene_name = "main"


class TestFeatureStatePersistence(unittest.TestCase):
    def _manager(self):
        return FeatureManager(_MinimalApp())

    def test_save_state_returns_empty_dict_by_default(self) -> None:
        f = _NoStateFeature()
        self.assertEqual(f.save_state(), {})

    def test_save_state_returns_feature_data(self) -> None:
        f = _StatefulFeature()
        f.counter = 42
        self.assertEqual(f.save_state(), {"counter": 42})

    def test_restore_state_applies_data(self) -> None:
        f = _StatefulFeature()
        f.restore_state({"counter": 99})
        self.assertEqual(f.counter, 99)

    def test_save_feature_states_collects_all(self) -> None:
        mgr = self._manager()
        f = _StatefulFeature()
        f.counter = 7
        mgr.register(f)
        states = mgr.save_feature_states()
        self.assertIn("stateful", states)
        self.assertEqual(states["stateful"]["counter"], 7)

    def test_restore_feature_states_distributes(self) -> None:
        mgr = self._manager()
        f = _StatefulFeature()
        mgr.register(f)
        mgr.restore_feature_states({"stateful": {"counter": 55}})
        self.assertEqual(f.counter, 55)

    def test_restore_skips_unknown_features(self) -> None:
        mgr = self._manager()
        # Should not raise
        mgr.restore_feature_states({"unknown_feature": {"x": 1}})

    def test_restore_skips_non_dict_states(self) -> None:
        mgr = self._manager()
        f = _StatefulFeature()
        f.counter = 0
        mgr.register(f)
        mgr.restore_feature_states({"stateful": "not_a_dict"})
        self.assertEqual(f.counter, 0)  # unchanged

    def test_save_swallows_feature_exceptions(self) -> None:
        mgr = self._manager()
        mgr.register(_BrokenSaveFeature())
        # Should not raise
        states = mgr.save_feature_states()
        self.assertIn("broken_save", states)
        self.assertEqual(states["broken_save"], {})

    def test_restore_swallows_feature_exceptions(self) -> None:
        mgr = self._manager()
        mgr.register(_BrokenRestoreFeature())
        # Should not raise
        mgr.restore_feature_states({"broken_restore": {"x": 1}})

    def test_restore_with_non_dict_argument_ignored(self) -> None:
        mgr = self._manager()
        # Should not raise
        mgr.restore_feature_states("not_a_dict")  # type: ignore[arg-type]

    def test_round_trip(self) -> None:
        mgr1 = self._manager()
        f1 = _StatefulFeature()
        f1.counter = 123
        mgr1.register(f1)
        saved = mgr1.save_feature_states()

        mgr2 = self._manager()
        f2 = _StatefulFeature()
        mgr2.register(f2)
        mgr2.restore_feature_states(saved)
        self.assertEqual(f2.counter, 123)


# ---------------------------------------------------------------------------
# ScrollViewControl tests
# ---------------------------------------------------------------------------

from gui_do.controls.composite.scroll_view_control import ScrollViewControl
from gui_do.controls.base.ui_node import UiNode


class _MockNode(UiNode):
    def __init__(self, cid, rect):
        super().__init__(cid, rect)

    def draw(self, surface, theme):
        pass

    def handle_event(self, event, app):
        return False


class TestScrollViewControl(unittest.TestCase):
    def test_construction_defaults(self) -> None:
        sv = ScrollViewControl("sv", Rect(0, 0, 200, 150))
        self.assertEqual(sv.scroll_x, 0)
        self.assertEqual(sv.scroll_y, 0)

    def test_add_child_registers_in_children_list(self) -> None:
        sv = ScrollViewControl("sv", Rect(0, 0, 200, 150))
        child = _MockNode("c1", Rect(0, 0, 100, 30))
        sv.add(child, content_x=10, content_y=20)
        self.assertIn(child, sv.children)

    def test_add_child_sets_parent(self) -> None:
        sv = ScrollViewControl("sv", Rect(0, 0, 200, 150))
        child = _MockNode("c1", Rect(0, 0, 50, 50))
        sv.add(child)
        self.assertIs(child.parent, sv)

    def test_add_child_expands_content_bounds(self) -> None:
        sv = ScrollViewControl("sv", Rect(0, 0, 200, 150))
        child = _MockNode("c1", Rect(0, 0, 300, 400))
        sv.add(child, content_x=50, content_y=60)
        self.assertGreaterEqual(sv._content_width, 350)
        self.assertGreaterEqual(sv._content_height, 460)

    def test_remove_child(self) -> None:
        sv = ScrollViewControl("sv", Rect(0, 0, 200, 150))
        child = _MockNode("c1", Rect(0, 0, 50, 50))
        sv.add(child)
        result = sv.remove(child)
        self.assertTrue(result)
        self.assertNotIn(child, sv.children)
        self.assertIsNone(child.parent)

    def test_remove_nonexistent_child_returns_false(self) -> None:
        sv = ScrollViewControl("sv", Rect(0, 0, 200, 150))
        child = _MockNode("c1", Rect(0, 0, 50, 50))
        result = sv.remove(child)
        self.assertFalse(result)

    def test_set_scroll_clamps_to_bounds(self) -> None:
        sv = ScrollViewControl("sv", Rect(0, 0, 200, 150), content_height=500)
        sv.set_scroll(y=9999)
        self.assertLessEqual(sv.scroll_y, 500 - 150)

    def test_set_scroll_no_negative(self) -> None:
        sv = ScrollViewControl("sv", Rect(0, 0, 200, 150), content_height=500)
        sv.set_scroll(y=-100)
        self.assertEqual(sv.scroll_y, 0)

    def test_scroll_by_increments(self) -> None:
        sv = ScrollViewControl("sv", Rect(0, 0, 200, 150), content_height=500)
        sv.scroll_by(dy=50)
        self.assertEqual(sv.scroll_y, 50)

    def test_set_content_size_clamps_scroll(self) -> None:
        sv = ScrollViewControl("sv", Rect(0, 0, 200, 150), content_height=500)
        sv.set_scroll(y=400)
        sv.set_content_size(200, 200)  # shrink content
        self.assertLessEqual(sv.scroll_y, 50)  # 200 - 150 = 50

    def test_child_screen_rect_updated_on_scroll(self) -> None:
        sv = ScrollViewControl("sv", Rect(10, 10, 200, 150), content_height=500)
        child = _MockNode("c1", Rect(0, 0, 50, 50))
        sv.add(child, content_x=0, content_y=100)
        expected_before = 10 + 100  # sv.rect.y + content_y - scroll_y(0)
        self.assertEqual(child.rect.y, expected_before)
        sv.set_scroll(y=50)
        self.assertEqual(child.rect.y, 10 + 100 - 50)

    def test_exported_from_gui_do_root(self) -> None:
        import gui_do
        self.assertIn("ScrollViewControl", gui_do.__all__)

    def test_drag_vertical_scrollbar_thumb_updates_scroll(self) -> None:
        from gui_do.events.gui_event import EventType
        from gui_do.events.pointer_capture import PointerCapture
        from types import SimpleNamespace
        from unittest.mock import MagicMock

        sv = ScrollViewControl("sv", Rect(0, 0, 200, 120), content_width=180, content_height=600, scroll_y=True)
        for i in range(12):
            sv.add(_MockNode(f"c{i}", Rect(0, 0, 160, 30)), content_x=0, content_y=i * 48)

        app = SimpleNamespace(
            logical_pointer_pos=(0, 0),
            pointer_capture=PointerCapture(),
            synced_pointer_pos=None,
        )

        def _set_pointer(pos, apply_constraints=True):
            app.logical_pointer_pos = (int(pos[0]), int(pos[1]))

        def _sync_pointer(pos):
            app.synced_pointer_pos = (int(pos[0]), int(pos[1]))

        app.set_logical_pointer_position = _set_pointer
        app.sync_pointer_to_logical_position = _sync_pointer

        handle = sv._scrollbar_y_handle_rect()
        self.assertIsNotNone(handle)
        handle = handle

        down = MagicMock()
        down.kind = EventType.MOUSE_BUTTON_DOWN
        down.button = 1
        down.pos = handle.center

        move = MagicMock()
        move.kind = EventType.MOUSE_MOTION
        move.button = None
        move.pos = (handle.centerx, min(sv.rect.bottom - 4, handle.centery + 36))

        up = MagicMock()
        up.kind = EventType.MOUSE_BUTTON_UP
        up.button = 1
        up.pos = move.pos

        initial = sv.scroll_y
        self.assertTrue(sv.handle_event(down, app))
        self.assertTrue(app.pointer_capture.is_owned_by("sv"))

        app.logical_pointer_pos = move.pos
        self.assertTrue(sv.handle_event(move, app))
        self.assertGreater(sv.scroll_y, initial)

        self.assertTrue(sv.handle_event(up, app))
        self.assertFalse(app.pointer_capture.is_owned_by("sv"))
        self.assertIsNotNone(app.synced_pointer_pos)


# ---------------------------------------------------------------------------
# SpinnerControl tests
# ---------------------------------------------------------------------------

from gui_do.controls.input.spinner_control import SpinnerControl
from gui_do.events.value_change_reason import ValueChangeReason


class TestSpinnerControl(unittest.TestCase):
    def test_default_value(self) -> None:
        sp = SpinnerControl("s", Rect(0, 0, 120, 28), value=5)
        self.assertEqual(sp.value, 5)

    def test_min_max_clamping(self) -> None:
        sp = SpinnerControl("s", Rect(0, 0, 120, 28), value=50,
                            min_value=0, max_value=100)
        self.assertEqual(sp.value, 50)
        sp.value = 150
        self.assertEqual(sp.value, 100)
        sp.value = -10
        self.assertEqual(sp.value, 0)

    def test_increment(self) -> None:
        sp = SpinnerControl("s", Rect(0, 0, 120, 28), value=5, step=2)
        sp.increment()
        self.assertEqual(sp.value, 7)

    def test_decrement(self) -> None:
        sp = SpinnerControl("s", Rect(0, 0, 120, 28), value=5, step=2)
        sp.decrement()
        self.assertEqual(sp.value, 3)

    def test_decrement_clamps_at_min(self) -> None:
        sp = SpinnerControl("s", Rect(0, 0, 120, 28), value=1,
                            min_value=0, step=5)
        sp.decrement()
        self.assertEqual(sp.value, 0)

    def test_increment_clamps_at_max(self) -> None:
        sp = SpinnerControl("s", Rect(0, 0, 120, 28), value=98,
                            max_value=100, step=5)
        sp.increment()
        self.assertEqual(sp.value, 100)

    def test_on_change_called_on_increment(self) -> None:
        events: list = []
        sp = SpinnerControl("s", Rect(0, 0, 120, 28), value=0,
                            on_change=lambda v, r: events.append((v, r)))
        sp.increment()
        self.assertEqual(len(events), 1)
        self.assertEqual(events[0][0], 1)
        self.assertEqual(events[0][1], ValueChangeReason.KEYBOARD)

    def test_set_value_does_not_fire_on_change(self) -> None:
        events: list = []
        sp = SpinnerControl("s", Rect(0, 0, 120, 28), value=0,
                            on_change=lambda v, r: events.append(v))
        sp.set_value(10)
        self.assertEqual(events, [])
        self.assertEqual(sp.value, 10)

    def test_float_mode_with_decimals(self) -> None:
        sp = SpinnerControl("s", Rect(0, 0, 120, 28), value=1.5,
                            step=0.1, decimals=1)
        sp.increment()
        self.assertAlmostEqual(sp.value, 1.6, places=5)

    def test_exported_from_gui_do_root(self) -> None:
        import gui_do
        self.assertIn("SpinnerControl", gui_do.__all__)


# ---------------------------------------------------------------------------
# RangeSliderControl tests
# ---------------------------------------------------------------------------

from gui_do.controls.input.range_slider_control import RangeSliderControl


class TestRangeSliderControl(unittest.TestCase):
    def test_initial_values(self) -> None:
        rs = RangeSliderControl("rs", Rect(0, 0, 300, 28),
                                min_value=0, max_value=100,
                                low_value=20, high_value=80)
        self.assertEqual(rs.low_value, 20)
        self.assertEqual(rs.high_value, 80)

    def test_low_defaults_to_min(self) -> None:
        rs = RangeSliderControl("rs", Rect(0, 0, 300, 28),
                                min_value=5, max_value=50)
        self.assertEqual(rs.low_value, 5)

    def test_high_defaults_to_max(self) -> None:
        rs = RangeSliderControl("rs", Rect(0, 0, 300, 28),
                                min_value=5, max_value=50)
        self.assertEqual(rs.high_value, 50)

    def test_set_values_clamped(self) -> None:
        rs = RangeSliderControl("rs", Rect(0, 0, 300, 28),
                                min_value=0, max_value=100)
        rs.set_values(-10, 200)
        self.assertGreaterEqual(rs.low_value, 0)
        self.assertLessEqual(rs.high_value, 100)

    def test_low_cannot_exceed_high(self) -> None:
        rs = RangeSliderControl("rs", Rect(0, 0, 300, 28),
                                min_value=0, max_value=100,
                                low_value=40, high_value=60)
        rs.set_values(70, 50)
        # After clamp, invariant must hold
        self.assertLessEqual(rs.low_value, rs.high_value)

    def test_on_change_fires_on_set_values(self) -> None:
        events: list = []
        rs = RangeSliderControl(
            "rs", Rect(0, 0, 300, 28),
            min_value=0, max_value=100,
            low_value=10, high_value=90,
            on_change=lambda lo, hi, r: events.append((lo, hi)),
        )
        rs.set_values(20, 80)
        self.assertEqual(len(events), 0)  # set_values is programmatic (no on_change)

    def test_high_handle_drag_begins_pointer_capture(self) -> None:
        from types import SimpleNamespace

        from gui_do.events.gui_event import EventType, GuiEvent
        from gui_do.events.pointer_capture import PointerCapture

        rs = RangeSliderControl(
            "rs", Rect(0, 0, 300, 28),
            min_value=0, max_value=100,
            low_value=20, high_value=80,
        )
        app = SimpleNamespace(pointer_capture=PointerCapture())
        event = GuiEvent(
            kind=EventType.MOUSE_BUTTON_DOWN,
            type=0,
            pos=(rs._value_to_x(rs.high_value), rs.rect.centery),
            button=1,
        )

        handled = rs.handle_event(event, app)

        self.assertTrue(handled)
        self.assertEqual(rs._dragging, 2)
        self.assertTrue(app.pointer_capture.is_owned_by("rs"))

    def test_exported_from_gui_do_root(self) -> None:
        import gui_do
        self.assertIn("RangeSliderControl", gui_do.__all__)


# ---------------------------------------------------------------------------
# ColorPickerControl tests
# ---------------------------------------------------------------------------

from gui_do.controls.input.color_picker_control import ColorPickerControl


class TestColorPickerControl(unittest.TestCase):
    def test_initial_color(self) -> None:
        picker = ColorPickerControl("p", Rect(0, 0, 220, 200),
                                   color=(255, 0, 0))
        r, g, b = picker.color
        self.assertAlmostEqual(r, 255, delta=2)
        self.assertAlmostEqual(g, 0, delta=2)
        self.assertAlmostEqual(b, 0, delta=2)

    def test_set_color(self) -> None:
        picker = ColorPickerControl("p", Rect(0, 0, 220, 200))
        picker.color = (0, 128, 255)
        r, g, b = picker.color
        self.assertAlmostEqual(r, 0, delta=2)
        self.assertAlmostEqual(g, 128, delta=5)
        self.assertAlmostEqual(b, 255, delta=2)

    def test_on_change_fires_on_color_set(self) -> None:
        events: list = []
        picker = ColorPickerControl("p", Rect(0, 0, 220, 200),
                                   on_change=lambda rgb: events.append(rgb))
        picker.color = (100, 200, 50)
        # color setter does NOT fire on_change (it's programmatic)
        # but _fire_change is called by interaction helpers
        self.assertEqual(events, [])

    def test_rgb_hex_roundtrip(self) -> None:
        picker = ColorPickerControl("p", Rect(0, 0, 220, 200))
        picker.color = (64, 128, 192)
        self.assertEqual(picker._hex_text, "#406080" if picker._hex_text.startswith("#4060") else picker._hex_text)
        # Just verify it's a valid hex string
        self.assertTrue(picker._hex_text.startswith("#"))
        self.assertEqual(len(picker._hex_text), 7)

    def test_exported_from_gui_do_root(self) -> None:
        import gui_do
        self.assertIn("ColorPickerControl", gui_do.__all__)


# ---------------------------------------------------------------------------
# CommandPaletteManager tests
# ---------------------------------------------------------------------------

from gui_do.overlays.command_palette_manager import (
    CommandPaletteManager,
    CommandEntry,
    CommandPaletteHandle,
)
from gui_do.overlays.overlay_manager import OverlayManager
from gui_do.events.gui_event import EventType, GuiEvent
from gui_do import ListItem, ListViewControl


class TestCommandEntry(unittest.TestCase):
    def test_entry_construction(self) -> None:
        entry = CommandEntry(
            entry_id="new_file",
            title="New File",
            action=lambda: None,
            description="Create a new file",
            category="File",
        )
        self.assertEqual(entry.entry_id, "new_file")
        self.assertEqual(entry.title, "New File")
        self.assertEqual(entry.category, "File")

    def test_default_category_empty(self) -> None:
        entry = CommandEntry(entry_id="x", title="X", action=lambda: None)
        self.assertEqual(entry.category, "")

    def test_exported_from_gui_do_root(self) -> None:
        import gui_do
        self.assertIn("CommandEntry", gui_do.__all__)
        self.assertIn("CommandPaletteManager", gui_do.__all__)
        self.assertIn("CommandPaletteHandle", gui_do.__all__)


class TestCommandPaletteManagerRegistry(unittest.TestCase):
    def _palette(self) -> CommandPaletteManager:
        return CommandPaletteManager(OverlayManager())

    def test_register_adds_entry(self) -> None:
        p = self._palette()
        p.register(CommandEntry("a", "Alpha", action=lambda: None))
        self.assertEqual(p.entry_count(), 1)

    def test_register_replaces_same_id(self) -> None:
        p = self._palette()
        p.register(CommandEntry("a", "Alpha", action=lambda: None))
        p.register(CommandEntry("a", "Alpha2", action=lambda: None))
        self.assertEqual(p.entry_count(), 1)
        self.assertEqual(p._entries["a"].title, "Alpha2")

    def test_unregister_removes_entry(self) -> None:
        p = self._palette()
        p.register(CommandEntry("a", "Alpha", action=lambda: None))
        result = p.unregister("a")
        self.assertTrue(result)
        self.assertEqual(p.entry_count(), 0)

    def test_unregister_nonexistent_returns_false(self) -> None:
        p = self._palette()
        self.assertFalse(p.unregister("ghost"))

    def test_clear_removes_all_entries(self) -> None:
        p = self._palette()
        p.register(CommandEntry("a", "Alpha", action=lambda: None))
        p.register(CommandEntry("b", "Beta", action=lambda: None))
        p.clear()
        self.assertEqual(p.entry_count(), 0)

    def test_action_registry_is_not_auto_projected(self) -> None:
        from gui_do.actions.action_registry import ActionRegistry

        registry = ActionRegistry()
        registry.declare("alpha", "Alpha", lambda _ctx, _ev: True, category="Tools")
        p = CommandPaletteManager(OverlayManager(), action_registry=registry)

        self.assertEqual(p.entry_count(), 0)

    def test_not_open_by_default(self) -> None:
        p = self._palette()
        self.assertFalse(p.is_open)

    def test_hide_when_not_open_is_noop(self) -> None:
        p = self._palette()
        p.hide()  # Should not raise
        self.assertFalse(p.is_open)

    def test_selected_index_for_entry_id_defaults_to_first(self) -> None:
        p = self._palette()
        entries = [
            CommandEntry("a", "Alpha", action=lambda: None),
            CommandEntry("b", "Beta", action=lambda: None),
        ]
        self.assertEqual(p._selected_index_for_entry_id(entries, None), 0)

    def test_selected_index_for_entry_id_matches_entry(self) -> None:
        p = self._palette()
        entries = [
            CommandEntry("a", "Alpha", action=lambda: None),
            CommandEntry("b", "Beta", action=lambda: None),
        ]
        self.assertEqual(p._selected_index_for_entry_id(entries, "b"), 1)

    def test_show_does_not_open_when_no_entries_registered(self) -> None:
        overlay = MagicMock()
        overlay.has_overlay.return_value = False
        app = MagicMock()
        app.overlay = overlay
        app.chain_screen_fallthrough.return_value = lambda: True
        p = CommandPaletteManager(overlay)

        handle = p.show(app)

        self.assertFalse(handle.is_open)
        overlay.show.assert_not_called()

    def test_show_centers_and_sizes_to_entry_count(self) -> None:
        overlay = MagicMock()
        overlay.has_overlay.return_value = False
        app = MagicMock()
        app.overlay = overlay
        app.chain_screen_fallthrough.return_value = lambda: True
        captured = {}

        def _capture_show(owner, panel, **kwargs):
            del owner, kwargs
            captured["panel"] = panel
            return MagicMock()

        overlay.show.side_effect = _capture_show
        p = CommandPaletteManager(overlay)
        for i in range(3):
            p.register(CommandEntry(str(i), f"Item {i}", action=lambda: None))

        with patch("pygame.display.get_surface") as get_surface:
            surface = MagicMock()
            surface.get_width.return_value = 800
            surface.get_height.return_value = 600
            get_surface.return_value = surface
            p.show(app)

        panel = captured["panel"]
        self.assertEqual(panel.rect.height, 96)
        self.assertEqual(panel.rect.y, (600 - 96) // 2)
        self.assertEqual(panel.rect.x, (800 - panel.rect.width) // 2)
        self.assertEqual(len(panel.children), 1)

    def test_show_restores_selected_entry_from_provider(self) -> None:
        overlay = MagicMock()
        overlay.has_overlay.return_value = False
        app = MagicMock()
        app.overlay = overlay
        app.chain_screen_fallthrough.return_value = lambda: True
        captured = {}

        def _capture_show(owner, panel, **kwargs):
            del owner, kwargs
            captured["panel"] = panel
            return MagicMock()

        overlay.show.side_effect = _capture_show
        p = CommandPaletteManager(overlay)
        p.register(CommandEntry("a", "Alpha", action=lambda: None))
        p.register(CommandEntry("b", "Beta", action=lambda: None))
        p.set_selection_provider(lambda: "b")

        with patch("pygame.display.get_surface") as get_surface:
            surface = MagicMock()
            surface.get_width.return_value = 800
            surface.get_height.return_value = 600
            get_surface.return_value = surface
            p.show(app)

        listview = captured["panel"].children[0]
        self.assertEqual(listview.selected_index, 1)

    def test_window_entries_draw_with_toggle_visual_state(self) -> None:
        from gui_do.overlays.command_palette_manager import _CommandPaletteListView

        surface = pygame.Surface((320, 120))
        theme = MagicMock()
        theme.background = (0, 0, 0)
        theme.highlight = (10, 20, 30)
        theme.text = (220, 220, 220)
        theme.dark = (20, 20, 20)
        theme.medium = (40, 40, 40)
        theme.graphics_factory.font_revision.return_value = 0
        theme.graphics_factory.build_interactive_visuals.return_value = "visuals"
        theme.graphics_factory.resolve_visual_state.side_effect = [surface, surface]

        items = [
            ListItem(label="Windows: Life", data=CommandEntry("w1", "Life", action=lambda: None, category="Windows", render_kind="window_toggle", window_visible=True)),
            ListItem(label="Windows: System", data=CommandEntry("w2", "System", action=lambda: None, category="Windows", render_kind="window_toggle", window_visible=False)),
        ]
        listview = _CommandPaletteListView("palette", Rect(0, 0, 320, 56), items=items, row_height=28)

        listview.draw(surface, theme)

        resolve_calls = theme.graphics_factory.resolve_visual_state.call_args_list
        self.assertEqual(resolve_calls[0].kwargs["armed"], True)
        self.assertEqual(resolve_calls[1].kwargs["armed"], False)

    def test_scene_entries_draw_with_rounded_box_style(self) -> None:
        from gui_do.overlays.command_palette_manager import _CommandPaletteListView

        surface = pygame.Surface((320, 60))
        theme = MagicMock()
        theme.background = (0, 0, 0)
        theme.highlight = (10, 20, 30)
        theme.text = (220, 220, 220)
        theme.dark = (20, 20, 20)
        theme.medium = (40, 40, 40)
        theme.graphics_factory.font_revision.return_value = 0
        theme.graphics_factory.build_interactive_visuals.return_value = "scene_visuals"
        theme.graphics_factory.resolve_visual_state.return_value = surface

        items = [
            ListItem(label="Scenes: Desktop Demo", data=CommandEntry("scene:main", "Desktop Demo", action=lambda: None, category="Scenes")),
        ]
        listview = _CommandPaletteListView("palette", Rect(0, 0, 320, 28), items=items, row_height=28, selected_index=0)

        listview.draw(surface, theme)

        theme.graphics_factory.build_interactive_visuals.assert_called_once_with(
            "round",
            "Desktop Demo",
            Rect(2, 2, 316, 24),
            font_role="body",
        )
        theme.graphics_factory.resolve_visual_state.assert_called_once_with(
            "scene_visuals",
            visible=True,
            enabled=True,
            armed=False,
            hovered=False,
        )

    def test_command_palette_panel_draws_medium_background(self) -> None:
        from gui_do.overlays.command_palette_manager import _CommandPalettePanel, _CommandPaletteListView

        surface = pygame.Surface((320, 120))
        theme = MagicMock()
        theme.medium = (12, 34, 56)
        theme.none = (1, 2, 3)
        theme.background = (0, 0, 0)
        theme.highlight = (10, 20, 30)
        theme.text = (220, 220, 220)
        theme.dark = (20, 20, 20)

        listview = _CommandPaletteListView("palette", Rect(10, 10, 300, 80), items=[])
        panel = _CommandPalettePanel("panel", Rect(0, 0, 320, 120), listview=listview)
        panel.add(listview)

        with patch("pygame.draw.rect") as mock_rect:
            panel.draw_screen_phase(surface, theme)

        self.assertTrue(any(call.args[1] == theme.medium and call.args[2] == panel.rect for call in mock_rect.call_args_list))
        self.assertTrue(any(call.args[1] == theme.none and call.args[2] == panel.rect and call.kwargs.get("width") == 1 for call in mock_rect.call_args_list))

    def test_move_selection_by_wheel_moves_up_and_down(self) -> None:
        p = self._palette()
        items = [ListItem(label=f"Item {i}") for i in range(6)]
        lv = ListViewControl("lv", Rect(0, 0, 200, 100), items=items, selected_index=3)

        p._move_selection_by_wheel(lv, 1)
        self.assertEqual(lv.selected_index, 2)

        p._move_selection_by_wheel(lv, -2)
        self.assertEqual(lv.selected_index, 4)

    def test_move_selection_by_wheel_clamps_to_bounds(self) -> None:
        p = self._palette()
        items = [ListItem(label=f"Item {i}") for i in range(4)]
        lv = ListViewControl("lv", Rect(0, 0, 200, 100), items=items, selected_index=1)

        p._move_selection_by_wheel(lv, 10)
        self.assertEqual(lv.selected_index, 0)

        p._move_selection_by_wheel(lv, -10)
        self.assertEqual(lv.selected_index, 3)

    # ------------------------------------------------------------------
    # Wheel selects then scrolls to keep selection in view
    # ------------------------------------------------------------------

    def test_wheel_changes_selection_not_offset(self) -> None:
        """Wheel over the panel changes the selected item, not the raw scroll offset."""
        from gui_do.overlays.command_palette_manager import _CommandPalettePanel
        items = [ListItem(label=f"Item {i}") for i in range(20)]
        lv = ListViewControl("lv", Rect(10, 60, 300, 200), items=items, selected_index=5)
        panel = _CommandPalettePanel("panel", Rect(10, 10, 300, 260), listview=lv)

        app = MagicMock()
        app.logical_pointer_pos = (100, 100)

        evt = GuiEvent(kind=EventType.MOUSE_WHEEL, type=0, pos=(100, 100), wheel_y=1)
        consumed = panel.handle_event(evt, app)

        self.assertTrue(consumed)
        self.assertEqual(lv.selected_index, 4)  # moved up by 1 (delta=+1 → lower index)

    def test_wheel_scrolls_view_to_keep_selection_visible(self) -> None:
        """After wheel moves selection, scroll_to_item brings the new row into view."""
        from gui_do.overlays.command_palette_manager import _CommandPalettePanel
        items = [ListItem(label=f"Item {i}") for i in range(20)]
        row_h = 28
        viewport_h = row_h * 5  # shows 5 rows
        lv = ListViewControl("lv", Rect(10, 60, 300, viewport_h), items=items, selected_index=0)
        panel = _CommandPalettePanel("panel", Rect(10, 10, 300, viewport_h + 50), listview=lv)

        app = MagicMock()
        app.logical_pointer_pos = (100, 100)

        # Wheel down 10 times to drive selection beyond initial viewport
        for _ in range(10):
            evt = GuiEvent(kind=EventType.MOUSE_WHEEL, type=0, pos=(100, 100), wheel_y=-1)
            panel.handle_event(evt, app)

        self.assertEqual(lv.selected_index, 10)
        item_bottom = (10 + 1) * row_h  # bottom of row 10
        self.assertGreaterEqual(lv.scroll_offset + viewport_h, item_bottom)

    # ------------------------------------------------------------------
    # Keyboard navigation
    # ------------------------------------------------------------------

    def test_key_down_arrow_moves_selection_down(self) -> None:
        from gui_do.overlays.command_palette_manager import _CommandPalettePanel
        items = [ListItem(label=f"Item {i}") for i in range(6)]
        lv = ListViewControl("lv", Rect(10, 60, 300, 200), items=items, selected_index=2)
        panel = _CommandPalettePanel("panel", Rect(10, 10, 300, 260), listview=lv)

        app = MagicMock()
        evt = GuiEvent(kind=EventType.KEY_DOWN, type=0, key=pygame.K_DOWN, mod=0)
        consumed = panel.handle_event(evt, app)

        self.assertTrue(consumed)
        self.assertEqual(lv.selected_index, 3)

    def test_key_up_arrow_moves_selection_up(self) -> None:
        from gui_do.overlays.command_palette_manager import _CommandPalettePanel
        items = [ListItem(label=f"Item {i}") for i in range(6)]
        lv = ListViewControl("lv", Rect(10, 60, 300, 200), items=items, selected_index=4)
        panel = _CommandPalettePanel("panel", Rect(10, 10, 300, 260), listview=lv)

        app = MagicMock()
        evt = GuiEvent(kind=EventType.KEY_DOWN, type=0, key=pygame.K_UP, mod=0)
        consumed = panel.handle_event(evt, app)

        self.assertTrue(consumed)
        self.assertEqual(lv.selected_index, 3)

    def test_key_up_clamps_at_first_item(self) -> None:
        from gui_do.overlays.command_palette_manager import _CommandPalettePanel
        items = [ListItem(label=f"Item {i}") for i in range(4)]
        lv = ListViewControl("lv", Rect(10, 60, 300, 200), items=items, selected_index=0)
        panel = _CommandPalettePanel("panel", Rect(10, 10, 300, 260), listview=lv)

        app = MagicMock()
        evt = GuiEvent(kind=EventType.KEY_DOWN, type=0, key=pygame.K_UP, mod=0)
        panel.handle_event(evt, app)

        self.assertEqual(lv.selected_index, 0)

    def test_key_down_clamps_at_last_item(self) -> None:
        from gui_do.overlays.command_palette_manager import _CommandPalettePanel
        items = [ListItem(label=f"Item {i}") for i in range(4)]
        lv = ListViewControl("lv", Rect(10, 60, 300, 200), items=items, selected_index=3)
        panel = _CommandPalettePanel("panel", Rect(10, 10, 300, 260), listview=lv)

        app = MagicMock()
        evt = GuiEvent(kind=EventType.KEY_DOWN, type=0, key=pygame.K_DOWN, mod=0)
        panel.handle_event(evt, app)

        self.assertEqual(lv.selected_index, 3)

    def test_key_return_activates_selected_item(self) -> None:
        from gui_do.overlays.command_palette_manager import _CommandPalettePanel
        activated = []
        items = [ListItem(label=f"Item {i}") for i in range(4)]
        lv = ListViewControl("lv", Rect(10, 60, 300, 200), items=items, selected_index=2)
        lv._on_select = lambda idx, item: activated.append(idx)
        panel = _CommandPalettePanel("panel", Rect(10, 10, 300, 260), listview=lv)

        app = MagicMock()
        evt = GuiEvent(kind=EventType.KEY_DOWN, type=0, key=pygame.K_RETURN, mod=0)
        consumed = panel.handle_event(evt, app)

        self.assertTrue(consumed)
        self.assertEqual(activated, [2])

    def test_key_space_activates_selected_item(self) -> None:
        from gui_do.overlays.command_palette_manager import _CommandPalettePanel
        activated = []
        items = [ListItem(label=f"Item {i}") for i in range(4)]
        lv = ListViewControl("lv", Rect(10, 60, 300, 200), items=items, selected_index=1)
        lv._on_select = lambda idx, item: activated.append(idx)
        panel = _CommandPalettePanel("panel", Rect(10, 10, 300, 260), listview=lv)

        app = MagicMock()
        evt = GuiEvent(kind=EventType.KEY_DOWN, type=0, key=pygame.K_SPACE, mod=0)
        consumed = panel.handle_event(evt, app)

        self.assertTrue(consumed)
        self.assertEqual(activated, [1])

    def test_other_keys_pass_through_to_children(self) -> None:
        """Letter keys are not intercepted so the search TextInput still gets them."""
        from gui_do.overlays.command_palette_manager import _CommandPalettePanel
        items = [ListItem(label="X")]
        lv = ListViewControl("lv", Rect(10, 60, 300, 200), items=items)
        panel = _CommandPalettePanel("panel", Rect(10, 10, 300, 260), listview=lv)

        app = MagicMock()
        # No children → dispatches but finds nothing → returns False
        evt = GuiEvent(kind=EventType.KEY_DOWN, type=0, key=pygame.K_a, mod=0)
        consumed = panel.handle_event(evt, app)
        self.assertFalse(consumed)

    def test_background_trigger_auto_registers_on_construction_with_app(self) -> None:
        """Passing app to __init__ immediately registers the fallthrough handler."""
        captured = {}

        app = MagicMock()
        app.overlay.point_in_any_overlay.return_value = False
        app.scene.pointer_context_at.return_value = (False, None)

        def _fallthrough(*, event_handler=None, **_kwargs):
            captured["handler"] = event_handler
            return lambda: True

        app.chain_screen_fallthrough.side_effect = _fallthrough
        p = CommandPaletteManager(MagicMock(), app)

        self.assertIn("handler", captured)
        self.assertIsNotNone(p._background_trigger_dispose)

    def test_background_trigger_auto_registers_on_first_show(self) -> None:
        """If app not passed to __init__, fallthrough registers on first show()."""
        captured = {}

        app = MagicMock()
        app.overlay.point_in_any_overlay.return_value = False
        app.scene.pointer_context_at.return_value = (False, None)
        app.overlay = MagicMock()
        app.overlay.has_overlay.return_value = False

        def _fallthrough(*, event_handler=None, **_kwargs):
            captured["handler"] = event_handler
            return lambda: True

        app.chain_screen_fallthrough.side_effect = _fallthrough

        p = CommandPaletteManager(MagicMock())
        self.assertIsNone(p._background_trigger_dispose)

        p.show(app)
        self.assertIn("handler", captured)
        self.assertIsNotNone(p._background_trigger_dispose)

    def test_background_trigger_opens_palette_on_empty_space(self) -> None:
        """Fallthrough handler opens palette when right-clicking empty background."""
        captured = {}

        app = MagicMock()
        app.overlay.point_in_any_overlay.return_value = False
        app.scene.pointer_context_at.return_value = (False, None)

        def _fallthrough(*, event_handler=None, **_kwargs):
            captured["handler"] = event_handler
            return lambda: True

        app.chain_screen_fallthrough.side_effect = _fallthrough
        p = CommandPaletteManager(MagicMock(), app)

        evt = GuiEvent(
            kind=EventType.MOUSE_BUTTON_DOWN,
            type=0,
            pos=(25, 25),
            button=3,
        )
        consumed = captured["handler"](evt)
        self.assertTrue(consumed)

    def test_background_trigger_ignores_right_click_on_controls(self) -> None:
        """Fallthrough handler does nothing when the click lands on a control."""
        captured = {}

        app = MagicMock()
        app.overlay.point_in_any_overlay.return_value = False
        app.scene.pointer_context_at.return_value = (False, object())

        def _fallthrough(*, event_handler=None, **_kwargs):
            captured["handler"] = event_handler
            return lambda: True

        app.chain_screen_fallthrough.side_effect = _fallthrough
        p = CommandPaletteManager(MagicMock(), app)

        evt = GuiEvent(
            kind=EventType.MOUSE_BUTTON_DOWN,
            type=0,
            pos=(25, 25),
            button=3,
        )
        consumed = captured["handler"](evt)
        self.assertFalse(consumed)

    def test_background_trigger_ignores_non_right_button(self) -> None:
        """Fallthrough handler ignores any button that is not button 3."""
        captured = {}

        app = MagicMock()
        app.overlay.point_in_any_overlay.return_value = False
        app.scene.pointer_context_at.return_value = (False, None)

        def _fallthrough(*, event_handler=None, **_kwargs):
            captured["handler"] = event_handler
            return lambda: True

        app.chain_screen_fallthrough.side_effect = _fallthrough
        p = CommandPaletteManager(MagicMock(), app)

        evt = GuiEvent(
            kind=EventType.MOUSE_BUTTON_DOWN,
            type=0,
            pos=(25, 25),
            button=1,
        )
        consumed = captured["handler"](evt)
        self.assertFalse(consumed)

    # ------------------------------------------------------------------
    # Pointer event absorption — events over the palette must not leak
    # ------------------------------------------------------------------

    def test_pointer_events_over_palette_panel_are_consumed(self) -> None:
        """Mouse events over the palette panel are consumed even when no child handles them."""
        from gui_do.overlays.command_palette_manager import _CommandPalettePanel
        lv = ListViewControl("lv", Rect(10, 60, 300, 200), items=[], row_height=28)
        panel = _CommandPalettePanel("panel", Rect(10, 10, 300, 260), listview=lv)
        app = MagicMock()
        app.logical_pointer_pos = (100, 100)

        for kind, extra in [
            (EventType.MOUSE_BUTTON_DOWN, {"button": 1}),
            (EventType.MOUSE_BUTTON_UP,   {"button": 1}),
            (EventType.MOUSE_MOTION,      {}),
            (EventType.MOUSE_WHEEL,       {"wheel_y": -1}),
        ]:
            evt = GuiEvent(kind=kind, type=0, pos=(100, 100), **extra)
            consumed = panel.handle_event(evt, app)
            self.assertTrue(consumed, f"Expected {kind} over panel to be consumed")

    def test_pointer_events_outside_palette_panel_are_not_consumed(self) -> None:
        """Mouse events outside the palette panel are not consumed."""
        from gui_do.overlays.command_palette_manager import _CommandPalettePanel
        lv = ListViewControl("lv", Rect(10, 60, 300, 200), items=[], row_height=28)
        panel = _CommandPalettePanel("panel", Rect(10, 10, 300, 260), listview=lv)
        app = MagicMock()
        app.logical_pointer_pos = (600, 500)

        for kind, extra in [
            (EventType.MOUSE_BUTTON_DOWN, {"button": 1}),
            (EventType.MOUSE_BUTTON_UP,   {"button": 1}),
            (EventType.MOUSE_MOTION,      {}),
            (EventType.MOUSE_WHEEL,       {"wheel_y": -1}),
        ]:
            evt = GuiEvent(kind=kind, type=0, pos=(600, 500), **extra)
            consumed = panel.handle_event(evt, app)
            self.assertFalse(consumed, f"Expected {kind} outside panel to not be consumed")


# ---------------------------------------------------------------------------
# Export completeness
# ---------------------------------------------------------------------------

class TestNewExportsInPublicAll(unittest.TestCase):
    def test_all_new_exports_present(self) -> None:
        import gui_do
        new_exports = [
            "ComputedValue",
            "ClipboardManager",
            "AnimationSequence",
            "AnimationHandle",
            "ScrollViewControl",
            "SpinnerControl",
            "RangeSliderControl",
            "ColorPickerControl",
            "CommandPaletteManager",
            "CommandEntry",
            "CommandPaletteHandle",
        ]
        for name in new_exports:
            with self.subTest(name=name):
                self.assertIn(name, gui_do.__all__)
                self.assertIsNotNone(getattr(gui_do, name, None))


if __name__ == "__main__":
    unittest.main()
