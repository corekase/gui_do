# gui_do Tutorial

## 1. Introduction

gui_do is a Python GUI framework built on pygame that emphasizes declarative app structure, feature lifecycle composition, and reactive state. Instead of hand-wiring every runtime service, you describe scenes, features, and actions as specs and let bootstrap assemble a deterministic runtime. That keeps feature code focused on behavior while the framework handles routing, sequencing, and teardown.

In this tutorial, you will build a real two-feature desktop app called **Counter Desk**. The app has a **Counter feature** (increment/reset and keyboard action) and an **Activity Log feature** (reactive status and message history). By the end, you will have keyboard shortcuts, reactive UI updates, feature-to-feature communication, routed runtime wiring, and clean shutdown.

Prerequisites:
- Python and pip
- pygame
- numpy
- No previous GUI framework experience required

For deeper detail at any point, use [MANUAL.md](MANUAL.md).

## 2. Core Concepts

### Declarative specs vs imperative wiring

Traditional GUI code often grows into long startup sequences where every action, handler, and scene is connected manually. gui_do uses declarative specs so your startup describes **what** exists, and bootstrap decides **how** to wire it.

Why this matters:
- You edit structured data instead of scattered wiring calls.
- Features stay isolated and do not import each other's internals.
- Bootstrap can apply consistent setup/teardown rules across all features.

### Reactive state

`ObservableValue` stores a value and notifies subscribers whenever it changes. That gives you push-based updates, so your UI reflects state transitions immediately.

```python
from gui_do import ObservableValue

count = ObservableValue(0)
unsubscribe = count.subscribe(lambda value: print(f"count changed: {value}"))
count.value = 1
unsubscribe()
```

Use `ObservableList` and `ObservableDict` for collection state. Use `ComputedValue` when you want derived state (for example, `"Even"` vs `"Odd"`) to stay synchronized with source observables.

### Feature lifecycle

gui_do features follow a lifecycle with clear intent:
- `build`: create controls and static structure.
- `bind_runtime`: connect subscriptions, actions, event handlers, and runtime resources.
- `on_update`: per-frame logic.
- `handle_event`: optional direct event handling.
- `draw`: optional custom rendering.
- `shutdown_runtime`: release subscriptions/bindings/resources.

Important guarantee: all features in a scene complete `build` before any `bind_runtime` starts. That means cross-feature references to built controls/state are safe when done in `bind_runtime`.

## 3. Installation and Setup

Install from repository root:

```bash
python -m pip install -e . --no-deps
```

Dependencies:
- pygame
- numpy (used internally for pixel buffer operations)

Verify installation:

```bash
python -c "import gui_do; print(gui_do.__version__)"
```

Minimal imports to begin:

```python
from gui_do import HostApplicationBindingSpec, build_host_application_config, bootstrap_host_application, Feature
```

There are two startup paths:
- Declarative bootstrap (recommended): this tutorial path.
- Manual `GuiApplication` construction: advanced path; see [MANUAL.md](MANUAL.md).

## 4. Your First Feature

We will start with one visible feature so you can see the lifecycle in action before adding inter-feature communication.

### Step 1. Define the feature class

`Feature` is the default choice for most UI modules. It gives lifecycle hooks without forcing low-level plumbing. `DirectFeature` and `RoutedFeature` are specialized variants covered later.

```python
from gui_do import Feature

class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")

    def build(self, host) -> None:
        pass
```

### Step 2. Add a control

Controls live inside the feature's region in the scene graph. They are not separate windows unless you declare window presentation specs.

```python
import pygame
from gui_do import LabelControl, PanelControl

class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")

    def build(self, host) -> None:
        host.root = host.app.add(
            PanelControl("root", host.screen_rect.copy(), draw_background=False),
            scene_name="main",
        )
        self.counter_label = host.root.add(
            LabelControl("counter_label", pygame.Rect(24, 24, 360, 44), "Count: 0")
        )
```

`host.screen_rect` is the available canvas for your top-level scene layout.

### Step 3. Declare the config

`HostApplicationBindingSpec` is your declarative app blueprint. `SceneBundleBindingSpec` defines scene setup and transition metadata. `FeatureSpec` declares which features are instantiated and where references are attached on host.

```python
from gui_do import (
    FeatureSpec,
    HostApplicationBindingSpec,
    SceneBundleBindingSpec,
    build_host_application_config,
)

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1080, 640),
        window_title="Counter Desk",
        fonts={"default": {"file": None, "size": 16}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(scene_name="main", pretty_name="Main", make_initial=True),
        ),
        feature_entries=(
            FeatureSpec("counter_feature", CounterFeature),
        ),
    )
)
```

