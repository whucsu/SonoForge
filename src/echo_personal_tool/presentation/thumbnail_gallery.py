"""GE-style 2-column thumbnail gallery (index, cine, DICOM badges)."""

from __future__ import annotations

import inspect
from collections.abc import Callable

from PySide6.QtCore import QSize, Qt, QTimer, Signal
from PySide6.QtGui import QIcon, QImage, QPixmap
from PySide6.QtWidgets import (
    QListWidget,
    QListWidgetItem,
    QSizePolicy,
    QStyle,
    QStyledItemDelegate,
    QStyleOptionViewItem,
)

from echo_personal_tool.application.thumbnail_scheduler import ThumbnailPriority
from echo_personal_tool.domain.models import InstanceMetadata, StudyMetadata
from echo_personal_tool.presentation.echopac_theme import ACCENT_BRIGHT, BG_DARK, TEXT

_ITEM_ROLE = Qt.ItemDataRole.UserRole
_THUMB_W = 96
_THUMB_H = 72
_CELL_W = 108
_CELL_H = 84
_VISIBLE_PADDING = 8
_SCROLL_DEBOUNCE_MS = 25

ThumbnailLoader = (
    Callable[[InstanceMetadata], None] | Callable[[InstanceMetadata, ThumbnailPriority], None]
)


class ThumbnailGalleryDelegate(QStyledItemDelegate):
    """Paint thumbnail with index (TL), cine (BL), DICOM (BR)."""

    def sizeHint(self, option: QStyleOptionViewItem, index) -> QSize:  # type: ignore[override]
        return QSize(_CELL_W, _CELL_H)

    def paint(self, painter, option, index) -> None:  # type: ignore[override]
        instance = index.data(_ITEM_ROLE)
        display_index = index.data(Qt.ItemDataRole.UserRole + 1)
        if not isinstance(instance, InstanceMetadata):
            super().paint(painter, option, index)
            return

        painter.save()
        rect = option.rect
        if option.state & QStyle.StateFlag.State_Selected:
            painter.setPen(QColor_from(ACCENT_BRIGHT))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRect(rect.adjusted(1, 1, -2, -2))
        else:
            painter.fillRect(rect, QColor_from(BG_DARK))

        thumb_rect = rect.adjusted(4, 4, -4, -4)
        list_widget = option.widget
        pixmap: QPixmap | None = None
        if isinstance(list_widget, ThumbnailGalleryWidget):
            pixmap = list_widget.thumbnail_pixmap(instance.sop_instance_uid)

        if pixmap is not None and not pixmap.isNull():
            scaled = pixmap.scaled(
                thumb_rect.width(),
                thumb_rect.height(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation,
            )
            x = thumb_rect.x() + (thumb_rect.width() - scaled.width()) // 2
            y = thumb_rect.y() + (thumb_rect.height() - scaled.height()) // 2
            painter.drawPixmap(x, y, scaled)
        else:
            painter.setPen(QColor_from("#4a5564"))
            painter.drawRect(thumb_rect)

        # Index top-left
        if display_index is not None:
            painter.setPen(QColor_from(TEXT))
            font = painter.font()
            font.setBold(True)
            font.setPointSize(9)
            painter.setFont(font)
            painter.drawText(
                rect.adjusted(6, 4, 0, 0),
                int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop),
                str(display_index),
            )

        # Cine bottom-left / single-frame
        is_cine = instance.number_of_frames > 1
        badge = "▶" if is_cine else "●"
        painter.setPen(QColor_from("#7ec8ff" if is_cine else "#6a7a8a"))
        font = painter.font()
        font.setPointSize(8)
        painter.setFont(font)
        painter.drawText(
            rect.adjusted(6, 0, 0, -4),
            int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignBottom),
            badge,
        )

        # DICOM bottom-right
        if _has_dicom_tags(instance):
            painter.setPen(QColor_from("#ffd54f"))
            font.setBold(True)
            font.setPointSize(9)
            painter.setFont(font)
            painter.drawText(
                rect.adjusted(0, 0, -6, -4),
                int(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignBottom),
                "D",
            )

        painter.restore()


def QColor_from(hex_color: str):  # noqa: N802
    from PySide6.QtGui import QColor

    return QColor(hex_color)


def _has_dicom_tags(instance: InstanceMetadata) -> bool:
    if instance.media_format != "dicom":
        return False
    return instance.pixel_spacing is not None or instance.frame_time_ms is not None


_COLUMN_COUNT = 2
_CELL_SPACING = 2
# Reserve gutter for vertical scrollbar + frame so two grid cells still fit in the viewport.
_SCROLLBAR_GUTTER = 24
_GALLERY_WIDTH = (
    _COLUMN_COUNT * _CELL_W + (_COLUMN_COUNT - 1) * _CELL_SPACING + _SCROLLBAR_GUTTER
)


