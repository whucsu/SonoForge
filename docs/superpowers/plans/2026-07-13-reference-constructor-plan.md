# Reference Constructor — Implementation Plan

## Overview

Build a visual editor for the structured reference handbook. 4 phases, ~20 tasks.

---

## Phase 1: Core (MVP) — 7 tasks

### T1: Storage Layer
**Files:** `constructor/storage/__init__.py`, `yaml_storage.py`, `schema_validator.py`, `image_storage.py`
**Spec ref:** §1.1, §5.2

- [ ] `YamlStorage.load(path) -> dict` — read YAML
- [ ] `YamlStorage.save(data, path)` — write YAML with backup (`.bak`)
- [ ] `SchemaValidator.validate(data) -> list[Error]` — JSON Schema validation
- [ ] `ImageStorage.resolve(path) -> Path` — resolve image path
- [ ] `ImageStorage.copy(src, dest) -> Path` — copy image to images dir
- [ ] Create `references_schema.json` from existing YAML structure
- [ ] Unit tests for load/save/validate

### T2: Working Copy Model
**Files:** `constructor/models/__init__.py`, `reference_model.py`
**Spec ref:** §1.3

- [ ] `ReferenceModel` class — mutable working copy
- [ ] `from_yaml(data) -> ReferenceModel` — deserialize
- [ ] `to_yaml() -> str` — serialize
- [ ] `deep_copy() -> ReferenceModel` — for undo snapshot
- [ ] `validate() -> list[Error]` — semantic validation (unique IDs, etc.)
- [ ] Unit tests for round-trip (load → modify → save → load)

### T3: Constructor Dialog
**Files:** `constructor/constructor_dialog.py`, `constructor/__init__.py`
**Spec ref:** §3.1

- [ ] Frameless maximizable QDialog (same style as AseReferenceDialog)
- [ ] Title bar with drag, min/max/close
- [ ] Toolbar: Save, Preview, Undo, Redo, Import Excel, Export PDF, Export HTML
- [ ] 3-panel QSplitter layout (left 20%, center 50%, right 30%)
- [ ] Bottom metadata bar
- [ ] Menu integration in AseReferenceDialog ("Файл → Конструктор")

### T4: Topic Editor (Left Panel)
**Files:** `constructor/editors/__init__.py`, `topic_editor.py`, `base_editor.py`
**Spec ref:** §3.2

- [ ] QListWidget with topic names
- [ ] Double-click rename (inline edit)
- [ ] Right-click: Add, Delete, Duplicate
- [ ] Selection signal → populate center + right panels
- [ ] Base editor class with undo hooks

### T5: Parameter Table Editor (Center Panel)
**Files:** `constructor/editors/parameter_table_editor.py`
**Spec ref:** §3.3

- [ ] QTableWidget with columns: id, name, unit, norm_male_low/high, norm_female_low/high, pathology_desc, source
- [ ] Editable cells (double-click)
- [ ] Add row button
- [ ] Delete row (select + Delete key)
- [ ] Selection → populate bottom metadata bar

### T6: Pathology Editor (Right-Top Panel)
**Files:** `constructor/editors/pathology_editor.py`
**Spec ref:** §3.4

- [ ] QListWidget with pathology names
- [ ] Add / Delete / Rename
- [ ] Selection → load pathology's parameters into center table
- [ ] Toggle: Flat vs Gradations mode

### T7: Save + Undo
**Files:** `constructor/constructor_widget.py`
**Spec ref:** §4.1

- [ ] Save button: validate → write YAML → update `_saved_state`
- [ ] Undo button: restore `_saved_state` → refresh all editors
- [ ] Dirty indicator in title bar ("*")

---

## Phase 2: Rich Editing — 4 tasks

### T8: Gradation Editor
**Files:** `constructor/editors/gradation_editor.py`
**Spec ref:** §3.3, §4.8

- [ ] Add/remove gradation columns in parameter table
- [ ] Gradation name editing
- [ ] Parameter rows span all gradation columns
- [ ] Visual grouping (colored headers per gradation)

