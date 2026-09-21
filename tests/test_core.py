"""Tests for melodic_time.core."""

import unittest

from melodic_time.core import (
    Clock,
    Meter,
    TempoMap,
    TimeSignature,
    beat_duration,
    beat_index_at,
    measure_at,
    measure_position_at,
    ticks_at,
)


class TimeSignatureTest(unittest.TestCase):
    def test_valid_signature(self) -> None:
        ts = TimeSignature(4, 4)
        self.assertEqual(ts.numerator, 4)
        self.assertEqual(ts.denominator, 4)

    def test_invalid_numerator(self) -> None:
        with self.assertRaises(ValueError):
            TimeSignature(0, 4)

    def test_invalid_denominator(self) -> None:
        with self.assertRaises(ValueError):
            TimeSignature(4, 0)


class MeterTest(unittest.TestCase):
    def test_time_signature_property(self) -> None:
        meter = Meter(3, 4)
        self.assertEqual(meter.time_signature, TimeSignature(3, 4))

    def test_invalid_beats(self) -> None:
        with self.assertRaises(ValueError):
            Meter(0)


class TempoMapTest(unittest.TestCase):
    def test_empty_tempos_rejected(self) -> None:
        with self.assertRaises(ValueError):
            TempoMap([])

    def test_first_tempo_not_at_zero_rejected(self) -> None:
        with self.assertRaises(ValueError):
            TempoMap([(1.0, 120.0)])

    def test_non_positive_bpm_rejected(self) -> None:
        with self.assertRaises(ValueError):
            TempoMap([(0.0, 0.0)])

    def test_out_of_order_changes_rejected(self) -> None:
        with self.assertRaises(ValueError):
            TempoMap([(0.0, 120.0), (2.0, 100.0), (1.0, 110.0)])

    def test_bpm_at_single_tempo(self) -> None:
        tempo_map = TempoMap([(0.0, 120.0)])
        self.assertEqual(tempo_map.bpm_at(10.0), 120.0)

    def test_bpm_at_exact_change(self) -> None:
        tempo_map = TempoMap([(0.0, 120.0), (5.0, 90.0)])
        self.assertEqual(tempo_map.bpm_at(5.0), 90.0)

    def test_bpm_at_just_before_change(self) -> None:
        tempo_map = TempoMap([(0.0, 120.0), (5.0, 90.0)])
        self.assertEqual(tempo_map.bpm_at(4.999), 120.0)

    def test_beats_elapsed_no_tempo_change(self) -> None:
        tempo_map = TempoMap([(0.0, 60.0)])
        self.assertAlmostEqual(tempo_map.beats_elapsed_at(2.0), 2.0)

    def test_beats_elapsed_with_tempo_change(self) -> None:
        tempo_map = TempoMap([(0.0, 60.0), (2.0, 120.0)])
        # 2 seconds at 60 bpm = 2 beats, then 1 second at 120 bpm = 2 beats
        self.assertAlmostEqual(tempo_map.beats_elapsed_at(3.0), 4.0)

    def test_beats_elapsed_before_first_change(self) -> None:
        tempo_map = TempoMap([(0.0, 60.0), (10.0, 120.0)])
        self.assertAlmostEqual(tempo_map.beats_elapsed_at(5.0), 5.0)


class ClockTest(unittest.TestCase):
    def test_clock_uses_time_function(self) -> None:
        current_time = [0.0]

        def fake_time() -> float:
            return current_time[0]

        tempo_map = TempoMap([(0.0, 60.0)])
        clock = Clock(tempo_map, fake_time)
        self.assertEqual(clock.ticks(), 0)

        current_time[0] = 1.0
        self.assertEqual(clock.ticks(), 60000)

    def test_clock_bpm(self) -> None:
        current_time = [0.0]

        def fake_time() -> float:
            return current_time[0]

        tempo_map = TempoMap([(0.0, 100.0)])
        clock = Clock(tempo_map, fake_time)
        self.assertEqual(clock.bpm(), 100.0)


class FunctionTest(unittest.TestCase):
    def setUp(self) -> None:
        self.tempo_map = TempoMap([(0.0, 120.0)])
        self.meter = Meter(4, 4)

    def test_beat_duration(self) -> None:
        self.assertAlmostEqual(beat_duration(self.tempo_map, 0.0), 0.5)

    def test_beat_index_at_start(self) -> None:
        self.assertEqual(beat_index_at(self.tempo_map, 0.0), 0)

    def test_beat_index_at_one_beat(self) -> None:
        self.assertEqual(beat_index_at(self.tempo_map, 0.5), 1)

    def test_measure_at_start(self) -> None:
        self.assertEqual(measure_at(self.tempo_map, self.meter, 0.0), 0)

    def test_measure_at_second_measure(self) -> None:
        # 2 seconds at 120 bpm = 4 beats = measure 1
        self.assertEqual(measure_at(self.tempo_map, self.meter, 2.0), 1)

    def test_measure_position_at(self) -> None:
        # 2.25 seconds at 120 bpm = 4.5 beats = measure 1, beat 0
        self.assertEqual(measure_position_at(self.tempo_map, self.meter, 2.25), (1, 0))

    def test_ticks_at_start(self) -> None:
        self.assertEqual(ticks_at(self.tempo_map, 0.0), 0)

    def test_ticks_at_one_beat(self) -> None:
        self.assertEqual(ticks_at(self.tempo_map, 0.5), 60000)

    def test_ticks_at_fractional(self) -> None:
        # 0.25 seconds at 120 bpm = 0.5 beat = 30000 ticks
        self.assertEqual(ticks_at(self.tempo_map, 0.25), 30000)


if __name__ == "__main__":
    unittest.main()
