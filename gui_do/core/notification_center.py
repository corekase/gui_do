"""NotificationCenter — persistent EventBus-backed activity log."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Callable, List, Optional, TYPE_CHECKING

from .toast_manager import ToastSeverity
from .presentation_model import ObservableValue

if TYPE_CHECKING:
    from .event_bus import EventBus


@dataclass
class NotificationRecord:
    """A single notification entry stored in the :class:`NotificationCenter`.

    Attributes:
        message: The notification body text.
        title: Optional short title / heading for the notification.
        severity: Reuses :class:`~gui_do.ToastSeverity` for visual
            classification (INFO, WARNING, ERROR, SUCCESS).
        topic: EventBus topic that produced this notification.
        timestamp: Creation time as an ISO-8601 string.
        read: ``False`` until the user has viewed the notification.
        data: Optional application payload carried alongside the message.
    """

    message: str
    title: str = ""
    severity: ToastSeverity = ToastSeverity.INFO
    topic: str = ""
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat(timespec="seconds"))
    read: bool = False
    data: object = None


class NotificationCenter:
    """Persistent, bounded activity log backed by the :class:`~gui_do.EventBus`.

    Subscribe to one or more EventBus topics and the center automatically
    creates a :class:`NotificationRecord` for each matching message.  The
    *unread_count* and *records* properties are :class:`~gui_do.ObservableValue`
    instances so they can drive badge labels or list views reactively.

    Usage::

        nc = NotificationCenter(app.events, max_records=200)
        nc.subscribe("file.saved", severity=ToastSeverity.SUCCESS)
        nc.subscribe("render.failed", severity=ToastSeverity.ERROR)

        # Bind a label to show unread count:
        nc.unread_count.on_change(lambda v: badge_label.__setattr__("text", str(v)))

        # Manually add a record:
        nc.add(NotificationRecord("Build succeeded", title="Build", severity=ToastSeverity.SUCCESS))
    """

    def __init__(
        self,
        event_bus: Optional["EventBus"] = None,
        *,
        max_records: int = 500,
    ) -> None:
        self._event_bus: Optional["EventBus"] = event_bus
        self._max_records: int = max(1, int(max_records))
        self._subscriptions: List[str] = []  # unsubscribe tokens / topic keys
        self._severity_map: dict[str, ToastSeverity] = {}
        self._title_map: dict[str, str] = {}
        # Public reactive state
        self._records_list: List[NotificationRecord] = []
        self.records: ObservableValue[List[NotificationRecord]] = ObservableValue([])
        self.unread_count: ObservableValue[int] = ObservableValue(0)

    # ------------------------------------------------------------------
    # Subscription
    # ------------------------------------------------------------------

    def subscribe(
        self,
        topic: str,
        *,
        severity: ToastSeverity = ToastSeverity.INFO,
        title: str = "",
    ) -> None:
        """Subscribe to *topic* on the EventBus.

        Incoming messages are converted to :class:`NotificationRecord` objects.
        *severity* and *title* are defaults for records from this topic; they
        can be overridden by message payload keys ``severity`` and ``title``.
        """
        if self._event_bus is None:
            return
        topic = str(topic)
        self._severity_map[topic] = severity
        self._title_map[topic] = title

        def _handler(payload: object) -> None:
            self._on_bus_message(topic, payload)

        self._event_bus.subscribe(topic, _handler)
        self._subscriptions.append(topic)

    def unsubscribe_all(self) -> None:
        """Remove all EventBus subscriptions."""
        self._subscriptions.clear()
        self._severity_map.clear()
        self._title_map.clear()

    # ------------------------------------------------------------------
    # Record management
    # ------------------------------------------------------------------

    def add(self, record: NotificationRecord) -> None:
        """Manually add a :class:`NotificationRecord`."""
        self._records_list.insert(0, record)
        if len(self._records_list) > self._max_records:
            self._records_list.pop()
        self.records.value = list(self._records_list)
        unread = sum(1 for r in self._records_list if not r.read)
        self.unread_count.value = unread

    def mark_all_read(self) -> None:
        """Mark every record as read and reset the unread count to 0."""
        for r in self._records_list:
            r.read = True
        self.unread_count.value = 0
        self.records.value = list(self._records_list)

    def mark_read(self, record: NotificationRecord) -> None:
        """Mark a single record as read."""
        if not record.read:
            record.read = True
            unread = sum(1 for r in self._records_list if not r.read)
            self.unread_count.value = unread
            self.records.value = list(self._records_list)

    def clear(self) -> None:
        """Remove all stored records."""
        self._records_list.clear()
        self.records.value = []
        self.unread_count.value = 0

    @property
    def all_records(self) -> List[NotificationRecord]:
        """Return a snapshot of all records (newest first)."""
        return list(self._records_list)

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _on_bus_message(self, topic: str, payload: object) -> None:
        """Convert an EventBus message to a NotificationRecord."""
        message = ""
        title = self._title_map.get(topic, "")
        severity = self._severity_map.get(topic, ToastSeverity.INFO)
        data = payload

        if isinstance(payload, dict):
            message = str(payload.get("message", payload.get("text", str(payload))))
            title = str(payload.get("title", title))
            sev_raw = payload.get("severity")
            if isinstance(sev_raw, ToastSeverity):
                severity = sev_raw
            elif isinstance(sev_raw, str):
                try:
                    severity = ToastSeverity[sev_raw.upper()]
                except KeyError:
                    pass
        elif isinstance(payload, str):
            message = payload
        else:
            message = str(payload)

        record = NotificationRecord(
            message=message,
            title=title,
            severity=severity,
            topic=topic,
            data=data,
        )
        self.add(record)
