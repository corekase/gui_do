# gui_do Tutorial

This tutorial teaches the gui_do programming model by building a complete two-feature interactive application from scratch. Every section explains both **how** to write the code and **why** gui_do is designed that way. By the end, you will understand the full lifecycle, reactive state, declarative wiring, keyboard actions, and clean teardown well enough to build your own gui_do applications.

For the complete API reference on any topic covered here, see [MANUAL.md](MANUAL.md).

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

gui_do is a Python GUI framework built on pygame. It organizes applications as collections of **features** — self-contained units that each own a slice of the screen, a set of controls, and a clear lifecycle. A declarative spec layer describes which features belong to which scenes; the bootstrap system reads those specs and wires everything together automatically.

**What we will build:** the **Counter Dashboard** — a two-panel monitoring application with:

- **CounterFeature**: owns a counter label that updates reactively, an increment button, and a keyboard shortcut that also increments.
- **LogFeature**: displays the most recent activity from CounterFeature, updated automatically whenever the counter changes.

The two features never import each other. CounterFeature exposes a public observable; LogFeature subscribes to it in `bind_runtime`. The bootstrap arranges both features in the same scene.

**Prerequisites:** Python 3.10+, `pygame`, `numpy`. No GUI framework experience required. Install instructions are in Section 3.

For deeper coverage of any topic introduced here, see [MANUAL.md](MANUAL.md).

---

## 2. Core Concepts

Before any code, three ideas are worth understanding clearly. They explain almost every design decision in gui_do.

### Declarative specs vs. imperative wiring

In most GUI frameworks you write imperative sequences: create a window, add a button, register an event handler, connect it to a callback. Every step depends on the previous one, so features must know about each other's internals.

gui_do uses **specs** instead. A spec is a plain data object that describes what your application contains: "there is a scene named `main`; it contains `CounterFeature` and `LogFeature`." The bootstrap system reads these specs and performs all wiring automatically. Features never call each other's constructors and never know which other features are present in their scene.

The benefit: you can add, remove, or reorder features by changing a one-line spec entry, not a tangled call sequence.

### Reactive state

An `ObservableValue` is a value that notifies subscribers when it changes. Instead of polling a variable every frame to check whether it has changed, you subscribe once:

```python
from gui_do import ObservableValue

count = ObservableValue(0)

def on_change(v: int) -> None:
    print(f"count changed to {v}")

unsub = count.subscribe(on_change)  # returns a callable that cancels the subscription
count.value = 5                     # prints "count changed to 5"

unsub()                             # cancel the subscription; on_change is never called again
```

Setting `.value` fires all registered callbacks synchronously. `ObservableList` and `ObservableDict` work the same way for collections, firing on append, pop, insert, and key assignment. `ComputedValue` derives a new observable from one or more existing observables and updates automatically when any dependency changes.

### Feature lifecycle

Every feature passes through the same ordered phases, called by the framework in the correct sequence:

| Phase | When called | Purpose |
|---|---|---|
| `build(host)` | Once, during scene construction | Create controls and add them to the scene tree |
| `bind_runtime(host)` | After **all** features in the scene finish `build` | Subscribe to observables, register callbacks, wire cross-feature interactions |
| `on_update(host)` | Each frame | Optional per-frame logic |
| `draw(host, surface, theme)` | Each frame | Optional custom rendering |
| `shutdown_runtime(host)` | On scene exit | Cancel subscriptions, release resources |

The critical guarantee: every feature's `build` completes before any feature's `bind_runtime` runs. This means that in `bind_runtime`, all sibling features already exist and their controls are fully built. Cross-feature wiring belongs in `bind_runtime`, not `build`.

Subscriptions set up in `bind_runtime` must be cancelled in `shutdown_runtime`. Failing to do so causes memory leaks and callbacks firing after the feature is gone.

---

## 3. Installation and Setup

Install from the repository root with:

```
python -m pip install -e . --no-deps
```

The `-e` flag installs in editable mode so source changes are reflected immediately. `--no-deps` skips resolving binary dependencies you may already have installed separately.

Requires `pygame` and `numpy`. numpy is used internally for pixel buffer operations via `PixelArray`.

Verify the installation:

```
python -c "import gui_do; print(gui_do.__version__)"
```

The minimal imports to start building:

```python
from gui_do import (
    Feature,
    HostApplicationBindingSpec,
    SceneBundleBindingSpec,
    FeatureSpec,
    build_host_application_config,
    bootstrap_host_application,
)
```

**Two startup paths.** This tutorial uses the declarative bootstrap (recommended for all new applications): build a `HostApplicationBindingSpec`, pass it to `build_host_application_config`, and call `bootstrap_host_application`. The alternative — constructing `GuiApplication` manually — is covered in MANUAL.md §8.1 for advanced use cases.

---

## 4. Your First Feature

*Narrative: build CounterFeature, the first panel of the Counter Dashboard.*

### Step 1 — Define the feature class

A `Feature` subclass is the fundamental unit of gui_do. It owns a region of the screen and manages its controls. `build` is where the control tree is constructed.

We use `Feature` here rather than `DirectFeature`, `LogicFeature`, or `RoutedFeature` because this is a visual feature with controls and state — the standard case. The other types are covered in Section 6.

```python
from gui_do import Feature


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")

    def build(self, host) -> None:
        pass  # controls added in the next step
```

The string `"counter_feature"` is the feature's identity key. `scene_name="main"` declares which scene this feature belongs to. The bootstrap uses this to route the feature to the right scene.

The `__init__` takes no user-facing arguments so the feature can be used as a zero-argument factory — required by `FeatureSpec`.

### Step 2 — Add controls

Controls are pixel-positioned within the window surface. `host.screen_rect` gives the full window bounds as a `pygame.Rect`. `host.app.add(control, scene_name=...)` registers the control with the application's scene tree.

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
        pass  # wired to the observable in the next section
```

`LabelControl(control_id, rect, text)` creates a text label. `ButtonControl(control_id, rect, text, on_click=...)` creates a clickable button. The `on_click` callback is called with no arguments when the button is activated.

### Step 3 — Declare the config

`HostApplicationBindingSpec` is the top-level spec. `SceneBundleBindingSpec` declares a named scene. `FeatureSpec` declares a feature class and the host attribute it will be stored under.

```python
from gui_do import (
    FeatureSpec,
    HostApplicationBindingSpec,
    SceneBundleBindingSpec,
    build_host_application_config,
)


config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(800, 200),
        window_title="Counter Dashboard",
        fonts={"default": {"size": 14}},
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

`build_host_application_config` merges the binding spec into a `HostApplicationConfig` that the bootstrap can consume. You never construct `HostApplicationConfig` fields manually.

`make_initial=True` marks this as the first scene shown. `bind_escape_to_exit=True` wires Escape to an exit action for this scene.

`FeatureSpec(attr_name="counter_feature", factory=CounterFeature)` tells the bootstrap to call `CounterFeature()` and attach the result to `host.counter_feature`.

### Step 4 — Bootstrap and run

`bootstrap_host_application` reads the config, initializes all systems, and populates the host object. `run_entrypoint` starts the frame loop.

```python
import pygame
from gui_do import bootstrap_host_application


class Host:
    pass


if __name__ == "__main__":
    pygame.init()
    host = Host()
    bootstrap_host_application(host, config)
    host.app.run_entrypoint(target_fps=60)
```

`Host` is a plain Python class. `bootstrap_host_application` attaches attributes to it: `host.app`, `host.screen_rect`, `host.font_roles`, `host.action_registry`, `host.counter_feature`, and more. After bootstrap, `host.app.run_entrypoint(target_fps=60)` runs the event-loop until the window is closed.

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


config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(800, 200),
        window_title="Counter Dashboard",
        fonts={"default": {"size": 14}},
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

Run this and you will see a window with a label and a button. The button does nothing yet — that is Section 5.

---

## 5. Reactive State: Making the UI Respond

*Narrative: wire the counter's observable to the label so it updates automatically.*

### Step 1 — Introduce `ObservableValue`

An `ObservableValue` is a value holder that fires callbacks when `.value` changes. Declare one on the feature in `__init__`:

```python
from gui_do import Feature, ObservableValue


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self.count = ObservableValue(0)  # public: other features can subscribe
        self._sub = None                 # holds the unsubscribe callable
```

