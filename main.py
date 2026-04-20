"""Development entry point for running the app directly.

Usage: python main.py

For production, use the installed console script: db-plugin
"""
import sys
from pathlib import Path

src_path = Path(__file__).parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

from db_plugin.main import main

if __name__ == "__main__":
    main()
