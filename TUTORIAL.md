# gui_do Tutorial: Build Pulse Desk

## Introduction

This tutorial builds one continuous project, Pulse Desk, to teach `gui_do` from startup bootstrap through feature communication and action routing.

Labeling policy used in this document:

- Blocks marked "Introspected anchor" are adapted directly from current repository code/tests/docs patterns.
- Blocks marked "Inferred example" are minimal valid tutorial constructions derived from those verified patterns.

You will build:

- A `RoutedFeature` that owns reactive state.
- A second `RoutedFeature` that receives cross-feature messages.
- A small keyboard/action layer with `ActionRegistry` and `InputMap`.
- A spec-driven host config bootstrapped by `build_host_application_config` and `bootstrap_host_application`.

Why this project shape:

- It mirrors how this repository’s demo keeps entrypoints thin and pushes composition into config/spec code.
- It gives you both a baseline path and an advanced refinement path while keeping one narrative.

Introspected anchor (from `gui_do_demo.py`, adapted verbatim usage):

```python
from gui_do import bootstrap_host_application
from demo_features.demo_config import DEMO_BOOTSTRAP_CONFIG


class GuiDoDemo:
    def __init__(self) -> None:
        bootstrap_host_application(self, DEMO_BOOTSTRAP_CONFIG)
```

Expected outcome after this tutorial: you can structure a maintainable `gui_do` application without relying on private/internal imports.

Troubleshooting note:

- If you are unsure whether a symbol is public, verify it exists on the root `gui_do` import surface before using it.

Verification cues:

- `tests/test_core_only_bootstrap_contracts.py`
- `tests/test_runtime_operating_contracts.py`
- `docs/runtime_operating_contracts.md`

Why this step now: before coding, you need a clear target architecture so each subsequent section adds one capability without hidden assumptions.

## Core Concepts

Pulse Desk uses four concepts throughout the entire build.

1. Bootstrap is declarative.
2. Features own behavior and lifecycle hooks.
3. Messages connect features without tight coupling.
4. Runtime ownership requires explicit cleanup discipline.

### Concept 1: Declarative bootstrap

`HostApplicationBindingSpec` captures host-level wiring, then `build_host_application_config` normalizes all shorthand into runtime-ready specs.

Introspected anchor (adapted from `demo_features/demo_config.py`):

```python
from gui_do import (
    HostApplicationBindingSpec,
    SceneBundleBindingSpec,
    build_host_application_config,
)

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1280, 720),
        window_title="Pulse Desk",
        fonts={"default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 14}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(scene_name="main", make_initial=True),
        ),
    )
)
```

### Concept 2: Feature types

`gui_do` supports multiple feature styles; the repository demo uses all three frequently.

- `DirectFeature`: direct event/update/draw path (used by moving-shapes backdrop).
- `LogicFeature`: command-driven domain logic.
- `RoutedFeature`: message-topic handler map plus runtime wiring.

Introspected anchor (adapted from `demo_features/moving_shapes/moving_shapes_backdrop_feature.py`):

```python
from gui_do import DirectFeature


class MovingBackdrop(DirectFeature):
    def on_direct_update(self, host, dt_seconds: float) -> None:
        pass

    def draw_direct(self, host, surface, theme) -> None:
        pass
```

### Concept 3: Message envelopes

`FeatureMessage` provides normalized payload access (`topic`, `command`, `event`).

Introspected anchor (adapted from `tests/test_feature_lifecycle_classes.py`):

```python
from gui_do import FeatureMessage

msg = FeatureMessage(sender="a", target="b", payload={"topic": "activity.append", "value": 3})
assert msg.topic == "activity.append"
assert msg.get("value") == 3
```

### Concept 4: Ownership and cleanup

Subscriptions should always be released predictably during runtime shutdown.

Introspected anchor (adapted from `tests/test_observable_value_binding_invalidation.py` behavior):

```python
from gui_do import ObservableValue

count = ObservableValue(0)
unsubscribe = count.subscribe(lambda value: print(value))
# ... later in shutdown path
unsubscribe()
```

Troubleshooting note:

- If a callback appears to fire after feature teardown, verify every subscription has a corresponding unsubscribe path in `shutdown_runtime`.

Verification cues:

