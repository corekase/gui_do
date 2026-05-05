# gui_do Tutorial

This tutorial teaches gui_do by building one complete project from zero to a feature-rich result. You will learn the full programming model in context: declarative specs, feature lifecycle sequencing, reactive state, feature communication, routed shortcuts, and clean shutdown.

## 1. Introduction

gui_do is a Python GUI framework built on pygame that treats GUI construction as data-driven runtime composition. You declare scenes, features, and actions with specs, and bootstrap wires systems consistently.

In this tutorial you will build **Counter Workbench**, a two-feature interactive application:
- `CounterFeature` owns the count state and increment interactions.
- `LogFeature` shows activity updates and keyboard-discoverable shortcuts.

By the end, the app will have shared observable state, message-based communication, at least one keyboard action, a reactive UI, and explicit teardown.

Prerequisites: Python, pip, `pygame`, and `numpy`. No GUI framework experience is required.

Use [MANUAL.md](MANUAL.md) as the deep reference while you follow along.

```python
from gui_do import __version__
print("gui_do version", __version__)
```

## 2. Core Concepts

### Declarative specs vs imperative wiring

Imperative wiring forces each feature to know about call order and neighbors. gui_do avoids that by using data specs (`FeatureSpec`, `SceneBundleBindingSpec`, `ActionSpec`) that describe structure; bootstrap performs wiring.

```python
from gui_do import FeatureSpec, SceneBundleBindingSpec

scene_spec = SceneBundleBindingSpec(scene_name="main", make_initial=True)
feature_spec = FeatureSpec(attr_name="counter_feature", factory=lambda: object())
print(scene_spec.scene_name, feature_spec.attr_name)
```

### Reactive state

`ObservableValue` notifies subscribers immediately on mutation. No polling loop is required.

```python
from gui_do import ObservableValue

count_value = ObservableValue(0)
unsubscribe = count_value.subscribe(lambda value: print("count changed", value))
count_value.value = 1
unsubscribe()
```

`ObservableList` and `ObservableDict` provide the same model for collections. `ComputedValue` gives derived state.

### Feature lifecycle

The key hooks are:
- `build`
- `bind_runtime`
- `on_update`
- `handle_event`
- `draw`
- `shutdown_runtime`

The framework guarantee is important: all features in a scene finish `build` before any feature enters `bind_runtime`. This is why cross-feature subscriptions belong in `bind_runtime`, and why cleanup belongs in `shutdown_runtime`.

```python
from gui_do import Feature

class LifecycleExample(Feature):
    def __init__(self) -> None:
        super().__init__("lifecycle_example", scene_name="main")

    def build(self, host) -> None:
        pass

    def bind_runtime(self, host) -> None:
        pass

    def shutdown_runtime(self, host) -> None:
        pass
```

## 3. Installation and Setup

Install from the repository root:

```bash
python -m pip install -e . --no-deps
```

Dependencies: `pygame` and `numpy`.

Verify installation:

```bash
python -c "import gui_do; print(gui_do.__version__)"
```

Minimal imports to start:

```python
from gui_do import (
    Feature,
    FeatureSpec,
    HostApplicationBindingSpec,
    SceneBundleBindingSpec,
    build_host_application_config,
    bootstrap_host_application,
)
```

Startup paths:
- Declarative bootstrap path (recommended and used here).
- Manual `GuiApplication` construction (advanced; see [MANUAL.md](MANUAL.md)).

## 4. Your First Feature

Narrative goal: build the first piece of Counter Workbench.

1. Define the feature class.

```python
from gui_do import Feature

class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")

    def build(self, host) -> None:
        pass
```

2. Add a control.

```python
from pygame import Rect
from gui_do import LabelControl

def build(self, host) -> None:
    self.count_label = host.app.add(
        LabelControl("count_label", Rect(24, 24, 320, 36), "Count: 0"),
        scene_name="main",
    )
```

3. Declare config with scene and feature specs.

