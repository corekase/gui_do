# gui_do Tutorial

## 1. Introduction

gui_do is a Python GUI framework built on pygame that helps you build applications as composed features instead of one monolithic event loop. You declare app structure with specs, then let bootstrap wire scenes, features, actions, and runtime systems in a deterministic order. That split keeps your feature code focused on behavior and UI intent rather than framework plumbing.

In this tutorial, you will build a complete project: a **Counter + Activity Log Dashboard**. It has two coordinated features with different responsibilities. The counter feature owns the main interaction and state updates, while the activity log feature receives messages and shows the latest activity. The final result includes reactive UI updates, keyboard actions, routed runtime wiring, shortcut discovery overlay support, and clean shutdown behavior.

As you explore built-in examples, follow the established demo organization convention: each folder under `demo_features/` is one feature package (or tightly related cluster), and each package `__init__.py` is the public import surface for that package. Bootstrap code should import package roots, not internal submodules.

Prerequisites:

- Working Python knowledge
- `pip`
- `pygame`
- `numpy`
- No prior GUI framework experience required

For deeper reference while reading, keep [MANUAL.md](MANUAL.md) open.

## 2. Core Concepts

### Declarative specs vs imperative wiring

In imperative GUI setups, startup code tends to grow into a large sequence of manual wiring calls. Every new scene, feature, action, or shortcut adds another place to edit. gui_do uses declarative specs instead: you describe **what exists** (scenes, features, actions, runtime bindings), then bootstrap builds **how it is connected**.

This matters because feature code stays decoupled. A feature does not need to know who constructed it, where other features live, or the order of low-level runtime hookups. It only implements lifecycle behavior for its own responsibility.

### Reactive state

`ObservableValue` is a value holder with subscriptions. When `.value` changes, subscribers are notified immediately. This removes polling loops and keeps data flow explicit.

```python
from gui_do import ObservableValue

count = ObservableValue(0)
unsubscribe = count.subscribe(lambda value: print(f"Count changed: {value}"))
count.value = 1
unsubscribe()
```

For collections, use `ObservableList` and `ObservableDict`. For derived values, use `ComputedValue`.

### Feature lifecycle

Each feature participates in clear phases:

- `build`: construct controls and structural UI for that feature
- `bind_runtime`: attach subscriptions, action handlers, runtime bindings
- `on_update`: per-frame logic updates
- `handle_event`: direct event handling when needed
- `draw`: custom drawing when needed
- `shutdown_runtime`: teardown subscriptions and runtime resources

A key guarantee is ordering: all features in a scene finish `build` before any `bind_runtime` runs. That lets you create controls first, then safely connect subscriptions/actions against a complete control tree. Subscriptions belong in `bind_runtime` and must be removed in `shutdown_runtime`.

## 3. Installation and Setup

Install from repository root:

```bash
python -m pip install -e . --no-deps
```

Dependencies: `pygame` and `numpy`.

Verify install:

```bash
python -c "import gui_do; print(gui_do.__version__)"
```

Minimal imports to start:

```python
from gui_do import (
    HostApplicationBindingSpec,
    build_host_application_config,
    bootstrap_host_application,
    Feature,
)
```

gui_do has two startup paths:

- Declarative bootstrap (recommended and used in this tutorial)
- Manual `GuiApplication` construction (advanced path; see [MANUAL.md](MANUAL.md))

## 4. Your First Feature

We start with a single visual feature so you can see the lifecycle shape in isolation.

### Step 1. Define the feature class

Use `Feature` as the default type for visual UI behavior. It gives a full lifecycle with sensible defaults. `DirectFeature` and `RoutedFeature` are specialized and will appear later.

```python
from gui_do import Feature


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")

    def build(self, host) -> None:
        pass
```

`build` is where you construct the control tree owned by this feature.

### Step 2. Add a control

Controls live inside a layout region; they are not independent top-level windows by default. `host.screen_rect` represents the available screen canvas.

