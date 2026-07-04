"""Pure Qt animation helpers for micro-UX feedback."""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import TYPE_CHECKING

from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QTimer,
    Qt,
    QObject,
    QEvent,
)
from PySide6.QtGui import QEnterEvent, QColor
from PySide6.QtWidgets import (
    QDialog,
    QGraphicsOpacityEffect,
    QPushButton,
    QWidget,
)

if TYPE_CHECKING:
    from collections.abc import Generator

logger = logging.getLogger(__name__)

_MAX_ANIMATIONS_PER_WIDGET = 1


class HoverButtonMixin(QObject):
    """Event filter for smooth hover lerp (100ms) on QPushButton/QToolButton.

    Apply via: HoverButtonMixin.install(button)
    """

    _instances: dict[QWidget, HoverButtonMixin] = {}

    def __init__(self, widget: QWidget) -> None:
        super().__init__(widget)
        self._widget = widget
        self._normal_bg: str = ""
        self._hover_bg: str = ""
        self._pressed_bg: str = ""
        self._anim: QPropertyAnimation | None = None
        widget.installEventFilter(self)

    @classmethod
    def install(cls, widget: QWidget) -> HoverButtonMixin:
        """Install hover mixin on a widget (idempotent)."""
        if widget not in cls._instances:
            cls._instances[widget] = cls(widget)
        return cls._instances[widget]

    def _read_colors(self) -> None:
        """Read colors from the current theme palette."""
        from echo_personal_tool.presentation.echopac_theme import get_theme_palette
        p = get_theme_palette()
        self._normal_bg = p.get("bg_button", "#2e4054")
        self._hover_bg = p.get("bg_button_hover", "#3a5068")
        self._pressed_bg = p.get("bg_button_pressed", "#1e2a38")

    def _animate_bg(self, target: str, duration_ms: int = 100) -> None:
        """Animate background-color to target."""
        if self._anim is not None:
            self._anim.stop()

        if not self._normal_bg:
            self._read_colors()

        self._widget.setStyleSheet(
            self._widget.styleSheet().replace(
                f"background: {self._normal_bg}",
                f"background: {target}"
            ) if self._normal_bg else ""
        )

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:
        """Handle enter/leave/press events for hover lerp."""
        if obj is not self._widget:
            return False

        if event.type() == QEvent.Type.Enter:
            if not self._normal_bg:
                self._read_colors()
            self._widget.setStyleSheet(
                self._widget.styleSheet().replace(
                    f"background: {self._normal_bg}",
                    f"background: {self._hover_bg}"
                ) if self._normal_bg else ""
            )
        elif event.type() == QEvent.Type.Leave:
            if not self._normal_bg:
                self._read_colors()
            self._widget.setStyleSheet(
                self._widget.styleSheet().replace(
                    f"background: {self._hover_bg}",
                    f"background: {self._normal_bg}"
                ) if self._normal_bg else ""
            )
        elif event.type() == QEvent.Type.MouseButtonPress:
            if not self._normal_bg:
                self._read_colors()
            self._widget.setStyleSheet(
                self._widget.styleSheet().replace(
                    f"background: {self._hover_bg}",
                    f"background: {self._pressed_bg}"
                ) if self._normal_bg else ""
            )
        elif event.type() == QEvent.Type.MouseButtonRelease:
            if not self._normal_bg:
                self._read_colors()
            self._widget.setStyleSheet(
                self._widget.styleSheet().replace(
                    f"background: {self._pressed_bg}",
                    f"background: {self._hover_bg}"
                ) if self._normal_bg else ""
            )

        return False


def animate_widget_opacity(
    widget: QWidget,
    from_val: float,
    to_val: float,
    duration_ms: int = 200,
    easing: QEasingCurve.Type = QEasingCurve.Type.OutCubic,
    on_finished: callable | None = None,
) -> QPropertyAnimation:
    """Animate widget opacity from *from_val* to *to_val*."""
    effect = widget.graphicsEffect()
    if not isinstance(effect, QGraphicsOpacityEffect):
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)

    anim = QPropertyAnimation(effect, b"opacity")
    anim.setDuration(duration_ms)
    anim.setStartValue(from_val)
    anim.setEndValue(to_val)
    anim.setEasingCurve(easing)
    if on_finished:
        anim.finished.connect(on_finished)
    anim.start()
    # Prevent GC — keep reference on widget
    widget.setProperty("_opacity_anim", anim)
    return anim


def show_dialog_animated(dialog: QDialog, duration_ms: int = 200) -> None:
    """Fade-in + scale 0.95→1.0 on dialog open."""
    dialog.setWindowOpacity(0.0)
    dialog.show()

    fade = animate_widget_opacity(dialog, 0.0, 1.0, duration_ms)

    # Scale animation via geometry
    geo = dialog.geometry()
    w, h = geo.width(), geo.height()
    dx, dy = int(w * 0.025), int(h * 0.025)
    dialog.setGeometry(geo.x() + dx, geo.y() + dy, w - 2 * dx, h - 2 * dy)

    scale = QPropertyAnimation(dialog, b"geometry")
    scale.setDuration(duration_ms)
    scale.setStartValue(dialog.geometry())
    scale.setEndValue(geo)
    scale.setEasingCurve(QEasingCurve.Type.OutCubic)
    scale.start()
    dialog.setProperty("_scale_anim", scale)
    dialog.setProperty("_fade_anim", fade)


def hide_dialog_animated(
    dialog: QDialog,
    on_done: callable | None = None,
    duration_ms: int = 120,
) -> None:
    """Fade-out dialog, then call *on_done* (typically accept/reject)."""
    anim = animate_widget_opacity(
        dialog,
        dialog.windowOpacity(),
        0.0,
        duration_ms,
        easing=QEasingCurve.Type.Linear,
        on_finished=on_done,
    )
    dialog.setProperty("_hide_anim", anim)


@contextmanager
def loading_button(btn: QPushButton, text: str = "...") -> Generator[None, None, None]:
    """Context manager that disables button and shows *text* while async work runs."""
    old_text = btn.text()
    old_enabled = btn.isEnabled()
    btn.setText(text)
    btn.setEnabled(False)
    try:
        yield
    finally:
        btn.setText(old_text)
        btn.setEnabled(old_enabled)


def exec_animated(dialog: QDialog, duration_ms: int = 200) -> int:
    """Show dialog with fade+scale animation and return exec result."""
    show_dialog_animated(dialog, duration_ms)
    return dialog.exec()
