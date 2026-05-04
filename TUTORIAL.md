# gui_do Tutorial

## 1. Introduction

gui_do is a Python GUI framework built on pygame that structures desktop applications around declarative specs and feature lifecycles instead of imperative wiring. You describe what your application needs — its scenes, features, actions, windows, and overlays — using plain data objects, and the bootstrap system builds the runtime from those descriptions automatically.

In this tutorial you will build a **Counter Dashboard** — a two-feature interactive application with a live counter display, a reactive activity log, a keyboard shortcut, and a shortcut help overlay. By the end you will have worked through the full gui_do programming model: feature classes, observable state, feature communication, actions, and routed runtime specs.

**Prerequisites.** Python 3.10+, `pip`, and `pygame` installed. No prior GUI framework experience is required. Familiarity with basic Python classes and functions is assumed.

For deeper reference on any topic introduced here, see [MANUAL.md](MANUAL.md). The MANUAL covers all 32 API tiers with full system chapters, usage patterns, integration recipes, and appendices.

---

## 2. Core Concepts

Before writing any code it is worth understanding the three ideas that shape every gui_do application.

### Declarative specs vs imperative wiring

Most GUI frameworks ask you to write setup code: create a scene, add it to a manager, register actions, connect callbacks, wire focus, attach overlays. Every call depends on the order of earlier calls. When you add a new feature you must also update setup code in several places.

gui_do inverts this. You declare your application as a collection of data objects — specs — and pass them to `bootstrap_host_application`. The bootstrap system reads all specs and performs all wiring in the correct order. A feature that declares its scene membership, its actions, and its window toggle in specs never needs to know the bootstrap exists. Adding a second feature is a matter of adding its spec to the collection; nothing else changes.

### Reactive state

An `ObservableValue` is a value with subscribers. When you assign to `.value`, every subscriber callback is called immediately with the new value. There is no polling, no explicit "refresh" call, and no manual diff.

```python
from gui_do import ObservableValue

count = ObservableValue(0)
sub = count.subscribe(lambda v: print(f"count is now {v}"))
count.value = 1   # prints: count is now 1
count.value = 2   # prints: count is now 2
sub.dispose()     # unsubscribe; no more callbacks
```

`ObservableList` and `ObservableDict` provide the same notification contract for ordered and keyed collections. `ComputedValue` derives a read-only observable from one or more source observables without manual recalculation.

### Feature lifecycle

Every feature implements some subset of these six hooks. The framework calls them in this order:

| Hook | When called | Purpose |
|------|------------|---------|
| `build(host)` | Once, before any `bind_runtime` | Construct controls, store references |
| `bind_runtime(host)` | After all `build` calls complete | Subscribe to observables, register callbacks |
| `handle_event(host, event)` | Each frame, for input events | Custom input handling |
| `on_update(host)` | Each frame | Per-frame logic updates |
| `draw(host, surface, theme)` | Each frame | Custom drawing |
| `shutdown_runtime(host)` | On scene or app exit | Dispose subscriptions, release resources |

**The build-before-bind guarantee** is critical: all features in a scene complete `build` before any feature's `bind_runtime` runs. This means when `bind_runtime` executes, every control from every other feature already exists. Cross-feature wiring through the host is safe in `bind_runtime`.

Set up subscriptions in `bind_runtime` and tear them down in `shutdown_runtime`. Subscriptions hold references. Forgetting to dispose them causes callbacks to fire after the feature is gone.

---

## 3. Installation and Setup

From the repository root, install in local editable mode:

```bash
python -m pip install -e . --no-deps
```

This performs no binary compilation. The `--no-deps` flag skips pip's dependency solver for the local package; install `pygame` separately if it is not already present.

Verify the install:

```bash
python -c "import gui_do; print(gui_do.__version__)"
```

The minimal imports for the bootstrap path are:

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

**Two startup paths.** The recommended path for new applications is the declarative bootstrap used throughout this tutorial: assemble `HostApplicationBindingSpec`, call `build_host_application_config`, then call `bootstrap_host_application`. The advanced path — constructing `GuiApplication` and `create_display` manually — gives full control but requires manual wiring of everything the bootstrap handles automatically. See MANUAL.md §8.1 for the advanced path.

---

