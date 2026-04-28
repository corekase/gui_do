import pygame


class UiEngine:
    """Main loop runner for GuiApplication."""

    def __init__(self, app, target_fps: int = 60) -> None:
        self.app = app
        self.target_fps = max(1, int(target_fps))
        self.clock = pygame.time.Clock()

    @property
    def current_fps(self) -> float:
        """Return the measured FPS of the last clock tick (0.0 before first tick)."""
        return float(self.clock.get_fps())

    def run(self, max_frames: int | None = None) -> int:
        """Run until app.running is set False or an optional frame limit is reached."""
        frame_count = 0
        app = self.app
        clock = self.clock
        target_fps = self.target_fps
        event_get = pygame.event.get
        display_update = pygame.display.update
        display_flip = pygame.display.flip
        try:
            while app.running:
                if max_frames is not None and frame_count >= max_frames:
                    break
                for event in event_get():
                    app.process_event(event)
                    if not app.running:
                        break
                if not app.running:
                    break
                dt_seconds = clock.tick(target_fps) / 1000.0
                app.update(dt_seconds)
                dirty = app.draw()
                if dirty:
                    display_update(dirty)
                else:
                    display_flip()
                frame_count += 1
        finally:
            app.shutdown()
        return frame_count
