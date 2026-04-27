from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Optional

from .telemetry import telemetry_collector


EventHandler = Callable[[object], None]


@dataclass(frozen=True)
class Subscription:
    topic: str
    handler: EventHandler
    scope: Optional[str]


class EventBus:
    """Simple scoped publish-subscribe bus for non-input UI events."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Subscription]] = defaultdict(list)

    def subscribe(self, topic: str, handler: EventHandler, *, scope: str | None = None) -> Subscription:
        sub = Subscription(topic=str(topic), handler=handler, scope=scope)
        self._subscribers[sub.topic].append(sub)
        return sub

    def unsubscribe(self, subscription: Subscription) -> None:
        subs = self._subscribers.get(subscription.topic)
        if not subs:
            return
        self._subscribers[subscription.topic] = [candidate for candidate in subs if candidate != subscription]

    def unsubscribe_scope(self, scope: str) -> int:
        """Remove all subscriptions whose scope matches *scope*. Returns the number removed."""
        removed = 0
        for topic in list(self._subscribers.keys()):
            before = self._subscribers[topic]
            after = [s for s in before if s.scope != scope]
            removed += len(before) - len(after)
            self._subscribers[topic] = after
        return removed

    def subscriber_count(self, topic: str | None = None) -> int:
        """Return the total number of active subscriptions, optionally filtered to *topic*."""
        if topic is not None:
            return len(self._subscribers.get(str(topic), []))
        return sum(len(subs) for subs in self._subscribers.values())

    def publish(self, topic: str, payload: object = None, *, scope: str | None = None) -> None:
        topic_name = str(topic)
        subscribers = self._subscribers.get(topic_name)
        if not subscribers:
            return
        # Snapshot for safe iteration (handlers may mutate the subscriber list).
        snapshot = list(subscribers)
        collector = telemetry_collector()
        # Fast path: skip all span/metadata overhead when telemetry is off.
        if not collector._enabled:  # noqa: SLF001 — intentional lock-free check
            for sub in snapshot:
                if sub.scope is None or sub.scope == scope:
                    sub.handler(payload)
            return
        with collector.span(
            "event_bus",
            "publish",
            metadata={
                "topic": topic_name,
                "scope": "" if scope is None else str(scope),
                "subscriber_count": len(snapshot),
            },
        ):
            for sub in snapshot:
                if sub.scope is None or sub.scope == scope:
                    with collector.span(
                        "event_bus",
                        "publish_handler",
                        metadata={
                            "topic": topic_name,
                            "scope": "" if scope is None else str(scope),
                            "subscriber_scope": "" if sub.scope is None else str(sub.scope),
                        },
                    ):
                        sub.handler(payload)

    def once(self, topic: str, handler: EventHandler, *, scope: str | None = None) -> Subscription:
        """Subscribe to *topic* and automatically unsubscribe after the first delivery.

        Returns the ``Subscription`` in case the caller wants to cancel it before
        the first event fires.
        """
        sub_holder: list[Subscription] = []

        def _one_shot_wrapper(payload: object) -> None:
            self.unsubscribe(sub_holder[0])
            handler(payload)

        sub = self.subscribe(topic, _one_shot_wrapper, scope=scope)
        sub_holder.append(sub)
        return sub
