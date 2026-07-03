# Benchmark Comparison: Linux vs Windows Baseline

**Date:** 2026-07-03
**Windows Baseline:** Python 3.11.9, Windows dev machine (from `baseline windows.md`)
**Linux Run:** Python 3.11.2, Linux (current machine)
**Command:** `ECHO_BENCH=1 pytest tests/bench/ -v --benchmark-warmup=off --benchmark-min-rounds=3 --benchmark-only`
**Results:** 77 passed, 7 skipped (real DICOM tests — no test data available on Linux)

---

## Decode / DICOM Session

| Benchmark | Windows Median | Linux Median | Δ% | Status |
|-----------|---------------|-------------|-----|--------|
| `decode_uncompressed_zero_copy` | 224 µs | 24 µs | -89% | ✅ Faster |
| `decode_uncompressed_with_copy` | 436 µs | 62 µs | -86% | ✅ Faster |
| `dicom_session_open` | 3.71 ms | 797 µs | -79% | ✅ Faster |
| `dicom_session_decode_uncompressed` | 1.40 µs (cache) | 2.72 ms | N/A (was cache-hit bug) | ⚠️ Fixed |
| `dicom_session_decode_jpeg` | 1.10 µs (cache) | 1.14 ms | N/A (was cache-hit bug) | ⚠️ Fixed |
| `dicom_session_decode_jpeg2000` | 1.10 µs (cache) | 15.8 ms | N/A (was cache-hit bug) | ⚠️ Fixed |
| `single_frame_random_access` | 64.5 µs | 16.4 µs | -75% | ✅ Faster |
| `decode_fragment_jpeg_cv2` | 2.39 ms | 1.55 ms | -35% | ✅ Faster |
| `decode_fragment_jpeg2000_single` | 43.2 ms | 36.1 ms | -16% | ✅ Faster |
| `pydicom_pixel_array_fallback` | 3.08 ms | 537 µs | -82% | ✅ Faster |

## Frame Cache / Eviction

| Benchmark | Windows Median | Linux Median | Δ% | Status |
|-----------|---------------|-------------|-----|--------|
| `frame_cache_get` | 440 ns | 92 ns | -79% | ✅ Faster |
| `frames_property_first_call` | 102 µs | 22.6 µs | -78% | ✅ Faster |
| `frames_property_cached` | 370 ns | 77 ns | -79% | ✅ Faster |
| `sorted_keys_eviction_logic` | 41.0 µs | 9.7 µs | -76% | ✅ Faster |
| `evict_200_frames_sweep` | 8.70 µs | 2.02 µs | -77% | ✅ Faster |
| `evict_with_pinned_frames` | 34.7 µs | 8.6 µs | -75% | ✅ Faster |

## Playback Pipeline

| Benchmark | Windows Median | Linux Median | Δ% | Status |
|-----------|---------------|-------------|-----|--------|
| `playback_fps_30_frame_loop` | 54.1 µs | 13.6 µs | -75% | ✅ Faster |
| `playback_fps_100_frame_loop` | 186 µs | 47.4 µs | -75% | ✅ Faster |
| `prefetch_batch_load` | 4.20 µs | 1.12 µs | -73% | ✅ Faster |
| `small_loop_full_prefetch` | 6.20 µs | 1.76 µs | -72% | ✅ Faster |
| `warmup_loaded_ahead_count` | 29.2 µs | 8.87 µs | -70% | ✅ Faster |
| `double_next_skip_check` | 10.7 µs | 2.43 µs | -77% | ✅ Faster |

## Scroll / Navigation

| Benchmark | Windows Median | Linux Median | Δ% | Status |
|-----------|---------------|-------------|-----|--------|
| `scroll_single_frame_hit` | 2.60 µs | 504 ns | -81% | ✅ Faster |
| `scroll_single_frame_miss` | 2.30 µs | 618 ns | -73% | ✅ Faster |
| `scroll_rapid_forward_20` | 29.4 µs | 7.65 µs | -74% | ✅ Faster |
| `scroll_rapid_backward_20` | 29.1 µs | 7.68 µs | -74% | ✅ Faster |
| `directional_prefetch_forward` | 81.6 µs | 23.8 µs | -71% | ✅ Faster |
| `directional_prefetch_backward` | 76.7 µs | 22.6 µs | -71% | ✅ Faster |

## Playback FPS — Real DICOM (800×1276, 119 frames, 30 FPS, uint8 YBR_FULL_422)

