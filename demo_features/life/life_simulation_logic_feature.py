"""Logic companion for the Life demo feature."""

from __future__ import annotations

from typing import Set, Tuple

from gui_do import FeatureMessage, LogicFeature


_KEY_TOPIC = "topic"
_KEY_EVENT = "event"
_KEY_LIFE_CELLS = "life_cells"
_LIFE_LOGIC_TOPIC = "life_logic"
_LIFE_EVENT_STATE = "state"


class LifeSimulationLogicFeature(LogicFeature):
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
		self._command_handlers = {
			"reset": self._handle_reset_command,
			"next": self._handle_next_command,
			"toggle_cell": self._handle_toggle_cell_command,
			"snapshot": self._handle_snapshot_command,
		}

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
		command = str(message.command)
		handler = self._command_handlers.get(command)
		if handler is None:
			return
		handler(str(message.sender), message)

	def _handle_reset_command(self, sender_name: str, _message: FeatureMessage) -> None:
		self.life_cells = set(self.DEFAULT_SEED)
		self._publish_state(sender_name)

	def _handle_next_command(self, sender_name: str, _message: FeatureMessage) -> None:
		self.life_cells = self.next_life_cycle(self.life_cells)
		self._publish_state(sender_name)

	def _handle_toggle_cell_command(self, sender_name: str, message: FeatureMessage) -> None:
		cell = message.get("cell")
		if isinstance(cell, tuple) and len(cell) == 2:
			normalized_cell = (int(cell[0]), int(cell[1]))
			if normalized_cell in self.life_cells:
				self.life_cells.remove(normalized_cell)
			else:
				self.life_cells.add(normalized_cell)
			self._publish_state(sender_name)

	def _handle_snapshot_command(self, sender_name: str, _message: FeatureMessage) -> None:
		self._publish_state(sender_name)

	def _publish_state(self, target_feature_name: str) -> None:
		self.send_message(
			target_feature_name,
			{
				_KEY_TOPIC: _LIFE_LOGIC_TOPIC,
				_KEY_EVENT: _LIFE_EVENT_STATE,
				_KEY_LIFE_CELLS: set(self.life_cells),
			},
		)


__all__ = ["LifeSimulationLogicFeature"]
