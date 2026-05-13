# gui_do Tutorial

## 1. Introduction

gui_do is a Python GUI framework built on pygame for data-driven desktop applications. Instead of hand-wiring runtime systems one by one, you describe application structure with specs and let bootstrap assemble a deterministic host. The result is feature code that focuses on behavior while framework systems handle routing, sequencing, and teardown.

In this tutorial, you will build a complete multi-feature app called **Counter Desk**. It has two primary features: a **Counter feature** that owns the main action flow, and an **Activity Log feature** that records and displays updates. The finished app includes reactive UI updates, keyboard actions, routed runtime wiring, feature communication, and clean shutdown.

Prerequisites:
- Python and pip
- pygame
- numpy
- No prior GUI framework experience required

For deeper reference while you work, keep [MANUAL.md](MANUAL.md) open.

## 2. Core Concepts

### Declarative specs vs imperative wiring

Imperative startup code usually grows into many distributed calls: create scene, register action, attach handler, bind key, build overlays, and so on. gui_do shifts that setup into declarative spec objects that describe what should exist.

Why this matters:
- You change app structure in one place, not across many wiring sites.
- Features do not need direct knowledge of each other's internal modules.
- The bootstrap pipeline applies consistent ordering and teardown rules.

### Reactive state

`ObservableValue` is a value holder that notifies subscribers when it changes. This gives push-based UI updates, which is simpler and less error-prone than polling for changes every frame.

```python
from gui_do import ObservableValue

count = ObservableValue(0)
unsubscribe = count.subscribe(lambda value: print(f"count changed to {value}"))
count.value = 1
unsubscribe()
```

Use `ObservableList` and `ObservableDict` for collections. Use `ComputedValue` when a value should be derived automatically from one or more observables.

### Feature lifecycle

Feature lifecycle phases have distinct intent:
- `build`: create controls and static structure.
- `bind_runtime`: connect subscriptions, actions, and runtime dependencies.
- `on_update`: per-frame logic.
- `handle_event`: direct event handling when needed.
- `draw`: optional custom drawing.
- `shutdown_runtime`: release subscriptions/bindings/resources.

Framework guarantee: all features in a scene complete `build` before any `bind_runtime` runs. This is important because subscriptions and cross-feature references in `bind_runtime` can rely on fully built control trees.

## 3. Installation and Setup

Install from the repository root:

```bash
python -m pip install -e . --no-deps
```

Dependencies:
- pygame
- numpy (used internally for pixel buffer and rendering paths)

Verify install:

```bash
python -c "import gui_do; print(gui_do.__version__)"
```

Minimal imports to start:

```python
from gui_do import HostApplicationBindingSpec, build_host_application_config, bootstrap_host_application, Feature
```

There are two startup paths:
- Declarative bootstrap (recommended, used in this tutorial)
- Manual `GuiApplication` construction (advanced; see [MANUAL.md](MANUAL.md))

## 4. Your First Feature

This section builds the first visible slice of Counter Desk so you can see the lifecycle model before adding reactive behavior and cross-feature communication.

1. **Define the feature class.** `Feature` is the default choice for visual modules because it gives clear lifecycle hooks with minimal boilerplate. `DirectFeature` and `RoutedFeature` are useful variants, but start with `Feature` unless you have a specific routing need.

```python
from gui_do import Feature


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")

    def build(self, host) -> None:
        pass
```

2. **Add a control.** Controls are layout-managed objects inside the feature's scene region. `host.screen_rect` gives you the full scene canvas bounds.

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
            LabelControl("counter_label", pygame.Rect(24, 24, 320, 40), "Count: 0")
        )
```

3. **Declare the config.** `HostApplicationBindingSpec` is the application declaration. `SceneBundleBindingSpec` declares a scene bundle. `FeatureSpec` declares what feature class to construct and attach.

```python
from gui_do import (
    FeatureSpec,
    HostApplicationBindingSpec,
    SceneBundleBindingSpec,
    build_host_application_config,
)


