# gui_do Architecture

## Tier Structure

- Tier 0: Package root (`gui_do/__init__.py`, `gui_do/_version.py`)
- Tier 1: Core infrastructure (`events`, `data`, `scheduling`)
- Tier 2: Graphics and rendering (`graphics`)
- Tier 3: Layout and geometry (`layout`)
- Tier 4: Theme and styling (`theme`)
- Tier 5: Focus and input management (`focus`)
- Tier 6: Actions and commands (`actions`)
- Tier 7: Controls (`controls`)
- Tier 8: Overlays and transient UI (`overlays`)
- Tier 9: Application and runtime (`app`, `features`)
- Tier 10: Specialized subsystems (`persistence`, `accessibility`, `telemetry`, `text`, `introspection`, `state`, `audio`, `forms`)
- Tier 11: Demo features (`demo_features` package outside `gui_do`)

## Subsystem Purposes

- `events`: Event normalization, bus and input events.
- `data`: Reactive values, collections, bindings, and cache utilities.
- `scheduling`: Timers, task scheduler, tween/animation orchestration.
- `graphics`: Rendering support, draw contexts, assets, and visual primitives.
- `layout`: Layout engines and geometry helpers.
- `theme`: Fonts, colors, and scoped theming.
- `focus`: Focus state and navigation.
- `actions`: Action registration, middleware, and input mapping.
- `controls`: Reusable UI controls and composites.
- `overlays`: Dialogs, toasts, context menus, tooltips, and drag-drop overlays.
- `app`: Runtime coordinator and render loop integration.
- `features`: Feature lifecycle and declarative runtime composition.
- Specialized folders: Persistence, accessibility, telemetry, text, introspection, and state-machine utilities.

## Main Entry Points

- `gui_do/__init__.py`: Public API re-exports.
- `gui_do/app/gui_application.py`: Runtime host application coordinator.
- `gui_do/features/feature_lifecycle.py`: Feature registration and lifecycle.
- `gui_do/features/data_driven_runtime.py`: Declarative runtime assembly.

## Import Rules

- Inside `gui_do`, imports should be package-relative (`from .`, `from ..`, etc.).
- Imports from external dependencies remain absolute (`pygame`, standard library, etc.).
- `demo_features` may import from `gui_do` using absolute imports.

## Patterns

- Keep public exports stable through `gui_do/__init__.py`.
- Prefer one canonical module path per symbol; avoid facades and re-export wrappers.
- Prefer focused modules for cross-cutting concerns (for example, `events/value_change.py`, `events/input_processing.py`).
