# Melodic Time

Melodic Time maps clock time to musical tempo and measure positions. It provides a small, dependency-free way to convert between seconds, beats, and measures under a tempo map.

## Usage

```python
from melodic_time import Clock, Meter, TempoMap, measure_position_at

tempo_map = TempoMap([(0.0, 120.0), (5.0, 90.0)])
meter = Meter(4, 4)

print(measure_position_at(tempo_map, meter, 7.0))  # (5, 1)

clock = Clock(tempo_map)
print(clock.bpm())
```

## Why this library exists

Digital audio workstations and music software often need to convert between wall-clock time and musical positions. A metronome, a sequencer display, or a playback cursor must answer questions like "how many beats have elapsed at 3.2 seconds?" or "what measure are we in now?"

Melodic Time solves this for a linear tempo map: a piecewise constant series of tempo changes. It deliberately does not support gradual tempo changes such as accelerando or ritardando. That trade-off keeps the mapping simple, fast, and deterministic. If you need continuous tempo curves, this library is not the right tool.

## Awkward edge

The `Clock` class uses `time.monotonic` by default. If you create a clock and immediately call `ticks()`, the result is usually 0, but it may be 1 or more if the process is delayed between construction and the call. Tests and applications that require exact values should pass an explicit `time_func` to `Clock`.

## Exports

The package exports:

- `Clock`
- `Meter`
- `TempoMap`
- `TimeSignature`
- `beat_duration`
- `beat_index_at`
- `measure_at`
- `measure_position_at`
- `ticks_at`

## Performance

The window keeps a bounded buffer, so `push` is constant time and memory does not
grow with the length of the stream. `peak` and `trough` are linear in the window
size, which is the trade that keeps `push` cheap.

## Limitations

Values are coerced to floats, so very large integers lose precision. If you need
exact integer aggregates over a window, this is the wrong tool.

