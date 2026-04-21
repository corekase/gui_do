from __future__ import annotations

import sys
import pygame
from typing import Any, Callable, Hashable, List, Optional
from .gui_manager import GuiManager
from .scheduler import Scheduler, TaskEvent, TaskKind, Timers
from .state_manager import StateManager

class Engine:
    """Owns the frame loop for the active GUI context."""

    def __init__(
        self,
        state_manager: StateManager,
        fps: int = 60,
        *,
        clock: Optional[Any] = None,
        ticks_provider: Optional[Callable[[], int]] = None,
        display_flip: Optional[Callable[[], None]] = None,
        quit_callable: Optional[Callable[[], None]] = None,
        exit_callable: Optional[Callable[[int], None]] = None,
        exit_on_finish: bool = True,
    ) -> None:
        """Create an engine bound to a state manager."""
        if not isinstance(state_manager, StateManager):
            raise TypeError('state_manager must be a StateManager instance')
        if not isinstance(fps, int) or fps <= 0:
            raise ValueError('fps must be > 0')
        if not isinstance(exit_on_finish, bool):
            raise TypeError('exit_on_finish must be a bool')
        self.state_manager: StateManager = state_manager
        self.clock: Any = clock or pygame.time.Clock()
        try:
            tick = self.clock.tick
        except AttributeError as exc:
            raise TypeError('clock must provide a callable tick(fps) method') from exc
        if not callable(tick):
            raise TypeError('clock must provide a callable tick(fps) method')
        self.fps: int = fps
        self._ticks_provider: Callable[[], int] = ticks_provider or pygame.time.get_ticks
        self._display_flip: Callable[[], None] = display_flip or pygame.display.flip
        self._quit_callable: Callable[[], None] = quit_callable or pygame.quit
        self._exit_callable: Callable[[int], None] = exit_callable or sys.exit
        self._exit_on_finish: bool = exit_on_finish
        if not callable(self._ticks_provider):
            raise TypeError('ticks_provider must be callable')
        if not callable(self._display_flip):
            raise TypeError('display_flip must be callable')
        if not callable(self._quit_callable):
            raise TypeError('quit_callable must be callable')
        if not callable(self._exit_callable):
            raise TypeError('exit_callable must be callable')

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
                        timers.timer_updates(self._ticks_provider())
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
                    gui._draw_gui()
                    self._display_flip()
                    if gui.buffered:
                        gui._undraw_gui()
                    self.clock.tick(self.fps)
        except Exception:
            exit_code = 1
            raise
        finally:
            self._quit_callable()
        if self._exit_on_finish:
            self._exit_callable(exit_code)
