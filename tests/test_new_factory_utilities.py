"""Tests for the new factory utilities added in the factory-expansion pass.

Covers:
- ControlRegistry (feature_lifecycle)
- make_labeled_slot_height_fn (feature_lifecycle)
- LayoutManager.column_flow_anchors_for (layout_manager)
- bind_task_panel_focus_toggle (data_driven_runtime)
"""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock, call

import pygame
from pygame import Rect

pygame.init()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _dummy_control(name: str = "ctrl"):
    ctrl = MagicMock()
    ctrl.set_rect = MagicMock()
    ctrl.set_accessibility = MagicMock()
    ctrl.set_tab_index = MagicMock()
    ctrl.enabled = True
    return ctrl


def _make_container():
    container = MagicMock()
    container.add = MagicMock(side_effect=lambda x: x)
    return container


def _make_placement_spec(name: str = "test", *, focusable: bool = True, labeled: bool = True):
    from gui_do.features.feature_lifecycle import ControlPlacementSpec
    ctrl = _dummy_control(name)
    return ControlPlacementSpec(
        name=name,
        control=ctrl,
        control_rect=Rect(0, 0, 100, 40),
        focusable=focusable,
        labeled=labeled,
        label_text=f"{name}_label" if labeled else "",
    )


# ===========================================================================
# ControlRegistry
# ===========================================================================

class TestControlRegistry(unittest.TestCase):

    def test_exported_from_gui_do(self):
        import gui_do
        self.assertTrue(hasattr(gui_do, "ControlRegistry"))

    def test_initial_lists_empty(self):
        from gui_do import ControlRegistry
        container = _make_container()
        reg = ControlRegistry(container)
        self.assertEqual(reg.controls, [])
        self.assertEqual(reg.control_labels, [])
        self.assertEqual(reg.placed_controls, [])

    def test_add_label_adds_to_container_and_tracks(self):
        from gui_do import ControlRegistry
        container = _make_container()
        reg = ControlRegistry(container)
        label = MagicMock()
        reg.add_label(label)
        container.add.assert_called_with(label)
        self.assertIn(label, reg.control_labels)
        self.assertEqual(reg.controls, [])

    def test_add_control_adds_to_container_and_tracks(self):
        from gui_do import ControlRegistry
        container = _make_container()
        reg = ControlRegistry(container)
        ctrl = MagicMock()
        reg.add_control(ctrl)
        container.add.assert_called_with(ctrl)
        self.assertIn(ctrl, reg.controls)
        self.assertEqual(reg.control_labels, [])

    def test_register_places_specs_and_populates_tracking_lists(self):
        from gui_do import ControlRegistry
        container = _make_container()
        reg = ControlRegistry(container)
        spec = _make_placement_spec("alpha", labeled=True)
        reg.register([spec])
        # placed_controls should have an entry for this spec
        self.assertEqual(len(reg.placed_controls), 1)
        self.assertEqual(reg.placed_controls[0].name, "alpha")
        # The control was added to the container
        added_controls = [c for (c,), _ in container.add.call_args_list]
        self.assertIn(spec.control, added_controls)

    def test_register_labeled_spec_tracks_label_in_control_labels(self):
        from gui_do import ControlRegistry
        container = _make_container()
        reg = ControlRegistry(container)
        spec = _make_placement_spec("beta", labeled=True, focusable=True)
        reg.register([spec])
        # A label control should have been added and tracked
        self.assertEqual(len(reg.control_labels), 1)

    def test_register_unlabeled_spec_no_label_created(self):
        from gui_do import ControlRegistry
        container = _make_container()
        reg = ControlRegistry(container)
        spec = _make_placement_spec("gamma", labeled=False)
        reg.register([spec])
        self.assertEqual(reg.control_labels, [])

    def test_multiple_registers_accumulate(self):
        from gui_do import ControlRegistry
        container = _make_container()
        reg = ControlRegistry(container)
        reg.register([_make_placement_spec("a")])
        reg.register([_make_placement_spec("b")])
        reg.add_label(MagicMock())
        reg.add_control(MagicMock())
        self.assertEqual(len(reg.placed_controls), 2)
        # 2 placed controls from register() + 1 from add_control()
        self.assertEqual(len(reg.controls), 3)
        # control_labels: 2 from labeled specs + 1 from add_label
        self.assertEqual(len(reg.control_labels), 3)

    def test_controls_property_returns_list(self):
        from gui_do import ControlRegistry
        container = _make_container()
        reg = ControlRegistry(container)
        self.assertIsInstance(reg.controls, list)

    def test_control_labels_property_returns_list(self):
        from gui_do import ControlRegistry
        container = _make_container()
        reg = ControlRegistry(container)
        self.assertIsInstance(reg.control_labels, list)

    def test_placed_controls_property_returns_list(self):
        from gui_do import ControlRegistry
        container = _make_container()
        reg = ControlRegistry(container)
        self.assertIsInstance(reg.placed_controls, list)