```python
from pygame import Rect
from gui_do import LabelControl, PanelControl


def build(self, host) -> None:
    panel_rect = Rect(24, 24, host.screen_rect.width - 48, 120)
    self.root_panel = host.app.add(PanelControl("counter_panel", panel_rect), scene_name="main")
    self.counter_label = self.root_panel.add(LabelControl("count_label", Rect(16, 16, 320, 40), "Count: 0"))
```

### Step 3. Declare the config

`HostApplicationBindingSpec` describes your app composition. `SceneBundleBindingSpec` declares scene behavior. `FeatureSpec` declares feature registration.

```python
from gui_do import (
    FeatureSpec,
    HostApplicationBindingSpec,
    SceneBundleBindingSpec,
    build_host_application_config,
)

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(960, 540),
        window_title="Counter Dashboard",
        fonts={"default": "arial"},
        initial_scene_name="main",
        scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
        feature_entries=(FeatureSpec("counter_feature", CounterFeature),),
    )
)
```

### Step 4. Bootstrap and run

`bootstrap_host_application` reads your built config, initializes systems, and attaches app/runtime attributes to your host object. `run_entrypoint` starts the frame loop.

```python
from gui_do import bootstrap_host_application


class CounterApp:
    def __init__(self) -> None:
        bootstrap_host_application(self, config)


host = CounterApp()
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
    PanelControl,
    SceneBundleBindingSpec,
    bootstrap_host_application,
    build_host_application_config,
)


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")

    def build(self, host) -> None:
        panel_rect = Rect(24, 24, host.screen_rect.width - 48, 120)
        self.root_panel = host.app.add(PanelControl("counter_panel", panel_rect), scene_name="main")
        self.counter_label = self.root_panel.add(LabelControl("count_label", Rect(16, 16, 320, 40), "Count: 0"))


class CounterApp:
    def __init__(self) -> None:
        config = build_host_application_config(
            HostApplicationBindingSpec(
                display_size=(960, 540),
                window_title="Counter Dashboard",
                fonts={"default": "arial"},
                initial_scene_name="main",
                scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
                feature_entries=(FeatureSpec("counter_feature", CounterFeature),),
            )
        )
        bootstrap_host_application(self, config)


if __name__ == "__main__":
    host = CounterApp()
    host.app.run_entrypoint(target_fps=60)
```

## 5. Reactive State: Making the UI Respond

Now we make the project interactive and reactive.

### Step 1. Introduce `ObservableValue`

`ObservableValue` stores the source-of-truth value. Setting `.value` notifies subscribers.

```python
from gui_do import ObservableValue


def __init__(self) -> None:
    super().__init__("counter_feature", scene_name="main")
    self.count_value = ObservableValue(0)
    self.count_subscription = None
```

### Step 2. Add a button

Buttons trigger behavior through callbacks. Here, click increments reactive state.

```python
from gui_do import ButtonControl


def build(self, host) -> None:
    self.increment_button = self.root_panel.add(
        ButtonControl("increment_button", Rect(16, 64, 180, 36), "Increment", on_click=self.increment)
    )


def increment(self) -> None:
    self.count_value.value = int(self.count_value.value) + 1
```

### Step 3. Wire observable to label in `bind_runtime`

This belongs in `bind_runtime`, not `build`, because the control tree is guaranteed ready and we are attaching runtime relationships.

```python
def bind_runtime(self, host) -> None:
    self.count_subscription = self.count_value.subscribe(
        lambda value: setattr(self.counter_label, "text", f"Count: {value}")
    )
```

### Step 4. Unsubscribe in `shutdown_runtime`

Subscriptions keep references alive. Always tear them down.

```python
def shutdown_runtime(self, host) -> None:
    if self.count_subscription is not None:
        self.count_subscription()
        self.count_subscription = None
```

### Step 5. Run the updated listing

