"""Tests for ASE reference dialog."""

from __future__ import annotations

from echo_personal_tool.presentation.ase_reference_dialog import AseReferenceDialog


def test_reference_dialog_loads_markdown(qtbot) -> None:
    dialog = AseReferenceDialog()
    qtbot.addWidget(dialog)
    html = dialog._browser.toHtml()
    assert "Левый желудочек" in html
    assert "LVEF" in html or "Показатель" in html
