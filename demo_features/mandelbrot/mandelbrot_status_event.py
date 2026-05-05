"""Typed status payload model for the Mandelbrot demo feature."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


MANDEL_KIND_STATUS = "status"


@dataclass(frozen=True)
class MandelStatusEvent:
	"""Typed status payload used for Mandelbrot status bus publication."""

	kind: str
	detail: Optional[str] = None

	def to_payload(self) -> dict[str, str]:
		"""Serialize event fields into a transport-safe dictionary payload."""
		payload = {"kind": str(self.kind)}
		if self.detail is not None:
			payload["detail"] = str(self.detail)
		return payload

	@classmethod
	def from_payload(cls, payload) -> "MandelStatusEvent":
		"""Build a status event from event instance, dict payload, or raw value."""
		if isinstance(payload, MandelStatusEvent):
			return payload
		if isinstance(payload, dict):
			kind = str(payload.get("kind", MANDEL_KIND_STATUS))
			detail = payload.get("detail")
			if detail is not None:
				detail = str(detail)
			return cls(kind=kind, detail=detail)
		return cls(kind=MANDEL_KIND_STATUS, detail=str(payload))


__all__ = ["MANDEL_KIND_STATUS", "MandelStatusEvent"]
