# Slider and Scrollbar Reimplementation Specification

## Scope
- Replace the current `Slider` and `Scrollbar` implementations with textbook GUI control patterns.
- Preserve the public API documented in README for:
  - `GuiManager.slider(...)`
  - `GuiManager.scrollbar(...)`
- Preserve behavior covered by current tests.

## Visual Style Extraction
- Slider track:
  - Thin centered track inside widget rect.
  - Contrasting dark fill.
  - Tick/notch marks drawn on the track.
- Slider handle:
  - Circular radio-style visual in idle/hover/armed/disabled states.
  - Handle size uses the current visual contract: base size reduced by 20% and clamped.
- Scrollbar:
  - Rectangular frame body with a rectangular moving bar/handle.
  - Optional increment/decrement arrow controls using `ArrowBox`.
- Scrollbar style variants:
  - `skip`: no arrow controls, full rect for bar area.
  - `split`: decrement at near edge, increment at far edge.
  - `near`: both arrows at near side.
  - `far`: both arrows at far side.

## Logical Purpose Extraction
- Slider:
  - Map pointer movement to a logical value in `[0, total_range]`.
  - Support float mode and integer-snap mode.
  - Support wheel movement while cursor is inside wheel hit corridor.
- Scrollbar:
  - Map pointer drag to logical `start_pos` in `[0, total_range - bar_size]`.
  - Move by `inc_size` via wheel and arrow controls.
  - Represent a visible logical window (`bar_size`) over a full logical range (`total_range`).

## Domain Knowledge Extraction

### Range and Graphical Conversion
- Axis-aligned conversions are required in both controls:
  - `pixel_to_total = pixel_point * total_range / graphical_range`
  - `total_to_pixel = total_point * graphical_range / total_range`
- Conversions are axis dependent:
  - Horizontal uses width.
  - Vertical uses height.
- Positions must be clamped to valid logical bounds after conversion.

### Slider Notches and Numeric Variants
- Float variant:
  - Notches at interval derived from `notch_interval_percent` over `total_range`.
- Integer variant:
  - Notches at every integer unit from `0` to `total_range`.
  - Value setter snaps to nearest integer.
- Wheel behavior:
  - Default wheel step is 10% of total range.
  - Integer sliders round default wheel step to nearest integer.
  - `wheel_step` overrides default when provided and valid.

### Scrollbar Arrow Controls
- Arrow controls are created on `on_added_to_gui()`.
- Arrow callbacks:
  - Decrement arrow -> `decrement()`.
  - Increment arrow -> `increment()`.
- Arrow geometry and direction are derived from orientation and style:
  - Horizontal: increment `0`, decrement `180`.
  - Vertical: increment `270`, decrement `90`.
- Registration must rollback created arrows on failure.

## Input and Interaction Contracts
- Drag lock behavior:
  - Acquire lock on left-button drag start.
  - Release lock on drag end/reset.
- Overlay cancel behavior:
  - Cancel drag if entering higher-priority window overlays.
- Release hint behavior:
  - On drag-release outside widget, use last in-bounds position when required.
- Disabled behavior:
  - Ignore input while disabled.
  - Reset drag state and lock state when disabled is applied.

## Compatibility Constraints
- Keep current internal attributes used by tests where relevant:
  - Slider: `_graphic_rect`, `_track_rect`, `_handle_size`, `_dragging`, `_wheel_active`, etc.
  - Scrollbar: `_increment_rect`, `_decrement_rect`, `_inc_degree`, `_dec_degree`, `_registered`, `_hit`, `_last_mouse_pos`, etc.
- Keep current method names used by tests.
