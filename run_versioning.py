#!/usr/bin/env python3
"""
Run model versioning system.
Creates version 1.0.0 from currently trained models.
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from models.versioning import version_current_models

if __name__ == "__main__":
    version_current_models()
    print("\n✓ Model versioning complete")
