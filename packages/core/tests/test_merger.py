"""Tests for the prompt merger module."""

import pytest
import tempfile
from pathlib import Path

from vibe_core.generators.merger import PromptMerger, PromptMetadata, PromptTemplate


@pytest.fixture
def temp_prompt_dir():
    """Create a temporary directory with test prompt files."""
    with tempfile.TemporaryDirectory() as temp_dir:
        prompt_dir = Path(temp_dir) / "prompts"
        prompt_dir.mkdir()
        
        # Create test prompt files
        (prompt_dir / "base.md").write_text("""---
priority: 10
---
# Base Prompt

This is the base prompt for {{project.name}}.
""")
        
        (prompt_dir / "fastapi.md").write_text("""---
stack: ["fastapi", "python"]
priority: 5
---
# FastAPI Specific

Configure FastAPI for {{backend.framework}}.
""")
        
        (prompt_dir / "auth.md").write_text("""---
auth_required: true
priority: 3
---
# Authentication

Set up {{auth.type}} authentication.
""")
        
        yield prompt_dir


def test_prompt_merger_initialization(temp_prompt_dir):
    """Test PromptMerger initialization."""
    merger = PromptMerger(temp_prompt_dir)
    
    assert merger.prompt_dir == temp_prompt_dir
    assert len(merger.templates) == 3  # base.md, fastapi.md, auth.md


def test_template_selection_all(temp_prompt_dir):
    """Test selecting all templates when conditions are met."""
    merger = PromptMerger(temp_prompt_dir)
    
    config = {
        "project": {"name": "test-project"},
        "backend": {"stack": "fastapi", "framework": "FastAPI"},
        "auth": {"type": "jwt"}
    }
    
    selected = merger.select_templates(config)
    
    # Should select all templates since conditions are met
    assert len(selected) == 3
    
    # Check priority ordering (higher priority first)
    assert selected[0].metadata.priority == 10  # base.md
    assert selected[1].metadata.priority == 5   # fastapi.md
    assert selected[2].metadata.priority == 3   # auth.md


def test_template_selection_filtered(temp_prompt_dir):
    """Test template selection with filtering."""
    merger = PromptMerger(temp_prompt_dir)
    
    config = {
        "project": {"name": "test-project"},
        "backend": {"stack": "django"},  # Different stack
        "auth": {"type": "none"}  # No auth
    }
    
    selected = merger.select_templates(config)
    
    # Should only select base.md (no stack requirement, no auth requirement)
    assert len(selected) == 1
    assert selected[0].path.name == "base.md"


def test_variable_replacement(temp_prompt_dir):
    """Test variable replacement in templates."""
    merger = PromptMerger(temp_prompt_dir)
    
    content = "Project: {{project.name}}, Framework: {{backend.framework}}"
    config = {
        "project": {"name": "my-app"},
        "backend": {"framework": "FastAPI"}
    }
    
    result, variables = merger.replace_variables(content, config)
    
    assert result == "Project: my-app, Framework: FastAPI"
    assert variables == {
        "project.name": "my-app",
        "backend.framework": "FastAPI"
    }


def test_merge_prompts(temp_prompt_dir):
    """Test full prompt merging process."""
    merger = PromptMerger(temp_prompt_dir)
    
    config = {
        "project": {"name": "test-app"},
        "backend": {"stack": "fastapi", "framework": "FastAPI"},
        "auth": {"type": "jwt"}
    }
    
    result = merger.merge_prompts(config)
    
    assert "test-app" in result.content  # Variable replaced
    assert "FastAPI" in result.content
    assert "jwt" in result.content
    assert len(result.templates_used) == 3
    assert "project.name" in result.variables_replaced


def test_frontmatter_parsing(temp_prompt_dir):
    """Test YAML frontmatter parsing."""
    merger = PromptMerger(temp_prompt_dir)
    
    content = """---
test_key: test_value
number: 42
---
Content here"""
    
    metadata, template_content = merger._parse_frontmatter(content)
    
    assert metadata["test_key"] == "test_value"
    assert metadata["number"] == 42
    assert template_content.strip() == "Content here"


def test_config_flattening():
    """Test configuration flattening."""
    merger = PromptMerger("dummy")
    
    config = {
        "level1": {
            "level2": {
                "key": "value"
            },
            "array": ["item1", "item2"]
        },
        "simple": "test"
    }
    
    flat = merger._flatten_config(config)
    
    assert flat["level1.level2.key"] == "value"
    assert flat["level1.array.0"] == "item1"
    assert flat["level1.array.1"] == "item2"
    assert flat["simple"] == "test"


def test_plan_generation():
    """Test project plan generation."""
    merger = PromptMerger("dummy")
    
    config = {
        "backend": {"stack": "FastAPI"},
        "auth": {"type": "JWT"},
        "database": {"type": "PostgreSQL"}
    }
    
    plan = merger.generate_plan_section(config)
    
    assert "FastAPI" in plan
    assert "JWT" in plan
    assert "PostgreSQL" in plan
    assert "1." in plan  # Should be numbered steps


def test_add_template_from_string():
    """Test adding template from string content."""
    merger = PromptMerger("dummy")
    
    content = "Test template with {{variable}}"
    metadata = {"priority": 1}
    
    merger.add_template_from_string("test.md", content, metadata)
    
    assert len(merger.templates) == 1
    template = merger.templates[0]
    assert template.content == content
    assert template.metadata.priority == 1
    assert "variable" in template.variables


def test_get_template_info():
    """Test getting template information."""
    merger = PromptMerger("dummy")
    
    merger.add_template_from_string(
        "test.md", 
        "Content with {{var}}", 
        {"priority": 5}
    )
    
    info = merger.get_template_info()
    
    assert len(info) == 1
    assert info[0]["name"] == "test.md"
    assert info[0]["variables"] == ["var"]
    assert info[0]["metadata"]["priority"] == 5


def test_empty_prompt_dir():
    """Test handling of empty or non-existent prompt directory."""
    with tempfile.TemporaryDirectory() as temp_dir:
        empty_dir = Path(temp_dir) / "empty"
        
        merger = PromptMerger(empty_dir)
        
        assert len(merger.templates) == 0
        
        result = merger.merge_prompts({})
        assert result.content == ""
        assert len(result.templates_used) == 0