### Step 4. Bootstrap and run

`bootstrap_host_application` reads the built config, creates runtime systems, registers features, and exposes host attributes. `run_entrypoint` starts the deterministic frame loop.

```python
from gui_do import bootstrap_host_application

class CounterApp:
    def __init__(self) -> None:
        bootstrap_host_application(self, config)

CounterApp().app.run_entrypoint(target_fps=60)
```

### Step 5. Full listing

```python
import pygame

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
        host.root = host.app.add(
            PanelControl("root", host.screen_rect.copy(), draw_background=False),
            scene_name="main",
        )
        self.counter_label = host.root.add(
            LabelControl("counter_label", pygame.Rect(24, 24, 360, 44), "Count: 0")
        )

class CounterApp:
    def __init__(self) -> None:
        config = build_host_application_config(
            HostApplicationBindingSpec(
                display_size=(1080, 640),
                window_title="Counter Desk",
                fonts={"default": {"file": None, "size": 16}},
                initial_scene_name="main",
                scene_bundle_entries=(
                    SceneBundleBindingSpec(scene_name="main", pretty_name="Main", make_initial=True),
                ),
                feature_entries=(
                    FeatureSpec("counter_feature", CounterFeature),
                ),
            )
        )
        bootstrap_host_application(self, config)

if __name__ == "__main__":
    CounterApp().app.run_entrypoint(target_fps=60)
```

## 5. Reactive State: Making the UI Respond

Now we make the label update itself when state changes, which is the core gui_do workflow for UI data flow.

### Step 1. Introduce `ObservableValue`

```python
from gui_do import ObservableValue

class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self.count_value = ObservableValue(0)
        self.count_unsubscribe = None
```

When `count_value.value` changes, subscribers are called immediately.

### Step 2. Add a button

```python
from gui_do import ButtonControl

class CounterFeature(Feature):
    def build(self, host) -> None:
        host.root = host.app.add(PanelControl("root", host.screen_rect.copy(), draw_background=False), scene_name="main")
        self.counter_label = host.root.add(LabelControl("counter_label", pygame.Rect(24, 24, 360, 44), "Count: 0"))
        self.increment_button = host.root.add(
            ButtonControl(
                "increment_button",
                pygame.Rect(24, 86, 220, 44),
                "Increment",
                on_click=self.increment_count,
            )
        )

    def increment_count(self) -> None:
        self.count_value.value += 1
```

### Step 3. Wire the observable to the label in `bind_runtime`

`build` constructs controls, but `bind_runtime` is where you connect live runtime relationships such as subscriptions.

```python
class CounterFeature(Feature):
    def bind_runtime(self, host) -> None:
        self.count_unsubscribe = self.count_value.subscribe(
            lambda value: setattr(self.counter_label, "text", f"Count: {value}")
        )
        self.counter_label.text = f"Count: {self.count_value.value}"
```

### Step 4. Unsubscribe in `shutdown_runtime`

Subscriptions keep references alive. Explicit teardown prevents leaks and stale callbacks.

```python
class CounterFeature(Feature):
    def shutdown_runtime(self, host) -> None:
        if self.count_unsubscribe is not None:
            self.count_unsubscribe()
            self.count_unsubscribe = None
```

### Step 5. Updated full listing

```python
import pygame

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
        self.count_unsubscribe = None

    def build(self, host) -> None:
        host.root = host.app.add(
            PanelControl("root", host.screen_rect.copy(), draw_background=False),
            scene_name="main",
        )
        self.counter_label = host.root.add(
            LabelControl("counter_label", pygame.Rect(24, 24, 360, 44), "Count: 0")
        )
        self.increment_button = host.root.add(
            ButtonControl(
                "increment_button",
                pygame.Rect(24, 86, 220, 44),
                "Increment",
                on_click=self.increment_count,
            )
        )

    def increment_count(self) -> None:
        self.count_value.value += 1

    def bind_runtime(self, host) -> None:
        self.count_unsubscribe = self.count_value.subscribe(
            lambda value: setattr(self.counter_label, "text", f"Count: {value}")
        )
        self.counter_label.text = f"Count: {self.count_value.value}"

    def shutdown_runtime(self, host) -> None:
        if self.count_unsubscribe is not None:
            self.count_unsubscribe()
            self.count_unsubscribe = None

class CounterApp:
    def __init__(self) -> None:
        config = build_host_application_config(
            HostApplicationBindingSpec(
                display_size=(1080, 640),
                window_title="Counter Desk",
                fonts={"default": {"file": None, "size": 16}},
                initial_scene_name="main",
                scene_bundle_entries=(
                    SceneBundleBindingSpec(scene_name="main", pretty_name="Main", make_initial=True),
                ),
                feature_entries=(
                    FeatureSpec("counter_feature", CounterFeature),
                ),
            )
        )
        bootstrap_host_application(self, config)

if __name__ == "__main__":
    CounterApp().app.run_entrypoint(target_fps=60)
```

