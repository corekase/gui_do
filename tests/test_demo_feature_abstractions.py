import unittest
from unittest.mock import patch
from pygame import Rect

from gui_do.features.data_driven_runtime import (
    AccessibilitySequenceSpec,
    AnchoredWindowSpec,
    LogicBindingSpec,
    TaskPanelLinearLayoutSpec,
    TaskPanelSceneNavButtonSpec,
    TaskPanelWindowToggleGroupSpec,
    RightAnchoredTaskPanelButtonSpec,
    TaskPanelButtonSpec,
    add_scene_task_panel_items,
    add_right_anchored_task_panel_button,
    add_task_panel_button,
    add_task_panel_buttons,
    add_task_panel_scene_nav_button,
    add_task_panel_window_toggle_group,
    add_window_button,
    add_window_button_row,
    add_window_control,
    add_window_label,
    add_window_toggle_task_panel_controls,
    apply_window_toggle_accessibility,
    apply_accessibility_sequence,
    apply_accessibility_sequence_from_attrs,
    bind_input_map_actions,
    bind_feature_logic_aliases,
    build_tab_builder_specs,
    build_tools_menu_entries,
    create_tab_control_from_specs,
    compute_tabbed_window_layout,
    collect_window_toggle_controls,
    create_task_panel_linear_layout,
    create_feature_presented_window,
    create_presented_anchored_window,
    create_presented_window_from_spec,
    ensure_scene_scheduler,
    initialize_locale_registry,
    instantiate_features_from_specs,
    make_exit_action,
    make_palette_open_action,
    make_scene_nav_action,
    make_static_accessibility_spec,
    make_window_toggle_spec,
    prewarm_runtime_scenes,
    register_features_from_specs,
    register_window_tab_builder_specs,
    register_window_presentation_specs,
    register_tooltip_specs,
    register_descriptors,
    register_companion_logic_features,
    register_window_toggle_tooltips,
    resolve_canvas_local_point,
    setup_feature_presenter_tabs,
    register_tab_update_handlers,
    ActiveTabUpdateRouter,
    TabLayoutContext,
    setup_routed_feature_runtime,
    apply_runtime_scene_pristine_assets,
    bind_runtime_scene_exit_keys,
)


class _StubActionRegistry:
    def context_menu_items(self, *, category: str):
        if category != "Tools":
            return []

        class _Item:
            def __init__(self, label: str):
                self.label = label

        return [_Item("One"), _Item("Open Command Palette (F5)"), _Item("Two")]


class _StubHost:
    def __init__(self, action_registry=None):
        self.action_registry = action_registry


class _StubControl:
    def __init__(self):
        self.tab_indices = []
        self.accessibility = []

    def set_tab_index(self, idx: int):
        self.tab_indices.append(int(idx))

    def set_accessibility(self, *, role: str, label: str):
        self.accessibility.append((str(role), str(label)))


class _StubFeatureManager:
    def __init__(self):
        self.register_calls = []

    def register(self, provider, host):
        self.register_calls.append((provider, host))


class _StubWindow:
    def __init__(self):
        self.presenter = None
        self.added = []

    def set_presenter(self, presenter):
        self.presenter = presenter

    def add(self, control):
        self.added.append(control)
        return control


class _StubSchedulerHostApp:
    def __init__(self, scheduler):
        self._scheduler = scheduler
        self.requests = []

    def get_scene_scheduler(self, scene_name: str):
        self.requests.append(str(scene_name))
        return self._scheduler


class _StubSchedulerHost:
    def __init__(self, scheduler):
        self.app = _StubSchedulerHostApp(scheduler)


class _StubFeatureWithScheduler:
    def __init__(self):
        self.scheduler = None


class _StubConfigurableScheduler:
    def __init__(self):
        self.dispatch_limits = []

    def set_message_dispatch_limit(self, value: int):
        self.dispatch_limits.append(int(value))


class _StubRoutedFeature:
    def __init__(self):
        self.scheduler = None
        self._aliases = {}

    def bound_logic_name(self, *, alias: str):
        return self._aliases.get(str(alias))

    def bind_logic(self, provider_name: str, *, alias: str):
        self._aliases[str(alias)] = str(provider_name)


class _StubToggleBinding:
    def __init__(
        self,
        *,
        key: str,
        toggle_attribute_name: str | None,
        task_panel_slot_index: int | None,
        accessibility_label: str | None,
        action_label: str | None,
        task_panel_toggle_button_id: str | None = None,
        task_panel_label: str | None = None,
        task_panel_style: str = "toggle",
    ):
        self.key = str(key)
        self.toggle_attribute_name = toggle_attribute_name
        self.task_panel_slot_index = task_panel_slot_index
        self.accessibility_label = accessibility_label
        self.action_label = action_label
        self.task_panel_toggle_button_id = task_panel_toggle_button_id
        self.task_panel_label = task_panel_label
        self.task_panel_style = task_panel_style


class _StubToggleWindowPresentation:
    def __init__(self, bindings):
        self._bindings = tuple(bindings)

    def bindings(self):
        return self._bindings


class _StubToggleControl:
    def __init__(self):
        self.accessibility_calls = []

    def set_accessibility(self, *, role: str, label: str):
        self.accessibility_calls.append((str(role), str(label)))


class _StubSequenceControl:
    def __init__(self):
        self.tab_indices = []
        self.accessibility = []

    def set_tab_index(self, idx: int):
        self.tab_indices.append(int(idx))

    def set_accessibility(self, *, role: str, label: str):
        self.accessibility.append((str(role), str(label)))


class _StubToggleHost:
    pass


class _StubLayout:
    def linear(self, index: int):
        return Rect(int(index), 0, 120, 30)


class _StubTaskPanel:
    def __init__(self):
        self.rect = Rect(0, 100, 400, 50)
        self.added_controls = []

    def add(self, control):
        self.added_controls.append(control)
        return control


class _StubTaskPanelHost:
    pass


class _StubWindowPresentation:
    def __init__(self, bindings):
        self._bindings = tuple(bindings)
        self.visible_calls = []

    def bindings(self):
        return self._bindings

    def set_visible(self, key: str, visible: bool, *, from_toggle: bool):
        self.visible_calls.append((str(key), bool(visible), bool(from_toggle)))


