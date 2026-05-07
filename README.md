[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg?branch=main)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)
# gui_do

### Latest Demonstration

---

<a href="https://www.youtube.com/watch?v=OVj54_BhDO4"><img src="https://img.youtube.com/vi/OVj54_BhDO4/0.jpg" alt="Demo Video"></img></a>

---

`gui_do` is a Python GUI framework built on pygame that structures applications around
declarative specs, a feature lifecycle, and reactive observable state. Instead of writing
imperative setup sequences, you describe what your application contains — scenes, features,
actions, and controls — and the bootstrap system wires everything together automatically.
The framework handles event routing, overlay dispatch, focus management, scene transitions,
and lifecycle sequencing so that your code focuses on behavior rather than plumbing. It is
suited for Python developers building desktop tools, game UIs, simulations, and interactive
applications of any complexity.

---

## Strengths

**Declarative runtime wiring.** Specs describe what your application contains; bootstrap
reads those specs and builds all connections. Features never need to know about each other's
internal structure.

**Feature lifecycle isolation.** Each feature owns its `build`, `bind_runtime`, `on_update`,
`handle_event`, `draw`, and `shutdown_runtime` phases. The framework guarantees all features
complete `build` before any `bind_runtime` runs — no manual ordering required.

**Reactive state.** `ObservableValue`, `ObservableList`, and `ObservableDict` notify
subscribers when they change. UI updates happen in callbacks, not polling loops. `ComputedValue`
derives state from other observables and propagates changes automatically.

**Composable overlays.** Dialogs, toasts, tooltips, the command palette, and context menus all
share consistent routing and focus semantics. Adding an overlay to a scene requires one spec and
one call — not a bespoke event chain.

**Tiered API surface.** Thirty-two tiers organize the public API from high-level bootstrap
helpers (Tier 1) down to the 2D scene graph, audio, and snapshot migration (Tiers 16–32).
Applications can work entirely at Tier 1–3 or reach deeper tiers as needed.

**Scene management.** Multi-scene applications declare transitions, initial scene, and
escape behavior in one binding spec. Animated transitions (fade, slide) and scene-scoped
event routing are built in.

**Persistence and migration.** Workspace state is saved and restored through a versioned
snapshot system with a BFS migration graph. Restore reports enumerate applied settings,
skipped keys, and scene switches.

**Accessibility and focus.** A semantic accessibility tree, focus rings, and live-region
announcements are available at Tier 21. Focus cycling is deterministic and ordered by
`control_id`.

**Built-in diagnostics.** Telemetry spans wrap high-frequency paths. `EventRecorder` and
`EventPlayback` support reproducible test scenarios. `PropertyInspectorPanel` exposes live
runtime values.

**Extensible without framework changes.** New features add behavior by implementing lifecycle
methods. The framework does not require modification — new capabilities compose in from outside.

---

## Use Cases

**Developer tools and internal utilities.** Dashboards, data inspectors, parameter explorers,
and pipeline monitors all compose naturally from `Feature`, observable state, and the
`ListViewControl` and `DataGridControl` components.

**Game interfaces and HUDs.** The `ParticleSystem`, `TileMap`, `SpriteSheet`, and `SceneGraph2D`
components are first-class citizens. Audio cues via `SoundEventBus` and frame-accurate animation
via `TweenManager` and `AnimationStateMachine` complete the toolkit.

**Interactive simulations.** Conway's Life, the Mandelbrot explorer, and the bouncing-shapes demo
in `demo_features/` show how to wire compute-intensive logic into a `LogicFeature`, keep UI
responsive, and exchange state with visual features through `ObservableValue` and `FeatureMessage`.

**Data visualization tools.** Sortable and filterable lists via `CollectionView` and
`SortFilterProxySource`, virtualized grids via `VirtualizationCore`, and dirty-region
rendering via `DirtyRegionTracker` support efficient displays of large datasets.

**Multi-window workbench applications.** Task panels, tabbed windows, floating tool windows,
and docked panes are all first-class presentation models. `DockWorkspace`, `TabControl`, and
`WindowControl` wire into the scene presentation system with one bundle spec.

**Rapid layout prototyping.** The adaptive constraint layout (`ConstraintLayoutEngine`),
flex layout (`FlexLayout`), and responsive breakpoint system (`ResponsiveLayout`) make it
straightforward to iterate on complex spatial arrangements.