# ===========================================================================
# make_labeled_slot_height_fn
# ===========================================================================

class TestMakeLabeledSlotHeightFn(unittest.TestCase):

    def test_exported_from_gui_do(self):
        import gui_do
        self.assertTrue(hasattr(gui_do, "make_labeled_slot_height_fn"))

    def test_returns_callable(self):
        from gui_do import make_labeled_slot_height_fn
        fn = make_labeled_slot_height_fn(18, 4)
        self.assertTrue(callable(fn))

    def test_matches_cell_caret_layout_labeled_slot_height(self):
        from gui_do import make_labeled_slot_height_fn
        from gui_do.layout.cell_caret_layout import CellCaretLayout
        label_h, label_gap = 18, 4
        fn = make_labeled_slot_height_fn(label_h, label_gap)
        for control_h in (28, 34, 48, 90, 120):
            expected = CellCaretLayout.labeled_slot_height(control_h, label_height=label_h, label_gap=label_gap)
            self.assertEqual(fn(control_h), expected, f"Mismatch for control_h={control_h}")

    def test_captures_parameters_independently(self):
        from gui_do import make_labeled_slot_height_fn
        from gui_do.layout.cell_caret_layout import CellCaretLayout
        fn_a = make_labeled_slot_height_fn(18, 4)
        fn_b = make_labeled_slot_height_fn(20, 8)
        h = 40
        self.assertEqual(fn_a(h), CellCaretLayout.labeled_slot_height(h, label_height=18, label_gap=4))
        self.assertEqual(fn_b(h), CellCaretLayout.labeled_slot_height(h, label_height=20, label_gap=8))
        self.assertNotEqual(fn_a(h), fn_b(h))

    def test_integer_coercion(self):
        from gui_do import make_labeled_slot_height_fn
        fn = make_labeled_slot_height_fn(18, 4)
        # Should not raise with float-ish input
        result = fn(34)
        self.assertIsInstance(result, int)


# ===========================================================================
# LayoutManager.column_flow_anchors_for
# ===========================================================================