## 6. Feature Types

Use feature types based on responsibility and routing style:

- `Feature`: default visual feature with all common lifecycle hooks. Use this for most scene UI features.
- `DirectFeature`: low-level variant when you want full manual control over direct hooks without default helper behavior.
- `LogicFeature`: logic-centric feature for background computation, pipelines, and coordination without a control tree.
- `RoutedFeature`: feature with topic-driven message dispatch, ideal for hotkeys, overlays, and declarative routed runtime via `RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec`.

For this tutorial, `CounterFeature` stays a plain `Feature`, and the log panel becomes a `RoutedFeature` so we can demonstrate declarative action/shortcut wiring.

## 7. A Second Feature and Feature Communication

Now we add a second feature with its own visual region and purpose.

### Step 1. Define the second feature

The second feature is responsible for activity reporting: current count, event log, and clear-log shortcuts.

```python
class ActivityLogFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("activity_log", scene_name="main")

    def build(self, host) -> None:
        self.log_panel = host.root.add(
            PanelControl("log_panel", pygame.Rect(420, 24, 620, 560), draw_background=True)
        )
        self.shared_count_label = self.log_panel.add(
            LabelControl("shared_count_label", pygame.Rect(20, 20, 420, 36), "Shared Count: 0")
        )
```

### Step 2. Shared state via `ObservableValue`

Approach A: share one observable through host after build.

```python
class CounterFeature(Feature):
    def build(self, host) -> None:
        host.shared_count = self.count_value

class ActivityLogFeature(RoutedFeature):
    def bind_runtime(self, host) -> None:
        self.shared_unsubscribe = host.shared_count.subscribe(
            lambda value: setattr(self.shared_count_label, "text", f"Shared Count: {value}")
        )
```

Why use this: direct and simple when one feature intentionally owns a shared observable.

### Step 3. Feature messaging with a typed message

Approach B: use `FeatureMessage` payload transport to avoid direct feature references.

```python
from gui_do import FeatureMessage

class CounterChangedMessage(FeatureMessage):
    @classmethod
    def create(cls, sender: str, target: str, count: int) -> "CounterChangedMessage":
        return cls(
            sender=sender,
            target=target,
            payload={"topic": "counter.updated", "count": int(count)},
        )

class CounterFeature(Feature):
    def increment_count(self) -> None:
        self.count_value.value += 1
        message = CounterChangedMessage.create(self.name, "activity_log", self.count_value.value)
        self.send_message("activity_log", message.payload)

class ActivityLogFeature(RoutedFeature):
    def message_handlers(self):
        return {"counter.updated": self.on_counter_updated}

    def on_counter_updated(self, host, message: FeatureMessage) -> None:
        count = int(message.payload.get("count", 0))
        self.log_lines.value = [f"Counter changed to {count}", *self.log_lines.value[:6]]
```

Why use this: better decoupling when features should communicate by contract instead of direct references.

### Step 4. Updated full listing with both features

