"""
Pytest configuration and fixtures for the FastAPI application tests.
"""

import pytest
from copy import deepcopy
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app."""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """
    Reset activities database to initial state for each test.
    This fixture ensures test isolation by resetting the in-memory database.
    """
    # Store original activities
    original_activities = deepcopy(activities)
    
    yield
    
    # Reset activities after test
    activities.clear()
    activities.update(deepcopy(original_activities))
