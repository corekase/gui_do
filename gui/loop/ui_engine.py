import pygame


class UiEngine:
    """Main loop runner for GuiApplication."""

    def __init__(self, app, target_fps: int = 60) -> None:
        self.app = app
        self.target_fps = max(1, int(target_fps))
        self.clock = pygame.time.Clock()

    def run(self) -> None:
        """Run until app.running is set False."""
        try:
            while self.app.running:
                self.app.input_state.begin_frame()
                for event in pygame.event.get():
                    self.app.process_event(event)
                dt_seconds = self.clock.tick(self.target_fps) / 1000.0
                self.app.update(dt_seconds)
                self.app.draw()
                pygame.display.flip()
        finally:
            self.app.shutdown()
