"""Core implementation for Melodic Time.

The library deliberately models musical time as a linear, tempo-mapped clock.
A clock's ticks progress at a rate determined by the tempo map. This design
keeps conversion between wall-clock seconds and musical positions simple and
predictable, at the cost of not representing gradual tempo changes such as
accelerando or ritardando.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, Optional, Sequence


@dataclass(frozen=True)
class TimeSignature:
    """A simple time signature represented by beats per measure and beat unit."""

    numerator: int
    denominator: int

    def __post_init__(self) -> None:
        if self.numerator <= 0:
            raise ValueError("numerator must be positive")
        if self.denominator <= 0:
            raise ValueError("denominator must be positive")


@dataclass(frozen=True)
class Meter:
    """Musical meter: how many beats per measure and what note value is one beat."""

    beats_per_measure: int
    beat_unit: int = 4

    def __post_init__(self) -> None:
        if self.beats_per_measure <= 0:
            raise ValueError("beats_per_measure must be positive")
        if self.beat_unit <= 0:
            raise ValueError("beat_unit must be positive")

    @property
    def time_signature(self) -> TimeSignature:
        """Return the equivalent TimeSignature."""
        return TimeSignature(self.beats_per_measure, self.beat_unit)


@dataclass(frozen=True)
class TempoMap:
    """A series of tempo changes over clock time.

    The first tempo starts at time 0. Each subsequent tempo takes effect at a
    precise clock time in seconds. Tempos must be positive and change times
    strictly increasing.
    """

    tempos: Sequence[tuple[float, float]]

    def __post_init__(self) -> None:
        if not self.tempos:
            raise ValueError("tempos must not be empty")

        previous_time = -1.0
        for change_time, bpm in self.tempos:
            if change_time < 0:
                raise ValueError("tempo change times must be non-negative")
            if bpm <= 0:
                raise ValueError("tempo must be positive")
            if change_time <= previous_time:
                raise ValueError("tempo change times must be strictly increasing")
            previous_time = change_time

        if self.tempos[0][0] != 0.0:
            raise ValueError("first tempo must start at time 0")

    def bpm_at(self, clock_time: float) -> float:
        """Return the beats per minute active at the given clock time."""
        if clock_time < 0:
            raise ValueError("clock_time must be non-negative")

        active_bpm = self.tempos[0][1]
        for change_time, bpm in self.tempos:
            if change_time > clock_time:
                break
            active_bpm = bpm
        return active_bpm

    def beat_duration_at(self, clock_time: float) -> float:
        """Return the duration of one beat in seconds at the given clock time."""
        return 60.0 / self.bpm_at(clock_time)

    def beats_elapsed_at(self, clock_time: float) -> float:
        """Return the number of beats elapsed from time 0 to clock_time."""
        if clock_time < 0:
            raise ValueError("clock_time must be non-negative")

        total_beats = 0.0
        previous_time = 0.0
        previous_bpm = self.tempos[0][1]

        for change_time, bpm in self.tempos[1:]:
            if change_time > clock_time:
                break
            total_beats += (change_time - previous_time) * (previous_bpm / 60.0)
            previous_time = change_time
            previous_bpm = bpm

        total_beats += (clock_time - previous_time) * (previous_bpm / 60.0)
        return total_beats


class Clock:
    """A musical clock that maps wall-clock time to ticks and vice versa.

    The clock advances monotonically and is initialised at tick 0. It accepts
    an optional time function for testing; defaults to time.monotonic.
    """

    def __init__(
        self,
        tempo_map: TempoMap,
        time_func: Optional[Callable[[], float]] = None,
    ) -> None:
        if time_func is None:
            import time as _time

            time_func = _time.monotonic

        self._tempo_map = tempo_map
        self._time_func = time_func
        self._origin = time_func()

    def ticks(self) -> int:
        """Return the current absolute tick count since clock creation."""
        return ticks_at(self._tempo_map, self._time_func() - self._origin)

    def bpm(self) -> float:
        """Return the current tempo in beats per minute."""
        return self._tempo_map.bpm_at(self._time_func() - self._origin)


def beat_duration(tempo_map: TempoMap, clock_time: float) -> float:
    """Return the duration of one beat in seconds at the given clock time."""
    return tempo_map.beat_duration_at(clock_time)


def beat_index_at(tempo_map: TempoMap, clock_time: float) -> int:
    """Return the zero-based beat index at the given clock time.

    The beat index is the floor of the total beats elapsed. Beat 0 starts at
    time 0.
    """
    return int(tempo_map.beats_elapsed_at(clock_time))


def measure_at(tempo_map: TempoMap, meter: Meter, clock_time: float) -> int:
    """Return the zero-based measure index at the given clock time."""
    beat = beat_index_at(tempo_map, clock_time)
    return beat // meter.beats_per_measure


def measure_position_at(
    tempo_map: TempoMap, meter: Meter, clock_time: float
) -> tuple[int, int]:
    """Return a (measure, beat_in_measure) tuple at the given clock time."""
    beat = beat_index_at(tempo_map, clock_time)
    return (beat // meter.beats_per_measure, beat % meter.beats_per_measure)


def ticks_at(tempo_map: TempoMap, clock_time: float) -> int:
    """Return the number of whole ticks elapsed at the given clock time.

    A tick is one millisecond of musical time, so one beat contains
    60000 / bpm ticks. The result is always an integer, rounded down.
    """
    beats = tempo_map.beats_elapsed_at(clock_time)
    return int(beats * 60000.0)
