# gui_do Tutorial

## 1. Introduction

gui_do is a Python GUI framework built on pygame that emphasizes declarative structure and predictable runtime behavior. Instead of hand-wiring every subsystem, you declare scenes, features, and actions as specs, then let bootstrap assemble the app. The result is a model that scales better as projects gain more UI surfaces and interaction paths.

In this tutorial, you will build one complete project: **Counter and Activity Workbench**. It has two features with distinct responsibilities: a counter panel that owns state and primary interactions, and an activity panel that logs updates, reacts to messages, and exposes routed shortcuts. By the end, you will have shared observable state, cross-feature messaging, keyboard actions, reactive UI updates, and clean shutdown behavior.

Prerequisites:
- Python
- pip
- pygame
- numpy
- No prior GUI-framework experience is required

Use [MANUAL.md](MANUAL.md) as the deeper reference while you follow this build.

## 2. Core Concepts

Before code, anchor the mental model.

### Declarative Specs vs Imperative Wiring

Imperative wiring tends to spread setup logic across multiple files and initialization orders. gui_do instead uses declarative specs like FeatureSpec, SceneBundleBindingSpec, and HostApplicationBindingSpec to describe structure. The bootstrap layer reads those specs and performs wiring consistently, which keeps features independent of each other.

### Reactive State

ObservableValue is a mutable value that notifies subscribers immediately when it changes. This means UI can react to state changes directly instead of polling every frame. ObservableList and ObservableDict provide the same pattern for collections, and ComputedValue supports derived values.

Subscribe/unsubscribe pattern:

```python
from gui_do import ObservableValue

count = ObservableValue(0)
unsubscribe = count.subscribe(lambda value: print("new value", value))
count.value = 1
unsubscribe()
```

### Feature Lifecycle

gui_do features are lifecycle-driven. The core hooks used in app features are build, bind_runtime, on_update, handle_event, draw, and shutdown_runtime.

Intent of each hook:
- build: construct controls and static structure.
- bind_runtime: connect subscriptions, actions, and runtime services.
- on_update: do per-frame work that belongs to the feature.
- handle_event: consume/ignore events for feature-specific behavior.
- draw: custom rendering when needed.
- shutdown_runtime: remove subscriptions/bindings and release runtime ties.

Important guarantee: all features in a scene complete build before any feature runs bind_runtime. That lets you safely set up cross-feature subscriptions in bind_runtime and tear them down in shutdown_runtime.

## 3. Installation and Setup

Install from repository root:

```bash
python -m pip install -e . --no-deps
```

Dependencies:
- pygame
- numpy (used internally for pixel-buffer operations)

Verify installation:

```bash
python -c "import gui_do; print(gui_do.__version__)"
```

Minimal imports to begin:

```python
from gui_do import (
    HostApplicationBindingSpec,
    build_host_application_config,
    bootstrap_host_application,
    Feature,
)
```

Startup paths:
- Declarative bootstrap path (recommended, used in this tutorial)
- Manual GuiApplication construction (advanced; see [MANUAL.md](MANUAL.md))

## 4. Your First Feature

Narrative goal: build the first working slice of Counter and Activity Workbench.

1. Define the feature class.

Why: Feature is the standard choice for visual UI units that need lifecycle hooks and state. DirectFeature and RoutedFeature are specialized variants we will cover later.

```python
from gui_do import Feature

class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")

    def build(self, host) -> None:
        pass
```

2. Add a control in build.

Why: build should create the control tree for the feature region. host.screen_rect represents the available application canvas.

```python
from pygame import Rect
from gui_do import LabelControl

def build(self, host) -> None:
    self.count_label = host.app.add(
        LabelControl("count_label", Rect(24, 24, 320, 36), "Count: 0"),
        scene_name="main",
    )
```

3. Declare the host config.

Why: HostApplicationBindingSpec is the declarative root object. SceneBundleBindingSpec declares the scene and baseline behavior, and FeatureSpec declares feature instantiation and host attribute wiring.

```python
from gui_do import (
    FeatureSpec,
    HostApplicationBindingSpec,
    SceneBundleBindingSpec,
    build_host_application_config,
)

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(980, 320),
        window_title="Counter and Activity Workbench",
        fonts={"default": {"size": 16}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(scene_name="main", make_initial=True, bind_escape_to_exit=True),
        ),
        feature_entries=(
            FeatureSpec(attr_name="counter_feature", factory=CounterFeature),
        ),
    )
)
```

