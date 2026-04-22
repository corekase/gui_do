"""Focus visualization with dashed rectangles and smooth fade-out."""
from __future__ import annotations

from typing import Optional

import pygame


class FocusVisualizer:
    """Manages visual focus indicators (dashed rectangles) with timing and fade-out.

    When a control gains focus, a dashed rectangle is drawn around its draw_rect.
    After 1 second of display, the rectangle fades out smoothly over 0.5 seconds.
    When focus switches to a new control, the previous hint immediately fades out.
    """

    # Timing constants (in seconds)
    HOLD_TIME = 1.0  # Display for 1 second before starting fade
    FADE_TIME = 0.5  # Fade out over 0.5 seconds
    FADE_STEPS = 10  # Smooth fade in 10 steps
    FADE_STEP_TIME = FADE_TIME / FADE_STEPS  # Time per fade step

    # Dashed rectangle rendering
    DASH_WIDTH = 2  # Width of dashes in pixels
    GAP_WIDTH = 2  # Width of gaps in pixels
    LINE_WIDTH = 1  # Thickness of rectangle outline
    PADDING = 2  # Padding between control rect and focus rectangle

    def __init__(self, app) -> None:
        self.app = app
        self._current_hint_node = None  # Node currently showing the focus hint
        self._current_hint_elapsed = 0.0  # Total time since hint started

    def set_focus_hint(self, node, show_hint: bool = True) -> None:
        """Start displaying a focus hint for the given node.

        Args:
            node: The node to show the hint for.
            show_hint: If True, display the visual hint. If False, no hint is shown.
                Default is True (show hint).

        When focus switches to a new control, the previous hint is immediately cleared
        (no fade-out). If show_hint is False, the hint is not displayed at all.
        """
        if node is self._current_hint_node:
            return  # Already showing this hint

        # Start displaying the new hint (old hint immediately clears)
        # Only store node if we're showing the hint
        self._current_hint_node = node if show_hint else None
        self._current_hint_elapsed = 0.0

    def clear_focus_hint(self) -> None:
        """Immediately clear the current focus hint (typically when focus is lost)."""
        self._current_hint_node = None
        self._current_hint_elapsed = 0.0

    def update(self, dt_seconds: float) -> None:
        """Update fade-out state. Call from app's update loop."""
        if dt_seconds <= 0:
            return

        # Update the currently-hinting node's hold/fade state
        if self._current_hint_node is not None:
            self._current_hint_elapsed += dt_seconds
            total_time = self.HOLD_TIME + self.FADE_TIME
            if self._current_hint_elapsed >= total_time:
                # Hold and fade-out complete, clear this hint
                self._current_hint_node = None
                self._current_hint_elapsed = 0.0

    def draw_hints(self, surface: "pygame.Surface", theme) -> None:
        """Draw focus rectangles for nodes currently showing/fading hints."""
        # Draw the current hint
        if self._current_hint_node is not None:
            if self._current_hint_elapsed < self.HOLD_TIME:
                # Still in hold phase, draw at full opacity
                alpha = 1.0
            else:
                # In fade phase, compute alpha based on fade elapsed time
                fade_elapsed = self._current_hint_elapsed - self.HOLD_TIME
                fade_progress = fade_elapsed / self.FADE_TIME
                alpha = 1.0 - fade_progress
            self._draw_dashed_rect(
                surface,
                self._current_hint_node,
                alpha=alpha,
                theme=theme,
            )

    def _draw_dashed_rect(
        self,
        surface: "pygame.Surface",
        node,
        alpha: float,
        theme,
    ) -> None:
        """Draw a dashed rectangle around a node's draw_rect with the given alpha."""
        if not hasattr(node, "rect") or not hasattr(node, "visible"):
            return
        if not node.visible:
            return

        rect = node.rect
        if rect.width < 2 or rect.height < 2:
            return

        # Calculate focus rectangle (with padding)
        focus_rect = rect.inflate(2 * self.PADDING, 2 * self.PADDING)

        # Get focus color (use highlight color with alpha)
        focus_color = theme.highlight
        if alpha < 1.0:
            # Apply alpha to the color
            focus_color_with_alpha = (*focus_color, int(255 * alpha))
        else:
            focus_color_with_alpha = (*focus_color, 255)

        # Draw dashed rectangle
        self._draw_dashed_rectangle(surface, focus_rect, focus_color_with_alpha)

    def _draw_dashed_rectangle(
        self,
        surface: "pygame.Surface",
        rect: "pygame.Rect",
        color,
    ) -> None:
        """Draw a dashed rectangle outline."""
        x, y, w, h = rect.x, rect.y, rect.width, rect.height

        # Helper to draw dashes along a line
        def draw_dashes(x1, y1, x2, y2):
            if x1 == x2:  # Vertical line
                start, end = min(y1, y2), max(y1, y2)
                pos = start
                while pos < end:
                    next_pos = min(pos + self.DASH_WIDTH, end)
                    pygame.draw.line(surface, color[:3], (x1, pos), (x1, next_pos), self.LINE_WIDTH)
                    pos = next_pos + self.GAP_WIDTH
            else:  # Horizontal line
                start, end = min(x1, x2), max(x1, x2)
                pos = start
                while pos < end:
                    next_pos = min(pos + self.DASH_WIDTH, end)
                    pygame.draw.line(surface, color[:3], (pos, y1), (next_pos, y1), self.LINE_WIDTH)
                    pos = next_pos + self.GAP_WIDTH

        # Draw four dashed lines (top, right, bottom, left)
        draw_dashes(x, y, x + w, y)  # Top
        draw_dashes(x + w, y, x + w, y + h)  # Right
        draw_dashes(x + w, y + h, x, y + h)  # Bottom
        draw_dashes(x, y + h, x, y)  # Left