```python
from gui_do import (
    FeatureSpec,
    HostApplicationBindingSpec,
    SceneBundleBindingSpec,
    build_host_application_config,
)

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(980, 280),
        window_title="Counter Workbench",
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
        display_size=(980, 280),
        window_title="Counter Workbench",
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

Narrative goal: turn static UI into a reactive UI.

1. Add `ObservableValue`.

```python
from gui_do import ObservableValue

self.count_value = ObservableValue(0)
self.count_subscription = None
```

2. Add a button that updates the observable.

```python
from pygame import Rect
from gui_do import ButtonControl

self.increment_button = host.app.add(
    ButtonControl("increment_button", Rect(24, 72, 160, 36), "Increment", on_click=self.increment_count),
    scene_name="main",
)


def increment_count(self) -> None:
    self.count_value.value += 1
```

3. Subscribe in `bind_runtime`.

```python
def bind_runtime(self, host) -> None:
    self.count_subscription = self.count_value.subscribe(
        lambda value: setattr(self.count_label, "text", f"Count: {value}")
    )
```

4. Unsubscribe in `shutdown_runtime`.

```python
def shutdown_runtime(self, host) -> None:
    if self.count_subscription:
        self.count_subscription()
        self.count_subscription = None
```

5. Updated full listing.

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
            ButtonControl("increment_button", Rect(24, 72, 160, 36), "Increment", on_click=self.increment_count),
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
        display_size=(980, 280),
        window_title="Counter Workbench",
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

Pick feature type by role:
- `Feature`: standard visual feature with full lifecycle.
- `DirectFeature`: direct frame/event hooks when you need explicit control.
- `LogicFeature`: non-visual message-driven logic.
- `RoutedFeature`: topic-based message routing plus routed runtime helpers.

```python
from gui_do import DirectFeature, Feature, LogicFeature, RoutedFeature

class UiFeature(Feature):
    pass

class DirectRenderFeature(DirectFeature):
    pass

class DomainLogicFeature(LogicFeature):
    pass

class RoutedUiFeature(RoutedFeature):
    pass
```

## 7. A Second Feature and Feature Communication

Narrative goal: add the second feature and connect responsibilities cleanly.

1. Define a second feature with a different role and region.

```python
from pygame import Rect
from gui_do import LabelControl, RoutedFeature

class LogFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("log_feature", scene_name="main")

    def build(self, host) -> None:
        self.log_label = host.app.add(
            LabelControl("log_label", Rect(24, 132, 900, 36), "Log: waiting for updates"),
            scene_name="main",
        )
```

2. Shared-state approach with `ObservableValue` on host.

```python
# CounterFeature.build
host.shared_count_value = self.count_value

# LogFeature.bind_runtime
self.shared_subscription = host.shared_count_value.subscribe(
    lambda value: setattr(self.log_label, "text", f"Log: shared value changed to {value}")
)
```

3. Messaging approach with a concrete `FeatureMessage` subclass.

```python
from gui_do import FeatureMessage

class CounterChangedMessage(FeatureMessage):
    pass

# Sender
message = CounterChangedMessage(
    sender=self.name,
    target="log_feature",
    payload={"topic": "counter.changed", "count": self.count_value.value},
)
self.send_message("log_feature", message.payload)

# Receiver in RoutedFeature
def message_handlers(self):
    return {"counter.changed": self.on_counter_changed}
