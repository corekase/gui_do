# gui_do Tutorial

## 1. Introduction

gui_do is a declarative, lifecycle-oriented GUI framework built on pygame. You describe application structure with specs, then implement behavior inside feature lifecycle methods, so startup and teardown stay predictable as your project grows.

In this tutorial, you will build a small but genuinely useful desktop app: a Counter and Activity Dashboard. It has two cooperating features: one feature owns counting and primary user actions, and one feature owns an activity/log panel with routed hotkeys and shortcut help. By the end, you will have shared reactive state, feature-to-feature messaging, keyboard actions, routed runtime wiring, and clean shutdown behavior.

Prerequisites: working Python knowledge, pip, pygame, and numpy. No prior GUI-framework experience is required.

For deeper system theory and complete API coverage while you work, keep MANUAL.md open: [MANUAL.md](MANUAL.md).

## 2. Core Concepts

### Declarative Specs vs Imperative Wiring

Before writing feature code, set your mental model: gui_do separates declaration from execution.

- Declarative side: specs such as HostApplicationBindingSpec, SceneBundleBindingSpec, FeatureSpec, ActionSpec, RoutedRuntimeSpec.
- Imperative side: feature methods such as build, bind_runtime, handle_event, on_update, draw, and shutdown_runtime.

Why this matters: declaration gives bootstrap enough information to wire scenes, actions, roots, and runtime managers deterministically. Feature code can then focus on behavior instead of constructing cross-cutting plumbing by hand.

### Reactive State

ObservableValue is a value container that notifies subscribers when value changes. That lets UI react at the moment state changes, rather than polling every frame.

```python
from gui_do import ObservableValue

count = ObservableValue(0)
unsubscribe = count.subscribe(lambda value: print("count changed:", value))
count.value = 1
unsubscribe()
```

ObservableList and ObservableDict provide the same pattern for collections. ComputedValue lets you model derived values from one or more observables.

### Feature Lifecycle

The feature lifecycle is the backbone of runtime behavior:

- build(host): construct controls and feature-owned objects.
- bind_runtime(host): attach runtime bindings such as subscriptions, action bindings, routed facilities, and timers.
- handle_event(host, event): feature-level event participation when needed.
- on_update(host): per-frame logic and message draining.
- draw(host, surface, theme): custom rendering when needed.
- shutdown_runtime(host): teardown subscriptions/bindings/resources.

Two important guarantees:

- All features in a scene complete build before any feature bind_runtime runs.
- Subscriptions/bindings should be created in bind_runtime and always removed in shutdown_runtime.

That lifecycle ownership is one of the core maintainability contracts of gui_do.

## 3. Installation and Setup

Install from repository root:

```bash
python -m pip install -e . --no-deps
```

Dependencies:

- pygame
- numpy (used internally by graphics/pixel-buffer paths such as PixelArray workflows)

Verify install:

```bash
python -c "import gui_do; print(gui_do.__version__)"
```

Minimal startup imports:

```python
from gui_do import HostApplicationBindingSpec, build_host_application_config, bootstrap_host_application, Feature
```

There are two startup paths:

- Declarative bootstrap (recommended): HostApplicationBindingSpec -> build_host_application_config -> bootstrap_host_application.
- Manual GuiApplication construction (advanced): use when you intentionally need lower-level control; see MANUAL.md chapter 8.1.

Project organization convention: model your app like demo_features with one folder per feature, one package __init__.py per folder as the only public import surface, and file-per-concern internals inside that folder. Keep cross-feature imports at package roots only.

## 4. Your First Feature

Narrative goal: build the first visible part of the dashboard.

### Step 1. Define the Feature Class

Use Feature as the default because it gives the standard lifecycle shape and plays well with scene wiring.

```python
from gui_do import Feature

class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter", scene_name="main")

    def build(self, host):
        pass
```

### Step 2. Add a Control

Controls are nodes inside your feature region, not independent native widgets.

```python
from gui_do import LabelControl

def build(self, host):
    self._label = LabelControl("hello_label", (24, 24, 420, 32), "Counter Dashboard")
    host.main_root.add(self._label)
```

