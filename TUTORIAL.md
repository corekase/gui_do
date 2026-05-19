# gui_do Tutorial

## 1. Introduction

gui_do is a data-driven GUI framework for Python that runs on pygame. You describe your app with specs, then let bootstrap assemble scenes, features, actions, and runtime systems in a consistent way. Feature code stays normal Python, but the repetitive integration work is automated.

In this tutorial, you will build a complete two-panel Dashboard and Activity Log application. The first feature is a counter panel with buttons and keyboard actions. The second feature is a routed activity log that receives typed feature messages, displays live updates, and demonstrates routed runtime wiring.

Prerequisites:

- Python 3.10+
- pip
- pygame
- numpy
- Basic Python classes/functions knowledge (no prior GUI framework experience required)

For deeper theory and full system reference while you work, use [MANUAL.md](MANUAL.md).

## 2. Core Concepts

Before writing code, lock in three ideas that make gui_do predictable.

### Declarative specs vs imperative wiring

In many GUI frameworks, startup becomes a long imperative script where every scene, key binding, and cross-system hook is manually connected. gui_do uses spec objects to declare app structure first, then bootstrap realizes that structure.

Why this matters:

- Specs are easy to diff and test.
- Wiring becomes deterministic.
- Features do not need to know each other’s internals.
- You can reorganize feature internals without changing bootstrap contracts.

### Reactive state

Reactive state means the UI updates because data changes, not because you poll and repaint manually.

- ObservableValue handles one value.
- ObservableList and ObservableDict handle collections.
- ComputedValue derives data from other observables.

The key pattern is subscribe and unsubscribe:

```python
from gui_do import ObservableValue

count = ObservableValue(0)
unsubscribe = count.subscribe(lambda value: print(f"Count changed to {value}"))
count.value = 1
unsubscribe()
```

Why this matters:

- You remove polling loops.
- Data flow is explicit.
- Teardown remains safe when features leave a scene.

### Feature lifecycle

The standard feature lifecycle is:

- build(host): Construct controls and initial structure.
- bind_runtime(host): Attach subscriptions, runtime resources, actions, and services.
- handle_event(host, event): Optional event interception.
- on_update(host): Per-frame logic.
- draw(host, surface, theme): Optional direct drawing.
- shutdown_runtime(host): Tear down runtime subscriptions/resources.

Important framework guarantee: all features in a scene complete build before any bind_runtime runs. That means your control tree exists before runtime subscriptions begin.

Current update/draw signatures are on_update(host) and draw(host, surface, theme), which match the public lifecycle class definitions.

## 3. Installation and Setup

Install from repository root:

```bash
python -m pip install -e . --no-deps
```

Dependencies:

- pygame
- numpy

Verify installation:

```bash
python -c "import gui_do; print(gui_do.__version__)"
```

Minimal startup imports:

```python
from gui_do import (
    Feature,
    HostApplicationBindingSpec,
    build_host_application_config,
    bootstrap_host_application,
)
```

Startup paths:

- Recommended: declarative bootstrap with HostApplicationBindingSpec, build_host_application_config, and bootstrap_host_application.
- Advanced: manual GuiApplication construction and explicit runtime wiring (see [MANUAL.md](MANUAL.md)).

## 4. Your First Feature

Now build the first part of the project: a counter panel.

### Step 1. Define the feature class

Feature is the default choice for UI features with normal lifecycle hooks.

```python
from gui_do import Feature

class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter_feature", scene_name="main")

    def build(self, host):
        pass
```

Why Feature here:

- You want standard lifecycle hooks.
- You want controls plus runtime subscriptions.
- You do not need direct low-level draw/event bypass behavior.

### Step 2. Add a control tree

Controls live in feature-owned regions. Here we create a panel and one label.

```python
from pygame import Rect
from gui_do import LabelControl, PanelControl

class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter_feature", scene_name="main")

    def build(self, host):
        panelRect = Rect(20, 20, host.screen_rect.width // 2 - 30, host.screen_rect.height - 40)
        self.panel = host.app.add(PanelControl("counter_panel", panelRect, draw_background=True), scene_name="main")
        self.title = self.panel.add(LabelControl("counter_title", Rect(16, 16, 320, 28), "Counter Panel"))
```

### Step 3. Declare host config

Use declarative specs to define scene and feature registration.