`self.count` is public so `LogFeature` (added in Section 7) can subscribe to it in `bind_runtime`.

### Step 2 — Wire the button

`_increment` sets `.value`, which fires all subscribers:

```python
    def _increment(self) -> None:
        self.count.value += 1
```

### Step 3 — Wire the observable to the label in `bind_runtime`

Subscriptions must be set up in `bind_runtime`, not `build`. In `build`, the control tree is being constructed; in `bind_runtime`, all controls in the scene already exist and all cross-feature references are safe to use.

```python
    def bind_runtime(self, host) -> None:
        self._sub = self.count.subscribe(
            lambda v: setattr(self._label, "text", f"Count: {v}")
        )
```

`subscribe` returns a callable that cancels the subscription. Store it in `self._sub`.

### Step 4 — Unsubscribe in `shutdown_runtime`

Every subscription set up in `bind_runtime` must be cancelled in `shutdown_runtime`. Subscriptions hold references; failing to cancel them causes callbacks to fire after the feature is gone and prevents garbage collection.

```python
    def shutdown_runtime(self, host) -> None:
        if self._sub:
            self._sub()
            self._sub = None
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
        self._sub = None

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
        self._sub = self.count.subscribe(
            lambda v: setattr(self._label, "text", f"Count: {v}")
        )

    def shutdown_runtime(self, host) -> None:
        if self._sub:
            self._sub()
            self._sub = None

    def _increment(self) -> None:
        self.count.value += 1


config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(800, 200),
        window_title="Counter Dashboard",
        fonts={"default": {"size": 14}},
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

Click the button — the label updates immediately. No polling, no frame check, no explicit redraw call.

---

## 6. Feature Types

gui_do provides four feature types. Use the simplest one that fits the feature's role:

**`Feature`** — the standard choice. Provides all lifecycle method stubs (`build`, `bind_runtime`, `on_update`, `draw`, `shutdown_runtime`) with default no-op implementations. Use this for any visual feature with controls, state, and user interaction. CounterFeature and LogFeature are both plain `Feature` instances until Section 8.

**`DirectFeature`** — no default method stubs; every method you override must be implemented fully. Use when you need precise control over which lifecycle hooks are present. Rarely needed.

**`LogicFeature`** — no `draw` or control tree. Use for background computation, cross-feature coordination, event processing, or data pipeline management that has no visual representation of its own.

**`RoutedFeature`** — extends `Feature` with topic-based message dispatch. Use when you want to wire hotkeys, shortcut overlays, and event subscriptions declaratively via `RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec`. The routed lifecycle helpers (`bind_routed_feature_lifecycle` / `shutdown_routed_feature_lifecycle`) handle all binding and unbinding automatically. We will promote `CounterFeature` to a `RoutedFeature` in Section 8 to add a keyboard shortcut.

For the Counter Dashboard: both features are plain `Feature` until Section 8, when we promote `CounterFeature` to `RoutedFeature` to add a keyboard shortcut and a shortcut-help overlay.

See MANUAL.md §8.2 for the complete feature type reference.

---

## 7. A Second Feature and Feature Communication

*Narrative: add LogFeature, the second panel of the Counter Dashboard.*

### Step 1 — Define LogFeature

`LogFeature` owns two controls: a header label and an activity label. Its responsibility is to display what CounterFeature reports.

```python
from pygame import Rect
from gui_do import Feature, LabelControl


class LogFeature(Feature):
    def __init__(self) -> None:
        super().__init__("log_feature", scene_name="main")
        self._log_label = None
        self._sub = None

    def build(self, host) -> None:
        host.app.add(
            LabelControl("log_header", Rect(24, 120, 300, 24), "Activity Log"),
            scene_name="main",
        )
        self._log_label = host.app.add(
            LabelControl("log_entry", Rect(24, 148, 300, 32), "No activity yet."),
            scene_name="main",
        )