```python
from pygame import Rect

from gui_do import (
    ButtonControl,
    Feature,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    ObservableValue,
    PanelControl,
    SceneBundleBindingSpec,
    bootstrap_host_application,
    build_host_application_config,
)


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self.count_value = ObservableValue(0)
        self.count_subscription = None

    def build(self, host) -> None:
        panel_rect = Rect(24, 24, host.screen_rect.width - 48, 160)
        self.root_panel = host.app.add(PanelControl("counter_panel", panel_rect), scene_name="main")
        self.counter_label = self.root_panel.add(LabelControl("count_label", Rect(16, 16, 320, 40), "Count: 0"))
        self.increment_button = self.root_panel.add(
            ButtonControl("increment_button", Rect(16, 64, 180, 36), "Increment", on_click=self.increment)
        )

    def bind_runtime(self, host) -> None:
        self.count_subscription = self.count_value.subscribe(
            lambda value: setattr(self.counter_label, "text", f"Count: {value}")
        )

    def shutdown_runtime(self, host) -> None:
        if self.count_subscription is not None:
            self.count_subscription()
            self.count_subscription = None

    def increment(self) -> None:
        self.count_value.value = int(self.count_value.value) + 1


class CounterApp:
    def __init__(self) -> None:
        config = build_host_application_config(
            HostApplicationBindingSpec(
                display_size=(960, 540),
                window_title="Counter Dashboard",
                fonts={"default": "arial"},
                initial_scene_name="main",
                scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
                feature_entries=(FeatureSpec("counter_feature", CounterFeature),),
            )
        )
        bootstrap_host_application(self, config)


if __name__ == "__main__":
    host = CounterApp()
    host.app.run_entrypoint(target_fps=60)
```

## 6. Feature Types

Use feature types by intent, not by habit:

- `Feature`: standard choice for visual behavior with lifecycle hooks. Use this by default.
- `DirectFeature`: low-level direct update/draw path with no default wiring conveniences. Rarely needed.
- `LogicFeature`: non-visual background coordination or pipeline logic with message-driven behavior.
- `RoutedFeature`: message-topic dispatch and declarative runtime bundles (`RoutedRuntimeSpec`, `RoutedFeatureLifecycleSpec`) for structured hotkeys, overlays, and subscriptions.

In this project, the counter UI stays a `Feature`, while the activity log becomes a `RoutedFeature` so it can show clean topic-based message handling and routed runtime wiring.

## 7. A Second Feature and Feature Communication

Now we add a second feature with a different responsibility: activity logging.

### Step 1. Define the second feature

The second feature gets its own region and owns display of the latest activity text.

### Step 2. Shared state via `ObservableValue`

There are two common communication paths:

- Shared observable reference (simple, direct coupling)
- Message passing via feature manager (looser coupling)

We will use both: counter state remains local to `CounterFeature`, while activity summaries are delivered by message to `ActivityLogFeature`.

Shared observable via host example:

```python
# In CounterFeature.build
host.shared_count = self.count_value

# In ActivityLogFeature.bind_runtime
self.shared_count_subscription = host.shared_count.subscribe(
    lambda value: setattr(self.log_label, "text", f"Shared count is {value}")
)
```

### Step 3. Feature messaging with a concrete `FeatureMessage` subclass

We define `CounterChangedMessage` to make payload structure explicit and typed.

```python
from gui_do import FeatureMessage


class CounterChangedMessage(FeatureMessage):
    @classmethod
    def create(cls, sender: str, target: str, count: int) -> "CounterChangedMessage":
        return cls(sender=sender, target=target, payload={"topic": "counter.changed", "count": int(count)})

    def to_payload(self) -> dict:
        return dict(self.payload)

    @classmethod
    def from_envelope(cls, envelope: FeatureMessage) -> "CounterChangedMessage":
        return cls(sender=envelope.sender, target=envelope.target, payload=dict(envelope.payload))
```

The sender uses `self.send_message(...)` with `message.to_payload()`. The routed receiver maps topic names to handler methods.

### Step 4. Updated full listing

