"""Tests for the new factory utilities added in the factory-expansion pass.

Covers:
- ControlRegistry (feature_lifecycle)
- make_labeled_slot_height_fn (feature_lifecycle)
- LayoutManager.column_flow_anchors_for (layout_manager)
- bind_task_panel_focus_toggle (data_driven_runtime)
"""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock

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

        app_actions.bind_global_key.assert_called_once_with(1, "my_toggle", scene="my_scene")

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


# ===========================================================================
# ActionHotkeySpec + register_action_hotkeys
# ===========================================================================

class TestRegisterActionHotkeys(unittest.TestCase):

    def test_action_hotkey_spec_exported_from_gui_do(self):
        import gui_do
        self.assertTrue(hasattr(gui_do, "ActionHotkeySpec"))

    def test_register_action_hotkeys_exported_from_gui_do(self):
        import gui_do
        self.assertTrue(hasattr(gui_do, "register_action_hotkeys"))

    def test_registers_action_without_key_binding(self):
        from gui_do import ActionHotkeySpec, register_action_hotkeys
        app_actions = MagicMock()
        handler = MagicMock()
        specs = (ActionHotkeySpec(action_name="a", handler=handler),)
        register_action_hotkeys(app_actions, specs)
        app_actions.register_action.assert_called_once_with("a", handler)
        app_actions.bind_key.assert_not_called()

    def test_registers_action_and_scene_key_binding(self):
        from gui_do import ActionHotkeySpec, register_action_hotkeys
        app_actions = MagicMock()
        handler = MagicMock()
        specs = (ActionHotkeySpec(action_name="a", handler=handler, key=99, scene_name="main"),)
        register_action_hotkeys(app_actions, specs)
        app_actions.register_action.assert_called_once_with("a", handler)
        app_actions.bind_key.assert_called_once_with(99, "a", scene="main")

    def test_registers_action_and_global_key_binding(self):
        from gui_do import ActionHotkeySpec, register_action_hotkeys
        app_actions = MagicMock()
        handler = MagicMock()
        specs = (ActionHotkeySpec(action_name="a", handler=handler, key=42, scene_name=None),)
        register_action_hotkeys(app_actions, specs)
        app_actions.bind_key.assert_called_once_with(42, "a")


# ===========================================================================
# draw_controls_prewarm
# ===========================================================================

class TestDrawControlsPrewarm(unittest.TestCase):

    def test_exported_from_gui_do(self):
        import gui_do
        self.assertTrue(hasattr(gui_do, "draw_controls_prewarm"))

    def test_draws_all_non_none_controls(self):
        from gui_do import draw_controls_prewarm
        surface = MagicMock()
        theme = MagicMock()
        c1 = MagicMock()
        c2 = MagicMock()
        draw_controls_prewarm(surface, theme, (c1, None, c2))
        c1.draw.assert_called_once_with(surface, theme)
        c2.draw.assert_called_once_with(surface, theme)

    def test_skips_objects_without_draw_method(self):
        from gui_do import draw_controls_prewarm
        surface = MagicMock()
        theme = MagicMock()
        nodraw = object()
        c1 = MagicMock()
        draw_controls_prewarm(surface, theme, (nodraw, c1))
        c1.draw.assert_called_once_with(surface, theme)


# ===========================================================================
# SceneTaskPanelSpec + task-panel scene-nav button helpers
# ===========================================================================

class TestSceneTaskPanelHelpers(unittest.TestCase):

    def test_scene_task_panel_spec_and_scene_nav_button_spec_exported(self):
        import gui_do
        self.assertTrue(hasattr(gui_do, "SceneTaskPanelSpec"))
        self.assertTrue(hasattr(gui_do, "TaskPanelLinearLayoutSpec"))
        self.assertTrue(hasattr(gui_do, "TaskPanelSceneNavButtonSpec"))

    def test_ensure_scene_task_panel_exported(self):
        import gui_do
        self.assertTrue(hasattr(gui_do, "ensure_scene_task_panel"))

    def test_add_scene_nav_button_helpers_exported(self):
        import gui_do
        self.assertTrue(hasattr(gui_do, "create_task_panel_linear_layout"))
        self.assertTrue(hasattr(gui_do, "add_task_panel_scene_nav_button"))
        self.assertTrue(hasattr(gui_do, "add_scene_task_panel_items"))

    def test_ensure_scene_task_panel_delegates_to_scene_presentation(self):
        from gui_do import SceneTaskPanelSpec, ensure_scene_task_panel
        host = MagicMock()
        panel = MagicMock()
        host.scene_presentation.ensure_scene_task_panel.return_value = panel
        spec = SceneTaskPanelSpec(
            scene_name="control_showcase",
            control_id="task_panel",
            height=44,
            hidden_peek_pixels=5,
            animation_step_px=7,
            dock_bottom=False,
            auto_hide=False,
        )
        result = ensure_scene_task_panel(host, spec)
        self.assertIs(result, panel)
        host.scene_presentation.ensure_scene_task_panel.assert_called_once_with(
            "control_showcase",
            control_id="task_panel",
            height=44,
            hidden_peek_pixels=5,
            animation_step_px=7,
            dock_bottom=False,
            auto_hide=False,
        )

    def test_add_task_panel_scene_nav_button_uses_go_to_attr_when_available(self):
        from gui_do import TaskPanelSceneNavButtonSpec, add_task_panel_scene_nav_button
        task_panel = MagicMock()
        button = MagicMock()
        task_panel.add.return_value = button
        app_layout = MagicMock()
        app_layout.linear.return_value = Rect(10, 108, 120, 24)
        host = MagicMock()
        host.go_to_main = MagicMock()
        spec = TaskPanelSceneNavButtonSpec(
            attr_name="scene_back",
            control_id="ret",
            slot_index=3,
            label="Return",
            target_scene="main",
            go_to_attr="go_to_main",
            style="angle",
            accessibility_role="button",
            accessibility_label="Return to main",
            tab_index=-1,
        )
        created = add_task_panel_scene_nav_button(task_panel, app_layout, host, spec)
        self.assertIs(created, button)
        task_panel.add.assert_called_once()
        self.assertIs(host.scene_back, button)
        button.set_accessibility.assert_called_once_with(role="button", label="Return to main")
        button.set_tab_index.assert_called_once_with(-1)

    def test_add_task_panel_scene_nav_button_falls_back_to_scene_transitions(self):
        from gui_do import TaskPanelSceneNavButtonSpec, add_task_panel_scene_nav_button
        task_panel = MagicMock()
        button = MagicMock()
        task_panel.add.return_value = button
        app_layout = MagicMock()
        app_layout.linear.return_value = Rect(0, 0, 110, 30)
        host = MagicMock()
        host.go_to_main = None
        host.scene_transitions = MagicMock()
        spec = TaskPanelSceneNavButtonSpec(target_scene="main", go_to_attr="go_to_main")
        add_task_panel_scene_nav_button(task_panel, app_layout, host, spec)
        on_click = task_panel.add.call_args[0][0].on_click
        on_click()
        host.scene_transitions.go.assert_called_once_with("main")


# ===========================================================================
# Overlay helpers and feature event subscription lifecycle helpers
# ===========================================================================