```python
import pygame

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
    RoutedFeature,
    SceneBundleBindingSpec,
    bootstrap_host_application,
    build_host_application_config,
)

class CounterChangedMessage(FeatureMessage):
    @classmethod
    def create(cls, sender: str, target: str, count: int) -> "CounterChangedMessage":
        return cls(sender=sender, target=target, payload={"topic": "counter.updated", "count": int(count)})

class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self.count_value = ObservableValue(0)
        self.count_unsubscribe = None

    def build(self, host) -> None:
        host.root = host.app.add(PanelControl("root", host.screen_rect.copy(), draw_background=False), scene_name="main")
        host.shared_count = self.count_value
        self.counter_label = host.root.add(LabelControl("counter_label", pygame.Rect(24, 24, 360, 44), "Count: 0"))
        self.increment_button = host.root.add(
            ButtonControl("increment_button", pygame.Rect(24, 86, 220, 44), "Increment", on_click=self.increment_count)
        )

    def increment_count(self) -> None:
        self.count_value.value += 1
        message = CounterChangedMessage.create(self.name, "activity_log", self.count_value.value)
        self.send_message("activity_log", message.payload)

    def bind_runtime(self, host) -> None:
        self.count_unsubscribe = self.count_value.subscribe(
            lambda value: setattr(self.counter_label, "text", f"Count: {value}")
        )
        self.counter_label.text = f"Count: {self.count_value.value}"

    def shutdown_runtime(self, host) -> None:
        if self.count_unsubscribe is not None:
            self.count_unsubscribe()
            self.count_unsubscribe = None

class ActivityLogFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("activity_log", scene_name="main")
        self.log_lines = ObservableList(["Activity log ready"])
        self.shared_unsubscribe = None
        self.log_unsubscribe = None

    def build(self, host) -> None:
        self.log_panel = host.root.add(PanelControl("log_panel", pygame.Rect(420, 24, 620, 560), draw_background=True))
        self.shared_count_label = self.log_panel.add(
            LabelControl("shared_count_label", pygame.Rect(20, 20, 420, 36), "Shared Count: 0")
        )
        self.log_label = self.log_panel.add(
            LabelControl("log_label", pygame.Rect(20, 70, 580, 460), "Activity log ready")
        )

    def message_handlers(self):
        return {"counter.updated": self.on_counter_updated}

    def on_counter_updated(self, host, message: FeatureMessage) -> None:
        count = int(message.payload.get("count", 0))
        self.log_lines.value = [f"Counter changed to {count}", *self.log_lines.value[:6]]

    def bind_runtime(self, host) -> None:
        self.shared_unsubscribe = host.shared_count.subscribe(
            lambda value: setattr(self.shared_count_label, "text", f"Shared Count: {value}")
        )
        self.log_unsubscribe = self.log_lines.subscribe(lambda lines: setattr(self.log_label, "text", "\n".join(lines)))

    def shutdown_runtime(self, host) -> None:
        if self.shared_unsubscribe is not None:
            self.shared_unsubscribe()
            self.shared_unsubscribe = None
        if self.log_unsubscribe is not None:
            self.log_unsubscribe()
            self.log_unsubscribe = None

class CounterDeskApp:
    def __init__(self) -> None:
        config = build_host_application_config(
            HostApplicationBindingSpec(
                display_size=(1080, 640),
                window_title="Counter Desk",
                fonts={"default": {"file": None, "size": 16}},
                initial_scene_name="main",
                scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", pretty_name="Main", make_initial=True),),
                feature_entries=(
                    FeatureSpec("counter_feature", CounterFeature),
                    FeatureSpec("activity_feature", ActivityLogFeature),
                ),
            )
        )
        bootstrap_host_application(self, config)

if __name__ == "__main__":
    CounterDeskApp().app.run_entrypoint(target_fps=60)
```

## 8. Actions and Keyboard Shortcuts

Now we wire keyboard actions in two styles: explicit feature-managed binding and declarative routed binding.

### Step 1. Declare `ActionSpec` and `ActionHotkeySpec`

`ActionSpec` entries live in `HostApplicationBindingSpec`. `ActionHotkeySpec` entries belong to `RoutedRuntimeSpec` for routed features.

```python
import pygame
from gui_do import ActionSpec, ActionHotkeySpec, HostApplicationBindingSpec, RoutedRuntimeSpec

host_binding = HostApplicationBindingSpec(
    display_size=(1080, 640),
    window_title="Counter Desk",
    fonts={"default": {"file": None, "size": 16}},
    initial_scene_name="main",
    action_entries=(
        ActionSpec(action_id="app.exit", label="Exit", kind="exit", key=pygame.K_ESCAPE),
    ),
)

log_runtime_spec = RoutedRuntimeSpec(
    scene_name="main",
    action_hotkeys=(
        ActionHotkeySpec(action_name="log.clear", handler=lambda _event: True, key=pygame.K_l, scene_name="main"),
    ),
)
```

### Step 2. Handle an action in a plain `Feature`

In current gui_do runtime, plain features bind through `host.app.actions.register_action(...)` plus `bind_key(...)`, and clean up with `unbind_key(...)` + `unregister_action(...)` in `shutdown_runtime`.

```python
class CounterFeature(Feature):
    def bind_runtime(self, host) -> None:
        host.app.actions.register_action("counter.increment", lambda _event: (self.increment_count() or True))
        host.app.actions.bind_key(pygame.K_i, "counter.increment", scene="main")

    def shutdown_runtime(self, host) -> None:
        host.app.actions.unbind_key(pygame.K_i, "counter.increment", scene="main")
        host.app.actions.unregister_action("counter.increment")
```

### Step 3. Use `RoutedFeature` lifecycle wiring

`RoutedFeatureLifecycleSpec` plus `bind_routed_feature_lifecycle` and `shutdown_routed_feature_lifecycle` keep routed runtime setup declarative and symmetrical.