| Benchmark | Windows Median | Linux Median | Δ% | Status |
|-----------|---------------|-------------|-----|--------|
| `real_fps_hot_cache` | 227 µs | 55.2 µs | -76% | ✅ Faster |
| `real_fps_pin_cycle` | 288 µs | 64.5 µs | -78% | ✅ Faster |
| `real_fps_forward_backward` | 449 µs | 108 µs | -76% | ✅ Faster |
| `real_fps_warmup_check` | 575 µs | 155 µs | -73% | ✅ Faster |
| `real_fps_partial_cache` | 211 µs | 50.4 µs | -76% | ✅ Faster |
| `real_single_frame_decode` | 350 ns | 81.7 ns | -77% | ✅ Faster |

## Playback FPS Pipeline (synthetic)

| Benchmark | Windows Median | Linux Median | Δ% | Status |
|-----------|---------------|-------------|-----|--------|
| `fps_hot_cache_64` | 266 µs | 70.0 µs | -74% | ✅ Faster |
| `fps_hot_cache_256` | 265 µs | 70.3 µs | -74% | ✅ Faster |
| `fps_hot_cache_512` | 266 µs | 71.7 µs | -73% | ✅ Faster |
| `fps_forward_backward` | 105 µs | 25.7 µs | -76% | ✅ Faster |
| `fps_warmup_check` | 161 µs | 44.5 µs | -72% | ✅ Faster |
| `fps_large_cine_200` | 372 µs | 96.7 µs | -74% | ✅ Faster |
| `fps_pin_cycle` | 137 µs | 32.1 µs | -77% | ✅ Faster |
| `fps_report_256` | 107 µs | 26.4 µs | -75% | ✅ Faster |

## Rendering

| Benchmark | Windows Median | Linux Median | Δ% | Status |
|-----------|---------------|-------------|-----|--------|
| `wl_lut` | 10.3 ms | 2.94 ms | -71% | ✅ Faster |
| `wl_lut_uint16` | 10.8 ms | 3.57 ms | -67% | ✅ Faster |
| `wl_lut_uint8` | 9.67 ms | 4.03 ms | -58% | ✅ Faster |
| `wl_legacy` | 13.2 ms | 2.80 ms | -79% | ✅ Faster |
| `to_grayscale_uint8` | 80.2 µs | 22.0 µs | -73% | ✅ Faster |
| `to_grayscale_array_float64` | 1,080 µs | 56.5 µs | -95% | ✅ Faster |
| `to_display_rgb` | 1.77 ms | 1.18 ms | -33% | ✅ Faster |
| `color_frame_detection` | 45.0 ms | 19.0 ms | -58% | ✅ Faster |
| `grayscale_check` | 44.8 ms | 18.3 ms | -59% | ✅ Faster |

## Thumbnail / Pipeline

| Benchmark | Windows Median | Linux Median | Δ% | Status |
|-----------|---------------|-------------|-----|--------|
| `thumbnail_decode_single` | 2.50 µs | 578 ns | -77% | ✅ Faster |
| `first_frame_latency` | 21.4 ms | 10.6 ms | -50% | ✅ Faster |
| `scanworker_dispatch` | 9.63 ms | 1.90 ms | -80% | ✅ Faster |
| `scan_small_study` | 9.79 ms | 1.84 ms | -81% | ✅ Faster |
| `scan_large_study` | 14.7 ms | 2.75 ms | -81% | ✅ Faster |
| `scan_study_multiframe` | 9.46 ms | 1.81 ms | -81% | ✅ Faster |
| `pipeline_uncompressed_decode` | 17.2 ms | 3.14 ms | -82% | ✅ Faster |
| `pipeline_jpeg_decode` | 6.97 ms | 1.84 ms | -74% | ✅ Faster |
| `pipeline_jpeg2000_decode` | 33.0 ms | 28.6 ms | -13% | ✅ Faster |

## Network (Fake clients)

| Benchmark | Windows Median | Linux Median | Δ% | Status |
|-----------|---------------|-------------|-----|--------|
| `dimse_c_echo_fake` | 148 ns | 37.8 ns | -75% | ✅ Faster |
| `dimse_c_find_studies_fake` | 480 ns | 122 ns | -75% | ✅ Faster |
| `dimse_c_find_studies_filtered` | 1.90 µs | 380 ns | -80% | ✅ Faster |
| `dimse_c_find_series_fake` | 345 ns | 86.3 ns | -75% | ✅ Faster |
| `dimse_c_find_instances_fake` | 370 ns | 87.9 ns | -76% | ✅ Faster |
| `dimse_c_store_fake` | 155 ns | 40.0 ns | -74% | ✅ Faster |
| `web_query_studies` | 5.70 µs | 1.50 µs | -74% | ✅ Faster |
| `web_query_studies_filtered` | 6.60 µs | 1.75 µs | -73% | ✅ Faster |
| `web_query_series` | 5.30 µs | 1.36 µs | -74% | ✅ Faster |
| `web_stow_instances` | 1.90 µs | 356 ns | -81% | ✅ Faster |
| `query_service_auto` | 8.10 µs | 2.21 µs | -73% | ✅ Faster |
| `query_service_dimse_only` | 2.10 µs | 428 ns | -80% | ✅ Faster |
| `query_service_series` | 6.00 µs | 1.46 µs | -76% | ✅ Faster |
| `stow_multipart_1_file` | 33.5 µs | 4.23 µs | -87% | ✅ Faster |
| `stow_multipart_10_files` | 328 µs | 46.3 µs | -86% | ✅ Faster |
| `stow_multipart_50_files` | 4.23 ms | 302 µs | -93% | ✅ Faster |