class _StubTooltipManager:
    def __init__(self):
        self.calls = []

    def register(self, control, message: str):
        self.calls.append((control, str(message)))


class _StubInputMap:
    def __init__(self):
        self.bind_calls = []

    def bind(self, action: str, *, key: int, mod: int):
        self.bind_calls.append((str(action), int(key), int(mod)))


class _StubDescriptorRegistry:
    def __init__(self):
        self.calls = []

    def register(self, owner_class, descriptor):
        self.calls.append((owner_class, descriptor))


class _StubRuntimeSceneSpec:
    def __init__(self, *, scene_name: str, pristine_asset=None, bind_escape_to_exit: bool = False, prewarm: bool = False):
        self.scene_name = str(scene_name)
        self.pristine_asset = pristine_asset
        self.bind_escape_to_exit = bool(bind_escape_to_exit)
        self.prewarm = bool(prewarm)


class _StubPristineApp:
    def __init__(self):
        self.calls = []

    def set_pristine(self, asset_path: str, *, scene_name: str):
        self.calls.append((str(asset_path), str(scene_name)))


class _StubBindActions:
    def __init__(self):
        self.calls = []

    def bind_key(self, key, action_name: str, *, scene: str):
        self.calls.append((key, str(action_name), str(scene)))


class _StubPrewarmApp:
    def __init__(self):
        self.calls = []

    def prewarm_scene(self, scene_name: str):
        self.calls.append(str(scene_name))


class _StubFeatureSpec:
    def __init__(self, *, attr_name: str, factory):
        self.attr_name = str(attr_name)
        self.factory = factory


class _StubRegisterApp:
    def __init__(self):
        self.calls = []

    def register_feature(self, feature, *, host):
        self.calls.append((feature, host))


class _StubWindowPresentationRegistrar:
    def __init__(self):
        self.calls = []

    def register_feature_window(self, key, **kwargs):
        self.calls.append((key, kwargs))


class _StubWindowSpec:
    def __init__(
        self,
        *,
        key: str,
        feature_attribute_name: str,
        toggle_attribute_name: str,
        action_name: str,
        action_label: str,
        task_panel_toggle_button_id: str,
        task_panel_label: str,
        task_panel_style: str,
        task_panel_slot_index: int,
        accessibility_label: str,
    ):
        self.key = key
        self.feature_attribute_name = feature_attribute_name
        self.toggle_attribute_name = toggle_attribute_name
        self.action_name = action_name
        self.action_label = action_label
        self.task_panel_toggle_button_id = task_panel_toggle_button_id
        self.task_panel_label = task_panel_label
        self.task_panel_style = task_panel_style
        self.task_panel_slot_index = task_panel_slot_index
        self.accessibility_label = accessibility_label


class _StubPointerPacket:
    def __init__(self, *, local_pos=None, pos=None):
        self.local_pos = local_pos
        self.pos = pos


class _StubAttrAccessibilityTarget:
    def __init__(self):
        self.first = _StubControl()
        self.second = _StubControl()


class _StubPresenter:
    def __init__(self):
        self.controls = []

    def add_control(self, control):
        self.controls.append(control)
        return control


