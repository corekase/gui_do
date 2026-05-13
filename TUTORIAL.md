# gui_do Tutorial: Build a Reactive Multi-Feature Dashboard

## 1. Introduction

gui_do is a data-driven GUI framework built on pygame. You describe application structure with specs, then let bootstrap wire runtime systems in a deterministic order. Feature classes stay focused on behavior and presentation instead of manual infrastructure glue.

In this tutorial, you will build a small but usable Notes Dashboard with two features: a note counter/editor feature and an activity-log feature. The result is a multi-feature desktop app with reactive labels, keyboard shortcuts, routed messages, and clean lifecycle teardown.

Prerequisites: working Python, pip, pygame, and numpy. No prior GUI framework experience is required. For deeper reference while you work, keep [MANUAL.md](MANUAL.md) open.

## 2. Core Concepts

Before writing code, anchor on three ideas that make gui_do predictable.

### Declarative specs vs imperative wiring

In imperative GUI setup, you usually call managers one by one in a brittle sequence. In gui_do, you define data objects such as `HostApplicationBindingSpec`, `SceneBundleBindingSpec`, and `FeatureSpec`, and bootstrap performs consistent wiring for you. That separation gives you stable startup behavior and keeps features decoupled from each other's internals.

### Reactive state

`ObservableValue` stores one value and notifies subscribers when `.value` changes. No polling loop is needed in your feature code. `ObservableList` and `ObservableDict` provide the same pattern for collections, and `ComputedValue` is useful when state is derived from other observables.

Subscribe/unsubscribe pattern:

```python
from gui_do import ObservableValue

count = ObservableValue(0)
unsubscribe = count.subscribe(lambda value: print(f"Count changed to {value}"))
count.value = 1
unsubscribe()
```

### Feature lifecycle

gui_do feature classes follow lifecycle phases with clear intent:

- `build`: create controls and structure.
- `bind_runtime`: connect subscriptions, actions, runtime wiring.
- `on_update`: per-frame logic.
- `handle_event`: explicit event handling when needed.
- `draw`: custom drawing when needed.
- `shutdown_runtime`: teardown subscriptions and runtime bindings.

A key framework guarantee is that all features in a scene complete `build` before any `bind_runtime` runs. That makes host-level shared references safe to establish in `build` and consume in `bind_runtime`.

## 3. Installation and Setup

Install from repository root:

```bash
python -m pip install -e . --no-deps
```

Dependencies: `pygame` and `numpy`.

Verify installation:

```bash
python -c "import gui_do; print(gui_do.__version__)"
```

Minimal startup imports:

```python
from gui_do import HostApplicationBindingSpec, build_host_application_config, bootstrap_host_application, Feature
```

gui_do supports two startup paths:

- Declarative bootstrap (recommended): specs + `build_host_application_config` + `bootstrap_host_application`.
- Manual `GuiApplication` construction (advanced): use when you need low-level control over runtime assembly.

This tutorial uses the declarative path. For the manual path details, see [MANUAL.md](MANUAL.md).

## 4. Your First Feature

Now you will build the first part of the dashboard, step by step.

### 1. Define the feature class

Use `Feature` as the standard baseline. It gives you lifecycle hooks with predictable defaults.

```python
from gui_do import Feature

class NotesFeature(Feature):
    def __init__(self) -> None:
        super().__init__("notes_feature", scene_name="main")

    def build(self, host) -> None:
        pass
```

Why this choice: `Feature` is ideal for visual, interactive units. `DirectFeature` and `RoutedFeature` are specialized and are covered later.

### 2. Add a control

Controls live inside your feature's region in the scene graph. `host.screen_rect` gives you viewport dimensions.

```python
from pygame import Rect
from gui_do import LabelControl

class NotesFeature(Feature):
    def __init__(self) -> None:
        super().__init__("notes_feature", scene_name="main")

    def build(self, host) -> None:
        self._label = host.main_root.add(
            LabelControl("notes_title", Rect(24, 24, host.screen_rect.width - 48, 36), "Notes Dashboard", align="left")
        )
```

