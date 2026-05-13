---
name: Hierarchy
description: Restructure the library for optimal organization, naming, and portability. Ensure all files, folders, classes, methods, and variables follow best practices; split, combine, create, or remove modules as needed; convert all imports to relative paths within gui_do/ so the library is deployable anywhere.
agent: agent
---

# Hierarchy — Library Organization & Refactoring Pipeline

You are an agent. Execute the phases below **sequentially in a single session**. Complete each phase fully before reading the next. Do not parallelize planning, analysis, or implementation. This file is the only entry point.

## Global Execution Command

All required work must be strictly sequential and never concurrent. Do not evaluate, run, or batch multiple phases in parallel. This sequential rule applies both to top-level phase order and to all operations inside every phase.

Run non-interactively. Do not ask follow-up confirmation questions during planning or execution.

---

## Objective

Transform the gui_do library to:
1. **Optimal naming** — all files, folders, classes, methods, and variables follow domain best practices.
2. **Logical hierarchy** — folder structure reflects the functional and architectural organization of the codebase.
3. **Complete portability** — all imports within `gui_do/` are relative (`from . import ...`, `from ..module import ...`) so the library can be placed anywhere on the user's filesystem without modifying imports.
4. **Reduced duplication** — eliminate redundant modules, consolidate related code, and split large modules where separation improves clarity.
5. **Consistency** — apply uniform conventions across all subsystems (naming patterns, module organization, docstring style).

---

## Scope

### In Scope
- All files and folders within `gui_do/`.
- All files and folders within `demo_features/`.
- All relative imports within `gui_do/` and between `gui_do/` and `demo_features/`.
- Naming of files, folders, classes, methods, and instance variables.
- File layout: restructuring, combining, splitting, creating, and removing modules.
- Consistency checks and corrections (docstring headers, comment style, blank line conventions).

## New Runtime Facilities Constraints

While restructuring, preserve and properly place the new routed runtime facilities and their ownership model.

- Keep runtime-facility primitives in coherent feature-runtime modules; do not scatter across unrelated subsystems.
- Preserve spec-to-runtime mapping paths in `data_driven_runtime` for:
  - service bindings/consumers
  - store/observable/signal effects
  - operation bus and failure policy registration
  - dependency/workflow/recompute/QoS/health/replay/hot-swap spec families
- Preserve teardown guarantees: any reorganization must keep `shutdown_runtime` disposal paths intact for runtime scope and operation bus resources.
- Preserve routed update-hook semantics for runtime systems (`_routed_runtime_on_update`) and manager attachment/cleanup attribute paths.
- If renaming or moving facility symbols, update root exports and all prompt/document references in the same pass.

### Out of Scope
- Changes to `tests/` structure (tests follow the modules they test; reorganize after module organization is stable).
- Changes to external imports (dependencies on `pygame`, `numpy`, etc. are kept as-is).
- Public API surface (`gui_do/__init__.py` exports) — these are protected by the declared contracts and should not be renamed without explicit approval.
- `docs/` files (separate documentation pipeline).

---

## Naming Conventions & Standards

### Files & Modules
- **Public modules**: `snake_case.py` (e.g., `button_control.py`, `event_manager.py`).
- **Private/internal modules**: `_leading_underscore.py` (e.g., `_internal_helpers.py`, `_platform_specific.py`).
- **File names match primary export**: If a module exports a single class `WindowLayoutHandler`, name the file `window_layout_handler.py`.
- **Avoid generic names**: Use specific, domain-appropriate names like `focus_manager.py`, not `manager.py`.

### Folders
- **Functional subsystems**: Use lowercase, plural or singular based on domain convention.
  - `gui_do/controls/` — collection of UI controls.
  - `gui_do/layout/` — layout engines (can be plural or singular; prefer singular for abstract domains).
  - `gui_do/events/` — event infrastructure (plural; events are a collection).
  - `gui_do/theme/` — theming and styling (can be singular; more abstract).
  - `gui_do/graphics/` — rendering and graphics (plural; many graphics subsystems).
  - `gui_do/actions/` — action/command infrastructure.
