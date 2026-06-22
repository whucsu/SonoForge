"""Tests for SystemBar widget."""

from __future__ import annotations

from PySide6.QtWidgets import QPushButton

from echo_personal_tool.presentation.system_bar import SystemBar


def test_system_bar_emits_caliper_requested(qtbot) -> None:
    bar = SystemBar()
    qtbot.addWidget(bar)
    caliper_btn = next(
        btn for btn in bar.findChildren(QPushButton) if btn.text() == "Caliper"
    )
    with qtbot.waitSignal(bar.caliper_requested, timeout=1000):
        caliper_btn.click()


def test_system_bar_study_context_and_status(qtbot) -> None:
    bar = SystemBar()
    qtbot.addWidget(bar)
    bar.set_study_context("A4C cine", "US")
    bar.set_status_message("Frame loaded")
    assert bar._study_label.text() == "A4C cine"
    assert "Frame" in bar._status_label.text()
    assert bar._actions_widget is not None


def test_system_bar_emits_settings_requested(qtbot) -> None:
    bar = SystemBar()
    qtbot.addWidget(bar)
    with qtbot.waitSignal(bar.settings_requested, timeout=1000):
        bar._btn_settings.click()


def test_system_bar_emits_references_requested(qtbot) -> None:
    bar = SystemBar()
    qtbot.addWidget(bar)
    with qtbot.waitSignal(bar.references_requested, timeout=1000):
        bar._btn_references.click()