host.screen_rect is your full display canvas; scene roots carve that into stable feature layout regions.

### Step 3. Declare Config

HostApplicationBindingSpec describes the app. SceneBundleBindingSpec declares scene/runtime defaults. FeatureSpec declares feature attribute and factory.

```python
from gui_do import FeatureSpec, HostApplicationBindingSpec, SceneBundleBindingSpec, build_host_application_config

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(960, 600),
        window_title="Counter Dashboard",
        fonts={"default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 14}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(
                scene_name="main",
                make_initial=True,
                emit_scene_root_spec=True,
                scene_root_id="main_root",
            ),
        ),
        feature_entries=(FeatureSpec("counter_feature", CounterFeature),),
    )
)
```

### Step 4. Bootstrap and Run

bootstrap_host_application reads config and wires display, scenes, features, actions, overlays, and runtime services into the host object.

```python
from gui_do import bootstrap_host_application

class AppHost:
    def __init__(self, config):
        bootstrap_host_application(self, config)

host = AppHost(config)
host.app.run_entrypoint(target_fps=60)
```

### Step 5. Full Listing (Section 4 State)

```python
from gui_do import (
    Feature,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    SceneBundleBindingSpec,
    bootstrap_host_application,
    build_host_application_config,
)

class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter", scene_name="main")
        self._label = None

    def build(self, host):
        self._label = LabelControl("hello_label", (24, 24, 420, 32), "Counter Dashboard")
        host.main_root.add(self._label)

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(960, 600),
        window_title="Counter Dashboard",
        fonts={"default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 14}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(scene_name="main", make_initial=True, emit_scene_root_spec=True, scene_root_id="main_root"),
        ),
        feature_entries=(FeatureSpec("counter_feature", CounterFeature),),
    )
)

class AppHost:
    def __init__(self):
        bootstrap_host_application(self, config)

host = AppHost()
host.app.run_entrypoint(target_fps=60)
```

## 5. Reactive State: Making the UI Respond

Narrative goal: make the dashboard interactive and reactive.

### Step 1. Introduce ObservableValue

```python
from gui_do import ObservableValue

self._count = ObservableValue(0)
```

Assigning self._count.value broadcasts to subscribers.

### Step 2. Add a Button

```python
from gui_do import ButtonControl

self._button = ButtonControl(
    "increment_button",
    (24, 72, 180, 34),
    "Increment",
    on_click=self._increment,
)
host.main_root.add(self._button)
```

### Step 3. Wire Observable to Label in bind_runtime

bind_runtime is the right place because controls are guaranteed to exist by then.

```python
def bind_runtime(self, host):
    self._count_unsub = self._count.subscribe(
        lambda value: setattr(self._label, "text", f"Count: {value}")
    )
```

### Step 4. Unsubscribe in shutdown_runtime

Subscriptions hold references; teardown prevents leaks and stale callbacks.

```python
def shutdown_runtime(self, host):
    if self._count_unsub:
        self._count_unsub()
        self._count_unsub = None
```

### Step 5. Full Listing (Section 5 State)

```python
from gui_do import (
    ButtonControl,
    Feature,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    ObservableValue,
    SceneBundleBindingSpec,
    bootstrap_host_application,
    build_host_application_config,
)

class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter", scene_name="main")
        self._count = ObservableValue(0)
        self._label = None
        self._button = None
        self._count_unsub = None

    def build(self, host):
        self._label = LabelControl("count_label", (24, 24, 320, 32), "Count: 0")
        self._button = ButtonControl("increment_button", (24, 72, 180, 34), "Increment", on_click=self._increment)
        host.main_root.add(self._label)
        host.main_root.add(self._button)

    def bind_runtime(self, host):
        self._count_unsub = self._count.subscribe(lambda value: setattr(self._label, "text", f"Count: {value}"))

    def shutdown_runtime(self, host):
        if self._count_unsub:
            self._count_unsub()
            self._count_unsub = None

    def _increment(self):
        self._count.value += 1

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(960, 600),
        window_title="Counter Dashboard",
        fonts={"default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 14}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(scene_name="main", make_initial=True, emit_scene_root_spec=True, scene_root_id="main_root"),
        ),
        feature_entries=(FeatureSpec("counter_feature", CounterFeature),),
    )
)

class AppHost:
    def __init__(self):
        bootstrap_host_application(self, config)

host = AppHost()
host.app.run_entrypoint(target_fps=60)
```