4. Bootstrap and run.

Why: bootstrap_host_application materializes the declarative config into a live runtime and mutates host with app/features/services. run_entrypoint starts the frame loop.

```python
import pygame
from gui_do import bootstrap_host_application

class Host:
    pass

pygame.init()
host = Host()
bootstrap_host_application(host, config)
host.app.run_entrypoint(target_fps=60)
```

5. Full listing for this stage.

```python
import pygame
from pygame import Rect
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
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")

    def build(self, host) -> None:
        self.count_label = host.app.add(
            LabelControl("count_label", Rect(24, 24, 320, 36), "Count: 0"),
            scene_name="main",
        )


config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(980, 320),
        window_title="Counter and Activity Workbench",
        fonts={"default": {"size": 16}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(scene_name="main", make_initial=True, bind_escape_to_exit=True),
        ),
        feature_entries=(
            FeatureSpec(attr_name="counter_feature", factory=CounterFeature),
        ),
    )
)


class Host:
    pass


if __name__ == "__main__":
    pygame.init()
    host = Host()
    bootstrap_host_application(host, config)
    host.app.run_entrypoint(target_fps=60)
```

## 5. Reactive State: Making the UI Respond

Narrative goal: make the first feature interactive and reactive.

1. Introduce ObservableValue.

Why: this replaces manual polling for basic state changes.

```python
from gui_do import ObservableValue

self.count_value = ObservableValue(0)
self.count_subscription = None
```

2. Add a button that updates observable state.

Why: we need a user interaction path that mutates model state.

```python
from pygame import Rect
from gui_do import ButtonControl

self.increment_button = host.app.add(
    ButtonControl("increment_button", Rect(24, 72, 180, 36), "Increment", on_click=self.increment_count),
    scene_name="main",
)
```

3. Wire observable to label in bind_runtime.

Why: controls exist after build, and runtime binding belongs in bind_runtime. That keeps setup order deterministic and teardown explicit.

```python
def bind_runtime(self, host) -> None:
    self.count_subscription = self.count_value.subscribe(
        lambda value: setattr(self.count_label, "text", f"Count: {value}")
    )
```

4. Unsubscribe in shutdown_runtime.

Why: subscriptions hold references. Failing to unsubscribe can leak memory and invoke callbacks after feature teardown.

```python
def shutdown_runtime(self, host) -> None:
    if self.count_subscription:
        self.count_subscription()
        self.count_subscription = None
```

5. Full updated listing for this stage.

```python
import pygame
from pygame import Rect
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
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self.count_value = ObservableValue(0)
        self.count_subscription = None

    def build(self, host) -> None:
        self.count_label = host.app.add(
            LabelControl("count_label", Rect(24, 24, 320, 36), "Count: 0"),
            scene_name="main",
        )
        self.increment_button = host.app.add(
            ButtonControl("increment_button", Rect(24, 72, 180, 36), "Increment", on_click=self.increment_count),
            scene_name="main",
        )

    def bind_runtime(self, host) -> None:
        self.count_subscription = self.count_value.subscribe(
            lambda value: setattr(self.count_label, "text", f"Count: {value}")
        )

    def shutdown_runtime(self, host) -> None:
        if self.count_subscription:
            self.count_subscription()
            self.count_subscription = None

    def increment_count(self) -> None:
        self.count_value.value += 1


config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(980, 320),
        window_title="Counter and Activity Workbench",
        fonts={"default": {"size": 16}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(scene_name="main", make_initial=True, bind_escape_to_exit=True),
        ),
        feature_entries=(
            FeatureSpec(attr_name="counter_feature", factory=CounterFeature),
        ),
    )
)


class Host:
    pass


if __name__ == "__main__":
    pygame.init()
    host = Host()
    bootstrap_host_application(host, config)
    host.app.run_entrypoint(target_fps=60)
```

## 6. Feature Types

Use feature type by responsibility:

- Feature: default visual feature type with standard lifecycle hooks. Use this for most UI feature implementations.
- DirectFeature: explicit direct event/update/draw hooks when bypassing control-pipeline behavior is required. Rare in typical app UI.
- LogicFeature: non-visual feature for domain logic, coordination, and background pipelines.
- RoutedFeature: Feature plus topic-based message routing via message_handlers, often paired with RoutedRuntimeSpec and RoutedFeatureLifecycleSpec for declarative runtime wiring.

Project mapping in this tutorial:
- CounterFeature uses Feature.
- ActivityFeature uses RoutedFeature for topic-based message handling and routed shortcut setup.

## 7. A Second Feature and Feature Communication

Narrative goal: add ActivityFeature and connect the two features cleanly.

1. Define the second feature with a separate responsibility and visual region.

```python
from pygame import Rect
from gui_do import LabelControl, RoutedFeature

class ActivityFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("activity_feature", scene_name="main")

    def build(self, host) -> None:
        self.log_label = host.app.add(
            LabelControl("log_label", Rect(24, 132, 900, 36), "Activity: waiting"),
            scene_name="main",
        )
```

2. Shared state via ObservableValue.

Why: direct shared observable references are useful for tightly coupled data flow.

```python
# CounterFeature.build
host.shared_count = self.count_value

# ActivityFeature.bind_runtime
self.shared_subscription = host.shared_count.subscribe(
    lambda value: setattr(self.log_label, "text", f"Activity: shared value changed -> {value}")
)
```

3. Feature messaging via FeatureMessage.

Why: messaging keeps features decoupled when they should not hold direct references.

```python
from gui_do import FeatureMessage

class CounterChangedMessage(FeatureMessage):
    pass

# Sender in CounterFeature.increment_count
message = CounterChangedMessage(
    sender=self.name,
    target="activity_feature",
    payload={"topic": "counter.changed", "count": self.count_value.value},
)
self.send_message("activity_feature", message.payload)

# Receiver in ActivityFeature

def message_handlers(self):
    return {"counter.changed": self.on_counter_changed}
```

4. Full updated listing for this stage.

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
    RoutedFeature,
    SceneBundleBindingSpec,
    bootstrap_host_application,
    build_host_application_config,
)


class CounterChangedMessage(FeatureMessage):
    pass


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self.count_value = ObservableValue(0)
        self.count_subscription = None

    def build(self, host) -> None:
        self.count_label = host.app.add(
            LabelControl("count_label", Rect(24, 24, 320, 36), "Count: 0"),
            scene_name="main",
        )
        self.increment_button = host.app.add(
            ButtonControl("increment_button", Rect(24, 72, 180, 36), "Increment", on_click=self.increment_count),
            scene_name="main",
        )
        host.shared_count = self.count_value

    def bind_runtime(self, host) -> None:
        self.count_subscription = self.count_value.subscribe(
            lambda value: setattr(self.count_label, "text", f"Count: {value}")
        )

    def shutdown_runtime(self, host) -> None:
        if self.count_subscription:
            self.count_subscription()
            self.count_subscription = None

    def increment_count(self) -> None:
        self.count_value.value += 1
        message = CounterChangedMessage(
            sender=self.name,
            target="activity_feature",
            payload={"topic": "counter.changed", "count": self.count_value.value},
        )
        self.send_message("activity_feature", message.payload)


class ActivityFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("activity_feature", scene_name="main")
        self.shared_subscription = None

    def build(self, host) -> None:
        self.log_label = host.app.add(
            LabelControl("log_label", Rect(24, 132, 900, 36), "Activity: waiting"),
            scene_name="main",
        )

    def bind_runtime(self, host) -> None:
        self.shared_subscription = host.shared_count.subscribe(
            lambda value: setattr(self.log_label, "text", f"Activity: shared value changed -> {value}")
        )

    def shutdown_runtime(self, host) -> None:
        if self.shared_subscription:
            self.shared_subscription()
            self.shared_subscription = None

    def message_handlers(self):
        return {"counter.changed": self.on_counter_changed}

    def on_counter_changed(self, host, message) -> None:
        self.log_label.text = f"Activity: message value -> {message.get('count', 0)}"


config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(980, 320),
        window_title="Counter and Activity Workbench",
        fonts={"default": {"size": 16}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(scene_name="main", make_initial=True, bind_escape_to_exit=True),
        ),
        feature_entries=(
            FeatureSpec(attr_name="counter_feature", factory=CounterFeature),
            FeatureSpec(attr_name="activity_feature", factory=ActivityFeature),
        ),
    )
)


