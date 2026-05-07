# gui_do Tutorial

This tutorial teaches the gui_do programming model by building a complete multi-feature
desktop application from scratch. You will learn how to declare features, wire reactive
state to UI controls, handle keyboard shortcuts declaratively, and compose features that
communicate without coupling directly to each other's internals.

For deeper coverage of any topic, see [MANUAL.md](MANUAL.md).

---

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

`gui_do` is a Python GUI framework built on pygame. It structures applications around
declarative specs, a feature lifecycle, and reactive observable state. Instead of writing
long imperative setup sequences, you describe what your application contains and the framework
wires it together automatically.

### What we will build

The tutorial builds a **Counter Dashboard** — a two-panel desktop application:

- **CounterFeature** (the left panel): displays a live count, provides `+1` and `-1` buttons,
  and supports keyboard shortcuts (`Up` arrow to increment, `Down` arrow to decrement) with a
  shortcut help overlay.
- **HistoryFeature** (the right panel): subscribes to the count and shows the last five changes
  as they happen, updated automatically without polling.

Both features are independent. They share state through an `ObservableValue` published on the
host object, so neither feature holds a direct reference to the other.

### Prerequisites

- Python 3.10 or later
- `pygame` and `numpy` installed
- No prior GUI framework experience required
- Basic Python class and function knowledge is sufficient

Whenever this tutorial mentions a system briefly, [MANUAL.md](MANUAL.md) has a full chapter on it.

---

## 2. Core Concepts

Before writing code, three ideas are worth understanding clearly. They appear in every gui_do
application and explain why the framework is structured the way it is.

### Declarative specs vs imperative wiring

Most GUI toolkits ask you to write code that creates objects, attaches handlers, and configures
systems in a specific order. That code is fragile — the order matters, objects must exist before
they can be referenced, and adding a new component means modifying the startup sequence.

`gui_do` inverts this: you write data objects called **specs** that describe what your
application contains. The bootstrap system reads those specs and builds all the connections.
Features never need to import each other or know what order they will be initialized in.

The core spec hierarchy:

- `HostApplicationBindingSpec` — the top-level declaration for a complete application
- `SceneBundleBindingSpec` — declares one scene with transition style and escape behavior
- `FeatureSpec` — declares one feature class and how to instantiate it
- `ActionSpec` / `ActionHotkeySpec` — declares a named action and optional keyboard binding

When `build_host_application_config` processes these specs, it produces a `HostApplicationConfig`.
When `bootstrap_host_application` processes that config, it initializes all systems and registers
all features. Your code then calls `host.app.run_entrypoint(target_fps=60)` to start the frame loop.

### Reactive state

`ObservableValue` is a typed container that holds one value and notifies subscribers when
that value changes. The notification is synchronous: the moment you write `obs.value = 42`,
every subscriber lambda runs before control returns.

```python
from gui_do import ObservableValue

count = ObservableValue(0)

# Subscribe: returns an unsubscribe callable
unsub = count.subscribe(lambda new_val: print(f"count changed to {new_val}"))

count.value = 1   # prints "count changed to 1"
count.value = 2   # prints "count changed to 2"

unsub()           # detach the subscriber
count.value = 3   # nothing prints
```

This eliminates polling. A label's text property is updated by a subscriber, not by code that
reads the count every frame and decides whether to redraw.

For collections, `ObservableList` and `ObservableDict` fire change events when items are
added, removed, or replaced. `ComputedValue` derives a new observable from one or more source
observables and propagates changes automatically.

### Feature lifecycle

Every feature class implements some or all of six lifecycle methods:

| Method | Purpose |
|--------|---------|
| `build(host)` | Construct the feature's control tree. All features complete `build` before any `bind_runtime` runs. |
| `bind_runtime(host)` | Subscribe to observables, bind action handlers, set up any inter-feature communication. |
| `on_update(host)` | Called every frame. Process logic, drain message queues, update non-reactive state. |
| `handle_event(host, event)` | Handle raw input events. Return `True` if the event is consumed. |
| `draw(host, surface, theme)` | Draw directly to the surface (used for custom rendering beyond controls). |
| `shutdown_runtime(host)` | Tear down subscriptions and release resources. Called when the scene is shut down. |

**The key guarantee:** all features in a scene complete `build` before any `bind_runtime` runs.
This means that when `bind_runtime` is called on any feature, the entire control tree for the
scene already exists. Features can safely read `host.some_attribute` set by other features'
`build` methods, without ordering concerns.

Subscriptions are always established in `bind_runtime` and torn down in `shutdown_runtime`.
This is not a convention — it is the correct lifecycle boundary. Controls exist after `build`;
subscriptions need live controls to be meaningful.

---

## 3. Installation and Setup

Install from the repository root (no binary compilation step required):

```
python -m pip install -e . --no-deps
```

`pygame` and `numpy` are required. `numpy` is used internally for pixel buffer operations via
`PixelArray`. Both are listed in `requirements-ci.txt`.

Verify the install:

```
python -c "import gui_do; print(gui_do.__version__)"
```

