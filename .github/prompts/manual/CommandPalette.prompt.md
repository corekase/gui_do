---
name: CommandPalette
description: Generate or update the Command Palette section in MANUAL.md
agent: agent
---

# Command Palette Documentation Generator

You are an agent tasked with creating or updating the Command Palette section within MANUAL.md. This section should be comprehensive, verbose, and discovered entirely from the current source code.

## Task Overview

1. **Discovery Phase**: Read and understand the current command palette implementation from:
   - `gui_do/features/data_driven_runtime.py` — spec definitions and setup functions
   - `gui_do/overlays/command_palette_manager.py` — runtime behavior and manager
   - `demo_features/main/main_specs.py` and `demo_features/showcase/showcase_specs.py` — usage examples
   - Tests in `tests/test_command_palette_grouped_entries.py` and related files

2. **Writing Phase**: Generate or update the command palette section in MANUAL.md under the heading:
   - **Location**: Section 8.8 "Overlays, Dialogs, Notifications, and Command Surfaces"
   - **Target**: Either create a new subsection "8.8.X Command Palette and Two-Bind Input Model" or replace existing command palette content with verbose, comprehensive text

3. **Content Requirements**:
   - Explain what a command palette is and its role in the application
   - Describe the two-bind input model (toggle bind and action bind)
   - Explain how the toggle bind works (opens/closes the palette via key or pointer button)
   - Explain how the action bind works:
     - **First action while palette closed**: Shows the palette and fully consumes the event (stops, no further processing)
     - **Action while palette open**: Toggles window entry visibility at pointer position; non-window entries are ignored
   - Describe the spec structure: `PaletteInputBindSpec`, `SceneCommandPaletteSpec`, and how they compose
   - Explain the rationale/why this design (flexibility, clarity, user control, single-event open behavior)
   - Include concrete code examples derived from the current source code
   - Link to the Specifications appendix where appropriate
   - Discuss lifecycle, dismissal behavior (left-click dismisses, action-bind does not), and event routing
   - Cover scene scoping and how to omit the palette from a scene if not needed

4. **Code Examples**: All examples must:
   - Be discovered from or derived from the current source code
   - Show actual field names and values from the refactored spec (`toggle`, `action`)
   - Be valid and executable in the context of the current API
   - Include comments explaining intent

5. **Validation**:
   - Verify all field names match the current spec (no obsolete names like `toggle_key`)
   - Ensure the examples align with demo features' actual specs
   - Cross-link to other relevant sections (Actions, Input Mapping, Overlays, etc.)
   - Remove any outdated references to "palette_open" action kind

## Current API State (May 2026)

The command palette now uses a two-bind model with these key components:

```python
@dataclass(frozen=True)
class PaletteInputBindSpec:
    action_name: str
    key: int | None = None
    pointer_button: int | None = None

@dataclass(frozen=True)
class SceneCommandPaletteSpec:
    scene_name: str | None = None
    toggle: PaletteInputBindSpec  # Opens/closes the palette
    action: PaletteInputBindSpec  # Shows palette if closed (stops), or toggles window entries if open
```

The setup function is `setup_scene_command_palette_bindings(app, palette_manager, spec)`.

**Behavior Details**:
- **Toggle bind**: Fires when spec.toggle.key or spec.toggle.pointer_button is triggered. Toggles palette visibility (open ↔ closed).
- **Action bind**: Fires when spec.action.key or spec.action.pointer_button is triggered.
  - If palette is **closed**: Opens the palette and returns immediately (fully consumes event, does not process pointer position)
  - If palette is **already open**: Calls `try_activate_window_at(pos)` to toggle window entry under pointer; non-window entries are silently ignored
- Both binds can independently use key, button, or both
- Current demo: toggle=F5, action=middle-click (button 2)

## Output Constraints

