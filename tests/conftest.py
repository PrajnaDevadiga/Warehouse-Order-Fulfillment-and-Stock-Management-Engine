from __future__ import annotations

import sys
from pathlib import Path


# Ensure the repository root is on sys.path so `import warehouse` works reliably
# when pytest uses importlib-based importing.
PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

