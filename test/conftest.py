"""Test configuration: add the package root to sys.path so both
`from core.models import ...` (legacy) and `from qgis_layer_diff.core.models import ...`
styles work.
"""

import sys
from pathlib import Path

# Add the project root (parent of test/) so `import core` works.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
