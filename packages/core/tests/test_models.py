"""Tests for VIBE Core models."""

import pytest
from pydantic import ValidationError

from vibe_core.models import ProjectConfig, GenerationResponse, DryRunResponse


class TestProjectConfig:
    """Test ProjectConfig model."""

    def test_minimal_config(self):
        """Test creating config with minimal required fields."""
        config = ProjectConfig(project_name="test-project")
        assert config.project_name == "test-project"
        assert config.project_description is None
        assert config.features == {}
        assert config.requirements == []

    def test_full_config(self, sample_config):
        """Test creating config with all fields."""
        assert sample_config.project_name == "test-project"
        assert sample_config.backend_framework == "fastapi"
        assert sample_config.frontend_framework == "react"
        assert sample_config.database_type == "postgresql"
        assert sample_config.cloud_provider == "aws"

    def test_empty_project_name_fails(self):
        """Test that empty project name raises validation error."""
        with pytest.raises(ValidationError):
            ProjectConfig(project_name="")

    def test_extra_fields_allowed(self):
        """Test that extra fields are allowed due to Config.extra = 'allow'."""
        config = ProjectConfig(
            project_name="test",
            custom_field="custom_value",
            another_field=123
        )
        assert config.project_name == "test"
        # Extra fields should be accessible
        assert hasattr(config, "custom_field")

    def test_team_size_validation(self):
        """Test team size must be >= 1."""
        config = ProjectConfig(project_name="test", team_size=5)
        assert config.team_size == 5

        with pytest.raises(ValidationError):
            ProjectConfig(project_name="test", team_size=0)

    def test_serialization(self, sample_config):
        """Test model serialization."""
        json_data = sample_config.model_dump_json()
        assert "test-project" in json_data
        assert "fastapi" in json_data

        # Test deserialization
        config_dict = sample_config.model_dump()
        new_config = ProjectConfig(**config_dict)
        assert new_config.project_name == sample_config.project_name


class TestGenerationResponse:
    """Test GenerationResponse model."""

    def test_successful_response(self):
        """Test successful generation response."""
        response = GenerationResponse(
            success=True,
            project_path="/path/to/project",
            archive_path="/path/to/archive.zip",
            files_created=["README.md", "main.py"],
            logs=["Project generated successfully"],
            errors=[]
        )
        
        assert response.success is True
        assert response.project_path == "/path/to/project"
        assert len(response.files_created) == 2
        assert len(response.logs) == 1
        assert len(response.errors) == 0

    def test_failed_response(self):
        """Test failed generation response."""
        response = GenerationResponse(
            success=False,
            errors=["API key not found", "Generation failed"]
        )
        
        assert response.success is False
        assert response.project_path is None
        assert len(response.errors) == 2
        assert len(response.files_created) == 0

    def test_default_values(self):
        """Test default values for optional fields."""
        response = GenerationResponse(success=True)
        
        assert response.project_path is None
        assert response.archive_path is None
        assert response.files_created == []
        assert response.logs == []
        assert response.errors == []


class TestDryRunResponse:
    """Test DryRunResponse model."""

    def test_dry_run_response(self):
        """Test dry run response creation."""
        files = [
            {"path": "README.md", "content": "# Test Project"},
            {"path": "main.py", "content": "def main(): pass"}
        ]
        
        response = DryRunResponse(
            files=files,
            estimated_time=1.5,
            conflicts=["duplicate.py"]
        )
        
        assert len(response.files) == 2
        assert response.estimated_time == 1.5
        assert response.conflicts == ["duplicate.py"]

    def test_default_values(self):
        """Test default values."""
        response = DryRunResponse()
        
        assert response.files == []
        assert response.estimated_time == 0.0
        assert response.conflicts == []
