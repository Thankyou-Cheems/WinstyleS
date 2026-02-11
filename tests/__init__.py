"""测试包与测试导入引导。"""

import sys
from pathlib import Path

# Ensure tests can import the local package without requiring editable install.
ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))
