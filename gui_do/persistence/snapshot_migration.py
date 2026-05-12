"""SnapshotMigration — versioned runtime persistence with migration graph.

Provides:

* :class:`SchemaVersion` — comparable ``(major, minor)`` version tuple
* :class:`VersionedSnapshot` — typed dict with ``schema_version`` and ``data``
* :class:`MigrationStep` — single ``(from_version, to_version, migrate_fn)``
* :class:`MigrationRegistry` — builds and traverses the migration graph
* :class:`SnapshotMigrator` — top-level API: migrate a snapshot to a target version
"""
from __future__ import annotations

import copy
from collections import deque
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple, TypedDict

__all__ = [
    "SchemaVersion",
    "VersionedSnapshot",
    "MigrationStep",
    "MigrationRegistry",
    "SnapshotMigrator",
]


# ---------------------------------------------------------------------------
# SchemaVersion
# ---------------------------------------------------------------------------


@dataclass(order=True, frozen=True)
class SchemaVersion:
    """Comparable ``(major, minor)`` schema version.

    Examples::

        v1 = SchemaVersion(1, 0)
        v2 = SchemaVersion(2, 0)
        assert v1 < v2
        assert str(v1) == "1.0"
    """

    major: int
    minor: int

    def __str__(self) -> str:
        return f"{self.major}.{self.minor}"

    @classmethod
    def parse(cls, text: str) -> "SchemaVersion":
        """Parse ``"major.minor"`` string into a :class:`SchemaVersion`."""
        parts = text.split(".", 1)
        try:
            major = int(parts[0])
            minor = int(parts[1]) if len(parts) > 1 else 0
        except (ValueError, IndexError) as exc:
            raise ValueError(f"Invalid version string: {text!r}") from exc
        return cls(major, minor)


# ---------------------------------------------------------------------------
# VersionedSnapshot
# ---------------------------------------------------------------------------


class VersionedSnapshot(TypedDict):
    """A snapshot dict that carries its own schema version."""

    schema_version: str
    data: Dict[str, Any]


def make_snapshot(version: SchemaVersion, data: Dict[str, Any]) -> VersionedSnapshot:
    """Convenience constructor for :class:`VersionedSnapshot`."""
    return {"schema_version": str(version), "data": copy.deepcopy(data)}


def read_version(snapshot: VersionedSnapshot) -> SchemaVersion:
    """Parse the ``schema_version`` field of *snapshot*."""
    return SchemaVersion.parse(snapshot["schema_version"])


# ---------------------------------------------------------------------------
# MigrationStep
# ---------------------------------------------------------------------------


MigrateFn = Callable[[Dict[str, Any]], Dict[str, Any]]
"""``(data: dict) -> dict`` — transforms data from one version to the next."""


@dataclass
class MigrationStep:
    """A single edge in the migration graph.

    Parameters
    ----------
    from_version:
        The source schema version.
    to_version:
        The target schema version.
    migrate:
        ``(data: dict) -> dict`` — must return a *new* or mutated copy of
        the data dict upgraded to ``to_version``.
    """

    from_version: SchemaVersion
    to_version: SchemaVersion
    migrate: MigrateFn

    def __post_init__(self) -> None:
        if self.from_version >= self.to_version:
            raise ValueError(
                f"MigrationStep: to_version ({self.to_version}) must be "
                f"greater than from_version ({self.from_version})"
            )


# ---------------------------------------------------------------------------
# MigrationRegistry
# ---------------------------------------------------------------------------


class MigrationRegistry:
    """Directed graph of :class:`MigrationStep` objects.

    Supports path finding (BFS) to compose multi-hop migration chains.
    """

    def __init__(self) -> None:
        self._steps: List[MigrationStep] = []

    def register(self, step: MigrationStep) -> None:
        """Add *step* to the registry."""
        self._steps.append(step)

    def find_path(
        self,
        from_version: SchemaVersion,
        to_version: SchemaVersion,
    ) -> Optional[List[MigrationStep]]:
        """Return an ordered list of steps that migrate from → to, or ``None``.

        Uses BFS to find the *shortest* path.
        """
        if from_version == to_version:
            return []

        # Build adjacency: version → list of steps
        adj: Dict[SchemaVersion, List[MigrationStep]] = {}
        for step in self._steps:
            adj.setdefault(step.from_version, []).append(step)

        # BFS
        queue = deque([(from_version, [])])
        visited: set[SchemaVersion] = {from_version}

        while queue:
            current, path = queue.popleft()
            for step in adj.get(current, []):
                new_path = path + [step]
                if step.to_version == to_version:
                    return new_path
                if step.to_version not in visited:
                    visited.add(step.to_version)
                    queue.append((step.to_version, new_path))

        return None

    @property
    def steps(self) -> List[MigrationStep]:
        return list(self._steps)


# ---------------------------------------------------------------------------
# SnapshotMigrator
# ---------------------------------------------------------------------------


class SnapshotMigrator:
    """Top-level API for migrating :class:`VersionedSnapshot` objects.

    Parameters
    ----------
    registry:
        The :class:`MigrationRegistry` containing all known migration steps.
    """

    def __init__(self, registry: MigrationRegistry) -> None:
        self._registry = registry

    def migrate(
        self,
        snapshot: VersionedSnapshot,
        target_version: SchemaVersion,
    ) -> VersionedSnapshot:
        """Return a new snapshot migrated to *target_version*.

        Raises :exc:`MigrationError` if no path exists.
        The original snapshot is not mutated.
        """
        current_version = read_version(snapshot)
        if current_version == target_version:
            return copy.deepcopy(snapshot)

        path = self._registry.find_path(current_version, target_version)
        if path is None:
            raise MigrationError(
                f"No migration path from {current_version} to {target_version}"
            )

        data = copy.deepcopy(snapshot["data"])
        for step in path:
            data = step.migrate(data)

        return make_snapshot(target_version, data)

    def can_migrate(
        self,
        from_version: SchemaVersion,
        to_version: SchemaVersion,
    ) -> bool:
        """``True`` if a migration path exists."""
        return self._registry.find_path(from_version, to_version) is not None


class MigrationError(Exception):
    """Raised when a migration path cannot be found."""