## 4. Your First Feature

We will build the first piece of the Counter Dashboard: a feature that displays a count label and an increment button.

### Step 1 — Define the feature class

A `Feature` subclass is the unit of composition in gui_do. It owns a region of the screen and a set of controls. `build` is called once, before any feature's `bind_runtime`, and is where you construct the control tree.

We use `Feature` here rather than `DirectFeature`, `LogicFeature`, or `RoutedFeature` because this is a visual feature with controls, state, and user interaction — the standard case. The other types are covered in Section 6.

```python
from gui_do import Feature


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")

    def build(self, host) -> None:
        pass  # controls added next
```

The string `"counter_feature"` is the feature's identity key. `scene_name="main"` declares which scene this feature belongs to. The bootstrap uses this to place the feature in the right scene.

### Step 2 — Add controls

Controls are placed with pixel rects relative to the full window surface (`host.screen_rect` gives its bounds). Here we add a label and a button:

```python
from pygame import Rect

from gui_do import Feature, LabelControl, ButtonControl


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")

    def build(self, host) -> None:
        self._label = host.app.add(
            LabelControl("count_label", Rect(24, 24, 260, 32), "Count: 0"),
            scene_name="main",
        )
        host.app.add(
            ButtonControl("inc_btn", Rect(24, 68, 140, 32), "+1", on_click=self._increment),
            scene_name="main",
        )

    def _increment(self) -> None:
        pass  # wired to observable in the next step
```

`host.app.add(control, scene_name=...)` registers the control with the scene so the framework draws and routes events to it.

### Step 3 — Declare the config

`HostApplicationBindingSpec` is the top-level spec that names everything the bootstrap needs to know. `SceneBundleBindingSpec` declares a named scene. `FeatureSpec` declares a feature class and the host attribute name it will be assigned to.

```python
from gui_do import (
    FeatureSpec,
    HostApplicationBindingSpec,
    SceneBundleBindingSpec,
    build_host_application_config,
)


binding = HostApplicationBindingSpec(
    scene_bundles=(
        SceneBundleBindingSpec(scene_name="main", initial=True),
    ),
    feature_specs=(
        FeatureSpec(attr_name="counter_feature", factory=CounterFeature),
    ),
)
config = build_host_application_config(
    binding,
    display_size=(800, 400),
    window_title="Counter Dashboard",
    target_fps=60,
)
```

`build_host_application_config` merges the binding spec with display parameters into a `HostApplicationConfig` that the bootstrap can consume. You never need to construct `HostApplicationConfig` fields manually.

### Step 4 — Bootstrap and run

`bootstrap_host_application(host, config)` reads all specs, initializes all framework systems, instantiates all features, runs their `build` hooks, and attaches the live `app` object to the host. After this call, `host.app` is the running `GuiApplication`.

`run_entrypoint` starts the frame loop and does not return until the application exits.

```python
import pygame

from gui_do import bootstrap_host_application


class App:
    def __init__(self) -> None:
        bootstrap_host_application(self, config)

    def run(self) -> None:
        self.app.run_entrypoint(target_fps=config.target_fps)


if __name__ == "__main__":
    pygame.init()
    try:
        App().run()
    finally:
        pygame.quit()
```

### Step 5 — Full listing for this step

```python
import pygame
from pygame import Rect

from gui_do import (
    ButtonControl,
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
        self._label = host.app.add(
            LabelControl("count_label", Rect(24, 24, 260, 32), "Count: 0"),
            scene_name="main",
        )
        host.app.add(
            ButtonControl("inc_btn", Rect(24, 68, 140, 32), "+1", on_click=self._increment),
            scene_name="main",
        )

    def _increment(self) -> None:
        pass


binding = HostApplicationBindingSpec(
    scene_bundles=(SceneBundleBindingSpec(scene_name="main", initial=True),),
    feature_specs=(FeatureSpec(attr_name="counter_feature", factory=CounterFeature),),
)
config = build_host_application_config(
    binding,
    display_size=(800, 400),
    window_title="Counter Dashboard",
    target_fps=60,
)


class App:
    def __init__(self) -> None:
        bootstrap_host_application(self, config)

    def run(self) -> None:
        self.app.run_entrypoint(target_fps=config.target_fps)


if __name__ == "__main__":
    pygame.init()
    try:
        App().run()
    finally:
        pygame.quit()
```