```python
from pygame import Rect

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
    bootstrap_host_application,
    build_host_application_config,
)


class CounterChangedMessage(FeatureMessage):
    @classmethod
    def create(cls, sender: str, target: str, count: int) -> "CounterChangedMessage":
        return cls(sender=sender, target=target, payload={"topic": "counter.changed", "count": int(count)})

    def to_payload(self) -> dict:
        return dict(self.payload)

    @classmethod
    def from_envelope(cls, envelope: FeatureMessage) -> "CounterChangedMessage":
        return cls(sender=envelope.sender, target=envelope.target, payload=dict(envelope.payload))


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self.count_value = ObservableValue(0)
        self.count_subscription = None

    def build(self, host) -> None:
        panel_rect = Rect(24, 24, 440, 200)
        self.root_panel = host.app.add(PanelControl("counter_panel", panel_rect), scene_name="main")
        self.counter_label = self.root_panel.add(LabelControl("count_label", Rect(16, 16, 300, 40), "Count: 0"))
        self.increment_button = self.root_panel.add(
            ButtonControl("increment_button", Rect(16, 64, 180, 36), "Increment", on_click=self.increment)
        )

    def bind_runtime(self, host) -> None:
        self.count_subscription = self.count_value.subscribe(
            lambda value: setattr(self.counter_label, "text", f"Count: {value}")
        )

    def shutdown_runtime(self, host) -> None:
        if self.count_subscription is not None:
            self.count_subscription()
            self.count_subscription = None

    def increment(self) -> None:
        next_value = int(self.count_value.value) + 1
        self.count_value.value = next_value
        message = CounterChangedMessage.create(self.name, "activity_log_feature", next_value)
        self.send_message("activity_log_feature", message.to_payload())


class ActivityLogFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("activity_log_feature", scene_name="main")
        self.log_text = ObservableValue("Activity: waiting for events")
        self.log_subscription = None

    def build(self, host) -> None:
        panel_rect = Rect(500, 24, 420, 200)
        self.root_panel = host.app.add(PanelControl("log_panel", panel_rect), scene_name="main")
        self.log_label = self.root_panel.add(LabelControl("log_label", Rect(16, 16, 380, 120), self.log_text.value))

    def bind_runtime(self, host) -> None:
        self.log_subscription = self.log_text.subscribe(lambda value: setattr(self.log_label, "text", str(value)))

    def shutdown_runtime(self, host) -> None:
        if self.log_subscription is not None:
            self.log_subscription()
            self.log_subscription = None

    def message_handlers(self) -> dict:
        return {"counter.changed": self.on_counter_changed}

    def on_counter_changed(self, host, envelope: FeatureMessage) -> None:
        typed_message = CounterChangedMessage.from_envelope(envelope)
        self.log_text.value = f"Activity: counter changed to {typed_message.payload['count']}"


class CounterApp:
    def __init__(self) -> None:
        config = build_host_application_config(
            HostApplicationBindingSpec(
                display_size=(960, 540),
                window_title="Counter Dashboard",
                fonts={"default": "arial"},
                initial_scene_name="main",
                scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
                feature_entries=(
                    FeatureSpec("counter_feature", CounterFeature),
                    FeatureSpec("activity_log_feature", ActivityLogFeature),
                ),
            )
        )
        bootstrap_host_application(self, config)


if __name__ == "__main__":
    host = CounterApp()
    host.app.run_entrypoint(target_fps=60)
```

## 8. Actions and Keyboard Shortcuts

Now we make the primary action available by keyboard and add shortcut discoverability.

### Step 1. Declare an `ActionSpec` and use `ActionHotkeySpec`

`ActionSpec` entries are part of host bootstrap declarations. In this project, we keep `exit` as a host action and add feature-local action hotkeys through routed runtime.

```python
import pygame
from gui_do import ActionSpec

action_entries = (
    ActionSpec(action_id="exit", label="Exit", kind="exit", key=pygame.K_ESCAPE),
)
```

### Step 2. Plain `Feature` action callback binding and teardown

In current gui_do, plain feature action binding is done through `host.app.actions.register_action(...)` and `bind_key(...)`, then cleaned up with `unbind_key(...)` and `unregister_action(...)`.

