"""Tests for Signal/SignalConnection, ValueChangeReason, and value_change_callback."""
import unittest

from gui_do.events.signal import Signal, SignalConnection, _SignalInstance
from gui_do.events.value_change import (
    ValueChangeReason,
    dispatch_value_change,
    validate_value_change_callback,
)


# ===========================================================================
# _SignalInstance
# ===========================================================================


class TestSignalInstance(unittest.TestCase):
    def test_connect_registers(self):
        sig = _SignalInstance()
        cb = lambda v: None
        sig.connect(cb)
        self.assertEqual(1, sig.connection_count)

    def test_connect_returns_connection(self):
        sig = _SignalInstance()
        conn = sig.connect(lambda v: None)
        self.assertIsInstance(conn, SignalConnection)

    def test_connect_noncallable_raises(self):
        sig = _SignalInstance()
        with self.assertRaises(TypeError):
            sig.connect("not callable")

    def test_connect_deduplicated(self):
        sig = _SignalInstance()
        cb = lambda v: None
        sig.connect(cb)
        sig.connect(cb)
        self.assertEqual(1, sig.connection_count)

    def test_emit_fires_callback(self):
        received = []
        sig = _SignalInstance()
        sig.connect(lambda v: received.append(v))
        sig.emit(42)
        self.assertEqual([42], received)

    def test_emit_fires_all_callbacks(self):
        received = []
        sig = _SignalInstance()
        sig.connect(lambda v: received.append(("a", v)))
        sig.connect(lambda v: received.append(("b", v)))
        sig.emit(10)
        self.assertEqual(2, len(received))

    def test_emit_no_callbacks_no_error(self):
        sig = _SignalInstance()
        sig.emit("ignored")  # should not raise

    def test_disconnect(self):
        received = []
        sig = _SignalInstance()
        cb = lambda v: received.append(v)
        sig.connect(cb)
        sig.disconnect(cb)
        sig.emit(1)
        self.assertEqual([], received)

    def test_disconnect_missing_no_error(self):
        sig = _SignalInstance()
        sig.disconnect(lambda v: None)  # should not raise

    def test_disconnect_all(self):
        sig = _SignalInstance()
        sig.connect(lambda v: None)
        sig.connect(lambda v: None)
        sig.disconnect_all()
        self.assertEqual(0, sig.connection_count)

    def test_connect_once_fires_once(self):
        received = []
        sig = _SignalInstance()
        sig.connect_once(lambda v: received.append(v))
        sig.emit(1)
        sig.emit(2)
        self.assertEqual([1], received)

    def test_connect_once_auto_disconnects(self):
        sig = _SignalInstance()
        sig.connect_once(lambda v: None)
        sig.emit(99)
        self.assertEqual(0, sig.connection_count)

    def test_connection_count_both_types(self):
        sig = _SignalInstance()
        sig.connect(lambda v: None)
        sig.connect_once(lambda v: None)
        self.assertEqual(2, sig.connection_count)


# ===========================================================================
# SignalConnection
# ===========================================================================


class TestSignalConnection(unittest.TestCase):
    def test_disconnect_via_handle(self):
        received = []
        sig = _SignalInstance()
        cb = lambda v: received.append(v)
        conn = sig.connect(cb)
        conn.disconnect()
        sig.emit(1)
        self.assertEqual([], received)

    def test_callback_property(self):
        sig = _SignalInstance()
        cb = lambda v: None
        conn = sig.connect(cb)
        self.assertIs(cb, conn.callback)


# ===========================================================================
# Signal descriptor
# ===========================================================================


class TestSignalDescriptor(unittest.TestCase):
    def test_signal_per_instance(self):
        class Widget:
            clicked: Signal = Signal()

        w1 = Widget()
        w2 = Widget()
        received_w1 = []
        received_w2 = []
        w1.clicked.connect(lambda v: received_w1.append(v))
        w2.clicked.connect(lambda v: received_w2.append(v))
        w1.clicked.emit("A")
        self.assertEqual(["A"], received_w1)
        self.assertEqual([], received_w2)

    def test_signal_not_reassignable(self):
        class Widget:
            clicked: Signal = Signal()

        w = Widget()
        with self.assertRaises(AttributeError):
            w.clicked = lambda: None

    def test_class_level_access_returns_descriptor(self):
        class Widget:
            clicked: Signal = Signal()

        self.assertIsInstance(Widget.clicked, Signal)


# ===========================================================================
# ValueChangeReason
# ===========================================================================


class TestValueChangeReason(unittest.TestCase):
    def test_is_string_enum(self):
        self.assertEqual("keyboard", ValueChangeReason.KEYBOARD)
        self.assertEqual("programmatic", ValueChangeReason.PROGRAMMATIC)

    def test_mouse_drag(self):
        self.assertEqual("mouse_drag", ValueChangeReason.MOUSE_DRAG)

    def test_wheel(self):
        self.assertEqual("wheel", ValueChangeReason.WHEEL)


# ===========================================================================
# validate_value_change_callback
# ===========================================================================


class TestValidateValueChangeCallback(unittest.TestCase):
    def test_none_is_valid(self):
        validate_value_change_callback(None)  # should not raise

    def test_callable_is_valid(self):
        validate_value_change_callback(lambda v, r: None)  # should not raise

    def test_non_callable_raises(self):
        with self.assertRaises(TypeError):
            validate_value_change_callback("not callable")

    def test_int_raises(self):
        with self.assertRaises(TypeError):
            validate_value_change_callback(42)


# ===========================================================================
# dispatch_value_change
# ===========================================================================


class TestDispatchValueChange(unittest.TestCase):
    def test_dispatch_none_callback_no_error(self):
        dispatch_value_change(None, 42, ValueChangeReason.PROGRAMMATIC)

    def test_dispatch_calls_callback(self):
        received = []
        dispatch_value_change(lambda v, r: received.append((v, r)),
                              10, ValueChangeReason.MOUSE_DRAG)
        self.assertEqual([(10, ValueChangeReason.MOUSE_DRAG)], received)

    def test_dispatch_with_reason(self):
        received = []
        dispatch_value_change(lambda v, r: received.append(r),
                              0, ValueChangeReason.KEYBOARD)
        self.assertEqual([ValueChangeReason.KEYBOARD], received)


if __name__ == "__main__":
    unittest.main()
