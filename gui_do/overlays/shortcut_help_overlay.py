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
from typing import TYPE_CHECKING, Dict, List, Optional

import pygame
from pygame import Rect

if TYPE_CHECKING:
    from ..overlays.overlay_manager import OverlayManager, OverlayHandle
    from ..actions.action_registry import ActionRegistry
    from ..actions.key_chord_manager import KeyChord, KeyChordManager
    from ..controls.composite.overlay_panel_control import OverlayPanelControl


def _wrap_text(font, text: str, max_width: int) -> List[str]:
    raw = str(text or "").strip()
    if not raw:
        return [""]
    if max_width <= 8:
        return [raw]
    words = raw.split()
    if not words:
        return [raw]
    lines: List[str] = []
    current = words[0]
    for word in words[1:]:
        candidate = f"{current} {word}"
        if _font_text_size(font, candidate)[0] <= max_width:
            current = candidate
            continue
        lines.append(current)
        current = word
    lines.append(current)
    return lines


def _font_render(font, text: str, color):
    return font.render(str(text), True, color)


def _font_text_size(font, text: str) -> tuple[int, int]:
    if hasattr(font, "text_size"):
        return tuple(map(int, font.text_size(str(text))))
    return tuple(map(int, font.size(str(text))))


def _font_line_height(font) -> int:
    if hasattr(font, "line_height"):
        return int(font.line_height)
    return int(font.get_height())


