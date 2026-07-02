# Benchmark Baseline

**Date:** 2026-07-02
**Hardware:** Linux dev machine (pytest-benchmark, ECHO_BENCH=1)
**Command:** `ECHO_BENCH=1 pytest tests/bench/ --benchmark-only --benchmark-warmup=off --benchmark-min-rounds=3`

Use this file to compare performance across machines. Re-run benchmarks on the target system and update the "Target" column.

---

## Playback Pipeline

| Benchmark | Median | OPS | Notes |
|-----------|--------|-----|-------|
| `playback_fps_30_frame_loop` | 13.4 µs | 72.6K | 30-frame get+set_current sweep |
| `playback_fps_100_frame_loop` | 46.4 µs | 20.6K | 100-frame loop, evict_window=100 |
| `prefetch_batch_load` | 1.09 ms | 865 | put() 8 frames into cache |
| `small_loop_full_prefetch` | 1.76 ms | 545K | List comprehension for 45-frame cine |
| `warmup_loaded_ahead_count` | 8.93 µs | 107K | loaded_ahead() sweep over 60 frames |
| `double_next_skip_check` | 2.57 µs | 377K | is_loaded(next) + is_loaded(next+1) loop |

## Scroll / Navigation

| Benchmark | Median | OPS | Notes |
|-----------|--------|-----|-------|
| `scroll_single_frame_hit` | 525 ns | 1.82M | set_current + get, cache hit |
| `scroll_single_frame_miss` | 638 ns | 1.36M | set_current to evicted frame |
| `scroll_rapid_forward_20` | 7.96 µs | 118K | 20 consecutive forward set_current |
| `scroll_rapid_backward_20` | 7.92 µs | 121K | 20 consecutive backward set_current |
| `directional_prefetch_forward` | 24.7 µs | 38.8K | loaded_ahead + nearest_loaded_ahead sweep |
| `directional_prefetch_backward` | 22.8 µs | 42.0K | loaded_before + nearest_loaded_before sweep |

## Decode / Cache

| Benchmark | Median | OPS | Notes |
|-----------|--------|-----|-------|
| `decode_uncompressed_zero_copy` | 23.7 µs | 42.6K | np.frombuffer view, 10 frames 256x256 uint16 |
| `decode_uncompressed_with_copy` | 55.5 µs | 17.9K | np.frombuffer + .copy(), same data |
| `zero_copy_vs_copy_gain` | — | — | **2.3x faster** without copy |
| `evict_200_frames_sweep` | 2.01 ms | 489 | set_current sweep over 200-frame cache |
| `evict_with_pinned_frames` | 8.62 ms | 115K | 50 pinned frames, evict guard overhead |
| `frame_cache_get` | 92.0 ns | 10.1M | Single get() on loaded frame |
| `frames_property_first_call` | 22.4 µs | 43.8K | np.stack rebuild (60 frames 16x16) |
| `frames_property_cached` | 75.8 ns | 13.0M | Cached result return |
| `sorted_keys_eviction_logic` | 9.64 µs | 102K | bisect-based eviction, 500 frames |

## Rendering

| Benchmark | Median | OPS | Notes |
|-----------|--------|-----|-------|
| `wl_lut_uint16` | 3.76 ms | 265 | W/L LUT on 512x512 uint16 |
| `wl_lut_uint8` | 4.13 ms | 238 | W/L LUT on 512x512 uint8 |
| `wl_lut_512x512` (existing) | 3.09 ms | 322 | W/L LUT reference from test_viewer_perf |
| `wl_legacy_512x512` (existing) | 2.94 ms | 334 | Legacy float percentile path |
| `to_grayscale_uint8` | 24.2 µs | 38.1K | BGR → grayscale, 512x512 |
| `to_grayscale_array_float64` | 72.5 µs | 13.5K | Full float64 grayscale, 512x512 |
| `to_display_rgb` | 1.23 ms | 803 | BGR → RGB for color Doppler, 512x512 |
| `color_frame_detection` | 20.1 ms | 49.6 | is_color_frame × 100 calls |
| `grayscale_check` | 18.6 ms | 52.9 | is_effective_grayscale × 100 calls |

## Network (Fake clients)

| Benchmark | Median | OPS | Notes |
|-----------|--------|-----|-------|
| `dimse_c_echo_fake` | 38.0 ns | 25.9M | FakeDimseClient.c_echo() |
| `dimse_c_find_studies_fake` | 125.0 ns | 7.83M | FakeDimseClient.c_find_studies() |
| `dimse_c_find_studies_filtered` | 385.0 ns | 2.54M | c_find_studies(patient_name="DOE") |
| `dimse_c_find_series_fake` | 85.5 ns | 11.3M | c_find_series() |
| `dimse_c_find_instances_fake` | 88.0 ns | 11.1M | c_find_instances() |
| `dimse_c_store_fake` | 40.1 ns | 23.9M | c_store(4KB) |
| `web_query_studies` | 1.52 µs | 642K | FakeDicomWebClient.query_studies() |
| `web_query_studies_filtered` | 1.75 µs | 553K | query_studies(patient_name="DOE") |
| `web_query_series` | 1.36 µs | 714K | query_series() |
| `web_stow_instances` | 360 ns | 2.71M | stow_instances(5×2KB) |
| `query_service_auto` | 2.25 µs | 418K | DicomQueryService AUTO mode |
| `query_service_dimse_only` | 427 ns | 2.26M | DicomQueryService DIMSE-only |
| `query_service_series` | 1.47 µs | 661K | query_series delegation |
| `stow_multipart_1_file` | 4.15 µs | 236K | Multipart body build, 1 file |
| `stow_multipart_10_files` | 48.2 µs | 20.3K | Multipart body build, 10 files |
| `stow_multipart_50_files` | 302 µs | 3.20K | Multipart body build, 50 files |

## Memory

| Benchmark | Median | Notes |
|-----------|--------|-------|
| `mem_30_frame_cine` | 32.9 µs | Load + sweep 30-frame cine (256x256 uint16) |
| `mem_200_frame_cine` | 77.4 µs | Load + sweep 200-frame cine (128x128 uint16) |
| `memory_bytes_tracking` | 6.26 µs | memory_bytes() call during playback |
| `zero_copy_view_lifetime` | 37.7 µs | 100 × np.frombuffer views (256x256) |
| `heap_copy_allocation` | 275.9 µs | 100 × frombuffer + copy (256x256) |
| `eviction_reclaims_memory` | 2.00 ms | Verify memory_bytes() drops after evict |

---

## Key Takeaways

1. **Zero-copy decode is 2.3x faster** than copy path — confirmed.
2. **FrameCache.get() is ~92ns** — negligible overhead.
3. **FrameCache.frames cached call is ~76ns** — memoization works.
4. **Scroll single-frame latency is sub-microsecond** (525ns hit, 638ns miss).
5. **W/L LUT is ~3-4ms** on 512x512 — within target for real-time slider.
6. **STOW multipart scales linearly** — 6µs/file.
7. **FakeDimseClient C-ECHO is ~38ns** — no overhead from fake layer.

## How to Re-run

```bash
# Full suite
ECHO_BENCH=1 pytest tests/bench/ -v --benchmark-only --benchmark-warmup=off --benchmark-min-rounds=3

# Single category
ECHO_BENCH=1 pytest tests/bench/test_playback_bench.py --benchmark-only

# Compare with saved baseline
ECHO_BENCH=1 pytest tests/bench/ --benchmark-only --benchmark-compare=0001
```