---

## Quick Look

```python
import pygame
from pygame import Rect
from gui_do import (
    Feature, PanelControl, LabelControl, ButtonControl, ObservableValue,
    FeatureSpec, SceneBundleBindingSpec, HostApplicationBindingSpec,
    build_host_application_config, bootstrap_host_application,
)

class CounterFeature(Feature):
    def __init__(self):
        super().__init__("counter", scene_name="main")

    def build(self, host):
        host.counter_value = ObservableValue(0)
        self._count = host.counter_value
        r = host.screen_rect
        root = host.app.add(PanelControl("root", Rect(0, 0, r.width, r.height),
                                         draw_background=False), scene_name="main")
        self._label = root.add(LabelControl("lbl", Rect(20, 20, 200, 36), "Count: 0"))
        root.add(ButtonControl("btn", Rect(20, 70, 100, 36), "+1",
                               on_click=lambda: setattr(self._count, "value",
                                                        self._count.value + 1)))

    def bind_runtime(self, host):
        self._sub = self._count.subscribe(
            lambda v: setattr(self._label, "text", f"Count: {v}"))

    def shutdown_runtime(self, host):
        if self._sub:
            self._sub(); self._sub = None

config = build_host_application_config(HostApplicationBindingSpec(
    display_size=(800, 600), window_title="Counter",
    fonts={"default": {"size": 14}}, initial_scene_name="main",
    feature_entries=[FeatureSpec(attr_name="counter", factory=CounterFeature)],
    scene_bundle_entries=[SceneBundleBindingSpec(scene_name="main", make_initial=True)],
))

class App:
    def __init__(self): bootstrap_host_application(self, config)

App().app.run_entrypoint(target_fps=60)
```

The pattern: declare features in specs → bootstrap builds the host → the frame loop runs.
Features are isolated; `ObservableValue` subscriptions connect state to UI without coupling
features directly to each other.

Read [TUTORIAL.md](TUTORIAL.md) to build a complete project from this foundation.
Read [MANUAL.md](MANUAL.md) for the full API and system reference.

---

## Documentation

| Document | Purpose |
|----------|---------|
| [TUTORIAL.md](TUTORIAL.md) | Step-by-step project tutorial — start here if you are new to gui_do |
| [MANUAL.md](MANUAL.md) | Complete developer reference for all systems and APIs |

**TUTORIAL.md** teaches the framework by building a complete multi-feature application from
scratch, explaining both how and why at every step. A reader who finishes the tutorial will
understand the gui_do programming model well enough to build their own feature-complete
application.

**MANUAL.md** is the comprehensive reference organized by system, with API tables, usage
patterns, full code examples, integration recipes, and appendices including a full glossary,
lifecycle sequence diagram, system dependency map, and API quick index.

---

## Installation

Install from the repository root (local editable install, no binary compilation step):

```
python -m pip install -e . --no-deps
```

Requires `pygame` and `numpy`. `numpy` is used internally for pixel buffer operations via
`PixelArray`. Both are listed in `requirements-ci.txt`.

---

## Project Structure

```
gui_do/          — The library. Public API surface is gui_do/__init__.py (32 tiers).
demo_features/   — Runnable reference patterns. Each subfolder is one feature package.
tests/           — Contract and behavioral tests covering all major systems.
docs/            — Architecture boundary and runtime operating contracts.
TUTORIAL.md      — Step-by-step tutorial for new developers.
MANUAL.md        — Complete developer reference manual.
```

`demo_features/` follows the established folder-per-feature convention: each subfolder is a
Python package whose `__init__.py` is the sole public surface. The framework's bootstrap reads
feature specs — it never imports from internal submodules. Internal reorganization has zero
effect on how features are registered.

---

## See Also

- [TUTORIAL.md](TUTORIAL.md) — Learn gui_do by building a complete project from scratch
- [MANUAL.md](MANUAL.md) — Full system reference, API tables, and integration recipes
- [`demo_features/`](demo_features/) — Living reference patterns: Game of Life, Mandelbrot,
  bouncing shapes, control showcase, and systems demonstration
- [`docs/`](docs/) — Architecture boundary specifications and runtime operating contracts
- [`gui_do/__init__.py`](gui_do/__init__.py) — Authoritative public API source (32 tiers)
