[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg?branch=main)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)

# gui_do

**gui_do** is a pygame-based GUI framework for building data-driven, feature-oriented desktop applications. It combines declarative configuration, observable reactive data, and composable feature lifecycles to eliminate boilerplate while keeping you in control. Applications define declarative specs, features build UI in lifecycle hooks, and gui_do handles automatic rendering, event routing, scene management, and cross-feature communication.

## Table of Contents

- [API Organization: Primary vs. Secondary](#api-organization-primary-vs-secondary)
- [Overview of Data-Driven Feature-Lifecycle Systems](#overview-of-data-driven-feature-lifecycle-systems)
- [Tutorial: Data-Driven Feature-Lifecycle Design](#tutorial-data-driven-feature-lifecycle-design)
  - [Fundamental Concepts](#fundamental-concepts)
  - [Building Your First Feature](#building-your-first-feature)
  - [Observable Data and Reactive Bindings](#observable-data-and-reactive-bindings)
  - [Feature Lifecycle Hooks and Host Integration](#feature-lifecycle-hooks-and-host-integration)
  - [Multiple Scenes and Feature Scope](#multiple-scenes-and-feature-scope)
  - [DirectFeature for Custom Drawing](#directfeature-for-custom-drawing)
  - [LogicFeature and RoutedFeature for Domain Logic](#logicfeature-and-routedfeature-for-domain-logic)
  - [Feature-to-Feature Communication](#feature-to-feature-communication)
- [Minimal Runnable Example and Configuration](#minimal-runnable-example-and-configuration)
- [Data-Driven Bootstrap and Runtime](#data-driven-bootstrap-and-runtime)
  - [HostApplicationConfig and bootstrap_host_application](#hostapplicationconfig-and-bootstrap_host_application)
  - [Declarative Specs](#declarative-specs)
  - [Feature Registration and Window Management](#feature-registration-and-window-management)
  - [Scene Setup and Transitions](#scene-setup-and-transitions)
  - [Action Registry and Command Palette](#action-registry-and-command-palette)
- [Feature Lifecycle and Messaging](#feature-lifecycle-and-messaging)
  - [Feature Lifecycle Hooks](#feature-lifecycle-hooks)
  - [Feature Types](#feature-types)
  - [FeatureManager and Feature Coordination](#featuremanager-and-feature-coordination)
  - [Feature Message Routing](#feature-message-routing)
  - [Font Roles and Feature Styling](#font-roles-and-feature-styling)
- [Common Patterns](#common-patterns)
- [Benefits of Data-Driven Lifecycle Approach](#benefits-of-data-driven-lifecycle-approach)
- [FAQ](#faq)
- [See Also](#see-also)

---

## API Organization: Primary vs. Secondary

**gui_do's public API is tiered by intended use:**

### Tier 1 — PRIMARY: Data-Driven & Lifecycle (USE THESE)
Start here. These are the recommended way to build applications:

- **`bootstrap_host_application(host, config)`** — One-line app initialization
- **`HostApplicationConfig`** — Declarative app specification
- **Specs** — `FeatureSpec`, `SceneSetupSpec`, `WindowSpec`, `ActionSpec`, etc.
- **Features** — `Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`
- **Core managers** — `GuiApplication`, `SceneTransitionManager`, `FeatureManager`

**Example:**
```python
from gui_do import bootstrap_host_application, HostApplicationConfig

config = HostApplicationConfig(
    display_size=(1200, 800),
    scene_specs=[SceneSetupSpec(name="main")],
    features=[FeatureSpec(attr_name="_game", factory=GameFeature)],
)
bootstrap_host_application(self, config)
```

### Tier 2-7 — SECONDARY: Infrastructure (USE WHEN NEEDED)
Core runtime systems accessed when you need them:

- **Data** — `ObservableValue`, `PresentationModel`, `Binding`
- **Events & Actions** — `EventBus`, `ActionRegistry`
- **Scheduling** — `TaskScheduler`, `TweenManager`
- **Overlays** — `DialogManager`, `ToastManager`, `CommandPaletteManager`
- **Layout** — `ConstraintLayout`, `DockWorkspace`, `FlexLayout`
- **Persistence** — `SettingsRegistry`, `WorkspacePersistenceManager`

### Tier 8+ — TERTIARY: Individual Controls (AVOID IF POSSIBLE)
Available for completeness, but discourage direct use:

- `ButtonControl`, `LabelControl`, `SliderControl`, `TextInputControl`, etc.

**Why?** These are better composed through features. Direct control instantiation adds boilerplate and breaks declarative structure.

**Better approach:**
```python
class MyFeature(Feature):
    def build(self, host):
        button = ButtonControl(title="Click Me")
        button.on_click = self.handle_click
        host.scene.add_control(button)

    def handle_click(self):
        print("Clicked!")
```

---

## Overview of Data-Driven Feature-Lifecycle Systems

[Back to Top](#table-of-contents)

gui_do is built on two intertwined paradigms: **data-driven reactive design** and **feature-based lifecycle composition**. Together, they provide a framework where application behavior is declaratively specified and automatically wired.

### Data-Driven Foundation
At the core, gui_do separates data from presentation. **Observable data sources** (`ObservableValue`, `ObservableList`, `ObservableDict`) emit notifications when they change. Controls and features subscribe to these sources, automatically staying in sync without polling or manual refresh calls. The reactive layer is complemented by **bindings** that wire observable data to control attributes, handling type conversion and two-way synchronization transparently.

### Feature-Lifecycle Composition
Applications are organized as composable **features**—self-contained modules that own controls, subscriptions, and cross-feature communication. Each feature progresses through well-defined lifecycle hooks:

- **`build(host)`** — Create and add UI controls to the scene
- **`bind_runtime(host)`** — Establish observable subscriptions and logic bindings, after all features are built
- **`configure_accessibility(host, tab_index_start)`** — Set tab order and accessibility metadata
- **`handle_event(host, event)`** — Route and handle per-frame input events
- **`on_update(host)`** — Per-frame logic, ideal for draining feature message queues
- **`draw(host, surface, theme)`** — Custom drawing (most features rely on control rendering)

A `FeatureManager` orchestrates all registered features through these phases in registration order, providing deterministic ordering for cross-feature bindings and message routing.

### Three Feature Subtypes
gui_do provides three feature subtypes for different architectural patterns:

1. **`Feature`** — The base unit; provides all lifecycle hooks and message routing
2. **`DirectFeature`** — Draws directly to the display surface before GUI controls composite on top (use for visualizations, renderers, and custom graphics)
3. **`LogicFeature`** and **`RoutedFeature`** — Message-handling patterns for pure domain logic decoupled from UI

### Declarative Bootstrap
Production applications use `bootstrap_host_application(host, HostApplicationConfig)` to automatically instantiate features, create scenes, register actions, and bind presentation state from declarative specs. This eliminates wiring boilerplate while preserving full control over layout, messaging, and runtime behavior.

### What gui_do Handles Automatically
- **Rendering and compositing** — Direct drawing, overlays, control trees, transitions
- **Event routing** — Keyboard/mouse dispatch to focused controls and features
- **Scene management** — Scene creation, switching, transitions with optional pristine assets
- **Layout** — Grid, flex, constraint, dock, and tiling layouts with optional animation
- **Data subscriptions** — Binding lifecycle, cleanup, and collection change diffing
- **Cross-feature messaging** — Message queuing, routing, and logic feature binding
- **Accessibility** — Tab order, screen-reader annotations, focus management
- **Themes and fonts** — Font role registry, theme application, dynamic styling

### Best For
gui_do excels at building tools, editors, dashboards, simulation frontends, and other desktop applications where:
- Controls and data must stay in sync reactively
- Multiple independent features or modules are active simultaneously
- Scene-based navigation or multi-window layouts are needed
- Custom rendering overlays standard controls
- Cross-feature communication and decoupling are important

---

## Tutorial: Data-Driven Feature-Lifecycle Design

[Back to Top](#table-of-contents)

This tutorial builds understanding from foundational concepts toward complete production patterns. All code examples use current state of the gui_do codebase.

### Fundamental Concepts

**Observable Data** — The building block of reactivity. Instead of manually updating controls, you create observable data sources and controls/subscriptions react when they change:

```python
from gui_do import ObservableValue

counter = ObservableValue(0)
counter.subscribe(lambda value: print(f"Count: {value}"))
counter.value = 5   # prints "Count: 5"
```

**Bindings** — Connect observables to control attributes automatically. Two-way bindings propagate changes in both directions:

```python
from gui_do import Binding, ObservableValue, SliderControl, LayoutAxis
from pygame import Rect

zoom = ObservableValue(1.0)
slider = SliderControl(
    "zoom", Rect(20, 20, 200, 24),
    LayoutAxis.HORIZONTAL, 0.5, 4.0, 1.0,
    on_change=lambda v, _reason: zoom.__setattr__("value", v),
)

# Zoom value ↔ Slider position (two-way sync)
binding = Binding(zoom, slider, "value", mode="two_way", control_change_signal="on_change")
```

**Computed Values** — Derive read-only reactive values from observables. They recalculate automatically:

```python
from gui_do import ComputedValue, ObservableValue

width = ObservableValue(640)
height = ObservableValue(480)
area = ComputedValue(lambda: width.value * height.value, deps=[width, height])

area.subscribe(lambda v: print(f"Area: {v}"))
width.value = 1280   # prints "Area: 614400"
```

### Building Your First Feature

A **feature** is a lifecycle-aware module that owns controls, subscriptions, and cross-feature logic. Create a feature by subclassing `Feature` and implementing `build()` and `bind_runtime()`:

```python
from pygame import Rect
from gui_do import Feature, LabelControl, ButtonControl, ObservableValue, create_display, GuiApplication

class CounterFeature(Feature):
    def build(self, host) -> None:
        # Create observable data
        self.count = ObservableValue(0)

        # Create controls and add to scene
        self.label = host.scene.add(
            LabelControl("counter_label", Rect(20, 20, 200, 28), "Count: 0")
        )
        host.scene.add(ButtonControl(
            "increment", Rect(20, 60, 120, 32), "+1",
            on_click=self._on_increment,
        ))

    def bind_runtime(self, host) -> None:
        # Wire the observable to the label text
        self.count.subscribe(lambda v: setattr(self.label, "text", f"Count: {v}"))
        # Trigger initial label update
        self.count.value = 0

    def _on_increment(self) -> None:
        self.count.value = self.count.value + 1

# Run the feature
surface = create_display((800, 600), fullscreen=False)
app = GuiApplication(surface)
app.features.register(CounterFeature("counter"), host=app)
app.features.build_features(app)
app.features.bind_runtime(app)
app.run_entrypoint(target_fps=60)
```

**Key Points:**
- The feature name `"counter"` is the unique identifier for this feature and is used in message routing
- `build()` creates controls; `bind_runtime()` connects subscriptions (after all features are built)
- `host.scene` is the active scene root; controls added there become top-level nodes
- `app.features` is the `FeatureManager` that drives all features through their lifecycle phases

### Observable Data and Reactive Bindings

For data-heavy applications, use `ObservableList` and `ObservableDict` to maintain collections that controls refresh automatically:

```python
from gui_do import ListItem, ListViewControl, ObservableList
from pygame import Rect

class TodoListFeature(Feature):
    def build(self, host) -> None:
        self.items = ObservableList([
            ListItem("Buy milk"),
            ListItem("Walk dog"),
        ])
        self.list_view = host.scene.add(
            ListViewControl("todos", Rect(20, 20, 350, 300))
        )

    def bind_runtime(self, host) -> None:
        # Refresh list whenever items change
        self.items.subscribe(lambda _change: self.list_view.set_items(self.items.snapshot()))
        # Trigger initial population
        self.list_view.set_items(self.items.snapshot())
```

**BindingGroup** collects multiple bindings and cleans them up together on teardown:

```python
from gui_do import Binding, BindingGroup

class FormFeature(Feature):
    def build(self, host) -> None:
        self.bindings = BindingGroup()
        self.name_model = ObservableValue("")
        self.age_model = ObservableValue(0)

        self.name_input = host.scene.add(TextInputControl(...))
        self.age_input = host.scene.add(...)

    def bind_runtime(self, host) -> None:
        self.bindings.add(Binding(self.name_model, self.name_input, "text", mode="two_way"))
        self.bindings.add(Binding(self.age_model, self.age_input, "text", mode="two_way"))
```

### Feature Lifecycle Hooks and Host Integration

Features implement lifecycle hooks that `FeatureManager` calls in well-defined phases:

| Hook | Phase | When Called | Return Value |
|------|-------|-----------|---|
| `on_register(host)` | Registration | Feature being registered | — |
| `build(host)` | Build | Build phase for all features | — |
| `bind_runtime(host)` | Runtime Binding | After all features built | — |
| `configure_accessibility(host, tab_start)` | Accessibility | Setting up tab order | Next tab index |
| `handle_event(host, event)` | Per-Event | Each input event | `True` if consumed |
| `on_update(host)` | Per-Frame | Every frame update | — |
| `draw(host, surface, theme)` | Per-Frame Draw | After control rendering | — |
| `prewarm(host, surface, theme)` | Pre-Render | Before runtime (optional) | — |
| `shutdown_runtime(host)` | Shutdown | On app close | — |

The host object is typically the `GuiApplication` or a host class passed to `bootstrap_host_application`. Features validate that host has required attributes via `HOST_REQUIREMENTS`:

```python
class AnalysisFeature(Feature):
    HOST_REQUIREMENTS = {
        "bind_runtime": ("data_cache", "scheduler"),
    }

    def bind_runtime(self, host) -> None:
        # host.data_cache and host.scheduler are guaranteed to exist
        self.subscription = host.data_cache.subscribe(self._on_data_change)
```

### Multiple Scenes and Feature Scope

Applications with multiple scenes create them declaratively and switch between them. Each scene has its own scheduler, timers, and overlay stack:

```python
from gui_do import SceneSetupSpec, SceneTransitionStyle

class MainFeature(Feature):
    def __init__(self):
        super().__init__("main", scene_name="main")

    def build(self, host) -> None:
        # Controls added to the "main" scene
        host.scene.add(LabelControl("title", Rect(20, 20, 200, 28), "Main Scene"))

class SettingsFeature(Feature):
    def __init__(self):
        super().__init__("settings", scene_name="settings")

    def build(self, host) -> None:
        # Controls added to the "settings" scene
        host.scene.add(LabelControl("title", Rect(20, 20, 200, 28), "Settings"))

# Bootstrap creates scenes from specs
SCENE_SPECS = (
    SceneSetupSpec(name="main", pretty_name="Main", make_initial=True),
    SceneSetupSpec(name="settings", pretty_name="Settings"),
)

# Switch scenes at runtime
app.switch_scene("settings")
```

### DirectFeature for Custom Drawing

`DirectFeature` is a specialized feature for content that draws directly to the display surface **before** GUI controls composite on top. Use it for visualizations, particle systems, custom renderers, and canvas-style editors:

```python
import math
import pygame
from gui_do import DirectFeature, SliderControl, LabelControl, LayoutAxis, ObservableValue
from pygame import Rect

class WaveformFeature(DirectFeature):
    """Renders a live waveform directly to screen; GUI overlays on top."""

    def build(self, host) -> None:
        self.amplitude = ObservableValue(80.0)
        self._phase = 0.0

        # These controls appear on top of direct drawing
        host.scene.add(SliderControl(
            "amp", Rect(20, 20, 200, 24),
            LayoutAxis.HORIZONTAL, 10.0, 200.0, 80.0,
            on_change=lambda v, _r: self.amplitude.__setattr__("value", v),
        ))
        host.scene.add(LabelControl("amp_label", Rect(230, 20, 100, 24), "Amplitude"))

    def on_direct_update(self, host, dt_seconds: float) -> None:
        # Simulate waveform progression each frame
        self._phase += dt_seconds * 2.0 * math.tau

    def draw_direct(self, host, surface, theme) -> None:
        # Draw to the pristine surface before GUI composites
        w, h = surface.get_size()
        cy = h // 2
        amp = self.amplitude.value

        points = [
            (px, cy + int(math.sin((px / w) * math.tau + self._phase) * amp))
            for px in range(w)
        ]
        if len(points) > 1:
            pygame.draw.lines(surface, (80, 200, 120), False, points, 2)

surface = create_display((800, 600), fullscreen=False)
app = GuiApplication(surface)
app.features.register(WaveformFeature("waveform"), host=app)
app.features.build_features(app)
app.features.bind_runtime(app)
app.run_entrypoint(target_fps=60)
```

DirectFeature provides three additional hooks:
- **`handle_direct_event(host, event)`** — Handle events before control pipeline
- **`on_direct_update(host, dt_seconds)`** — Per-frame update with delta time
- **`draw_direct(host, surface, theme)`** — Draw to pristine surface before overlays

### LogicFeature and RoutedFeature for Domain Logic

Decouple UI features from domain logic by using message-handling features. A **LogicFeature** receives commands; a **RoutedFeature** routes messages by topic.

**LogicFeature** — Command Handler Pattern:

```python
from gui_do import LogicFeature, FeatureMessage

class CalculatorLogic(LogicFeature):
    def on_logic_command(self, host, message: FeatureMessage) -> None:
        if message.command == "add":
            a = message.get("a", 0)
            b = message.get("b", 0)
            # Could store result or emit event
            print(f"Result: {a + b}")

# Usage from another feature
class CalculatorUI(Feature):
    def build(self, host) -> None:
        host.scene.add(ButtonControl(
            "calculate", Rect(20, 20, 120, 32), "Add",
            on_click=lambda: self.send_logic_message("calculator", {"a": 10, "b": 32}),
        ))

    def send_logic_message(self, logic_feature_name: str, payload):
        message = FeatureMessage.from_payload(self.name, logic_feature_name, {"command": "add", **payload})
        self.send_message(logic_feature_name, {"command": "add", **payload})
```

**RoutedFeature** — Topic-Based Routing:

```python
from gui_do import RoutedFeature, FeatureMessage

class EventRouter(RoutedFeature):
    def message_handlers(self):
        return {
            "selection_changed": self._on_selection_changed,
            "data_loaded": self._on_data_loaded,
        }

    def _on_selection_changed(self, host, message: FeatureMessage) -> None:
        item = message.get("item")
        print(f"Selected: {item}")

    def _on_data_loaded(self, host, message: FeatureMessage) -> None:
        data = message.get("data", [])
        print(f"Loaded {len(data)} items")

# Usage from UI feature
ui_feature.send_message("event_router", {"topic": "selection_changed", "item": "foo"})
```

### Feature-to-Feature Communication

Features communicate via messages, logic binding, and observable subscriptions. **Messages** are asynchronous and decoupled; **logic binding** connects routed/logic features; **subscriptions** share observable data:

```python
from gui_do import Feature, FeatureMessage

class ProducerFeature(Feature):
    def build(self, host) -> None:
        host.scene.add(ButtonControl(
            "emit", Rect(20, 20, 100, 32), "Emit",
            on_click=self._emit_event,
        ))

    def _emit_event(self) -> None:
        # Send message to consumer feature
        self.send_message("consumer", {"topic": "event", "data": "hello"})

class ConsumerFeature(Feature):
    def build(self, host) -> None:
        self.status = host.scene.add(LabelControl("status", Rect(20, 60, 200, 28), "Waiting…"))

    def on_update(self, host) -> None:
        # Drain queued messages from producer
        while self.has_messages():
            message = self.pop_message()
            if message.topic == "event":
                self.status.text = f"Received: {message.get('data')}"
```

---

## Minimal Runnable Example and Configuration

[Back to Top](#table-of-contents)

```python
import pygame
from gui_do import (
    Feature,
    FeatureSpec,
    HostApplicationConfig,
    LabelControl,
    ButtonControl,
    ObservableValue,
    SceneSetupSpec,
    RuntimeSceneSpec,
    bootstrap_host_application,
    make_exit_action,
)
from pygame import Rect


class CounterFeature(Feature):
    """A simple counter that reacts to button presses."""

    def build(self, host) -> None:
        self.count = ObservableValue(0)
        screen = host.screen_rect
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
        self.count.subscribe(
            lambda v: setattr(self.label, "text", f"Count: {v}")
        )

    def _on_click(self) -> None:
        self.count.value += 1


CONFIG = HostApplicationConfig(
    display_size=(800, 600),
    window_title="Counter",
    fonts={"default": {"system_name": "Arial", "size": 14},
           "window": {"system_name": "Arial"}},
    font_role_specs=({"body": {"size": 14, "font": "default"},
                      "title": {"size": 18, "font": "window"}},),
    cursors=(),
    scene_specs=(SceneSetupSpec(name="main", make_initial=True),),
    feature_specs=(FeatureSpec(attr_name="_counter", factory=CounterFeature),),
    window_specs=(),
    runtime_scene_specs=(RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),),
    action_specs=(make_exit_action(),),
    static_accessibility_specs=(),
    initial_scene_name="main",
    target_fps=60,
)


class CounterApp:
    def __init__(self) -> None:
        bootstrap_host_application(self, CONFIG)

    def run(self) -> None:
        self.app.run_entrypoint(target_fps=CONFIG.target_fps)


if __name__ == "__main__":
    CounterApp().run()
```

---

## Data-Driven Bootstrap and Runtime

[Back to Top](#table-of-contents)

### HostApplicationConfig and bootstrap_host_application

`bootstrap_host_application(host, config: HostApplicationConfig)` bootstraps a complete application from declarative specs in a single call. It:

1. Creates the pygame display surface and sets window title
2. Instantiates `GuiApplication`
3. Registers font roles from declarative specs
4. Instantiates and registers all features
5. Creates and configures all scenes with transitions
6. Creates action registry and command palette
7. Registers all standard actions (exit, scene navigation, window toggles)
8. Calls `build_features()` and `bind_runtime()` automatically
9. Sets up accessibility metadata and tab order

`bootstrap_host_application` sets the following attributes on the host object:

| Attribute | Type | Content |
|---|---|---|
| `host.screen` | pygame Surface | Display surface |
| `host.screen_rect` | pygame.Rect | Screen bounding rect |
| `host.app` | `GuiApplication` | Main application |
| `host.font_roles` | `FontRoleRegistry` | Font role registry |
| `host.scene_transitions` | `SceneTransitionManager` | Scene transition controller |
| `host.scene_presentation` | `ScenePresentationModel` | Scene root and task panel management |
| `host.window_presentation` | `FeatureWindowPresentationModel` | Feature window bindings and visibility |
| `host.action_registry` | `ActionRegistry` | All declared actions |
| `host._palette_manager` | `CommandPaletteManager` | Command palette overlay |
| `host.go_to_{scene_name}` | callable | Navigation helper per scene |
| `host.{feature_attr}` | `Feature` subclass | One attribute per `FeatureSpec.attr_name` |

Example:

```python
from gui_do import HostApplicationConfig, bootstrap_host_application

class MyApp:
    pass

host = MyApp()
config = HostApplicationConfig(
    display_size=(1280, 720),
    window_title="My App",
    fonts={"default": {"file": "fonts/default.ttf", "size": 12}},
    font_role_specs=({"body": {"size": 12, "font": "default"}},),
    cursors=(),
    scene_specs=(...),
    feature_specs=(...),
    window_specs=(),
    runtime_scene_specs=(...),
    action_specs=(...),
    static_accessibility_specs=(),
    initial_scene_name="main",
    target_fps=60,
)
bootstrap_host_application(host, config)
host.app.run_entrypoint(target_fps=config.target_fps)
```

### Declarative Specs

Declarative specs are dataclass configurations that describe application structure as data:

**FeatureSpec** — Declarative feature registration:

```python
FeatureSpec(
    attr_name="my_feature",        # Host attribute to store feature instance
    factory=lambda: MyFeature(),   # Callable returning feature instance
)
```

**SceneSetupSpec** — Declarative scene configuration:

```python
SceneSetupSpec(
    name="main",                          # Scene identifier
    pretty_name="Main Scene",             # Human-readable name
    transition_style=SceneTransitionStyle.SLIDE_LEFT,  # Optional transition
    transition_duration=0.5,              # Transition duration in seconds
    tiling_enabled=True,                  # Enable window tiling
    make_initial=True,                    # Make this the initial scene
)
```

**RuntimeSceneSpec** — Runtime scene behavior:

```python
RuntimeSceneSpec(
    scene_name="main",
    pristine_asset="assets/backdrop.jpg",  # Optional background image
    bind_escape_to_exit=True,              # Escape key triggers "exit" action
    prewarm=False,                         # Pre-render before displaying
)
```

**WindowSpec** — Feature window presentation (use `make_window_toggle_spec` helper):

```python
make_window_toggle_spec(
    "my_window",              # Key identifier
    "_my_feature",            # Feature attribute name
    slot_index=2,             # Task panel slot position
    task_panel_label="Tool",  # Button label
    task_panel_style="round", # Button style ("round" or "angle")
    tab_before_showcase=False,
    action_label="Show Tool", # Action menu label
    action_name="show_tool",  # Action registry name
)
```

**ActionSpec** — Application action (use factory helpers):

```python
make_exit_action()              # Standard exit action
make_scene_nav_action(
    "go_settings",
    label="Go to Settings",
    target_scene="settings",
)
make_palette_open_action()      # Standard command palette action
```

### Feature Registration and Window Management

Features are instantiated, registered, and built automatically during `bootstrap_host_application`. Feature windows managed by declarative specs are anchored using the layout system and toggle visibility through task panel buttons or action registry entries.

Use `FeatureWindowPresentationModel` to programmatically manage feature window visibility:

```python
# From inside Feature.bind_runtime:
window_presentation = host.window_presentation
window_presentation.show("my_window")      # Show window
window_presentation.hide("my_window")      # Hide window
window_presentation.toggle("my_window")    # Toggle visibility
```

### Scene Setup and Transitions

Scenes are created from `SceneSetupSpec` entries. Each scene is fully isolated with its own scheduler, timers, tweens, overlays, and input routing. Scene transitions are configured per-scene and applied automatically when switching:

```python
# Switch scenes at runtime
host.scene_transitions.go("settings")

# Or use the convenience helper created by bootstrap
host.go_to_settings()
```

Transition styles:

- `SceneTransitionStyle.FADE` — Fade in/out
- `SceneTransitionStyle.SLIDE_LEFT` — Slide from left
- `SceneTransitionStyle.SLIDE_RIGHT` — Slide from right
- `SceneTransitionStyle.SLIDE_UP` — Slide from top
- `SceneTransitionStyle.SLIDE_DOWN` — Slide from bottom

### Action Registry and Command Palette

Actions are declared via `ActionSpec` entries and automatically registered during bootstrap. Actions appear in the command palette and can be invoked via keyboard, buttons, or programmatically:

```python
# Programmatic invocation
host.action_registry.dispatch("show_tool")

# From command palette (F5 by default)
# User types action name or label
```

All window toggles are automatically registered as actions so they appear in the command palette.

---

## Feature Lifecycle and Messaging

[Back to Top](#table-of-contents)

### Feature Lifecycle Hooks

Every `Feature` instance progresses through these lifecycle phases:

| Hook | Phase | Host | Return |
|---|---|---|---|
| `on_register(host)` | Registration | Feature is being registered | — |
| `build(host)` | Build | Create and add controls | — |
| `bind_runtime(host)` | Runtime Setup | Wire subscriptions after all features built | — |
| `configure_accessibility(host, tab_start)` | Accessibility | Set tab order and accessibility | Next tab index |
| `handle_event(host, event)` | Per-Event | Route per-frame input events | `True` if consumed |
| `on_update(host)` | Per-Frame Update | Per-frame logic | — |
| `draw(host, surface, theme)` | Per-Frame Draw | Custom drawing | — |
| `prewarm(host, surface, theme)` | Pre-Render | Optional pre-rendering | — |
| `shutdown_runtime(host)` | Shutdown | Cleanup on app close | — |

`FeatureManager` calls all registered features through each phase in registration order. This ensures deterministic ordering for cross-feature bindings and consistent state transitions.

### Feature Types

**Feature** — Base type for all features. Implements full lifecycle and messaging.

**DirectFeature** — Specialized feature for direct screen drawing. Adds:

- `handle_direct_event(host, event)` — Receive events before control pipeline
- `on_direct_update(host, dt_seconds)` — Per-frame update with delta time
- `draw_direct(host, surface, theme)` — Draw to pristine surface before GUI composites

Use `DirectFeature` for visualizations, simulations, and canvas-style editors where custom rendering is the primary content.

**LogicFeature** — Pure command handler endpoint:

- `on_logic_command(host, message: FeatureMessage)` — Handle command messages
- `on_update(host)` — Automatically drains command message queue

Callers send messages with a `"command"` field; the logic feature handles them. Decouples UI from business logic.

**RoutedFeature** — Topic-based message router:

- `message_handlers()` — Return dict mapping topic → handler callable
- `on_message(host, message: FeatureMessage)` — Route messages by topic
- `on_update(host)` — Automatically drains routed message queue

Callers send messages with a `"topic"` field; the feature routes to the matching handler.

### FeatureManager and Feature Coordination

`FeatureManager` (available as `app.features`) coordinates lifecycle and messaging for all registered features:

**Registration:**
- `register(feature, host=None)` — Register feature with optional host override
- `unregister(name)` — Unregister feature by name
- `get(name)` — Retrieve feature by name
- `names()` — Return tuple of all feature names
- `features()` — Iterate all registered features

**Lifecycle:**
- `build_features(host)` — Call `build()` for all features
- `bind_runtime(host)` — Call `bind_runtime()` for all features
- `configure_accessibility(host, tab_start)` — Call accessibility hooks
- `update_features(host)` — Call `on_update()` for all features
- `draw(surface, theme, host)` — Call `draw()` for all features
- `handle_event(event, host)` — Dispatch event to all features; return `True` if consumed

**DirectFeature Support:**
- `update_direct_features(dt_seconds, host)` — Call `on_direct_update()` for direct features
- `draw_direct_features(surface, theme, host)` — Call `draw_direct()` for direct features

**Messaging:**
- `send_message(sender_name, target_name, payload)` — Send inter-feature message
- `send_logic_message(consumer_name, payload, alias="default")` — Send to bound logic feature

**Logic Binding:**
- `bind_logic(consumer_name, provider_name, alias="default")` — Bind logic feature
- `unbind_logic(consumer_name, alias="default")` — Unbind logic feature
- `bound_logic_name(consumer_name, alias="default")` — Query bound logic name

### Feature Message Routing

Features communicate asynchronously through `FeatureMessage` envelopes:

```python
from gui_do import FeatureMessage

# Send from any feature
self.send_message("target_feature", {"topic": "data.changed", "data": [1, 2, 3]})

# Receiver side (RoutedFeature)
class DataConsumer(RoutedFeature):
    def message_handlers(self):
        return {
            "data.changed": self._on_data_changed,
        }

    def _on_data_changed(self, host, message: FeatureMessage) -> None:
        data = message.get("data", [])
        print(f"Received: {data}")
```

Messages are queued per-feature and drained in `on_update()` so they are processed predictably each frame.

### Font Roles and Feature Styling

Features can register custom font roles for use in their controls:

```python
class StyledFeature(Feature):
    def build(self, host) -> None:
        # Register feature-local font roles
        self.font_roles = self.register_font_roles(host, {
            "title": {"size": 20, "file_path": "fonts/title.ttf", "bold": True},
            "body": {"size": 12, "file_path": "fonts/body.ttf"},
        })

        # Create controls using the registered roles
        label = host.scene.add(LabelControl("title", Rect(...), "Title"))
        label.font_role = self.font_role("title")  # Access via font_role()
```

Registered font roles are automatically namespaced as `feature.{feature_name}.{role_name}`, preventing collisions across features.

---

## Common Patterns

[Back to Top](#table-of-contents)

### Window Toggle with Task Panel Button

Create a feature window with a task panel button to toggle visibility:

```python
from gui_do import make_window_toggle_spec

config = HostApplicationConfig(
    # ...
    window_specs=(
        make_window_toggle_spec(
            "debug",              # window key
            "_debug_feature",     # feature attribute
            slot_index=2,
            task_panel_label="Debug",
            task_panel_style="angle",
        ),
    )
)
```

### Scene Navigation with Action Specs

Define actions that navigate between scenes:

```python
from gui_do import make_scene_nav_action

config = HostApplicationConfig(
    # ...
    action_specs=(
        make_scene_nav_action("go_menu", label="Main Menu", target_scene="main"),
        make_scene_nav_action("go_game", label="Start Game", target_scene="gameplay"),
    )
)
```

### Observable State Management in Features

Use observable values in features for reactive state management:

```python
from gui_do import Feature, ObservableValue, LabelControl
from pygame import Rect

class ScoreFeature(Feature):
    def build(self, host) -> None:
        self.score = ObservableValue(0)
        self.label = host.scene.add(
            LabelControl("score_label", Rect(20, 20, 200, 28), "Score: 0")
        )

    def bind_runtime(self, host) -> None:
        self.score.subscribe(lambda v: setattr(self.label, "text", f"Score: {v}"))
        self.score.value = 0

    def add_points(self, points: int) -> None:
        self.score.value += points
```

### Feature-to-Feature Messaging

`RoutedFeature` enables inter-feature communication with named topics:

```python
from gui_do import RoutedFeature, Feature, FeatureMessage

class ScoreTracker(RoutedFeature):
    def build(self, host) -> None:
        self.total = 0

    def message_handlers(self):
        return {
            "add_points": self._on_add_points,
        }

    def _on_add_points(self, host, message: FeatureMessage) -> None:
        self.total += message.get("points", 0)
        print(f"Total score: {self.total}")

class GameLogic(Feature):
    def on_player_achievement(self) -> None:
        self.send_message("score_tracker", {"topic": "add_points", "points": 100})
```

---

## Benefits of Data-Driven Lifecycle Approach

[Back to Top](#table-of-contents)

- **Declarative Over Imperative** — Specs are easier to read, understand, and maintain than procedural setup code
- **Automatic Wiring** — `bootstrap_host_application` handles setup, reducing boilerplate by ~50% compared to manual construction
- **Better Separation of Concerns** — Features encapsulate UI, logic, and state independently
- **Improved Testability** — Declarative specs and isolated features are easier to unit test
- **Feature Composability** — Features are independent modules that can be easily added, removed, or reused
- **Framework Automation** — gui_do handles rendering, event routing, scene management, and layout—you focus on domain logic
- **Clear Lifecycle** — Well-defined feature hooks (`build`, `bind_runtime`, `handle_event`, `on_update`, `draw`) make code flow predictable
- **Observable Reactivity** — Data automatically propagates changes without polling or manual refresh calls
- **Zero-Boilerplate Bootstrap** — A single `bootstrap_host_application` call replaces hundreds of lines of manual app wiring
- **Consistent Patterns** — Spec-based configuration and lifecycle hooks apply uniformly across all application sizes

---

## FAQ

[Back to Top](#table-of-contents)

**Q: Can I still directly instantiate individual controls?**

A: Yes, controls remain in the public API. However, this is discouraged. Instead, instantiate controls within feature lifecycle methods, where they integrate naturally with the feature's state and lifecycle.

**Q: How do I customize control creation?**

A: Create a Feature with a factory method that builds and configures controls in `build()`. The feature owns the controls and wires them to observable data in `bind_runtime()`.

**Q: What if I need low-level event handling?**

A: Implement `handle_event(host, event)` in your Feature. Features receive events in registration order after controls process them. For events that should preempt the control pipeline, use `DirectFeature.handle_direct_event()`.

**Q: How do I access the application from a feature?**

A: The `host` parameter in feature lifecycle methods provides access to the application, scene, action registry, and other services. With `bootstrap_host_application`, `host.app` is the `GuiApplication` instance.

**Q: Can I mix old imperative and new declarative styles?**

A: Not recommended. For consistency and maintainability, use declarative specs and features throughout your application.

**Q: How do I visualize graphics that appear behind controls?**

A: Use `DirectFeature` to draw directly to the surface before the control tree composites on top. Useful for backgrounds, visualizations, and custom renderers.

**Q: What about custom themes or styling?**

A: Use font roles and the `FontRoleRegistry` for consistent styling. Register font roles in `HostApplicationConfig.font_role_specs` and apply them to controls via `control.font_role = "role_name"`.

---

## See Also

[Back to Top](#table-of-contents)

- **[Public API Specification](docs/public_api_spec.md)** — Complete API reference organized by tier (primary, secondary, tertiary)
- **[Architecture Boundary Specification](docs/architecture_boundary_spec.md)** — Package boundaries between framework and demo code
- **[Runtime Operating Contracts](docs/runtime_operating_contracts.md)** — Runtime invariants and guarantees
- **[Feature Lifecycle Implementation](gui_do/features/feature_lifecycle.py)** — Base Feature classes and lifecycle details
- **[Data-Driven Runtime Implementation](gui_do/features/data_driven_runtime.py)** — Bootstrapping and spec handling
- **[Demo Features](demo_features/)** — Example feature implementations in the demo application
