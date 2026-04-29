"""Tests for ParticleSystem, Emitter, and ParticleLayer."""
import unittest
from unittest.mock import MagicMock

import pygame
from pygame import Rect, Surface

from gui_do.graphics.particle_system import ParticleSystem, Emitter, ParticleLayer


def _surface(w: int = 640, h: int = 480) -> Surface:
    pygame.init()
    return Surface((w, h))


class TestEmitterDefaults(unittest.TestCase):
    def test_instantiates_with_minimal_args(self) -> None:
        e = Emitter(x=0, y=0)
        self.assertTrue(e.active)
        self.assertGreaterEqual(e.rate, 0)  # rate has a non-zero default (30.0)

    def test_burst_count_default(self) -> None:
        e = Emitter(x=0, y=0)
        self.assertIsNotNone(e.burst_count)


class TestParticleSystemEmpty(unittest.TestCase):
    def test_no_particles_initially(self) -> None:
        ps = ParticleSystem()
        self.assertEqual(ps.active_particle_count, 0)


class TestParticleSystemAddRemoveEmitter(unittest.TestCase):
    def test_add_emitter(self) -> None:
        ps = ParticleSystem()
        e = Emitter(x=100, y=100)
        ps.add_emitter(e)
        self.assertEqual(ps.emitter_count, 1)

    def test_remove_emitter(self) -> None:
        ps = ParticleSystem()
        e = Emitter(x=100, y=100)
        ps.add_emitter(e)
        ps.remove_emitter(e)
        self.assertEqual(ps.emitter_count, 0)

    def test_clear_removes_all(self) -> None:
        ps = ParticleSystem()
        ps.add_emitter(Emitter(x=0, y=0))
        ps.add_emitter(Emitter(x=50, y=50))
        ps.clear()
        self.assertEqual(ps.emitter_count, 0)


class TestParticleSystemBurstEmission(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    def test_burst_spawns_particles(self) -> None:
        ps = ParticleSystem(max_particles=200)
        burst = Emitter(
            x=200, y=200,
            rate=0,
            burst_count=10,
            lifetime=(0.5, 1.0),
            speed=(50, 100),
            angle_range=(0, 360),
            size=(2, 4),
            colors=[(255, 0, 0)],
        )
        ps.add_emitter(burst)
        ps.update(0.016)
        self.assertGreater(ps.active_particle_count, 0)

    def test_continuous_rate_emitter(self) -> None:
        ps = ParticleSystem(max_particles=200)
        e = Emitter(
            x=100, y=100,
            rate=60,
            lifetime=(0.5, 0.5),
            speed=(20, 50),
            angle_range=(0, 360),
            size=(2, 3),
            colors=[(0, 255, 0)],
        )
        ps.add_emitter(e)
        ps.update(0.1)  # should emit ~6 particles at rate=60/s
        self.assertGreater(ps.active_particle_count, 0)


class TestParticleSystemUpdateKillsOld(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    def test_particles_die_after_lifetime(self) -> None:
        ps = ParticleSystem(max_particles=100)
        burst = Emitter(
            x=0, y=0,
            rate=0,
            burst_count=5,
            lifetime=(0.1, 0.1),
            speed=(10, 20),
            angle_range=(0, 360),
            size=(2, 2),
            colors=[(100, 100, 100)],
        )
        ps.add_emitter(burst)
        ps.update(0.016)
        count_after_spawn = ps.active_particle_count
        self.assertGreater(count_after_spawn, 0)
        ps.update(0.2)  # lifetime exceeded
        self.assertEqual(ps.active_particle_count, 0)


class TestParticleSystemDraw(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    def test_draw_does_not_raise(self) -> None:
        ps = ParticleSystem(max_particles=50)
        burst = Emitter(
            x=50, y=50,
            rate=0,
            burst_count=5,
            lifetime=(1.0, 1.0),
            speed=(10, 20),
            angle_range=(0, 360),
            size=(3, 5),
            colors=[(255, 255, 0)],
        )
        ps.add_emitter(burst)
        ps.update(0.016)
        surface = _surface()
        ps.draw(surface)  # should not raise


class TestParticleLayer(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        pygame.init()

    def test_particle_layer_is_ui_node(self) -> None:
        from gui_do.controls.base.ui_node import UiNode
        layer = ParticleLayer("layer", Rect(0, 0, 640, 480))
        self.assertIsInstance(layer, UiNode)

    def test_has_particle_system(self) -> None:
        layer = ParticleLayer("layer", Rect(0, 0, 640, 480))
        self.assertIsInstance(layer.particle_system, ParticleSystem)

    def test_update_particles_delegates(self) -> None:
        layer = ParticleLayer("layer", Rect(0, 0, 640, 480))
        # Should not raise
        layer.update_particles(0.016)