- **Sub-folders within subsystems**: Use clear functional grouping.
  - `controls/base/` — abstract base classes and mixins for controls.
  - `controls/input/` — input controls (buttons, text input, sliders).
  - `controls/display/` — display controls (labels, images, progress bars).
  - `controls/chrome/` — application shells and window chrome (windows, menu bars, status bars).
  - `controls/composite/` — composite controls and containers (panels, scroll views, grids).
  - `controls/data/` — data-bound controls (data grids, lists, trees).
- **Avoid deep nesting**: Prefer 2–3 levels max. If a subdirectory has only 1–2 files, consider flattening.

### Classes & Types
- **Public classes**: `PascalCase` (e.g., `ButtonControl`, `EventManager`, `WindowLayoutHandler`).
- **Private classes**: `_PascalCase` prefix (e.g., `_InternalEventDispatcher`, `_PlatformSpecificRenderer`).
- **Abstract base classes**: Use `ABC` from `abc` module and follow naming: `_BaseClassName` or `_AbstractClassName` for truly internal ABCs; `PublicBaseClass` if part of the extension API.
- **Enums**: `PascalCase` (e.g., `EventType`, `LayoutMode`).
- **Data classes / named tuples**: `PascalCase` (e.g., `GridTrack`, `GridPlacement`, `FontRole`).

### Methods & Functions
- **Public methods**: `snake_case` (e.g., `apply_layout()`, `on_mouse_down()`).
- **Private methods**: `_snake_case` prefix (e.g., `_update_dirty_state()`, `_handle_platform_event()`).
- **Properties**: `snake_case` (e.g., `visible`, `enabled`, `focused`).
- **Lifecycle hooks**: Use consistent verb prefixes: `on_*` for event handlers (`on_added_to_gui`, `on_removed_from_gui`, `on_enabled_changed`), `_on_*` for private handlers.
- **Callbacks / signals**: `*_changed`, `*_pressed`, `*_clicked`, etc. (e.g., `on_value_changed`, `on_button_pressed`).

### Variables & Attributes
- **Instance attributes**: `snake_case` (e.g., `self.rect`, `self.control_id`, `self._enabled`).
- **Private instance attributes**: `_snake_case` prefix (e.g., `self._dirty`, `self._cached_layout`).
- **Module-level constants**: `UPPER_CASE` (e.g., `DEFAULT_PADDING`, `MAX_RECURSION_DEPTH`).
- **Avoid single-letter names** except in well-established contexts (e.g., `x`, `y` for coordinates; `i`, `j` for loop indices in short, obvious loops).
- **Boolean attributes**: Use `is_*` or `has_*` prefix sparingly; prefer simple names like `visible`, `enabled`, `dirty` where the type is clear.

---

## Architectural Hierarchy & Folder Organization

### Tier 0: Package Root (`gui_do/`)

- `__init__.py` — Public API re-exports. Protected; do not move symbols without updating the contract.
- `_version.py` — Version metadata.

### Tier 1: Core Infrastructure

**Purpose**: Foundation systems that all other subsystems depend on.

- **`gui_do/events/`** — Event bus, input routing, event types, pointer capture, input state.
  - `event_manager.py` — Event dispatch and routing.
  - `gui_event.py` — Core event types and phases.
  - `keyboard_manager.py` — Keyboard input handling.
  - `pointer_capture.py` — Pointer/mouse capture logic.
  - `input_state.py` — Current input state snapshots.
  - `event_bus.py` — Event subscription and dispatch.

- **`gui_do/data/`** — Observable values, bindings, reactive data structures.
  - `observable_value.py` — Single-value reactive wrapper.
  - `observable_collections.py` — List/dict/set reactive wrappers.
  - `binding.py` — Two-way binding between observables and control properties.
  - `binding_group.py` — Grouped binding lifecycle.
  - `command_history.py` — Undo/redo stack.
  - `object_pool.py` — Object reuse pool for allocation reduction.

- **`gui_do/scheduling/`** — Task scheduler, timers, tweens, animation.
  - `task_scheduler.py` — Primary task scheduler with budget enforcement.
  - `timers.py` — Timer management and scheduling.
  - `tween_manager.py` — Animation tweening.
  - `cooperative_scheduler.py` — Cooperative task yielding.

### Tier 2: Graphics & Rendering

**Purpose**: Low-level rendering, surfaces, scene graphs.

