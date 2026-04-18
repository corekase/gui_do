import unittest
from types import SimpleNamespace
from unittest.mock import patch

from pygame import Rect

from event_mouse_fixtures import build_mouse_gui_stub
from gui_manager_test_factory import build_gui_manager_stub
from gui.utility.constants import GuiError
from gui.utility.guimanager import GuiManager
from gui.utility.task_panel import _ManagedTaskPanel
from gui.utility.widget import Widget
from gui.widgets.window import Window


class _PanelStub:
    def __init__(self, visible=True):
        self.widgets = []
        self.visible = visible
        self.surface = object()
        self.set_visible_calls = []
        self.dispose_calls = 0

    def set_visible(self, visible):
        self.set_visible_calls.append(visible)
        self.visible = visible

    def dispose(self):
        self.dispose_calls += 1


class GuiManagerRoiBatch9Tests(unittest.TestCase):
    def _build_manager_stub(self):
        gui = build_gui_manager_stub(
            surface=SimpleNamespace(get_rect=lambda: Rect(0, 0, 100, 60)),
            include_ui_factory=True,
        )
        return gui

    def test_module_noop_helpers_are_callable(self) -> None:
        import gui.utility.guimanager as gm

        self.assertIsNone(gm._noop())
        self.assertIsNone(gm._noop_event(SimpleNamespace()))

    def test_configure_task_panel_validates_remaining_inputs(self) -> None:
        gui = self._build_manager_stub()

        with self.assertRaises(GuiError):
            GuiManager.configure_task_panel(gui, timer_interval=True)  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            GuiManager.configure_task_panel(gui, backdrop=1)  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            GuiManager.configure_task_panel(gui, backdrop="")
        with self.assertRaises(GuiError):
            GuiManager.configure_task_panel(gui, preamble=1)  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            GuiManager.configure_task_panel(gui, event_handler=1)  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            GuiManager.configure_task_panel(gui, postamble=1)  # type: ignore[arg-type]

    def test_configure_task_panel_preserves_visible_true_state(self) -> None:
        gui = self._build_manager_stub()
        old_panel = _PanelStub(visible=True)
        widget = Widget.__new__(Widget)
        widget.window = None
        widget.surface = None
        old_panel.widgets = [widget]
        gui.task_panel = old_panel

        created = _PanelStub(visible=True)
        with patch("gui.utility.task_panel._ManagedTaskPanel", return_value=created):
            GuiManager.configure_task_panel(gui)

        self.assertIs(gui.task_panel, created)
        self.assertEqual(created.set_visible_calls, [True])
        self.assertEqual(old_panel.dispose_calls, 1)
        self.assertIs(widget.window, created)
        self.assertIs(widget.surface, created.surface)

    def test_add_rejects_window_when_task_panel_capture_active(self) -> None:
        gui = self._build_manager_stub()
        gui.task_panel = _PanelStub()
        gui.workspace_state.task_panel_capture = True

        window = Window.__new__(Window)

        with self.assertRaises(GuiError):
            GuiManager.add(gui, window)

    def test_add_task_panel_widget_and_rollback_on_post_add_failure(self) -> None:
        gui = self._build_manager_stub()
        panel = _PanelStub()
        gui.task_panel = panel
        gui.workspace_state.task_panel_capture = True

        widget = Widget.__new__(Widget)
        widget.id = "tp-w"
        widget.window = None
        widget.surface = None

        def _boom():
            raise RuntimeError("post add fail")

        widget._on_added_to_gui = _boom

        with self.assertRaises(RuntimeError):
            GuiManager.add(gui, widget)

        self.assertNotIn(widget, panel.widgets)
        self.assertIsNone(widget.window)
        self.assertIsNone(widget.surface)

    def test_set_cursor_validates_name(self) -> None:
        gui = self._build_manager_stub()

        with self.assertRaises(GuiError):
            GuiManager.set_cursor(gui, "")

    def test_set_lock_point_none_delegates_release(self) -> None:
        gui = self._build_manager_stub()
        calls = []
        gui.set_lock_area = lambda locking_object, area=None: calls.append((locking_object, area))

        GuiManager.set_lock_point(gui, None)

        self.assertEqual(calls, [(None, None)])

    def test_enforce_point_lock_rejects_invalid_hardware_position(self) -> None:
        gui = self._build_manager_stub()
        gui.lock_point_pos = (10, 10)
        gui.point_lock_recenter_rect = Rect(0, 0, 20, 20)

        with self.assertRaises(GuiError):
            GuiManager.enforce_point_lock(gui, "bad")  # type: ignore[arg-type]

    def test_restore_pristine_uses_default_area_when_none(self) -> None:
        gui = self._build_manager_stub()
        pristine = SimpleNamespace(get_rect=lambda: Rect(2, 3, 4, 5))
        blits = []
        target = SimpleNamespace(pristine=pristine, surface=SimpleNamespace(blit=lambda src, pos, area: blits.append((src, pos, area))))

        GuiManager.restore_pristine(gui, area=None, obj=target)

        self.assertEqual(len(blits), 1)
        self.assertEqual(blits[0][1], (2, 3))
        self.assertEqual(blits[0][2], Rect(2, 3, 4, 5))

    def test_helper_resolvers_cover_positive_paths(self) -> None:
        gui = self._build_manager_stub()

        # _is_registered_button_group false path when attached and not found.
        button = SimpleNamespace(surface=object())
        self.assertFalse(GuiManager._is_registered_button_group(gui, button))

        # _resolve_active_object returns active when present.
        win = Window.__new__(Window)
        gui.windows = [win]
        gui.workspace_state.active_object = win
        self.assertIs(gui.object_registry.resolve_active_object(), win)

        # _resolve_current_widget returns current when registered.
        widget = Widget.__new__(Widget)
        gui.focus_state_data.current_widget = widget
        gui.object_registry.is_registered_object = lambda obj: obj is widget
        self.assertIs(gui.focus_state.resolve_current_widget(), widget)

        # _resolve_locking_state early return when no locking object and no lock flags.
        gui.locking_object = None
        gui.mouse_locked = False
        gui.lock_area_rect = None
        gui.lock_point_pos = None
        self.assertIsNone(gui.lock_state.resolve())

    def test_managed_task_panel_helper_methods_success_paths(self) -> None:
        import gui.utility.guimanager as gm

        timer_calls = []
        pre_calls = []
        event_calls = []
        post_calls = []
        restore_calls = []

        panel = _ManagedTaskPanel.__new__(_ManagedTaskPanel)
        panel.gui = build_mouse_gui_stub(
            mouse_pos=(20, 65),
            extras={
                "timers": SimpleNamespace(remove_timer=lambda timer_id: timer_calls.append(timer_id)),
                "surface": SimpleNamespace(get_rect=lambda: Rect(0, 0, 120, 70)),
                "restore_pristine": lambda area, obj: restore_calls.append((area, obj)),
            },
        )
        panel._timer_id = ("task-panel-motion", 1)
        panel._preamble = lambda: pre_calls.append(True)
        panel._event_handler = lambda event: event_calls.append(event)
        panel._postamble = lambda: post_calls.append(True)
        panel.x = 10
        panel.y = 50
        panel.width = 110
        panel.height = 18
        panel.reveal_pixels = 4
        panel.surface = SimpleNamespace(get_rect=lambda: Rect(0, 0, 110, 18))
        panel.pristine = object()

        panel.dispose()
        panel.run_preamble()
        panel.handle_event("evt")
        panel.run_postamble()
        self.assertEqual(timer_calls, [("task-panel-motion", 1)])
        self.assertEqual(pre_calls, [True])
        self.assertEqual(event_calls, ["evt"])
        self.assertEqual(post_calls, [True])
        self.assertEqual(panel.get_rect(), Rect(10, 50, 110, 18))

        panel.refresh_targets()
        self.assertEqual(panel._shown_y, 52)
        self.assertEqual(panel._hidden_y, 66)
        self.assertTrue(panel._hovered)

        panel.draw_background()
        self.assertEqual(len(restore_calls), 1)

    def test_configure_task_panel_validates_primary_numeric_types(self) -> None:
        gui = self._build_manager_stub()

        with self.assertRaises(GuiError):
            GuiManager.configure_task_panel(gui, height=0)
        with self.assertRaises(GuiError):
            GuiManager.configure_task_panel(gui, x="bad")  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            GuiManager.configure_task_panel(gui, reveal_pixels=0)
        with self.assertRaises(GuiError):
            GuiManager.configure_task_panel(gui, auto_hide=1)  # type: ignore[arg-type]
        with self.assertRaises(GuiError):
            GuiManager.configure_task_panel(gui, movement_step=0)

    def test_add_widget_task_panel_capture_success_and_guards(self) -> None:
        gui = self._build_manager_stub()
        panel = _PanelStub()
        gui.task_panel = panel
        gui.workspace_state.task_panel_capture = True

        widget = Widget.__new__(Widget)
        widget.id = "ok"
        widget.window = None
        widget.surface = None

        out = GuiManager.add(gui, widget)
        self.assertIs(out, widget)
        self.assertIn(widget, panel.widgets)
        self.assertIs(widget.window, panel)
        self.assertIs(widget.surface, panel.surface)

        duplicate = Widget.__new__(Widget)
        duplicate.id = "dup"
        duplicate.window = None
        duplicate.surface = None
        gui.object_registry.is_registered_object = lambda obj: obj is duplicate
        with self.assertRaises(GuiError):
            GuiManager.add(gui, duplicate)

        gui.object_registry.is_registered_object = lambda _obj: False
        bad_id = Widget.__new__(Widget)
        bad_id.id = ""
        bad_id.window = None
        bad_id.surface = None
        with self.assertRaises(GuiError):
            GuiManager.add(gui, bad_id)

    def test_add_widget_active_window_rollback_when_collection_membership_false(self) -> None:
        class _NoContainList(list):
            def append(self, _value):
                return None

        gui = self._build_manager_stub()
        active_window = SimpleNamespace(surface=object(), widgets=_NoContainList())
        gui.windows = [active_window]
        gui.workspace_state.active_object = active_window

        widget = Widget.__new__(Widget)
        widget.id = "active"
        widget.window = None
        widget.surface = None

        def _boom():
            raise RuntimeError("post add fail")

        widget._on_added_to_gui = _boom

        with self.assertRaises(RuntimeError):
            GuiManager.add(gui, widget)

        self.assertIsNone(widget.window)
        self.assertIsNone(widget.surface)

    def test_raise_and_lower_window_clear_stale_active_when_unregistered(self) -> None:
        gui = self._build_manager_stub()
        stale = Window.__new__(Window)
        gui.workspace_state.active_object = stale

        GuiManager.lower_window(gui, stale)
        self.assertIsNone(gui.workspace_state.active_object)

        gui.workspace_state.active_object = stale
        GuiManager.raise_window(gui, stale)
        self.assertIsNone(gui.workspace_state.active_object)

    def test_lock_area_success_and_release_mouse_locked_non_point_mode(self) -> None:
        gui = self._build_manager_stub()
        widget = Widget.__new__(Widget)
        gui.object_registry.is_registered_object = lambda obj: obj is widget
        gui.mouse_pos = (9, 8)
        set_calls = []
        gui.pointer.set_physical_mouse_pos = lambda pos: set_calls.append(pos)

        GuiManager.set_lock_area(gui, widget, Rect(1, 2, 5, 6))
        self.assertIs(gui.locking_object, widget)
        self.assertTrue(gui.mouse_locked)
        self.assertFalse(gui.mouse_point_locked)

        gui.mouse_locked = True
        gui.mouse_point_locked = False
        GuiManager.set_lock_area(gui, None)
        self.assertEqual(set_calls, [(9, 8)])

    def test_set_lock_point_defaults_and_invalid_point(self) -> None:
        gui = self._build_manager_stub()
        widget = Widget.__new__(Widget)
        gui.object_registry.is_registered_object = lambda obj: obj is widget
        gui.input_providers.mouse_get_pos = lambda: (12, 13)

        GuiManager.set_lock_point(gui, widget)
        self.assertEqual(gui.lock_point_pos, (12, 13))

        with self.assertRaises(GuiError):
            GuiManager.set_lock_point(gui, widget, point="bad")  # type: ignore[arg-type]

    def test_set_pristine_success_path_and_default_target_assignment(self) -> None:
        gui = self._build_manager_stub()
        scaled = SimpleNamespace(convert=lambda: object(), get_rect=lambda: Rect(0, 0, 10, 6))
        target = SimpleNamespace(
            surface=SimpleNamespace(get_rect=lambda: Rect(0, 0, 10, 6), blit=lambda *_args, **_kwargs: None),
            pristine=None,
        )
        gui._bitmap_factory = SimpleNamespace(file_resource=lambda *_args: "image-path")
        gui.graphics.copy_graphic_area = lambda *_args, **_kwargs: SimpleNamespace(convert=lambda: "copied")

        with patch("gui.utility.graphics_coordinator.pygame.image.load", return_value=SimpleNamespace()), patch(
            "gui.utility.graphics_coordinator.pygame.transform.smoothscale",
            return_value=scaled,
        ):
            GuiManager.set_pristine(gui, "bg.png", target)

        self.assertEqual(target.pristine, "copied")

    def test_enforce_point_lock_non_recenter_paths_and_lock_area_validation(self) -> None:
        gui = self._build_manager_stub()
        gui.lock_point_recenter_pending = True
        gui.lock_point_pos = None
        gui.point_lock_recenter_rect = Rect(0, 0, 10, 10)
        GuiManager.enforce_point_lock(gui, (2, 2))
        self.assertFalse(gui.lock_point_recenter_pending)

        gui.lock_point_pos = (4, 4)
        gui.lock_point_recenter_pending = False
        set_calls = []
        gui.pointer.set_physical_mouse_pos = lambda pos: set_calls.append(pos)
        GuiManager.enforce_point_lock(gui, (3, 3))
        self.assertEqual(set_calls, [])

        with self.assertRaises(GuiError):
            GuiManager.lock_area(gui, "bad")  # type: ignore[arg-type]

    def test_managed_task_panel_branches_for_no_refresh_paths(self) -> None:
        import gui.utility.guimanager as gm

        panel = _ManagedTaskPanel.__new__(_ManagedTaskPanel)
        refresh_calls = []
        panel.refresh_targets = lambda: refresh_calls.append(True)
        panel.visible = True
        panel.auto_hide = True
        panel._hovered = False
        panel._shown_y = 10
        panel._hidden_y = 20
        panel.y = 20
        panel.movement_step = 3

        panel.set_visible(False)
        panel.set_auto_hide(True)
        panel.animate()

        self.assertFalse(panel.visible)
        self.assertTrue(panel.auto_hide)
        self.assertEqual(panel.y, 20)
        self.assertEqual(refresh_calls, [])

    def test_current_widget_same_assignment_does_not_leave(self) -> None:
        gui = self._build_manager_stub()
        widget = Widget.__new__(Widget)
        leave_calls = []
        widget.leave = lambda: leave_calls.append(True)
        gui.focus_state_data.current_widget = widget
        gui.object_registry.is_registered_object = lambda obj: obj is widget

        GuiManager.current_widget.fset(gui, widget)

        self.assertEqual(leave_calls, [])
        self.assertIs(gui.focus_state_data.current_widget, widget)

    def test_label_wrapper_explicit_id_path(self) -> None:
        import gui.utility.guimanager as gm

        gui = self._build_manager_stub()
        added = []
        gui.add = lambda obj: added.append(obj) or obj

        with patch("gui.utility.ui_factory.gLabel", side_effect=lambda *_args: SimpleNamespace(args=_args)):
            gm.GuiManager.Label(gui, (1, 2), "text", id="explicit")

        self.assertEqual(added[0].args[1], "explicit")
        self.assertEqual(gui.ui_factory._label_sequence, 0)

    def test_configure_task_panel_without_old_panel_path(self) -> None:
        gui = self._build_manager_stub()
        created = _PanelStub(visible=True)

        with patch("gui.utility.task_panel._ManagedTaskPanel", return_value=created):
            GuiManager.configure_task_panel(gui)

        self.assertIs(gui.task_panel, created)
        self.assertEqual(created.set_visible_calls, [])

    def test_lower_raise_window_unregistered_paths_with_preserved_active(self) -> None:
        gui = self._build_manager_stub()
        window = Window.__new__(Window)
        gui.workspace_state.active_object = window

        GuiManager.lower_window(gui, window)
        self.assertIsNone(gui.workspace_state.active_object)

        gui.workspace_state.active_object = window
        GuiManager.raise_window(gui, window)
        self.assertIsNone(gui.workspace_state.active_object)

    def test_set_cursor_without_prior_cursor_anchor_uses_mouse_pos(self) -> None:
        gui = self._build_manager_stub()
        bitmap = SimpleNamespace(get_rect=lambda: Rect(0, 0, 6, 6))
        gui._bitmap_factory = SimpleNamespace(get_cursor=lambda _name: (bitmap, (1, 1)))
        gui.mouse_pos = (10, 10)
        gui.mouse_point_locked = False
        gui.lock_point_pos = None
        gui.cursor_rect = None
        gui.cursor_hotspot = None

        GuiManager.set_cursor(gui, "cursor")

        self.assertEqual(gui.cursor_rect.topleft, (9, 9))

    def test_set_lock_area_release_when_not_mouse_locked(self) -> None:
        gui = self._build_manager_stub()
        gui.mouse_locked = False
        gui.mouse_point_locked = False
        gui.mouse_pos = (4, 5)
        set_calls = []
        gui.pointer.set_physical_mouse_pos = lambda pos: set_calls.append(pos)

        GuiManager.set_lock_area(gui, None)

        self.assertEqual(set_calls, [])

    def test_set_lock_point_unregistered_guard(self) -> None:
        gui = self._build_manager_stub()
        widget = Widget.__new__(Widget)
        gui.object_registry.is_registered_object = lambda _obj: False

        with self.assertRaises(GuiError):
            GuiManager.set_lock_point(gui, widget, (1, 2))

    def test_set_pristine_default_obj_and_error_wrap_path(self) -> None:
        gui = self._build_manager_stub()
        gui.surface = SimpleNamespace(get_rect=lambda: Rect(0, 0, 10, 6), blit=lambda *_args, **_kwargs: None)
        gui.pristine = None
        gui._bitmap_factory = SimpleNamespace(file_resource=lambda *_args: "image-path")
        gui.graphics.copy_graphic_area = lambda *_args, **_kwargs: SimpleNamespace(convert=lambda: "copied")

        scaled = SimpleNamespace(convert=lambda: object(), get_rect=lambda: Rect(0, 0, 10, 6))
        with patch("gui.utility.graphics_coordinator.pygame.image.load", return_value=SimpleNamespace()), patch(
            "gui.utility.graphics_coordinator.pygame.transform.smoothscale",
            return_value=scaled,
        ):
            GuiManager.set_pristine(gui, "bg.png")

        self.assertEqual(gui.pristine, "copied")

        with patch("gui.utility.graphics_coordinator.pygame.image.load", side_effect=RuntimeError("load fail")), patch(
            "gui.utility.graphics_coordinator.DataResourceErrorHandler.raise_load_error",
            side_effect=GuiError("wrapped"),
        ):
            with self.assertRaises(GuiError):
                GuiManager.set_pristine(gui, "bg.png")

    def test_restore_pristine_with_explicit_area(self) -> None:
        gui = self._build_manager_stub()
        area = Rect(1, 2, 3, 4)
        blits = []
        target = SimpleNamespace(pristine=object(), surface=SimpleNamespace(blit=lambda src, pos, arg: blits.append((src, pos, arg))))

        GuiManager.restore_pristine(gui, area=area, obj=target)

        self.assertEqual(blits[0][1], (1, 2))
        self.assertEqual(blits[0][2], area)

    def test_find_widget_id_conflict_skips_candidate_self(self) -> None:
        gui = self._build_manager_stub()
        candidate = Widget.__new__(Widget)
        candidate.id = "same"
        gui.widgets = [candidate]
        gui.task_panel = SimpleNamespace(widgets=[candidate])
        gui.windows = [SimpleNamespace(widgets=[candidate])]

        self.assertIsNone(GuiManager._find_widget_id_conflict(gui, "same", candidate))

    def test_registered_button_group_true_paths(self) -> None:
        gui = self._build_manager_stub()
        button = Widget.__new__(Widget)
        button.surface = object()

        gui.widgets = [button]
        self.assertTrue(GuiManager._is_registered_button_group(gui, button))

        gui.widgets = []
        gui.task_panel = SimpleNamespace(widgets=[button])
        self.assertTrue(GuiManager._is_registered_button_group(gui, button))

        gui.task_panel = None
        gui.windows = [SimpleNamespace(widgets=[button])]
        self.assertTrue(GuiManager._is_registered_button_group(gui, button))

    def test_registered_object_window_and_false_paths(self) -> None:
        gui = self._build_manager_stub()
        window = Window.__new__(Window)

        gui.windows = [window]
        self.assertTrue(gui.object_registry.is_registered_object(window))

        gui.windows = []
        self.assertFalse(gui.object_registry.is_registered_object(window))

    def test_resolve_locking_state_non_widget_and_unregistered_paths(self) -> None:
        gui = self._build_manager_stub()

        gui.locking_object = object()
        gui.mouse_locked = True
        gui.mouse_point_locked = True
        gui.lock_area_rect = Rect(0, 0, 3, 3)
        gui.lock_point_pos = (1, 1)
        gui.lock_point_recenter_pending = True
        gui.lock_point_tolerance_rect = Rect(0, 0, 1, 1)
        self.assertIsNone(gui.lock_state.resolve())

        widget = Widget.__new__(Widget)
        gui.locking_object = widget
        gui.mouse_locked = True
        gui.mouse_point_locked = True
        gui.lock_area_rect = Rect(0, 0, 3, 3)
        gui.lock_point_pos = (1, 1)
        gui.lock_point_recenter_pending = True
        gui.lock_point_tolerance_rect = Rect(0, 0, 1, 1)
        gui.object_registry.is_registered_object = lambda _obj: False
        self.assertIsNone(gui.lock_state.resolve())

    def test_managed_task_panel_animate_no_movement_when_at_target(self) -> None:
        import gui.utility.guimanager as gm

        panel = _ManagedTaskPanel.__new__(_ManagedTaskPanel)
        panel.visible = True
        panel.auto_hide = True
        panel._hovered = False
        panel._shown_y = 10
        panel._hidden_y = 20
        panel.y = 20
        panel.movement_step = 3
        panel.refresh_targets = lambda: None

        panel.animate()

        self.assertEqual(panel.y, 20)

    def test_current_widget_assignment_from_none_registered_path(self) -> None:
        gui = self._build_manager_stub()
        widget = Widget.__new__(Widget)
        gui.focus_state_data.current_widget = None
        gui.object_registry.is_registered_object = lambda obj: obj is widget

        GuiManager.current_widget.fset(gui, widget)

        self.assertIs(gui.focus_state_data.current_widget, widget)

    def test_run_preamble_postamble_hidden_panel_branches(self) -> None:
        gui = self._build_manager_stub()
        calls = []
        hidden_window = SimpleNamespace(visible=False, run_preamble=lambda: calls.append("wp"), run_postamble=lambda: calls.append("wo"))
        gui.windows = [hidden_window]
        gui.task_panel = SimpleNamespace(visible=False, run_preamble=lambda: calls.append("pp"), run_postamble=lambda: calls.append("po"))
        gui.screen_lifecycle.set_lifecycle(
            lambda: calls.append("sp"),
            gui.screen_lifecycle.event_handler,
            lambda: calls.append("so"),
        )

        GuiManager.run_preamble(gui)
        GuiManager.run_postamble(gui)

        self.assertEqual(calls, ["sp", "so"])

    def test_set_task_panel_enabled_true_keeps_capture_state(self) -> None:
        gui = self._build_manager_stub()
        panel = _PanelStub(visible=False)
        gui.task_panel = panel
        gui.workspace_state.task_panel_capture = True

        GuiManager.set_task_panel_enabled(gui, True)

        self.assertEqual(panel.set_visible_calls, [True])
        self.assertTrue(gui.workspace_state.task_panel_capture)

    def test_add_screen_widget_rollback_without_membership(self) -> None:
        class _NoContainList(list):
            def append(self, _value):
                return None

        gui = self._build_manager_stub()
        gui.widgets = _NoContainList()

        widget = Widget.__new__(Widget)
        widget.id = "screen"
        widget.window = None
        widget.surface = None

        def _boom():
            raise RuntimeError("post add fail")

        widget._on_added_to_gui = _boom

        with self.assertRaises(RuntimeError):
            GuiManager.add(gui, widget)

        self.assertIsNone(widget.window)
        self.assertIsNone(widget.surface)

    def test_set_pristine_reraises_guierror_from_loader(self) -> None:
        gui = self._build_manager_stub()
        gui._bitmap_factory = SimpleNamespace(file_resource=lambda *_args: "image-path")
        target = SimpleNamespace(surface=SimpleNamespace(get_rect=lambda: Rect(0, 0, 10, 6), blit=lambda *_args, **_kwargs: None), pristine=None)

        with patch("gui.utility.graphics_coordinator.pygame.image.load", side_effect=GuiError("load guierror")):
            with self.assertRaises(GuiError):
                GuiManager.set_pristine(gui, "bg.png", target)

    def test_registered_helpers_cover_false_loop_paths(self) -> None:
        gui = self._build_manager_stub()
        button = SimpleNamespace(surface=object())
        gui.windows = [SimpleNamespace(widgets=[object()])]
        self.assertFalse(GuiManager._is_registered_button_group(gui, button))

        widget = Widget.__new__(Widget)
        gui.widgets = []
        gui.task_panel = None
        gui.windows = [SimpleNamespace(widgets=[Widget.__new__(Widget)])]
        self.assertFalse(gui.object_registry.is_registered_object(widget))

    def test_resolve_locking_state_registered_with_no_area_or_point(self) -> None:
        gui = self._build_manager_stub()
        widget = Widget.__new__(Widget)
        gui.locking_object = widget
        gui.mouse_locked = True
        gui.mouse_point_locked = True
        gui.lock_area_rect = None
        gui.lock_point_pos = None
        gui.lock_point_recenter_pending = True
        gui.lock_point_tolerance_rect = Rect(0, 0, 1, 1)
        gui.object_registry.is_registered_object = lambda obj: obj is widget

        self.assertIsNone(gui.lock_state.resolve())

    def test_manager_init_task_panel_enabled_type_and_true_branch(self) -> None:
        import gui.utility.guimanager as gm

        surface = SimpleNamespace(get_rect=lambda: Rect(0, 0, 100, 60))
        bitmap_factory = SimpleNamespace(load_font=lambda *_args: None)

        with patch("gui.utility.guimanager.EventDispatcher", side_effect=lambda gui: SimpleNamespace(gui=gui)), patch(
            "gui.utility.guimanager.LayoutManager", return_value=SimpleNamespace()
        ), patch("gui.utility.guimanager.Renderer", side_effect=lambda gui: SimpleNamespace(gui=gui)), patch(
            "gui.utility.guimanager.Scheduler", side_effect=lambda gui: SimpleNamespace(gui=gui)
        ), patch("gui.utility.guimanager.Timers", return_value=SimpleNamespace()), patch(
            "gui.utility.guimanager.ButtonGroupMediator", return_value=SimpleNamespace()
        ):
            with self.assertRaises(GuiError):
                gm.GuiManager(
                    surface,
                    [("main", "a.ttf", 12)],
                    bitmap_factory=bitmap_factory,
                    task_panel_enabled="yes",  # type: ignore[arg-type]
                    event_getter=lambda: [],
                    mouse_get_pos=lambda: (0, 0),
                    mouse_set_pos=lambda _pos: None,
                    mouse_set_visible=lambda _visible: None,
                )

        with patch("gui.utility.guimanager.EventDispatcher", side_effect=lambda gui: SimpleNamespace(gui=gui)), patch(
            "gui.utility.guimanager.LayoutManager", return_value=SimpleNamespace()
        ), patch("gui.utility.guimanager.Renderer", side_effect=lambda gui: SimpleNamespace(gui=gui)), patch(
            "gui.utility.guimanager.Scheduler", side_effect=lambda gui: SimpleNamespace(gui=gui)
        ), patch("gui.utility.guimanager.Timers", return_value=SimpleNamespace()), patch(
            "gui.utility.guimanager.ButtonGroupMediator", return_value=SimpleNamespace()
        ), patch.object(gm.GuiManager, "configure_task_panel", return_value=None) as configure_task_panel:
            gm.GuiManager(
                surface,
                [("main", "a.ttf", 12)],
                bitmap_factory=bitmap_factory,
                task_panel_enabled=True,
                event_getter=lambda: [],
                mouse_get_pos=lambda: (0, 0),
                mouse_set_pos=lambda _pos: None,
                mouse_set_visible=lambda _visible: None,
            )

        configure_task_panel.assert_called_once()

    def test_add_window_success_arc_to_return(self) -> None:
        gui = self._build_manager_stub()
        window = Window.__new__(Window)

        out = GuiManager.add(gui, window)

        self.assertIs(out, window)
        self.assertIn(window, gui.windows)
        self.assertIs(gui.workspace_state.active_object, window)

    def test_is_registered_object_widget_unmatched_with_nonempty_windows(self) -> None:
        gui = self._build_manager_stub()
        widget = Widget.__new__(Widget)
        other = Widget.__new__(Widget)
        gui.widgets = []
        gui.task_panel = None
        gui.windows = [SimpleNamespace(widgets=[other])]

        self.assertFalse(gui.object_registry.is_registered_object(widget))

    def test_resolve_locking_state_none_owner_alt_short_circuit_paths(self) -> None:
        gui = self._build_manager_stub()
        gui.locking_object = None

        gui.mouse_locked = False
        gui.lock_area_rect = Rect(0, 0, 2, 2)
        gui.lock_point_pos = None
        gui.lock_state.resolve()
        self.assertIsNone(gui.lock_area_rect)

        gui.mouse_locked = False
        gui.lock_area_rect = None
        gui.lock_point_pos = (3, 4)
        gui.lock_state.resolve()
        self.assertIsNone(gui.lock_point_pos)


if __name__ == "__main__":
    unittest.main()
