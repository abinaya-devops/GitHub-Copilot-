"""
Pytest fixtures for FastAPI app testing.
"""

import pytest
import copy
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """
    Provide a TestClient for the FastAPI app.
    """
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """
    Reset activities to initial state before each test.
    This fixture ensures test isolation by restoring the in-memory database.
    """
    # Store initial state
    initial_state = copy.deepcopy(activities)
    
    yield
    
    # Restore initial state after test
    activities.clear()
    activities.update(initial_state)
