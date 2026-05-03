# gui_do Tutorial

## 1. Introduction

gui_do is a pygame-based GUI framework for building desktop applications through declarative specs and feature lifecycles instead of manually wiring every scene, action, and overlay. In this tutorial you will build a small multi-feature application, learn how bootstrap configuration works, and see how observable state, feature messaging, and routed runtime helpers fit together.

You should already be comfortable with basic Python classes and functions. Familiarity with pygame helps, but the tutorial explains the gui_do-specific pieces before using them.

## 2. Core Concepts

gui_do is data-driven. Instead of writing imperative setup code everywhere, you describe your application with specs such as `FeatureSpec`, `SceneSetupSpec`, `ActionSpec`, `WindowSpec`, and `RoutedRuntimeSpec`. Bootstrap code reads those specs and wires the runtime for you.

Reactive state is built around observable types:

- `ObservableValue` for a single reactive value.
- `ObservableList` for ordered reactive collections.
- `ObservableDict` for keyed reactive collections.
- `ComputedValue` when you want derived, read-only state from one or more observables.

Features are the units of composition. The main hooks are:

- `build(host)` to create controls and store references.
- `bind_runtime(host)` to connect subscriptions, actions, event-bus handlers, and routed-runtime helpers.
- `handle_event(host, event)` for feature-specific input handling.
- `on_update(host)` for per-frame logic.
- `draw(host, surface, theme)` for custom drawing.

## 3. Installation and Setup

Install the package with pip:

```bash
pip install gui-do
```

Minimal imports for the bootstrap path usually look like this:

```python
from gui_do import (
    Feature,
    FeatureSpec,
    HostApplicationConfig,
    SceneSetupSpec,
    RuntimeSceneSpec,
    ActionSpec,
    bootstrap_host_application,
)
```

There are two ways to start an app:

- Bootstrap path: create `HostApplicationConfig`, call `bootstrap_host_application`, and let gui_do build the runtime.
- Manual path: create a display surface yourself, construct `GuiApplication`, and wire scenes, features, and actions manually.

For new applications, prefer the bootstrap path. When a config grows large, `HostApplicationBindingSpec` and `build_host_application_config` let you assemble scenes, features, actions, and windows from smaller binding specs rather than building every tuple manually.

## 4. Your First Application — Step by Step

### 1. Create a surface and GuiApplication (and explain bootstrap alternative)

The manual path is useful to understand what bootstrap is doing under the hood:

```python
import pygame

from gui_do import GuiApplication, create_display

pygame.init()
surface = create_display((800, 600))
app = GuiApplication(surface)
```

In the rest of this tutorial, you will use `bootstrap_host_application`, which creates the display and `GuiApplication` for you.

### 2. Define a Feature with build hook

```python
from pygame import Rect

from gui_do import Feature, LabelControl


class HelloFeature(Feature):
    def __init__(self) -> None:
        super().__init__("hello_feature", scene_name="main")

    def build(self, host) -> None:
        host.app.add(
            LabelControl("hello_label", Rect(24, 24, 320, 32), "Hello from gui_do"),
            scene_name="main",
        )
```

### 3. Declare HostApplicationConfig + FeatureSpec

```python
from gui_do import (
    ActionSpec,
    FeatureSpec,
    HostApplicationConfig,
    RuntimeSceneSpec,
    SceneSetupSpec,
    TelemetryConfig,
)


config = HostApplicationConfig(
    display_size=(800, 600),
    window_title="gui_do tutorial app",
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
        FeatureSpec(attr_name="_hello_feature", factory=HelloFeature),
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
```

### 4. Call bootstrap_host_application

```python
from gui_do import bootstrap_host_application


class HelloApp:
    def __init__(self) -> None:
        self.config = config
        bootstrap_host_application(self, self.config)
```

After this call, the host has `app`, `screen`, `screen_rect`, `scene_presentation`, `window_presentation`, `action_registry`, and any feature attributes declared in `feature_specs`.

### 5. Add main run loop

```python
class HelloApp:
    def __init__(self) -> None:
        self.config = config
        bootstrap_host_application(self, self.config)

    def run(self) -> None:
        self.app.run_entrypoint(target_fps=self.config.target_fps)
```

### 6. Show full combined listing

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
            LabelControl("hello_label", Rect(24, 24, 320, 32), "Hello from gui_do"),
            scene_name="main",
        )


