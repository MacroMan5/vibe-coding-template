"""Integration tests for the VIBE Core CLI and workflow."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from vibe_core.cli.main import VibeCLI
from vibe_core.workflows.generate import GenerationWorkflow, WorkflowOptions
from vibe_core.models import ProjectConfig


class TestCLIIntegration:
    """Test CLI integration with workflows."""
    
    def test_cli_initialization(self):
        """Test that CLI can be initialized without errors."""
        cli = VibeCLI()
        assert cli is not None
        assert hasattr(cli, 'create_parser')
        assert hasattr(cli, 'handle_generate')
        assert hasattr(cli, 'handle_status')
    
    def test_cli_parser_creation(self):
        """Test that CLI parser is created correctly."""
        cli = VibeCLI()
        parser = cli.create_parser()
        
        # Test basic parser properties
        assert parser.prog == "vibe"
        assert "VIBE" in parser.description
        
        # Test that required subcommands exist
        subparsers = parser._subparsers._group_actions[0]
        subcommand_names = list(subparsers.choices.keys())
        assert "generate" in subcommand_names
        assert "status" in subcommand_names
    
    def test_status_command(self):
        """Test status command execution."""
        cli = VibeCLI()
        result = cli.handle_status(Mock())
        assert result == 0
    
    @patch('vibe_core.utils.env.load_api_keys')
    def test_workflow_initialization(self, mock_load_api_keys):
        """Test that workflow can be initialized."""
        # Mock API key loading to avoid environment requirements
        mock_load_api_keys.return_value = ("fake-openai-key", "fake-anthropic-key")
        
        workflow = GenerationWorkflow()
        assert workflow is not None
        assert hasattr(workflow, 'run')
        assert hasattr(workflow, '_load_config')
        assert hasattr(workflow, '_merge_prompts')


class TestWorkflowIntegration:
    """Test workflow integration components."""
    
    def test_project_config_creation(self):
        """Test ProjectConfig creation from dictionary."""
        config_data = {
            "project_name": "test-project",
            "project_description": "A test project",
            "architecture_style": "monolith",
            "cloud_provider": "aws"
        }
        
        config = ProjectConfig.from_dict(config_data)
        assert config.project_name == "test-project"
        assert config.project_description == "A test project"
        assert config.architecture_style == "monolith"
        assert config.cloud_provider == "aws"
    
    def test_project_config_serialization(self):
        """Test ProjectConfig to_dict conversion."""
        config = ProjectConfig(
            project_name="test-project",
            project_description="A test project"
        )
        
        config_dict = config.to_dict()
        assert isinstance(config_dict, dict)
        assert config_dict["project_name"] == "test-project"
        assert config_dict["project_description"] == "A test project"
    
    def test_workflow_options_creation(self):
        """Test WorkflowOptions creation."""
        config_data = {"project_name": "test"}
        options = WorkflowOptions(
            config_json=json.dumps(config_data),
            dry_run=True,
            verbose=True
        )
        
        assert options.config_json is not None
        assert options.dry_run is True
        assert options.verbose is True
        assert options.model == "claude-3-5-sonnet-20241022"  # Default value
    
    @patch('vibe_core.utils.env.load_api_keys')
    def test_workflow_config_loading(self, mock_load_api_keys):
        """Test workflow configuration loading."""
        mock_load_api_keys.return_value = ("fake-openai-key", "fake-anthropic-key")
        
        config_data = {
            "project_name": "test-project",
            "project_description": "Test description"
        }
        
        options = WorkflowOptions(
            config_json=json.dumps(config_data),
            dry_run=True
        )
        
        workflow = GenerationWorkflow()
        config = workflow._load_config(options)
        
        assert isinstance(config, ProjectConfig)
        assert config.project_name == "test-project"
        assert config.project_description == "Test description"
    
    @patch('vibe_core.utils.env.load_api_keys')
    def test_workflow_prompt_merging(self, mock_load_api_keys):
        """Test workflow prompt merging."""
        mock_load_api_keys.return_value = ("fake-openai-key", "fake-anthropic-key")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            config = ProjectConfig(
                project_name="test-project",
                project_description="Test description"
            )
            
            options = WorkflowOptions(
                config_json=json.dumps(config.to_dict()),
                output_dir=temp_path,
                dry_run=True
            )
            
            workflow = GenerationWorkflow()
            result = workflow._merge_prompts(config, options)
            
            assert result["success"] is True
            assert "output_file" in result
            
            # Check that merged prompt file was created
            merged_prompt_path = temp_path / "merged_prompt.md"
            assert merged_prompt_path.exists()
            
            content = merged_prompt_path.read_text()
            assert "test-project" in content
            assert "Test description" in content


class TestEndToEndIntegration:
    """End-to-end integration tests."""
    
    @patch('vibe_core.generators.architect.CodeArchitect.generate_dry_run')
    @patch('vibe_core.utils.env.load_api_keys')
    def test_full_dry_run_workflow(self, mock_load_api_keys, mock_generate_dry_run):
        """Test full workflow in dry run mode."""
        # Mock dependencies
        mock_load_api_keys.return_value = ("fake-openai-key", "fake-anthropic-key")
        
        # Mock dry run response
        from vibe_core.models import DryRunResponse
        mock_dry_run_response = DryRunResponse(
            files=[
                {"path": "src/main.py", "content": "# Main file"},
                {"path": "README.md", "content": "# Test Project"}
            ],
            estimated_time=30.0,
            conflicts=[]
        )
        mock_generate_dry_run.return_value = mock_dry_run_response
        
        # Test workflow
        with tempfile.TemporaryDirectory() as temp_dir:
            config_data = {
                "project_name": "test-project",
                "project_description": "Integration test project"
            }
            
            options = WorkflowOptions(
                config_json=json.dumps(config_data),
                dry_run=True,
                output_dir=Path(temp_dir)
            )
            
            workflow = GenerationWorkflow()
            result = workflow.run(options)
            
            assert result.success is True
            assert result.generation_result is not None
            assert len(result.generation_result.files_created) == 2
            assert "src/main.py" in result.generation_result.files_created
            assert "README.md" in result.generation_result.files_created


if __name__ == "__main__":
    # Simple test runner for manual execution
    import sys
    
    print("Running VIBE Core Integration Tests...")
    
    # Test CLI initialization
    try:
        cli = VibeCLI()
        print("✅ CLI initialization: PASSED")
    except Exception as e:
        print(f"❌ CLI initialization: FAILED - {e}")
        sys.exit(1)
    
    # Test parser creation
    try:
        parser = cli.create_parser()
        print("✅ Parser creation: PASSED")
    except Exception as e:
        print(f"❌ Parser creation: FAILED - {e}")
        sys.exit(1)
    
    # Test ProjectConfig
    try:
        config = ProjectConfig.from_dict({"project_name": "test"})
        config_dict = config.to_dict()
        print("✅ ProjectConfig serialization: PASSED")
    except Exception as e:
        print(f"❌ ProjectConfig serialization: FAILED - {e}")
        sys.exit(1)
    
    print("\n🎉 All basic integration tests passed!")
    print("Note: Full workflow tests require API keys or mocking.")