```python
from gui_do import (
    RoutedFeatureLifecycleSpec,
    ShortcutOverlaySpec,
    bind_routed_feature_lifecycle,
    shutdown_routed_feature_lifecycle,
)

class ActivityLogFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("activity_log", scene_name="main")
        self.lifecycle_spec = RoutedFeatureLifecycleSpec(
            runtime_spec=RoutedRuntimeSpec(
                scene_name="main",
                action_hotkeys=(
                    ActionHotkeySpec(
                        action_name="log.clear",
                        handler=self.clear_log_action,
                        key=pygame.K_l,
                        scene_name="main",
                    ),
                ),
                shortcut_overlays=(
                    ShortcutOverlaySpec(
                        attr_name="help_overlay",
                        toggle_action_name="help.toggle",
                        toggle_key=pygame.K_F1,
                        toggle_scene_name="main",
                        manual_shortcut_lines=(
                            "I: Increment counter",
                            "L: Clear log",
                            "F1: Toggle shortcut help",
                            "Esc: Exit",
                        ),
                        manual_section_title="Counter Desk",
                        prepend_manual_shortcuts=True,
                    ),
                ),
            )
        )

    def bind_runtime(self, host) -> None:
        bind_routed_feature_lifecycle(self, host, self.lifecycle_spec)

    def shutdown_runtime(self, host) -> None:
        shutdown_routed_feature_lifecycle(self, host, self.lifecycle_spec)
```

### Step 4. Shortcut help overlay

`ShortcutOverlaySpec` turns your action registry and optional manual lines into a discoverable in-app keyboard help overlay with one toggle key.

### Step 5. Updated listing with actions wired

```python
import pygame

from gui_do import (
    ActionSpec,
    ActionHotkeySpec,
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
    bootstrap_host_application,
    build_host_application_config,
    shutdown_routed_feature_lifecycle,
)

class CounterChangedMessage(FeatureMessage):
    @classmethod
    def create(cls, sender: str, target: str, count: int) -> "CounterChangedMessage":
        return cls(sender=sender, target=target, payload={"topic": "counter.updated", "count": int(count)})

class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self.count_value = ObservableValue(0)
        self.count_unsubscribe = None

    def build(self, host) -> None:
        host.root = host.app.add(PanelControl("root", host.screen_rect.copy(), draw_background=False), scene_name="main")
        host.shared_count = self.count_value
        self.counter_label = host.root.add(LabelControl("counter_label", pygame.Rect(24, 24, 360, 44), "Count: 0"))
        self.increment_button = host.root.add(
            ButtonControl("increment_button", pygame.Rect(24, 86, 220, 44), "Increment", on_click=self.increment_count)
        )

    def increment_count(self) -> None:
        self.count_value.value += 1
        message = CounterChangedMessage.create(self.name, "activity_log", self.count_value.value)
        self.send_message("activity_log", message.payload)

    def bind_runtime(self, host) -> None:
        self.count_unsubscribe = self.count_value.subscribe(
            lambda value: setattr(self.counter_label, "text", f"Count: {value}")
        )
        self.counter_label.text = f"Count: {self.count_value.value}"
        host.app.actions.register_action("counter.increment", lambda _event: (self.increment_count() or True))
        host.app.actions.bind_key(pygame.K_i, "counter.increment", scene="main")

    def shutdown_runtime(self, host) -> None:
        if self.count_unsubscribe is not None:
            self.count_unsubscribe()
            self.count_unsubscribe = None
        host.app.actions.unbind_key(pygame.K_i, "counter.increment", scene="main")
        host.app.actions.unregister_action("counter.increment")

class ActivityLogFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("activity_log", scene_name="main")
        self.log_lines = ObservableList(["Activity log ready"])
        self.shared_unsubscribe = None
        self.log_unsubscribe = None
        self.lifecycle_spec = RoutedFeatureLifecycleSpec(
            runtime_spec=RoutedRuntimeSpec(
                scene_name="main",
                action_hotkeys=(
                    ActionHotkeySpec(
                        action_name="log.clear",
                        handler=self.clear_log_action,
                        key=pygame.K_l,
                        scene_name="main",
                    ),
                ),
                shortcut_overlays=(
                    ShortcutOverlaySpec(
                        attr_name="help_overlay",
                        toggle_action_name="help.toggle",
                        toggle_key=pygame.K_F1,
                        toggle_scene_name="main",
                        manual_shortcut_lines=(
                            "I: Increment counter",
                            "L: Clear log",
                            "F1: Toggle shortcut help",
                            "Esc: Exit",
                        ),
                        manual_section_title="Counter Desk",
                        prepend_manual_shortcuts=True,
                    ),
                ),
            )
        )

    def build(self, host) -> None:
        self.log_panel = host.root.add(PanelControl("log_panel", pygame.Rect(420, 24, 620, 560), draw_background=True))
        self.shared_count_label = self.log_panel.add(
            LabelControl("shared_count_label", pygame.Rect(20, 20, 420, 36), "Shared Count: 0")
        )
        self.log_label = self.log_panel.add(
            LabelControl("log_label", pygame.Rect(20, 70, 580, 460), "Activity log ready")
        )

    def message_handlers(self):
        return {"counter.updated": self.on_counter_updated}

    def on_counter_updated(self, host, message: FeatureMessage) -> None:
        count = int(message.payload.get("count", 0))
        self.log_lines.value = [f"Counter changed to {count}", *self.log_lines.value[:6]]

    def clear_log_action(self, _event) -> bool:
        self.log_lines.value = ["Activity log cleared"]
        return True

    def bind_runtime(self, host) -> None:
        bind_routed_feature_lifecycle(self, host, self.lifecycle_spec)
        self.shared_unsubscribe = host.shared_count.subscribe(
            lambda value: setattr(self.shared_count_label, "text", f"Shared Count: {value}")
        )
        self.log_unsubscribe = self.log_lines.subscribe(lambda lines: setattr(self.log_label, "text", "\n".join(lines)))

    def shutdown_runtime(self, host) -> None:
        if self.shared_unsubscribe is not None:
            self.shared_unsubscribe()
            self.shared_unsubscribe = None
        if self.log_unsubscribe is not None:
            self.log_unsubscribe()
            self.log_unsubscribe = None
        shutdown_routed_feature_lifecycle(self, host, self.lifecycle_spec)

class CounterDeskApp:
    def __init__(self) -> None:
        config = build_host_application_config(
            HostApplicationBindingSpec(
                display_size=(1080, 640),
                window_title="Counter Desk",
                fonts={"default": {"file": None, "size": 16}},
                initial_scene_name="main",
                scene_bundle_entries=(
                    SceneBundleBindingSpec(scene_name="main", pretty_name="Main", make_initial=True),
                ),
                action_entries=(
                    ActionSpec(action_id="app.exit", label="Exit", kind="exit", key=pygame.K_ESCAPE),
                ),
                feature_entries=(
                    FeatureSpec("counter_feature", CounterFeature),
                    FeatureSpec("activity_feature", ActivityLogFeature),
                ),
            )
        )
        bootstrap_host_application(self, config)

if __name__ == "__main__":
    CounterDeskApp().app.run_entrypoint(target_fps=60)
```