```

### Step 2 — Shared state via `ObservableValue`

In `bind_runtime`, LogFeature accesses CounterFeature's public observable through the host. This works because `bootstrap_host_application` attaches each feature to the host under its `FeatureSpec.attr_name`, and `bind_runtime` is called after all features are registered.

```python
    def bind_runtime(self, host) -> None:
        # host.counter_feature is set by bootstrap from FeatureSpec(attr_name="counter_feature", ...)
        counter = host.counter_feature
        self._sub = counter.count.subscribe(
            lambda v: setattr(self._log_label, "text", f"Counter changed \u2192 {v}")
        )

    def shutdown_runtime(self, host) -> None:
        if self._sub:
            self._sub()
            self._sub = None
```

This is the recommended approach when two features share observable state and one is clearly the "owner." The owning feature exposes a public observable; consumers subscribe to it in `bind_runtime`.

### Step 3 — Feature messaging (the alternative)

When features should not hold direct references to each other — for example, in a large application where features are loaded independently — use `FeatureMessage` to communicate via `host.app.features.send_message`:

```python
from gui_do import FeatureMessage

# In CounterFeature._increment, after updating the count:
host.app.features.send_message(
    "counter_feature",       # sender
    "log_feature",           # target
    {"topic": "count_changed", "count": self.count.value},
)
```

The target feature receives the message in its `on_message` method (available on `RoutedFeature`). For the Counter Dashboard, the direct observable approach is simpler and cleaner, so we use it here.

### Step 4 — Updated full listing

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
        self._sub = None

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
        self._sub = self.count.subscribe(
            lambda v: setattr(self._label, "text", f"Count: {v}")
        )

    def shutdown_runtime(self, host) -> None:
        if self._sub:
            self._sub()
            self._sub = None

    def _increment(self) -> None:
        self.count.value += 1


class LogFeature(Feature):
    def __init__(self) -> None:
        super().__init__("log_feature", scene_name="main")
        self._log_label = None
        self._sub = None

    def build(self, host) -> None:
        host.app.add(
            LabelControl("log_header", Rect(24, 120, 300, 24), "Activity Log"),
            scene_name="main",
        )
        self._log_label = host.app.add(
            LabelControl("log_entry", Rect(24, 148, 300, 32), "No activity yet."),
            scene_name="main",
        )

    def bind_runtime(self, host) -> None:
        counter = host.counter_feature
        self._sub = counter.count.subscribe(
            lambda v: setattr(self._log_label, "text", f"Counter changed \u2192 {v}")
        )

    def shutdown_runtime(self, host) -> None:
        if self._sub:
            self._sub()
            self._sub = None


config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(800, 260),
        window_title="Counter Dashboard",
        fonts={"default": {"size": 14}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(scene_name="main", make_initial=True, bind_escape_to_exit=True),
        ),
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

Now both panels update when the button is clicked. The log label is driven by the same `count` observable as the counter label — one increment triggers both.

---

## 8. Actions and Keyboard Shortcuts

*Narrative: promote CounterFeature to a RoutedFeature, add a `+` keyboard shortcut, and add a shortcut-help overlay.*

### Step 1 — Understand the action wiring

In gui_do, an **action** is a named operation with a handler callable. `ActionHotkeySpec` registers an action name, its handler, and an optional key binding. The `RoutedRuntimeSpec` groups these specs together; `bind_routed_feature_lifecycle` activates them all in a single call; `shutdown_routed_feature_lifecycle` tears them all down cleanly.

This eliminates scattered `register_action` / `unbind_key` calls spread across `bind_runtime` and `shutdown_runtime`.

### Step 2 — Promote CounterFeature to `RoutedFeature`

Change the base class and build the lifecycle spec in `__init__`, where `self._increment` is available as a callable:

```python
import pygame
from gui_do import (
    RoutedFeature,
    RoutedRuntimeSpec,
    RoutedFeatureLifecycleSpec,
    ActionHotkeySpec,
    ShortcutOverlaySpec,
    bind_routed_feature_lifecycle,
    shutdown_routed_feature_lifecycle,
    ObservableValue,
)


class CounterFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self.count = ObservableValue(0)
        self._sub = None
        # Build the lifecycle spec here so self._increment is available as a handler reference.
        self._lifecycle_spec = RoutedFeatureLifecycleSpec(
            runtime_spec=RoutedRuntimeSpec(
                scene_name="main",
                action_hotkeys=(
                    ActionHotkeySpec(
                        action_name="increment",
                        handler=self._increment,
                        key=pygame.K_PLUS,
                        scene_name="main",
                    ),
                ),
                shortcut_overlays=(
                    ShortcutOverlaySpec(
                        attr_name="_shortcut_overlay",
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
        )
```

### Step 3 — Wire via `bind_routed_feature_lifecycle`

Replace the manual subscription calls with one call to `bind_routed_feature_lifecycle`:

```python
    def bind_runtime(self, host) -> None:
        self._sub = self.count.subscribe(
            lambda v: setattr(self._label, "text", f"Count: {v}")
        )
        # One call wires the + hotkey and the F1 shortcut overlay.
        bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)

    def shutdown_runtime(self, host) -> None:
        shutdown_routed_feature_lifecycle(self, host, self._lifecycle_spec)
        if self._sub:
            self._sub()
            self._sub = None
```

`bind_routed_feature_lifecycle` reads the `RoutedRuntimeSpec`, registers the `increment` action with the `+` key, creates the shortcut overlay, and registers the F1 toggle — all automatically. `shutdown_routed_feature_lifecycle` undoes all of it.

### Step 4 — Handler signature for action handlers

Action handlers registered via `ActionHotkeySpec` are called with one argument — the triggering event (which may be `None` for programmatic calls). Update `_increment` to accept an optional event parameter:

```python
    def _increment(self, _event=None) -> None:
        self.count.value += 1
```

### Step 5 — Updated full listing

```python
import pygame
from pygame import Rect

from gui_do import (
    ActionHotkeySpec,
    ButtonControl,
    Feature,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    ObservableValue,
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


class CounterFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self.count = ObservableValue(0)
        self._sub = None
        self._lifecycle_spec = RoutedFeatureLifecycleSpec(
            runtime_spec=RoutedRuntimeSpec(
                scene_name="main",
                action_hotkeys=(
                    ActionHotkeySpec(
                        action_name="increment",
                        handler=self._increment,
                        key=pygame.K_PLUS,
                        scene_name="main",
                    ),
                ),
                shortcut_overlays=(
                    ShortcutOverlaySpec(
                        attr_name="_shortcut_overlay",
                        action_registry_attr="action_registry",
                        toggle_action_name="show_help",
                        toggle_key=pygame.K_F1,
                        manual_shortcut_lines=(
                            "+: Increment counter",
                            "F1: Show this help overlay",
                            "Escape: Exit",
                        ),
                        prepend_manual_shortcuts=True,
                    ),
                ),
            )
        )

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
        self._sub = self.count.subscribe(
            lambda v: setattr(self._label, "text", f"Count: {v}")
        )
        bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)

    def shutdown_runtime(self, host) -> None:
        shutdown_routed_feature_lifecycle(self, host, self._lifecycle_spec)
        if self._sub:
            self._sub()
            self._sub = None

    def _increment(self, _event=None) -> None:
        self.count.value += 1


class LogFeature(Feature):
    def __init__(self) -> None:
        super().__init__("log_feature", scene_name="main")
        self._log_label = None
        self._sub = None

    def build(self, host) -> None:
        host.app.add(
            LabelControl("log_header", Rect(24, 120, 300, 24), "Activity Log"),
            scene_name="main",
        )
        self._log_label = host.app.add(
            LabelControl("log_entry", Rect(24, 148, 300, 32), "No activity yet."),
            scene_name="main",
        )

    def bind_runtime(self, host) -> None:
        counter = host.counter_feature
        self._sub = counter.count.subscribe(
            lambda v: setattr(self._log_label, "text", f"Counter changed \u2192 {v}")
        )

    def shutdown_runtime(self, host) -> None:
        if self._sub:
            self._sub()
            self._sub = None


config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(800, 260),
        window_title="Counter Dashboard",
        fonts={"default": {"size": 14}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(scene_name="main", make_initial=True, bind_escape_to_exit=True),
        ),
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

Press `+` to increment. Press `F1` to see the shortcut overlay. Press `Escape` to exit.

---

## 9. Spec Reference for Builders

This section is a concise reference for the specs used throughout the tutorial. For full detail on each, see the linked MANUAL.md section.

### `FeatureSpec`

Declares a feature class and the host attribute it will be assigned to after bootstrap. `factory` must be a zero-argument callable.

```python
from gui_do import FeatureSpec

FeatureSpec(attr_name="counter_feature", factory=CounterFeature)
```

See MANUAL.md §8.2.

### `SceneBundleBindingSpec`

Declares a named scene. `make_initial=True` marks it as the first scene shown. `bind_escape_to_exit=True` wires Escape to exit.

```python
from gui_do import SceneBundleBindingSpec

SceneBundleBindingSpec(scene_name="main", make_initial=True, bind_escape_to_exit=True)
```

See MANUAL.md §8.9.

### `ActionHotkeySpec`

Registers a named action with a handler callable and an optional keyboard key binding. Used inside `RoutedRuntimeSpec.action_hotkeys`.

```python
import pygame
from gui_do import ActionHotkeySpec

ActionHotkeySpec(
    action_name="increment",
    handler=self._increment,   # callable(event_or_None) -> None
    key=pygame.K_PLUS,
    scene_name="main",         # optional: scope the key binding to one scene
)
```

See MANUAL.md §8.3.

### `ShortcutOverlaySpec`

Configures a shortcut-discovery overlay. The overlay is toggled by a registered action name and key. `manual_shortcut_lines` lists the shortcut text to display.

```python
from gui_do import ShortcutOverlaySpec

ShortcutOverlaySpec(
    attr_name="_shortcut_overlay",          # where the overlay is stored on the feature
    action_registry_attr="action_registry", # host attr for the action registry
    toggle_action_name="show_help",         # action name registered to toggle the overlay
    toggle_key=pygame.K_F1,
    manual_shortcut_lines=("+: Increment counter", "F1: Show this help"),
    prepend_manual_shortcuts=True,
)
```

See MANUAL.md §8.8.

### `RoutedRuntimeSpec` + `RoutedFeatureLifecycleSpec`

Bundle a `RoutedFeature`'s runtime wiring into a single data structure. `bind_routed_feature_lifecycle` activates everything; `shutdown_routed_feature_lifecycle` tears it all down.

```python
from gui_do import RoutedRuntimeSpec, RoutedFeatureLifecycleSpec

runtime_spec = RoutedRuntimeSpec(
    scene_name="main",
    action_hotkeys=(...),
    shortcut_overlays=(...),
)
lifecycle_spec = RoutedFeatureLifecycleSpec(runtime_spec=runtime_spec)
```

See MANUAL.md §8.2 and §8.3.

### `ToastManager`

Show a transient notification from any feature that has access to the host:

```python
from gui_do import ToastSeverity

host.app.toasts.show("Counter reset", severity=ToastSeverity.INFO)
```

`ToastManager` is available as `host.app.toasts`. See MANUAL.md §8.8.

---

## 10. Complete Project Listing

The full Counter Dashboard as built through this tutorial. Two features with distinct responsibilities, observable state wired to UI controls, a keyboard action, a shortcut-help overlay, and clean subscription teardown throughout.

```python
import pygame
from pygame import Rect

# ---------------------------------------------------------------------------
# Feature lifecycle and routing
# ---------------------------------------------------------------------------
from gui_do import (
    Feature,
    RoutedFeature,
    RoutedRuntimeSpec,
    RoutedFeatureLifecycleSpec,
    bind_routed_feature_lifecycle,
    shutdown_routed_feature_lifecycle,
)

# ---------------------------------------------------------------------------
# Controls: label and button are sufficient for this project
# ---------------------------------------------------------------------------
from gui_do import (
    ButtonControl,
    LabelControl,
)

# ---------------------------------------------------------------------------
# State: ObservableValue notifies subscribers automatically on .value change
# ---------------------------------------------------------------------------
from gui_do import ObservableValue

# ---------------------------------------------------------------------------
# Actions: ActionHotkeySpec wires an action name to a handler and a key
# ---------------------------------------------------------------------------
from gui_do import ActionHotkeySpec

# ---------------------------------------------------------------------------
# Overlays: ShortcutOverlaySpec shows discoverable keyboard shortcuts
# ---------------------------------------------------------------------------
from gui_do import ShortcutOverlaySpec

# ---------------------------------------------------------------------------
# Bootstrap: specs declare the app structure; bootstrap populates the host
# ---------------------------------------------------------------------------
from gui_do import (
    FeatureSpec,
    HostApplicationBindingSpec,
    SceneBundleBindingSpec,
    build_host_application_config,
    bootstrap_host_application,
)


# ---------------------------------------------------------------------------
# CounterFeature: owns the counter observable, the label, and the button.
# Promoted to RoutedFeature so the + hotkey is declared, not imperative.
# ---------------------------------------------------------------------------
class CounterFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")

        # Public observable: LogFeature subscribes to this in its bind_runtime.
        self.count = ObservableValue(0)
        self._sub = None

        # The lifecycle spec is built here so self._increment is a valid handler.
        # bind_routed_feature_lifecycle reads this spec in bind_runtime and
        # registers the hotkey and overlay automatically.
        self._lifecycle_spec = RoutedFeatureLifecycleSpec(
            runtime_spec=RoutedRuntimeSpec(
                scene_name="main",
                action_hotkeys=(
                    ActionHotkeySpec(
                        action_name="increment",
                        handler=self._increment,
                        key=pygame.K_PLUS,
                        scene_name="main",
                    ),
                ),
                shortcut_overlays=(
                    ShortcutOverlaySpec(
                        attr_name="_shortcut_overlay",
                        action_registry_attr="action_registry",
                        toggle_action_name="show_help",
                        toggle_key=pygame.K_F1,
                        manual_shortcut_lines=(
                            "+: Increment counter",
                            "F1: Show this help overlay",
                            "Escape: Exit",
                        ),
                        prepend_manual_shortcuts=True,
                    ),
                ),
            )
        )

    def build(self, host) -> None:
        # Controls are created and registered here. Subscriptions come later,
        # in bind_runtime, once all sibling features have also completed build.
        self._label = host.app.add(
            LabelControl("count_label", Rect(24, 24, 300, 32), "Count: 0"),
            scene_name="main",
        )
        host.app.add(
            ButtonControl(
                "inc_btn", Rect(24, 68, 160, 32), "Increment (+1)",
                on_click=self._increment,
            ),
            scene_name="main",
        )

    def bind_runtime(self, host) -> None:
        # Wire the observable to the label. The lambda runs every time
        # self.count.value changes, updating the label text with no polling.
        self._sub = self.count.subscribe(
            lambda v: setattr(self._label, "text", f"Count: {v}")
        )
        # One call wires the + hotkey and the F1 shortcut overlay from the spec.
        bind_routed_feature_lifecycle(self, host, self._lifecycle_spec)

    def shutdown_runtime(self, host) -> None:
        # Tear down routed bindings first (hotkey, overlay), then the observable.
        shutdown_routed_feature_lifecycle(self, host, self._lifecycle_spec)
        if self._sub:
            self._sub()
            self._sub = None

    def _increment(self, _event=None) -> None:
        # Called by both the button (no event) and the + hotkey (event passed).
        self.count.value += 1


# ---------------------------------------------------------------------------
# LogFeature: displays the most recent activity from CounterFeature.
# Subscribes to counter.count in bind_runtime; never imports CounterFeature.
# The host attribute "counter_feature" is set by bootstrap from FeatureSpec.
# ---------------------------------------------------------------------------
class LogFeature(Feature):
    def __init__(self) -> None:
        super().__init__("log_feature", scene_name="main")
        self._log_label = None
        self._sub = None

    def build(self, host) -> None:
        host.app.add(
            LabelControl("log_header", Rect(24, 120, 300, 24), "Activity Log"),
            scene_name="main",
        )
        self._log_label = host.app.add(
            LabelControl("log_entry", Rect(24, 148, 300, 32), "No activity yet."),
            scene_name="main",
        )

    def bind_runtime(self, host) -> None:
        # host.counter_feature is available because all features complete build
        # before any feature's bind_runtime runs. This is a framework guarantee.
        counter = host.counter_feature
        self._sub = counter.count.subscribe(
            lambda v: setattr(self._log_label, "text", f"Counter changed \u2192 {v}")
        )

    def shutdown_runtime(self, host) -> None:
        # Cancel the subscription to avoid callbacks firing after teardown.
        if self._sub:
            self._sub()
            self._sub = None


# ---------------------------------------------------------------------------
# Application bootstrap: specs declare the app; build_host_application_config
# resolves them; bootstrap_host_application populates the host object.
# ---------------------------------------------------------------------------
class Dashboard:
    """Minimal host object; bootstrap attaches all attributes to it."""
    pass


CONFIG = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(800, 260),
        window_title="Counter Dashboard",
        fonts={"default": {"size": 14}},
        initial_scene_name="main",
        scene_bundle_entries=(
            # Declare the "main" scene as the initial scene.
            # bind_escape_to_exit wires Escape to an automatic exit action.
            SceneBundleBindingSpec(
                scene_name="main",
                make_initial=True,
                bind_escape_to_exit=True,
            ),
        ),
        feature_entries=(
            # Each FeatureSpec calls factory() and attaches the result to
            # host.{attr_name}. Features are built in declaration order.
            FeatureSpec(attr_name="counter_feature", factory=CounterFeature),
            FeatureSpec(attr_name="log_feature", factory=LogFeature),
        ),
    )
)


if __name__ == "__main__":
    pygame.init()
    host = Dashboard()
    bootstrap_host_application(host, CONFIG)
    host.app.run_entrypoint(target_fps=60)
```

**What this demonstrates:**
- Two features with distinct responsibilities, each owning its own controls and lifecycle
- `ObservableValue` wired to a `LabelControl` via `bind_runtime` subscription
- `RoutedFeatureLifecycleSpec` with `ActionHotkeySpec` and `ShortcutOverlaySpec` for declarative action and overlay wiring
- Cross-feature communication via a public observable (no direct import between features)
- Complete `shutdown_runtime` teardown for every subscription set up in `bind_runtime`

---

## 11. Next Steps

### What to read next

[MANUAL.md](MANUAL.md) is the complete developer reference. After finishing this tutorial, the most relevant sections are:

- **§8.1 Application Bootstrap and Host Configuration** — full `HostApplicationBindingSpec` field reference, telemetry configuration, cursor registration
- **§8.2 Feature Lifecycle and Feature Types** — full lifecycle reference, `DirectFeature`, `LogicFeature`, companion providers, prewarming
- **§8.3 Events, Actions, Input Mapping, and Routing** — `EventBus`, `InputMap`, `KeyChordManager`, advanced action routing
- **§8.4 State and Observables** — `ObservableList`, `ObservableDict`, `ComputedValue`, `reactive_batch`, `Binding`, `CollectionView`
- **§8.8 Overlays, Dialogs, Notifications, and Command Surfaces** — `DialogManager`, `ToastManager`, command palette, context menus, file dialogs

### What to explore in the codebase

**`demo_features/`** contains living reference patterns for every major gui_do subsystem. Each subfolder is one feature package following the established pattern: `__init__.py` is the sole public surface, internal files are organized by concern. Reading `demo_features/systems/` alongside MANUAL.md §8 is an efficient way to see all 10 newer systems in action.

**`gui_do/features/data_driven_runtime.py`** and **`gui_do/features/feature_lifecycle.py`** are readable and well-commented. Working through the bootstrap function in `data_driven_runtime.py` will demystify exactly what `bootstrap_host_application` does and why the lifecycle phases fire in the order they do.

### Topics to explore next

- **Overlays:** `DialogManager`, `ToastManager`, `ContextMenuManager`, command palette — all composable with consistent event routing
- **Persistence:** `WorkspacePersistenceManager`, `SnapshotMigrator` — save and restore workspace state across sessions with versioned migration
- **Scene navigation:** multi-scene applications with animated transitions and per-scene event scoping
- **Telemetry:** `configure_telemetry`, `TelemetryCollector` — performance instrumentation across all feature lifecycle paths
- **Graphics:** `CanvasControl`, `SceneGraph2D`, `ParticleSystem`, `TileMap`, `DirtyRegionTracker` — 2D rendering and animation integration

You are ready to build. Start with [MANUAL.md](MANUAL.md) and use `demo_features/` as your living reference.
