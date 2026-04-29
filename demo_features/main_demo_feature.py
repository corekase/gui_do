"""Main scene feature extracted from the gui_do demo entrypoint."""

from __future__ import annotations

from pygame import Rect

from gui_do import (
    ArrowBoxControl,
    ArrangeContext,
    Binding,
    BindingGroup,
    ButtonControl,
    ButtonGroupControl,
    CanvasViewport,
    ColorPickerControl,
    CommandHistory,
    DataGridControl,
    DesignTokens,
    DropdownControl,
    DropdownOption,
    ErrorBoundary,
    Feature,
    FixedItemSource,
    FixedPatternFormatter,
    FrameControl,
    GridColumn,
    GridRow,
    ImageControl,
    LabelControl,
    LayoutAxis,
    LayoutRoot,
    MeasureContext,
    MenuEntry,
    SceneMenuStripControl,
    NotificationCenter,
    NotificationPanelControl,
    NotificationRecord,
    NumericFormatter,
    ObservableDict,
    ObservableList,
    ObservableValue,
    OverlayPanelControl,
    PanelControl,
    PatternFormatter,
    RichLabelControl,
    Router,
    ScrollbarControl,
    ScrollViewControl,
    ScopedTheme,
    ScopedThemeManager,
    SelectionMode,
    SelectionModel,
    SettingsRegistry,
    SplitterControl,
    StateMachine,
    TaskPanelControl,
    ThemeManager,
    ToastSeverity,
    ToggleControl,
    TooltipManager,
    CollectionView,
    CollectionViewQuery,
    ContextMenuHandle,
    ContextMenuManager,
    ContextMenuItem,
    DocumentModel,
    FormSchema,
    GridLayout,
    GridPlacement,
    GridTrack,
    InvalidationTracker,
    OverlayHandle,
    OverlayManager,
    PresentationModel,
    SchemaField,
    TransferData,
    TransferManager,


)


