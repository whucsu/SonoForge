"""SonoForge installer stub — extracts embedded zip and runs setup.bat."""

import io
import os
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path


def get_embedded_zip():
    """Read zip data bundled as a resource by PyInstaller."""
    if getattr(sys, "frozen", False):
        # Running as PyInstaller exe — bundled files are in sys._MEIPASS
        bundle_dir = Path(sys._MEIPASS)
        zip_path = bundle_dir / "installer_data.zip"
        if zip_path.exists():
            return zip_path.read_bytes()
    return None


def main():
    print("=" * 50)
    print("  SonoForge Installer")
    print("=" * 50)
    print()

    zip_data = get_embedded_zip()
    if not zip_data:
        print("Error: embedded archive not found.")
        input("Press Enter to exit...")
        sys.exit(1)

    # Extract to temp directory
    tmp_dir = tempfile.mkdtemp(prefix="SonoForge-Setup-")
    print("Extracting files...")
    with zipfile.ZipFile(io.BytesIO(zip_data)) as zf:
        zf.extractall(tmp_dir)

    print(f"Extracted to: {tmp_dir}")
    print()

    # Run setup.bat
    setup_bat = os.path.join(tmp_dir, "setup.bat")
    if os.path.exists(setup_bat):
        subprocess.call(["cmd", "/c", setup_bat], cwd=tmp_dir)
    else:
        print("Error: setup.bat not found in archive.")
        input("Press Enter to exit...")
        sys.exit(1)

    # Cleanup
    try:
        shutil.rmtree(tmp_dir, ignore_errors=True)
    except Exception:
        pass


if __name__ == "__main__":
    main()