### 3. Declare the config

`HostApplicationBindingSpec` defines app structure. `SceneBundleBindingSpec` declares scene setup/root defaults. `FeatureSpec` declares feature factory and host attribute name.

```python
from gui_do import FeatureSpec, HostApplicationBindingSpec, SceneBundleBindingSpec, build_host_application_config

binding = HostApplicationBindingSpec(
    display_size=(980, 620),
    window_title="gui_do Tutorial App",
    fonts={"default": {"file": None, "size": 16}},
    initial_scene_name="main",
    scene_bundle_entries=(
        SceneBundleBindingSpec(scene_name="main", pretty_name="Main", make_initial=True, emit_scene_root_spec=True),
    ),
    feature_entries=(
        FeatureSpec("notes", NotesFeature),
    ),
)
config = build_host_application_config(binding)
```

### 4. Bootstrap and run

`bootstrap_host_application` reads the built config and wires display, scene setup, feature registration, action registry, and runtime binding.

```python
from types import SimpleNamespace
from gui_do import bootstrap_host_application

host = SimpleNamespace()
bootstrap_host_application(host, config)
host.app.run_entrypoint(target_fps=60)
```

### 5. Full listing

```python
from types import SimpleNamespace
from pygame import Rect

from gui_do import (
    Feature,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    SceneBundleBindingSpec,
    bootstrap_host_application,
    build_host_application_config,
)

class NotesFeature(Feature):
    def __init__(self) -> None:
        super().__init__("notes_feature", scene_name="main")

    def build(self, host) -> None:
        self._label = host.main_root.add(
            LabelControl("notes_title", Rect(24, 24, host.screen_rect.width - 48, 36), "Notes Dashboard", align="left")
        )

binding = HostApplicationBindingSpec(
    display_size=(980, 620),
    window_title="gui_do Tutorial App",
    fonts={"default": {"file": None, "size": 16}},
    initial_scene_name="main",
    scene_bundle_entries=(
        SceneBundleBindingSpec(scene_name="main", pretty_name="Main", make_initial=True, emit_scene_root_spec=True),
    ),
    feature_entries=(
        FeatureSpec("notes", NotesFeature),
    ),
)

config = build_host_application_config(binding)
host = SimpleNamespace()
bootstrap_host_application(host, config)
host.app.run_entrypoint(target_fps=60)
```

## 5. Reactive State: Making the UI Respond

Now you make the first feature interactive and reactive.

### 1. Introduce `ObservableValue`

Use one observable as the source of truth for note count.

```python
from gui_do import ObservableValue

self._count = ObservableValue(0)
```

When you assign `self._count.value`, subscribers update automatically.

### 2. Add a button

Add a button that increments the observable.

```python
from gui_do import ButtonControl

self._increment = host.main_root.add(
    ButtonControl("notes_add_button", Rect(24, 76, 180, 36), "Add Note", on_click=self._add_note)
)
```

### 3. Wire observable to label in `bind_runtime`

Subscribe after controls exist and runtime is live.

```python
def bind_runtime(self, host) -> None:
    self._unsubscribe = self._count.subscribe(
        lambda value: setattr(self._count_label, "text", f"Notes: {value}")
    )
```

### 4. Unsubscribe in `shutdown_runtime`

Always tear down subscriptions.

```python
def shutdown_runtime(self, host) -> None:
    if self._unsubscribe:
        self._unsubscribe()
        self._unsubscribe = None
```

### 5. Updated full listing

