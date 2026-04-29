"""DataCache — typed LRU cache with reactive invalidation.

A thread-safe LRU (Least Recently Used) cache with optional TTL (time-to-live)
per entry.  Integrates with :class:`~gui_do.Signal` for reactive cache events.

Usage::

    from gui_do import DataCache, CacheStats

    cache: DataCache[str, dict] = DataCache(max_size=256)

    # Basic operations:
    cache.put("user:42", user_data)
    val = cache.get("user:42")       # → user_data or None
    cache.invalidate("user:42")
    cache.invalidate_all()

    # With a factory (load-on-miss):
    user = cache.get_or_load("user:42", lambda: fetch_user(42))

    # With TTL (seconds):
    cache2: DataCache[str, bytes] = DataCache(max_size=100, ttl_seconds=30.0)

    # React to eviction/invalidation:
    cache.on_evicted.subscribe(lambda kv: print("evicted", kv[0]))
    cache.on_invalidated.subscribe(lambda k: print("invalidated", k))

    # Stats:
    stats = cache.stats()
    print(stats.hit_rate)
"""
from __future__ import annotations

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Callable, Generic, Optional, Tuple, TypeVar

from ..events.signal import Signal

K = TypeVar("K")
V = TypeVar("V")


# ---------------------------------------------------------------------------
# CacheStats
# ---------------------------------------------------------------------------


@dataclass
class CacheStats:
    """Snapshot of :class:`DataCache` performance counters.

    Attributes
    ----------
    size:
        Current number of entries.
    hits:
        Number of successful cache lookups since creation.
    misses:
        Number of cache misses since creation.
    evictions:
        Number of entries evicted due to size limit.
    invalidations:
        Number of entries explicitly invalidated.
    """
    size: int
    hits: int
    misses: int
    evictions: int
    invalidations: int

    @property
    def total_lookups(self) -> int:
        return self.hits + self.misses

    @property
    def hit_rate(self) -> float:
        """Fraction of lookups that were hits.  ``0.0`` if no lookups."""
        total = self.total_lookups
        return self.hits / total if total > 0 else 0.0


# ---------------------------------------------------------------------------
# _CacheEntry — internal
# ---------------------------------------------------------------------------


class _CacheEntry(Generic[V]):
    __slots__ = ("value", "expires_at")

    def __init__(self, value: V, expires_at: Optional[float]) -> None:
        self.value = value
        self.expires_at = expires_at


# ---------------------------------------------------------------------------
# DataCache
# ---------------------------------------------------------------------------


class DataCache(Generic[K, V]):
    """Typed LRU cache with optional TTL and reactive signals.

    Parameters
    ----------
    max_size:
        Maximum number of entries.  When exceeded, the least recently used
        entry is evicted.
    ttl_seconds:
        Optional per-entry time-to-live in seconds.  Expired entries are
        evicted lazily on next access.  ``None`` means entries never expire.
    factory:
        Optional default factory used by :meth:`get_or_load`.  Must be a
        callable that accepts the key and returns a value.

    Thread safety
    -------------
    All public methods are protected by an internal lock and safe to call
    from background threads or the main frame thread.
    """

    on_evicted: Signal = Signal()
    """Emitted with ``(key, value)`` when an entry is evicted by LRU pressure."""

    on_invalidated: Signal = Signal()
    """Emitted with ``key`` when an entry is explicitly invalidated."""

    def __init__(
        self,
        max_size: int = 256,
        *,
        ttl_seconds: Optional[float] = None,
        factory: Optional[Callable[[K], V]] = None,
    ) -> None:
        if max_size <= 0:
            raise ValueError(f"max_size must be > 0, got {max_size}")
        self._max_size = max_size
        self._ttl = ttl_seconds
        self._factory = factory
        self._store: OrderedDict[K, _CacheEntry[V]] = OrderedDict()
        self._lock = threading.Lock()
        self._hits = 0
        self._misses = 0
        self._evictions = 0
        self._invalidations = 0

    # ------------------------------------------------------------------
    # Properties
    # ------------------------------------------------------------------

    @property
    def max_size(self) -> int:
        return self._max_size

    # ------------------------------------------------------------------
    # Core operations
    # ------------------------------------------------------------------

    def get(self, key: K) -> Optional[V]:
        """Return the cached value for *key*, or ``None`` on miss/expiry."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                self._misses += 1
                return None
            if self._is_expired(entry):
                del self._store[key]
                self._misses += 1
                return None
            # Move to end (most recently used)
            self._store.move_to_end(key)
            self._hits += 1
            return entry.value

    def get_or_load(self, key: K, loader: Optional[Callable[[], V]] = None) -> V:
        """Return cached value or compute it via *loader* (or default factory).

        Parameters
        ----------
        key:
            The cache key.
        loader:
            Zero-argument callable returning the value.  If ``None``, the
            *factory* passed to the constructor is used with *key* as argument.

        Raises
        ------
        ValueError
            If no loader and no factory was configured.
        """
        val = self.get(key)
        if val is not None:
            return val
        if loader is not None:
            val = loader()
        elif self._factory is not None:
            val = self._factory(key)
        else:
            raise ValueError(
                "get_or_load requires either a loader argument or a factory"
            )
        self.put(key, val)
        return val

    def invalidate(self, key: K) -> bool:
        """Remove *key* from the cache.

        Returns ``True`` if the key existed.
        Emits :attr:`on_invalidated` when found.
        """
        with self._lock:
            if key in self._store:
                del self._store[key]
                self._invalidations += 1
                fire = True
            else:
                fire = False
        if fire:
            self.on_invalidated.emit(key)
        return fire

    def invalidate_all(self) -> int:
        """Remove all entries from the cache.

        Returns the number of entries removed.
        Emits :attr:`on_invalidated` once per removed entry.
        """
        with self._lock:
            keys = list(self._store.keys())
            self._store.clear()
            self._invalidations += len(keys)
        for k in keys:
            self.on_invalidated.emit(k)
        return len(keys)

    def contains(self, key: K) -> bool:
        """Return ``True`` if *key* is present and not expired."""
        with self._lock:
            entry = self._store.get(key)
            if entry is None:
                return False
            if self._is_expired(entry):
                del self._store[key]
                return False
            return True

    def __len__(self) -> int:
        with self._lock:
            return len(self._store)

    # ------------------------------------------------------------------
    # Stats
    # ------------------------------------------------------------------

    def stats(self) -> CacheStats:
        """Return a snapshot of cache performance counters."""
        with self._lock:
            return CacheStats(
                size=len(self._store),
                hits=self._hits,
                misses=self._misses,
                evictions=self._evictions,
                invalidations=self._invalidations,
            )

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _is_expired(self, entry: _CacheEntry) -> bool:
        if entry.expires_at is None:
            return False
        return time.monotonic() >= entry.expires_at

    def put(self, key: K, value: V) -> None:
        """Insert or update *key* in the cache."""
        expires_at = (time.monotonic() + self._ttl) if self._ttl is not None else None
        pending: Optional[Tuple] = None
        with self._lock:
            if key in self._store:
                self._store.move_to_end(key)
                self._store[key] = _CacheEntry(value, expires_at)
            else:
                self._store[key] = _CacheEntry(value, expires_at)
                if len(self._store) > self._max_size:
                    evict_key, evict_entry = self._store.popitem(last=False)
                    self._evictions += 1
                    pending = (evict_key, evict_entry.value)
        if pending is not None:
            self.on_evicted.emit(pending)
