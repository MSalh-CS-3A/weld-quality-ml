"""Run the stdlib-only downloader without installing the project first."""

import sys
from pathlib import Path

# This standalone entry point works from any current working directory.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from weld_quality.download import main


if __name__ == "__main__":
    raise SystemExit(main())
