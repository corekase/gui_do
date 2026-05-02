# gui_do Tutorial

A complete beginner's guide to building desktop GUI applications with gui_do.

---

## Table of Contents

1. [Introduction](#1-introduction)
2. [Core Concepts](#2-core-concepts)
   - [Data-Driven Design](#data-driven-design)
   - [Reactive Programming](#reactive-programming)
   - [Feature Lifecycle](#feature-lifecycle)
3. [Installation and Setup](#3-installation-and-setup)
4. [Your First Application — Step by Step](#4-your-first-application--step-by-step)
   - [Step 1: Create a Surface and GuiApplication](#step-1-create-a-surface-and-guiapplication)
   - [Step 2: Define a Feature with a build Hook](#step-2-define-a-feature-with-a-build-hook)
   - [Step 3: Declare the Feature with HostApplicationConfig and FeatureSpec](#step-3-declare-the-feature-with-hostapplicationconfig-and-featurespec)
   - [Step 4: Call bootstrap_host_application](#step-4-call-bootstrap_host_application)
   - [Step 5: Write the Main Run Loop](#step-5-write-the-main-run-loop)
   - [Step 6: Complete Listing](#step-6-complete-listing)
5. [Observable Data and Reactive UI](#5-observable-data-and-reactive-ui)
6. [Feature Types](#6-feature-types)
7. [Feature Messaging](#7-feature-messaging)
8. [Scene Navigation](#8-scene-navigation)
9. [Spec Reference for Beginners](#9-spec-reference-for-beginners)
10. [Complete Example Application](#10-complete-example-application)
11. [Next Steps](#11-next-steps)

---

## 1. Introduction

**gui_do** is a pygame-based GUI framework for building data-driven, feature-oriented desktop applications. Instead of writing hundreds of lines of manual wiring, you describe your application as declarative data structures — called *specs* — and gui_do handles rendering, event routing, scene management, and cross-feature communication automatically.

In this tutorial you will learn the three foundational ideas behind gui_do — data-driven design, reactive programming, and the feature lifecycle — and you will build a complete, runnable application from the first line of code to a finished product with multiple features, reactive state, and scene navigation.

**What you need to know before starting:** Basic Python — functions, classes, and modules. You do not need prior GUI framework experience.

---

## 2. Core Concepts

Before writing code, it is worth understanding the three ideas that everything in gui_do is built on. Each one builds on the previous.

### Data-Driven Design

In a traditional GUI framework you write setup code: create a window, add a button, register a callback, add a label, size it, position it. This is *imperative* setup — you are giving the computer a list of instructions.

gui_do takes a *declarative* approach. You describe what you want as plain Python data structures called *specs*, and gui_do reads those specs and creates the application for you.

**Imperative (without gui_do):**

```python
import pygame
pygame.init()
screen = pygame.display.set_mode((800, 600))
# ... 200 lines of manual control creation, layout, event wiring ...
```

**Declarative (gui_do style):**

```python
from gui_do import HostApplicationConfig, FeatureSpec, SceneSetupSpec, bootstrap_host_application

CONFIG = HostApplicationConfig(
    display_size=(800, 600),
    window_title="My App",
    scene_specs=(SceneSetupSpec(name="main", make_initial=True),),
    feature_specs=(FeatureSpec(attr_name="_my_feature", factory=MyFeature),),
    # ... other declarative settings ...
)

class MyApp:
    def __init__(self):
        bootstrap_host_application(self, CONFIG)
```

The data describes the structure; `bootstrap_host_application` does all the wiring. You focus on what your application does, not how the framework initializes.

### Reactive Programming

Reactive programming means that your UI updates automatically when your data changes. You do not call a refresh function or manually update a label — instead, you store data in *observable* objects, and anything subscribed to them reacts when they change.

gui_do provides three observable types:

- **`ObservableValue`** — A single value that notifies subscribers when it changes.
- **`ObservableList`** — A list that notifies subscribers when items are added, removed, or replaced.
- **`ObservableDict`** — A dictionary that notifies subscribers when entries change.

```python
from gui_do import ObservableValue

score = ObservableValue(0)

# Subscribe: this function runs automatically whenever score changes
score.subscribe(lambda new_value: print(f"Score is now: {new_value}"))

score.value = 10   # prints "Score is now: 10"
score.value = 25   # prints "Score is now: 25"
```

You can also use **`ComputedValue`** to derive a read-only value from one or more observables. It recalculates automatically whenever any of its dependencies change:

```python
from gui_do import ObservableValue, ComputedValue

width = ObservableValue(800)
height = ObservableValue(600)
area = ComputedValue(lambda: width.value * height.value)

area.subscribe(lambda v: print(f"Area: {v}"))
width.value = 1024   # prints "Area: 614400"
```

**Signals** are a lower-level mechanism for one-to-many callbacks, available via `Signal` from the public API. Most beginners will use `ObservableValue.subscribe()` rather than signals directly.

### Feature Lifecycle

A **feature** is a self-contained module that owns a piece of your application — its controls, its data, and its logic. You create a feature by subclassing `Feature` and overriding lifecycle hooks.

The lifecycle hooks are called by gui_do's `FeatureManager` in a well-defined order:

| Hook | When it fires | What to do here |
|---|---|---|
| `build(host)` | Once, during startup | Create controls and add them to the scene |
| `bind_runtime(host)` | Once, after all features are built | Wire observable subscriptions and logic bindings |
| `handle_event(host, event)` | Every input event | Handle keyboard/mouse events; return `True` if consumed |
| `on_update(host)` | Every frame | Update state, drain message queues, run per-frame logic |
| `draw(host, surface, theme)` | Every frame | Custom drawing (most features skip this; controls draw themselves) |

The separation between `build` and `bind_runtime` is important: all features' `build` hooks run first, so by the time `bind_runtime` fires, every feature's controls already exist. This means you can safely subscribe to data owned by another feature in `bind_runtime`.

```python
from gui_do import Feature, LabelControl
from pygame import Rect

class GreetingFeature(Feature):
    def build(self, host) -> None:
        # Create a label and add it to the active scene
        host.app.add(LabelControl("greeting", Rect(20, 20, 300, 30), "Hello, world!"))

    def bind_runtime(self, host) -> None:
        # Wire subscriptions here — all features are built by now
        pass

    def handle_event(self, host, event) -> bool:
        # Return True to consume the event (stop further processing)
        return False

    def on_update(self, host) -> None:
        # Called every frame
        pass
```

---

## 3. Installation and Setup

Install gui_do with pip. gui_do requires Python 3.10+ and pygame.

```
pip install gui_do
```

The minimal set of imports you need to get started:

```python
from gui_do import (
    Feature,
    FeatureSpec,
    HostApplicationConfig,
    SceneSetupSpec,
    RuntimeSceneSpec,
    bootstrap_host_application,
    make_exit_action,
    LabelControl,
    ButtonControl,
    ObservableValue,
)
from pygame import Rect
```

gui_do creates and manages the pygame display surface for you through `bootstrap_host_application`. You do not need to call `pygame.init()` or `pygame.display.set_mode()` manually when using the bootstrap path.

---

## 4. Your First Application — Step by Step

In this section you will build a simple "Hello, world!" application one step at a time.

### Step 1: Create a Surface and GuiApplication

When using `bootstrap_host_application`, gui_do handles surface creation for you. All you need to provide is the desired display size in `HostApplicationConfig`. However, if you ever want to manage the surface yourself, this is how it works:

```python
# Manual surface creation (shown for understanding — bootstrap handles this for you)
import pygame
from gui_do import GuiApplication

pygame.init()
surface = pygame.display.set_mode((800, 600))
app = GuiApplication(surface)
```

In practice you will use the bootstrap path from Step 4 onwards, which handles this automatically.

### Step 2: Define a Feature with a build Hook

A feature is a class that subclasses `Feature`. Give it a unique name in `__init__` and override `build` to create your controls:

```python
from gui_do import Feature, LabelControl
from pygame import Rect

class HelloFeature(Feature):
    def __init__(self):
        super().__init__("hello")  # "hello" is the unique name of this feature

    def build(self, host) -> None:
        # host.app is the GuiApplication
        # host.app.add() adds a control to the currently active scene
        host.app.add(
            LabelControl("hello_label", Rect(20, 20, 400, 40), "Hello, world!")
        )
```

`LabelControl` takes:
- a unique `control_id` string
- a `pygame.Rect` for position and size (x, y, width, height)
- the text to display

### Step 3: Declare the Feature with HostApplicationConfig and FeatureSpec

`HostApplicationConfig` is the single declarative description of your entire application. `FeatureSpec` tells the bootstrap system which features to create:

```python
from gui_do import (
    HostApplicationConfig,
    FeatureSpec,
    SceneSetupSpec,
    RuntimeSceneSpec,
    make_exit_action,
)

CONFIG = HostApplicationConfig(
    display_size=(800, 600),
    window_title="Hello World",
    # Fonts: "window" key seeds the title role used by chrome controls
    fonts={"default": {"system_name": "Arial", "size": 14},
           "window": {"system_name": "Arial"}},
    font_role_specs=({"body": {"size": 14, "font": "default"},
                      "title": {"size": 16, "font": "window"}},),
    cursors=(),
    # Declare scenes
    scene_specs=(SceneSetupSpec(name="main", make_initial=True),),
    # Declare features — factory is a callable that returns the feature instance
    feature_specs=(FeatureSpec(attr_name="_hello", factory=HelloFeature),),
    window_specs=(),
    runtime_scene_specs=(RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),),
    action_specs=(make_exit_action(),),
    static_accessibility_specs=(),
    initial_scene_name="main",
    target_fps=120,
)
```

The `attr_name` in `FeatureSpec` determines which attribute on your host object stores the feature instance (e.g., `host._hello`). The `factory` is called by bootstrap to create the instance.

### Step 4: Call bootstrap_host_application

Create a host class and call `bootstrap_host_application` in its `__init__`:

```python
from gui_do import bootstrap_host_application

class HelloApp:
    def __init__(self):
        # bootstrap_host_application reads CONFIG and:
        # - creates the pygame display
        # - creates GuiApplication (stored as self.app)
        # - instantiates all features and calls build() then bind_runtime()
        # - creates all scenes and registers all actions
        bootstrap_host_application(self, CONFIG)
```

After `bootstrap_host_application` returns, `self.app` is the fully initialized `GuiApplication`.

### Step 5: Write the Main Run Loop

Call `run_entrypoint` on the application. It handles the pygame event loop, frame updates, rendering, and cleanup:

```python
class HelloApp:
    def __init__(self):
        bootstrap_host_application(self, CONFIG)

    def run(self) -> None:
        self.app.run_entrypoint(target_fps=CONFIG.target_fps)

if __name__ == "__main__":
    HelloApp().run()
```

`run_entrypoint` blocks until the application closes. It calls `update()` and `draw()` every frame and processes all pygame events automatically.

### Step 6: Complete Listing

Here is the entire application in one file:

```python
# hello_world.py

from gui_do import (
    Feature,
    FeatureSpec,
    HostApplicationConfig,
    LabelControl,
    RuntimeSceneSpec,
    SceneSetupSpec,
    bootstrap_host_application,
    make_exit_action,
)
from pygame import Rect


class HelloFeature(Feature):
    def __init__(self):
        super().__init__("hello")

    def build(self, host) -> None:
        host.app.add(
            LabelControl("hello_label", Rect(20, 20, 400, 40), "Hello, world!")
        )


CONFIG = HostApplicationConfig(
    display_size=(800, 600),
    window_title="Hello World",
    fonts={"default": {"system_name": "Arial", "size": 14},
           "window": {"system_name": "Arial"}},
    font_role_specs=({"body": {"size": 14, "font": "default"},
                      "title": {"size": 16, "font": "window"}},),
    cursors=(),
    scene_specs=(SceneSetupSpec(name="main", make_initial=True),),
    feature_specs=(FeatureSpec(attr_name="_hello", factory=HelloFeature),),
    window_specs=(),
    runtime_scene_specs=(RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),),
    action_specs=(make_exit_action(),),
    static_accessibility_specs=(),
    initial_scene_name="main",
    target_fps=120,
)


class HelloApp:
    def __init__(self):
        bootstrap_host_application(self, CONFIG)

    def run(self) -> None:
        self.app.run_entrypoint(target_fps=CONFIG.target_fps)


if __name__ == "__main__":
    HelloApp().run()
```

Run it with `python hello_world.py`. You will see an 800×600 window with "Hello, world!" displayed. Press Escape to exit.

---

## 5. Observable Data and Reactive UI

With the basics working, the next step is making your UI respond to changing data. This section shows how to use `ObservableValue` to create a reactive counter.

### ObservableValue — A Single Reactive Value

`ObservableValue` wraps a single value. When you change `.value`, every subscriber is notified:

```python
from gui_do import ObservableValue

count = ObservableValue(0)
count.subscribe(lambda v: print(f"New value: {v}"))

count.value = 1   # prints "New value: 1"
count.value = 2   # prints "New value: 2"
```

The `subscribe` method returns an *unsubscribe callable*. Call it to remove the subscription:

```python
unsubscribe = count.subscribe(lambda v: print(v))
# ... later ...
unsubscribe()  # stop receiving updates
```

### Reading and Writing from a Feature

Features store observables as instance attributes in `build` and wire subscriptions in `bind_runtime`. The separation keeps construction and subscription ordered correctly:

```python
from gui_do import Feature, LabelControl, ButtonControl, ObservableValue
from pygame import Rect

class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter")

    def build(self, host) -> None:
        # Create observable data
        self.count = ObservableValue(0)

        # Create controls
        self.label = host.app.add(
            LabelControl("count_label", Rect(20, 20, 300, 32), "Count: 0")
        )
        host.app.add(ButtonControl(
            "increment",
            Rect(20, 64, 140, 32),
            "+1",
            on_click=self._on_click,
        ))

    def bind_runtime(self, host) -> None:
        # Wire the observable to the label — runs whenever count changes
        self.count.subscribe(
            lambda v: setattr(self.label, "text", f"Count: {v}")
        )

    def _on_click(self) -> None:
        self.count.value += 1
```

Notice: `bind_runtime` uses `setattr(self.label, "text", ...)` because lambda bodies are expressions, not statements. This is a common pattern in gui_do features.

### ObservableList — A Reactive Collection

`ObservableList` notifies subscribers with a `CollectionChange` object whenever the list is modified:

```python
from gui_do import ObservableList

items = ObservableList(["apple", "banana"])
items.subscribe(lambda change: print(f"Changed: {change.kind}"))

items.append("cherry")     # notifies with ChangeKind.INSERT
items.remove("banana")     # notifies with ChangeKind.REMOVE
```

`ObservableList` is useful when you have a `ListViewControl` or `DataGridControl` that should refresh when data changes:

```python
from gui_do import Feature, ListViewControl, ListItem, ObservableList
from pygame import Rect

class TaskListFeature(Feature):
    def __init__(self):
        super().__init__("task_list")

    def build(self, host) -> None:
        self.tasks = ObservableList([
            ListItem("Buy groceries"),
            ListItem("Write tests"),
        ])
        self.list_view = host.app.add(
            ListViewControl("tasks", Rect(20, 20, 300, 240))
        )

    def bind_runtime(self, host) -> None:
        # Refresh list whenever tasks change
        self.tasks.subscribe(
            lambda _: self.list_view.set_items(list(self.tasks))
        )
        # Trigger initial population
        self.list_view.set_items(list(self.tasks))
```

### Signals

A `Signal` is a lower-level pub/sub primitive. You emit it explicitly and subscribers receive any arguments you pass. `ObservableValue` uses signals internally, but you can use `Signal` directly for custom event patterns:

```python
from gui_do import Signal

# Create a signal
on_player_died = Signal()

# Connect a handler
connection = on_player_died.connect(lambda player_id: print(f"Player {player_id} died"))

# Emit — all connected handlers are called
on_player_died.emit(42)   # prints "Player 42 died"

# Disconnect
connection.disconnect()
```

For most data-binding needs, `ObservableValue.subscribe()` is the right tool. Use `Signal` when you need to broadcast a discrete event rather than track a changing value.

---

## 6. Feature Types

gui_do provides four feature types. Each is a subclass of `Feature` and adds specialized behavior for a different role.

### Feature — General Purpose

The base `Feature` class is what you subclass for most work. It provides all lifecycle hooks and inter-feature messaging. Use it whenever your feature creates controls, handles events, and manages state.

```python
from gui_do import Feature

class MyFeature(Feature):
    def __init__(self):
        super().__init__("my_feature")

    def build(self, host) -> None:
        pass  # create controls here

    def bind_runtime(self, host) -> None:
        pass  # wire subscriptions here

    def handle_event(self, host, event) -> bool:
        return False  # return True to consume the event

    def on_update(self, host) -> None:
        pass  # per-frame logic here
```

### FrameTimer — Per-Frame Delta Time

When you need accurate time elapsed between frames inside `on_update`, use `FrameTimer`:

```python
from gui_do import Feature, FrameTimer

class AnimatedFeature(Feature):
    def __init__(self) -> None:
        super().__init__("animated")
        self._timer = FrameTimer()
        self._phase = 0.0

    def on_update(self, host) -> None:
        dt = self._timer.tick()   # Seconds since last call; 0.0 on first call
        self._phase += dt * 2.0   # Advance animation at 2 rad/sec
```

Call `self._timer.reset()` if you want the next `tick()` to return `0.0` again (e.g., after pausing).

### DirectFeature — Custom Rendering

`DirectFeature` is for content that draws directly to the display surface *before* GUI controls composite on top. Use it for visualizations, particle systems, simulations, and canvas-style editors where custom drawing is the primary content.

`DirectFeature` adds three extra hooks:

- `handle_direct_event(host, event)` — Receives events before the control pipeline
- `on_direct_update(host, dt_seconds)` — Per-frame update with delta time in seconds
- `draw_direct(host, surface, theme)` — Draws to the raw surface before controls appear

```python
import pygame
from gui_do import DirectFeature

class BackgroundFeature(DirectFeature):
    def __init__(self):
        super().__init__("background")

    def draw_direct(self, host, surface, theme) -> None:
        # Draw a gradient or custom art directly to the surface
        # Controls will appear on top of this after it returns
        surface.fill((30, 30, 50))
        pygame.draw.circle(surface, (80, 120, 200), (400, 300), 150)
```

### LogicFeature — Pure Logic

`LogicFeature` receives command messages and handles them. It has no draw hook — it is for pure business logic that is completely separate from any UI. Other features send it messages with a `"command"` field, and it processes them.

```python
from gui_do import LogicFeature, FeatureMessage

class CalculatorLogic(LogicFeature):
    def __init__(self):
        super().__init__("calculator")
        self.result = 0

    def on_logic_command(self, host, message: FeatureMessage) -> None:
        if message.command == "add":
            self.result += message.get("value", 0)
        elif message.command == "reset":
            self.result = 0
```

Another feature sends commands to it:

```python
# From inside any other feature's method:
self.send_message("calculator", {"command": "add", "value": 10})
```

`LogicFeature.on_update` automatically drains queued command messages each frame, so you do not need to write the drain loop yourself.

### RoutedFeature — Topic-Based Messaging

`RoutedFeature` is similar to `LogicFeature` but routes messages by *topic* rather than *command*. Override `message_handlers()` to return a dict mapping topic strings to handler methods:

```python
from gui_do import RoutedFeature, FeatureMessage

class EventHub(RoutedFeature):
    def __init__(self):
        super().__init__("event_hub")

    def message_handlers(self):
        return {
            "user.login":  self._on_user_login,
            "user.logout": self._on_user_logout,
        }

    def _on_user_login(self, host, message: FeatureMessage) -> None:
        username = message.get("username", "unknown")
        print(f"{username} logged in")

    def _on_user_logout(self, host, message: FeatureMessage) -> None:
        print("User logged out")
```

Send a routed message using the `"topic"` key:

```python
self.send_message("event_hub", {"topic": "user.login", "username": "alice"})
```

`RoutedFeature.on_update` automatically drains and routes queued messages each frame.

---

## 7. Feature Messaging

Features communicate asynchronously through **messages**. A message is a dict of data sent from one feature to another. The receiving feature processes messages in its `on_update` hook, making inter-feature communication safe across frame boundaries.

### Publishing a Message

Any feature can send a message to another feature by name using `send_message`:

```python
class ButtonFeature(Feature):
    def __init__(self):
        super().__init__("button_panel")

    def build(self, host) -> None:
        host.app.add(ButtonControl(
            "add_btn",
            Rect(20, 20, 140, 32),
            "Add Point",
            on_click=self._on_add_clicked,
        ))

    def _on_add_clicked(self) -> None:
        # Send a message to the "score" feature
        self.send_message("score", {"topic": "add_points", "amount": 10})
```

### Subscribing to Messages

On the receiving side, use `has_messages()` and `pop_message()` in `on_update` to drain messages:

```python
class ScoreFeature(Feature):
    def __init__(self):
        super().__init__("score")

    def build(self, host) -> None:
        self.total = 0
        self.label = host.app.add(
            LabelControl("score_label", Rect(20, 60, 300, 32), "Score: 0")
        )

    def on_update(self, host) -> None:
        while self.has_messages():
            message = self.pop_message()
            if message.get("topic") == "add_points":
                self.total += message.get("amount", 0)
                self.label.text = f"Score: {self.total}"
```

### Practical Example — Counter with Two Features

This example shows a `ButtonFeature` and a `ScoreFeature` communicating through messages:

```python
from gui_do import (
    Feature,
    FeatureSpec,
    HostApplicationConfig,
    LabelControl,
    ButtonControl,
    RuntimeSceneSpec,
    SceneSetupSpec,
    bootstrap_host_application,
    make_exit_action,
)
from pygame import Rect


class ButtonFeature(Feature):
    def __init__(self):
        super().__init__("button_panel")

    def build(self, host) -> None:
        host.app.add(ButtonControl(
            "add_btn", Rect(20, 20, 140, 32), "+10 Points",
            on_click=self._on_click,
        ))

    def _on_click(self) -> None:
        self.send_message("score", {"topic": "add_points", "amount": 10})


class ScoreFeature(Feature):
    def __init__(self):
        super().__init__("score")

    def build(self, host) -> None:
        self.total = 0
        self.label = host.app.add(
            LabelControl("score_label", Rect(20, 70, 300, 32), "Score: 0")
        )

    def on_update(self, host) -> None:
        while self.has_messages():
            msg = self.pop_message()
            if msg.get("topic") == "add_points":
                self.total += msg.get("amount", 0)
                self.label.text = f"Score: {self.total}"
```

---

## 8. Scene Navigation

A **scene** is an isolated context for controls and features. Each scene has its own layout, scheduler, and overlay stack. Use scenes to separate major areas of your application — a main menu, a game screen, a settings screen.

### Declaring Multiple Scenes

Declare scenes with `SceneSetupSpec`. The `make_initial=True` flag marks the scene that opens first:

```python
from gui_do import SceneSetupSpec, SceneTransitionStyle

SCENE_SPECS = (
    SceneSetupSpec(
        name="main",
        pretty_name="Main Menu",
        transition_style=SceneTransitionStyle.SLIDE_LEFT,
        transition_duration=0.4,
        make_initial=True,
    ),
    SceneSetupSpec(
        name="settings",
        pretty_name="Settings",
        transition_style=SceneTransitionStyle.SLIDE_RIGHT,
        transition_duration=0.4,
    ),
)
```

Available transition styles: `FADE`, `SLIDE_LEFT`, `SLIDE_RIGHT`, `SLIDE_UP`, `SLIDE_DOWN`.

### Navigating Between Scenes Using ActionSpec

The simplest way to navigate is to declare a `make_scene_nav_action`. Bootstrap wires it to the action registry and creates a convenience helper on the host:

```python
from gui_do import make_scene_nav_action, make_exit_action

ACTION_SPECS = (
    make_exit_action(),
    make_scene_nav_action("go_settings", label="Open Settings", target_scene="settings"),
    make_scene_nav_action("go_main",     label="Back to Main",  target_scene="main"),
)
```

After bootstrap, `host.go_to_settings()` navigates to the settings scene. Features can also trigger navigation by dispatching the action:

```python
# From inside a feature
host.action_registry.dispatch("go_settings")
```

### Navigating Programmatically

You can also switch scenes directly through the application or the scene transition manager:

```python
# From inside a feature's handle_event or on_update:
host.app.switch_scene("settings")

# Or using the transition manager (with animation):
host.scene_transitions.go("settings")
```

### Scoping a Feature to a Scene

When you create a `Feature`, pass `scene_name` to restrict it to one scene. This feature's controls will only be added to that scene:

```python
class SettingsFeature(Feature):
    def __init__(self):
        super().__init__("settings_ui", scene_name="settings")

    def build(self, host) -> None:
        # This control appears only in the "settings" scene
        host.app.add(
            LabelControl("settings_title", Rect(20, 20, 400, 36), "Settings"),
            scene_name="settings",
        )
```

### Example — Two-Scene App

```python
from gui_do import (
    Feature,
    FeatureSpec,
    HostApplicationConfig,
    LabelControl,
    ButtonControl,
    RuntimeSceneSpec,
    SceneSetupSpec,
    SceneTransitionStyle,
    bootstrap_host_application,
    make_exit_action,
    make_scene_nav_action,
)
from pygame import Rect


class MainMenuFeature(Feature):
    def __init__(self):
        super().__init__("main_menu", scene_name="main")

    def build(self, host) -> None:
        host.app.add(
            LabelControl("title", Rect(20, 20, 400, 36), "Main Menu"),
            scene_name="main",
        )
        host.app.add(ButtonControl(
            "go_settings_btn", Rect(20, 70, 180, 32), "Go to Settings",
            on_click=lambda: host.action_registry.dispatch("go_settings"),
        ), scene_name="main")


class SettingsFeature(Feature):
    def __init__(self):
        super().__init__("settings_ui", scene_name="settings")

    def build(self, host) -> None:
        host.app.add(
            LabelControl("settings_title", Rect(20, 20, 400, 36), "Settings"),
            scene_name="settings",
        )
        host.app.add(ButtonControl(
            "back_btn", Rect(20, 70, 140, 32), "Back",
            on_click=lambda: host.action_registry.dispatch("go_main"),
        ), scene_name="settings")


CONFIG = HostApplicationConfig(
    display_size=(800, 600),
    window_title="Two-Scene App",
    fonts={"default": {"system_name": "Arial", "size": 14},
           "window": {"system_name": "Arial"}},
    font_role_specs=({"body": {"size": 14, "font": "default"},
                      "title": {"size": 16, "font": "window"}},),
    cursors=(),
    scene_specs=(
        SceneSetupSpec(name="main", pretty_name="Main Menu",
                       transition_style=SceneTransitionStyle.SLIDE_LEFT,
                       transition_duration=0.3, make_initial=True),
        SceneSetupSpec(name="settings", pretty_name="Settings",
                       transition_style=SceneTransitionStyle.SLIDE_RIGHT,
                       transition_duration=0.3),
    ),
    feature_specs=(
        FeatureSpec(attr_name="_main_menu", factory=MainMenuFeature),
        FeatureSpec(attr_name="_settings",  factory=SettingsFeature),
    ),
    window_specs=(),
    runtime_scene_specs=(
        RuntimeSceneSpec(scene_name="main",     bind_escape_to_exit=True),
        RuntimeSceneSpec(scene_name="settings", bind_escape_to_exit=False),
    ),
    action_specs=(
        make_exit_action(),
        make_scene_nav_action("go_settings", label="Settings", target_scene="settings"),
        make_scene_nav_action("go_main",     label="Main Menu", target_scene="main"),
    ),
    static_accessibility_specs=(),
    initial_scene_name="main",
    target_fps=120,
)


class TwoSceneApp:
    def __init__(self):
        bootstrap_host_application(self, CONFIG)

    def run(self) -> None:
        self.app.run_entrypoint(target_fps=CONFIG.target_fps)


if __name__ == "__main__":
    TwoSceneApp().run()
```

---

## 9. Spec Reference for Beginners

Specs are frozen dataclasses that describe application structure as data. Here are the ones you will use most often.

### FeatureSpec

Declares a feature to be instantiated and registered during bootstrap.

```python
from gui_do import FeatureSpec

FeatureSpec(
    attr_name="_my_feature",    # Host attribute that stores the instance
    factory=MyFeature,          # Callable returning the feature instance
)
```

`attr_name` is set on the host object, so `host._my_feature` gives you the instance after bootstrap.

### SceneSetupSpec

Declares a scene to be created and configured.

```python
from gui_do import SceneSetupSpec, SceneTransitionStyle

SceneSetupSpec(
    name="gameplay",                               # Internal scene identifier
    pretty_name="Gameplay",                        # Human-readable name
    transition_style=SceneTransitionStyle.FADE,    # Optional animated transition
    transition_duration=0.5,                       # Seconds
    make_initial=True,                             # This scene opens first
)
```

### ActionSpec — via factory helpers

Instead of constructing `ActionSpec` directly, use the provided helpers:

```python
from gui_do import make_exit_action, make_scene_nav_action, make_palette_open_action

make_exit_action()                              # Closes the application
make_scene_nav_action("go_game", label="Play", target_scene="gameplay")
make_palette_open_action()                      # Opens the command palette (F5)
```

### WindowSpec — via make_window_toggle_spec

`WindowSpec` declares a feature-owned floating window with a task panel toggle button.

```python
from gui_do import make_window_toggle_spec

make_window_toggle_spec(
    "debug",                      # Window key identifier
    "_debug_feature",             # Feature attr_name that owns the window
    slot_index=1,                 # Position in the task panel
    task_panel_label="Debug",     # Button label
    task_panel_style="angle",     # "angle" or "round"
)
```

### RuntimeSceneSpec

Controls per-scene runtime behavior such as background images and key bindings.

```python
from gui_do import RuntimeSceneSpec

RuntimeSceneSpec(
    scene_name="main",
    pristine_asset="assets/backdrop.jpg",   # Optional background image path
    bind_escape_to_exit=True,               # Escape triggers the "exit" action
    prewarm=False,                          # Pre-render scene before first display
)
```

### SceneRootSpec

Declares a managed root `PanelControl` for a named scene. Bootstrap creates the panel and stores it on the host as `host.{scene_name}_root`.

```python
from gui_do import SceneRootSpec

SceneRootSpec(
    scene_name="main",          # Scene this root belongs to
    control_id="main_root",     # Identifier for the PanelControl
    draw_background=False,      # Whether the panel draws its own background
)
```

With this spec in `HostApplicationConfig(scene_roots=(...))`, you get `host.main_root` as a ready-made container for your scene content.

### CursorSpec

Declares a custom cursor to register during bootstrap.

```python
from gui_do import CursorSpec

CursorSpec(
    name="crosshair",                  # Cursor identifier used at runtime
    asset="assets/cursors/cross.png",  # Path to cursor image
    hot_x=16,                          # Hotspot x offset (pixels from left)
    hot_y=16,                          # Hotspot y offset (pixels from top)
)
```

Pass as `HostApplicationConfig(cursors=(CursorSpec(...),))`. Registered cursors can be activated at runtime via the cursor manager.

### TelemetryConfig

Optional configuration for built-in performance telemetry. Disabled by default.

```python
from gui_do import TelemetryConfig

HostApplicationConfig(
    # ...
    telemetry=TelemetryConfig(
        enabled=False,               # Master switch
        live_analysis_enabled=True,  # In-process telemetry collector
        file_logging_enabled=False,  # Write spans to disk
    ),
)
```

When `enabled=False` (the default), there is no performance overhead.

### TaskPanelButtonSpec

Adds a custom button to the task panel strip (the auto-hiding bar at the bottom).

```python
from gui_do.features.data_driven_runtime import TaskPanelButtonSpec

TaskPanelButtonSpec(
    attr_name="_debug_btn",        # Host attribute for the button control
    control_id="debug_toggle",
    slot_index=2,
    label="Debug",
    on_click=lambda: host.window_presentation.toggle("debug"),
    style="angle",                 # "angle" or "round"
)
```

---

## 10. Complete Example Application

The following is a fully self-contained application that brings together everything covered in this tutorial:

- Two features (`CounterFeature` and `HistoryFeature`) with inter-feature messaging
- `ObservableValue` for reactive UI
- A `ButtonControl` that triggers state changes
- Scene navigation between a main view and a history log view
- A complete run loop via `bootstrap_host_application`

```python
# complete_example.py

from gui_do import (
    Feature,
    FeatureSpec,
    HostApplicationConfig,
    LabelControl,
    ButtonControl,
    ObservableValue,
    RuntimeSceneSpec,
    SceneSetupSpec,
    SceneTransitionStyle,
    bootstrap_host_application,
    make_exit_action,
    make_scene_nav_action,
)
from pygame import Rect


# ---------------------------------------------------------------------------
# Feature 1: Counter — owns observable count and a button
# ---------------------------------------------------------------------------

class CounterFeature(Feature):
    """Displays a counter and sends increment events to the history feature."""

    def __init__(self):
        super().__init__("counter", scene_name="main")

    def build(self, host) -> None:
        self.count = ObservableValue(0)

        self.count_label = host.app.add(
            LabelControl("count_lbl", Rect(20, 20, 360, 36), "Count: 0"),
            scene_name="main",
        )
        host.app.add(ButtonControl(
            "inc_btn", Rect(20, 68, 140, 32), "+1",
            on_click=self._on_increment,
        ), scene_name="main")

        host.app.add(ButtonControl(
            "view_history_btn", Rect(180, 68, 160, 32), "View History",
            on_click=lambda: host.action_registry.dispatch("go_history"),
        ), scene_name="main")

    def bind_runtime(self, host) -> None:
        self.count.subscribe(
            lambda v: setattr(self.count_label, "text", f"Count: {v}")
        )

    def _on_increment(self) -> None:
        self.count.value += 1
        # Notify the history feature about this event
        self.send_message("history", {
            "topic": "record",
            "entry": f"Incremented to {self.count.value}",
        })


# ---------------------------------------------------------------------------
# Feature 2: History — collects log entries sent by other features
# ---------------------------------------------------------------------------

class HistoryFeature(Feature):
    """Receives log messages and displays them on the history scene."""

    def __init__(self):
        super().__init__("history", scene_name="history")

    def build(self, host) -> None:
        self.entries = []
        self.log_label = host.app.add(
            LabelControl("log_lbl", Rect(20, 20, 560, 400), "(no events yet)"),
            scene_name="history",
        )
        host.app.add(ButtonControl(
            "back_btn", Rect(20, 440, 120, 32), "Back",
            on_click=lambda: host.action_registry.dispatch("go_main"),
        ), scene_name="history")

    def on_update(self, host) -> None:
        changed = False
        while self.has_messages():
            msg = self.pop_message()
            if msg.get("topic") == "record":
                self.entries.append(msg.get("entry", ""))
                changed = True
        if changed:
            # Show most recent 10 entries
            self.log_label.text = "\n".join(self.entries[-10:])


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CONFIG = HostApplicationConfig(
    display_size=(800, 600),
    window_title="Counter + History",
    fonts={"default": {"system_name": "Arial", "size": 14},
           "window": {"system_name": "Arial"}},
    font_role_specs=({"body":  {"size": 14, "font": "default"},
                      "title": {"size": 16, "font": "window"}},),
    cursors=(),
    scene_specs=(
        SceneSetupSpec(
            name="main",
            pretty_name="Counter",
            transition_style=SceneTransitionStyle.SLIDE_LEFT,
            transition_duration=0.3,
            make_initial=True,
        ),
        SceneSetupSpec(
            name="history",
            pretty_name="History",
            transition_style=SceneTransitionStyle.SLIDE_RIGHT,
            transition_duration=0.3,
        ),
    ),
    feature_specs=(
        FeatureSpec(attr_name="_counter", factory=CounterFeature),
        FeatureSpec(attr_name="_history", factory=HistoryFeature),
    ),
    window_specs=(),
    runtime_scene_specs=(
        RuntimeSceneSpec(scene_name="main",    bind_escape_to_exit=True),
        RuntimeSceneSpec(scene_name="history", bind_escape_to_exit=False),
    ),
    action_specs=(
        make_exit_action(),
        make_scene_nav_action("go_history", label="History", target_scene="history"),
        make_scene_nav_action("go_main",    label="Counter", target_scene="main"),
    ),
    static_accessibility_specs=(),
    initial_scene_name="main",
    target_fps=120,
)


# ---------------------------------------------------------------------------
# Application host
# ---------------------------------------------------------------------------

class CounterHistoryApp:
    def __init__(self):
        bootstrap_host_application(self, CONFIG)

    def run(self) -> None:
        self.app.run_entrypoint(target_fps=CONFIG.target_fps)


if __name__ == "__main__":
    CounterHistoryApp().run()
```

**How it works:**

1. Two features are declared via `FeatureSpec` — one per scene.
2. `CounterFeature.build` creates an `ObservableValue(0)` and wires it to a label in `bind_runtime`. When the button is clicked, the observable changes and the label updates automatically.
3. Each click also calls `self.send_message("history", {...})` to push a log entry to `HistoryFeature`.
4. `HistoryFeature.on_update` drains its message queue every frame and refreshes the log label when new entries arrive.
5. Two `make_scene_nav_action` entries wire the "View History" and "Back" buttons to scene transitions with a slide animation.

---

## 11. Next Steps

You have now learned the core concepts and patterns of gui_do. Here is where to go next:

**[README.md](README.md)** — The full API overview organized by tier. Start with the "API Organization" section for a map of every public symbol and when to use it.

**[demo_features/](demo_features/)** — The source code for the included demo application. It shows every control type, scene transitions, window toggles, custom rendering with `DirectFeature`, data grids, overlays, and more. Read `demo_config.py` to see a production-scale `HostApplicationConfig`, and any `*_demo_feature.py` file for full `Feature` subclass examples.

**[docs/](docs/)** — Architecture and contract documentation:
- `public_api_spec.md` — Complete public API reference
- `architecture_boundary_spec.md` — Boundaries between the framework and demo/application layers
- `runtime_operating_contracts.md` — Runtime invariants and guarantees

**[gui_do/features/feature_lifecycle.py](gui_do/features/feature_lifecycle.py)** — The source code for `Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, and `FeatureManager`. Reading this file directly is the fastest way to discover every lifecycle hook, helper, and advanced capability.

**[gui_do/features/data_driven_runtime.py](gui_do/features/data_driven_runtime.py)** — The source code for `bootstrap_host_application`, `HostApplicationConfig`, and all spec dataclasses. Useful for understanding exactly what bootstrap does in each step.
