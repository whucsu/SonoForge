# Build

Скрипты и конфигурации для сборки приложения.

## Структура

| Папка | Описание |
|-------|----------|
| `linux/` | Сборка для Linux (.deb) |
| `windows/` | Сборка для Windows (.zip) |

## Linux

| Файл | Описание |
|------|----------|
| `build-lite.sh` | Lightweight .deb (~50MB, deps скачиваются) |
| `build.sh` | Полная .deb сборка (PyInstaller) |
| `build.spec` | PyInstaller spec |
| `sonoforge-launcher` | Bash-лаунчер с автоустановкой |
| `sonoforge.desktop` | Desktop entry |

## Windows

| Файл | Описание |
|------|----------|
| `build-lite.bat` | Lightweight .zip (~50MB, deps скачиваются) |
| `build.bat` | Полная сборка (PyInstaller) |
| `build.spec` | PyInstaller spec |
| `sonoforge-launcher.bat` | Batch-лаунчер с автоустановкой |

## Сборка

```bash
# Linux (.deb)
./build/linux/build-lite.sh

# Windows (.zip)
build\windows\build-lite.bat
```
