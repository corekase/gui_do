# gui_do Tutorial

## 1. Introduction

gui_do is a data-driven GUI framework for Python applications built on pygame. Instead of wiring every manager manually, you describe scenes, features, actions, and runtime behavior through specs, then let bootstrap assemble the runtime consistently. The result is a clear separation between declarative app structure and imperative feature behavior.

In this tutorial, we will build a multi-feature application called **PulseBoard**. It has a counter feature, an activity-log feature, reactive shared state, typed feature messaging, and keyboard shortcuts with a routed shortcut-help overlay. By the end, you will have a complete project structure you can extend into a real tool.

Prerequisites:

- Python and pip
- `pygame`
- `numpy`
- No prior GUI-framework experience required

For deeper system theory while you read, keep [MANUAL.md](MANUAL.md) open.

## 2. Core Concepts

Before writing code, align on the three ideas that make gui_do predictable.

### Declarative specs vs imperative wiring

In many GUI stacks, startup logic becomes a long, order-sensitive imperative script. gui_do shifts that to declarative specs such as `HostApplicationBindingSpec`, `FeatureSpec`, and `SceneBundleBindingSpec`. You describe *what* should exist, and bootstrap handles *how* to build and connect it.

Why this matters:

- You can reason about app structure from data objects.
- Feature code stays local and focused.
- Bootstrap ordering stays deterministic as projects grow.

### Reactive state

`ObservableValue` is a value container that notifies subscribers when `.value` changes. That means UI updates can be direct and event-driven instead of polled each frame.

```python
from gui_do import ObservableValue

count = ObservableValue(0)
unsubscribe = count.subscribe(lambda value: print(f"count changed to {value}"))
count.value = 1
unsubscribe()
```

You also have `ObservableList` and `ObservableDict` for collections, and `ComputedValue` for derived state.

### Feature lifecycle

A standard `Feature` can participate in these phases:

- `build(host)`: construct control tree and static structure.
- `bind_runtime(host)`: attach runtime wiring such as subscriptions, action handlers, and service hooks.
- `handle_event(host, event)`: consume targeted events.
- `on_update(host)`: per-frame update logic.
- `draw(host, surface, theme)`: custom drawing path when needed.
- `shutdown_runtime(host)`: release subscriptions/resources.

Framework guarantee: all scene features finish `build` before any `bind_runtime` begins. This ensures runtime wiring sees complete structure. Subscriptions should be created in `bind_runtime` and torn down in `shutdown_runtime`.

## 3. Installation and Setup

Install from repository root:

```bash
python -m pip install -e . --no-deps
```

Dependencies:

- `pygame`
- `numpy` (used internally for pixel-buffer operations)

Verify the install:

```bash
python -c "import gui_do; print(gui_do.__version__)"
```

Minimal imports to start a declarative app:

```python
from gui_do import HostApplicationBindingSpec, build_host_application_config, bootstrap_host_application, Feature
```

Two startup paths exist:

- Declarative bootstrap via `HostApplicationBindingSpec` and `build_host_application_config` (recommended here)
- Manual `GuiApplication` assembly (advanced; see [MANUAL.md](MANUAL.md))

## 4. Your First Feature

Now we build the first PulseBoard feature: a counter panel.

### Step 1. Define the feature class

`Feature` is the standard starting point because it includes the full lifecycle. We begin with an empty `build` method.

```python
from gui_do import Feature

class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")

    def build(self, host) -> None:
        pass
```

### Step 2. Add a control

Controls are layout nodes inside a feature region, not independent windows. `host.screen_rect` gives the available canvas dimensions.

```python
from pygame import Rect
from gui_do import LabelControl, PanelControl

class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self.root_panel = None
        self.counter_label = None

    def build(self, host) -> None:
        self.root_panel = host.app.add(
            PanelControl("main_root", Rect(0, 0, host.screen_rect.width, host.screen_rect.height)),
            scene_name="main",
        )
        self.counter_label = self.root_panel.add(
            LabelControl("counter_label", Rect(24, 24, 360, 36), "Count: 0")
        )
```

### Step 3. Declare the config

`HostApplicationBindingSpec` describes app-level structure. `SceneBundleBindingSpec` gives scene setup defaults. `FeatureSpec` connects a host attribute to a feature factory.

