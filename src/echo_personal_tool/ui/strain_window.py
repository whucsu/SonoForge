"""Separate window for STE strain visualization — quad-view layout."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QCheckBox,
    QFrame,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from echo_personal_tool.domain.models.speckle import StrainResult

logger = logging.getLogger(__name__)


class CinePanel(QWidget):
    """Single cine panel with image viewer, contour overlay, and info labels."""

    def __init__(self, title: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._title = title
        self.setObjectName("cinePanel")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(2)

        # Title + info row
        header = QHBoxLayout()
        self._title_label = QLabel(title)
        self._title_label.setStyleSheet("font-weight: bold; color: #e0e0e0; font-size: 12px;")
        header.addWidget(self._title_label)

        self._info_label = QLabel("")
        self._info_label.setStyleSheet("color: #80cbc4; font-size: 11px;")
        self._info_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        header.addWidget(self._info_label)
        layout.addLayout(header)

        # PyQtGraph plot widget
        self._plot = pg.PlotWidget()
        self._plot.setBackground("black")
        self._plot.hideAxis("left")
        self._plot.hideAxis("bottom")
        self._plot.setAspectLocked(True)
        self._plot.setMouseEnabled(x=False, y=False)
        self._plot.setMinimumHeight(200)
        layout.addWidget(self._plot, stretch=1)

        # Bottom row: HR + frame counter
        footer = QHBoxLayout()
        self._hr_label = QLabel("HR: --")
        self._hr_label.setStyleSheet("color: #4caf50; font-size: 10px;")
        footer.addWidget(self._hr_label)
        footer.addStretch()
        self._frame_label = QLabel("--/--")
        self._frame_label.setStyleSheet("color: #9e9e9e; font-size: 10px;")
        footer.addWidget(self._frame_label)
        layout.addLayout(footer)

        # Contour items
        self._contour_item: pg.PlotDataItem | None = None
        self._kernel_scatter: pg.ScatterPlotItem | None = None
        self._segment_labels: list[pg.TextItem] = []

    @property
    def plot(self) -> pg.PlotWidget:
        return self._plot

    def set_title_info(self, text: str) -> None:
        self._info_label.setText(text)

    def set_hr(self, hr: float) -> None:
        self._hr_label.setText(f"HR: {hr:.0f}")

    def set_frame(self, current: int, total: int) -> None:
        self._frame_label.setText(f"{current}/{total}")

    def show_contour(self, points: np.ndarray, color: str = "#ff1744") -> None:
        """Draw closed contour on the plot."""
        if self._contour_item is not None:
            self._plot.removeItem(self._contour_item)
        if len(points) < 3:
            return
        x = np.append(points[:, 0], points[0, 0])
        y = np.append(points[:, 1], points[0, 1])
        pen = pg.mkPen(color, width=2)
        self._contour_item = pg.PlotDataItem(x, y, pen=pen)
        self._contour_item.setZValue(5)
        self._plot.addItem(self._contour_item)

    def show_kernels(
        self,
        positions: np.ndarray,
        ncc_scores: np.ndarray | None = None,
        valid_mask: np.ndarray | None = None,
    ) -> None:
        """Draw tracking kernels as squares, colored by quality."""
        if self._kernel_scatter is not None:
            self._plot.removeItem(self._kernel_scatter)

        if len(positions) == 0:
            return

        x = positions[:, 0]
        y = positions[:, 1]

        if ncc_scores is not None and valid_mask is not None:
            colors = []
            for i in range(len(positions)):
                score = float(ncc_scores[i]) if i < len(ncc_scores) else 0.0
                is_valid = valid_mask[i] if i < len(valid_mask) else False
                if not is_valid or score < 0.3:
                    colors.append(pg.mkBrush(255, 0, 0, 200))  # red = rejected
                elif score < 0.5:
                    colors.append(pg.mkBrush(255, 193, 7, 200))  # yellow = low
                else:
                    colors.append(pg.mkBrush(255, 255, 255, 200))  # white = good
            self._kernel_scatter = pg.ScatterPlotItem(
                x=x, y=y, pen=None, brush=colors, symbol="s", size=6
            )
        else:
            self._kernel_scatter = pg.ScatterPlotItem(
                x=x, y=y, pen=pg.mkPen("w", width=0.5),
                brush=pg.mkBrush(255, 255, 255, 180), symbol="s", size=6
            )

        self._kernel_scatter.setZValue(10)
        self._plot.addItem(self._kernel_scatter)

    def show_segment_labels(
        self,
        positions: np.ndarray,
        labels: list[str],
        segments: list[int],
    ) -> None:
        """Draw segment name labels near kernel clusters."""
        # Clear old labels
        for item in self._segment_labels:
            self._plot.removeItem(item)
        self._segment_labels.clear()

        if len(positions) == 0 or len(labels) == 0:
            return

        # Group positions by segment
        segment_positions: dict[int, list[np.ndarray]] = {}
        for i, seg in enumerate(segments):
            if seg > 0 and i < len(positions):
                segment_positions.setdefault(seg, []).append(positions[i])

        for seg, label_text in zip(segments, labels):
            if seg not in segment_positions:
                continue
            pts = np.array(segment_positions[seg])
            centroid = pts.mean(axis=0)

            text_item = pg.TextItem(
                label_text,
                color=(200, 200, 200),
                anchor=(0.5, 0.5),
            )
            text_item.setPos(centroid[0], centroid[1])
            text_item.setFont(QFont("sans-serif", 8))
            text_item.setZValue(20)
            self._plot.addItem(text_item)
            self._segment_labels.append(text_item)

    def clear(self) -> None:
        if self._contour_item is not None:
            self._plot.removeItem(self._contour_item)
            self._contour_item = None
        if self._kernel_scatter is not None:
            self._plot.removeItem(self._kernel_scatter)
            self._kernel_scatter = None
        for item in self._segment_labels:
            self._plot.removeItem(item)
        self._segment_labels.clear()
        self._info_label.setText("")
        self._hr_label.setText("HR: --")
        self._frame_label.setText("--/--")


class BullseyePlaceholder(QWidget):
    """Placeholder for Bull's Eye plot — to be replaced in Phase 5."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumHeight(200)
        self._plot = pg.PlotWidget()
        self._plot.setBackground("black")
        self._plot.hideAxis("left")
        self._plot.hideAxis("bottom")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(2, 2, 2, 2)

        title = QLabel("17-Segment Bull's Eye")
        title.setStyleSheet("font-weight: bold; color: #e0e0e0; font-size: 12px;")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        layout.addWidget(self._plot, stretch=1)

        # Draw placeholder circle
        theta = np.linspace(0, 2 * np.pi, 100)
        r_outer = 0.9
        r_mid = 0.6
        r_inner = 0.3
        cx, cy = 0.5, 0.5

        pen = pg.mkPen("#42a5f5", width=1)
        self._plot.plot(cx + r_outer * np.cos(theta), cy + r_outer * np.sin(theta), pen=pen)
        self._plot.plot(cx + r_mid * np.cos(theta), cy + r_mid * np.sin(theta), pen=pen)
        self._plot.plot(cx + r_inner * np.cos(theta), cy + r_inner * np.sin(theta), pen=pen)

        # Radial lines
        for angle in np.linspace(0, 2 * np.pi, 7)[:-1]:
            self._plot.plot(
                [cx, cx + r_outer * np.cos(angle)],
                [cy, cy + r_outer * np.sin(angle)],
                pen=pen,
            )

        self._plot.setXRange(0, 1)
        self._plot.setYRange(0, 1)
        self._plot.setAspectLocked(True)


