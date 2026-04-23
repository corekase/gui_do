import unittest
from collections.abc import Callable as AbcCallable
from typing import Literal, Union, get_args, get_origin

import gui
from tests.contract_test_catalog import PUBLIC_API_EXPORT_ORDER

from gui import ActionManager
from gui import EventBus
from gui import EventPhase
from gui import EventType
from gui import FocusManager
from gui import FontManager
from gui import GuiEvent
from gui import InvalidationTracker
from gui import ensure_reason_callback
from gui import normalize_value_change_callback_mode
from gui import ObservableValue
from gui import PresentationModel
from gui import VALUE_CHANGE_CALLBACK_MODES
from gui import ValueChangeCallback
from gui import ValueChangeCallbackMode


EXPECTED_PUBLIC_EXPORTS = set(PUBLIC_API_EXPORT_ORDER)


class PublicApiExportsTests(unittest.TestCase):
    def test_core_api_exports_are_importable(self) -> None:
        self.assertTrue(callable(ActionManager))
        self.assertTrue(callable(EventBus))
        self.assertTrue(callable(FocusManager))
        self.assertTrue(callable(FontManager))
        self.assertTrue(callable(InvalidationTracker))
        self.assertTrue(callable(ObservableValue))
        self.assertTrue(callable(PresentationModel))

    def test_event_phase_export_integrates_with_guievent(self) -> None:
        event = GuiEvent(kind=EventType.PASS, type=0)

        event.with_phase(EventPhase.CAPTURE)

        self.assertEqual(event.phase, EventPhase.CAPTURE)

    def test_demo_specific_mandel_symbols_not_exported_from_gui(self) -> None:
        self.assertFalse(hasattr(gui, "MANDEL_STATUS_TOPIC"))
        self.assertFalse(hasattr(gui, "MandelStatusEvent"))

    def test_public_all_excludes_demo_symbols(self) -> None:
        exported = set(gui.__all__)

        self.assertNotIn("MandelStatusEvent", exported)
        self.assertFalse(any(name.startswith("MANDEL_") for name in exported))
        self.assertFalse(any("mandel" in name.lower() for name in exported))

    def test_public_all_matches_expected_export_surface(self) -> None:
        self.assertEqual(set(gui.__all__), EXPECTED_PUBLIC_EXPORTS)

    def test_public_all_matches_expected_export_order(self) -> None:
        self.assertEqual(tuple(gui.__all__), PUBLIC_API_EXPORT_ORDER)

    def test_public_all_names_are_resolvable_attributes(self) -> None:
        for export_name in gui.__all__:
            self.assertTrue(hasattr(gui, export_name), f"gui missing attribute for __all__ export: {export_name}")

    def test_value_change_callback_modes_export_is_canonical_tuple(self) -> None:
        self.assertEqual(VALUE_CHANGE_CALLBACK_MODES, ("compat", "reason-required"))

    def test_callback_mode_normalizer_export_is_canonical(self) -> None:
        self.assertEqual(normalize_value_change_callback_mode("  COMPAT  "), "compat")
        self.assertEqual(normalize_value_change_callback_mode("reason-required"), "reason-required")

    def test_ensure_reason_callback_export_adapts_value_only_callback(self) -> None:
        seen = []
        adapted = ensure_reason_callback(lambda value: seen.append(value))

        self.assertIsNotNone(adapted)
        adapted(3, gui.ValueChangeReason.KEYBOARD)
        self.assertEqual(seen, [3])

    def test_value_change_callback_mode_type_alias_export_shape(self) -> None:
        self.assertIs(get_origin(ValueChangeCallbackMode), Literal)
        self.assertEqual(get_args(ValueChangeCallbackMode), ("compat", "reason-required"))

    def test_value_change_callback_type_alias_export_shape(self) -> None:
        self.assertIs(get_origin(ValueChangeCallback), Union)
        variants = get_args(ValueChangeCallback)
        self.assertEqual(len(variants), 2)
        for variant in variants:
            self.assertIs(get_origin(variant), AbcCallable)


if __name__ == "__main__":
    unittest.main()