class TestDemoFeatureAbstractions(unittest.TestCase):
    def test_build_tools_menu_entries_handles_missing_registry(self):
        entries = build_tools_menu_entries(_StubHost(None))
        self.assertEqual([], entries)

    def test_build_tools_menu_entries_applies_exclusions(self):
        entries = build_tools_menu_entries(
            _StubHost(_StubActionRegistry()),
            exclude_labels=("Open Command Palette (F5)",),
        )
        self.assertEqual(1, len(entries))
        self.assertEqual("Tools", entries[0].label)
        labels = [item.label for item in entries[0].items]
        self.assertEqual(["One", "Two"], labels)

    def test_apply_accessibility_sequence_sets_tab_order_and_labels(self):
        first = _StubControl()
        second = _StubControl()

        next_index = apply_accessibility_sequence(
            [
                (first, "button", "First"),
                (None, "button", "Skipped"),
                (second, "toggle", "Second"),
            ],
            5,
        )

        self.assertEqual(7, next_index)
        self.assertEqual([5], first.tab_indices)
        self.assertEqual([("button", "First")], first.accessibility)
        self.assertEqual([6], second.tab_indices)
        self.assertEqual([("toggle", "Second")], second.accessibility)

    def test_register_companion_logic_features_registers_all_providers(self):
        manager = _StubFeatureManager()
        host = object()
        providers = [object(), object(), object()]

        register_companion_logic_features(manager, host, providers)

        self.assertEqual(3, len(manager.register_calls))
        self.assertEqual(
            [(providers[0], host), (providers[1], host), (providers[2], host)],
            manager.register_calls,
        )

    def test_create_presented_anchored_window_attaches_presenter(self):
        host = object()
        presenter = object()
        window = _StubWindow()

        with patch("gui_do.features.data_driven_runtime.create_anchored_feature_window", return_value=window) as create_window:
            result = create_presented_anchored_window(
                host,
                control_id="x",
                title="Demo",
                size=(320, 240),
                anchor="top_left",
                margin=(10, 10),
                presenter=presenter,
            )

        self.assertIs(window, result)
        self.assertIs(presenter, window.presenter)
        self.assertEqual(1, create_window.call_count)

    def test_create_presented_window_from_spec_uses_spec_values(self):
        host = object()
        presenter = object()
        window = _StubWindow()
        spec = AnchoredWindowSpec(
            control_id="demo_window",
            title="Demo",
            size=(420, 260),
            anchor="top_left",
            margin=(12, 14),
            use_frame_backdrop=False,
        )

        with patch("gui_do.features.data_driven_runtime.create_anchored_feature_window", return_value=window):
            result = create_presented_window_from_spec(host, presenter=presenter, spec=spec)

        self.assertIs(window, result)
        self.assertIs(presenter, window.presenter)

    def test_create_feature_presented_window_builds_presenter_from_types(self):
        host = object()
        feature = object()
        window = _StubWindow()
        spec = AnchoredWindowSpec(
            control_id="demo_window",
            title="Demo",
            size=(320, 240),
            anchor="top_left",
            margin=(8, 8),
        )

        class _Presenter:
            def __init__(self, f, h):
                self.feature = f
                self.host = h

        with patch("gui_do.features.data_driven_runtime.create_anchored_feature_window", return_value=window):
            result = create_feature_presented_window(
                host,
                feature=feature,
                presenter_cls=_Presenter,
                spec=spec,
            )

        self.assertIs(window, result)
        self.assertIs(feature, window.presenter.feature)
        self.assertIs(host, window.presenter.host)

    def test_ensure_scene_scheduler_caches_scheduler_on_feature(self):
        scheduler = object()
        host = _StubSchedulerHost(scheduler)
        feature = _StubFeatureWithScheduler()

        first = ensure_scene_scheduler(feature, host, scene_name="main")
        second = ensure_scene_scheduler(feature, host, scene_name="main")

        self.assertIs(scheduler, first)
        self.assertIs(scheduler, second)
        self.assertIs(scheduler, feature.scheduler)
        self.assertEqual(["main"], host.app.requests)

    def test_setup_routed_feature_runtime_sets_scheduler_and_logic_aliases(self):
        scheduler = _StubConfigurableScheduler()
        host = _StubSchedulerHost(scheduler)
        feature = _StubRoutedFeature()

        result = setup_routed_feature_runtime(
            feature,
            host,
            scene_name="main",
            scheduler_dispatch_limit=256,
            logic_bindings=(
                LogicBindingSpec(alias="primary", provider_name="provider.main"),
                LogicBindingSpec(alias="can1", provider_name="provider.can1"),
            ),
        )

        self.assertIs(scheduler, result)
        self.assertIs(scheduler, feature.scheduler)
        self.assertEqual([256], scheduler.dispatch_limits)
        self.assertEqual("provider.main", feature.bound_logic_name(alias="primary"))
        self.assertEqual("provider.can1", feature.bound_logic_name(alias="can1"))

    def test_bind_feature_logic_aliases_is_idempotent(self):
        feature = _StubRoutedFeature()
        feature.bind_logic("existing.provider", alias="primary")

        bind_feature_logic_aliases(
            feature,
            (
                LogicBindingSpec(alias="primary", provider_name="new.provider"),
                LogicBindingSpec(alias="secondary", provider_name="secondary.provider"),
            ),
        )

        self.assertEqual("existing.provider", feature.bound_logic_name(alias="primary"))
        self.assertEqual("secondary.provider", feature.bound_logic_name(alias="secondary"))

    def test_collect_window_toggle_controls_returns_sorted_existing_controls(self):
        host = _StubToggleHost()
        host.first_toggle = _StubToggleControl()
        host.second_toggle = _StubToggleControl()
        presentation = _StubToggleWindowPresentation(
            (
                _StubToggleBinding(
                    key="second",
                    toggle_attribute_name="second_toggle",
                    task_panel_slot_index=2,
                    accessibility_label="Second",
                    action_label="Second Action",
                ),
                _StubToggleBinding(
                    key="missing",
                    toggle_attribute_name="missing_toggle",
                    task_panel_slot_index=3,
                    accessibility_label="Missing",
                    action_label="Missing Action",
                ),
                _StubToggleBinding(
                    key="first",
                    toggle_attribute_name="first_toggle",
                    task_panel_slot_index=1,
                    accessibility_label="First",
                    action_label="First Action",
                ),
            )
        )

        controls = collect_window_toggle_controls(host, presentation)

        self.assertEqual(["first", "second"], [binding.key for binding, _control in controls])

    def test_apply_window_toggle_accessibility_prefers_accessibility_label(self):
        host = _StubToggleHost()
        host.first_toggle = _StubToggleControl()
        host.second_toggle = _StubToggleControl()
        presentation = _StubToggleWindowPresentation(
            (
                _StubToggleBinding(
                    key="first",
                    toggle_attribute_name="first_toggle",
                    task_panel_slot_index=1,
                    accessibility_label="First Toggle",
                    action_label="First Action",
                ),
                _StubToggleBinding(
                    key="second",
                    toggle_attribute_name="second_toggle",
                    task_panel_slot_index=2,
                    accessibility_label=None,
                    action_label="Second Action",
                ),
            )
        )

        apply_window_toggle_accessibility(host, presentation, role="toggle")

        self.assertEqual([("toggle", "First Toggle")], host.first_toggle.accessibility_calls)
        self.assertEqual([("toggle", "Second Action")], host.second_toggle.accessibility_calls)

    def test_add_window_toggle_task_panel_controls_builds_and_binds_toggles(self):
        host = _StubToggleHost()
        task_panel = _StubTaskPanel()
        layout = _StubLayout()
        window_presentation = _StubWindowPresentation(
            (
                _StubToggleBinding(
                    key="later",
                    toggle_attribute_name="later_toggle",
                    task_panel_slot_index=3,
                    accessibility_label="Later",
                    action_label="Later Action",
                ),
                _StubToggleBinding(
                    key="first",
                    toggle_attribute_name="first_toggle",
                    task_panel_slot_index=1,
                    accessibility_label="First",
                    action_label="First Action",
                ),
            )
        )

        controls, max_slot = add_window_toggle_task_panel_controls(
            host,
            task_panel,
            layout,
            window_presentation,
        )

        self.assertEqual(["first", "later"], [binding.key for binding, _ in controls])
        self.assertEqual(3, max_slot)
        self.assertEqual(2, len(task_panel.added_controls))
        self.assertIs(task_panel.added_controls[0], host.first_toggle)
        self.assertIs(task_panel.added_controls[1], host.later_toggle)

        first_toggle = task_panel.added_controls[0]
        later_toggle = task_panel.added_controls[1]
        self.assertEqual(1, first_toggle.tab_index)
        self.assertEqual(3, later_toggle.tab_index)
        first_toggle.on_toggle(True)
        later_toggle.on_toggle(False)
        self.assertEqual(
            [
                ("first", True, True),
                ("later", False, True),
            ],
            window_presentation.visible_calls,
        )

    def test_register_window_toggle_tooltips_uses_binding_labels(self):
        tooltip_manager = _StubTooltipManager()
        first_toggle = object()
        second_toggle = object()
        toggle_controls = [
            (
                _StubToggleBinding(
                    key="first",
                    toggle_attribute_name="first_toggle",
                    task_panel_slot_index=1,
                    accessibility_label=None,
                    action_label="First Action",
                ),
                first_toggle,
            ),
            (
                _StubToggleBinding(
                    key="second",
                    toggle_attribute_name="second_toggle",
                    task_panel_slot_index=2,
                    accessibility_label=None,
                    action_label=None,
                ),
                second_toggle,
            ),
        ]

        register_window_toggle_tooltips(tooltip_manager, toggle_controls)

        self.assertEqual(
            [
                (first_toggle, "Toggle the First Action window"),
                (second_toggle, "Toggle the Second window"),
            ],
            tooltip_manager.calls,
        )

    def test_task_panel_window_toggle_group_supports_per_scene_owner_and_independent_tab_order(self):
        host = _StubToggleHost()
        window_presentation = _StubWindowPresentation(
            (
                _StubToggleBinding(
                    key="alpha",
                    toggle_attribute_name="alpha_toggle",
                    task_panel_slot_index=1,
                    accessibility_label="Alpha",
                    action_label="Alpha Action",
                ),
                _StubToggleBinding(
                    key="beta",
                    toggle_attribute_name="beta_toggle",
                    task_panel_slot_index=2,
                    accessibility_label="Beta",
                    action_label="Beta Action",
                ),
            )
        )

        scene_a = _StubToggleHost()
        scene_b = _StubToggleHost()
        panel_a = _StubTaskPanel()
        panel_b = _StubTaskPanel()
        layout = _StubLayout()

        toggles_a = add_task_panel_window_toggle_group(
            host,
            panel_a,
            layout,
            window_presentation,
            TaskPanelWindowToggleGroupSpec(start_index=1),
            attr_owner=scene_a,
        )
        toggles_b = add_task_panel_window_toggle_group(
            host,
            panel_b,
            layout,
            window_presentation,
            TaskPanelWindowToggleGroupSpec(start_index=1),
            attr_owner=scene_b,
        )

        self.assertTrue(hasattr(scene_a, "alpha_toggle"))
        self.assertTrue(hasattr(scene_b, "alpha_toggle"))
        self.assertIsNot(scene_a.alpha_toggle, scene_b.alpha_toggle)
        self.assertFalse(hasattr(host, "alpha_toggle"))

        scene_a_back = _StubSequenceControl()
        scene_b_back = _StubSequenceControl()
        next_a = apply_accessibility_sequence(
            [
                (scene_a_back, "button", "Back A"),
                (toggles_a[0][1], "toggle", "Alpha"),
                (toggles_a[1][1], "toggle", "Beta"),
            ],
            40,
        )
        next_b = apply_accessibility_sequence(
            [
                (scene_b_back, "button", "Back B"),
                (toggles_b[0][1], "toggle", "Alpha"),
                (toggles_b[1][1], "toggle", "Beta"),
            ],
            60,
        )

        self.assertEqual(43, next_a)
        self.assertEqual(63, next_b)
        self.assertEqual([40], scene_a_back.tab_indices)
        self.assertEqual([60], scene_b_back.tab_indices)
        self.assertEqual(41, toggles_a[0][1].tab_index)
        self.assertEqual(61, toggles_b[0][1].tab_index)

    def test_apply_accessibility_sequence_from_attrs_uses_target_attributes(self):
        target = _StubAttrAccessibilityTarget()

        next_index = apply_accessibility_sequence_from_attrs(
            target,
            (
                AccessibilitySequenceSpec(control_attr="first", role="button", label="First"),
                AccessibilitySequenceSpec(control_attr="missing", role="button", label="Missing"),
                AccessibilitySequenceSpec(control_attr="second", role="toggle", label="Second"),
            ),
            3,
        )

        self.assertEqual(5, next_index)
        self.assertEqual([3], target.first.tab_indices)
        self.assertEqual([("button", "First")], target.first.accessibility)
        self.assertEqual([4], target.second.tab_indices)
        self.assertEqual([("toggle", "Second")], target.second.accessibility)

    def test_initialize_locale_registry_registers_tables_and_initial_locale(self):
        from gui_do import StringTable

        en = StringTable("en", {"greeting": "Hello"})
        es = StringTable("es", {"greeting": "Hola"})

        locale_registry = initialize_locale_registry([en, es], initial_locale="en")

        self.assertIsNotNone(locale_registry)
        self.assertEqual("en", locale_registry.active_locale)

    def test_bind_input_map_actions_binds_all_pairs(self):
        input_map = _StubInputMap()

        bind_input_map_actions(
            input_map,
            [(1, "move_up"), (2, "move_down")],
            mod=4,
        )

        self.assertEqual(
            [
                ("move_up", 1, 4),
                ("move_down", 2, 4),
            ],
            input_map.bind_calls,
        )

    def test_register_descriptors_registers_all_descriptors(self):
        registry = _StubDescriptorRegistry()
        owner_class = object()
        descriptors = [object(), object(), object()]

        register_descriptors(registry, owner_class, descriptors)

        self.assertEqual(
            [
                (owner_class, descriptors[0]),
                (owner_class, descriptors[1]),
                (owner_class, descriptors[2]),
            ],
            registry.calls,
        )

    def test_resolve_canvas_local_point_prefers_local_pos(self):
        packet = _StubPointerPacket(local_pos=(12, 34), pos=(200, 300))

        point = resolve_canvas_local_point(packet, Rect(50, 80, 300, 200))

        self.assertEqual((12.0, 34.0), point)

    def test_resolve_canvas_local_point_falls_back_to_global_pos(self):
        packet = _StubPointerPacket(local_pos=None, pos=(120, 90))

        point = resolve_canvas_local_point(packet, Rect(100, 70, 300, 200))

        self.assertEqual((20.0, 20.0), point)

    def test_resolve_canvas_local_point_returns_none_when_missing_positions(self):
        packet = _StubPointerPacket(local_pos=None, pos=None)

        point = resolve_canvas_local_point(packet, Rect(0, 0, 10, 10))

        self.assertIsNone(point)

    def test_apply_runtime_scene_pristine_assets_applies_only_configured_specs(self):
        app = _StubPristineApp()
        specs = [
            _StubRuntimeSceneSpec(scene_name="main", pristine_asset="a.png"),
            _StubRuntimeSceneSpec(scene_name="secondary", pristine_asset=None),
            _StubRuntimeSceneSpec(scene_name="third", pristine_asset="b.png"),
        ]

        apply_runtime_scene_pristine_assets(app, specs)

        self.assertEqual([("a.png", "main"), ("b.png", "third")], app.calls)

    def test_bind_runtime_scene_exit_keys_binds_only_opted_in_specs(self):
        actions = _StubBindActions()
        specs = [
            _StubRuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),
            _StubRuntimeSceneSpec(scene_name="secondary", bind_escape_to_exit=False),
            _StubRuntimeSceneSpec(scene_name="overlay", bind_escape_to_exit=True),
        ]

        bind_runtime_scene_exit_keys(actions, specs, key=27, action_name="exit")

        self.assertEqual([(27, "exit", "main"), (27, "exit", "overlay")], actions.calls)

    def test_prewarm_runtime_scenes_prewarms_only_opted_in_specs(self):
        app = _StubPrewarmApp()
        specs = [
            _StubRuntimeSceneSpec(scene_name="main", prewarm=False),
            _StubRuntimeSceneSpec(scene_name="control_showcase", prewarm=True),
            _StubRuntimeSceneSpec(scene_name="systems", prewarm=True),
        ]

        prewarm_runtime_scenes(app, specs)

        self.assertEqual(["control_showcase", "systems"], app.calls)

    def test_add_task_panel_button_adds_button_via_layout_slot(self):
        task_panel = _StubTaskPanel()
        layout = _StubLayout()

        button = add_task_panel_button(
            task_panel,
            layout,
            control_id="run",
            slot_index=3,
            label="Run",
            on_click=lambda: None,
            style="angle",
        )

        self.assertEqual(1, len(task_panel.added_controls))
        self.assertIs(button, task_panel.added_controls[0])
        self.assertEqual("run", button.control_id)
        self.assertEqual("Run", button.text)
        self.assertEqual(3, button.rect.left)

    def test_add_task_panel_buttons_assigns_controls_to_host_attributes(self):
        host = _StubTaskPanelHost()
        task_panel = _StubTaskPanel()
        layout = _StubLayout()

        add_task_panel_buttons(
            host,
            task_panel,
            layout,
            (
                TaskPanelButtonSpec(
                    attr_name="first_button",
                    control_id="first",
                    slot_index=0,
                    label="First",
                    on_click=lambda: None,
                ),
                TaskPanelButtonSpec(
                    attr_name="second_button",
                    control_id="second",
                    slot_index=2,
                    label="Second",
                    on_click=lambda: None,
                    style="round",
                ),
            ),
        )

        self.assertEqual(2, len(task_panel.added_controls))
        self.assertIs(host.first_button, task_panel.added_controls[0])
        self.assertIs(host.second_button, task_panel.added_controls[1])

    def test_create_task_panel_linear_layout_anchors_to_task_panel_top(self):
        task_panel = _StubTaskPanel()

        layout = create_task_panel_linear_layout(
            task_panel,
            TaskPanelLinearLayoutSpec(
                left=16,
                top_offset=10,
                item_width=124,
                item_height=30,
                spacing=10,
                horizontal=True,
            ),
        )

        rect0 = layout.linear(0)
        rect1 = layout.linear(1)
        self.assertEqual((16, 110, 124, 30), (rect0.left, rect0.top, rect0.width, rect0.height))
        self.assertEqual(150, rect1.left)

    def test_add_task_panel_scene_nav_button_uses_slot_layout_and_sets_attr(self):
        host = _StubTaskPanelHost()
        task_panel = _StubTaskPanel()
        layout = _StubLayout()

        button = add_task_panel_scene_nav_button(
            task_panel,
            layout,
            host,
            TaskPanelSceneNavButtonSpec(
                attr_name="back_button",
                control_id="back",
                slot_index=2,
                label="Back",
                target_scene="main",
                accessibility_label="Return to main",
            ),
        )

        self.assertIs(button, host.back_button)
        self.assertEqual("back", button.control_id)
        self.assertEqual("Back", button.text)
        self.assertEqual(2, button.rect.left)

    def test_add_scene_task_panel_items_builds_buttons_nav_and_toggles(self):
        host = _StubTaskPanelHost()
        task_panel = _StubTaskPanel()
        layout = _StubLayout()
        presentation = _StubWindowPresentation(
            (
                _StubToggleBinding(
                    key="first",
                    toggle_attribute_name="first_toggle",
                    task_panel_slot_index=9,
                    accessibility_label="First Toggle",
                    action_label="First Action",
                ),
                _StubToggleBinding(
                    key="second",
                    toggle_attribute_name="second_toggle",
                    task_panel_slot_index=10,
                    accessibility_label="Second Toggle",
                    action_label="Second Action",
                ),
            )
        )

        result = add_scene_task_panel_items(
            host,
            task_panel,
            layout,
            button_specs=(
                TaskPanelButtonSpec(
                    attr_name="exit_button",
                    control_id="exit",
                    slot_index=0,
                    label="Exit",
                    on_click=lambda: None,
                ),
            ),
            scene_nav_button_specs=(
                TaskPanelSceneNavButtonSpec(
                    attr_name="showcase_button",
                    control_id="showcase",
                    slot_index=4,
                    label="Showcase",
                    target_scene="control_showcase",
                    accessibility_label="Open showcase",
                ),
            ),
            window_toggle_group_spec=TaskPanelWindowToggleGroupSpec(start_index=1),
            window_presentation=presentation,
            window_toggle_slot_overrides={"first": 1, "second": 2},
            tab_sequence_start=40,
        )

        self.assertEqual(1, len(result.scene_nav_buttons))
        self.assertEqual(2, len(result.window_toggle_controls))
        self.assertIs(host.exit_button, task_panel.added_controls[0])
        self.assertIs(host.showcase_button, task_panel.added_controls[1])
        self.assertEqual(1, result.window_toggle_controls[0][1].rect.left)
        self.assertEqual(2, result.window_toggle_controls[1][1].rect.left)
        self.assertEqual(40, host.exit_button.tab_index)
        self.assertEqual(43, host.showcase_button.tab_index)

    def test_add_scene_task_panel_items_clamps_out_of_range_toggle_group_start_to_panel_end(self):
        host = _StubTaskPanelHost()
        task_panel = _StubTaskPanel()
        layout = _StubLayout()
        presentation = _StubWindowPresentation(
            (
                _StubToggleBinding(
                    key="first",
                    toggle_attribute_name="first_toggle",
                    task_panel_slot_index=None,
                    accessibility_label="First Toggle",
                    action_label="First Action",
                ),
                _StubToggleBinding(
                    key="second",
                    toggle_attribute_name="second_toggle",
                    task_panel_slot_index=None,
                    accessibility_label="Second Toggle",
                    action_label="Second Action",
                ),
            )
        )

        result = add_scene_task_panel_items(
            host,
            task_panel,
            layout,
            button_specs=(
                TaskPanelButtonSpec(
                    attr_name="exit_button",
                    control_id="exit",
                    slot_index=0,
                    label="Exit",
                    on_click=lambda: None,
                ),
            ),
            window_toggle_group_spec=TaskPanelWindowToggleGroupSpec(start_index=99),
            window_presentation=presentation,
        )

        self.assertEqual(2, len(result.window_toggle_controls))
        self.assertEqual(1, result.window_toggle_controls[0][1].rect.left)
        self.assertEqual(2, result.window_toggle_controls[1][1].rect.left)

    def test_add_window_control_and_label_and_button_helpers(self):
        window = _StubWindow()
        controls = []

        label = add_window_label(window, controls, "lbl", Rect(1, 2, 120, 20), "Hello")
        button = add_window_button(window, controls, "btn", Rect(3, 4, 130, 26), "Run", lambda: None)
        raw_control = object()
        added = add_window_control(window, controls, raw_control)

        self.assertEqual("Hello", label.text)
        self.assertEqual("left", label.align)
        self.assertEqual("Run", button.text)
        self.assertEqual("lbl", label.control_id)
        self.assertEqual("btn", button.control_id)
        self.assertEqual(3, len(controls))
        self.assertEqual(3, len(window.added))
        self.assertIs(added, controls[2])
        self.assertIs(raw_control, added)

    def test_add_right_anchored_task_panel_button_includes_task_panel_focus_cycle_by_default(self):
        host = _StubTaskPanelHost()
        task_panel = _StubTaskPanel()
        task_panel.rect = Rect(0, 100, 500, 50)

        button = add_right_anchored_task_panel_button(
            host,
            task_panel,
            RightAnchoredTaskPanelButtonSpec(
                attr_name="help_button",
                control_id="help",
                label="Help",
                on_click=lambda: None,
                width=124,
                height=30,
                top_offset=10,
                right_padding=16,
                style="angle",
            ),
        )

        self.assertIs(button, host.help_button)
        self.assertEqual(0, button.tab_index)
        self.assertFalse(getattr(button, "task_panel_focus_excluded", False))

    def test_add_right_anchored_task_panel_button_appends_after_existing_ordered_controls(self):
        host = _StubTaskPanelHost()
        task_panel = _StubTaskPanel()
        layout = _StubLayout()

        add_task_panel_button(
            task_panel,
            layout,
            control_id="exit",
            slot_index=0,
            label="Exit",
            on_click=lambda: None,
        )
        add_task_panel_button(
            task_panel,
            layout,
            control_id="systems",
            slot_index=1,
            label="System",
            on_click=lambda: None,
        )

        help_button = add_right_anchored_task_panel_button(
            host,
            task_panel,
            RightAnchoredTaskPanelButtonSpec(
                attr_name="help_button",
                control_id="help",
                label="Help",
                on_click=lambda: None,
                width=124,
                height=30,
                top_offset=10,
                right_padding=16,
                style="angle",
            ),
        )

        self.assertEqual(2, help_button.tab_index)

    def test_add_window_button_row_places_buttons_horizontally(self):
        window = _StubWindow()
        controls = []

        buttons = add_window_button_row(
            window,
            controls,
            x=10,
            y=20,
            width=100,
            height=30,
            gap=8,
            specs=(
                ("btn_one", "One", lambda: None),
                ("btn_two", "Two", lambda: None, "round"),
            ),
        )

        self.assertEqual(2, len(buttons))
        self.assertEqual("btn_one", buttons[0].control_id)
        self.assertEqual("btn_two", buttons[1].control_id)
        self.assertEqual(10, buttons[0].rect.left)
        self.assertEqual(118, buttons[1].rect.left)
        self.assertEqual(2, len(controls))
        self.assertEqual(2, len(window.added))

    def test_make_spec_builders_provide_compact_defaults(self):
        window = make_window_toggle_spec("logs", "_logs_feature", task_panel_slot_index=6)
        self.assertEqual("logs", window.key)
        self.assertEqual("_logs_feature", window.feature_attribute_name)
        self.assertEqual("logs_toggle_window", window.toggle_attribute_name)
        self.assertEqual("win_logs", window.action_name)
        self.assertEqual("show_logs", window.task_panel_toggle_button_id)
        self.assertEqual("Logs", window.task_panel_label)
        self.assertEqual(6, window.task_panel_slot_index)

        nav = make_scene_nav_action("nav_logs", label="Go to Logs", target_scene="logs")
        self.assertEqual("scene_nav", nav.kind)
        self.assertEqual("logs", nav.target)
        self.assertEqual("Scenes", nav.category)

        exit_spec = make_exit_action()
        self.assertEqual("exit", exit_spec.action_id)
        self.assertEqual("exit", exit_spec.kind)

        palette = make_palette_open_action()
        self.assertEqual("palette_open", palette.action_id)
        self.assertEqual("palette_open", palette.kind)
        self.assertIsNone(palette.category)

        accessibility = make_static_accessibility_spec("save_button", label="Save")
        self.assertEqual("save_button", accessibility.control_attr)
        self.assertEqual("button", accessibility.role)
        self.assertEqual("Save", accessibility.label)

    def test_build_tab_builder_specs_applies_builder_naming_defaults(self):
        specs = build_tab_builder_specs(
            (
                ("filter", "Filter"),
                ("tilemap", "TileMap"),
            )
        )

        self.assertEqual(["filter", "tilemap"], [spec.key for spec in specs])
        self.assertEqual(["Filter", "TileMap"], [spec.label for spec in specs])
        self.assertEqual(["_build_filter_tab", "_build_tilemap_tab"], [spec.builder_attr for spec in specs])

    def test_create_tab_control_from_specs_materializes_tab_items(self):
        specs = build_tab_builder_specs((("filter", "Filter"), ("event", "Event")))

        tab = create_tab_control_from_specs(
            "tabs",
            Rect(0, 0, 300, 120),
            specs,
            selected_key="event",
            on_change=lambda _key: None,
        )

        self.assertEqual("event", tab.selected_key)
        self.assertEqual(["filter", "event"], [item.key for item in tab.items()])
        self.assertEqual(["Filter", "Event"], [item.label for item in tab.items()])

    def test_register_window_tab_builder_specs_registers_builder_pairs(self):
        class _Feature:
            def _build_filter_tab(self, _host, _rect):
                return ["filter"]

            def _build_event_tab(self, _host, _rect):
                return ["event"]

        class _TabManager:
            def __init__(self):
                self.calls = []

            def register(self, key, controls):
                self.calls.append((str(key), list(controls)))

        feature = _Feature()
        tab_manager = _TabManager()
        specs = build_tab_builder_specs((("filter", "Filter"), ("event", "Event")))

        register_window_tab_builder_specs(
            tab_manager,
            feature,
            object(),
            Rect(0, 0, 100, 80),
            specs,
        )

        self.assertEqual(
            [("filter", ["filter"]), ("event", ["event"])],
            tab_manager.calls,
        )

    def test_setup_feature_presenter_tabs_adds_control_and_registers_builders(self):
        class _Feature:
            def _build_filter_tab(self, _host, _rect):
                return ["filter"]

        class _TabManager:
            def __init__(self):
                self.calls = []
                self.activated = None

            def register(self, key, controls):
                self.calls.append((str(key), list(controls)))

            def activate(self, key):
                self.activated = key

        presenter = _StubPresenter()
        feature = _Feature()
        tab_manager = _TabManager()
        specs = build_tab_builder_specs((("filter", "Filter"),))

        tab = setup_feature_presenter_tabs(
            presenter,
            control_id="tabs",
            tab_rect=Rect(0, 0, 320, 160),
            tab_specs=specs,
            selected_key="filter",
            on_change=lambda _key: None,
            tab_manager=tab_manager,
            feature=feature,
            host=object(),
            tab_content_rect=Rect(0, 40, 320, 120),
        )

        self.assertIs(tab, presenter.controls[0])
        self.assertEqual([("filter", ["filter"])], tab_manager.calls)
        self.assertEqual("filter", tab_manager.activated)

    def test_compute_tabbed_window_layout_returns_expected_body_and_content_rects(self):
        content = Rect(10, 20, 300, 200)

        body_rect, body_content_rect = compute_tabbed_window_layout(
            content,
            tab_height=36,
            tab_rows=2,
            padding=0,
            min_content_height=60,
        )

        self.assertEqual(Rect(10, 20, 300, 200), body_rect)
        self.assertEqual(Rect(10, 92, 300, 128), body_content_rect)

    def test_active_tab_update_router_runs_only_active_handler(self):
        router = ActiveTabUpdateRouter()
        calls = []

        router.register("a", lambda host, dt: calls.append(("a", host, dt)))
        router.register("b", lambda host, dt: calls.append(("b", host, dt)))

        ran = router.run("b", "HOST", 0.25)

        self.assertTrue(ran)
        self.assertEqual([("b", "HOST", 0.25)], calls)
        self.assertEqual(("a", "b"), router.keys())

    def test_register_tab_update_handlers_batches_registration(self):
        router = ActiveTabUpdateRouter()
        calls = []

        register_tab_update_handlers(
            router,
            (
                ("locale", lambda: calls.append("locale")),
                ("particle", lambda: calls.append("particle")),
            ),
        )

        self.assertTrue(router.run("locale"))
        self.assertTrue(router.run("particle"))
        self.assertFalse(router.run("missing"))
        self.assertEqual(["locale", "particle"], calls)

        self.assertTrue(router.unregister("locale"))
        self.assertFalse(router.unregister("locale"))

    def test_register_tooltip_specs_registers_all_messages(self):
        manager = _StubTooltipManager()
        a = object()
        b = object()

        register_tooltip_specs(
            manager,
            (
                (a, "First tooltip"),
                (b, "Second tooltip"),
            ),
        )

        self.assertEqual([(a, "First tooltip"), (b, "Second tooltip")], manager.calls)

    def test_instantiate_features_from_specs_sets_host_attributes(self):
        class _Host:
            pass

        host = _Host()
        specs = [
            _StubFeatureSpec(attr_name="first_feature", factory=lambda: "one"),
            _StubFeatureSpec(attr_name="second_feature", factory=lambda: "two"),
        ]

        instantiate_features_from_specs(host, specs)

        self.assertEqual("one", getattr(host, "first_feature"))
        self.assertEqual("two", getattr(host, "second_feature"))

    def test_register_features_from_specs_registers_host_features(self):
        class _Host:
            pass

        host = _Host()
        host.first_feature = "one"
        host.second_feature = "two"
        app = _StubRegisterApp()
        specs = [
            _StubFeatureSpec(attr_name="first_feature", factory=lambda: None),
            _StubFeatureSpec(attr_name="second_feature", factory=lambda: None),
        ]

        register_features_from_specs(app, host, specs)

        self.assertEqual([("one", host), ("two", host)], app.calls)

    def test_register_window_presentation_specs_forwards_spec_fields(self):
        presentation = _StubWindowPresentationRegistrar()
        specs = [
            _StubWindowSpec(
                key="extra",
                feature_attribute_name="extra_demo",
                toggle_attribute_name="extra_toggle",
                action_name="toggle_extra",
                action_label="Toggle Extra",
                task_panel_toggle_button_id="extra_btn",
                task_panel_label="Extra",
                task_panel_style="toggle",
                task_panel_slot_index=1,
                accessibility_label="Extra Window",
            )
        ]

        register_window_presentation_specs(presentation, specs)

        self.assertEqual(1, len(presentation.calls))
        key, kwargs = presentation.calls[0]
        self.assertEqual("extra", key)
        self.assertEqual("extra_demo", kwargs["feature_attribute_name"])
        self.assertEqual("extra_toggle", kwargs["toggle_attribute_name"])
        self.assertEqual("toggle_extra", kwargs["action_name"])
        self.assertEqual("Toggle Extra", kwargs["action_label"])
        self.assertEqual("extra_btn", kwargs["task_panel_toggle_button_id"])
        self.assertEqual("Extra", kwargs["task_panel_label"])
        self.assertEqual("toggle", kwargs["task_panel_style"])
        self.assertEqual(1, kwargs["task_panel_slot_index"])
        self.assertEqual("Extra Window", kwargs["accessibility_label"])

    # ------------------------------------------------------------------
    # TabLayoutContext
    # ------------------------------------------------------------------

    def _make_ctx(self, left=10, top=20, width=400, height=300, *, pad=8):
        from pygame import Rect
        window = _StubWindow()
        rect = Rect(left, top, width, height)
        return TabLayoutContext(window, rect, pad=pad), window

    def test_tab_layout_context_geometry_properties(self):
        ctx, _ = self._make_ctx(left=10, top=20, width=400, height=300, pad=8)
        self.assertEqual(10 + 8, ctx.x)
        self.assertEqual(20 + 8, ctx.y)
        self.assertEqual(400 - 16, ctx.width)
        self.assertEqual(8, ctx.pad)

    def test_tab_layout_context_add_label_default_advance(self):
        ctx, window = self._make_ctx()
        start_y = ctx.y
        ctx.add_label("lbl1", 22, "Hello")
        # default advance = height + 8
        self.assertEqual(start_y + 22 + 8, ctx.y)
        self.assertEqual(1, len(window.added))
        self.assertEqual("lbl1", window.added[0].control_id)

    def test_tab_layout_context_add_label_explicit_advance(self):
        ctx, _ = self._make_ctx()
        start_y = ctx.y
        ctx.add_label("lbl", 20, "Text", advance=30)
        self.assertEqual(start_y + 30, ctx.y)

    def test_tab_layout_context_add_label_advance_zero_keeps_y(self):
        ctx, _ = self._make_ctx()
        start_y = ctx.y
        ctx.add_label("lbl", 26, "Side label", advance=0)
        self.assertEqual(start_y, ctx.y)

    def test_tab_layout_context_add_label_custom_width(self):
        ctx, window = self._make_ctx()
        ctx.add_label("lbl", 26, "Narrow", width=60)
        ctrl = window.added[0]
        self.assertEqual(60, ctrl.rect.width)

    def test_tab_layout_context_add_button_default_advance(self):
        ctx, window = self._make_ctx()
        start_y = ctx.y
        ctx.add_button("btn1", 120, 28, "Click", lambda: None)
        self.assertEqual(start_y + 28 + 8, ctx.y)
        self.assertEqual(1, len(window.added))
        self.assertEqual("btn1", window.added[0].control_id)

    def test_tab_layout_context_add_button_x_offset(self):
        ctx, window = self._make_ctx(left=10, pad=8)
        ctx.add_label("lbl", 26, "Side", advance=0)
        ctx.add_control(__import__("gui_do").ButtonControl(
            "btn_offset",
            __import__("pygame").Rect(ctx.x + 70, ctx.y, 100, 28),
            "Go",
            lambda: None,
        ))
        btn = window.added[-1]
        self.assertEqual(ctx.x + 70, btn.rect.left)

    def test_tab_layout_context_add_button_row_advances_correctly(self):
        ctx, window = self._make_ctx()
        start_y = ctx.y
        ctx.add_button_row(height=28, gap=8, width=100, specs=(
            ("r1", "A", lambda: None),
            ("r2", "B", lambda: None),
        ))
        self.assertEqual(start_y + 28 + 8, ctx.y)
        self.assertEqual(2, len(window.added))

    def test_tab_layout_context_advance_moves_cursor(self):
        ctx, _ = self._make_ctx()
        start_y = ctx.y
        ctx.advance(15)
        self.assertEqual(start_y + 15, ctx.y)

    def test_tab_layout_context_remaining_height(self):
        from pygame import Rect
        window = _StubWindow()
        rect = Rect(0, 0, 400, 300)
        ctx = TabLayoutContext(window, rect, pad=8)
        # After construction y = 8, rect.bottom = 300
        self.assertEqual(300 - 8, ctx.remaining_height())
        self.assertEqual(300 - 8 - 8, ctx.remaining_height(margin=8))

    def test_tab_layout_context_build_returns_copy(self):
        ctx, _ = self._make_ctx()
        ctx.add_label("l1", 20, "A")
        ctx.add_label("l2", 20, "B")
        result = ctx.build()
        self.assertEqual(2, len(result))
        # build() returns a copy; mutating it does not affect ctx internals
        result.clear()
        self.assertEqual(2, len(ctx.build()))

    def test_tab_layout_context_add_control_no_advance(self):
        import gui_do
        import pygame
        ctx, window = self._make_ctx()
        start_y = ctx.y
        ctrl = gui_do.LabelControl("raw", pygame.Rect(ctx.x, ctx.y, 200, 20), "raw")
        ctx.add_control(ctrl)
        # add_control does NOT advance y
        self.assertEqual(start_y, ctx.y)
        self.assertIn(ctrl, window.added)


if __name__ == "__main__":
    unittest.main()
