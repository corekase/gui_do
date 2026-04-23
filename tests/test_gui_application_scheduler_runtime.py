import unittest
from unittest.mock import patch

import pygame
from pygame import Surface

from gui.app.gui_application import GuiApplication


class GuiApplicationSchedulerRuntimeTests(unittest.TestCase):
    def test_scene_scheduler_uses_conservative_worker_count_and_dispatch_budget(self) -> None:
        pygame.init()
        try:
            with patch("gui.core.task_scheduler.os.cpu_count", return_value=4):
                app = GuiApplication(Surface((240, 180)))
            try:
                self.assertEqual(app.scheduler._max_workers, 3)
                self.assertEqual(app.scheduler.get_message_dispatch_time_budget_ms(), 2.0)

                app.update(1.0 / 120.0)
                self.assertEqual(app.scheduler.get_message_dispatch_time_budget_ms(), 1.0)

                app.update(1.0 / 30.0)
                self.assertEqual(app.scheduler.get_message_dispatch_time_budget_ms(), 4.0)

                app.update(0.0)
                self.assertEqual(app.scheduler.get_message_dispatch_time_budget_ms(), 0.5)
            finally:
                app.shutdown()
        finally:
            pygame.quit()


if __name__ == "__main__":
    unittest.main()
