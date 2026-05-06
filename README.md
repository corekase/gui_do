[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg?branch=main)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)
# gui_do
### Latest Demonstration

---

<a href="https://www.youtube.com/watch?v=OVj54_BhDO4"><img src="https://img.youtube.com/vi/OVj54_BhDO4/0.jpg" alt="Demo Video"></img></a>

---

gui_do is a Python GUI framework built on pygame for teams that want predictable structure without hand-wiring every runtime system. The core programming model is declarative: you define scenes, features, and actions as specs, then bootstrap assembles the application consistently. Features follow a clear lifecycle and pair naturally with reactive state so UI updates are driven by data changes instead of polling loops. The framework handles event routing, overlay dispatch, focus behavior, scene transitions, and lifecycle sequencing so feature code can stay isolated. It is designed for Python developers building desktop tools, game UIs, simulations, and other interactive applications.

## Strengths

- **Declarative runtime wiring**: Specs describe what exists; bootstrap decides how it is composed and initialized.
- **Feature lifecycle isolation**: Each feature owns build, bind_runtime, update, draw, and teardown responsibilities with deterministic ordering.
- **Reactive state primitives**: ObservableValue, ObservableList, and ObservableDict propagate changes immediately to subscribed UI logic.
- **Composable overlays**: Dialogs, toasts, tooltips, command palette, context menus, and shortcut help share consistent routing behavior.
- **Tiered API surface**: A 32-tier export model lets you stay high-level or drop lower when needed.
- **Scene management**: Multi-scene apps get scene-scoped routing, transitions, and explicit scene presentation boundaries.
- **Persistence and migration**: Workspace restore reports and snapshot migration support long-lived tools and evolving state models.
- **Accessibility and focus**: Semantic accessibility nodes, focus rings, and live announcements are first-class runtime concerns.
- **Built-in diagnostics**: Telemetry hooks, event recording/playback, and inspection surfaces make behavior observable.
- **Extensible architecture**: New behavior is usually added by implementing feature lifecycle methods, not patching framework internals.

## Use Cases

gui_do is a strong fit for internal developer tools such as dashboards, inspectors, and data explorers where deterministic lifecycle boundaries keep complex interfaces maintainable. It also maps well to game-facing interfaces and HUD tooling that benefit from scene transitions, overlay systems, 2D rendering helpers, and audio cues in one runtime model. Interactive simulations and parameter explorers benefit from reactive state and predictable update loops, while data-heavy utilities can combine lists, grids, and targeted redraw strategies for responsiveness. For workbench-style software, gui_do supports tabbed and windowed compositions, task-panel command surfaces, and scene-scoped workflows. It is also effective for rapid prototyping with constraint and flex layout systems.

## Quick Look

```python
import pygame
from pygame import Rect
from gui_do import (
    Feature,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    ObservableValue,
    SceneBundleBindingSpec,
    bootstrap_host_application,
    build_host_application_config,
)


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self.count = ObservableValue(0)

    def build(self, host) -> None:
        self.label = host.app.add(LabelControl("count", Rect(24, 24, 260, 36), "Count: 0"), scene_name="main")

    def bind_runtime(self, host) -> None:
        self._sub = self.count.subscribe(lambda v: setattr(self.label, "text", f"Count: {v}"))


class Host:
    pass


config = build_host_application_config(HostApplicationBindingSpec(
    display_size=(640, 180), window_title="gui_do Quick Look", fonts={"default": {"size": 16}}, initial_scene_name="main",
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

TUTORIAL.md teaches the framework through one complete project built from scratch, explaining both how and why at each step. MANUAL.md is the comprehensive reference organized by system, with API tables, usage patterns, examples, integration recipes, and appendices.

## Installation

python -m pip install -e . --no-deps

Dependencies: pygame and numpy.

## Project Structure

- gui_do/: library source and the authoritative public API exports.
- demo_features/: runnable folder-per-feature reference packages with package-root public surfaces.
- tests/: contract and behavioral tests for runtime and API expectations.
- docs/: architecture boundaries and runtime operating contracts.
- TUTORIAL.md: complete step-by-step learning path.
- MANUAL.md: full developer reference.

## See Also

- [TUTORIAL.md](TUTORIAL.md)
- [MANUAL.md](MANUAL.md)
- [demo_features/](demo_features/)
- [docs/](docs/)
- [gui_do/__init__.py](gui_do/__init__.py)