- **Tone**: Verbose, comprehensive, non-redundant. Assume reader understands feature lifecycle.
- **Length**: 800–1200 words, structured as a cohesive subsection.
- **Format**: Markdown with proper headings, code blocks, lists, and emphasis.
- **Links**: Provide back-to-top link and cross-links to related sections.
- **Examples**: Minimum 3–4 code examples showing different configuration patterns.
- **Clarity**: Use the tri-lens model (control-plane, runtime-plane, lifecycle) where relevant.

## Execution Model

1. Inspect the current MANUAL.md to find section 8.8.
2. Locate or create the command palette subsection.
3. Replace the command palette content with newly discovered, verbose documentation.
4. Verify all examples are current and correct.
5. Update the Table of Contents if needed.
6. Return confirmation that the section is complete and non-empty.

---

## Discovery Checklist

Before writing, verify you have examined:

- [ ] `gui_do/features/data_driven_runtime.py`: PaletteInputBindSpec and SceneCommandPaletteSpec definitions (lines ~412–438)
- [ ] `setup_scene_command_palette_bindings()` function (lines ~1393–1455) — how the spec is realized into runtime binds
- [ ] `gui_do/overlays/command_palette_manager.py`: CommandPaletteManager class and behavior (show/hide, entry filtering, selection, dismissal on left-click, action-bind suppression on window entries)
- [ ] `demo_features/main/main_specs.py`: MAIN_RUNTIME_SCENE_SPEC usage at lines ~64–73 — toggle bind (F5 key) and action bind (middle-click/pointer button 2)
- [ ] `demo_features/showcase/showcase_specs.py`: showcase scene command palette spec — similar pattern
- [ ] Test file `tests/test_command_palette_grouped_entries.py`: regression tests covering left-click dismissal, action-bind suppression on window toggle, and non-window entry behavior
- [ ] `tests/test_demo_action_specs.py`: factory and kind assertions for palette_toggle action
- [ ] Any test files asserting the new PaletteInputBindSpec structure

## Writing Guidance

Use this structure for the command palette subsection:

1. **Overview**: What is a command palette? Why use one?
2. **Conceptual Model**: The two-bind design (toggle and action).
3. **Spec Structure**: PaletteInputBindSpec and SceneCommandPaletteSpec with field descriptions.
4. **Setup and Lifecycle**: How to declare and register binds, when binding occurs, teardown.
5. **Behavior Details**:
   - Toggle bind: Opens/closes palette via key or button
   - Action bind: Shows palette if closed (fully consumes event), or toggles window entries if open
   - Left-click dismissal: Not affected by action bind
   - Window entry suppression: Action bind only affects window entries, non-window entries are ignored
   - Palette filtering: User search/filtering behavior
6. **Single-Event Open Behavior**: Explain why action bind on first trigger (palette closed) opens and stops without also processing pointer position
7. **Scene Scoping**: How scene_name constrains bind registration.
8. **Flexibility**: Both binds can independently use key, button, or both; any combination is valid.
9. **Examples**:
   - Minimal palette with F5 toggle and middle-click action
   - Palette with only keyboard toggles (no mouse actions)
   - Palette with custom action names
   - Palette with both key and button on same bind
   - Omitting palette from a scene
10. **Cross-Links**: Actions/Input Mapping (8.3), Overlays (8.8 parent), Task Panel (8.9).

Write with verbose clarity. A reader should understand:
- Why the two-bind model is superior to a single "open" action
- How independent key/button flexibility serves different user preferences
- Why the action bind opens-then-stops on first trigger (prevents simultaneous open and toggle)
- Why filtering and selection are separate from invocation
- How scene scoping allows different scenes to have different palette bindings
- Why opting out of the palette is a valid choice

Use the control-plane/runtime-plane lens: SceneCommandPaletteSpec is control-plane (declarative intent), and CommandPaletteManager with input routing is runtime-plane (concrete behavior). Emphasize lifecycle: binding occurs in scene setup, updates happen every frame, and cleanup happens on scene teardown.
