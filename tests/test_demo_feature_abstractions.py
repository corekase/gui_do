import unittest
from unittest.mock import patch
from pygame import Rect

from demo_features.feature_abstractions import (
    add_task_panel_button,
    add_window_toggle_task_panel_controls,
    apply_window_toggle_accessibility,
    apply_accessibility_sequence,
    bind_input_map_actions,
    build_tools_menu_entries,
    collect_window_toggle_controls,
    create_presented_anchored_window,
    ensure_scene_scheduler,
    initialize_locale_registry,
    instantiate_features_from_specs,
    prewarm_runtime_scenes,
    register_features_from_specs,
    register_window_presentation_specs,
    register_tooltip_specs,
    register_descriptors,
    register_companion_logic_features,
    register_window_toggle_tooltips,
    resolve_canvas_local_point,
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

    def set_presenter(self, presenter):
        self.presenter = presenter


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


class _StubToggleBinding:
    def __init__(
        self,
        *,
        key: str,
        toggle_attr: str | None,
        task_panel_slot_index: int | None,
        accessibility_label: str | None,
        action_label: str | None,
        task_panel_button_id: str | None = None,
        task_panel_label: str | None = None,
        task_panel_style: str = "toggle",
    ):
        self.key = str(key)
        self.toggle_attr = toggle_attr
        self.task_panel_slot_index = task_panel_slot_index
        self.accessibility_label = accessibility_label
        self.action_label = action_label
        self.task_panel_button_id = task_panel_button_id
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


class _StubToggleHost:
    pass


class _StubLayout:
    def linear(self, index: int):
        return Rect(int(index), 0, 120, 30)


class _StubTaskPanel:
    def __init__(self):
        self.added_controls = []

    def add(self, control):
        self.added_controls.append(control)
        return control


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
        feature_attr: str,
        toggle_attr: str,
        action_name: str,
        action_label: str,
        task_panel_button_id: str,
        task_panel_label: str,
        task_panel_style: str,
        task_panel_slot_index: int,
        tab_before_showcase: bool,
        accessibility_label: str,
    ):
        self.key = key
        self.feature_attr = feature_attr
        self.toggle_attr = toggle_attr
        self.action_name = action_name
        self.action_label = action_label
        self.task_panel_button_id = task_panel_button_id
        self.task_panel_label = task_panel_label
        self.task_panel_style = task_panel_style
        self.task_panel_slot_index = task_panel_slot_index
        self.tab_before_showcase = tab_before_showcase
        self.accessibility_label = accessibility_label


class _StubPointerPacket:
    def __init__(self, *, local_pos=None, pos=None):
        self.local_pos = local_pos
        self.pos = pos


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

    def test_collect_window_toggle_controls_returns_sorted_existing_controls(self):
        host = _StubToggleHost()
        host.first_toggle = _StubToggleControl()
        host.second_toggle = _StubToggleControl()
        presentation = _StubToggleWindowPresentation(
            (
                _StubToggleBinding(
                    key="second",
                    toggle_attr="second_toggle",
                    task_panel_slot_index=2,
                    accessibility_label="Second",
                    action_label="Second Action",
                ),
                _StubToggleBinding(
                    key="missing",
                    toggle_attr="missing_toggle",
                    task_panel_slot_index=3,
                    accessibility_label="Missing",
                    action_label="Missing Action",
                ),
                _StubToggleBinding(
                    key="first",
                    toggle_attr="first_toggle",
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
                    toggle_attr="first_toggle",
                    task_panel_slot_index=1,
                    accessibility_label="First Toggle",
                    action_label="First Action",
                ),
                _StubToggleBinding(
                    key="second",
                    toggle_attr="second_toggle",
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
                    toggle_attr="later_toggle",
                    task_panel_slot_index=3,
                    accessibility_label="Later",
                    action_label="Later Action",
                ),
                _StubToggleBinding(
                    key="first",
                    toggle_attr="first_toggle",
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
                    toggle_attr="first_toggle",
                    task_panel_slot_index=1,
                    accessibility_label=None,
                    action_label="First Action",
                ),
                first_toggle,
            ),
            (
                _StubToggleBinding(
                    key="second",
                    toggle_attr="second_toggle",
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
                key="systems",
                feature_attr="systems_demo",
                toggle_attr="systems_toggle",
                action_name="toggle_systems",
                action_label="Toggle Systems",
                task_panel_button_id="systems_btn",
                task_panel_label="Systems",
                task_panel_style="toggle",
                task_panel_slot_index=1,
                tab_before_showcase=True,
                accessibility_label="Systems Window",
            )
        ]

        register_window_presentation_specs(presentation, specs)

        self.assertEqual(1, len(presentation.calls))
        key, kwargs = presentation.calls[0]
        self.assertEqual("systems", key)
        self.assertEqual("systems_demo", kwargs["feature_attr"])
        self.assertEqual("systems_toggle", kwargs["toggle_attr"])
        self.assertEqual("toggle_systems", kwargs["action_name"])
        self.assertEqual("Toggle Systems", kwargs["action_label"])
        self.assertEqual("systems_btn", kwargs["task_panel_button_id"])
        self.assertEqual("Systems", kwargs["task_panel_label"])
        self.assertEqual("toggle", kwargs["task_panel_style"])
        self.assertEqual(1, kwargs["task_panel_slot_index"])
        self.assertTrue(kwargs["tab_before_showcase"])
        self.assertEqual("Systems Window", kwargs["accessibility_label"])


if __name__ == "__main__":
    unittest.main()