- **`gui_do/graphics/`** — Rendering primitives, surfaces, fonts, scene graphs.
  - `draw_context.py` — High-level drawing API.
  - `scene_graph_2d.py` — 2D scene graph representation.
  - `font_manager.py` — Font loading, caching, and role management.
  - `color_theme.py` — Color palette and theme application.
  - `built_in_factory.py` — Built-in graphics resources (fonts, cursors, etc.).

### Tier 3: Layout & Geometry

**Purpose**: Layout engines and geometric calculation.

- **`gui_do/layout/`** — Layout engines (flex, grid, dock, etc.).
  - `anchor_layout.py` — Anchor-based placement helper.
  - `flex_layout.py` — CSS Flexbox-like layout.
  - `grid_layout.py` — CSS Grid-like layout.
  - `dock_workspace.py` — Dock-panel workspace layout.
  - `window_layout_handler.py` — Window tiling and resizing.
  - `adaptive_constraint_layout.py` — Constraint-based layout.

### Tier 4: Theme & Styling

**Purpose**: Visual theming, color schemes, role-based styling.

- **`gui_do/theme/`** — Theme management and application.
  - `theme_manager.py` — Theme lifecycle and application.
  - `scoped_theme.py` — Per-subtree theme overrides.
  - `color_palette.py` — Color definitions and palettes.

### Tier 5: Focus & Input Management

**Purpose**: Focus routing, keyboard navigation, accessibility.

- **`gui_do/focus/`** — Focus state, routing, and visual indicators.
  - `focus_manager.py` — Primary focus lifecycle.
  - `focus_visualizer.py` — Focus indicators and visual feedback.
  - `window_focus_manager.py` — Window-level focus management.
  - `task_panel_focus_manager.py` — Task-panel focus routing.

### Tier 6: Actions & Commands

**Purpose**: Action definitions, dispatching, hotkey binding.

- **`gui_do/actions/`** — Action system and command execution.
  - `action_manager.py` — Action registry and dispatch.
  - `action_registry.py` — Global action registry.
  - `input_map.py` — Hotkey to action mapping.
  - `action_middleware.py` — Action validation and transformation.

### Tier 7: Controls (UI Components)

**Purpose**: User-facing UI elements; depends on all infrastructure.

- **`gui_do/controls/`** — UI controls and components.

  - **`base/`** — Abstract base classes and mixins.
    - `ui_node.py` — Base node for all controls.
    - `_control_base.py` — Abstract base for all controls.
    - `_text_control_base.py` — Text rendering mixin.
    - `_text_button_control_base.py` — Text button mixin.
    - `_hover_press_control_base.py` — Hover/press interaction mixin.
    - `_focusable_control_base.py` — Focus and keyboard interaction mixin.

  - **`input/`** — Input controls (buttons, text fields, sliders, checkboxes).
    - `button_control.py` — Push button.
    - `toggle_button_control.py` — Toggle/checkbox button.
    - `text_input_control.py` — Single-line text input.
    - `multiline_text_input_control.py` — Multi-line text input.
    - `slider_control.py` — Numeric slider.
    - `spin_box_control.py` — Numeric spinner.
    - `dropdown_control.py` — Dropdown menu.
    - `chip_input_control.py` — Tag/chip input.

  - **`display/`** — Display controls (labels, images, progress, etc.).
    - `label_control.py` — Static text display.
    - `image_control.py` — Image display.
    - `progress_bar_control.py` — Progress indicator.
    - `separator_control.py` — Visual separator.
    - `code_view_control.py` — Syntax-highlighted code display.

  - **`chrome/`** — Application chrome and containers.
    - `window_control.py` — Top-level window.
    - `panel_control.py` — Basic container panel.
    - `menu_bar_control.py` — Application menu bar.
    - `status_bar_control.py` — Status bar.
    - `task_panel_control.py` — Side panel for task controls.

  - **`composite/`** — Complex composite controls.
    - `scroll_view_control.py` — Scrolling container.
    - `tab_control.py` — Tabbed pane.
    - `split_view_control.py` — Splitter/resizable panes.
    - `tree_view_control.py` — Hierarchical tree.
    - `collection_view.py` — Generic list/collection view.

  - **`data/`** — Data-bound controls.
    - `data_grid_control.py` — Tabular data grid.
    - `list_control.py` — List bound to observable collection.
    - `table_control.py` — Table control.

### Tier 8: Overlays & Transient UI

**Purpose**: Transient UI elements (tooltips, dialogs, notifications, overlays).