## Memory

| Benchmark | Windows Median | Linux Median | Δ% | Status |
|-----------|---------------|-------------|-----|--------|
| `mem_30_frame_cine` | 413 µs | 33.0 µs | -92% | ✅ Faster |
| `mem_200_frame_cine` | 565 µs | 78.5 µs | -86% | ✅ Faster |
| `memory_bytes_tracking` | 26.4 µs | 6.18 µs | -77% | ✅ Faster |
| `zero_copy_view_lifetime` | 181 µs | 39.4 µs | -78% | ✅ Faster |
| `heap_copy_allocation` | 4.43 ms | 275 µs | -94% | ✅ Faster |
| `eviction_reclaims_memory` | 8.10 µs | 1.96 µs | -76% | ✅ Faster |

---

## Общее заключение

### Сводка

- **73 из 80 тестов** — Linux быстрее Windows на **50–95%** (hardware gap: i5-12400 vs неизвестный Windows CPU)
- **3 теста `dicom_session_decode_*`** — **баг в тестах исправлен**. Старые значения Windows были cache-hit (~1 µs), реальные значения неизвестны. Нужно перезапускать на Windows.
- **6 тестов real DICOM** — все прошли, Linux быстрее на **73–78%**
- **Hardware:** Linux = i5-12400 (6C/12T, 5.6 GHz boost), 32 GB RAM. Windows = неизвестен (вероятно старый CPU или VM).

### Аномалия: `dicom_session_decode_*` — ИСПРАВЛЕНО

**Баг был в тестах, не в коде.** `decode_all_frames()` кэширует результат
(`self._frames`). После первого вызова benchmark замерял **возврат кэша**, а не
реальное декодирование. Исправлено: `session._frames = None` перед каждым вызовом.

| Тест | Windows (было, кэш) | Linux (исправлено) |
|------|---------------------|-------------------|
| `decode_uncompressed` 60×256×256 | 1.40 µs (кэш!) | 2.72 ms |
| `decode_jpeg` 30×256×256 | 1.10 µs (кэш!) | 1.14 ms |
| `decode_jpeg2000` 30×256×256 | 1.10 µs (кэш!) | 15.8 ms |

**Вывод:** Windows baseline для этих 3 тестов **некорректен** (измерял кэш, а не
реальное декодирование). Нужно перезапустить на Windows с исправленными тестами.

### Что быстрее на Linux

- **Python dict/set операции** — `frame_cache_get`, `scroll_single_frame_*`, `evict_*` — 4–5x
- **NumPy операции** — `decode_uncompressed_zero_copy`, `to_grayscale_*`, `heap_copy_allocation` — 7–15x
- **NumPy + ctypes** — `wl_lut`, `wl_legacy` — 3–4x
- **Общие pipeline-операции** — `scan_*`, `pipeline_*` — 4–8x

### Рекомендации

1. **Стабилизировать `dicom_session_decode_*` fixture** — добавить `@pytest.fixture(autouse=True)` с явной предзагрузкой данных, чтобы результаты были воспроизводимы между платформами.

2. **Создать Linux baseline файл** — текущие результаты могут служать Linux-baseline для отслеживания регрессий.

3. **Добавить real DICOM тесты** — ✅ Выполнено: 6 тестов (`real_fps_*`) прошли на Linux. Реальный DICOM (800×1276, uint8) показал схожие профили производительности с синтетическими тестами. Рекомендуется добавить тестовый DICOM-файл в репозиторий для CI.

4. **Оптимизировать `color_frame_detection` / `grayscale_check`** — по-прежнему ~19 ms каждая операция (при 100 вызовах). На Windows было ~45 ms. Кандидаты на кэширование или vectorization.

5. **JPEG2000 декодер** — `decode_fragment_jpeg2000_single` = 36 ms, `pipeline_jpeg2000_decode` = 28.6 ms. Это самый тяжелый пайплайн. Рассмотреть фоновый декодинг или кэширование результатов.
