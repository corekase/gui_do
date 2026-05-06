# gui_do Tutorial

## 1. Introduction

gui_do is a data-driven Python GUI framework built on pygame. Instead of hard-coding setup order across many subsystems, you declare scenes, features, and actions as specs and let bootstrap assemble the runtime graph. This tutorial builds a complete multi-feature app so you can learn the framework by shipping something useful.

We will build FocusLog, a small desktop tool with two features: a counter workspace and an activity log panel. The final app has reactive labels, a keyboard shortcut, routed runtime wiring, feature-to-feature messaging, and clean shutdown behavior.

Prerequisites: Python, pip, pygame, and numpy. No prior GUI framework experience is required.

For deeper reference while you read, use [MANUAL.md](MANUAL.md).

## 2. Core Concepts

### Declarative specs vs imperative wiring

gui_do favors declarative specs because they describe application structure as data. You declare scene bundles, feature entries, and action entries, then bootstrap applies deterministic wiring for registration, setup, and runtime ownership. This keeps features independent from each other and reduces startup coupling.

### Reactive state

ObservableValue is a state container that notifies subscribers when its value changes. ObservableList and ObservableDict provide the same reactive behavior for collections. ComputedValue can express derived state from one or more observables.

```python
from gui_do import ObservableDict, ObservableList, ObservableValue

count = ObservableValue(0)
items = ObservableList(["boot"])
meta = ObservableDict({"mode": "ready"})

unsubscribe = count.subscribe(lambda value: print(f"count changed -> {value}"))
count.value = 1
unsubscribe()
```

### Feature lifecycle

A feature moves through build, bind_runtime, handle_event, on_update, draw, and shutdown_runtime. In gui_do, all features in a scene complete build before any bind_runtime executes. That guarantee lets you wire subscriptions safely in bind_runtime after controls exist. Subscriptions and other runtime handles should be released in shutdown_runtime.

## 3. Installation and Setup

Install from repository root:

```bash
python -m pip install -e . --no-deps
```

Dependencies: pygame and numpy. numpy is used internally by rendering paths such as pixel buffer workflows.

Verify installation:

```bash
python -c "import gui_do; print(gui_do.__version__)"
```

Minimal imports used throughout this tutorial:

```python
from gui_do import HostApplicationBindingSpec, build_host_application_config, bootstrap_host_application, Feature
```

Startup paths:
- Recommended: declarative bootstrap with HostApplicationBindingSpec.
- Advanced: manual GuiApplication construction and explicit subsystem wiring (see [MANUAL.md](MANUAL.md)).

## 4. Your First Feature

### Step 1. Define the feature class

Use Feature when you want standard lifecycle methods and a visual control tree.

```python
from gui_do import Feature


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")

    def build(self, host) -> None:
        pass
```

### Step 2. Add a control

Controls are scene layout nodes owned by the feature, not standalone OS widgets.

```python
from pygame import Rect
from gui_do import Feature, LabelControl


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")

    def build(self, host) -> None:
        self.count_label = host.app.add(
            LabelControl("count_label", Rect(24, 24, 300, 40), "Count: 0"),
            scene_name="main",
        )
```

### Step 3. Declare the config

HostApplicationBindingSpec describes the app boundary and build_host_application_config turns it into a runtime config object.

```python
from gui_do import (
    FeatureSpec,
    HostApplicationBindingSpec,
    SceneBundleBindingSpec,
    build_host_application_config,
)

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(900, 520),
        window_title="FocusLog",
        fonts={"default": {"system": "arial", "size": 16}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(scene_name="main", make_initial=True),
        ),
        feature_entries=(FeatureSpec("counter_feature", CounterFeature),),
    )
)
```

### Step 4. Bootstrap and run

bootstrap_host_application reads the config and attaches runtime objects to your host instance. run_entrypoint starts the frame loop.

```python
host = type("Host", (), {})()
bootstrap_host_application(host, config)
host.app.run_entrypoint(target_fps=60)
```

### Step 5. Full listing

```python
from pygame import Rect

from gui_do import (
    Feature,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    SceneBundleBindingSpec,
    build_host_application_config,
    bootstrap_host_application,
)


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")

    def build(self, host) -> None:
        self.count_label = host.app.add(
            LabelControl("count_label", Rect(24, 24, 300, 40), "Count: 0"),
            scene_name="main",
        )


config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(900, 520),
        window_title="FocusLog",
        fonts={"default": {"system": "arial", "size": 16}},
        initial_scene_name="main",
        scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
        feature_entries=(FeatureSpec("counter_feature", CounterFeature),),
    )
)

host = type("Host", (), {})()
bootstrap_host_application(host, config)
host.app.run_entrypoint(target_fps=60)
```

