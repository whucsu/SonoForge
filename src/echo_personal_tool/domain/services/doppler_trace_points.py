"""Helpers for manual Doppler VTI trace point lists."""

from __future__ import annotations

from collections.abc import Sequence


def finalize_vti_trace_points(
    points: Sequence[tuple[float, float]],
    *,
    min_dt_ms: float = 2.0,
) -> tuple[tuple[float, float], ...]:
    """Sort envelope samples by time, decimate, keep onset/offset on baseline."""
    if len(points) < 3:
        return tuple((float(t), float(v)) for t, v in points)

    onset = (float(points[0][0]), float(points[0][1]))
    offset = (float(points[-1][0]), float(points[-1][1]))
    middle = sorted(
        ((float(t), float(v)) for t, v in points[1:-1]),
        key=lambda item: item[0],
    )

    filtered: list[tuple[float, float]] = [onset]
    for time_ms, velocity_cm_s in middle:
        if time_ms <= filtered[-1][0]:
            continue
        if time_ms - filtered[-1][0] < min_dt_ms:
            continue
        filtered.append((time_ms, velocity_cm_s))

    if offset[0] <= filtered[-1][0]:
        offset = (filtered[-1][0] + min_dt_ms, offset[1])
    filtered.append(offset)
    return tuple(filtered)