```

4. Updated full listing with both features.

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
        self.count_label = host.app.add(LabelControl("count_label", Rect(24, 24, 320, 36), "Count: 0"), scene_name="main")
        self.increment_button = host.app.add(ButtonControl("increment_button", Rect(24, 72, 160, 36), "Increment", on_click=self.increment_count), scene_name="main")
        host.shared_count_value = self.count_value

    def bind_runtime(self, host) -> None:
        self.count_subscription = self.count_value.subscribe(lambda value: setattr(self.count_label, "text", f"Count: {value}"))

    def shutdown_runtime(self, host) -> None:
        if self.count_subscription:
            self.count_subscription()
            self.count_subscription = None

    def increment_count(self) -> None:
        self.count_value.value += 1
        message = CounterChangedMessage(
            sender=self.name,
            target="log_feature",
            payload={"topic": "counter.changed", "count": self.count_value.value},
        )
        self.send_message("log_feature", message.payload)

class LogFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("log_feature", scene_name="main")
        self.shared_subscription = None

    def build(self, host) -> None:
        self.log_label = host.app.add(LabelControl("log_label", Rect(24, 132, 900, 36), "Log: waiting for updates"), scene_name="main")

    def bind_runtime(self, host) -> None:
        self.shared_subscription = host.shared_count_value.subscribe(
            lambda value: setattr(self.log_label, "text", f"Log: shared value changed to {value}")
        )

    def shutdown_runtime(self, host) -> None:
        if self.shared_subscription:
            self.shared_subscription()
            self.shared_subscription = None

    def message_handlers(self):
        return {"counter.changed": self.on_counter_changed}

    def on_counter_changed(self, host, message) -> None:
        self.log_label.text = f"Log: message value {message.get('count', 0)}"

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(980, 280),
        window_title="Counter Workbench",
        fonts={"default": {"size": 16}},
        initial_scene_name="main",
        scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True, bind_escape_to_exit=True),),
        feature_entries=(
            FeatureSpec(attr_name="counter_feature", factory=CounterFeature),
            FeatureSpec(attr_name="log_feature", factory=LogFeature),
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

Narrative goal: add keyboard-driven behavior that users can discover.

1. Declare `ActionSpec` and `ActionHotkeySpec`.

```python
import pygame
from gui_do import ActionHotkeySpec, ActionSpec, RoutedRuntimeSpec

action_entries = (
    ActionSpec(action_id="quit_app", label="Quit", kind="exit", key=pygame.K_ESCAPE),
)

runtime_spec = RoutedRuntimeSpec(
    scene_name="main",
    action_hotkeys=(
        ActionHotkeySpec(action_name="counter.increment", handler=lambda event: True, key=pygame.K_SPACE, scene_name="main"),
    ),
)
```

2. Plain feature binding pattern using current action API.

```python
import pygame

host.app.actions.register_action("counter.increment.manual", lambda event: (self.increment_count() or True))
host.app.actions.bind_key(pygame.K_i, "counter.increment.manual", scene="main")

host.app.actions.unbind_key(pygame.K_i, "counter.increment.manual", scene="main")
host.app.actions.unregister_action("counter.increment.manual")
```

3. Routed feature lifecycle with declarative hotkeys.

```python
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
            ActionHotkeySpec(action_name="log.clear", handler=self.clear_log, key=pygame.K_c, scene_name="main"),
        ),
    )
)

bind_routed_feature_lifecycle(self, host, self.lifecycle_spec)
shutdown_routed_feature_lifecycle(self, host, self.lifecycle_spec)
```

4. Add a shortcut help overlay.

```python
from gui_do import ShortcutOverlaySpec

shortcut_overlay = ShortcutOverlaySpec(
    attr_name="shortcut_overlay",
    toggle_action_name="shortcut.overlay.toggle",
    toggle_key=pygame.K_F1,
    toggle_scene_name="main",
    manual_shortcut_lines=("Space: Increment", "C: Clear log", "F1: Shortcut help"),
)
```

5. Updated full project listing is in Section 10.

## 9. Spec Reference for Builders

This is a compact bridge to the full reference. See [MANUAL.md](MANUAL.md) for exhaustive detail.

- `FeatureSpec` declares feature class factories and host attributes. See [MANUAL.md §8.2](MANUAL.md#82-feature-lifecycle-and-feature-types).

```python
from gui_do import FeatureSpec
FeatureSpec(attr_name="counter_feature", factory=CounterFeature)
```

- `SceneBundleBindingSpec` declares scene setup, initial selection, and common scene behavior. See [MANUAL.md §8.1](MANUAL.md#81-application-bootstrap-and-host-configuration).

```python
from gui_do import SceneBundleBindingSpec
SceneBundleBindingSpec(scene_name="main", make_initial=True, bind_escape_to_exit=True)
```

- `ActionSpec` and `ActionHotkeySpec` declare host-level and routed hotkey actions. See [MANUAL.md §8.3](MANUAL.md#83-events-actions-input-mapping-and-routing).

```python
import pygame
from gui_do import ActionHotkeySpec, ActionSpec

