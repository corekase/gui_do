"""Tests for ShortcutHelpOverlay, ShortcutSection, ShortcutEntry."""
import unittest
from unittest.mock import MagicMock

import pygame
from pygame import Rect

from gui_do.overlays.shortcut_help_overlay import (
    ShortcutHelpOverlay,
    ShortcutSection,
    ShortcutEntry,
)


class TestShortcutEntryDataclass(unittest.TestCase):
    def test_fields_stored(self) -> None:
        entry = ShortcutEntry(
            label="Save File",
            chord_display="Ctrl+S",
            description="Save the current document",
            category="File",
        )
        self.assertEqual(entry.label, "Save File")
        self.assertEqual(entry.chord_display, "Ctrl+S")
        self.assertEqual(entry.description, "Save the current document")
        self.assertEqual(entry.category, "File")

    def test_description_defaults_empty(self) -> None:
        entry = ShortcutEntry(label="Undo", chord_display="Ctrl+Z")
        self.assertEqual(entry.description, "")
        self.assertEqual(entry.category, "")


class TestShortcutSectionDataclass(unittest.TestCase):
    def test_title_stored(self) -> None:
        sec = ShortcutSection(title="Editing")
        self.assertEqual(sec.title, "Editing")

    def test_entries_default_empty(self) -> None:
        sec = ShortcutSection(title="Editing")
        self.assertEqual(sec.entries, [])

    def test_entries_appended(self) -> None:
        sec = ShortcutSection(title="Nav")
        sec.entries.append(ShortcutEntry("Go Up", "K"))
        self.assertEqual(len(sec.entries), 1)


class TestShortcutHelpOverlayNoRegistry(unittest.TestCase):
    def _mgr(self):
        mgr = MagicMock()
        handle = MagicMock()
        handle.is_open = True
        mgr.show.return_value = handle
        return mgr

    def test_sections_empty_with_no_registry(self) -> None:
        overlay = ShortcutHelpOverlay(overlay_manager=self._mgr())
        self.assertEqual(overlay.sections, [])

    def test_is_open_false_initially(self) -> None:
        overlay = ShortcutHelpOverlay(overlay_manager=self._mgr())
        self.assertFalse(overlay.is_open)


class TestShortcutHelpOverlayWithRegistry(unittest.TestCase):
    def _mgr(self):
        mgr = MagicMock()
        handle = MagicMock()
        handle.is_open = True
        mgr.show.return_value = handle
        return mgr

    def _registry(self):
        from gui_do.actions.action_registry import ActionRegistry, ActionDescriptor
        reg = ActionRegistry()
        reg.declare(
            "file.save",
            label="Save",
            callback=lambda ctx, evt: True,
            category="File",
            shortcut_hint="Ctrl+S",
            description="Save file",
        )
        reg.declare(
            "edit.undo",
            label="Undo",
            callback=lambda ctx, evt: True,
            category="Edit",
            shortcut_hint="Ctrl+Z",
        )
        return reg

    def test_sections_built_from_registry(self) -> None:
        overlay = ShortcutHelpOverlay(
            overlay_manager=self._mgr(),
            action_registry=self._registry(),
        )
        sections = overlay.sections
        self.assertGreater(len(sections), 0)
        titles = [s.title for s in sections]
        self.assertIn("File", titles)
        self.assertIn("Edit", titles)

    def test_general_section_appears_first(self) -> None:
        from gui_do.actions.action_registry import ActionRegistry
        reg = ActionRegistry()
        reg.declare("x.general", "General Action", lambda ctx, evt: True, category="General")
        reg.declare("x.edit", "Edit Action", lambda ctx, evt: True, category="Edit")
        overlay = ShortcutHelpOverlay(overlay_manager=self._mgr(), action_registry=reg)
        sections = overlay.sections
        if sections and sections[0].title in ("General", "Edit"):
            self.assertEqual(sections[0].title, "General")

    def test_entry_label_and_chord_from_registry(self) -> None:
        overlay = ShortcutHelpOverlay(
            overlay_manager=self._mgr(),
            action_registry=self._registry(),
        )
        sections = overlay.sections
        file_section = next(s for s in sections if s.title == "File")
        entry = file_section.entries[0]
        self.assertEqual(entry.label, "Save")
        self.assertEqual(entry.chord_display, "Ctrl+S")


class TestShortcutHelpOverlayShowHideToggle(unittest.TestCase):
    def _setup(self):
        handle = MagicMock()
        handle.is_open = True
        mgr = MagicMock()
        mgr.show.return_value = handle
        overlay = ShortcutHelpOverlay(overlay_manager=mgr)
        return overlay, mgr, handle

    def test_show_calls_overlay_manager(self) -> None:
        overlay, mgr, handle = self._setup()
        overlay.show()
        mgr.show.assert_called_once()

    def test_is_open_after_show(self) -> None:
        overlay, mgr, handle = self._setup()
        overlay.show()
        self.assertTrue(overlay.is_open)

    def test_hide_calls_dismiss(self) -> None:
        overlay, mgr, handle = self._setup()
        overlay.show()
        overlay.hide()
        handle.dismiss.assert_called_once()

    def test_show_twice_does_not_double_open(self) -> None:
        overlay, mgr, handle = self._setup()
        overlay.show()
        overlay.show()
        # show() on overlay_manager should be called exactly once
        self.assertEqual(mgr.show.call_count, 1)

    def test_toggle_opens_when_closed(self) -> None:
        handle = MagicMock()
        handle.is_open = False
        mgr = MagicMock()
        mgr.show.return_value = handle
        overlay = ShortcutHelpOverlay(overlay_manager=mgr)
        overlay.toggle()
        mgr.show.assert_called_once()

    def test_toggle_closes_when_open(self) -> None:
        overlay, mgr, handle = self._setup()
        overlay.show()
        overlay.toggle()
        handle.dismiss.assert_called_once()


class TestShortcutHelpOverlaySetRect(unittest.TestCase):
    def test_set_rect_updates_rect(self) -> None:
        mgr = MagicMock()
        overlay = ShortcutHelpOverlay(overlay_manager=mgr)
        new_rect = Rect(50, 50, 800, 600)
        overlay.set_rect(new_rect)
        self.assertEqual(overlay._rect, new_rect)