class SummaryTable(QWidget):
    """Summary metrics table (GLS, EF, volumes, HR)."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setMinimumWidth(220)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        title = QLabel("Summary")
        title.setStyleSheet("font-weight: bold; color: #e0e0e0; font-size: 12px;")
        layout.addWidget(title)

        self._rows: dict[str, tuple[QLabel, QLabel]] = {}
        row_defs = [
            ("gls", "GLS (avg)", "--"),
            ("gls_a4c", "GLS A4C", "--"),
            ("gls_a2c", "GLS A2C", "--"),
            ("gls_dao", "GLS DAO", "--"),
            ("ef", "EF (biplane)", "--"),
            ("edv", "EDV", "--"),
            ("esv", "ESV", "--"),
            ("hr", "Heart Rate", "--"),
        ]
        for key, label_text, default_val in row_defs:
            row = QHBoxLayout()
            lbl = QLabel(label_text)
            lbl.setStyleSheet("color: #bdbdbd; font-size: 11px;")
            val = QLabel(default_val)
            val.setStyleSheet("color: #ffd54f; font-weight: bold; font-size: 11px;")
            val.setAlignment(Qt.AlignmentFlag.AlignRight)
            row.addWidget(lbl)
            row.addStretch()
            row.addWidget(val)
            layout.addLayout(row)
            self._rows[key] = (lbl, val)

        layout.addStretch()

    def update_values(self, **kwargs: float | str | None) -> None:
        """Update table values. Accepts: gls, gls_a4c, gls_a2c, gls_dao, ef, edv, esv, hr."""
        for key, val in kwargs.items():
            if key in self._rows:
                _, val_label = self._rows[key]
                if val is None:
                    val_label.setText("--")
                elif isinstance(val, str):
                    val_label.setText(val)
                else:
                    val_label.setText(f"{val:.1f}")


class ControlPanel(QWidget):
    """Left-side control panel for Strain Window."""

    view_toggled = Signal(str, bool)  # view_name, checked

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedWidth(180)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(6)

        # View toggles
        group_views = QGroupBox("Views")
        group_views.setStyleSheet("QGroupBox { font-weight: bold; color: #e0e0e0; }")
        views_layout = QVBoxLayout()

        self._cb_a4c = QCheckBox("A4C")
        self._cb_a4c.setChecked(True)
        self._cb_a4c.setStyleSheet("color: #e0e0e0;")
        self._cb_a4c.toggled.connect(lambda c: self.view_toggled.emit("A4C", c))
        views_layout.addWidget(self._cb_a4c)

        self._cb_a2c = QCheckBox("A2C")
        self._cb_a2c.setChecked(True)
        self._cb_a2c.setStyleSheet("color: #e0e0e0;")
        self._cb_a2c.toggled.connect(lambda c: self.view_toggled.emit("A2C", c))
        views_layout.addWidget(self._cb_a2c)

        self._cb_dao = QCheckBox("DAO (A3C)")
        self._cb_dao.setChecked(True)
        self._cb_dao.setStyleSheet("color: #e0e0e0;")
        self._cb_dao.toggled.connect(lambda c: self.view_toggled.emit("DAO", c))
        views_layout.addWidget(self._cb_dao)

        group_views.setLayout(views_layout)
        layout.addWidget(group_views)

        # Quality info
        group_quality = QGroupBox("Quality Gate")
        group_quality.setStyleSheet("QGroupBox { font-weight: bold; color: #e0e0e0; }")
        quality_layout = QVBoxLayout()

        self._quality_label = QLabel("-- / --")
        self._quality_label.setStyleSheet("color: #80cbc4; font-size: 11px;")
        quality_layout.addWidget(self._quality_label)

        self._rejected_label = QLabel("")
        self._rejected_label.setStyleSheet("color: #ff9800; font-size: 10px;")
        self._rejected_label.setWordWrap(True)
        quality_layout.addWidget(self._rejected_label)

        group_quality.setLayout(quality_layout)
        layout.addWidget(group_quality)

        # Actions
        group_actions = QGroupBox("Actions")
        group_actions.setStyleSheet("QGroupBox { font-weight: bold; color: #e0e0e0; }")
        actions_layout = QVBoxLayout()

        self._btn_save = QPushButton("Save Deformation")
        self._btn_save.setEnabled(False)
        actions_layout.addWidget(self._btn_save)

        self._btn_export = QPushButton("Export PNG")
        self._btn_export.setEnabled(False)
        actions_layout.addWidget(self._btn_export)

        self._btn_close = QPushButton("Close")
        actions_layout.addWidget(self._btn_close)

        group_actions.setLayout(actions_layout)
        layout.addWidget(group_actions)

        layout.addStretch()

    def update_quality(self, accepted: int, total: int, rejected: int) -> None:
        if total > 0:
            pct = (accepted / total) * 100.0
            self._quality_label.setText(f"{accepted} / {total} ({pct:.0f}%)")
        else:
            self._quality_label.setText("-- / --")

        if rejected > 0:
            self._rejected_label.setText(f"{rejected} kernels rejected")
        else:
            self._rejected_label.setText("")


class StrainWindow(QMainWindow):
    """Separate window for STE strain visualization with quad-view layout."""

    closed = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Strain Analysis")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(4, 4, 4, 4)
        main_layout.setSpacing(4)

        # Splitter: control panel | content
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Control panel
        self._control = ControlPanel()
        self._control.view_toggled.connect(self._on_view_toggled)
        self._control._btn_close.clicked.connect(self.close)
        splitter.addWidget(self._control)

        # Content area
        content = QWidget()
        content_layout = QHBoxLayout(content)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(4)

        # Quad view (2x2 grid)
        quad = QWidget()
        quad_layout = QGridLayout(quad)
        quad_layout.setContentsMargins(0, 0, 0, 0)
        quad_layout.setSpacing(4)

        self._panel_a4c = CinePanel("A4C")
        self._panel_a2c = CinePanel("A2C")
        self._panel_dao = CinePanel("DAO (A3C)")
        self._panel_bullseye = BullseyePlaceholder()

        quad_layout.addWidget(self._panel_a4c, 0, 0)
        quad_layout.addWidget(self._panel_a2c, 0, 1)
        quad_layout.addWidget(self._panel_dao, 1, 0)
        quad_layout.addWidget(self._panel_bullseye, 1, 1)

        content_layout.addWidget(quad, stretch=3)

        # Summary table
        self._summary = SummaryTable()
        content_layout.addWidget(self._summary, stretch=1)

        splitter.addWidget(content)
        splitter.setSizes([180, 1220])

        main_layout.addWidget(splitter)

        # State
        self._result: StrainResult | None = None

    def show_result(self, result: StrainResult) -> None:
        """Display strain results in quad-view layout."""
        self._result = result

        # Update quality gate info
        self._control.update_quality(
            result.kernels_accepted_count,
            result.kernels_total_count,
            result.kernels_rejected_count,
        )

        # Update summary table
        self._summary.update_values(
            gls=result.gls,
            hr=result.heart_rate_bpm if result.heart_rate_bpm > 0 else None,
        )

        # Update A4C panel
        self._panel_a4c.set_title_info(f"GLS: {result.gls:.1f}%")
        if result.ed_contour is not None and len(result.ed_contour) >= 3:
            self._panel_a4c.show_contour(result.ed_contour, color="#ff1744")
        if result.tracked_ed_positions is not None:
            endo_mask = np.array([k.layer == "endo" for k in result.kernels], dtype=bool)
            endo_positions = result.tracked_ed_positions[endo_mask]
            if result.es_ncc_scores is not None and result.es_valid_mask is not None:
                endo_ncc = result.es_ncc_scores[endo_mask]
                endo_valid = result.es_valid_mask[endo_mask]
                self._panel_a4c.show_kernels(endo_positions, endo_ncc, endo_valid)
            else:
                self._panel_a4c.show_kernels(endo_positions)
        self._panel_a4c.set_hr(result.heart_rate_bpm)
        self._panel_a4c.set_frame(result.es_index, len(result.longitudinal) if result.longitudinal is not None else 0)

        # Placeholder panels — show same data for now
        self._panel_a2c.set_title_info(f"GLS: {result.gls:.1f}%")
        self._panel_dao.set_title_info(f"GLS: {result.gls:.1f}%")

        if not self.isVisible():
            self.show()
        self.raise_()
        self.activateWindow()

    def _on_view_toggled(self, view: str, checked: bool) -> None:
        """Handle view checkbox toggle."""
        panel_map = {
            "A4C": self._panel_a4c,
            "A2C": self._panel_a2c,
            "DAO": self._panel_dao,
        }
        panel = panel_map.get(view)
        if panel is not None:
            panel.setVisible(checked)

    def closeEvent(self, event) -> None:
        self.closed.emit()
        super().closeEvent(event)
