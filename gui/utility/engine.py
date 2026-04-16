import pygame
from typing import Hashable, List, Optional
from .guimanager import GuiManager
from .scheduler import Scheduler, TaskEvent, TaskKind, Timers
from .statemanager import StateManager

class Engine:
    """Main application event loop controller.

    Orchestrates the complete application lifecycle including event processing,
    timer updates, task scheduling, and rendering. Works with StateManager to
    support multiple application contexts (screens/states).
    """
    def __init__(self, state_manager: StateManager) -> None:
        """Initialize the engine.

        Args:
            state_manager: StateManager to control application state transitions.
        """
        if not isinstance(state_manager, StateManager):
            raise TypeError('state_manager must be a StateManager instance')
        self.state_manager: StateManager = state_manager
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.fps: int = 60
        if self.fps <= 0:
            raise ValueError('fps must be > 0')

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
                gui: Optional[GuiManager] = self.state_manager.get_active_gui()
                if gui is None:
                    break
                scheduler: Scheduler = gui.scheduler
                timers: Timers = gui.timers
                # Phase 1: Preamble
                gui.run_preamble()
                # Phase 2: Update timers
                if timers:
                    timers.timer_updates(pygame.time.get_ticks())
                # Phase 3: Process events
                for event in gui.events():
                    gui.dispatch_event(event)
                # Phase 4: Update scheduler (tasks) and get finished tasks
                finished_task_ids: List[Hashable] = scheduler.update()
                # Phase 5: Dispatch task-finished events
                for task_id in finished_task_ids:
                    task_event: TaskEvent = scheduler.event(TaskKind.Finished, task_id)
                    gui.dispatch_event(task_event)
                # Dispatch task-failed events
                for task_id, error_message in scheduler.get_failed_tasks():
                    task_event = scheduler.event(TaskKind.Failed, task_id, error_message)
                    gui.dispatch_event(task_event)
                # Phase 6: Postamble
                gui.run_postamble()
                # Phase 7: Render
                gui.draw_gui()
                pygame.display.flip()
                # Undo changes if using buffering
                if gui.buffered:
                    gui.undraw_gui()
                # Control frame rate
                self.clock.tick(self.fps)
