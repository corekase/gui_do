# gui_do Tutorial

## 1. Introduction

gui_do is a data-driven GUI framework built on pygame. You describe application composition with declarative specs, then write imperative feature behavior in clearly scoped lifecycle methods. That split keeps application wiring predictable while feature logic stays readable and testable.

In this tutorial, you will build Pulse Desk: a small multi-feature dashboard with a Counter feature and an Activity Log feature. The app has reactive labels, button interactions, keyboard shortcuts, routed runtime wiring, and clean shutdown behavior.

Prerequisites are standard Python development skills, pip, pygame, and numpy. No prior GUI-framework experience or pygame internals are required.

For deeper system detail while you follow this guide, keep MANUAL.md open, especially [8.1 Application Bootstrap and Host Configuration](MANUAL.md#81-application-bootstrap-and-host-configuration), [8.2 Feature Lifecycle and Feature Types](MANUAL.md#82-feature-lifecycle-and-feature-types), [8.3 Events, Actions, Input Mapping, and Routing](MANUAL.md#83-events-actions-input-mapping-and-routing), and [8.4 State and Observables](MANUAL.md#84-state-and-observables).

## 2. Core Concepts

### Declarative specs vs imperative wiring

gui_do treats app composition as data. You declare scenes, features, and actions using specs such as HostApplicationBindingSpec, SceneBundleBindingSpec, FeatureSpec, and ActionSpec. Then bootstrap reads those specs and wires runtime systems.

Why this matters:
- Feature code stays focused on behavior.
- Wiring is consistent and easy to test.
- Refactors inside feature packages do not force bootstrap rewrites when package surfaces stay stable.

### Reactive state

ObservableValue is a value container with subscriptions. When .value changes, subscribers run immediately. You can connect UI text updates to state changes without frame-by-frame polling.

ObservableList and ObservableDict provide the same model for collections. ComputedValue is useful for derived state that should stay in sync with source values.

```python
from gui_do import ObservableValue

count = ObservableValue(0)
unsubscribe = count.subscribe(lambda value: print(f"count changed -> {value}"))
count.value = 1
unsubscribe()
```

### Feature lifecycle

The main lifecycle hooks are:
- build(host): construct controls and scene graph.
- bind_runtime(host): connect subscriptions, actions, and runtime wiring.
- handle_event(host, event): feature-level event handling.
- on_update(host): per-frame feature update.
- draw(host, surface, theme): custom drawing if needed.
- shutdown_runtime(host): remove subscriptions and handlers.

The framework guarantee is important: all features in a scene complete build before any bind_runtime runs. That lets features safely subscribe to shared state and reference sibling feature runtime objects during bind_runtime. As a rule, subscribe and register actions in bind_runtime, then tear down in shutdown_runtime.

## 3. Installation and Setup

Install from repository root:

```bash
python -m pip install -e . --no-deps
```

Dependencies:
- pygame
- numpy

Verify install:

```bash
python -c "import gui_do; print(gui_do.__version__)"
```

Minimal startup imports:

```python
from gui_do import (
    Feature,
    HostApplicationBindingSpec,
    build_host_application_config,
    bootstrap_host_application,
)
```

You have two startup paths:
- Declarative bootstrap with build_host_application_config + bootstrap_host_application (recommended, used in this tutorial).
- Manual GuiApplication construction (advanced path; see MANUAL.md).

## 4. Your First Feature

### Step 1. Define the feature class

Feature is the default choice for visual features with standard lifecycle hooks. DirectFeature and RoutedFeature are specialized variants covered later.

```python
from gui_do import Feature

class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")

    def build(self, host) -> None:
        pass
```

### Step 2. Add a control in build

Controls are scene-graph nodes inside your feature region. host.screen_rect is the full available canvas in this simple one-scene app.

```python
from gui_do import LabelControl, PanelControl

def build(self, host) -> None:
    self._root = PanelControl("counter_root", host.screen_rect, draw_background=True)
    self._title = LabelControl("counter_title", (24, 24, 320, 32), "Pulse Desk")
    self._root.add(self._title)
    host.app.add(self._root, scene_name="main")
```

### Step 3. Declare the host config

HostApplicationBindingSpec describes app composition. SceneBundleBindingSpec declares scene setup. FeatureSpec tells bootstrap which host attribute receives each feature instance.

```python
from gui_do import FeatureSpec, HostApplicationBindingSpec, SceneBundleBindingSpec, build_host_application_config

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1000, 620),
        window_title="Pulse Desk",
        fonts={"default": {"size": 16}},
        initial_scene_name="main",
        scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
        feature_entries=(FeatureSpec("counter_feature", CounterFeature),),
    )
)
```

### Step 4. Bootstrap and run

bootstrap_host_application reads specs, creates core managers, registers features, runs feature build/bind lifecycle, and leaves you with a host whose app is ready to run.

```python
class PulseDeskHost:
    def __init__(self) -> None:
        bootstrap_host_application(self, config)

PulseDeskHost().app.run_entrypoint(target_fps=60)
```

### Step 5. Full listing so far

```python
from gui_do import (
    Feature,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    PanelControl,
    SceneBundleBindingSpec,
    build_host_application_config,
    bootstrap_host_application,
)


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")

    def build(self, host) -> None:
        self._root = PanelControl("counter_root", host.screen_rect, draw_background=True)
        self._title = LabelControl("counter_title", (24, 24, 320, 32), "Pulse Desk")
        self._root.add(self._title)
        host.app.add(self._root, scene_name="main")


class PulseDeskHost:
    def __init__(self) -> None:
        config = build_host_application_config(
            HostApplicationBindingSpec(
                display_size=(1000, 620),
                window_title="Pulse Desk",
                fonts={"default": {"size": 16}},
                initial_scene_name="main",
                scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
                feature_entries=(FeatureSpec("counter_feature", CounterFeature),),
            )
        )
        bootstrap_host_application(self, config)


if __name__ == "__main__":
    PulseDeskHost().app.run_entrypoint(target_fps=60)
```

## 5. Reactive State: Making the UI Respond

### Step 1. Add ObservableValue

Use observables to express state changes once, then subscribe UI updates to them.

```python
from gui_do import ObservableValue

self._count = ObservableValue(0)
```

### Step 2. Add a button

The button updates observable state. UI updates should not be manually pushed from multiple places.

```python
from gui_do import ButtonControl

self._increment = ButtonControl(
    "increment_button",
    (24, 140, 180, 36),
    "Increment",
    on_click=self._increment_count,
)
self._root.add(self._increment)
```

### Step 3. Subscribe in bind_runtime

bind_runtime is the right place because controls are built and mounted by then.

```python
def bind_runtime(self, host) -> None:
    self._sub = self._count.subscribe(lambda value: setattr(self._value_label, "text", f"Count: {value}"))
```

### Step 4. Unsubscribe in shutdown_runtime

Subscriptions retain references. Always tear them down during shutdown to avoid stale callbacks.

```python
def shutdown_runtime(self, host) -> None:
    if self._sub is not None:
        self._sub()
        self._sub = None
```

### Step 5. Full listing so far

```python
from gui_do import (
    ButtonControl,
    Feature,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    ObservableValue,
    PanelControl,
    SceneBundleBindingSpec,
    build_host_application_config,
    bootstrap_host_application,
)


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self._count = ObservableValue(0)
        self._sub = None

    def build(self, host) -> None:
        self._root = PanelControl("counter_root", host.screen_rect, draw_background=True)
        self._title = LabelControl("counter_title", (24, 24, 320, 32), "Pulse Desk")
        self._value_label = LabelControl("counter_value", (24, 80, 320, 32), "Count: 0")
        self._increment = ButtonControl(
            "increment_button",
            (24, 140, 180, 36),
            "Increment",
            on_click=self._increment_count,
        )
        self._root.add(self._title)
        self._root.add(self._value_label)
        self._root.add(self._increment)
        host.app.add(self._root, scene_name="main")

    def bind_runtime(self, host) -> None:
        self._sub = self._count.subscribe(lambda value: setattr(self._value_label, "text", f"Count: {value}"))

    def shutdown_runtime(self, host) -> None:
        if self._sub is not None:
            self._sub()
            self._sub = None

    def _increment_count(self) -> None:
        self._count.value += 1


class PulseDeskHost:
    def __init__(self) -> None:
        config = build_host_application_config(
            HostApplicationBindingSpec(
                display_size=(1000, 620),
                window_title="Pulse Desk",
                fonts={"default": {"size": 16}},
                initial_scene_name="main",
                scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
                feature_entries=(FeatureSpec("counter_feature", CounterFeature),),
            )
        )
        bootstrap_host_application(self, config)


if __name__ == "__main__":
    PulseDeskHost().app.run_entrypoint(target_fps=60)
```

## 6. Feature Types

Use feature types intentionally:

- Feature: the standard choice for most visual features with lifecycle hooks and control trees.
- DirectFeature: direct event/update/draw hooks for high-control rendering paths when bypassing normal control behavior is intentional.
- DirectFeature (full-control emphasis): same subtype, but used when you want explicit ownership of direct lifecycle hooks rather than default visual composition flows.
- LogicFeature: non-visual feature for domain logic, background orchestration, and cross-feature coordination.
- RoutedFeature: Feature subtype with topic-based message routing and declarative runtime wiring through RoutedRuntimeSpec and RoutedFeatureLifecycleSpec.

In Pulse Desk, the counter panel remains a Feature while the log panel becomes a RoutedFeature so we can declaratively wire shortcut help and routed runtime behavior.

## 7. A Second Feature and Feature Communication

### Step 1. Add the second feature

Create ActivityLogFeature with its own visual area and responsibility.

```python
from gui_do import LabelControl, PanelControl, RoutedFeature

class ActivityLogFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("activity_log", scene_name="main")

    def build(self, host) -> None:
        self._root = PanelControl("log_root", (520, 24, 440, 520), draw_background=True)
        self._title = LabelControl("log_title", (536, 40, 300, 30), "Activity Log")
        self._last = LabelControl("log_last", (536, 84, 400, 30), "Last event: none")
        self._root.add(self._title)
        self._root.add(self._last)
        host.app.add(self._root, scene_name="main")
```

### Step 2. Shared state option

For tightly coupled features, shared observables on host can be enough.

```python
host.shared_count = self._count
```

Use this when direct coupling is acceptable. For looser coupling, use feature messaging.

### Step 3. Feature messaging with a concrete FeatureMessage subclass

Typed message envelopes keep payload intent explicit.

```python
from gui_do import FeatureMessage

class CounterChangedMessage(FeatureMessage):
    def __init__(self, sender: str, target: str, count: int) -> None:
        super().__init__(
            sender=sender,
            target=target,
            payload={"topic": "counter.changed", "count": count},
        )
```

Publish from CounterFeature:

```python
def _publish_count_change(self, host) -> None:
    target = host.app.feature_manager.get("activity_log")
    if target is not None:
        target.enqueue_message(CounterChangedMessage(self.name, "activity_log", self._count.value))
```

Receive in ActivityLogFeature:

```python
def message_handlers(self):
    return {"counter.changed": self._on_counter_changed}

def _on_counter_changed(self, host, message):
    self._last.text = f"Last event: count -> {message.get('count', 0)}"
```

### Step 4. Full listing with two communicating features

```python
from gui_do import (
    ButtonControl,
    Feature,
    FeatureMessage,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    ObservableValue,
    PanelControl,
    RoutedFeature,
    SceneBundleBindingSpec,
    build_host_application_config,
    bootstrap_host_application,
)


class CounterChangedMessage(FeatureMessage):
    def __init__(self, sender: str, target: str, count: int) -> None:
        super().__init__(sender=sender, target=target, payload={"topic": "counter.changed", "count": count})


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self._count = ObservableValue(0)
        self._sub = None

    def build(self, host) -> None:
        self._root = PanelControl("counter_root", (24, 24, 460, 520), draw_background=True)
        self._title = LabelControl("counter_title", (40, 40, 320, 32), "Pulse Desk Counter")
        self._value_label = LabelControl("counter_value", (40, 84, 320, 32), "Count: 0")
        self._increment = ButtonControl("increment_button", (40, 140, 180, 36), "Increment", on_click=lambda: self._increment_count(host))
        self._root.add(self._title)
        self._root.add(self._value_label)
        self._root.add(self._increment)
        host.app.add(self._root, scene_name="main")
        host.shared_count = self._count

    def bind_runtime(self, host) -> None:
        self._sub = self._count.subscribe(lambda value: setattr(self._value_label, "text", f"Count: {value}"))

    def shutdown_runtime(self, host) -> None:
        if self._sub is not None:
            self._sub()
            self._sub = None

    def _increment_count(self, host) -> None:
        self._count.value += 1
        target = host.app.feature_manager.get("activity_log")
        if target is not None:
            target.enqueue_message(CounterChangedMessage(self.name, "activity_log", self._count.value))


class ActivityLogFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("activity_log", scene_name="main")

    def build(self, host) -> None:
        self._root = PanelControl("log_root", (520, 24, 440, 520), draw_background=True)
        self._title = LabelControl("log_title", (536, 40, 320, 32), "Activity Log")
        self._last = LabelControl("log_last", (536, 84, 400, 32), "Last event: none")
        self._shared = LabelControl("log_shared", (536, 124, 400, 32), "Shared count mirror: 0")
        self._root.add(self._title)
        self._root.add(self._last)
        self._root.add(self._shared)
        host.app.add(self._root, scene_name="main")

    def bind_runtime(self, host) -> None:
        shared = getattr(host, "shared_count", None)
        if shared is not None:
            self._shared_sub = shared.subscribe(lambda value: setattr(self._shared, "text", f"Shared count mirror: {value}"))

    def shutdown_runtime(self, host) -> None:
        unsub = getattr(self, "_shared_sub", None)
        if unsub is not None:
            unsub()
            self._shared_sub = None

    def message_handlers(self):
        return {"counter.changed": self._on_counter_changed}

    def _on_counter_changed(self, host, message):
        self._last.text = f"Last event: count -> {message.get('count', 0)}"


class PulseDeskHost:
    def __init__(self) -> None:
        config = build_host_application_config(
            HostApplicationBindingSpec(
                display_size=(1000, 620),
                window_title="Pulse Desk",
                fonts={"default": {"size": 16}},
                initial_scene_name="main",
                scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
                feature_entries=(
                    FeatureSpec("counter_feature", CounterFeature),
                    FeatureSpec("log_feature", ActivityLogFeature),
                ),
            )
        )
        bootstrap_host_application(self, config)


if __name__ == "__main__":
    PulseDeskHost().app.run_entrypoint(target_fps=60)
```

## 8. Actions and Keyboard Shortcuts

### Step 1. Declare an ActionSpec

ActionSpec is declarative registration in host config. For a keyboard shortcut, provide key. In this app we declare a built-in palette action so users can open command search with a key.

```python
from gui_do import ActionSpec

action_entries=(
    ActionSpec(action_id="palette_open", label="Open Command Palette", kind="palette_open", key=ord("p")),
),
```

### Step 2. Bind a plain feature action callback

In the current public API, plain features use register_action and bind_key on host.app.actions, then unbind and unregister in shutdown_runtime.

```python
def bind_runtime(self, host) -> None:
    host.app.actions.register_action("counter.increment", self._on_increment_action)
    host.app.actions.bind_key(ord("i"), "counter.increment", scene="main")

def shutdown_runtime(self, host) -> None:
    host.app.actions.unbind_key(ord("i"), "counter.increment", scene="main")
    host.app.actions.unregister_action("counter.increment")
```

### Step 3. RoutedFeature shortcut wiring with RoutedRuntimeSpec

Routed runtime can declaratively register hotkeys and shortcut overlay wiring. bind_routed_feature_lifecycle and shutdown_routed_feature_lifecycle apply lifecycle-safe setup and teardown.

```python
from gui_do import (
    ActionHotkeySpec,
    RoutedFeatureLifecycleSpec,
    RoutedRuntimeSpec,
    ShortcutOverlaySpec,
    bind_routed_feature_lifecycle,
    shutdown_routed_feature_lifecycle,
)

self._lifecycle_spec = RoutedFeatureLifecycleSpec(
    runtime_spec=RoutedRuntimeSpec(
        scene_name="main",
        action_hotkeys=(
            ActionHotkeySpec(action_name="counter.reset", handler=self._on_reset_action, key=ord("r"), scene_name="main"),
            ActionHotkeySpec(action_name="help.toggle", handler=self._toggle_shortcuts, key=ord("h"), scene_name="main"),
        ),
        shortcut_overlays=(
            ShortcutOverlaySpec(attr_name="_shortcut_overlay", toggle_action_name="help.toggle"),
        ),
    )
)
```

### Step 4. Full listing with shortcuts

```python
from gui_do import (
    ActionHotkeySpec,
    ActionSpec,
    ButtonControl,
    Feature,
    FeatureMessage,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    ObservableValue,
    PanelControl,
    RoutedFeature,
    RoutedFeatureLifecycleSpec,
    RoutedRuntimeSpec,
    SceneBundleBindingSpec,
    ShortcutOverlaySpec,
    bind_routed_feature_lifecycle,
    build_host_application_config,
    bootstrap_host_application,
    shutdown_routed_feature_lifecycle,
)


class CounterChangedMessage(FeatureMessage):
    def __init__(self, sender: str, target: str, count: int) -> None:
        super().__init__(sender=sender, target=target, payload={"topic": "counter.changed", "count": count})


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self._count = ObservableValue(0)
        self._sub = None

    def build(self, host) -> None:
        self._root = PanelControl("counter_root", (24, 24, 460, 520), draw_background=True)
        self._title = LabelControl("counter_title", (40, 40, 320, 32), "Pulse Desk Counter")
        self._value_label = LabelControl("counter_value", (40, 84, 320, 32), "Count: 0")
        self._increment = ButtonControl("increment_button", (40, 140, 180, 36), "Increment", on_click=lambda: self._increment_count(host))
        self._root.add(self._title)
        self._root.add(self._value_label)
        self._root.add(self._increment)
        host.app.add(self._root, scene_name="main")
        host.shared_count = self._count

    def bind_runtime(self, host) -> None:
        self._sub = self._count.subscribe(lambda value: setattr(self._value_label, "text", f"Count: {value}"))
        host.app.actions.register_action("counter.increment", self._on_increment_action)
        host.app.actions.bind_key(ord("i"), "counter.increment", scene="main")

    def shutdown_runtime(self, host) -> None:
        if self._sub is not None:
            self._sub()
            self._sub = None
        host.app.actions.unbind_key(ord("i"), "counter.increment", scene="main")
        host.app.actions.unregister_action("counter.increment")

    def _increment_count(self, host) -> None:
        self._count.value += 1
        self._publish_change(host)

    def _on_increment_action(self, event) -> bool:
        self._count.value += 1
        return True

    def _publish_change(self, host) -> None:
        target = host.app.feature_manager.get("activity_log")
        if target is not None:
            target.enqueue_message(CounterChangedMessage(self.name, "activity_log", self._count.value))

    def reset_count(self) -> None:
        self._count.value = 0


class ActivityLogFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("activity_log", scene_name="main")
        self._lifecycle_spec = RoutedFeatureLifecycleSpec(
            runtime_spec=RoutedRuntimeSpec(
                scene_name="main",
                action_hotkeys=(
                    ActionHotkeySpec(action_name="counter.reset", handler=self._on_reset_action, key=ord("r"), scene_name="main"),
                    ActionHotkeySpec(action_name="help.toggle", handler=self._toggle_shortcuts, key=ord("h"), scene_name="main"),
                ),
                shortcut_overlays=(
                    ShortcutOverlaySpec(attr_name="_shortcut_overlay", toggle_action_name="help.toggle"),
                ),
            )
        )

    def build(self, host) -> None:
        self._root = PanelControl("log_root", (520, 24, 440, 520), draw_background=True)
        self._title = LabelControl("log_title", (536, 40, 320, 32), "Activity Log")
        self._last = LabelControl("log_last", (536, 84, 400, 32), "Last event: none")
        self._shared = LabelControl("log_shared", (536, 124, 400, 32), "Shared count mirror: 0")
        self._root.add(self._title)
        self._root.add(self._last)
        self._root.add(self._shared)
        host.app.add(self._root, scene_name="main")

    def bind_runtime(self, host) -> None:
        bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)
        shared = getattr(host, "shared_count", None)
        if shared is not None:
            self._shared_sub = shared.subscribe(lambda value: setattr(self._shared, "text", f"Shared count mirror: {value}"))

    def shutdown_runtime(self, host) -> None:
        unsub = getattr(self, "_shared_sub", None)
        if unsub is not None:
            unsub()
            self._shared_sub = None
        shutdown_routed_feature_lifecycle(self, host, self._lifecycle_spec)

    def message_handlers(self):
        return {"counter.changed": self._on_counter_changed}

    def _on_counter_changed(self, host, message):
        self._last.text = f"Last event: count -> {message.get('count', 0)}"

    def _on_reset_action(self, event) -> bool:
        counter = self._feature_manager.get("counter") if self._feature_manager is not None else None
        if counter is not None and hasattr(counter, "reset_count"):
            counter.reset_count()
        self._last.text = "Last event: counter reset"
        return True

    def _toggle_shortcuts(self, event) -> bool:
        overlay = getattr(self, "_shortcut_overlay", None)
        if overlay is not None:
            overlay.toggle()
        return True


class PulseDeskHost:
    def __init__(self) -> None:
        config = build_host_application_config(
            HostApplicationBindingSpec(
                display_size=(1000, 620),
                window_title="Pulse Desk",
                fonts={"default": {"size": 16}},
                initial_scene_name="main",
                scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
                feature_entries=(
                    FeatureSpec("counter_feature", CounterFeature),
                    FeatureSpec("log_feature", ActivityLogFeature),
                ),
                action_entries=(
                    ActionSpec(action_id="palette_open", label="Open Command Palette", kind="palette_open", key=ord("p")),
                ),
            )
        )
        bootstrap_host_application(self, config)


if __name__ == "__main__":
    PulseDeskHost().app.run_entrypoint(target_fps=60)
```

## 9. Spec Reference for Builders

This section is a concise builder-oriented map. For full semantics, behavior contracts, and edge cases, see MANUAL.md, especially [8.1 Application Bootstrap and Host Configuration](MANUAL.md#81-application-bootstrap-and-host-configuration), [8.2 Feature Lifecycle and Feature Types](MANUAL.md#82-feature-lifecycle-and-feature-types), [8.3 Events, Actions, Input Mapping, and Routing](MANUAL.md#83-events-actions-input-mapping-and-routing), and [8.4 State and Observables](MANUAL.md#84-state-and-observables).

FeatureSpec declares a feature attribute slot and factory used by bootstrap.

```python
FeatureSpec("counter_feature", CounterFeature)
```

FeatureSpec also defines scene membership indirectly via the produced feature instance scene_name.

```python
class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter", scene_name="main")
```

SceneBundleBindingSpec declares scene creation, initial activation, and optional scene-level facilities.

```python
SceneBundleBindingSpec(scene_name="main", make_initial=True)
```

ActionSpec and ActionHotkeySpec declare named actions and optional key bindings.

```python
ActionSpec(action_id="palette_open", label="Open Palette", kind="palette_open", key=ord("p"))
ActionHotkeySpec(action_name="counter.reset", handler=self._on_reset_action, key=ord("r"), scene_name="main")
```

ShortcutOverlaySpec configures the shortcut discovery overlay.

```python
ShortcutOverlaySpec(attr_name="_shortcut_overlay", toggle_action_name="help.toggle")
```

RoutedRuntimeSpec and RoutedFeatureLifecycleSpec bundle declarative wiring for routed features.

```python
RoutedFeatureLifecycleSpec(
    runtime_spec=RoutedRuntimeSpec(scene_name="main", action_hotkeys=(...), shortcut_overlays=(...))
)
```

Higher-level runtime faculties are declared through RoutedRuntimeSpec fields and corresponding spec types. These include policy/effects/pipelines/durable queue/capability/projection and dependency/workflow/recompute/QoS/health/replay/hot-swap facilities:
- RuntimePolicySpec with RuntimePolicyEngine.
- EffectBindingSpec with EffectLifetimeOrchestrator.
- EventPipelineSpec with EventPipelineRuntime.
- DurableOperationQueueSpec with DurableOperationQueueRuntime.
- CapabilityProviderSpec and CapabilityRequirementSpec with CapabilityContractRuntime.
- ProjectionSpec with ProjectionRuntime.
- FeatureDependencySpec for dependency validation.
- WorkflowSpec with WorkflowCoordinator.
- RecomputeNodeSpec with RecomputeOrchestrator.
- QoSPolicySpec with QoSPolicyRuntime.
- HealthProbeSpec with FeatureHealthRuntime.
- ReplaySpec with RuntimeReplayHarness.
- ReplacePolicySpec with FeatureHotSwapManager.

Map these to manual system chapters using [Main Systems Reference](MANUAL.md#main-systems-reference) and [Appendix F: Specifications and Option Reference](MANUAL.md#appendix-f-specifications-and-option-reference).

ToastManager is available from host to publish lightweight user feedback.

```python
host.app.toasts.show("Saved")
```

## 10. Complete Project Listing

The listing below is end-to-end and runnable. It contains two features, observable UI updates, keyboard actions, routed runtime wiring, message-based feature communication, and cleanup in shutdown_runtime.

```python
from gui_do import (
    ActionHotkeySpec,
    ActionSpec,
    ButtonControl,
    Feature,
    FeatureMessage,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    ObservableValue,
    PanelControl,
    RoutedFeature,
    RoutedFeatureLifecycleSpec,
    RoutedRuntimeSpec,
    SceneBundleBindingSpec,
    ShortcutOverlaySpec,
    bind_routed_feature_lifecycle,
    build_host_application_config,
    bootstrap_host_application,
    shutdown_routed_feature_lifecycle,
)


# Typed message for decoupled feature-to-feature communication.
class CounterChangedMessage(FeatureMessage):
    def __init__(self, sender: str, target: str, count: int) -> None:
        super().__init__(
            sender=sender,
            target=target,
            payload={"topic": "counter.changed", "count": count},
        )


# Visual feature that owns counter state and direct user interactions.
class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self._count = ObservableValue(0)
        self._count_sub = None

    def build(self, host) -> None:
        self._root = PanelControl("counter_root", (24, 24, 460, 520), draw_background=True)
        self._title = LabelControl("counter_title", (40, 40, 380, 30), "Pulse Desk Counter")
        self._value = LabelControl("counter_value", (40, 82, 260, 30), "Count: 0")
        self._hint = LabelControl("counter_hint", (40, 118, 360, 24), "Buttons and hotkeys: I increment, R reset")
        self._increment = ButtonControl("counter_increment", (40, 160, 160, 36), "Increment", on_click=lambda: self._increment_count(host))
        self._root.add(self._title)
        self._root.add(self._value)
        self._root.add(self._hint)
        self._root.add(self._increment)
        host.app.add(self._root, scene_name="main")
        host.shared_count = self._count

    def bind_runtime(self, host) -> None:
        self._count_sub = self._count.subscribe(lambda value: setattr(self._value, "text", f"Count: {value}"))
        host.app.actions.register_action("counter.increment", self._on_increment_action)
        host.app.actions.bind_key(ord("i"), "counter.increment", scene="main")

    def shutdown_runtime(self, host) -> None:
        if self._count_sub is not None:
            self._count_sub()
            self._count_sub = None
        host.app.actions.unbind_key(ord("i"), "counter.increment", scene="main")
        host.app.actions.unregister_action("counter.increment")

    def _increment_count(self, host) -> None:
        self._count.value += 1
        self._publish_counter_change(host)

    def _on_increment_action(self, event) -> bool:
        self._count.value += 1
        self._value.text = f"Count: {self._count.value}"
        return True

    def _publish_counter_change(self, host) -> None:
        target = host.app.feature_manager.get("activity_log")
        if target is not None:
            target.enqueue_message(CounterChangedMessage(self.name, "activity_log", self._count.value))

    def reset_count(self) -> None:
        self._count.value = 0


# Routed feature that consumes typed messages and declarative runtime helpers.
class ActivityLogFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("activity_log", scene_name="main")
        self._shared_sub = None
        self._events_seen = 0
        self._lifecycle_spec = RoutedFeatureLifecycleSpec(
            runtime_spec=RoutedRuntimeSpec(
                scene_name="main",
                action_hotkeys=(
                    ActionHotkeySpec(
                        action_name="counter.reset",
                        handler=self._on_reset_action,
                        key=ord("r"),
                        scene_name="main",
                    ),
                    ActionHotkeySpec(
                        action_name="help.toggle",
                        handler=self._toggle_shortcuts,
                        key=ord("h"),
                        scene_name="main",
                    ),
                ),
                shortcut_overlays=(
                    ShortcutOverlaySpec(
                        attr_name="_shortcut_overlay",
                        toggle_action_name="help.toggle",
                        manual_shortcut_lines=(
                            "I: increment counter",
                            "R: reset counter",
                            "P: open command palette",
                            "H: toggle this help overlay",
                        ),
                    ),
                ),
            )
        )

    def build(self, host) -> None:
        self._root = PanelControl("log_root", (520, 24, 440, 520), draw_background=True)
        self._title = LabelControl("log_title", (536, 40, 360, 30), "Activity Log")
        self._last_event = LabelControl("log_last", (536, 82, 400, 30), "Last event: none")
        self._summary = LabelControl("log_summary", (536, 118, 400, 30), "Events seen: 0")
        self._mirror = LabelControl("log_mirror", (536, 154, 400, 30), "Shared count mirror: 0")
        self._root.add(self._title)
        self._root.add(self._last_event)
        self._root.add(self._summary)
        self._root.add(self._mirror)
        host.app.add(self._root, scene_name="main")

    def bind_runtime(self, host) -> None:
        bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)
        shared = getattr(host, "shared_count", None)
        if shared is not None:
            self._shared_sub = shared.subscribe(lambda value: setattr(self._mirror, "text", f"Shared count mirror: {value}"))

    def shutdown_runtime(self, host) -> None:
        if self._shared_sub is not None:
            self._shared_sub()
            self._shared_sub = None
        shutdown_routed_feature_lifecycle(self, host, self._lifecycle_spec)

    def message_handlers(self):
        return {"counter.changed": self._on_counter_changed}

    def _on_counter_changed(self, host, message) -> None:
        self._events_seen += 1
        count = int(message.get("count", 0))
        self._last_event.text = f"Last event: counter changed -> {count}"
        self._summary.text = f"Events seen: {self._events_seen}"

    def _on_reset_action(self, event) -> bool:
        counter = self._feature_manager.get("counter") if self._feature_manager is not None else None
        if counter is None:
            return False
        if hasattr(counter, "reset_count"):
            counter.reset_count()
        self._events_seen += 1
        self._last_event.text = "Last event: counter reset by hotkey"
        self._summary.text = f"Events seen: {self._events_seen}"
        return True

    def _toggle_shortcuts(self, event) -> bool:
        overlay = getattr(self, "_shortcut_overlay", None)
        if overlay is None:
            return False
        overlay.toggle()
        return True


# Host object owns bootstrap and keeps composition declarative.
class PulseDeskHost:
    def __init__(self) -> None:
        config = build_host_application_config(
            HostApplicationBindingSpec(
                display_size=(1000, 620),
                window_title="Pulse Desk",
                fonts={"default": {"size": 16}},
                initial_scene_name="main",
                scene_bundle_entries=(
                    SceneBundleBindingSpec(scene_name="main", make_initial=True),
                ),
                feature_entries=(
                    FeatureSpec("counter_feature", CounterFeature),
                    FeatureSpec("log_feature", ActivityLogFeature),
                ),
                action_entries=(
                    ActionSpec(
                        action_id="palette_open",
                        label="Open Command Palette",
                        kind="palette_open",
                        key=ord("p"),
                    ),
                ),
            )
        )
        bootstrap_host_application(self, config)


# Script entrypoint starts the managed run loop.
if __name__ == "__main__":
    PulseDeskHost().app.run_entrypoint(target_fps=60)
```

## 11. Next Steps

Read MANUAL.md next, then inspect demo_features/ as living reference packages that model the folder-per-feature and package-root import conventions.

Good next areas to explore:
- overlays and command surfaces
- persistence and restore flows
- scene navigation and presentation models
- telemetry and operational diagnostics
- graphics and audio integration points

Start with these manual chapters:
- [8.1 Application Bootstrap and Host Configuration](MANUAL.md#81-application-bootstrap-and-host-configuration)
- [8.2 Feature Lifecycle and Feature Types](MANUAL.md#82-feature-lifecycle-and-feature-types)
- [8.3 Events, Actions, Input Mapping, and Routing](MANUAL.md#83-events-actions-input-mapping-and-routing)
- [8.4 State and Observables](MANUAL.md#84-state-and-observables)

After that, read gui_do/features/data_driven_runtime.py and gui_do/features/feature_lifecycle.py directly. They are readable and explain most runtime behavior in straightforward Python.
