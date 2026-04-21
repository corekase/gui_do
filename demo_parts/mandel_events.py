from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


MANDEL_STATUS_TOPIC = "demo.mandel.status"
MANDEL_STATUS_SCOPE = "main"

MANDEL_KIND_IDLE = "idle"
MANDEL_KIND_CLEARED = "cleared"
MANDEL_KIND_RUNNING_ITERATIVE = "running_iterative"
MANDEL_KIND_RUNNING_RECURSIVE = "running_recursive"
MANDEL_KIND_RUNNING_ONE_SPLIT = "running_one_split"
MANDEL_KIND_RUNNING_FOUR_SPLIT = "running_four_split"
MANDEL_KIND_FAILED = "failed"
MANDEL_KIND_COMPLETE = "complete"
MANDEL_KIND_STATUS = "status"


@dataclass(frozen=True)
class MandelStatusEvent:
    kind: str
    detail: Optional[str] = None

    def to_payload(self) -> dict[str, str]:
        payload = {"kind": str(self.kind)}
        if self.detail is not None:
            payload["detail"] = str(self.detail)
        return payload

    @classmethod
    def from_payload(cls, payload) -> "MandelStatusEvent":
        if isinstance(payload, MandelStatusEvent):
            return payload
        if isinstance(payload, dict):
            kind = str(payload.get("kind", MANDEL_KIND_STATUS))
            detail = payload.get("detail")
            if detail is not None:
                detail = str(detail)
            return cls(kind=kind, detail=detail)
        return cls(kind=MANDEL_KIND_STATUS, detail=str(payload))
