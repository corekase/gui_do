# gui_do Tutorial

## Table of Contents

1. [Introduction](#1-introduction)
2. [Core Concepts](#2-core-concepts)
3. [Installation and Setup](#3-installation-and-setup)
4. [Your First Feature](#4-your-first-feature)
5. [Reactive State: Making the UI Respond](#5-reactive-state-making-the-ui-respond)
6. [Feature Types](#6-feature-types)
7. [A Second Feature and Feature Communication](#7-a-second-feature-and-feature-communication)
8. [Actions and Keyboard Shortcuts](#8-actions-and-keyboard-shortcuts)
9. [Spec Reference for Builders](#9-spec-reference-for-builders)
10. [Complete Project Listing](#10-complete-project-listing)
11. [Next Steps](#11-next-steps)

---

## 1. Introduction

**gui_do** is a Python GUI framework built on pygame. It brings a declarative, feature-lifecycle-oriented programming model to interactive desktop applications: instead of wiring widgets imperatively, you describe your application's structure with data objects called specs, and the bootstrap system reads those specs to initialize every system — events, focus, routing, overlays, scene transitions — without boilerplate.

### What We Will Build

This tutorial builds a **Session Dashboard** — a two-feature application where:

- `CounterFeature` displays a running count, provides "Increment" and "Reset" buttons, and exposes a keyboard shortcut for resetting.
- `ActivityFeature` listens for messages from `CounterFeature` and displays the most recent activity in a status label.

By the end you will have a working, runnable application that demonstrates the full gui_do programming model: reactive state, feature lifecycle, declarative bootstrap, inter-feature messaging, and keyboard actions.

### Prerequisites

- Python 3.10 or newer
- `pygame` and `numpy` installed (`python -m pip install pygame numpy`)
- No prior knowledge of gui_do or other GUI frameworks is required
- Basic Python knowledge (classes, methods, lambdas) is assumed

For deeper coverage of any topic introduced here, consult [MANUAL.md](MANUAL.md). Every system in this tutorial has a dedicated chapter there.

---

## 2. Core Concepts

Before writing any code, it helps to understand three ideas that the entire framework is built around. Every gui_do application is an expression of these three concepts.

### Declarative Specs vs Imperative Wiring

In most GUI frameworks you write imperative code: create a window, add a button, register a click handler, register the button with a layout manager, etc. Each step is a call with side effects, and the order matters.

gui_do takes a different approach. You describe what your application looks like using **data objects called specs**: a `HostApplicationBindingSpec` says which scenes exist, which features are active, what actions are registered, and what fonts to load. A `SceneBundleBindingSpec` declares one scene with its transition style and name. A `FeatureSpec` (or a `(attr_name, factory)` tuple in `feature_entries`) declares which feature class to instantiate.

Once you have a spec, you pass it to `build_host_application_config` and then to `bootstrap_host_application`. The bootstrap system reads the spec and wires everything — scenes, features, actions, overlays, scheduling — automatically. Features never need to know about each other's existence to be wired together.

**Why this matters:** when you add a new feature, you add a spec entry and a class. You do not touch any other feature's code. Bootstrap handles the sequencing.

### Reactive State

The fundamental data primitive in gui_do is `ObservableValue`. It wraps a single value and allows you to subscribe to changes:

```python
from gui_do import ObservableValue

count = ObservableValue(0)

# Subscribe: the lambda is called whenever count.value changes.
unsubscribe = count.subscribe(lambda v: print(f"Count changed to: {v}"))

count.value = 1   # prints: Count changed to: 1
count.value = 2   # prints: Count changed to: 2

# Clean up when done.
unsubscribe()
count.value = 3   # nothing printed — subscription removed
```

`subscribe` returns a callable. Calling that callable removes the subscription. This is how you avoid memory leaks: store the return value, call it in `shutdown_runtime`.

For collections, gui_do provides `ObservableList` and `ObservableDict`, which fire change notifications whenever items are added, removed, or replaced. For values that are derived from other observables, `ComputedValue` recalculates automatically when any of its dependencies changes — without polling.

**Why this matters:** reactive state means UI controls stay in sync with data automatically. You never write `refresh()` calls scattered through event handlers. You set a value once, and every subscriber — whether it is a label, a log panel, or a remote observer — updates immediately.

### Feature Lifecycle

A feature is a class that inherits from `Feature` (or one of its subtypes). It implements a fixed set of lifecycle methods, each of which the framework calls at the right time:

| Method | When it runs | What to do |
|--------|-------------|-----------|
| `build(host)` | Once, during bootstrap. All features in the scene build before any `bind_runtime` runs. | Create controls, register them with the application. |
| `bind_runtime(host)` | After all features in the scene have completed `build`. | Subscribe to observables, bind actions, register callbacks. |
| `on_update(host)` | Every frame. | Update non-visual state, process messages, tick timers. |
| `handle_event(host, event)` | For each GUI event the framework delivers. | Respond to input that controls do not handle. Return `True` to consume. |
| `draw(host, surface, theme)` | Every frame, after update. | Draw anything that is not a managed control (custom graphics, etc.). |
| `shutdown_runtime(host)` | When the scene or application exits. | Unsubscribe from observables, unbind actions, release resources. |

**The critical sequencing guarantee:** all features in a scene complete `build` before any feature's `bind_runtime` is called. This is a framework guarantee, not a coincidence. It means that in `bind_runtime` you can safely reference controls and state that other features created in their `build` methods, because you know every feature has already built.

**Why this matters:** this separation eliminates initialization-order bugs. You never need to check "has the other feature initialized yet?" The answer is always yes by the time `bind_runtime` runs.

---

## 3. Installation and Setup

### Install

From the repository root, install gui_do as a local editable package:

```bash
python -m pip install -e . --no-deps
```

The `--no-deps` flag skips automatic dependency resolution because gui_do's dependencies (`pygame`, `numpy`) are standard packages that you likely already have. If not, install them separately:

```bash
python -m pip install pygame numpy
```

`numpy` is used internally for pixel buffer operations via `PixelArray`. You do not need to import it in your application code.

### Verify the Install

```bash
python -c "import gui_do; print(gui_do.__version__)"
```

If this prints a version number (e.g., `0.0.9`), your environment is correctly configured.

### The Two Startup Paths

gui_do supports two startup patterns:

1. **Declarative bootstrap (recommended, covered in this tutorial):** describe your application with a `HostApplicationBindingSpec`, call `build_host_application_config`, then `bootstrap_host_application`. The framework handles everything.

2. **Manual `GuiApplication` construction (advanced):** create `GuiApplication` directly and wire systems yourself. This path is documented in [MANUAL.md §8.1](MANUAL.md#81-application-bootstrap-and-host-configuration) and is appropriate when you need fine control over the startup sequence.

This tutorial uses the declarative path exclusively.

### Minimal Imports

Every tutorial example uses only public names importable from the `gui_do` root:

```python
from gui_do import (
    Feature,
    RoutedFeature,
    FeatureMessage,
    ObservableValue,
    LabelControl,
    ButtonControl,
    PanelControl,
    SceneBundleBindingSpec,
    HostApplicationBindingSpec,
    ActionHotkeySpec,
    RoutedRuntimeSpec,
    RoutedFeatureLifecycleSpec,
    build_host_application_config,
    bootstrap_host_application,
    bind_routed_feature_lifecycle,
    shutdown_routed_feature_lifecycle,
)
```

You do not need to import submodules directly. `gui_do/__init__.py` is the authoritative public surface.

---

## 4. Your First Feature

*Narrative: we begin the Session Dashboard by building the `CounterFeature`. At this stage it just shows a static label — we will make it reactive in the next section.*

### Step 1: Define the Feature Class

A `Feature` subclass is the fundamental unit of behavior in gui_do. It owns a named region of the UI and is fully responsible for what that region displays and how it responds to input.

Every `Feature` subclass must call `super().__init__` with a unique feature name and the name of the scene it belongs to:

```python
from gui_do import Feature

class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter", scene_name="main")
```

The `name` argument (`"counter"`) is used by the framework for messaging, logging, and feature lookup. The `scene_name` (`"main"`) tells the framework which scene this feature belongs to; it is only active when that scene is displayed. Both strings must be non-empty.

Why `Feature` rather than one of the other types? Use `Feature` when your feature has visual controls, reads user input, and needs state. `Feature` provides all five lifecycle methods with sensible no-op defaults, so you implement only what you need. See [Section 6](#6-feature-types) for when to use `RoutedFeature`, `LogicFeature`, or `DirectFeature`.

### Step 2: Add a Control

Controls are added inside `build`. The `build` method receives a `host` object that carries everything the feature needs: `host.app` (the application), `host.screen_rect` (the available canvas bounds), and whatever the bootstrap system has added to it.

Add a `LabelControl` to display the count:

```python
from pygame import Rect
from gui_do import Feature, LabelControl, PanelControl

class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter", scene_name="main")
        self._label = None

    def build(self, host):
        # A PanelControl is a container. Add it as a root node in the "main" scene.
        panel = host.app.add(
            PanelControl("counter_panel", host.screen_rect, draw_background=False),
            scene_name="main",
        )
        # Add a LabelControl as a child of the panel.
        self._label = panel.add(
            LabelControl("count_lbl", Rect(20, 20, 300, 48), "Count: 0")
        )
```

Controls are layout objects inside the feature's region, not independent widgets floating on screen. They live inside a `PanelControl` (or another container), which in turn is registered with `host.app.add(...)` as a root node of a scene. `host.app.add` returns the added node, so `panel.add(LabelControl(...))` returns the label and you can store a reference to it for later use.

`host.screen_rect` is a `pygame.Rect` describing the full window bounds. The values `Rect(20, 20, 300, 48)` position the label 20 pixels from the top-left of the panel, 300 pixels wide, 48 pixels tall.

### Step 3: Declare the Config

The application config is built from a `HostApplicationBindingSpec` — a data object that describes the whole application:

```python
from gui_do import (
    SceneBundleBindingSpec,
    HostApplicationBindingSpec,
    build_host_application_config,
)

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1024, 600),
        window_title="Session Dashboard",
        fonts={"default": {"file": "path/to/font.ttf", "size": 14}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(
                scene_name="main",
                pretty_name="Main",
            ),
        ),
        feature_entries=(
            ("_counter", CounterFeature),
        ),
    )
)
```

Key fields:

- `display_size` — initial window size in pixels.
- `window_title` — the title bar string.
- `fonts` — a mapping from role names to font descriptors. The `"default"` role is used by controls unless overridden.
- `initial_scene_name` — which scene is shown on startup.
- `scene_bundle_entries` — declares the set of available scenes. Each `SceneBundleBindingSpec` gives a scene its name and display properties.
- `feature_entries` — declares which feature classes to instantiate. Each entry is a `(attr_name, factory)` tuple. The `attr_name` becomes an attribute on the host object after bootstrap, so you can reference the feature as `host._counter` if needed.

`build_host_application_config` validates the spec and produces a `HostApplicationConfig` ready to pass to the bootstrap function.

### Step 4: Bootstrap and Run

Pass the config to `bootstrap_host_application` to start the application. `bootstrap_host_application(host, config)` attaches all framework systems to `host` as side effects — `host.app`, `host.screen`, `host.screen_rect`, feature attributes, and more.

```python
from gui_do import bootstrap_host_application

class SessionDashboard:
    def __init__(self):
        bootstrap_host_application(self, config)

SessionDashboard().app.run_entrypoint(target_fps=60)
```

The pattern of wrapping bootstrap in a class is idiomatic: any Python object can serve as the host, and using a class makes attribute access natural. `host.app.run_entrypoint(target_fps=60)` starts the frame loop — it blocks until the window is closed.

### Step 5: Full Listing for Step 4

Here is the complete, runnable file for what we have built so far:

```python
from pygame import Rect
from gui_do import (
    Feature, LabelControl, PanelControl,
    SceneBundleBindingSpec, HostApplicationBindingSpec,
    build_host_application_config, bootstrap_host_application,
)

class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter", scene_name="main")
        self._label = None

    def build(self, host):
        panel = host.app.add(
            PanelControl("counter_panel", host.screen_rect, draw_background=False),
            scene_name="main",
        )
        self._label = panel.add(
            LabelControl("count_lbl", Rect(20, 20, 300, 48), "Count: 0")
        )

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1024, 600),
        window_title="Session Dashboard",
        fonts={"default": {"file": "path/to/font.ttf", "size": 14}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(scene_name="main", pretty_name="Main"),
        ),
        feature_entries=(
            ("_counter", CounterFeature),
        ),
    )
)

class SessionDashboard:
    def __init__(self):
        bootstrap_host_application(self, config)

SessionDashboard().app.run_entrypoint(target_fps=60)
```

Run this file and you will see a window with a static label displaying "Count: 0". The next section wires the count to reactive state so the label updates automatically when the value changes.

---

## 5. Reactive State: Making the UI Respond

*Narrative: we add `ObservableValue` and a button. Clicking the button increments the count, and the label updates itself automatically through a subscription.*

### Step 1: Introduce `ObservableValue`

`ObservableValue` wraps a single value. When `.value` is set to a new value, every subscriber is notified immediately. Add one to the feature:

```python
from gui_do import Feature, ObservableValue

class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter", scene_name="main")
        self._count = ObservableValue(0)
        self._label = None
        self._sub = None
```

`ObservableValue(0)` creates an observable initialized to `0`. `self._sub` will store the unsubscribe callable returned by `.subscribe()` — we need to call it in `shutdown_runtime` to release the subscription.

### Step 2: Add a Button

Add a `ButtonControl` to `build`. `ButtonControl` takes an `on_click` callable that is called with no arguments when the user clicks the button:

```python
from pygame import Rect
from gui_do import Feature, ObservableValue, LabelControl, ButtonControl, PanelControl

class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter", scene_name="main")
        self._count = ObservableValue(0)
        self._label = None
        self._sub = None

    def build(self, host):
        panel = host.app.add(
            PanelControl("counter_panel", host.screen_rect, draw_background=False),
            scene_name="main",
        )
        self._label = panel.add(
            LabelControl("count_lbl", Rect(20, 20, 300, 48), "Count: 0")
        )
        panel.add(
            ButtonControl("inc_btn", Rect(20, 80, 160, 36), "Increment",
                          on_click=self._increment)
        )

    def _increment(self):
        # Setting .value triggers all subscribers immediately.
        self._count.value += 1
```

The `_increment` method is a plain Python method; `on_click=self._increment` stores a bound method reference. No special decorator is needed.

### Step 3: Wire the Observable to the Label

In `bind_runtime`, subscribe to the observable and update the label's `text` property whenever the value changes. This is done in `bind_runtime` — not in `build` — because subscriptions need a live control tree. `build` creates controls; `bind_runtime` connects them to data:

```python
    def bind_runtime(self, host):
        # subscribe returns an unsubscribe callable. Store it.
        self._sub = self._count.subscribe(
            lambda v: setattr(self._label, "text", f"Count: {v}")
        )
```

`setattr(self._label, "text", f"Count: {v}")` is equivalent to `self._label.text = f"Count: {v}"`. Both work; the `setattr` form fits neatly inside a lambda.

### Step 4: Unsubscribe in `shutdown_runtime`

When the scene exits, the framework calls `shutdown_runtime`. Subscriptions hold references to the callable and to the observable's observer list. Failing to unsubscribe causes memory leaks and may fire callbacks on a control that no longer exists:

```python
    def shutdown_runtime(self, host):
        if self._sub:
            self._sub()       # remove the subscription
            self._sub = None
```

Calling `self._sub()` removes the lambda from the observable's observer list. Setting `self._sub = None` clears the reference. Always unsubscribe in `shutdown_runtime` for every subscription set up in `bind_runtime`.

### Step 5: Full Listing for Section 5

```python
from pygame import Rect
from gui_do import (
    Feature, ObservableValue, LabelControl, ButtonControl, PanelControl,
    SceneBundleBindingSpec, HostApplicationBindingSpec,
    build_host_application_config, bootstrap_host_application,
)

class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter", scene_name="main")
        self._count = ObservableValue(0)
        self._label = None
        self._sub = None

    def build(self, host):
        panel = host.app.add(
            PanelControl("counter_panel", host.screen_rect, draw_background=False),
            scene_name="main",
        )
        self._label = panel.add(
            LabelControl("count_lbl", Rect(20, 20, 300, 48), "Count: 0")
        )
        panel.add(
            ButtonControl("inc_btn", Rect(20, 80, 160, 36), "Increment",
                          on_click=self._increment)
        )

    def _increment(self):
        self._count.value += 1

    def bind_runtime(self, host):
        self._sub = self._count.subscribe(
            lambda v: setattr(self._label, "text", f"Count: {v}")
        )

    def shutdown_runtime(self, host):
        if self._sub:
            self._sub()
            self._sub = None

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1024, 600),
        window_title="Session Dashboard",
        fonts={"default": {"file": "path/to/font.ttf", "size": 14}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(scene_name="main", pretty_name="Main"),
        ),
        feature_entries=(("_counter", CounterFeature),),
    )
)

class SessionDashboard:
    def __init__(self):
        bootstrap_host_application(self, config)

SessionDashboard().app.run_entrypoint(target_fps=60)
```

Run this file. Each click of the "Increment" button increments the count, and the label updates itself instantly — no polling, no manual refresh. The reactive subscription does all the work.

---

## 6. Feature Types

gui_do provides four feature base classes. They share the same lifecycle contract but differ in what they automate and what they allow:

### `Feature`

The standard choice for any feature that has a visual presence, manages state, and responds to user input. Provides all lifecycle methods with no-op defaults. You implement only what you need.

**Use when:** building a UI panel with controls, observable state, event handling, and/or scheduled updates.

```python
class MyFeature(Feature):
    def __init__(self):
        super().__init__("my_feature", scene_name="main")

    def build(self, host): ...          # create controls
    def bind_runtime(self, host): ...   # subscribe, bind actions
    def on_update(self, host): ...      # per-frame logic
    def shutdown_runtime(self, host): ...  # clean up
```

### `DirectFeature`

Provides no default lifecycle stubs. Every method you implement is called directly by the framework with no superclass behavior. Useful when you want complete control and do not want to inherit any default behavior.

**Use when:** the default no-op stubs from `Feature` would be misleading, or you are implementing a very specialized protocol. Most application code does not need this.

### `LogicFeature`

No `draw` method and no control tree. Participates in the lifecycle for computation, coordination, and state management but does not render anything.

**Use when:** you need background computation, cross-feature coordination, or a data pipeline that has no direct visual output. For example, a `LogicFeature` might compute Mandelbrot tiles and push results to a canvas controlled by a sibling feature.

```python
class ComputationLogic(LogicFeature):
    def __init__(self):
        super().__init__("computation_logic", scene_name="main")

    def on_update(self, host):
        # process data, emit messages, update shared observables
        ...
```

### `RoutedFeature`

Extends `Feature` with topic-based message dispatch. When a `RoutedFeature` receives a `FeatureMessage` via the messaging system, its `on_update` automatically routes the message to the right handler method via the topic key returned by `message_handlers()`. It also integrates cleanly with `RoutedRuntimeSpec` for declarative action hotkey and event subscription registration.

**Use when:** a feature declares keyboard shortcuts via `RoutedRuntimeSpec`, needs to participate in a tabbed presentation model, or receives typed messages from sibling features and needs clean per-topic dispatch.

```python
class MyRoutedFeature(RoutedFeature):
    def __init__(self):
        super().__init__("my_routed", scene_name="main")

    def message_handlers(self):
        return {
            "data_ready": self._on_data_ready,
        }

    def _on_data_ready(self, host, message: FeatureMessage) -> None:
        # handle the message
        ...
```

We will use `RoutedFeature` for `CounterFeature` in [Section 8](#8-actions-and-keyboard-shortcuts) to wire a keyboard shortcut declaratively.

---

## 7. A Second Feature and Feature Communication

*Narrative: we add `ActivityFeature` to the Session Dashboard. It displays the most recent event logged by `CounterFeature`. The two features communicate via `FeatureMessage`.*

### Step 1: Define the Second Feature

`ActivityFeature` occupies the right half of the window and displays a status label:

```python
from pygame import Rect
from gui_do import Feature, LabelControl, PanelControl

class ActivityFeature(Feature):
    def __init__(self):
        super().__init__("activity", scene_name="main")
        self._status_label = None

    def build(self, host):
        # Place this feature in the right half of the screen.
        x = host.screen_rect.width // 2
        w = host.screen_rect.width // 2
        h = host.screen_rect.height
        panel = host.app.add(
            PanelControl("activity_panel", Rect(x, 0, w, h), draw_background=False),
            scene_name="main",
        )
        self._status_label = panel.add(
            LabelControl("status_lbl", Rect(20, 20, w - 40, 48), "No events yet.")
        )
```

Add it to `feature_entries` in the config:

```python
feature_entries=(
    ("_counter", CounterFeature),
    ("_activity", ActivityFeature),
),
```

Both features share the same `scene_name="main"`, so they are both active when the main scene is displayed.

### Step 2: Shared State via Observable

The simplest form of inter-feature communication is a shared `ObservableValue`. If you set an observable on `host` during `build`, both features can subscribe to it in `bind_runtime`:

```python
# In CounterFeature.build:
host.shared_count = self._count   # expose on host

# In ActivityFeature.bind_runtime:
self._sub = host.shared_count.subscribe(
    lambda v: setattr(self._status_label, "text", f"Count is now: {v}")
)
```

This works and is sometimes the right choice. However, it creates a direct dependency between features through the host — `ActivityFeature` must know that `CounterFeature` exposes `host.shared_count`. For features that should be fully independent, `FeatureMessage` is the better approach.

### Step 3: Feature Messaging

`FeatureMessage` is a structured envelope for inter-feature communication. A feature sends a message by name; the framework delivers it to the named feature's message queue; the receiving feature drains its queue in `on_update`.

First, define the message. Subclassing `FeatureMessage` is optional but makes the intent explicit. Any `Mapping` can be the payload:

```python
from gui_do import FeatureMessage

class CounterChangedMessage(FeatureMessage):
    """Sent by CounterFeature when the count changes."""

    @classmethod
    def create(cls, sender: str, new_value: int) -> "CounterChangedMessage":
        return cls.from_payload(
            sender=sender,
            target="activity",
            payload={"event": "changed", "value": new_value, "topic": "count"},
        )
```

The `"topic"` key is used by `RoutedFeature` for automatic dispatch, but a plain `Feature` can also read it directly. The `"event"` and `"value"` keys are application-defined.

In `CounterFeature`, send the message whenever the count changes:

```python
    def _on_count_changed(self, new_value: int) -> None:
        # Update the label directly.
        self._label.text = f"Count: {new_value}"
        # Notify the activity feature via the messaging system.
        self.send_message(
            "activity",
            {"event": "changed", "value": new_value, "topic": "count"},
        )
```

`self.send_message(target_name, payload_dict)` places a `FeatureMessage` into the named feature's message queue. It requires the feature to be registered (which the framework guarantees by the time `bind_runtime` runs).

In `ActivityFeature`, drain the message queue in `on_update`:

```python
    def on_update(self, host):
        while self.has_messages():
            msg = self.pop_message()
            if msg is not None and msg.get("event") == "changed":
                self._status_label.text = f"Last event: count → {msg.get('value')}"
```

`has_messages()` returns `True` if there are queued messages. `pop_message()` returns and removes the first message, or `None` if the queue is empty. `msg.get("key")` reads from the payload dict.

**When to use messaging vs shared state:**
- Use a shared observable when features are naturally coupled through the same data (a selection in a list view and a detail panel that shows the selection).
- Use `FeatureMessage` when features should not hold direct references to each other — when they are independently testable units that happen to coexist in the same scene.

### Step 4: Updated Full Listing

Here is the full listing with both features and messaging wired:

```python
from pygame import Rect
from gui_do import (
    Feature, ObservableValue, FeatureMessage,
    LabelControl, ButtonControl, PanelControl,
    SceneBundleBindingSpec, HostApplicationBindingSpec,
    build_host_application_config, bootstrap_host_application,
)

# Message type for cross-feature communication
class CounterChangedMessage(FeatureMessage):
    @classmethod
    def create(cls, sender: str, new_value: int) -> "CounterChangedMessage":
        return cls.from_payload(
            sender=sender,
            target="activity",
            payload={"event": "changed", "value": new_value, "topic": "count"},
        )

class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter", scene_name="main")
        self._count = ObservableValue(0)
        self._label = None
        self._sub = None

    def build(self, host):
        w = host.screen_rect.width // 2
        h = host.screen_rect.height
        panel = host.app.add(
            PanelControl("counter_panel", Rect(0, 0, w, h), draw_background=False),
            scene_name="main",
        )
        self._label = panel.add(
            LabelControl("count_lbl", Rect(20, 20, w - 40, 48), "Count: 0")
        )
        panel.add(ButtonControl("inc_btn", Rect(20, 80, 160, 36), "Increment",
                                on_click=self._increment))

    def _increment(self):
        self._count.value += 1

    def bind_runtime(self, host):
        self._sub = self._count.subscribe(self._on_count_changed)

    def _on_count_changed(self, new_value: int) -> None:
        self._label.text = f"Count: {new_value}"
        self.send_message(
            "activity",
            {"event": "changed", "value": new_value, "topic": "count"},
        )

    def shutdown_runtime(self, host):
        if self._sub:
            self._sub()
            self._sub = None

class ActivityFeature(Feature):
    def __init__(self):
        super().__init__("activity", scene_name="main")
        self._status_label = None

    def build(self, host):
        x = host.screen_rect.width // 2
        w = host.screen_rect.width // 2
        h = host.screen_rect.height
        panel = host.app.add(
            PanelControl("activity_panel", Rect(x, 0, w, h), draw_background=False),
            scene_name="main",
        )
        self._status_label = panel.add(
            LabelControl("status_lbl", Rect(20, 20, w - 40, 48), "No events yet.")
        )

    def on_update(self, host):
        while self.has_messages():
            msg = self.pop_message()
            if msg is not None and msg.get("event") == "changed":
                self._status_label.text = f"Last event: count → {msg.get('value')}"

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1024, 600),
        window_title="Session Dashboard",
        fonts={"default": {"file": "path/to/font.ttf", "size": 14}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(scene_name="main", pretty_name="Main"),
        ),
        feature_entries=(
            ("_counter", CounterFeature),
            ("_activity", ActivityFeature),
        ),
    )
)

class SessionDashboard:
    def __init__(self):
        bootstrap_host_application(self, config)

SessionDashboard().app.run_entrypoint(target_fps=60)
```

Run this. Click "Increment" and the count label updates on the left. Simultaneously, the status label on the right shows the most recent event. The two features communicate through the messaging system without holding direct references to each other.

---

## 8. Actions and Keyboard Shortcuts

*Narrative: we wire a keyboard shortcut so pressing `R` resets the counter. We convert `CounterFeature` to a `RoutedFeature` to use the declarative `RoutedRuntimeSpec` pattern.*

### Step 1: Declare an Action

An action is a named, registerable operation. You declare one in `HostApplicationBindingSpec` by adding it to `action_entries`, or you register it directly inside a `RoutedRuntimeSpec`. For custom feature-level actions, the `RoutedRuntimeSpec` + `ActionHotkeySpec` pattern is the right choice — you describe the action name, its handler, and the key binding in one place, and the framework wires everything automatically.

`ActionHotkeySpec` fields:

- `action_name` — a string identifier for the action in the registry.
- `handler` — a callable that receives the raw pygame event. Called when the action fires.
- `key` — a pygame key constant (`pygame.K_r`, `pygame.K_F1`, etc.). When this key is pressed in the right scene, the handler fires.
- `scene_name` — optional. If given, the key binding is scoped to that scene.

### Step 2: Handle the Action in a Plain `Feature`

For a plain `Feature`, you bind and unbind manually via `host.app.actions`:

```python
import pygame

class CounterFeature(Feature):
    ...
    def bind_runtime(self, host):
        self._sub = self._count.subscribe(self._on_count_changed)
        # Register and bind the reset action manually.
        host.app.actions.register_action("reset_counter", self._keyboard_reset)
        host.app.actions.bind_key(pygame.K_r, "reset_counter", scene="main")

    def _keyboard_reset(self, _event):
        self._reset()

    def shutdown_runtime(self, host):
        if self._sub:
            self._sub()
            self._sub = None
        # Unbind the action.
        host.app.actions.unregister_action("reset_counter")
```

This works, but requires remembering to call `unregister_action` in `shutdown_runtime`. The `RoutedFeature` approach automates this.

### Step 3: `RoutedFeature` with Declarative Shortcut Wiring

Convert `CounterFeature` to a `RoutedFeature` and declare the action hotkey in a `RoutedRuntimeSpec`. The `bind_routed_feature_lifecycle` / `shutdown_routed_feature_lifecycle` helpers handle registration and teardown automatically:

```python
import pygame
from gui_do import (
    RoutedFeature, ActionHotkeySpec, RoutedRuntimeSpec, RoutedFeatureLifecycleSpec,
    bind_routed_feature_lifecycle, shutdown_routed_feature_lifecycle,
)

# Build the runtime spec at bind time so the handler can reference `self`.
def _make_counter_runtime_spec(feature, host) -> RoutedRuntimeSpec:
    return RoutedRuntimeSpec(
        scene_name="main",
        action_hotkeys=(
            ActionHotkeySpec(
                action_name="reset_counter",
                handler=feature._keyboard_reset,
                key=pygame.K_r,
                scene_name="main",
            ),
        ),
    )

_COUNTER_LIFECYCLE_SPEC = RoutedFeatureLifecycleSpec(
    runtime_spec_factory=_make_counter_runtime_spec,
)

class CounterFeature(RoutedFeature):
    def __init__(self):
        super().__init__("counter", scene_name="main")
        self._count = ObservableValue(0)
        self._label = None
        self._sub = None
        self.scheduler = None

    def build(self, host):
        ...  # same as before

    def bind_runtime(self, host):
        # bind_routed_feature_lifecycle registers actions and returns a scheduler.
        self.scheduler = bind_routed_feature_lifecycle(self, host, _COUNTER_LIFECYCLE_SPEC)
        self._sub = self._count.subscribe(self._on_count_changed)

    def _keyboard_reset(self, _event):
        self._count.value = 0

    def shutdown_runtime(self, host):
        if self._sub:
            self._sub()
            self._sub = None
        # shutdown_routed_feature_lifecycle unregisters everything declared in the spec.
        shutdown_routed_feature_lifecycle(self, host, _COUNTER_LIFECYCLE_SPEC)
```

`bind_routed_feature_lifecycle(feature, host, lifecycle_spec)` reads the `RoutedFeatureLifecycleSpec`, calls `runtime_spec_factory` (if provided) to get the `RoutedRuntimeSpec`, registers each `ActionHotkeySpec`, and wires any event subscriptions. The return value is a scheduler — store it on the feature if you need it.

`shutdown_routed_feature_lifecycle(feature, host, lifecycle_spec)` undoes everything `bind_routed_feature_lifecycle` did — unregisters actions, removes event subscriptions, and cleans up the scheduler.

The `runtime_spec_factory=_make_counter_runtime_spec` pattern is used because the `ActionHotkeySpec.handler` needs to reference `feature._keyboard_reset`, which requires a live feature instance. The factory is called at `bind_runtime` time when the feature exists, not at module import time.

### Step 4: Adding a Shortcut Help Overlay

Users cannot discover keyboard shortcuts by inspection. Adding a `ShortcutOverlaySpec` to the `RoutedRuntimeSpec` creates a `ShortcutHelpOverlay` that displays all registered shortcuts when toggled. Wire it to `F1`:

```python
import pygame
from gui_do import ShortcutOverlaySpec

def _make_counter_runtime_spec(feature, host) -> RoutedRuntimeSpec:
    return RoutedRuntimeSpec(
        scene_name="main",
        action_hotkeys=(
            ActionHotkeySpec(
                action_name="reset_counter",
                handler=feature._keyboard_reset,
                key=pygame.K_r,
                scene_name="main",
            ),
        ),
        shortcut_overlays=(
            ShortcutOverlaySpec(
                attr_name="_shortcut_overlay",
                toggle_action_name="toggle_shortcuts",
                toggle_key=pygame.K_F1,
                toggle_scene_name="main",
            ),
        ),
    )
```

`setup_routed_runtime` (called internally by `bind_routed_feature_lifecycle`) reads each `ShortcutOverlaySpec`, creates the overlay, stores it as `feature._shortcut_overlay`, registers a `toggle_shortcuts` action, and binds `F1` to it — all from the declarative spec. Press `F1` in the running app and the overlay displays all registered actions.

### Step 5: Updated Listing

Here is the updated listing with `RoutedFeature`, `ActionHotkeySpec`, and `ShortcutOverlaySpec`:

```python
import pygame
from pygame import Rect
from gui_do import (
    RoutedFeature, Feature, ObservableValue, FeatureMessage,
    LabelControl, ButtonControl, PanelControl,
    ActionHotkeySpec, ShortcutOverlaySpec, RoutedRuntimeSpec, RoutedFeatureLifecycleSpec,
    SceneBundleBindingSpec, HostApplicationBindingSpec,
    build_host_application_config, bootstrap_host_application,
    bind_routed_feature_lifecycle, shutdown_routed_feature_lifecycle,
)

def _make_counter_runtime_spec(feature, host) -> RoutedRuntimeSpec:
    return RoutedRuntimeSpec(
        scene_name="main",
        action_hotkeys=(
            ActionHotkeySpec(
                action_name="reset_counter",
                handler=feature._keyboard_reset,
                key=pygame.K_r,
                scene_name="main",
            ),
        ),
        shortcut_overlays=(
            ShortcutOverlaySpec(
                attr_name="_shortcut_overlay",
                toggle_action_name="toggle_shortcuts",
                toggle_key=pygame.K_F1,
                toggle_scene_name="main",
            ),
        ),
    )

_COUNTER_LIFECYCLE_SPEC = RoutedFeatureLifecycleSpec(
    runtime_spec_factory=_make_counter_runtime_spec,
)

class CounterFeature(RoutedFeature):
    def __init__(self):
        super().__init__("counter", scene_name="main")
        self._count = ObservableValue(0)
        self._label = None
        self._sub = None
        self.scheduler = None

    def build(self, host):
        w = host.screen_rect.width // 2
        h = host.screen_rect.height
        panel = host.app.add(
            PanelControl("counter_panel", Rect(0, 0, w, h), draw_background=False),
            scene_name="main",
        )
        self._label = panel.add(
            LabelControl("count_lbl", Rect(20, 20, w - 40, 48), "Count: 0")
        )
        panel.add(ButtonControl("inc_btn", Rect(20, 80, 160, 36), "Increment",
                                on_click=self._increment))
        panel.add(ButtonControl("rst_btn", Rect(190, 80, 140, 36), "Reset",
                                on_click=self._reset))

    def bind_runtime(self, host):
        self.scheduler = bind_routed_feature_lifecycle(self, host, _COUNTER_LIFECYCLE_SPEC)
        self._sub = self._count.subscribe(self._on_count_changed)

    def _increment(self):
        self._count.value += 1

    def _reset(self):
        self._count.value = 0

    def _keyboard_reset(self, _event):
        self._reset()

    def _on_count_changed(self, new_value: int) -> None:
        self._label.text = f"Count: {new_value}"
        self.send_message(
            "activity",
            {"event": "changed", "value": new_value, "topic": "count"},
        )

    def shutdown_runtime(self, host):
        if self._sub:
            self._sub()
            self._sub = None
        shutdown_routed_feature_lifecycle(self, host, _COUNTER_LIFECYCLE_SPEC)

class ActivityFeature(Feature):
    def __init__(self):
        super().__init__("activity", scene_name="main")
        self._status_label = None

    def build(self, host):
        x = host.screen_rect.width // 2
        w = host.screen_rect.width // 2
        h = host.screen_rect.height
        panel = host.app.add(
            PanelControl("activity_panel", Rect(x, 0, w, h), draw_background=False),
            scene_name="main",
        )
        self._status_label = panel.add(
            LabelControl("status_lbl", Rect(20, 20, w - 40, 48), "No events yet.")
        )

    def on_update(self, host):
        while self.has_messages():
            msg = self.pop_message()
            if msg is not None and msg.get("event") == "changed":
                self._status_label.text = f"Last event: count → {msg.get('value')}"

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1024, 600),
        window_title="Session Dashboard",
        fonts={"default": {"file": "path/to/font.ttf", "size": 14}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(scene_name="main", pretty_name="Main"),
        ),
        feature_entries=(
            ("_counter", CounterFeature),
            ("_activity", ActivityFeature),
        ),
    )
)

class SessionDashboard:
    def __init__(self):
        bootstrap_host_application(self, config)

SessionDashboard().app.run_entrypoint(target_fps=60)
```

Press `R` to reset the counter from the keyboard. Press `F1` to toggle the shortcut help overlay. Both behaviors are declared in the spec — no manual input-map wiring or teardown code beyond `shutdown_routed_feature_lifecycle`.

---

## 9. Spec Reference for Builders

This section is a concise reference for the spec types used in this tutorial. For full detail on any spec — including all optional fields, behavioral guarantees, and integration recipes — consult [MANUAL.md §8.1 (Bootstrap)](MANUAL.md#81-application-bootstrap-and-host-configuration), [§8.2 (Feature Lifecycle)](MANUAL.md#82-feature-lifecycle-and-feature-types), and [§8.3 (Events and Actions)](MANUAL.md#83-events-actions-input-mapping-and-routing).

### `FeatureSpec`

Declares a feature class and its scene membership as a typed data object. In most cases you use the shorthand tuple form `(attr_name, factory)` in `feature_entries`, which the bootstrap converts automatically.

```python
from gui_do import FeatureSpec

FeatureSpec(attr_name="_counter", factory=CounterFeature)
# Equivalent shorthand in feature_entries:
# ("_counter", CounterFeature)
```

### `SceneBundleBindingSpec`

Declares one named scene with its display name, optional transition style, prewarm policy, and optional scene root panel.

```python
from gui_do import SceneBundleBindingSpec, SceneTransitionStyle

SceneBundleBindingSpec(
    scene_name="main",
    pretty_name="Main",
    transition_style=SceneTransitionStyle.SLIDE_RIGHT,  # optional
    transition_duration=0.4,                            # optional
    prewarm=True,                                       # pre-render before showing
)
```

See [MANUAL.md §8.9](MANUAL.md#89-scene-window-and-task-panel-presentation-models) for multi-scene navigation patterns.

### `ActionSpec` + `ActionHotkeySpec`

`ActionSpec` (in `action_entries`) declares a high-level application action such as exit or scene navigation. `ActionHotkeySpec` (in `RoutedRuntimeSpec`) declares a feature-level action with a handler and optional key binding.

```python
from gui_do import ActionHotkeySpec
import pygame

ActionHotkeySpec(
    action_name="reset_counter",
    handler=feature._keyboard_reset,  # called with the raw pygame event
    key=pygame.K_r,
    scene_name="main",               # scope to one scene
)
```

See [MANUAL.md §8.3](MANUAL.md#83-events-actions-input-mapping-and-routing) for the full action routing pipeline.

### `ShortcutOverlaySpec`

Configures a `ShortcutHelpOverlay` for user-discoverable keyboard shortcut documentation. Attach it to a `RoutedRuntimeSpec`; `bind_routed_feature_lifecycle` creates the overlay and wires the toggle key automatically.

```python
from gui_do import ShortcutOverlaySpec
import pygame

ShortcutOverlaySpec(
    attr_name="_shortcut_overlay",       # stored as feature._shortcut_overlay
    toggle_action_name="toggle_shortcuts",
    toggle_key=pygame.K_F1,
    toggle_scene_name="main",
)
```

See [MANUAL.md §8.8](MANUAL.md#88-overlays-dialogs-notifications-and-command-surfaces) for overlay management.

### `RoutedRuntimeSpec` + `RoutedFeatureLifecycleSpec`

The declarative bundle for a `RoutedFeature`. `RoutedRuntimeSpec` describes what to wire (hotkeys, event subscriptions, shortcut overlays). `RoutedFeatureLifecycleSpec` holds the spec or factory and is passed to `bind_routed_feature_lifecycle` / `shutdown_routed_feature_lifecycle`.

```python
from gui_do import RoutedRuntimeSpec, RoutedFeatureLifecycleSpec

_LIFECYCLE_SPEC = RoutedFeatureLifecycleSpec(
    runtime_spec_factory=lambda feature, host: RoutedRuntimeSpec(
        scene_name="main",
        action_hotkeys=(...),
        shortcut_overlays=(...),
    ),
)
```

See [MANUAL.md §8.2](MANUAL.md#82-feature-lifecycle-and-feature-types) for the full `RoutedFeature` lifecycle.

### `ToastManager`

Show a brief notification message from any feature using `host.toasts.show(...)`. `ToastManager` is accessible via `host.toasts` after bootstrap:

```python
from gui_do import ToastSeverity

# In any lifecycle method that has access to host:
host.toasts.show("Reset complete", severity=ToastSeverity.INFO, duration=2.0)
```

See [MANUAL.md §8.8](MANUAL.md#88-overlays-dialogs-notifications-and-command-surfaces) for full `ToastManager` options including severity levels and stacking behavior.

---

## 10. Complete Project Listing

The listing below is the full, runnable Session Dashboard built throughout this tutorial. It requires a valid font file at the path specified in `fonts`. Replace `"path/to/font.ttf"` with an actual `.ttf` file path, or use one from `demo_features/data/fonts/` if you have the repository checked out.

```python
# Session Dashboard — complete gui_do tutorial project.
#
# Two features share a scene:
#   CounterFeature (RoutedFeature) — manages reactive count state, exposes
#     "Increment" and "Reset" buttons, and wires R to keyboard reset via
#     RoutedRuntimeSpec + ActionHotkeySpec. Sends FeatureMessage to ActivityFeature
#     on every count change.
#
#   ActivityFeature (Feature) — receives messages from CounterFeature and
#     displays the most recent event in a status label.
#
# Press R to reset the counter from the keyboard.
# Press F1 to toggle the shortcut help overlay.

import pygame
from pygame import Rect

from gui_do import (
    # Feature base classes
    Feature,
    RoutedFeature,
    FeatureMessage,
    # Reactive state
    ObservableValue,
    # Controls
    LabelControl,
    ButtonControl,
    PanelControl,
    # Action and routing specs
    ActionHotkeySpec,
    ShortcutOverlaySpec,
    RoutedRuntimeSpec,
    RoutedFeatureLifecycleSpec,
    # Bootstrap specs
    SceneBundleBindingSpec,
    HostApplicationBindingSpec,
    build_host_application_config,
    bootstrap_host_application,
    # Routed lifecycle helpers
    bind_routed_feature_lifecycle,
    shutdown_routed_feature_lifecycle,
)


# ---------------------------------------------------------------------------
# Messages used for cross-feature communication
# ---------------------------------------------------------------------------

class CounterChangedMessage(FeatureMessage):
    """Payload sent by CounterFeature to ActivityFeature on every count change.

    Using a FeatureMessage subclass is optional — a plain dict payload works too.
    Subclassing makes the intent explicit and allows isinstance checks.
    """

    @classmethod
    def create(cls, sender: str, new_value: int) -> "CounterChangedMessage":
        return cls.from_payload(
            sender=sender,
            target="activity",
            payload={"event": "changed", "value": new_value, "topic": "count"},
        )


# ---------------------------------------------------------------------------
# CounterFeature — left panel, owns count state and keyboard shortcut
# ---------------------------------------------------------------------------

def _make_counter_runtime_spec(feature, host) -> RoutedRuntimeSpec:
    """Build the runtime spec at bind time so handler can capture `feature`."""
    return RoutedRuntimeSpec(
        scene_name="main",
        action_hotkeys=(
            ActionHotkeySpec(
                action_name="reset_counter",
                handler=feature._keyboard_reset,    # bound method reference
                key=pygame.K_r,
                scene_name="main",
            ),
        ),
        shortcut_overlays=(
            ShortcutOverlaySpec(
                attr_name="_shortcut_overlay",
                toggle_action_name="toggle_shortcuts",
                toggle_key=pygame.K_F1,
                toggle_scene_name="main",
            ),
        ),
    )


# Module-level lifecycle spec — holds the factory used by bind/shutdown helpers.
_COUNTER_LIFECYCLE_SPEC = RoutedFeatureLifecycleSpec(
    runtime_spec_factory=_make_counter_runtime_spec,
)


class CounterFeature(RoutedFeature):
    """Manages the counter value and exposes controls and a keyboard shortcut.

    Uses RoutedFeature so that bind_routed_feature_lifecycle can wire the
    ActionHotkeySpec and ShortcutOverlaySpec declared in _COUNTER_LIFECYCLE_SPEC.
    """

    def __init__(self):
        super().__init__("counter", scene_name="main")
        self._count = ObservableValue(0)   # reactive value — drives the label
        self._label = None                  # LabelControl reference
        self._sub = None                    # unsubscribe callable
        self.scheduler = None               # returned by bind_routed_feature_lifecycle

    def build(self, host):
        # Place this feature in the left half of the screen.
        w = host.screen_rect.width // 2
        h = host.screen_rect.height
        panel = host.app.add(
            PanelControl("counter_panel", Rect(0, 0, w, h), draw_background=False),
            scene_name="main",
        )

        # Label displays the current count. Updated reactively via subscription.
        self._label = panel.add(
            LabelControl("count_lbl", Rect(20, 20, w - 40, 56), "Count: 0")
        )

        # Increment button — calls _increment on click.
        panel.add(
            ButtonControl("inc_btn", Rect(20, 90, 160, 40), "Increment",
                          on_click=self._increment)
        )

        # Reset button — calls _reset on click (same method as keyboard reset).
        panel.add(
            ButtonControl("rst_btn", Rect(190, 90, 140, 40), "Reset",
                          on_click=self._reset)
        )

        # Hint label so users know about the keyboard shortcut.
        panel.add(
            LabelControl("hint_lbl", Rect(20, 145, w - 40, 32),
                         "Press R to reset  |  F1 for shortcuts")
        )

    def bind_runtime(self, host):
        # Wire actions, scheduler, and shortcut overlay from the lifecycle spec.
        # This registers the ActionHotkeySpec and ShortcutOverlaySpec automatically.
        self.scheduler = bind_routed_feature_lifecycle(self, host, _COUNTER_LIFECYCLE_SPEC)

        # Subscribe to the count observable. _on_count_changed updates the label
        # and sends a message to ActivityFeature on every change.
        self._sub = self._count.subscribe(self._on_count_changed)

    def shutdown_runtime(self, host):
        # Always unsubscribe before shutdown to prevent stale callbacks.
        if self._sub:
            self._sub()
            self._sub = None

        # Unregisters all actions and event subscriptions declared in the lifecycle spec.
        shutdown_routed_feature_lifecycle(self, host, _COUNTER_LIFECYCLE_SPEC)

    def _increment(self):
        self._count.value += 1

    def _reset(self):
        self._count.value = 0

    def _keyboard_reset(self, _event):
        # Handler passed to ActionHotkeySpec. Receives the raw pygame event.
        self._reset()

    def _on_count_changed(self, new_value: int) -> None:
        # Update our own label (reactive subscription keeps it in sync).
        self._label.text = f"Count: {new_value}"

        # Notify ActivityFeature via the messaging system.
        # send_message enqueues a FeatureMessage on the named feature's queue.
        self.send_message(
            "activity",
            {"event": "changed", "value": new_value, "topic": "count"},
        )


# ---------------------------------------------------------------------------
# ActivityFeature — right panel, displays messages from CounterFeature
# ---------------------------------------------------------------------------

class ActivityFeature(Feature):
    """Receives FeatureMessage notifications and displays recent activity.

    Uses a plain Feature (not RoutedFeature) because it has no action hotkeys.
    It drains its message queue manually in on_update.
    """

    def __init__(self):
        super().__init__("activity", scene_name="main")
        self._status_label = None

    def build(self, host):
        # Place this feature in the right half of the screen.
        x = host.screen_rect.width // 2
        w = host.screen_rect.width // 2
        h = host.screen_rect.height
        panel = host.app.add(
            PanelControl("activity_panel", Rect(x, 0, w, h), draw_background=False),
            scene_name="main",
        )

        panel.add(LabelControl("activity_hdr", Rect(20, 20, w - 40, 32), "Activity Log"))

        self._status_label = panel.add(
            LabelControl("status_lbl", Rect(20, 60, w - 40, 48), "No events yet.")
        )

    def on_update(self, host):
        # Drain all queued messages from CounterFeature.
        # has_messages() / pop_message() are the standard queue-drain pattern.
        while self.has_messages():
            msg = self.pop_message()
            if msg is not None and msg.get("event") == "changed":
                self._status_label.text = f"Last event: count → {msg.get('value')}"


# ---------------------------------------------------------------------------
# Bootstrap — build config and start the application
# ---------------------------------------------------------------------------

# Build the host application config from the declarative spec.
# bootstrap_host_application reads this config and wires every system.
config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1024, 600),
        window_title="Session Dashboard",
        fonts={"default": {"file": "path/to/font.ttf", "size": 14}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(scene_name="main", pretty_name="Main"),
        ),
        feature_entries=(
            ("_counter", CounterFeature),
            ("_activity", ActivityFeature),
        ),
    )
)


class SessionDashboard:
    """Host object. bootstrap_host_application attaches all framework systems to self."""

    def __init__(self):
        bootstrap_host_application(self, config)


if __name__ == "__main__":
    SessionDashboard().app.run_entrypoint(target_fps=60)
```

Run this file (after replacing `"path/to/font.ttf"` with a real path). The left panel shows the counter and buttons. The right panel shows activity messages. Press `R` to reset. Press `F1` to see the shortcut help overlay.

---

## 11. Next Steps

### What to Read Next

[MANUAL.md](MANUAL.md) is the comprehensive reference for every system in gui_do. The sections most relevant to common next steps after this tutorial:

- **§8.1 Application Bootstrap and Host Configuration** — all fields of `HostApplicationBindingSpec`, advanced bootstrap patterns, multi-font configuration, telemetry setup.
- **§8.2 Feature Lifecycle and Feature Types** — full `Feature`, `RoutedFeature`, `LogicFeature`, and `DirectFeature` reference; lifecycle sequencing guarantees; companion features.
- **§8.3 Events, Actions, Input Mapping, and Routing** — the full event dispatch pipeline, action registry, multi-scene routing, key chord sequences.
- **§8.4 State and Observables** — `ObservableList`, `ObservableDict`, `ComputedValue`, `reactive_batch`, `Binding`, `SelectionModel`.

After MANUAL.md, read `demo_features/` — each folder is a living reference pattern showing a complete feature with its own specs, presenter, and logic. The Mandelbrot and Life features demonstrate the `RoutedFeature` + `LogicFeature` companion pattern. The showcase feature demonstrates the control gallery layout system. The system feature demonstrates eight of the newer optional systems.

### What to Explore

- **Overlays** — `DialogManager`, `ToastManager`, `ContextMenuManager`, `CommandPaletteManager`, `TooltipManager` (MANUAL.md §8.8)
- **Persistence** — save and restore workspace state across sessions with `WorkspacePersistenceManager` and versioned snapshot migration (MANUAL.md §8.11)
- **Scene navigation** — multi-scene apps with animated transitions, per-scene routing, and nav actions (`make_scene_nav_action`, `SceneBundleBindingSpec` with `transition_style`)
- **Telemetry** — instrument any system path with `telemetry_collector().span(...)` to measure frame performance (MANUAL.md §8.16)
- **Graphics** — `SceneGraph2D`, `ParticleSystem`, `TileMap`, `OffscreenRenderTarget`, dirty-region rendering (MANUAL.md §8.15)

### Reading the Source

`gui_do/features/data_driven_runtime.py` and `gui_do/features/feature_lifecycle.py` are well-commented and directly readable. Reading them will demystify bootstrap entirely — the bootstrap function is a straightforward sequence of calls that mirrors the spec fields. Understanding the source code of these two files gives you complete mental ownership of the framework's initialization path.