- **`gui_do/overlays/`** — Overlay managers and transient UI.
  - `overlay_manager.py` — Base overlay orchestration.
  - `tooltip_manager.py` — Tooltip display and positioning.
  - `dialog_manager.py` — Dialog/modal window management.
  - `notification_center.py` — Toast/notification management.
  - `toast_manager.py` — Toast message lifecycle.
  - `drag_drop_manager.py` — Drag-and-drop support.
  - `shortcut_overlay_manager.py` — Keyboard shortcut help overlay.
  - `cursor_tooltip_overlay_manager.py` — Cursor-following tooltip.

### Tier 9: Application & Runtime

**Purpose**: Application lifecycle, scene management, feature system.

- **`gui_do/app/`** — Main application engine.
  - `gui_application.py` — Primary application class.
  - `ui_engine.py` — Rendering and update loop.
  - `scene.py` — Scene definition and lifecycle.
  - `renderer.py` — Frame rendering.
  - `error_handling.py` — Error reporting and handling.
  - `first_frame_profiler.py` — Initial frame profiling.

- **`gui_do/features/`** — Feature system and data-driven specs.
  - `feature_lifecycle.py` — Feature and manager lifecycle.
  - `data_driven_runtime.py` — Declarative spec system.
  - `control_spec.py` — Control definition from specs.
  - `action_spec.py` — Action spec definition.

### Tier 10: Specialized Subsystems

**Purpose**: Cross-cutting concerns and specialized features.

- **`gui_do/persistence/`** — State persistence and loading.
  - `workspace_persistence.py` — Workspace layout saving/restoring.
  - `state_store.py` — Application state persistence.

- **`gui_do/accessibility/`** — Accessibility and semantic trees.
  - `accessibility_tree.py` — Accessibility tree for screen readers.
  - `accessibility_roles.py` — Accessibility role definitions.

- **`gui_do/telemetry/`** — Usage and performance telemetry.
  - `telemetry.py` — Telemetry collection and reporting.
  - `telemetry_collector.py` — Data aggregation.

- **`gui_do/text/`** — Text processing and rendering.
  - `text_layout.py` — Text measurement and layout.
  - `text_renderer.py` — Text rendering primitives.
  - `text_input_manager.py` — IME and input method integration.

- **`gui_do/introspection/`** — Runtime introspection and inspection.
  - `contract_catalog.py` — Catalog of runtime contracts.
  - `runtime_inspection.py` — Introspection utilities.

- **`gui_do/state/`** — State management and store.
  - `app_state_store.py` — Global application state.
  - `invalidation.py` — Invalidation tracking.

### Tier 11: Demo Features (`demo_features/`)

**Purpose**: Example applications demonstrating the framework.

- **Feature structure**: Each feature is self-contained.
  - `{feature_name}_feature.py` — Feature entry point (implements `Feature` interface).
  - `{feature_name}_specs.py` — Runtime specs (if data-driven).
  - `{feature_name}_presenter.py` — Presentation logic (if needed).
  - `{feature_name}_logic.py` — Business logic (if needed).
  - `models/` — Data models (if needed).
  - `assets/` — Local assets (fonts, images, sounds).

- **Shared assets** (`demo_features/data/`):
  - `fonts/` — Shared fonts.
  - `images/` — Shared images.
  - `sounds/` — Shared audio.
  - `cursors/` — Shared cursors.

---

## Import & Portability Rules

### Relative Imports Within gui_do/

All imports within `gui_do/` **must** be relative:

```python
# Correct
from . import some_module
from .sibling_module import SomeClass
from ..parent.module import AnotherClass
from ...top_level import TopLevelClass

# Incorrect (never use absolute imports within gui_do/)
from gui_do.some_module import SomeClass  # ❌
from gui_do_do.sibling_module import Class  # ❌
import gui_do.parent.module  # ❌
```

### Demo Features Importing from gui_do

Demo features may import from gui_do using absolute imports (since they are outside the library):

```python
from gui_do import ButtonControl, Event, FeatureManager  # ✓ OK for demo_features/
```

### Why: Portability

Relative imports allow the `gui_do/` folder to be deployed anywhere on the user's filesystem:

