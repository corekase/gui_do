---
name: Manual.p5
description: Expand Main Systems chapters 5–8 (Controls, Layout, Focus/Accessibility, Overlays)
---

# Manual Step 5 — Systems 5–8

## Scope

Replace four system chapter placeholders:
- `### Controls and Control Composition` (8.5)
- `### Layout Systems` (8.6)
- `### Focus and Accessibility` (8.7)
- `### Overlays, Dialogs, Notifications, and Command Surfaces` (8.8)

Replace from `### Controls and Control Composition` through to (but not including)
`### Scene, Window, and Task-Panel Presentation Models`.

## Inventory (Required Before Writing)

1. Read the current text of these four sections in `MANUAL.md`.
2. Read `gui_do/__init__.py` **Tier 12** (primary controls), **Tier 13** (extended controls),
   **Tier 8** (layout engines), **Tier 28** (adaptive constraint layout), **Tier 29**
   (virtualization), **Tier 4** (Focus* and accessibility in Tier 21), and **Tier 21**
   (accessibility) sections. Extract all exported names from each tier block.
3. Skim `gui_do/controls/chrome/window_presenter.py` top docstring (presenter pattern).

Use only names found in the actual `gui_do/__init__.py` tier blocks.
If Tier 13 now includes new controls not previously documented, include them.

## Standard Chapter Template

Every chapter: What/why · Mental model · Primary APIs · Typical usage flow · Minimal example ·
Advanced pattern · Common mistakes · Cross-links · `[Back to Table of Contents](#table-of-contents)`

---

## 8.5 — Controls and Control Composition

**What/why:** Controls are reusable UI primitives. Features compose them inside owned root
panels. The control tree drives layout, hit-testing, focus, and rendering without features
needing to coordinate these concerns manually.

**Mental model:** Controls are children of panels which are children of scene roots. A feature
owns one root `PanelControl`; everything it creates lives inside that root. Controls never
reach across feature boundaries — cross-feature communication uses observables and messages.

**Primary Controls (Tier 12 from `gui_do/__init__.py`):**
Use all names discovered from the TIER 12 section in the inventory step. As of the last
audit this includes basic panel, label, button, toggle, slider, scrollbar, canvas, frame,
image, and tab controls. Always use the current names from `__init__.py`.

**Extended Controls (Tier 13 from `gui_do/__init__.py`):**
Use all names discovered from the TIER 13 section in the inventory step. This tier includes
text input, dropdown, list view, data grid, tree, splitter, color picker, scroll view,
progress bar, error boundary, chrome controls (window, task panel, menu bar, toolbar, status
bar, notification panel, property inspector), and specialty input controls (date picker, time
picker, breadcrumb, split button, chip input). Always use the current names from `__init__.py`
— new controls added since the last manual generation must be included.

**`WindowPresenter`:** A base class for window-level UI construction. A feature subclasses it to
own the layout and control creation for a floating window, keeping the Feature class focused on
lifecycle and routing. Instantiated lazily in `build`.

**`ErrorBoundary`:** Wraps a subtree of controls; if rendering or event handling raises, the
boundary catches the error and renders a fallback instead of crashing the frame.

**`CanvasControl`:** A raw drawing surface inside the control tree. Use with `CanvasViewport`
for scrollable/zoomed custom drawing. `CanvasEventPacket` carries pointer events with
canvas-local coordinates.

**`ControlDefinition` and `build_specs_from_column_section`:** Higher-level helpers for
declaratively specifying groups of controls (e.g. property panels with labeled columns).

**Typical usage:**
1. In `build`, create a root `PanelControl` and add it to the scene via `host.app.add(...)`.
2. Add child controls to the root using `root.add(...)`.
3. Bind callbacks and observable subscriptions in `bind_runtime`.

**Minimal example:**
```python
def build(self, host):
    self.root = host.app.add(
        PanelControl("my_root", Rect(0, 0, 400, 300)),
        scene_name="main",
    )
    self.label = self.root.add(LabelControl("status", Rect(8, 8, 200, 24), "Ready"))
    self.root.add(
        ButtonControl("go", Rect(8, 40, 100, 28), "Go", on_click=self._on_go)
    )
```

**Advanced pattern:** Presenter pattern — subclass `WindowPresenter`, build the window layout
inside its `build` method, instantiate it from the Feature's `build`. Keeps window construction
separate from lifecycle management. Combine with `TabbedPresenterSpec` and `TabBuilderSpec`
for tabbed window content.

