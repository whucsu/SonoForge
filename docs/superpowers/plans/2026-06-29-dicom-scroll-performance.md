# DICOM Scroll Performance (P0) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make DICOM multiframe (JPEG) wheel scroll responsive on weak and strong systems via debounce, target-first decode, adaptive neighbor prefetch, and fast display path.

**Architecture:** Coalesce wheel events in `ViewerWidget`; `AppController` loads target frame first (`batch_size=1`), then optional neighbor batch using `PlaybackConfig.scroll_batch_size`; cancel stale loads via `scroll_load_id`; `MainWindow` uses `show_frame_fast` during active scroll.

**Tech Stack:** PySide6, QTimer, QThreadPool, existing `FrameLoaderWorker` / `FrameCache` / `DicomSession`.

**Spec:** [`docs/superpowers/specs/2026-06-29-dicom-scroll-performance-design.md`](../specs/2026-06-29-dicom-scroll-performance-design.md)

---

## File Map

| File | Responsibility |
|------|----------------|
| `infrastructure/system_profiler.py` | Add `scroll_debounce_ms`, `scroll_batch_size` to `PlaybackConfig` |
| `presentation/viewer_widget.py` | Wheel debounce → single `frame_selected` |
| `application/app_controller.py` | Two-phase scroll load, `scroll_load_id`, scroll-active flag |
| `presentation/main_window.py` | `show_frame_fast` vs `show_frame` during scroll |
| `tests/unit/test_scroll_debounce.py` | Debounce behavior |
| `tests/unit/test_scroll_two_phase_load.py` | Phase 1/2 + cancellation |
| `tests/unit/test_system_profiler.py` | Extended config fields |

---

### Task 1: Extend PlaybackConfig

**Files:**
- Modify: `src/echo_personal_tool/infrastructure/system_profiler.py`
- Test: `tests/unit/test_system_profiler.py`

- [ ] **Step 1: Write failing test for new fields**

```python
def test_playback_config_includes_scroll_fields():
    cfg = detect_playback_config()
    assert cfg.scroll_debounce_ms in (50, 80)
    assert cfg.scroll_batch_size in (3, 8)
```

- [ ] **Step 2: Run test — expect FAIL**

Run: `uv run pytest tests/unit/test_system_profiler.py::test_playback_config_includes_scroll_fields -v`

- [ ] **Step 3: Add fields to dataclass and profiles**

```python
scroll_debounce_ms: int
scroll_batch_size: int
# _LOW_END: scroll_debounce_ms=80, scroll_batch_size=3
# _HIGH_END: scroll_debounce_ms=50, scroll_batch_size=8
```

- [ ] **Step 4: Run tests — expect PASS**

Run: `uv run pytest tests/unit/test_system_profiler.py -v`

---

### Task 2: Wheel debounce in ViewerWidget

**Files:**
- Modify: `src/echo_personal_tool/presentation/viewer_widget.py`
- Create: `tests/unit/test_scroll_debounce.py`

- [ ] **Step 1: Write failing test**

Use `qtbot` + `QSignalSpy` on `frame_selected`:
- Emit 5 rapid `_handle_wheel` events with increasing index
- Before timer: spy count == 0
- After `qtbot.wait(100)`: spy count == 1, last arg == final index

- [ ] **Step 2: Run test — expect FAIL**

Run: `uv run pytest tests/unit/test_scroll_debounce.py -v`

- [ ] **Step 3: Implement debounce**

- Add `_scroll_debounce_timer` (single-shot), `_pending_scroll_index: int | None`
- `_handle_wheel`: compute `new_index`, store in `_pending_scroll_index`, restart timer with `scroll_debounce_ms` from controller/preferences (pass via `ViewerWidget.set_scroll_debounce_ms` or read from controller ref)
- On timeout: `frame_selected.emit(_pending_scroll_index)`

- [ ] **Step 4: Run test — expect PASS**

---

### Task 3: Two-phase scroll load in AppController

