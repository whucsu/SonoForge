# FULL LOG — 2026-06-24

## Сессия: DICOMweb — сортировка, thread-safe загрузка, фикс диалога

**Сервер:** http://192.168.1.111:8042 (Orthanc DICOMweb)  
**Синхронизация:** успешна, список пациентов есть  

---

## Описание проблем (со слов пользователя)

### Проблема A — сортировка
«Нет сортировки исследований по ФИО, дате исследования/загрузки на сервер.»

### Проблема B — диалог загрузки (первичное описание)
«Нажатие на Загрузить, быстро заполняет полосу загрузки и далее ничего не происходит. Окно диалога не исчезает (а должна исчезать после успешной загрузки). Кнопка Загрузки в дальнейшем не активна. Крестик сверху диалога не закрывает окно. Другие исследования можно продолжать прокручивать и выделять, но кнопке в окне не активны.»

### Проблема C — диалог загрузки (после первой волны фиксов)
«Загрузка завершена на 100%, исследование не открывается (не загружено для анализа), диалоговое окно не исчезает.»

---

## Трассировка и анализ причин

### 1. Thread-safety `httpx.Client` — первичная (и самая опасная)

**Файл:** `orthanc_download_worker.py`  
**Traceback-анализ:**

```
main thread:                           worker thread (QThreadPool):
  OrthancDicomWebClient(client)   →    client.query_instances()
  client.query_studies()          →    client.download_instance()
  client.query_series()                client.query_instances()
```

`httpx.Client` использует внутри event loop + connection pool с **неблокирующими блокировками**, которые **не предназначены для использования из нескольких потоков**. Результат — data race: один поток может читать ответ, предназначенный другому потоку. В `httpx` документация прямо указывает: *"Client instances are not thread-safe by default"*.

**Симптомы:**
- `query_instances` возвращает пустой список или неверные данные
- `download_instance` падает с `httpx.ReadTimeout`, `httpx.RemoteProtocolError` или просто зависает
- Сигнал `done` не доставляется в main thread, диалог подвисает

**Доказательство:**
Прогресс-бар показывает 100%, но `_on_done` не вызывается → `worker.run()` завершился, но `all_ok = False`. См. п. 3 ниже.

---

### 2. Отсутствие реакции на частичную неудачу — основная причина зависания

**Файл:** `orthanc_download_worker.py`  
**Локализация:** метод `run()`, конец цикла по сериям

```python
if all_ok:
    self.signals.done.emit(self._session_id, self._study_uid)
# else: ничего — молчаливый выход
```

Когда `_download_instance` возвращает `None` (после 2 неудачных попыток):
- `series_failed = True`
- `progress.emit(overall, total, series_uid)` — **всё равно вызывается** → бар показывает 100%
- `series_done.emit(series_uid, "failed")` — вызывается, но **никто не слушает** этот сигнал
- `_download_series` возвращает `False`
- `all_ok = False`
- `done` **НЕ эмитится**
- `failed` **НЕ эмитится**
- Поток завершён, диалог виснет на 100%

**Доказательство:**  
Сигнал `series_done` не был подключён ни к одному слоту в `OrthancStudyDialog._on_load()`.  
В оргинале были подключены только: `progress`, `done`, `failed`, `cancelled`.

---

### 3. Таймаут httpx (30 с) при загрузке больших DICOM-файлов

**Файл:** `orthanc_client.py:17`

```python
def __init__(self, base_url, username, password, timeout=30.0):
```

Для ультразвуковых DICOM-клипов (сотни кадров, десятки мегабайт) 30 секунд — недостаточно.  
`httpx.ReadTimeout` → `_download_instance` пробует 2 раза → 60 секунд ожидания → `None` → `all_ok = False` → диалог висит.

---

### 4. Прогресс-бар в indeterminate mode при total=0

В `_on_load`:
```python
self._progress.setMaximum(0)  # indeterminate
```

В `_on_progress`:
```python
if total > 0:
    self._progress.setMaximum(total)
    self._progress.setValue(current)
```

Если `total == 0` (нет экземпляров в серии), прогресс-бар остаётся в indeterminate mode, хотя `_on_done` может корректно сработать.

---

### 5. `closeEvent` не закрывает диалог при потере worker