class TestColumnFlowAnchorsFor(unittest.TestCase):

    def test_classmethod_accessible(self):
        from gui_do.layout.layout_manager import LayoutManager
        self.assertTrue(hasattr(LayoutManager, "column_flow_anchors_for"))
        self.assertTrue(callable(LayoutManager.column_flow_anchors_for))

    def test_returns_tuple_of_rects(self):
        from gui_do.layout.layout_manager import LayoutManager
        bounds = Rect(0, 0, 800, 400)
        anchors = LayoutManager.column_flow_anchors_for(
            bounds, 4, overall_rows=4, overall_columns=1
        )
        self.assertIsInstance(anchors, tuple)
        self.assertEqual(len(anchors), 4)
        for r in anchors:
            self.assertIsInstance(r, Rect)

    def test_matches_equivalent_instance_call(self):
        from gui_do.layout.layout_manager import LayoutManager
        bounds = Rect(10, 20, 600, 300)
        count = 6
        kwargs = dict(overall_rows=6, overall_columns=2, column_spacing=8, row_spacing=8)

        # via classmethod
        anchors_cls = LayoutManager.column_flow_anchors_for(bounds, count, **kwargs)

        # via instance
        mgr = LayoutManager()
        mgr.set_column_flow_properties(bounds=bounds, **kwargs)
        anchors_inst = mgr.column_flow_anchors(count)

        self.assertEqual(anchors_cls, anchors_inst)

    def test_column_span_respected(self):
        from gui_do.layout.layout_manager import LayoutManager
        bounds = Rect(0, 0, 400, 200)
        anchors = LayoutManager.column_flow_anchors_for(
            bounds, 2, overall_rows=4, overall_columns=1, column_span=2
        )
        self.assertEqual(len(anchors), 2)
        # Each anchor should span 2 columns, so should be wider than a single-span anchor
        single = LayoutManager.column_flow_anchors_for(
            bounds, 2, overall_rows=4, overall_columns=1, column_span=1
        )
        self.assertGreater(anchors[0].width, single[0].width)

    def test_zero_count_returns_empty_tuple(self):
        from gui_do.layout.layout_manager import LayoutManager
        bounds = Rect(0, 0, 400, 200)
        anchors = LayoutManager.column_flow_anchors_for(
            bounds, 0, overall_rows=4, overall_columns=1
        )
        self.assertEqual(anchors, ())


# ===========================================================================
# bind_task_panel_focus_toggle
# ===========================================================================

class TestBindTaskPanelFocusToggle(unittest.TestCase):

    def test_exported_from_gui_do(self):
        import gui_do
        self.assertTrue(hasattr(gui_do, "bind_task_panel_focus_toggle"))

    def test_registers_action_and_binds_key(self):
        from gui_do import bind_task_panel_focus_toggle
        app_actions = MagicMock()
        app = MagicMock()
        bind_task_panel_focus_toggle(
            app_actions,
            app,
            action_name="my_toggle",
            scene_name="my_scene",
            key=1,  # dummy key code
        )
        app_actions.register_action.assert_called_once()
        name_arg = app_actions.register_action.call_args[0][0]
        self.assertEqual(name_arg, "my_toggle")

        app_actions.bind_key.assert_called_once_with(1, "my_toggle", scene="my_scene")

    def test_toggle_returns_true_when_palette_open(self):
        from gui_do import bind_task_panel_focus_toggle
        app_actions = MagicMock()
        overlay = MagicMock()
        overlay.has_overlay.return_value = True
        app = MagicMock()
        app.overlay = overlay
        bind_task_panel_focus_toggle(
            app_actions, app,
            action_name="t", scene_name="s", key=0,
        )
        handler = app_actions.register_action.call_args[0][1]
        result = handler(None)
        overlay.has_overlay.assert_called_with("__command_palette__")
        self.assertTrue(result)

    def test_toggle_delegates_to_task_panel_focus(self):
        from gui_do import bind_task_panel_focus_toggle
        app_actions = MagicMock()
        overlay = MagicMock()
        overlay.has_overlay.return_value = False
        task_panel_focus = MagicMock()
        task_panel_focus.toggle.return_value = True
        app = MagicMock()
        app.overlay = overlay
        app.task_panel_focus = task_panel_focus
        bind_task_panel_focus_toggle(
            app_actions, app,
            action_name="t", scene_name="s", key=0,
        )
        handler = app_actions.register_action.call_args[0][1]
        result = handler(None)
        task_panel_focus.toggle.assert_called_once_with(app.scene, app)
        self.assertTrue(result)

    def test_toggle_returns_false_when_no_task_panel_focus(self):
        from gui_do import bind_task_panel_focus_toggle
        app_actions = MagicMock()
        overlay = MagicMock()
        overlay.has_overlay.return_value = False
        app = MagicMock()
        app.overlay = overlay
        app.task_panel_focus = None
        bind_task_panel_focus_toggle(
            app_actions, app,
            action_name="t", scene_name="s", key=0,
        )
        handler = app_actions.register_action.call_args[0][1]
        result = handler(None)
        self.assertFalse(result)


if __name__ == "__main__":
    unittest.main()
