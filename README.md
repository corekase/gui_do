[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg?branch=main)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)
# gui_do
### Latest Demonstration

---

<a href="https://www.youtube.com/watch?v=OVj54_BhDO4"><img src="https://img.youtube.com/vi/OVj54_BhDO4/0.jpg" alt="Demo Video"></img></a>

---

gui_do is a Python GUI framework built on pygame for developers who want structured, scalable desktop interfaces without hand-wiring every system by hand. Its core model combines declarative specs, feature lifecycles, and reactive state so application structure is described once and bootstrap handles the runtime composition. The framework automates event routing, overlay dispatch, focus flow, scene transitions, and lifecycle ordering so features can stay isolated and focused on behavior. gui_do is a strong fit for Python teams building desktop tools, game UIs, simulations, and other interactive applications.

## Strengths

- **Declarative runtime wiring.** Specs describe what the app contains; bootstrap builds how everything is connected.
- **Feature lifecycle isolation.** Each feature owns `build`, `bind_runtime`, `on_update`, `draw`, and `shutdown_runtime` with deterministic ordering.
- **Reactive state.** `ObservableValue`, `ObservableList`, and `ObservableDict` propagate change immediately without polling loops.
- **Composable overlays.** Dialogs, toasts, tooltips, command palette, context menus, and shortcut help share consistent routing behavior.
- **Tiered API surface.** A 32-tier export model supports both high-level app bootstrap and lower-level rendering/audio systems.
- **Scene management.** Multi-scene apps get scene-scoped routing, transition support, and clear scene ownership boundaries.
- **Persistence and migration.** Workspace state supports restore reporting and versioned snapshot migration.
- **Accessibility and focus.** Semantic accessibility nodes, focus rings, and live announcements are built into the runtime.
- **Built-in diagnostics.** Telemetry, recording/playback, and inspection tools make runtime behavior observable.
- **Extensible by feature design.** New behavior is added by implementing lifecycle methods, not by changing framework internals.

For guided learning, continue with [TUTORIAL.md](TUTORIAL.md). For complete system detail, see [MANUAL.md](MANUAL.md).

## Use Cases

gui_do is well suited to internal developer tools such as dashboards, inspectors, and data explorers where strong lifecycle boundaries keep large interfaces maintainable. It also works well for game interfaces and HUD workflows that need scene changes, overlays, 2D rendering, and audio cues in one runtime model. Interactive simulations benefit from reactive controls and deterministic per-frame updates, while data visualization tools can combine list/grid controls with targeted redraw behavior for responsiveness. Workbench-style applications with task panels, tabbed windows, and command surfaces map naturally to the scene and window presentation systems. It is also a practical rapid-prototyping stack for layout-heavy interfaces using constraint and flex approaches.

For full build guidance and rationale, see [TUTORIAL.md](TUTORIAL.md). For complete API/system reference, see [MANUAL.md](MANUAL.md).

## Quick Look

```python
import pygame
from pygame import Rect
from gui_do import (
    Feature, FeatureSpec, HostApplicationBindingSpec, LabelControl,
    ObservableValue, SceneBundleBindingSpec,
    build_host_application_config, bootstrap_host_application,
)


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self.count_value = ObservableValue(0)
        self.count_label = None
        self.count_subscription = None

    def build(self, host) -> None:
        self.count_label = host.app.add(
            LabelControl("count_label", Rect(24, 24, 320, 36), "Count: 0"),
            scene_name="main",
        )

    def bind_runtime(self, host) -> None:
        self.count_subscription = self.count_value.subscribe(lambda value: setattr(self.count_label, "text", f"Count: {value}"))


class Host:
    pass


config = build_host_application_config(HostApplicationBindingSpec(
    display_size=(700, 180), window_title="gui_do Quick Look", fonts={"default": {"size": 16}}, initial_scene_name="main",
    scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True, bind_escape_to_exit=True),),
    feature_entries=(FeatureSpec(attr_name="counter_feature", factory=CounterFeature),),
))

pygame.init(); host = Host(); bootstrap_host_application(host, config); host.app.run_entrypoint(target_fps=60)
```

## Documentation

| Document | Purpose |
|----------|---------|
| [TUTORIAL.md](TUTORIAL.md) | Step-by-step project tutorial — start here if you are new to gui_do |
| [MANUAL.md](MANUAL.md) | Complete developer reference for all systems and APIs |

TUTORIAL.md teaches the framework by building a complete project from zero, explaining both how and why at each step. MANUAL.md is the full reference organized by systems, with API tables, usage patterns, examples, integration recipes, and appendices.

## Installation

`python -m pip install -e . --no-deps`

Requires `pygame` and `numpy`.

## Project Structure

- `gui_do/` - library source and public exports
- `demo_features/` - runnable reference patterns using folder-per-feature packages and package-root `__init__.py` exports
- `tests/` - contract and behavioral tests
- `docs/` - architecture and runtime operating contracts
- `TUTORIAL.md` - complete step-by-step tutorial
- `MANUAL.md` - complete developer reference

## See Also

- [TUTORIAL.md](TUTORIAL.md)
- [MANUAL.md](MANUAL.md)
- [demo_features/](demo_features/)
- [docs/](docs/)
- [gui_do/__init__.py](gui_do/__init__.py)