```
/home/user/projects/my_app/
  ├── gui_do/           ← library; can be moved here
  │   ├── __init__.py
  │   ├── controls/
  │   └── ...
  └── app.py            ← imports: from gui_do import ...

/another/deep/path/
  ├── gui_do/           ← or here
  │   ├── __init__.py
  │   ├── controls/
  │   └── ...
  └── application.py    ← still works with relative imports inside gui_do/
```

---

## File Loading & Working Directory Rules

### Working Directory is Application-Owned

All file loading routines in gui_do **must begin with the working directory the application was launched from**. The library does not assume or enforce any specific filesystem location; instead, it respects the user's current working directory.

**Principle**: The application (or user script) determines the working directory. gui_do loads files relative to that context, not relative to the gui_do module's location.

### Implementation Pattern

When loading files (images, fonts, data, configs, etc.):

```python
# ✓ Correct: Uses current working directory
import os
file_path = os.path.join(os.getcwd(), "assets", "image.png")
image = load_image(file_path)

# ✓ Also correct: Relative path from cwd
image = load_image("./assets/image.png")

# ❌ Wrong: Uses gui_do's module location
import gui_do
module_dir = os.path.dirname(gui_do.__file__)
file_path = os.path.join(module_dir, "assets", "image.png")  # ✗

# ❌ Wrong: Hardcoded absolute path
file_path = "/home/user/project/assets/image.png"  # ✗ (not portable)
```

### Key Rules

