from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Optional


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
        for sub in list(self._subscribers.get(str(topic), ())):
            if sub.scope is None or sub.scope == scope:
                sub.handler(payload)
