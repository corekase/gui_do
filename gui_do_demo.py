from gui_do import bootstrap_host_application

from demo_features.demo_config import DEMO_BOOTSTRAP_CONFIG


class GuiDoDemo:
    """Interactive demo app showcasing gui_do controls and scene workflows."""

    def __init__(self) -> None:
        bootstrap_host_application(self, DEMO_BOOTSTRAP_CONFIG)

    def run(self) -> int:
        return self.app.run_entrypoint(target_fps=DEMO_BOOTSTRAP_CONFIG.target_fps)


def main() -> None:
    """Entrypoint for running the gui_do demo as a script."""
    GuiDoDemo().run()


if __name__ == "__main__":
    main()