```python
from types import SimpleNamespace
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

class NotesFeature(Feature):
    def __init__(self) -> None:
        super().__init__("notes_feature", scene_name="main")
        self._count = ObservableValue(0)
        self._unsubscribe = None

    def build(self, host) -> None:
        self._title = host.main_root.add(LabelControl("notes_title", Rect(24, 24, 320, 36), "Notes Dashboard"))
        self._count_label = host.main_root.add(LabelControl("notes_count", Rect(24, 64, 320, 36), "Notes: 0"))
        self._increment = host.main_root.add(
            ButtonControl("notes_add_button", Rect(24, 108, 180, 36), "Add Note", on_click=self._add_note)
        )

    def bind_runtime(self, host) -> None:
        self._unsubscribe = self._count.subscribe(
            lambda value: setattr(self._count_label, "text", f"Notes: {value}")
        )

    def shutdown_runtime(self, host) -> None:
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None

    def _add_note(self) -> None:
        self._count.value = self._count.value + 1

binding = HostApplicationBindingSpec(
    display_size=(980, 620),
    window_title="gui_do Tutorial App",
    fonts={"default": {"file": None, "size": 16}},
    initial_scene_name="main",
    scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True, emit_scene_root_spec=True),),
    feature_entries=(FeatureSpec("notes", NotesFeature),),
)

config = build_host_application_config(binding)
host = SimpleNamespace()
bootstrap_host_application(host, config)
host.app.run_entrypoint(target_fps=60)
```

## 6. Feature Types

Use feature subtypes based on responsibility, not preference.

- `Feature`: standard default for visual and interactive features with lifecycle hooks.
- `DirectFeature`: low-level direct update/draw path when bypassing control pipelines is intentional.
- `LogicFeature`: background logic coordination without a control tree or draw responsibility.
- `RoutedFeature`: feature with topic-based message routing and declarative runtime wiring through `RoutedRuntimeSpec` and `RoutedFeatureLifecycleSpec`.

In this project, `NotesFeature` stays a `Feature`, while the logging panel becomes a `RoutedFeature` to demonstrate declarative shortcut/runtime routing.

## 7. A Second Feature and Feature Communication

You will add an activity-log feature and connect it to the first feature.

### 1. Define the second feature

`ActivityLogFeature` owns its own UI region and displays what happened.

### 2. Shared observable through host

`NotesFeature.build` stores `host.note_count = self._count`. Because all `build` hooks finish before any `bind_runtime`, the log feature can subscribe safely in `bind_runtime`.

### 3. Feature messaging with `FeatureMessage`

Use messages when features should communicate without direct references.

```python
from gui_do import FeatureMessage

class NoteAddedMessage(FeatureMessage):
    @classmethod
    def create(cls, count: int) -> "NoteAddedMessage":
        return cls(
            sender="notes_feature",
            target="activity_log",
            payload={"topic": "note_added", "count": count, "text": f"Added note #{count}"},
        )
```

`NotesFeature` publishes the message payload using `send_message`, and `ActivityLogFeature` handles it by topic.

### 4. Updated full listing