class Host:
    pass


if __name__ == "__main__":
    pygame.init()
    host = Host()
    bootstrap_host_application(host, config)
    host.app.run_entrypoint(target_fps=60)
```

## 8. Actions and Keyboard Shortcuts

Narrative goal: add discoverable keyboard-driven behavior.

1. Declare ActionSpec and ActionHotkeySpec.

Why: ActionSpec declares host-level named actions. ActionHotkeySpec declares routed action+key bindings as data.

```python
import pygame
from gui_do import ActionHotkeySpec, ActionSpec, RoutedRuntimeSpec

action_entries = (
    ActionSpec(action_id="quit_app", label="Quit", kind="exit", key=pygame.K_ESCAPE),
)

runtime_spec = RoutedRuntimeSpec(
    scene_name="main",
    action_hotkeys=(
        ActionHotkeySpec(action_name="activity.clear", handler=lambda _event: True, key=pygame.K_c, scene_name="main"),
    ),
)
```

2. Bind a plain Feature action callback in bind_runtime and remove it in shutdown_runtime.

Why: for non-routed features, explicit register/bind and unbind/unregister makes lifetime ownership clear.

```python
import pygame

# CounterFeature.bind_runtime
host.app.actions.register_action("counter.increment.hotkey", lambda _event: (self.increment_count() or True))
host.app.actions.bind_key(pygame.K_i, "counter.increment.hotkey", scene="main")

# CounterFeature.shutdown_runtime
host.app.actions.unbind_key(pygame.K_i, "counter.increment.hotkey", scene="main")
host.app.actions.unregister_action("counter.increment.hotkey")
```

3. RoutedFeature shortcut setup with RoutedRuntimeSpec and RoutedFeatureLifecycleSpec.

Why: routed lifecycle helpers centralize registration and teardown for action hotkeys and related routed runtime services.

```python
import pygame
from gui_do import (
    ActionHotkeySpec,
    RoutedFeatureLifecycleSpec,
    RoutedRuntimeSpec,
    bind_routed_feature_lifecycle,
    shutdown_routed_feature_lifecycle,
)

self.lifecycle_spec = RoutedFeatureLifecycleSpec(
    runtime_spec=RoutedRuntimeSpec(
        scene_name="main",
        action_hotkeys=(
            ActionHotkeySpec(action_name="activity.clear", handler=self.clear_log, key=pygame.K_c, scene_name="main"),
        ),
    )
)

bind_routed_feature_lifecycle(self, host, self.lifecycle_spec)
shutdown_routed_feature_lifecycle(self, host, self.lifecycle_spec)
```

4. Add shortcut-help discoverability with ShortcutOverlaySpec.

Why: users should not need to remember shortcuts from external docs.

```python
import pygame
from gui_do import ShortcutOverlaySpec

