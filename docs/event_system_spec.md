# Event System Specification

## Purpose

This specification defines the canonical event object model and routing flow for the `gui` package.
It replaces ad hoc direct usage of raw `pygame` events in app-level dispatch with normalized `GuiEvent` objects.

Terminology mirrors README/public API docs: canonical events at ingress, strict contracts in dispatch, and scene-aware routing behavior.

## Goals

- Provide one event shape throughout GUI internals.
- Preserve strict event-shape guarantees while still exposing raw pygame type where needed.
- Align key routing with GUI best practice: active/focused window first, then screen fallback.
- Keep pointer lock and logical pointer transforms explicit and testable.

## Event Objects

### `EventType` enum

Semantic categories for GUI-level event intent:

- `PASS`
- `QUIT`
- `KEY_DOWN`
- `KEY_UP`
- `MOUSE_BUTTON_DOWN`
- `MOUSE_BUTTON_UP`
- `MOUSE_MOTION`
- `MOUSE_WHEEL`
- `TEXT_INPUT`
- `TEXT_EDITING`
- `WIDGET`
- `GROUP`
- `TASK`

### `GuiEvent` dataclass

Canonical event object used by the app pipeline:

- `kind: EventType` semantic type.
- `type: int` raw `pygame` event type (raw-type field).
- `key: Optional[int]`
- `pos: Optional[tuple[int, int]]`
- `rel: Optional[tuple[int, int]]`
- `raw_pos: Optional[tuple[int, int]]`
- `raw_rel: Optional[tuple[int, int]]`
- `button: Optional[int]`
- `wheel_x: int`
- `wheel_y: int`
- `mod: int` (keyboard modifier bitmask; non-zero on key events with active modifiers)
- `text: Optional[str]`
- `widget_id: Optional[str]`
- `group: Optional[str]`
- `window: Optional[object]`
- `task_panel: bool`
- `task_id: Optional[Hashable]`
- `error: Optional[str]`
- `source_event: Optional[object]` (raw source event, when present)
- `phase: EventPhase` (`CAPTURE`, `TARGET`, `BUBBLE`)
- `propagation_stopped: bool`
- `default_prevented: bool`

Helper operations on `GuiEvent` simplify consumer code:

- `is_kind(...)`
- `is_key_down(key=None)` / `is_key_up(key=None)`
- `is_mouse_down(button=None)` / `is_mouse_up(button=None)`
- `is_mouse_motion()` / `is_mouse_wheel()`
- `wheel_delta`
- `collides(rect)`
- `with_phase(phase)`
- `stop_propagation()`
- `prevent_default()`

## Construction and Normalization

### `GuiEvent.from_pygame`

Input: a raw `pygame` event and optional pointer fallback position.

Rules:

1. Map `pygame` type to `EventType` (`PASS` when unknown).
2. Normalize optional scalar and tuple fields to strict types.
3. For wheel events with no event-local `pos`, use fallback pointer position.
4. Preserve the original source event in `source_event` for diagnostics.

### `EventManager`

`EventManager.to_gui_event(event, pointer_pos)` converts arbitrary input into `GuiEvent`:

- If already `GuiEvent`, return as-is.
- Otherwise normalize from raw `pygame` event.

## Dispatch and Routing Flow

App pipeline (`GuiApplication.process_event`) must execute in this order:

1. Convert input to `GuiEvent`.
2. Handle process quit (`EventType.QUIT`).
3. Update shared input state from normalized event.
4. Update logical pointer position from event position (including wheel fallback behavior).
5. Apply lock-area clamp and pointer-capture clamp.
6. Enforce point lock recentering policy.
7. Logicalize pointer events: keep raw coordinates in `raw_pos/raw_rel`, dispatch logical coordinates in `pos/rel`.
8. Route key/text events via keyboard manager:
   - active visible enabled window first,
   - then screen handler fallback.
   - any consumed key path marks default/prevented propagation semantics.
9. Route non-key events to screen handler first; if unhandled, dispatch to scene graph.
   - when `default_prevented` or `propagation_stopped` is set, fallback dispatch is suppressed.

Scene containment note:

- Event routing is always evaluated against the active scene graph.
- Scene-scoped screen lifecycle layers are applied only when their `scene_name` matches the active scene.

## Routed Phase Behavior

Scene routing executes in three phases for each event:

1. `CAPTURE` from root toward targets.
2. `TARGET` on normal hit-tested/stacked dispatch.
3. `BUBBLE` from target context back outward.

Container controls (`PanelControl`, `WindowControl`) propagate routed phases to children using the same canonical event object.

Propagation and default semantics:

- `stop_propagation()` halts remaining listeners/phases.
- `prevent_default()` marks fallback/default paths as consumed.
- Keyboard ownership paths (actions, focus traversal, active window) set these flags when consuming events.

## Best-Practice Integration Notes

- Widgets and controls should consume `GuiEvent` as the canonical event object.
- New widget code should prefer semantic checks (`event.kind`) where practical.
- Existing code paths may still rely on `event.type == pygame.*` while all app-level routing remains `GuiEvent`-based.
- Prefer semantic helper checks in application/demo code to avoid manual `getattr(event, ...)` probing.
- Synthetic internal events should use `GuiEvent` directly rather than fabricating `pygame.event.Event` objects.
- Event objects should remain immutable-by-convention after dispatch creation; transform steps should replace fields explicitly.

Focus and keyboard ownership note:

- Mouse click focus paths can suppress focus-hint visualization (`show_hint=False`) while keyboard traversal keeps hint visualization enabled.
- Keyboard routing precedence is active focused/visible/enabled target first, then screen fallback.
- Focus traversal must reconcile hover flags from live pointer position while cycling; if the pointer has moved off a control during the hint window, that control returns to idle (non-hover) state.
- Button and toggle-button activation from focused keyboard events (`Return`/`Space`) must show a focus hint and use the same timeout constant as focus traversal hinting.

## Completion Criteria

The package is considered converted when:

- app-level event intake normalizes to `GuiEvent` before dispatch,
- keyboard and scene routing consume normalized events,
- pointer logicalization preserves raw vs logical coordinates on `GuiEvent`,
- control and test contracts remain stable under the canonical `GuiEvent` pipeline.
