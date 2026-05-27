## Introduction

This tutorial walks through the repository’s runnable demo as one continuous project. The goal is not just to show isolated API calls, but to explain how the pieces in [gui_do_demo.py](gui_do_demo.py), [demo_features/demo_config.py](demo_features/demo_config.py), and the feature packages under [demo_features/](demo_features) fit together.

The tutorial follows the same design stance as the codebase and the manual:

- use the root package exports from `gui_do` as the supported application surface;
- assemble runtime behavior from declarative specs whenever the framework already provides that path;
- treat subscriptions, feature-owned state, and routed work as lifecycle-managed resources;
- keep the demo organized by feature package, not by one-off modules.

For deeper subsystem coverage while you read, keep [MANUAL.md](MANUAL.md#title-and-purpose) open. The manual explains the architecture and the export tiers in more depth; this tutorial focuses on the sequence of decisions that gets the demo running.

Why this section now: before writing any feature code, you need the mental model for where the host lives, where feature packages live, and why the public API is intentionally tiered.

## Core Concepts

The repo’s demo is built around four concepts that recur throughout the rest of the tutorial.

1. The host bootstraps the application through `bootstrap_host_application()` and a host config built from spec objects.
2. Feature packages own scene-level behavior, runtime bindings, and any helper modules they need.
3. Observable state carries data through the runtime without requiring every consumer to poll.
4. Routed and logic features split communication and update work into ownership-aware pieces.

The public root package is the preferred import surface. That is the reason the examples in this tutorial use names such as `Feature`, `DirectFeature`, `LogicFeature`, `RoutedFeature`, `ObservableValue`, `ActionManager`, and `KeyChordManager` from `gui_do` instead of importing from private submodules.

An inferred minimal skeleton looks like this:

```python
from gui_do import Feature, ObservableValue


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self.count = ObservableValue(0)

    def increment(self) -> int:
        self.count.value += 1
        return self.count.value
```

Expected runtime outcome: the feature owns its state, and any observer subscribed to `count` can react when the value changes.

Caution: observable state is only useful when ownership is clear. If a feature creates subscriptions or background work, it should also define where that work is released.

Evidence: the repo’s feature packages, the root exports in [gui_do/__init__.py](gui_do/__init__.py), and the runtime contracts in [docs/runtime_operating_contracts.md](docs/runtime_operating_contracts.md).

## Installation and Setup

Install the project in editable mode without automatic dependency resolution:

```bash
python -m pip install -e . --no-deps
```

Then install the discovered dependencies manually:

- `pygame`
- `numpy`
- `coverage` if you plan to run the test and coverage workflow

Manual installation matters on Windows because binary dependency builds can be fragile, and the repository intentionally avoids forcing a wheel/build decision during the editable install step.

After installation, run the demo entrypoint from the repository root:

```bash
python gui_do_demo.py
```

Expected runtime outcome: the demo opens using the configuration assembled in `demo_features/demo_config.py`.

Troubleshooting: if the app fails before opening a window, check that `pygame` and `numpy` are installed in the active environment and that the editable install was done from the repository root.

Why this section now: once the environment can launch the demo, every later step becomes easy to verify against a real runtime instead of a hypothetical one.

## Your First Feature

The first feature in the demo is the main-scene feature. It is the place where the host’s scene surface gets built and where the runtime behavior for the main scene is bound.

The repository entrypoint stays thin:

```python
from gui_do import bootstrap_host_application

from demo_features.demo_config import DEMO_BOOTSTRAP_CONFIG


class GuiDoDemo:
    """Interactive demo app showcasing gui_do controls and scene workflows."""

    def __init__(self) -> None:
        bootstrap_host_application(self, DEMO_BOOTSTRAP_CONFIG)


if __name__ == "__main__":
    GuiDoDemo().app.run_entrypoint(target_fps=DEMO_BOOTSTRAP_CONFIG.target_fps)
```

The main feature itself is built as a normal `Feature` subclass. In the repo, [demo_features/main/main_feature.py](demo_features/main/main_feature.py) does two things that matter for this tutorial:

- `build()` calls a helper that constructs the main scene surface;
- `bind_runtime()` wires the runtime spec, including the exit key behavior for the main scene.

An excerpted version of that pattern is:

```python
from gui_do import Feature, ShortcutHelpOverlay, ToastSeverity


class MainFeature(Feature):
    HOST_REQUIREMENTS = {
        "build": ("app", "screen_rect", "scene_presentation", "window_presentation", "action_registry"),
        "bind_runtime": ("app",),
    }

    def __init__(self) -> None:
        super().__init__("main_demo", scene_name="main")
        self._help_overlay: ShortcutHelpOverlay | None = None

    def build(self, host) -> None:
        ...

    def bind_runtime(self, host) -> None:
        ...
```

Expected runtime outcome: the main scene becomes the host’s entry scene, the scene surface is constructed, and the runtime hooks are installed before the update loop begins.

Troubleshooting: if the scene does not appear, verify that `initial_scene_name` in the demo config points at a declared scene bundle and that the feature entry name matches the bootstrap config.

Milestone listing so far:

- `gui_do_demo.py`
- `demo_features/demo_config.py`
- `demo_features/main/main_feature.py`

## Reactive State: Making the UI Respond

This section explains how the demo keeps values reactive instead of manually copying state through every layer. The repository’s showcase feature is the clearest example because it combines `ObservableValue` with an observable effect spec.

The direct pattern in [demo_features/showcase/showcase_feature.py](demo_features/showcase/showcase_feature.py) is:

```python
from gui_do import ObservableValue, ObservableEffectSpec, RoutedRuntimeSpec


class ShowcaseFeature(...):
    def __init__(self, rect=None) -> None:
        ...
        self._live_slider_value = ObservableValue(float(self.SLIDER_DEFAULT_VALUE))

    def bind_runtime(self, host) -> None:
        runtime_spec = RoutedRuntimeSpec(
            scene_name=_CONTROLS_RUNTIME_SPEC.scene_name,
            task_panel_focus_toggles=tuple(_CONTROLS_RUNTIME_SPEC.task_panel_focus_toggles),
            command_palette=_CONTROLS_RUNTIME_SPEC.command_palette,
            global_pointer_actions=tuple(_CONTROLS_RUNTIME_SPEC.global_pointer_actions),
            observable_effects=(
                ObservableEffectSpec(
                    handler=self._on_live_slider_value,
                    observable_attr_name="_live_slider_value",
                    invoke_immediately=True,
                ),
            ),
        )
```

That tells the runtime to re-run the handler when the observable value changes, and it also requests an immediate first invocation so the UI starts from a consistent state.

An inferred cleanup pattern for a feature-owned subscription looks like this:

```python
from gui_do import ObservableValue


class CounterFeature:
    def __init__(self) -> None:
        self.count = ObservableValue(0)
        self._release_callbacks = []

    def bind(self) -> None:
        unsubscribe = self.count.subscribe(self._on_count_changed)
        self._release_callbacks.append(unsubscribe)

    def shutdown(self) -> None:
        for release in self._release_callbacks:
            release()
        self._release_callbacks.clear()

    def _on_count_changed(self, value: int) -> None:
        ...
```

Expected runtime outcome: the observer sees updates while the feature is active, and teardown releases the subscription deterministically.

Caution: do not let a subscription outlive the feature that created it. The runtime contracts explicitly care about teardown discipline, so this is not a cosmetic detail.

Troubleshooting: if a handler keeps firing after a feature is gone, check whether the subscription is stored in the feature’s runtime scope or released in shutdown.

Milestone listing at this point:

- `gui_do_demo.py`
- `demo_features/demo_config.py`
- `demo_features/main/main_feature.py`
- `demo_features/showcase/showcase_feature.py`

## Feature Types

The repo uses different feature base classes for different jobs:

- `Feature` for ordinary scene-owned feature logic and lifecycle hooks;
- `DirectFeature` for drawing and update work that acts directly on the frame surface;
- `LogicFeature` for companion logic that registers runnable tasks or algorithm work;
- `RoutedFeature` for features that exchange structured messages with other parts of the runtime.

The demo gives one real example of each. `MainFeature` is a `Feature`. `MovingShapesBackdropFeature` is a `DirectFeature` that animates and draws cached sprites. `MandelbrotLogicFeature` is a `LogicFeature` that registers iterative and recursive Mandelbrot tasks. `LifeFeature` is a `RoutedFeature` that owns the Conway’s Game of Life window and message handling.

An inferred public-surface example of the four base classes is:

```python
from gui_do import DirectFeature, Feature, FeatureMessage, LogicFeature, RoutedFeature


class SceneFeature(Feature):
    ...


class BackdropFeature(DirectFeature):
    ...


class AlgorithmFeature(LogicFeature):
    ...


class RoutedSceneFeature(RoutedFeature):
    def message_handlers(self):
        return {"demo.topic": self._on_message}

    def _on_message(self, _host, message: FeatureMessage) -> None:
        ...
```

Expected runtime outcome: each feature type receives the lifecycle and routing support it is designed for, instead of inheriting a one-size-fits-all API.

Why this distinction matters: the feature base class is a design signal. When the runtime work is mostly visual and immediate, `DirectFeature` fits better; when the work is logic-only and reusable, `LogicFeature` keeps it separated; when messages or lifecycle events must cross a boundary, `RoutedFeature` makes the contract explicit.

Troubleshooting: if a feature feels overcomplicated, the most common mistake is using the wrong base class and then compensating with ad hoc hooks. Move the behavior to the closest matching feature type first.

## A Second Feature and Feature Communication

The demo becomes more interesting once the first scene is no longer alone. The repository’s second major story is feature communication, and the clearest example is the pairing between the Life feature and its logic companion.

In [demo_features/life/life_feature.py](demo_features/life/life_feature.py), the routed feature declares message handlers and updates local state when the companion logic sends back data:

```python
from gui_do import FeatureMessage, RoutedFeature, WindowControl


class LifeFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("life_simulation", scene_name="main")
        self.life_cells = set()

    def message_handlers(self):
        return {
            "life.logic": self._handle_life_logic_message,
        }

    def _handle_life_logic_message(self, _host, message: FeatureMessage) -> None:
        if message.event != "life.state":
            return
        cells = message.get("cells")
        if cells is not None:
            self.life_cells = set(cells)
```

The companion logic feature in [demo_features/mandelbrot/mandelbrot_logic_feature.py](demo_features/mandelbrot/mandelbrot_logic_feature.py) shows the other side of the split: a `LogicFeature` registers runnable work during `bind_runtime()` and keeps the computational heavy lifting separate from presentation.

An inferred communication pattern that mirrors the repo is:

```python
from gui_do import FeatureMessage, LogicFeature, RoutedFeature


class LogicPart(LogicFeature):
    def bind_runtime(self, host) -> None:
        ...


class ViewPart(RoutedFeature):
    def message_handlers(self):
        return {"demo.logic": self._on_logic_message}

    def _on_logic_message(self, _host, message: FeatureMessage) -> None:
        self.latest_value = message.get("value")
```

Expected runtime outcome: the logic feature can process work independently while the routed feature reacts to the resulting messages and keeps presentation state in sync.

Troubleshooting: if the UI is not updating, check the topic name first. A routed feature only receives the messages it declares a handler for, and mismatched topics fail silently by design.

Milestone listing now includes the second feature path:

- `gui_do_demo.py`
- `demo_features/demo_config.py`
- `demo_features/main/main_feature.py`
- `demo_features/showcase/showcase_feature.py`
- `demo_features/life/life_feature.py`
- `demo_features/mandelbrot/mandelbrot_logic_feature.py`

Why this section now: once one feature can talk to another, you can separate compute from presentation without inventing new coupling rules for every subsystem.

## Actions and Keyboard Shortcuts

The demo’s command and shortcut layer uses the public action and input APIs to keep behavior explicit. The main ideas are:

- `ActionBindingSpec` and `build_action_specs()` normalize declarative action declarations;
- `ActionManager` stores action handlers and key bindings;
- `InputMap` records one-step key bindings;
- `KeyChordManager` handles multi-step chords.

The repository already exercises these APIs in tests. A compact example from [tests/test_new_factory_utilities.py](tests/test_new_factory_utilities.py) is:

```python
from gui_do import ActionBindingSpec, ActionSpec, build_action_specs


passthrough = ActionSpec(
    action_id="custom",
    label="Custom",
    kind="scene_nav",
    target="main",
    category="Scenes",
)

built = build_action_specs(
    (
        ActionBindingSpec(kind="exit", action_id="exit", label="Exit", category="File"),
        ActionBindingSpec(kind="scene_nav", action_id="nav_tools", label="Go Tools", target="tools", category="Scenes"),
        ActionBindingSpec(kind="palette_toggle", action_id="palette_toggle", label="Toggle Command Palette (F5)"),
        passthrough,
    )
)
```

The imperative side of the API is just as direct:

```python
from gui_do import ActionManager, ChordStep, InputMap, KeyChord, KeyChordManager


actions = ActionManager()
actions.register_action("file.save", lambda event: True)
actions.bind_key(83, "file.save")

shortcuts = InputMap()
shortcuts.declare("file.save", key=83, label="Save")

chords = KeyChordManager(actions)
chords.bind(KeyChord([ChordStep(75, 4), ChordStep(67, 4)]), "file.save")
```

Expected runtime outcome: actions can be triggered from keyboard input, scene navigation actions can be generated from bindings, and multi-step chords remain separate from single-key shortcuts.

Caution: use `InputMap` for declarative bindings and `ActionManager` for dispatch. Mixing the two responsibilities makes it harder to reason about who owns the shortcut state.

Troubleshooting: if a shortcut does not fire, check the binding order and the action id first. The tests show that duplicate binds may be ignored, missing targets are rejected, and unknown kinds raise errors.

Milestone listing:

- `demo_features/demo_config.py` declares the demo actions.
- `tests/test_action_middleware_and_theme_manager.py` and `tests/test_input_map_and_chord.py` cover the public shortcut behavior.

## Spec Reference for Builders

This section is a reference for the builder functions that assemble the demo’s runtime configuration. The important takeaway is that the builders do validation and normalization, while the binding specs remain the human-authored description of what should exist.

The most important builders for the demo are:

- `build_host_application_config()` for the top-level runtime config;
- `build_scene_bundle_specs()` for scene, runtime-scene, root, and navigation spec assembly;
- `build_feature_window_bundle_specs()` for pairing features with windows and task-panel entries;
- `build_action_specs()` for validating and normalizing action declarations;
- `build_window_toggle_specs()` for scene/window visibility wiring;
- `build_scene_setup_specs()` and `build_runtime_scene_specs()` for scene-local runtime assembly.

The repository’s tests show the builder contract clearly. A direct example from [tests/test_new_factory_utilities.py](tests/test_new_factory_utilities.py) is:

```python
from gui_do import (
    ActionBindingSpec,
    CursorBindingSpec,
    HostApplicationBindingSpec,
    RuntimeSceneBindingSpec,
    SceneBundleBindingSpec,
    SceneTransitionStyle,
    TelemetryConfig,
    WindowToggleBindingSpec,
    build_host_application_config,
)


config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(800, 600),
        window_title="Test App",
        fonts={"default": {"file": "font.ttf", "size": 12}},
        initial_scene_name="main",
        scene_entries=(("main", "Main"),),
        feature_entries=(("_main_feature", object()),),
        window_entries=(WindowToggleBindingSpec("main", "_main_feature", task_panel_slot_index=1),),
        runtime_scene_entries=(RuntimeSceneBindingSpec("main", "asset.png", True, False),),
        action_entries=(ActionBindingSpec(kind="exit", action_id="exit", label="Exit"),),
        static_accessibility_entries=(("exit_button", "Exit"),),
        font_role_entries=(("title", 14, "default"),),
        cursor_entries=(CursorBindingSpec("normal", "cursor.png", (1, 1)),),
        scene_default_transition_style=SceneTransitionStyle.FADE,
        scene_default_transition_duration=0.25,
        telemetry=TelemetryConfig(enabled=False),
        target_fps=144,
    )
)
```

Expected runtime outcome: the builder returns a normalized config object whose derived scene, feature, action, cursor, and telemetry specs are ready for bootstrap.

Troubleshooting: if a builder raises a validation error, check the field family first. Most builder failures come from a missing scene target, an unsupported action kind, or a bundle entry that does not match the expected shape.

Why this section now: at this point in the tutorial, you already know what the app is doing; the builder reference explains how the repo turns a declarative description into the runtime object graph.

## Complete Project Listing

This is the runnable project that the tutorial has been describing.

```text
.
├── gui_do_demo.py
├── MANUAL.md
├── README.md
├── TUTORIAL.md
├── docs/
│   ├── architecture.md
│   ├── architecture_boundary_spec.md
│   ├── demo_feature_layout.md
│   ├── event_system_spec.md
│   ├── library_demo_separation_contract.md
│   ├── package_contracts.md
│   ├── public_api_spec.md
│   ├── runtime_operating_contracts.md
│   └── unified_layout_spec.md
├── demo_features/
│   ├── __init__.py
│   ├── demo_config.py
│   ├── data/
│   ├── life/
│   │   ├── __init__.py
│   │   ├── life_feature.py
│   │   ├── life_logic_feature.py
│   │   ├── life_logic_helpers.py
│   │   ├── life_presenter.py
│   │   ├── life_runtime_helpers.py
│   │   └── life_specs.py
│   ├── main/
│   │   ├── __init__.py
│   │   ├── main_build_helpers.py
│   │   ├── main_feature.py
│   │   └── main_specs.py
│   ├── mandelbrot/
│   │   ├── __init__.py
│   │   ├── mandelbrot_canvas_helpers.py
│   │   ├── mandelbrot_feature.py
│   │   ├── mandelbrot_logic_feature.py
│   │   ├── mandelbrot_presenter.py
│   │   ├── mandelbrot_runtime_helpers.py
│   │   ├── mandelbrot_scheduling_helpers.py
│   │   ├── mandelbrot_specs.py
│   │   └── mandelbrot_status_event.py
│   ├── moving_shapes/
│   │   ├── __init__.py
│   │   ├── moving_shapes_backdrop_feature.py
│   │   ├── moving_shapes_specs.py
│   │   └── shape_sprite_state.py
│   ├── showcase/
│   │   ├── __init__.py
│   │   ├── showcase_advanced_helpers.py
│   │   ├── showcase_basics_helpers.py
│   │   ├── showcase_data_helpers.py
│   │   ├── showcase_extended_helpers.py
│   │   ├── showcase_feature.py
│   │   ├── showcase_helpers.py
│   │   ├── showcase_inspectable.py
│   │   ├── showcase_runtime_helpers.py
│   │   └── showcase_specs.py
│   └── systems/
│       ├── __init__.py
│       ├── systems_commands.py
│       ├── systems_data_helpers.py
│       ├── systems_feature.py
│       ├── systems_graphics_helpers.py
│       ├── systems_helpers.py
│       ├── systems_history_helpers.py
│       ├── systems_infrastructure_helpers.py
│       ├── systems_models.py
│       ├── systems_motion_helpers.py
│       ├── systems_persistence_helpers.py
│       ├── systems_presenter.py
│       ├── systems_scheduling_helpers.py
│       ├── systems_state_helpers.py
│       ├── systems_text_helpers.py
│       ├── systems_theme_helpers.py
│       └── systems_validation_helpers.py
├── gui_do/
│   ├── __init__.py
│   ├── _version.py
│   └── ... tiered subsystem packages matching the export surface
├── tests/
│   ├── test_public_api_exports.py
│   ├── test_public_api_docs_contracts.py
│   ├── test_package_contracts_public_api.py
│   └── ... contract and behavior coverage for the runtime, builders, and demo features
└── pyproject.toml
```

The important structural takeaway is that each feature package keeps its own public boundary in `__init__.py`, while bootstrap orchestration stays in `demo_features/demo_config.py`.

Expected runtime outcome: if you follow this layout in a new app, you get a consistent import boundary, predictable feature ownership, and a demo structure that maps directly to the runtime contract documents.

Troubleshooting: when a project starts to feel unstructured, check whether feature-specific code has leaked out of its package root. That is usually the first sign the runtime boundaries are getting blurry.

## Next Steps

1. Read [MANUAL.md](MANUAL.md#how-to-use-this-manual) for the subsystem reference and the export-tier guidance.
2. Review [docs/runtime_operating_contracts.md](docs/runtime_operating_contracts.md) before changing routing, focus, layout, or teardown behavior.
3. Run [gui_do_demo.py](gui_do_demo.py) after you make a change so the demo remains the final integration check.