class TestOverlayHelpers(unittest.TestCase):

    def test_overlay_helpers_exported_from_gui_do(self):
        import gui_do
        self.assertTrue(hasattr(gui_do, "centered_overlay_rect"))
        self.assertTrue(hasattr(gui_do, "create_shortcut_help_overlay"))

    def test_centered_overlay_rect_computes_centered_rect(self):
        from gui_do import centered_overlay_rect
        surface = MagicMock()
        surface.get_width.return_value = 1000
        surface.get_height.return_value = 700
        rect = centered_overlay_rect(surface, width=600, height=440)
        self.assertEqual(rect, Rect(200, 130, 600, 440))

    def test_centered_overlay_rect_applies_offsets(self):
        from gui_do import centered_overlay_rect
        surface = MagicMock()
        surface.get_width.return_value = 1000
        surface.get_height.return_value = 700
        rect = centered_overlay_rect(surface, width=600, height=440, offset_x=10, offset_y=-5)
        self.assertEqual(rect, Rect(210, 125, 600, 440))

    def test_create_shortcut_help_overlay_uses_centered_overlay_rect(self):
        from gui_do import create_shortcut_help_overlay
        app = MagicMock()
        app.surface.get_width.return_value = 1000
        app.surface.get_height.return_value = 700
        app.overlay = MagicMock()
        action_registry = MagicMock()

        with unittest.mock.patch(
            "gui_do.features.data_driven_runtime.ShortcutHelpOverlay",
            create=True,
        ) as overlay_cls:
            # The helper imports ShortcutHelpOverlay inside the function from
            # gui_do.overlays.shortcut_help_overlay; patch the resolved target.
            with unittest.mock.patch(
                "gui_do.overlays.shortcut_help_overlay.ShortcutHelpOverlay",
                overlay_cls,
            ):
                create_shortcut_help_overlay(
                    app,
                    action_registry=action_registry,
                    width=560,
                    height=400,
                )

        overlay_cls.assert_called_once()
        kwargs = overlay_cls.call_args.kwargs
        self.assertEqual(kwargs["action_registry"], action_registry)
        self.assertEqual(kwargs["overlay_rect"], Rect(220, 150, 560, 400))


class TestFeatureEventSubscriptionHelpers(unittest.TestCase):

    def test_event_subscription_spec_and_helpers_exported_from_gui_do(self):
        import gui_do
        self.assertTrue(hasattr(gui_do, "EventSubscriptionSpec"))
        self.assertTrue(hasattr(gui_do, "bind_feature_event_subscription"))
        self.assertTrue(hasattr(gui_do, "unbind_feature_event_subscription"))

    def test_bind_feature_event_subscription_sets_attr_and_returns_token(self):
        from gui_do import EventSubscriptionSpec, bind_feature_event_subscription
        feature = MagicMock()
        app_events = MagicMock()
        token = object()
        app_events.subscribe.return_value = token
        handler = MagicMock()
        spec = EventSubscriptionSpec(
            attr_name="status_subscription",
            topic="status",
            handler=handler,
            scope="scope",
        )
        result = bind_feature_event_subscription(feature, app_events, spec)
        self.assertIs(result, token)
        app_events.subscribe.assert_called_once_with("status", handler, scope="scope")
        self.assertIs(getattr(feature, "status_subscription"), token)

    def test_unbind_feature_event_subscription_unsubscribes_and_clears_attr(self):
        from gui_do import unbind_feature_event_subscription
        feature = MagicMock()
        token = object()
        setattr(feature, "status_subscription", token)
        app_events = MagicMock()
        result = unbind_feature_event_subscription(feature, app_events, attr_name="status_subscription")
        self.assertTrue(result)
        app_events.unsubscribe.assert_called_once_with(token)
        self.assertIsNone(getattr(feature, "status_subscription"))

    def test_unbind_feature_event_subscription_noop_when_missing(self):
        from gui_do import unbind_feature_event_subscription
        feature = MagicMock()
        setattr(feature, "status_subscription", None)
        app_events = MagicMock()
        result = unbind_feature_event_subscription(feature, app_events, attr_name="status_subscription")
        self.assertFalse(result)
        app_events.unsubscribe.assert_not_called()

    def test_bind_feature_event_subscription_graceful_without_app_events(self):
        from gui_do import EventSubscriptionSpec, bind_feature_event_subscription
        feature = MagicMock()
        spec = EventSubscriptionSpec(attr_name="sub", topic="t", handler=MagicMock())
        result = bind_feature_event_subscription(feature, None, spec)
        self.assertIsNone(result)
        self.assertIsNone(getattr(feature, "sub"))

    def test_unbind_feature_event_subscription_clears_attr_without_app_events(self):
        from gui_do import unbind_feature_event_subscription
        feature = MagicMock()
        token = object()
        setattr(feature, "sub", token)
        result = unbind_feature_event_subscription(feature, None, attr_name="sub")
        self.assertFalse(result)
        self.assertIsNone(getattr(feature, "sub"))


# ===========================================================================
# Tabbed presenter setup helpers
# ===========================================================================

class TestTabbedPresenterSetupHelpers(unittest.TestCase):

    def test_tabbed_presenter_spec_and_setup_helper_exported(self):
        import gui_do
        self.assertTrue(hasattr(gui_do, "TabbedPresenterSpec"))
        self.assertTrue(hasattr(gui_do, "setup_feature_presenter_tabs_from_window_content"))

    def test_setup_helper_composes_compute_and_setup_calls(self):
        from gui_do import TabbedPresenterSpec, setup_feature_presenter_tabs_from_window_content

        presenter = MagicMock()
        window = MagicMock()
        window.content_rect.return_value = Rect(10, 20, 500, 300)
        spec = TabbedPresenterSpec(
            control_id="tab_ctrl",
            selected_key="one",
            tab_height=34,
            tab_rows=2,
            padding=2,
            min_content_height=60,
        )
        tab_specs = [MagicMock()]
        on_change = MagicMock()
        tab_manager = MagicMock()
        feature = MagicMock()
        host = MagicMock()

        fake_tab_rect = Rect(12, 22, 496, 280)
        fake_content_rect = Rect(12, 90, 496, 210)
        fake_tab_control = MagicMock()

        with unittest.mock.patch(
            "gui_do.features.data_driven_runtime.compute_tabbed_window_layout",
            return_value=(fake_tab_rect, fake_content_rect),
        ) as compute_mock, unittest.mock.patch(
            "gui_do.features.data_driven_runtime.setup_feature_presenter_tabs",
            return_value=fake_tab_control,
        ) as setup_mock:
            result = setup_feature_presenter_tabs_from_window_content(
                presenter,
                window=window,
                spec=spec,
                tab_specs=tab_specs,
                on_change=on_change,
                tab_manager=tab_manager,
                feature=feature,
                host=host,
                on_activate_callbacks=(("locale", MagicMock()),),
            )

        self.assertIs(result, fake_tab_control)
        compute_mock.assert_called_once_with(
            window.content_rect.return_value,
            tab_height=34,
            tab_rows=2,
            padding=2,
            min_content_height=60,
        )
        setup_mock.assert_called_once_with(
            presenter,
            control_id="tab_ctrl",
            tab_rect=fake_tab_rect,
            tab_specs=tab_specs,
            selected_key="one",
            on_change=on_change,
            tab_manager=tab_manager,
            feature=feature,
            host=host,
            tab_content_rect=fake_content_rect,
        )
        tab_manager.on_activate.assert_called_once()


