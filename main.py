import sys
from pathlib import Path

# Add src to path for direct python main.py execution
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from db_plugin.main import main

if __name__ == "__main__":
    main()
