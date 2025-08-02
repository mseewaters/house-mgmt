"""
Pytest configuration and fixtures for backend
"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'house_mgmt'))

import pytest
from fastapi.testclient import TestClient
from main import app

@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)