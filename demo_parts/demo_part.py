"""Demo-specific Part base with optional lifecycle extension points."""

from __future__ import annotations

from part_system import Part


class DemoPart(Part):
    """Base class for gui_do demo parts.

    Extends the generic Part with demo-oriented setup hooks so the demo can
    remain concise while using managed Part lifecycle orchestration.
    """

    def build(self, demo) -> None:
        """Create and attach this feature's controls/windows onto the demo scene."""
        return None

    def bind_runtime(self, demo) -> None:
        """Register feature-specific runtime hooks (actions, subscriptions, limits)."""
        return None

    def configure_accessibility(self, demo, tab_index_start: int) -> int:
        """Configure tab order/accessibility and return the next tab index."""
        return int(tab_index_start)

    def on_post_frame(self, demo) -> None:
        """Backward-compatible alias for frame-end reconciliation."""
        return None

    def postamble(self, host) -> None:
        """Map generic Part postamble into the demo-specific frame-end hook."""
        self.on_post_frame(host)