class _ShortcutHelpPanel:
    """Internal overlay panel that renders shortcut sections with wrapped text."""

    def __init__(self, control_id: str, rect: Rect, sections: List["ShortcutSection"]) -> None:
        from ..controls.composite.overlay_panel_control import OverlayPanelControl

        self._base = OverlayPanelControl(control_id, rect)
        self.rect = self._base.rect
        self.visible = self._base.visible
        self.enabled = self._base.enabled
        self.sections = list(sections)

    def handle_routed_event(self, event, app, theme=None):
        return self._base.handle_routed_event(event, app, theme=theme)

    def draw(self, surface, theme) -> None:
        self._base.draw(surface, theme)
        if not self.visible:
            return

        panel_rect = Rect(self.rect)
        title_color = getattr(theme, "text", (230, 230, 230))
        body_color = getattr(theme, "text", (230, 230, 230))
        chord_color = getattr(theme, "highlight", (140, 180, 255))
        divider = getattr(theme, "border", (80, 80, 90))

        try:
            title_font = theme.fonts.font_instance("menu_bar.entry", size=19)
            section_font = theme.fonts.font_instance("menu_bar.entry", size=17)
            body_font = theme.fonts.font_instance("default", size=16)
        except Exception:
            if not pygame.font.get_init():
                pygame.font.init()
            title_font = pygame.font.SysFont(None, 22)
            section_font = pygame.font.SysFont(None, 19)
            body_font = pygame.font.SysFont(None, 17)

        pad_x = 20
        pad_y = 12
        chord_col_min_w = 260
        chord_col_max_w = 360
        col_gap = 28
        min_text_col_w = 260
        line_gap = 4
        section_gap = 10

        x = panel_rect.left + pad_x
        y = panel_rect.top + pad_y
        max_w = max(40, panel_rect.width - (pad_x * 2))
        measured_chord_w = 0
        for section in self.sections:
            for entry in section.entries:
                chord = str(getattr(entry, "chord_display", "")).strip()
                measured_chord_w = max(measured_chord_w, _font_text_size(body_font, chord)[0])
        chord_col_w = min(
            chord_col_max_w,
            max(chord_col_min_w, measured_chord_w + 18),
        )
        max_chord_by_layout = max(120, max_w - min_text_col_w - col_gap)
        chord_col_w = min(chord_col_w, max_chord_by_layout)
        text_col_w = max(120, max_w - chord_col_w - col_gap)

        title_surf = _font_render(title_font, "Keyboard Shortcuts", title_color)
        surface.blit(title_surf, (x, y))
        y += title_surf.get_height() + 8
        pygame.draw.line(surface, divider, (x, y), (x + max_w, y), 1)
        y += 8

        if not self.sections:
            empty_surf = _font_render(body_font, "No shortcuts available.", body_color)
            surface.blit(empty_surf, (x, y))
            return

        for section in self.sections:
            section_surf = _font_render(section_font, str(section.title), title_color)
            surface.blit(section_surf, (x, y))
            y += section_surf.get_height() + 6

            for entry in section.entries:
                chord = str(getattr(entry, "chord_display", "")).strip()
                label = str(getattr(entry, "label", "")).strip()
                detail = str(getattr(entry, "description", "")).strip()

                text_body = label if not detail else f"{label} - {detail}"
                wrapped = _wrap_text(body_font, text_body, text_col_w)
                wrapped = wrapped or [text_body]

                chord_surf = _font_render(body_font, chord, chord_color)
                surface.blit(chord_surf, (x + 2, y))

                text_x = x + chord_col_w + col_gap
                for i, line in enumerate(wrapped):
                    line_surf = _font_render(body_font, line, body_color)
                    surface.blit(line_surf, (text_x, y + i * (line_surf.get_height() + line_gap)))

                row_h = max(chord_surf.get_height(), len(wrapped) * (_font_line_height(body_font) + line_gap) - line_gap)
                y += row_h + 6

                if y > panel_rect.bottom - 24:
                    more = _font_render(body_font, "...", body_color)
                    surface.blit(more, (x + max_w - 16, panel_rect.bottom - 20))
                    return

            y += section_gap


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
        app=None,
        action_registry: Optional["ActionRegistry"] = None,
        key_chord_manager: Optional["KeyChordManager"] = None,
        *,
        overlay_rect: Optional[Rect] = None,
        overlay_id: str = _OVERLAY_ID,
        manual_shortcut_lines: tuple[str, ...] = (),
        manual_section_title: str = "Keyboard",
        prepend_manual_shortcuts: bool = False,
        manual_shortcuts_only: bool = False,
        exclude_section_titles: tuple[str, ...] = (),
        exclude_entry_labels: tuple[str, ...] = (),
    ) -> None:
        self._overlay_manager = overlay_manager
        self._app = app
        self._action_registry = action_registry
        self._key_chord_manager = key_chord_manager
        self._rect = overlay_rect or Rect(100, 80, 600, 440)
        self._overlay_id = overlay_id
        self._handle: Optional["OverlayHandle"] = None
        self._saved_focus_node = None
        self._pending_focus_restore = False
        self._manual_shortcut_lines = tuple(str(line) for line in manual_shortcut_lines)
        self._manual_section_title = str(manual_section_title)
        self._prepend_manual_shortcuts = bool(prepend_manual_shortcuts)
        self._manual_shortcuts_only = bool(manual_shortcuts_only)
        self._exclude_section_titles = {
            str(title).strip().lower()
            for title in exclude_section_titles
            if str(title).strip()
        }
        self._exclude_entry_labels = {
            str(label).strip().lower()
            for label in exclude_entry_labels
            if str(label).strip()
        }

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
        self._fit_rect_height_to_sections(sections)
        self._capture_focus_before_open()
        panel = self._build_panel(sections)
        self._handle = self._overlay_manager.show(
            self._overlay_id,
            panel,
            dismiss_on_outside_click=True,
            dismiss_on_escape=True,
            consume_unhandled_keys=True,
            on_dismiss=self._on_dismiss,
        )

    def hide(self) -> None:
        """Dismiss the help overlay if open."""
        if self._handle is not None and self._handle.is_open:
            self._handle.dismiss()
        self._finalize_dismiss()

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
        manual_section = self._manual_section()
        if manual_section is not None and manual_section.title.strip().lower() in self._exclude_section_titles:
            manual_section = None
        if manual_section is not None:
            filtered_manual_entries = [
                entry
                for entry in manual_section.entries
                if entry.label.strip().lower() not in self._exclude_entry_labels
            ]
            manual_section = ShortcutSection(title=manual_section.title, entries=filtered_manual_entries)
        if self._manual_shortcuts_only:
            if manual_section is None or not manual_section.entries:
                return []
            return [manual_section]

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
                if category.strip().lower() in self._exclude_section_titles:
                    continue
                if desc.label.strip().lower() in self._exclude_entry_labels:
                    continue
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
                    if category.lower() in self._exclude_section_titles:
                        continue
                    if str(action_name).strip().lower() in self._exclude_entry_labels:
                        continue
                    if category not in section_map:
                        section_map[category] = ShortcutSection(title=category)
                    section_map[category].entries.append(ShortcutEntry(
                        label=action_name,
                        chord_display=_format_chord(chord),
                    ))

        if manual_section is not None:
            target = section_map.get(manual_section.title)
            if target is None:
                section_map[manual_section.title] = manual_section
            else:
                seen = {(e.chord_display, e.label, e.description) for e in target.entries}
                for entry in manual_section.entries:
                    if entry.label.strip().lower() in self._exclude_entry_labels:
                        continue
                    key = (entry.chord_display, entry.label, entry.description)
                    if key in seen:
                        continue
                    target.entries.append(entry)

        if not section_map:
            return []

        # Sort: General first, then alphabetically
        def _sort_key(title: str) -> tuple:
            return (0 if title == "General" else 1, title.lower())

        sorted_sections = sorted(section_map.values(), key=lambda s: _sort_key(s.title))
        if not self._prepend_manual_shortcuts or manual_section is None:
            return sorted_sections

        manual_title = manual_section.title
        manual_only = [s for s in sorted_sections if s.title == manual_title]
        others = [s for s in sorted_sections if s.title != manual_title]
        return manual_only + others

    def _manual_section(self) -> Optional[ShortcutSection]:
        if not self._manual_shortcut_lines:
            return None
        entries: List[ShortcutEntry] = []
        for line in self._manual_shortcut_lines:
            text = str(line).strip()
            if not text:
                continue
            chord_part, sep, label_part = text.partition(":")
            chord = chord_part.strip()
            label = label_part.strip() if sep else text
            entries.append(
                ShortcutEntry(
                    label=label,
                    chord_display=chord,
                    category=self._manual_section_title,
                )
            )
        if not entries:
            return None
        return ShortcutSection(title=self._manual_section_title, entries=entries)

    # ------------------------------------------------------------------
    # Panel builder
    # ------------------------------------------------------------------

    def _build_panel(self, sections: List[ShortcutSection]) -> "OverlayPanelControl":  # type: ignore[return]
        """Create an :class:`~gui_do.OverlayPanelControl` rendering the shortcut help."""
        return _ShortcutHelpPanel(self._overlay_id, self._rect, sections)  # type: ignore[return-value]

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_dismiss(self) -> None:
        self._finalize_dismiss()

    def _capture_focus_before_open(self) -> None:
        app = self._app
        focus = getattr(app, "focus", None)
        if focus is None:
            self._saved_focus_node = None
            self._pending_focus_restore = False
            return
        self._saved_focus_node = getattr(focus, "focused_node", None)
        self._pending_focus_restore = True
        focus.clear_focus()

    def _finalize_dismiss(self) -> None:
        self._handle = None
        if not self._pending_focus_restore:
            self._saved_focus_node = None
            return
        self._pending_focus_restore = False

        app = self._app
        focus = getattr(app, "focus", None)
        saved = self._saved_focus_node
        self._saved_focus_node = None
        if focus is None:
            return

        current = getattr(focus, "focused_node", None)
        if current is not None:
            return
        if self._is_focus_target_valid(saved):
            focus.set_focus(saved)
            return
        focus.clear_focus()

    def _is_focus_target_valid(self, node) -> bool:
        if node is None:
            return False
        app = self._app
        scene = getattr(app, "scene", None)
        if scene is None:
            return False
        if not getattr(node, "visible", False) or not getattr(node, "enabled", False):
            return False
        contains = getattr(scene, "contains", None)
        if callable(contains):
            try:
                return bool(contains(node))
            except Exception:
                return False
        return True

    def _fit_rect_height_to_sections(self, sections: List[ShortcutSection]) -> None:
        width = max(120, int(self._rect.width))
        if not pygame.font.get_init():
            pygame.font.init()
        try:
            title_font = self._app.theme.fonts.font_instance("menu_bar.entry", size=19)
            section_font = self._app.theme.fonts.font_instance("menu_bar.entry", size=17)
            body_font = self._app.theme.fonts.font_instance("default", size=16)
        except Exception:
            title_font = pygame.font.SysFont(None, 22)
            section_font = pygame.font.SysFont(None, 19)
            body_font = pygame.font.SysFont(None, 17)

        pad_x = 20
        pad_y = 12
        chord_col_min_w = 260
        chord_col_max_w = 360
        col_gap = 28
        min_text_col_w = 260
        line_gap = 4
        section_gap = 10

        max_w = max(40, width - (pad_x * 2))
        measured_chord_w = 0
        for section in sections:
            for entry in section.entries:
                chord = str(getattr(entry, "chord_display", "")).strip()
                measured_chord_w = max(measured_chord_w, _font_text_size(body_font, chord)[0])
        chord_col_w = min(chord_col_max_w, max(chord_col_min_w, measured_chord_w + 18))
        max_chord_by_layout = max(120, max_w - min_text_col_w - col_gap)
        chord_col_w = min(chord_col_w, max_chord_by_layout)
        text_col_w = max(120, max_w - chord_col_w - col_gap)

        estimated = pad_y
        estimated += _font_line_height(title_font) + 8
        estimated += 1 + 8
        if not sections:
            estimated += _font_line_height(body_font)
        else:
            for section in sections:
                estimated += _font_line_height(section_font) + 6
                for entry in section.entries:
                    label = str(getattr(entry, "label", "")).strip()
                    detail = str(getattr(entry, "description", "")).strip()
                    text_body = label if not detail else f"{label} - {detail}"
                    wrapped = _wrap_text(body_font, text_body, text_col_w) or [text_body]
                    row_h = max(_font_line_height(body_font), len(wrapped) * (_font_line_height(body_font) + line_gap) - line_gap)
                    estimated += row_h + 6
                estimated += section_gap
        estimated += pad_y

        desired_h = max(140, int(estimated))
        if desired_h != int(self._rect.height):
            next_rect = Rect(self._rect)
            next_rect.height = desired_h
            next_rect.centery = self._rect.centery
            self._rect = next_rect


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
