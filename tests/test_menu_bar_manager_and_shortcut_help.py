"""Tests for MenuBarManager and ShortcutHelpOverlay data structures."""
import unittest
from types import SimpleNamespace

import pygame
from pygame import Rect

from gui_do.overlays.menu_bar_manager import MenuBarManager
from gui_do.overlays.context_menu_manager import ContextMenuItem
from gui_do.controls.chrome.menu_bar_control import MenuStripControl
from gui_do.overlays.shortcut_help_overlay import (
    ShortcutEntry, ShortcutSection, ShortcutHelpOverlay,
)

pygame.init()


# ---------------------------------------------------------------------------
# Stub helpers
# ---------------------------------------------------------------------------


def _item(label: str) -> ContextMenuItem:
    return ContextMenuItem(label, action=lambda: None)


class _StubHandle:
    def __init__(self, open_=True):
        self.is_open = open_
        self.dismissed = False

    def dismiss(self):
        self.dismissed = True
        self.is_open = False


class _StubOverlayManager:
    def __init__(self):
        self._handle = None
        self.shown = []
        self.hidden = []

    def show(self, overlay_id, panel, **kwargs) -> _StubHandle:
        h = _StubHandle(open_=True)
        self._handle = h
        self.shown.append(overlay_id)
        self._on_dismiss = kwargs.get("on_dismiss")
        return h

    def hide(self, overlay_id) -> bool:
        if self._handle is not None:
            self._handle.is_open = False
        if callable(getattr(self, "_on_dismiss", None)):
            self._on_dismiss()
        self.hidden.append(overlay_id)
        return True


class _StubFocus:
    def __init__(self):
        self.focused_node = None

    def set_focus(self, node, *, via_keyboard=False):
        self.focused_node = node

    def clear_focus(self):
        self.focused_node = None


class _StubActionDescriptor:
    def __init__(self, action_id, label, category="General", description="", shortcut_hint=""):
        self.action_id = action_id
        self.label = label
        self.category = category
        self.description = description
        self.shortcut_hint = shortcut_hint


class _StubActionRegistry:
    def __init__(self, descs):
        self._descs = descs

    def descriptors(self):
        return list(self._descs)

    def has(self, action_id):
        return any(d.action_id == action_id for d in self._descs)

    def context_menu_items(self, *, context=None, category=None):
        return [_item(d.label) for d in self._descs]


# ===========================================================================
# MenuBarManager
# ===========================================================================


class TestMenuBarManagerRegistration(unittest.TestCase):
    def test_initial_empty(self):
        mgr = MenuBarManager()
        self.assertEqual([], mgr.menu_labels)

    def test_register_single_menu(self):
        mgr = MenuBarManager()
        mgr.register_menu("File", [_item("New"), _item("Open")])
        self.assertEqual(["File"], mgr.menu_labels)

    def test_register_multiple_menus_order_preserved(self):
        mgr = MenuBarManager()
        mgr.register_menu("File", [_item("New")])
        mgr.register_menu("Edit", [_item("Undo")])
        mgr.register_menu("View", [_item("Zoom")])
        self.assertEqual(["File", "Edit", "View"], mgr.menu_labels)

    def test_register_same_label_appends_items(self):
        mgr = MenuBarManager()
        mgr.register_menu("Edit", [_item("Undo")])
        mgr.register_menu("Edit", [_item("Redo")])
        items = mgr.items_for("Edit")
        self.assertEqual(2, len(items))
        labels = [it.label for it in items]
        self.assertIn("Undo", labels)
        self.assertIn("Redo", labels)

    def test_register_same_label_not_duplicated_in_order(self):
        mgr = MenuBarManager()
        mgr.register_menu("Edit", [_item("Undo")])
        mgr.register_menu("Edit", [_item("Redo")])
        self.assertEqual(1, mgr.menu_labels.count("Edit"))

    def test_items_for_unknown_returns_empty(self):
        mgr = MenuBarManager()
        self.assertEqual([], mgr.items_for("Unknown"))

    def test_items_for_known(self):
        mgr = MenuBarManager()
        mgr.register_menu("File", [_item("New"), _item("Open")])
        items = mgr.items_for("File")
        self.assertEqual(2, len(items))

    def test_items_for_returns_copy(self):
        mgr = MenuBarManager()
        mgr.register_menu("File", [_item("New")])
        copy_a = mgr.items_for("File")
        copy_a.clear()
        self.assertEqual(1, len(mgr.items_for("File")))