Run this and you will see a window with a label and a button. The button does not react yet — that is the next step.

---

## 5. Reactive State: Making the UI Respond

Now we wire `ObservableValue` so that clicking the button updates the label automatically.

### Step 1 — Declare the observable

Add `ObservableValue` to the feature's `__init__`. This is the source of truth for the count; the label and the log will both derive from it.

```python
from gui_do import Feature, ObservableValue


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self.count = ObservableValue(0)  # public so other features can subscribe
```

### Step 2 — Update the observable in the callback

The button's `on_click` should mutate the observable, not the label directly. When `.value` is set, every subscriber will be called.

```python
    def _increment(self) -> None:
        self.count.value = self.count.value + 1
```

### Step 3 — Wire the observable to the label in `bind_runtime`

We subscribe in `bind_runtime` rather than `build` because subscriptions need a live control tree. By the time `bind_runtime` runs, `self._label` is guaranteed to exist (the build-before-bind guarantee).

```python
    def bind_runtime(self, host) -> None:
        def _sync(v: int) -> None:
            self._label.text = f"Count: {v}"

        self._sub = self.count.subscribe(_sync)
        _sync(self.count.value)  # initialize the label to the current value
```

`subscribe` returns a subscription handle. Calling `_sync` immediately after ensures the label shows the right initial text without needing a first click.

### Step 4 — Dispose the subscription in `shutdown_runtime`

Subscriptions hold references. When the scene shuts down, the feature's `shutdown_runtime` is called. If you do not dispose the subscription here, the callback can fire after the control is gone.

```python
    def shutdown_runtime(self, host) -> None:
        self._sub.dispose()
```

### Step 5 — Full listing for this step

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
        self.count = ObservableValue(0)

    def build(self, host) -> None:
        self._label = host.app.add(
            LabelControl("count_label", Rect(24, 24, 260, 32), "Count: 0"),
            scene_name="main",
        )
        host.app.add(
            ButtonControl("inc_btn", Rect(24, 68, 140, 32), "+1", on_click=self._increment),
            scene_name="main",
        )

    def bind_runtime(self, host) -> None:
        def _sync(v: int) -> None:
            self._label.text = f"Count: {v}"

        self._sub = self.count.subscribe(_sync)
        _sync(self.count.value)

    def shutdown_runtime(self, host) -> None:
        self._sub.dispose()

    def _increment(self) -> None:
        self.count.value = self.count.value + 1


binding = HostApplicationBindingSpec(
    scene_bundles=(SceneBundleBindingSpec(scene_name="main", initial=True),),
    feature_specs=(FeatureSpec(attr_name="counter_feature", factory=CounterFeature),),
)
config = build_host_application_config(
    binding,
    display_size=(800, 400),
    window_title="Counter Dashboard",
    target_fps=60,
)


class App:
    def __init__(self) -> None:
        bootstrap_host_application(self, config)

    def run(self) -> None:
        self.app.run_entrypoint(target_fps=config.target_fps)


if __name__ == "__main__":
    pygame.init()
    try:
        App().run()
    finally:
        pygame.quit()
```

Click the button and the label updates immediately. No manual refresh call, no frame-poll. The observable notifies the subscriber; the subscriber updates the label.

---

## 6. Feature Types

gui_do provides four feature base classes. Choose the simplest one that fits the feature's role.

**`Feature`** is the standard choice. It provides all six lifecycle hooks with sensible defaults. Use it when your feature has controls, state, and user interaction — which covers most features in an application.

**`DirectFeature`** provides the same lifecycle hooks but with no default method bodies. Use it when you want a clean slate and intend to override only the specific methods your feature needs. Rarely required; `Feature` defaults do nothing, so the practical difference is minimal.

**`LogicFeature`** has no draw call and no control tree. Use it for background computation, cross-feature coordination, or data pipeline management that does not need a visual presence.

**`RoutedFeature`** extends `Feature` with topic-based message dispatch. Use it when you want to wire hotkeys, shortcut overlays, and event subscriptions declaratively via `RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec`. The routed lifecycle helpers (`bind_routed_feature_lifecycle`, `shutdown_routed_feature_lifecycle`) handle binding and unbinding automatically from a single spec object.

For the Counter Dashboard: `CounterFeature` is a plain `Feature`. The activity log we will add in Section 7 is also a plain `Feature`. In Section 8 we will promote the counter to a `RoutedFeature` to add a keyboard shortcut and a shortcut overlay declaratively.

---

## 7. A Second Feature and Feature Communication

The Counter Dashboard needs an activity log — a second feature that shows a line of text each time the counter increments. We will build it two ways: first by subscribing to the counter's observable directly, then using `FeatureMessage` for looser coupling.

### Step 1 — Define the log feature

The log feature subscribes to `host.counter_feature.count` in `bind_runtime`. This is safe because of the build-before-bind guarantee: by the time `bind_runtime` runs, `counter_feature` is a fully built host attribute.

```python
from pygame import Rect