```python
from gui_do import (
    FeatureSpec,
    HostApplicationBindingSpec,
    SceneBundleBindingSpec,
    build_host_application_config,
)

config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1100, 680),
        window_title="gui_do Tutorial App",
        fonts={"default": {"file": None, "size": 16}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(scene_name="main", make_initial=True),
        ),
        feature_entries=(
            FeatureSpec("counterFeature", CounterFeature),
        ),
    )
)
```

What each part means:

- HostApplicationBindingSpec: top-level declaration for app bootstrapping.
- SceneBundleBindingSpec: scene lifecycle/startup declaration.
- FeatureSpec: host attribute slot and feature factory binding.

### Step 4. Bootstrap and run

Bootstrap populates host fields and wires all declared runtime systems.

```python
from gui_do import bootstrap_host_application

class Host:
    pass

host = Host()
bootstrap_host_application(host, config)
host.app.run_entrypoint(target_fps=60)
```

### Step 5. Full listing so far

```python
import pygame
from pygame import Rect

from gui_do import (
    Feature,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    PanelControl,
    SceneBundleBindingSpec,
    bootstrap_host_application,
    build_host_application_config,
)

class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter_feature", scene_name="main")

    def build(self, host):
        panelRect = Rect(20, 20, host.screen_rect.width // 2 - 30, host.screen_rect.height - 40)
        self.panel = host.app.add(PanelControl("counter_panel", panelRect, draw_background=True), scene_name="main")
        self.panel.add(LabelControl("counter_title", Rect(16, 16, 320, 28), "Counter Panel"))

class Host:
    pass

host = Host()
config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1100, 680),
        window_title="gui_do Tutorial App",
        fonts={"default": {"file": None, "size": 16}},
        initial_scene_name="main",
        scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
        feature_entries=(FeatureSpec("counterFeature", CounterFeature),),
    )
)
bootstrap_host_application(host, config)
host.app.run_entrypoint(target_fps=60)
```

## 5. Reactive State: Making the UI Respond

Now make the first feature interactive.

### Step 1. Add ObservableValue

```python
from gui_do import ObservableValue

class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter_feature", scene_name="main")
        self.count = ObservableValue(0)
        self.countSubscription = None
```

### Step 2. Add a button to mutate state

```python
from gui_do import ButtonControl

def build(self, host):
    panelRect = Rect(20, 20, host.screen_rect.width // 2 - 30, host.screen_rect.height - 40)
    self.panel = host.app.add(PanelControl("counter_panel", panelRect, draw_background=True), scene_name="main")
    self.valueLabel = self.panel.add(LabelControl("count_label", Rect(16, 60, 320, 30), "Count: 0"))
    self.incrementButton = self.panel.add(
        ButtonControl("increment_button", Rect(16, 104, 160, 34), "Increment", on_click=self.incrementCount)
    )

def incrementCount(self):
    self.count.value = int(self.count.value) + 1
```

### Step 3. Subscribe in bind_runtime

Subscribe when the runtime is live and controls are present.

```python
def bind_runtime(self, host):
    self.countSubscription = self.count.subscribe(
        lambda value: setattr(self.valueLabel, "text", f"Count: {value}")
    )
```

### Step 4. Unsubscribe in shutdown_runtime

```python
def shutdown_runtime(self, host):
    if self.countSubscription is not None:
        self.countSubscription()
        self.countSubscription = None
```

Why this cleanup matters:

- Prevents stale callbacks after feature removal.
- Prevents leaked references.
- Keeps scene transitions safe.

### Step 5. Full updated listing

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
    PanelControl,
    SceneBundleBindingSpec,
    bootstrap_host_application,
    build_host_application_config,
)

