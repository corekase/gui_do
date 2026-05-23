from __future__ import annotations

import inspect
from collections.abc import Callable
from uuid import uuid4

from ..app.error_handling import report_nonfatal_error
from ..app.service_scope import ServiceScope


_EMPTY_FAILURE_POLICY: dict[str, object] = {}


class FeatureRuntimeScope:
    """Lifecycle-owned runtime scope for one feature binding pass.

    The scope provides two facilities:

    - a cleanup bag for unsubscribe/disconnect/cancel callables
    - a child ServiceScope for scene-local service publication and disposal
    """

    def __init__(self, parent_scope: ServiceScope | None = None) -> None:
        self._service_scope = parent_scope.child() if isinstance(parent_scope, ServiceScope) else ServiceScope()
        self._cleanups: list[Callable[[], object]] = []
        self._disposed = False

    @property
    def service_scope(self) -> ServiceScope:
        return self._service_scope

    @property
    def is_disposed(self) -> bool:
        return self._disposed

    def add_cleanup(self, cleanup: Callable[[], object] | None) -> Callable[[], object] | None:
        if cleanup is None:
            return None
        if not callable(cleanup):
            raise TypeError("cleanup must be callable")
        self._cleanups.append(cleanup)
        return cleanup

    def own_connection(self, connection: object) -> object:
        disconnect = getattr(connection, "disconnect", None)
        if callable(disconnect):
            self.add_cleanup(disconnect)
        else:
            raise TypeError("connection must expose disconnect()")
        return connection

    def own_cancel_handle(self, handle: object) -> object:
        cancel = getattr(handle, "cancel", None)
        if callable(cancel):
            self.add_cleanup(cancel)
        else:
            raise TypeError("handle must expose cancel()")
        return handle

    def own_disposable(self, instance: object) -> object:
        dispose = getattr(instance, "dispose", None)
        if callable(dispose):
            self.add_cleanup(dispose)
        else:
            raise TypeError("instance must expose dispose()")
        return instance

    def subscribe(self, observable: object, handler: Callable[..., object]) -> Callable[[], object]:
        subscribe = getattr(observable, "subscribe", None)
        if not callable(subscribe):
            raise TypeError("observable must expose subscribe()")
        unsubscribe = subscribe(handler)
        if not callable(unsubscribe):
            raise TypeError("observable subscribe() must return an unsubscribe callable")
        self.add_cleanup(unsubscribe)
        return unsubscribe

    def bind_service(self, key, instance: object, *, owned: bool = True) -> object:
        self._service_scope.bind(key, instance, owned=owned)
        return instance

    def get_service(self, key):
        return self._service_scope.get(key)

    def get_optional_service(self, key):
        return self._service_scope.get_optional(key)

    def dispose(self) -> None:
        if self._disposed:
            return
        self._disposed = True
        for cleanup in reversed(self._cleanups):
            try:
                cleanup()
            except Exception:
                pass
        self._cleanups.clear()
        self._service_scope.dispose()


class FeatureOperationHandle:
    """Mutable handle tracking the lifecycle of one operation request."""

    __slots__ = (
        "request_id",
        "operation_name",
        "status",
        "result",
        "error",
        "progress",
        "_bus",
    )

    def __init__(self, bus: "FeatureOperationBus", operation_name: str) -> None:
        self.request_id = uuid4().hex
        self.operation_name = str(operation_name)
        self.status = "pending"
        self.result: object = None
        self.error: BaseException | None = None
        self.progress: object = None
        self._bus = bus

    @property
    def is_pending(self) -> bool:
        return self.status == "pending"

    @property
    def is_complete(self) -> bool:
        return self.status == "completed"

    @property
    def is_failed(self) -> bool:
        return self.status == "failed"

    @property
    def is_cancelled(self) -> bool:
        return self.status == "cancelled"

    @property
    def is_timed_out(self) -> bool:
        return self.status == "timeout"

    def cancel(self) -> None:
        self._bus.cancel(self)


class FeatureOperationContext:
    """Execution context passed to operation handlers."""

    __slots__ = (
        "feature",
        "host",
        "runtime_scope",
        "handle",
        "attempt_index",
        "_deferred",
    )

    def __init__(self, *, feature, host, runtime_scope: FeatureRuntimeScope | None, handle: FeatureOperationHandle, attempt_index: int) -> None:
        self.feature = feature
        self.host = host
        self.runtime_scope = runtime_scope
        self.handle = handle
        self.attempt_index = int(attempt_index)
        self._deferred = False

    @property
    def is_cancelled(self) -> bool:
        return self.handle.is_cancelled or self.handle.is_timed_out

    @property
    def deferred(self) -> bool:
        return self._deferred

    def defer(self) -> None:
        self._deferred = True

    def complete(self, result: object = None) -> None:
        self.handle._bus.complete(self.handle, result)

    def fail(self, error: BaseException) -> None:
        self.handle._bus.fail(self.handle, error)

    def publish_progress(self, payload: object) -> None:
        self.handle.progress = payload