```python
from gui_do import FeatureSpec, HostApplicationBindingSpec, SceneBundleBindingSpec, build_host_application_config

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1100, 700),
        window_title="PulseBoard",
        fonts={"default": "arial"},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(scene_name="main", make_initial=True),
        ),
        feature_entries=(
            FeatureSpec("counter_feature", CounterFeature),
        ),
    )
)
```

### Step 4. Bootstrap and run

`bootstrap_host_application(host, config)` creates display, app, scenes, features, actions, and runtime wiring from the config. `run_entrypoint` starts the frame loop.

```python
from gui_do import bootstrap_host_application

class PulseBoardHost:
    pass

host = PulseBoardHost()
bootstrap_host_application(host, config)
host.app.run_entrypoint(target_fps=config.target_fps)
```

### Step 5. Full listing so far

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
        super().__init__("counter", scene_name="main")
        self.root_panel = None
        self.counter_label = None

    def build(self, host) -> None:
        self.root_panel = host.app.add(
            PanelControl("main_root", Rect(0, 0, host.screen_rect.width, host.screen_rect.height)),
            scene_name="main",
        )
        self.counter_label = self.root_panel.add(
            LabelControl("counter_label", Rect(24, 24, 360, 36), "Count: 0")
        )


config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1100, 700),
        window_title="PulseBoard",
        fonts={"default": "arial"},
        initial_scene_name="main",
        scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
        feature_entries=(FeatureSpec("counter_feature", CounterFeature),),
    )
)


class PulseBoardHost:
    pass


if __name__ == "__main__":
    host = PulseBoardHost()
    bootstrap_host_application(host, config)
    host.app.run_entrypoint(target_fps=config.target_fps)
```

## 5. Reactive State: Making the UI Respond

Now we make the counter interactive and reactive.

### Step 1. Introduce `ObservableValue`

`ObservableValue` stores ordinary data, but assigning `.value` notifies subscribers.

```python
from gui_do import ObservableValue

class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self.count_value = ObservableValue(0)
```

### Step 2. Add a button

The button callback mutates the observable.

```python
from gui_do import ButtonControl

self.increment_button = self.root_panel.add(
    ButtonControl(
        "increment_button",
        Rect(24, 72, 220, 36),
        "Increment",
        on_click=lambda: setattr(self.count_value, "value", self.count_value.value + 1),
    )
)
```

### Step 3. Wire observable to label in `bind_runtime`

`bind_runtime` is where feature runtime wiring belongs. By this point, controls are fully built.

```python
def bind_runtime(self, host) -> None:
    def sync_count(value) -> None:
        self.counter_label.text = f"Count: {value}"

    self.count_subscription = self.count_value.subscribe(sync_count)
    sync_count(self.count_value.value)
```

### Step 4. Unsubscribe in `shutdown_runtime`

Subscriptions hold callable references, so always unsubscribe during teardown.

```python
def shutdown_runtime(self, host) -> None:
    if self.count_subscription is not None:
        self.count_subscription()
        self.count_subscription = None
```

### Step 5. Full listing after reactive wiring

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
        super().__init__("counter", scene_name="main")
        self.root_panel = None
        self.counter_label = None
        self.increment_button = None
        self.count_value = ObservableValue(0)
        self.count_subscription = None

    def build(self, host) -> None:
        self.root_panel = host.app.add(
            PanelControl("main_root", Rect(0, 0, host.screen_rect.width, host.screen_rect.height)),
            scene_name="main",
        )
        self.counter_label = self.root_panel.add(
            LabelControl("counter_label", Rect(24, 24, 360, 36), "Count: 0")
        )
        self.increment_button = self.root_panel.add(
            ButtonControl(
                "increment_button",
                Rect(24, 72, 220, 36),
                "Increment",
                on_click=lambda: setattr(self.count_value, "value", self.count_value.value + 1),
            )
        )

    def bind_runtime(self, host) -> None:
        def sync_count(value) -> None:
            self.counter_label.text = f"Count: {value}"

        self.count_subscription = self.count_value.subscribe(sync_count)
        sync_count(self.count_value.value)

    def shutdown_runtime(self, host) -> None:
        if self.count_subscription is not None:
            self.count_subscription()
            self.count_subscription = None


config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1100, 700),
        window_title="PulseBoard",
        fonts={"default": "arial"},
        initial_scene_name="main",
        scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
        feature_entries=(FeatureSpec("counter_feature", CounterFeature),),
    )
)


class PulseBoardHost:
    pass


if __name__ == "__main__":
    host = PulseBoardHost()
    bootstrap_host_application(host, config)
    host.app.run_entrypoint(target_fps=config.target_fps)
```