class MainDemoFeature(Feature):
    """Build the demo's main scene surface and dock controls."""

    HOST_REQUIREMENTS = {
        "build": (
            "app",
            "screen_rect",
            "font_roles",
            "TASK_PANEL_CONTROL_FONT_ROLE",
            "SCREEN_TITLE_FONT_ROLE",
            "go_to_main",
            "go_to_control_showcase",
            "set_life_window_visible",
            "set_mandel_window_visible",
            "set_system_window_visible",
            "action_registry",
        )
    }

    def __init__(self) -> None:
        super().__init__("main_demo", scene_name="main")

    def build(self, host) -> None:
        self._register_screen_font_roles(host)

        host.root = host.app.add(
            PanelControl("main_root", Rect(0, 0, host.screen_rect.width, host.screen_rect.height), draw_background=False),
            scene_name="main",
        )

        def _extra_entries() -> list[MenuEntry]:
            tools_items = host.action_registry.context_menu_items(category="Tools")
            if not tools_items:
                return []
            return [MenuEntry("Tools", tools_items)]

        scene_select = getattr(
            getattr(host, "scene_transitions", None),
            "go",
            getattr(host.app, "switch_scene", lambda _scene: None),
        )

        host.desktop_menu_bar = host.root.add(
            SceneMenuStripControl(
                "desktop_menu_bar",
                Rect(0, 0, host.screen_rect.width, 28),
                host.app,
                scene_name="main",
                scenes_shown=True,
                windows_shown=True,
                extra_entries_provider=_extra_entries,
                on_scene_selected=scene_select,
            )
        )
        host.screen_title = host.root.add(
            self._make_sized_title_label(host, "screen_title", "gui_do", 24, 36, fallback_size=(640, 96))
        )
        host.task_panel = host.app.add(
            TaskPanelControl(
                "task_panel",
                Rect(0, host.screen_rect.height - 50, host.screen_rect.width, 50),
                auto_hide=True,
                hidden_peek_pixels=6,
                animation_step_px=8,
                dock_bottom=True,
            ),
            scene_name="main",
        )

        host.app.layout.set_linear_properties(
            anchor=(16, host.screen_rect.height - 40),
            item_width=124,
            item_height=30,
            spacing=10,
            horizontal=True,
        )

        def _on_life_toggle(pushed: bool) -> None:
            host.set_life_window_visible(bool(pushed), from_toggle=True)

        def _on_mandel_toggle(pushed: bool) -> None:
            host.set_mandel_window_visible(bool(pushed), from_toggle=True)

        def _on_system_toggle(pushed: bool) -> None:
            host.set_system_window_visible(bool(pushed), from_toggle=True)

        def _open_notifications_panel() -> None:
            system_feature = getattr(host, "_system_feature", None)
            if system_feature is not None:
                system_feature.show_notifications_panel()

        host.exit_button = host.task_panel.add(
            ButtonControl(
                "exit",
                host.app.layout.linear(0),
                "Exit",
                lambda: setattr(host.app, "running", False),
                style="angle",
                font_role=host.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )
        host.showcase_button = host.task_panel.add(
            ButtonControl(
                "showcase",
                host.app.layout.linear(1),
                "Showcase",
                host.go_to_control_showcase,
                style="angle",
                font_role=host.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )
        host.life_toggle_window = host.task_panel.add(
            ToggleControl(
                "show_life",
                host.app.layout.linear(2),
                "Life",
                "Life",
                pushed=False,
                on_toggle=_on_life_toggle,
                style="round",
                font_role=host.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )
        host.mandel_toggle_window = host.task_panel.add(
            ToggleControl(
                "show_mandel",
                host.app.layout.linear(3),
                "Mandelbrot",
                "Mandelbrot",
                pushed=False,
                on_toggle=_on_mandel_toggle,
                style="round",
                font_role=host.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )
        host.system_toggle_window = host.task_panel.add(
            ToggleControl(
                "show_system",
                host.app.layout.linear(4),
                "System",
                "System",
                pushed=False,
                on_toggle=_on_system_toggle,
                style="round",
                font_role=host.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )
        host.inbox_button = host.task_panel.add(
            ButtonControl(
                "show_notifications",
                host.app.layout.linear(5),
                "Inbox",
                _open_notifications_panel,
                style="angle",
                font_role=host.TASK_PANEL_CONTROL_FONT_ROLE,
            )
        )

        right_margin = 16
        right_gap = 10
        system_w = host.system_toggle_window.rect.width
        inbox_w = host.inbox_button.rect.width
        y = host.task_panel.rect.top + 10
        inbox_x = host.task_panel.rect.right - right_margin - inbox_w
        system_x = inbox_x - right_gap - system_w
        host.system_toggle_window.rect.topleft = (system_x, y)
        host.inbox_button.rect.topleft = (inbox_x, y)

        host._main_tooltip_manager = TooltipManager(default_delay_ms=500)
        host._main_tooltip_manager.register(host.exit_button, "Exit the application")
        host._main_tooltip_manager.register(host.showcase_button, "Open the control showcase scene")
        host._main_tooltip_manager.register(host.life_toggle_window, "Toggle the Life simulation window")
        host._main_tooltip_manager.register(host.mandel_toggle_window, "Toggle the Mandelbrot fractal window")
        host._main_tooltip_manager.register(host.system_toggle_window, "Toggle the system utilities window")
        host._main_tooltip_manager.register(host.inbox_button, "Open the notification inbox panel")

        self._build_main_scene_controls_dock(host)
        host.app.tile_windows()

    def _build_main_scene_extra_systems(self, host, scroll_stack, content_w, row_lbl_h, row_val_h, item_gap) -> None:
        """Add all public-API systems not yet demonstrated in the dock scroll area."""
        fn = host.TASK_PANEL_CONTROL_FONT_ROLE
        section_gap = item_gap * 2

        # ── Observable collections ──────────────────────────────────────
        host._main_obs_list = ObservableList(["Alpha", "Beta", "Gamma"])
        _obs_list_val = LabelControl(
            "main_obs_list_val", Rect(0, 0, content_w, row_val_h),
            "Items [3]: Alpha, Beta, Gamma", align="left",
        )
        _obs_list_val.font_role = fn

        def _on_obs_list_change(_ch):
            items = list(host._main_obs_list)
            _obs_list_val.text = f"Items [{len(items)}]: {', '.join(str(v) for v in items[:6])}"

        host._main_obs_list.subscribe(_on_obs_list_change)
        scroll_stack.add_labeled_value(
            LabelControl("main_obs_list_lbl", Rect(0, 0, content_w, row_lbl_h), "ObservableList + ChangeKind + CollectionChange", align="left"),
            _obs_list_val, x=0, label_gap=4, item_gap=4,
        )
        scroll_stack.add(
            ButtonControl(
                "main_obs_list_btn", Rect(0, 0, 110, 26), "Append Item",
                lambda: host._main_obs_list.append(f"Item {len(host._main_obs_list) + 1}"),
                font_role=fn,
            ),
            gap_after=item_gap, focusable=True,
        )

        host._main_obs_dict = ObservableDict({"color": "#4080ff", "opacity": "1.0"})
        _obs_dict_val = LabelControl(
            "main_obs_dict_val", Rect(0, 0, content_w, row_val_h),
            "Keys: color, opacity", align="left",
        )
        _obs_dict_val.font_role = fn
        _dict_counter = [2]

        def _on_obs_dict_change(_ch):
            _obs_dict_val.text = f"Keys: {', '.join(host._main_obs_dict.keys())}"

        host._main_obs_dict.subscribe(_on_obs_dict_change)

        def _toggle_dict_key():
            key = f"entry_{_dict_counter[0]}"
            if key in host._main_obs_dict:
                del host._main_obs_dict[key]
            else:
                host._main_obs_dict[key] = f"val{_dict_counter[0]}"
                _dict_counter[0] += 1

        scroll_stack.add_labeled_value(
            LabelControl("main_obs_dict_lbl", Rect(0, 0, content_w, row_lbl_h), "ObservableDict", align="left"),
            _obs_dict_val, x=0, label_gap=4, item_gap=4,
        )
        scroll_stack.add(
            ButtonControl("main_obs_dict_btn", Rect(0, 0, 110, 26), "Toggle Key", _toggle_dict_key, font_role=fn),
            gap_after=item_gap, focusable=True,
        )

        # Binding + BindingGroup
        host._main_bind_src = ObservableValue(False)
        _bind_toggle = ToggleControl(
            "main_bind_toggle", Rect(0, 0, 80, 26), "On", "Off",
            pushed=False, font_role=fn,
        )
        _bind_label_val = LabelControl(
            "main_bind_label_val", Rect(0, 0, content_w, row_val_h), "Bound: Off", align="left",
        )
        _bind_label_val.font_role = fn

        def _on_bind_toggle(pushed: bool) -> None:
            host._main_bind_src.value = bool(pushed)

        _bind_toggle.on_toggle = _on_bind_toggle
        host._main_binding = Binding(
            host._main_bind_src, _bind_label_val, "text",
            mode="one_way",
            to_control=lambda v: "Bound: On" if v else "Bound: Off",
        )
        host._main_binding_group = BindingGroup()
        host._main_binding_group.add(host._main_binding)
        scroll_stack.add_labeled_value(
            LabelControl("main_binding_lbl", Rect(0, 0, content_w, row_lbl_h), "Binding + BindingGroup  (toggle → label)", align="left"),
            _bind_toggle, x=0, label_gap=4, item_gap=4, focusable_value=True,
        )
        scroll_stack.add(_bind_label_val, gap_after=section_gap)

        # ── Command history ──────────────────────────────────────────────
        _counter = [0]
        _cmd_label_val = LabelControl(
            "main_cmd_val", Rect(0, 0, content_w, row_val_h),
            "Value: 0  undo: 0  redo: 0", align="left",
        )
        _cmd_label_val.font_role = fn
        host._main_cmd_history = CommandHistory(max_size=20)

        class _IncrCmd:
            @property
            def description(self) -> str:
                return "Increment"

            def execute(self) -> None:
                _counter[0] += 1

            def undo(self) -> None:
                _counter[0] -= 1

        def _update_cmd_label() -> None:
            h = host._main_cmd_history
            _cmd_label_val.text = f"Value: {_counter[0]}  undo: {h.undo_stack_size}  redo: {h.redo_stack_size}"

        def _do_incr() -> None:
            host._main_cmd_history.push(_IncrCmd())
            _update_cmd_label()

        def _do_undo() -> None:
            host._main_cmd_history.undo()
            _update_cmd_label()

        def _do_redo() -> None:
            host._main_cmd_history.redo()
            _update_cmd_label()

        scroll_stack.add_labeled_value(
            LabelControl("main_cmd_lbl", Rect(0, 0, content_w, row_lbl_h), "CommandHistory + Command + CommandTransaction", align="left"),
            _cmd_label_val, x=0, label_gap=4, item_gap=4,
        )
        _cmd_btn_y = scroll_stack.y
        scroll_stack.add(
            ButtonControl("main_cmd_incr_btn", Rect(0, 0, 52, 26), "+1", _do_incr, font_role=fn),
            x=0, y=_cmd_btn_y, focusable=True,
        )
        scroll_stack.add(
            ButtonControl("main_cmd_undo_btn", Rect(0, 0, 58, 26), "Undo", _do_undo, font_role=fn),
            x=60, y=_cmd_btn_y, focusable=True,
        )
        scroll_stack.add(
            ButtonControl("main_cmd_redo_btn", Rect(0, 0, 58, 26), "Redo", _do_redo, font_role=fn),
            x=126, y=_cmd_btn_y, focusable=True,
        )
        scroll_stack.advance(30 + item_gap)

        # StateMachine
        _sm_states = ["Idle", "Running", "Paused", "Done"]
        host._main_state_machine = StateMachine("Idle")
        for _st in _sm_states[1:]:
            host._main_state_machine.add_state(_st)
        for _i in range(len(_sm_states)):
            host._main_state_machine.add_transition(
                _sm_states[_i], _sm_states[(_i + 1) % len(_sm_states)], trigger="next"
            )
        _sm_val = LabelControl("main_sm_val", Rect(0, 0, content_w, row_val_h), "State: Idle", align="left")
        _sm_val.font_role = fn
        host._main_state_machine.current.subscribe(lambda s: setattr(_sm_val, "text", f"State: {s}"))
        scroll_stack.add_labeled_value(
            LabelControl("main_sm_lbl", Rect(0, 0, content_w, row_lbl_h), "StateMachine  (Idle → Running → Paused → Done → …)", align="left"),
            _sm_val, x=0, label_gap=4, item_gap=4,
        )
        scroll_stack.add(
            ButtonControl(
                "main_sm_btn", Rect(0, 0, 110, 26), "Next State",
                lambda: host._main_state_machine.trigger("next"), font_role=fn,
            ),
            gap_after=item_gap, focusable=True,
        )

        # Router + RouteEntry
        host._main_router = Router()
        host._main_router.register("/dashboard", "main")
        host._main_router.register("/settings", "settings")
        host._main_router.register("/editor", "editor")
        host._main_router.push("/dashboard")
        _router_val = LabelControl(
            "main_router_val", Rect(0, 0, content_w, row_val_h),
            "Route: /dashboard  depth: 1", align="left",
        )
        _router_val.font_role = fn
        _router_routes = ["/dashboard", "/settings", "/editor"]

        def _push_route() -> None:
            current = host._main_router.current_route or "/dashboard"
            idx = _router_routes.index(current) if current in _router_routes else 0
            host._main_router.push(_router_routes[(idx + 1) % len(_router_routes)])
            r = host._main_router
            _router_val.text = f"Route: {r.current_route}  depth: {len(r._history)}"

        def _pop_route() -> None:
            host._main_router.pop()
            r = host._main_router
            _router_val.text = f"Route: {r.current_route}  depth: {len(r._history)}"

        scroll_stack.add_labeled_value(
            LabelControl("main_router_lbl", Rect(0, 0, content_w, row_lbl_h), "Router + RouteEntry", align="left"),
            _router_val, x=0, label_gap=4, item_gap=4,
        )
        _router_btn_y = scroll_stack.y
        scroll_stack.add(
            ButtonControl("main_router_push_btn", Rect(0, 0, 90, 26), "Push Route", _push_route, font_role=fn),
            x=0, y=_router_btn_y, focusable=True,
        )
        scroll_stack.add(
            ButtonControl("main_router_pop_btn", Rect(0, 0, 80, 26), "Pop Route", _pop_route, font_role=fn),
            x=98, y=_router_btn_y, focusable=True,
        )
        scroll_stack.advance(30 + item_gap)

        # FormModel + FormField + ValidationRule + FieldError
        scroll_stack.add_labeled_value(
            LabelControl("main_form_lbl", Rect(0, 0, content_w, row_lbl_h), "FormModel + FormField + ValidationRule + FieldError", align="left"),
            LabelControl(
                "main_form_val", Rect(0, 0, content_w, row_val_h),
                "form.add_field('name', '')  form.validate_all() -> list[FieldError]",
                align="left",
            ),
            x=0, label_gap=4, item_gap=item_gap,
        )

        # SettingsRegistry + SettingDescriptor
        host._main_settings = SettingsRegistry()
        _vol_obs = host._main_settings.declare("audio", "volume", 0.8, label="Master Volume")
        _dark_obs = host._main_settings.declare("ui", "dark_mode", True, label="Dark Mode")
        _fps_obs = host._main_settings.declare("render", "fps_cap", 120, label="FPS Cap")
        scroll_stack.add_labeled_value(
            LabelControl("main_settings_lbl", Rect(0, 0, content_w, row_lbl_h), "SettingsRegistry + SettingDescriptor", align="left"),
            LabelControl(
                "main_settings_val", Rect(0, 0, content_w, row_val_h),
                f"audio.volume={_vol_obs.value}  ui.dark_mode={_dark_obs.value}  render.fps_cap={_fps_obs.value}",
                align="left",
            ),
            x=0, label_gap=4, item_gap=section_gap,
        )

        # ── Scheduling ──────────────────────────────────────────────────
        _tick_counter = [0]
        _timer_val = LabelControl(
            "main_timer_val", Rect(0, 0, content_w, row_val_h), "Ticks: 0", align="left",
        )
        _timer_val.font_role = fn

        def _on_tick() -> None:
            _tick_counter[0] += 1
            _timer_val.text = f"Ticks: {_tick_counter[0]}"

        host.app.timers.add_timer("main_dock_tick", 1.0, _on_tick)
        scroll_stack.add_labeled_value(
            LabelControl("main_timers_lbl", Rect(0, 0, content_w, row_lbl_h), "Timers  (fires every 1 s)", align="left"),
            _timer_val, x=0, label_gap=4, item_gap=item_gap,
        )

        # ToastManager + ToastHandle
        scroll_stack.add_labeled_value(
            LabelControl("main_toast_lbl", Rect(0, 0, content_w, row_lbl_h), "ToastManager + ToastHandle", align="left"),
            LabelControl(
                "main_toast_desc", Rect(0, 0, content_w, row_val_h),
                "app.toasts.show(message, title, severity, duration_seconds) -> ToastHandle",
                align="left",
            ),
            x=0, label_gap=4, item_gap=4,
        )
        _toast_btn_y = scroll_stack.y
        scroll_stack.add(
            ButtonControl(
                "main_toast_info_btn", Rect(0, 0, 110, 26), "Info Toast",
                lambda: host.app.toasts.show(
                    "Demo task completed", title="Scheduler",
                    severity=ToastSeverity.INFO, duration_seconds=3.0,
                ),
                font_role=fn,
            ),
            x=0, y=_toast_btn_y, focusable=True,
        )
        scroll_stack.add(
            ButtonControl(
                "main_toast_warn_btn", Rect(0, 0, 130, 26), "Warning Toast",
                lambda: host.app.toasts.show(
                    "Low memory detected", title="System",
                    severity=ToastSeverity.WARNING, duration_seconds=4.0,
                ),
                font_role=fn,
            ),
            x=118, y=_toast_btn_y, focusable=True,
        )
        scroll_stack.advance(30 + item_gap)

        # DialogManager + DialogHandle
        scroll_stack.add_labeled_value(
            LabelControl("main_dialog_lbl", Rect(0, 0, content_w, row_lbl_h), "DialogManager + DialogHandle", align="left"),
            LabelControl(
                "main_dialog_desc", Rect(0, 0, content_w, row_val_h),
                "app.dialogs.show_alert/confirm/prompt() returns DialogHandle; handle.close() dismisses",
                align="left",
            ),
            x=0, label_gap=4, item_gap=4,
        )
        _dlg_btn_y = scroll_stack.y
        scroll_stack.add(
            ButtonControl(
                "main_dlg_alert_btn", Rect(0, 0, 76, 26), "Alert",
                lambda: host.app.dialogs.show_alert("gui_do", "Alert from DialogManager"),
                font_role=fn,
            ),
            x=0, y=_dlg_btn_y, focusable=True,
        )
        scroll_stack.add(
            ButtonControl(
                "main_dlg_confirm_btn", Rect(0, 0, 88, 26), "Confirm",
                lambda: host.app.dialogs.show_confirm("gui_do", "Proceed?", on_confirm=lambda: None),
                font_role=fn,
            ),
            x=84, y=_dlg_btn_y, focusable=True,
        )
        scroll_stack.advance(30 + section_gap)

        # ── Animation ───────────────────────────────────────────────────
        scroll_stack.add_labeled_value(
            LabelControl("main_tween_lbl", Rect(0, 0, content_w, row_lbl_h), "TweenHandle + Easing", align="left"),
            LabelControl(
                "main_tween_val", Rect(0, 0, content_w, row_val_h),
                "handle = tweens.tween(target, attr, end, secs, easing=Easing.EASE_IN_OUT)  handle.cancel()",
                align="left",
            ),
            x=0, label_gap=4, item_gap=item_gap,
        )
        scroll_stack.add_labeled_value(
            LabelControl("main_lanim_lbl", Rect(0, 0, content_w, row_lbl_h), "LayoutAnimator", align="left"),
            LabelControl(
                "main_lanim_val", Rect(0, 0, content_w, row_val_h),
                "LayoutAnimator(tweens, duration, easing)  intercepts layout reflows and tweens children",
                align="left",
            ),
            x=0, label_gap=4, item_gap=section_gap,
        )

        # ── Input ───────────────────────────────────────────────────────
        scroll_stack.add_labeled_value(
            LabelControl("main_gesture_lbl", Rect(0, 0, content_w, row_lbl_h), "GestureRecognizer", align="left"),
            LabelControl(
                "main_gesture_val", Rect(0, 0, content_w, row_val_h),
                "GestureRecognizer(on_double_click, on_long_press, on_swipe)  .process_event(event)",
                align="left",
            ),
            x=0, label_gap=4, item_gap=item_gap,
        )
        scroll_stack.add_labeled_value(
            LabelControl("main_rate_lbl", Rect(0, 0, content_w, row_lbl_h), "Debouncer + Throttler", align="left"),
            LabelControl(
                "main_rate_val", Rect(0, 0, content_w, row_val_h),
                "Debouncer(delay_ms, callback, timers)  Throttler(interval_ms, callback)",
                align="left",
            ),
            x=0, label_gap=4, item_gap=item_gap,
        )
        scroll_stack.add_labeled_value(
            LabelControl("main_chord_lbl", Rect(0, 0, content_w, row_lbl_h), "KeyChordManager + KeyChord + ChordStep", align="left"),
            LabelControl(
                "main_chord_val", Rect(0, 0, content_w, row_val_h),
                "KeyChordManager(actions, timers)  .bind(KeyChord([ChordStep(K_k, CTRL), ChordStep(K_c, CTRL)]), action)",
                align="left",
            ),
            x=0, label_gap=4, item_gap=section_gap,
        )

        # ── Services ────────────────────────────────────────────────────
        _ = ErrorBoundary  # imported; see tests/test_error_handling_runtime.py for full usage
        scroll_stack.add_labeled_value(
            LabelControl("main_eb_lbl", Rect(0, 0, content_w, row_lbl_h), "ErrorBoundary  (wraps child UiNode)", align="left"),
            LabelControl(
                "main_eb_val", Rect(0, 0, content_w, row_val_h),
                "ErrorBoundary(child=ctrl, on_error=cb, error_text='...')  .has_error  .recover()",
                align="left",
            ),
            x=0, label_gap=4, item_gap=item_gap,
        )
        scroll_stack.add_labeled_value(
            LabelControl("main_resize_lbl", Rect(0, 0, content_w, row_lbl_h), "ResizeManager", align="left"),
            LabelControl(
                "main_resize_val", Rect(0, 0, content_w, row_val_h),
                "ResizeManager(initial_size, event_bus)  .on_resize(callback)  .notify_resize(w, h)",
                align="left",
            ),
            x=0, label_gap=4, item_gap=item_gap,
        )
        scroll_stack.add_labeled_value(
            LabelControl("main_drag_lbl", Rect(0, 0, content_w, row_lbl_h), "DragDropManager + DragPayload", align="left"),
            LabelControl(
                "main_drag_val", Rect(0, 0, content_w, row_val_h),
                "app.drag_drop.begin_drag(DragPayload(kind='file', data={...}))  resolved via on_drop callback",
                align="left",
            ),
            x=0, label_gap=4, item_gap=item_gap,
        )
        scroll_stack.add_labeled_value(
            LabelControl("main_constraint_lbl", Rect(0, 0, content_w, row_lbl_h), "ConstraintLayout + AnchorConstraint", align="left"),
            LabelControl(
                "main_constraint_val", Rect(0, 0, content_w, row_val_h),
                "ConstraintLayout()  .add(AnchorConstraint(node, left=12, bottom=12, width=100, height=28))  .apply(rect)",
                align="left",
            ),
            x=0, label_gap=4, item_gap=section_gap,
        )

        # ── Theme ────────────────────────────────────────────────────────
        host._main_theme_manager = ThemeManager()
        host._main_theme_manager.register_theme("contrast", {"primary": (255, 220, 0), "surface": (10, 10, 10)})
        _primary_tok = host._main_theme_manager.token("primary")
        scroll_stack.add_labeled_value(
            LabelControl("main_theme_mgr_lbl", Rect(0, 0, content_w, row_lbl_h), "ThemeManager + DesignTokens", align="left"),
            LabelControl(
                "main_theme_mgr_val", Rect(0, 0, content_w, row_val_h),
                f"Active: '{host._main_theme_manager.active_theme.value}'  primary={_primary_tok}  .switch('contrast') hot-swaps tokens",
                align="left",
            ),
            x=0, label_gap=4, item_gap=section_gap,
        )

        # ── Feature types ────────────────────────────────────────────────
        scroll_stack.add_labeled_value(
            LabelControl("main_dfeat_lbl", Rect(0, 0, content_w, row_lbl_h), "DirectFeature + LogicFeature + FeatureMessage", align="left"),
            LabelControl(
                "main_dfeat_val", Rect(0, 0, content_w, row_val_h),
                "DirectFeature: owns draw/update hooks; LogicFeature: pure logic provider; RoutedFeature: message-routed",
                align="left",
            ),
            x=0, label_gap=4, item_gap=section_gap,
        )

        # ── FixedPatternFormatter ─────────────────────────────────────────
        _fpp_fmt = FixedPatternFormatter("#####-####")
        _fpp_input = _fpp_fmt.create_text_input(
            "main_fixed_pattern_input",
            Rect(0, 0, 200, 30),
            raw_value="941010001",
            placeholder="#####-####",
            font_role=fn,
        )
        scroll_stack.add_labeled_value(
            LabelControl("main_fpp_lbl", Rect(0, 0, content_w, row_lbl_h), "FixedPatternFormatter  (ZIP+4 postal code)", align="left"),
            _fpp_input, x=0, label_gap=4, item_gap=item_gap, focusable_value=True,
        )

        # ── GridLayout ──────────────────────────────────────────────────
        _grid_layout = GridLayout(
            row_tracks=[GridTrack("auto"), GridTrack("auto")],
            col_tracks=[GridTrack("1fr"), GridTrack("2fr"), GridTrack("1fr")],
            gap=8,
        )
        _grid_placement_header = GridPlacement(row=0, col=0, colspan=3)
        _grid_placement_left   = GridPlacement(row=1, col=0)
        _grid_placement_center = GridPlacement(row=1, col=1)
        _grid_placement_right  = GridPlacement(row=1, col=2)
        scroll_stack.add_labeled_value(
            LabelControl("main_grid_lbl", Rect(0, 0, content_w, row_lbl_h), "GridLayout + GridTrack + GridPlacement", align="left"),
            LabelControl(
                "main_grid_val", Rect(0, 0, content_w, row_val_h),
                "2×3 grid (auto/auto rows, 1fr/2fr/1fr cols, gap=8)  placements: header(0,0 span=3)  left(1,0)  center(1,1)  right(1,2)",
                align="left",
            ),
            x=0, label_gap=4, item_gap=section_gap,
        )

        # ── FormSchema ──────────────────────────────────────────────────
        _form_schema = FormSchema([
            SchemaField("name",    default="",  label="Name",    required=True),
            SchemaField("email",   default="",  label="Email",   required=True),
            SchemaField("company", default="",  label="Company"),
        ])
        _required_count = sum(1 for f in _form_schema.fields if f.required)
        scroll_stack.add_labeled_value(
            LabelControl("main_fschema_lbl", Rect(0, 0, content_w, row_lbl_h), "FormSchema + SchemaField", align="left"),
            LabelControl(
                "main_fschema_val", Rect(0, 0, content_w, row_val_h),
                f"Profile schema: {len(_form_schema.fields)} fields  required={_required_count}  (name, email, company)",
                align="left",
            ),
            x=0, label_gap=4, item_gap=section_gap,
        )

        # ── DocumentModel ───────────────────────────────────────────────
        host._main_document = DocumentModel(
            "draft-001",
            content="# Meeting Notes\n- Agenda item 1\n- Follow-up tasks",
        )
        host._main_document.set_content("# Meeting Notes\n- Agenda item 1\n- Agenda item 2\n- Follow-up tasks")
        _doc_val_lbl = LabelControl(
            "main_doc_val", Rect(0, 0, content_w, row_val_h),
            f"id=draft-001  rev={host._main_document.revision}  dirty={host._main_document.is_dirty}",
            align="left",
        )
        _doc_val_lbl.font_role = fn
        scroll_stack.add_labeled_value(
            LabelControl("main_doc_lbl", Rect(0, 0, content_w, row_lbl_h), "DocumentModel", align="left"),
            _doc_val_lbl, x=0, label_gap=4, item_gap=4,
        )
        _doc_btn_y = scroll_stack.y
        scroll_stack.add(
            ButtonControl(
                "main_doc_save_btn", Rect(0, 0, 110, 26), "Mark Saved",
                lambda: (host._main_document.mark_saved() or setattr(
                    _doc_val_lbl, "text",
                    f"id=draft-001  rev={host._main_document.revision}  dirty={host._main_document.is_dirty}",
                )),
                font_role=fn,
            ),
            x=0, y=_doc_btn_y, focusable=True,
        )
        scroll_stack.advance(30 + section_gap)

        # ── TransferData + TransferManager ──────────────────────────────
        host._main_xfer_mgr = TransferManager()
        _xfer_init = TransferData(
            formats={"text/plain": "Scene layout snapshot", "application/json": '{"scene":"main","widgets":12}'},
            preferred_format="text/plain",
        )
        host._main_xfer_mgr.set_clipboard(_xfer_init)
        _xfer_val_lbl = LabelControl(
            "main_xfer_val", Rect(0, 0, content_w, row_val_h),
            f"formats: {_xfer_init.format_names()}  preferred: {_xfer_init.preferred_format}",
            align="left",
        )
        _xfer_val_lbl.font_role = fn
        scroll_stack.add_labeled_value(
            LabelControl("main_xfer_lbl", Rect(0, 0, content_w, row_lbl_h), "TransferData + TransferManager", align="left"),
            _xfer_val_lbl, x=0, label_gap=4, item_gap=4,
        )
        _xfer_btn_y = scroll_stack.y
        _xfer_counter = [0]

        def _do_copy_xfer() -> None:
            _xfer_counter[0] += 1
            td = TransferData(
                {"text/plain": f"Layout snapshot #{_xfer_counter[0]}"},
                preferred_format="text/plain",
            )
            host._main_xfer_mgr.set_clipboard(td)
            cb = host._main_xfer_mgr.get_clipboard()
            _xfer_val_lbl.text = f"Clipboard: {cb.get('text/plain') if cb else '(empty)'}"

        scroll_stack.add(
            ButtonControl("main_xfer_copy_btn", Rect(0, 0, 110, 26), "Copy Snapshot", _do_copy_xfer, font_role=fn),
            x=0, y=_xfer_btn_y, focusable=True,
        )
        scroll_stack.advance(30 + section_gap)

        # ── CollectionViewQuery + CollectionView ─────────────────────────
        _asset_names = ["backdrop.jpg", "cursor.png", "hand.png", "realize.png", "fonts.ttf", "config.json"]
        _cv_query = CollectionViewQuery(filters=[lambda x: not x.endswith(".json")])
        host._main_coll_view = CollectionView(_asset_names, query=_cv_query)
        _cv_items = host._main_coll_view.items
        scroll_stack.add_labeled_value(
            LabelControl("main_cv_lbl", Rect(0, 0, content_w, row_lbl_h), "CollectionViewQuery + CollectionView", align="left"),
            LabelControl(
                "main_cv_val", Rect(0, 0, content_w, row_val_h),
                f"Filtered (exclude .json): {len(_cv_items)} of {len(_asset_names)}  [{', '.join(_cv_items)}]",
                align="left",
            ),
            x=0, label_gap=4, item_gap=section_gap,
        )

        # ── InvalidationTracker ──────────────────────────────────────────
        host._main_invalidation = InvalidationTracker()
        host._main_invalidation.set_screen_size((host.screen_rect.width, host.screen_rect.height))
        host._main_invalidation.end_frame()
        host._main_invalidation.invalidate_rect(Rect(0, 0, 120, 80))
        host._main_invalidation.invalidate_rect(Rect(60, 40, 120, 80))
        _inv_merged = host._main_invalidation.merge_dirty_rects()
        scroll_stack.add_labeled_value(
            LabelControl("main_inv_lbl", Rect(0, 0, content_w, row_lbl_h), "InvalidationTracker", align="left"),
            LabelControl(
                "main_inv_val", Rect(0, 0, content_w, row_val_h),
                f"2 overlapping dirty rects merged → {len(_inv_merged)} region(s)  bounds={[f'{r.width}×{r.height}' for r in _inv_merged]}",
                align="left",
            ),
            x=0, label_gap=4, item_gap=section_gap,
        )

        # ── PresentationModel ────────────────────────────────────────────
        host._main_pres_obs = ObservableValue("Idle")
        host._main_pres_model = PresentationModel()
        _pres_val_lbl = LabelControl(
            "main_pres_val", Rect(0, 0, content_w, row_val_h),
            "State: Idle", align="left",
        )
        _pres_val_lbl.font_role = fn
        host._main_pres_model.bind(host._main_pres_obs, lambda v: setattr(_pres_val_lbl, "text", f"State: {v}"))
        scroll_stack.add_labeled_value(
            LabelControl("main_pres_lbl", Rect(0, 0, content_w, row_lbl_h), "PresentationModel  (bind observable → label)", align="left"),
            _pres_val_lbl, x=0, label_gap=4, item_gap=4,
        )
        _pres_btn_y = scroll_stack.y
        _pres_states = ["Idle", "Loading", "Ready", "Error"]
        _pres_idx = [0]

        def _cycle_pres_state() -> None:
            _pres_idx[0] = (_pres_idx[0] + 1) % len(_pres_states)
            host._main_pres_obs.value = _pres_states[_pres_idx[0]]

        scroll_stack.add(
            ButtonControl("main_pres_cycle_btn", Rect(0, 0, 110, 26), "Cycle State", _cycle_pres_state, font_role=fn),
            x=0, y=_pres_btn_y, focusable=True,
        )
        scroll_stack.advance(30 + section_gap)

        # ── OverlayManager + OverlayHandle ───────────────────────────────
        # app.overlay is the app's OverlayManager; show() renders above the scene.
        _overlay_status_lbl = LabelControl(
            "main_overlay_status", Rect(0, 0, content_w, row_val_h),
            "No overlay active", align="left",
        )
        _overlay_status_lbl.font_role = fn
        _overlay_handle_ref: list = [None]
        _overlay_panel_inner = OverlayPanelControl(
            "main_overlay_mgr_panel",
            Rect(0, 0, 180, 64),
            draw_background=True,
        )
        for _oi, _ot in enumerate(("Overlay item A", "Overlay item B")):
            _ol = LabelControl(f"main_overlay_inner_{_oi}", Rect(0, 0, 164, 20), _ot, align="left")
            _ol.font_role = fn
            _overlay_panel_inner.add_at(_ol, rel_x=8, rel_y=6 + _oi * 24)

        def _toggle_overlay() -> None:
            h = _overlay_handle_ref[0]
            if h is not None and h.is_open:
                h.dismiss()
                _overlay_handle_ref[0] = None
                _overlay_status_lbl.text = "Overlay dismissed"
            else:
                _overlay_handle_ref[0] = host.app.overlay.show(
                    "main_dock_status_overlay",
                    _overlay_panel_inner,
                    dismiss_on_outside_click=True,
                    on_dismiss=lambda: setattr(_overlay_status_lbl, "text", "Overlay dismissed (auto)"),
                )
                _overlay_status_lbl.text = f"Overlay open  count={host.app.overlay.overlay_count}"

        scroll_stack.add_labeled_value(
            LabelControl("main_overlay_mgr_lbl", Rect(0, 0, content_w, row_lbl_h), "OverlayManager + OverlayHandle  (app.overlay)", align="left"),
            _overlay_status_lbl, x=0, label_gap=4, item_gap=4,
        )
        scroll_stack.add(
            ButtonControl("main_overlay_toggle_btn", Rect(0, 0, 130, 26), "Toggle Overlay", _toggle_overlay, font_role=fn),
            gap_after=section_gap, focusable=True,
        )

        # ── ContextMenuManager + ContextMenuHandle ───────────────────────
        host._main_ctx_menu_mgr = ContextMenuManager(host.app)
        _ctx_status_lbl = LabelControl(
            "main_ctx_status", Rect(0, 0, content_w, row_val_h),
            "No context menu shown", align="left",
        )
        _ctx_status_lbl.font_role = fn
        _ctx_items = [
            ContextMenuItem("Cut"),
            ContextMenuItem("Copy"),
            ContextMenuItem("Paste"),
            ContextMenuItem("Delete"),
        ]

        def _show_ctx_menu() -> None:
            host._main_ctx_menu_mgr.show(
                (host.screen_rect.centerx, host.screen_rect.centery),
                _ctx_items,
                on_dismiss=lambda: setattr(_ctx_status_lbl, "text", "Context menu dismissed"),
            )
            _ctx_status_lbl.text = f"Context menu open  has_menu={host._main_ctx_menu_mgr.has_menu}"

        scroll_stack.add_labeled_value(
            LabelControl("main_ctx_menu_lbl", Rect(0, 0, content_w, row_lbl_h), "ContextMenuManager + ContextMenuHandle", align="left"),
            _ctx_status_lbl, x=0, label_gap=4, item_gap=4,
        )
        scroll_stack.add(
            ButtonControl("main_ctx_menu_btn", Rect(0, 0, 140, 26), "Show Context Menu", _show_ctx_menu, font_role=fn),
            gap_after=section_gap, focusable=True,
        )

    def _register_screen_font_roles(self, host) -> None:
        for scene_name in ("main", "control_showcase"):
            host.font_roles.apply(host.app, scene_name=scene_name)

    def _make_sized_title_label(
        self,
        host,
        control_id: str,
        text: str,
        left: int,
        top: int,
        *,
        fallback_size: tuple[int, int],
    ) -> LabelControl:
        label = host.app.style_label(
            LabelControl(control_id, Rect(left, top, int(fallback_size[0]), int(fallback_size[1])), text),
            size=64,
            role=host.SCREEN_TITLE_FONT_ROLE,
        )
        if host.app.theme.fonts.has_role(label.font_role):
            font = host.app.theme.fonts.font_instance(label.font_role, size=label.font_size)
            label.rect.size = font.text_surface_size(label.text, shadow=True)
        return label

    def _build_main_scene_controls_dock(self, host) -> None:
        dock_width = 560
        dock_margin_right = 24
        dock_top = 112
        dock_left = host.screen_rect.right - dock_margin_right - dock_width
        dock_bottom = host.task_panel.rect.top - 18
        dock_height = max(320, dock_bottom - dock_top)
        header_h = 28
        scroll_margin = 12
        notification_panel_h = 188
        notification_label_h = 20
        notification_gap = 8
        preview_gap = 14
        overlay_h = 88

        host.main_controls_dock = host.root.add(
            PanelControl(
                "main_controls_dock",
                Rect(dock_left, dock_top, dock_width, dock_height),
                draw_background=True,
            )
        )

        dock_title = LabelControl(
            "main_controls_dock_title",
            Rect(dock_left + scroll_margin, dock_top + 10, dock_width - (scroll_margin * 2), header_h),
            "Main Scene Control Dock",
            align="left",
        )
        dock_title.font_role = host.TASK_PANEL_CONTROL_FONT_ROLE
        host.main_controls_dock.add(dock_title)

        scroll_top = dock_top + header_h + 18
        fixed_preview_h = notification_label_h + notification_gap + notification_panel_h
        scroll_bottom = dock_top + dock_height - overlay_h - fixed_preview_h - (preview_gap * 2)
        scroll_rect = Rect(
            dock_left + scroll_margin,
            scroll_top,
            dock_width - (scroll_margin * 2),
            max(160, scroll_bottom - scroll_top),
        )
        host.main_controls_scroll = host.main_controls_dock.add(
            ScrollViewControl(
                "main_controls_scroll",
                scroll_rect,
                content_width=scroll_rect.width - 14,
                content_height=1050,
                scroll_y=True,
            )
        )
        host.main_controls_scroll.set_tab_index(-1)

        content_w = scroll_rect.width - 24
        scroll_stack = host.app.compose_scroll_stack(host.main_controls_scroll)
        y = 0

        def add_scroll_child(control, x: int, y_pos: int, *, focusable: bool = False) -> None:
            scroll_stack.add(control, x=x, y=y_pos, focusable=focusable)

        add_scroll_child(
            RichLabelControl(
                "main_controls_intro",
                Rect(0, 0, content_w, 68),
                text="This dock integrates the remaining gui_do controls directly into the main scene using concrete utility-style samples.",
                font_role=host.TASK_PANEL_CONTROL_FONT_ROLE,
            ),
            0,
            y,
        )
        y += 82

        add_scroll_child(LabelControl("main_controls_nav_label", Rect(0, 0, 180, 20), "Arrow Pad", align="left"), 0, y)
        arrow_y = y + 24
        arrow_size = 34
        arrow_gap = 8
        add_scroll_child(ArrowBoxControl("main_arrow_up", Rect(0, 0, arrow_size, arrow_size), 90), 0, arrow_y)
        add_scroll_child(ArrowBoxControl("main_arrow_down", Rect(0, 0, arrow_size, arrow_size), 270), arrow_size + arrow_gap, arrow_y)
        add_scroll_child(ArrowBoxControl("main_arrow_left", Rect(0, 0, arrow_size, arrow_size), 180), (arrow_size + arrow_gap) * 2, arrow_y)
        add_scroll_child(ArrowBoxControl("main_arrow_right", Rect(0, 0, arrow_size, arrow_size), 0), (arrow_size + arrow_gap) * 3, arrow_y)
        y = arrow_y + arrow_size + 22

        add_scroll_child(LabelControl("main_controls_group_label", Rect(0, 0, 180, 20), "View Mode", align="left"), 0, y)
        group_y = y + 24
        group_w = 104
        add_scroll_child(ButtonGroupControl("main_group_overview", Rect(0, 0, group_w, 28), "main_scene_mode", "Overview", selected=True, font_role=host.TASK_PANEL_CONTROL_FONT_ROLE), 0, group_y)
        add_scroll_child(ButtonGroupControl("main_group_logs", Rect(0, 0, group_w, 28), "main_scene_mode", "Logs", font_role=host.TASK_PANEL_CONTROL_FONT_ROLE), group_w + 8, group_y)
        add_scroll_child(ButtonGroupControl("main_group_assets", Rect(0, 0, group_w, 28), "main_scene_mode", "Assets", font_role=host.TASK_PANEL_CONTROL_FONT_ROLE), (group_w + 8) * 2, group_y)
        y = group_y + 44

        add_scroll_child(LabelControl("main_controls_dropdown_label", Rect(0, 0, 220, 20), "Scene Preset", align="left"), 0, y)
        add_scroll_child(
            DropdownControl(
                "main_scene_preset_dropdown",
                Rect(0, 0, 220, 30),
                [
                    DropdownOption("Presentation"),
                    DropdownOption("Diagnostics"),
                    DropdownOption("Quiet Mode"),
                ],
                selected_index=0,
                font_role=host.TASK_PANEL_CONTROL_FONT_ROLE,
            ),
            0,
            y + 24,
        )
        y += 68

        add_scroll_child(LabelControl("main_controls_splitter_label", Rect(0, 0, 220, 20), "Split Workspace", align="left"), 0, y)
        add_scroll_child(
            SplitterControl(
                "main_scene_splitter",
                Rect(0, 0, content_w, 48),
                axis=LayoutAxis.HORIZONTAL,
                ratio=0.62,
            ),
            0,
            y + 24,
        )
        y += 88

        add_scroll_child(LabelControl("main_controls_color_label", Rect(0, 0, 220, 20), "Accent Color", align="left"), 0, y)
        picker_y = y + 24
        add_scroll_child(
            ColorPickerControl(
                "main_scene_color_picker",
                Rect(0, 0, 220, 180),
                color=(64, 128, 255),
            ),
            0,
            picker_y,
        )
        add_scroll_child(
            ScrollbarControl(
                "main_scene_scrollbar",
                Rect(0, 0, 18, 180),
                LayoutAxis.VERTICAL,
                content_size=1000,
                viewport_size=220,
                offset=140,
                step=24,
            ),
            232,
            picker_y,
        )
        add_scroll_child(FrameControl("main_scene_preview_frame", Rect(0, 0, 120, 120), border_width=2), 276, picker_y)
        add_scroll_child(
            ImageControl(
                "main_scene_preview_image",
                Rect(0, 0, 104, 104),
                "demo_features/data/images/realize.png",
            ),
            284,
            picker_y + 8,
        )
        y = picker_y + 198

        add_scroll_child(LabelControl("main_controls_grid_label", Rect(0, 0, 220, 20), "Job Queue", align="left"), 0, y)
        add_scroll_child(
            DataGridControl(
                "main_scene_data_grid",
                Rect(0, 0, content_w, 176),
                columns=[
                    GridColumn("task", "Task", width=200),
                    GridColumn("state", "State", width=120),
                    GridColumn("owner", "Owner", width=120),
                ],
                rows=[
                    GridRow({"task": "Build main scene", "state": "Ready", "owner": "UI"}, row_id="job-1"),
                    GridRow({"task": "Tile windows", "state": "Queued", "owner": "Layout"}, row_id="job-2"),
                    GridRow({"task": "Publish toast", "state": "Done", "owner": "Events"}, row_id="job-3"),
                ],
                show_scrollbar=True,
            ),
            0,
            y + 24,
        )
        y += 216

        row_lbl_h = 20
        row_val_h = 22
        item_gap = 8
        scroll_stack.set_y(y)

        _num_fmt = NumericFormatter(decimals=2, thousands_sep=",")
        budget_input = _num_fmt.create_text_input(
            "main_budget_input",
            Rect(0, 0, 220, 30),
            raw_value="12500",
            placeholder="0.00",
            font_role=host.TASK_PANEL_CONTROL_FONT_ROLE,
        )
        scroll_stack.add_labeled_value(
            LabelControl("main_num_fmt_label", Rect(0, 0, content_w, row_lbl_h), "Budget USD (NumericFormatter)", align="left"),
            budget_input,
            x=0,
            label_gap=4,
            item_gap=item_gap,
            focusable_value=True,
        )

        _pat_fmt = PatternFormatter("###-###-####")
        phone_input = _pat_fmt.create_text_input(
            "main_phone_input",
            Rect(0, 0, 220, 30),
            raw_value="5551234567",
            placeholder="###-###-####",
            font_role=host.TASK_PANEL_CONTROL_FONT_ROLE,
        )
        scroll_stack.add_labeled_value(
            LabelControl("main_phone_label", Rect(0, 0, content_w, row_lbl_h), "Phone (PatternFormatter)", align="left"),
            phone_input,
            x=0,
            label_gap=4,
            item_gap=item_gap,
            focusable_value=True,
        )

        host._main_sel_model = SelectionModel(mode=SelectionMode.MULTI, item_count=4)
        host._main_sel_model.select(0)
        host._main_sel_model.select(2)
        scroll_stack.add_labeled_value(
            LabelControl("main_sel_label", Rect(0, 0, content_w, row_lbl_h), "Selection Model (MULTI)", align="left"),
            LabelControl(
                "main_sel_value",
                Rect(0, 0, content_w, row_val_h),
                f"Selected: {sorted(host._main_sel_model.selected_indices)}",
                align="left",
            ),
            x=0,
            label_gap=4,
            item_gap=item_gap,
        )

        host._main_asset_source = FixedItemSource(["backdrop.jpg", "cursor.png", "hand.png", "realize.png"])
        scroll_stack.add(
            LabelControl("main_src_label", Rect(0, 0, content_w, row_lbl_h), "Asset Library (FixedItemSource)", align="left"),
            x=0,
            gap_after=4,
        )
        for idx in range(host._main_asset_source.item_count()):
            scroll_stack.add(
                LabelControl(
                    f"main_src_item_{idx}",
                    Rect(0, 0, content_w - 12, row_val_h),
                    f"  {host._main_asset_source.item_at(idx)}",
                    align="left",
                ),
                x=12,
            )
        scroll_stack.advance(item_gap)

        host._main_canvas_viewport = CanvasViewport(
            content_size=(1280, 960),
            min_scale=0.1,
            max_scale=8.0,
        )
        viewport = host._main_canvas_viewport
        scroll_stack.add_labeled_value(
            LabelControl("main_vp_label", Rect(0, 0, content_w, row_lbl_h), "Canvas Viewport", align="left"),
            LabelControl(
                "main_vp_value",
                Rect(0, 0, content_w, row_val_h),
                f"Scale: {viewport.scale:.2f}  Content: {viewport.content_size[0]}x{viewport.content_size[1]}  Offset: {viewport.offset}",
                align="left",
            ),
            x=0,
            label_gap=4,
            item_gap=item_gap,
        )

        scroll_stack.add_labeled_value(
            LabelControl("main_adp_label", Rect(0, 0, content_w, row_lbl_h), "Async Data Provider", align="left"),
            LabelControl(
                "main_adp_value",
                Rect(0, 0, content_w, row_val_h),
                "State: IDLE  -  call .load(fn) to start a background fetch",
                align="left",
            ),
            x=0,
            label_gap=4,
            item_gap=item_gap,
        )

        host._main_scoped_theme_mgr = ScopedThemeManager({"color.accent": (64, 128, 255), "color.surface": (30, 30, 40)})
        host._main_scoped_theme_mgr.push(ScopedTheme({"color.accent": (255, 140, 0)}, name="dock-theme"))
        accent = host._main_scoped_theme_mgr.resolve("color.accent", (0, 0, 0))
        scroll_stack.add_labeled_value(
            LabelControl("main_theme_label", Rect(0, 0, content_w, row_lbl_h), "Scoped Theme", align="left"),
            LabelControl(
                "main_theme_value",
                Rect(0, 0, content_w, row_val_h),
                f"Depth: {host._main_scoped_theme_mgr.depth}  accent -> {accent}",
                align="left",
            ),
            x=0,
            label_gap=4,
            item_gap=item_gap,
        )

        scroll_stack.add_labeled_value(
            LabelControl("main_fscope_label", Rect(0, 0, content_w, row_lbl_h), "Focus Scope Manager", align="left"),
            LabelControl(
                "main_fscope_value",
                Rect(0, 0, content_w, row_val_h),
                "push(FocusScope(root, id)) -> Tab contained to modal subtree",
                align="left",
            ),
            x=0,
            label_gap=4,
            item_gap=item_gap,
        )

        class _DockLayout:
            def measure(self, ctx: MeasureContext) -> tuple:
                return (content_w, 200)

            def arrange(self, ctx: ArrangeContext) -> None:
                return None

        host._main_layout_root = LayoutRoot(layout=_DockLayout())
        host._main_layout_root.update(Rect(0, 0, content_w, 200))
        scroll_stack.add_labeled_value(
            LabelControl("main_layout_label", Rect(0, 0, content_w, row_lbl_h), "Layout Root (two-pass)", align="left"),
            LabelControl(
                "main_layout_value",
                Rect(0, 0, content_w, row_val_h),
                f"Preferred: {host._main_layout_root.preferred_size[0]}x{host._main_layout_root.preferred_size[1]}  dirty: {host._main_layout_root.is_dirty}",
                align="left",
            ),
            x=0,
            label_gap=4,
            item_gap=item_gap,
        )

        scroll_stack.add_labeled_value(
            LabelControl("main_trans_label", Rect(0, 0, content_w, row_lbl_h), "Transition Manager", align="left"),
            LabelControl(
                "main_trans_value",
                Rect(0, 0, content_w, row_val_h),
                "register(id, SHOW, TransitionSpec(attr, val, secs)) -> tween on state change",
                align="left",
            ),
            x=0,
            label_gap=4,
            item_gap=item_gap,
        )

        scroll_stack.add_labeled_value(
            LabelControl("main_tooltip_label", Rect(0, 0, content_w, row_lbl_h), "Tooltip Manager", align="left"),
            LabelControl(
                "main_tooltip_value",
                Rect(0, 0, content_w, row_val_h),
                "Delay: 500 ms  6 tooltips registered on task panel buttons",
                align="left",
            ),
            x=0,
            label_gap=4,
            item_gap=item_gap,
        )

        self._build_main_scene_extra_systems(host, scroll_stack, content_w, row_lbl_h, row_val_h, item_gap)

        y = scroll_stack.y

        host.main_controls_scroll.set_content_size(content_w, y + 12)

        preview_top = scroll_rect.bottom + preview_gap
        host.main_controls_notifications_label = LabelControl(
            "main_controls_notifications_label",
            Rect(dock_left + scroll_margin, preview_top, dock_width - (scroll_margin * 2), notification_label_h),
            "Inbox Preview",
            align="left",
        )
        host.main_controls_notifications_label.font_role = host.TASK_PANEL_CONTROL_FONT_ROLE
        host.main_controls_dock.add(host.main_controls_notifications_label)

        host.main_scene_notification_center = NotificationCenter(host.app.events, max_records=16)
        host.main_scene_notification_center.add(NotificationRecord("Main scene controls dock ready", title="Dock", severity=ToastSeverity.SUCCESS))
        host.main_scene_notification_center.add(NotificationRecord("Window tiling available", title="Workspace", severity=ToastSeverity.INFO))
        host.main_scene_notification_center.add(NotificationRecord("Two background tasks queued", title="Scheduler", severity=ToastSeverity.WARNING))
        host.main_scene_notification_panel = NotificationPanelControl(
            "main_scene_notification_panel",
            Rect(
                dock_left + scroll_margin,
                preview_top + notification_label_h + notification_gap,
                dock_width - (scroll_margin * 2),
                notification_panel_h,
            ),
            host.main_scene_notification_center,
        )
        host.main_scene_notification_panel.set_tab_index(-1)
        host.main_controls_dock.add(host.main_scene_notification_panel)

        overlay_top = dock_top + dock_height - overlay_h - 10
        host.main_scene_overlay_panel = host.main_controls_dock.add(
            OverlayPanelControl(
                "main_scene_overlay_panel",
                Rect(dock_left + 12, overlay_top, dock_width - 24, overlay_h),
                draw_background=True,
            )
        )
        overlay_items = (
            "Overlay HUD",
            "Pinned status card",
            "Quick glance summary",
        )
        for index, text in enumerate(overlay_items):
            label = LabelControl(
                f"main_scene_overlay_label_{index}",
                Rect(0, 0, host.main_scene_overlay_panel.rect.width - 20, 18),
                text,
                align="left",
            )
            label.font_role = host.TASK_PANEL_CONTROL_FONT_ROLE
            host.main_scene_overlay_panel.add_at(label, rel_x=10, rel_y=8 + index * 22)
