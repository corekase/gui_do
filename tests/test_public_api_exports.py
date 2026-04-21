import unittest

import gui

from gui import ActionManager
from gui import EventBus
from gui import EventPhase
from gui import EventType
from gui import FocusManager
from gui import GuiEvent
from gui import InvalidationTracker
from gui import ObservableValue
from gui import PresentationModel


EXPECTED_PUBLIC_EXPORTS = {
    "GuiApplication",
    "UiEngine",
    "PanelControl",
    "LabelControl",
    "ButtonControl",
    "ArrowBoxControl",
    "ButtonGroupControl",
    "CanvasControl",
    "CanvasEventPacket",
    "FrameControl",
    "ImageControl",
    "SliderControl",
    "ScrollbarControl",
    "TaskPanelControl",
    "ToggleControl",
    "WindowControl",
    "LayoutAxis",
    "LayoutManager",
    "WindowTilingManager",
    "ActionManager",
    "EventManager",
    "EventBus",
    "FocusManager",
    "EventPhase",
    "EventType",
    "GuiEvent",
    "InvalidationTracker",
    "ObservableValue",
    "PresentationModel",
    "TaskEvent",
    "TaskScheduler",
    "Timers",
    "BuiltInGraphicsFactory",
    "ColorTheme",
}


class PublicApiExportsTests(unittest.TestCase):
    def test_core_api_exports_are_importable(self) -> None:
        self.assertTrue(callable(ActionManager))
        self.assertTrue(callable(EventBus))
        self.assertTrue(callable(FocusManager))
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

    def test_public_all_names_are_resolvable_attributes(self) -> None:
        for export_name in gui.__all__:
            self.assertTrue(hasattr(gui, export_name), f"gui missing attribute for __all__ export: {export_name}")


if __name__ == "__main__":
    unittest.main()