**Files:**
- Modify: `src/echo_personal_tool/application/app_controller.py`
- Create: `tests/unit/test_scroll_two_phase_load.py`

- [ ] **Step 1: Write failing tests**

1. `test_scroll_phase1_uses_batch_size_one` — spy `FrameLoaderWorker`, wheel target frame 5 → first worker has `batch_size=1`, `frame_index=5`
2. `test_scroll_phase2_after_phase1` — after phase1 callback, second worker starts with `batch_size=scroll_batch_size`, `frame_index=6`
3. `test_scroll_cancel_phase2_on_new_target` — phase1 done, new target before phase2 → no phase2 for old id

- [ ] **Step 2: Run tests — expect FAIL**

- [ ] **Step 3: Implement scroll load state machine**

Add fields:
```python
_scroll_load_id: int = 0
_scroll_phase: Literal["idle", "target", "neighbors"] = "idle"
_scroll_active: bool = False
```

Refactor `_request_frame_if_needed`:
1. Cache hit → `_emit_cached_frame`, return
2. Increment `_scroll_load_id`, set phase `target`
3. Start worker `batch_size=1`
4. On batch callback (1 frame): emit UI, set phase `neighbors`, if `loaded_ahead < scroll_batch_size` start second worker
5. On neighbor callback: cache only

Use `_scroll_load_id` instead of reusing `_batch_load_id` for scroll-specific path (or namespace clearly).

Invalidate prefetch: `_invalidate_prefetch()` when starting scroll target load.

- [ ] **Step 4: Run tests — expect PASS**

Run: `uv run pytest tests/unit/test_scroll_two_phase_load.py tests/unit/test_app_controller_dicom_cache.py -v`

---

### Task 4: Fast display path during scroll

**Files:**
- Modify: `src/echo_personal_tool/presentation/main_window.py`
- Modify: `src/echo_personal_tool/application/app_controller.py` (expose `scroll_active` or signal)

- [ ] **Step 1: Write failing test (optional integration-style)**

In `test_scroll_two_phase_load.py` or new test: mock viewer, assert `show_frame_fast` called when `controller.scroll_active` during `frame_loaded`.

- [ ] **Step 2: Implement scroll_active lifecycle**

- Set `_scroll_active = True` on new scroll target
- `QTimer.singleShot(scroll_debounce_ms + 50, clear_scroll_active)` on each scroll
- `MainWindow._on_frame_loaded`: use `show_frame_fast` when `is_playing or controller.is_scroll_active()`
- When scroll settles (timer): call `show_frame` once for full overlay restore if needed

- [ ] **Step 3: Manual smoke**

Run app, open multiframe DICOM, fast wheel — verify image updates without long freeze.

---

### Task 5: Wire debounce ms from config

**Files:**
- Modify: `src/echo_personal_tool/presentation/main_window.py` (on init / controller connect)
- Modify: `src/echo_personal_tool/presentation/viewer_widget.py`

- [ ] Pass `controller._playback_config.scroll_debounce_ms` to viewer after `MainWindow` init
- [ ] Verify multiview viewer2 gets same debounce if it emits wheel events

---

### Task 6: Full regression

- [ ] Run: `uv run pytest tests/unit/test_playback_prefetch.py tests/unit/test_decode_workers_lazy.py tests/unit/test_scroll_debounce.py tests/unit/test_scroll_two_phase_load.py -v`
- [ ] Run: `uv run pytest tests/ -q --tb=line` (full suite)
- [ ] Manual QA per spec §6.2 (JPEG multiframe, Linux/Windows)

---

## Notes for implementer

- Do **not** change `DicomSession` fragment parsing in P0.
- Keep `_BATCH_LOAD_SIZE` only if still used elsewhere; scroll path uses `PlaybackConfig.scroll_batch_size`.
- Timeline slider drag is out of scope; only wheel debounce in P0.
- Follow existing patterns: `partial(callback, request_id, path)` for worker signals.
