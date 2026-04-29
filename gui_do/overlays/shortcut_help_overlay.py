"""ShortcutHelpOverlay — auto-generated keyboard shortcut reference panel.

Reads structured metadata from :class:`~gui_do.ActionRegistry` and
:class:`~gui_do.KeyChordManager` and renders a formatted shortcut reference
panel using the :class:`~gui_do.OverlayManager`.

The overlay can be triggered by any callable (e.g. bound to a ``?`` key
action) or shown/hidden programmatically.

Usage::

    from gui_do import ShortcutHelpOverlay

    help_overlay = ShortcutHelpOverlay(
        overlay_manager=app.overlays,
        action_registry=action_registry,
        key_chord_manager=chord_manager,
    )

    # Show/hide:
    help_overlay.show()
    help_overlay.hide()
    help_overlay.toggle()

    # Access the structured shortcut data (before rendering):
    for section in help_overlay.sections:
        print(section.title)
        for entry in section.entries:
            print(f"  {entry.chord_display}  —  {entry.label}")
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, TYPE_CHECKING

import pygame
from pygame import Rect

if TYPE_CHECKING:
    from ..overlays.overlay_manager import OverlayManager, OverlayHandle
    from ..actions.action_registry import ActionRegistry
    from ..actions.key_chord_manager import KeyChordManager


# ---------------------------------------------------------------------------
# Data types
# ---------------------------------------------------------------------------


@dataclass
class ShortcutEntry:
    """One shortcut entry in the help overlay.

    Attributes
    ----------
    label:
        Human-readable action name (from :class:`~gui_do.ActionDescriptor.label`).
    chord_display:
        Formatted keystroke string (e.g. ``"Ctrl+K, Ctrl+C"``).
    description:
        Optional longer description from the action descriptor.
    category:
        Category grouping string.
    """
    label: str
    chord_display: str
    description: str = ""
    category: str = ""


@dataclass
class ShortcutSection:
    """A group of related :class:`ShortcutEntry` objects under a shared title.

    Attributes
    ----------
    title:
        Section heading (corresponds to :attr:`~gui_do.ActionDescriptor.category`).
    entries:
        Ordered list of shortcut entries in this section.
    """
    title: str
    entries: List[ShortcutEntry] = field(default_factory=list)


# ---------------------------------------------------------------------------
# ShortcutHelpOverlay
# ---------------------------------------------------------------------------


class ShortcutHelpOverlay:
    """Auto-generated shortcut reference panel.

    Parameters
    ----------
    overlay_manager:
        The application's :class:`~gui_do.OverlayManager`.
    action_registry:
        Optional :class:`~gui_do.ActionRegistry`.  Provides action labels,
        categories, and descriptions.
    key_chord_manager:
        Optional :class:`~gui_do.KeyChordManager`.  Provides chord-to-action
        bindings for display.
    overlay_rect:
        The screen rect for the help panel.  Defaults to a centred 600×400
        panel (use :meth:`set_rect` to update at runtime).
    overlay_id:
        Unique overlay identifier.  Defaults to ``"shortcut_help_overlay"``.
    """

    _OVERLAY_ID = "shortcut_help_overlay"

    def __init__(
        self,
        overlay_manager: "OverlayManager",
        action_registry: Optional["ActionRegistry"] = None,
        key_chord_manager: Optional["KeyChordManager"] = None,
        *,
        overlay_rect: Optional[Rect] = None,
        overlay_id: str = _OVERLAY_ID,
    ) -> None:
        self._overlay_manager = overlay_manager
        self._action_registry = action_registry
        self._key_chord_manager = key_chord_manager
        self._rect = overlay_rect or Rect(100, 80, 600, 440)
        self._overlay_id = overlay_id
        self._handle: Optional["OverlayHandle"] = None

    # ------------------------------------------------------------------
    # Rect
    # ------------------------------------------------------------------

    def set_rect(self, rect: Rect) -> None:
        """Update the display rect of the overlay panel."""
        self._rect = Rect(rect)

    # ------------------------------------------------------------------
    # Show / hide / toggle
    # ------------------------------------------------------------------

    def show(self) -> None:
        """Build and display the shortcut help overlay."""
        if self._handle is not None and self._handle.is_open:
            return
        sections = self.sections
        panel = self._build_panel(sections)
        self._handle = self._overlay_manager.show(
            self._overlay_id,
            panel,
            dismiss_on_outside_click=True,
            dismiss_on_escape=True,
            on_dismiss=self._on_dismiss,
        )

    def hide(self) -> None:
        """Dismiss the help overlay if open."""
        if self._handle is not None and self._handle.is_open:
            self._handle.dismiss()
        self._handle = None

    def toggle(self) -> None:
        """Show if hidden; hide if visible."""
        if self._handle is not None and self._handle.is_open:
            self.hide()
        else:
            self.show()

    @property
    def is_open(self) -> bool:
        """``True`` if the overlay is currently visible."""
        return self._handle is not None and self._handle.is_open

    # ------------------------------------------------------------------
    # Structured data
    # ------------------------------------------------------------------

    @property
    def sections(self) -> List[ShortcutSection]:
        """Build and return the structured shortcut data.

        Sections are sorted alphabetically by title; the *General* section
        (if present) is placed first.
        """
        # Build chord display map: action_id → display string
        chord_map: Dict[str, str] = {}
        if self._key_chord_manager is not None:
            for chord, action_name in self._key_chord_manager._chords:
                if action_name not in chord_map:
                    chord_map[action_name] = _format_chord(chord)

        # Build sections from action registry
        section_map: Dict[str, ShortcutSection] = {}
        if self._action_registry is not None:
            for desc in self._action_registry.descriptors():
                category = desc.category or "General"
                if category not in section_map:
                    section_map[category] = ShortcutSection(title=category)
                chord_str = chord_map.get(desc.action_id, desc.shortcut_hint)
                entry = ShortcutEntry(
                    label=desc.label,
                    chord_display=chord_str,
                    description=desc.description,
                    category=category,
                )
                section_map[category].entries.append(entry)

        # Also add chord bindings that have no matching action registry entry
        if self._key_chord_manager is not None:
            for chord, action_name in self._key_chord_manager._chords:
                if action_name and (
                    self._action_registry is None
                    or not self._action_registry.has(action_name)
                ):
                    category = "Keyboard"
                    if category not in section_map:
                        section_map[category] = ShortcutSection(title=category)
                    section_map[category].entries.append(ShortcutEntry(
                        label=action_name,
                        chord_display=_format_chord(chord),
                    ))

        if not section_map:
            return []

        # Sort: General first, then alphabetically
        def _sort_key(title: str) -> tuple:
            return (0 if title == "General" else 1, title.lower())

        return sorted(section_map.values(), key=lambda s: _sort_key(s.title))

    # ------------------------------------------------------------------
    # Panel builder
    # ------------------------------------------------------------------

    def _build_panel(self, sections: List[ShortcutSection]) -> "OverlayPanelControl":  # type: ignore[return]
        """Create an :class:`~gui_do.OverlayPanelControl` rendering the shortcut help."""
        from ..controls.composite.overlay_panel_control import OverlayPanelControl

        panel = OverlayPanelControl(self._overlay_id, self._rect)
        panel.sections = sections  # type: ignore[attr-defined]
        panel.draw_shortcut_help = True  # type: ignore[attr-defined]
        return panel

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_dismiss(self) -> None:
        self._handle = None


# ---------------------------------------------------------------------------
# KeyChord formatting helper
# ---------------------------------------------------------------------------


def _format_chord(chord: "KeyChord") -> str:  # type: ignore[name-defined]
    """Return a human-readable string for *chord* (e.g. ``"Ctrl+K, Ctrl+C"``)."""
    import pygame

    _MOD_NAMES = [
        (pygame.KMOD_CTRL,  "Ctrl"),
        (pygame.KMOD_ALT,   "Alt"),
        (pygame.KMOD_SHIFT, "Shift"),
        (pygame.KMOD_META,  "Meta"),
    ]

    step_strs = []
    for step in chord:
        parts = []
        for mask, name in _MOD_NAMES:
            if step.mod & mask:
                parts.append(name)
        key_name = pygame.key.name(step.key).upper()
        parts.append(key_name)
        step_strs.append("+".join(parts))
    return ", ".join(step_strs)
