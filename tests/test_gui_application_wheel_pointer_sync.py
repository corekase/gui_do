import unittest
from unittest.mock import patch

import pygame

from gui_do.app.gui_application import GuiApplication


pygame.init()


class TestGuiApplicationWheelPointerSync(unittest.TestCase):
    def test_mouse_wheel_syncs_logical_pointer_from_hardware_when_unlocked(self):
        app = GuiApplication(pygame.Surface((320, 240)))
        app.set_logical_pointer_position((0, 0), apply_constraints=False)

        wheel = pygame.event.Event(pygame.MOUSEWHEEL, {"x": 0, "y": 1})
        with patch("gui_do.app.gui_application.pygame.mouse.get_pos", return_value=(123, 77)):
            app.process_event(wheel)

        self.assertEqual((123, 77), app.logical_pointer_pos)


if __name__ == "__main__":
    unittest.main()