from gui_do import Feature, LabelControl


class LogFeature(Feature):
    def __init__(self) -> None:
        super().__init__("log_feature", scene_name="main")
        self._entries: list[str] = []

    def build(self, host) -> None:
        self._log_label = host.app.add(
            LabelControl("log_label", Rect(24, 140, 600, 28), "Activity: —"),
            scene_name="main",
        )

    def bind_runtime(self, host) -> None:
        counter = host.counter_feature

        def _on_count(v: int) -> None:
            self._entries.append(f"count → {v}")
            # show the last entry
            self._log_label.text = f"Activity: {self._entries[-1]}"

        self._sub = counter.count.subscribe(_on_count)

    def shutdown_runtime(self, host) -> None:
        self._sub.dispose()
```

Accessing `host.counter_feature` in `bind_runtime` is the correct pattern when two features share a stable, long-lived observable. The host attribute is set by bootstrap from the `FeatureSpec` `attr_name`.

### Step 2 — Alternatively: FeatureMessage for decoupled communication

When features should not hold direct references to each other's internals, `FeatureMessage` provides a decoupled channel. The sender calls `self.send_message(target_name, payload_dict)`. The receiver is a `RoutedFeature` and routes messages by `topic` via `message_handlers()`.

Sender — add to `_increment`:

```python
    def _increment(self) -> None:
        self.count.value = self.count.value + 1
        # send_message routes the payload dict to the named feature as a FeatureMessage
        self.send_message("log_feature", {"topic": "count_changed", "value": self.count.value})
```

Receiver — `LogFeature` becomes a `RoutedFeature`:

```python
from gui_do import RoutedFeature, FeatureMessage


class LogFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("log_feature", scene_name="main")

    def build(self, host) -> None:
        self._log_label = host.app.add(
            LabelControl("log_label", Rect(24, 140, 600, 28), "Activity: —"),
            scene_name="main",
        )

    def message_handlers(self):
        return {"count_changed": self._on_count_changed}

    def _on_count_changed(self, host, message: FeatureMessage) -> None:
        v = message.get("value", "?")
        self._log_label.text = f"Activity: count → {v}"