class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter_feature", scene_name="main")
        self.count = ObservableValue(0)
        self.countSubscription = None

    def build(self, host):
        panelRect = Rect(20, 20, host.screen_rect.width // 2 - 30, host.screen_rect.height - 40)
        self.panel = host.app.add(PanelControl("counter_panel", panelRect, draw_background=True), scene_name="main")
        self.panel.add(LabelControl("counter_title", Rect(16, 16, 320, 28), "Counter Panel"))
        self.valueLabel = self.panel.add(LabelControl("count_label", Rect(16, 60, 320, 30), "Count: 0"))
        self.incrementButton = self.panel.add(
            ButtonControl("increment_button", Rect(16, 104, 160, 34), "Increment", on_click=self.incrementCount)
        )

    def bind_runtime(self, host):
        self.countSubscription = self.count.subscribe(
            lambda value: setattr(self.valueLabel, "text", f"Count: {value}")
        )

    def shutdown_runtime(self, host):
        if self.countSubscription is not None:
            self.countSubscription()
            self.countSubscription = None

    def incrementCount(self):
        self.count.value = int(self.count.value) + 1

class Host:
    pass

host = Host()
config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1100, 680),
        window_title="gui_do Tutorial App",
        fonts={"default": {"file": None, "size": 16}},
        initial_scene_name="main",
        scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
        feature_entries=(FeatureSpec("counterFeature", CounterFeature),),
    )
)
bootstrap_host_application(host, config)
host.app.run_entrypoint(target_fps=60)
```

## 6. Feature Types

Use feature types by intent, not by habit.

- Feature: default choice for most visual features with full standard lifecycle.
- DirectFeature: high-control path for direct event/update/draw hooks when bypassing the usual control pipeline is intentional.
- LogicFeature: non-visual background coordination and domain logic without a control tree.
- RoutedFeature: Feature subtype with topic-routed message handling and declarative runtime wiring through RoutedRuntimeSpec and RoutedFeatureLifecycleSpec.

Practical rule:

- Start with Feature.
- Use RoutedFeature when runtime wiring and message routing become substantial.
- Use LogicFeature for pure computation/coordinator roles.
- Use DirectFeature only for explicit low-level rendering/event control paths.

For full lifecycle semantics and selection guidance, see [MANUAL.md](MANUAL.md).

## 7. A Second Feature and Feature Communication

Now add the Activity Log feature so the project has two distinct responsibilities.

### Step 1. Define second feature

The log panel shows events and gives users visibility into app behavior.

```python
from pygame import Rect
from gui_do import LabelControl, ObservableList, PanelControl, RoutedFeature

