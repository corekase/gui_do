# gui_do Tutorial

## Introduction

This tutorial builds one continuous project, start to finish, using the current public `gui_do` root API.

Project goal: create a small scene-based app called Pulse Desk with:
- one feature that owns reactive counter state,
- one feature that reacts to that state,
- keyboard actions for fast interaction,
- declarative bootstrap config that stays readable as the project grows.

You will learn both how and why the workflow is designed this way:
- How: concrete file layout, imports, specs, and feature lifecycle methods.
- Why: deterministic runtime routing, declarative composition, and cleanup-safe behavior.

For deeper system details while you work, keep these manual sections open:
- Runtime model: [MANUAL.md#7-architecture-and-runtime-model](MANUAL.md#7-architecture-and-runtime-model)
- Build/bind/update flow: [MANUAL.md#8-core-workflow-build-bind-route-update-draw](MANUAL.md#8-core-workflow-build-bind-route-update-draw)
- Main systems reference: [MANUAL.md#9-main-systems-reference](MANUAL.md#9-main-systems-reference)
- Specifications reference: [MANUAL.md#appendix-f-specifications-and-option-reference](MANUAL.md#appendix-f-specifications-and-option-reference)

## Core Concepts

Before writing code, lock in four ideas.

1. Declarative wiring versus imperative behavior.
- Declarative wiring: use specs (`HostApplicationBindingSpec`, scene/window/action specs, palette specs) to describe runtime structure.
- Imperative behavior: put live logic inside feature methods (`build`, `bind_runtime`, `on_update`, `shutdown_runtime`).
- Why this split matters: the app remains easy to reason about when structure and behavior are separated.

2. Feature lifecycle ownership.
- `build` is for object creation and initial model setup.
- `bind_runtime` is for subscriptions and runtime connections.
- `shutdown_runtime` is for deterministic cleanup.
- Why this matters: cleanup is a contract, not a best-effort guess.

3. Scene-scoped optional facilities.
- Menu strip, task panel, and command palette are opt-in by spec.
- They exist only when declared.
- Why this matters: runtime shape stays explicit and testable.

4. Runtime contracts are practical, not academic.
- Events are normalized before app-level dispatch.
- Scheduler work is bounded by fixed budget rails.
- Workspace restore/report behavior is structured and observable.
- Why this matters: large apps stay predictable under load and easier to diagnose.

See operating details in [docs/runtime_operating_contracts.md](docs/runtime_operating_contracts.md).

## Installation and Setup

From the repository root:

```bash
python -m pip install -e . --no-deps
```

Because editable install is intentionally run with `--no-deps` (to avoid problematic binary dependency builds on Windows), install runtime dependencies manually:

```bash
python -m pip install pygame numpy
```

Create a tutorial workspace folder inside the repo:

```text
tutorial_pulse_desk/
  __init__.py
  features.py
  config.py
  main.py
```

Run with:

```bash
python -m tutorial_pulse_desk.main
```

If your local environment does not already provide runtime dependencies like `pygame`, install the missing dependency in your environment before running.

## Your First Feature

Start with one feature that owns a counter value and prints updates. This first pass proves lifecycle wiring and app bootstrap.

Create [tutorial_pulse_desk/features.py](tutorial_pulse_desk/features.py):

```python
from __future__ import annotations

from gui_do import Feature, ObservableValue


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self.count = ObservableValue(0)
        self._unsubscribe_count = None

    def build(self, host) -> None:
        self.count.value = 0

    def bind_runtime(self, host) -> None:
        self._unsubscribe_count = self.count.subscribe(
            lambda value: print(f"[counter] value={value}")
        )

    def increment(self) -> bool:
        self.count.value += 1
        return True

    def shutdown_runtime(self, host) -> None:
        if callable(self._unsubscribe_count):
            self._unsubscribe_count()
            self._unsubscribe_count = None
```

Now create [tutorial_pulse_desk/config.py](tutorial_pulse_desk/config.py):

```python
from gui_do import (
    ActionBindingSpec,
    HostApplicationBindingSpec,
    WindowToggleBindingSpec,
    build_host_application_config,
)

from tutorial_pulse_desk.features import CounterFeature


TUTORIAL_CONFIG = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1280, 720),
        window_title="Pulse Desk",
        fonts={"default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 14}},
        initial_scene_name="main",
        scene_entries=(("main", "Main"),),
        feature_entries=(("_counter_feature", CounterFeature),),
        window_entries=(
            WindowToggleBindingSpec("main", "_counter_feature", task_panel_slot_index=1),
        ),
        action_entries=(
            ActionBindingSpec(kind="exit", action_id="exit", label="Exit"),
        ),
        static_accessibility_entries=(("exit_button", "Exit"),),
        target_fps=60,
    )
)
```

Create [tutorial_pulse_desk/main.py](tutorial_pulse_desk/main.py):

```python
from gui_do import bootstrap_host_application

from tutorial_pulse_desk.config import TUTORIAL_CONFIG


class PulseDeskApp:
    def __init__(self) -> None:
        bootstrap_host_application(self, TUTORIAL_CONFIG)


if __name__ == "__main__":
    PulseDeskApp().app.run_entrypoint(target_fps=TUTORIAL_CONFIG.target_fps)
```

Why this milestone matters:
- You already have declarative host config.
- You already have lifecycle-safe subscription cleanup.
- Your app entrypoint stays minimal.

## Reactive State: Making the UI Respond

Now improve the first feature by adding derived text and explicit subscription ownership. This is where reactive patterns become practical.

Update [tutorial_pulse_desk/features.py](tutorial_pulse_desk/features.py):

```python
from __future__ import annotations

from gui_do import ComputedValue, Feature, ObservableValue


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self.count = ObservableValue(0)
        self.count_label = ComputedValue(lambda: f"Count: {self.count.value}")
        self._unsubscribe_count = None
        self._unsubscribe_label = None

    def build(self, host) -> None:
        self.count.value = 0

    def bind_runtime(self, host) -> None:
        self._unsubscribe_count = self.count.subscribe(
            lambda value: print(f"[counter] raw value={value}")
        )
        self._unsubscribe_label = self.count_label.subscribe(
            lambda text: print(f"[counter] derived label={text}")
        )

    def increment(self) -> bool:
        self.count.value += 1
        return True

    def reset(self) -> bool:
        self.count.value = 0
        return True

    def shutdown_runtime(self, host) -> None:
        if callable(self._unsubscribe_label):
            self._unsubscribe_label()
            self._unsubscribe_label = None
        if callable(self._unsubscribe_count):
            self._unsubscribe_count()
            self._unsubscribe_count = None
```

Why this is the preferred pattern:
- Use `ObservableValue` for mutable source-of-truth state.
- Use `ComputedValue` for read-only projection logic.
- Keep every subscription paired with deterministic `shutdown_runtime` cleanup.

Related manual context:
- [MANUAL.md#94-state-and-observables](MANUAL.md#94-state-and-observables)
- [MANUAL.md#92-feature-lifecycle-and-feature-types](MANUAL.md#92-feature-lifecycle-and-feature-types)

## Feature Types

As projects grow, choose the feature type by intent:

- `Feature`: default for most behavior with explicit lifecycle methods.
- `LogicFeature`: useful when you need behavior-only units that are not UI surfaces.
- `RoutedFeature`: best when runtime bindings are largely declarative and you want a routed spec-based lifecycle.

Practical rule:
- Start with `Feature`.
- Introduce `LogicFeature` when behavior should be shared or independently testable.
- Introduce `RoutedFeature` when runtime wiring is becoming repetitive and spec-driven.

Minimal reference example:

```python
from gui_do import Feature, LogicFeature, RoutedFeature


class BasicFeature(Feature):
    pass


class SharedLogic(LogicFeature):
    pass


class RoutedPanel(RoutedFeature):
    pass
```

Deep design guidance:
- [MANUAL.md#92-feature-lifecycle-and-feature-types](MANUAL.md#92-feature-lifecycle-and-feature-types)
- [MANUAL.md#5-conceptual-foundations](MANUAL.md#5-conceptual-foundations)

## A Second Feature and Feature Communication

Add a second feature that listens to the counter and publishes a summary line. This gives you feature-to-feature communication without tightly coupling internal modules.

Update [tutorial_pulse_desk/features.py](tutorial_pulse_desk/features.py):

```python
from __future__ import annotations

from gui_do import ComputedValue, Feature, ObservableValue


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self.count = ObservableValue(0)
        self.count_label = ComputedValue(lambda: f"Count: {self.count.value}")
        self._unsubscribe_count = None
        self._unsubscribe_label = None

    def build(self, host) -> None:
        self.count.value = 0

    def bind_runtime(self, host) -> None:
        self._unsubscribe_count = self.count.subscribe(
            lambda value: print(f"[counter] raw value={value}")
        )
        self._unsubscribe_label = self.count_label.subscribe(
            lambda text: print(f"[counter] derived label={text}")
        )

    def increment(self) -> bool:
        self.count.value += 1
        return True

    def reset(self) -> bool:
        self.count.value = 0
        return True

    def shutdown_runtime(self, host) -> None:
        if callable(self._unsubscribe_label):
            self._unsubscribe_label()
            self._unsubscribe_label = None
        if callable(self._unsubscribe_count):
            self._unsubscribe_count()
            self._unsubscribe_count = None


class SummaryFeature(Feature):
    def __init__(self) -> None:
        super().__init__("summary", scene_name="main")
        self.status = ObservableValue("Summary: waiting for updates")
        self._unsubscribe_status = None
        self._unsubscribe_counter = None

    def bind_runtime(self, host) -> None:
        self._unsubscribe_status = self.status.subscribe(
            lambda text: print(f"[summary] {text}")
        )

        counter = host.app.features.get("counter")
        if counter is None:
            return

        self._unsubscribe_counter = counter.count.subscribe(self._on_counter_changed)

    def _on_counter_changed(self, value: int) -> None:
        self.status.value = f"Summary: counter changed to {value}"

    def shutdown_runtime(self, host) -> None:
        if callable(self._unsubscribe_counter):
            self._unsubscribe_counter()
            self._unsubscribe_counter = None
        if callable(self._unsubscribe_status):
            self._unsubscribe_status()
            self._unsubscribe_status = None
```

Then update [tutorial_pulse_desk/config.py](tutorial_pulse_desk/config.py) to register both features:

```python
from gui_do import (
    ActionBindingSpec,
    HostApplicationBindingSpec,
    WindowToggleBindingSpec,
    build_host_application_config,
)

from tutorial_pulse_desk.features import CounterFeature, SummaryFeature


TUTORIAL_CONFIG = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1280, 720),
        window_title="Pulse Desk",
        fonts={"default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 14}},
        initial_scene_name="main",
        scene_entries=(("main", "Main"),),
        feature_entries=(
            ("_counter_feature", CounterFeature),
            ("_summary_feature", SummaryFeature),
        ),
        window_entries=(
            WindowToggleBindingSpec("main", "_counter_feature", task_panel_slot_index=1),
            WindowToggleBindingSpec("main", "_summary_feature", task_panel_slot_index=2),
        ),
        action_entries=(
            ActionBindingSpec(kind="exit", action_id="exit", label="Exit"),
            ActionBindingSpec(
                kind="palette_toggle",
                action_id="palette_toggle",
                label="Toggle Command Palette",
            ),
        ),
        static_accessibility_entries=(("exit_button", "Exit"),),
        target_fps=60,
    )
)
```

Why this communication style works:
- It keeps each feature self-contained.
- It uses public lifecycle hooks only.
- It avoids private imports or hidden runtime dependencies.

## Actions and Keyboard Shortcuts

Now wire keyboard shortcuts for the counter feature with `ActionHotkeySpec` and `register_action_hotkeys`.

Update [tutorial_pulse_desk/features.py](tutorial_pulse_desk/features.py) one more time:

```python
from __future__ import annotations

import pygame

from gui_do import (
    ActionHotkeySpec,
    ComputedValue,
    Feature,
    ObservableValue,
    register_action_hotkeys,
)


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self.count = ObservableValue(0)
        self.count_label = ComputedValue(lambda: f"Count: {self.count.value}")
        self._unsubscribe_count = None
        self._unsubscribe_label = None

    def build(self, host) -> None:
        self.count.value = 0

    def bind_runtime(self, host) -> None:
        self._unsubscribe_count = self.count.subscribe(
            lambda value: print(f"[counter] raw value={value}")
        )
        self._unsubscribe_label = self.count_label.subscribe(
            lambda text: print(f"[counter] derived label={text}")
        )

        register_action_hotkeys(
            host.app.actions,
            (
                ActionHotkeySpec(
                    action_name="counter.increment",
                    handler=lambda _event: self.increment(),
                    key=pygame.K_F2,
                    scene_name="main",
                    global_key=True,
                ),
                ActionHotkeySpec(
                    action_name="counter.reset",
                    handler=lambda _event: self.reset(),
                    key=pygame.K_F3,
                    scene_name="main",
                    global_key=True,
                ),
            ),
        )

    def increment(self) -> bool:
        self.count.value += 1
        return True

    def reset(self) -> bool:
        self.count.value = 0
        return True

    def shutdown_runtime(self, host) -> None:
        if callable(self._unsubscribe_label):
            self._unsubscribe_label()
            self._unsubscribe_label = None
        if callable(self._unsubscribe_count):
            self._unsubscribe_count()
            self._unsubscribe_count = None


class SummaryFeature(Feature):
    def __init__(self) -> None:
        super().__init__("summary", scene_name="main")
        self.status = ObservableValue("Summary: waiting for updates")
        self._unsubscribe_status = None
        self._unsubscribe_counter = None

    def bind_runtime(self, host) -> None:
        self._unsubscribe_status = self.status.subscribe(
            lambda text: print(f"[summary] {text}")
        )

        counter = host.app.features.get("counter")
        if counter is None:
            return

        self._unsubscribe_counter = counter.count.subscribe(self._on_counter_changed)

    def _on_counter_changed(self, value: int) -> None:
        self.status.value = f"Summary: counter changed to {value}"

    def shutdown_runtime(self, host) -> None:
        if callable(self._unsubscribe_counter):
            self._unsubscribe_counter()
            self._unsubscribe_counter = None
        if callable(self._unsubscribe_status):
            self._unsubscribe_status()
            self._unsubscribe_status = None
```

Try it:
- Press F2 to increment the counter.
- Press F3 to reset it.
- Use your palette toggle action to open command palette if configured in your scene.

Related manual sections:
- [MANUAL.md#93-events-actions-input-mapping-and-routing](MANUAL.md#93-events-actions-input-mapping-and-routing)
- [MANUAL.md#98-overlays-dialogs-notifications-and-command-surfaces](MANUAL.md#98-overlays-dialogs-notifications-and-command-surfaces)

## Spec Reference for Builders

These are the most useful builder-facing specs used in this tutorial and in the repository demo architecture.

| Spec or API | What it does | Why you use it |
|---|---|---|
| `HostApplicationBindingSpec` | Declares host-level setup and composition entries | Keeps app assembly declarative and auditable |
| `build_host_application_config` | Materializes a runtime-ready host config | Central conversion point for binding specs |
| `WindowToggleBindingSpec` | Declares scene-window toggle wiring and task panel placement | Keeps window chrome synchronized across facilities |
| `ActionBindingSpec` | Declares high-level actions (`exit`, `scene_nav`, `palette_toggle`) | Standard action behavior without manual glue |
| `ActionHotkeySpec` + `register_action_hotkeys` | Registers named actions and optional key bindings | Explicit keyboard routing with scene/global scope control |
| `Feature` | Base lifecycle unit (`build`, `bind_runtime`, `shutdown_runtime`) | Primary place for app behavior and cleanup ownership |
| `ObservableValue` and `ComputedValue` | Reactive source and derived state | Clear, testable UI-state updates |
| `bootstrap_host_application` | Applies config to a host instance | Keeps entrypoint simple and consistent |

For deeper spec breadth and option matrices, use:
- [MANUAL.md#appendix-f-specifications-and-option-reference](MANUAL.md#appendix-f-specifications-and-option-reference)
- [MANUAL.md#appendix-d-api-quick-index-by-topic](MANUAL.md#appendix-d-api-quick-index-by-topic)

## Complete Project Listing

Final file tree:

```text
tutorial_pulse_desk/
  __init__.py
  features.py
  config.py
  main.py
```

Final [tutorial_pulse_desk/features.py](tutorial_pulse_desk/features.py):

```python
from __future__ import annotations

import pygame

from gui_do import (
    ActionHotkeySpec,
    ComputedValue,
    Feature,
    ObservableValue,
    register_action_hotkeys,
)


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter", scene_name="main")
        self.count = ObservableValue(0)
        self.count_label = ComputedValue(lambda: f"Count: {self.count.value}")
        self._unsubscribe_count = None
        self._unsubscribe_label = None

    def build(self, host) -> None:
        self.count.value = 0

    def bind_runtime(self, host) -> None:
        self._unsubscribe_count = self.count.subscribe(
            lambda value: print(f"[counter] raw value={value}")
        )
        self._unsubscribe_label = self.count_label.subscribe(
            lambda text: print(f"[counter] derived label={text}")
        )

        register_action_hotkeys(
            host.app.actions,
            (
                ActionHotkeySpec(
                    action_name="counter.increment",
                    handler=lambda _event: self.increment(),
                    key=pygame.K_F2,
                    scene_name="main",
                    global_key=True,
                ),
                ActionHotkeySpec(
                    action_name="counter.reset",
                    handler=lambda _event: self.reset(),
                    key=pygame.K_F3,
                    scene_name="main",
                    global_key=True,
                ),
            ),
        )

    def increment(self) -> bool:
        self.count.value += 1
        return True

    def reset(self) -> bool:
        self.count.value = 0
        return True

    def shutdown_runtime(self, host) -> None:
        if callable(self._unsubscribe_label):
            self._unsubscribe_label()
            self._unsubscribe_label = None
        if callable(self._unsubscribe_count):
            self._unsubscribe_count()
            self._unsubscribe_count = None


class SummaryFeature(Feature):
    def __init__(self) -> None:
        super().__init__("summary", scene_name="main")
        self.status = ObservableValue("Summary: waiting for updates")
        self._unsubscribe_status = None
        self._unsubscribe_counter = None

    def bind_runtime(self, host) -> None:
        self._unsubscribe_status = self.status.subscribe(
            lambda text: print(f"[summary] {text}")
        )

        counter = host.app.features.get("counter")
        if counter is None:
            return

        self._unsubscribe_counter = counter.count.subscribe(self._on_counter_changed)

    def _on_counter_changed(self, value: int) -> None:
        self.status.value = f"Summary: counter changed to {value}"

    def shutdown_runtime(self, host) -> None:
        if callable(self._unsubscribe_counter):
            self._unsubscribe_counter()
            self._unsubscribe_counter = None
        if callable(self._unsubscribe_status):
            self._unsubscribe_status()
            self._unsubscribe_status = None
```

Final [tutorial_pulse_desk/config.py](tutorial_pulse_desk/config.py):

```python
from gui_do import (
    ActionBindingSpec,
    HostApplicationBindingSpec,
    WindowToggleBindingSpec,
    build_host_application_config,
)

from tutorial_pulse_desk.features import CounterFeature, SummaryFeature


TUTORIAL_CONFIG = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1280, 720),
        window_title="Pulse Desk",
        fonts={"default": {"file": "demo_features/data/fonts/Gimbot.ttf", "size": 14}},
        initial_scene_name="main",
        scene_entries=(("main", "Main"),),
        feature_entries=(
            ("_counter_feature", CounterFeature),
            ("_summary_feature", SummaryFeature),
        ),
        window_entries=(
            WindowToggleBindingSpec("main", "_counter_feature", task_panel_slot_index=1),
            WindowToggleBindingSpec("main", "_summary_feature", task_panel_slot_index=2),
        ),
        action_entries=(
            ActionBindingSpec(kind="exit", action_id="exit", label="Exit"),
            ActionBindingSpec(
                kind="palette_toggle",
                action_id="palette_toggle",
                label="Toggle Command Palette",
            ),
        ),
        static_accessibility_entries=(("exit_button", "Exit"),),
        target_fps=60,
    )
)
```

Final [tutorial_pulse_desk/main.py](tutorial_pulse_desk/main.py):

```python
from gui_do import bootstrap_host_application

from tutorial_pulse_desk.config import TUTORIAL_CONFIG


class PulseDeskApp:
    def __init__(self) -> None:
        bootstrap_host_application(self, TUTORIAL_CONFIG)


if __name__ == "__main__":
    PulseDeskApp().app.run_entrypoint(target_fps=TUTORIAL_CONFIG.target_fps)
```

## Next Steps

You now have a clean baseline using public root imports and lifecycle-safe reactive patterns.

Suggested expansions:
1. Add scene bundles with navigation actions using `SceneBundleBindingSpec`.
2. Add command palette custom entries for domain actions and status commands.
3. Introduce `AppStateStore` for cross-feature state snapshots and transactions.
4. Add persistence via workspace state and snapshot migration specs.
5. Add tests around hotkey behavior, feature cleanup, and scene-scoped routing guarantees.

When you move into those expansions, use MANUAL sections 9 through 12 and Appendix F as your reference map.