```

`RoutedFeature.on_update` drains the message queue automatically and dispatches by topic. No `bind_runtime` or `shutdown_runtime` is needed for message routing — the framework handles queue draining each frame.

Use the shared-observable pattern when both features are in the same scene and the observable is genuinely shared state. Use `FeatureMessage` when you want stricter encapsulation or when the sender should not know who is listening.

For the Counter Dashboard we continue with the shared-observable approach for simplicity.

### Step 3 — Register the second feature

Add `LogFeature` to the binding spec alongside `CounterFeature`:

```python
binding = HostApplicationBindingSpec(
    scene_bundles=(SceneBundleBindingSpec(scene_name="main", initial=True),),
    feature_specs=(
        FeatureSpec(attr_name="counter_feature", factory=CounterFeature),
        FeatureSpec(attr_name="log_feature", factory=LogFeature),
    ),
)
```

### Step 4 — Full listing for this step

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
        self.count = ObservableValue(0)

    def build(self, host) -> None:
        self._label = host.app.add(
            LabelControl("count_label", Rect(24, 24, 260, 32), "Count: 0"),
            scene_name="main",
        )
        host.app.add(
            ButtonControl("inc_btn", Rect(24, 68, 140, 32), "+1", on_click=self._increment),
            scene_name="main",
        )

    def bind_runtime(self, host) -> None:
        def _sync(v: int) -> None:
            self._label.text = f"Count: {v}"

        self._sub = self.count.subscribe(_sync)
        _sync(self.count.value)

    def shutdown_runtime(self, host) -> None:
        self._sub.dispose()

    def _increment(self) -> None:
        self.count.value = self.count.value + 1


class LogFeature(Feature):
    def __init__(self) -> None:
        super().__init__("log_feature", scene_name="main")
        self._entries: list[str] = []

    def build(self, host) -> None:
        self._log_label = host.app.add(
            LabelControl("log_label", Rect(24, 140, 600, 28), "Activity: —"),
            scene_name="main",
        )

    def bind_runtime(self, host) -> None:
        counter = host.counter_feature

        def _on_count(v: int) -> None:
            self._entries.append(f"count → {v}")
            self._log_label.text = f"Activity: {self._entries[-1]}"

        self._sub = counter.count.subscribe(_on_count)

    def shutdown_runtime(self, host) -> None:
        self._sub.dispose()


binding = HostApplicationBindingSpec(
    scene_bundles=(SceneBundleBindingSpec(scene_name="main", initial=True),),
    feature_specs=(
        FeatureSpec(attr_name="counter_feature", factory=CounterFeature),
        FeatureSpec(attr_name="log_feature", factory=LogFeature),
    ),
)
config = build_host_application_config(
    binding,
    display_size=(800, 400),
    window_title="Counter Dashboard",
    target_fps=60,
)


class App:
    def __init__(self) -> None:
        bootstrap_host_application(self, config)

    def run(self) -> None:
        self.app.run_entrypoint(target_fps=config.target_fps)


if __name__ == "__main__":
    pygame.init()
    try:
        App().run()
    finally:
        pygame.quit()
```

---

## 8. Actions and Keyboard Shortcuts

The Counter Dashboard should support incrementing the counter with a keyboard shortcut. We will wire this with `ActionSpec` and `ActionHotkeySpec`, then promote the counter to a `RoutedFeature` to handle it declaratively.

### Step 1 — Declare an ActionSpec with a hotkey

`ActionSpec` names an action. `ActionHotkeySpec` binds it to a key. Both go into the `HostApplicationBindingSpec`. This is the entire registration — no manual input map wiring is needed.

```python
import pygame

from gui_do import ActionSpec, ActionHotkeySpec, HostApplicationBindingSpec, SceneBundleBindingSpec


binding = HostApplicationBindingSpec(
    scene_bundles=(SceneBundleBindingSpec(scene_name="main", initial=True),),
    feature_specs=(...),
    action_specs=(
        ActionSpec(
            action_id="increment",
            label="Increment Counter",
            kind="command",
            category="Counter",
        ),
    ),
    action_hotkey_specs=(
        ActionHotkeySpec(action_id="increment", key=pygame.K_PLUS),
    ),
)
```

### Step 2 — Handle the action in a plain Feature

For a plain `Feature`, register the action handler in `bind_runtime` via `host.app.actions` and unregister in `shutdown_runtime`:

```python
    def bind_runtime(self, host) -> None:
        ...
        host.app.actions.register_action("increment", self._increment)

    def shutdown_runtime(self, host) -> None:
        host.app.actions.unregister_action("increment")
        self._sub.dispose()
```

### Step 3 — Use RoutedFeature for declarative wiring

A `RoutedFeature` paired with `RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec` handles action binding and unbinding automatically. You declare what the feature needs; the routed lifecycle helpers wire it.

We promote `CounterFeature` to a `RoutedFeature`:

```python
import pygame
from pygame import Rect

from gui_do import (
    ActionHotkeySpec,
    ActionSpec,
    ButtonControl,
    LabelControl,
    ObservableValue,
    RoutedFeature,
    RoutedFeatureLifecycleSpec,
    RoutedRuntimeSpec,
    ShortcutOverlaySpec,
    bind_routed_feature_lifecycle,
    shutdown_routed_feature_lifecycle,
)


COUNTER_RUNTIME_SPEC = RoutedRuntimeSpec(
    scene_name="main",
    action_specs=(
        ActionSpec(action_id="increment", label="Increment Counter", kind="command", category="Counter"),
    ),
    action_hotkey_specs=(
        ActionHotkeySpec(action_id="increment", key=pygame.K_PLUS),
    ),
    shortcut_overlays=(
        ShortcutOverlaySpec(
            attr_name="shortcut_overlay",
            action_registry_attr="action_registry",
            toggle_action_name="show_help",
            toggle_key=pygame.K_F1,
            manual_shortcut_lines=("+: Increment counter", "F1: Show this help"),
            prepend_manual_shortcuts=True,
        ),
    ),
)

COUNTER_LIFECYCLE_SPEC = RoutedFeatureLifecycleSpec(
    feature_attr="counter_feature",
    runtime_spec=COUNTER_RUNTIME_SPEC,
    action_handlers={"increment": "_increment"},
)


class CounterFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self.count = ObservableValue(0)

    def build(self, host) -> None:
        self._label = host.app.add(
            LabelControl("count_label", Rect(24, 24, 260, 32), "Count: 0"),
            scene_name="main",
        )
        host.app.add(
            ButtonControl("inc_btn", Rect(24, 68, 140, 32), "+1", on_click=self._increment),
            scene_name="main",
        )

    def bind_runtime(self, host) -> None:
        def _sync(v: int) -> None:
            self._label.text = f"Count: {v}"

        self._sub = self.count.subscribe(_sync)
        _sync(self.count.value)
        bind_routed_feature_lifecycle(host, self, COUNTER_LIFECYCLE_SPEC)

    def shutdown_runtime(self, host) -> None:
        shutdown_routed_feature_lifecycle(host, self, COUNTER_LIFECYCLE_SPEC)
        self._sub.dispose()

    def _increment(self) -> None:
        self.count.value = self.count.value + 1
```

`bind_routed_feature_lifecycle` reads `COUNTER_LIFECYCLE_SPEC` and wires action handlers, hotkeys, and the shortcut overlay automatically. `shutdown_routed_feature_lifecycle` tears them all down. No manual binding or unbinding needed.

### Step 4 — Shortcut help overlay

`ShortcutOverlaySpec` in `COUNTER_RUNTIME_SPEC` configures the overlay already. Pressing F1 will toggle a help panel showing all registered shortcuts for the scene, plus the manual lines added via `manual_shortcut_lines`. No additional wiring is required.

---

## 9. Spec Reference for Builders

This section is a quick reference for the specs used throughout the tutorial. For full detail, see [MANUAL.md](MANUAL.md) §8.1 (bootstrap), §8.2 (features), §8.3 (events/actions), §8.4 (state/observables), and §8.8 (overlays).

### `FeatureSpec`

Declares a feature class and the host attribute it will be assigned to after bootstrap.

```python
from gui_do import FeatureSpec

FeatureSpec(attr_name="counter_feature", factory=CounterFeature)
```

See MANUAL.md §8.2.

### `SceneBundleBindingSpec`

Declares a named scene. `initial=True` marks it as the first scene shown.

```python
from gui_do import SceneBundleBindingSpec

SceneBundleBindingSpec(scene_name="main", initial=True)
```

See MANUAL.md §8.9.

### `ActionSpec` + `ActionHotkeySpec`

Declare a named action and an optional keyboard binding.

```python
import pygame
from gui_do import ActionSpec, ActionHotkeySpec

ActionSpec(action_id="increment", label="Increment Counter", kind="command", category="Counter")
ActionHotkeySpec(action_id="increment", key=pygame.K_PLUS)
```

See MANUAL.md §8.3.

### `ShortcutOverlaySpec`

Configures a shortcut discovery overlay toggled by a key. Renders all registered actions for the scene plus any manual lines.

```python
from gui_do import ShortcutOverlaySpec

ShortcutOverlaySpec(
    attr_name="shortcut_overlay",
    action_registry_attr="action_registry",
    toggle_action_name="show_help",
    toggle_key=pygame.K_F1,
    manual_shortcut_lines=("+: Increment", "F1: Show help"),
    prepend_manual_shortcuts=True,
)
```

See MANUAL.md §8.8.

### `RoutedRuntimeSpec` + `RoutedFeatureLifecycleSpec`

