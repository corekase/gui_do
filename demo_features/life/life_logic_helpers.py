"""Command dispatch helpers for LifeLogicFeature."""

from __future__ import annotations

from typing import TYPE_CHECKING

from gui_do import FeatureMessage

_KEY_TOPIC = "topic"
_KEY_EVENT = "event"
_KEY_LIFE_CELLS = "life_cells"
_LIFE_LOGIC_TOPIC = "life_logic"
_LIFE_EVENT_STATE = "state"

if TYPE_CHECKING:
    from .life_logic_feature import LifeLogicFeature


def build_command_handlers(feature: LifeLogicFeature) -> dict[str, object]:
    return {
        "reset": feature._handle_reset_command,
        "next": feature._handle_next_command,
        "toggle_cell": feature._handle_toggle_cell_command,
        "snapshot": feature._handle_snapshot_command,
    }


def on_logic_command(feature: LifeLogicFeature, message: FeatureMessage) -> None:
    command = str(message.command)
    handler = feature._command_handlers.get(command)
    if handler is None:
        return
    handler(str(message.sender), message)


def handle_reset_command(feature: LifeLogicFeature, sender_name: str) -> None:
    feature.life_cells = set(feature.DEFAULT_SEED)
    feature._publish_state(sender_name)


def handle_next_command(feature: LifeLogicFeature, sender_name: str) -> None:
    feature.life_cells = feature.next_life_cycle(feature.life_cells)
    feature._publish_state(sender_name)


def handle_toggle_cell_command(feature: LifeLogicFeature, sender_name: str, message: FeatureMessage) -> None:
    cell = message.get("cell")
    if isinstance(cell, tuple) and len(cell) == 2:
        normalized_cell = (int(cell[0]), int(cell[1]))
        if normalized_cell in feature.life_cells:
            feature.life_cells.remove(normalized_cell)
        else:
            feature.life_cells.add(normalized_cell)
        feature._publish_state(sender_name)


def handle_snapshot_command(feature: LifeLogicFeature, sender_name: str) -> None:
    feature._publish_state(sender_name)


def publish_state(feature: LifeLogicFeature, target_feature_name: str) -> None:
    feature.send_message(
        target_feature_name,
        {
            _KEY_TOPIC: _LIFE_LOGIC_TOPIC,
            _KEY_EVENT: _LIFE_EVENT_STATE,
            _KEY_LIFE_CELLS: set(feature.life_cells),
        },
    )


__all__ = [
    "build_command_handlers",
    "handle_next_command",
    "handle_reset_command",
    "handle_snapshot_command",
    "handle_toggle_cell_command",
    "on_logic_command",
    "publish_state",
]