## 6. Feature Types

Use the project context to choose the right type:

- Feature: default choice for visual features with lifecycle stubs and control-tree composition.
- DirectFeature: full manual control over direct event/update/draw hooks when bypassing the standard control pipeline is intentional.
- DirectFeature (high-control rendering emphasis): use when you need direct frame-time and direct rendering paths for advanced drawing behavior.
- LogicFeature: non-visual feature for domain logic, orchestration, or background coordination.
- RoutedFeature: Feature subtype with topic-based message routing plus declarative runtime bundles through RoutedRuntimeSpec and RoutedFeatureLifecycleSpec.

Rule of thumb: start with Feature, move to RoutedFeature when declarative runtime facilities and topic dispatch make code thinner, and use DirectFeature/LogicFeature only when their tradeoffs are clearly needed.

## 7. A Second Feature and Feature Communication

Narrative goal: add an Activity feature and connect it to the counter.

### Step 1. Define the Second Feature

We will place a second panel to display latest activity and an event count.

### Step 2. Shared State via ObservableValue

Two valid approaches:

- Shared observable through host attribute: first feature exposes host.shared_count = self._count in build.
- Message passing: features publish typed payloads through FeatureMessage transport so they stay decoupled.

### Step 3. Feature Messaging

Concrete message type (thin subclass) plus publish/receive pattern:

```python
from gui_do import FeatureMessage

class CounterChangedMessage(FeatureMessage):
    @classmethod
    def make(cls, sender, target, count):
        return cls(sender=sender, target=target, payload={"topic": "counter.changed", "count": count})
```

Publishing from CounterFeature:

```python
self.send_message("activity_log", {"topic": "counter.changed", "count": next_value})
```

Receiving in ActivityFeature:

```python
def on_update(self, host):
    while self.has_messages():
        message = self.pop_message()
        if message and message.topic == "counter.changed":
            self._latest_label.text = f"Last event: counter -> {message['count']}"
```

Use messaging when you want low coupling and explicit cross-feature contracts.

### Step 4. Full Listing (Section 7 State)

```python
from gui_do import (
    ButtonControl,
    Feature,
    FeatureMessage,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    ObservableValue,
    SceneBundleBindingSpec,
    bootstrap_host_application,
    build_host_application_config,
)

class CounterChangedMessage(FeatureMessage):
    @classmethod
    def make(cls, sender, target, count):
        return cls(sender=sender, target=target, payload={"topic": "counter.changed", "count": count})

class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter", scene_name="main")
        self._count = ObservableValue(0)
        self._label = None
        self._unsub = None

    def build(self, host):
        host.shared_count = self._count
        self._label = LabelControl("count_label", (24, 24, 320, 32), "Count: 0")
        host.main_root.add(self._label)
        host.main_root.add(ButtonControl("increment_button", (24, 72, 180, 34), "Increment", on_click=self._increment))

    def bind_runtime(self, host):
        self._unsub = self._count.subscribe(lambda value: setattr(self._label, "text", f"Count: {value}"))

    def shutdown_runtime(self, host):
        if self._unsub:
            self._unsub()
            self._unsub = None

    def _increment(self):
        next_value = self._count.value + 1
        self._count.value = next_value
        self.send_message("activity_log", {"topic": "counter.changed", "count": next_value})

class ActivityFeature(Feature):
    def __init__(self):
        super().__init__("activity_log", scene_name="main")
        self._latest_label = None
        self._mirror_label = None
        self._shared_unsub = None

    def build(self, host):
        self._latest_label = LabelControl("latest_event", (380, 24, 520, 32), "Last event: none")
        self._mirror_label = LabelControl("mirror_count", (380, 64, 520, 32), "Shared count: 0")
        host.main_root.add(self._latest_label)
        host.main_root.add(self._mirror_label)

    def bind_runtime(self, host):
        shared = getattr(host, "shared_count", None)
        if shared is not None:
            self._shared_unsub = shared.subscribe(lambda value: setattr(self._mirror_label, "text", f"Shared count: {value}"))

    def on_update(self, host):
        while self.has_messages():
            message = self.pop_message()
            if message and message.topic == "counter.changed":
                self._latest_label.text = f"Last event: counter -> {message['count']}"

    def shutdown_runtime(self, host):
        if self._shared_unsub:
            self._shared_unsub()
            self._shared_unsub = None

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(980, 620),
        window_title="Counter and Activity Dashboard",
        fonts={"default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 14}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(scene_name="main", make_initial=True, emit_scene_root_spec=True, scene_root_id="main_root"),
        ),
        feature_entries=(
            FeatureSpec("counter_feature", CounterFeature),
            FeatureSpec("activity_feature", ActivityFeature),
        ),
    )
)

class AppHost:
    def __init__(self):
        bootstrap_host_application(self, config)

host = AppHost()
host.app.run_entrypoint(target_fps=60)
```