shortcut_overlay = ShortcutOverlaySpec(
    attr_name="shortcut_overlay",
    toggle_action_name="shortcut.overlay.toggle",
    toggle_key=pygame.K_F1,
    toggle_scene_name="main",
    manual_shortcut_lines=("I: Increment", "C: Clear activity", "F1: Shortcut help"),
)
```

5. Full updated listing for this stage.

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
    RoutedFeature,
    RoutedFeatureLifecycleSpec,
    RoutedRuntimeSpec,
    SceneBundleBindingSpec,
    ShortcutOverlaySpec,
    ToastSeverity,
    bind_routed_feature_lifecycle,
    bootstrap_host_application,
    build_host_application_config,
    shutdown_routed_feature_lifecycle,
)


class CounterChangedMessage(FeatureMessage):
    pass


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self.count_value = ObservableValue(0)
        self.count_subscription = None

    def build(self, host) -> None:
        self.count_label = host.app.add(
            LabelControl("count_label", Rect(24, 24, 320, 36), "Count: 0"),
            scene_name="main",
        )
        self.increment_button = host.app.add(
            ButtonControl("increment_button", Rect(24, 72, 180, 36), "Increment", on_click=self.increment_count),
            scene_name="main",
        )
        host.shared_count = self.count_value

    def bind_runtime(self, host) -> None:
        self.count_subscription = self.count_value.subscribe(
            lambda value: setattr(self.count_label, "text", f"Count: {value}")
        )
        host.app.actions.register_action("counter.increment.hotkey", lambda _event: (self.increment_count() or True))
        host.app.actions.bind_key(pygame.K_i, "counter.increment.hotkey", scene="main")

    def shutdown_runtime(self, host) -> None:
        host.app.actions.unbind_key(pygame.K_i, "counter.increment.hotkey", scene="main")
        host.app.actions.unregister_action("counter.increment.hotkey")
        if self.count_subscription:
            self.count_subscription()
            self.count_subscription = None

    def increment_count(self) -> None:
        self.count_value.value += 1
        message = CounterChangedMessage(
            sender=self.name,
            target="activity_feature",
            payload={"topic": "counter.changed", "count": self.count_value.value},
        )
        self.send_message("activity_feature", message.payload)


class ActivityFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("activity_feature", scene_name="main")
        self.shared_subscription = None
        self.lifecycle_spec = RoutedFeatureLifecycleSpec(
            runtime_spec=RoutedRuntimeSpec(
                scene_name="main",
                action_hotkeys=(
                    ActionHotkeySpec(action_name="activity.clear", handler=self.clear_log, key=pygame.K_c, scene_name="main"),
                ),
                shortcut_overlays=(
                    ShortcutOverlaySpec(
                        attr_name="shortcut_overlay",
                        toggle_action_name="shortcut.overlay.toggle",
                        toggle_key=pygame.K_F1,
                        toggle_scene_name="main",
                        manual_shortcut_lines=("I: Increment", "C: Clear activity", "F1: Shortcut help"),
                    ),
                ),
            )
        )

    def build(self, host) -> None:
        self.log_label = host.app.add(
            LabelControl("log_label", Rect(24, 132, 900, 36), "Activity: waiting"),
            scene_name="main",
        )

    def bind_runtime(self, host) -> None:
        bind_routed_feature_lifecycle(self, host, self.lifecycle_spec)
        self.shared_subscription = host.shared_count.subscribe(
            lambda value: setattr(self.log_label, "text", f"Activity: shared value changed -> {value}")
        )

    def shutdown_runtime(self, host) -> None:
        shutdown_routed_feature_lifecycle(self, host, self.lifecycle_spec)
        if self.shared_subscription:
            self.shared_subscription()
            self.shared_subscription = None

    def message_handlers(self):
        return {"counter.changed": self.on_counter_changed}

    def on_counter_changed(self, host, message) -> None:
        self.log_label.text = f"Activity: message value -> {message.get('count', 0)}"
        host.app.toasts.show("Counter updated", title="Workbench", severity=ToastSeverity.INFO)

    def clear_log(self, _event) -> bool:
        self.log_label.text = "Activity: cleared"
        return True


config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(980, 320),
        window_title="Counter and Activity Workbench",
        fonts={"default": {"size": 16}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(scene_name="main", make_initial=True, bind_escape_to_exit=True),
        ),
        feature_entries=(
            FeatureSpec(attr_name="counter_feature", factory=CounterFeature),
            FeatureSpec(attr_name="activity_feature", factory=ActivityFeature),
        ),
        action_entries=(
            ActionSpec(action_id="quit_app", label="Quit", kind="exit", key=pygame.K_ESCAPE),
        ),
    )
)


class Host:
    pass


if __name__ == "__main__":
    pygame.init()
    host = Host()
    bootstrap_host_application(host, config)
    host.app.run_entrypoint(target_fps=60)
```

## 9. Spec Reference for Builders

This section is a compact bridge to the full reference. For complete details, read [MANUAL.md](MANUAL.md).

