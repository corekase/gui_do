"""Tests for gui_do/features/control_spec.py and related data-driven factory utilities."""
from __future__ import annotations

import unittest
from unittest.mock import MagicMock

import pygame
from pygame import Rect

pygame.init()  # required for Rect operations


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_stack(top: int = 0, bottom: int = 400, left: int = 0, width: int = 200, gap: int = 4):
    from gui_do.layout.cell_caret_layout import CellCaretLayout
    bounds = Rect(left, top, width, bottom - top)
    return CellCaretLayout(
        bounds=bounds,
        cell_width=width,
        cell_height=bottom - top,
        columns=1,
        item_gap_y=gap,
    )


def _dummy_control():
    ctrl = MagicMock()
    ctrl.set_rect = MagicMock()
    ctrl.set_accessibility = MagicMock()
    return ctrl


def _identity_slot_height(h: int) -> int:
    """Trivial slot_height_for that adds label overhead (18 + 4 = 22 px)."""
    return h + 22


# ===========================================================================
# ControlDefinition
# ===========================================================================


class TestControlDefinition(unittest.TestCase):
    def test_required_fields(self):
        from gui_do.features.control_spec import ControlDefinition
        ctrl = _dummy_control()
        defn = ControlDefinition(
            name="spinner",
            label_text="Spinner",
            control_height=30,
            row_index=10,
            control_factory=lambda: ctrl,
        )
        self.assertEqual("spinner", defn.name)
        self.assertEqual("Spinner", defn.label_text)
        self.assertEqual(30, defn.control_height)
        self.assertEqual(10, defn.row_index)
        self.assertIs(ctrl, defn.control_factory())

    def test_defaults(self):
        from gui_do.features.control_spec import ControlDefinition
        defn = ControlDefinition(
            name="x", label_text="X", control_height=20, row_index=0, control_factory=lambda: None
        )
        self.assertEqual(0, defn.column_index)
        self.assertIsNone(defn.focusable)
        self.assertIsNone(defn.accessibility_role)
        self.assertIsNone(defn.accessibility_label)

    def test_frozen(self):
        from gui_do.features.control_spec import ControlDefinition
        defn = ControlDefinition(
            name="x", label_text="X", control_height=20, row_index=0, control_factory=lambda: None
        )
        with self.assertRaises(Exception):
            defn.name = "y"  # type: ignore[misc]

    def test_exported_from_gui_do(self):
        from gui_do import ControlDefinition
        self.assertIsNotNone(ControlDefinition)


# ===========================================================================
# build_specs_from_column_section
# ===========================================================================


class TestBuildSpecsFromColumnSection(unittest.TestCase):
    def _make_defs(self, count: int = 2, *, column_index: int = 0):
        from gui_do.features.control_spec import ControlDefinition
        return tuple(
            ControlDefinition(
                name=f"ctrl_{i}",
                label_text=f"Label {i}",
                control_height=30,
                row_index=i,
                control_factory=_dummy_control,
                column_index=column_index,
                focusable=True,
                accessibility_role="button",
                accessibility_label=f"Button {i}",
            )
            for i in range(count)
        )

    def test_returns_correct_count(self):
        from gui_do.features.control_spec import build_specs_from_column_section
        defs = self._make_defs(3)
        stack = _make_stack()
        specs, _ = build_specs_from_column_section(defs, stack=stack, slot_height_for=_identity_slot_height)
        self.assertEqual(3, len(specs))

    def test_specs_are_tuple(self):
        from gui_do.features.control_spec import build_specs_from_column_section
        defs = self._make_defs(2)
        stack = _make_stack()
        specs, _ = build_specs_from_column_section(defs, stack=stack, slot_height_for=_identity_slot_height)
        self.assertIsInstance(specs, tuple)

    def test_names_preserved(self):
        from gui_do.features.control_spec import build_specs_from_column_section
        defs = self._make_defs(2)
        stack = _make_stack()
        specs, _ = build_specs_from_column_section(defs, stack=stack, slot_height_for=_identity_slot_height)
        self.assertEqual("ctrl_0", specs[0].name)
        self.assertEqual("ctrl_1", specs[1].name)

    def test_column_index_forwarded(self):
        from gui_do.features.control_spec import build_specs_from_column_section
        defs = self._make_defs(2, column_index=5)
        stack = _make_stack()
        specs, _ = build_specs_from_column_section(defs, stack=stack, slot_height_for=_identity_slot_height)
        self.assertEqual(5, specs[0].column_index)
        self.assertEqual(5, specs[1].column_index)

    def test_row_indices_preserved(self):
        from gui_do.features.control_spec import build_specs_from_column_section
        defs = self._make_defs(3)
        stack = _make_stack()
        specs, _ = build_specs_from_column_section(defs, stack=stack, slot_height_for=_identity_slot_height)
        for i, spec in enumerate(specs):
            self.assertEqual(i, spec.row_index)

    def test_accessibility_forwarded(self):
        from gui_do.features.control_spec import build_specs_from_column_section
        defs = self._make_defs(1)
        stack = _make_stack()
        specs, _ = build_specs_from_column_section(defs, stack=stack, slot_height_for=_identity_slot_height)
        self.assertEqual("button", specs[0].accessibility_role)
        self.assertEqual("Button 0", specs[0].accessibility_label)

    def test_bottom_y_advances(self):
        from gui_do.features.control_spec import build_specs_from_column_section
        defs = self._make_defs(3)
        stack = _make_stack(top=10)
        specs, bottom_y = build_specs_from_column_section(defs, stack=stack, slot_height_for=_identity_slot_height)
        last_spec = specs[-1]
        self.assertEqual(last_spec.control_rect.bottom, bottom_y)

    def test_empty_definitions_returns_empty_tuple(self):
        from gui_do.features.control_spec import build_specs_from_column_section
        stack = _make_stack(top=50)
        specs, bottom_y = build_specs_from_column_section((), stack=stack, slot_height_for=_identity_slot_height)
        self.assertEqual((), specs)
        self.assertEqual(50, bottom_y)

    def test_control_factory_called_once_per_definition(self):
        from gui_do.features.control_spec import ControlDefinition, build_specs_from_column_section
        call_counts = [0, 0]

        def factory0():
            call_counts[0] += 1
            return _dummy_control()

        def factory1():
            call_counts[1] += 1
            return _dummy_control()

        defs = (
            ControlDefinition("a", "A", 30, 0, factory0),
            ControlDefinition("b", "B", 30, 1, factory1),
        )
        stack = _make_stack()
        build_specs_from_column_section(defs, stack=stack, slot_height_for=_identity_slot_height)
        self.assertEqual([1, 1], call_counts)

    def test_overflow_gap_accepted(self):
        from gui_do.features.control_spec import build_specs_from_column_section
        defs = self._make_defs(2)
        stack = _make_stack()
        # Just verify no error raised with positive overflow_gap
        specs, _ = build_specs_from_column_section(
            defs, stack=stack, slot_height_for=_identity_slot_height, overflow_gap=10
        )
        self.assertEqual(2, len(specs))

    def test_exported_from_gui_do(self):
        from gui_do import build_specs_from_column_section
        self.assertIsNotNone(build_specs_from_column_section)

    def test_rects_are_non_empty(self):
        from gui_do.features.control_spec import build_specs_from_column_section
        defs = self._make_defs(2)
        stack = _make_stack()
        specs, _ = build_specs_from_column_section(defs, stack=stack, slot_height_for=_identity_slot_height)
        for spec in specs:
            r = spec.control_rect
            self.assertGreater(r.width, 0)
            self.assertGreater(r.height, 0)


