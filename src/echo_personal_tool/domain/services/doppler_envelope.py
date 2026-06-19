"""Semi-automatic Doppler spectral envelope tracing."""

from __future__ import annotations

import numpy as np

from echo_personal_tool.domain.models.doppler_roi import DopplerSpectrogramRoi


def _envelope_row_in_column(
    column: np.ndarray,
    baseline_row: int,
    *,
    above_baseline: bool,
    min_intensity: float,
) -> int | None:
    if above_baseline:
        end = baseline_row + 1 if baseline_row >= 0 else 1
        search = column[:end]
    else:
        search = column[baseline_row:] if baseline_row < column.size else column[-1:]

    if search.size == 0:
        return None

    peak = float(search.max())
    if peak < min_intensity:
        return None

    row = int(np.argmax(search))
    if not above_baseline:
        row = baseline_row + row
    return row


def _active_column_range(
    patch: np.ndarray,
    baseline_row: int,
    *,
    above_baseline: bool,
    min_intensity: float,
) -> tuple[int, int] | None:
    active: list[int] = []
    for col in range(patch.shape[1]):
        if (
            _envelope_row_in_column(
                patch[:, col],
                baseline_row,
                above_baseline=above_baseline,
                min_intensity=min_intensity,
            )
            is not None
        ):
            active.append(col)
    if not active:
        return None
    return active[0], active[-1]


def trace_envelope(
    grayscale: np.ndarray,
    roi: DopplerSpectrogramRoi,
    baseline_y_px: float,
    *,
    num_samples: int = 32,
    above_baseline: bool = True,
    start_at_baseline: bool = True,
) -> tuple[tuple[float, float], ...]:
    """Column-wise intensity ridge inside spectral flow; plot coordinates (x, y).

    Skips empty margin columns at ROI edges and can anchor the first point on the
    baseline at spectral onset (start of VTI trace).
    """
    if grayscale.ndim != 2 or num_samples < 2:
        return ()

    height, width = grayscale.shape[:2]
    x0 = int(max(0, min(roi.x0, width - 1)))
    y0 = int(max(0, min(roi.y0, height - 1)))
    x1 = int(max(x0 + 1, min(roi.x1, width)))
    y1 = int(max(y0 + 1, min(roi.y1, height)))

    patch = grayscale[y0:y1, x0:x1].astype(np.float64)
    if patch.size == 0:
        return ()

    baseline_row = int(round(baseline_y_px - y0))
    baseline_row = max(0, min(baseline_row, patch.shape[0] - 1))
    baseline_plot_y = float(baseline_y_px)

    min_intensity = max(12.0, float(patch.max()) * 0.08)
    column_range = _active_column_range(
        patch,
        baseline_row,
        above_baseline=above_baseline,
        min_intensity=min_intensity,
    )
    if column_range is None:
        return ()

    col_start, col_end = column_range
    if col_end <= col_start:
        return ()

    cols = np.linspace(col_start, col_end, num=num_samples, dtype=int)
    points: list[tuple[float, float]] = []

    if start_at_baseline:
        onset_x = float(x0 + col_start)
        points.append((onset_x, baseline_plot_y))

    for col in cols:
        row = _envelope_row_in_column(
            patch[:, col],
            baseline_row,
            above_baseline=above_baseline,
            min_intensity=min_intensity,
        )
        if row is None:
            continue
        plot_x = float(x0 + col)
        plot_y = float(y0 + row) + 0.5
        if points and abs(plot_x - points[-1][0]) < 0.5 and abs(plot_y - points[-1][1]) < 0.5:
            continue
        points.append((plot_x, plot_y))

    if len(points) < 2:
        return ()
    return tuple(points)


def trace_envelope_above_baseline(trace_label: str) -> bool:
    """TR/PR regurgitation envelopes are usually below the baseline."""
    normalized = trace_label.strip().upper()
    return normalized not in {"VTI TR", "VTI PR", "TR", "PR"}
