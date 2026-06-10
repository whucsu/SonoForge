"""2D image viewer using PyQtGraph."""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtWidgets import QVBoxLayout, QWidget


class ViewerWidget(QWidget):
    """Display a single grayscale frame with PyQtGraph ImageItem."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._graphics = pg.GraphicsLayoutWidget()
        self._view = self._graphics.addViewBox(lockAspect=True, invertY=True)
        self._image_item = pg.ImageItem(axisOrder="row-major")
        self._image_item.setAutoDownsample(True)
        self._view.addItem(self._image_item)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.addWidget(self._graphics)

    def show_frame(self, pixels: np.ndarray) -> None:
        """Render a 2D numpy array (H, W) or (H, W, C)."""
        frame = np.asarray(pixels)
        if frame.ndim == 3:
            frame = frame[..., 0]
        self._image_item.setImage(frame, autoLevels=True)

    def clear(self) -> None:
        self._image_item.clear()
