"""Router — named-route navigation with push/pop/replace semantics and guards."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..app.gui_application import GuiApplication

# Guard signature: (from_route, to_route, params) -> bool
# Return False to block the navigation.
NavigationGuard = Callable[[str, str, Dict[str, Any]], bool]


@dataclass
class RouteEntry:
    """A single entry in the Router's navigation history."""

    route: str
    params: Dict[str, Any] = field(default_factory=dict)

    def __repr__(self) -> str:  # pragma: no cover
        return f"RouteEntry(route={self.route!r}, params={self.params!r})"


class Router:
    """Named-route navigation stack with push/pop/replace semantics.

    Routes are mapped to scene names via :meth:`register`.  When navigation
    occurs the router calls :meth:`GuiApplication.switch_scene` automatically
    if an *app* is provided and the scene is registered.

    Guards can block any navigation attempt; they are called in registration
    order and any ``False`` return cancels the transition.

    Usage::

        router = Router()
        router.register("/home", "home_scene")
        router.register("/editor", "editor_scene")

        router.on_route_change(lambda e: print("navigated to", e.route))

        router.push("/home", app=app)           # switches to home_scene
        router.push("/editor", app=app)         # switches to editor_scene
        router.pop(app=app)                     # back to home_scene
    """

    def __init__(self) -> None:
        # route name -> scene name
        self._routes: Dict[str, str] = {}
        self._history: List[RouteEntry] = []
        self._guards: List[NavigationGuard] = []
        self._on_change: List[Callable[[RouteEntry], None]] = []

    # ------------------------------------------------------------------
    # Registration
    # ------------------------------------------------------------------

    def register(self, route: str, scene_name: str) -> None:
        """Map a named route to a scene name.

        Routes may be any non-empty string (``"/home"``, ``"editor"``, etc.).
        """
        route = str(route).strip()
        scene_name = str(scene_name).strip()
        if not route:
            raise ValueError("route must be a non-empty string")
        if not scene_name:
            raise ValueError("scene_name must be a non-empty string")
        self._routes[route] = scene_name

    def add_guard(self, guard: NavigationGuard) -> None:
        """Add a navigation guard.

        The guard is called with ``(from_route, to_route, params)`` and must
        return ``True`` to allow or ``False`` to block the navigation.
        """
        if not callable(guard):
            raise ValueError("guard must be callable")
        self._guards.append(guard)

    def on_route_change(
        self, callback: Callable[[RouteEntry], None]
    ) -> Callable[[], None]:
        """Subscribe to route changes.

        Returns an *unsubscribe* callable that removes this subscriber.
        """
        if not callable(callback):
            raise ValueError("callback must be callable")
        self._on_change.append(callback)

        def _unsub() -> None:
            try:
                self._on_change.remove(callback)
            except ValueError:
                pass

        return _unsub

    # ------------------------------------------------------------------
    # Navigation
    # ------------------------------------------------------------------

    def push(
        self,
        route: str,
        params: Optional[Dict[str, Any]] = None,
        *,
        app: "Optional[GuiApplication]" = None,
    ) -> bool:
        """Navigate to *route*, appending to history.

        Returns ``True`` if the navigation occurred (no guard blocked it).
        """
        params = dict(params or {})
        current = self._history[-1].route if self._history else ""
        if not self._allow(current, route, params):
            return False
        entry = RouteEntry(route=str(route), params=params)
        self._history.append(entry)
        self._activate(entry, app)
        return True

    def pop(self, *, app: "Optional[GuiApplication]" = None) -> bool:
        """Navigate back one entry in history.

        Returns ``True`` if the navigation occurred.
        Returns ``False`` when history has fewer than two entries or a guard
        blocks the transition.
        """
        if len(self._history) < 2:
            return False
        current = self._history[-1].route
        target = self._history[-2].route
        if not self._allow(current, target, {}):
            return False
        self._history.pop()
        entry = self._history[-1]
        self._activate(entry, app)
        return True

    def replace(
        self,
        route: str,
        params: Optional[Dict[str, Any]] = None,
        *,
        app: "Optional[GuiApplication]" = None,
    ) -> bool:
        """Replace the current history entry with *route*.

        Returns ``True`` if the navigation occurred.
        """
        params = dict(params or {})
        current = self._history[-1].route if self._history else ""
        if not self._allow(current, route, params):
            return False
        entry = RouteEntry(route=str(route), params=params)
        if self._history:
            self._history[-1] = entry
        else:
            self._history.append(entry)
        self._activate(entry, app)
        return True

    # ------------------------------------------------------------------
    # Inspection
    # ------------------------------------------------------------------

    @property
    def current_route(self) -> Optional[str]:
        """The current route name, or *None* when the history is empty."""
        return self._history[-1].route if self._history else None

    @property
    def current_params(self) -> Dict[str, Any]:
        """A copy of the current route params dict."""
        return dict(self._history[-1].params) if self._history else {}

    @property
    def history(self) -> List[RouteEntry]:
        """A shallow copy of the navigation history stack."""
        return list(self._history)

    def can_pop(self) -> bool:
        """Return True when there is at least one entry to pop back to."""
        return len(self._history) > 1

    def scene_for(self, route: str) -> Optional[str]:
        """Return the registered scene name for *route*, or *None*."""
        return self._routes.get(str(route))

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _allow(
        self, from_route: str, to_route: str, params: Dict[str, Any]
    ) -> bool:
        for guard in self._guards:
            try:
                if not guard(from_route, to_route, params):
                    return False
            except Exception:
                pass
        return True

    def _activate(self, entry: RouteEntry, app: "Optional[GuiApplication]") -> None:
        scene_name = self._routes.get(entry.route)
        if app is not None and scene_name is not None:
            if app.has_scene(scene_name):
                app.switch_scene(scene_name)
        for cb in self._on_change:
            try:
                cb(entry)
            except Exception:
                pass