- `tests/test_feature_lifecycle_classes.py`
- `tests/test_observable_value_binding_invalidation.py`

Why this step now: these concepts define every implementation decision in later sections.

## Installation and Setup

Install editable source without dependency resolution first:

```bash
python -m pip install -e . --no-deps
```

Then install dependencies manually because `--no-deps` skips them.

Runtime dependencies discovered from `pyproject.toml`:

- `pygame>=2.0`
- `numpy>=1.24`

Install command:

```bash
python -m pip install "pygame>=2.0" "numpy>=1.24"
```

Optional tooling discovered from repository dependency files:

- `coverage`
- `pytest`

Optional install command:

```bash
python -m pip install coverage pytest
```

Why manual dependency installation is called out explicitly:

- On Windows, binary dependency builds can fail for environment-specific reasons.
- Installing dependencies directly gives clearer control and faster troubleshooting than relying on implicit transitive resolution.

Create this tutorial workspace layout:

```text
pulse_desk/
  __init__.py
  features/
    __init__.py
    pulse_feature.py
run_pulse_desk.py
```

Initial package files:

```python
# pulse_desk/__init__.py
"""Pulse Desk tutorial package."""
```

```python
# pulse_desk/features/__init__.py
"""Feature package for the Pulse Desk tutorial."""
```

Troubleshooting note:

- If `python -m pip install -e . --no-deps` succeeds but imports fail at runtime, install runtime dependencies manually first before debugging feature code.

Verification cues:

- `pyproject.toml`
- `requirements-ci.txt`
- [MANUAL.md](MANUAL.md#4-feature-organization-conventions)

Why this step now: a stable environment and folder boundary prevent false errors while we add actual runtime behavior.

## Your First Feature

Now we implement the first feature, `PulseFeature`, as a `RoutedFeature` with a reactive counter.

Problem framing:

- We need one feature that owns local state and can report updates to other features.

Implementation file:

Inferred example (derived from verified `RoutedFeature`, `ObservableValue`, and message-routing patterns in demo features and lifecycle tests):

```python
# pulse_desk/features/pulse_feature.py
from gui_do import ObservableValue, RoutedFeature


class PulseFeature(RoutedFeature):
    """Owns a reactive counter and emits activity messages."""

    def __init__(self) -> None:
        super().__init__("pulse_counter", scene_name="main")
        self.count = ObservableValue(0)
        self._count_unsubscribe = None

    def bind_runtime(self, host) -> None:
        # Lifecycle-safe subscription: retained and explicitly released in shutdown_runtime.
        self._count_unsubscribe = self.count.subscribe(lambda value: self._emit_activity(value))

    def shutdown_runtime(self, host) -> None:
        if callable(self._count_unsubscribe):
            self._count_unsubscribe()
            self._count_unsubscribe = None

    def increment(self) -> None:
        self.count.value = int(self.count.value) + 1

    def _emit_activity(self, value: int) -> None:
        self.send_message(
            "activity_feed",
            {"topic": "activity.append", "line": f"Pulse incremented to {value}"},
        )
```

Checkpoint:

- You now have a feature with lifecycle-safe reactive behavior.
- No UI controls yet, but state and outbound messaging are in place.

Milestone listing (first runnable shell):

```python
# run_pulse_desk.py
from gui_do import bootstrap_host_application
from pulse_desk.config import PULSE_CONFIG


class PulseDeskApp:
    def __init__(self) -> None:
        bootstrap_host_application(self, PULSE_CONFIG)


if __name__ == "__main__":
    PulseDeskApp().app.run_entrypoint(target_fps=PULSE_CONFIG.target_fps)
```

Troubleshooting note:

- Calling `send_message` before feature registration raises runtime errors. Keep message sends inside lifecycle hooks or user actions that run after bootstrap.

Verification cues:

- `gui_do/features/feature_lifecycle.py` (`Feature.send_message`, `RoutedFeature`)
- `tests/test_feature_lifecycle_classes.py`

Why this step now: this creates the smallest meaningful unit that later sections can observe, route, and automate.

## Reactive State: Making the UI Respond

Next, refine the first feature by introducing transactional state for derived data.

Problem framing:

- Raw counters are useful, but we also want a stable state snapshot and atomically-updated metadata.

Implementation update:

Inferred example (derived from verified `AppStateStore` and `StateTransaction` behavior in tests):

```python
# pulse_desk/features/pulse_feature.py
from gui_do import AppStateStore, ObservableValue, RoutedFeature, StateTransaction


class PulseFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("pulse_counter", scene_name="main")
        self.count = ObservableValue(0)
        self.store = AppStateStore({"count": 0, "status": "idle"})
        self._count_unsubscribe = None

    def bind_runtime(self, host) -> None:
        self._count_unsubscribe = self.count.subscribe(self._on_count_changed)

    def shutdown_runtime(self, host) -> None:
        if callable(self._count_unsubscribe):
            self._count_unsubscribe()
            self._count_unsubscribe = None

    def increment(self) -> None:
        self.count.value = int(self.count.value) + 1

    def _on_count_changed(self, value: int) -> None:
        with StateTransaction(self.store):
            self.store.dispatch({"count": int(value)})
            self.store.dispatch({"status": "active" if int(value) > 0 else "idle"})
        self._emit_activity(int(value))

    def _emit_activity(self, value: int) -> None:
        self.send_message(
            "activity_feed",
            {"topic": "activity.append", "line": f"Pulse incremented to {value}"},
        )
```

Runtime behavior and ownership semantics:

- `ObservableValue` notifies on value changes.
- `StateTransaction` ensures grouped state patches commit atomically.
- Subscription teardown remains explicit in `shutdown_runtime`.

Introspected anchor (adapted from `tests/test_app_state_store.py`):

```python
from gui_do import AppStateStore, StateTransaction

store = AppStateStore({"a": 0, "b": 0})
with StateTransaction(store):
    store.dispatch({"a": 1})
    store.dispatch({"b": 2})
```

Checkpoint:

- Counter changes now update both observable and store-backed state safely.

Troubleshooting note:

- If you see partial updates, make sure grouped `dispatch` calls happen inside one `StateTransaction` context.

Verification cues:

- `tests/test_observable_value_binding_invalidation.py`
- `tests/test_app_state_store.py`
- [MANUAL.md](MANUAL.md#94-state-and-observables)

Why this step now: reactive and transactional state gives us reliable data to share with additional features.

## Feature Types

Before adding the second feature, clarify when to choose each feature type.

### Minimal examples

```python
from gui_do import DirectFeature, LogicFeature, RoutedFeature


class BackgroundRenderFeature(DirectFeature):
    def on_direct_update(self, host, dt_seconds: float) -> None:
        pass


class DomainMathFeature(LogicFeature):
    def on_logic_command(self, host, message) -> None:
        pass


class WindowOrchestrationFeature(RoutedFeature):
    def message_handlers(self):
        return {"topic.name": self._handle_topic}

    def _handle_topic(self, host, message) -> None:
        pass
```

Applied guidance for Pulse Desk:

- Keep `PulseFeature` as `RoutedFeature` because it reacts to topic messages and runtime hooks.
- Keep any pure transformation service as `LogicFeature` when command routing is dominant.
- Add `DirectFeature` only if you need direct draw/update loops that bypass control pipelines.

Common mistake:

- Putting domain logic and rendering logic into one large `Feature` class makes teardown and testing harder.

Troubleshooting note:

- If your feature has no `message_handlers` topics but still subclasses `RoutedFeature`, consider whether `Feature` or `LogicFeature` is a cleaner fit.

Verification cues:

- `demo_features/moving_shapes/moving_shapes_backdrop_feature.py`
- `demo_features/life/life_feature.py`
- `demo_features/life/life_logic_feature.py`
- [MANUAL.md](MANUAL.md#92-feature-lifecycle-and-feature-types)

Why this step now: type boundaries reduce design churn before we wire inter-feature communication.

## A Second Feature and Feature Communication

Now add `ActivityFeature`, then connect it to `PulseFeature` message output.

Problem framing:

- We need a second feature that receives updates without directly reaching into first-feature internals.

Implementation file:

Inferred example (derived from verified `RoutedFeature.message_handlers` usage in demo features):

```python
# pulse_desk/features/activity_feature.py
from gui_do import RoutedFeature


class ActivityFeature(RoutedFeature):
    """Receives pulse activity lines and keeps a bounded feed."""

    def __init__(self) -> None:
        super().__init__("activity_feed", scene_name="main")
        self.lines: list[str] = []

    def message_handlers(self):
        return {
            "activity.append": self._on_activity_append,
            "activity.clear": self._on_activity_clear,
        }

    def _on_activity_append(self, host, message) -> None:
        line = str(message.get("line", ""))
        if not line:
            return
        self.lines.append(line)
        self.lines = self.lines[-10:]

    def _on_activity_clear(self, host, message) -> None:
        self.lines.clear()
```

Update config to register both features:

Inferred example (derived from verified host bootstrap binding patterns in `demo_features/demo_config.py`):

```python
# pulse_desk/config.py
from gui_do import (
    ActionBindingSpec,
    HostApplicationBindingSpec,
    SceneBundleBindingSpec,
    build_host_application_config,
)

from pulse_desk.features.activity_feature import ActivityFeature
from pulse_desk.features.pulse_feature import PulseFeature


PULSE_CONFIG = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1280, 720),
        window_title="Pulse Desk",
        fonts={"default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 14}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(
                scene_name="main",
                make_initial=True,
                emit_nav_action_spec=False,
                pristine_asset="demo_features/data/images/backdrop.jpg",
                prewarm=True,
            ),
        ),
        feature_entries=(
            ("pulse_feature", PulseFeature),
            ("activity_feature", ActivityFeature),
        ),
        action_entries=(
            ActionBindingSpec(kind="exit", action_id="exit", label="Exit", category="File"),
            ActionBindingSpec(kind="palette_toggle", action_id="palette_toggle", label="Toggle Command Palette"),
        ),
        target_fps=60,
    )
)
```

Introspected anchor for routed message handling (adapted from `demo_features/life/life_feature.py`):

```python
from gui_do import FeatureMessage, RoutedFeature


class RoutedSample(RoutedFeature):
    def message_handlers(self):
        return {"logic.topic": self._handle_logic}

    def _handle_logic(self, host, message: FeatureMessage) -> None:
        if message.event == "state":
            pass
```

Checkpoint:

- Incrementing pulse state now emits feed lines to the second feature.

Troubleshooting note:

- If communication fails silently, verify target feature names exactly match constructor names (`pulse_counter`, `activity_feed`).

Verification cues:

- `gui_do/features/feature_lifecycle.py` (`FeatureManager.send_message`)
- `tests/test_feature_lifecycle_classes.py`
- [MANUAL.md](MANUAL.md#99-scene-window-and-task-panel-presentation-models)

Why this step now: once two features communicate through message contracts, you have the core architecture pattern used by larger `gui_do` applications.

## Actions and Keyboard Shortcuts

Now add a reusable action layer that can trigger project behavior from keyboard shortcuts.

Problem framing:

- We need stable action descriptors for command surfaces and separately managed key bindings for user overrides.

Implementation file:

Inferred example (derived from verified `ActionRegistry` and `InputMap` behavior in source/tests):

```python
# pulse_desk/actions.py
import pygame

from gui_do import ActionManager, ActionRegistry, InputMap


def build_action_system(increment_callback):
    actions = ActionManager()
    registry = ActionRegistry()
    keymap = InputMap()

    registry.declare(
        "pulse.increment",
        "Increment Pulse",
        callback=lambda context, event: increment_callback() or True,
        category="Pulse",
        shortcut_hint="Ctrl+I",
        description="Increase pulse count by one.",
    )

    registry.bind_into(actions)

    keymap.declare("pulse.increment", key=pygame.K_i, mod=pygame.KMOD_CTRL, label="Increment Pulse")
    keymap.apply(actions)

    return actions, registry, keymap
```

How this integrates with project lifecycle:

- Build action system after bootstrap, once feature instances exist.
- Bind callback to `PulseFeature.increment`.

Introspected anchor (adapted from `gui_do/actions/input_map.py` and tests):

```python
from gui_do import ActionManager, InputMap

actions = ActionManager()
imap = InputMap()
imap.declare("edit.copy", key=67, mod=64, label="Copy")
imap.apply(actions)
```

Checkpoint:

- You have one canonical action definition and one keyboard mapping path.

Failure modes and recovery:

- Binding reserved accessibility keys (for example Tab) is blocked by action routing safeguards.
- If a key does not trigger, verify the action is registered before `InputMap.apply`.

Troubleshooting note:

- If callbacks appear to do nothing, confirm your callback returns truthy or a meaningful side effect and that the correct `ActionManager` instance is used.

Verification cues:

- `tests/test_action_registry_and_input_map.py`
- `tests/test_input_map_and_chord.py`
- [MANUAL.md](MANUAL.md#93-events-actions-input-mapping-and-routing)

Why this step now: after feature communication is working, action routing gives you user-facing control entry points.

## Spec Reference for Builders

This section summarizes the spec builders you used and when to choose each.

### API map used in this tutorial

- `HostApplicationBindingSpec`: top-level host declaration.
- `SceneBundleBindingSpec`: scene setup/runtime/action/root bundle shorthand.
- `ActionBindingSpec`: high-level action declarations for common kinds.
- `build_host_application_config`: normalizes shorthand into a runtime-ready config.
- `bootstrap_host_application`: materializes display, app, features, actions, and scene helpers.

### Minimal builder path (baseline)

```python
from gui_do import (
    HostApplicationBindingSpec,
    SceneBundleBindingSpec,
    build_host_application_config,
)

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1280, 720),
        window_title="Pulse Desk",
        fonts={"default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 14}},
        initial_scene_name="main",
        scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
    )
)
```

### Applied refinement path (production-friendly)

Add explicit runtime defaults and action declarations as your app grows:

- Use `prewarm=True` for scenes where first draw latency matters.
- Add `ActionBindingSpec` entries for command palette and explicit scene navigation.
- Keep scene/feature naming consistent to avoid routing mismatches.

Common mistake:

- Mixing inconsistent scene names across features, scene bundles, and action targets.

Troubleshooting note:

- If bootstrap succeeds but behavior is missing, inspect your generated config object first; most issues originate from incomplete spec declarations.

Verification cues:

- `demo_features/demo_config.py`
- `tests/test_data_driven_runtime_specs.py`
- [MANUAL.md](MANUAL.md#91-application-bootstrap-and-host-configuration)
- [MANUAL.md](MANUAL.md#8-core-workflow-build-bind-route-update-draw)

Why this step now: a spec map consolidates everything built so far and prepares you to reason about complete listings.

## Complete Project Listing

This section shows the full final project with all tutorial steps integrated.

Inferred complete listing (assembled from the verified patterns used in earlier sections).

```python
# pulse_desk/__init__.py
"""Pulse Desk tutorial package."""
```

```python
# pulse_desk/features/__init__.py
"""Feature package for the Pulse Desk tutorial."""
```

```python
# pulse_desk/features/pulse_feature.py
from gui_do import AppStateStore, ObservableValue, RoutedFeature, StateTransaction


class PulseFeature(RoutedFeature):
    """Owns a reactive counter and emits activity messages."""

    def __init__(self) -> None:
        super().__init__("pulse_counter", scene_name="main")
        self.count = ObservableValue(0)
        self.store = AppStateStore({"count": 0, "status": "idle"})
        self._count_unsubscribe = None

    def bind_runtime(self, host) -> None:
        self._count_unsubscribe = self.count.subscribe(self._on_count_changed)

    def shutdown_runtime(self, host) -> None:
        if callable(self._count_unsubscribe):
            self._count_unsubscribe()
            self._count_unsubscribe = None

    def increment(self) -> None:
        self.count.value = int(self.count.value) + 1

    def _on_count_changed(self, value: int) -> None:
        with StateTransaction(self.store):
            self.store.dispatch({"count": int(value)})
            self.store.dispatch({"status": "active" if int(value) > 0 else "idle"})
        self.send_message(
            "activity_feed",
            {"topic": "activity.append", "line": f"Pulse incremented to {value}"},
        )
```

```python
# pulse_desk/features/activity_feature.py
from gui_do import RoutedFeature


class ActivityFeature(RoutedFeature):
    """Receives pulse activity lines and keeps a bounded feed."""

    def __init__(self) -> None:
        super().__init__("activity_feed", scene_name="main")
        self.lines: list[str] = []

    def message_handlers(self):
        return {
            "activity.append": self._on_activity_append,
            "activity.clear": self._on_activity_clear,
        }

    def _on_activity_append(self, host, message) -> None:
        line = str(message.get("line", ""))
        if not line:
            return
        self.lines.append(line)
        self.lines = self.lines[-10:]

    def _on_activity_clear(self, host, message) -> None:
        self.lines.clear()
```

```python
# pulse_desk/actions.py
import pygame

from gui_do import ActionManager, ActionRegistry, InputMap


def build_action_system(increment_callback):
    actions = ActionManager()
    registry = ActionRegistry()
    keymap = InputMap()

    registry.declare(
        "pulse.increment",
        "Increment Pulse",
        callback=lambda context, event: increment_callback() or True,
        category="Pulse",
        shortcut_hint="Ctrl+I",
        description="Increase pulse count by one.",
    )

    registry.bind_into(actions)

    keymap.declare("pulse.increment", key=pygame.K_i, mod=pygame.KMOD_CTRL, label="Increment Pulse")
    keymap.apply(actions)

    return actions, registry, keymap
```

```python
# pulse_desk/config.py
from gui_do import (
    ActionBindingSpec,
    HostApplicationBindingSpec,
    SceneBundleBindingSpec,
    build_host_application_config,
)

from pulse_desk.features.activity_feature import ActivityFeature
from pulse_desk.features.pulse_feature import PulseFeature


PULSE_CONFIG = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1280, 720),
        window_title="Pulse Desk",
        fonts={"default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 14}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(
                scene_name="main",
                make_initial=True,
                emit_nav_action_spec=False,
                pristine_asset="demo_features/data/images/backdrop.jpg",
                prewarm=True,
            ),
        ),
        feature_entries=(
            ("pulse_feature", PulseFeature),
            ("activity_feature", ActivityFeature),
        ),
        action_entries=(
            ActionBindingSpec(kind="exit", action_id="exit", label="Exit", category="File"),
            ActionBindingSpec(kind="palette_toggle", action_id="palette_toggle", label="Toggle Command Palette"),
        ),
        target_fps=60,
    )
)
```

```python
# run_pulse_desk.py
from gui_do import bootstrap_host_application

from pulse_desk.config import PULSE_CONFIG


class PulseDeskApp:
    def __init__(self) -> None:
        bootstrap_host_application(self, PULSE_CONFIG)


if __name__ == "__main__":
    app = PulseDeskApp()

    # Optional integration: wire local action system after bootstrap.
    from pulse_desk.actions import build_action_system

    pulse_feature = app.app.features.get("pulse_counter")
    if pulse_feature is not None:
        app._local_actions, app._local_registry, app._local_keymap = build_action_system(pulse_feature.increment)

    app.app.run_entrypoint(target_fps=PULSE_CONFIG.target_fps)
```

Milestone validation checklist:

- App bootstraps from one config object.
- `PulseFeature` updates state and emits message envelopes.
- `ActivityFeature` receives topic messages and maintains bounded history.
- Action system can invoke `PulseFeature.increment` through a declared action.

Troubleshooting note:

- If local action shortcuts are not reflected in app-wide routing, wire the same `ActionRegistry`/`InputMap` concepts into your app-level action manager path once your integration design is finalized.

Why this step now: this is the synchronized snapshot before moving to extension paths.

## Next Steps

You now have a complete baseline project and an advanced refinement path.

Recommended continuation order:

1. Add visible controls and bind them to `PulseFeature.increment` and `ActivityFeature.lines`.
2. Promote local action wiring into app-level action routing so key handling shares one manager.
3. Add persistence (`WorkspacePersistenceManager`, snapshots, or settings) for count/feed restoration.
4. Add telemetry and diagnostics hooks for update/message timing.
5. Extend scene model with additional `SceneBundleBindingSpec` entries and explicit navigation actions.

Deep-link references for those expansions:

- [MANUAL.md](MANUAL.md#91-application-bootstrap-and-host-configuration)
- [MANUAL.md](MANUAL.md#92-feature-lifecycle-and-feature-types)
- [MANUAL.md](MANUAL.md#93-events-actions-input-mapping-and-routing)
- [MANUAL.md](MANUAL.md#911-persistence-and-workspacesession-state)
- [MANUAL.md](MANUAL.md#916-telemetry-introspection-and-operational-hooks)

Final caution:

- Keep imports on the root `gui_do` surface in application code to stay aligned with public-surface stability policy and reduce migration cost as internals evolve.
