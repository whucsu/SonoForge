"""Scrollable ASE reference viewer backed by ``References ASE+.md``."""

from __future__ import annotations

from PySide6.QtCore import QSettings, Qt, QUrl
from PySide6.QtGui import QDesktopServices, QFont
from PySide6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFontComboBox,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QMenuBar,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTextBrowser,
    QVBoxLayout,
    QWidget,
)

from echo_personal_tool.domain.services.ase_reference_parser import (
    default_ase_reference_path,
    load_ase_reference_text,
    markdown_to_html,
)
from echo_personal_tool.infrastructure.i18n import tr
from echo_personal_tool.presentation.echopac_theme import get_theme_palette
from echo_personal_tool.resources.bundled_fonts import FONT_FAMILY_UI

_SETTINGS_ORG = "echo-personal-tool"
_SETTINGS_APP = "ase-reference"
_DEFAULT_FONT_FAMILY = FONT_FAMILY_UI
_DEFAULT_FONT_SIZE = 12
_MIN_FONT_SIZE = 8
_MAX_FONT_SIZE = 28


def show_ase_reference_dialog(parent: QWidget | None = None) -> None:
    try:
        dialog = AseReferenceDialog(parent)
    except Exception as exc:  # noqa: BLE001 — show load errors in UI
        QMessageBox.critical(
            parent,
            tr("ase_refs.load_error.title"),
            tr("ase_refs.load_error.body", exc=str(exc)),
        )
        return
    dialog.exec()


class AseReferenceDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("ase_refs.title"))
        self.resize(980, 720)

        self._settings = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
        self._md_path = default_ase_reference_path()
        self._font_family = str(
            self._settings.value("font_family", _DEFAULT_FONT_FAMILY)
        )
        self._font_size = int(self._settings.value("font_size", _DEFAULT_FONT_SIZE))

        root = QVBoxLayout(self)
        root.setMenuBar(self._build_menu())

        hint = QLabel(
            tr("ase_refs.hint", name=self._md_path.name)
        )
        hint.setWordWrap(True)
        hint.setTextFormat(Qt.TextFormat.RichText)
        root.addWidget(hint)

        toolbar = QHBoxLayout()
        btn_reload = QPushButton(tr("ase_refs.reload"))
        btn_reload.setToolTip(tr("ase_refs.reload_tip"))
        btn_reload.clicked.connect(self._reload_document)
        btn_open = QPushButton(tr("ase_refs.open_file"))
        btn_open.setToolTip(tr("ase_refs.open_file_tip"))
        btn_open.clicked.connect(self._open_markdown_file)
        toolbar.addWidget(btn_reload)
        toolbar.addWidget(btn_open)
        toolbar.addStretch(1)
        root.addLayout(toolbar)

        self._browser = QTextBrowser()
        self._browser.setOpenExternalLinks(True)
        self._browser.setLineWrapMode(QTextBrowser.LineWrapMode.WidgetWidth)
        p = get_theme_palette()
        self._browser.document().setDefaultStyleSheet(
            f"body {{ color: {p['text']}; }}"
            f"h1, h2, h3 {{ color: {p['text']}; }}"
            f"table {{ border-collapse: collapse; width: 100%; margin: 12px 0; }}"
            f"th, td {{ border: 1px solid {p['border']}; vertical-align: top; }}"
            f"th {{ background: {p['bg_control']}; }}"
            f"blockquote {{ color: {p['text_dim']}; margin: 8px 0 8px 12px; }}"
            f"hr {{ border: none; border-top: 1px solid {p['border']}; margin: 16px 0; }}"
        )
        root.addWidget(self._browser, stretch=1)

        self._apply_font()
        self._reload_document()

    def _build_menu(self) -> QMenuBar:
        from PySide6.QtWidgets import QMenu

        menu_bar = QMenuBar(self)

        file_menu = QMenu(tr("ase_refs.file_menu"), menu_bar)
        file_menu.addAction(tr("ase_refs.reload"), self._reload_document)
        file_menu.addAction(tr("ase_refs.open_file"), self._open_markdown_file)
        menu_bar.addMenu(file_menu)

        settings_menu = QMenu(tr("ase_refs.settings_menu"), menu_bar)
        settings_menu.addAction(tr("ase_refs.font_action"), self._show_font_settings)
        menu_bar.addMenu(settings_menu)

        return menu_bar

    def _reload_document(self) -> None:
        try:
            markdown = load_ase_reference_text(self._md_path)
        except OSError as exc:
            QMessageBox.warning(
                self,
                tr("ase_refs.read_error.title"),
                tr("ase_refs.read_error.body", path=str(self._md_path), exc=str(exc)),
            )
            return
        self._browser.setHtml(markdown_to_html(markdown))
        self._apply_font()

    def _open_markdown_file(self) -> None:
        if not QDesktopServices.openUrl(QUrl.fromLocalFile(str(self._md_path))):
            QMessageBox.warning(
                self,
                tr("ase_refs.open_error.title"),
                tr("ase_refs.open_error.body", path=str(self._md_path)),
            )

    def _show_font_settings(self) -> None:
        dialog = ReferenceFontSettingsDialog(
            self._font_family,
            self._font_size,
            parent=self,
        )
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return
        self._font_family = dialog.selected_family()
        self._font_size = dialog.selected_size()
        self._settings.setValue("font_family", self._font_family)
        self._settings.setValue("font_size", self._font_size)
        self._apply_font()

    def _apply_font(self) -> None:
        font = QFont(self._font_family, self._font_size)
        self._browser.setFont(font)


class ReferenceFontSettingsDialog(QDialog):
    def __init__(
        self,
        family: str,
        size: int,
        *,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle(tr("ase_refs.font_settings"))

        self._family = QFontComboBox()
        self._family.setCurrentFont(QFont(family))

        self._size = QSpinBox()
        self._size.setRange(_MIN_FONT_SIZE, _MAX_FONT_SIZE)
        self._size.setSuffix(" pt")
        self._size.setValue(size)

        form = QFormLayout()
        form.addRow(tr("ase_refs.font"), self._family)
        form.addRow(tr("ase_refs.font_size"), self._size)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def selected_family(self) -> str:
        return self._family.currentFont().family()

    def selected_size(self) -> int:
        return self._size.value()