- FeatureSpec declares feature factories and the host attribute names where those instances are stored. See [MANUAL.md](MANUAL.md#82-feature-lifecycle-and-feature-types).

```python
from gui_do import FeatureSpec
FeatureSpec(attr_name="counter_feature", factory=CounterFeature)
```

- SceneBundleBindingSpec declares scene setup, initial-scene choice, and optional escape behavior. See [MANUAL.md](MANUAL.md#81-application-bootstrap-and-host-configuration).

```python
from gui_do import SceneBundleBindingSpec
SceneBundleBindingSpec(scene_name="main", make_initial=True, bind_escape_to_exit=True)
```

- ActionSpec plus ActionHotkeySpec declare named actions and keyboard bindings. See [MANUAL.md](MANUAL.md#83-events-actions-input-mapping-and-routing).

```python
import pygame
from gui_do import ActionHotkeySpec, ActionSpec

ActionSpec(action_id="quit_app", label="Quit", kind="exit", key=pygame.K_ESCAPE)
ActionHotkeySpec(action_name="activity.clear", handler=lambda _event: True, key=pygame.K_c, scene_name="main")
```

- ShortcutOverlaySpec declares the shortcut-help overlay behavior and toggle key. See [MANUAL.md](MANUAL.md#88-overlays-dialogs-notifications-and-command-surfaces).

```python
import pygame
from gui_do import ShortcutOverlaySpec
ShortcutOverlaySpec(attr_name="shortcut_overlay", toggle_action_name="shortcut.overlay.toggle", toggle_key=pygame.K_F1)
```

- RoutedRuntimeSpec plus RoutedFeatureLifecycleSpec declare routed runtime wiring for a RoutedFeature. See [MANUAL.md](MANUAL.md#82-feature-lifecycle-and-feature-types).

```python
from gui_do import RoutedFeatureLifecycleSpec, RoutedRuntimeSpec
RoutedFeatureLifecycleSpec(runtime_spec=RoutedRuntimeSpec(scene_name="main"))
```

- ToastManager is available through host.app.toasts for lightweight user notifications from features. See [MANUAL.md](MANUAL.md#88-overlays-dialogs-notifications-and-command-surfaces).

```python
from gui_do import ToastSeverity
host.app.toasts.show("Saved", title="Workbench", severity=ToastSeverity.SUCCESS)
```

## 10. Complete Project Listing

The full project below is runnable end to end. It includes two distinct features, observable-driven UI, keyboard actions, a routed feature runtime spec, and explicit cleanup in shutdown_runtime.

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
    RoutedFeature,
    RoutedFeatureLifecycleSpec,
    RoutedRuntimeSpec,
    SceneBundleBindingSpec,
    ShortcutOverlaySpec,
    ToastSeverity,
    bind_routed_feature_lifecycle,
    bootstrap_host_application,
    build_host_application_config,
    shutdown_routed_feature_lifecycle,
)


# Define a typed message envelope for counter-change notifications.
class CounterChangedMessage(FeatureMessage):
    pass


# CounterFeature owns primary count state and user increment interactions.
class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self.count_value = ObservableValue(0)
        self.count_subscription = None

    # Build creates controls and exposes shared observable state for other features.
    def build(self, host) -> None:
        self.count_label = host.app.add(
            LabelControl("count_label", Rect(24, 24, 320, 36), "Count: 0"),
            scene_name="main",
        )
        self.increment_button = host.app.add(
            ButtonControl("increment_button", Rect(24, 72, 180, 36), "Increment", on_click=self.increment_count),
            scene_name="main",
        )
        host.shared_count = self.count_value

    # Bind runtime wires reactive updates and a plain-feature key action.
    def bind_runtime(self, host) -> None:
        self.count_subscription = self.count_value.subscribe(
            lambda value: setattr(self.count_label, "text", f"Count: {value}")
        )
        host.app.actions.register_action("counter.increment.hotkey", lambda _event: (self.increment_count() or True))
        host.app.actions.bind_key(pygame.K_i, "counter.increment.hotkey", scene="main")

    # Shutdown runtime removes key bindings and subscriptions to prevent stale callbacks.
    def shutdown_runtime(self, host) -> None:
        host.app.actions.unbind_key(pygame.K_i, "counter.increment.hotkey", scene="main")
        host.app.actions.unregister_action("counter.increment.hotkey")
        if self.count_subscription:
            self.count_subscription()
            self.count_subscription = None

    # Increment updates observable state and sends a routed message to ActivityFeature.
    def increment_count(self) -> None:
        self.count_value.value += 1
        message = CounterChangedMessage(
            sender=self.name,
            target="activity_feature",
            payload={"topic": "counter.changed", "count": self.count_value.value},
        )
        self.send_message("activity_feature", message.payload)


# ActivityFeature consumes shared state, routed messages, and routed hotkeys.
class ActivityFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("activity_feature", scene_name="main")
        self.shared_subscription = None
        self.lifecycle_spec = RoutedFeatureLifecycleSpec(
            runtime_spec=RoutedRuntimeSpec(
                scene_name="main",
                action_hotkeys=(
                    ActionHotkeySpec(action_name="activity.clear", handler=self.clear_log, key=pygame.K_c, scene_name="main"),
                ),
                shortcut_overlays=(
                    ShortcutOverlaySpec(
                        attr_name="shortcut_overlay",
                        toggle_action_name="shortcut.overlay.toggle",
                        toggle_key=pygame.K_F1,
                        toggle_scene_name="main",
                        manual_shortcut_lines=("I: Increment", "C: Clear activity", "F1: Shortcut help"),
                    ),
                ),
            )
        )

    # Build creates the activity readout panel that reflects runtime events.
    def build(self, host) -> None:
        self.log_label = host.app.add(
            LabelControl("log_label", Rect(24, 132, 920, 36), "Activity: waiting"),
            scene_name="main",
        )
        self.hint_label = host.app.add(
            LabelControl("hint_label", Rect(24, 176, 920, 36), "Shortcuts: I increment, C clear, F1 help"),
            scene_name="main",
        )

    # Bind runtime enables routed lifecycle wiring and shared-state subscription.
    def bind_runtime(self, host) -> None:
        bind_routed_feature_lifecycle(self, host, self.lifecycle_spec)
        self.shared_subscription = host.shared_count.subscribe(
            lambda value: setattr(self.log_label, "text", f"Activity: shared value changed -> {value}")
        )

    # Shutdown runtime tears down routed registrations and observable subscription.
    def shutdown_runtime(self, host) -> None:
        shutdown_routed_feature_lifecycle(self, host, self.lifecycle_spec)
        if self.shared_subscription:
            self.shared_subscription()
            self.shared_subscription = None

    # RoutedFeature dispatch table maps message topics to handler methods.
    def message_handlers(self):
        return {"counter.changed": self.on_counter_changed}

    # Message handler updates UI and raises a toast for immediate user feedback.
    def on_counter_changed(self, host, message) -> None:
        self.log_label.text = f"Activity: message value -> {message.get('count', 0)}"
        host.app.toasts.show("Counter updated", title="Workbench", severity=ToastSeverity.INFO)

    # Routed hotkey handler clears activity text and reports event consumption.
    def clear_log(self, _event) -> bool:
        self.log_label.text = "Activity: cleared"
        return True


# Host config declares scene, features, and host-level action specs.
config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(980, 320),
        window_title="Counter and Activity Workbench",
        fonts={"default": {"size": 16}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(scene_name="main", make_initial=True, bind_escape_to_exit=True),
        ),
        feature_entries=(
            FeatureSpec(attr_name="counter_feature", factory=CounterFeature),
            FeatureSpec(attr_name="activity_feature", factory=ActivityFeature),
        ),
        action_entries=(
            ActionSpec(action_id="quit_app", label="Quit", kind="exit", key=pygame.K_ESCAPE),
        ),
    )
)


# Host is a plain object that bootstrap mutates with app and feature attributes.
class Host:
    pass


# Entrypoint initializes pygame, bootstraps config, and starts the frame loop.
if __name__ == "__main__":
    pygame.init()
    host = Host()
    bootstrap_host_application(host, config)
    host.app.run_entrypoint(target_fps=60)
```

## 11. Next Steps

Read [MANUAL.md](MANUAL.md) next for complete system coverage, then browse [demo_features/](demo_features/) as living reference implementations of the folder-per-feature, package-root export pattern.

Most relevant manual chapters after this tutorial:
- [MANUAL.md 8.1](MANUAL.md#81-application-bootstrap-and-host-configuration)
- [MANUAL.md 8.2](MANUAL.md#82-feature-lifecycle-and-feature-types)
- [MANUAL.md 8.3](MANUAL.md#83-events-actions-input-mapping-and-routing)
- [MANUAL.md 8.4](MANUAL.md#84-state-and-observables)

Suggested next systems to explore in your own project:
- overlays and command surfaces
- persistence and workspace restore flows
- scene navigation and transitions
- telemetry and diagnostics
- graphics and audio integration

Reading gui_do/features/data_driven_runtime.py and gui_do/features/feature_lifecycle.py is strongly recommended. Both are readable and make the bootstrap and lifecycle model fully transparent.
