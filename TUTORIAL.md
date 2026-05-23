# Introduction

This tutorial builds one continuous gui_do project from start to finish: a keyboard-driven task tracker with two features.

You will learn how to:

1. Bootstrap a host app from declarative specs.
2. Build features with lifecycle-owned runtime wiring.
3. Add reactive state with cleanup-safe subscriptions.
4. Connect features with message routing.
5. Register actions and keyboard shortcuts with routed runtime specs.

The tutorial focuses on practical implementation and why each design choice is made. For deeper subsystem reference, use [MANUAL.md](MANUAL.md), especially [Main Systems Reference](MANUAL.md#main-systems-reference) and [Architecture and Runtime Model](MANUAL.md#architecture-and-runtime-model).

# Core Concepts

Before writing code, lock in the mental model:

1. Declarative wiring: host composition is described by specs like SceneSetupSpec, RuntimeSceneSpec, FeatureSpec, and ActionBindingSpec.
2. Imperative behavior: feature classes own runtime behavior (on_update, message handling, actions).
3. Lifecycle ownership: setup_routed_runtime and shutdown_routed_runtime define where subscriptions and registrations should live and die.
4. Scene isolation: runtime behavior is scoped per scene; optional facilities only exist when declared.
5. Stable API surface: import from gui_do package root, not submodules.

These concepts map directly to runtime contracts documented in [docs/runtime_operating_contracts.md](docs/runtime_operating_contracts.md) and system chapters in [MANUAL.md](MANUAL.md#main-systems-reference).

# Installation and Setup

Install the project in editable mode without automatic dependency installation:

```bash
python -m pip install -e . --no-deps
```

Because --no-deps skips dependency installation, install discovered runtime dependencies manually:

- pygame>=2.0
- numpy>=1.24

Optional local CI/test tooling discovered from repository dependency files:

- coverage

Why manual dependencies are called out explicitly: binary dependency builds can be problematic on Windows, so controlling dependency installation directly helps you avoid unexpected build-toolchain issues.

Create a folder for tutorial files:

```text
tutorial_project/
  app.py
  tasks_feature.py
```

# Your First Feature

We start with one feature that tracks the number of created tasks.

Create tutorial_project/tasks_feature.py:

```python
from gui_do import RoutedFeature, RoutedRuntimeSpec, setup_routed_runtime, shutdown_routed_runtime


class TasksFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("tasks", scene_name="main")
        self.task_total = 0

    def bind_runtime(self, host) -> None:
        setup_routed_runtime(
            self,
            host,
            RoutedRuntimeSpec(scene_name="main"),
        )

    def shutdown_runtime(self, host) -> None:
        shutdown_routed_runtime(self, host)

    def add_task(self, event=None) -> bool:
        self.task_total += 1
        print(f"[tasks] total={self.task_total}")
        return True
```

Now wire a host app in tutorial_project/app.py:

```python
from gui_do import (
    ActionBindingSpec,
    FeatureSpec,
    HostApplicationBindingSpec,
    RuntimeSceneSpec,
    SceneSetupSpec,
    bootstrap_host_application,
    build_host_application_config,
)

from tasks_feature import TasksFeature


class TutorialHost:
    def __init__(self) -> None:
        config = build_host_application_config(
            HostApplicationBindingSpec(
                display_size=(1280, 720),
                window_title="gui_do tutorial project",
                fonts={"default": None},
                initial_scene_name="main",
                scene_entries=(
                    SceneSetupSpec(name="main", pretty_name="Main", make_initial=True),
                ),
                runtime_scene_entries=(
                    RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),
                ),
                feature_entries=(
                    FeatureSpec(attr_name="tasks_feature", factory=TasksFeature),
                ),
                action_entries=(
                    ActionBindingSpec(kind="exit", action_id="exit", label="Exit", category="File"),
                ),
                target_fps=60,
            )
        )
        bootstrap_host_application(self, config)


if __name__ == "__main__":
    TutorialHost().app.run_entrypoint(target_fps=60)
```

Why this is the right first milestone:

1. You establish scene/runtime declarations up front.
2. You keep behavior in a feature class instead of global script state.
3. You get lifecycle-safe runtime setup and teardown from day one.

For deeper host bootstrapping details, see [MANUAL.md: Application Bootstrap and Host Configuration](MANUAL.md#application-bootstrap-and-host-configuration).

# Reactive State: Making the UI Respond

Next, convert primitive counters to reactive values so downstream behavior can subscribe safely.

Update tutorial_project/tasks_feature.py:

```python
from gui_do import (
    ComputedValue,
    ObservableValue,
    RoutedFeature,
    RoutedRuntimeSpec,
    setup_routed_runtime,
    shutdown_routed_runtime,
)


class TasksFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("tasks", scene_name="main")
        self.task_total = ObservableValue(0)
        self.completed_total = ObservableValue(0)
        self.completion_ratio = ComputedValue(
            lambda: 0.0
            if self.task_total.value == 0
            else self.completed_total.value / self.task_total.value
        )
        self._unsub_task_total = None
        self._unsub_completion_ratio = None

    def bind_runtime(self, host) -> None:
        setup_routed_runtime(self, host, RoutedRuntimeSpec(scene_name="main"))

        # Subscription cleanup is explicit and lifecycle-owned.
        self._unsub_task_total = self.task_total.subscribe(self._on_task_total_changed)
        self._unsub_completion_ratio = self.completion_ratio.subscribe(self._on_completion_ratio_changed)

    def shutdown_runtime(self, host) -> None:
        if callable(self._unsub_task_total):
            self._unsub_task_total()
            self._unsub_task_total = None
        if callable(self._unsub_completion_ratio):
            self._unsub_completion_ratio()
            self._unsub_completion_ratio = None
        shutdown_routed_runtime(self, host)

    def add_task(self, event=None) -> bool:
        self.task_total.value = self.task_total.value + 1
        return True

    def complete_task(self, event=None) -> bool:
        if self.task_total.value == 0:
            return False
        self.completed_total.value = min(self.completed_total.value + 1, self.task_total.value)
        return True

    def _on_task_total_changed(self, value: int) -> None:
        print(f"[tasks] task_total={value}")

    def _on_completion_ratio_changed(self, value: float) -> None:
        print(f"[tasks] completion_ratio={value:.2f}")
```

Why this change matters:

1. ObservableValue gives explicit change boundaries.
2. ComputedValue centralizes derived state instead of duplicating arithmetic.
3. Stored unsubscribe callables make cleanup behavior obvious during shutdown.

For more on reactive data and lifecycle ownership, see [MANUAL.md: State and Observables](MANUAL.md#state-and-observables) and [MANUAL.md: Feature Lifecycle and Feature Types](MANUAL.md#feature-lifecycle-and-feature-types).

# Feature Types

gui_do exposes four key feature styles for different behavior shapes:

1. Feature: base lifecycle hooks.
2. DirectFeature: direct event/update/draw integration.
3. LogicFeature: message-command driven logic.
4. RoutedFeature: topic-routed message handling plus routed runtime helpers.

In this project we use RoutedFeature because we want action hotkeys, scoped runtime wiring, and topic-based communication. Keep this practical rule:

1. Start with Feature for simple state-only behavior.
2. Move to RoutedFeature when you need declarative runtime services, key bindings, or cross-feature messaging.
3. Use DirectFeature for low-level render loops that intentionally bypass control pipelines.
4. Use LogicFeature for domain modules that mostly consume command messages.

See [MANUAL.md: Feature Lifecycle and Feature Types](MANUAL.md#feature-lifecycle-and-feature-types) for extended patterns and tradeoffs.

# A Second Feature and Feature Communication

Now add a second feature that listens for task updates from TasksFeature.

Create tutorial_project/stats_feature.py:

```python
from gui_do import ObservableValue, RoutedFeature, RoutedRuntimeSpec, setup_routed_runtime, shutdown_routed_runtime


class StatsFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("stats", scene_name="main")
        self.summary_line = ObservableValue("No task updates yet.")
        self._unsub_summary = None

    def bind_runtime(self, host) -> None:
        setup_routed_runtime(self, host, RoutedRuntimeSpec(scene_name="main"))
        self._unsub_summary = self.summary_line.subscribe(self._on_summary_changed)

    def shutdown_runtime(self, host) -> None:
        if callable(self._unsub_summary):
            self._unsub_summary()
            self._unsub_summary = None
        shutdown_routed_runtime(self, host)

    def message_handlers(self):
        return {
            "tasks.changed": self._handle_tasks_changed,
        }

    def _handle_tasks_changed(self, host, message) -> None:
        count = int(message.get("count", 0))
        completed = int(message.get("completed", 0))
        self.summary_line.value = f"Tasks: {count}, Completed: {completed}"

    def _on_summary_changed(self, line: str) -> None:
        print(f"[stats] {line}")
```

Update tutorial_project/tasks_feature.py to publish messages:

```python
from gui_do import (
    ComputedValue,
    ObservableValue,
    RoutedFeature,
    RoutedRuntimeSpec,
    setup_routed_runtime,
    shutdown_routed_runtime,
)


class TasksFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("tasks", scene_name="main")
        self.task_total = ObservableValue(0)
        self.completed_total = ObservableValue(0)
        self.completion_ratio = ComputedValue(
            lambda: 0.0
            if self.task_total.value == 0
            else self.completed_total.value / self.task_total.value
        )
        self._unsub_task_total = None
        self._unsub_completion_ratio = None

    def bind_runtime(self, host) -> None:
        setup_routed_runtime(self, host, RoutedRuntimeSpec(scene_name="main"))
        self._unsub_task_total = self.task_total.subscribe(self._on_task_total_changed)
        self._unsub_completion_ratio = self.completion_ratio.subscribe(self._on_completion_ratio_changed)

    def shutdown_runtime(self, host) -> None:
        if callable(self._unsub_task_total):
            self._unsub_task_total()
            self._unsub_task_total = None
        if callable(self._unsub_completion_ratio):
            self._unsub_completion_ratio()
            self._unsub_completion_ratio = None
        shutdown_routed_runtime(self, host)

    def add_task(self, event=None) -> bool:
        self.task_total.value = self.task_total.value + 1
        self._publish_counts()
        return True

    def complete_task(self, event=None) -> bool:
        if self.task_total.value == 0:
            return False
        self.completed_total.value = min(self.completed_total.value + 1, self.task_total.value)
        self._publish_counts()
        return True

    def _publish_counts(self) -> None:
        self.send_message(
            "stats",
            {
                "topic": "tasks.changed",
                "count": self.task_total.value,
                "completed": self.completed_total.value,
            },
        )

    def _on_task_total_changed(self, value: int) -> None:
        print(f"[tasks] task_total={value}")

    def _on_completion_ratio_changed(self, value: float) -> None:
        print(f"[tasks] completion_ratio={value:.2f}")
```

Update tutorial_project/app.py to register both features:

```python
from gui_do import (
    ActionBindingSpec,
    FeatureSpec,
    HostApplicationBindingSpec,
    RuntimeSceneSpec,
    SceneSetupSpec,
    bootstrap_host_application,
    build_host_application_config,
)

from stats_feature import StatsFeature
from tasks_feature import TasksFeature


class TutorialHost:
    def __init__(self) -> None:
        config = build_host_application_config(
            HostApplicationBindingSpec(
                display_size=(1280, 720),
                window_title="gui_do tutorial project",
                fonts={"default": None},
                initial_scene_name="main",
                scene_entries=(
                    SceneSetupSpec(name="main", pretty_name="Main", make_initial=True),
                ),
                runtime_scene_entries=(
                    RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),
                ),
                feature_entries=(
                    FeatureSpec(attr_name="tasks_feature", factory=TasksFeature),
                    FeatureSpec(attr_name="stats_feature", factory=StatsFeature),
                ),
                action_entries=(
                    ActionBindingSpec(kind="exit", action_id="exit", label="Exit", category="File"),
                ),
                target_fps=60,
            )
        )
        bootstrap_host_application(self, config)


if __name__ == "__main__":
    TutorialHost().app.run_entrypoint(target_fps=60)
```

Why this pattern scales:

1. Features keep independent state ownership.
2. Communication uses stable topic messages instead of direct tight coupling.
3. Each feature still cleans up its own subscriptions.

For architecture context, review [MANUAL.md: Core Workflow: Build, Bind, Route, Update, Draw](MANUAL.md#core-workflow-build-bind-route-update-draw) and [MANUAL.md: Integration Patterns and Composition Recipes](MANUAL.md#integration-patterns-and-composition-recipes).

# Actions and Keyboard Shortcuts

Now connect hotkeys so the app is interactive immediately:

1. N adds a task.
2. D marks one task completed.

Update tutorial_project/tasks_feature.py:

```python
import pygame

from gui_do import (
    ActionHotkeySpec,
    ComputedValue,
    ObservableValue,
    RoutedFeature,
    RoutedRuntimeSpec,
    setup_routed_runtime,
    shutdown_routed_runtime,
)


class TasksFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("tasks", scene_name="main")
        self.task_total = ObservableValue(0)
        self.completed_total = ObservableValue(0)
        self.completion_ratio = ComputedValue(
            lambda: 0.0
            if self.task_total.value == 0
            else self.completed_total.value / self.task_total.value
        )
        self._unsub_task_total = None
        self._unsub_completion_ratio = None

    def bind_runtime(self, host) -> None:
        setup_routed_runtime(
            self,
            host,
            RoutedRuntimeSpec(
                scene_name="main",
                action_hotkeys=(
                    ActionHotkeySpec(
                        action_name="tasks.add",
                        handler=self.add_task,
                        key=pygame.K_n,
                        scene_name="main",
                        global_key=True,
                    ),
                    ActionHotkeySpec(
                        action_name="tasks.complete",
                        handler=self.complete_task,
                        key=pygame.K_d,
                        scene_name="main",
                        global_key=True,
                    ),
                ),
            ),
        )
        self._unsub_task_total = self.task_total.subscribe(self._on_task_total_changed)
        self._unsub_completion_ratio = self.completion_ratio.subscribe(self._on_completion_ratio_changed)

    def shutdown_runtime(self, host) -> None:
        if callable(self._unsub_task_total):
            self._unsub_task_total()
            self._unsub_task_total = None
        if callable(self._unsub_completion_ratio):
            self._unsub_completion_ratio()
            self._unsub_completion_ratio = None
        shutdown_routed_runtime(self, host)

    def add_task(self, event=None) -> bool:
        self.task_total.value = self.task_total.value + 1
        self._publish_counts()
        return True

    def complete_task(self, event=None) -> bool:
        if self.task_total.value == 0:
            return False
        self.completed_total.value = min(self.completed_total.value + 1, self.task_total.value)
        self._publish_counts()
        return True

    def _publish_counts(self) -> None:
        self.send_message(
            "stats",
            {
                "topic": "tasks.changed",
                "count": self.task_total.value,
                "completed": self.completed_total.value,
            },
        )

    def _on_task_total_changed(self, value: int) -> None:
        print(f"[tasks] task_total={value}")

    def _on_completion_ratio_changed(self, value: float) -> None:
        print(f"[tasks] completion_ratio={value:.2f}")
```

Run the app, then press N and D to drive updates. You should see task and stats output lines in the console.

For deeper action/input routing details, see [MANUAL.md: Events, Actions, Input Mapping, and Routing](MANUAL.md#events-actions-input-mapping-and-routing).

# Spec Reference for Builders

These are the key specs used in this tutorial and why each exists:

| Spec / API | Purpose | Why it helps |
| --- | --- | --- |
| HostApplicationBindingSpec | Single declarative input for host build | Keeps startup wiring explicit and testable |
| build_host_application_config | Converts binding spec into full host config | Centralizes defaulting and normalization |
| SceneSetupSpec | Declares scene identity and transition metadata | Makes scene ownership explicit |
| RuntimeSceneSpec | Declares runtime behavior flags per scene | Enables scene-level runtime controls |
| FeatureSpec | Registers a feature factory on host + app | Decouples composition from concrete class imports in bootstrap logic |
| ActionBindingSpec | Declares host-level actions (exit, scene nav, palette toggle) | Keeps core actions visible at config layer |
| RoutedRuntimeSpec | Declarative runtime wiring for routed features | Packs hotkeys, subscriptions, and runtime faculties into one contract |
| ActionHotkeySpec | Action registration + optional key bind | Reduces ad hoc key-handling code |

When to use declarative vs imperative:

1. Declarative specs for composition, registration, and static wiring.
2. Imperative feature methods for behavior, domain rules, and runtime decision logic.

For broader spec depth, use [MANUAL.md: Appendix F: Specifications and Option Reference](MANUAL.md#appendix-f-specifications-and-option-reference).

# Complete Project Listing

Final runnable tutorial project:

tutorial_project/app.py

```python
from gui_do import (
    ActionBindingSpec,
    FeatureSpec,
    HostApplicationBindingSpec,
    RuntimeSceneSpec,
    SceneSetupSpec,
    bootstrap_host_application,
    build_host_application_config,
)

from stats_feature import StatsFeature
from tasks_feature import TasksFeature


class TutorialHost:
    def __init__(self) -> None:
        config = build_host_application_config(
            HostApplicationBindingSpec(
                display_size=(1280, 720),
                window_title="gui_do tutorial project",
                fonts={"default": None},
                initial_scene_name="main",
                scene_entries=(
                    SceneSetupSpec(name="main", pretty_name="Main", make_initial=True),
                ),
                runtime_scene_entries=(
                    RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),
                ),
                feature_entries=(
                    FeatureSpec(attr_name="tasks_feature", factory=TasksFeature),
                    FeatureSpec(attr_name="stats_feature", factory=StatsFeature),
                ),
                action_entries=(
                    ActionBindingSpec(kind="exit", action_id="exit", label="Exit", category="File"),
                ),
                target_fps=60,
            )
        )
        bootstrap_host_application(self, config)


if __name__ == "__main__":
    TutorialHost().app.run_entrypoint(target_fps=60)
```

tutorial_project/tasks_feature.py

```python
import pygame

from gui_do import (
    ActionHotkeySpec,
    ComputedValue,
    ObservableValue,
    RoutedFeature,
    RoutedRuntimeSpec,
    setup_routed_runtime,
    shutdown_routed_runtime,
)


class TasksFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("tasks", scene_name="main")
        self.task_total = ObservableValue(0)
        self.completed_total = ObservableValue(0)
        self.completion_ratio = ComputedValue(
            lambda: 0.0
            if self.task_total.value == 0
            else self.completed_total.value / self.task_total.value
        )
        self._unsub_task_total = None
        self._unsub_completion_ratio = None

    def bind_runtime(self, host) -> None:
        setup_routed_runtime(
            self,
            host,
            RoutedRuntimeSpec(
                scene_name="main",
                action_hotkeys=(
                    ActionHotkeySpec(
                        action_name="tasks.add",
                        handler=self.add_task,
                        key=pygame.K_n,
                        scene_name="main",
                        global_key=True,
                    ),
                    ActionHotkeySpec(
                        action_name="tasks.complete",
                        handler=self.complete_task,
                        key=pygame.K_d,
                        scene_name="main",
                        global_key=True,
                    ),
                ),
            ),
        )
        self._unsub_task_total = self.task_total.subscribe(self._on_task_total_changed)
        self._unsub_completion_ratio = self.completion_ratio.subscribe(self._on_completion_ratio_changed)

    def shutdown_runtime(self, host) -> None:
        if callable(self._unsub_task_total):
            self._unsub_task_total()
            self._unsub_task_total = None
        if callable(self._unsub_completion_ratio):
            self._unsub_completion_ratio()
            self._unsub_completion_ratio = None
        shutdown_routed_runtime(self, host)

    def add_task(self, event=None) -> bool:
        self.task_total.value = self.task_total.value + 1
        self._publish_counts()
        return True

    def complete_task(self, event=None) -> bool:
        if self.task_total.value == 0:
            return False
        self.completed_total.value = min(self.completed_total.value + 1, self.task_total.value)
        self._publish_counts()
        return True

    def _publish_counts(self) -> None:
        self.send_message(
            "stats",
            {
                "topic": "tasks.changed",
                "count": self.task_total.value,
                "completed": self.completed_total.value,
            },
        )

    def _on_task_total_changed(self, value: int) -> None:
        print(f"[tasks] task_total={value}")

    def _on_completion_ratio_changed(self, value: float) -> None:
        print(f"[tasks] completion_ratio={value:.2f}")
```

tutorial_project/stats_feature.py

```python
from gui_do import ObservableValue, RoutedFeature, RoutedRuntimeSpec, setup_routed_runtime, shutdown_routed_runtime


class StatsFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("stats", scene_name="main")
        self.summary_line = ObservableValue("No task updates yet.")
        self._unsub_summary = None

    def bind_runtime(self, host) -> None:
        setup_routed_runtime(self, host, RoutedRuntimeSpec(scene_name="main"))
        self._unsub_summary = self.summary_line.subscribe(self._on_summary_changed)

    def shutdown_runtime(self, host) -> None:
        if callable(self._unsub_summary):
            self._unsub_summary()
            self._unsub_summary = None
        shutdown_routed_runtime(self, host)

    def message_handlers(self):
        return {
            "tasks.changed": self._handle_tasks_changed,
        }

    def _handle_tasks_changed(self, host, message) -> None:
        count = int(message.get("count", 0))
        completed = int(message.get("completed", 0))
        self.summary_line.value = f"Tasks: {count}, Completed: {completed}"

    def _on_summary_changed(self, line: str) -> None:
        print(f"[stats] {line}")
```

Run command from tutorial_project:

```bash
python app.py
```

# Next Steps

You now have a working baseline with declarative bootstrap, reactive state, inter-feature messaging, and hotkeys.

From here, expand in this order:

1. Add windows and scene-level UI composition using WindowSpec, FeatureWindowBundleBindingSpec, and scene presentation helpers.
2. Add command palette behavior with PaletteBindingSpec and SceneCommandPaletteSpec.
3. Add persistence with WorkspacePersistenceManager and scene snapshots.
4. Add telemetry with configure_telemetry and report analysis utilities.
5. Refine layout with adaptive constraints and virtualization for large data views.

Reference map for deeper work:

- [MANUAL.md: Controls and Control Composition](MANUAL.md#controls-and-control-composition)
- [MANUAL.md: Scene, Window, and Task-Panel Presentation Models](MANUAL.md#scene-window-and-task-panel-presentation-models)
- [MANUAL.md: Persistence and Workspace/Session State](MANUAL.md#persistence-and-workspacesession-state)
- [MANUAL.md: Telemetry, Introspection, and Operational Hooks](MANUAL.md#telemetry-introspection-and-operational-hooks)
- [docs/runtime_operating_contracts.md](docs/runtime_operating_contracts.md)
