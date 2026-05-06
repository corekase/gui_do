from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Callable, Optional

from ..telemetry.telemetry import telemetry_collector


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
        self._subscriptions_by_scope: dict[str, set[Subscription]] = defaultdict(set)

    def subscribe(self, topic: str, handler: EventHandler, *, scope: str | None = None) -> Subscription:
        sub = Subscription(topic=str(topic), handler=handler, scope=scope)
        self._subscribers[sub.topic].append(sub)
        if sub.scope is not None:
            self._subscriptions_by_scope[sub.scope].add(sub)
        return sub

    def unsubscribe(self, subscription: Subscription) -> None:
        subs = self._subscribers.get(subscription.topic)
        if not subs:
            return
        # Identity-based remove: only the exact returned subscription object is
        # removed, so duplicate (equal) subscriptions are not accidentally purged.
        # Avoids allocating a new list in the common case.
        for i, s in enumerate(subs):
            if s is subscription:
                del subs[i]
                if not subs:
                    del self._subscribers[subscription.topic]
                scope = subscription.scope
                if scope is not None:
                    scoped = self._subscriptions_by_scope.get(scope)
                    if scoped is not None:
                        scoped.discard(subscription)
                        if not scoped:
                            del self._subscriptions_by_scope[scope]
                return

    def unsubscribe_scope(self, scope: str) -> int:
        """Remove all subscriptions whose scope matches *scope*. Returns the number removed."""
        scoped = self._subscriptions_by_scope.pop(scope, None)
        if not scoped:
            return 0
        # Group subs to remove by topic so we scan each topic list at most once.
        by_topic: dict = {}
        for sub in scoped:
            by_topic.setdefault(sub.topic, set()).add(id(sub))
        removed = 0
        for topic, id_set in by_topic.items():
            subs = self._subscribers.get(topic)
            if not subs:
                continue
            new_subs = [s for s in subs if id(s) not in id_set]
            removed += len(subs) - len(new_subs)
            if new_subs:
                self._subscribers[topic] = new_subs
            else:
                del self._subscribers[topic]
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
        count = len(subscribers)
        collector = telemetry_collector()
        # Snapshot for safe iteration (handlers may mutate the subscriber list).
        # Avoid tuple allocation in the common single-subscriber case.
        snapshot = subscribers if count == 1 else tuple(subscribers)
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
                "subscriber_count": count,
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