class ActivityLogFeature(RoutedFeature):
    def __init__(self):
        super().__init__("activity_log", scene_name="main")
        self.items = ObservableList([])
        self.itemsSubscription = None

    def build(self, host):
        panelRect = Rect(host.screen_rect.width // 2 + 10, 20, host.screen_rect.width // 2 - 30, host.screen_rect.height - 40)
        self.panel = host.app.add(PanelControl("log_panel", panelRect, draw_background=True), scene_name="main")
        self.title = self.panel.add(LabelControl("log_title", Rect(16, 16, 320, 28), "Activity Log"))
        self.latest = self.panel.add(LabelControl("log_latest", Rect(16, 60, 420, 30), "Latest: (none)"))
```

### Step 2. Shared observable approach

Simple case: publish shared ObservableValue from one feature and read it in another.

```python
def build(self, host):
    host.sharedCount = self.count

# In ActivityLogFeature.bind_runtime
self.sharedCountSubscription = host.sharedCount.subscribe(
    lambda value: setattr(self.latest, "text", f"Latest shared count: {value}")
)
```

Use this when features are intentionally coupled around shared state.

### Step 3. Typed message approach with FeatureMessage subclass

Use message passing when you want looser coupling.

```python
from gui_do import FeatureMessage

class CounterIncrementedMessage(FeatureMessage):
    @classmethod
    def create(cls, sender, target, value):
        return cls(
            sender=sender,
            target=target,
            payload={"topic": "activity", "event": "incremented", "value": int(value)},
        )

# In CounterFeature
message = CounterIncrementedMessage.create(self.name, "activity_log", self.count.value)
self.send_message(message.target, message.payload)
```

Then the routed log feature handles topic activity:

```python
def message_handlers(self):
    return {"activity": self.handleActivityMessage}

def handleActivityMessage(self, host, message):
    if message.event == "incremented":
        self.items.append(f"Counter changed to {message.get('value')}")
```

### Step 4. Full updated listing with two features

```python
import pygame
from pygame import Rect

from gui_do import (
    ButtonControl,
    Feature,
    FeatureMessage,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    ObservableList,
    ObservableValue,
    PanelControl,
    RoutedFeature,
    SceneBundleBindingSpec,
    bootstrap_host_application,
    build_host_application_config,
)

class CounterIncrementedMessage(FeatureMessage):
    @classmethod
    def create(cls, sender, target, value):
        return cls(sender=sender, target=target, payload={"topic": "activity", "event": "incremented", "value": int(value)})

class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter_feature", scene_name="main")
        self.count = ObservableValue(0)
        self.countSubscription = None

    def build(self, host):
        host.sharedCount = self.count
        panelRect = Rect(20, 20, host.screen_rect.width // 2 - 30, host.screen_rect.height - 40)
        self.panel = host.app.add(PanelControl("counter_panel", panelRect, draw_background=True), scene_name="main")
        self.valueLabel = self.panel.add(LabelControl("count_label", Rect(16, 60, 320, 30), "Count: 0"))
        self.incrementButton = self.panel.add(ButtonControl("increment_button", Rect(16, 104, 160, 34), "Increment", on_click=self.incrementCount))

    def bind_runtime(self, host):
        self.countSubscription = self.count.subscribe(lambda value: setattr(self.valueLabel, "text", f"Count: {value}"))

    def shutdown_runtime(self, host):
        if self.countSubscription is not None:
            self.countSubscription()
            self.countSubscription = None

    def incrementCount(self):
        self.count.value = int(self.count.value) + 1
        message = CounterIncrementedMessage.create(self.name, "activity_log", self.count.value)
        self.send_message(message.target, message.payload)

class ActivityLogFeature(RoutedFeature):
    def __init__(self):
        super().__init__("activity_log", scene_name="main")
        self.items = ObservableList([])
        self.itemsSubscription = None
        self.sharedCountSubscription = None

    def build(self, host):
        panelRect = Rect(host.screen_rect.width // 2 + 10, 20, host.screen_rect.width // 2 - 30, host.screen_rect.height - 40)
        self.panel = host.app.add(PanelControl("log_panel", panelRect, draw_background=True), scene_name="main")
        self.latest = self.panel.add(LabelControl("log_latest", Rect(16, 60, 420, 30), "Latest: (none)"))

    def bind_runtime(self, host):
        self.itemsSubscription = self.items.subscribe(lambda values: setattr(self.latest, "text", f"Latest: {values[-1] if values else '(none)'}"))
        self.sharedCountSubscription = host.sharedCount.subscribe(lambda value: self.items.append(f"Shared count observed: {value}"))

    def shutdown_runtime(self, host):
        if self.itemsSubscription is not None:
            self.itemsSubscription()
            self.itemsSubscription = None
        if self.sharedCountSubscription is not None:
            self.sharedCountSubscription()
            self.sharedCountSubscription = None

    def message_handlers(self):
        return {"activity": self.handleActivityMessage}

    def handleActivityMessage(self, host, message):
        if message.event == "incremented":
            self.items.append(f"Counter changed to {message.get('value')}")

class Host:
    pass

host = Host()
config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1100, 680),
        window_title="gui_do Tutorial App",
        fonts={"default": {"file": None, "size": 16}},
        initial_scene_name="main",
        scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
        feature_entries=(
            FeatureSpec("counterFeature", CounterFeature),
            FeatureSpec("logFeature", ActivityLogFeature),
        ),
    )
)
bootstrap_host_application(host, config)
host.app.run_entrypoint(target_fps=60)
```

## 8. Actions and Keyboard Shortcuts

Now wire keyboard shortcuts to project behavior.

### Step 1. Declare ActionSpec and ActionHotkeySpec

ActionSpec declares host-level actions. ActionHotkeySpec declares per-feature hotkeys in routed runtime wiring.

```python
import pygame
from gui_do import ActionHotkeySpec, ActionSpec, RoutedRuntimeSpec

hostActionEntries = (
    ActionSpec(action_id="exit", label="Exit", kind="exit", category="File", key=pygame.K_ESCAPE),
    ActionSpec(action_id="palette_toggle", label="Toggle Command Palette", kind="palette_toggle", key=pygame.K_BACKQUOTE),
)

routedRuntimeSpec = RoutedRuntimeSpec(
    scene_name="main",
    action_hotkeys=(
        ActionHotkeySpec(
            action_name="activity.clear",
            key=pygame.K_l,
            scene_name="main",
        ),
    ),
)
```

### Step 2. Bind action callback in a plain Feature

In standard Feature, register/unregister callbacks in runtime hooks.

```python
import pygame

class CounterFeature(Feature):
    def bind_runtime(self, host):
        self.countSubscription = self.count.subscribe(lambda value: setattr(self.valueLabel, "text", f"Count: {value}"))
        host.app.actions.register_action("counter.increment", lambda event: (self.incrementCount() or True))
        host.app.actions.bind_key(pygame.K_SPACE, "counter.increment", scene="main")

    def shutdown_runtime(self, host):
        host.app.actions.unbind_key(pygame.K_SPACE, "counter.increment", scene="main")
        host.app.actions.unregister_action("counter.increment")
        if self.countSubscription is not None:
            self.countSubscription()
            self.countSubscription = None
