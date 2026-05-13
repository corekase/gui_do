"""Systems demo window integrated into the gui_do main scene."""

from __future__ import annotations

from dataclasses import dataclass

from pygame import Rect

from gui_do import (
    AnchoredWindowSpec,
    AsyncFieldValidator,
    AsyncFormValidator,
    ButtonControl,
    CollectionView,
    CollectionViewQuery,
    CommandHistory,
    DataCache,
    DropdownControl,
    DropdownOption,
    Feature,
    FormField,
    FrameTimer,
    LabelControl,
    ListViewControl,
    PanelControl,
    ScopedTheme,
    ScopedThemeManager,
    TabControl,
    TabItem,
    TextInputControl,
    ThemeManager,
    WindowControl,
    create_feature_presented_window,
)
from gui_do.controls.chrome.window_presenter import WindowPresenter
from gui_do.controls.data.list_view_control import ListItem


@dataclass(frozen=True)
class _BacklogItem:
    title: str
    status: str
    priority: int
    owner: str


class _StatusChangeCommand:
    def __init__(self, feature: "SystemsFeature", new_index: int, description: str) -> None:
        self._feature = feature
        self._new_index = int(new_index)
        self._old_index = int(feature._history_stage_index)
        self._description = str(description)

    @property
    def description(self) -> str:
        return self._description

    def execute(self) -> None:
        self._feature._history_stage_index = self._new_index
        self._feature._refresh_history_labels()

    def undo(self) -> None:
        self._feature._history_stage_index = self._old_index
        self._feature._refresh_history_labels()


class _SystemsPresenter(WindowPresenter):
    def __init__(self, feature: "SystemsFeature", host) -> None:
        super().__init__(None)
        self.feature = feature
        self.host = host

    def on_create(self) -> None:
        feature = self.feature
        content_rect = self.window.content_rect()
        tab_height = 36
        tab_gap = 8
        tabs = TabControl(
            "systems_tabs",
            Rect(content_rect.left, content_rect.top, content_rect.width, tab_height),
            items=[
                TabItem("data", "Data"),
                TabItem("validation", "Validation"),
                TabItem("history", "History"),
                TabItem("theme", "Theme"),
            ],
            selected_key=feature.active_tab_key,
            on_change=feature.set_active_tab,
            horizontal_padding=2,
        )
        tabs.set_accessibility(role="tablist", label="Systems demo categories")
        self.add_control(tabs)
        feature.systems_tabs = tabs

        panel_rect = Rect(
            content_rect.left,
            content_rect.top + tab_height + tab_gap,
            content_rect.width,
            max(1, content_rect.height - tab_height - tab_gap),
        )

        data_panel = feature.build_data_panel(panel_rect)
        validation_panel = feature.build_validation_panel(panel_rect)
        history_panel = feature.build_history_panel(panel_rect)
        theme_panel = feature.build_theme_panel(panel_rect)
        for panel in (data_panel, validation_panel, history_panel, theme_panel):
            self.add_control(panel)

        feature._tab_panels = {
            "data": data_panel,
            "validation": validation_panel,
            "history": history_panel,
            "theme": theme_panel,
        }
        feature.window = self.window
        feature.demo = self.host
        feature.set_active_tab(feature.active_tab_key)
        self.window.visible = False


