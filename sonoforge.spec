# -*- mode: python ; coding: utf-8 -*-
from PyInstaller.utils.hooks import collect_data_files

datas = [('src/echo_personal_tool/resources/fonts', 'echo_personal_tool/resources/fonts'), ('src/echo_personal_tool/resources/references', 'echo_personal_tool/resources/references'), ('src/echo_personal_tool/resources/icons', 'echo_personal_tool/resources/icons'), ('models', 'models')]
datas += collect_data_files('echo_personal_tool')


a = Analysis(
    ['src/echo_personal_tool/__main__.py'],
    pathex=[],
    binaries=[],
    datas=datas,
    hiddenimports=['pyside6', 'pyqtgraph', 'pydicom', 'pylibjpeg', 'pylibjpeg_openjpeg', 'pylibjpeg_libjpeg', 'numpy', 'scipy', 'cv2', 'httpx', 'psutil', 'pymupdf', 'pynetdicom', 'yaml', 'jsonschema', 'onnxruntime', 'reportlab', 'openpyxl', 'echo_personal_tool'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='sonoforge',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='sonoforge',
)
