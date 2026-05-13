[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg?branch=main)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)
# gui_do
### Latest Demonstration

---

<a href="https://www.youtube.com/watch?v=LYfCgm7G95E"><img src="https://img.youtube.com/vi/LYfCgm7G95E/0.jpg" alt="Demo Video"></img></a>

---

## Overview

gui_do is a Python GUI framework built on pygame for data-driven desktop applications. You declare scenes, features, actions, and runtime behaviors with specs, then bootstrap assembles those declarations into a running application. The core model combines feature lifecycle phases with reactive state so UI updates flow from data changes rather than polling. It automates event routing, overlay dispatch, focus handling, scene transitions, and lifecycle sequencing so each feature can focus on its own responsibility. gui_do is aimed at Python developers building desktop tools, game UIs, simulations, and other interactive applications.

## Strengths

- Declarative runtime wiring: specs describe what exists, and bootstrap builds how it is wired.
- Feature lifecycle isolation: each feature owns `build`, `bind_runtime`, `on_update`, `draw`, and `shutdown_runtime` boundaries.
- Reactive state: `ObservableValue`, `ObservableList`, and `ObservableDict` trigger updates without manual polling loops.
- Composable overlays: dialogs, toasts, tooltips, command palette, and context menus share consistent dispatch behavior.
- Tiered API surface: 32 tiers support high-level bootstrap usage and lower-level control when needed.
- Scene management: multi-scene apps support transition styles and scene-scoped routing.
- Persistence and migration: workspace state save/restore supports versioned snapshot migration paths.
- Accessibility and focus: semantic accessibility tree support, focus rings, and live announcements are built in.
- Built-in diagnostics: telemetry spans, property inspection, and event record/playback are available for operations.
- Extensible composition: new behavior is added by implementing feature lifecycle methods rather than editing framework internals.

For deeper system detail, continue in [TUTORIAL.md](TUTORIAL.md) and [MANUAL.md](MANUAL.md).

## Use Cases

gui_do fits developer tools and internal utilities such as dashboards, inspectors, and data explorers. It also supports game interfaces and HUDs with particle effects, tile maps, 2D scene graph support, and audio cues. Interactive simulations benefit from deterministic updates and reactive state for parameter exploration. Data visualization tools can combine sortable/filterable views with efficient redraw patterns. Multi-window workbench applications can compose tabbed panels and tool windows, and rapid layout prototyping is supported through constraint and flex layout systems.

If you want a full build path, start with [TUTORIAL.md](TUTORIAL.md). If you want complete API coverage, use [MANUAL.md](MANUAL.md).

## Quick Look

```python
import pygame
from gui_do import Feature, FeatureSpec, HostApplicationBindingSpec, LabelControl, ObservableValue, PanelControl, SceneBundleBindingSpec, bootstrap_host_application, build_host_application_config

class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter_feature", scene_name="main")
        self.count = ObservableValue(0)
        self.unsub = None

    def build(self, host):
        root = host.app.add(PanelControl("root", host.screen_rect.copy(), draw_background=False), scene_name="main")
        self.label = root.add(LabelControl("count_label", pygame.Rect(20, 20, 280, 36), "Count: 0"))

    def bind_runtime(self, host):
        self.unsub = self.count.subscribe(lambda value: setattr(self.label, "text", f"Count: {value}"))

class QuickLookHost:
    def __init__(self):
        binding = HostApplicationBindingSpec(
            display_size=(960, 540),
            window_title="Quick Look",
            fonts={"default": {"file": None, "size": 16}},
            initial_scene_name="main",
            scene_bundle_entries=(SceneBundleBindingSpec(scene_name="main", make_initial=True),),
            feature_entries=(FeatureSpec("counter_feature", CounterFeature),),
        )
        config = build_host_application_config(binding)
        bootstrap_host_application(self, config)

QuickLookHost().app.run_entrypoint(target_fps=60)
```

## Documentation

| Document | Purpose |
|----------|---------|
| [TUTORIAL.md](TUTORIAL.md) | Step-by-step project tutorial - start here if you are new to gui_do |
| [MANUAL.md](MANUAL.md) | Complete developer reference for all systems and APIs |

[TUTORIAL.md](TUTORIAL.md) teaches the framework by building a complete project from scratch and explains both how and why each step works. [MANUAL.md](MANUAL.md) is the comprehensive reference organized by system, including API tables, usage patterns, integration recipes, and appendices.

## Installation

```bash
python -m pip install -e . --no-deps
```

Dependencies: `pygame` and `numpy`.

## Project Structure

- `gui_do/`: library source and the authoritative root API surface.
- `demo_features/`: runnable reference patterns using the folder-per-feature package convention.
- `tests/`: behavioral and contract test coverage.
- `docs/`: architecture boundaries and runtime operating contracts.
- `TUTORIAL.md`: step-by-step project tutorial.
- `MANUAL.md`: full system and API reference.

## See Also

- [TUTORIAL.md](TUTORIAL.md)
- [MANUAL.md](MANUAL.md)
- [demo_features/](demo_features)
- [docs/](docs)
- [gui_do/__init__.py](gui_do/__init__.py)
