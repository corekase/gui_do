# gui_do

### Latest Demonstration

---

<a href="https://www.youtube.com/watch?v=OVj54_BhDO4"><img src="https://img.youtube.com/vi/OVj54_BhDO4/0.jpg" alt="Demo Video"></img></a>

---

[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg?branch=main)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)

gui_do is a Python GUI framework built on pygame that replaces imperative scene setup with a declarative spec-and-lifecycle model. You describe your application — its scenes, features, actions, windows, and overlays — using data objects, and the bootstrap system wires the full runtime automatically. Reactive state, focus management, event routing, overlay dispatch, and lifecycle sequencing are handled by the framework so your code stays focused on application behavior. It targets Python developers building desktop tools, game UIs, simulations, and interactive applications.

---

## Strengths

**Declarative runtime wiring.** Specs describe what the application needs; `bootstrap_host_application` reads them and builds the runtime — no manual wiring of scenes, actions, or overlays required.

**Feature lifecycle isolation.** Each feature owns its `build`, `bind_runtime`, `on_update`, `handle_event`, `draw`, and `shutdown_runtime` hooks. Features never need to coordinate their setup order with each other.

**Reactive state.** `ObservableValue`, `ObservableList`, and `ObservableDict` notify subscribers when they change. UI updates are driven by state, not polling.

**Composable overlays.** Dialogs, toasts, tooltips, the command palette, context menus, and shortcut help overlays all share consistent dispatch routing and keyboard/mouse dismissal semantics.

**Tiered API surface.** 32 tiers span from high-level bootstrap helpers (`HostApplicationBindingSpec`, `build_host_application_config`) down to a 2D scene graph, particle systems, tile maps, and audio cues. Use only the tiers your application needs.

**Scene management.** Multi-scene applications with animated transitions, scene-scoped routing, and per-scene task panels and return buttons are declared with `SceneBundleBindingSpec` and `RuntimeSceneSpec`.

**Persistence and migration.** `WorkspacePersistenceManager` saves and restores workspace state across sessions. `SnapshotMigrator` handles versioned migration with a composable BFS migration graph.

**Accessibility and focus.** A semantic `AccessibilityTree`, `FocusRing`, live-region announcements via `AccessibilityBus`, and `AccessibilityRole` vocabulary provide structured accessibility support.

**Built-in diagnostics.** `TelemetryCollector` instruments high-frequency paths. `EventRecorder` and `EventPlayback` replay input sequences. `PropertyInspector` exposes live runtime state.

**Extensible without framework changes.** New behavior is added by implementing lifecycle methods on a `Feature` subclass. The framework never requires modification to accommodate new patterns.

---

## Use Cases

**Developer tools and internal utilities.** Dashboards, data explorers, and property inspectors fit naturally into the feature-per-concern model. Observable state means the UI stays live as underlying data changes.

**Game interfaces and HUDs.** `DirectFeature` supports custom draw passes. `ParticleSystem`, `TileMap`, `SpriteSheet`, `SceneGraph2D`, and `SoundEventBus` provide the rendering and audio primitives needed for game overlays and full game UIs.

**Interactive simulations.** Cellular automata, physics visualizations, and parameter explorers use `CooperativeScheduler` for frame-budget-aware background computation and `ObservableValue` to bind parameter controls to simulation state.

**Data visualization tools.** `ListViewControl`, `DataGridControl`, `CollectionView`, `SortFilterProxySource`, and dirty-region rendering combine to produce performant data displays with sortable, filterable collections.

**Multi-window workbench applications.** `WindowSpec`, `FeatureWindowBundleBindingSpec`, and `WindowToggleBindingSpec` declare floating tool windows with task-panel toggle buttons, keyboard shortcuts, and accessibility labels in a single spec object.

**Rapid GUI layout prototyping.** `ConstraintLayout`, `FlexLayout`, `GridLayout`, `AdaptivePolicy`, and `ResponsiveLayout` cover a wide range of layout strategies without custom geometry code.

---

## Quick Look

A minimal runnable application showing the core pattern — one feature, one observable value, one reactive label, bootstrapped from specs:

```python
import pygame
from pygame import Rect

from gui_do import (
    Feature,
    FeatureSpec,
    HostApplicationBindingSpec,
    LabelControl,
    ButtonControl,
    ObservableValue,
    SceneBundleBindingSpec,
    build_host_application_config,
    bootstrap_host_application,
)


class CounterFeature(Feature):
    def __init__(self) -> None:
        super().__init__("counter_feature", scene_name="main")
        self._count = ObservableValue(0)

    def build(self, host) -> None:
        self._label = host.app.add(
            LabelControl("count_label", Rect(24, 24, 260, 32), "Count: 0"),
            scene_name="main",
        )
        host.app.add(
            ButtonControl("inc_btn", Rect(24, 68, 120, 32), "+1", on_click=self._increment),
            scene_name="main",
        )

    def bind_runtime(self, host) -> None:
        def _sync(v: int) -> None:
            self._label.text = f"Count: {v}"
        self._sub = self._count.subscribe(_sync)
        _sync(self._count.value)

    def shutdown_runtime(self, host) -> None:
        self._sub.dispose()

    def _increment(self) -> None:
        self._count.value = self._count.value + 1


binding = HostApplicationBindingSpec(
    scene_bundles=(SceneBundleBindingSpec(scene_name="main", initial=True),),
    feature_specs=(FeatureSpec(attr_name="counter_feature", factory=CounterFeature),),
)
config = build_host_application_config(
    binding,
    display_size=(640, 200),
    window_title="Quick Look",
    target_fps=60,
)


class App:
    def __init__(self) -> None:
        bootstrap_host_application(self, config)

    def run(self) -> None:
        self.app.run_entrypoint(target_fps=config.target_fps)


if __name__ == "__main__":
    pygame.init()
    try:
        App().run()
    finally:
        pygame.quit()
```

See [TUTORIAL.md](TUTORIAL.md) for a full step-by-step walkthrough of this pattern, and [MANUAL.md](MANUAL.md) for the complete API reference.

---

## Documentation

| Document | Purpose |
|----------|---------|
| [TUTORIAL.md](TUTORIAL.md) | Step-by-step project tutorial — start here if you are new to gui_do |
| [MANUAL.md](MANUAL.md) | Complete developer reference for all systems and APIs |

TUTORIAL.md teaches the framework by building a complete multi-feature application from scratch, explaining both how and why at every step. By the end you will understand feature lifecycles, reactive state, actions, routed features, and the bootstrap model well enough to build your own application.

MANUAL.md is the comprehensive reference organized by system — 16 system chapters covering bootstrap, feature lifecycle, events and actions, state and observables, controls, layout, focus, overlays, scene/window/task-panel presentation, scheduling, persistence, theme, text and forms, data and dataflow, graphics and audio, and telemetry. It includes API tables, usage patterns, integration recipes, and appendices (glossary, lifecycle sequence, system dependency map, API quick index, architecture templates).

---

## Installation

From the repository root:

```bash
python -m pip install -e . --no-deps
```

Requires `pygame`. The `--no-deps` flag skips pip's dependency resolution for the local install; install `pygame` separately if it is not already present.

---

## Project Structure

```
gui_do/           Python package — the framework library (32 API tiers)
demo_features/    Runnable reference patterns organized by feature/scene folder
tests/            Contract and behavioral test suite
docs/             Architecture boundary and runtime operating contracts
TUTORIAL.md       Step-by-step project tutorial
MANUAL.md         Complete developer reference
```

Each subfolder under `demo_features/` is a self-contained feature package. Its `__init__.py` is the sole public surface — bootstrap only ever imports from the package root, never from internal submodules. This is the established organizational pattern for gui_do applications.

---

## See Also

- [TUTORIAL.md](TUTORIAL.md) — learn gui_do by building a project from scratch
- [MANUAL.md](MANUAL.md) — complete reference for all systems, APIs, and patterns
- [demo_features/](demo_features/) — living reference patterns: routed runtime specs, scene shell helpers, shortcut overlays, window presentation
- [docs/](docs/) — architecture boundary specifications and runtime operating contracts
- [gui_do/\_\_init\_\_.py](gui_do/__init__.py) — authoritative public API source (32 tiers)
