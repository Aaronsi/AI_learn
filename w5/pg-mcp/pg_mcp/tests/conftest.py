"""Pytest configuration and fixtures"""

import pytest
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock

# Test fixtures will be added as needed

@pytest.fixture
def test_data_dir():
    """Test data directory"""
    return Path(__file__).parent / "data"
