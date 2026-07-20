# Tests

Юнит-тесты, интеграционные тесты и бенчмарки SonoForge.

## Структура

| Папка | Описание |
|-------|----------|
| `unit/` | 166 юнит-тестов для domain, infrastructure, presentation |
| `integration/` | Интеграционные тесты с реальным DICOM и Orthanc |
| `bench/` | Бенчмарки производительности (декодирование, сеть, рендеринг) |
| `fixtures/` | Тестовые данные: синтетические DICOM, моки Orthanc |

## Запуск

```bash
# Все тесты
python -m pytest tests/ -x -q

# Только юнит-тесты
python -m pytest tests/unit/ -x -q

# Интеграционные тесты (требуется Orthanc)
ECHO_ORTHANC=1 python -m pytest tests/integration/ -v

# Бенчмарки
python -m pytest tests/bench/ -v
```

## Юнит-тесты (`unit/`)

Покрывают:
- Модели данных (Contour, Doppler, Speckle, MMode)
- Расчёты (Simpson, Bernoulli, Teichholz, BSA, RWT, FAC)
- Инфраструктуру (DICOM, Orthanc, ONNX, DIMSE)
- Презентационный слой (Viewer, M-Mode, Doppler, STE)
- Безопасность (валидация, PHI-фильтрация, TLS)

## Интеграционные тесты (`integration/`)

- `test_dicom_reader.py` — чтение реальных DICOM файлов
- `test_orthanc_live.py` — тесты с живым Orthanc (DICOMweb, DIMSE, C-GET, C-MOVE)

## Бенчмарки (`bench/`)

- `test_decode_bench.py` — декодирование DICOM кадров
- `test_memory_bench.py` — потребление памяти
- `test_network_bench.py` — сетевые операции
- `test_pipeline_bench.py` — полный pipeline
- `test_playback_bench.py` — воспроизведение cine
- `test_scroll_bench.py` — прокрутка
- `test_rendering_bench.py` — рендеринг

## Фикстуры (`fixtures/`)

- `generate_synthetic_dicom.py` — генерация синтетических DICOM файлов
- `generate_synthetic_media.py` — генерация MP4/JPEG тестовых данных
- `orthanc/` — моки ответов Orthanc API
- `reference_manifest.json` — тестовый манифест справочника