```

### Step 3. RoutedFeature shortcut lifecycle

Routed feature runtime can own declarative hotkey setup/teardown.

```python
import pygame
from gui_do import (
    ActionHotkeySpec,
    RoutedFeatureLifecycleSpec,
    RoutedRuntimeSpec,
    bind_routed_feature_lifecycle,
    shutdown_routed_feature_lifecycle,
)

class ActivityLogFeature(RoutedFeature):
    def __init__(self):
        super().__init__("activity_log", scene_name="main")
        self.lifecycleSpec = RoutedFeatureLifecycleSpec(
            runtime_spec=RoutedRuntimeSpec(
                scene_name="main",
                action_hotkeys=(
                    ActionHotkeySpec(
                        action_name="activity.clear",
                        handler=self.clearLogAction,
                        key=pygame.K_l,
                        scene_name="main",
                    ),
                ),
            )
        )

    def bind_runtime(self, host):
        bind_routed_feature_lifecycle(self, host, self.lifecycleSpec)

    def shutdown_runtime(self, host):
        shutdown_routed_feature_lifecycle(self, host, self.lifecycleSpec)
```

### Step 4. Add shortcut help overlay

```python
import pygame
from gui_do import ShortcutOverlaySpec

runtimeSpec = RoutedRuntimeSpec(
    scene_name="main",
    shortcut_overlays=(
        ShortcutOverlaySpec(
            attr_name="shortcutOverlay",
            toggle_action_name="show_shortcuts",
            toggle_key=pygame.K_F1,
            toggle_scene_name="main",
            manual_shortcut_lines=(
                "Space: Increment counter",
                "L: Clear activity log",
                "F1: Toggle this shortcut overlay",
            ),
        ),
    ),
)
```

### Step 5. Updated full listing with actions and shortcuts

```python
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
    ObservableList,
    ObservableValue,
    PanelControl,
    RoutedFeature,
    RoutedFeatureLifecycleSpec,
    RoutedRuntimeSpec,
    SceneBundleBindingSpec,
    ShortcutOverlaySpec,
    bootstrap_host_application,
    bind_routed_feature_lifecycle,
    build_host_application_config,
    shutdown_routed_feature_lifecycle,
)

class CounterIncrementedMessage(FeatureMessage):
    @classmethod
    def create(cls, sender, target, value):
        return cls(sender=sender, target=target, payload={"topic": "activity", "event": "incremented", "value": int(value)})