binding = HostApplicationBindingSpec(
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
config = build_host_application_config(binding)
```

4. **Bootstrap and run.** `bootstrap_host_application` reads your config and wires runtime systems. `run_entrypoint` starts the frame loop.

```python
from gui_do import bootstrap_host_application


class CounterDeskApp:
    def __init__(self) -> None:
        bootstrap_host_application(self, config)


CounterDeskApp().app.run_entrypoint(target_fps=60)
```

5. **Show the full listing.** Run this file to verify window creation and baseline feature wiring.

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
            LabelControl("counter_label", pygame.Rect(24, 24, 320, 40), "Count: 0")
        )


class CounterDeskApp:
    def __init__(self) -> None:
        binding = HostApplicationBindingSpec(
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
        config = build_host_application_config(binding)
        bootstrap_host_application(self, config)


if __name__ == "__main__":
    CounterDeskApp().app.run_entrypoint(target_fps=60)
```

## 5. Reactive State: Making the UI Respond

Now we make Counter Desk interactive by connecting state changes to UI updates with subscriptions.

1. **Introduce `ObservableValue`.** It is a plain value container with notifications. Updating `.value` triggers subscribers immediately.

```python
from gui_do import ObservableValue


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self.count_value = ObservableValue(0)
        self.count_unsubscribe = None
```

2. **Add a button.** The button callback mutates observable state. UI updates come from subscriptions, not manual text updates in the callback.

```python
from gui_do import ButtonControl


class CounterFeature(Feature):
    def build(self, host) -> None:
        host.root = host.app.add(
            PanelControl("root", host.screen_rect.copy(), draw_background=False),
            scene_name="main",
        )
        self.counter_label = host.root.add(
            LabelControl("counter_label", pygame.Rect(24, 24, 320, 40), "Count: 0")
        )
        self.increment_button = host.root.add(
            ButtonControl(
                "increment_button",
                pygame.Rect(24, 76, 220, 44),
                "Increment",
                on_click=self.increment_count,
            )
        )

    def increment_count(self) -> None:
        self.count_value.value += 1
```

3. **Wire the observable to the label in `bind_runtime`.** `build` creates controls; `bind_runtime` attaches live behavior to those controls.

```python
class CounterFeature(Feature):
    def bind_runtime(self, host) -> None:
        self.count_unsubscribe = self.count_value.subscribe(
            lambda value: setattr(self.counter_label, "text", f"Count: {value}")
        )
        self.counter_label.text = f"Count: {self.count_value.value}"
```

4. **Unsubscribe in `shutdown_runtime`.** Subscription teardown is required lifecycle hygiene to avoid leaks and late callbacks.

```python
class CounterFeature(Feature):
    def shutdown_runtime(self, host) -> None:
        if self.count_unsubscribe is not None:
            self.count_unsubscribe()
            self.count_unsubscribe = None
```

5. **Run the updated listing.** This version should increment the label reactively when clicking the button.

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
            LabelControl("counter_label", pygame.Rect(24, 24, 320, 40), "Count: 0")
        )
        self.increment_button = host.root.add(
            ButtonControl(
                "increment_button",
                pygame.Rect(24, 76, 220, 44),
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


class CounterDeskApp:
    def __init__(self) -> None:
        binding = HostApplicationBindingSpec(
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
        config = build_host_application_config(binding)
        bootstrap_host_application(self, config)


if __name__ == "__main__":
    CounterDeskApp().app.run_entrypoint(target_fps=60)
```

## 6. Feature Types

Use feature types based on behavior ownership:

- `Feature`: standard visual feature with lifecycle hooks. Use this for most UI logic.
- `DirectFeature`: low-level control where you provide the exact lifecycle methods you need, with fewer defaults.
- `LogicFeature`: non-visual feature for background orchestration, data pipelines, and coordination.
- `RoutedFeature`: visual feature with topic-based message and runtime routing support, ideal for declarative action and shortcut wiring with `RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec`.

Counter Desk keeps the counter as a `Feature` and uses a `RoutedFeature` for the activity log so we can demonstrate declarative keyboard routing.

## 7. A Second Feature and Feature Communication

Now we add a second feature with a distinct responsibility: showing shared status and a message log.

1. **Define the second feature.** This feature owns a separate panel region and log display.

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

2. **Shared state via `ObservableValue`.** You can expose a shared observable on host in one feature and subscribe in another.

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

3. **Feature messaging with `FeatureMessage`.** Use typed messages when you want looser coupling between features.

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
        outbound = CounterChangedMessage.create(self.name, "activity_log", self.count_value.value)
        self.send_message("activity_log", outbound.payload)


class ActivityLogFeature(RoutedFeature):
    def message_handlers(self):
        return {"counter.updated": self.on_counter_updated}

    def on_counter_updated(self, host, message: FeatureMessage) -> None:
        count = int(message.payload.get("count", 0))
        self.log_lines.value = [f"Counter changed to {count}", *self.log_lines.value[:6]]
```

4. **Updated full listing.** This version shows both features, shared observable state, and message-driven updates.

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
        return cls(
            sender=sender,
            target=target,
            payload={"topic": "counter.updated", "count": int(count)},
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
        host.shared_count = self.count_value
        self.counter_label = host.root.add(
            LabelControl("counter_label", pygame.Rect(24, 24, 320, 40), "Count: 0")
        )
        self.increment_button = host.root.add(
            ButtonControl(
                "increment_button",
                pygame.Rect(24, 76, 220, 44),
                "Increment",
                on_click=self.increment_count,
            )
        )

    def increment_count(self) -> None:
        self.count_value.value += 1
        outbound = CounterChangedMessage.create(self.name, "activity_log", self.count_value.value)
        self.send_message("activity_log", outbound.payload)

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
        self.log_panel = host.root.add(
            PanelControl("log_panel", pygame.Rect(420, 24, 620, 560), draw_background=True)
        )
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
        self.log_unsubscribe = self.log_lines.subscribe(
            lambda lines: setattr(self.log_label, "text", "\n".join(lines))
        )

    def shutdown_runtime(self, host) -> None:
        if self.shared_unsubscribe is not None:
            self.shared_unsubscribe()
            self.shared_unsubscribe = None
        if self.log_unsubscribe is not None:
            self.log_unsubscribe()
            self.log_unsubscribe = None


class CounterDeskApp:
    def __init__(self) -> None:
        binding = HostApplicationBindingSpec(
            display_size=(1080, 640),
            window_title="Counter Desk",
            fonts={"default": {"file": None, "size": 16}},
            initial_scene_name="main",
            scene_bundle_entries=(
                SceneBundleBindingSpec(scene_name="main", pretty_name="Main", make_initial=True),
            ),
            feature_entries=(
                FeatureSpec("counter_feature", CounterFeature),
                FeatureSpec("activity_feature", ActivityLogFeature),
            ),
        )
        config = build_host_application_config(binding)
        bootstrap_host_application(self, config)


if __name__ == "__main__":
    CounterDeskApp().app.run_entrypoint(target_fps=60)
```

## 8. Actions and Keyboard Shortcuts

This section wires keyboard-driven actions in both plain and routed styles.

1. **Declare an `ActionSpec` and `ActionHotkeySpec`.** Add host-level actions declaratively and route feature-local hotkeys through routed specs.

```python
import pygame
from gui_do import ActionSpec, ActionHotkeySpec, HostApplicationBindingSpec, RoutedRuntimeSpec


binding = HostApplicationBindingSpec(
    display_size=(1080, 640),
    window_title="Counter Desk",
    fonts={"default": {"file": None, "size": 16}},
    initial_scene_name="main",
    action_entries=(
        ActionSpec(action_id="counter.increment", label="Increment Counter", key=pygame.K_i),
        ActionSpec(action_id="app.exit", label="Exit", kind="exit", key=pygame.K_ESCAPE),
    ),
)

routed_runtime = RoutedRuntimeSpec(
    scene_name="main",
    action_hotkeys=(
        ActionHotkeySpec(action_name="log.clear", handler=lambda event: True, key=pygame.K_l, scene_name="main"),
    ),
)
```

2. **Handle an action in a plain `Feature`.** Bind and unbind in lifecycle methods so feature ownership stays explicit.

```python
class CounterFeature(Feature):
    def bind_runtime(self, host) -> None:
        self.action_unbind = host.actions.bind("counter.increment", lambda event: self.increment_count())

    def shutdown_runtime(self, host) -> None:
        if self.action_unbind is not None:
            self.action_unbind()
            self.action_unbind = None
```

3. **Use routed lifecycle wiring in `RoutedFeature`.** `RoutedFeatureLifecycleSpec` plus bind/shutdown helpers keeps registration symmetrical and declarative.

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
        self.routed_lifecycle = RoutedFeatureLifecycleSpec(
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
                        attr_name="shortcut_overlay",
                        toggle_action_name="help.toggle",
                        toggle_key=pygame.K_F1,
                        toggle_scene_name="main",
                        manual_shortcut_lines=(
                            "I: Increment counter",
                            "L: Clear activity log",
                            "F1: Toggle shortcut help",
                            "Esc: Exit app",
                        ),
                        manual_section_title="Counter Desk",
                        prepend_manual_shortcuts=True,
                    ),
                ),
            )
        )

    def bind_runtime(self, host) -> None:
        bind_routed_feature_lifecycle(self, host, self.routed_lifecycle)

    def shutdown_runtime(self, host) -> None:
        shutdown_routed_feature_lifecycle(self, host, self.routed_lifecycle)
```

4. **Shortcut help overlay.** `ShortcutOverlaySpec` creates an in-app discoverability surface so users do not need external shortcut docs.

5. **Updated listing with actions wired.** This version includes host action declaration, plain feature binding, routed hotkeys, and shortcut help overlay support.

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
        return cls(
            sender=sender,
            target=target,
            payload={"topic": "counter.updated", "count": int(count)},
        )


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self.count_value = ObservableValue(0)
        self.count_unsubscribe = None
        self.action_unbind = None

    def build(self, host) -> None:
        host.root = host.app.add(
            PanelControl("root", host.screen_rect.copy(), draw_background=False),
            scene_name="main",
        )
        host.shared_count = self.count_value
        self.counter_label = host.root.add(
            LabelControl("counter_label", pygame.Rect(24, 24, 320, 40), "Count: 0")
        )
        self.increment_button = host.root.add(
            ButtonControl(
                "increment_button",
                pygame.Rect(24, 76, 220, 44),
                "Increment",
                on_click=self.increment_count,
            )
        )

    def increment_count(self) -> None:
        self.count_value.value += 1
        outbound = CounterChangedMessage.create(self.name, "activity_log", self.count_value.value)
        self.send_message("activity_log", outbound.payload)

    def bind_runtime(self, host) -> None:
        self.count_unsubscribe = self.count_value.subscribe(
            lambda value: setattr(self.counter_label, "text", f"Count: {value}")
        )
        self.counter_label.text = f"Count: {self.count_value.value}"
        self.action_unbind = host.actions.bind("counter.increment", lambda event: self.increment_count())

    def shutdown_runtime(self, host) -> None:
        if self.count_unsubscribe is not None:
            self.count_unsubscribe()
            self.count_unsubscribe = None
        if self.action_unbind is not None:
            self.action_unbind()
            self.action_unbind = None


class ActivityLogFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("activity_log", scene_name="main")
        self.log_lines = ObservableList(["Activity log ready"])
        self.shared_unsubscribe = None
        self.log_unsubscribe = None
        self.routed_lifecycle = RoutedFeatureLifecycleSpec(
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
                        attr_name="shortcut_overlay",
                        toggle_action_name="help.toggle",
                        toggle_key=pygame.K_F1,
                        toggle_scene_name="main",
                        manual_shortcut_lines=(
                            "I: Increment counter",
                            "L: Clear activity log",
                            "F1: Toggle shortcut help",
                            "Esc: Exit app",
                        ),
                        manual_section_title="Counter Desk",
                        prepend_manual_shortcuts=True,
                    ),
                ),
            )
        )

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

    def message_handlers(self):
        return {"counter.updated": self.on_counter_updated}

    def on_counter_updated(self, host, message: FeatureMessage) -> None:
        count = int(message.payload.get("count", 0))
        self.log_lines.value = [f"Counter changed to {count}", *self.log_lines.value[:6]]

    def clear_log_action(self, event) -> bool:
        self.log_lines.value = ["Activity log cleared"]
        return True

    def bind_runtime(self, host) -> None:
        bind_routed_feature_lifecycle(self, host, self.routed_lifecycle)
        self.shared_unsubscribe = host.shared_count.subscribe(
            lambda value: setattr(self.shared_count_label, "text", f"Shared Count: {value}")
        )
        self.log_unsubscribe = self.log_lines.subscribe(
            lambda lines: setattr(self.log_label, "text", "\n".join(lines))
        )

    def shutdown_runtime(self, host) -> None:
        if self.shared_unsubscribe is not None:
            self.shared_unsubscribe()
            self.shared_unsubscribe = None
        if self.log_unsubscribe is not None:
            self.log_unsubscribe()
            self.log_unsubscribe = None
        shutdown_routed_feature_lifecycle(self, host, self.routed_lifecycle)


class CounterDeskApp:
    def __init__(self) -> None:
        binding = HostApplicationBindingSpec(
            display_size=(1080, 640),
            window_title="Counter Desk",
            fonts={"default": {"file": None, "size": 16}},
            initial_scene_name="main",
            scene_bundle_entries=(
                SceneBundleBindingSpec(scene_name="main", pretty_name="Main", make_initial=True),
            ),
            action_entries=(
                ActionSpec(action_id="counter.increment", label="Increment Counter", key=pygame.K_i),
                ActionSpec(action_id="app.exit", label="Exit", kind="exit", key=pygame.K_ESCAPE),
            ),
            feature_entries=(
                FeatureSpec("counter_feature", CounterFeature),
                FeatureSpec("activity_feature", ActivityLogFeature),
            ),
        )
        config = build_host_application_config(binding)
        bootstrap_host_application(self, config)


if __name__ == "__main__":
    CounterDeskApp().app.run_entrypoint(target_fps=60)
```

## 9. Spec Reference for Builders

This is a concise builder map. For full option-level reference and integration details, see [MANUAL.md](MANUAL.md), especially [8.1](MANUAL.md#81-application-bootstrap-and-host-configuration), [8.2](MANUAL.md#82-feature-lifecycle-and-feature-types), [8.3](MANUAL.md#83-events-actions-input-mapping-and-routing), and [8.4](MANUAL.md#84-state-and-observables).

### `FeatureSpec`

Declares a feature class for bootstrap construction and host attachment.

```python
FeatureSpec("counter_feature", CounterFeature)
```

Reference: [MANUAL.md 8.1](MANUAL.md#81-application-bootstrap-and-host-configuration)

### `SceneBundleBindingSpec`

Declares a named scene with initial-scene selection and transition behavior.

```python
SceneBundleBindingSpec(scene_name="main", pretty_name="Main", make_initial=True)
```

Reference: [MANUAL.md 8.1](MANUAL.md#81-application-bootstrap-and-host-configuration)

### `ActionSpec` + `ActionHotkeySpec`

`ActionSpec` registers host actions. `ActionHotkeySpec` declares routed hotkey handlers for routed runtime.

```python
ActionSpec(action_id="counter.increment", label="Increment Counter", key=pygame.K_i)
ActionHotkeySpec(action_name="log.clear", handler=self.clear_log_action, key=pygame.K_l, scene_name="main")
```

Reference: [MANUAL.md 8.3](MANUAL.md#83-events-actions-input-mapping-and-routing)

### `ShortcutOverlaySpec`

Configures the keyboard shortcut help overlay so users can discover key bindings in-app.

```python
ShortcutOverlaySpec(
    attr_name="shortcut_overlay",
    toggle_action_name="help.toggle",
    toggle_key=pygame.K_F1,
    toggle_scene_name="main",
)
```

Reference: [MANUAL.md 8.8](MANUAL.md#88-overlays-dialogs-notifications-and-command-surfaces)

### `RoutedRuntimeSpec` + `RoutedFeatureLifecycleSpec`

Bundles routed action, overlay, and event subscription behavior into declarative lifecycle wiring.

```python
RoutedFeatureLifecycleSpec(
    runtime_spec=RoutedRuntimeSpec(
        scene_name="main",
        action_hotkeys=(
            ActionHotkeySpec(action_name="log.clear", handler=self.clear_log_action, key=pygame.K_l, scene_name="main"),
        ),
    )
)
```

Reference: [MANUAL.md 8.2](MANUAL.md#82-feature-lifecycle-and-feature-types)

### `ToastManager`

Use toasts for lightweight user feedback after actions.

```python
host.toasts.show("Activity log cleared")
```

Reference: [MANUAL.md 8.8](MANUAL.md#88-overlays-dialogs-notifications-and-command-surfaces)

## 10. Complete Project Listing

```python
# Counter Desk tutorial application.
# This section imports only public root APIs and wires the app declaratively.

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


# Typed cross-feature message keeps payload shape explicit.
class CounterChangedMessage(FeatureMessage):
    @classmethod
    def create(cls, sender: str, target: str, count: int) -> "CounterChangedMessage":
        return cls(
            sender=sender,
            target=target,
            payload={"topic": "counter.updated", "count": int(count)},
        )


# Counter feature owns primary state and publishes updates.
class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self.count_value = ObservableValue(0)
        self.count_unsubscribe = None
        self.action_unbind = None

    # Build creates controls and exposes shared observable to host.
    def build(self, host) -> None:
        host.root = host.app.add(
            PanelControl("root", host.screen_rect.copy(), draw_background=False),
            scene_name="main",
        )
        host.shared_count = self.count_value

        self.counter_label = host.root.add(
            LabelControl("counter_label", pygame.Rect(24, 24, 320, 40), "Count: 0")
        )
        self.increment_button = host.root.add(
            ButtonControl(
                "increment_button",
                pygame.Rect(24, 76, 220, 44),
                "Increment",
                on_click=self.increment_count,
            )
        )
        self.reset_button = host.root.add(
            ButtonControl(
                "reset_button",
                pygame.Rect(24, 130, 220, 44),
                "Reset",
                on_click=self.reset_count,
            )
        )

    # Action methods mutate state and broadcast typed messages.
    def increment_count(self) -> None:
        self.count_value.value += 1
        outbound = CounterChangedMessage.create(self.name, "activity_log", self.count_value.value)
        self.send_message("activity_log", outbound.payload)

    def reset_count(self) -> None:
        self.count_value.value = 0
        outbound = CounterChangedMessage.create(self.name, "activity_log", self.count_value.value)
        self.send_message("activity_log", outbound.payload)

    # Runtime binding wires subscriptions and action callback.
    def bind_runtime(self, host) -> None:
        self.count_unsubscribe = self.count_value.subscribe(
            lambda value: setattr(self.counter_label, "text", f"Count: {value}")
        )
        self.counter_label.text = f"Count: {self.count_value.value}"
        self.action_unbind = host.actions.bind("counter.increment", lambda event: self.increment_count())

    # Shutdown detaches resources owned by this feature.
    def shutdown_runtime(self, host) -> None:
        if self.count_unsubscribe is not None:
            self.count_unsubscribe()
            self.count_unsubscribe = None
        if self.action_unbind is not None:
            self.action_unbind()
            self.action_unbind = None


# Activity log feature owns routed hotkeys and log rendering.
class ActivityLogFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("activity_log", scene_name="main")
        self.log_lines = ObservableList(["Activity log ready"])
        self.shared_unsubscribe = None
        self.log_unsubscribe = None
        self.routed_lifecycle = RoutedFeatureLifecycleSpec(
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
                        attr_name="shortcut_overlay",
                        toggle_action_name="help.toggle",
                        toggle_key=pygame.K_F1,
                        toggle_scene_name="main",
                        manual_shortcut_lines=(
                            "I: Increment counter",
                            "L: Clear activity log",
                            "F1: Toggle shortcut help",
                            "Esc: Exit app",
                        ),
                        manual_section_title="Counter Desk",
                        prepend_manual_shortcuts=True,
                    ),
                ),
            )
        )

    # Build creates a second panel with shared status and log text.
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

    # Routed message map defines topic-to-handler dispatch.
    def message_handlers(self):
        return {"counter.updated": self.on_counter_updated}

    # Message handler appends new entries to reactive log state.
    def on_counter_updated(self, host, message: FeatureMessage) -> None:
        count = int(message.payload.get("count", 0))
        self.log_lines.value = [f"Counter changed to {count}", *self.log_lines.value[:8]]

    # Routed action handler clears log and shows a toast.
    def clear_log_action(self, event) -> bool:
        self.log_lines.value = ["Activity log cleared"]
        return True

    # Runtime binding wires routed lifecycle plus local subscriptions.
    def bind_runtime(self, host) -> None:
        bind_routed_feature_lifecycle(self, host, self.routed_lifecycle)

        self.shared_unsubscribe = host.shared_count.subscribe(
            lambda value: setattr(self.shared_count_label, "text", f"Shared Count: {value}")
        )
        self.log_unsubscribe = self.log_lines.subscribe(
            lambda lines: setattr(self.log_label, "text", "\n".join(lines))
        )

    # Shutdown cleans up both observable and routed resources.
    def shutdown_runtime(self, host) -> None:
        if self.shared_unsubscribe is not None:
            self.shared_unsubscribe()
            self.shared_unsubscribe = None
        if self.log_unsubscribe is not None:
            self.log_unsubscribe()
            self.log_unsubscribe = None
        shutdown_routed_feature_lifecycle(self, host, self.routed_lifecycle)