```python
from types import SimpleNamespace
from pygame import Rect

from gui_do import (
    ButtonControl,
    Feature,
    FeatureMessage,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    ObservableValue,
    RoutedFeature,
    SceneBundleBindingSpec,
    bootstrap_host_application,
    build_host_application_config,
)

class NoteAddedMessage(FeatureMessage):
    @classmethod
    def create(cls, count: int) -> "NoteAddedMessage":
        return cls(
            sender="notes_feature",
            target="activity_log",
            payload={"topic": "note_added", "count": count, "text": f"Added note #{count}"},
        )

class NotesFeature(Feature):
    def __init__(self) -> None:
        super().__init__("notes_feature", scene_name="main")
        self._count = ObservableValue(0)
        self._unsubscribe = None

    def build(self, host) -> None:
        host.note_count = self._count
        self._count_label = host.main_root.add(LabelControl("notes_count", Rect(24, 24, 320, 32), "Notes: 0"))
        self._button = host.main_root.add(ButtonControl("notes_add", Rect(24, 64, 180, 36), "Add Note", on_click=self._add_note))

    def bind_runtime(self, host) -> None:
        self._unsubscribe = self._count.subscribe(lambda value: setattr(self._count_label, "text", f"Notes: {value}"))

    def shutdown_runtime(self, host) -> None:
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None

    def _add_note(self) -> None:
        self._count.value = self._count.value + 1
        msg = NoteAddedMessage.create(self._count.value)
        self.send_message(msg.target, msg.payload)

class ActivityLogFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("activity_log", scene_name="main")
        self._log = []
        self._count_unsubscribe = None

    def build(self, host) -> None:
        self._title = host.main_root.add(LabelControl("log_title", Rect(420, 24, 420, 32), "Activity Log"))
        self._line = host.main_root.add(LabelControl("log_line", Rect(420, 64, 520, 32), "Waiting for updates..."))

    def bind_runtime(self, host) -> None:
        self._count_unsubscribe = host.note_count.subscribe(
            lambda value: setattr(self._line, "text", f"Shared count now {value}")
        )

    def shutdown_runtime(self, host) -> None:
        if self._count_unsubscribe:
            self._count_unsubscribe()
            self._count_unsubscribe = None

    def message_handlers(self):
        return {"note_added": self._on_note_added}

    def _on_note_added(self, host, message: FeatureMessage) -> None:
        self._line.text = str(message.get("text", "note added"))

binding = HostApplicationBindingSpec(
    display_size=(980, 620),
    window_title="gui_do Tutorial App",
    fonts={"default": {"file": None, "size": 16}},
    initial_scene_name="main",
    scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True, emit_scene_root_spec=True),),
    feature_entries=(
        FeatureSpec("notes", NotesFeature),
        FeatureSpec("activity", ActivityLogFeature),
    ),
)

config = build_host_application_config(binding)
host = SimpleNamespace()
bootstrap_host_application(host, config)
host.app.run_entrypoint(target_fps=60)
```

## 8. Actions and Keyboard Shortcuts

Now wire keyboard behavior for faster usage and discoverability.

### 1. Declare action specs in config

Use `ActionSpec` in app binding to register host-level actions declaratively.

```python
from gui_do import ActionSpec

action_entries=(
    ActionSpec(action_id="exit", label="Exit", kind="exit", key=27),
)
```

You can also pass pygame constants (for example `pygame.K_ESCAPE`) when constructing the spec.

### 2. Handle feature action callback

For custom feature actions, register handlers through the app action manager in `bind_runtime`, then unregister in `shutdown_runtime`.

```python
def bind_runtime(self, host) -> None:
    host.app.actions.register_action("notes_add_hotkey", lambda _event: (self._add_note() or True))

def shutdown_runtime(self, host) -> None:
    host.app.actions.unregister_action("notes_add_hotkey")
```

### 3. Routed shortcut wiring with lifecycle spec

`RoutedFeature` can declare runtime wiring through `RoutedRuntimeSpec` and bind it in one call using `bind_routed_feature_lifecycle`.

### 4. Shortcut help overlay

Add a `ShortcutOverlaySpec` so users can discover shortcuts with a toggle key.

### 5. Updated listing