# ===========================================================================
# Routed runtime contract helpers
# ===========================================================================

class TestRoutedRuntimeHelpers(unittest.TestCase):

    def test_routed_runtime_spec_and_helpers_exported(self):
        import gui_do
        self.assertTrue(hasattr(gui_do, "RoutedRuntimeSpec"))
        self.assertTrue(hasattr(gui_do, "RoutedFeatureLifecycleSpec"))
        self.assertTrue(hasattr(gui_do, "ShortcutOverlaySpec"))
        self.assertTrue(hasattr(gui_do, "TaskPanelFocusToggleSpec"))
        self.assertTrue(hasattr(gui_do, "setup_routed_runtime"))
        self.assertTrue(hasattr(gui_do, "shutdown_routed_runtime"))
        self.assertTrue(hasattr(gui_do, "register_routed_feature_companions"))
        self.assertTrue(hasattr(gui_do, "bind_routed_feature_lifecycle"))
        self.assertTrue(hasattr(gui_do, "shutdown_routed_feature_lifecycle"))

    def test_task_panel_focus_toggle_spec_fields(self):
        from gui_do import TaskPanelFocusToggleSpec
        spec = TaskPanelFocusToggleSpec(action_name="toggle_tp", scene_name="main", key=282)
        self.assertEqual(spec.action_name, "toggle_tp")
        self.assertEqual(spec.scene_name, "main")
        self.assertEqual(spec.key, 282)

    def test_shortcut_overlay_spec_toggle_fields_default_none(self):
        from gui_do import ShortcutOverlaySpec
        spec = ShortcutOverlaySpec(attr_name="_overlay")
        self.assertIsNone(spec.toggle_action_name)
        self.assertIsNone(spec.toggle_key)
        self.assertIsNone(spec.toggle_scene_name)

    def test_shortcut_overlay_spec_toggle_fields_set(self):
        from gui_do import ShortcutOverlaySpec
        spec = ShortcutOverlaySpec(
            attr_name="_overlay",
            toggle_action_name="show_help",
            toggle_key=280,
            toggle_scene_name="main",
        )
        self.assertEqual(spec.toggle_action_name, "show_help")
        self.assertEqual(spec.toggle_key, 280)
        self.assertEqual(spec.toggle_scene_name, "main")

    def test_RoutedRuntimeSpec_task_panel_focus_toggles_defaults_empty(self):
        from gui_do import RoutedRuntimeSpec
        spec = RoutedRuntimeSpec()
        self.assertEqual(len(spec.task_panel_focus_toggles), 0)

    def test_setup_routed_runtime_registers_overlay_toggle_action_and_key(self):
        from gui_do import RoutedRuntimeSpec, ShortcutOverlaySpec, setup_routed_runtime

        feature = MagicMock()
        host = MagicMock()
        overlay_mock = MagicMock()
        runtime_spec = RoutedRuntimeSpec(
            shortcut_overlays=(
                ShortcutOverlaySpec(
                    attr_name="_help_overlay",
                    toggle_action_name="show_help",
                    toggle_key=280,
                    toggle_scene_name="main",
                ),
            ),
        )

        with unittest.mock.patch(
            "gui_do.features.data_driven_runtime.setup_routed_feature_runtime",
            return_value=object(),
        ), unittest.mock.patch(
            "gui_do.features.data_driven_runtime.create_shortcut_help_overlay",
            return_value=overlay_mock,
        ):
            setup_routed_runtime(feature, host, runtime_spec)

        host.app.actions.register_action.assert_called_with("show_help", unittest.mock.ANY)
        host.app.actions.bind_key.assert_called_with(280, "show_help", scene="main")

    def test_setup_routed_runtime_registers_task_panel_focus_toggles(self):
        from gui_do import RoutedRuntimeSpec, TaskPanelFocusToggleSpec, setup_routed_runtime

        feature = MagicMock()
        host = MagicMock()
        host.app.task_panel_focus = MagicMock()
        runtime_spec = RoutedRuntimeSpec(
            task_panel_focus_toggles=(
                TaskPanelFocusToggleSpec(action_name="toggle_tp", scene_name="main", key=282),
            ),
        )

        with unittest.mock.patch(
            "gui_do.features.data_driven_runtime.setup_routed_feature_runtime",
            return_value=object(),
        ), unittest.mock.patch(
            "gui_do.features.data_driven_runtime.bind_task_panel_focus_toggle",
        ) as bind_mock:
            setup_routed_runtime(feature, host, runtime_spec)

        bind_mock.assert_called_once_with(
            host.app.actions,
            host.app,
            action_name="toggle_tp",
            scene_name="main",
            key=282,
        )

    def test_setup_routed_runtime_skips_task_panel_toggles_when_app_missing(self):
        from gui_do import RoutedRuntimeSpec, TaskPanelFocusToggleSpec, setup_routed_runtime

        feature = MagicMock()
        host = MagicMock()
        host.app = None
        runtime_spec = RoutedRuntimeSpec(
            task_panel_focus_toggles=(
                TaskPanelFocusToggleSpec(action_name="toggle_tp", scene_name="main", key=282),
            ),
        )

        with unittest.mock.patch(
            "gui_do.features.data_driven_runtime.setup_routed_feature_runtime",
            return_value=object(),
        ), unittest.mock.patch(
            "gui_do.features.data_driven_runtime.bind_task_panel_focus_toggle",
        ) as bind_mock:
            setup_routed_runtime(feature, host, runtime_spec)

        bind_mock.assert_not_called()

    def test_setup_routed_runtime_composes_all_declared_wiring(self):
        from gui_do import (
            ActionHotkeySpec,
            EventSubscriptionSpec,
            LogicBindingSpec,
            RoutedRuntimeSpec,
            ShortcutOverlaySpec,
            setup_routed_runtime,
        )

        feature = MagicMock()
        host = MagicMock()
        scheduler = object()
        hotkey = ActionHotkeySpec(action_name="show_help", handler=MagicMock(), key=1, scene_name="main")
        event_spec = EventSubscriptionSpec(attr_name="status_subscription", topic="status", handler=MagicMock(), scope="demo")
        overlay_spec = ShortcutOverlaySpec(attr_name="_shortcut_overlay", action_registry_attr="action_registry", width=500, height=320)
        runtime_spec = RoutedRuntimeSpec(
            scene_name="main",
            scheduler_attr_name="scheduler",
            scheduler_dispatch_limit=128,
            logic_bindings=(LogicBindingSpec(alias="life", provider_name="life_logic"),),
            action_hotkeys=(hotkey,),
            event_subscriptions=(event_spec,),
            shortcut_overlays=(overlay_spec,),
        )

        with unittest.mock.patch(
            "gui_do.features.data_driven_runtime.setup_routed_feature_runtime",
            return_value=scheduler,
        ) as setup_runtime_mock, unittest.mock.patch(
            "gui_do.features.data_driven_runtime.register_action_hotkeys",
        ) as register_hotkeys_mock, unittest.mock.patch(
            "gui_do.features.data_driven_runtime.bind_feature_event_subscription",
        ) as bind_event_mock, unittest.mock.patch(
            "gui_do.features.data_driven_runtime.create_shortcut_help_overlay",
            return_value=MagicMock(),
        ) as create_overlay_mock:
            result = setup_routed_runtime(feature, host, runtime_spec)

        self.assertIs(result, scheduler)
        setup_runtime_mock.assert_called_once_with(
            feature,
            host,
            scene_name="main",
            scheduler_attr_name="scheduler",
            scheduler_dispatch_limit=128,
            logic_bindings=runtime_spec.logic_bindings,
        )
        register_hotkeys_mock.assert_called_once_with(host.app.actions, runtime_spec.action_hotkeys)
        bind_event_mock.assert_called_once_with(feature, host.app.events, event_spec)
        create_overlay_mock.assert_called_once()
        self.assertTrue(hasattr(feature, "_shortcut_overlay"))

    def test_shutdown_routed_runtime_unbinds_declared_event_subscriptions(self):
        from gui_do import EventSubscriptionSpec, RoutedRuntimeSpec, shutdown_routed_runtime

        feature = MagicMock()
        host = MagicMock()
        runtime_spec = RoutedRuntimeSpec(
            event_subscriptions=(
                EventSubscriptionSpec(attr_name="status_subscription", topic="status", handler=MagicMock()),
                EventSubscriptionSpec(attr_name="other_subscription", topic="other", handler=MagicMock()),
            )
        )
        with unittest.mock.patch(
            "gui_do.features.data_driven_runtime.unbind_feature_event_subscription",
        ) as unbind_mock:
            shutdown_routed_runtime(feature, host, runtime_spec)

        self.assertEqual(unbind_mock.call_count, 2)
        unbind_mock.assert_any_call(feature, host.app.events, attr_name="status_subscription")
        unbind_mock.assert_any_call(feature, host.app.events, attr_name="other_subscription")

    def test_setup_routed_runtime_skips_optional_wiring_when_app_parts_missing(self):
        from gui_do import ActionHotkeySpec, EventSubscriptionSpec, RoutedRuntimeSpec, ShortcutOverlaySpec, setup_routed_runtime

        feature = MagicMock()
        host = MagicMock()
        host.app = None
        runtime_spec = RoutedRuntimeSpec(
            action_hotkeys=(ActionHotkeySpec(action_name="a", handler=MagicMock(), key=1),),
            event_subscriptions=(EventSubscriptionSpec(attr_name="s", topic="t", handler=MagicMock()),),
            shortcut_overlays=(ShortcutOverlaySpec(attr_name="o"),),
        )

        with unittest.mock.patch(
            "gui_do.features.data_driven_runtime.setup_routed_feature_runtime",
            return_value=object(),
        ) as setup_runtime_mock, unittest.mock.patch(
            "gui_do.features.data_driven_runtime.register_action_hotkeys",
        ) as register_hotkeys_mock, unittest.mock.patch(
            "gui_do.features.data_driven_runtime.bind_feature_event_subscription",
        ) as bind_event_mock, unittest.mock.patch(
            "gui_do.features.data_driven_runtime.create_shortcut_help_overlay",
        ) as create_overlay_mock:
            setup_routed_runtime(feature, host, runtime_spec)

        setup_runtime_mock.assert_called_once()
        register_hotkeys_mock.assert_not_called()
        bind_event_mock.assert_not_called()
        create_overlay_mock.assert_not_called()

    def test_shutdown_routed_runtime_skips_when_events_missing(self):
        from gui_do import EventSubscriptionSpec, RoutedRuntimeSpec, shutdown_routed_runtime

        feature = MagicMock()
        host = MagicMock()
        host.app = MagicMock()
        host.app.events = None
        runtime_spec = RoutedRuntimeSpec(
            event_subscriptions=(
                EventSubscriptionSpec(attr_name="status_subscription", topic="status", handler=MagicMock()),
            )
        )

        with unittest.mock.patch(
            "gui_do.features.data_driven_runtime.unbind_feature_event_subscription",
        ) as unbind_mock:
            shutdown_routed_runtime(feature, host, runtime_spec)

        unbind_mock.assert_not_called()

    def test_register_routed_feature_companions_with_instances_and_factories(self):
        from gui_do import RoutedFeatureLifecycleSpec, register_routed_feature_companions

        feature = MagicMock()
        feature._feature_manager = MagicMock()
        host = MagicMock()

        instance_provider = object()
        factory_provider = object()
        lifecycle_spec = RoutedFeatureLifecycleSpec(
            companion_providers=(
                instance_provider,
                lambda: factory_provider,
            )
        )

        with unittest.mock.patch(
            "gui_do.features.data_driven_runtime.register_companion_logic_features",
        ) as register_mock:
            providers = register_routed_feature_companions(feature, host, lifecycle_spec)

        self.assertEqual(providers, (instance_provider, factory_provider))
        register_mock.assert_called_once_with(
            feature._feature_manager,
            host,
            [instance_provider, factory_provider],
        )

    def test_bind_routed_feature_lifecycle_with_static_spec(self):
        from gui_do import RoutedFeatureLifecycleSpec, RoutedRuntimeSpec, bind_routed_feature_lifecycle

        feature = MagicMock()
        host = MagicMock()
        runtime_spec = RoutedRuntimeSpec(scene_name="main")
        scheduler = object()
        lifecycle_spec = RoutedFeatureLifecycleSpec(
            runtime_spec=runtime_spec,
            runtime_spec_attr_name="_runtime_spec",
            scheduler_attr_name="scheduler",
        )

        with unittest.mock.patch(
            "gui_do.features.data_driven_runtime.setup_routed_runtime",
            return_value=scheduler,
        ) as setup_mock:
            result = bind_routed_feature_lifecycle(feature, host, lifecycle_spec)

        self.assertIs(result, scheduler)
        setup_mock.assert_called_once_with(feature, host, runtime_spec)
        self.assertIs(feature._runtime_spec, runtime_spec)
        self.assertIs(feature.scheduler, scheduler)

    def test_bind_routed_feature_lifecycle_with_factory_spec(self):
        from gui_do import RoutedFeatureLifecycleSpec, RoutedRuntimeSpec, bind_routed_feature_lifecycle

        feature = MagicMock()
        host = MagicMock()
        runtime_spec = RoutedRuntimeSpec(scene_name="main")
        lifecycle_spec = RoutedFeatureLifecycleSpec(
            runtime_spec_factory=lambda _feature, _host: runtime_spec,
            runtime_spec_attr_name="_runtime_spec",
            scheduler_attr_name="scheduler",
        )

        with unittest.mock.patch(
            "gui_do.features.data_driven_runtime.setup_routed_runtime",
            return_value=object(),
        ) as setup_mock:
            bind_routed_feature_lifecycle(feature, host, lifecycle_spec)

        setup_mock.assert_called_once_with(feature, host, runtime_spec)
        self.assertIs(feature._runtime_spec, runtime_spec)

    def test_shutdown_routed_feature_lifecycle_from_stored_runtime_spec(self):
        from gui_do import RoutedFeatureLifecycleSpec, RoutedRuntimeSpec, shutdown_routed_feature_lifecycle

        feature = MagicMock()
        host = MagicMock()
        runtime_spec = RoutedRuntimeSpec(scene_name="main")
        feature._runtime_spec = runtime_spec
        feature.scheduler = object()
        lifecycle_spec = RoutedFeatureLifecycleSpec(
            runtime_spec_attr_name="_runtime_spec",
            scheduler_attr_name="scheduler",
        )

        with unittest.mock.patch(
            "gui_do.features.data_driven_runtime.shutdown_routed_runtime",
        ) as shutdown_mock:
            result = shutdown_routed_feature_lifecycle(feature, host, lifecycle_spec)

        self.assertTrue(result)
        shutdown_mock.assert_called_once_with(feature, host, runtime_spec)
        self.assertIsNone(feature._runtime_spec)
        self.assertIsNone(feature.scheduler)

    def test_shutdown_routed_feature_lifecycle_uses_static_runtime_spec_fallback(self):
        from gui_do import RoutedFeatureLifecycleSpec, RoutedRuntimeSpec, shutdown_routed_feature_lifecycle

        class _Feature:
            _runtime_spec = None

        feature = _Feature()
        host = MagicMock()
        runtime_spec = RoutedRuntimeSpec(scene_name="main")
        lifecycle_spec = RoutedFeatureLifecycleSpec(
            runtime_spec=runtime_spec,
            runtime_spec_attr_name="_runtime_spec",
            scheduler_attr_name=None,
        )

        with unittest.mock.patch(
            "gui_do.features.data_driven_runtime.shutdown_routed_runtime",
        ) as shutdown_mock:
            result = shutdown_routed_feature_lifecycle(feature, host, lifecycle_spec)

        self.assertTrue(result)
        shutdown_mock.assert_called_once_with(feature, host, runtime_spec)

    def test_shutdown_routed_feature_lifecycle_returns_false_without_runtime_spec(self):
        from gui_do import RoutedFeatureLifecycleSpec, shutdown_routed_feature_lifecycle

        class _Feature:
            _runtime_spec = None
            scheduler = None

        feature = _Feature()
        host = MagicMock()
        lifecycle_spec = RoutedFeatureLifecycleSpec(
            runtime_spec_attr_name="_runtime_spec",
            scheduler_attr_name="scheduler",
        )

        with unittest.mock.patch(
            "gui_do.features.data_driven_runtime.shutdown_routed_runtime",
        ) as shutdown_mock:
            result = shutdown_routed_feature_lifecycle(feature, host, lifecycle_spec)

        self.assertFalse(result)
        shutdown_mock.assert_not_called()


