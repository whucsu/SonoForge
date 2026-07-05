@echo off
REM ============================================
REM  ECHO Personal Tool — Windows 10 Build
REM  Folder mode (portable directory)
REM ============================================
setlocal enabledelayedexpansion

echo.
echo === ECHO Personal Tool — Windows Build ===
echo.

REM [1] Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found. Install Python 3.11 and add to PATH.
    exit /b 1
)

REM [2] Установка зависимостей
echo [1/3] Installing dependencies...
pip install -e ".[phase2]" --quiet
pip install pyinstaller --quiet
if errorlevel 1 (
    echo [ERROR] Failed to install dependencies.
    exit /b 1
)

REM [3] Сборка
echo [2/3] Building (folder mode)...
pyinstaller build\windows\build.spec --noconfirm --clean
if errorlevel 1 (
    echo [ERROR] PyInstaller build failed.
    exit /b 1
)

REM [4] Готово
echo.
echo [3/3] Build complete!
echo.
echo   Output: dist\ECHO-Personal-Tool\
echo   Launch: dist\ECHO-Personal-Tool\ECHO-Personal-Tool.exe
echo.

endlocal
