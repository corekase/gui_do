from typing import Callable, Dict, List, Optional, TYPE_CHECKING
from .constants import InteractiveState

if TYPE_CHECKING:
    from ..widgets.buttongroup import ButtonGroup

class ButtonGroupMediator:
    """Mediator coordinating mutually exclusive selection per button group."""

    def __init__(self, is_registered: Callable[["ButtonGroup"], bool]) -> None:
        self._is_registered = is_registered
        self._groups: Dict[str, List["ButtonGroup"]] = {}
        self._selections: Dict[str, "ButtonGroup"] = {}

    def _prune(self, group: str) -> None:
        buttons = self._groups.get(group)
        if buttons is None:
            return
        deduped: List["ButtonGroup"] = []
        for button in buttons:
            if button in deduped:
                continue
            if self._is_registered(button):
                deduped.append(button)
        self._groups[group] = deduped
        if len(deduped) == 0:
            self._groups.pop(group, None)
            self._selections.pop(group, None)
            return
        selected = self._selections.get(group)
        if selected not in deduped:
            selected = deduped[0]
            self._selections[group] = selected
        for button in deduped:
            if button is selected:
                button.state = InteractiveState.Armed
            elif button.state == InteractiveState.Armed:
                button.state = InteractiveState.Idle

    def register(self, group: str, button: "ButtonGroup") -> None:
        self._prune(group)
        if group not in self._groups:
            self._groups[group] = []
            self._selections[group] = button
        if button in self._groups[group]:
            return
        self._groups[group].append(button)

    def select(self, group: str, button: "ButtonGroup") -> None:
        self._prune(group)
        if not self._is_registered(button):
            return
        previous = self._selections.get(group)
        if previous is not None and previous is not button:
            previous.state = InteractiveState.Idle
        self._selections[group] = button

    def get_selection(self, group: str) -> Optional["ButtonGroup"]:
        self._prune(group)
        return self._selections.get(group)

    def clear(self) -> None:
        self._groups.clear()
        self._selections.clear()
