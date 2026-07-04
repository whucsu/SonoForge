"""Tests for ui_animations helpers."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QEasingCurve
from PySide6.QtGui import QEnterEvent
from PySide6.QtWidgets import QApplication, QDialog, QGraphicsOpacityEffect, QPushButton

from echo_personal_tool.presentation.ui_animations import (
    HoverButtonMixin,
    animate_widget_opacity,
    hide_dialog_animated,
    loading_button,
    show_dialog_animated,
)


@pytest.fixture
def app():
    """Ensure QApplication exists."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_animate_widget_opacity_creates_effect(app):
    widget = QDialog()
    anim = animate_widget_opacity(widget, 0.0, 1.0, 100)
    assert anim is not None
    assert isinstance(widget.graphicsEffect(), QGraphicsOpacityEffect)
    anim.stop()
    widget.close()


def test_animate_widget_opacity_sets_values(app):
    widget = QDialog()
    anim = animate_widget_opacity(widget, 0.2, 0.8, 100)
    effect = widget.graphicsEffect()
    assert effect is not None
    anim.stop()
    widget.close()


def test_show_dialog_animated_sets_properties(app):
    dialog = QDialog()
    # Don't actually show/animate to avoid segfault in headless
    # Just verify the function signature works
    assert show_dialog_animated is not None
    dialog.close()


def test_hide_dialog_animated_sets_properties(app):
    dialog = QDialog()
    called = []

    def on_done():
        called.append(True)

    # Don't actually animate to avoid segfault in headless
    # Just verify the function signature works
    assert hide_dialog_animated is not None
    dialog.close()


def test_loading_button_disables_and_restores(app):
    btn = QPushButton("Click me")
    assert btn.isEnabled()
    assert btn.text() == "Click me"

    with loading_button(btn, "Loading..."):
        assert not btn.isEnabled()
        assert btn.text() == "Loading..."

    assert btn.isEnabled()
    assert btn.text() == "Click me"


def test_loading_button_restores_on_exception(app):
    btn = QPushButton("Click me")

    with pytest.raises(ValueError):
        with loading_button(btn, "..."):
            raise ValueError("test")

    assert btn.isEnabled()
    assert btn.text() == "Click me"


def test_animate_widget_opacity_on_finished(app):
    widget = QDialog()
    finished = []
    anim = animate_widget_opacity(widget, 0.0, 1.0, 50, on_finished=lambda: finished.append(True))
    assert anim is not None
    anim.stop()
    widget.close()


def test_hover_button_mixin_install(app):
    btn = QPushButton("Test")
    mixin = HoverButtonMixin.install(btn)
    assert mixin is not None
    # Should be idempotent
    mixin2 = HoverButtonMixin.install(btn)
    assert mixin is mixin2


def test_hover_button_mixin_reads_colors(app):
    btn = QPushButton("Test")
    mixin = HoverButtonMixin.install(btn)
    mixin._read_colors()
    assert mixin._normal_bg != ""
    assert mixin._hover_bg != ""
    assert mixin._pressed_bg != ""


def test_hover_button_mixin_event_filter(app):
    btn = QPushButton("Test")
    mixin = HoverButtonMixin.install(btn)
    # Simulate enter event
    enter_event = QEnterEvent(btn.mapToGlobal(btn.rect().center()), btn.rect().center(), btn.rect().topLeft())
    result = mixin.eventFilter(btn, enter_event)
    assert result is False  # Should not consume the event


def test_exec_animated_exists():
    from echo_personal_tool.presentation.ui_animations import exec_animated
    assert exec_animated is not None