## 8. Actions and Keyboard Shortcuts

Narrative goal: wire keyboard-driven behavior for primary actions.

### Step 1. Declare an ActionSpec

Add an ActionSpec in HostApplicationBindingSpec action_entries. This gives a declarative action registration path and optional key binding.

```python
from gui_do import ActionSpec

action_entries=(
    ActionSpec(
        action_id="palette_open",
        label="Open Command Palette",
        kind="palette_open",
        key=ord("p"),
        category="Tools",
    ),
)
```

### Step 2. Plain Feature Action Binding

For a plain Feature, bind custom actions in bind_runtime and unbind in shutdown_runtime:

```python
def bind_runtime(self, host):
    host.app.actions.register_action("increment_counter", self._on_increment_hotkey)
    host.app.actions.bind_key(ord("i"), "increment_counter", scene="main")


def shutdown_runtime(self, host):
    host.app.actions.unbind_key(ord("i"), "increment_counter", scene="main")
    host.app.actions.unregister_action("increment_counter")
```

### Step 3. RoutedFeature Shortcut Binding

RoutedFeature can declare action hotkeys in RoutedRuntimeSpec. The routed lifecycle helper binds/unbinds them automatically.

```python
from gui_do import ActionHotkeySpec, RoutedFeatureLifecycleSpec, RoutedRuntimeSpec

runtime_spec = RoutedRuntimeSpec(
    scene_name="main",
    action_hotkeys=(
        ActionHotkeySpec(
            action_name="clear_activity",
            handler=self._clear_from_hotkey,
            key=ord("l"),
            scene_name="main",
        ),
    ),
)
self._lifecycle_spec = RoutedFeatureLifecycleSpec(runtime_spec=runtime_spec)
```

### Step 4. Shortcut Help Overlay

Add ShortcutOverlaySpec to routed runtime so users can discover shortcuts quickly:

```python
from gui_do import ShortcutOverlaySpec

shortcut_overlays=(
    ShortcutOverlaySpec(
        attr_name="shortcut_overlay",
        toggle_key=ord("h"),
        toggle_scene_name="main",
        manual_shortcut_lines=("I - increment", "L - clear activity", "P - command palette"),
        manual_section_title="Project shortcuts",
    ),
)
```

### Step 5. Full Listing (Section 8 State)