Bundles a `RoutedFeature`'s runtime requirements into a single spec. `bind_routed_feature_lifecycle` and `shutdown_routed_feature_lifecycle` read it to wire and unwire everything.

```python
from gui_do import RoutedRuntimeSpec, RoutedFeatureLifecycleSpec

RUNTIME_SPEC = RoutedRuntimeSpec(scene_name="main", action_specs=(...), shortcut_overlays=(...))
LIFECYCLE_SPEC = RoutedFeatureLifecycleSpec(
    feature_attr="counter_feature",
    runtime_spec=RUNTIME_SPEC,
    action_handlers={"increment": "_increment"},
)
```

See MANUAL.md §8.2 and §8.3.

### `ToastManager`

Show a transient notification from any feature that has access to the host:

```python
host.app.toasts.show("Counter reset", severity=ToastSeverity.INFO)
```

See MANUAL.md §8.8.

---

## 10. Complete Project Listing

The full Counter Dashboard as built through this tutorial. Two features, shared observable state, a keyboard shortcut, a shortcut overlay, and clean teardown.

```python
import pygame
from pygame import Rect

# Feature lifecycle and routing
from gui_do import (
    Feature,
    RoutedFeature,
    RoutedRuntimeSpec,
    RoutedFeatureLifecycleSpec,
    bind_routed_feature_lifecycle,
    shutdown_routed_feature_lifecycle,
)

# Controls
from gui_do import (
    ButtonControl,
    LabelControl,
)

# State
from gui_do import ObservableValue

# Actions
from gui_do import ActionSpec, ActionHotkeySpec

# Overlays
from gui_do import ShortcutOverlaySpec

# Bootstrap
from gui_do import (
    FeatureSpec,
    HostApplicationBindingSpec,
    SceneBundleBindingSpec,
    build_host_application_config,
    bootstrap_host_application,
)


# ---------------------------------------------------------------------------
# Routed runtime spec: declares the increment action, its hotkey,
# and the F1 shortcut overlay. bind_routed_feature_lifecycle reads this.
# ---------------------------------------------------------------------------
COUNTER_RUNTIME_SPEC = RoutedRuntimeSpec(
    scene_name="main",
    action_specs=(
        ActionSpec(
            action_id="increment",
            label="Increment Counter",
            kind="command",
            category="Counter",
        ),
    ),
    action_hotkey_specs=(
        ActionHotkeySpec(action_id="increment", key=pygame.K_PLUS),
    ),
    shortcut_overlays=(
        ShortcutOverlaySpec(
            attr_name="shortcut_overlay",
            action_registry_attr="action_registry",
            toggle_action_name="show_help",
            toggle_key=pygame.K_F1,
            manual_shortcut_lines=(
                "+: Increment counter",
                "F1: Show this help overlay",
            ),
            prepend_manual_shortcuts=True,
        ),
    ),
)

# Lifecycle spec maps the action id to the method name on the feature.
COUNTER_LIFECYCLE_SPEC = RoutedFeatureLifecycleSpec(
    feature_attr="counter_feature",
    runtime_spec=COUNTER_RUNTIME_SPEC,
    action_handlers={"increment": "_increment"},
)


# ---------------------------------------------------------------------------
# CounterFeature: owns the count observable, the count label, and the
# increment button. Promoted to RoutedFeature for declarative action wiring.
# ---------------------------------------------------------------------------
class CounterFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        # Public observable so LogFeature can subscribe without messaging overhead
        self.count = ObservableValue(0)

    def build(self, host) -> None:
        # Build controls; subscriptions cannot be set here (bind_runtime is the right place)
        self._label = host.app.add(
            LabelControl("count_label", Rect(24, 24, 300, 32), "Count: 0"),
            scene_name="main",
        )
        host.app.add(
            ButtonControl(
                "inc_btn", Rect(24, 68, 160, 32), "Increment (+1)", on_click=self._increment
            ),
            scene_name="main",
        )

    def bind_runtime(self, host) -> None:
        # Wire the observable to the label; initialize immediately
        def _sync(v: int) -> None:
            self._label.text = f"Count: {v}"

        self._sub = self.count.subscribe(_sync)
        _sync(self.count.value)

        # Wire actions, hotkeys, and overlays declared in COUNTER_LIFECYCLE_SPEC
        bind_routed_feature_lifecycle(host, self, COUNTER_LIFECYCLE_SPEC)

    def shutdown_runtime(self, host) -> None:
        # Tear down routed wiring first, then subscriptions
        shutdown_routed_feature_lifecycle(host, self, COUNTER_LIFECYCLE_SPEC)
        self._sub.dispose()

    def _increment(self) -> None:
        self.count.value = self.count.value + 1


# ---------------------------------------------------------------------------
# LogFeature: subscribes to the counter observable and keeps a running
# activity log, showing the most recent entry in a label.
# ---------------------------------------------------------------------------
class LogFeature(Feature):
    def __init__(self) -> None:
        super().__init__("log_feature", scene_name="main")
        self._entries: list[str] = []

    def build(self, host) -> None:
        self._log_label = host.app.add(
            LabelControl("log_label", Rect(24, 128, 700, 28), "Activity: —"),
            scene_name="main",
        )
        self._hint_label = host.app.add(
            LabelControl("hint_label", Rect(24, 168, 700, 24), "Press + or click Increment. F1 for shortcuts."),
            scene_name="main",
        )

    def bind_runtime(self, host) -> None:
        # Access the counter's observable via host; safe because build-before-bind is guaranteed
        counter = host.counter_feature

        def _on_count(v: int) -> None:
            self._entries.append(f"count changed to {v}")
            self._log_label.text = f"Activity: {self._entries[-1]}"

        self._sub = counter.count.subscribe(_on_count)

    def shutdown_runtime(self, host) -> None:
        self._sub.dispose()


# ---------------------------------------------------------------------------
# Application bootstrap: assembles the binding spec and runs the app.
# ---------------------------------------------------------------------------
binding = HostApplicationBindingSpec(
    scene_bundles=(
        SceneBundleBindingSpec(scene_name="main", initial=True),
    ),
    feature_specs=(
        FeatureSpec(attr_name="counter_feature", factory=CounterFeature),
        FeatureSpec(attr_name="log_feature", factory=LogFeature),
    ),
)
config = build_host_application_config(
    binding,
    display_size=(800, 240),
    window_title="Counter Dashboard",
    target_fps=60,
)


class App:
    def __init__(self) -> None:
        bootstrap_host_application(self, config)

    def run(self) -> None:
        self.app.run_entrypoint(target_fps=config.target_fps)


if __name__ == "__main__":
    pygame.init()
    try:
        App().run()
    finally:
        pygame.quit()
```

