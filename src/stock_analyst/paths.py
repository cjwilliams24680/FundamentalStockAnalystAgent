"""Repository-anchored filesystem locations shared across the package.

These anchors resolve relative to the repository checkout, which holds because
uv installs the project in editable mode (the package is imported from src/).
"""

from pathlib import Path

_REPOSITORY_ROOT = Path(__file__).resolve().parents[2]
DATA_DIRECTORY = _REPOSITORY_ROOT / "data"
SANDBOX_DIRECTORY = _REPOSITORY_ROOT / "sandbox"
OUTPUT_DIRECTORY = _REPOSITORY_ROOT / "output"
