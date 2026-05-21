[![unittest](https://github.com/corekase/gui_do/actions/workflows/unittest.yml/badge.svg?branch=main)](https://github.com/corekase/gui_do/actions/workflows/unittest.yml)
# gui_do
### Latest Demonstration

---

<a href="https://www.youtube.com/watch?v=JLnkEEAQ43Q"><img src="https://img.youtube.com/vi/JLnkEEAQ43Q/0.jpg" alt="Demo Video"></img></a>

---

## Overview

gui_do is a data-driven GUI runtime for building scene-based desktop apps with predictable behavior and testable contracts. You declare features, scenes, windows, actions, and optional runtime facilities, then let `bootstrap_host_application` wire them into a coherent host application.

If you want deep system details, use MANUAL.md. If you want a guided build path, use TUTORIAL.md.

## Strengths

- Declarative host assembly through `HostApplicationBindingSpec`, scene bundles, and runtime scene specs.
- Strong lifecycle model with `Feature`, `LogicFeature`, `RoutedFeature`, and runtime-owned cleanup hooks.
- Reactive data primitives (`ObservableValue`, collection views, bindings, and state store utilities) for predictable UI updates.
- Rich runtime systems spanning events, actions, focus, scheduling, layout, overlays, controls, forms, persistence, graphics, telemetry, and accessibility.
- Explicit operating contracts for determinism, optional-facility behavior, bounded scheduling budgets, and restore diagnostics.

## Use Cases

- Multi-scene productivity or operations tools with keyboard-driven workflows.
- Rich data and control surfaces using windows, overlays, command palettes, and docked chrome.
- Test-heavy GUI systems where lifecycle safety, deterministic routing, and docs-backed contracts matter.
- Demo-style feature composition where each feature lives in its own package and exposes a clean package root.

## Quick Look

A minimal runnable entrypoint can be as small as this:

```python
#!/usr/bin/env python3
from gui_do import bootstrap_host_application

from demo_features.demo_config import DEMO_BOOTSTRAP_CONFIG


class GuiDoDemo:
    def __init__(self) -> None:
        bootstrap_host_application(self, DEMO_BOOTSTRAP_CONFIG)


if __name__ == "__main__":
    GuiDoDemo().app.run_entrypoint(target_fps=DEMO_BOOTSTRAP_CONFIG.target_fps)
```

The pattern is intentionally compact. Keep your entrypoint thin, keep composition declarative, and keep feature behavior inside feature classes.

## Documentation

| What you need | Where to go | Why |
|---|---|---|
| Quick orientation and setup | TUTORIAL.md | Step-by-step project walkthrough with runnable milestones |
| Runtime model and deep system details | MANUAL.md | Full conceptual and operational reference |
| Runtime operating guarantees | docs/runtime_operating_contracts.md | Determinism, safety rails, and release-gate behavior |
| Architecture boundaries | docs/architecture.md and docs/architecture_boundary_spec.md | Framework/demo separation and subsystem boundaries |

Recommended path:
1. Read TUTORIAL.md first.
2. Use MANUAL.md sections 5 to 10 for deeper concept and system understanding.
3. Use MANUAL.md appendix sections for spec-level details when building advanced flows.

## Installation

From the repository root:

```bash
python -m pip install -e . --no-deps
```

Because editable install is intentionally run with `--no-deps` (to avoid problematic binary dependency builds on Windows), install runtime dependencies manually:

```bash
python -m pip install pygame numpy
```

Then run the demo:

```bash
python gui_do_demo.py
```

## Project Structure

- `gui_do/`: public framework package and runtime systems.
- `demo_features/`: consumer-side demo features organized one package per feature/scene.
- `demo_features/data/`: demo assets (fonts, images, cursors, sounds).
- `docs/`: architecture and contract documentation.
- `tests/`: behavior and contract test suite.
- `gui_do_demo.py`: bootstrap entrypoint that consumes `gui_do` as a package client.

Feature-package convention in `demo_features/`:
- One folder package per feature (`main`, `life`, `systems`, `mandelbrot`, `moving_shapes`, `showcase`).
- Package-root `__init__.py` provides package metadata/public surface.
- Internal modules remain focused by concern (feature class, specs, helpers, presenters).
- Cross-feature imports should target package roots, not internal submodules.

## See Also

- TUTORIAL.md
- MANUAL.md
- docs/runtime_operating_contracts.md
- docs/library_demo_separation_contract.md
