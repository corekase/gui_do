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
        try:
            while self.app.running:
                if max_frames is not None and frame_count >= max_frames:
                    break
                for event in pygame.event.get():
                    self.app.process_event(event)
                    if not self.app.running:
                        break
                if not self.app.running:
                    break
                dt_seconds = self.clock.tick(self.target_fps) / 1000.0
                self.app.update(dt_seconds)
                dirty = self.app.draw()
                if dirty:
                    pygame.display.update(dirty)
                else:
                    pygame.display.flip()
                frame_count += 1
        finally:
            self.app.shutdown()
        return frame_count