## 9. Spec Reference for Builders

This section is a compact map of the specs used in this tutorial. For complete option matrices and deeper patterns, see [MANUAL.md](MANUAL.md), especially [8.1](MANUAL.md#81-application-bootstrap-and-host-configuration), [8.2](MANUAL.md#82-feature-lifecycle-and-feature-types), [8.3](MANUAL.md#83-events-actions-input-mapping-and-routing), and [8.4](MANUAL.md#84-state-and-observables).

### `FeatureSpec`

Declares a feature factory and where the instantiated feature is attached on host.

```python
FeatureSpec("counter_feature", CounterFeature)
```

Reference: [MANUAL.md 8.1](MANUAL.md#81-application-bootstrap-and-host-configuration)

### `SceneBundleBindingSpec`

Declares scene-level setup, transitions, and optional scene action/root generation.

```python
SceneBundleBindingSpec(scene_name="main", pretty_name="Main", make_initial=True)
```

Reference: [MANUAL.md 8.1](MANUAL.md#81-application-bootstrap-and-host-configuration)

### `ActionSpec` + `ActionHotkeySpec`

`ActionSpec` declares host-level actions; `ActionHotkeySpec` declares routed action bindings inside routed runtime specs.

```python
ActionSpec(action_id="app.exit", label="Exit", kind="exit", key=pygame.K_ESCAPE)
ActionHotkeySpec(action_name="log.clear", handler=self.clear_log_action, key=pygame.K_l, scene_name="main")
```

Reference: [MANUAL.md 8.3](MANUAL.md#83-events-actions-input-mapping-and-routing)

### `ShortcutOverlaySpec`

Configures an overlay that exposes keyboard shortcuts in-app.

```python
ShortcutOverlaySpec(
    attr_name="help_overlay",
    toggle_action_name="help.toggle",
    toggle_key=pygame.K_F1,
    toggle_scene_name="main",
)
```

Reference: [MANUAL.md 8.8](MANUAL.md#88-overlays-dialogs-notifications-and-command-surfaces)

### `RoutedRuntimeSpec` + `RoutedFeatureLifecycleSpec`

Declarative bundle for routed lifecycle setup and teardown.

```python
RoutedFeatureLifecycleSpec(
    runtime_spec=RoutedRuntimeSpec(
        scene_name="main",
        action_hotkeys=(ActionHotkeySpec(action_name="log.clear", handler=self.clear_log_action),),
    )
)
```

Reference: [MANUAL.md 8.2](MANUAL.md#82-feature-lifecycle-and-feature-types)

### `ToastManager`

Use toast notifications for lightweight status messages from feature logic. In running apps, toast usage is typically through `host.app.toasts.show(...)`.

```python
host.app.toasts.show("Saved successfully")
```

Reference: [MANUAL.md 8.8](MANUAL.md#88-overlays-dialogs-notifications-and-command-surfaces)

## 10. Complete Project Listing

```python
# Counter Desk complete project.
# This file demonstrates declarative bootstrap, two collaborating features,
# reactive state, keyboard actions, routed runtime setup, and clean teardown.

import pygame

from gui_do import (
    ActionSpec,
    ActionHotkeySpec,
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
    bootstrap_host_application,
    build_host_application_config,
    shutdown_routed_feature_lifecycle,
)

# Typed message envelope describing one counter update event.
class CounterChangedMessage(FeatureMessage):
    @classmethod
    def create(cls, sender: str, target: str, count: int) -> "CounterChangedMessage":
        return cls(
            sender=sender,
            target=target,
            payload={"topic": "counter.updated", "count": int(count)},
        )

# Primary visual feature: owns counter state and user-facing increment/reset controls.
class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self.count_value = ObservableValue(0)
        self.count_unsubscribe = None

    # Build creates controls and publishes shared observable for other features.
    def build(self, host) -> None:
        host.root = host.app.add(
            PanelControl("root", host.screen_rect.copy(), draw_background=False),
            scene_name="main",
        )
        host.shared_count = self.count_value

        self.counter_label = host.root.add(
            LabelControl("counter_label", pygame.Rect(24, 24, 360, 44), "Count: 0")
        )
        self.increment_button = host.root.add(
            ButtonControl(
                "increment_button",
                pygame.Rect(24, 86, 220, 44),
                "Increment",
                on_click=self.increment_count,
            )
        )
        self.reset_button = host.root.add(
            ButtonControl(
                "reset_button",
                pygame.Rect(24, 140, 220, 44),
                "Reset",
                on_click=self.reset_count,
            )
        )

    # Increment updates reactive state and emits a typed feature message.
    def increment_count(self) -> None:
        self.count_value.value += 1
        message = CounterChangedMessage.create(self.name, "activity_log", self.count_value.value)
        self.send_message("activity_log", message.payload)

    # Reset follows the same messaging path so downstream features stay consistent.
    def reset_count(self) -> None:
        self.count_value.value = 0
        message = CounterChangedMessage.create(self.name, "activity_log", self.count_value.value)
        self.send_message("activity_log", message.payload)

    # Runtime binding connects subscriptions and keyboard actions.
    def bind_runtime(self, host) -> None:
        self.count_unsubscribe = self.count_value.subscribe(
            lambda value: setattr(self.counter_label, "text", f"Count: {value}")
        )
        self.counter_label.text = f"Count: {self.count_value.value}"

        host.app.actions.register_action("counter.increment", lambda _event: (self.increment_count() or True))
        host.app.actions.bind_key(pygame.K_i, "counter.increment", scene="main")

    # Shutdown detaches all runtime resources owned by this feature.
    def shutdown_runtime(self, host) -> None:
        if self.count_unsubscribe is not None:
            self.count_unsubscribe()
            self.count_unsubscribe = None

        host.app.actions.unbind_key(pygame.K_i, "counter.increment", scene="main")
        host.app.actions.unregister_action("counter.increment")

# Routed feature: owns log display and declarative routed action/overlay bindings.
class ActivityLogFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("activity_log", scene_name="main")
        self.log_lines = ObservableList(["Activity log ready"])
        self.shared_unsubscribe = None
        self.log_unsubscribe = None

        self.lifecycle_spec = RoutedFeatureLifecycleSpec(
            runtime_spec=RoutedRuntimeSpec(
                scene_name="main",
                action_hotkeys=(
                    ActionHotkeySpec(
                        action_name="log.clear",
                        handler=self.clear_log_action,
                        key=pygame.K_l,
                        scene_name="main",
                    ),
                ),
                shortcut_overlays=(
                    ShortcutOverlaySpec(
                        attr_name="help_overlay",
                        toggle_action_name="help.toggle",
                        toggle_key=pygame.K_F1,
                        toggle_scene_name="main",
                        manual_shortcut_lines=(
                            "I: Increment counter",
                            "L: Clear log",
                            "F1: Toggle shortcut help",
                            "Esc: Exit",
                        ),
                        manual_section_title="Counter Desk",
                        prepend_manual_shortcuts=True,
                    ),
                ),
            )
        )

    # Build creates the log panel and labels for shared state plus event history.
    def build(self, host) -> None:
        self.log_panel = host.root.add(
            PanelControl("log_panel", pygame.Rect(420, 24, 620, 560), draw_background=True)
        )
        self.shared_count_label = self.log_panel.add(
            LabelControl("shared_count_label", pygame.Rect(20, 20, 420, 36), "Shared Count: 0")
        )
        self.log_label = self.log_panel.add(
            LabelControl("log_label", pygame.Rect(20, 70, 580, 460), "Activity log ready")
        )

    # Topic routing map for inbound feature messages.
    def message_handlers(self):
        return {"counter.updated": self.on_counter_updated}

    # Routed handler updates log state when counter events arrive.
    def on_counter_updated(self, host, message: FeatureMessage) -> None:
        count = int(message.payload.get("count", 0))
        self.log_lines.value = [f"Counter changed to {count}", *self.log_lines.value[:8]]

    # Routed action handler for keyboard clear command.
    def clear_log_action(self, _event) -> bool:
        self.log_lines.value = ["Activity log cleared"]
        return True

    # Runtime binding wires routed lifecycle resources plus local subscriptions.
    def bind_runtime(self, host) -> None:
        bind_routed_feature_lifecycle(self, host, self.lifecycle_spec)

        self.shared_unsubscribe = host.shared_count.subscribe(
            lambda value: setattr(self.shared_count_label, "text", f"Shared Count: {value}")
        )
        self.log_unsubscribe = self.log_lines.subscribe(
            lambda lines: setattr(self.log_label, "text", "\n".join(lines))
        )

    # Shutdown removes subscriptions and routed runtime resources.
    def shutdown_runtime(self, host) -> None:
        if self.shared_unsubscribe is not None:
            self.shared_unsubscribe()
            self.shared_unsubscribe = None
        if self.log_unsubscribe is not None:
            self.log_unsubscribe()
            self.log_unsubscribe = None

        shutdown_routed_feature_lifecycle(self, host, self.lifecycle_spec)

# Application host: declarative spec assembly plus bootstrap.
class CounterDeskApp:
    def __init__(self) -> None:
        config = build_host_application_config(
            HostApplicationBindingSpec(
                display_size=(1080, 640),
                window_title="Counter Desk",
                fonts={"default": {"file": None, "size": 16}},
                initial_scene_name="main",
                scene_bundle_entries=(
                    SceneBundleBindingSpec(
                        scene_name="main",
                        pretty_name="Main",
                        make_initial=True,
                    ),
                ),
                action_entries=(
                    ActionSpec(
                        action_id="app.exit",
                        label="Exit",
                        kind="exit",
                        key=pygame.K_ESCAPE,
                    ),
                ),
                feature_entries=(
                    FeatureSpec("counter_feature", CounterFeature),
                    FeatureSpec("activity_feature", ActivityLogFeature),
                ),
            )
        )
        bootstrap_host_application(self, config)

# Entrypoint starts the runtime loop with a stable frame budget.
if __name__ == "__main__":
    CounterDeskApp().app.run_entrypoint(target_fps=60)
```

## 11. Next Steps

Next reading path:
- Start with [MANUAL.md](MANUAL.md)
- Continue with [demo_features/](demo_features) as living reference packages

High-value areas to explore next:
- Overlays and command surfaces
- Persistence and workspace restore
- Scene navigation and transitions
- Telemetry and diagnostics
- Graphics and audio composition

Most relevant manual chapters for immediate progress:
- [MANUAL.md 8.1](MANUAL.md#81-application-bootstrap-and-host-configuration)
- [MANUAL.md 8.2](MANUAL.md#82-feature-lifecycle-and-feature-types)
- [MANUAL.md 8.3](MANUAL.md#83-events-actions-input-mapping-and-routing)
- [MANUAL.md 8.4](MANUAL.md#84-state-and-observables)

If you want to demystify bootstrap internals, read `data_driven_runtime.py` and `feature_lifecycle.py` after finishing this tutorial; both are intentionally readable and map directly to what you built.
