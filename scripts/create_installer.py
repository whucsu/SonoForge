"""Create a self-extracting installer for SonoForge on Windows.

Produces SonoForge-Setup.exe — a .bat + .zip hybrid that extracts itself
and runs setup.bat. Uses a marker to separate batch header from zip data.
"""

import io
import os
import struct
import sys
import zipfile
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
STAGING = PROJECT_ROOT / "dist" / "SonoForge-Setup"
OUTPUT = PROJECT_ROOT / "dist" / "SonoForge-Setup.exe"
MARKER = b"__SONOFORGE_ZIP_START__"

# Header batch script that extracts the embedded zip and runs setup.bat
HEADER = r"""@echo off
setlocal
set "DIR=%TEMP%\SonoForge-Setup-%RANDOM%"
mkdir "%DIR%" 2>nul

echo Extracting SonoForge installer...

REM Find zip data after marker in this file
powershell -NoProfile -Command ^
 "$f='%~f0';" ^
 "$d=[IO.File]::ReadAllBytes($f);" ^
 "$m=[Text.Encoding]::UTF8.GetBytes('__SONOFORGE_ZIP_START__');" ^
 "$i=[Array]::IndexOf($d,$m,0);" ^
 "$s=$i+$m.Length;" ^
 "$ms=New-Object IO.MemoryStream($d,$s,$d.Length-$s);" ^
 "$z=New-Object IO.Compression.ZipArchive($ms,[IO.Compression.ZipArchiveMode]::Read);" ^
 "foreach($e in $z.Entries){" ^
 "  $t=Join-Path '%DIR%' $e.FullName;" ^
 "  $p=Split-Path $t -Parent;" ^
 "  if(!(Test-Path $p)){New-Item -ItemType Directory -Path $p -Force|Out-Null}" ^
 "  if($e.Name){[IO.Compression.ZipFileExtensions]::ExtractToFile($e,$t,$true)}" ^
 "}"

echo Extracted to %DIR%
echo.
cd /d "%DIR%"
call setup.bat
echo.
echo Cleaning up...
rmdir /s /q "%DIR%" 2>nul
endlocal
"""


def create_installer():
    if not STAGING.exists():
        print(f"Error: staging directory not found: {STAGING}")
        sys.exit(1)

    print("Creating self-extracting installer...")

    # Create zip in memory
    zip_buf = io.BytesIO()
    with zipfile.ZipFile(zip_buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(STAGING):
            # Skip .sed files
            dirs[:] = [d for d in dirs]
            for f in files:
                if f.endswith(".sed"):
                    continue
                fp = Path(root) / f
                arcname = str(fp.relative_to(STAGING))
                zf.write(fp, arcname)
                print(f"  + {arcname}")

    # Write: header batch + marker + zip data
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT, "wb") as out:
        out.write(HEADER.encode("utf-8"))
        out.write(b"\r\n")
        out.write(MARKER)
        out.write(zip_buf.getvalue())

    size_mb = OUTPUT.stat().st_size / (1024 * 1024)
    print()
    print(f"Installer created: {OUTPUT}")
    print(f"Size: {size_mb:.1f} MB")
    print()
    print("Run SonoForge-Setup.exe to install.")


if __name__ == "__main__":
    create_installer()