```python
from gui_do import (
    ActionHotkeySpec,
    ActionSpec,
    ButtonControl,
    Feature,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    ObservableValue,
    RoutedFeature,
    RoutedFeatureLifecycleSpec,
    RoutedRuntimeSpec,
    SceneBundleBindingSpec,
    ShortcutOverlaySpec,
    bind_routed_feature_lifecycle,
    bootstrap_host_application,
    build_host_application_config,
    shutdown_routed_feature_lifecycle,
)

class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter", scene_name="main")
        self._count = ObservableValue(0)
        self._label = None
        self._count_unsub = None

    def build(self, host):
        host.shared_count = self._count
        self._label = LabelControl("count_label", (24, 24, 320, 32), "Count: 0")
        host.main_root.add(self._label)
        host.main_root.add(ButtonControl("increment_button", (24, 72, 180, 34), "Increment", on_click=self._increment))

    def bind_runtime(self, host):
        self._count_unsub = self._count.subscribe(lambda value: setattr(self._label, "text", f"Count: {value}"))
        host.app.actions.register_action("increment_counter", self._on_increment_hotkey)
        host.app.actions.bind_key(ord("i"), "increment_counter", scene="main")

    def shutdown_runtime(self, host):
        if self._count_unsub:
            self._count_unsub()
            self._count_unsub = None
        host.app.actions.unbind_key(ord("i"), "increment_counter", scene="main")
        host.app.actions.unregister_action("increment_counter")

    def _increment(self):
        next_value = self._count.value + 1
        self._count.value = next_value
        self.send_message("activity_log", {"topic": "counter.changed", "count": next_value})

    def _on_increment_hotkey(self, _event):
        self._increment()
        return True

class ActivityFeature(RoutedFeature):
    def __init__(self):
        super().__init__("activity_log", scene_name="main")
        self._latest_label = None
        self._mirror_label = None
        self._shared_unsub = None
        self._runtime_spec = None
        self._lifecycle_spec = None

    def build(self, host):
        self._latest_label = LabelControl("latest_event", (380, 24, 560, 32), "Last event: none")
        self._mirror_label = LabelControl("mirror_count", (380, 64, 560, 32), "Shared count: 0")
        host.main_root.add(self._latest_label)
        host.main_root.add(self._mirror_label)

    def bind_runtime(self, host):
        shared = getattr(host, "shared_count", None)
        if shared is not None:
            self._shared_unsub = shared.subscribe(lambda value: setattr(self._mirror_label, "text", f"Shared count: {value}"))

        self._runtime_spec = RoutedRuntimeSpec(
            scene_name="main",
            action_hotkeys=(
                ActionHotkeySpec(action_name="clear_activity", handler=self._clear_from_hotkey, key=ord("l"), scene_name="main"),
            ),
            shortcut_overlays=(
                ShortcutOverlaySpec(
                    attr_name="shortcut_overlay",
                    toggle_key=ord("h"),
                    toggle_scene_name="main",
                    manual_shortcut_lines=("I - increment", "L - clear activity", "P - command palette"),
                    manual_section_title="Project shortcuts",
                ),
            ),
        )
        self._lifecycle_spec = RoutedFeatureLifecycleSpec(runtime_spec=self._runtime_spec)
        bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)

    def message_handlers(self):
        return {"counter.changed": self._on_counter_changed}

    def _on_counter_changed(self, host, message):
        self._latest_label.text = f"Last event: counter -> {message['count']}"

    def _clear_from_hotkey(self, _event):
        self._latest_label.text = "Last event: cleared"
        return True

    def shutdown_runtime(self, host):
        if self._shared_unsub:
            self._shared_unsub()
            self._shared_unsub = None
        if self._lifecycle_spec is not None:
            shutdown_routed_feature_lifecycle(self, host, self._lifecycle_spec)
            self._lifecycle_spec = None

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(980, 620),
        window_title="Counter and Activity Dashboard",
        fonts={"default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 14}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(scene_name="main", make_initial=True, emit_scene_root_spec=True, scene_root_id="main_root"),
        ),
        feature_entries=(
            FeatureSpec("counter_feature", CounterFeature),
            FeatureSpec("activity_feature", ActivityFeature),
        ),
        action_entries=(
            ActionSpec(action_id="palette_open", label="Open Command Palette", kind="palette_open", key=ord("p"), category="Tools"),
        ),
    )
)

class AppHost:
    def __init__(self):
        bootstrap_host_application(self, config)

host = AppHost()
host.app.run_entrypoint(target_fps=60)
```