**Mistakes:** Direct cross-feature control references (creates hidden coupling; use observables);
using controls as the source of truth for state (controls should mirror observable state, not own
it); building controls outside `build` phase (e.g., in `on_update`).

**Cross-links:** 8.2 (Feature lifecycle), 8.6 (Layout), 8.7 (Focus), 8.9 (Window presentation)

---

## 8.6 — Layout Systems

**What/why:** Layout engines manage spatial constraints, responsive behavior, and docking
composition so features don't hardcode pixel positions that break on resize.

**Mental model:** Choose the simplest layout family for each region. Prefer declarative
constraints over manual position arithmetic. Layout runs as a pass triggered by the app's
layout manager before draw.

**APIs (Tier 8, 28, 29 from `gui_do/__init__.py`):**
Use all names discovered from the TIER 8 (layout engines), TIER 28 (adaptive constraint layout
v2), and TIER 29 (virtualization core) sections in the inventory step. Check `__init__.py` for
any new layout types added since the last generation.

**Family guide:**
- `FlexLayout`: row/column arrangements with grow/shrink ratios. Best for toolbars and panels.
- `GridLayout`: fixed track definitions with spanning. Best for forms and data grids.
- `FlowLayout`: wrapping item flow. Best for tag/chip displays.
- `ConstraintLayout` / `ConstraintLayoutEngine`: anchor-based relationships between controls.
  Best for dialog layouts with relative positioning.
- `AdaptivePolicy` + `resolve_adaptive_policy`: breakpoint-aware constraint switching.
  Best for responsive panels that rearrange at viewport size thresholds.
- `DockWorkspace`: complex multi-pane workbenches with splits and tabbed panes.
- `SnapGrid` + `SnapComposer`: snap-to-grid and alignment guides for drag-placed controls.
- `ResponsiveLayout` + `Breakpoint`: policy selection by width breakpoint.

**Typical usage (FlexLayout):**
```python
layout = FlexLayout(direction=FlexDirection.ROW, gap=8)
layout.add(FlexItem(control=sidebar, grow=0, basis=200))
layout.add(FlexItem(control=main_area, grow=1))
```

**Minimal example:** `FlexLayout` with two panels.

**Advanced pattern:** `ConstraintLayoutEngine` with `AdaptivePolicy` for a panel that
rearranges controls at narrow/wide breakpoints. `WindowLayoutHandler` for desktop-style
window tiling.

**Mistakes:** Mixing conflicting layout systems in one container without clear ownership;
hardcoding pixel dimensions where responsive breakpoints are needed; calling layout APIs
before controls are added to the tree.

**Cross-links:** 8.5 (Controls), 8.7 (Focus), 8.9 (Window/task-panel)

---

## 8.7 — Focus and Accessibility

**What/why:** Focus management keeps keyboard interaction coherent — only one control
receives key events at a time. Accessibility semantics expose a machine-readable role tree
for assistive technology and testing.

**Mental model:** `FocusManager` owns the focused control. `FocusScopeManager` groups
controls so focus can be locked to a subtree (e.g., inside an open dialog). Accessibility
is a parallel tree of `AccessibilityNode` objects that mirrors the semantic structure of the
control tree.

**APIs (Tier 4 — Focus, from `gui_do/__init__.py`):**
Use the Focus* names from the TIER 4 section discovered in the inventory step
(`FocusManager`, `FocusScope`, `FocusScopeManager`, `WindowFocusManager`, `FocusRing`).

**APIs (Tier 21 — Accessibility, from `gui_do/__init__.py`):**
Use all names from the TIER 21 section discovered in the inventory step.
Check `__init__.py` for any new accessibility types added since the last generation.

**Specs (from Tier 1 discovery):** `AccessibilitySequenceSpec`, `StaticAccessibilitySpec`,
`TaskPanelFocusToggleSpec` — verify these names still exist in the Tier 1 block.

**Focus lifecycle:** Controls join the focus ring in `build`; hidden/disabled controls must
be excluded from the ring. When a window becomes hidden, its controls must leave the focus ring
or focus cycling will stall on invisible targets. `TaskPanelFocusToggleSpec` handles this
automatically for task-panel-managed windows.

**`AccessibilityNode`:** Carries `role`, `name`, `description`, and optional live-region
politeness. `AccessibilityBus` delivers `AccessibilityAnnouncement` events for
screen-reader-like consumers.

**`FocusRing`:** Ordered list of focusable controls in a scene. Navigation wraps around.
`WindowFocusManager` coordinates per-window focus so Alt+Tab-style switching works correctly.