1. **Respect `os.getcwd()`** — all file loading operations should resolve paths relative to the application's working directory.
2. **Allow user override** — if loading a file, accept either absolute paths or paths relative to cwd. If a path is absolute, use it directly; if relative, resolve it from `os.getcwd()`.
3. **Document path expectations** — in docstrings and error messages, clarify whether paths are expected to be absolute or relative to cwd.
4. **Use `pathlib.Path` or `os.path`** — for cross-platform path handling (Windows `\` vs Unix `/`).

### Example: Asset Loader

```python
from pathlib import Path
import os

def load_asset(filename: str) -> bytes:
    """Load an asset file relative to the application's working directory.

    Args:
        filename: Path to the asset (relative to cwd or absolute).

    Returns:
        The file contents as bytes.

    Raises:
        FileNotFoundError: If the file does not exist.
    """
    # Resolve relative to cwd
    path = Path(filename)
    if not path.is_absolute():
        path = Path(os.getcwd()) / path

    if not path.exists():
        raise FileNotFoundError(f"Asset not found: {path} (cwd: {os.getcwd()})")

    return path.read_bytes()
```

### Why: User Control & Deployability

- **User control**: Applications can organize assets however they want; gui_do does not dictate directory structure.
- **Deployability**: A user can place assets next to their app, in a separate `data/` folder, or anywhere else — as long as they set the cwd correctly before launching.
- **Testability**: Tests can run from any directory without modifying gui_do code; just set the cwd appropriately.

---

## Execution Phases

### Phase 1: Analysis & Planning
**Goal**: Audit the codebase and produce a detailed refactoring plan.

**Steps**:

1. **Walk the entire `gui_do/` and `demo_features/` tree** and list:
   - Every module (file) with its current path, size (lines of code), primary exports.
   - Every folder with its purpose and contents.
   - Every absolute import within `gui_do/` (must be converted to relative).
   - Naming violations (classes, methods, variables not following conventions).
   - Duplicate or redundant modules (e.g., multiple similar event types, multiple layout wrappers).
   - Modules that should be split (> 500 lines, multiple unrelated classes).
   - Modules that should be combined (< 50 lines, single trivial class).
   - Orphaned files or folders (not imported, unused).

2. **Classify each finding**:
   - `rename_only` — just rename the file or symbol.
   - `merge` — combine with another module.
   - `split` — break into multiple files.
   - `reorganize` — move to a different folder.
   - `delete` — remove (after confirming it is unused).
   - `create` — new module needed to reduce duplication or improve organization.

3. **Identify inter-module dependencies** to determine safe reordering and merging. Specifically:
   - Circular imports (must be broken).
   - Very deep import chains (may indicate missing intermediate abstraction).
   - Imports that cross "tiers" inappropriately (e.g., a Tier 6 module importing from Tier 9 should be questioned).

4. **Check test coverage**:
   - For every planned deletion, confirm there are no tests that depend on it.
   - For every planned rename, identify all test imports that must be updated.

5. **Document the plan** as a structured report with sections:
   - **Summary** — count of renames, merges, splits, moves, deletes, creates.
   - **Renames** — list of `old_name.py` → `new_name.py` and `OldClass` → `NewClass`.
   - **Merges** — list of `file_a.py + file_b.py` → `merged_file.py`.
   - **Splits** — list of `large_file.py` → `file_part_1.py, file_part_2.py`.
   - **Moves** — list of `old/path/file.py` → `new/path/file.py`.
   - **Deletes** — list of `file.py` with reason.
   - **Creates** — list of new files with purpose.
   - **Import fixes** — list of absolute imports to convert to relative.

6. **Await confirmation** before proceeding to Phase 2. Present the plan and ask for approval or specific adjustments.

---

### Phase 2: Implement Naming Fixes & Simple Renames
**Goal**: Fix names that require no refactoring (file renames, class renames, method renames with no structural changes).

**Steps**:

1. **Rename files** in the order they appear in the plan (renames that don't affect imports first, then those with local impact).
   - Use your file management tools to rename.
   - Update all relative import statements that reference the renamed file.

2. **Rename classes** by using find-and-replace within affected files.
   - Update all usages, including in test files.
   - Verify no references are missed.

3. **Rename methods and attributes** for all naming violations.
   - Use find-and-replace scoped to the class definition and its usages.

4. **Update docstrings** where necessary to reflect new names.

5. **Run the test suite** after each batch of renames to confirm nothing broke:
   ```
   python -m unittest discover -s tests -p "test_*.py"
   ```

---

### Phase 3: Convert Absolute Imports to Relative
**Goal**: Ensure all imports within `gui_do/` are relative, enabling portability.

**Steps**:

1. **Scan all Python files in `gui_do/`** for absolute imports (those starting with `gui_do` or `gui_do_do`).

2. **For each absolute import**, convert it:
   - `from gui_do.module import X` → `from .module import X`
   - `from gui_do.parent.child import Y` → `from ..parent.child import Y`
   - `from gui_do import Z` → `from . import Z` (if re-exporting) or appropriate relative path.

3. **Handle edge cases**:
   - Relative imports in test files that import from `gui_do` stay absolute (tests are outside the library).
   - Demo files that import from `gui_do` stay absolute.
   - TYPE_CHECKING imports are updated the same way as regular imports.

4. **Use sed/find-replace or a script** to make bulk conversions safely.

5. **Run the full test suite** after all import conversions:
   ```
   python -m unittest discover -s tests -p "test_*.py"
   ```

6. **Verify portability** by:
   - Moving the `gui_do/` folder to a temporary location.
   - Running `demo_features/` against the moved library.
   - Confirming all imports still work.

---

### Phase 4: Implement Merges
**Goal**: Combine small, related modules into larger, more cohesive modules.

**Steps**:

1. **For each merge operation** (in the plan order):
   - Open both files.
   - Identify any name conflicts (same class/function name in both files).
   - Resolve conflicts by renaming one or both entities if needed.
   - Copy the public exports from the "source" file into the "target" file.
   - Update all imports across the codebase that referenced the source module.
   - Delete the source file.

2. **Update `__init__.py` re-exports** if either file was re-exported from a package.

3. **Run the test suite** after each merge:
   ```
   python -m unittest discover -s tests -p "test_*.py"
   ```

---

### Phase 5: Implement Splits
**Goal**: Break large modules into smaller, more focused modules.

**Steps**:

1. **For each split operation** (in the plan order):
   - Open the large file.
   - Identify which classes/functions will move to the new module(s).
   - Create the new file(s) with those entities.
   - Update imports in the original file to re-export newly split entities (if they were public).
   - Update all usages across the codebase to import from the correct new module.
   - If the original file is now empty or trivial, delete it; otherwise, keep it as a facade for backward compatibility.

2. **Maintain the `__all__` export** to preserve public API.

3. **Run the test suite** after each split:
   ```
   python -m unittest discover -s tests -p "test_*.py"
   ```

---

### Phase 6: Implement Moves & Reorganization
**Goal**: Move files to the correct folders to match the logical hierarchy.

**Steps**:

1. **For each move operation** (in the plan order):
   - Identify the file to move and its target folder.
   - Ensure the target folder exists; create it if needed.
   - Move the file.
   - Update all imports that referenced the old path.
   - If moving between tiers, check that no imports violate tier rules (e.g., Tier 2 depending on Tier 9).

2. **Update `__init__.py` re-exports** if the moved file was re-exported.

3. **Run the test suite** after each move:
   ```
   python -m unittest discover -s tests -p "test_*.py"
   ```

---

### Phase 7: Implement Deletions
**Goal**: Remove dead, orphaned, or duplicate code.

**Steps**:

1. **For each deletion** (in the plan order):
   - Confirm once more that the file/class is not imported or used anywhere.
   - Delete the file or symbol.
   - Run the test suite to confirm nothing broke:
     ```
     python -m unittest discover -s tests -p "test_*.py"
     ```

---

### Phase 8: Implement New Modules
**Goal**: Create new modules to improve organization and reduce duplication.

**Steps**:

1. **For each new module** (in the plan order):
   - Create the new file in its target folder.
   - Write or move code into it based on the plan.
   - Update imports across the codebase to use the new module.
   - Ensure the public API is correctly exported via `__init__.py` if needed.

2. **Run the test suite** after each creation:
   ```
   python -m unittest discover -s tests -p "test_*.py"
   ```

---

### Phase 9: Final Consistency & Cleanup
**Goal**: Ensure naming, documentation, and structure are fully consistent.

**Steps**:

1. **Re-walk all files** and verify:
   - All file names are in `snake_case`.
   - All class names are in `PascalCase` (private classes have `_` prefix).
   - All method/function names are in `snake_case` (private ones have `_` prefix).
   - All module-level constants are in `UPPER_CASE`.
   - All imports are relative within `gui_do/`.
   - Docstrings follow a consistent style (Google or Numpy style throughout).
   - No orphaned files or empty folders exist.

2. **Verify folder hierarchy** matches the architectural tiers document (Phase section above).

3. **Create/update `gui_do/ARCHITECTURE.md`** (if not present) documenting:
   - The tier structure.
   - Each subsystem's purpose.
   - Main entry points and patterns.
   - Import rules.

4. **Run the full test suite** one final time:
   ```
   python -m unittest discover -s tests -p "test_*.py"
   ```

5. **Verify portability**: Move `gui_do/` to a temporary location and run demo again.

---

## Rollback & Verification

If at any point the test suite fails:

1. Stop immediately.
2. Review the most recent changes.
3. Either fix the issue or roll back to the previous stable state.
4. Document the problem and the fix for the session record.

---

## Session Record & Artifacts

Throughout execution, maintain a **session log** that records:

- **Phase completion**: When each phase is complete, note the date/time and summary of work done.
- **Renames**: File and class renames executed, with before/after paths.
- **Merges**: Source and target modules, any conflicts resolved.
- **Splits**: Original module and new modules created.
- **Moves**: Old and new paths.
- **Deletes**: Files deleted and reason.
- **Import conversions**: Files updated from absolute to relative imports.
- **Test suite results**: Pass/fail status after each major batch.
- **Final state**: Summary of the refactored library, highlighting improvements.

Provide the session log as a summary output at the end of Phase 9.

---

## Success Criteria

Upon completion, the library must satisfy:

1. ✅ **Naming compliance**: 100% of files, classes, methods, and constants follow the conventions above.
2. ✅ **Relative imports**: Every import within `gui_do/` is relative (no `from gui_do import ...` inside `gui_do/`).
3. ✅ **Portability**: The `gui_do/` folder can be moved to any location and all demo features work without import changes.
4. ✅ **Logical hierarchy**: Folders reflect the tier structure and functional organization.
5. ✅ **No duplication**: Related modules are consolidated; no orphaned or dead files remain.
6. ✅ **Test coverage**: Full test suite passes with zero failures.
7. ✅ **Documentation**: Architecture is documented; subsystems are clear and consistent.

---

## Notes

- This is a **complex, multi-step refactoring**. Take time in Phase 1 to plan thoroughly; a good plan makes execution much faster and safer.
- **Test after each major batch** — do not defer testing to the end.
- **Preserve public API** — exported symbols in `gui_do/__init__.py` must not be renamed or removed without explicit approval.
- **Be thorough with imports** — missing a single import update can create silent failures or false positives in the test suite.
- **Maintain clarity** — if you are uncertain whether a file should be deleted, kept, or moved, err on the side of keeping it unless the plan explicitly designates it for deletion.