## 5. Reactive State: Making the UI Respond

Now we make the counter interactive.

### Step 1. Introduce ObservableValue

```python
from gui_do import ObservableValue

self.count = ObservableValue(0)
```

### Step 2. Add a button

```python
self.increment_button = host.app.add(
    ButtonControl("increment_button", Rect(24, 76, 180, 40), "Increment", on_click=self.increment_count),
    scene_name="main",
)
```

### Step 3. Wire observable to label in bind_runtime

Subscriptions belong in bind_runtime because controls are guaranteed to exist after build.

```python
self.stop_count_subscription = self.count.subscribe(
    lambda value: setattr(self.count_label, "text", f"Count: {value}")
)
```

### Step 4. Unsubscribe in shutdown_runtime

```python
if self.stop_count_subscription is not None:
    self.stop_count_subscription()
    self.stop_count_subscription = None
```

### Step 5. Updated full listing

```python
from pygame import Rect

from gui_do import (
    ButtonControl,
    Feature,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    ObservableValue,
    SceneBundleBindingSpec,
    build_host_application_config,
    bootstrap_host_application,
)


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self.count = ObservableValue(0)
        self.stop_count_subscription = None

    def build(self, host) -> None:
        self.count_label = host.app.add(
            LabelControl("count_label", Rect(24, 24, 300, 40), "Count: 0"),
            scene_name="main",
        )
        self.increment_button = host.app.add(
            ButtonControl("increment_button", Rect(24, 76, 180, 40), "Increment", on_click=self.increment_count),
            scene_name="main",
        )

    def bind_runtime(self, host) -> None:
        self.stop_count_subscription = self.count.subscribe(
            lambda value: setattr(self.count_label, "text", f"Count: {value}")
        )

    def shutdown_runtime(self, host) -> None:
        if self.stop_count_subscription is not None:
            self.stop_count_subscription()
            self.stop_count_subscription = None

    def increment_count(self) -> None:
        self.count.value += 1


config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(900, 520),
        window_title="FocusLog",
        fonts={"default": {"system": "arial", "size": 16}},
        initial_scene_name="main",
        scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
        feature_entries=(FeatureSpec("counter_feature", CounterFeature),),
    )
)

host = type("Host", (), {})()
bootstrap_host_application(host, config)
host.app.run_entrypoint(target_fps=60)
```

## 6. Feature Types

- Feature: default choice for visual features with control trees, state, and interaction.
- DirectFeature: low-level lifecycle with direct update and draw methods when you need full control.
- LogicFeature: non-visual background orchestration for state transforms, data loading, and coordination.
- RoutedFeature: Feature plus topic-based wiring through RoutedRuntimeSpec and RoutedFeatureLifecycleSpec.

In practice, most apps use Feature for primary UI and add RoutedFeature where declarative hotkeys, overlay specs, or structured companion wiring improve maintainability.

## 7. A Second Feature and Feature Communication

We add an ActivityLogFeature to show events from CounterFeature.

### 1. Define the second feature

ActivityLogFeature renders recent messages in a dedicated panel region.

### 2. Shared state via ObservableValue

Approach A: share an ObservableValue on the host and subscribe from both features. This is good for continuous, shared state.

Approach B: send FeatureMessage payloads for discrete events. This is better when producers and consumers should not hold direct references.

### 3. Feature messaging example

```python
from gui_do import FeatureMessage


class CounterMessage(FeatureMessage):
    pass

payload = CounterMessage.from_payload(
    sender="counter",
    target="activity_log",
    payload={"topic": "counter", "event": "incremented", "value": 3},
)
host.app.features.send_message(payload.sender, payload.target, payload.payload)
```

### 4. Updated full listing

