"""Vertical icon bar (VS Code style, ~48px)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (
    QPushButton,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

_ICON_DIR = Path(__file__).resolve().parent.parent / "resources" / "icons"


def _load_icon(name: str) -> QIcon:
    from echo_personal_tool.presentation.echopac_theme import get_theme_palette
    svg_path = _ICON_DIR / f"{name}.svg"
    if svg_path.is_file():
        svg_text = svg_path.read_text(encoding="utf-8")
        color = get_theme_palette().get("text", "#f1f5f9")
        svg_text = svg_text.replace("currentColor", color)
        pixmap = QPixmap()
        pixmap.loadFromData(svg_text.encode("utf-8"))
        if not pixmap.isNull():
            return QIcon(pixmap)
    return QIcon()


class ActivityBar(QWidget):
    """Vertical icon bar (VS Code style, ~48px)."""

    tab_activated = Signal(str)
    tab_deactivated = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("activityBar")
        self.setFixedWidth(48)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self._buttons: dict[str, QPushButton] = {}
        for name, icon_file in [
            ("measures", "activity_measures"),
            ("controls", "activity_controls"),
        ]:
            btn = QPushButton()
            btn.setIcon(_load_icon(icon_file))
            btn.setCheckable(True)
            btn.setToolTip(name.capitalize())
            btn.clicked.connect(lambda _, n=name: self._on_click(n))
            layout.addWidget(btn)
            self._buttons[name] = btn
        layout.addStretch(1)

    def _on_click(self, name: str) -> None:
        btn = self._buttons[name]
        if btn.isChecked():
            for n, b in self._buttons.items():
                if n != name:
                    b.setChecked(False)
            self.tab_activated.emit(name)
        else:
            self.tab_deactivated.emit(name)

    def set_active(self, name: str | None) -> None:
        for n, b in self._buttons.items():
            b.setChecked(n == name)

    def reload_text(self) -> None:
        from echo_personal_tool.infrastructure.i18n import tr
        names = {"measures": tr("measures"), "controls": tr("controls")}
        for name, btn in self._buttons.items():
            btn.setToolTip(names.get(name, name.capitalize()))
