# Event System Specification

## Purpose

This specification defines the canonical event object model and routing flow for the `gui` package.
It replaces ad hoc direct usage of raw `pygame` events in app-level dispatch with normalized `GuiEvent` objects.

## Goals

- Provide one event shape throughout GUI internals.
- Preserve compatibility with existing widget logic that checks `event.type` against `pygame` constants.
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
- `type: int` raw `pygame` event type (compatibility field).
- `key: Optional[int]`
- `pos: Optional[tuple[int, int]]`
- `rel: Optional[tuple[int, int]]`
- `raw_pos: Optional[tuple[int, int]]`
- `raw_rel: Optional[tuple[int, int]]`
- `button: Optional[int]`
- `wheel_x: int`
- `wheel_y: int`
- `text: Optional[str]`
- `widget_id: Optional[str]`
- `group: Optional[str]`
- `window: Optional[object]`
- `task_panel: bool`
- `task_id: Optional[Hashable]`
- `error: Optional[str]`
- `source_event: Optional[object]` (raw source event, when present)

Helper operations on `GuiEvent` simplify consumer code:

- `is_kind(...)`
- `is_key_down(key=None)` / `is_key_up(key=None)`
- `is_mouse_down(button=None)` / `is_mouse_up(button=None)`
- `is_mouse_motion()` / `is_mouse_wheel()`
- `wheel_delta`
- `collides(rect)`

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
9. Route non-key events to screen handler first; if unhandled, dispatch to scene graph.

## Best-Practice Integration Notes

- Widgets and controls should consume `GuiEvent` as the canonical event object.
- New widget code should prefer semantic checks (`event.kind`) where practical.
- Existing code paths that rely on `event.type == pygame.*` remain supported for incremental migration.
- Prefer semantic helper checks in application/demo code to avoid manual `getattr(event, ...)` probing.
- Synthetic internal events should use `GuiEvent` directly rather than fabricating `pygame.event.Event` objects.
- Event objects should remain immutable-by-convention after dispatch creation; transform steps should replace fields explicitly.

## Completion Criteria

The package is considered converted when:

- app-level event intake normalizes to `GuiEvent` before dispatch,
- keyboard and scene routing consume normalized events,
- pointer logicalization preserves raw vs logical coordinates on `GuiEvent`,
- compatibility with existing controls and tests is maintained.