The minimal set of imports you will use in this tutorial:

```python
from gui_do import (
    # Bootstrap
    HostApplicationBindingSpec, SceneBundleBindingSpec, FeatureSpec,
    build_host_application_config, bootstrap_host_application,
    # Feature types
    Feature, RoutedFeature, LogicFeature,
    # State
    ObservableValue,
    # Controls
    PanelControl, LabelControl, ButtonControl,
    # Routed wiring
    ActionHotkeySpec, ShortcutOverlaySpec,
    RoutedRuntimeSpec, RoutedFeatureLifecycleSpec,
    bind_routed_feature_lifecycle, shutdown_routed_feature_lifecycle,
)
```

### Two startup paths

There are two ways to start a gui_do application:

- **Declarative bootstrap** (recommended, covered in this tutorial): write specs, call
  `build_host_application_config`, then `bootstrap_host_application`. All systems are
  initialized for you.
- **Manual `GuiApplication` construction** (advanced): instantiate `GuiApplication` directly
  and register features, scenes, and actions imperatively. See
  [MANUAL.md — Section 8.1](MANUAL.md#81-application-bootstrap-and-host-configuration)
  for the manual path.

This tutorial uses the declarative bootstrap path throughout.

---

## 4. Your First Feature

We will build the first piece of the Counter Dashboard: a feature that shows a label in the
window. Each step builds on the previous one.

### Step 1: Define the feature class

A `Feature` subclass is the unit of composition in gui_do. It owns a region of the screen and
a set of lifecycle methods. At minimum, `build` constructs the control tree.

```python
import pygame
from pygame import Rect
from gui_do import Feature, PanelControl, LabelControl

class CounterFeature(Feature):
    def __init__(self):
        # Name identifies this feature uniquely; scene_name scopes it to the "main" scene.
        super().__init__("counter", scene_name="main")

    def build(self, host):
        # host.screen_rect is the full display rectangle, set by bootstrap.
        r = host.screen_rect
        # Add a root panel to the "main" scene — covers the left half.
        root = host.app.add(
            PanelControl("counter_root", Rect(0, 0, r.width // 2, r.height),
                         draw_background=True),
            scene_name="main",
        )
        # Add a label inside the panel using absolute screen coordinates.
        self._label = root.add(
            LabelControl("count_lbl", Rect(20, 30, 200, 36), "Count: 0")
        )
```

`Feature` is the right base class here because this feature will have state, controls, and
event interaction. (Section 6 explains when to choose `DirectFeature`, `LogicFeature`, or
`RoutedFeature` instead.)

`build` receives `host` — the application object. Bootstrap sets `host.screen_rect` and
`host.app` before calling `build` on any feature. Controls are not independent widgets; they
are layout nodes inside the feature's region in the scene.

### Step 2: Declare the config

A `HostApplicationBindingSpec` declares the complete application. It requires a display size,
window title, fonts mapping, initial scene name, a list of features, and scene declarations.

```python
from gui_do import (
    FeatureSpec, SceneBundleBindingSpec,
    HostApplicationBindingSpec, build_host_application_config,
)

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1024, 600),
        window_title="Counter Dashboard",
        # fonts maps role names to specs. "default" uses the system font as fallback.
        fonts={"default": {"size": 14}},
        initial_scene_name="main",
        # feature_entries registers feature factories with the host.
        feature_entries=[
            FeatureSpec(attr_name="counter", factory=CounterFeature),
        ],
        # scene_bundle_entries declares scenes. make_initial=True marks this as the
        # starting scene.
        scene_bundle_entries=[
            SceneBundleBindingSpec(scene_name="main", make_initial=True),
        ],
    )
)
```

`FeatureSpec(attr_name="counter", factory=CounterFeature)` tells bootstrap to call
`CounterFeature()` and store the result as `host.counter`. The `attr_name` is how you access
the feature instance on the host from other parts of the application if needed.

`SceneBundleBindingSpec` declares the scene, its transition style, and escape behavior in one
spec. With no transition specified, the default (fade) is used.

### Step 3: Bootstrap and run

```python
from gui_do import bootstrap_host_application

class App:
    def __init__(self):
        bootstrap_host_application(self, config)

App().app.run_entrypoint(target_fps=60)
```

`bootstrap_host_application(host, config)` reads all specs, initializes the display, font
roles, `GuiApplication`, scene transitions, action registry, and more — then calls `build` on
every registered feature. The host object (here, `App()`) receives all initialized attributes
as side-effects (`host.app`, `host.screen_rect`, `host.font_roles`, etc.).

`run_entrypoint(target_fps=60)` starts the frame loop: poll events → dispatch → update
features → draw → flip. It exits cleanly when the window is closed.

### Step 4: Full listing for this step

Running this file produces a window with a panel on the left and a static label reading "Count: 0".

```python
import pygame
from pygame import Rect
from gui_do import (
    Feature, PanelControl, LabelControl,
    FeatureSpec, SceneBundleBindingSpec,
    HostApplicationBindingSpec, build_host_application_config,
    bootstrap_host_application,
)


class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter", scene_name="main")

    def build(self, host):
        r = host.screen_rect
        root = host.app.add(
            PanelControl("counter_root", Rect(0, 0, r.width // 2, r.height),
                         draw_background=True),
            scene_name="main",
        )
        self._label = root.add(
            LabelControl("count_lbl", Rect(20, 30, 200, 36), "Count: 0")
        )


config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1024, 600),
        window_title="Counter Dashboard",
        fonts={"default": {"size": 14}},
        initial_scene_name="main",
        feature_entries=[FeatureSpec(attr_name="counter", factory=CounterFeature)],
        scene_bundle_entries=[SceneBundleBindingSpec(scene_name="main", make_initial=True)],
    )
)


class App:
    def __init__(self):
        bootstrap_host_application(self, config)


App().app.run_entrypoint(target_fps=60)
```

---

## 5. Reactive State: Making the UI Respond

Now we add a button that increments a count, and wire the count to the label so it updates
automatically. This is the core of gui_do's reactive model.

### Step 1: Introduce `ObservableValue`

An `ObservableValue` holds one value. Writing to `.value` synchronously notifies all
subscribers. There is no polling; the label updates the instant the value changes.

Declare it in `build` because the observable's lifetime matches the feature's lifetime —
it should exist for as long as the control tree exists.

```python
from gui_do import ObservableValue

# Inside build:
self._count = ObservableValue(0)
# Expose it on host so other features can subscribe to it.
host.counter_value = self._count
```

### Step 2: Add a button

`ButtonControl` takes an `on_click` callback. The callback is called with no arguments when
the button is activated (mouse click or Enter key when focused).

```python
from gui_do import ButtonControl

# Inside build, after adding the label:
root.add(
    ButtonControl("inc_btn", Rect(20, 90, 100, 36), "+1",
                  on_click=lambda: setattr(self._count, "value", self._count.value + 1))
)
root.add(
    ButtonControl("dec_btn", Rect(130, 90, 100, 36), "-1",
                  on_click=lambda: setattr(self._count, "value", self._count.value - 1))
)
```

### Step 3: Wire the observable to the label

Subscriptions go in `bind_runtime`, not `build`. Here is why: `build` constructs the control
tree, but the observable subscription needs a live control (the label) to update. Both are
ready by the time `bind_runtime` is called — that is the framework's guarantee.

```python
def bind_runtime(self, host):
    # subscribe() returns a callable that removes the subscription.
    self._sub = self._count.subscribe(
        lambda v: setattr(self._label, "text", f"Count: {v}")
    )
```

The lambda receives the new value. It sets `self._label.text`, which triggers a redraw on
the next frame. No other code needs to run; the label always reflects the current count.

### Step 4: Unsubscribe in `shutdown_runtime`

Every subscription set up in `bind_runtime` must be removed in `shutdown_runtime`.
A subscription holds a reference to the feature instance. If you do not remove it, the feature
and its controls remain in memory after the scene shuts down, and the callback may fire into a
stale control tree.

```python
def shutdown_runtime(self, host):
    if self._sub:
        self._sub()      # calling the returned callable removes the subscription
        self._sub = None
```

This pattern — subscribe in `bind_runtime`, store the returned unsubscribe callable, call it in
`shutdown_runtime` — applies to every `ObservableValue`, `ObservableList`, and `ObservableDict`
subscription your feature creates.

### Step 5: Full listing for this step

The count increments and decrements when you click the buttons; the label updates instantly.

```python
import pygame
from pygame import Rect
from gui_do import (
    Feature, PanelControl, LabelControl, ButtonControl, ObservableValue,
    FeatureSpec, SceneBundleBindingSpec,
    HostApplicationBindingSpec, build_host_application_config,
    bootstrap_host_application,
)


class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter", scene_name="main")

    def build(self, host):
        r = host.screen_rect
        # Create the observable and expose it on host for other features.
        self._count = ObservableValue(0)
        host.counter_value = self._count

        root = host.app.add(
            PanelControl("counter_root", Rect(0, 0, r.width // 2, r.height),
                         draw_background=True),
            scene_name="main",
        )
        self._label = root.add(
            LabelControl("count_lbl", Rect(20, 30, 200, 36), "Count: 0")
        )
        root.add(ButtonControl("inc_btn", Rect(20, 90, 100, 36), "+1",
                               on_click=lambda: setattr(self._count, "value",
                                                        self._count.value + 1)))
        root.add(ButtonControl("dec_btn", Rect(130, 90, 100, 36), "-1",
                               on_click=lambda: setattr(self._count, "value",
                                                        self._count.value - 1)))

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
        window_title="Counter Dashboard",
        fonts={"default": {"size": 14}},
        initial_scene_name="main",
        feature_entries=[FeatureSpec(attr_name="counter", factory=CounterFeature)],
        scene_bundle_entries=[SceneBundleBindingSpec(scene_name="main", make_initial=True)],
    )
)


class App:
    def __init__(self):
        bootstrap_host_application(self, config)


App().app.run_entrypoint(target_fps=60)
```

---

## 6. Feature Types

`gui_do` provides four feature base classes. Choosing the right one for each responsibility
keeps your codebase organized and makes the framework's lifecycle guarantees work correctly.

### `Feature`

The standard choice. Provides all six lifecycle stubs (`build`, `bind_runtime`, `on_update`,
`handle_event`, `draw`, `shutdown_runtime`) as no-ops that you override as needed. Use
`Feature` when you are building a visual feature with controls, state, and interaction.

Our `CounterFeature` and `HistoryFeature` are both `Feature` subclasses.

### `DirectFeature`

Full lifecycle control with no default stubs. Use `DirectFeature` when you need to override
only an exact subset of lifecycle methods and want the framework to leave the others
completely empty (no no-op overhead). Rarely needed in practice; `Feature` is correct for
almost all cases.

### `LogicFeature`

No `draw` or control tree. `LogicFeature` is for background computation, cross-feature
coordination, and data pipeline management. Use it when a feature's job is to produce or
transform data rather than to render anything. In the demo application, the `MandelbrotFeature`
offloads computation to companion `LogicFeature` instances that run iterative rendering in
background tasks.

`LogicFeature.on_update` drains a message queue keyed on the `command` field of each
`FeatureMessage`, dispatching to `on_logic_command`. This makes logic features easy to
command from a visual feature without tight coupling.

### `RoutedFeature`

Extends `Feature` with topic-based message dispatch. `on_update` automatically drains the
feature's message queue and dispatches each message to the handler matching its `topic` field.
You declare handlers by overriding `message_handlers()` to return a dict of
`{topic_name: handler_function}`.

`RoutedFeature` is the preferred base class for features that:
- Declare keyboard shortcuts via `ActionHotkeySpec` in a `RoutedRuntimeSpec`
- Show a shortcut help overlay via `ShortcutOverlaySpec`
- Receive typed messages from other features by topic
- Use the cooperative scheduler for background tasks

In the Counter Dashboard, `CounterFeature` becomes a `RoutedFeature` in Section 8 when we
add keyboard shortcuts.

---

## 7. A Second Feature and Feature Communication

The Counter Dashboard needs a second panel that shows a history of recent count changes. This
is `HistoryFeature`. Adding it demonstrates how features can communicate through shared state
without referencing each other directly.

### Step 1: Define the second feature

`HistoryFeature` occupies the right half of the screen. Its `build` creates a panel and a label.
In `bind_runtime`, it subscribes to `host.counter_value` — the observable that `CounterFeature`
published during its own `build`. Because all `build` calls complete before any `bind_runtime`
runs, this ordering is guaranteed by the framework.

```python
class HistoryFeature(Feature):
    def __init__(self):
        super().__init__("history", scene_name="main")
        self._log = []

    def build(self, host):
        r = host.screen_rect
        half = r.width // 2
        root = host.app.add(
            PanelControl("history_root", Rect(half, 0, half, r.height),
                         draw_background=True),
            scene_name="main",
        )
        # Label uses absolute screen coordinates.
        self._log_label = root.add(
            LabelControl("history_lbl", Rect(half + 20, 30, half - 40, 300),
                         "No changes yet")
        )

    def bind_runtime(self, host):
        # host.counter_value was set by CounterFeature.build().
        # The framework guarantees all build() calls are complete before any
        # bind_runtime() runs, so this attribute is always present here.
        self._sub = host.counter_value.subscribe(self._on_count_changed)

    def shutdown_runtime(self, host):
        if self._sub:
            self._sub()
            self._sub = None

    def _on_count_changed(self, new_value):
        self._log.append(f"→ {new_value}")
        # Keep the last 5 changes.
        self._log_label.text = "\n".join(self._log[-5:])
```

### Step 2: Shared state via `ObservableValue` — why this works

`CounterFeature.build` writes `host.counter_value = self._count`. `HistoryFeature.bind_runtime`
reads `host.counter_value`. The host object is the shared namespace — features use it to publish
state they want to share without importing each other. Neither feature needs to know the other
exists; both just know the protocol (`host.counter_value` is an `ObservableValue[int]`).

This is the preferred approach for reactive data: one feature owns the observable, others
subscribe to it. Changes propagate automatically.

### Step 3: Feature messaging — `FeatureMessage`

Sometimes two features should not share a live observable reference. They may live in
different scenes, or the communication is event-driven rather than state-driven. In those
cases, use `FeatureMessage`.

A feature sends a message by calling `self.send_message(target_name, payload_dict)`. The
payload dict should include a `"topic"` key so a `RoutedFeature` receiver can dispatch it
to the right handler.

```python
# Sender (inside some method of CounterFeature):
self.send_message("history", {"topic": "count_changed", "new_value": self._count.value})
```

The receiver — if it is a `RoutedFeature` — declares a handler in `message_handlers()`:

```python
class HistoryFeature(RoutedFeature):
    def message_handlers(self):
        return {"count_changed": self._handle_count_changed}

    def _handle_count_changed(self, host, message):
        new_val = message.get("new_value", 0)
        self._log.append(f"→ {new_val}")
        self._log_label.text = "\n".join(self._log[-5:])
```

`RoutedFeature.on_update` automatically drains the message queue each frame and dispatches
by topic. The sender calls `self.send_message("history", payload)` — the string `"history"`
is the feature's `name` as declared in `__init__`.

**When to use messaging vs shared observables:**

| Shared observable | FeatureMessage |
|---|---|
| State that multiple features react to continuously | One-time events or commands |
| Same scene, guaranteed ordering | Features in different scenes or late-bound |
| Push-on-change semantics | Request-response or fire-and-forget semantics |

For the Counter Dashboard, the shared observable is cleaner. The tutorial's full listing
(Section 10) uses the shared observable approach.

### Step 4: Register the second feature

Add `HistoryFeature` to `feature_entries` in the config:

```python
feature_entries=[
    FeatureSpec(attr_name="counter", factory=CounterFeature),
    FeatureSpec(attr_name="history", factory=HistoryFeature),
],
```

Both features appear in the same scene (`scene_name="main"`), so bootstrap will call their
`build` methods in registration order, then call their `bind_runtime` methods.

---

## 8. Actions and Keyboard Shortcuts

Keyboard shortcuts in gui_do are named actions registered with `ActionManager`. Declaring them
with `ActionHotkeySpec` inside a `RoutedRuntimeSpec` means the framework handles registration
and cleanup automatically. You do not write manual `bind_key` / `unbind_key` calls.

### Step 1: Upgrade CounterFeature to RoutedFeature

Change the base class and add keyboard shortcut support via `RoutedRuntimeSpec`. The spec is
built in a factory method so handlers can reference `self`:

```python
import pygame
from gui_do import RoutedFeature, ActionHotkeySpec, RoutedRuntimeSpec

class CounterFeature(RoutedFeature):
    def __init__(self):
        super().__init__("counter", scene_name="main")
        self._sub = None

    def _build_runtime_spec(self, host):
        # Handlers receive the event object and must return True to mark the action handled.
        return RoutedRuntimeSpec(
            scene_name="main",
            action_hotkeys=(
                ActionHotkeySpec(
                    action_name="counter.increment",
                    handler=lambda event: (setattr(self._count, "value",
                                                   self._count.value + 1), True)[1],
                    key=pygame.K_UP,
                    scene_name="main",
                ),
                ActionHotkeySpec(
                    action_name="counter.decrement",
                    handler=lambda event: (setattr(self._count, "value",
                                                   self._count.value - 1), True)[1],
                    key=pygame.K_DOWN,
                    scene_name="main",
                ),
            ),
        )
```

The `handler` callable receives the triggering `GuiEvent` and returns `True` to signal that
the action consumed the event.

### Step 2: Define the lifecycle spec

The `RoutedFeatureLifecycleSpec` bundles the runtime spec factory with wiring configuration.
It is stored as a module-level constant so `bind_routed_feature_lifecycle` and
`shutdown_routed_feature_lifecycle` can read it:

```python
from gui_do import RoutedFeatureLifecycleSpec

_COUNTER_LIFECYCLE = RoutedFeatureLifecycleSpec(
    runtime_spec_factory=lambda feature, host: feature._build_runtime_spec(host),
    runtime_spec_attr_name="_runtime_spec",
    scheduler_attr_name="scheduler",
)
```

### Step 3: Call bind and shutdown helpers

In `bind_runtime`, call `bind_routed_feature_lifecycle` to register all actions and key
bindings declared in the `RoutedRuntimeSpec`. In `shutdown_runtime`, call
`shutdown_routed_feature_lifecycle` to remove them.

```python
from gui_do import bind_routed_feature_lifecycle, shutdown_routed_feature_lifecycle

def bind_runtime(self, host):
    bind_routed_feature_lifecycle(self, host, _COUNTER_LIFECYCLE)
    self._sub = self._count.subscribe(
        lambda v: setattr(self._label, "text", f"Count: {v}")
    )

def shutdown_runtime(self, host):
    shutdown_routed_feature_lifecycle(self, host, _COUNTER_LIFECYCLE)
    if self._sub:
        self._sub()
        self._sub = None
```

After this change, pressing the `Up` and `Down` arrow keys increments and decrements the
count just as the buttons do.

### Step 4: Add the shortcut help overlay

`ShortcutOverlaySpec` adds a togglable overlay that displays all registered keyboard shortcuts
in the current scene. Add it to the `RoutedRuntimeSpec`:

```python
from gui_do import ShortcutOverlaySpec

# Inside _build_runtime_spec, add shortcut_overlays:
return RoutedRuntimeSpec(
    scene_name="main",
    action_hotkeys=(...),   # as before
    shortcut_overlays=(
        ShortcutOverlaySpec(
            attr_name="_shortcut_overlay",  # attribute name on the feature instance
            toggle_key=pygame.K_F1,
            toggle_scene_name="main",
        ),
    ),
)
```

With this spec in place, pressing `F1` opens and closes the shortcut overlay, which
automatically lists all `action_name` / key pairs registered in the scene — including
`counter.increment` (`Up`) and `counter.decrement` (`Down`).

### Step 5: Full listing for this step

At this point the Counter Dashboard has reactive buttons, keyboard shortcuts, and a shortcut
overlay. The complete listing is in Section 10.

---

## 9. Spec Reference for Builders

This section provides a concise reference for the specs used in this tutorial. For full
field documentation, see [MANUAL.md — Section 8.1](MANUAL.md#81-application-bootstrap-and-host-configuration)
and [Appendix F](MANUAL.md#appendix-f-specifications-and-option-reference).

### `FeatureSpec`

Declares one feature class and how to instantiate it.

```python
FeatureSpec(attr_name="counter", factory=CounterFeature)
```

`attr_name` is the attribute set on the host object to hold the feature instance.
`factory` is a zero-argument callable that returns the feature.

### `SceneBundleBindingSpec`

Declares one scene with its transition style and escape behavior. Combines scene setup,
runtime scene, and optional navigation action into one declaration.

```python
SceneBundleBindingSpec(
    scene_name="main",
    make_initial=True,                          # This is the first scene shown.
    transition_style=SceneTransitionStyle.FADE, # Optional; defaults to fade.
    bind_escape_to_exit=True,                   # Escape key exits the app.
)
```

### `ActionSpec` and `ActionHotkeySpec`

`ActionSpec` declares a named built-in action (exit, scene navigation, palette open).
`ActionHotkeySpec` registers an arbitrary user action with an optional key binding, for use
inside `RoutedRuntimeSpec.action_hotkeys`.

```python
ActionHotkeySpec(
    action_name="counter.increment",  # Unique string identifier for this action.
    handler=lambda event: True,       # Receives GuiEvent; returns True if consumed.
    key=pygame.K_UP,                  # Optional pygame key constant.
    scene_name="main",                # Optional scene scope; None = global.
)
```

### `ShortcutOverlaySpec`

Configures the shortcut discovery overlay for a `RoutedFeature`.

```python
ShortcutOverlaySpec(
    attr_name="_shortcut_overlay",    # Feature instance attribute to hold the overlay.
    toggle_key=pygame.K_F1,           # Key that opens/closes the overlay.
    toggle_scene_name="main",         # Optional scene scope for the toggle key.
    width=600,                        # Overlay width in pixels.
    height=440,                       # Overlay height in pixels.
)
```

### `RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec`

`RoutedRuntimeSpec` is the declarative bundle of runtime wiring for a `RoutedFeature`:
action hotkeys, control key bindings, event subscriptions, shortcut overlays, and the
cooperative scheduler configuration.

`RoutedFeatureLifecycleSpec` wraps the runtime spec and controls how `bind_routed_feature_lifecycle`
resolves it (static spec, factory, or attribute on the feature).

```python
_LIFECYCLE = RoutedFeatureLifecycleSpec(
    runtime_spec_factory=lambda feature, host: feature._build_runtime_spec(host),
    runtime_spec_attr_name="_runtime_spec",
    scheduler_attr_name="scheduler",
)
```

See [MANUAL.md — Section 8.2](MANUAL.md#82-feature-lifecycle-and-feature-types) and
[Section 8.3](MANUAL.md#83-events-actions-input-mapping-and-routing).

### `ToastManager`

To show a toast notification from any feature in `bind_runtime` or an event handler:

```python
host.app.toasts.show("Action completed", severity=ToastSeverity.INFO)
```

`host.app.toasts` is the `ToastManager` instance. `ToastSeverity` has `INFO`, `WARNING`,
and `ERROR` variants. See [MANUAL.md — Section 8.8](MANUAL.md#88-overlays-dialogs-notifications-and-command-surfaces).

---

## 10. Complete Project Listing

The following is the full, runnable Counter Dashboard built throughout this tutorial. It
requires `pygame`, `numpy`, and `gui_do` installed.

```python
"""
Counter Dashboard — complete gui_do tutorial project.

Two features share state through an ObservableValue on the host:
  - CounterFeature: RoutedFeature with +/- buttons and keyboard shortcuts.
  - HistoryFeature: Feature that subscribes to counter changes and logs them.
"""

import pygame
from pygame import Rect

from gui_do import (
    # Bootstrap
    FeatureSpec,
    SceneBundleBindingSpec,
    HostApplicationBindingSpec,
    build_host_application_config,
    bootstrap_host_application,
    # Feature base classes
    Feature,
    RoutedFeature,
    # State
    ObservableValue,
    # Controls
    PanelControl,
    LabelControl,
    ButtonControl,
    # Routed wiring
    ActionHotkeySpec,
    ShortcutOverlaySpec,
    RoutedRuntimeSpec,
    RoutedFeatureLifecycleSpec,
    bind_routed_feature_lifecycle,
    shutdown_routed_feature_lifecycle,
)


# ─── Lifecycle spec for CounterFeature ────────────────────────────────────────
#
# RoutedFeatureLifecycleSpec bundles how the runtime spec is resolved and which
# host attributes receive the scheduler and runtime spec references.
# Using runtime_spec_factory lets handlers reference `self` on the feature instance.

_COUNTER_LIFECYCLE = RoutedFeatureLifecycleSpec(
    runtime_spec_factory=lambda feature, host: feature._build_runtime_spec(host),
    runtime_spec_attr_name="_runtime_spec",
    scheduler_attr_name="scheduler",
)


# ─── CounterFeature ───────────────────────────────────────────────────────────
#
# RoutedFeature adds topic-based message dispatch and integrates cleanly with
# RoutedRuntimeSpec for action hotkeys and the shortcut overlay.

class CounterFeature(RoutedFeature):
    def __init__(self):
        super().__init__("counter", scene_name="main")
        self._count = None
        self._label = None
        self._sub = None
        self.scheduler = None
        self._runtime_spec = None

    def build(self, host):
        # Declare the observable and publish it on host so HistoryFeature can subscribe.
        # All build() calls complete before any bind_runtime() runs — host.counter_value
        # is guaranteed to be present when HistoryFeature.bind_runtime() reads it.
        self._count = ObservableValue(0)
        host.counter_value = self._count

        r = host.screen_rect
        half = r.width // 2

        # Add the left-panel root.
        root = host.app.add(
            PanelControl("counter_root", Rect(0, 0, half, r.height), draw_background=True),
            scene_name="main",
        )

        # Count display — updated reactively by the subscription in bind_runtime.
        self._label = root.add(
            LabelControl("count_lbl", Rect(20, 30, 200, 42), "Count: 0")
        )

        # Increment and decrement buttons with absolute screen coordinates.
        root.add(ButtonControl("inc_btn", Rect(20, 100, 100, 36), "+1",
                               on_click=self._increment))
        root.add(ButtonControl("dec_btn", Rect(130, 100, 100, 36), "-1",
                               on_click=self._decrement))

        # Hint label for the shortcut overlay.
        root.add(LabelControl("hint_lbl", Rect(20, 160, 280, 28),
                              "F1: keyboard shortcuts  |  Up/Down: change count"))

    def _increment(self):
        self._count.value += 1

    def _decrement(self):
        self._count.value -= 1

    def _build_runtime_spec(self, host):
        # Build the RoutedRuntimeSpec here so action handlers can close over self.
        # Handlers receive the GuiEvent and must return True to mark the action consumed.
        return RoutedRuntimeSpec(
            scene_name="main",
            action_hotkeys=(
                ActionHotkeySpec(
                    action_name="counter.increment",
                    handler=lambda event: (self._increment(), True)[1],
                    key=pygame.K_UP,
                    scene_name="main",
                ),
                ActionHotkeySpec(
                    action_name="counter.decrement",
                    handler=lambda event: (self._decrement(), True)[1],
                    key=pygame.K_DOWN,
                    scene_name="main",
                ),
            ),
            shortcut_overlays=(
                ShortcutOverlaySpec(
                    attr_name="_shortcut_overlay",
                    toggle_key=pygame.K_F1,
                    toggle_scene_name="main",
                    width=560,
                    height=360,
                ),
            ),
        )

    def bind_runtime(self, host):
        # Register all action hotkeys and the shortcut overlay declared in the spec.
        bind_routed_feature_lifecycle(self, host, _COUNTER_LIFECYCLE)
        # Wire the observable to the label — subscription runs every time count changes.
        self._sub = self._count.subscribe(
            lambda v: setattr(self._label, "text", f"Count: {v}")
        )

    def shutdown_runtime(self, host):
        # Clean up all registered actions and key bindings from the RoutedRuntimeSpec.
        shutdown_routed_feature_lifecycle(self, host, _COUNTER_LIFECYCLE)
        # Remove the observable subscription to prevent stale callbacks.
        if self._sub:
            self._sub()
            self._sub = None


# ─── HistoryFeature ───────────────────────────────────────────────────────────
#
# Plain Feature — no draw or routing overhead. Subscribes to host.counter_value
# which CounterFeature.build() publishes. The subscription is set up in
# bind_runtime(), which runs after all build() calls are complete.

class HistoryFeature(Feature):
    def __init__(self):
        super().__init__("history", scene_name="main")
        self._log = []
        self._log_label = None
        self._sub = None

    def build(self, host):
        r = host.screen_rect
        half = r.width // 2

        # Right-panel root — starts at the horizontal midpoint.
        root = host.app.add(
            PanelControl("history_root", Rect(half, 0, half, r.height),
                         draw_background=True),
            scene_name="main",
        )

        # Title label for the history panel.
        root.add(LabelControl("history_title", Rect(half + 20, 30, 200, 30),
                              "Recent changes:"))

        # Log label — text is updated by the observable subscription.
        self._log_label = root.add(
            LabelControl("history_log", Rect(half + 20, 80, half - 40, 300),
                         "No changes yet")
        )

    def bind_runtime(self, host):
        # Subscribe to host.counter_value, published by CounterFeature.build().
        # This is safe because all build() calls complete before any bind_runtime() runs.
        self._sub = host.counter_value.subscribe(self._on_count_changed)

    def shutdown_runtime(self, host):
        # Always remove subscriptions to prevent callbacks into a torn-down feature.
        if self._sub:
            self._sub()
            self._sub = None

    def _on_count_changed(self, new_value):
        self._log.append(f"→ {new_value}")
        # Display the most recent five changes.
        self._log_label.text = "\n".join(self._log[-5:])


# ─── Application config ───────────────────────────────────────────────────────
#
# HostApplicationBindingSpec is the top-level declaration. build_host_application_config
# processes it into a HostApplicationConfig that bootstrap_host_application can consume.

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1024, 600),
        window_title="Counter Dashboard",
        # fonts maps role names to specs. "default" falls back to the system font.
        fonts={"default": {"size": 14}},
        initial_scene_name="main",
        # Register both features. Bootstrap calls CounterFeature() and HistoryFeature()
        # and stores the instances as host.counter and host.history respectively.
        feature_entries=[
            FeatureSpec(attr_name="counter", factory=CounterFeature),
            FeatureSpec(attr_name="history", factory=HistoryFeature),
        ],
        # Declare the "main" scene as the starting scene.
        scene_bundle_entries=[
            SceneBundleBindingSpec(scene_name="main", make_initial=True),
        ],
    )
)


# ─── Entry point ──────────────────────────────────────────────────────────────
#
# The App object is the host. bootstrap_host_application sets host.app, host.screen_rect,
# host.counter, host.history, and all other bootstrap-time attributes as side-effects.
# run_entrypoint starts the frame loop: poll → dispatch → update → draw → flip.

class App:
    def __init__(self):
        bootstrap_host_application(self, config)


App().app.run_entrypoint(target_fps=60)
```

**What this listing demonstrates:**

- `CounterFeature` (RoutedFeature) owns the count observable and publishes it on host.
- `HistoryFeature` (Feature) subscribes without importing or referencing `CounterFeature`.
- Keyboard shortcuts (`Up`, `Down`) are declared in `RoutedRuntimeSpec` and cleaned up
  automatically by `shutdown_routed_feature_lifecycle`.
- The shortcut overlay opens with `F1` and lists all registered shortcuts.
- Both features tear down their subscriptions cleanly in `shutdown_runtime`.
- The frame loop, event routing, focus management, and scene lifecycle are all framework-managed.

---

## 11. Next Steps

### Read next

- **[MANUAL.md](MANUAL.md)** — the complete developer reference. Start with the Quickstart
  Path (Section 3), then read the Core Workflow chapter (Section 5), then the system chapters
  most relevant to what you are building.
- **`demo_features/`** — living reference patterns for the full bootstrap flow, window
  presentation models, the cooperative scheduler, and complex multi-feature scenes.

### MANUAL.md sections most useful after this tutorial

| Section | Topic |
|---------|--------|
| [8.1 Bootstrap](MANUAL.md#81-application-bootstrap-and-host-configuration) | Full HostApplicationBindingSpec field reference and advanced config |
| [8.2 Feature Lifecycle](MANUAL.md#82-feature-lifecycle-and-feature-types) | DirectFeature, LogicFeature, companion features, and message dispatch |
| [8.3 Events and Actions](MANUAL.md#83-events-actions-input-mapping-and-routing) | Input map, key chord manager, middleware, and event routing rules |
| [8.4 State and Observables](MANUAL.md#84-state-and-observables) | ObservableList, ObservableDict, ComputedValue, reactive_batch |
| [8.8 Overlays](MANUAL.md#88-overlays-dialogs-notifications-and-command-surfaces) | Dialog, toast, context menu, command palette, and tooltip integration |
| [8.11 Persistence](MANUAL.md#811-persistence-and-workspacesession-state) | WorkspacePersistenceManager, versioned snapshots, restore reports |

### What to explore from here

- **Overlays**: add a `DialogManager` confirmation dialog or `ToastManager` notifications
  to your features.
- **Persistence**: save the counter value across runs using `WorkspacePersistenceManager`
  and the `SnapshotMigrator`.
- **Scene navigation**: add a second scene and a `SceneBundleBindingSpec` with a
  `SceneTransitionStyle` to animate between them.
- **Telemetry**: wrap expensive sections with `telemetry_collector().span(...)` to profile
  frame-time distribution.
- **Graphics**: use `CanvasControl` and `DrawContext` for custom rendering inside a feature,
  or add a `ParticleSystem` to the scene.

### Reading the source

`gui_do/features/data_driven_runtime.py` and `gui_do/features/feature_lifecycle.py` are
readable and well-commented. Reading them will demystify bootstrap completely — the 32-tier
public API reduces to a few hundred lines of setup logic, and every spec field maps directly
to a call you can trace through.