class FeatureOperationBus:
    """Scene-local operation registry with retry, timeout, and cancellation support."""

    def __init__(self, *, feature=None, host=None, runtime_scope: FeatureRuntimeScope | None = None, timers=None, event_bus=None) -> None:
        self._feature = feature
        self._host = host
        self._runtime_scope = runtime_scope
        self._timers = timers
        self._event_bus = event_bus
        self._handlers: dict[str, tuple[Callable[..., object], str | None]] = {}
        self._failure_policies: dict[str, dict[str, object]] = {}
        self._handles: dict[str, FeatureOperationHandle] = {}
        self._timeout_ids: dict[str, object] = {}
        self._retry_ids: dict[str, object] = {}

    def dispose(self) -> None:
        for handle in tuple(self._handles.values()):
            self.cancel(handle)
        self._handlers.clear()
        self._failure_policies.clear()

    def register_failure_policy(
        self,
        name: str,
        *,
        retries: int = 0,
        retry_delay_seconds: float = 0.0,
        timeout_seconds: float | None = None,
        publish_topic: str | None = None,
        publish_scope: str | None = None,
    ) -> None:
        self._failure_policies[str(name)] = {
            "retries": max(0, int(retries)),
            "retry_delay_seconds": max(0.0, float(retry_delay_seconds)),
            "timeout_seconds": None if timeout_seconds is None else max(0.0, float(timeout_seconds)),
            "publish_topic": None if publish_topic is None else str(publish_topic),
            "publish_scope": None if publish_scope is None else str(publish_scope),
        }

    def register(self, operation_name: str, handler: Callable[..., object], *, failure_policy: str | None = None) -> Callable[[], None]:
        name = str(operation_name)
        self._handlers[name] = (handler, None if failure_policy is None else str(failure_policy))

        def _unregister() -> None:
            self._handlers.pop(name, None)

        return _unregister

    def call(self, operation_name: str, payload: object = None, *, timeout_seconds: float | None = None) -> FeatureOperationHandle:
        name = str(operation_name)
        handle = FeatureOperationHandle(self, name)
        self._handles[handle.request_id] = handle
        entry = self._handlers.get(name)
        if entry is None:
            self.fail(handle, KeyError(f"unknown operation: {name}"))
            return handle
        _handler, failure_policy_name = entry
        policy = self._failure_policies.get(str(failure_policy_name), _EMPTY_FAILURE_POLICY) if failure_policy_name is not None else _EMPTY_FAILURE_POLICY
        effective_timeout = timeout_seconds
        if effective_timeout is None:
            effective_timeout = policy.get("timeout_seconds")
        if isinstance(effective_timeout, (int, float)) and float(effective_timeout) > 0.0:
            self._schedule_timeout(handle, float(effective_timeout))
        self._dispatch(handle, payload, attempt_index=0)
        return handle

    def cancel(self, handle: FeatureOperationHandle) -> None:
        if not handle.is_pending:
            return
        self._clear_timer(self._timeout_ids.pop(handle.request_id, None))
        self._clear_timer(self._retry_ids.pop(handle.request_id, None))
        handle.status = "cancelled"
        self._handles.pop(handle.request_id, None)

    def complete(self, handle: FeatureOperationHandle, result: object = None) -> None:
        if not handle.is_pending:
            return
        self._clear_timer(self._timeout_ids.pop(handle.request_id, None))
        self._clear_timer(self._retry_ids.pop(handle.request_id, None))
        handle.status = "completed"
        handle.result = result
        self._handles.pop(handle.request_id, None)

    def fail(self, handle: FeatureOperationHandle, error: BaseException) -> None:
        if not handle.is_pending:
            return
        self._clear_timer(self._timeout_ids.pop(handle.request_id, None))
        self._clear_timer(self._retry_ids.pop(handle.request_id, None))
        handle.status = "failed"
        handle.error = error
        self._handles.pop(handle.request_id, None)

    def _timeout(self, handle: FeatureOperationHandle) -> None:
        if not handle.is_pending:
            return
        self._clear_timer(self._retry_ids.pop(handle.request_id, None))
        self._timeout_ids.pop(handle.request_id, None)
        handle.status = "timeout"
        handle.error = TimeoutError(f"operation timed out: {handle.operation_name}")
        self._handles.pop(handle.request_id, None)

    def _schedule_timeout(self, handle: FeatureOperationHandle, timeout_seconds: float) -> None:
        if self._timers is None:
            return
        timer_id = ("feature_operation_timeout", handle.request_id)
        self._timeout_ids[handle.request_id] = timer_id
        self._timers.add_once(timer_id, timeout_seconds, lambda: self._timeout(handle))

    def _dispatch(self, handle: FeatureOperationHandle, payload: object, *, attempt_index: int) -> None:
        entry = self._handlers.get(handle.operation_name)
        if entry is None:
            self.fail(handle, KeyError(f"unknown operation: {handle.operation_name}"))
            return
        handler, failure_policy_name = entry
        context = FeatureOperationContext(
            feature=self._feature,
            host=self._host,
            runtime_scope=self._runtime_scope,
            handle=handle,
            attempt_index=attempt_index,
        )
        try:
            result = self._invoke_handler(handler, payload, context)
        except Exception as exc:
            if self._maybe_retry(handle, payload, attempt_index=attempt_index, error=exc, failure_policy_name=failure_policy_name):
                return
            self._report_failure(handle.operation_name, exc, failure_policy_name=failure_policy_name, attempt_index=attempt_index)
            self.fail(handle, exc)
            return
        if context.deferred or not handle.is_pending:
            return
        self.complete(handle, result)

    def _maybe_retry(
        self,
        handle: FeatureOperationHandle,
        payload: object,
        *,
        attempt_index: int,
        error: BaseException,
        failure_policy_name: str | None,
    ) -> bool:
        if failure_policy_name is None:
            return False
        policy = self._failure_policies.get(str(failure_policy_name))
        if not policy:
            return False
        retries = int(policy.get("retries", 0))
        if attempt_index >= retries:
            return False
        delay_seconds = float(policy.get("retry_delay_seconds", 0.0))
        if delay_seconds <= 0.0 or self._timers is None:
            self._report_failure(handle.operation_name, error, failure_policy_name=failure_policy_name, attempt_index=attempt_index, retrying=True)
            self._dispatch(handle, payload, attempt_index=attempt_index + 1)
            return True
        timer_id = ("feature_operation_retry", handle.request_id, attempt_index + 1)
        self._retry_ids[handle.request_id] = timer_id
        self._report_failure(handle.operation_name, error, failure_policy_name=failure_policy_name, attempt_index=attempt_index, retrying=True)
        self._timers.add_once(
            timer_id,
            delay_seconds,
            lambda: self._dispatch(handle, payload, attempt_index=attempt_index + 1),
        )
        return True

    @staticmethod
    def _invoke_handler(handler: Callable[..., object], payload: object, context: FeatureOperationContext):
        try:
            signature = inspect.signature(handler)
        except (TypeError, ValueError):
            return handler(payload, context)
        parameters = tuple(signature.parameters.values())
        if any(parameter.kind is inspect.Parameter.VAR_POSITIONAL for parameter in parameters):
            return handler(payload, context)
        positional = [
            parameter
            for parameter in parameters
            if parameter.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD)
        ]
        argc = len(positional)
        if argc <= 0:
            return handler()
        if argc == 1:
            return handler(payload)
        return handler(payload, context)

    def _report_failure(
        self,
        operation_name: str,
        error: BaseException,
        *,
        failure_policy_name: str | None,
        attempt_index: int,
        retrying: bool = False,
    ) -> None:
        report_nonfatal_error(
            f"operation '{operation_name}' failed",
            kind="runtime_operation",
            subsystem="feature_operations",
            operation=operation_name,
            cause=error,
            details={
                "attempt_index": int(attempt_index),
                "failure_policy": failure_policy_name,
                "retrying": bool(retrying),
            },
            source_skip_frames=1,
        )
        if failure_policy_name is None:
            return
        policy = self._failure_policies.get(str(failure_policy_name))
        if not policy:
            return
        topic = policy.get("publish_topic")
        if topic is None or self._event_bus is None:
            return
        self._event_bus.publish(
            str(topic),
            {
                "operation_name": str(operation_name),
                "error": str(error),
                "attempt_index": int(attempt_index),
                "retrying": bool(retrying),
            },
            scope=policy.get("publish_scope"),
        )

    def _clear_timer(self, timer_id: object | None) -> None:
        if timer_id is None or self._timers is None:
            return
        self._timers.remove_timer(timer_id)