class TestRegisterActionHotkeysGeneralCases(unittest.TestCase):

    def test_register_action_hotkeys_graceful_with_none_actions(self):
        from gui_do import ActionHotkeySpec, register_action_hotkeys
        spec = ActionHotkeySpec(action_name="show", handler=MagicMock(), key=1, scene_name="main")
        # Should not raise when actions registry is unavailable.
        register_action_hotkeys(None, (spec,))


# ===========================================================================
# Generic bootstrap collection builders
# ===========================================================================

class TestBootstrapCollectionBuilders(unittest.TestCase):

    def test_builders_exported_from_gui_do(self):
        import gui_do
        self.assertTrue(hasattr(gui_do, "WindowToggleBindingSpec"))
        self.assertTrue(hasattr(gui_do, "SceneSetupBindingSpec"))
        self.assertTrue(hasattr(gui_do, "RuntimeSceneBindingSpec"))
        self.assertTrue(hasattr(gui_do, "SceneRootBindingSpec"))
        self.assertTrue(hasattr(gui_do, "CursorBindingSpec"))
        self.assertTrue(hasattr(gui_do, "FontRoleBindingSpec"))
        self.assertTrue(hasattr(gui_do, "HostApplicationBindingSpec"))
        self.assertTrue(hasattr(gui_do, "SceneBundleBindingSpec"))
        self.assertTrue(hasattr(gui_do, "build_feature_specs"))
        self.assertTrue(hasattr(gui_do, "build_window_toggle_specs"))
        self.assertTrue(hasattr(gui_do, "build_scene_setup_specs"))
        self.assertTrue(hasattr(gui_do, "build_runtime_scene_specs"))
        self.assertTrue(hasattr(gui_do, "build_scene_root_specs"))
        self.assertTrue(hasattr(gui_do, "build_cursor_specs"))
        self.assertTrue(hasattr(gui_do, "build_font_role_specs"))
        self.assertTrue(hasattr(gui_do, "build_scene_nav_actions"))
        self.assertTrue(hasattr(gui_do, "build_scene_bundle_specs"))
        self.assertTrue(hasattr(gui_do, "build_host_application_config"))
        self.assertTrue(hasattr(gui_do, "build_static_accessibility_specs"))

    def test_build_feature_specs_from_tuples_and_passthrough(self):
        from gui_do import FeatureSpec, build_feature_specs
        fn = MagicMock()
        existing = FeatureSpec(attr_name="_existing", factory=fn)
        built = build_feature_specs((("_a", fn), existing))
        self.assertEqual(len(built), 2)
        self.assertEqual(built[0].attr_name, "_a")
        self.assertIs(built[0].factory, fn)
        self.assertIs(built[1], existing)

    def test_build_window_toggle_specs_from_binding_specs_and_passthrough(self):
        from gui_do import WindowSpec, WindowToggleBindingSpec, build_window_toggle_specs

        existing = WindowSpec(
            key="existing",
            feature_attr="_x",
            toggle_attr="toggle_x",
            action_name="win_x",
            action_label="Show X Window",
            task_panel_button_id="show_x",
            task_panel_label="X",
            task_panel_style="round",
            task_panel_slot_index=9,
            accessibility_label="Show X window",
        )
        built = build_window_toggle_specs(
            (
                WindowToggleBindingSpec(
                    key="life",
                    feature_attr="_life",
                    slot_index=2,
                    task_panel_label="Life",
                    task_panel_style="angle",
                ),
                existing,
            )
        )
        self.assertEqual(len(built), 2)
        self.assertEqual(built[0].key, "life")
        self.assertEqual(built[0].feature_attr, "_life")
        self.assertEqual(built[0].task_panel_slot_index, 2)
        self.assertEqual(built[0].task_panel_style, "angle")
        self.assertIs(built[1], existing)

    def test_build_scene_nav_actions_from_tuples_and_passthrough(self):
        from gui_do import ActionSpec, build_scene_nav_actions
        existing = ActionSpec(action_id="exit", label="Exit", kind="exit", target=None, category="File")
        built = build_scene_nav_actions((("nav_main", "Main", "main"), existing), category="Scenes")
        self.assertEqual(len(built), 2)
        self.assertEqual(built[0].action_id, "nav_main")
        self.assertEqual(built[0].label, "Main")
        self.assertEqual(built[0].kind, "scene_nav")
        self.assertEqual(built[0].target, "main")
        self.assertEqual(built[0].category, "Scenes")
        self.assertIs(built[1], existing)

    def test_build_static_accessibility_specs_from_tuples_and_passthrough(self):
        from gui_do import StaticAccessibilitySpec, build_static_accessibility_specs
        existing = StaticAccessibilitySpec(control_attr="b", role="toggle", label="B")
        built = build_static_accessibility_specs((("a", "A"), existing), role="button")
        self.assertEqual(len(built), 2)
        self.assertEqual(built[0].control_attr, "a")
        self.assertEqual(built[0].label, "A")
        self.assertEqual(built[0].role, "button")
        self.assertIs(built[1], existing)

    def test_build_scene_setup_specs_from_bindings_and_tuples(self):
        from gui_do import SceneSetupBindingSpec, SceneTransitionStyle, build_scene_setup_specs

        built = build_scene_setup_specs(
            (
                SceneSetupBindingSpec(
                    name="main",
                    pretty_name="Main",
                    transition_style=SceneTransitionStyle.SLIDE_RIGHT,
                    transition_duration=0.5,
                ),
                ("showcase", "Showcase", SceneTransitionStyle.SLIDE_LEFT, 0.4),
                ("tools", "Tools"),
            ),
            default_transition_style=SceneTransitionStyle.FADE,
            default_transition_duration=0.25,
            initial_scene_name="main",
        )

        self.assertEqual(len(built), 3)
        self.assertEqual(built[0].name, "main")
        self.assertTrue(built[0].make_initial)
        self.assertEqual(built[1].name, "showcase")
        self.assertEqual(built[1].transition_duration, 0.4)
        self.assertEqual(built[2].name, "tools")
        self.assertEqual(built[2].transition_style, SceneTransitionStyle.FADE)
        self.assertEqual(built[2].transition_duration, 0.25)

    def test_build_runtime_scene_specs_from_names_bindings_and_tuples(self):
        from gui_do import RuntimeSceneBindingSpec, build_runtime_scene_specs

        built = build_runtime_scene_specs(
            (
                "main",
                RuntimeSceneBindingSpec("showcase", "asset.png", True, True),
                ("tools", "tools.png", True, False),
            ),
            pristine_asset="default.png",
            bind_escape_to_exit=True,
            prewarm=False,
        )
        self.assertEqual(len(built), 3)
        self.assertEqual(built[0].scene_name, "main")
        self.assertEqual(built[0].pristine_asset, "default.png")
        self.assertTrue(built[0].bind_escape_to_exit)
        self.assertEqual(built[1].scene_name, "showcase")
        self.assertEqual(built[1].pristine_asset, "asset.png")
        self.assertTrue(built[1].prewarm)
        self.assertEqual(built[2].scene_name, "tools")
        self.assertEqual(built[2].pristine_asset, "tools.png")

    def test_build_scene_root_specs_from_bindings_and_tuples(self):
        from gui_do import SceneRootBindingSpec, build_scene_root_specs

        built = build_scene_root_specs(
            (
                SceneRootBindingSpec("main", "main_root", draw_background=True),
                ("showcase", "showcase_root"),
                ("tools", "tools_root", True),
            )
        )
        self.assertEqual(len(built), 3)
        self.assertEqual(built[0].scene_name, "main")
        self.assertTrue(built[0].draw_background)
        self.assertEqual(built[1].control_id, "showcase_root")
        self.assertFalse(built[1].draw_background)
        self.assertEqual(built[2].scene_name, "tools")
        self.assertTrue(built[2].draw_background)

    def test_build_cursor_specs_from_bindings_tuples_and_passthrough(self):
        from gui_do import CursorBindingSpec, CursorSpec, build_cursor_specs

        existing = CursorSpec("existing", "existing.png", (7, 7))
        built = build_cursor_specs(
            (
                CursorBindingSpec("normal", "cursor.png", (1, 1)),
                ("hand", "hand.png", (12, 12)),
                ("ibeam", "ibeam.png"),
                existing,
            ),
            default_hotspot=(0, 0),
        )

        self.assertEqual(len(built), 4)
        self.assertEqual(built[0].name, "normal")
        self.assertEqual(built[0].hotspot, (1, 1))
        self.assertEqual(built[1].name, "hand")
        self.assertEqual(built[1].hotspot, (12, 12))
        self.assertEqual(built[2].name, "ibeam")
        self.assertEqual(built[2].hotspot, (0, 0))
        self.assertIs(built[3], existing)

    def test_build_font_role_specs_from_bindings_tuples_and_passthrough(self):
        from gui_do import FontRoleBindingSpec, build_font_role_specs

        passthrough = {"caption": {"size": 10, "font": "body", "bold": False, "italic": False}}
        built = build_font_role_specs(
            (
                FontRoleBindingSpec("title", 14, "window", bold=True),
                ("body", 12, "default"),
                ("mono", 11, "default", False, True),
                passthrough,
            )
        )

        self.assertEqual(len(built), 2)
        role_map = built[0]
        self.assertIn("title", role_map)
        self.assertEqual(role_map["title"]["size"], 14)
        self.assertTrue(role_map["title"]["bold"])
        self.assertIn("body", role_map)
        self.assertEqual(role_map["body"]["font"], "default")
        self.assertIn("mono", role_map)
        self.assertTrue(role_map["mono"]["italic"])
        self.assertEqual(built[1]["caption"]["size"], 10)

    def test_build_action_specs_from_bindings_and_passthrough(self):
        from gui_do import ActionBindingSpec, ActionSpec, build_action_specs

        passthrough = ActionSpec(
            action_id="custom",
            label="Custom",
            kind="scene_nav",
            target="main",
            category="Scenes",
        )
        built = build_action_specs(
            (
                ActionBindingSpec(kind="exit", action_id="exit", label="Exit", category="File"),
                ActionBindingSpec(kind="scene_nav", action_id="nav_tools", label="Go Tools", target="tools", category="Scenes"),
                ActionBindingSpec(kind="palette_open", action_id="palette_open", label="Open Command Palette (F5)"),
                passthrough,
            )
        )

        self.assertEqual(len(built), 4)
        self.assertEqual(built[0].kind, "exit")
        self.assertEqual(built[1].kind, "scene_nav")
        self.assertEqual(built[1].target, "tools")
        self.assertEqual(built[2].kind, "palette_open")
        self.assertIs(built[3], passthrough)

    def test_build_action_specs_scene_nav_requires_target(self):
        from gui_do import ActionBindingSpec, build_action_specs

        with self.assertRaises(ValueError):
            build_action_specs(
                (
                    ActionBindingSpec(kind="scene_nav", action_id="nav_missing", label="Nav Missing"),
                )
            )

    def test_build_action_specs_rejects_unknown_kind(self):
        from gui_do import ActionBindingSpec, build_action_specs

        with self.assertRaises(ValueError):
            build_action_specs(
                (
                    ActionBindingSpec(kind="unknown", action_id="x", label="X"),
                )
            )

    def test_build_scene_bundle_specs_from_bindings_and_passthrough(self):
        from gui_do import (
            ActionSpec,
            RuntimeSceneSpec,
            SceneBundleBindingSpec,
            SceneRootSpec,
            SceneSetupSpec,
            SceneTransitionStyle,
            build_scene_bundle_specs,
        )

        passthrough_scene = SceneSetupSpec(name="raw", pretty_name="Raw")
        passthrough_runtime = RuntimeSceneSpec(scene_name="raw")
        passthrough_root = SceneRootSpec(scene_name="raw", control_id="raw_root", draw_background=True)
        passthrough_action = ActionSpec(action_id="nav_raw", label="Raw", kind="scene_nav", target="raw", category="Scenes")

        scene_specs, runtime_specs, root_specs, action_specs = build_scene_bundle_specs(
            (
                SceneBundleBindingSpec(
                    scene_name="main",
                    pretty_name="Main",
                    transition_style=SceneTransitionStyle.SLIDE_RIGHT,
                    transition_duration=0.5,
                    include_nav_action=True,
                    nav_action_id="nav_main",
                    nav_label="Go to Main",
                    pristine_asset="main.png",
                    bind_escape_to_exit=True,
                    prewarm=True,
                    include_scene_root=True,
                    scene_root_id="main_root",
                ),
                passthrough_scene,
                passthrough_runtime,
                passthrough_root,
                passthrough_action,
            ),
            initial_scene_name="main",
        )

        self.assertEqual(len(scene_specs), 2)
        self.assertEqual(scene_specs[0].name, "main")
        self.assertTrue(scene_specs[0].make_initial)
        self.assertEqual(scene_specs[0].transition_style, SceneTransitionStyle.SLIDE_RIGHT)
        self.assertIs(scene_specs[1], passthrough_scene)

        self.assertEqual(len(runtime_specs), 2)
        self.assertEqual(runtime_specs[0].scene_name, "main")
        self.assertEqual(runtime_specs[0].pristine_asset, "main.png")
        self.assertTrue(runtime_specs[0].bind_escape_to_exit)
        self.assertTrue(runtime_specs[0].prewarm)
        self.assertIs(runtime_specs[1], passthrough_runtime)

        self.assertEqual(len(root_specs), 2)
        self.assertEqual(root_specs[0].scene_name, "main")
        self.assertEqual(root_specs[0].control_id, "main_root")
        self.assertIs(root_specs[1], passthrough_root)

        self.assertEqual(len(action_specs), 2)
        self.assertEqual(action_specs[0].action_id, "nav_main")
        self.assertEqual(action_specs[0].target, "main")
        self.assertIs(action_specs[1], passthrough_action)

    def test_build_scene_bundle_specs_can_disable_each_output_collection(self):
        from gui_do import SceneBundleBindingSpec, build_scene_bundle_specs

        scene_specs, runtime_specs, root_specs, action_specs = build_scene_bundle_specs(
            (
                SceneBundleBindingSpec(
                    scene_name="tools",
                    include_scene_setup=False,
                    include_runtime_scene=False,
                    include_scene_root=False,
                    include_nav_action=False,
                ),
            )
        )

        self.assertEqual(scene_specs, ())
        self.assertEqual(runtime_specs, ())
        self.assertEqual(root_specs, ())
        self.assertEqual(action_specs, ())

    def test_build_host_application_config_from_binding_spec(self):
        from gui_do import (
            ActionBindingSpec,
            CursorBindingSpec,
            HostApplicationBindingSpec,
            RuntimeSceneBindingSpec,
            SceneSetupBindingSpec,
            SceneTransitionStyle,
            TelemetryConfig,
            WindowToggleBindingSpec,
            build_host_application_config,
        )

        factory = MagicMock()
        config = build_host_application_config(
            HostApplicationBindingSpec(
                display_size=(800, 600),
                window_title="Test App",
                fonts={"default": {"file": "font.ttf", "size": 12}},
                initial_scene_name="main",
                scene_entries=(("main", "Main"),),
                feature_entries=(("_main_feature", factory),),
                window_entries=(
                    WindowToggleBindingSpec("main", "_main_feature", slot_index=1),
                ),
                runtime_scene_entries=(
                    RuntimeSceneBindingSpec("main", "asset.png", True, False),
                ),
                action_entries=(
                    ActionBindingSpec(kind="exit", action_id="exit", label="Exit"),
                ),
                static_accessibility_entries=(("exit_button", "Exit"),),
                font_role_entries=(("title", 14, "default"),),
                cursor_entries=(
                    CursorBindingSpec("normal", "cursor.png", (1, 1)),
                ),
                scene_default_transition_style=SceneTransitionStyle.FADE,
                scene_default_transition_duration=0.25,
                telemetry=TelemetryConfig(enabled=False),
                target_fps=144,
            )
        )

        self.assertEqual(config.display_size, (800, 600))
        self.assertEqual(config.window_title, "Test App")
        self.assertEqual(config.initial_scene_name, "main")
        self.assertEqual(config.target_fps, 144)
        self.assertEqual(len(config.scene_specs), 1)
        self.assertTrue(config.scene_specs[0].make_initial)
        self.assertEqual(config.scene_specs[0].transition_style, SceneTransitionStyle.FADE)
        self.assertEqual(config.scene_specs[0].transition_duration, 0.25)
        self.assertEqual(len(config.feature_specs), 1)
        self.assertEqual(config.feature_specs[0].attr_name, "_main_feature")
        self.assertIs(config.feature_specs[0].factory, factory)
        self.assertEqual(len(config.window_specs), 1)
        self.assertEqual(config.window_specs[0].key, "main")
        self.assertEqual(len(config.runtime_scene_specs), 1)
        self.assertEqual(config.runtime_scene_specs[0].scene_name, "main")
        self.assertTrue(config.runtime_scene_specs[0].bind_escape_to_exit)
        self.assertEqual(len(config.action_specs), 1)
        self.assertEqual(config.action_specs[0].kind, "exit")
        self.assertEqual(len(config.static_accessibility_specs), 1)
        self.assertEqual(config.static_accessibility_specs[0].role, "button")
        self.assertEqual(len(config.cursors), 1)
        self.assertEqual(config.cursors[0].name, "normal")

    def test_build_host_application_config_merges_scene_bundle_entries(self):
        from gui_do import (
            ActionBindingSpec,
            HostApplicationBindingSpec,
            SceneBundleBindingSpec,
            WindowToggleBindingSpec,
            build_host_application_config,
        )

        factory = MagicMock()
        config = build_host_application_config(
            HostApplicationBindingSpec(
                display_size=(800, 600),
                window_title="Bundle App",
                fonts={"default": {"file": "font.ttf", "size": 12}},
                initial_scene_name="main",
                scene_entries=(),
                scene_bundle_entries=(
                    SceneBundleBindingSpec(
                        scene_name="main",
                        pretty_name="Main",
                        include_nav_action=True,
                        pristine_asset="main.png",
                        bind_escape_to_exit=True,
                        prewarm=True,
                        include_scene_root=True,
                        scene_root_id="main_root",
                    ),
                ),
                feature_entries=(("_main_feature", factory),),
                window_entries=(
                    WindowToggleBindingSpec("main", "_main_feature", slot_index=1),
                ),
                runtime_scene_entries=(),
                action_entries=(
                    ActionBindingSpec(kind="exit", action_id="exit", label="Exit"),
                ),
                static_accessibility_entries=(("exit_button", "Exit"),),
            )
        )

        self.assertEqual(len(config.scene_specs), 1)
        self.assertEqual(config.scene_specs[0].name, "main")
        self.assertEqual(len(config.runtime_scene_specs), 1)
        self.assertEqual(config.runtime_scene_specs[0].scene_name, "main")
        self.assertEqual(len(config.scene_roots), 1)
        self.assertEqual(config.scene_roots[0].control_id, "main_root")
        self.assertEqual(len(config.action_specs), 2)
        self.assertEqual(config.action_specs[0].kind, "scene_nav")
        self.assertEqual(config.action_specs[0].target, "main")
        self.assertEqual(config.action_specs[1].kind, "exit")

    def test_build_host_application_config_passthrough(self):
        from gui_do import HostApplicationConfig, TelemetryConfig, build_host_application_config

        existing = HostApplicationConfig(
            display_size=(640, 480),
            window_title="Existing",
            fonts={"default": {"file": "font.ttf", "size": 12}},
            font_role_specs=(),
            cursors=(),
            scene_specs=(),
            feature_specs=(),
            window_specs=(),
            runtime_scene_specs=(),
            action_specs=(),
            static_accessibility_specs=(),
            initial_scene_name="main",
            scene_roots=(),
            telemetry=TelemetryConfig(enabled=False),
            target_fps=60,
        )

        built = build_host_application_config(existing)
        self.assertIs(built, existing)

    def test_build_feature_window_bundle_specs_exported(self):
        import gui_do
        self.assertTrue(hasattr(gui_do, "FeatureWindowBundleBindingSpec"))
        self.assertTrue(hasattr(gui_do, "build_feature_window_bundle_specs"))

    def test_build_feature_window_bundle_specs_from_bindings(self):
        from gui_do import FeatureWindowBundleBindingSpec, build_feature_window_bundle_specs

        factory_a = MagicMock()
        factory_b = MagicMock()
        feature_specs, window_specs = build_feature_window_bundle_specs(
            (
                FeatureWindowBundleBindingSpec(
                    "_life_feature",
                    factory_a,
                    "life",
                    slot_index=3,
                    task_panel_label="Life",
                    task_panel_style="round",
                ),
                FeatureWindowBundleBindingSpec(
                    "_mandel_feature",
                    factory_b,
                    "mandel",
                    slot_index=4,
                    task_panel_label="Mandelbrot",
                    task_panel_style="round",
                ),
            )
        )
        self.assertEqual(len(feature_specs), 2)
        self.assertEqual(feature_specs[0].attr_name, "_life_feature")
        self.assertIs(feature_specs[0].factory, factory_a)
        self.assertEqual(feature_specs[1].attr_name, "_mandel_feature")
        self.assertIs(feature_specs[1].factory, factory_b)

        self.assertEqual(len(window_specs), 2)
        self.assertEqual(window_specs[0].key, "life")
        self.assertEqual(window_specs[0].feature_attr, "_life_feature")
        self.assertEqual(window_specs[0].task_panel_slot_index, 3)
        self.assertEqual(window_specs[0].task_panel_label, "Life")
        self.assertEqual(window_specs[0].task_panel_style, "round")
        self.assertEqual(window_specs[1].task_panel_slot_index, 4)

    def test_build_feature_window_bundle_specs_passthrough(self):
        from gui_do import (
            FeatureSpec,
            FeatureWindowBundleBindingSpec,
            WindowSpec,
            build_feature_window_bundle_specs,
        )

        factory_a = MagicMock()
        factory_b = MagicMock()
        bare_feature = FeatureSpec(attr_name="_extra", factory=factory_b)
        bare_window = WindowSpec(
            key="extra",
            feature_attr="_extra",
            toggle_attr="toggle_extra",
            action_name="win_extra",
            action_label="Show Extra Window",
            task_panel_button_id="show_extra",
            task_panel_label="Extra",
            task_panel_style="angle",
            task_panel_slot_index=9,
            accessibility_label="Show Extra window",
        )
        feature_specs, window_specs = build_feature_window_bundle_specs(
            (
                FeatureWindowBundleBindingSpec("_life", factory_a, "life", slot_index=2),
                bare_feature,
                bare_window,
            )
        )
        self.assertEqual(len(feature_specs), 2)
        self.assertIs(feature_specs[1], bare_feature)
        self.assertEqual(len(window_specs), 2)
        self.assertIs(window_specs[1], bare_window)

    def test_build_feature_window_bundle_specs_applies_window_defaults(self):
        from gui_do import FeatureWindowBundleBindingSpec, build_feature_window_bundle_specs

        factory = MagicMock()
        _, window_specs = build_feature_window_bundle_specs(
            (
                FeatureWindowBundleBindingSpec("_sys", factory, "systems", slot_index=1),
            )
        )
        w = window_specs[0]
        self.assertEqual(w.key, "systems")
        self.assertEqual(w.feature_attr, "_sys")
        self.assertEqual(w.toggle_attr, "systems_toggle_window")
        self.assertEqual(w.action_name, "win_systems")
        self.assertEqual(w.task_panel_button_id, "show_systems")
        self.assertIn("Systems", w.task_panel_label)
        self.assertEqual(w.task_panel_style, "round")

    def test_build_host_application_config_merges_feature_window_bundles(self):
        from gui_do import (
            ActionBindingSpec,
            FeatureWindowBundleBindingSpec,
            HostApplicationBindingSpec,
            build_host_application_config,
        )

        factory_a = MagicMock()
        factory_b = MagicMock()
        factory_plain = MagicMock()
        config = build_host_application_config(
            HostApplicationBindingSpec(
                display_size=(800, 600),
                window_title="Bundle Test",
                fonts={"default": {"file": "font.ttf", "size": 12}},
                initial_scene_name="main",
                scene_entries=(("main", "Main"),),
                feature_entries=(("_plain_feature", factory_plain),),
                window_entries=(),
                feature_window_bundle_entries=(
                    FeatureWindowBundleBindingSpec(
                        "_life_feature",
                        factory_a,
                        "life",
                        slot_index=3,
                        task_panel_label="Life",
                    ),
                    FeatureWindowBundleBindingSpec(
                        "_mandel_feature",
                        factory_b,
                        "mandel",
                        slot_index=4,
                        task_panel_label="Mandelbrot",
                        task_panel_style="angle",
                    ),
                ),
                runtime_scene_entries=(),
                action_entries=(
                    ActionBindingSpec(kind="exit", action_id="exit", label="Exit"),
                ),
                static_accessibility_entries=(),
            )
        )
        # Explicit feature_entries come before bundle features
        self.assertEqual(len(config.feature_specs), 3)
        self.assertEqual(config.feature_specs[0].attr_name, "_plain_feature")
        self.assertEqual(config.feature_specs[1].attr_name, "_life_feature")
        self.assertIs(config.feature_specs[1].factory, factory_a)
        self.assertEqual(config.feature_specs[2].attr_name, "_mandel_feature")
        self.assertIs(config.feature_specs[2].factory, factory_b)
        # Bundle windows
        self.assertEqual(len(config.window_specs), 2)
        self.assertEqual(config.window_specs[0].key, "life")
        self.assertEqual(config.window_specs[0].task_panel_slot_index, 3)
        self.assertEqual(config.window_specs[1].key, "mandel")
        self.assertEqual(config.window_specs[1].task_panel_style, "angle")


if __name__ == "__main__":
    unittest.main()