### T9: Image Editor (Right-Bottom Panel)
**Files:** `constructor/editors/image_editor.py`
**Spec ref:** §3.5

- [ ] QListWidget with thumbnails + filenames
- [ ] Drag & drop from OS file manager
- [ ] Context menu: Remove, Rename, Open External
- [ ] Zoom: Fit, 50%, 100%, 200%, 400%
- [ ] Preview pane with selected image

### T10: Metadata Editor (Bottom Bar)
**Files:** `constructor/editors/metadata_editor.py`
**Spec ref:** §3.6

- [ ] Sex radio buttons (M/F/Both)
- [ ] Age spinbox (0-120, optional)
- [ ] Source line edit
- [ ] Description line edit
- [ ] Changes apply to selected parameter/pathology

### T11: Preview
**Files:** `constructor/preview/__init__.py`, `reference_preview.py`, `overlay_preview.py`
**Spec ref:** §4.2

- [ ] Preview button opens new window
- [ ] Renders `StructuredReferenceWidget` from working copy
- [ ] Renders overlay HTML from working copy
- [ ] Read-only, non-modal
- [ ] Refresh on demand (button click)

---

## Phase 3: Import/Export — 3 tasks

### T12: Excel Importer
**Files:** `constructor/importers/__init__.py`, `excel_importer.py`
**Spec ref:** §4.5

- [ ] Read .xlsx via openpyxl
- [ ] Mapping dialog: map columns → ParameterRef fields
- [ ] Preview diff before import
- [ ] Merge or replace modes

### T13: PDF Exporter
**Files:** `constructor/exporters/__init__.py`, `pdf_exporter.py`
**Spec ref:** §4.6

- [ ] Render StructuredReferenceWidget to QPrinter
- [ ] One section per topic
- [ ] Pathology tables, images inline
- [ ] Page numbers, headers

### T14: HTML Exporter
**Files:** `constructor/exporters/__init__.py`, `html_exporter.py`
**Spec ref:** §4.7

- [ ] Standalone HTML with embedded CSS
- [ ] Base64-encoded images
- [ ] Client-side search (JS)
- [ ] Collapsible sections

---

## Phase 4: Polish — 4 tasks

### T15: Drag-Reorder
**Spec ref:** §4.3

- [ ] Topics: drag-reorder in QListWidget
- [ ] Pathologies: drag-reorder
- [ ] Parameters: drag-reorder rows in table

### T16: Validation UI
**Spec ref:** §4.4

- [ ] Inline badges: red on invalid ID, orange on missing norms
- [ ] Validation summary dialog on save failure
- [ ] Orphaned images detection

### T17: Keyboard Shortcuts
- [ ] Ctrl+S: Save
- [ ] Ctrl+Z: Undo
- [ ] Ctrl+P: Preview
- [ ] Delete: remove selected row/item
- [ ] Ctrl+N: add new topic/pathology/parameter

### T18: Tests
- [ ] Unit: all storage, model, importers, exporters
- [ ] Integration: full save/load cycle
- [ ] Widget: all editors (QTest)

---

## Dependencies

```
Phase 1 (T1-T7) → Phase 2 (T8-T11) → Phase 3 (T12-T14) → Phase 4 (T15-T18)
```

Within Phase 1:
```
T1 → T2 → T3
         ├→ T4 → T5
         ├→ T6
         └→ T7
```

---

## Estimated Effort

| Phase | Tasks | Hours |
|-------|-------|-------|
| Phase 1 | 7 | 8-10 |
| Phase 2 | 4 | 6-8 |
| Phase 3 | 3 | 4-6 |
| Phase 4 | 4 | 4-6 |
| **Total** | **18** | **22-30** |

---

## Success Criteria

1. Can create/edit/delete topics, pathologies, parameters via UI
2. Can add/remove/reorder images with drag-drop
3. Save produces valid YAML + passes JSON Schema validation
4. Preview shows reference exactly as StructuredReferenceWidget would render it
5. Undo reverts to last save
6. Excel import works with mapping dialog
7. PDF/HTML export produces readable output
8. No regressions to existing reference viewer
