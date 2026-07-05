#!/usr/bin/env bash
# ============================================
#  ECHO Personal Tool — Linux Build
#  Folder mode (portable directory)
# ============================================
set -euo pipefail

echo ""
echo "=== ECHO Personal Tool — Linux Build ==="
echo ""

# [1] Проверка venv
VENV_PYTHON=".venv/bin/python"
VENV_PIP=".venv/bin/pip"
if [ ! -f "$VENV_PYTHON" ]; then
    echo "[ERROR] .venv not found."
    echo "  Run: python3 -m venv .venv && .venv/bin/pip install -e '.[phase2]'"
    exit 1
fi

# [2] Установка зависимостей
echo "[1/3] Installing dependencies..."
$VENV_PIP install -e ".[phase2]" --quiet 2>/dev/null || $VENV_PIP install -e "." --quiet
$VENV_PIP install pyinstaller --quiet

# [3] Сборка
echo "[2/3] Building (folder mode)..."
$VENV_PYTHON -m PyInstaller build/linux/build.spec --noconfirm --clean

# [4] Готово
echo ""
echo "[3/3] Build complete!"
echo ""
echo "  Output: dist/ECHO-Personal-Tool/"
echo "  Launch: ./dist/ECHO-Personal-Tool/ECHO-Personal-Tool"
echo ""