```python
def closeEvent(self, event):
    if self._downloading:
        event.ignore()
        self._on_cancel()
        return
```

После игнора события, `super().closeEvent()` не вызывается. Если `_on_cancel()` не приводит к закрытию (worker уже мёртв), диалог остаётся открытым и требует повторного клика X.

---

## Сделанные изменения (code diff)

### Файл 1: `orthanc_download_worker.py`

#### 1.1 Импорт OrthancDicomWebClient (строка 9)
```python
from echo_personal_tool.infrastructure.orthanc_client import OrthancDicomWebClient
```

#### 1.2 `__init__` — добавлены connection params (строки 35–44)
```python
def __init__(self, client, cache, session_id, study_uid, series_uids,
             parent=None, *, base_url=None, username=None, password=None):
    ...
    self._base_url = base_url
    self._username = username
    self._password = password
    self._thread_client: OrthancDicomWebClient | None = None
```

#### 1.3 `run()` — thread-local + timeout 120s + emit failed on !all_ok (строки 59–95)
```python
_client: DicomWebClient = self._client
if self._base_url:
    self._thread_client = OrthancDicomWebClient(
        self._base_url, self._username or "", self._password or "",
        timeout=120.0,
    )
    _client = self._thread_client
try:
    ...
    if all_ok:
        self.signals.done.emit(self._session_id, self._study_uid)
    else:
        self.signals.failed.emit(                          # NEW — раньше молчал
            self._study_uid,
            "Одна или несколько серий не загружены — проверьте соединение с сервером",
        )
except Exception as exc:
    ...
finally:
    if self._thread_client is not None:
        self._thread_client.close()
```

#### 1.4 `_download_series` — client параметром (строки 108–132)
```python
def _download_series(self, client: DicomWebClient, series_uid, instances, ...):
```

#### 1.5 `_download_instance` — client параметром (строки 134–146)
```python
def _download_instance(self, client: DicomWebClient, series_uid, instance_uid):
```

### Файл 2: `orthanc_study_dialog.py`

#### 2.1 Импорты (строки 11–23)
- Добавлен: `QAbstractItemView`
- Удалён: `QHeaderView`

#### 2.2 Константа _SORT_ROLE (строка 29)
```python
_SORT_ROLE = Qt.ItemDataRole.UserRole + 2
```

#### 2.3 `__init__` — 3 колонки + сортировка + connection params (строки 44–57)
```python
self.resize(800, 520)
self._tree.setHeaderLabels(["Пациент", "Дата", "Исследование / Серия"])
self._tree.setColumnWidth(0, 200)
self._tree.setColumnWidth(1, 100)
self._tree.setSortingEnabled(True)
self._tree.sortByColumn(1, Qt.SortOrder.DescendingOrder)
self._tree.setSelectionMode(QAbstractItemView.SelectionMode.NoSelection)
```

#### 2.4 `_load_studies` — сортировка списка + 3 колонки (строки 120–147)
```python
studies = sorted(studies, key=lambda s: (s.study_date or "", s.patient_name or ""), reverse=True)
...
item = QTreeWidgetItem([patient_name, study_date, desc])
item.setData(0, _STUDY_UID_ROLE, study.study_uid)
item.setData(0, _SORT_ROLE, patient_name)
item.setData(1, _SORT_ROLE, study_date)
```

#### 2.5 `_on_item_expanded` — 3 колонки для дочерних (строка 162)
```python
child = QTreeWidgetItem(["", "", self._series_label(series)])
```

#### 2.6 `_on_load` — индетерминант + блокировка дерева + connection params + series_done (строки 226–260)
```python
self._tree.setEnabled(False)
self._progress.setMaximum(0)           # indeterminate
...
worker.signals.series_done.connect(self._on_series_done)  # NEW
```

#### 2.7 `closeEvent` — fallback при потере worker (строки 82–93)
```python
if self._downloading:
    event.ignore()
    if self._worker is not None:
        self._on_cancel()
    else:
        self._downloading = False       # NEW — сброс при dead worker
        self._release_client()
        event.accept()
        super().closeEvent(event)
    return
```