class ThumbnailGalleryWidget(QListWidget):
    """Two-column vertical thumbnail strip (EchoPac left panel)."""

    instance_selected = Signal(object)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self.setObjectName("thumbnailGallery")
        self.setItemDelegate(ThumbnailGalleryDelegate(self))
        # LeftToRight + wrap => exactly two columns, rows grow downward (vertical scroll).
        self.setViewMode(QListWidget.ViewMode.IconMode)
        self.setFlow(QListWidget.Flow.LeftToRight)
        self.setWrapping(True)
        self.setResizeMode(QListWidget.ResizeMode.Fixed)
        self.setUniformItemSizes(True)
        self.setMovement(QListWidget.Movement.Static)
        self.setSpacing(_CELL_SPACING)
        self.setGridSize(QSize(_CELL_W, _CELL_H))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setIconSize(QSize(_THUMB_W, _THUMB_H))
        self.setFixedWidth(_GALLERY_WIDTH)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)
        self.itemClicked.connect(self._on_item_clicked)

        self._thumbnail_cache: dict[str, QIcon] = {}
        self._thumbnail_pixmaps: dict[str, QPixmap] = {}
        self._items_by_uid: dict[str, QListWidgetItem] = {}
        self._instances: list[InstanceMetadata] = []
        self._thumbnail_loader: ThumbnailLoader | None = None
        self._loader_accepts_priority = False
        self._building = False
        self._scroll_timer = QTimer(self)
        self._scroll_timer.setSingleShot(True)
        self._scroll_timer.setInterval(_SCROLL_DEBOUNCE_MS)
        self._scroll_timer.timeout.connect(self.request_visible_previews)
        self.verticalScrollBar().valueChanged.connect(lambda _v: self._scroll_timer.start())

    def set_thumbnail_loader(self, loader: ThumbnailLoader) -> None:
        self._thumbnail_loader = loader
        try:
            sig = inspect.signature(loader)
            self._loader_accepts_priority = len(sig.parameters) >= 2
        except (TypeError, ValueError):
            self._loader_accepts_priority = False

    def populate(self, studies: list[StudyMetadata]) -> None:
        self._building = True
        self.clear()
        self._items_by_uid.clear()
        self._instances.clear()
        index = 1
        for study in studies:
            for series in study.series:
                for instance in series.instances:
                    self._instances.append(instance)
                    item = QListWidgetItem()
                    item.setData(_ITEM_ROLE, instance)
                    item.setData(Qt.ItemDataRole.UserRole + 1, index)
                    item.setSizeHint(QSize(_CELL_W, _CELL_H))
                    cached = self._thumbnail_cache.get(instance.sop_instance_uid)
                    if cached is not None:
                        item.setIcon(cached)
                    self.addItem(item)
                    self._items_by_uid[instance.sop_instance_uid] = item
                    index += 1
        self._building = False
        QTimer.singleShot(0, self._after_populate)

    def _after_populate(self) -> None:
        self.request_visible_previews()
        self._enqueue_background_previews()

    def _enqueue_background_previews(self) -> None:
        if self._thumbnail_loader is None:
            return
        for instance in self._instances:
            uid = instance.sop_instance_uid
            if uid in self._thumbnail_pixmaps:
                continue
            if self._loader_accepts_priority:
                self._thumbnail_loader(instance, ThumbnailPriority.P2_BACKGROUND)  # type: ignore[misc]
            else:
                self._thumbnail_loader(instance)  # type: ignore[misc]

    def request_visible_previews(self, selected_instance: InstanceMetadata | None = None) -> None:
        if self._building or self._thumbnail_loader is None:
            return
        selected_uid = selected_instance.sop_instance_uid if selected_instance is not None else None
        if selected_uid is None:
            current = self.currentItem()
            if current is not None:
                payload = current.data(_ITEM_ROLE)
                if isinstance(payload, InstanceMetadata):
                    selected_uid = payload.sop_instance_uid

        visible_uids = self._visible_instance_uids()
        for row in range(self.count()):
            item = self.item(row)
            if item is None:
                continue
            instance = item.data(_ITEM_ROLE)
            if not isinstance(instance, InstanceMetadata):
                continue
            uid = instance.sop_instance_uid
            if uid in self._thumbnail_pixmaps:
                continue
            if uid not in visible_uids and uid != selected_uid:
                continue
            priority = (
                ThumbnailPriority.P0_VISIBLE_SELECTED
                if uid == selected_uid
                else ThumbnailPriority.P1_NEAR_VISIBLE
            )
            if self._loader_accepts_priority:
                self._thumbnail_loader(instance, priority)  # type: ignore[misc]
            else:
                self._thumbnail_loader(instance)  # type: ignore[misc]

    def set_thumbnail(self, instance_uid: str, image: QImage) -> None:
        if image.isNull():
            return
        pixmap = QPixmap.fromImage(image)
        icon = QIcon(pixmap)
        self._thumbnail_cache[instance_uid] = icon
        self._thumbnail_pixmaps[instance_uid] = pixmap
        item = self._items_by_uid.get(instance_uid)
        if item is not None:
            item.setIcon(icon)
            self.viewport().update()
        QTimer.singleShot(0, self.request_visible_previews)

    def thumbnail_pixmap(self, instance_uid: str) -> QPixmap | None:
        return self._thumbnail_pixmaps.get(instance_uid)

    def select_instance(self, instance: InstanceMetadata) -> None:
        item = self._items_by_uid.get(instance.sop_instance_uid)
        if item is not None:
            self.setCurrentItem(item)
            self.scrollToItem(item)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        instance = item.data(_ITEM_ROLE)
        if isinstance(instance, InstanceMetadata):
            self.instance_selected.emit(instance)

    def _visible_instance_uids(self) -> set[str]:
        uids: set[str] = set()
        viewport = self.viewport()
        if viewport is None:
            return uids
        for row in range(self.count()):
            item = self.item(row)
            if item is None:
                continue
            rect = self.visualItemRect(item)
            padded = rect.adjusted(0, -_VISIBLE_PADDING * 4, 0, _VISIBLE_PADDING * 4)
            if not viewport.rect().intersects(padded):
                continue
            instance = item.data(_ITEM_ROLE)
            if isinstance(instance, InstanceMetadata):
                uids.add(instance.sop_instance_uid)
        return uids
