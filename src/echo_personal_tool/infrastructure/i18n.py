"""Simple i18n translation module with Russian/English support."""

from __future__ import annotations

_current_language: str = "ru"

_TRANSLATIONS: dict[str, dict[str, str]] = {
    # ── System bar ────────────────────────────────────────────────
    "no_study_loaded": {"ru": "No study loaded", "en": "No study loaded"},
    "open_folder": {"ru": "Open folder…", "en": "Open folder…"},
    "load_from_server": {"ru": "Загрузить с сервера…", "en": "Load from server…"},
    "settings": {"ru": "Настройки", "en": "Settings"},
    "caliper": {"ru": "Caliper", "en": "Caliper"},
    "calibration_bmode": {"ru": "Calibration B-mode", "en": "Calibration B-mode"},
    "calibration_doppler": {"ru": "Calibration Doppler", "en": "Calibration Doppler"},
    "references": {"ru": "Нормативы", "en": "References"},
    "reset": {"ru": "Reset", "en": "Reset"},
    "ready": {"ru": "Ready", "en": "Ready"},
    "minimize": {"ru": "Свернуть", "en": "Minimize"},
    "maximize": {"ru": "Развернуть", "en": "Maximize"},
    "restore": {"ru": "Восстановить", "en": "Restore"},
    "close": {"ru": "Закрыть", "en": "Close"},

    # ── Tool panel ────────────────────────────────────────────────
    "measures": {"ru": "Измерения", "en": "Measures"},
    "controls": {"ru": "Управление", "en": "Controls"},
    "dicom": {"ru": "DICOM", "en": "DICOM"},
    "linear_caliper": {"ru": "Линейный калипер", "en": "Linear caliper"},
    "calibrate_bmode": {"ru": "Калибровка B-mode", "en": "Calibrate B-mode"},
    "calibrate_doppler": {"ru": "Калибровка Doppler", "en": "Calibrate Doppler"},
    "cine_speed": {"ru": "Скорость cine:", "en": "Cine speed:"},
    "wl_preset": {"ru": "Пресет W/L:", "en": "W/L preset:"},
    "thumbnail_size": {"ru": "Размер миниатюр:", "en": "Thumbnail size:"},
    "crosshair": {"ru": "Перекрестие:", "en": "Crosshair:"},
    "panel_frames": {"ru": "Рамки панелей:", "en": "Panel frames:"},
    "caliper_labels": {"ru": "Подписи калиперов:", "en": "Caliper labels:"},
    "caliper_inline_labels": {"ru": "Подписи на изображении:", "en": "Inline labels:"},
    "small": {"ru": "Маленькие", "en": "Small"},
    "medium": {"ru": "Средние", "en": "Medium"},
    "large": {"ru": "Крупные", "en": "Large"},

    # ── Preferences dialog ────────────────────────────────────────
    "preferences": {"ru": "Настройки", "en": "Settings"},
    "reset_defaults": {"ru": "По умолчанию", "en": "Defaults"},
    "reset_confirm": {"ru": "Вернуть все параметры к значениям по умолчанию?", "en": "Reset all parameters to defaults?"},
    "yes": {"ru": "Да", "en": "Yes"},
    "no": {"ru": "Нет", "en": "No"},

    # ── Tabs ──────────────────────────────────────────────────────
    "tab_interface": {"ru": "Интерфейс", "en": "Interface"},
    "tab_display": {"ru": "Отображение", "en": "Display"},
    "tab_measurement": {"ru": "Измерения", "en": "Measurement"},
    "tab_server": {"ru": "Сервер", "en": "Server"},

    # ── Theme names ───────────────────────────────────────────────
    "theme_dark": {"ru": "Тёмная", "en": "Dark"},
    "theme_light": {"ru": "Светлая", "en": "Light"},
    "theme_vscode_dark": {"ru": "VS Code Dark", "en": "VS Code Dark"},
    "theme_vscode_light": {"ru": "VS Code Light", "en": "VS Code Light"},
    "theme_system": {"ru": "Системная", "en": "System"},
    "language": {"ru": "Язык:", "en": "Language:"},
    "lang_ru": {"ru": "Русский", "en": "Russian"},
    "lang_en": {"ru": "Английский", "en": "English"},

    # ── Measurements menu ─────────────────────────────────────────
    "menu_lv_diastole": {"ru": "ЛЖ/ДИАСТ", "en": "LV/DIAST"},
    "menu_lv_systole": {"ru": "ЛЖ/СИСТ", "en": "LV/SYST"},
    "menu_la": {"ru": "ЛП", "en": "LA"},
    "menu_ra": {"ru": "ПП", "en": "RA"},
    "menu_rv": {"ru": "ПЖ", "en": "RV"},
    "menu_doppler_mitral": {"ru": "МК/АК", "en": "MV/AV"},
    "menu_doppler_tricuspid": {"ru": "ТК/ЛК", "en": "TV/PV"},
    "menu_strain": {"ru": "Стрейн", "en": "Strain"},
    "menu_doppler_flow": {"ru": "Doppler Flow", "en": "Doppler Flow"},

    # ── Viewer prompts ────────────────────────────────────────────
    "caliper_click_start": {"ru": "1-й клик — начало", "en": "1st click — start"},
    "caliper_click_end": {"ru": "2-й клик — конец", "en": "2nd click — end"},

    # ── Measurement results ───────────────────────────────────────
    "mm": {"ru": "mm", "en": "mm"},
    "cm": {"ru": "cm", "en": "cm"},
    "px": {"ru": "px", "en": "px"},
    "cm_s": {"ru": "cm/s", "en": "cm/s"},
    "mmhg": {"ru": "mmHg", "en": "mmHg"},
    "ms": {"ru": "ms", "en": "ms"},
    "ml": {"ru": "mL", "en": "mL"},
    "cm2": {"ru": "cm²", "en": "cm²"},
    "percent": {"ru": "%", "en": "%"},

    # ── Status messages ───────────────────────────────────────────
    "loading": {"ru": "Загрузка {name}…", "en": "Loading {name}…"},
    "decoding": {"ru": "Декодирование {name}… ({total} кадров)", "en": "Decoding {name}… ({total} frames)"},
    "first_frame_ready": {"ru": "Первый кадр готов", "en": "First frame ready"},
    "load_failed": {"ru": "Ошибка загрузки: {message}", "en": "Load failed: {message}"},

    # ── Contour modes ─────────────────────────────────────────────
    "manual": {"ru": "Ручная", "en": "Manual"},
    "ai": {"ru": "AI", "en": "AI"},
    "model": {"ru": "Модель", "en": "Model"},
}


def set_language(lang: str) -> None:
    """Set the current language ('ru' or 'en')."""
    global _current_language
    _current_language = lang


def get_language() -> str:
    """Get the current language code."""
    return _current_language


def tr(key: str, **kwargs: str) -> str:
    """Translate a key to the current language.

    Supports simple variable substitution: tr("loading", name="file.dcm")
    """
    entry = _TRANSLATIONS.get(key)
    if entry is None:
        return key
    text = entry.get(_current_language, entry.get("en", key))
    if kwargs:
        try:
            return text.format(**kwargs)
        except KeyError:
            return text
    return text
