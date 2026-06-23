"""Dialog for Orthanc server connection settings."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QLineEdit,
    QVBoxLayout,
    QWidget,
)

from echo_personal_tool.infrastructure.server_settings import (
    ServerSettings,
    load_server_settings,
    save_server_settings,
)


def show_server_settings_dialog(parent: QWidget | None = None) -> bool:
    dialog = ServerSettingsDialog(parent)
    return dialog.exec() == QDialog.DialogCode.Accepted


class ServerSettingsDialog(QDialog):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("Настройки сервера")

        current = load_server_settings()

        self._url_edit = QLineEdit(current.url)
        self._username_edit = QLineEdit(current.username)
        self._password_edit = QLineEdit(current.password)
        self._password_edit.setEchoMode(QLineEdit.EchoMode.Password)
        self._mock_check = QCheckBox("Mock (без сервера)")
        self._mock_check.setChecked(current.use_mock)

        form = QFormLayout()
        form.addRow("URL:", self._url_edit)
        form.addRow("Имя пользователя:", self._username_edit)
        form.addRow("Пароль:", self._password_edit)
        form.addRow("", self._mock_check)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)

        layout = QVBoxLayout(self)
        layout.addLayout(form)
        layout.addWidget(buttons)

    def _on_accept(self) -> None:
        save_server_settings(
            ServerSettings(
                url=self._url_edit.text().strip(),
                username=self._username_edit.text(),
                password=self._password_edit.text(),
                use_mock=self._mock_check.isChecked(),
            )
        )
        self.accept()
