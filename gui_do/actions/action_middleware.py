"""ActionMiddleware — composable pre/post interception for ActionManager dispatch.

A middleware is a callable (or class instance) that wraps each action
dispatch.  It may inspect, modify, block, or enrich the action context before
forwarding it to the next middleware or the final handler.

Middlewares are registered on :class:`~gui_do.ActionManager` via
``action_manager.add_middleware(mw)``.  They form a LIFO (last-in, first-out)
pipeline: the most-recently added middleware runs *first* on every dispatch so
that cross-cutting concerns such as logging, undo, and authorization can be
added non-invasively without changing existing registrations.

Usage::

    from gui_do import ActionContext, ActionMiddleware

    class LoggingMiddleware:
        def __call__(self, ctx: ActionContext, next_handler) -> bool:
            print(f"[action] {ctx.action_name}")
            result = next_handler(ctx)
            print(f"[action] {ctx.action_name} → {result}")
            return result

    app.action_manager.add_middleware(LoggingMiddleware())

    # Block actions not permitted in read-only mode:
    def read_only_guard(ctx: ActionContext, next_handler) -> bool:
        if app.read_only and ctx.action_name.startswith("edit."):
            return False   # action blocked
        return next_handler(ctx)

    app.action_manager.add_middleware(read_only_guard)

Middleware protocol
-------------------
A middleware is any callable with the signature::

    def middleware(ctx: ActionContext, next_handler: Callable[[ActionContext], bool]) -> bool

- *ctx* is the :class:`ActionContext` for this dispatch (mutable: you may
  attach extra data via ``ctx.extras``).
- *next_handler* is the continuation — call it to forward to the next
  middleware or the final action handler.  You may call it zero or more times.
- Return ``True`` to indicate the action was consumed, ``False`` otherwise.

``ActionMiddleware`` is a convenience protocol type alias for type-checkers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..events.gui_event import GuiEvent


# ---------------------------------------------------------------------------
# ActionContext
# ---------------------------------------------------------------------------


@dataclass
class ActionContext:
    """Mutable context object passed through the middleware pipeline.

    Attributes
    ----------
    action_name:
        The name of the action being dispatched (e.g. ``"file.open"``).
    event:
        The originating :class:`~gui_do.GuiEvent`, or ``None`` for
        programmatically triggered actions.
    extras:
        Mutable dict for middleware to attach cross-cutting metadata (e.g.
        ``{"log_entry": "…", "timing_start": t}``).
    """

    action_name: str
    event: Optional["GuiEvent"] = None
    extras: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Type alias
# ---------------------------------------------------------------------------

#: Protocol type for action middleware callables.
#:
#: A middleware is ``Callable[[ActionContext, Callable[[ActionContext], bool]], bool]``.
ActionMiddleware = Callable[["ActionContext", Callable[["ActionContext"], bool]], bool]


# ---------------------------------------------------------------------------
# Middleware chain builder
# ---------------------------------------------------------------------------


def build_middleware_chain(
    middlewares: List[ActionMiddleware],
    terminal: Callable[["ActionContext"], bool],
) -> Callable[["ActionContext"], bool]:
    """Compose a list of middlewares and a terminal handler into one callable.

    Middlewares are applied in *reverse* order so the last-added middleware
    wraps outermost (LIFO stack).

    Parameters
    ----------
    middlewares:
        Ordered list of middlewares (outermost last).
    terminal:
        The final action handler called after all middlewares.

    Returns
    -------
    Callable[[ActionContext], bool]
        A single callable that runs the full pipeline.
    """
    chain: Callable[["ActionContext"], bool] = terminal
    for mw in middlewares:
        # Capture mw and chain in a closure to avoid loop-variable aliasing.
        def _make_link(
            middleware: ActionMiddleware,
            next_fn: Callable[["ActionContext"], bool],
        ) -> Callable[["ActionContext"], bool]:
            def _link(ctx: "ActionContext") -> bool:
                return bool(middleware(ctx, next_fn))
            return _link

        chain = _make_link(mw, chain)
    return chain
