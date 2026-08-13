# =============================================================================
# conftest.py
# =============================================================================
# Pytest configuration for FIFA2026 tests
#
# Shared fixtures and configuration for all tests
# =============================================================================

import pytest
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@pytest.fixture(scope="session")
def project_root_path():
    """Return project root directory path."""
    return project_root


@pytest.fixture(scope="session")
def models_dir(project_root_path):
    """Return models directory path."""
    return os.path.join(project_root_path, "models")


@pytest.fixture(scope="session")
def features_dir(project_root_path):
    """Return features directory path."""
    return os.path.join(project_root_path, "data", "features")


@pytest.fixture(scope="session")
def models_exist(models_dir):
    """Check if trained models exist."""
    return os.path.exists(os.path.join(models_dir, "best_model.json"))


@pytest.fixture(scope="session")
def features_exist(features_dir):
    """Check if features file exists."""
    return os.path.exists(os.path.join(features_dir, "match_features.csv"))
