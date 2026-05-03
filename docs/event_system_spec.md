# Event System Specification

## Purpose

This document defines the canonical event model used by the `gui_do` runtime.
The app pipeline normalizes incoming `pygame` events to `GuiEvent` before dispatch.

## Event Model

### `EventType`

Current semantic event kinds:

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

### `EventPhase`

Routing phase values:

- `CAPTURE`
- `TARGET`
- `BUBBLE`

### `GuiEvent`

Canonical event object fields include:

- `kind`, `type`
- `key`, `pos`, `rel`, `raw_pos`, `raw_rel`, `button`
- `wheel_x`, `wheel_y`, `mod`, `text`
- `control_id`, `group`, `window`, `task_panel`, `task_id`, `error`
- `source_event`
- `phase`, `propagation_stopped`, `default_prevented`

Common helpers:

- Semantic checks: `is_kind`, `is_key_down`, `is_key_up`, `is_mouse_down`, `is_mouse_up`, `is_mouse_motion`, `is_mouse_wheel`, `is_text_event`
- Button helpers: `is_left_down`, `is_left_up`, `is_right_down`, `is_right_up`, `is_middle_down`, `is_middle_up`
- Behavior helpers: `clone`, `with_phase`, `stop_propagation`, `prevent_default`, `wheel_delta`, `collides`

## Normalization

- `GuiEvent.from_pygame(event, pointer_pos)` maps `pygame` events into normalized `GuiEvent` instances.
- Unknown `pygame` event types map to `EventType.PASS`.
- Wheel events can use the fallback pointer position when event-local position data is missing.
- `EventManager.to_gui_event(...)` is the runtime conversion gateway:
  - passthrough when input is already a `GuiEvent`
  - conversion otherwise

## Runtime Dispatch Flow

`GuiApplication.process_event` follows this contract:

1. Normalize input to `GuiEvent`.
2. Handle quit events early.
3. Update shared input state.
4. Update logical pointer state and apply pointer lock/capture clamping.
5. Logicalize pointer events while preserving raw coordinates.
6. Route overlays/toasts/focus management.
7. Route keyboard events through keyboard manager and screen handler policy.
8. Route feature handlers, scene dispatch, then fallthrough handlers.
9. Respect `default_prevented` and `propagation_stopped` as hard stop signals.

## Behavioral Contracts

- Application-level routing is `GuiEvent` based.
- Scene dispatch always targets the active scene runtime.
- Pointer processing keeps logical and raw pointer coordinates distinct.
- `GuiEvent.clone()` must produce an independent event object for propagation flags.

## Verification

Relevant tests include:

- `tests/test_runtime_operating_contracts.py`
- `tests/test_gui_application_workspace_contracts.py`
- `tests/test_boundary_contracts.py`