class TestMenuBarManagerSetEnabled(unittest.TestCase):
    def test_default_enabled_true(self):
        mgr = MenuBarManager()
        mgr.register_menu("File", [_item("New")])
        # enabled is stored internally; we verify via build entries
        rect = Rect(0, 0, 800, 28)
        bar = mgr.build("bar", rect)
        entry = bar.entries[0]
        self.assertTrue(entry.enabled)

    def test_set_enabled_false(self):
        mgr = MenuBarManager()
        mgr.register_menu("File", [_item("New")])
        mgr.set_enabled("File", False)
        rect = Rect(0, 0, 800, 28)
        bar = mgr.build("bar", rect)
        entry = bar.entries[0]
        self.assertFalse(entry.enabled)

    def test_set_enabled_unknown_label_no_error(self):
        mgr = MenuBarManager()
        mgr.set_enabled("DoesNotExist", False)   # should not raise


class TestMenuBarManagerClear(unittest.TestCase):
    def test_clear_removes_all(self):
        mgr = MenuBarManager()
        mgr.register_menu("File", [_item("New")])
        mgr.register_menu("Edit", [_item("Undo")])
        mgr.clear()
        self.assertEqual([], mgr.menu_labels)

    def test_clear_then_register_works(self):
        mgr = MenuBarManager()
        mgr.register_menu("File", [_item("New")])
        mgr.clear()
        mgr.register_menu("Help", [_item("About")])
        self.assertEqual(["Help"], mgr.menu_labels)


class TestMenuBarManagerBuild(unittest.TestCase):
    def _mgr(self):
        mgr = MenuBarManager()
        mgr.register_menu("File", [_item("New"), _item("Open")])
        mgr.register_menu("Edit", [_item("Undo")])
        return mgr

    def test_build_returns_menu_bar_control(self):
        bar = self._mgr().build("bar", Rect(0, 0, 800, 28))
        self.assertIsInstance(bar, MenuStripControl)

    def test_build_control_id(self):
        bar = self._mgr().build("mybar", Rect(0, 0, 800, 28))
        self.assertEqual("mybar", bar.control_id)

    def test_build_entries_count(self):
        bar = self._mgr().build("bar", Rect(0, 0, 800, 28))
        self.assertEqual(2, len(bar.entries))

    def test_build_entries_labels(self):
        bar = self._mgr().build("bar", Rect(0, 0, 800, 28))
        labels = [e.label for e in bar.entries]
        self.assertEqual(["File", "Edit"], labels)

    def test_build_rect_set(self):
        r = Rect(0, 0, 1024, 32)
        bar = self._mgr().build("bar", r)
        self.assertEqual(r, bar.rect)

    def test_empty_manager_builds_empty_bar(self):
        bar = MenuBarManager().build("bar", Rect(0, 0, 800, 28))
        self.assertEqual(0, len(bar.entries))


class TestMenuBarManagerRegisterActions(unittest.TestCase):
    def test_register_actions_creates_menu(self):
        registry = _StubActionRegistry([
            _StubActionDescriptor("new", "New"),
            _StubActionDescriptor("open", "Open"),
        ])
        mgr = MenuBarManager()
        mgr.register_actions("File", registry)
        self.assertIn("File", mgr.menu_labels)
        self.assertEqual(2, len(mgr.items_for("File")))


# ===========================================================================
# ShortcutEntry / ShortcutSection dataclasses
# ===========================================================================


