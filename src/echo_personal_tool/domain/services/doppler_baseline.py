"""Auto-detect Doppler zero-velocity baseline within a spectrogram ROI."""

from __future__ import annotations

import numpy as np

from echo_personal_tool.domain.models.doppler_roi import DopplerSpectrogramRoi


def detect_baseline_y(grayscale: np.ndarray, roi: DopplerSpectrogramRoi) -> float:
    """Return plot Y of the quietest horizontal band (min row variance) in ROI."""
    if grayscale.ndim != 2:
        return roi.y0 + roi.height / 2.0

    height, width = grayscale.shape[:2]
    x0 = int(max(0, min(roi.x0, width - 1)))
    y0 = int(max(0, min(roi.y0, height - 1)))
    x1 = int(max(x0 + 1, min(roi.x1, width)))
    y1 = int(max(y0 + 1, min(roi.y1, height)))

    patch = grayscale[y0:y1, x0:x1].astype(np.float64)
    if patch.size == 0:
        return roi.y0 + roi.height / 2.0

    row_var = np.var(patch, axis=1)
    if row_var.size == 0:
        return roi.y0 + roi.height / 2.0

    idx = int(np.argmin(row_var))
    return float(y0 + idx) + 0.5
