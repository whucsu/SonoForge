# ECHO Personal Tool

Персональный десктопный инструмент для анализа эхокардиографических исследований (DICOM, MP4, JPEG/PNG).

**Стек:** PySide6, PyQtGraph, pydicom, NumPy, httpx — Clean Architecture.

**Ветка разработки:** `feat/phase2-echopac-ui` (EchoPac-style UI, измерения, ONNX, DICOMweb).

## Возможности

| Область | Что есть |
|---------|----------|
| **Загрузка** | Локальная папка (DICOM / MP4 / JPEG) или **Orthanc DICOMweb** (QIDO/WADO) |
| **Просмотр** | Gallery, 2D viewer, таймлайн, play/pause, W/L |
| **Измерения** | Калиперы, Simpson LV/LA/RA, planimeter, RWT, Doppler, M-mode |
| **Workflow** | Blink следующей кнопки, study overlay, рост/вес, индексы BSA |
| **RV FAC** | Одна кнопка FAC: ED → blink → ES, crescent open-arc |
| **ONNX** | LV Auto A4C (EchoNet), hotkey `I`, refine `R` |
| **Отчёты** | Окно «Результаты», экспорт PDF, справочник ASE |

Актуальный статус по коду: **[ROADMAP.md](ROADMAP.md)**.

## Требования

- Python 3.10–3.11
- [uv](https://docs.astral.sh/uv/) (рекомендуется) или `pip` + virtualenv

## Установка

```bash
# С uv (рекомендуется)
uv sync --extra dev --extra phase2
uv run echo-personal-tool

# Или pip
pip install -e ".[dev,phase2]"
python -m echo_personal_tool
```

`phase2` — ONNX (`onnxruntime`) и PDF (`reportlab`). Базовые зависимости включают `httpx` для DICOMweb.

## Быстрый старт

1. **Open folder…** — выбрать папку с DICOM/MP4, или  
   **Загрузить с сервера…** — Orthanc (см. ниже).
2. Выбрать серию в gallery → измерения в панели **Measures**.
3. **Результаты** — сводка по исследованию и PDF.

## Orthanc DICOMweb

Загрузка исследований с PACS/Orthanc без STOW (только чтение).

1. **Настройки → Сервер…** — URL, логин, пароль.  
   Дома без сервера: включить **Mock (без сервера)**.
2. **Загрузить с сервера…** — поиск, выбор серий, скачивание во временный кэш.
3. После загрузки открывается тот же pipeline, что и для локальной папки.

Спека: [`docs/superpowers/specs/2026-06-23-dicomweb-orthanc-design.md`](docs/superpowers/specs/2026-06-23-dicomweb-orthanc-design.md)  
Обзор: [`DICOM_parsing.md`](DICOM_parsing.md)

## ONNX (LV Auto)

Автосегментация эндокарда (EchoNet Segmentation Lite) и сплайн-редактор контуров.

### Экспорт модели

```bash
python scripts/export_echonet_seg_to_onnx.py --verify
```

Создаёт `models/echonet_seg_resnet50.onnx` и обновляет `models/model_manifest.json`.

### В приложении

1. Worksheet: **A4C ED** / **A4C ES** (контекст фазы).
2. Кадр → **`I`** (Auto Segment) — open-arc контур (`source="ai"`).
3. **`R`** — gradient refine; drag узлов для коррекции.

Спека: [`docs/superpowers/specs/2026-06-19-onnx-lv-auto-segment-design.md`](docs/superpowers/specs/2026-06-19-onnx-lv-auto-segment-design.md)

## Разработка

```bash
uv run pytest
uv run ruff check src tests
```

Отладка: `.vscode/launch.json` → `echo_personal_tool`.

Изолированные ветки: `git worktree add .worktrees/<name> -b feat/<name>` (каталог `.worktrees/` в `.gitignore`).

## Структура

```text
src/echo_personal_tool/
├── domain/           # Модели, расчёты, порты (без pydicom/Qt)
├── infrastructure/   # DICOM, сканер, ONNX, Orthanc DICOMweb
├── application/      # AppController, workers
└── presentation/     # MainWindow, Viewer, Measures, диалоги
```

## Документация

| Документ | Назначение |
|----------|------------|
| [ROADMAP.md](ROADMAP.md) | Статус фич по коду |
| [CHANGELOG_SESSION.md](CHANGELOG_SESSION.md) | Контекст для новых чатов Cursor |
| [docs/superpowers/specs/](docs/superpowers/specs/) | Утверждённые спеки |
| [docs/superpowers/plans/](docs/superpowers/plans/) | Планы реализации |
| [Общий план.md](Общий%20план.md), [Этап2.md](Этап2.md), [Этап3.md](Этап3.md) | Исходная архитектура |

## Лицензия

См. репозиторий / автор.