```python
from types import SimpleNamespace
import pygame
from pygame import Rect

from gui_do import (
    ActionHotkeySpec,
    ActionSpec,
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

class NotesFeature(Feature):
    def __init__(self) -> None:
        super().__init__("notes_feature", scene_name="main")
        self._count = ObservableValue(0)
        self._unsubscribe = None

    def build(self, host) -> None:
        host.note_count = self._count
        self._count_label = host.main_root.add(LabelControl("notes_count", Rect(24, 24, 320, 32), "Notes: 0"))
        self._button = host.main_root.add(ButtonControl("notes_add", Rect(24, 64, 180, 36), "Add Note", on_click=self._add_note))

    def bind_runtime(self, host) -> None:
        self._unsubscribe = self._count.subscribe(lambda value: setattr(self._count_label, "text", f"Notes: {value}"))

    def shutdown_runtime(self, host) -> None:
        if self._unsubscribe:
            self._unsubscribe()
            self._unsubscribe = None

    def _add_note(self) -> None:
        self._count.value = self._count.value + 1

class ActivityLogFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("activity_log", scene_name="main")
        self._lifecycle = RoutedFeatureLifecycleSpec(
            runtime_spec=RoutedRuntimeSpec(
                scene_name="main",
                action_hotkeys=(
                    ActionHotkeySpec(
                        action_name="notes_add_hotkey",
                        handler=lambda _event: self._trigger_hotkey_note_add(),
                        key=pygame.K_n,
                        scene_name="main",
                    ),
                ),
                shortcut_overlays=(
                    ShortcutOverlaySpec(
                        attr_name="_shortcut_overlay",
                        toggle_action_name="toggle_shortcut_help",
                        toggle_key=pygame.K_F1,
                        toggle_scene_name="main",
                        manual_shortcut_lines=("N - Add note", "F1 - Toggle shortcut help"),
                        manual_section_title="Tutorial",
                    ),
                ),
            ),
        )

    def build(self, host) -> None:
        self._line = host.main_root.add(LabelControl("log_line", Rect(420, 24, 520, 32), "Press N or click Add Note"))

    def bind_runtime(self, host) -> None:
        bind_routed_feature_lifecycle(self, host, self._lifecycle)

    def shutdown_runtime(self, host) -> None:
        shutdown_routed_feature_lifecycle(self, host, self._lifecycle)

    def _trigger_hotkey_note_add(self) -> bool:
        self._line.text = "Hotkey pressed: N"
        return True

binding = HostApplicationBindingSpec(
    display_size=(980, 620),
    window_title="gui_do Tutorial App",
    fonts={"default": {"file": None, "size": 16}},
    initial_scene_name="main",
    scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True, emit_scene_root_spec=True),),
    feature_entries=(
        FeatureSpec("notes", NotesFeature),
        FeatureSpec("activity", ActivityLogFeature),
    ),
    action_entries=(
        ActionSpec(action_id="exit", label="Exit", kind="exit", key=pygame.K_ESCAPE),
    ),
)

config = build_host_application_config(binding)
host = SimpleNamespace()
bootstrap_host_application(host, config)
host.app.run_entrypoint(target_fps=60)
```

## 9. Spec Reference for Builders

This section is a concise orientation map. For deep option tables and system behavior, use [MANUAL.md](MANUAL.md).

### `FeatureSpec`

Declares one feature factory and the host attribute name used during bootstrap.

```python
from gui_do import FeatureSpec

FeatureSpec("notes", NotesFeature)
```

