import unittest
from collections.abc import Callable as AbcCallable
from typing import get_origin

import gui_do
from tests.contract_test_catalog import PUBLIC_API_EXPORT_ORDER

from gui_do import ActionManager
from gui_do import EventBus
from gui_do import EventPhase
from gui_do import EventType
from gui_do import FocusManager
from gui_do import FontManager
from gui_do import GuiEvent
from gui_do import InvalidationTracker
from gui_do import ObservableValue
from gui_do import PresentationModel
from gui_do import ValueChangeCallback


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
        self.assertFalse(hasattr(gui_do, "MANDEL_STATUS_TOPIC"))
        self.assertFalse(hasattr(gui_do, "MandelStatusEvent"))

    def test_public_all_excludes_demo_symbols(self) -> None:
        exported = set(gui_do.__all__)

        self.assertNotIn("MandelStatusEvent", exported)
        self.assertFalse(any(name.startswith("MANDEL_") for name in exported))
        self.assertFalse(any("mandel" in name.lower() for name in exported))

    def test_public_all_matches_expected_export_surface(self) -> None:
        self.assertEqual(set(gui_do.__all__), EXPECTED_PUBLIC_EXPORTS)

    def test_public_all_matches_expected_export_order(self) -> None:
        self.assertEqual(tuple(gui_do.__all__), PUBLIC_API_EXPORT_ORDER)

    def test_public_all_names_are_resolvable_attributes(self) -> None:
        for export_name in gui_do.__all__:
            self.assertTrue(hasattr(gui_do, export_name), f"gui_do missing attribute for __all__ export: {export_name}")

    def test_value_change_callback_type_alias_export_shape(self) -> None:
        self.assertIs(get_origin(ValueChangeCallback), AbcCallable)


if __name__ == "__main__":
    unittest.main()
