from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MModeScanLine:
    start: tuple[float, float]
    end: tuple[float, float]
    num_samples: int = 256


@dataclass(frozen=True)
class MModeState:
    active: bool = False
    scan_line: MModeScanLine | None = None
    buffer_width: int = 512
    sweep_x: int = 0


@dataclass(frozen=True)
class MModeCaliperMeasurement:
    kind: str  # "distance" | "time"
    start: tuple[float, float]
    end: tuple[float, float]
    value_mm: float | None = None
    value_ms: float | None = None