```python
import pygame


def bind_runtime(self, host) -> None:
    self.action_name = "increment_counter"
    host.app.actions.register_action(self.action_name, lambda event: (self.increment() or True))
    host.app.actions.bind_key(pygame.K_I, self.action_name, scene="main")


def shutdown_runtime(self, host) -> None:
    host.app.actions.unbind_key(pygame.K_I, self.action_name, scene="main")
    host.app.actions.unregister_action(self.action_name)
```

### Step 3. RoutedFeature shortcut wiring with lifecycle helpers

`RoutedFeature` supports declarative runtime bundles. We can attach `ActionHotkeySpec` and let lifecycle helper functions wire/unwire runtime resources.

```python
import pygame
from gui_do import (
    ActionHotkeySpec,
    RoutedFeatureLifecycleSpec,
    RoutedRuntimeSpec,
    bind_routed_feature_lifecycle,
    shutdown_routed_feature_lifecycle,
)

lifecycle_spec = RoutedFeatureLifecycleSpec(
    runtime_spec=RoutedRuntimeSpec(
        scene_name="main",
        action_hotkeys=(
            ActionHotkeySpec(action_name="clear_activity", handler=lambda event: True, key=pygame.K_L, scene_name="main"),
        ),
    )
)
```

### Step 4. Add shortcut help overlay

`ShortcutOverlaySpec` makes keyboard discoverability declarative.

```python
import pygame
from gui_do import ShortcutOverlaySpec

shortcut_overlays = (
    ShortcutOverlaySpec(
        attr_name="shortcut_overlay",
        toggle_action_name="toggle_shortcuts",
        toggle_key=pygame.K_F1,
        toggle_scene_name="main",
        manual_shortcut_lines=(
            "I: Increment counter",
            "L: Clear activity log",
            "F1: Toggle shortcut help",
            "Escape: Exit",
        ),
    ),
)
```

### Step 5. Updated listing with keyboard actions

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
    ObservableValue,
    PanelControl,
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


class CounterChangedMessage(FeatureMessage):
    @classmethod
    def create(cls, sender: str, target: str, count: int) -> "CounterChangedMessage":
        return cls(sender=sender, target=target, payload={"topic": "counter.changed", "count": int(count)})

    def to_payload(self) -> dict:
        return dict(self.payload)

    @classmethod
    def from_envelope(cls, envelope: FeatureMessage) -> "CounterChangedMessage":
        return cls(sender=envelope.sender, target=envelope.target, payload=dict(envelope.payload))


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self.count_value = ObservableValue(0)
        self.count_subscription = None
        self.action_name = "increment_counter"

    def build(self, host) -> None:
        panel_rect = Rect(24, 24, 440, 220)
        self.root_panel = host.app.add(PanelControl("counter_panel", panel_rect), scene_name="main")
        self.counter_label = self.root_panel.add(LabelControl("count_label", Rect(16, 16, 300, 40), "Count: 0"))
        self.increment_button = self.root_panel.add(
            ButtonControl("increment_button", Rect(16, 64, 180, 36), "Increment", on_click=self.increment)
        )

    def bind_runtime(self, host) -> None:
        self.count_subscription = self.count_value.subscribe(
            lambda value: setattr(self.counter_label, "text", f"Count: {value}")
        )
        host.app.actions.register_action(self.action_name, lambda event: (self.increment() or True))
        host.app.actions.bind_key(pygame.K_I, self.action_name, scene="main")

    def shutdown_runtime(self, host) -> None:
        if self.count_subscription is not None:
            self.count_subscription()
            self.count_subscription = None
        host.app.actions.unbind_key(pygame.K_I, self.action_name, scene="main")
        host.app.actions.unregister_action(self.action_name)

    def increment(self) -> None:
        next_value = int(self.count_value.value) + 1
        self.count_value.value = next_value
        message = CounterChangedMessage.create(self.name, "activity_log_feature", next_value)
        self.send_message("activity_log_feature", message.to_payload())


class ActivityLogFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("activity_log_feature", scene_name="main")
        self.log_text = ObservableValue("Activity: waiting for events")
        self.log_subscription = None
        self.lifecycle_spec = RoutedFeatureLifecycleSpec(
            runtime_spec=RoutedRuntimeSpec(
                scene_name="main",
                action_hotkeys=(
                    ActionHotkeySpec(
                        action_name="clear_activity",
                        handler=lambda event: (self.clear_activity() or True),
                        key=pygame.K_L,
                        scene_name="main",
                    ),
                ),
                shortcut_overlays=(
                    ShortcutOverlaySpec(
                        attr_name="shortcut_overlay",
                        toggle_action_name="toggle_shortcuts",
                        toggle_key=pygame.K_F1,
                        toggle_scene_name="main",
                        manual_shortcut_lines=(
                            "I: Increment counter",
                            "L: Clear activity log",
                            "F1: Toggle shortcut help",
                            "Escape: Exit",
                        ),
                    ),
                ),
            )
        )

    def build(self, host) -> None:
        panel_rect = Rect(500, 24, 420, 220)
        self.root_panel = host.app.add(PanelControl("log_panel", panel_rect), scene_name="main")
        self.log_label = self.root_panel.add(LabelControl("log_label", Rect(16, 16, 380, 160), self.log_text.value))

    def bind_runtime(self, host) -> None:
        self.log_subscription = self.log_text.subscribe(lambda value: setattr(self.log_label, "text", str(value)))
        bind_routed_feature_lifecycle(self, host, self.lifecycle_spec)

    def shutdown_runtime(self, host) -> None:
        if self.log_subscription is not None:
            self.log_subscription()
            self.log_subscription = None
        shutdown_routed_feature_lifecycle(self, host, self.lifecycle_spec)

    def message_handlers(self) -> dict:
        return {"counter.changed": self.on_counter_changed}

    def on_counter_changed(self, host, envelope: FeatureMessage) -> None:
        typed_message = CounterChangedMessage.from_envelope(envelope)
        self.log_text.value = f"Activity: counter changed to {typed_message.payload['count']}"

    def clear_activity(self) -> None:
        self.log_text.value = "Activity: cleared"


class CounterApp:
    def __init__(self) -> None:
        config = build_host_application_config(
            HostApplicationBindingSpec(
                display_size=(960, 540),
                window_title="Counter Dashboard",
                fonts={"default": "arial"},
                initial_scene_name="main",
                scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
                feature_entries=(
                    FeatureSpec("counter_feature", CounterFeature),
                    FeatureSpec("activity_log_feature", ActivityLogFeature),
                ),
                action_entries=(
                    ActionSpec(action_id="exit", label="Exit", kind="exit", key=pygame.K_ESCAPE),
                ),
            )
        )
        bootstrap_host_application(self, config)


if __name__ == "__main__":
    host = CounterApp()
    host.app.run_entrypoint(target_fps=60)
