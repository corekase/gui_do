"""Logic companion for the Life demo feature."""

from __future__ import annotations

from typing import Set, Tuple

from gui_do import FeatureMessage, LogicFeature
from .life_logic_helpers import (
	build_command_handlers as build_command_handlers_helper,
	handle_next_command as handle_next_command_helper,
	handle_reset_command as handle_reset_command_helper,
	handle_snapshot_command as handle_snapshot_command_helper,
	handle_toggle_cell_command as handle_toggle_cell_command_helper,
	on_logic_command as on_logic_command_helper,
	publish_state as publish_state_helper,
)

class LifeLogicFeature(LogicFeature):
	"""Domain logic service for Conway life cycles."""

	DEFAULT_SEED: Set[Tuple[int, int]] = {
		(0, 0),
		(1, 0),
		(-1, 0),
		(0, -1),
		(1, -2),
	}
	NEIGHBOURS = (
		(-1, -1), (-1, 0), (-1, 1),
		(0, -1),           (0, 1),
		(1, -1),  (1, 0),  (1, 1),
	)

	def __init__(self) -> None:
		super().__init__("life_simulation_logic", scene_name="main")
		self.life_cells: Set[Tuple[int, int]] = set(self.DEFAULT_SEED)
		self._command_handlers = build_command_handlers_helper(self)

	@classmethod
	def next_life_cycle(cls, cells: Set[Tuple[int, int]]) -> Set[Tuple[int, int]]:
		new_life: Set[Tuple[int, int]] = set()
		for cell in cells:
			pop = cls._life_population(cells, cell)
			if pop in (2, 3):
				new_life.add(cell)
			for dx, dy in cls.NEIGHBOURS:
				n_cell = (cell[0] + dx, cell[1] + dy)
				if cls._life_population(cells, n_cell) == 3:
					new_life.add(n_cell)
		return new_life

	@classmethod
	def _life_population(cls, cells: Set[Tuple[int, int]], cell: Tuple[int, int]) -> int:
		count = 0
		for dx, dy in cls.NEIGHBOURS:
			if (cell[0] + dx, cell[1] + dy) in cells:
				count += 1
		return count

	def on_logic_command(self, _host, message: FeatureMessage) -> None:
		on_logic_command_helper(self, message)

	def _handle_reset_command(self, sender_name: str, _message: FeatureMessage) -> None:
		handle_reset_command_helper(self, sender_name)

	def _handle_next_command(self, sender_name: str, _message: FeatureMessage) -> None:
		handle_next_command_helper(self, sender_name)

	def _handle_toggle_cell_command(self, sender_name: str, message: FeatureMessage) -> None:
		handle_toggle_cell_command_helper(self, sender_name, message)

	def _handle_snapshot_command(self, sender_name: str, _message: FeatureMessage) -> None:
		handle_snapshot_command_helper(self, sender_name)

	def _publish_state(self, target_feature_name: str) -> None:
		publish_state_helper(self, target_feature_name)


__all__ = ["LifeLogicFeature"]
