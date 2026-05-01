import unittest

from gui_do.events.signal import Signal, SignalConnection


class _Owner:
    clicked: Signal[int] = Signal()
    value_changed: Signal[float] = Signal()


class TestSignalDescriptor(unittest.TestCase):
    def test_each_instance_gets_its_own_signal_state(self):
        a = _Owner()
        b = _Owner()
        calls_a = []
        calls_b = []

        a.clicked.connect(calls_a.append)
        b.clicked.connect(calls_b.append)

        a.clicked.emit(1)
        b.clicked.emit(2)

        self.assertEqual([1], calls_a)
        self.assertEqual([2], calls_b)

    def test_reassigning_signal_raises_attribute_error(self):
        obj = _Owner()
        with self.assertRaises(AttributeError):
            obj.clicked = object()

    def test_class_level_access_returns_descriptor(self):
        self.assertIsInstance(_Owner.clicked, Signal)

    def test_connect_returns_signal_connection(self):
        obj = _Owner()
        conn = obj.clicked.connect(lambda v: None)
        self.assertIsInstance(conn, SignalConnection)

    def test_emit_calls_connected_callback_with_value(self):
        obj = _Owner()
        received = []
        obj.clicked.connect(received.append)

        obj.clicked.emit(42)

        self.assertEqual([42], received)

    def test_disconnect_via_connection_handle_stops_delivery(self):
        obj = _Owner()
        received = []
        conn = obj.clicked.connect(received.append)

        conn.disconnect()
        obj.clicked.emit(99)

        self.assertEqual([], received)

    def test_disconnect_via_signal_instance_stops_delivery(self):
        obj = _Owner()
        received = []
        cb = received.append
        obj.clicked.connect(cb)

        obj.clicked.disconnect(cb)
        obj.clicked.emit(7)

        self.assertEqual([], received)

    def test_connect_once_fires_exactly_one_time(self):
        obj = _Owner()
        received = []
        obj.clicked.connect_once(received.append)

        obj.clicked.emit(1)
        obj.clicked.emit(2)
        obj.clicked.emit(3)

        self.assertEqual([1], received)

    def test_connect_and_connect_once_coexist(self):
        obj = _Owner()
        always = []
        once = []

        obj.clicked.connect(always.append)
        obj.clicked.connect_once(once.append)

        obj.clicked.emit(10)
        obj.clicked.emit(20)

        self.assertEqual([10, 20], always)
        self.assertEqual([10], once)

    def test_disconnect_all_removes_all_connections(self):
        obj = _Owner()
        received = []
        obj.clicked.connect(received.append)
        obj.clicked.connect_once(received.append)

        obj.clicked.disconnect_all()
        obj.clicked.emit(5)

        self.assertEqual([], received)

    def test_connection_count_reflects_active_connections(self):
        obj = _Owner()
        self.assertEqual(0, obj.clicked.connection_count)

        obj.clicked.connect(lambda v: None)
        obj.clicked.connect_once(lambda v: None)
        self.assertEqual(2, obj.clicked.connection_count)

    def test_emit_with_no_connections_is_a_noop(self):
        obj = _Owner()
        # Should not raise.
        obj.clicked.emit(0)

    def test_duplicate_connect_does_not_add_duplicate_callback(self):
        obj = _Owner()
        received = []
        cb = received.append

        obj.clicked.connect(cb)
        obj.clicked.connect(cb)
        obj.clicked.emit(1)

        self.assertEqual([1], received)

    def test_disconnect_inside_emit_does_not_raise(self):
        obj = _Owner()
        received = []
        conn = [None]

        def _cb(v):
            received.append(v)
            conn[0].disconnect()

        conn[0] = obj.clicked.connect(_cb)
        obj.clicked.emit(1)
        obj.clicked.emit(2)

        self.assertEqual([1], received)

    def test_multiple_signals_on_same_instance_are_independent(self):
        obj = _Owner()
        clicks = []
        values = []

        obj.clicked.connect(clicks.append)
        obj.value_changed.connect(values.append)

        obj.clicked.emit(1)
        obj.value_changed.emit(3.14)

        self.assertEqual([1], clicks)
        self.assertEqual([3.14], values)


if __name__ == "__main__":
    unittest.main()