```

## 9. Spec Reference for Builders

This is a quick map of the key specs used above. For full details, use [MANUAL.md](MANUAL.md), especially the systems reference chapters.

### `FeatureSpec`

Declares a feature attribute name and a factory.

```python
FeatureSpec("counter_feature", CounterFeature)
```

Reference: [MANUAL.md Section 8.2](MANUAL.md#82-feature-lifecycle-and-feature-types)

### `SceneBundleBindingSpec`

Declares scene setup/runtime bundle details, including transition and initial-scene behavior.

```python
SceneBundleBindingSpec(scene_name="main", make_initial=True)
```

Reference: [MANUAL.md Section 8.1](MANUAL.md#81-application-bootstrap-and-host-configuration)

### `ActionSpec` + `ActionHotkeySpec`

`ActionSpec` defines host-level standard actions. `ActionHotkeySpec` is ideal for routed feature-local hotkeys.

```python
ActionSpec(action_id="exit", label="Exit", kind="exit", key=pygame.K_ESCAPE)
ActionHotkeySpec(action_name="clear_activity", handler=lambda event: True, key=pygame.K_L, scene_name="main")
```

Reference: [MANUAL.md Section 8.3](MANUAL.md#83-events-actions-input-mapping-and-routing)

### `ShortcutOverlaySpec`

Configures shortcut help overlay behavior and toggle action.

```python
ShortcutOverlaySpec(attr_name="shortcut_overlay", toggle_action_name="toggle_shortcuts", toggle_key=pygame.K_F1)
```

Reference: [MANUAL.md Section 8.8](MANUAL.md#88-overlays-dialogs-notifications-and-command-surfaces)

### `RoutedRuntimeSpec` + `RoutedFeatureLifecycleSpec`

Bundles routed runtime wiring (hotkeys, subscriptions, overlays) and connects bind/shutdown with helpers.

```python
RoutedFeatureLifecycleSpec(runtime_spec=RoutedRuntimeSpec(scene_name="main", action_hotkeys=(), shortcut_overlays=()))
```

Reference: [MANUAL.md Section 8.2](MANUAL.md#82-feature-lifecycle-and-feature-types) and [MANUAL.md Section 8.3](MANUAL.md#83-events-actions-input-mapping-and-routing)

### `ToastManager`

Toast notifications are available through the host toast manager.

```python
host.toasts.show("Saved", title="Counter Dashboard")
```

Reference: [MANUAL.md Section 8.8](MANUAL.md#88-overlays-dialogs-notifications-and-command-surfaces)

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
    ObservableValue,
    PanelControl,
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


# Typed message helper keeps payload format explicit between features.
class CounterChangedMessage(FeatureMessage):
    @classmethod
    def create(cls, sender: str, target: str, count: int) -> "CounterChangedMessage":
        return cls(sender=sender, target=target, payload={"topic": "counter.changed", "count": int(count)})

    def to_payload(self) -> dict:
        return dict(self.payload)

    @classmethod
    def from_envelope(cls, envelope: FeatureMessage) -> "CounterChangedMessage":
        return cls(sender=envelope.sender, target=envelope.target, payload=dict(envelope.payload))


# Feature 1 owns primary interaction and source-of-truth counter state.
class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self.count_value = ObservableValue(0)
        self.count_subscription = None
        self.action_name = "increment_counter"

    def build(self, host) -> None:
        panel_rect = Rect(24, 24, 440, 240)
        self.root_panel = host.app.add(PanelControl("counter_panel", panel_rect), scene_name="main")
        self.counter_label = self.root_panel.add(LabelControl("count_label", Rect(16, 16, 320, 40), "Count: 0"))
        self.increment_button = self.root_panel.add(
            ButtonControl("increment_button", Rect(16, 64, 200, 36), "Increment", on_click=self.increment)
        )
        self.help_label = self.root_panel.add(
            LabelControl("counter_help", Rect(16, 116, 360, 32), "Hotkeys: I increment, L clear log, F1 shortcuts")
        )

    def bind_runtime(self, host) -> None:
        self.count_subscription = self.count_value.subscribe(
            lambda value: setattr(self.counter_label, "text", f"Count: {value}")
        )
        host.app.actions.register_action(self.action_name, lambda event: (self.increment() or True))
        host.app.actions.bind_key(pygame.K_I, self.action_name, scene="main")

    def shutdown_runtime(self, host) -> None:
        if self.count_subscription is not None:
            self.count_subscription()
            self.count_subscription = None
        host.app.actions.unbind_key(pygame.K_I, self.action_name, scene="main")
        host.app.actions.unregister_action(self.action_name)

    def increment(self) -> None:
        next_value = int(self.count_value.value) + 1
        self.count_value.value = next_value
        typed_message = CounterChangedMessage.create(self.name, "activity_log_feature", next_value)
        self.send_message("activity_log_feature", typed_message.to_payload())


# Feature 2 is routed and focuses on activity display plus routed shortcuts.
class ActivityLogFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("activity_log_feature", scene_name="main")
        self.log_text = ObservableValue("Activity: waiting for events")
        self.log_subscription = None
        self.lifecycle_spec = RoutedFeatureLifecycleSpec(
            runtime_spec=RoutedRuntimeSpec(
                scene_name="main",
                action_hotkeys=(
                    ActionHotkeySpec(
                        action_name="clear_activity",
                        handler=lambda event: (self.clear_activity() or True),
                        key=pygame.K_L,
                        scene_name="main",
                    ),
                ),
                shortcut_overlays=(
                    ShortcutOverlaySpec(
                        attr_name="shortcut_overlay",
                        toggle_action_name="toggle_shortcuts",
                        toggle_key=pygame.K_F1,
                        toggle_scene_name="main",
                        manual_shortcut_lines=(
                            "I: Increment counter",
                            "L: Clear activity log",
                            "F1: Toggle shortcut help",
                            "Escape: Exit",
                        ),
                    ),
                ),
            )
        )

    def build(self, host) -> None:
        panel_rect = Rect(500, 24, 420, 240)
        self.root_panel = host.app.add(PanelControl("log_panel", panel_rect), scene_name="main")
        self.log_label = self.root_panel.add(LabelControl("log_label", Rect(16, 16, 380, 140), self.log_text.value))

    def bind_runtime(self, host) -> None:
        self.log_subscription = self.log_text.subscribe(lambda value: setattr(self.log_label, "text", str(value)))
        bind_routed_feature_lifecycle(self, host, self.lifecycle_spec)

    def shutdown_runtime(self, host) -> None:
        if self.log_subscription is not None:
            self.log_subscription()
            self.log_subscription = None
        shutdown_routed_feature_lifecycle(self, host, self.lifecycle_spec)

    def message_handlers(self) -> dict:
        return {"counter.changed": self.on_counter_changed}

    def on_counter_changed(self, host, envelope: FeatureMessage) -> None:
        typed_message = CounterChangedMessage.from_envelope(envelope)
        count_value = typed_message.payload["count"]
        self.log_text.value = f"Activity: counter changed to {count_value}"
        host.app.toasts.show(f"Counter is now {count_value}", title="Activity")

    def clear_activity(self) -> None:
        self.log_text.value = "Activity: cleared"


# Host application declares scene, features, and standard actions declaratively.
class CounterDashboardApp:
    def __init__(self) -> None:
        config = build_host_application_config(
            HostApplicationBindingSpec(
                display_size=(960, 540),
                window_title="Counter + Activity Dashboard",
                fonts={"default": "arial"},
                initial_scene_name="main",
                scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
                feature_entries=(
                    FeatureSpec("counter_feature", CounterFeature),
                    FeatureSpec("activity_log_feature", ActivityLogFeature),
                ),
                action_entries=(
                    ActionSpec(action_id="exit", label="Exit", kind="exit", key=pygame.K_ESCAPE),
                ),
            )
        )
        bootstrap_host_application(self, config)


# Entry point starts the deterministic application frame loop.
if __name__ == "__main__":
    host = CounterDashboardApp()
    host.app.run_entrypoint(target_fps=60)
```

## 11. Next Steps

Now that you can build a complete feature-composed app, go deeper in this order:

1. Read [MANUAL.md](MANUAL.md) end-to-end for full system reference.
2. Explore [demo_features/](demo_features) as living package-level reference patterns.
3. Expand your project with overlays, persistence, scene navigation, telemetry, and graphics.

Most relevant manual sections for immediate progress:

- [MANUAL.md Section 8.1](MANUAL.md#81-application-bootstrap-and-host-configuration)
- [MANUAL.md Section 8.2](MANUAL.md#82-feature-lifecycle-and-feature-types)
- [MANUAL.md Section 8.3](MANUAL.md#83-events-actions-input-mapping-and-routing)
- [MANUAL.md Section 8.4](MANUAL.md#84-state-and-observables)

For framework internals that are especially readable, inspect `data_driven_runtime.py` and `feature_lifecycle.py`. Reading those files after finishing this tutorial usually demystifies bootstrap and runtime sequencing quickly.
