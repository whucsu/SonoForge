"""Application entry point."""

import multiprocessing
import sys

multiprocessing.freeze_support()

from echo_personal_tool.main import main

if __name__ == "__main__":
    raise SystemExit(main())