# Host assembly remains declarative: specs first, bootstrap second.
class CounterDeskApp:
    def __init__(self) -> None:
        binding = HostApplicationBindingSpec(
            display_size=(1080, 640),
            window_title="Counter Desk",
            fonts={"default": {"file": None, "size": 16}},
            initial_scene_name="main",
            scene_bundle_entries=(
                SceneBundleBindingSpec(scene_name="main", pretty_name="Main", make_initial=True),
            ),
            action_entries=(
                ActionSpec(action_id="counter.increment", label="Increment Counter", key=pygame.K_i),
                ActionSpec(action_id="app.exit", label="Exit", kind="exit", key=pygame.K_ESCAPE),
            ),
            feature_entries=(
                FeatureSpec("counter_feature", CounterFeature),
                FeatureSpec("activity_feature", ActivityLogFeature),
            ),
        )
        config = build_host_application_config(binding)
        bootstrap_host_application(self, config)


# Entry point starts the runtime loop and supports clean shutdown sequencing.
if __name__ == "__main__":
    CounterDeskApp().app.run_entrypoint(target_fps=60)
```

## 11. Next Steps

Continue your learning path in this order:
- [MANUAL.md](MANUAL.md)
- [demo_features/](demo_features) as living reference patterns (one folder per feature, package-root `__init__.py` as public surface)

Explore these systems next:
- overlays and command surfaces
- persistence and workspace restore
- scene navigation and transitions
- telemetry and diagnostics
- graphics and audio features

Most relevant manual sections for your next steps:
- [MANUAL.md 8.1](MANUAL.md#81-application-bootstrap-and-host-configuration)
- [MANUAL.md 8.2](MANUAL.md#82-feature-lifecycle-and-feature-types)
- [MANUAL.md 8.3](MANUAL.md#83-events-actions-input-mapping-and-routing)
- [MANUAL.md 8.4](MANUAL.md#84-state-and-observables)

When you want to fully demystify bootstrap behavior, read `gui_do/features/data_driven_runtime.py` and `gui_do/features/feature_lifecycle.py`. They are readable and map directly to the patterns used in this tutorial.