## 9. Spec Reference for Builders

This is a compact builder-side reference. For full behavior, options, and caveats, see MANUAL.md systems chapters, especially [MANUAL.md](MANUAL.md#main-systems-reference).

- FeatureSpec: declare feature attribute slot and factory used during bootstrap.

```python
FeatureSpec("counter_feature", CounterFeature)
```

- FeatureSpec (scene membership note): feature instances participate in scene behavior through feature scene_name and scene bundle setup.

```python
class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter", scene_name="main")
```

- SceneBundleBindingSpec: declarative scene setup, transition policy, optional roots/navigation/runtime scene options.

```python
SceneBundleBindingSpec(scene_name="main", make_initial=True, emit_scene_root_spec=True, scene_root_id="main_root")
```

- ActionSpec plus ActionHotkeySpec: ActionSpec declares host-level actions; ActionHotkeySpec declares routed runtime action bindings.

```python
ActionSpec(action_id="palette_open", label="Open Command Palette", kind="palette_open", key=ord("p"))
ActionHotkeySpec(action_name="clear_activity", handler=self._clear_from_hotkey, key=ord("l"), scene_name="main")
```

- ShortcutOverlaySpec: declarative shortcut help overlay and toggle key.

```python
ShortcutOverlaySpec(attr_name="shortcut_overlay", toggle_key=ord("h"), toggle_scene_name="main")
```

- RoutedRuntimeSpec plus RoutedFeatureLifecycleSpec: declarative routed runtime bundle and lifecycle-owned setup/teardown for RoutedFeature.

```python
runtime_spec = RoutedRuntimeSpec(scene_name="main", action_hotkeys=(ActionHotkeySpec("clear_activity", self._clear_from_hotkey, ord("l"), "main"),))
lifecycle_spec = RoutedFeatureLifecycleSpec(runtime_spec=runtime_spec)
```

- Higher-level runtime faculties: RuntimePolicySpec and RuntimePolicyEngine, EffectBindingSpec and EffectLifetimeOrchestrator, EventPipelineSpec and EventPipelineRuntime, DurableOperationQueueSpec and DurableOperationQueueRuntime, CapabilityProviderSpec/CapabilityRequirementSpec and CapabilityContractRuntime, ProjectionSpec and ProjectionRuntime, plus WorkflowSpec/WorkflowCoordinator, RecomputeNodeSpec/RecomputeOrchestrator, QoSPolicySpec/QoSPolicyRuntime, HealthProbeSpec/FeatureHealthRuntime, ReplaySpec/RuntimeReplayHarness, and ReplacePolicySpec/FeatureHotSwapManager.

```python
RoutedRuntimeSpec(
    scene_name="main",
    policy_specs=(),
    effect_bindings=(),
    event_pipelines=(),
    durable_queue_spec=None,
    capability_providers=(),
    capability_requirements=(),
    projection_spec=None,
    workflow_specs=(),
    recompute_nodes=(),
    qos_policies=(),
    health_probes=(),
    replay_spec=None,
    replace_policy=None,
)
```

- ToastManager: from a feature, show a toast through host.app.toasts.show(...).

```python
host.app.toasts.show("Saved", title="Dashboard")
```

For full details per system, cross-reference MANUAL.md chapters 8.1 through 8.16: [MANUAL.md](MANUAL.md#main-systems-reference).

## 10. Complete Project Listing

The full listing below is end-to-end runnable and includes two feature responsibilities, shared observable state, message routing, ActionSpec declaration, one RoutedFeature with RoutedRuntimeSpec, and teardown cleanup.

```python
from gui_do import (
    ActionHotkeySpec,
    ActionSpec,
    ButtonControl,
    Feature,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    ObservableList,
    ObservableValue,
    RoutedFeature,
    RoutedFeatureLifecycleSpec,
    RoutedRuntimeSpec,
    SceneBundleBindingSpec,
    ShortcutOverlaySpec,
    bootstrap_host_application,
    build_host_application_config,
    bind_routed_feature_lifecycle,
    shutdown_routed_feature_lifecycle,
)

# CounterFeature owns the primary domain state and user increment action.
class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter", scene_name="main")
        self._count = ObservableValue(0)
        self._events = ObservableList()
        self._count_label = None
        self._events_label = None
        self._count_unsub = None
        self._events_unsub = None

    # Build controls once; runtime bindings are attached later in bind_runtime.
    def build(self, host):
        host.shared_count = self._count
        host.shared_events = self._events

        self._count_label = LabelControl("count_label", (24, 24, 320, 32), "Count: 0")
        self._events_label = LabelControl("events_label", (24, 60, 320, 32), "Events: 0")
        host.main_root.add(self._count_label)
        host.main_root.add(self._events_label)

        host.main_root.add(
            ButtonControl("increment_button", (24, 108, 190, 34), "Increment", on_click=self._increment)
        )
        host.main_root.add(
            ButtonControl("reset_button", (224, 108, 190, 34), "Reset", on_click=self._reset)
        )

    # Wire reactivity and keyboard action when runtime services are live.
    def bind_runtime(self, host):
        self._count_unsub = self._count.subscribe(
            lambda value: setattr(self._count_label, "text", f"Count: {value}")
        )
        self._events_unsub = self._events.subscribe(
            lambda values: setattr(self._events_label, "text", f"Events: {len(values)}")
        )

        host.app.actions.register_action("increment_counter", self._on_increment_hotkey)
        host.app.actions.bind_key(ord("i"), "increment_counter", scene="main")

    # Always undo every subscription/binding created in bind_runtime.
    def shutdown_runtime(self, host):
        if self._count_unsub:
            self._count_unsub()
            self._count_unsub = None
        if self._events_unsub:
            self._events_unsub()
            self._events_unsub = None
        host.app.actions.unbind_key(ord("i"), "increment_counter", scene="main")
        host.app.actions.unregister_action("increment_counter")

    # Increment updates local state, shared state, and sends a routed message.
    def _increment(self):
        next_value = self._count.value + 1
        self._count.value = next_value
        self._events.append(f"increment:{next_value}")
        self.send_message("activity_log", {"topic": "counter.changed", "count": next_value})

    # Reset demonstrates another primary action path.
    def _reset(self):
        self._count.value = 0
        self._events.append("reset")
        self.send_message("activity_log", {"topic": "counter.reset", "count": 0})

    # Hotkey callback returns bool for ActionManager dispatch contract.
    def _on_increment_hotkey(self, _event):
        self._increment()
        return True


# ActivityFeature owns log presentation and routed hotkeys/shortcut overlay.
class ActivityFeature(RoutedFeature):
    def __init__(self):
        super().__init__("activity_log", scene_name="main")
        self._latest_label = None
        self._mirror_label = None
        self._events_tail_label = None
        self._count_unsub = None
        self._events_unsub = None
        self._lifecycle_spec = None

    # Build visual controls for secondary panel responsibilities.
    def build(self, host):
        self._latest_label = LabelControl("latest_label", (460, 24, 480, 32), "Last event: none")
        self._mirror_label = LabelControl("mirror_label", (460, 60, 480, 32), "Shared count: 0")
        self._events_tail_label = LabelControl("tail_label", (460, 96, 480, 32), "Recent: []")
        host.main_root.add(self._latest_label)
        host.main_root.add(self._mirror_label)
        host.main_root.add(self._events_tail_label)

    # Bind shared-observable mirrors and routed runtime facilities.
    def bind_runtime(self, host):
        shared_count = getattr(host, "shared_count", None)
        if shared_count is not None:
            self._count_unsub = shared_count.subscribe(
                lambda value: setattr(self._mirror_label, "text", f"Shared count: {value}")
            )

        shared_events = getattr(host, "shared_events", None)
        if shared_events is not None:
            self._events_unsub = shared_events.subscribe(self._on_events_changed)

        runtime_spec = RoutedRuntimeSpec(
            scene_name="main",
            action_hotkeys=(
                ActionHotkeySpec(
                    action_name="clear_activity",
                    handler=self._clear_activity,
                    key=ord("l"),
                    scene_name="main",
                ),
            ),
            shortcut_overlays=(
                ShortcutOverlaySpec(
                    attr_name="shortcut_overlay",
                    toggle_key=ord("h"),
                    toggle_scene_name="main",
                    manual_shortcut_lines=(
                        "I - Increment counter",
                        "L - Clear activity panel",
                        "P - Open command palette",
                    ),
                    manual_section_title="Project shortcuts",
                ),
            ),
        )
        self._lifecycle_spec = RoutedFeatureLifecycleSpec(runtime_spec=runtime_spec)
        bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)

    # RoutedFeature dispatches by payload topic through message_handlers.
    def message_handlers(self):
        return {
            "counter.changed": self._on_counter_changed,
            "counter.reset": self._on_counter_reset,
        }

    # Update latest event line on increment messages.
    def _on_counter_changed(self, host, message):
        self._latest_label.text = f"Last event: increment -> {message['count']}"
        host.app.toasts.show(f"Count is now {message['count']}")

    # Update latest event line on reset messages.
    def _on_counter_reset(self, host, message):
        self._latest_label.text = "Last event: reset"
        host.app.toasts.show("Counter reset")

    # Keep a short tail from shared ObservableList changes.
    def _on_events_changed(self, values):
        tail = list(values)[-3:]
        self._events_tail_label.text = f"Recent: {tail}"

    # Routed ActionHotkeySpec callback to clear panel state.
    def _clear_activity(self, _event):
        self._latest_label.text = "Last event: cleared"
        self._events_tail_label.text = "Recent: []"
        return True

    # Teardown shared subscriptions and routed lifecycle resources.
    def shutdown_runtime(self, host):
        if self._count_unsub:
            self._count_unsub()
            self._count_unsub = None
        if self._events_unsub:
            self._events_unsub()
            self._events_unsub = None
        if self._lifecycle_spec is not None:
            shutdown_routed_feature_lifecycle(self, host, self._lifecycle_spec)
            self._lifecycle_spec = None


# Declarative host config defines scene, features, and host-level actions.
CONFIG = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1000, 640),
        window_title="Counter and Activity Dashboard",
        fonts={"default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 14}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(
                scene_name="main",
                make_initial=True,
                emit_scene_root_spec=True,
                scene_root_id="main_root",
            ),
        ),
        feature_entries=(
            FeatureSpec("counter_feature", CounterFeature),
            FeatureSpec("activity_feature", ActivityFeature),
        ),
        action_entries=(
            ActionSpec(
                action_id="palette_open",
                label="Open Command Palette",
                kind="palette_open",
                key=ord("p"),
                category="Tools",
            ),
        ),
    )
)


# Host bootstraps from specs, then enters the app loop.
class AppHost:
    def __init__(self):
        bootstrap_host_application(self, CONFIG)


if __name__ == "__main__":
    host = AppHost()
    host.app.run_entrypoint(target_fps=60)
```

## 11. Next Steps

Read next in this order:

1. MANUAL.md for complete system depth and API coverage: [MANUAL.md](MANUAL.md)
2. demo_features/ for living package-layout and runtime composition examples: [demo_features/](demo_features/)

High-value exploration targets after this tutorial:

- Overlays, dialogs, command surfaces, and shortcut discoverability
- Persistence and restore flows with migration-safe snapshots
- Scene navigation patterns and transition tuning
- Telemetry and introspection for operational debugging
- Graphics/audio subsystems for richer runtime feedback

The most relevant MANUAL.md sections for immediate follow-up are 8.1 (bootstrap), 8.2 (features), 8.3 (events/actions), and 8.4 (state/observables).

If you want to demystify bootstrap internals, read the data-driven runtime and lifecycle implementation files in the library code. They are readable, strongly structured, and map directly to the specs and lifecycle methods used throughout this tutorial.