## 6. Feature Types

Use feature types by responsibility, not habit.

- `Feature`: Default choice for visual feature logic with lifecycle hooks.
- `DirectFeature`: High-control option when you want explicit lifecycle control without default behavior assumptions.
- `LogicFeature`: Non-visual logic component for background processing and coordination.
- `RoutedFeature`: A `Feature` variant designed for declarative routing via `RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec`.

For deeper type-level behavior and lifecycle semantics, see [MANUAL.md](MANUAL.md#82-feature-lifecycle-and-feature-types).

## 7. A Second Feature and Feature Communication

Now PulseBoard gets a second feature: an activity log panel.

### Step 1. Define the second feature

The log panel has a separate region and responsibility: showing event history.

```python
class ActivityLogFeature(Feature):
    def __init__(self) -> None:
        super().__init__("activity_log", scene_name="main")
        self.root_panel = None
        self.log_label = None
        self.log_lines = []

    def build(self, host) -> None:
        self.root_panel = host.app.add(
            PanelControl("log_root", Rect(400, 0, 700, host.screen_rect.height)),
            scene_name="main",
        )
        self.log_label = self.root_panel.add(
            LabelControl("log_label", Rect(20, 24, 620, 420), "Activity log is empty")
        )
```

### Step 2. Shared state with `ObservableValue`

Both features can read/write one observable through the host.

```python
# in CounterFeature.build
host.shared_count = self.count_value

# in ActivityLogFeature.bind_runtime
self.shared_subscription = host.shared_count.subscribe(
    lambda value: self.log_lines.append(f"Observable count now {value}")
)
```

Use this when the dependency is explicit and simple.

### Step 3. Feature messaging with `FeatureMessage`

Use messaging when features should remain decoupled.

```python
from gui_do import FeatureMessage

class IncrementMessage(FeatureMessage):
    @classmethod
    def create(cls, sender: str, target: str, amount: int):
        return cls(sender=sender, target=target, payload={"event": "increment", "amount": amount})

# publish from CounterFeature
message = IncrementMessage.create(self.name, "activity_log", 1)
self.send_message("activity_log", message.payload)

# consume in ActivityLogFeature.on_update
def on_update(self, host) -> None:
    while self.has_messages():
        message = self.pop_message()
        if message is None:
            continue
        if message.event == "increment":
            amount = int(message.payload.get("amount", 0))
            self.log_lines.append(f"Message: increment by {amount}")
            self.log_label.text = "\n".join(self.log_lines[-8:])
```

### Step 4. Full listing with both features

```python
import pygame
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
    SceneBundleBindingSpec,
    bootstrap_host_application,
    build_host_application_config,
)


class IncrementMessage(FeatureMessage):
    @classmethod
    def create(cls, sender: str, target: str, amount: int):
        return cls(sender=sender, target=target, payload={"event": "increment", "amount": amount})


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self.root_panel = None
        self.counter_label = None
        self.increment_button = None
        self.count_value = ObservableValue(0)
        self.count_subscription = None

    def build(self, host) -> None:
        self.root_panel = host.app.add(
            PanelControl("main_root", Rect(0, 0, 380, host.screen_rect.height)),
            scene_name="main",
        )
        self.counter_label = self.root_panel.add(LabelControl("counter_label", Rect(24, 24, 320, 36), "Count: 0"))

        def increment() -> None:
            self.count_value.value += 1
            message = IncrementMessage.create(self.name, "activity_log", 1)
            self.send_message("activity_log", message.payload)

        self.increment_button = self.root_panel.add(
            ButtonControl("increment_button", Rect(24, 72, 220, 36), "Increment", on_click=increment)
        )
        host.shared_count = self.count_value

    def bind_runtime(self, host) -> None:
        def sync_count(value) -> None:
            self.counter_label.text = f"Count: {value}"

        self.count_subscription = self.count_value.subscribe(sync_count)
        sync_count(self.count_value.value)

    def shutdown_runtime(self, host) -> None:
        if self.count_subscription is not None:
            self.count_subscription()
            self.count_subscription = None


class ActivityLogFeature(Feature):
    def __init__(self) -> None:
        super().__init__("activity_log", scene_name="main")
        self.root_panel = None
        self.log_label = None
        self.log_lines = []
        self.shared_subscription = None

    def build(self, host) -> None:
        self.root_panel = host.app.add(
            PanelControl("log_root", Rect(390, 0, 700, host.screen_rect.height)),
            scene_name="main",
        )
        self.log_label = self.root_panel.add(
            LabelControl("log_label", Rect(20, 24, 640, 420), "Activity log is empty")
        )

    def bind_runtime(self, host) -> None:
        def on_shared_count(value) -> None:
            self.log_lines.append(f"Observable count now {value}")
            self.log_label.text = "\n".join(self.log_lines[-8:])

        self.shared_subscription = host.shared_count.subscribe(on_shared_count)

    def on_update(self, host) -> None:
        while self.has_messages():
            message = self.pop_message()
            if message is None:
                continue
            if message.event == "increment":
                amount = int(message.payload.get("amount", 0))
                self.log_lines.append(f"Message: increment by {amount}")
                self.log_label.text = "\n".join(self.log_lines[-8:])

    def shutdown_runtime(self, host) -> None:
        if self.shared_subscription is not None:
            self.shared_subscription()
            self.shared_subscription = None


config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1100, 700),
        window_title="PulseBoard",
        fonts={"default": "arial"},
        initial_scene_name="main",
        scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
        feature_entries=(
            FeatureSpec("counter_feature", CounterFeature),
            FeatureSpec("log_feature", ActivityLogFeature),
        ),
    )
)


class PulseBoardHost:
    pass


if __name__ == "__main__":
    pygame.init()
    host = PulseBoardHost()
    bootstrap_host_application(host, config)
    host.app.run_entrypoint(target_fps=config.target_fps)
```

## 8. Actions and Keyboard Shortcuts

Now we add keyboard-driven behavior.

### Step 1. Declare `ActionSpec`

`ActionSpec` belongs in `HostApplicationBindingSpec.action_entries` and can attach a key directly.

```python
import pygame
from gui_do import ActionSpec

action_entries = (
    ActionSpec(action_id="exit", label="Exit", kind="exit", key=pygame.K_ESCAPE),
    ActionSpec(action_id="palette_toggle", label="Toggle Palette", kind="palette_toggle", key=pygame.K_F1),
)
```

### Step 2. Plain `Feature` action callback

Earlier docs sometimes describe this as `host.actions.bind(action_id, callback)`. In current runtime code, the concrete app action dispatcher is `host.app.actions`, so plain features should use `register_action`/`unregister_action`.

```python
def bind_runtime(self, host) -> None:
    def reset_handler(event) -> bool:
        self.count_value.value = 0
        return True

    self.reset_action_name = "counter_reset"
    host.app.actions.register_action(self.reset_action_name, reset_handler)
    host.app.actions.bind_key(pygame.K_r, self.reset_action_name, scene="main")
```

```python
def shutdown_runtime(self, host) -> None:
    if self.reset_action_name:
        host.app.actions.unregister_action(self.reset_action_name)
```

### Step 3. `RoutedFeature` shortcut path

For routed features, declare shortcut behavior in `RoutedRuntimeSpec` and let lifecycle helpers manage setup and teardown.

```python
from gui_do import (
    ActionHotkeySpec,
    RoutedFeature,
    RoutedFeatureLifecycleSpec,
    RoutedRuntimeSpec,
    bind_routed_feature_lifecycle,
    shutdown_routed_feature_lifecycle,
)

class ShortcutFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("shortcuts", scene_name="main")
        self.runtime_lifecycle = RoutedFeatureLifecycleSpec(
            runtime_spec_factory=lambda feature, host: RoutedRuntimeSpec(
                scene_name="main",
                action_hotkeys=(
                    ActionHotkeySpec(action_name="log_ping", handler=feature.on_log_ping, key=pygame.K_p, scene_name="main"),
                ),
            ),
            runtime_spec_attr_name="runtime_spec",
            scheduler_attr_name="scheduler",
        )

    def bind_runtime(self, host) -> None:
        bind_routed_feature_lifecycle(self, host, self.runtime_lifecycle)

    def shutdown_runtime(self, host) -> None:
        shutdown_routed_feature_lifecycle(self, host, self.runtime_lifecycle)
```

### Step 4. Shortcut help overlay with `ShortcutOverlaySpec`

Add a discoverable overlay users can toggle from keyboard.

```python
from gui_do import ShortcutOverlaySpec

RoutedRuntimeSpec(
    scene_name="main",
    shortcut_overlays=(
        ShortcutOverlaySpec(
            attr_name="shortcut_help",
            toggle_action_name="toggle_shortcuts",
            toggle_key=pygame.K_F9,
            toggle_scene_name="main",
            manual_shortcut_lines=("R: reset count", "P: add log ping", "F9: toggle help"),
        ),
    ),
)
```

### Step 5. Full listing with keyboard shortcuts

```python
import pygame
from pygame import Rect
from gui_do import (
    ActionSpec,
    ActionHotkeySpec,
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


class IncrementMessage(FeatureMessage):
    @classmethod
    def create(cls, sender: str, target: str, amount: int):
        return cls(sender=sender, target=target, payload={"event": "increment", "amount": amount})


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self.root_panel = None
        self.counter_label = None
        self.increment_button = None
        self.count_value = ObservableValue(0)
        self.count_subscription = None
        self.reset_action_name = "counter_reset"

    def build(self, host) -> None:
        self.root_panel = host.app.add(
            PanelControl("main_root", Rect(0, 0, 380, host.screen_rect.height)),
            scene_name="main",
        )
        self.counter_label = self.root_panel.add(LabelControl("counter_label", Rect(24, 24, 320, 36), "Count: 0"))

        def increment() -> None:
            self.count_value.value += 1
            message = IncrementMessage.create(self.name, "activity_log", 1)
            self.send_message("activity_log", message.payload)

        self.increment_button = self.root_panel.add(
            ButtonControl("increment_button", Rect(24, 72, 220, 36), "Increment", on_click=increment)
        )
        host.shared_count = self.count_value

    def bind_runtime(self, host) -> None:
        def sync_count(value) -> None:
            self.counter_label.text = f"Count: {value}"

        self.count_subscription = self.count_value.subscribe(sync_count)
        sync_count(self.count_value.value)

        def reset_handler(event) -> bool:
            self.count_value.value = 0
            return True

        host.app.actions.register_action(self.reset_action_name, reset_handler)
        host.app.actions.bind_key(pygame.K_r, self.reset_action_name, scene="main")

    def shutdown_runtime(self, host) -> None:
        if self.count_subscription is not None:
            self.count_subscription()
            self.count_subscription = None
        host.app.actions.unregister_action(self.reset_action_name)


class ActivityLogFeature(Feature):
    def __init__(self) -> None:
        super().__init__("activity_log", scene_name="main")
        self.root_panel = None
        self.log_label = None
        self.log_lines = []
        self.shared_subscription = None

    def build(self, host) -> None:
        self.root_panel = host.app.add(
            PanelControl("log_root", Rect(390, 0, 700, host.screen_rect.height)),
            scene_name="main",
        )
        self.log_label = self.root_panel.add(LabelControl("log_label", Rect(20, 24, 640, 420), "Activity log is empty"))

    def bind_runtime(self, host) -> None:
        def on_shared_count(value) -> None:
            self.log_lines.append(f"Observable count now {value}")
            self.log_label.text = "\n".join(self.log_lines[-8:])

        self.shared_subscription = host.shared_count.subscribe(on_shared_count)

    def on_update(self, host) -> None:
        while self.has_messages():
            message = self.pop_message()
            if message is None:
                continue
            if message.event == "increment":
                amount = int(message.payload.get("amount", 0))
                self.log_lines.append(f"Message: increment by {amount}")
            if message.event == "ping":
                self.log_lines.append("Routed hotkey ping received")
            self.log_label.text = "\n".join(self.log_lines[-8:])

    def shutdown_runtime(self, host) -> None:
        if self.shared_subscription is not None:
            self.shared_subscription()
            self.shared_subscription = None


class ShortcutFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("shortcuts", scene_name="main")
        self.runtime_lifecycle = RoutedFeatureLifecycleSpec(
            runtime_spec_factory=lambda feature, host: RoutedRuntimeSpec(
                scene_name="main",
                action_hotkeys=(
                    ActionHotkeySpec(action_name="log_ping", handler=feature.on_log_ping, key=pygame.K_p, scene_name="main"),
                ),
                shortcut_overlays=(
                    ShortcutOverlaySpec(
                        attr_name="shortcut_help",
                        toggle_action_name="toggle_shortcuts",
                        toggle_key=pygame.K_F9,
                        toggle_scene_name="main",
                        manual_shortcut_lines=("R: reset count", "P: add log ping", "F9: toggle help"),
                    ),
                ),
            ),
            runtime_spec_attr_name="runtime_spec",
            scheduler_attr_name="scheduler",
        )

    def on_log_ping(self, event) -> bool:
        self.send_message("activity_log", {"event": "ping"})
        return True

    def bind_runtime(self, host) -> None:
        bind_routed_feature_lifecycle(self, host, self.runtime_lifecycle)

    def shutdown_runtime(self, host) -> None:
        shutdown_routed_feature_lifecycle(self, host, self.runtime_lifecycle)


config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1100, 700),
        window_title="PulseBoard",
        fonts={"default": "arial"},
        initial_scene_name="main",
        scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
        feature_entries=(
            FeatureSpec("counter_feature", CounterFeature),
            FeatureSpec("log_feature", ActivityLogFeature),
            FeatureSpec("shortcut_feature", ShortcutFeature),
        ),
        action_entries=(
            ActionSpec(action_id="exit", label="Exit", kind="exit", key=pygame.K_ESCAPE),
            ActionSpec(action_id="palette_toggle", label="Toggle Palette", kind="palette_toggle", key=pygame.K_F1),
        ),
    )
)


class PulseBoardHost:
    pass


if __name__ == "__main__":
    pygame.init()
    host = PulseBoardHost()
    bootstrap_host_application(host, config)
    host.app.run_entrypoint(target_fps=config.target_fps)
```

## 9. Spec Reference for Builders

This is a concise builder-facing map. For full depth, use [MANUAL.md](MANUAL.md), especially [8.1](MANUAL.md#81-application-bootstrap-and-host-configuration), [8.2](MANUAL.md#82-feature-lifecycle-and-feature-types), [8.3](MANUAL.md#83-events-actions-input-mapping-and-routing), [8.4](MANUAL.md#84-state-and-observables), and [8.16](MANUAL.md#816-telemetry-introspection-and-operational-hooks).

### `FeatureSpec`

Declares feature class participation in bootstrap and scene behavior through factory registration.

```python
FeatureSpec("counter_feature", CounterFeature)
```

### `FeatureSpec` (attribute slot + factory)

Declares the host attribute slot plus factory used by bootstrap.

```python
FeatureSpec("log_feature", ActivityLogFeature)
```

### `SceneBundleBindingSpec`

Declares a scene bundle with transition/runtime/root/action emission options.

```python
SceneBundleBindingSpec(scene_name="main", make_initial=True)
```

### `ActionSpec` + `ActionHotkeySpec`

`ActionSpec` defines host-level actions; `ActionHotkeySpec` declares routed hotkeys.

```python
ActionSpec(action_id="exit", label="Exit", kind="exit", key=pygame.K_ESCAPE)
ActionHotkeySpec(action_name="log_ping", handler=self.on_log_ping, key=pygame.K_p, scene_name="main")
```

### `ShortcutOverlaySpec`

Configures discoverable keyboard-help overlays.

```python
ShortcutOverlaySpec(attr_name="shortcut_help", toggle_action_name="toggle_shortcuts", toggle_key=pygame.K_F9)
```

### `RoutedRuntimeSpec` + `RoutedFeatureLifecycleSpec`

Defines declarative runtime wiring for `RoutedFeature` and lifecycle attachment/teardown behavior.

```python
RoutedFeatureLifecycleSpec(
    runtime_spec=RoutedRuntimeSpec(scene_name="main", action_hotkeys=(ActionHotkeySpec(...),)),
    runtime_spec_attr_name="runtime_spec",
)
```

### Higher-level runtime faculties

Use `RoutedRuntimeSpec` fields to opt in to advanced faculties:

- Policy/admission: `RuntimePolicySpec`, `RuntimePolicyEngine`
- Effect lifetime: `EffectBindingSpec`, `EffectLifetimeOrchestrator`
- Event pipelines: `EventPipelineSpec`, `EventPipelineRuntime`
- Durable queues: `DurableOperationQueueSpec`, `DurableOperationQueueRuntime`
- Capability contracts: `CapabilityProviderSpec`, `CapabilityContractRuntime`
- Projections: `ProjectionSpec`, `ProjectionRuntime`
- Dependency/workflow/recompute/QoS/health/replay/hot-swap: `FeatureDependencySpec`, `WorkflowSpec`, `RecomputeNodeSpec`, `QoSPolicySpec`, `HealthProbeSpec`, `ReplaySpec`, `ReplacePolicySpec`

See [Main Systems Reference](MANUAL.md#main-systems-reference) and [8.16](MANUAL.md#816-telemetry-introspection-and-operational-hooks).

### `ToastManager`

Show transient notifications through the host app's toasts facility.

```python
host.toasts.show("Saved", severity="info")
```

See [MANUAL overlays chapter](MANUAL.md#88-overlays-dialogs-notifications-and-command-surfaces) for options.

## 10. Complete Project Listing

```python
import pygame
from pygame import Rect
from gui_do import (
    ActionSpec,
    ActionHotkeySpec,
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


# Typed message helper keeps payload shape consistent between sender and receiver.
class IncrementMessage(FeatureMessage):
    @classmethod
    def create(cls, sender: str, target: str, amount: int):
        return cls(sender=sender, target=target, payload={"event": "increment", "amount": amount})


# Counter feature owns reactive count state and user-triggered increment/reset behavior.
class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self.root_panel = None
        self.counter_label = None
        self.increment_button = None
        self.count_value = ObservableValue(0)
        self.count_subscription = None
        self.reset_action_name = "counter_reset"

    def build(self, host) -> None:
        self.root_panel = host.app.add(
            PanelControl("counter_root", Rect(0, 0, 380, host.screen_rect.height)),
            scene_name="main",
        )
        self.counter_label = self.root_panel.add(
            LabelControl("counter_label", Rect(24, 24, 320, 36), "Count: 0")
        )

        def increment() -> None:
            self.count_value.value += 1
            msg = IncrementMessage.create(self.name, "activity_log", 1)
            self.send_message("activity_log", msg.payload)

        self.increment_button = self.root_panel.add(
            ButtonControl("increment_button", Rect(24, 72, 220, 36), "Increment", on_click=increment)
        )

        host.shared_count = self.count_value

    def bind_runtime(self, host) -> None:
        def sync_count(value) -> None:
            self.counter_label.text = f"Count: {value}"

        self.count_subscription = self.count_value.subscribe(sync_count)
        sync_count(self.count_value.value)

        def reset_handler(event) -> bool:
            self.count_value.value = 0
            self.send_message("activity_log", {"event": "reset"})
            return True

        host.app.actions.register_action(self.reset_action_name, reset_handler)
        host.app.actions.bind_key(pygame.K_r, self.reset_action_name, scene="main")

    def shutdown_runtime(self, host) -> None:
        if self.count_subscription is not None:
            self.count_subscription()
            self.count_subscription = None
        host.app.actions.unregister_action(self.reset_action_name)


# Activity-log feature shows observable changes and inter-feature messages.
class ActivityLogFeature(Feature):
    def __init__(self) -> None:
        super().__init__("activity_log", scene_name="main")
        self.root_panel = None
        self.log_label = None
        self.log_lines = []
        self.shared_subscription = None

    def build(self, host) -> None:
        self.root_panel = host.app.add(
            PanelControl("log_root", Rect(390, 0, 700, host.screen_rect.height)),
            scene_name="main",
        )
        self.log_label = self.root_panel.add(
            LabelControl("log_label", Rect(20, 24, 640, 420), "Activity log is empty")
        )

    def bind_runtime(self, host) -> None:
        def on_shared_count(value) -> None:
            self.log_lines.append(f"Observable count now {value}")
            self.log_label.text = "\n".join(self.log_lines[-10:])

        self.shared_subscription = host.shared_count.subscribe(on_shared_count)

    def on_update(self, host) -> None:
        while self.has_messages():
            message = self.pop_message()
            if message is None:
                continue
            if message.event == "increment":
                amount = int(message.payload.get("amount", 0))
                self.log_lines.append(f"Message: increment by {amount}")
            elif message.event == "reset":
                self.log_lines.append("Message: counter reset")
            elif message.event == "ping":
                self.log_lines.append("Message: routed hotkey ping")
            self.log_label.text = "\n".join(self.log_lines[-10:])

    def shutdown_runtime(self, host) -> None:
        if self.shared_subscription is not None:
            self.shared_subscription()
            self.shared_subscription = None


# Routed feature declares hotkeys and a shortcut-help overlay through runtime specs.
class ShortcutFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("shortcuts", scene_name="main")
        self.runtime_lifecycle = RoutedFeatureLifecycleSpec(
            runtime_spec_factory=lambda feature, host: RoutedRuntimeSpec(
                scene_name="main",
                action_hotkeys=(
                    ActionHotkeySpec(action_name="log_ping", handler=feature.on_log_ping, key=pygame.K_p, scene_name="main"),
                ),
                shortcut_overlays=(
                    ShortcutOverlaySpec(
                        attr_name="shortcut_help",
                        toggle_action_name="toggle_shortcuts",
                        toggle_key=pygame.K_F9,
                        toggle_scene_name="main",
                        manual_shortcut_lines=(
                            "Increment button: click",
                            "R: reset counter",
                            "P: add ping entry",
                            "F9: toggle shortcut help",
                            "Esc: exit",
                        ),
                    ),
                ),
            ),
            runtime_spec_attr_name="runtime_spec",
            scheduler_attr_name="scheduler",
        )

    def on_log_ping(self, event) -> bool:
        self.send_message("activity_log", {"event": "ping"})
        return True

    def bind_runtime(self, host) -> None:
        bind_routed_feature_lifecycle(self, host, self.runtime_lifecycle)

    def shutdown_runtime(self, host) -> None:
        shutdown_routed_feature_lifecycle(self, host, self.runtime_lifecycle)


# Declarative host config wires scenes, features, and global actions.
config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1100, 700),
        window_title="PulseBoard",
        fonts={"default": "arial"},
        initial_scene_name="main",
        scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
        feature_entries=(
            FeatureSpec("counter_feature", CounterFeature),
            FeatureSpec("log_feature", ActivityLogFeature),
            FeatureSpec("shortcut_feature", ShortcutFeature),
        ),
        action_entries=(
            ActionSpec(action_id="exit", label="Exit", kind="exit", key=pygame.K_ESCAPE),
            ActionSpec(action_id="palette_toggle", label="Toggle Palette", kind="palette_toggle", key=pygame.K_F1),
        ),
    )
)


# Host container is an empty object that bootstrap populates with runtime attributes.
class PulseBoardHost:
    pass


# Entrypoint starts pygame and runs the gui_do application loop.
if __name__ == "__main__":
    pygame.init()
    host = PulseBoardHost()
    bootstrap_host_application(host, config)
    host.app.run_entrypoint(target_fps=config.target_fps)
```

## 11. Next Steps

Read [MANUAL.md](MANUAL.md) next, then inspect [demo_features/](demo_features) as living package-level patterns. The most relevant chapters for immediate expansion are:

- [8.1 Application Bootstrap and Host Configuration](MANUAL.md#81-application-bootstrap-and-host-configuration)
- [8.2 Feature Lifecycle and Feature Types](MANUAL.md#82-feature-lifecycle-and-feature-types)
- [8.3 Events, Actions, Input Mapping, and Routing](MANUAL.md#83-events-actions-input-mapping-and-routing)
- [8.4 State and Observables](MANUAL.md#84-state-and-observables)

Then explore overlays, persistence, scene navigation, telemetry, and graphics facilities as you scale your app.

If you want to demystify bootstrap internals, read `data_driven_runtime.py` and `feature_lifecycle.py` directly after this tutorial; they are designed to be readable and map closely to the public API surface.
