import unittest

from gui import ActionManager
from gui import EventBus
from gui import EventPhase
from gui import EventType
from gui import FocusManager
from gui import GuiEvent
from gui import InvalidationTracker
from gui import ObservableValue
from gui import PresentationModel


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


if __name__ == "__main__":
    unittest.main()
