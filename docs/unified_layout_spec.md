# Unified Layout System Specification for gui_do

## 1. Layout Handler Responsibilities

Each layout handler must:
- Implement the two-pass protocol: `measure(context)` and `arrange(context)`.
- Accept and apply standardized parameters: `padding`, `gap`, `inset`, and `margin`.
- Be composable: layouts can be nested, and containers can wrap other layouts.
- Register itself in a `LayoutRegistry` for extensibility.

## 2. Supported Layout Schemes

### FlexLayout
- Parameters: `direction`, `gap`, `align`, `justify`, `padding`, `inset`
- Use: Linear arrangements, responsive UIs

### GridLayout
- Parameters: `rows`, `columns`, `row_gap`, `column_gap`, `padding`, `inset`
- Use: Tabular, dashboard, form layouts

### ConstraintLayout
- Parameters: `constraints`, `padding`, `inset`
- Use: Complex, overlapping, or anchored layouts

### FlowLayout
- Parameters: `direction`, `gap_x`, `gap_y`, `align`, `padding`, `inset`
- Use: Wrapping, tag clouds, adaptive groups

### DockLayout
- Parameters: `splitters`, `ratios`, `padding`, `inset`
- Use: IDE-style, multi-pane UIs

### StackLayout
- Parameters: `z_order`, `padding`, `inset`
- Use: Overlays, modals, navigation stacks

### AbsoluteLayout
- Parameters: `positions`, `padding`, `inset`
- Use: Tooltips, popovers, custom overlays

## 3. Padding, Gap, Inset, Margin
- All layouts must support `padding` (inside container), `gap` (between children), `inset` (shorthand for all edges), and `margin` (outside container).
- Use design tokens for spacing (e.g., multiples of 4px).

## 4. Composability
- Layouts can be nested arbitrarily.
- Each layout context is responsible for its children only.
- Layout parameters are not inherited—must be explicit at each level.

## 5. Extensibility
- New layouts can be registered via `LayoutRegistry.register(name, handler)`.
- Layouts must declare their parameters and supported features.

## 6. Focus and Navigation
- Logical tab order follows layout order.
- Focus ring and navigation are handled by querying the layout manager for next/previous focusable.

## 7. Demo Feature Migration
- All demo features must use only these built-in layouts.
- Custom placement logic is to be removed except for unique cases.
- All layout parameters (window size, spacing, etc.) must be constants at the top of each demo feature.

---

This specification is to be implemented in gui_do/layout and adopted by all demo_features/.