See [8.2 Feature Lifecycle and Feature Types](MANUAL.md#82-feature-lifecycle-and-feature-types).

### `SceneBundleBindingSpec`

Declares scene setup/runtime/root/navigation behavior in one bundle.

```python
from gui_do import SceneBundleBindingSpec

SceneBundleBindingSpec(scene_name="main", make_initial=True, emit_scene_root_spec=True)
```

See [8.1 Application Bootstrap and Host Configuration](MANUAL.md#81-application-bootstrap-and-host-configuration).

### `ActionSpec` + `ActionHotkeySpec`

`ActionSpec` declares host-level standard actions; `ActionHotkeySpec` declares routed feature hotkeys.

```python
from gui_do import ActionHotkeySpec, ActionSpec

ActionSpec(action_id="exit", label="Exit", kind="exit")
ActionHotkeySpec(action_name="notes_add_hotkey", handler=lambda _event: True)
```

See [8.3 Events, Actions, Input Mapping, and Routing](MANUAL.md#83-events-actions-input-mapping-and-routing).

### `ShortcutOverlaySpec`

Configures built-in shortcut discovery overlay wiring.

```python
from gui_do import ShortcutOverlaySpec

ShortcutOverlaySpec(attr_name="_shortcut_overlay", toggle_action_name="toggle_shortcuts")
```

See [8.8 Overlays, Dialogs, Notifications, and Command Surfaces](MANUAL.md#88-overlays-dialogs-notifications-and-command-surfaces).

### `RoutedRuntimeSpec` + `RoutedFeatureLifecycleSpec`

Bundles routed runtime declarations and lifecycle hookup for `RoutedFeature`.

```python
from gui_do import RoutedFeatureLifecycleSpec, RoutedRuntimeSpec

RoutedFeatureLifecycleSpec(runtime_spec=RoutedRuntimeSpec(scene_name="main"))
```

See [8.2 Feature Lifecycle and Feature Types](MANUAL.md#82-feature-lifecycle-and-feature-types) and [8.3 Events, Actions, Input Mapping, and Routing](MANUAL.md#83-events-actions-input-mapping-and-routing).

### `ToastManager`

Toast notifications are available through host wiring, typically via `host.toasts.show(...)` from inside a feature.

```python
# Example shape:
# host.toasts.show("Saved note", severity="info")
```

See [8.8 Overlays, Dialogs, Notifications, and Command Surfaces](MANUAL.md#88-overlays-dialogs-notifications-and-command-surfaces).

## 10. Complete Project Listing

The listing below is the full end-to-end tutorial project. It includes two distinct features, shared reactive state, typed message payloads through `FeatureMessage`, a routed feature runtime with shortcut overlay, an `ActionSpec` keyboard action, and explicit teardown in `shutdown_runtime`.

```python
from types import SimpleNamespace
import pygame
from pygame import Rect

from gui_do import (
    ActionHotkeySpec,
    ActionSpec,
    ButtonControl,
    Feature,
    FeatureMessage,
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

# Message object shape keeps inter-feature payloads consistent and self-documenting.
class NoteAddedMessage(FeatureMessage):
    @classmethod
    def create(cls, count: int, source: str = "button") -> "NoteAddedMessage":
        return cls(
            sender="notes_feature",
            target="activity_log",
            payload={
                "topic": "note_added",
                "count": count,
                "source": source,
                "text": f"Added note #{count} via {source}",
            },
        )


# NotesFeature owns note state and user-triggered changes.
class NotesFeature(Feature):
    def __init__(self) -> None:
        super().__init__("notes_feature", scene_name="main")
        self._count = ObservableValue(0)
        self._count_unsubscribe = None

    def build(self, host) -> None:
        host.note_count = self._count
        host.add_note_callback = self.add_note_from_hotkey

        self._title = host.main_root.add(
            LabelControl("notes_title", Rect(24, 24, 340, 32), "Notes Panel")
        )
        self._count_label = host.main_root.add(
            LabelControl("notes_count", Rect(24, 64, 340, 32), "Notes: 0")
        )
        self._hint = host.main_root.add(
            LabelControl("notes_hint", Rect(24, 100, 360, 28), "Use button or press N")
        )
        self._add_button = host.main_root.add(
            ButtonControl("notes_add_button", Rect(24, 136, 200, 36), "Add Note", on_click=self._add_note_from_button)
        )

    def bind_runtime(self, host) -> None:
        self._count_unsubscribe = self._count.subscribe(
            lambda value: setattr(self._count_label, "text", f"Notes: {value}")
        )

    def shutdown_runtime(self, host) -> None:
        if self._count_unsubscribe:
            self._count_unsubscribe()
            self._count_unsubscribe = None

    def add_note_from_hotkey(self) -> bool:
        self._increment_and_publish(source="hotkey")
        return True

    def _add_note_from_button(self) -> None:
        self._increment_and_publish(source="button")

    def _increment_and_publish(self, source: str) -> None:
        self._count.value = self._count.value + 1
        msg = NoteAddedMessage.create(self._count.value, source=source)
        self.send_message(msg.target, msg.payload)


# ActivityLogFeature displays updates and owns routed runtime shortcuts/overlay.
class ActivityLogFeature(RoutedFeature):
    def __init__(self) -> None:
        super().__init__("activity_log", scene_name="main")
        self._lines = []
        self._count_unsubscribe = None

        self._lifecycle = RoutedFeatureLifecycleSpec(
            runtime_spec=RoutedRuntimeSpec(
                scene_name="main",
                action_hotkeys=(
                    ActionHotkeySpec(
                        action_name="notes_add_hotkey",
                        handler=lambda _event: self._add_note_via_hotkey(),
                        key=pygame.K_n,
                        scene_name="main",
                    ),
                ),
                shortcut_overlays=(
                    ShortcutOverlaySpec(
                        attr_name="_shortcut_overlay",
                        toggle_action_name="toggle_shortcut_help",
                        toggle_key=pygame.K_F1,
                        toggle_scene_name="main",
                        manual_shortcut_lines=(
                            "N - Add Note",
                            "F1 - Toggle shortcut help",
                            "Esc - Exit",
                        ),
                        manual_section_title="Tutorial Shortcuts",
                    ),
                ),
            ),
        )

    def build(self, host) -> None:
        self._title = host.main_root.add(
            LabelControl("activity_title", Rect(420, 24, 520, 32), "Activity Log")
        )
        self._status = host.main_root.add(
            LabelControl("activity_status", Rect(420, 64, 520, 32), "No events yet")
        )
        self._total = host.main_root.add(
            LabelControl("activity_total", Rect(420, 100, 520, 32), "Shared total: 0")
        )

    def bind_runtime(self, host) -> None:
        bind_routed_feature_lifecycle(self, host, self._lifecycle)
        self._add_note_callback = getattr(host, "add_note_callback", None)
        self._count_unsubscribe = host.note_count.subscribe(
            lambda value: setattr(self._total, "text", f"Shared total: {value}")
        )

    def shutdown_runtime(self, host) -> None:
        shutdown_routed_feature_lifecycle(self, host, self._lifecycle)
        self._add_note_callback = None
        if self._count_unsubscribe:
            self._count_unsubscribe()
            self._count_unsubscribe = None

    def message_handlers(self):
        return {"note_added": self._on_note_added}

    def _on_note_added(self, host, message: FeatureMessage) -> None:
        text = str(message.get("text", "Added note"))
        self._lines.append(text)
        self._status.text = text

    def _add_note_via_hotkey(self) -> bool:
        add_note = getattr(self, "_add_note_callback", None)
        if callable(add_note):
            add_note()
            return True
        self._status.text = "Hotkey pressed, but note callback is unavailable"
        return True


# Declarative binding keeps startup predictable and avoids manual wiring sequences.
binding = HostApplicationBindingSpec(
    display_size=(980, 620),
    window_title="gui_do Tutorial App",
    fonts={"default": {"file": None, "size": 16}},
    initial_scene_name="main",
    scene_bundle_entries=(
        SceneBundleBindingSpec(
            scene_name="main",
            pretty_name="Main",
            make_initial=True,
            emit_scene_root_spec=True,
        ),
    ),
    feature_entries=(
        FeatureSpec("notes", NotesFeature),
        FeatureSpec("activity", ActivityLogFeature),
    ),
    action_entries=(
        ActionSpec(action_id="exit", label="Exit", kind="exit", key=pygame.K_ESCAPE),
    ),
)

# Bootstrapping executes spec wiring and returns a host with app runtime attached.
config = build_host_application_config(binding)
host = SimpleNamespace()
bootstrap_host_application(host, config)
host.app.run_entrypoint(target_fps=60)
```

## 11. Next Steps

Next, read [MANUAL.md](MANUAL.md), then study [demo_features/](demo_features) as living patterns that mirror recommended project organization (one package per feature, package root exports only).

Good expansion targets for this project are overlays, persistence, scene navigation, telemetry, and graphics subsystems.

Most relevant MANUAL sections for immediate growth:

- [8.1 Application Bootstrap and Host Configuration](MANUAL.md#81-application-bootstrap-and-host-configuration)
- [8.2 Feature Lifecycle and Feature Types](MANUAL.md#82-feature-lifecycle-and-feature-types)
- [8.3 Events, Actions, Input Mapping, and Routing](MANUAL.md#83-events-actions-input-mapping-and-routing)
- [8.4 State and Observables](MANUAL.md#84-state-and-observables)

As you deepen your understanding, read `data_driven_runtime.py` and `feature_lifecycle.py` in the library source. They are approachable and will demystify exactly how bootstrap and lifecycle orchestration work.
