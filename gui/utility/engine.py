import sys
import pygame
from typing import Hashable, List, Optional
from .guimanager import GuiManager
from .scheduler import Scheduler, TaskEvent, TaskKind, Timers
from .statemanager import StateManager

class Engine:
    """Owns the frame loop for the active GUI context."""

    def __init__(self, state_manager: StateManager) -> None:
        """Create an engine bound to a state manager."""
        if not isinstance(state_manager, StateManager):
            raise TypeError('state_manager must be a StateManager instance')
        self.state_manager: StateManager = state_manager
        self.clock: pygame.time.Clock = pygame.time.Clock()
        self.fps: int = 60
        if self.fps <= 0:
            raise ValueError('fps must be > 0')

    def run(self) -> None:
        """Run frames until no active context remains or shutdown is requested."""
        exit_code = 0
        try:
            with self.state_manager:
                while self.state_manager.is_running:
                    gui: Optional[GuiManager] = self.state_manager.get_active_gui()
                    if gui is None:
                        break
                    scheduler: Scheduler = gui.scheduler
                    timers: Timers = gui.timers
                    gui.run_preamble()
                    if timers:
                        timers.timer_updates(pygame.time.get_ticks())
                    for event in gui.events():
                        gui.dispatch_event(event)
                    finished_task_ids: List[Hashable] = scheduler.update()
                    for task_id in finished_task_ids:
                        task_event: TaskEvent = scheduler.event(TaskKind.Finished, task_id)
                        gui.dispatch_event(task_event)
                    for task_id, error_message in scheduler.get_failed_tasks():
                        task_event = scheduler.event(TaskKind.Failed, task_id, error_message)
                        gui.dispatch_event(task_event)
                    gui.run_postamble()
                    gui.draw_gui()
                    pygame.display.flip()
                    if gui.buffered:
                        gui.undraw_gui()
                    self.clock.tick(self.fps)
        except Exception:
            exit_code = 1
            raise
        finally:
            pygame.quit()
        sys.exit(exit_code)