class TestShortcutEntryDataclass(unittest.TestCase):
    def test_required_fields(self):
        entry = ShortcutEntry(label="Save", chord_display="Ctrl+S")
        self.assertEqual("Save", entry.label)
        self.assertEqual("Ctrl+S", entry.chord_display)

    def test_default_description_empty(self):
        entry = ShortcutEntry("New", "Ctrl+N")
        self.assertEqual("", entry.description)

    def test_default_category_empty(self):
        entry = ShortcutEntry("New", "Ctrl+N")
        self.assertEqual("", entry.category)

    def test_explicit_values(self):
        entry = ShortcutEntry("Quit", "Ctrl+Q", description="Exit app", category="File")
        self.assertEqual("Exit app", entry.description)
        self.assertEqual("File", entry.category)


class TestShortcutSectionDataclass(unittest.TestCase):
    def test_title_stored(self):
        sec = ShortcutSection(title="Edit")
        self.assertEqual("Edit", sec.title)

    def test_default_entries_empty(self):
        sec = ShortcutSection("Edit")
        self.assertEqual([], sec.entries)

    def test_entries_stored(self):
        entries = [ShortcutEntry("Undo", "Ctrl+Z"), ShortcutEntry("Redo", "Ctrl+Y")]
        sec = ShortcutSection("Edit", entries=entries)
        self.assertEqual(2, len(sec.entries))


# ===========================================================================
# ShortcutHelpOverlay — sections property
# ===========================================================================


class TestShortcutHelpOverlaySections(unittest.TestCase):
    def _overlay(self, registry=None, chord_mgr=None):
        mgr = _StubOverlayManager()
        return ShortcutHelpOverlay(mgr, action_registry=registry, key_chord_manager=chord_mgr)

    def test_sections_empty_when_no_registry_or_chords(self):
        ov = self._overlay()
        self.assertEqual([], ov.sections)

    def test_sections_from_registry(self):
        registry = _StubActionRegistry([
            _StubActionDescriptor("save", "Save", category="File"),
            _StubActionDescriptor("undo", "Undo", category="Edit"),
        ])
        ov = self._overlay(registry=registry)
        sections = ov.sections
        titles = {s.title for s in sections}
        self.assertIn("File", titles)
        self.assertIn("Edit", titles)

    def test_sections_general_first(self):
        registry = _StubActionRegistry([
            _StubActionDescriptor("zzz", "Z Action", category="Zzz"),
            _StubActionDescriptor("gen", "General Action", category="General"),
        ])
        ov = self._overlay(registry=registry)
        sections = ov.sections
        self.assertEqual("General", sections[0].title)

    def test_sections_entry_label(self):
        registry = _StubActionRegistry([
            _StubActionDescriptor("save", "Save", category="File"),
        ])
        ov = self._overlay(registry=registry)
        entries = ov.sections[0].entries
        self.assertEqual(1, len(entries))
        self.assertEqual("Save", entries[0].label)

    def test_sections_entry_shortcut_hint(self):
        registry = _StubActionRegistry([
            _StubActionDescriptor("save", "Save", shortcut_hint="Ctrl+S"),
        ])
        ov = self._overlay(registry=registry)
        entry = ov.sections[0].entries[0]
        self.assertEqual("Ctrl+S", entry.chord_display)

    def test_sections_sorted_alphabetically_after_general(self):
        registry = _StubActionRegistry([
            _StubActionDescriptor("z", "Z", category="Zoo"),
            _StubActionDescriptor("a", "A", category="Animals"),
        ])
        ov = self._overlay(registry=registry)
        titles = [s.title for s in ov.sections]
        self.assertEqual(["Animals", "Zoo"], titles)

    def test_sections_include_manual_shortcut_lines(self):
        ov = ShortcutHelpOverlay(
            _StubOverlayManager(),
            manual_shortcut_lines=(
                "F1: Raise/Lower Task Panel",
                "F5: Toggle Command Palette",
            ),
            manual_section_title="Keyboard",
        )

        sections = ov.sections
        self.assertEqual(1, len(sections))
        self.assertEqual("Keyboard", sections[0].title)
        self.assertEqual("F1", sections[0].entries[0].chord_display)
        self.assertEqual("Raise/Lower Task Panel", sections[0].entries[0].label)

    def test_sections_prepend_manual_shortcuts_when_requested(self):
        registry = _StubActionRegistry([
            _StubActionDescriptor("save", "Save", category="General"),
        ])
        ov = ShortcutHelpOverlay(
            _StubOverlayManager(),
            action_registry=registry,
            manual_shortcut_lines=("F9: Display this help",),
            manual_section_title="Keyboard",
            prepend_manual_shortcuts=True,
        )

        titles = [s.title for s in ov.sections]
        self.assertEqual("Keyboard", titles[0])

    def test_manual_shortcuts_only_omits_registry_sections(self):
        registry = _StubActionRegistry([
            _StubActionDescriptor("save", "Save", category="General"),
        ])
        ov = ShortcutHelpOverlay(
            _StubOverlayManager(),
            action_registry=registry,
            manual_shortcut_lines=("F9: Display this help",),
            manual_section_title="Keyboard",
            manual_shortcuts_only=True,
        )

        sections = ov.sections
        self.assertEqual(1, len(sections))
        self.assertEqual("Keyboard", sections[0].title)
        self.assertEqual("Display this help", sections[0].entries[0].label)