# ===========================================================================
# NotificationSpec
# ===========================================================================


class TestNotificationSpec(unittest.TestCase):
    def test_required_field(self):
        from gui_do.features.data_driven_runtime import NotificationSpec
        spec = NotificationSpec(message="Hello")
        self.assertEqual("Hello", spec.message)

    def test_defaults(self):
        from gui_do.features.data_driven_runtime import NotificationSpec
        spec = NotificationSpec(message="Hello")
        self.assertEqual("", spec.title)
        self.assertIsNone(spec.severity)

    def test_custom_values(self):
        from gui_do.features.data_driven_runtime import NotificationSpec
        spec = NotificationSpec(message="Msg", title="T", severity="custom_sev")
        self.assertEqual("Msg", spec.message)
        self.assertEqual("T", spec.title)
        self.assertEqual("custom_sev", spec.severity)

    def test_frozen(self):
        from gui_do.features.data_driven_runtime import NotificationSpec
        spec = NotificationSpec(message="x")
        with self.assertRaises(Exception):
            spec.message = "y"  # type: ignore[misc]

    def test_exported_from_gui_do(self):
        from gui_do import NotificationSpec
        self.assertIsNotNone(NotificationSpec)


# ===========================================================================
# build_notification_center
# ===========================================================================


class TestBuildNotificationCenter(unittest.TestCase):
    def test_returns_notification_center(self):
        from gui_do.features.data_driven_runtime import build_notification_center
        from gui_do.overlays.notification_center import NotificationCenter
        nc = build_notification_center((), max_records=10)
        self.assertIsInstance(nc, NotificationCenter)

    def test_records_populated(self):
        from gui_do import ToastSeverity
        from gui_do.features.data_driven_runtime import NotificationSpec, build_notification_center
        specs = (
            NotificationSpec("Build OK", title="CI", severity=ToastSeverity.SUCCESS),
            NotificationSpec("Disk low", title="System", severity=ToastSeverity.WARNING),
        )
        nc = build_notification_center(specs, max_records=10)
        records = nc.records.value
        self.assertEqual(2, len(records))
        messages = {r.message for r in records}
        self.assertIn("Build OK", messages)
        self.assertIn("Disk low", messages)
        by_message = {r.message: r for r in records}
        self.assertEqual(ToastSeverity.SUCCESS, by_message["Build OK"].severity)
        self.assertEqual("CI", by_message["Build OK"].title)
        self.assertEqual(ToastSeverity.WARNING, by_message["Disk low"].severity)

    def test_empty_specs(self):
        from gui_do.features.data_driven_runtime import build_notification_center
        nc = build_notification_center((), max_records=5)
        self.assertEqual(0, len(nc.records.value))

    def test_default_severity_is_info(self):
        from gui_do import ToastSeverity
        from gui_do.features.data_driven_runtime import NotificationSpec, build_notification_center
        nc = build_notification_center((NotificationSpec("Hi"),), max_records=5)
        record = nc.records.value[0]
        self.assertEqual(ToastSeverity.INFO, record.severity)

    def test_max_records_honored(self):
        from gui_do.features.data_driven_runtime import NotificationSpec, build_notification_center
        specs = tuple(NotificationSpec(f"Msg {i}") for i in range(10))
        nc = build_notification_center(specs, max_records=3)
        # NotificationCenter caps at max_records; newest records retained
        self.assertLessEqual(len(nc.records.value), 3)

    def test_exported_from_gui_do(self):
        from gui_do import build_notification_center
        self.assertIsNotNone(build_notification_center)


if __name__ == "__main__":
    unittest.main()