class HelloApp:
    def __init__(self) -> None:
        self.config = HostApplicationConfig(
            display_size=(800, 600),
            window_title="gui_do tutorial app",
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
                FeatureSpec(attr_name="_hello_feature", factory=HelloFeature),
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

## 5. Observable Data and Reactive UI

Reactive state is one of the main reasons to use gui_do. Here is a simple pattern with `ObservableValue`:

```python
from pygame import Rect

from gui_do import ButtonControl, Feature, LabelControl, ObservableValue


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self.count = ObservableValue(0)

    def build(self, host) -> None:
        self.label = host.app.add(
            LabelControl("count_label", Rect(24, 24, 220, 28), "Count: 0"),
            scene_name="main",
        )
        host.app.add(
            ButtonControl("increment_button", Rect(24, 64, 140, 32), "+1", on_click=self._increment),
            scene_name="main",
        )

    def bind_runtime(self, host) -> None:
        def _sync(value: int) -> None:
            self.label.text = f"Count: {value}"

        self._count_subscription = self.count.subscribe(_sync)
        _sync(self.count.value)

    def shutdown_runtime(self, host) -> None:
        if hasattr(self, "_count_subscription"):
            self._count_subscription.dispose()

    def _increment(self) -> None:
        self.count.value = self.count.value + 1
```

The key pattern is:

- store the observable on the feature or a presentation object
- subscribe in `bind_runtime()`
- keep the subscription handle when cleanup is required
- dispose it in `shutdown_runtime()` if the binding is not otherwise managed

## 6. Feature Types

- `Feature`: best for normal UI composition with controls and runtime wiring.
- `DirectFeature`: best for custom drawing, renderers, particle layers, or simulations that draw directly.
- `LogicFeature`: best for non-visual services that process command messages.
- `RoutedFeature`: best for topic-routed feature messages where handlers are easier to express as a mapping.

Use the simplest type that fits the feature. Most application modules should begin as `Feature` and only move to the others when the behavior clearly matches.

When a `RoutedFeature` also needs companion logic features and a lifecycle-scoped runtime spec, `RoutedFeatureLifecycleSpec` plus the three orchestration helpers (`register_routed_feature_companions`, `bind_routed_feature_lifecycle`, `shutdown_routed_feature_lifecycle`) keep that wiring declarative across build, bind, and shutdown hooks.

## 7. Feature Messaging

Features can communicate without tightly coupling themselves to each other's internals.

```python
from gui_do import Feature, LogicFeature


class SaveLogicFeature(LogicFeature):
    def __init__(self) -> None:
        super().__init__("save_logic", scene_name="main")

    def on_logic_command(self, host, message) -> None:
        if message.command == "save":
            host.app.toasts.show("Document saved")


class ToolbarFeature(Feature):
    def __init__(self) -> None:
        super().__init__("toolbar_feature", scene_name="main")

    def bind_runtime(self, host) -> None:
        self.bind_logic("save_logic", alias="save")

    def save_document(self) -> None:
        self.send_logic_message({"command": "save"}, alias="save")
```

This is a good pattern when one feature owns the UI and another owns domain behavior.

## 8. Scene Navigation

`SceneSetupSpec` defines scenes. `bootstrap_host_application` also adds `go_to_{scene_name}` helpers to the host, which makes scene changes simple.

```python
import pygame

from gui_do import ActionSpec, RuntimeSceneSpec, SceneSetupSpec


scene_specs = (
    SceneSetupSpec(name="main", pretty_name="Main", initial=True),
    SceneSetupSpec(name="settings", pretty_name="Settings"),
)

runtime_scene_specs = (
    RuntimeSceneSpec(scene_name="main", bind_escape_to_exit=True),
    RuntimeSceneSpec(scene_name="settings", bind_escape_to_exit=True),
)

action_specs = (
    ActionSpec(
        action_id="go_to_settings",
        label="Go to Settings",
        kind="scene_nav",
        target="settings",
        category="Scenes",
        key=pygame.K_F2,
    ),
)
```

You can navigate either through scene actions or by calling the generated host helper such as `host.go_to_settings()`.

## 9. Spec Reference for Beginners

`FeatureSpec`

```python
FeatureSpec(attr_name="_editor_feature", factory=EditorFeature)
```

Use it to declare one host-owned feature instance.

`SceneSetupSpec`

```python
SceneSetupSpec(name="editor", pretty_name="Editor")
```

Use it to declare scenes and transitions.

`ActionSpec`

```python
ActionSpec(action_id="exit", label="Exit", kind="exit", category="File")
```

Use it for host-level actions such as exit, scene navigation, and command palette open.

`WindowSpec`

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

Use it when a feature owns a window that also needs action and task-panel integration.

Task panel spec/runtime helper patterns

```python
from gui_do import SceneTaskPanelSpec, TaskPanelButtonSpec


task_panel_spec = SceneTaskPanelSpec(scene_name="main", control_id="main_task_panel")
button_spec = TaskPanelButtonSpec(
    attr_name="settings_button",
    control_id="settings_button",
    slot_index=1,
    label="Settings",
    on_click=lambda: None,
)
```

Use these with the task-panel helper utilities in `data_driven_runtime.py` when you want declarative scene shell controls.

Toast/notification specs or manager usage

```python
from gui_do import NotificationSpec, ToastSeverity, build_notification_center


notification_center = build_notification_center(
    (
        NotificationSpec("Build succeeded", title="Pipeline", severity=ToastSeverity.SUCCESS),
        NotificationSpec("Unsaved changes", title="Editor", severity=ToastSeverity.WARNING),
    )
)
```

For live notifications, use `app.toasts.show(...)` or `app.toasts.show_persistent(...)`. Toast clicks are consumed by default, and `on_click=` is optional and explicit.

Shortcut/help overlay spec/runtime helper patterns

```python
import pygame

from gui_do import RoutedRuntimeSpec, ShortcutOverlaySpec


runtime_spec = RoutedRuntimeSpec(
    scene_name="main",
    shortcut_overlays=(
        ShortcutOverlaySpec(
            attr_name="_help_overlay",
            action_registry_attr="action_registry",
            toggle_action_name="show_help",
            toggle_key=pygame.K_F9,
            manual_shortcut_lines=(
                "F5: Open command palette",
                "F9: Display this help",
            ),
            prepend_manual_shortcuts=True,
        ),
    ),
)
```

This helper path is the easiest way to keep shortcut overlay behavior declarative. Current overlay semantics still apply: escape dismissal, outside-click dismissal, and optional modal key capture of otherwise unhandled keys.

For tighter control over displayed content, `ShortcutOverlaySpec` also supports `manual_shortcuts_only` (show only the manual lines), `exclude_section_titles` (hide named registry sections), and `exclude_entry_labels` (hide specific entries by label).

## 10. Complete Example Application

```python
import pygame
from pygame import Rect

from gui_do import (
    ActionSpec,
    ButtonControl,
    Feature,
    FeatureSpec,
    HostApplicationConfig,
    LabelControl,
    ObservableValue,
    RuntimeSceneSpec,
    SceneSetupSpec,
    TelemetryConfig,
    bootstrap_host_application,
)


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self.count = ObservableValue(0)

    def build(self, host) -> None:
        self.label = host.app.add(
            LabelControl("count_label", Rect(24, 24, 260, 32), "Count: 0"),
            scene_name="main",
        )
        host.app.add(
            ButtonControl("increment_button", Rect(24, 72, 160, 32), "Increment", on_click=self.increment),
            scene_name="main",
        )

    def bind_runtime(self, host) -> None:
        def _sync(value: int) -> None:
            self.label.text = f"Count: {value}"

        self._subscription = self.count.subscribe(_sync)
        _sync(self.count.value)

    def shutdown_runtime(self, host) -> None:
        self._subscription.dispose()

    def increment(self) -> None:
        self.count.value = self.count.value + 1


class StatusFeature(Feature):
    def __init__(self) -> None:
        super().__init__("status_feature", scene_name="main")

    def build(self, host) -> None:
        self.status_label = host.app.add(
            LabelControl("status_label", Rect(24, 128, 360, 28), "Status: waiting"),
            scene_name="main",
        )

    def bind_runtime(self, host) -> None:
        counter = host._counter_feature

        def _sync(value: int) -> None:
            self.status_label.text = f"Status: counter is now {value}"

        self._subscription = counter.count.subscribe(_sync)
        _sync(counter.count.value)

    def shutdown_runtime(self, host) -> None:
        self._subscription.dispose()


class TutorialApp:
    def __init__(self) -> None:
        self.config = HostApplicationConfig(
            display_size=(900, 640),
            window_title="gui_do complete tutorial example",
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
                FeatureSpec(attr_name="_counter_feature", factory=CounterFeature),
                FeatureSpec(attr_name="_status_feature", factory=StatusFeature),
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
        TutorialApp().run()
    finally:
        pygame.quit()
```

This example has two features, one shared observable value, one button-driven flow, and a normal gui_do run loop.

## 11. Next Steps

Read [README.md](README.md) for the broader API guide and higher-level patterns. Then study [demo_features/](demo_features/) to see routed runtime specs, scene shell helpers, window presentation, and shortcut overlays in a larger application. After that, the best source-level references are [gui_do/features/data_driven_runtime.py](gui_do/features/data_driven_runtime.py) and [gui_do/features/feature_lifecycle.py](gui_do/features/feature_lifecycle.py), followed by the documents under [docs/](docs/).
