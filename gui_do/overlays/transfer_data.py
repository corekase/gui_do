"""Transfer data — shared clipboard/drag payload surface."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(slots=True)
class TransferData:
    """Portable transfer payload with one or more typed representations."""

    formats: Dict[str, Any] = field(default_factory=dict)
    preferred_format: str = "text/plain"

    def has_format(self, format_name: str) -> bool:
        return str(format_name) in self.formats

    def get(self, format_name: str, default: Any = None) -> Any:
        return self.formats.get(str(format_name), default)

    def set(self, format_name: str, value: Any) -> None:
        self.formats[str(format_name)] = value

    def format_names(self) -> List[str]:
        return sorted(self.formats.keys())


class TransferManager:
    """Coordinates clipboard-like and drag-like data exchange in-process."""

    def __init__(self) -> None:
        self._clipboard: Optional[TransferData] = None
        self._drag: Optional[TransferData] = None

    def set_clipboard(self, data: TransferData) -> None:
        self._clipboard = data

    def get_clipboard(self) -> Optional[TransferData]:
        return self._clipboard

    def clear_clipboard(self) -> None:
        self._clipboard = None

    def begin_drag(self, data: TransferData) -> None:
        self._drag = data

    def current_drag(self) -> Optional[TransferData]:
        return self._drag

    def end_drag(self) -> Optional[TransferData]:
        data = self._drag
        self._drag = None
        return data

    def copy_drag_to_clipboard(self) -> bool:
        if self._drag is None:
            return False
        self._clipboard = self._drag
        return True
