"""Tests for the memory module."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from vibe_core.utils.memory import JsonVectorMemory, MemoryEntry, MemorySearchResult


@pytest.fixture
def temp_memory_file():
    """Create a temporary file for memory storage."""
    with tempfile.NamedTemporaryFile(suffix='.json', delete=False) as f:
        temp_path = Path(f.name)
    yield temp_path
    if temp_path.exists():
        temp_path.unlink()


@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    mock_client = Mock()
    mock_response = Mock()
    mock_response.data = [Mock(embedding=[0.1, 0.2, 0.3, 0.4, 0.5])]
    mock_client.embeddings.create.return_value = mock_response
    return mock_client


def test_memory_initialization(temp_memory_file, mock_openai_client):
    """Test memory initialization."""
    memory = JsonVectorMemory(temp_memory_file, client=mock_openai_client)
    
    assert memory.path == temp_memory_file
    assert memory.model == "text-embedding-3-small"
    assert len(memory.entries) == 0


def test_add_memory_entry(temp_memory_file, mock_openai_client):
    """Test adding a memory entry."""
    memory = JsonVectorMemory(temp_memory_file, client=mock_openai_client)
    
    memory.add("Test content", author="test", context="unit_test")
    
    assert len(memory.entries) == 1
    entry = memory.entries[0]
    assert entry.text == "Test content"
    assert entry.author == "test"
    assert entry.context == "unit_test"
    assert len(entry.embedding) == 5  # Mock embedding size


def test_search_memory(temp_memory_file, mock_openai_client):
    """Test memory search functionality."""
    memory = JsonVectorMemory(temp_memory_file, client=mock_openai_client)
    
    # Add multiple entries
    memory.add("Python programming", author="developer", context="coding")
    memory.add("JavaScript frameworks", author="developer", context="coding")
    memory.add("Database design", author="architect", context="design")
    
    # Search for entries
    results = memory.search("programming", top_k=2)
    
    assert len(results) <= 2
    assert all(isinstance(result, MemorySearchResult) for result in results)
    assert all(0 <= result.score <= 1 for result in results)


def test_memory_persistence(temp_memory_file, mock_openai_client):
    """Test memory persistence across instances."""
    # Create first memory instance and add data
    memory1 = JsonVectorMemory(temp_memory_file, client=mock_openai_client)
    memory1.add("Persistent data", author="test")
    
    # Create second memory instance and verify data is loaded
    memory2 = JsonVectorMemory(temp_memory_file, client=mock_openai_client)
    assert len(memory2.entries) == 1
    assert memory2.entries[0].text == "Persistent data"


def test_memory_clear(temp_memory_file, mock_openai_client):
    """Test clearing memory."""
    memory = JsonVectorMemory(temp_memory_file, client=mock_openai_client)
    
    memory.add("Data to clear")
    assert len(memory.entries) == 1
    
    memory.clear()
    assert len(memory.entries) == 0


def test_memory_filtering(temp_memory_file, mock_openai_client):
    """Test memory filtering methods."""
    memory = JsonVectorMemory(temp_memory_file, client=mock_openai_client)
    
    memory.add("Entry 1", author="alice", context="project_a")
    memory.add("Entry 2", author="bob", context="project_b")
    memory.add("Entry 3", author="alice", context="project_a")
    
    # Test filter by author
    alice_entries = memory.filter_by_author("alice")
    assert len(alice_entries) == 2
    
    # Test filter by context
    project_a_entries = memory.filter_by_context("project_a")
    assert len(project_a_entries) == 2


def test_empty_text_handling(temp_memory_file, mock_openai_client):
    """Test handling of empty text."""
    memory = JsonVectorMemory(temp_memory_file, client=mock_openai_client)
    
    # Should not add empty text
    memory.add("")
    memory.add("   ")  # Just whitespace
    
    assert len(memory.entries) == 0


def test_cosine_similarity():
    """Test cosine similarity calculation."""
    memory = JsonVectorMemory("dummy", client=Mock())
    
    # Test identical vectors
    vec1 = [1, 0, 0]
    vec2 = [1, 0, 0]
    similarity = memory._cosine_similarity(vec1, vec2)
    assert similarity == 1.0
    
    # Test orthogonal vectors
    vec1 = [1, 0, 0]
    vec2 = [0, 1, 0]
    similarity = memory._cosine_similarity(vec1, vec2)
    assert similarity == 0.0
    
    # Test dimension mismatch
    vec1 = [1, 0]
    vec2 = [1, 0, 0]
    similarity = memory._cosine_similarity(vec1, vec2)
    assert similarity == 0.0


def test_get_recent_entries(temp_memory_file, mock_openai_client):
    """Test getting recent entries."""
    memory = JsonVectorMemory(temp_memory_file, client=mock_openai_client)
    
    # Add entries (they will have timestamps)
    memory.add("Old entry")
    memory.add("Newer entry")
    memory.add("Newest entry")
    
    recent = memory.get_recent(limit=2)
    assert len(recent) == 2
    # Note: In a real test, you'd want to control timestamps to verify order