**Typical usage:**
1. Declare `StaticAccessibilitySpec` entries in `HostApplicationConfig`.
2. For custom controls, add `AccessibilityNode` to `AccessibilityTree` in `build`.
3. Use `TaskPanelFocusToggleSpec` in `RoutedRuntimeSpec` for windows that need
   focus-exclusion when hidden.

**Minimal example:**
```python
tree = AccessibilityTree()
node = AccessibilityNode(role=AccessibilityRole.BUTTON, name="Submit")
tree.root.add_child(node)
```

**Advanced pattern:** `AccessibilitySequenceSpec` for scene-level sequential focus order;
`FocusScope` to lock focus inside a modal dialog's control subtree.

**Mistakes:** Duplicate focus targets when a window is both hidden and still in the ring;
missing semantic roles on custom `CanvasControl` widgets; building accessibility nodes before
the tree is initialized.

Include one anti-pattern about registering focus/accessibility-related subscriptions without
runtime-scope ownership and explain the proper teardown path.

**Cross-links:** 8.3 (Events), 8.5 (Controls), 8.8 (Overlays — modal focus capture), 8.9 (Window)

---

## 8.8 — Overlays, Dialogs, Notifications, and Command Surfaces

**What/why:** Transient and modal surfaces need their own routing layer so they don't
destabilize main control event flow. gui_do provides a family of managers, each handling
a distinct surface kind with the correct dismissal contract.

**Mental model:** Overlays sit on top of the main control tree. The overlay manager processes
events first; if an overlay consumes an event, the main tree never sees it. Each overlay type
has its own manager so concerns stay separated.

Include a short note on pairing overlay/event subscriptions with routed runtime disposal
when overlay behavior is wired through declarative runtime specs.

**APIs (Tier 9 from `gui_do/__init__.py`):**
Use all names from the TIER 9 section discovered in the inventory step. This tier covers
overlay managers for dialogs, toasts, context menus, command palette, tooltip, menu bar,
file dialog, notification center, resize, cursor, drag-and-drop, clipboard, transfer, and
shortcut help overlay. Check `__init__.py` for any new overlay types.

**Spec integration (from Tier 1 discovery):** `ShortcutOverlaySpec` in `RoutedRuntimeSpec`,
`NotificationSpec` \u2014 verify these still appear in the Tier 1 block.

**Dismissal contracts:**
- Toasts: clicks within toast bounds are consumed (no click-through). Use `on_click` for
  intentional interactions.
- Dialogs: modal by default; can be configured for dismiss-on-escape or dismiss-on-outside-click.
- Context menus: dismiss on outside click or Escape.
- Command palette: dismiss on Escape or selection.
- Tooltip: dismiss on pointer leave; shown after hover dwell.

**`PopupPlacement` and `compute_popup_rect`:** Compute an overlay rect that avoids clipping
at screen edges, given an anchor rect, preferred side, and alignment.

**`ShortcutHelpOverlay`:** A full-screen or partial overlay that renders the action registry's
shortcut list. Configure via `ShortcutOverlaySpec` — specify `toggle_action_name`, `toggle_key`,
`manual_shortcut_lines`, `manual_section_title`, `exclude_section_titles`, etc.

**`DragDropManager` and `DragPayload`:** Manages drag-and-drop operations. Source initiates
drag with a `DragPayload`; manager routes drag-enter/leave/drop events to registered targets.

**`ClipboardManager` and `TransferData`/`TransferManager`:** Cross-control clipboard
operations and data transfer.

**Typical usage (toast):**
```python
host.toasts.show("File saved", severity=ToastSeverity.SUCCESS)
```

**Typical usage (dialog):**
```python
handle = host.dialogs.show(my_dialog_control, modal=True)
handle.on_dismiss = lambda: print("closed")
```

**Minimal example:** Toast notification on button click.

**Advanced pattern:** `ShortcutHelpOverlay` with `ShortcutOverlaySpec` including manual sections,
section filtering, and action-registry integration. `CommandPaletteManager` with dynamic
`CommandEntry` population from the action registry.

**Mistakes:** Allowing overlays without a dismissal contract (users cannot close them);
expecting toast clicks to pass to underlying controls; neglecting to check `OverlayHandle`
validity before updating a dismissed overlay.

**Cross-links:** 8.3 (Event routing), 8.7 (Modal focus capture), 8.9 (Scene/window presentation)

---

## Replace Target

Replace from the line containing:
```
### Controls and Control Composition
```
through to (but not including) the line containing:
```
### Scene, Window, and Task-Panel Presentation Models
```

Include the `### Controls and Control Composition` heading in your output.
