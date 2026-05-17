"""
Generalized status event and publisher base.
User code only specifies payload; event wiring is automatic.
"""

from __future__ import annotations


class StatusEventBase:
    """Typed, transport-safe status event model.

    Supports both compact construction with ``kind/detail`` and legacy raw payload
    construction. Subclasses can override ``DEFAULT_KIND``.
    """

    DEFAULT_KIND = "status"

    def __init__(
        self,
        payload=None,
        *,
        kind: str | None = None,
        detail: str | None = None,
        **extra,
    ):
        resolved_kind = str(kind if kind is not None else self.DEFAULT_KIND)
        self.kind = resolved_kind
        self.detail = None if detail is None else str(detail)
        self.extra = dict(extra)

        if payload is None:
            merged = {"kind": self.kind}
            if self.detail is not None:
                merged["detail"] = self.detail
            merged.update(self.extra)
            self.payload = merged
        else:
            self.payload = payload

    def to_payload(self) -> dict:
        payload = {"kind": str(self.kind)}
        if self.detail is not None:
            payload["detail"] = str(self.detail)
        payload.update(self.extra)
        return payload

    @classmethod
    def from_payload(cls, payload):
        if isinstance(payload, cls):
            return payload
        if isinstance(payload, dict):
            data = dict(payload)
            kind = str(data.pop("kind", cls.DEFAULT_KIND))
            detail = data.pop("detail", None)
            if detail is not None:
                detail = str(detail)
            return cls(kind=kind, detail=detail, **data)
        return cls(kind=cls.DEFAULT_KIND, detail=str(payload))

    def serialize(self):
        return str(self.to_payload())

class StatusEventPublisher:
    def __init__(self):
        self._subscribers = []
    def subscribe(self, handler):
        self._subscribers.append(handler)
    def publish(self, event):
        for handler in self._subscribers:
            handler(event)