class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter_feature", scene_name="main")
        self.count = ObservableValue(0)
        self.countSubscription = None

    def build(self, host):
        host.sharedCount = self.count
        panelRect = Rect(20, 20, host.screen_rect.width // 2 - 30, host.screen_rect.height - 40)
        self.panel = host.app.add(PanelControl("counter_panel", panelRect, draw_background=True), scene_name="main")
        self.valueLabel = self.panel.add(LabelControl("count_label", Rect(16, 60, 320, 30), "Count: 0"))
        self.incrementButton = self.panel.add(ButtonControl("increment_button", Rect(16, 104, 200, 34), "Increment (Space)", on_click=self.incrementCount))

    def bind_runtime(self, host):
        self.countSubscription = self.count.subscribe(lambda value: setattr(self.valueLabel, "text", f"Count: {value}"))
        host.app.actions.register_action("counter.increment", lambda event: (self.incrementCount() or True))
        host.app.actions.bind_key(pygame.K_SPACE, "counter.increment", scene="main")

    def shutdown_runtime(self, host):
        host.app.actions.unbind_key(pygame.K_SPACE, "counter.increment", scene="main")
        host.app.actions.unregister_action("counter.increment")
        if self.countSubscription is not None:
            self.countSubscription()
            self.countSubscription = None

    def incrementCount(self):
        self.count.value = int(self.count.value) + 1
        message = CounterIncrementedMessage.create(self.name, "activity_log", self.count.value)
        self.send_message(message.target, message.payload)

class ActivityLogFeature(RoutedFeature):
    def __init__(self):
        super().__init__("activity_log", scene_name="main")
        self.items = ObservableList([])
        self.itemsSubscription = None
        self.lifecycleSpec = RoutedFeatureLifecycleSpec(
            runtime_spec=RoutedRuntimeSpec(
                scene_name="main",
                action_hotkeys=(
                    ActionHotkeySpec(
                        action_name="activity.clear",
                        handler=self.clearLogAction,
                        key=pygame.K_l,
                        scene_name="main",
                    ),
                ),
                shortcut_overlays=(
                    ShortcutOverlaySpec(
                        attr_name="shortcutOverlay",
                        toggle_action_name="show_shortcuts",
                        toggle_key=pygame.K_F1,
                        toggle_scene_name="main",
                        manual_shortcut_lines=(
                            "Space: Increment counter",
                            "L: Clear activity log",
                            "F1: Toggle shortcut overlay",
                        ),
                    ),
                ),
            )
        )

    def build(self, host):
        panelRect = Rect(host.screen_rect.width // 2 + 10, 20, host.screen_rect.width // 2 - 30, host.screen_rect.height - 40)
        self.panel = host.app.add(PanelControl("log_panel", panelRect, draw_background=True), scene_name="main")
        self.latest = self.panel.add(LabelControl("log_latest", Rect(16, 60, 420, 30), "Latest: (none)"))

    def bind_runtime(self, host):
        self.itemsSubscription = self.items.subscribe(lambda values: setattr(self.latest, "text", f"Latest: {values[-1] if values else '(none)'}"))
        bind_routed_feature_lifecycle(self, host, self.lifecycleSpec)

    def shutdown_runtime(self, host):
        shutdown_routed_feature_lifecycle(self, host, self.lifecycleSpec)
        if self.itemsSubscription is not None:
            self.itemsSubscription()
            self.itemsSubscription = None

    def message_handlers(self):
        return {"activity": self.handleActivityMessage}

    def handleActivityMessage(self, host, message):
        if message.event == "incremented":
            self.items.append(f"Counter changed to {message.get('value')}")

    def clearLogAction(self, event):
        self.items.clear()
        self.items.append("Log cleared by keyboard action")
        return True

class Host:
    pass

host = Host()
config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1100, 680),
        window_title="gui_do Tutorial App",
        fonts={"default": {"file": None, "size": 16}},
        initial_scene_name="main",
        scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
        action_entries=(
            ActionSpec(action_id="exit", label="Exit", kind="exit", category="File", key=pygame.K_ESCAPE),
            ActionSpec(action_id="palette_toggle", label="Toggle Command Palette", kind="palette_toggle", key=pygame.K_BACKQUOTE),
        ),
        feature_entries=(
            FeatureSpec("counterFeature", CounterFeature),
            FeatureSpec("logFeature", ActivityLogFeature),
        ),
    )
)
bootstrap_host_application(host, config)
host.app.run_entrypoint(target_fps=60)
```

## 9. Spec Reference for Builders

This section is a concise builder reference. For full behavior, defaults, and integration rules, use [MANUAL.md](MANUAL.md).

### FeatureSpec

Declares one feature host slot and factory.

```python
from gui_do import FeatureSpec
featureSpecs = (
    FeatureSpec("counterFeature", CounterFeature),
)
```

### SceneBundleBindingSpec

Declares one named scene, transitions, and optional scene/root/nav emission.

```python
from gui_do import SceneBundleBindingSpec
sceneBundles = (
    SceneBundleBindingSpec(scene_name="main", make_initial=True),
)
```

### ActionSpec and ActionHotkeySpec

ActionSpec is host-level action declaration. ActionHotkeySpec is routed runtime hotkey declaration.

```python
import pygame
from gui_do import ActionHotkeySpec, ActionSpec
hostActions = (
    ActionSpec(action_id="exit", label="Exit", kind="exit", key=pygame.K_ESCAPE),
)
routedHotkeys = (
    ActionHotkeySpec(action_name="activity.clear", key=pygame.K_l, scene_name="main"),
)
```

### ShortcutOverlaySpec

Declares a feature-scoped shortcut help overlay and toggle binding.

```python
import pygame
from gui_do import ShortcutOverlaySpec
overlaySpecs = (
    ShortcutOverlaySpec(attr_name="shortcutOverlay", toggle_action_name="show_shortcuts", toggle_key=pygame.K_F1, toggle_scene_name="main"),
)
```

### RoutedRuntimeSpec and RoutedFeatureLifecycleSpec

Bundle routed runtime wiring and lifecycle setup/teardown.

```python
from gui_do import RoutedFeatureLifecycleSpec, RoutedRuntimeSpec
lifecycleSpec = RoutedFeatureLifecycleSpec(runtime_spec=RoutedRuntimeSpec(scene_name="main"))
```

### Higher-level runtime faculties

RoutedRuntimeSpec can declaratively wire policy/effects/pipelines/durable queue/capability/projection and dependency/workflow/recompute/QoS/health/replay/hot-swap systems.

```python
from gui_do import RoutedRuntimeSpec
runtimeSpec = RoutedRuntimeSpec(
    scene_name="main",
    policy_specs=(),
    effect_bindings=(),
    event_pipelines=(),
    durable_queue_spec=None,
    capability_providers=(),
    capability_requirements=(),
    projection_spec=None,
    feature_dependencies=(),
    workflow_specs=(),
    recompute_nodes=(),
    qos_policies=(),
    health_probes=(),
    replay_spec=None,
    replace_policy=None,
)
```

### ToastManager

ToastManager is available on host.app for transient user feedback.

```python
from gui_do import ToastSeverity
host.app.toasts.show("Saved", severity=ToastSeverity.INFO)
```

For details and full option matrices, use [MANUAL.md](MANUAL.md) and especially sections 8.1, 8.2, 8.3, and 8.4.

## 10. Complete Project Listing

The listing below is a full runnable project with:

- Two features with distinct responsibilities.
- Observable state driving labels.
- Keyboard actions with ActionSpec and routed action hotkeys.
- One RoutedFeature using RoutedRuntimeSpec.
- Clean subscription and runtime teardown.

```python
# Standard library and pygame imports for runtime and rect geometry.
import pygame
from pygame import Rect