# ===========================================================================
# ShortcutHelpOverlay — show / hide / toggle / is_open
# ===========================================================================


class TestShortcutHelpOverlayVisibility(unittest.TestCase):
    def _overlay(self):
        mgr = _StubOverlayManager()
        return ShortcutHelpOverlay(mgr), mgr

    def test_not_open_initially(self):
        ov, _ = self._overlay()
        self.assertFalse(ov.is_open)

    def test_show_opens(self):
        ov, _ = self._overlay()
        ov.show()
        self.assertTrue(ov.is_open)

    def test_hide_closes(self):
        ov, mgr = self._overlay()
        ov.show()
        ov.hide()
        self.assertFalse(ov.is_open)

    def test_toggle_opens_when_closed(self):
        ov, _ = self._overlay()
        ov.toggle()
        self.assertTrue(ov.is_open)

    def test_toggle_closes_when_open(self):
        ov, _ = self._overlay()
        ov.show()
        ov.toggle()
        self.assertFalse(ov.is_open)

    def test_show_when_already_open_no_duplicate(self):
        ov, mgr = self._overlay()
        ov.show()
        ov.show()   # second call should be no-op
        self.assertEqual(1, len(mgr.shown))

    def test_set_rect(self):
        ov, _ = self._overlay()
        new_rect = Rect(50, 50, 800, 600)
        ov.set_rect(new_rect)
        self.assertEqual(Rect(50, 50, 800, 600), ov._rect)

    def test_show_captures_focus_and_hide_restores_when_no_new_focus(self):
        mgr = _StubOverlayManager()
        focus = _StubFocus()
        prior = SimpleNamespace(control_id="prior", visible=True, enabled=True)
        focus.set_focus(prior)
        app = SimpleNamespace(focus=focus, scene=SimpleNamespace(contains=lambda node: node is prior))
        ov = ShortcutHelpOverlay(mgr, app=app)

        ov.show()
        self.assertIsNone(focus.focused_node)

        ov.hide()
        self.assertIs(focus.focused_node, prior)

    def test_hide_preserves_clicked_focus_target(self):
        mgr = _StubOverlayManager()
        focus = _StubFocus()
        prior = SimpleNamespace(control_id="prior", visible=True, enabled=True)
        clicked = SimpleNamespace(control_id="clicked", visible=True, enabled=True)
        focus.set_focus(prior)
        app = SimpleNamespace(
            focus=focus,
            scene=SimpleNamespace(contains=lambda node: node in (prior, clicked)),
        )
        ov = ShortcutHelpOverlay(mgr, app=app)

        ov.show()
        focus.set_focus(clicked)
        ov.hide()
        self.assertIs(focus.focused_node, clicked)


if __name__ == "__main__":
    unittest.main()
