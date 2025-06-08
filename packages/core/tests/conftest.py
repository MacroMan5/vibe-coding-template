"""Test configuration for VIBE Core package."""

import pytest
from pathlib import Path
import tempfile
import shutil
from unittest.mock import Mock

from vibe_core.models import ProjectConfig


@pytest.fixture
def sample_config():
    """Sample project configuration for testing."""
    return ProjectConfig(
        project_name="test-project",
        project_description="A test project",
        backend_framework="fastapi",
        frontend_framework="react",
        database_type="postgresql",
        cloud_provider="aws",
    )


@pytest.fixture
def temp_dir():
    """Temporary directory for test files."""
    temp_path = Path(tempfile.mkdtemp())
    yield temp_path
    shutil.rmtree(temp_path)


@pytest.fixture
def mock_anthropic_client():
    """Mock Anthropic client for testing."""
    mock_client = Mock()
    mock_stream = Mock()
    mock_stream.text_stream = ["Hello", " world", "!"]
    mock_client.messages.stream.return_value.__enter__.return_value = mock_stream
    return mock_client


@pytest.fixture
def sample_claude_response():
    """Sample Claude response text for testing."""
    return """
Fichier: README.md
# Test Project

This is a test project.

Fichier: main.py
def main():
    print("Hello, world!")

if __name__ == "__main__":
    main()

Fichier: requirements.txt
fastapi==0.104.0
uvicorn==0.24.0
"""


@pytest.fixture
def sample_prompt_text():
    """Sample prompt text for testing."""
    return """
Create a web application with the following requirements:
- FastAPI backend
- React frontend  
- PostgreSQL database
- AWS deployment
"""


@pytest.fixture
def sample_system_prompt():
    """Sample system prompt for testing."""
    return """
You are an expert software architect. Generate a complete project structure
based on the provided configuration and requirements.
"""