```python
from pygame import Rect

from gui_do import (
    ButtonControl,
    Feature,
    FeatureMessage,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    ObservableList,
    ObservableValue,
    PanelControl,
    SceneBundleBindingSpec,
    build_host_application_config,
    bootstrap_host_application,
)


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self.count = ObservableValue(0)
        self.stop_count_subscription = None

    def build(self, host) -> None:
        self.container = host.app.add(PanelControl("counter_panel", Rect(16, 16, 420, 220)), scene_name="main")
        self.count_label = self.container.add(LabelControl("count_label", Rect(16, 16, 320, 36), "Count: 0"))
        self.increment_button = self.container.add(
            ButtonControl("increment_button", Rect(16, 64, 180, 40), "Increment", on_click=self.increment_count)
        )

    def bind_runtime(self, host) -> None:
        self.stop_count_subscription = self.count.subscribe(
            lambda value: setattr(self.count_label, "text", f"Count: {value}")
        )

    def shutdown_runtime(self, host) -> None:
        if self.stop_count_subscription is not None:
            self.stop_count_subscription()
            self.stop_count_subscription = None

    def increment_count(self) -> None:
        self.count.value += 1
        event_message = FeatureMessage.from_payload(
            sender="counter",
            target="activity_log",
            payload={"topic": "counter", "event": "incremented", "value": self.count.value},
        )
        host_ref = getattr(self, "host", None)
        if host_ref is not None:
            host_ref.app.features.send_message(event_message.sender, event_message.target, event_message.payload)


class ActivityLogFeature(Feature):
    def __init__(self) -> None:
        super().__init__("activity_log", scene_name="main")
        self.lines = ObservableList([])
        self.stop_log_subscription = None

    def build(self, host) -> None:
        self.container = host.app.add(PanelControl("log_panel", Rect(460, 16, 420, 220)), scene_name="main")
        self.title = self.container.add(LabelControl("log_title", Rect(16, 16, 320, 32), "Activity"))
        self.content = self.container.add(LabelControl("log_content", Rect(16, 56, 380, 140), "No events yet"))

    def on_register(self, host) -> None:
        self.host = host

    def bind_runtime(self, host) -> None:
        self.stop_log_subscription = self.lines.subscribe(
            lambda _change: setattr(self.content, "text", "\n".join(list(self.lines)[-4:]) if self.lines else "No events yet")
        )

    def on_update(self, host) -> None:
        while self.has_messages():
            message = self.pop_message()
            if message is None:
                continue
            if message.topic == "counter" and message.event == "incremented":
                value = message.get("value", 0)
                self.lines.append(f"Counter incremented to {value}")

    def shutdown_runtime(self, host) -> None:
        if self.stop_log_subscription is not None:
            self.stop_log_subscription()
            self.stop_log_subscription = None


config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(920, 520),
        window_title="FocusLog",
        fonts={"default": {"system": "arial", "size": 16}},
        initial_scene_name="main",
        scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
        feature_entries=(
            FeatureSpec("counter_feature", CounterFeature),
            FeatureSpec("activity_feature", ActivityLogFeature),
        ),
    )
)

host = type("Host", (), {})()
bootstrap_host_application(host, config)
host.counter_feature.host = host
host.activity_feature.host = host
host.app.run_entrypoint(target_fps=60)
```

## 8. Actions and Keyboard Shortcuts

### 1. Declare an ActionSpec

Add application-level actions in HostApplicationBindingSpec. Use action entries for global intent and key defaults where appropriate.

```python
from gui_do import ActionSpec

action_entries = (
    ActionSpec(action_id="exit", label="Exit", kind="exit", key=27),
)
```

### 2. Handle action in a plain Feature

For non-routed features, register and bind with the action manager in bind_runtime, then unbind and unregister in shutdown_runtime.

```python
def bind_runtime(self, host) -> None:
    host.app.actions.register_action("increment_counter", self.handle_increment_action)
    host.app.actions.bind_key(32, "increment_counter", scene="main")

def shutdown_runtime(self, host) -> None:
    host.app.actions.unbind_key(32, "increment_counter", scene="main")
    host.app.actions.unregister_action("increment_counter")
```

### 3. RoutedFeature shortcut with RoutedRuntimeSpec

RoutedRuntimeSpec can register hotkeys and overlays declaratively, and bind_routed_feature_lifecycle handles setup and teardown.

```python
import pygame

from gui_do import (
    ActionHotkeySpec,
    RoutedFeatureLifecycleSpec,
    RoutedRuntimeSpec,
    ShortcutOverlaySpec,
)

runtime_spec = RoutedRuntimeSpec(
    scene_name="main",
    action_hotkeys=(
        ActionHotkeySpec(action_name="quick_reset", handler=self.handle_reset_shortcut, key=pygame.K_r, scene_name="main"),
    ),
    shortcut_overlays=(
        ShortcutOverlaySpec(
            attr_name="help_overlay",
            toggle_action_name="show_help",
            toggle_key=pygame.K_F1,
            toggle_scene_name="main",
            manual_shortcut_lines=("Space: Increment", "R: Reset", "F1: Help"),
            manual_section_title="FocusLog",
            prepend_manual_shortcuts=True,
        ),
    ),
)
```

