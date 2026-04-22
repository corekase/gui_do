"""Feature contracts for composing demo feature modules."""

from __future__ import annotations

from typing import Protocol


class DemoPart(Protocol):
    """Protocol for a self-contained demo feature module."""

    name: str

    def build(self, demo) -> None:
        """Create and attach this feature's controls/windows onto the demo scene."""

    def bind_runtime(self, demo) -> None:
        """Register feature-specific runtime hooks (actions, subscriptions, limits)."""

    def configure_accessibility(self, demo, tab_index_start: int) -> int:
        """Configure tab order/accessibility and return the next tab index."""

    def on_post_frame(self, demo) -> None:
        """Run feature-specific end-of-frame reconciliation logic."""
