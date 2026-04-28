"""TooltipManager — hover-triggered contextual hint service.

Attach tooltips to any :class:`~gui_do.UiNode` by registering it with a
:class:`TooltipManager`.  The manager tracks pointer hover state and fires
after a configurable delay using :class:`~gui_do.Timers`-compatible elapsed
time accumulation.

Usage::

    tooltip_mgr = TooltipManager(default_delay_ms=500)

    # Register a control:
    handle = tooltip_mgr.register(my_button, "Click to submit")

    # Per frame — supply the hovered node id (None when pointer is over background):
    tooltip_mgr.update(dt_seconds, hovered_node_id=gui.hovered_node_id)

    # At end of draw pass:
    if tooltip_mgr.is_visible:
        tooltip_mgr.draw(screen_surface, mouse_pos, theme)

    # Remove when the control is destroyed:
    handle.unregister()
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    from ..theme.color_theme import ColorTheme


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class _TooltipRecord:
    node_id: str
    text: str
    delay_ms: int


class TooltipHandle:
    """Returned by :meth:`TooltipManager.register`.  Call :meth:`unregister`
    to remove the tooltip when the owning control is destroyed."""

    def __init__(self, node_id: str, manager: "TooltipManager") -> None:
        self._node_id = node_id
        self._manager = manager

    @property
    def node_id(self) -> str:
        return self._node_id

    def unregister(self) -> None:
        """Remove the tooltip registration for this handle."""
        self._manager.unregister(self._node_id)

    def update_text(self, text: str) -> None:
        """Change the tooltip text without re-registering."""
        self._manager.update_text(self._node_id, text)

    def __repr__(self) -> str:  # pragma: no cover
        return f"TooltipHandle(node_id={self._node_id!r})"


# ---------------------------------------------------------------------------
# Manager
# ---------------------------------------------------------------------------


class TooltipManager:
    """App-level service for hover-triggered tooltip hints.

    Parameters
    ----------
    default_delay_ms:
        Milliseconds of continuous hover before the tooltip appears (default 600).
    dismiss_ms:
        Milliseconds after which a visible tooltip auto-hides (default 5000).
        Set to 0 to disable auto-dismiss.
    """

    def __init__(
        self,
        *,
        default_delay_ms: int = 600,
        dismiss_ms: int = 5000,
    ) -> None:
        self._default_delay_ms = max(0, int(default_delay_ms))
        self._dismiss_ms = max(0, int(dismiss_ms))
        self._records: Dict[str, _TooltipRecord] = {}
        self._hover_node_id: Optional[str] = None
        self._elapsed_ms: float = 0.0
        self._visible_id: Optional[str] = None
        self._visible_elapsed_ms: float = 0.0

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(
        self,
        node: Any,
        text: str,
        *,
        delay_ms: Optional[int] = None,
    ) -> TooltipHandle:
        """Register *node* to display *text* as a tooltip on hover.

        Parameters
        ----------
        node:
            Any object with a ``control_id`` attribute
            (typically a :class:`~gui_do.UiNode`).
        text:
            Tooltip text to display.
        delay_ms:
            Override the default hover delay for this node.
        """
        nid = str(node.control_id)
        self._records[nid] = _TooltipRecord(
            node_id=nid,
            text=str(text),
            delay_ms=delay_ms if delay_ms is not None else self._default_delay_ms,
        )
        return TooltipHandle(nid, self)

    def unregister(self, node_id: str) -> None:
        """Remove the tooltip registration for *node_id*."""
        self._records.pop(str(node_id), None)
        if self._hover_node_id == node_id:
            self._hover_node_id = None
            self._elapsed_ms = 0.0
        if self._visible_id == node_id:
            self._visible_id = None

    def update_text(self, node_id: str, text: str) -> None:
        """Update tooltip text for an already-registered *node_id*."""
        record = self._records.get(str(node_id))
        if record is not None:
            record.text = str(text)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    def update(self, dt_seconds: float, hovered_node_id: Optional[str]) -> None:
        """Advance hover and dismiss timers.

        Call once per frame with the currently hovered node id (``None`` when
        the pointer is over non-registered or background areas).
        """
        dt_ms = float(dt_seconds) * 1000.0

        if hovered_node_id != self._hover_node_id:
            # Pointer moved to a different node — reset pending-show timer.
            self._hover_node_id = hovered_node_id
            self._elapsed_ms = 0.0
            # Hide tooltip if moving to a different registered node.
            if self._visible_id != hovered_node_id:
                self._visible_id = None
                self._visible_elapsed_ms = 0.0

        if self._hover_node_id is not None and self._hover_node_id in self._records:
            record = self._records[self._hover_node_id]
            if self._visible_id == self._hover_node_id:
                # Tooltip is visible — advance dismiss timer.
                if self._dismiss_ms > 0:
                    self._visible_elapsed_ms += dt_ms
                    if self._visible_elapsed_ms >= self._dismiss_ms:
                        self._visible_id = None
                        self._visible_elapsed_ms = 0.0
            else:
                # Accumulate hover time toward delay threshold.
                self._elapsed_ms += dt_ms
                if self._elapsed_ms >= record.delay_ms:
                    self._visible_id = self._hover_node_id
                    self._visible_elapsed_ms = 0.0
        else:
            # No registered node hovered — hide any visible tooltip.
            self._visible_id = None
            self._visible_elapsed_ms = 0.0

    # ------------------------------------------------------------------
    # Query
    # ------------------------------------------------------------------

    @property
    def is_visible(self) -> bool:
        """True when a tooltip is currently displayed."""
        return self._visible_id is not None

    @property
    def visible_text(self) -> Optional[str]:
        """The text of the currently visible tooltip, or ``None``."""
        if self._visible_id is None:
            return None
        record = self._records.get(self._visible_id)
        return record.text if record is not None else None

    @property
    def visible_node_id(self) -> Optional[str]:
        """The ``control_id`` of the node whose tooltip is currently shown."""
        return self._visible_id

    # ------------------------------------------------------------------
    # Draw
    # ------------------------------------------------------------------

    def draw(
        self,
        surface: Any,
        pointer_pos: Tuple[int, int],
        theme: "ColorTheme",
    ) -> None:
        """Render the active tooltip near *pointer_pos* on *surface*.

        Parameters
        ----------
        surface:
            A ``pygame.Surface`` to draw onto (typically the screen).
        pointer_pos:
            Current screen-space mouse position used to anchor the tooltip.
        theme:
            The active :class:`~gui_do.ColorTheme` instance.
        """
        text = self.visible_text
        if text is None:
            return

        import pygame

        pad = 6
        try:
            font_surf = theme.render_text(text, role="body")
        except Exception:  # pragma: no cover — theme stub or missing font
            return

        w = font_surf.get_width() + pad * 2
        h = font_surf.get_height() + pad * 2
        sw, sh = surface.get_size()
        x = min(pointer_pos[0] + 16, sw - w - 4)
        y = min(pointer_pos[1] + 16, sh - h - 4)

        bg = pygame.Surface((w, h))
        bg.fill(theme.surface)
        pygame.draw.rect(bg, theme.outline, bg.get_rect(), 1)
        bg.blit(font_surf, (pad, pad))
        surface.blit(bg, (x, y))
