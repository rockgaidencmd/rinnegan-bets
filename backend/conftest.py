"""Root conftest.py — pytest loads this before any test collection.

Ensures backend/ is on sys.path so tests can import data.*, db.*, scripts.*
This file lives at backend/ root (not tests/) so pytest sees it during
its very first init pass, before module discovery.
"""

import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BACKEND_DIR))
