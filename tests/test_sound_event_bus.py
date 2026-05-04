"""Tests for SoundEventBus — portable audio cue system."""
import unittest

import gui_do
from gui_do import SoundEventBus, SoundCue, SoundBankRegistry
from gui_do.data.observable_collections import ChangeKind


class TestSoundCue(unittest.TestCase):
    def test_defaults(self):
        cue = SoundCue("sounds/click.wav")
        self.assertEqual(cue.path, "sounds/click.wav")
        self.assertEqual(cue.volume, 1.0)
        self.assertEqual(cue.loops, 0)
        self.assertEqual(cue.max_time_ms, 0)

    def test_volume_clamped(self):
        cue = SoundCue("x.wav", volume=2.5)
        self.assertEqual(cue.volume, 1.0)
        cue2 = SoundCue("x.wav", volume=-1.0)
        self.assertEqual(cue2.volume, 0.0)


class TestSoundBankRegistry(unittest.TestCase):
    def test_register_and_get(self):
        bank = SoundBankRegistry()
        cue = SoundCue("a.wav")
        bank.register("button.click", cue)
        self.assertIs(bank.get("button.click"), cue)

    def test_unregister(self):
        bank = SoundBankRegistry()
        bank.register("x", SoundCue("x.wav"))
        result = bank.unregister("x")
        self.assertTrue(result)
        self.assertIsNone(bank.get("x"))

    def test_unregister_missing_returns_false(self):
        bank = SoundBankRegistry()
        self.assertFalse(bank.unregister("nonexistent"))

    def test_merge_later_wins(self):
        bank1 = SoundBankRegistry()
        bank1.register("click", SoundCue("a.wav"))
        bank2 = SoundBankRegistry()
        new_cue = SoundCue("b.wav")
        bank2.register("click", new_cue)
        bank1.merge(bank2)
        self.assertIs(bank1.get("click"), new_cue)

    def test_event_names_sorted(self):
        bank = SoundBankRegistry()
        bank.register("z", SoundCue("z.wav"))
        bank.register("a", SoundCue("a.wav"))
        self.assertEqual(bank.event_names(), ["a", "z"])

    def test_len(self):
        bank = SoundBankRegistry()
        self.assertEqual(len(bank), 0)
        bank.register("x", SoundCue("x.wav"))
        self.assertEqual(len(bank), 1)


class TestSoundEventBusDegradedMode(unittest.TestCase):
    """Tests that work without real audio hardware (degraded/no-op mode)."""

    def _bus_with_bad_mixer(self) -> SoundEventBus:
        """Return a bus that cannot initialise the mixer (simulates no audio)."""
        bus = SoundEventBus()
        # Force degraded state by marking mixer unavailable
        bus._available = False
        return bus

    def test_emit_returns_false_when_unavailable(self):
        bus = self._bus_with_bad_mixer()
        bus.register("click", SoundCue("sounds/click.wav"))
        self.assertFalse(bus.emit("click"))

    def test_emit_returns_false_for_unregistered_event(self):
        bus = self._bus_with_bad_mixer()
        self.assertFalse(bus.emit("nonexistent"))

    def test_mute_prevents_playback(self):
        bus = self._bus_with_bad_mixer()
        bus.register("click", SoundCue("sounds/click.wav"))
        bus.mute("click")
        self.assertTrue(bus.is_muted("click"))
        self.assertFalse(bus.emit("click"))

    def test_unmute_restores(self):
        bus = SoundEventBus()
        bus._available = False
        bus.register("click", SoundCue("sounds/click.wav"))
        bus.mute("click")
        bus.unmute("click")
        self.assertFalse(bus.is_muted("click"))

    def test_master_volume_clamped(self):
        bus = SoundEventBus()
        bus.set_master_volume(2.0)
        self.assertEqual(bus.master_volume, 1.0)
        bus.set_master_volume(-1.0)
        self.assertEqual(bus.master_volume, 0.0)

    def test_load_bank_registers_events(self):
        bus = SoundEventBus()
        bank = SoundBankRegistry()
        bank.register("a", SoundCue("a.wav"))
        bus.load_bank(bank)
        self.assertIn("a", bus.registered_event_names())

    def test_registered_event_names_sorted(self):
        bus = SoundEventBus()
        bus.register("z", SoundCue("z.wav"))
        bus.register("a", SoundCue("a.wav"))
        self.assertEqual(bus.registered_event_names(), ["a", "z"])

    def test_stop_all_no_op_when_unavailable(self):
        bus = self._bus_with_bad_mixer()
        bus.stop_all()  # Should not raise

    def test_is_available_reflects_state(self):
        bus = SoundEventBus()
        bus._available = False
        self.assertFalse(bus.is_available)

    def test_exports_from_gui_do(self):
        self.assertTrue(hasattr(gui_do, "SoundEventBus"))
        self.assertTrue(hasattr(gui_do, "SoundCue"))
        self.assertTrue(hasattr(gui_do, "SoundBankRegistry"))
