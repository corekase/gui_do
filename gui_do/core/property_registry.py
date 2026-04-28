"""PropertyRegistry — declarative property metadata for UiNode introspection.

The :func:`ui_property` decorator annotates Python ``property`` descriptors on
:class:`~gui_do.UiNode` subclasses with display metadata (label, type, range,
group).  :class:`PropertyRegistry` scans class hierarchies and collects those
descriptors so tooling can auto-generate settings panels, debug inspectors,
and theme editors without hard-coding control internals.

Usage::

    from gui_do import ui_property, property_registry, PropertyDescriptor

    class MyControl(PanelControl):
        def __init__(self, ...):
            super().__init__(...)
            self._alpha: float = 1.0
            self._title: str = ""

        @property
        @ui_property(label="Opacity", type="float", min=0.0, max=1.0, group="Appearance")
        def alpha(self) -> float:
            return self._alpha

        @alpha.setter
        def alpha(self, v: float) -> None:
            self._alpha = float(v)
            self.invalidate()

        @property
        @ui_property(label="Title", type="str", group="Content")
        def title(self) -> str:
            return self._title

    # Retrieve descriptors for a control instance or class:
    descs = property_registry.descriptors_for(MyControl)
    for d in descs:
        print(d.name, d.label, d.type)

    # All registered classes:
    classes = property_registry.all_classes()
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set, Type


# ---------------------------------------------------------------------------
# PropertyDescriptor
# ---------------------------------------------------------------------------


@dataclass
class PropertyDescriptor:
    """Metadata for one introspectable property on a :class:`~gui_do.UiNode`.

    Attributes
    ----------
    name:
        Attribute name (matches the Python ``property`` name).
    label:
        Human-readable display label for settings UI.
    type:
        Data type hint: ``"str"``, ``"int"``, ``"float"``, ``"bool"``,
        ``"color"``, or any custom string.
    min:
        Minimum allowed value (``None`` if unbounded).
    max:
        Maximum allowed value (``None`` if unbounded).
    group:
        UI grouping category (e.g. ``"Appearance"``, ``"Content"``).
    read_only:
        ``True`` when the property has no public setter.
    owner_class:
        The class that declares this property.
    """

    name: str
    label: str
    type: str = "str"
    min: Any = None
    max: Any = None
    group: str = "General"
    read_only: bool = False
    owner_class: Optional[type] = None


# ---------------------------------------------------------------------------
# _UI_PROPERTY_ATTR
# ---------------------------------------------------------------------------

_UI_PROPERTY_ATTR = "_ui_property_meta"


# ---------------------------------------------------------------------------
# ui_property decorator
# ---------------------------------------------------------------------------


def ui_property(
    label: str,
    *,
    type: str = "str",          # noqa: A002
    min: Any = None,            # noqa: A002
    max: Any = None,            # noqa: A002
    group: str = "General",
    read_only: bool = False,
) -> Any:
    """Decorator that attaches display metadata to a Python ``property``.

    Apply *before* ``@property`` (i.e. innermost decorator)::

        @property
        @ui_property(label="Opacity", type="float", min=0.0, max=1.0)
        def alpha(self) -> float:
            return self._alpha

    The decorated function gains a ``_ui_property_meta`` attribute that
    :class:`PropertyRegistry` reads during class scanning.
    """

    def decorator(fn: Any) -> Any:
        meta = {
            "label": str(label),
            "type": str(type),
            "min": min,
            "max": max,
            "group": str(group),
            "read_only": bool(read_only),
        }
        # Attach to the underlying function (works whether fn is a function
        # or an already-built property from a prior @property application).
        target = fn.fget if isinstance(fn, property) else fn
        setattr(target, _UI_PROPERTY_ATTR, meta)
        return fn

    return decorator


# ---------------------------------------------------------------------------
# PropertyRegistry
# ---------------------------------------------------------------------------


class PropertyRegistry:
    """Collects :func:`ui_property` descriptors per class.

    The singleton :data:`property_registry` is pre-created at module load.
    Use :meth:`descriptors_for` to introspect any class or instance without
    calling :meth:`register` manually — the registry scans on first access.
    """

    def __init__(self) -> None:
        # class -> list of PropertyDescriptor
        self._cache: Dict[type, List[PropertyDescriptor]] = {}
        self._scanned: Set[type] = set()

    def register(self, cls: Type, descriptor: PropertyDescriptor) -> None:
        """Manually register a :class:`PropertyDescriptor` for *cls*.

        Use this when the ``@ui_property`` decorator cannot be applied directly
        (e.g. for third-party classes).
        """
        descriptor = PropertyDescriptor(
            name=descriptor.name,
            label=descriptor.label,
            type=descriptor.type,
            min=descriptor.min,
            max=descriptor.max,
            group=descriptor.group,
            read_only=descriptor.read_only,
            owner_class=cls,
        )
        self._cache.setdefault(cls, []).append(descriptor)

    def descriptors_for(self, node_or_class: Any) -> List[PropertyDescriptor]:
        """Return all :class:`PropertyDescriptor` objects for *node_or_class*.

        Scans the full MRO for ``@ui_property`` annotations so descriptors
        declared on base classes are included.  Results are cached.
        """
        cls = node_or_class if isinstance(node_or_class, type) else type(node_or_class)
        if cls in self._cache and cls in self._scanned:
            return list(self._cache[cls])
        return self._scan(cls)

    def all_classes(self) -> List[type]:
        """Return all classes that have at least one registered descriptor."""
        return [c for c, descs in self._cache.items() if descs]

    # ------------------------------------------------------------------
    # Internal scanning
    # ------------------------------------------------------------------

    def _scan(self, cls: type) -> List[PropertyDescriptor]:
        if cls in self._scanned:
            return list(self._cache.get(cls, []))
        self._scanned.add(cls)
        descs: List[PropertyDescriptor] = list(self._cache.get(cls, []))

        # Walk the MRO (skip `object`)
        for klass in cls.__mro__:
            if klass is object:
                continue
            for attr_name, attr_val in vars(klass).items():
                # Handle @property decorated with @ui_property
                fn = None
                if isinstance(attr_val, property):
                    fn = attr_val.fget
                elif callable(attr_val):
                    fn = attr_val
                if fn is None:
                    continue
                meta = getattr(fn, _UI_PROPERTY_ATTR, None)
                if meta is None:
                    continue
                # Check for duplicates (same name already found)
                if any(d.name == attr_name for d in descs):
                    continue
                read_only = isinstance(attr_val, property) and attr_val.fset is None
                descs.append(PropertyDescriptor(
                    name=attr_name,
                    label=meta["label"],
                    type=meta["type"],
                    min=meta["min"],
                    max=meta["max"],
                    group=meta["group"],
                    read_only=meta.get("read_only", read_only),
                    owner_class=klass,
                ))

        self._cache[cls] = descs
        return list(descs)

    def clear(self) -> None:
        """Clear the entire registry and scan cache (useful in tests)."""
        self._cache.clear()
        self._scanned.clear()


# ---------------------------------------------------------------------------
# Module-level singleton
# ---------------------------------------------------------------------------

property_registry: PropertyRegistry = PropertyRegistry()