class SystemsFeature(Feature):
    """Tabbed main-scene systems window with practical demo integrations."""

    HOST_REQUIREMENTS = {
        "build": ("app", "root", "screen_rect"),
        "on_update": ("app",),
    }

    def __init__(self) -> None:
        super().__init__("systems_demo", scene_name="main")
        self._frame_timer = FrameTimer()
        self.active_tab_key = "data"
        self.demo = None
        self.window = None
        self.systems_tabs = None
        self._tab_panels: dict[str, PanelControl] = {}

        self._backlog_items = [
            _BacklogItem("QA smoke pass", "Review", 1, "Mira"),
            _BacklogItem("Keyboard navigation audit", "Review", 2, "Jules"),
            _BacklogItem("Screenshot export", "Ready", 3, "Tao"),
            _BacklogItem("Theme preset sync", "Planned", 4, "Ari"),
        ]
        self._next_backlog_index = 0
        self._backlog_cache = DataCache(max_size=8)
        self._backlog_view = CollectionView(
            self._backlog_items,
            query=CollectionViewQuery(
                sort_key=lambda item: (item.priority, item.title),
                projector=self._project_backlog_item,
            ),
        )
        self._backlog_unsub = None
        self._selected_backlog_item: _BacklogItem | None = None
        self.data_filter_dropdown = None
        self.data_list = None
        self.data_summary_label = None
        self.data_cache_label = None
        self.data_detail_label = None

        self._deployment_name_field = FormField("deployment_name", "nightly-gui")
        self._environment_field = FormField("environment", "Staging")
        self._name_validator = AsyncFieldValidator(
            field=self._deployment_name_field,
            local_rules=[lambda value: None if str(value).strip() else "Name is required"],
            async_check=self._check_pipeline_name,
            debounce_ms=250,
        )
        self._environment_validator = AsyncFieldValidator(
            field=self._environment_field,
            local_rules=[
                lambda value: None
                if str(value) in {"Staging", "QA", "Production"}
                else "Choose a valid target environment"
            ],
        )
        self._form_validator = AsyncFormValidator([self._name_validator, self._environment_validator])
        self.validation_name_input = None
        self.validation_environment_dropdown = None
        self.validation_state_label = None
        self.validation_local_label = None
        self.validation_async_label = None

        self._history = CommandHistory()
        self._history_stages = (
            "Draft",
            "Ready for Review",
            "Approved",
            "Shipped",
        )
        self._history_stage_index = 0
        self.history_current_label = None
        self.history_undo_label = None
        self.history_redo_label = None

        self._theme_manager = ThemeManager()
        self._theme_manager.register_theme(
            "sunrise",
            {
                "primary": (203, 92, 44),
                "surface": (246, 234, 219),
                "text": (54, 37, 29),
            },
        )
        self._review_scope = ScopedTheme(
            {
                "primary": (194, 66, 43),
                "surface": (255, 240, 231),
                "text": (78, 44, 35),
            },
            name="review",
        )
        self._review_scope_enabled = False
        self.theme_dropdown = None
        self.theme_state_label = None
        self.theme_scope_label = None
        self.theme_resolved_label = None

    def build(self, host) -> None:
        self.window = create_feature_presented_window(
            host,
            feature=self,
            presenter_cls=_SystemsPresenter,
            spec=self._make_window_spec(host),
            window_control_cls=WindowControl,
        )

    def on_update(self, host) -> None:
        if self.window is None or not self.window.visible:
            return
        if self.active_tab_key != "validation":
            return
        self._form_validator.update(self._frame_timer.tick())
        self._refresh_validation_labels()

    def set_active_tab(self, key: str) -> None:
        next_key = str(key)
        self.active_tab_key = next_key
        for tab_key, panel in self._tab_panels.items():
            is_active = tab_key == next_key
            panel.visible = is_active
            panel.enabled = is_active
        if next_key == "data":
            self._refresh_backlog_view()
        elif next_key == "validation":
            self._refresh_validation_labels()
        elif next_key == "history":
            self._refresh_history_labels()
        elif next_key == "theme":
            self._refresh_theme_labels()

    def build_data_panel(self, rect: Rect) -> PanelControl:
        panel = PanelControl("systems_data_panel", Rect(rect), draw_background=False)
        left_w = max(280, int(rect.width * 0.58))
        right_x = left_w + 20
        right_w = max(180, rect.width - right_x)
        action_button_w = 120
        action_button_gap = 8
        action_button_right_pad = 12

        panel.add_at(LabelControl("systems_data_filter_label", Rect(0, 0, 72, 28), "Status", align="left"), 0, 0)
        self.data_filter_dropdown = DropdownControl(
            "systems_data_filter",
            Rect(0, 0, 180, 32),
            options=[
                DropdownOption("All", "All"),
                DropdownOption("Review", "Review"),
                DropdownOption("Ready", "Ready"),
                DropdownOption("Planned", "Planned"),
            ],
            selected_index=0,
            on_change=lambda value, _index: self._on_backlog_filter_changed(value),
        )
        panel.add_at(self.data_filter_dropdown, 80, 0)

        add_button = ButtonControl(
            "systems_add_review_item",
            Rect(0, 0, action_button_w, 32),
            "Queue Review",
            self._add_backlog_item,
            style="round",
        )
        cache_button = ButtonControl(
            "systems_clear_cache",
            Rect(0, 0, action_button_w, 32),
            "Clear Cache",
            self._clear_backlog_cache,
            style="round",
        )
        cache_button_x = max(0, rect.width - action_button_right_pad - action_button_w)
        add_button_x = max(0, cache_button_x - action_button_gap - action_button_w)
        panel.add_at(add_button, add_button_x, 0)
        panel.add_at(cache_button, cache_button_x, 0)

        self.data_list = ListViewControl(
            "systems_backlog_list",
            Rect(0, 0, left_w, max(120, rect.height - 52)),
            row_height=28,
            on_select=self._on_backlog_selected,
        )
        self.data_list.set_accessibility(role="listbox", label="Deployment backlog")
        panel.add_at(self.data_list, 0, 44)

        self.data_summary_label = LabelControl(
            "systems_data_summary",
            Rect(0, 0, right_w, 28),
            "CollectionView keeps the release backlog filtered and sorted.",
            align="left",
        )
        self.data_cache_label = LabelControl(
            "systems_data_cache",
            Rect(0, 0, right_w, 28),
            "DataCache is ready.",
            align="left",
        )
        self.data_detail_label = LabelControl(
            "systems_data_detail",
            Rect(0, 0, right_w, 84),
            "Select a backlog item to inspect its cached deployment note.",
            align="left",
        )
        panel.add_at(self.data_summary_label, right_x, 52)
        panel.add_at(self.data_cache_label, right_x, 88)
        panel.add_at(self.data_detail_label, right_x, 132)

        self._backlog_unsub = self.data_list.bind_collection_view(
            self._backlog_view,
            on_refresh=self._on_backlog_view_refreshed,
        )
        self._refresh_backlog_view()
        return panel

    def build_validation_panel(self, rect: Rect) -> PanelControl:
        panel = PanelControl("systems_validation_panel", Rect(rect), draw_background=False)
        panel.add_at(LabelControl("systems_validation_name_label", Rect(0, 0, 180, 28), "Pipeline Name", align="left"), 0, 0)
        self.validation_name_input = TextInputControl(
            "systems_validation_name",
            Rect(0, 0, min(320, rect.width - 16), 32),
            value=self._deployment_name_field.value.value,
            placeholder="nightly-gui",
            on_change=self._on_deployment_name_changed,
        )
        panel.add_at(self.validation_name_input, 0, 30)

        panel.add_at(LabelControl("systems_validation_env_label", Rect(0, 0, 180, 28), "Target Environment", align="left"), 0, 82)
        self.validation_environment_dropdown = DropdownControl(
            "systems_validation_environment",
            Rect(0, 0, 220, 32),
            options=[
                DropdownOption("Staging", "Staging"),
                DropdownOption("QA", "QA"),
                DropdownOption("Production", "Production"),
            ],
            selected_index=0,
            on_change=lambda value, _index: self._on_environment_changed(value),
        )
        panel.add_at(self.validation_environment_dropdown, 0, 112)

        run_checks = ButtonControl(
            "systems_validation_run_checks",
            Rect(0, 0, 148, 32),
            "Run Local Checks",
            self._run_local_validation_checks,
            style="round",
        )
        suggested = ButtonControl(
            "systems_validation_use_suggested",
            Rect(0, 0, 160, 32),
            "Use Suggested Name",
            self._apply_suggested_name,
            style="round",
        )
        panel.add_at(run_checks, 248, 112)
        panel.add_at(suggested, 408, 112)

        self.validation_state_label = LabelControl(
            "systems_validation_state",
            Rect(0, 0, rect.width, 28),
            "Form state pending.",
            align="left",
        )
        self.validation_local_label = LabelControl(
            "systems_validation_local",
            Rect(0, 0, rect.width, 28),
            "Local checks pending.",
            align="left",
        )
        self.validation_async_label = LabelControl(
            "systems_validation_async",
            Rect(0, 0, rect.width, 28),
            "Async availability check pending.",
            align="left",
        )
        panel.add_at(self.validation_state_label, 0, 176)
        panel.add_at(self.validation_local_label, 0, 212)
        panel.add_at(self.validation_async_label, 0, 248)
        self._refresh_validation_labels()
        return panel

    def build_history_panel(self, rect: Rect) -> PanelControl:
        panel = PanelControl("systems_history_panel", Rect(rect), draw_background=False)
        advance_button = ButtonControl(
            "systems_history_advance",
            Rect(0, 0, 140, 32),
            "Advance Stage",
            self._advance_history_stage,
            style="round",
        )
        batch_button = ButtonControl(
            "systems_history_batch",
            Rect(0, 0, 160, 32),
            "Batch Promote",
            self._batch_promote_history_stage,
            style="round",
        )
        undo_button = ButtonControl(
            "systems_history_undo",
            Rect(0, 0, 96, 32),
            "Undo",
            self._undo_history_stage,
            style="round",
        )
        redo_button = ButtonControl(
            "systems_history_redo",
            Rect(0, 0, 96, 32),
            "Redo",
            self._redo_history_stage,
            style="round",
        )
        panel.add_at(advance_button, 0, 0)
        panel.add_at(batch_button, 152, 0)
        panel.add_at(undo_button, 324, 0)
        panel.add_at(redo_button, 432, 0)

        self.history_current_label = LabelControl(
            "systems_history_current",
            Rect(0, 0, rect.width, 28),
            "",
            align="left",
        )
        self.history_undo_label = LabelControl(
            "systems_history_undo_label",
            Rect(0, 0, rect.width, 28),
            "",
            align="left",
        )
        self.history_redo_label = LabelControl(
            "systems_history_redo_label",
            Rect(0, 0, rect.width, 28),
            "",
            align="left",
        )
        panel.add_at(self.history_current_label, 0, 68)
        panel.add_at(self.history_undo_label, 0, 104)
        panel.add_at(self.history_redo_label, 0, 140)
        self._refresh_history_labels()
        return panel

    def build_theme_panel(self, rect: Rect) -> PanelControl:
        panel = PanelControl("systems_theme_panel", Rect(rect), draw_background=False)
        panel.add_at(LabelControl("systems_theme_select_label", Rect(0, 0, 128, 28), "Theme", align="left"), 0, 0)
        self.theme_dropdown = DropdownControl(
            "systems_theme_picker",
            Rect(0, 0, 180, 32),
            options=[
                DropdownOption("Dark", "dark"),
                DropdownOption("Light", "light"),
                DropdownOption("Sunrise", "sunrise"),
            ],
            selected_index=0,
            on_change=lambda value, _index: self._on_theme_changed(value),
        )
        panel.add_at(self.theme_dropdown, 0, 30)

        toggle_scope = ButtonControl(
            "systems_theme_toggle_scope",
            Rect(0, 0, 164, 32),
            "Toggle Review Scope",
            self._toggle_review_scope,
            style="round",
        )
        panel.add_at(toggle_scope, 204, 30)

        self.theme_state_label = LabelControl(
            "systems_theme_state",
            Rect(0, 0, rect.width, 28),
            "",
            align="left",
        )
        self.theme_scope_label = LabelControl(
            "systems_theme_scope",
            Rect(0, 0, rect.width, 28),
            "",
            align="left",
        )
        self.theme_resolved_label = LabelControl(
            "systems_theme_resolved",
            Rect(0, 0, rect.width, 28),
            "",
            align="left",
        )
        panel.add_at(self.theme_state_label, 0, 92)
        panel.add_at(self.theme_scope_label, 0, 128)
        panel.add_at(self.theme_resolved_label, 0, 164)
        self._refresh_theme_labels()
        return panel

    def _make_window_spec(self, host) -> AnchoredWindowSpec:
        width = max(640, int(host.screen_rect.width * 0.8))
        height = max(420, int(host.screen_rect.height * 0.8))
        return AnchoredWindowSpec(
            control_id="systems_window",
            title="Systems Demo",
            size=(width, height),
            anchor="center",
            margin=(0, 0),
            use_frame_backdrop=True,
        )

    def _project_backlog_item(self, item: _BacklogItem) -> ListItem:
        return ListItem(
            label=f"[{item.status}] P{item.priority} {item.title}",
            value=item.title,
            data=item,
        )

    def _selected_backlog_filter(self) -> str:
        selected = getattr(self.data_filter_dropdown, "selected_option", None)
        if selected is None:
            return "All"
        return str(selected.value)

    def _refresh_backlog_view(self) -> None:
        selected_filter = self._selected_backlog_filter()
        self._backlog_view.query.filters = []
        if selected_filter != "All":
            self._backlog_view.query.filters.append(lambda item, status=selected_filter: item.status == status)
        self._backlog_view.refresh()
        self._refresh_backlog_labels()

    def _on_backlog_filter_changed(self, value: str) -> None:
        _ = value
        self._selected_backlog_item = None
        self._refresh_backlog_view()

    def _on_backlog_view_refreshed(self) -> None:
        if self.data_list is None:
            return
        items = self.data_list.items
        if items:
            self.data_list.selected_index = 0
            self._on_backlog_selected(0, items[0])
            return
        self._selected_backlog_item = None
        self._refresh_backlog_labels()

    def _on_backlog_selected(self, _index: int, item: ListItem) -> None:
        data = item.data if isinstance(item.data, _BacklogItem) else None
        self._selected_backlog_item = data
        if data is not None:
            self._backlog_cache.get_or_load(data.title, lambda: self._cache_payload_for_backlog_item(data))
        self._refresh_backlog_labels()

    def _cache_payload_for_backlog_item(self, item: _BacklogItem) -> str:
        return f"{item.owner} owns the {item.title.lower()} handoff while the item is in {item.status.lower()} state."

    def _refresh_backlog_labels(self) -> None:
        if self.data_summary_label is not None:
            self.data_summary_label.text = (
                f"CollectionView showing {self._backlog_view.count()} items for {self._selected_backlog_filter().lower()} routing."
            )
        if self.data_cache_label is not None:
            stats = self._backlog_cache.stats()
            self.data_cache_label.text = (
                f"DataCache size {stats.size} | hits {stats.hits} | misses {stats.misses} | evictions {stats.evictions}"
            )
        if self.data_detail_label is not None:
            if self._selected_backlog_item is None:
                self.data_detail_label.text = "Select a backlog item to inspect its cached deployment note."
            else:
                payload = self._backlog_cache.get_or_load(
                    self._selected_backlog_item.title,
                    lambda item=self._selected_backlog_item: self._cache_payload_for_backlog_item(item),
                )
                self.data_detail_label.text = payload

    def _add_backlog_item(self) -> None:
        templates = (
            ("Localization review", "Review", 2, "Nia"),
            ("Accessibility script", "Ready", 3, "Mira"),
            ("Telemetry snapshot", "Planned", 5, "Tao"),
        )
        title, status, priority, owner = templates[self._next_backlog_index % len(templates)]
        self._next_backlog_index += 1
        item = _BacklogItem(f"{title} {self._next_backlog_index}", status, priority, owner)
        self._backlog_items.append(item)
        self._refresh_backlog_view()

    def _clear_backlog_cache(self) -> None:
        self._backlog_cache.invalidate_all()
        self._refresh_backlog_labels()

    def _check_pipeline_name(self, value: object) -> str | None:
        reserved = {"admin", "root", "prod"}
        normalized = str(value).strip().lower()
        if normalized in reserved:
            return "Reserved pipeline name"
        return None

    def _on_deployment_name_changed(self, value: str) -> None:
        self._deployment_name_field.value.value = str(value)
        self._refresh_validation_labels()

    def _on_environment_changed(self, value: str) -> None:
        self._environment_field.value.value = str(value)
        self._refresh_validation_labels()

    def _run_local_validation_checks(self) -> None:
        self._form_validator.validate_all_local()
        self._refresh_validation_labels()

    def _apply_suggested_name(self) -> None:
        suggested = "staging-gui-release"
        if self.validation_name_input is not None:
            self.validation_name_input.set_value(suggested)
        self._deployment_name_field.value.value = suggested
        self._refresh_validation_labels()

    def _refresh_validation_labels(self) -> None:
        if self.validation_state_label is not None:
            environment = self._environment_field.value.value
            if self._form_validator.is_valid:
                self.validation_state_label.text = f"AsyncFormValidator: ready to route build to {environment}."
            else:
                self.validation_state_label.text = "AsyncFormValidator: deployment form still needs attention."
        if self.validation_local_label is not None:
            local_error = self._name_validator.local_error.value or self._environment_validator.local_error.value
            self.validation_local_label.text = (
                f"Local validation: {local_error}" if local_error is not None else "Local validation: passed"
            )
        if self.validation_async_label is not None:
            if self._name_validator.is_validating.value:
                self.validation_async_label.text = "Async validation: checking pipeline name availability..."
            else:
                async_error = self._name_validator.async_error.value
                self.validation_async_label.text = (
                    f"Async validation: {async_error}" if async_error is not None else "Async validation: pipeline name available"
                )

    def _advance_history_stage(self) -> None:
        current = self._history_stage_index
        if current >= len(self._history_stages) - 1:
            return
        next_index = current + 1
        description = f"Promote to {self._history_stages[next_index]}"
        self._history.push(_StatusChangeCommand(self, next_index, description))
        self._refresh_history_labels()

    def _batch_promote_history_stage(self) -> None:
        current = self._history_stage_index
        if current >= len(self._history_stages) - 1:
            return
        with self._history.transaction("Prepare release bundle"):
            mid_index = min(current + 1, len(self._history_stages) - 1)
            self._history.push(
                _StatusChangeCommand(self, mid_index, f"Promote to {self._history_stages[mid_index]}")
            )
            final_index = min(mid_index + 1, len(self._history_stages) - 1)
            if final_index != mid_index:
                self._history.push(
                    _StatusChangeCommand(self, final_index, f"Promote to {self._history_stages[final_index]}")
                )
        self._refresh_history_labels()

    def _undo_history_stage(self) -> None:
        self._history.undo()
        self._refresh_history_labels()

    def _redo_history_stage(self) -> None:
        self._history.redo()
        self._refresh_history_labels()

    def _refresh_history_labels(self) -> None:
        if self.history_current_label is not None:
            self.history_current_label.text = (
                f"CommandHistory current milestone: {self._history_stages[self._history_stage_index]}"
            )
        if self.history_undo_label is not None:
            undo_desc = self._history.undo_description or "Nothing to undo"
            self.history_undo_label.text = f"Undo: {undo_desc}"
        if self.history_redo_label is not None:
            redo_desc = self._history.redo_description or "Nothing to redo"
            self.history_redo_label.text = f"Redo: {redo_desc}"

    def _on_theme_changed(self, value: str) -> None:
        self._theme_manager.switch(str(value))
        self._refresh_theme_labels()

    def _toggle_review_scope(self) -> None:
        self._review_scope_enabled = not self._review_scope_enabled
        self._refresh_theme_labels()

    def _refresh_theme_labels(self) -> None:
        active_name = self._theme_manager.active_theme.value
        scoped = ScopedThemeManager(self._theme_manager.active_tokens.value)
        if self._review_scope_enabled:
            scoped.push(self._review_scope)
        global_primary = self._theme_manager.token("primary")
        scoped_primary = scoped.resolve("primary")
        if self.theme_state_label is not None:
            self.theme_state_label.text = f"ThemeManager active theme: {active_name}"
        if self.theme_scope_label is not None:
            scope_state = "enabled" if self._review_scope_enabled else "disabled"
            self.theme_scope_label.text = f"ScopedThemeManager review scope: {scope_state}"
        if self.theme_resolved_label is not None:
            self.theme_resolved_label.text = (
                f"Resolved primary token global {global_primary} | scoped {scoped_primary}"
            )
