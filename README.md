[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg?branch=main)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)

Latest Demo (click):

<a href="https://www.youtube.com/watch?v=wkEmwIOquCo"><img src="https://img.youtube.com/vi/wkEmwIOquCo/0.jpg" alt="Demo Video"></img></a>

# gui_do

## Project Overview

[Back to Top](#table-of-contents)

gui_do is a pygame-based GUI framework for building desktop applications through declarative runtime specs and feature lifecycles instead of hand-wired scene code. You describe scenes, features, actions, overlays, and window presentation in data, then bind focused behavior inside Feature hooks. gui_do removes a large amount of boilerplate around scene setup, event routing, overlay dispatch, focus handling, and lifecycle sequencing.

## Table of Contents

- [Project Overview](#project-overview)
- [API Organization](#api-organization)
  - [Tier 1: Primary APIs](#tier-1-primary-apis)
  - [Tier 2-7: Runtime Infrastructure](#tier-2-7-runtime-infrastructure)
  - [Tier 8+: Controls and Low-Level Building Blocks](#tier-8-controls-and-low-level-building-blocks)
- [Overview](#overview)
  - [How the Pieces Fit Together](#how-the-pieces-fit-together)
  - [What gui_do Handles Automatically](#what-gui_do-handles-automatically)
  - [Overlay and Toast Behavior](#overlay-and-toast-behavior)
- [Comprehensive Tutorial](#comprehensive-tutorial)
  - [Start with Feature Composition](#start-with-feature-composition)
  - [Feature Types](#feature-types)
  - [Routed Runtime Specs](#routed-runtime-specs)
  - [Reactive Data Flow](#reactive-data-flow)
  - [Scenes and Windows](#scenes-and-windows)
- [Minimal Runnable Example and Configuration](#minimal-runnable-example-and-configuration)
- [Data-Driven Bootstrap and Runtime](#data-driven-bootstrap-and-runtime)
  - [HostApplicationConfig and bootstrap_host_application](#hostapplicationconfig-and-bootstrap_host_application)
  - [FeatureSpec](#featurespec)
  - [SceneSetupSpec](#scenesetupspec)
  - [ActionSpec](#actionspec)
  - [WindowSpec](#windowspec)
  - [RuntimeSceneSpec and Scene Roots](#runtimescenespec-and-scene-roots)
  - [Routed Runtime Helpers](#routed-runtime-helpers)
- [Feature Lifecycle and Messaging](#feature-lifecycle-and-messaging)
  - [Lifecycle Order](#lifecycle-order)
  - [Where Wiring Belongs](#where-wiring-belongs)
  - [FeatureManager Coordination](#featuremanager-coordination)
  - [Feature Messaging](#feature-messaging)
- [Common Patterns](#common-patterns)
  - [Scene Menu Strip and Task Panel Setup](#scene-menu-strip-and-task-panel-setup)
  - [Window Toggles and Focus-Aware Routing](#window-toggles-and-focus-aware-routing)
  - [Shortcut Help Overlay](#shortcut-help-overlay)
  - [Toast Notifications](#toast-notifications)
  - [Observable State Across Features](#observable-state-across-features)
- [Benefits of Data-Driven Lifecycle Approach](#benefits-of-data-driven-lifecycle-approach)
- [FAQ](#faq)
- [See Also](#see-also)

## API Organization

[Back to Top](#table-of-contents)

New applications should start with Tier 1 and stay there for as long as possible. The lower tiers are public and useful, but they are supporting layers for the runtime rather than the preferred starting point.

### Tier 1: Primary APIs

Start here first.

- `HostApplicationConfig` and `HostApplicationBindingSpec` for declarative host setup, with `build_host_application_config` for composing large configs from binding specs.
- `bootstrap_host_application` for display, app, scenes, features, actions, overlays, and runtime wiring.
- `Feature`, `DirectFeature`, `LogicFeature`, and `RoutedFeature` for lifecycle composition.
- `FeatureSpec`, `SceneSetupSpec`, `RuntimeSceneSpec`, `ActionSpec`, and `WindowSpec` for declarative runtime structure.
- `RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec` for standard routed-feature wiring.
- `ScenePresentationModel` for scene and window coordination.

### Tier 2-7: Runtime Infrastructure

Use these when Tier 1 composition needs more direct control.

- Reactive data and bindings: `ObservableValue`, `ObservableList`, `ObservableDict`, `ComputedValue`, `Binding`, `BindingGroup`.
- Events and actions: `GuiEvent`, `EventBus`, `ActionManager`, `ActionRegistry`, `InputMap`, `KeyChordManager`.
- Scheduling and animation: `TaskScheduler`, `CooperativeScheduler`, `TweenManager`, `Timers`, `TransitionManager`.
- Theme and layout: `ColorTheme`, `ThemeManager`, `ConstraintLayout`, `DockWorkspace`, `FlexLayout`, `GridLayout`.
- Overlays and persistence: `OverlayManager`, `ToastManager`, `DialogManager`, `CommandPaletteManager`, `WorkspacePersistenceManager`.

### Tier 8+: Controls and Low-Level Building Blocks

Controls such as `ButtonControl`, `LabelControl`, `SliderControl`, `TextInputControl`, `WindowControl`, and `TaskPanelControl` are public, but they are best consumed inside a Feature or a data-driven helper rather than as the top-level architecture.

## Overview

[Back to Top](#table-of-contents)

### How the Pieces Fit Together

gui_do combines four ideas into one runtime model:

- Observable data stores application state in `ObservableValue`, `ObservableList`, and `ObservableDict` objects.
- Features own one bounded area of UI or logic and implement lifecycle hooks instead of ad hoc setup code.
- Declarative specs describe scenes, actions, window toggles, shortcut overlays, task panels, and runtime scene behavior.
- Bootstrap helpers instantiate the application, create scenes, register features, wire actions, and bind runtime behavior in a deterministic order.

That combination means you can declare the shell of an application up front, let gui_do handle scene creation and shared plumbing, and keep the feature classes focused on the controls, subscriptions, and message handling they own.

### What gui_do Handles Automatically

gui_do takes care of:

- Rendering control trees and direct-draw features.
- Keyboard and mouse routing through overlays, windows, focus targets, and fallthrough handlers.
- Scene creation, transitions, and runtime scene startup behavior.
- Focus movement, task-panel focus mode, and window-aware routing.
- Feature registration, build ordering, bind ordering, update sequencing, and shutdown.
- Action registration and key binding dispatch.
- Overlay coordination, toast dispatch, and command palette integration.
- Accessibility key routing: Tab drives traversal, and focused-control Up/Down accessibility navigation keys are consumed at the focused control so they do not fall through to scene-level handlers.
- Non-accessibility key routing precedence: focused control first, then active window, then screen lifecycle handlers.

### Overlay and Toast Behavior

Current overlay behavior matters when you build menus, help panels, or modal surfaces:

- `OverlayManager` supports dismiss-on-escape overlays.
- `OverlayManager` supports dismiss-on-outside-click overlays.
- Overlays can opt into modal-style key capture with `consume_unhandled_keys=True`, which consumes unhandled keyboard input before it falls through to the scene.
- `ToastManager.route_event()` consumes clicks inside toast bounds so clicks do not pass through to underlying controls.
- Toasts can optionally take an `on_click` callback when you want toast interaction to trigger follow-up behavior explicitly.

## Comprehensive Tutorial

[Back to Top](#table-of-contents)

### Start with Feature Composition

The normal gui_do flow is:

1. Define one or more Feature classes.
2. Describe them in `FeatureSpec` entries.
3. Describe scenes and actions in `SceneSetupSpec`, `RuntimeSceneSpec`, and `ActionSpec` entries.
4. Put everything in `HostApplicationConfig`.
5. Call `bootstrap_host_application` once.

Inside a feature, keep `build()` for creating controls and `bind_runtime()` for subscriptions, event-bus bindings, and other runtime wiring that depends on the whole host being present.

### Feature Types

- `Feature` is the general-purpose unit for most UI work.
- `DirectFeature` is for custom drawing and per-frame direct rendering that should bypass normal control composition.
- `LogicFeature` is for domain logic that mostly drains command-style messages in `on_update()`.
- `RoutedFeature` is for topic-based message dispatch where `message_handlers()` maps topic names to handlers.

Practical rule: if you are building a panel, window, or control tree, use `Feature`. If you are building a simulation service or coordinator with no visible controls, use `LogicFeature`. If you need message-topic fan-out, use `RoutedFeature`. If you need direct pixels, use `DirectFeature`.

### Routed Runtime Specs

`RoutedRuntimeSpec` keeps `bind_runtime()` small by declaring standard runtime wiring:

- logic aliases via `LogicBindingSpec`
- action hotkeys via `ActionHotkeySpec`
- control activation keys via `ControlKeyBindingSpec`
- event-bus subscriptions via `EventSubscriptionSpec`
- shortcut help overlays via `ShortcutOverlaySpec`
- task-panel focus toggles via `TaskPanelFocusToggleSpec`

This pattern is used heavily in the demo features and is the easiest way to keep routed features declarative instead of hand-registering every runtime dependency.

```python
import pygame

from gui_do import (
    RoutedRuntimeSpec,
    ShortcutOverlaySpec,
    TaskPanelFocusToggleSpec,
)

runtime_spec = RoutedRuntimeSpec(
    scene_name="main",
    shortcut_overlays=(
        ShortcutOverlaySpec(
            attr_name="help_overlay",
            action_registry_attr="action_registry",
            toggle_action_name="show_help",
            toggle_key=pygame.K_F9,
            toggle_scene_name="main",
            manual_shortcut_lines=(
                "F5: Open command palette",
                "F9: Display this help",
            ),
            prepend_manual_shortcuts=True,
        ),
    ),
    task_panel_focus_toggles=(
        TaskPanelFocusToggleSpec(
            action_name="toggle_task_panel_focus",
            scene_name="main",
            key=pygame.K_F1,
        ),
    ),
)
```

### Reactive Data Flow

Use observables for data, not widget-driven state. A typical feature creates `ObservableValue` or `ObservableList` instances during `build()`, then attaches subscriptions or bindings during `bind_runtime()`.

```python
from pygame import Rect

from gui_do import Feature, LabelControl, ObservableValue


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self.count = ObservableValue(0)

    def build(self, host) -> None:
        self.label = host.app.add(
            LabelControl("counter_label", Rect(24, 24, 220, 28), "Count: 0"),
            scene_name="main",
        )

    def bind_runtime(self, host) -> None:
        def _apply(value: int) -> None:
            self.label.text = f"Count: {value}"

        self.count.subscribe(_apply)
        _apply(self.count.value)
```

### Scenes and Windows

`SceneSetupSpec` describes scene creation and transitions. `WindowSpec` describes feature-window toggle metadata. `RuntimeSceneSpec` describes startup behavior such as pristine assets, prewarming, and whether escape binds to the exit action. That split keeps scene structure, window presentation, and runtime startup behavior independent but composable.

## Minimal Runnable Example and Configuration

[Back to Top](#table-of-contents)

```python
import pygame
from pygame import Rect

from gui_do import (
    ActionSpec,
    Feature,
    FeatureSpec,
    HostApplicationConfig,
    LabelControl,
    RuntimeSceneSpec,
    SceneSetupSpec,
    TelemetryConfig,
    bootstrap_host_application,
)


class HelloFeature(Feature):
    def __init__(self) -> None:
        super().__init__("hello_feature", scene_name="main")

    def build(self, host) -> None:
        host.app.add(
            LabelControl(
                "hello_label",
                Rect(24, 24, 320, 32),
                "Hello from gui_do",
            ),
            scene_name="main",
        )


class HelloApp:
    def __init__(self) -> None:
        self.config = HostApplicationConfig(
            display_size=(800, 600),
            window_title="gui_do minimal example",
            fonts={
                "default": {"system": "arial", "size": 16},
                "window": {"system": "arial", "size": 18, "bold": True},
            },
            font_role_specs=(),
            cursors=(),
            scene_specs=(
                SceneSetupSpec(name="main", pretty_name="Main", initial=True),
            ),
            feature_specs=(
                FeatureSpec(attr_name="hello_feature", factory=HelloFeature),
            ),
            window_specs=(),
            runtime_scene_specs=(
                RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),
            ),
            action_specs=(
                ActionSpec(action_id="exit", label="Exit", kind="exit", category="File"),
            ),
            static_accessibility_specs=(),
            initial_scene_name="main",
            telemetry=TelemetryConfig(enabled=False),
            target_fps=120,
        )
        bootstrap_host_application(self, self.config)

    def run(self) -> None:
        self.app.run_entrypoint(target_fps=self.config.target_fps)


if __name__ == "__main__":
    pygame.init()
    try:
        HelloApp().run()
    finally:
        pygame.quit()
```

## Data-Driven Bootstrap and Runtime

[Back to Top](#table-of-contents)

### HostApplicationConfig and bootstrap_host_application

`HostApplicationConfig` is the full declarative input for host bootstrap. It includes display metadata, fonts, scenes, features, window presentation, runtime scene behavior, actions, static accessibility metadata, optional scene roots, telemetry, target fps, and optional palette configuration.

`bootstrap_host_application(host, config)` performs the standard setup sequence:

1. Creates the display surface.
2. Initializes font roles.
3. Creates `GuiApplication`.
4. Registers cursors.
5. Configures telemetry.
6. Applies layout anchor bounds.
7. Creates scenes and scene transitions.
8. Adds `go_to_{scene}` helpers.
9. Creates scene presentation support.
10. Creates any declarative scene roots.
11. Instantiates and registers features and window-presentation bindings.
12. Builds action registry and command palette support.
13. Builds features, syncs initial window visibility, applies runtime-scene setup, and binds feature runtime.

For apps with a lot of entries, `HostApplicationBindingSpec` plus `build_host_application_config()` is often easier than constructing every tuple manually.

### FeatureSpec

`FeatureSpec(attr_name, factory)` declares one host-owned feature. `bootstrap_host_application` instantiates it, stores it on the host at `attr_name`, and registers it with the app.

```python
FeatureSpec(attr_name="editor_feature", factory=EditorFeature)
```

### SceneSetupSpec

`SceneSetupSpec` declares scene name, pretty name, initial-scene status, and transition settings. Use it for user-facing scene structure, not runtime details such as prewarming or pristine assets.

```python
SceneSetupSpec(
    name="dashboard",
    pretty_name="Dashboard",
    initial=True,
)
```

### ActionSpec

`ActionSpec` declares host-level actions such as exit, scene navigation, and palette open actions. The common `kind` values are `"exit"`, `"scene_nav"`, and `"palette_open"`.

```python
import pygame

ActionSpec(
    action_id="palette_open",
    label="Open Command Palette",
    kind="palette_open",
    category="Tools",
    key=pygame.K_F5,
)
```

### WindowSpec

`WindowSpec` is the declarative contract between a feature-owned window and the host presentation model. It captures the feature attribute, toggle attribute, action metadata, and task-panel metadata used to keep window actions and task-panel toggles in sync.

```python
WindowSpec(
    key="inspector",
    feature_attr="_inspector_feature",
    toggle_attr="inspector_toggle_window",
    action_name="toggle_inspector_window",
    action_label="Show Inspector Window",
    task_panel_button_id="inspector_toggle",
    task_panel_label="Inspector",
    task_panel_style="round",
    task_panel_slot_index=2,
    tab_before_showcase=False,
    accessibility_label="Inspector window toggle",
)
```

### RuntimeSceneSpec and Scene Roots

`RuntimeSceneSpec` describes runtime behavior for a scene:

- `pristine_asset` for backdrop restoration
- `bind_escape_to_exit` to bind escape to the exit action for that scene
- `prewarm` to render startup assets early

`SceneRootSpec` lets you declare named scene root panels on the host when you want features to build into a stable scene-owned container.

### Routed Runtime Helpers

For routed features, `setup_routed_runtime(feature, host, spec)` wires the standard runtime resources from one `RoutedRuntimeSpec`. The helper can:

- bind logic aliases
- register action hotkeys
- register control activation keys
- subscribe feature handlers to the event bus
- create `ShortcutHelpOverlay` instances from `ShortcutOverlaySpec`
- register task-panel focus toggles

This is the preferred path when a feature would otherwise contain repetitive `bind_runtime()` code.

For features with companion logic features and lifecycle-scoped runtime specs, `RoutedFeatureLifecycleSpec` pairs with three helpers — `register_routed_feature_companions`, `bind_routed_feature_lifecycle`, and `shutdown_routed_feature_lifecycle` — to orchestrate the full lifecycle declaratively.

## Feature Lifecycle and Messaging

[Back to Top](#table-of-contents)

### Lifecycle Order

The main public hook order is:

1. `on_register`
2. `build`
3. `bind_runtime`
4. `configure_accessibility`
5. frame loop: `handle_event`, `on_update`, `draw`
6. `shutdown_runtime`
7. `on_unregister`

Feature subclasses may also implement `prewarm`, `save_state`, and `restore_state` when those behaviors matter.

### Where Wiring Belongs

- Put control construction in `build()`.
- Put subscriptions, action hookups, event-bus subscriptions, and routed-runtime helpers in `bind_runtime()`.
- Put per-frame logic in `on_update()`.
- Put direct rendering in `draw()` or `draw_direct()` depending on feature type.
- Put cleanup for anything not owned by the feature manager in `shutdown_runtime()`.

### FeatureManager Coordination

`FeatureManager` owns registration order and runs the lifecycle consistently across scenes. That gives you deterministic build and bind ordering, which is important for cross-feature subscriptions, window presentation, and action registration.

### Feature Messaging

Feature-to-feature coordination uses `FeatureMessage` and feature-manager routing:

- `send_message(target_feature_name, message)` for direct feature messages
- `bind_logic()` and `send_logic_message()` for UI-to-logic aliases
- `LogicFeature.on_logic_command()` for command-style logic processing
- `RoutedFeature.message_handlers()` for topic-based routing

Practical guideline: use messages to coordinate features, not direct attribute reach-through, unless a host-level presentation model already exists for that relationship.

## Common Patterns

[Back to Top](#table-of-contents)

### Scene Menu Strip and Task Panel Setup

The demo uses declarative helpers such as `SceneMenuStripSpec`, `SceneTaskPanelSpec`, `TaskPanelButtonSpec`, and helper builders from `data_driven_runtime.py` to keep scene shell setup out of individual control wiring. That is the recommended pattern for menu strips, task panels, scene return buttons, and standard shell controls.

`SceneMenuStripControl` ignores selecting the already active scene, so reselecting the current scene is a no-op instead of triggering a redundant scene switch.

### Window Toggles and Focus-Aware Routing

Use `WindowSpec` entries with `register_window_presentation_specs` (wired automatically by `bootstrap_host_application`) when a window also has an action entry or task-panel toggle. That keeps command palette window toggles, app actions, and task-panel buttons synchronized with actual window visibility.

### Shortcut Help Overlay

`ShortcutHelpOverlay` can be created directly or declared through `ShortcutOverlaySpec` inside `RoutedRuntimeSpec`. Current supported behaviors include:

- manual shortcut lines
- prepending manual shortcuts before registry-generated sections
- showing only manual shortcuts
- excluding section titles
- excluding entry labels
- overlay dismissal on escape and outside click
- modal-style keyboard capture of unhandled keys while open

### Toast Notifications

Toasts are usually published through `app.toasts.show(...)` or `app.toasts.show_persistent(...)`. Clicks on visible toast bounds are consumed intentionally so they do not click through to the scene behind them. If you need a toast to perform an action, pass `on_click=` explicitly.

### Observable State Across Features

Shared `ObservableValue`, `ObservableList`, and `ObservableDict` objects work best when they are owned by one feature or presentation object and observed by others through explicit subscriptions or messages. Keep ownership clear, and do subscription cleanup in your feature runtime lifecycle when the subscription is not managed elsewhere.

## Benefits of Data-Driven Lifecycle Approach

[Back to Top](#table-of-contents)

- Declarative configuration makes application structure visible in one place.
- Features stay small and easier to test because lifecycle hooks have clear roles.
- Build and bind ordering is deterministic.
- Reactive data reduces manual refresh code.
- Scene wiring, transitions, and navigation helpers become repeatable.
- Window presentation and task-panel toggles stay synchronized.
- Routed runtime specs remove repetitive event and overlay plumbing.
- Overlay semantics are centralized instead of reimplemented per feature.
- The architecture scales from one screen to many features without changing patterns.

## FAQ

[Back to Top](#table-of-contents)

**Should I start with direct controls or with features?**

Start with features. Direct controls are public, but they work best as implementation details inside a feature or declarative runtime helper.

**Which lifecycle hook should I use?**

Use `build()` for control creation, `bind_runtime()` for subscriptions and runtime wiring, `handle_event()` for feature-specific input handling, `on_update()` for per-frame logic, and `draw()` only when the feature needs custom rendering.

**How does event routing work?**

gui_do routes events through overlays, focus-aware controls, scene/window hit testing, feature handlers, and fallthrough handlers. In practice that means overlays get first shot, focused or hit controls handle next, and scene-level logic runs after that. For keyboard input, accessibility navigation keys are consumed in focused-control routing (Tab traversal plus focused-control Up/Down accessibility navigation), while non-accessibility keys route focused control first, then active window, then screen lifecycle handlers.

**What overlay behavior should I expect by default?**

Overlays can dismiss on escape, dismiss on outside click, and optionally consume otherwise unhandled keys. Those behaviors are per-overlay options managed by `OverlayManager`.

**Do toast clicks pass through to the scene?**

No. Toast clicks are consumed by default. If you want a toast click to do something, supply `on_click=`.

## See Also

[Back to Top](#table-of-contents)

- [TUTORIAL.md](TUTORIAL.md)
- [docs/public_api_spec.md](docs/public_api_spec.md)
- [docs/package_contracts.md](docs/package_contracts.md)
- [docs/event_system_spec.md](docs/event_system_spec.md)
- [docs/runtime_operating_contracts.md](docs/runtime_operating_contracts.md)
- [docs/architecture_boundary_spec.md](docs/architecture_boundary_spec.md)
- [gui_do/features/data_driven_runtime.py](gui_do/features/data_driven_runtime.py)
- [gui_do/features/feature_lifecycle.py](gui_do/features/feature_lifecycle.py)
- [gui_do/app/gui_application.py](gui_do/app/gui_application.py)
- [gui_do/overlays/overlay_manager.py](gui_do/overlays/overlay_manager.py)
- [gui_do/overlays/shortcut_help_overlay.py](gui_do/overlays/shortcut_help_overlay.py)
- [gui_do/overlays/toast_manager.py](gui_do/overlays/toast_manager.py)
- [demo_features/](demo_features/)