---

## 11. Next Steps

**Read [MANUAL.md](MANUAL.md).** It is the complete reference for every system: 16 system chapters with API tables, usage patterns, integration recipes, and appendices. The chapters most relevant to your next steps:
- §8.1 — Application Bootstrap and Host Configuration: full `HostApplicationConfig` field reference, multi-scene setup
- §8.2 — Feature Lifecycle and Feature Types: `LogicFeature`, `DirectFeature`, companion features, scene setup specs
- §8.3 — Events, Actions, Input Mapping, and Routing: key chords, action middleware, event recorder/playback
- §8.4 — State and Observables: `ComputedValue`, `ObservableList`, `ObservableDict`, `CollectionView`, `Binding`

**Explore [demo_features/](demo_features/).** Every subfolder is a self-contained feature package showing real gui_do patterns: routed runtime specs, scene shell helpers, shortcut overlays, window presentation, and multi-feature coordination. Each `__init__.py` is the sole public surface; this folder-per-feature layout is the established organizational pattern for gui_do applications.

**Topics to explore from here:**
- Scene navigation: `SceneBundleBindingSpec` with multiple scenes, animated transitions
- Overlays: `ToastManager`, `DialogManager`, `CommandPaletteManager`
- Persistence: `WorkspacePersistenceManager` saves and restores session state across runs
- Telemetry: `TelemetryCollector` instruments performance-sensitive paths
- Graphics: `DirectFeature` with `DrawContext`, `ParticleSystem`, `SceneGraph2D`, `TileMap`

**Read the source.** `gui_do/features/data_driven_runtime.py` and `gui_do/features/feature_lifecycle.py` are well-commented and readable. Reading them will demystify exactly what `bootstrap_host_application` does and why the lifecycle ordering is guaranteed.
