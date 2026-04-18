import unittest
from types import SimpleNamespace

from pygame import Rect

from gui_manager_test_factory import build_gui_manager_stub
from gui.utility.constants import GuiError
from gui.utility.guimanager import GuiManager
from gui.utility.widget import Widget


class GuiManagerHelperApiTests(unittest.TestCase):
    def _build_manager_stub(self):
        return build_gui_manager_stub()

    def _build_widget_stub(self, visible=True):
        widget = Widget.__new__(Widget)
        widget._visible = visible
        return widget

    def test_hide_and_show_widgets_toggle_visibility(self) -> None:
        gui = self._build_manager_stub()
        w1 = self._build_widget_stub(True)
        w2 = self._build_widget_stub(False)

        GuiManager.hide_widgets(gui, w1, w2)
        self.assertFalse(w1.visible)
        self.assertFalse(w2.visible)

        GuiManager.show_widgets(gui, w1, w2)
        self.assertTrue(w1.visible)
        self.assertTrue(w2.visible)

    def test_hide_and_show_widgets_reject_non_widget_inputs(self) -> None:
        gui = self._build_manager_stub()
        widget = self._build_widget_stub(True)

        with self.assertRaises(GuiError):
            GuiManager.hide_widgets(gui, widget, object())  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            GuiManager.show_widgets(gui, object())  # type: ignore[arg-type]

    def test_convert_to_screen_and_window_apply_window_offsets(self) -> None:
        gui = self._build_manager_stub()
        window = SimpleNamespace(x=100, y=50)
        gui.windows = [window]

        screen_point = GuiManager.convert_to_screen(gui, (5, 7), window)
        window_point = GuiManager.convert_to_window(gui, (105, 57), window)

        self.assertEqual(screen_point, (105, 57))
        self.assertEqual(window_point, (5, 7))

    def test_convert_helpers_fallback_when_window_unregistered(self) -> None:
        gui = self._build_manager_stub()
        window = SimpleNamespace(x=100, y=50)

        screen_point = GuiManager.convert_to_screen(gui, (5, 7), window)
        window_point = GuiManager.convert_to_window(gui, (105, 57), window)

        self.assertEqual(screen_point, (5, 7))
        self.assertEqual(window_point, (105, 57))

    def test_convert_helpers_validate_point_shape(self) -> None:
        gui = self._build_manager_stub()

        with self.assertRaises(GuiError):
            GuiManager.convert_to_screen(gui, (1,), None)  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            GuiManager.convert_to_window(gui, "bad", None)  # type: ignore[arg-type]

    def test_set_screen_lifecycle_validates_callables(self) -> None:
        gui = self._build_manager_stub()

        with self.assertRaises(GuiError):
            GuiManager.set_screen_lifecycle(gui, preamble="nope")  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            GuiManager.set_screen_lifecycle(gui, event_handler=123)  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            GuiManager.set_screen_lifecycle(gui, postamble=[])  # type: ignore[arg-type]

        pre = lambda: None
        ev = lambda _event: None
        post = lambda: None
        GuiManager.set_screen_lifecycle(gui, preamble=pre, event_handler=ev, postamble=post)

        self.assertIs(gui.screen_lifecycle.preamble, pre)
        self.assertIs(gui.screen_lifecycle.event_handler, ev)
        self.assertIs(gui.screen_lifecycle.postamble, post)

    def test_set_task_panel_lifecycle_requires_existing_task_panel(self) -> None:
        gui = self._build_manager_stub()

        with self.assertRaises(GuiError):
            GuiManager.set_task_panel_lifecycle(gui)

    def test_set_task_panel_lifecycle_validates_callables(self) -> None:
        gui = self._build_manager_stub()
        panel = SimpleNamespace(_preamble=None, _event_handler=None, _postamble=None)

        def set_lifecycle(preamble, event_handler, postamble):
            panel._preamble = preamble if preamble is not None else (lambda: None)
            panel._event_handler = event_handler if event_handler is not None else (lambda _event: None)
            panel._postamble = postamble if postamble is not None else (lambda: None)

        panel.set_lifecycle = set_lifecycle
        gui.task_panel = panel

        with self.assertRaises(GuiError):
            GuiManager.set_task_panel_lifecycle(gui, preamble=1)  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            GuiManager.set_task_panel_lifecycle(gui, event_handler=1)  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            GuiManager.set_task_panel_lifecycle(gui, postamble=1)  # type: ignore[arg-type]

        pre = lambda: None
        ev = lambda _event: None
        post = lambda: None
        GuiManager.set_task_panel_lifecycle(gui, preamble=pre, event_handler=ev, postamble=post)

        self.assertIs(panel._preamble, pre)
        self.assertIs(panel._event_handler, ev)
        self.assertIs(panel._postamble, post)

    def test_buffered_property_validates_bool(self) -> None:
        gui = self._build_manager_stub()
        gui._buffered = False

        gui.buffered = True
        self.assertTrue(gui.buffered)

        with self.assertRaises(GuiError):
            gui.buffered = 1  # type: ignore[assignment]

    def test_current_widget_switch_calls_leave_and_normalizes_invalid_assignment(self) -> None:
        gui = self._build_manager_stub()
        leave_calls = []
        old_widget = Widget.__new__(Widget)
        old_widget.leave = lambda: leave_calls.append("left")
        new_widget = Widget.__new__(Widget)
        new_widget.leave = lambda: None
        registered = {old_widget, new_widget}
        gui.focus_state_data.current_widget = old_widget
        gui._is_registered_object = lambda obj: obj in registered

        gui.current_widget = new_widget
        self.assertEqual(leave_calls, ["left"])
        self.assertIs(gui.current_widget, new_widget)

        gui.current_widget = object()  # type: ignore[assignment]
        self.assertIsNone(gui.current_widget)

    def test_task_panel_enable_disable_and_settings_wrappers(self) -> None:
        gui = self._build_manager_stub()
        set_visible_calls = []
        panel = SimpleNamespace(
            visible=True,
            auto_hide=True,
            reveal_pixels=4,
            movement_step=5,
            timer_interval=12.5,
            get_rect=lambda: Rect(1, 2, 10, 20),
            set_visible=lambda enabled: set_visible_calls.append(enabled),
            set_auto_hide=lambda value: set_visible_calls.append(("auto", value)),
            set_reveal_pixels=lambda value: set_visible_calls.append(("reveal", value)),
            set_movement_step=lambda value: set_visible_calls.append(("step", value)),
            set_timer_interval=lambda value: set_visible_calls.append(("interval", value)),
        )
        gui.task_panel = panel
        gui.workspace_state.task_panel_capture = True
        gui.workspace_state.active_object = object()

        GuiManager.begin_task_panel(gui)
        self.assertTrue(gui.workspace_state.task_panel_capture)
        self.assertIsNone(gui.workspace_state.active_object)

        GuiManager.set_task_panel_enabled(gui, False)
        self.assertFalse(gui.workspace_state.task_panel_capture)
        self.assertEqual(set_visible_calls[0], False)

        GuiManager.set_task_panel_auto_hide(gui, False)
        GuiManager.set_task_panel_reveal_pixels(gui, 3)
        GuiManager.set_task_panel_movement_step(gui, 2)
        GuiManager.set_task_panel_timer_interval(gui, 6.0)
        settings = GuiManager.read_task_panel_settings(gui)
        GuiManager.end_task_panel(gui)

        self.assertFalse(gui.workspace_state.task_panel_capture)
        self.assertEqual(settings["enabled"], panel.visible)
        self.assertEqual(settings["auto_hide"], panel.auto_hide)
        self.assertEqual(settings["reveal_pixels"], panel.reveal_pixels)
        self.assertEqual(settings["movement_step"], panel.movement_step)
        self.assertEqual(settings["timer_interval"], panel.timer_interval)
        self.assertEqual(settings["rect"], Rect(1, 2, 10, 20))
        self.assertIn(("auto", False), set_visible_calls)
        self.assertIn(("reveal", 3), set_visible_calls)
        self.assertIn(("step", 2), set_visible_calls)
        self.assertIn(("interval", 6.0), set_visible_calls)

    def test_task_panel_wrappers_require_panel_when_disabled(self) -> None:
        gui = self._build_manager_stub()

        with self.assertRaises(GuiError):
            GuiManager.begin_task_panel(gui)
        with self.assertRaises(GuiError):
            GuiManager.set_task_panel_enabled(gui, True)
        with self.assertRaises(GuiError):
            GuiManager.set_task_panel_auto_hide(gui, True)
        with self.assertRaises(GuiError):
            GuiManager.set_task_panel_reveal_pixels(gui, 4)
        with self.assertRaises(GuiError):
            GuiManager.set_task_panel_movement_step(gui, 1)
        with self.assertRaises(GuiError):
            GuiManager.set_task_panel_timer_interval(gui, 1.0)
        with self.assertRaises(GuiError):
            GuiManager.read_task_panel_settings(gui)

    def test_resolve_locking_state_clears_invalid_and_orphaned_states(self) -> None:
        gui = self._build_manager_stub()
        gui.locking_object = object()
        gui.mouse_locked = True
        gui.mouse_point_locked = True
        gui.lock_area_rect = Rect(0, 0, 10, 10)
        gui.lock_point_pos = (2, 3)
        gui.lock_point_recenter_pending = True
        gui.lock_point_tolerance_rect = Rect(0, 0, 2, 2)
        gui._is_registered_object = lambda _obj: False

        self.assertIsNone(GuiManager._resolve_locking_state(gui))
        self.assertIsNone(gui.locking_object)
        self.assertFalse(gui.mouse_locked)
        self.assertFalse(gui.mouse_point_locked)
        self.assertIsNone(gui.lock_area_rect)
        self.assertIsNone(gui.lock_point_pos)
        self.assertFalse(gui.lock_point_recenter_pending)
        self.assertIsNone(gui.lock_point_tolerance_rect)

        widget = Widget.__new__(Widget)
        gui.locking_object = widget
        gui.mouse_locked = True
        gui.mouse_point_locked = True
        gui.lock_area_rect = None
        gui.lock_point_pos = None
        gui._is_registered_object = lambda obj: obj is widget

        self.assertIsNone(GuiManager._resolve_locking_state(gui))
        self.assertIsNone(gui.locking_object)
        self.assertFalse(gui.mouse_locked)
        self.assertFalse(gui.mouse_point_locked)

    def test_build_centered_recenter_rect_validates_coverage_and_center(self) -> None:
        gui = self._build_manager_stub()
        gui.surface = SimpleNamespace(get_rect=lambda: Rect(0, 0, 100, 60))

        recenter = GuiManager._build_centered_recenter_rect(gui, coverage=0.5)
        self.assertEqual(recenter.width, 50)
        self.assertEqual(recenter.height, 30)
        self.assertEqual(recenter.center, Rect(0, 0, 100, 60).center)

        with self.assertRaises(GuiError):
            GuiManager._build_centered_recenter_rect(gui, coverage=0.0)
        with self.assertRaises(GuiError):
            GuiManager._build_centered_recenter_rect(gui, coverage=1.1)

    def test_run_preamble_and_postamble_only_call_visible_targets(self) -> None:
        gui = self._build_manager_stub()
        calls = []
        visible_window = SimpleNamespace(visible=True, run_preamble=lambda: calls.append("wp1"), run_postamble=lambda: calls.append("wo1"))
        hidden_window = SimpleNamespace(visible=False, run_preamble=lambda: calls.append("wp2"), run_postamble=lambda: calls.append("wo2"))
        panel = SimpleNamespace(visible=True, run_preamble=lambda: calls.append("pp"), run_postamble=lambda: calls.append("po"))
        gui.windows = [visible_window, hidden_window]
        gui.task_panel = panel
        gui.screen_lifecycle.set_lifecycle(
            lambda: calls.append("sp"),
            gui.screen_lifecycle.event_handler,
            lambda: calls.append("so"),
        )

        GuiManager.run_preamble(gui)
        GuiManager.run_postamble(gui)

        self.assertEqual(calls, ["sp", "wp1", "pp", "wo1", "po", "so"])

    def test_raise_and_lower_window_handle_registered_and_stale_active(self) -> None:
        gui = self._build_manager_stub()
        w1 = object()
        w2 = object()
        w3 = object()
        gui.windows = [w1, w2, w3]
        gui.workspace_state.active_object = w2

        GuiManager.lower_window(gui, w3)
        self.assertEqual(gui.windows, [w3, w1, w2])

        GuiManager.raise_window(gui, w3)
        self.assertEqual(gui.windows, [w1, w2, w3])

        stale = object()
        gui.workspace_state.active_object = stale
        GuiManager.raise_window(gui, stale)
        self.assertIsNone(gui.workspace_state.active_object)

    def test_handle_widget_executes_callback_paths_and_validates_callable(self) -> None:
        gui = self._build_manager_stub()
        marker = []
        event = object()

        widget = SimpleNamespace(
            id="w",
            on_activate=lambda: marker.append("called"),
            handle_event=lambda _event, _window: True,
        )
        self.assertFalse(GuiManager.handle_widget(gui, widget, event))
        self.assertEqual(marker, ["called"])

        widget.on_activate = None
        self.assertTrue(GuiManager.handle_widget(gui, widget, event))

        widget.on_activate = "nope"
        with self.assertRaises(GuiError):
            GuiManager.handle_widget(gui, widget, event)

        widget.on_activate = lambda: marker.append("unused")
        widget.handle_event = lambda _event, _window: False
        self.assertFalse(GuiManager.handle_widget(gui, widget, event))

    def test_set_cursor_prefers_existing_cursor_rect_hotspot_when_present(self) -> None:
        gui = self._build_manager_stub()
        cursor_bitmap = SimpleNamespace(get_rect=lambda: Rect(0, 0, 6, 8))
        gui._bitmap_factory = SimpleNamespace(get_cursor=lambda name: (cursor_bitmap, (1, 2)))
        gui.mouse_point_locked = True
        gui.lock_point_pos = (50, 60)
        gui.mouse_pos = (10, 20)
        gui.cursor_hotspot = (2, 3)
        gui.cursor_rect = Rect(100, 200, 4, 4)

        GuiManager.set_cursor(gui, "arrow")

        self.assertIs(gui.cursor_image, cursor_bitmap)
        # Existing cursor_rect/cursor_hotspot establishes hotspot anchor precedence.
        self.assertEqual(gui.cursor_rect.topleft, (101, 201))

    def test_set_lock_area_validates_area_and_locking_object_requirements(self) -> None:
        gui = self._build_manager_stub()
        widget = Widget.__new__(Widget)
        gui._is_registered_object = lambda obj: obj is widget

        with self.assertRaises(GuiError):
            GuiManager.set_lock_area(gui, widget, area="bad")  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            GuiManager.set_lock_area(gui, None, area=Rect(0, 0, 2, 2))
        with self.assertRaises(GuiError):
            GuiManager.set_lock_area(gui, object(), area=Rect(0, 0, 2, 2))  # type: ignore[arg-type]

        gui._is_registered_object = lambda _obj: False
        with self.assertRaises(GuiError):
            GuiManager.set_lock_area(gui, widget, area=Rect(0, 0, 2, 2))

        gui._is_registered_object = lambda obj: obj is widget
        with self.assertRaises(GuiError):
            GuiManager.set_lock_area(gui, widget, area=Rect(0, 0, 0, 2))

    def test_set_mouse_pos_respects_update_physical_flag(self) -> None:
        gui = self._build_manager_stub()
        set_calls = []
        gui._set_physical_mouse_pos = lambda pos: set_calls.append(pos)

        GuiManager.set_mouse_pos(gui, (5, 6), update_physical_coords=False)
        self.assertEqual(gui.mouse_pos, (5, 6))
        self.assertEqual(set_calls, [])

        GuiManager.set_mouse_pos(gui, (7, 8), update_physical_coords=True)
        self.assertEqual(gui.mouse_pos, (7, 8))
        self.assertEqual(set_calls, [(7, 8)])

        with self.assertRaises(GuiError):
            GuiManager.set_mouse_pos(gui, (1,), update_physical_coords=True)  # type: ignore[arg-type]

    def test_clear_task_owners_for_window_is_noop_when_window_unregistered(self) -> None:
        gui = self._build_manager_stub()
        window = object()
        gui.event_delivery._task_owner_by_id = {"a": window}

        GuiManager.clear_task_owners_for_window(gui, window)

        self.assertEqual(gui.event_delivery._task_owner_by_id, {"a": window})

    def test_current_widget_property_clears_stale_registration(self) -> None:
        gui = self._build_manager_stub()
        widget = Widget.__new__(Widget)
        gui.focus_state_data.current_widget = widget
        gui._is_registered_object = lambda _obj: False

        self.assertIsNone(gui.current_widget)
        self.assertIsNone(gui.focus_state_data.current_widget)

    def test_clear_button_groups_delegates_to_mediator(self) -> None:
        gui = self._build_manager_stub()
        calls = []
        gui.button_group_mediator = SimpleNamespace(clear=lambda: calls.append("clear"))

        GuiManager.clear_button_groups(gui)

        self.assertEqual(calls, ["clear"])

    def test_set_grid_properties_validates_and_forwards(self) -> None:
        gui = self._build_manager_stub()
        forwarded = []
        gui.layout_manager = SimpleNamespace(set_properties=lambda a, w, h, s, r: forwarded.append((a, w, h, s, r)))

        with self.assertRaises(GuiError):
            GuiManager.set_grid_properties(gui, (0, 0), 0, 10, 1)
        with self.assertRaises(GuiError):
            GuiManager.set_grid_properties(gui, (0, 0), 10, 0, 1)
        with self.assertRaises(GuiError):
            GuiManager.set_grid_properties(gui, (0, 0), 10, 10, -1)
        with self.assertRaises(GuiError):
            GuiManager.set_grid_properties(gui, (0,), 10, 10, 1)  # type: ignore[arg-type]

        GuiManager.set_grid_properties(gui, (2, 3), 11, 12, 4, use_rect=False)

        self.assertEqual(forwarded, [((2, 3), 11, 12, 4, False)])

    def test_gridded_delegates_to_layout_manager(self) -> None:
        gui = self._build_manager_stub()
        gui.layout_manager = SimpleNamespace(get_cell=lambda x, y: (x + 10, y + 20))

        self.assertEqual(GuiManager.gridded(gui, 1, 2), (11, 22))

    def test_restore_pristine_requires_initialized_snapshot(self) -> None:
        gui = self._build_manager_stub()
        gui.surface = SimpleNamespace(blit=lambda *_args, **_kwargs: None)
        gui.pristine = None

        with self.assertRaises(GuiError):
            GuiManager.restore_pristine(gui)

    def test_set_pristine_validates_target_surface_and_image_name(self) -> None:
        gui = self._build_manager_stub()

        target = SimpleNamespace(surface=None, pristine=None)
        with self.assertRaises(GuiError):
            GuiManager.set_pristine(gui, "bg.png", target)

        target.surface = SimpleNamespace(get_rect=lambda: Rect(0, 0, 10, 10), blit=lambda *_args, **_kwargs: None)
        with self.assertRaises(GuiError):
            GuiManager.set_pristine(gui, None, target)  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            GuiManager.set_pristine(gui, "", target)

    def test_resolve_active_object_clears_stale_window(self) -> None:
        gui = self._build_manager_stub()
        stale = object()
        gui.workspace_state.active_object = stale

        self.assertIsNone(GuiManager._resolve_active_object(gui))
        self.assertIsNone(gui.workspace_state.active_object)


if __name__ == "__main__":
    unittest.main()