# All gui_do imports come from the public root surface.
from gui_do import (
    ActionHotkeySpec,
    ActionSpec,
    ButtonControl,
    Feature,
    FeatureMessage,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    ObservableList,
    ObservableValue,
    PanelControl,
    RoutedFeature,
    RoutedFeatureLifecycleSpec,
    RoutedRuntimeSpec,
    SceneBundleBindingSpec,
    ShortcutOverlaySpec,
    bootstrap_host_application,
    bind_routed_feature_lifecycle,
    build_host_application_config,
    shutdown_routed_feature_lifecycle,
)

# Typed message envelope keeps cross-feature communication explicit.
class CounterIncrementedMessage(FeatureMessage):
    @classmethod
    def create(cls, sender, target, value):
        return cls(
            sender=sender,
            target=target,
            payload={"topic": "activity", "event": "incremented", "value": int(value)},
        )

# Counter feature owns increment behavior and shared counter state.
class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter_feature", scene_name="main")
        self.count = ObservableValue(0)
        self.countSubscription = None

    def build(self, host):
        host.sharedCount = self.count
        panelRect = Rect(20, 20, host.screen_rect.width // 2 - 30, host.screen_rect.height - 40)
        self.panel = host.app.add(PanelControl("counter_panel", panelRect, draw_background=True), scene_name="main")

        self.panel.add(LabelControl("counter_title", Rect(16, 16, 360, 28), "Counter Dashboard"))
        self.valueLabel = self.panel.add(LabelControl("count_label", Rect(16, 60, 360, 30), "Count: 0"))
        self.hintLabel = self.panel.add(LabelControl("counter_hint", Rect(16, 92, 380, 30), "Use button or Space key."))

        self.incrementButton = self.panel.add(
            ButtonControl(
                "increment_button",
                Rect(16, 130, 220, 36),
                "Increment (Space)",
                on_click=self.incrementCount,
                style="round",
            )
        )

    def bind_runtime(self, host):
        self.countSubscription = self.count.subscribe(
            lambda value: setattr(self.valueLabel, "text", f"Count: {value}")
        )

        host.app.actions.register_action(
            "counter.increment",
            lambda event: (self.incrementCount() or True),
        )
        host.app.actions.bind_key(pygame.K_SPACE, "counter.increment", scene="main")

    def shutdown_runtime(self, host):
        host.app.actions.unbind_key(pygame.K_SPACE, "counter.increment", scene="main")
        host.app.actions.unregister_action("counter.increment")

        if self.countSubscription is not None:
            self.countSubscription()
            self.countSubscription = None

    def incrementCount(self):
        self.count.value = int(self.count.value) + 1
        typedMessage = CounterIncrementedMessage.create(
            self.name,
            "activity_log",
            self.count.value,
        )
        self.send_message(typedMessage.target, typedMessage.payload)

# Routed log feature receives topic-based messages and manages shortcut helpers.
class ActivityLogFeature(RoutedFeature):
    def __init__(self):
        super().__init__("activity_log", scene_name="main")
        self.items = ObservableList([])
        self.itemsSubscription = None
        self.sharedCountSubscription = None

        self.lifecycleSpec = RoutedFeatureLifecycleSpec(
            runtime_spec=RoutedRuntimeSpec(
                scene_name="main",
                action_hotkeys=(
                    ActionHotkeySpec(
                        action_name="activity.clear",
                        handler=self.clearLogAction,
                        key=pygame.K_l,
                        scene_name="main",
                    ),
                ),
                shortcut_overlays=(
                    ShortcutOverlaySpec(
                        attr_name="shortcutOverlay",
                        toggle_action_name="show_shortcuts",
                        toggle_key=pygame.K_F1,
                        toggle_scene_name="main",
                        manual_shortcut_lines=(
                            "Space: Increment counter",
                            "L: Clear activity log",
                            "F1: Toggle shortcut help",
                            "Escape: Exit application",
                        ),
                    ),
                ),
            )
        )

    def build(self, host):
        panelRect = Rect(
            host.screen_rect.width // 2 + 10,
            20,
            host.screen_rect.width // 2 - 30,
            host.screen_rect.height - 40,
        )
        self.panel = host.app.add(PanelControl("log_panel", panelRect, draw_background=True), scene_name="main")

        self.panel.add(LabelControl("log_title", Rect(16, 16, 420, 28), "Activity Log"))
        self.latest = self.panel.add(LabelControl("log_latest", Rect(16, 60, 460, 30), "Latest: (none)"))
        self.countMirror = self.panel.add(LabelControl("count_mirror", Rect(16, 92, 460, 30), "Shared count: 0"))

    def bind_runtime(self, host):
        self.itemsSubscription = self.items.subscribe(
            lambda values: setattr(self.latest, "text", f"Latest: {values[-1] if values else '(none)'}")
        )
        self.sharedCountSubscription = host.sharedCount.subscribe(
            lambda value: setattr(self.countMirror, "text", f"Shared count: {value}")
        )

        bind_routed_feature_lifecycle(self, host, self.lifecycleSpec)

    def shutdown_runtime(self, host):
        shutdown_routed_feature_lifecycle(self, host, self.lifecycleSpec)

        if self.itemsSubscription is not None:
            self.itemsSubscription()
            self.itemsSubscription = None

        if self.sharedCountSubscription is not None:
            self.sharedCountSubscription()
            self.sharedCountSubscription = None

    def message_handlers(self):
        return {"activity": self.handleActivityMessage}

    def handleActivityMessage(self, host, message):
        if message.event == "incremented":
            self.items.append(f"Counter changed to {message.get('value')}")

    def clearLogAction(self, event):
        self.items.clear()
        self.items.append("Log cleared by routed keyboard action")
        return True

# Host container receives runtime attributes during bootstrap.
class Host:
    pass

# Declarative app setup keeps startup wiring centralized and testable.
host = Host()
config = build_host_application_config(
    HostApplicationBindingSpec(
        display_size=(1200, 720),
        window_title="gui_do Dashboard and Activity Log",
        fonts={"default": {"file": None, "size": 16}},
        initial_scene_name="main",
        scene_bundle_entries=(
            SceneBundleBindingSpec(scene_name="main", make_initial=True),
        ),
        action_entries=(
            ActionSpec(action_id="exit", label="Exit", kind="exit", category="File", key=pygame.K_ESCAPE),
            ActionSpec(action_id="palette_toggle", label="Toggle Command Palette", kind="palette_toggle", key=pygame.K_BACKQUOTE),
        ),
        feature_entries=(
            FeatureSpec("counterFeature", CounterFeature),
            FeatureSpec("logFeature", ActivityLogFeature),
        ),
    )
)

# Bootstrap all declared systems, then enter the frame loop.
bootstrap_host_application(host, config)
host.app.run_entrypoint(target_fps=60)
```

## 11. Next Steps

You now have a complete, data-driven multi-feature app built on the public gui_do root API. The best next move is to use [MANUAL.md](MANUAL.md) as your system reference while iterating on your own project.

Recommended path:

1. Read [MANUAL.md](MANUAL.md) sections 8.1, 8.2, 8.3, and 8.4 to deepen your bootstrap, lifecycle, actions, and state model.
2. Explore [demo_features/](demo_features) as living package-layout patterns (one folder per feature package, package root as public import surface).
3. Expand this app with overlays, persistence, scene navigation, telemetry spans, and graphics helpers.

If you want to demystify the runtime internals, read data_driven_runtime.py and feature_lifecycle.py in the library source. They are designed to be readable and map directly to the concepts you just used.