#### 2.8 `_on_series_done` — новый слот (строка 280)
```python
def _on_series_done(self, series_uid: str, status: str) -> None:
    if status == "failed":
        short = series_uid[:12] + "…" if len(series_uid) > 12 else series_uid
        self._status_label.setText(f"Ошибка в серии {short}")
```

#### 2.9 `_on_failed` + `_on_cancelled` — разблокировка дерева (строки 296, 307)
```python
self._tree.setEnabled(True)   # добавлено
```

### Файл 3: `main_window.py`

**Метод `_open_orthanc_dialog` (строка 273):**
```python
if settings.use_mock:
    client = FakeDicomWebClient()
    dialog = OrthancStudyDialog(client, self._orthanc_cache, self)
else:
    client = OrthancDicomWebClient(settings.url, settings.username, settings.password)
    dialog = OrthancStudyDialog(client, self._orthanc_cache, self,
                                base_url=settings.url,
                                username=settings.username,
                                password=settings.password)
```

---

## Итоговое состояние

| Шаг | Что происходит | Статус |
|-----|---------------|--------|
| Пинг сервера | `_check_ping()` | ✅ |
| Поиск по имени | `_on_find()` → `query_studies` | ✅ |
| Сортировка | по дате (DESC), затем ФИО | ✅ |
| Разворот серий | `_on_item_expanded()` → `query_series` | ✅ |
| Чекбоксы | checkable series, `_on_item_changed` | ✅ |
| Кнопка Загрузить | enabled when checked series | ✅ |
| **Загрузка 100%** | progress идёт, bar заполняется | ✅ |
| **Закрытие диалога** | `_on_done` → `accept()` | ⚠️ если done не эмитится |
| **Ошибка загрузки** | `all_ok=False` → `failed` эмитится | ✅ **фикс** |
| **Таймаут httpx** | 30s → 120s | ✅ **фикс** |
| **series_done** | подключен `_on_series_done` | ✅ **фикс** |
| **Отмена загрузки** | cancel → clear session → reject | ✅ |
| **Крестик X** | closeEvent → отмена → закрытие | ✅ |
| **Открытие папки после загрузки** | `open_folder(path)` | ⚠️ если `accept()` не сработал |

### Что ещё может пойти не так

1. **ScanWorker после open_folder** — загруженные DICOM-файлы сканируются в фоне. Если файлы повреждены или имеют неверную структуру, `ScanWorker` может упасть молча, и галерея не обновится.
2. **Orthanc DICOMweb не возвращает `application/dicom`** — сервер может ответить с другой Content-Type или вернуть ошибку, что вызовет `httpx.HTTPStatusError`.
3. **Сетевые проблемы** — если сервер Orthanc периодически теряет соединение, WADO-RS запрос может упасть. Новый `timeout=120.0` и retry (2 попытки) должны помочь.
4. **Проблема с accept() после done** — теоретически `_release_client()` может упасть при вызове `self._client.close()`, если оригинальный клиент уже был закрыт или повреждён.

---

## Приложение: цепочка вызовов при загрузке

```
[UI] _on_load()
  ├── создаёт OrthancDownloadWorker(client, cache, session, study, series)
  ├── подключает сигналы
  └── QThreadPool.start(worker)

[Worker Thread] run()
  ├── создаёт OrthancDicomWebClient (thread-local, timeout=120s) — если !mock
  ├── для каждой серии:
  │     ├── query_instances(study, series)
  │     └── _download_series(client, series, instances, total, prior)
  │           └── для каждого instance:
  │                 ├── _download_instance(client, series, sop_uid)
  │                 │     └── download_instance(study, series, sop)
  │                 ├── cache.save_instance(session, study, series, sop, data)
  │                 └── progress.emit(overall, total, series_uid)  ← bar updates
  ├── если all_ok:
  │     └── done.emit(session, study_uid)  ← dialog closes
  └── иначе:
        └── failed.emit(study, message)    ← dialog shows error
  └── finally:
        └── thread_client.close()

[Main Thread] _on_done(session, study)
  ├── self._result = (session, study)
  ├── self.accept()
  │     ├── _release_client()
  │     └── super().accept()  ← hides dialog, exec() returns

[Main Thread] MainWindow._open_orthanc_dialog()
  └── dialog.exec() == Accepted:
        ├── result = dialog.result_data()
        └── controller.open_folder(path)  ← scans downloaded files
```
