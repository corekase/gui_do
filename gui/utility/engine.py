import pygame
from typing import Optional, Callable, Any
from ..guimanager import GuiManager
from .scheduler import Scheduler, TaskKind
from .statemanager import StateManager

class Engine:
    def __init__(self, state_manager: 'StateManager') -> None:
        self.state_manager = state_manager
        self.clock = pygame.time.Clock()
        self.fps = 60

    def run(self) -> None:
        """
        Main application loop using StateManager contexts.

        This loop manages the complete application lifecycle:
        1. Preamble: pre-frame setup (if defined)
        2. Update Timers: process timer events
        3. Handle Events: process pygame/gui events
        4. Scheduler Update: process tasks
        5. Dispatch Task Events: send finished task events to handler
        6. Postamble: post-frame cleanup (if defined)
        7. Render: draw GUI and flip display
        """
        with self.state_manager:
            while self.state_manager.is_running:
                active_context = self.state_manager.get_active_context()
                if not active_context:
                    break

                gui, scheduler, timers, preamble, event_handler, postamble = active_context

                # Phase 1: Preamble
                preamble()

                # Phase 2: Update timers
                if timers:
                    timers.timer_updates(pygame.time.get_ticks())

                # Phase 3: Process events
                for event in gui.events():
                    event_handler(event)

                # Phase 4: Update scheduler (tasks) and get finished tasks
                finished_task_ids = scheduler.update()

                # Phase 5: Dispatch task-finished events
                for task_id in finished_task_ids:
                    task_event = scheduler.event(TaskKind.Finished, task_id)
                    event_handler(task_event)

                # Phase 6: Postamble
                postamble()

                # Phase 7: Render
                gui.draw_gui()
                pygame.display.flip()

                # Undo changes if using buffering
                if gui.buffered:
                    gui.undraw_gui()

                # Control frame rate
                self.clock.tick(self.fps)