ActionSpec(action_id="quit_app", label="Quit", kind="exit", key=pygame.K_ESCAPE)
ActionHotkeySpec(action_name="counter.increment", handler=lambda event: True, key=pygame.K_SPACE, scene_name="main")
```

- `ShortcutOverlaySpec` configures shortcut discovery UX. See [MANUAL.md §8.8](MANUAL.md#88-overlays-dialogs-notifications-and-command-surfaces).

```python
import pygame
from gui_do import ShortcutOverlaySpec
ShortcutOverlaySpec(attr_name="shortcut_overlay", toggle_action_name="shortcut.overlay.toggle", toggle_key=pygame.K_F1)
```

- `RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec` package routed wiring declaratively. See [MANUAL.md §8.2](MANUAL.md#82-feature-lifecycle-and-feature-types).

```python
from gui_do import RoutedFeatureLifecycleSpec, RoutedRuntimeSpec
RoutedFeatureLifecycleSpec(runtime_spec=RoutedRuntimeSpec(scene_name="main"))
```

- `ToastManager` usage in features is available through `host.app.toasts.show(...)`. See [MANUAL.md §8.8](MANUAL.md#88-overlays-dialogs-notifications-and-command-surfaces).

```python
from gui_do import ToastSeverity
host.app.toasts.show("Counter incremented", title="Counter", severity=ToastSeverity.SUCCESS)
```

## 10. Complete Project Listing

This complete listing is runnable and includes:
- two features with distinct responsibilities,
- observable state wired to controls,
- keyboard actions via `ActionSpec` and `ActionHotkeySpec`,
- one `RoutedFeature` with `RoutedRuntimeSpec`,
- explicit cleanup in `shutdown_runtime`.

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


# Counter feature owns primary state and user increment interactions.
class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self.count_value = ObservableValue(0)
        self.count_subscription = None

    # Build creates controls for the counter panel.
    def build(self, host) -> None:
        self.count_label = host.app.add(
            LabelControl("count_label", Rect(24, 24, 320, 36), "Count: 0"),
            scene_name="main",
        )
        self.increment_button = host.app.add(
            ButtonControl("increment_button", Rect(24, 72, 160, 36), "Increment", on_click=self.increment_count),
            scene_name="main",
        )
        host.shared_count_value = self.count_value

    # Bind runtime subscribes the label to observable updates.
    def bind_runtime(self, host) -> None:
        self.count_subscription = self.count_value.subscribe(
            lambda value: setattr(self.count_label, "text", f"Count: {value}")
        )

    # Shutdown runtime unsubscribes to avoid stale callbacks.
    def shutdown_runtime(self, host) -> None:
        if self.count_subscription:
            self.count_subscription()
            self.count_subscription = None

    # Increment updates state and sends a typed message payload.
    def increment_count(self) -> None:
        self.count_value.value += 1
        message = CounterChangedMessage(
            sender=self.name,
            target="log_feature",
            payload={"topic": "counter.changed", "count": self.count_value.value},
        )
        self.send_message("log_feature", message.payload)


# Routed log feature handles message topics and routed hotkeys.
class LogFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("log_feature", scene_name="main")
        self.shared_subscription = None
        self.host_ref = None
        self.lifecycle_spec = RoutedFeatureLifecycleSpec(
            runtime_spec=RoutedRuntimeSpec(
                scene_name="main",
                action_hotkeys=(
                    ActionHotkeySpec(action_name="counter.increment", handler=self.on_increment_shortcut, key=pygame.K_SPACE, scene_name="main"),
                    ActionHotkeySpec(action_name="log.clear", handler=self.clear_log, key=pygame.K_c, scene_name="main"),
                ),
                shortcut_overlays=(
                    ShortcutOverlaySpec(
                        attr_name="shortcut_overlay",
                        toggle_action_name="shortcut.overlay.toggle",
                        toggle_key=pygame.K_F1,
                        toggle_scene_name="main",
                        manual_shortcut_lines=("Space: Increment", "C: Clear log", "F1: Shortcut help"),
                    ),
                ),
            )
        )

    # Build creates status labels for user feedback.
    def build(self, host) -> None:
        self.log_label = host.app.add(
            LabelControl("log_label", Rect(24, 132, 920, 36), "Log: waiting for activity"),
            scene_name="main",
        )
        self.help_label = host.app.add(
            LabelControl("help_label", Rect(24, 176, 920, 36), "Shortcuts: Space increment, C clear, F1 help"),
            scene_name="main",
        )

    # Bind runtime wires routed helper setup and shared-state subscription.
    def bind_runtime(self, host) -> None:
        self.host_ref = host
        bind_routed_feature_lifecycle(self, host, self.lifecycle_spec)
        self.shared_subscription = host.shared_count_value.subscribe(self.on_shared_count_change)

    # Shutdown runtime performs routed teardown and unsubscribes shared observer.
    def shutdown_runtime(self, host) -> None:
        shutdown_routed_feature_lifecycle(self, host, self.lifecycle_spec)
        if self.shared_subscription:
            self.shared_subscription()
            self.shared_subscription = None

    # Message routing table maps topics to handlers.
    def message_handlers(self):
        return {"counter.changed": self.on_counter_changed}

    # Shared observable callback keeps log UI synced to state changes.
    def on_shared_count_change(self, value: int) -> None:
        self.log_label.text = f"Log: shared observable value={int(value)}"

    # Routed message callback records explicit cross-feature events.
    def on_counter_changed(self, host, message) -> None:
        self.log_label.text = f"Log: routed message value={int(message.get('count', 0))}"
        host.app.toasts.show("Counter updated", title="Workbench", severity=ToastSeverity.INFO)

    # Routed shortcut triggers primary action through the counter feature.
    def on_increment_shortcut(self, event) -> bool:
        if self.host_ref is not None:
            self.host_ref.counter_feature.increment_count()
        return True

    # Routed shortcut clears log label text.
    def clear_log(self, event) -> bool:
        self.log_label.text = "Log: cleared"
        return True


# Host config declares scenes, features, and host-level actions.
config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(980, 280),
        window_title="Counter Workbench",
        fonts={"default": {"size": 16}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(scene_name="main", make_initial=True, bind_escape_to_exit=True),
        ),
        feature_entries=(
            FeatureSpec(attr_name="counter_feature", factory=CounterFeature),
            FeatureSpec(attr_name="log_feature", factory=LogFeature),
        ),
        action_entries=(
            ActionSpec(action_id="quit_app", label="Quit", kind="exit", key=pygame.K_ESCAPE),
        ),
    )
)


# Host instance receives runtime services and feature attributes at bootstrap.
class Host:
    pass


# Entrypoint initializes pygame, bootstraps config, and runs the app loop.
if __name__ == "__main__":
    pygame.init()
    host = Host()
    bootstrap_host_application(host, config)
    host.app.run_entrypoint(target_fps=60)
```

## 11. Next Steps

Continue with [MANUAL.md](MANUAL.md), then explore `demo_features/` as living, package-root export examples.

Recommended next chapters in MANUAL:
- 8.1 bootstrap
- 8.2 feature lifecycle and feature types
- 8.3 events, actions, input mapping, routing
- 8.4 state and observables

Next systems to explore:
- overlays and command surfaces
- persistence and workspace restore behavior
- scene navigation and transitions
- telemetry and diagnostics
- graphics pipeline integration

Reading `gui_do/features/data_driven_runtime.py` and `gui_do/features/feature_lifecycle.py` after this tutorial is strongly recommended; both files are readable and make bootstrap behavior transparent.