### 4. Shortcut help overlay

ShortcutOverlaySpec keeps discoverability inside the app and uses the same action registry and scene routing conventions as the rest of the runtime.

### 5. Updated listing

The complete listing with routed runtime is provided in Section 10.

## 9. Spec Reference for Builders

This section is intentionally concise. Use [MANUAL.md](MANUAL.md) for full detail.

- FeatureSpec: Declares a host attribute and factory for one feature instance.

```python
FeatureSpec("counter_feature", CounterFeature)
```

See bootstrap details in [MANUAL.md](MANUAL.md#81-application-bootstrap-and-host-configuration).

- SceneBundleBindingSpec: Declares one scene, transition behavior, and optional bundle extras.

```python
SceneBundleBindingSpec(scene_name="main", make_initial=True)
```

See scene composition guidance in [MANUAL.md](MANUAL.md#89-scene-window-and-task-panel-presentation-models).

- ActionSpec + ActionHotkeySpec: ActionSpec declares application actions at bootstrap; ActionHotkeySpec is used in routed runtime bundles.

```python
ActionSpec(action_id="exit", label="Exit", kind="exit", key=27)
ActionHotkeySpec(action_name="quick_reset", handler=self.handle_reset_shortcut, key=114, scene_name="main")
```

See routing details in [MANUAL.md](MANUAL.md#83-events-actions-input-mapping-and-routing).

- ShortcutOverlaySpec: Configures keyboard-help overlay content and toggle wiring.

```python
ShortcutOverlaySpec(attr_name="help_overlay", toggle_action_name="show_help", toggle_key=112)
```

See overlay systems in [MANUAL.md](MANUAL.md#88-overlays-dialogs-notifications-and-command-surfaces).

- RoutedRuntimeSpec + RoutedFeatureLifecycleSpec: Declarative bundle for routed feature runtime setup and teardown.

```python
RoutedFeatureLifecycleSpec(runtime_spec=runtime_spec)
```

See feature lifecycle details in [MANUAL.md](MANUAL.md#82-feature-lifecycle-and-feature-types).

- ToastManager: Use host.app.toasts.show(...) to present lightweight user notifications.

```python
host.app.toasts.show("Saved", duration_seconds=1.5)
```

See runtime services in [MANUAL.md](MANUAL.md#88-overlays-dialogs-notifications-and-command-surfaces).

## 10. Complete Project Listing

```python
import pygame
from pygame import Rect

from gui_do import (
    ActionHotkeySpec,
    ActionSpec,
    ButtonControl,
    Feature,
    FeatureMessage,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    ObservableList,
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


# Counter feature owns the primary user interaction and publishes counter events.
class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self.count = ObservableValue(0)
        self.stop_count_subscription = None
        self.host_ref = None

    def on_register(self, host) -> None:
        self.host_ref = host

    # Build creates controls and static layout only.
    def build(self, host) -> None:
        self.container = host.app.add(PanelControl("counter_panel", Rect(16, 16, 420, 240)), scene_name="main")
        self.title_label = self.container.add(LabelControl("counter_title", Rect(16, 14, 320, 32), "Counter"))
        self.count_label = self.container.add(LabelControl("count_label", Rect(16, 52, 320, 36), "Count: 0"))
        self.increment_button = self.container.add(
            ButtonControl("increment_button", Rect(16, 96, 180, 40), "Increment", on_click=self.increment_count)
        )

    # bind_runtime installs subscriptions and action bindings after all features built.
    def bind_runtime(self, host) -> None:
        self.stop_count_subscription = self.count.subscribe(
            lambda value: setattr(self.count_label, "text", f"Count: {value}")
        )
        host.app.actions.register_action("increment_counter", self.handle_increment_action)
        host.app.actions.bind_key(pygame.K_SPACE, "increment_counter", scene="main")

    # shutdown_runtime removes runtime bindings to prevent stale callbacks.
    def shutdown_runtime(self, host) -> None:
        if self.stop_count_subscription is not None:
            self.stop_count_subscription()
            self.stop_count_subscription = None
        host.app.actions.unbind_key(pygame.K_SPACE, "increment_counter", scene="main")
        host.app.actions.unregister_action("increment_counter")

    def handle_increment_action(self, event) -> bool:
        self.increment_count()
        return True

    def increment_count(self) -> None:
        self.count.value += 1
        if self.host_ref is None:
            return
        payload = FeatureMessage.from_payload(
            sender="counter",
            target="activity_log",
            payload={"topic": "counter", "event": "incremented", "value": self.count.value},
        )
        self.host_ref.app.features.send_message(payload.sender, payload.target, payload.payload)


# Activity log uses RoutedFeature to get declarative hotkey and overlay runtime wiring.
class ActivityLogFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("activity_log", scene_name="main")
        self.lines = ObservableList([])
        self.stop_lines_subscription = None
        self.help_overlay = None
        self.runtime_spec = RoutedRuntimeSpec(
            scene_name="main",
            action_hotkeys=(
                ActionHotkeySpec(
                    action_name="quick_reset",
                    handler=self.handle_reset_shortcut,
                    key=pygame.K_r,
                    scene_name="main",
                ),
            ),
            shortcut_overlays=(
                ShortcutOverlaySpec(
                    attr_name="help_overlay",
                    toggle_action_name="show_help",
                    toggle_key=pygame.K_F1,
                    toggle_scene_name="main",
                    manual_shortcut_lines=(
                        "Space: Increment",
                        "R: Reset log",
                        "F1: Shortcut help",
                    ),
                    manual_section_title="FocusLog",
                    prepend_manual_shortcuts=True,
                ),
            ),
        )
        self.lifecycle_spec = RoutedFeatureLifecycleSpec(runtime_spec=self.runtime_spec)

    def build(self, host) -> None:
        self.container = host.app.add(PanelControl("log_panel", Rect(460, 16, 420, 240)), scene_name="main")
        self.title = self.container.add(LabelControl("log_title", Rect(16, 14, 320, 32), "Activity Log"))
        self.content = self.container.add(LabelControl("log_content", Rect(16, 52, 380, 160), "No events yet"))

    def bind_runtime(self, host) -> None:
        bind_routed_feature_lifecycle(self, host, self.lifecycle_spec)
        self.stop_lines_subscription = self.lines.subscribe(
            lambda _change: setattr(self.content, "text", "\n".join(list(self.lines)[-6:]) if self.lines else "No events yet")
        )

    def shutdown_runtime(self, host) -> None:
        if self.stop_lines_subscription is not None:
            self.stop_lines_subscription()
            self.stop_lines_subscription = None
        shutdown_routed_feature_lifecycle(self, host, self.lifecycle_spec)

    def on_update(self, host) -> None:
        while self.has_messages():
            message = self.pop_message()
            if message is None:
                continue
            if message.topic == "counter" and message.event == "incremented":
                self.lines.append(f"Counter -> {message.get('value', 0)}")

    def handle_reset_shortcut(self, event) -> bool:
        self.lines.clear()
        self.lines.append("Log reset with keyboard shortcut")
        return True


# Declarative app config describes scenes, actions, and feature composition.
config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(920, 540),
        window_title="FocusLog",
        fonts={"default": {"system": "arial", "size": 16}},
        initial_scene_name="main",
        scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
        feature_entries=(
            FeatureSpec("counter_feature", CounterFeature),
            FeatureSpec("activity_feature", ActivityLogFeature),
        ),
        action_entries=(
            ActionSpec(action_id="exit", label="Exit", kind="exit", key=pygame.K_ESCAPE),
        ),
    )
)


# Host object receives runtime attributes and starts the frame loop.
host = type("Host", (), {})()
bootstrap_host_application(host, config)
host.app.run_entrypoint(target_fps=60)
```

## 11. Next Steps

Read [MANUAL.md](MANUAL.md) next for full system coverage, then inspect [demo_features/](demo_features) as living composition references that follow the folder-per-feature pattern where package root init files are the public import surface.

Suggested exploration topics:
- Overlays and command surfaces.
- Persistence and snapshot migration.
- Scene navigation and transitions.
- Telemetry and diagnostics.
- Graphics and audio integration points.

Most relevant manual chapters for immediate progress:
- [8.1 Application Bootstrap and Host Configuration](MANUAL.md#81-application-bootstrap-and-host-configuration)
- [8.2 Feature Lifecycle and Feature Types](MANUAL.md#82-feature-lifecycle-and-feature-types)
- [8.3 Events, Actions, Input Mapping, and Routing](MANUAL.md#83-events-actions-input-mapping-and-routing)
- [8.4 State and Observables](MANUAL.md#84-state-and-observables)

data_driven_runtime.py and feature_lifecycle.py are readable and practical; reading them will make bootstrap and lifecycle sequencing much easier to reason about.
