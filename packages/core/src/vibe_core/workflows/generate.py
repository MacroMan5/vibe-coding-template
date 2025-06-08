"""Generation workflow for VIBE Core - merge and generate."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from ..models import ProjectConfig
from ..utils import PromptMerger, create_merger
from ..generators.architect import CodeArchitect
from ..models import GenerationResponse, DryRunResponse

logger = logging.getLogger(__name__)


class WorkflowOptions(BaseModel):
    """Options for generation workflow."""
    
    config_file: Optional[Path] = Field(None, description="Path to configuration file")
    config_json: Optional[str] = Field(None, description="Configuration as JSON string")
    dry_run: bool = Field(default=False, description="Run in dry-run mode")
    json_output: bool = Field(default=False, description="Return JSON output")
    verbose: bool = Field(default=False, description="Enable verbose logging")
    model: str = Field(default="claude-3-5-sonnet-20241022", description="Claude model to use")
    output_dir: Optional[Path] = Field(None, description="Output directory")
    templates_dir: Optional[Path] = Field(None, description="Templates directory")


class WorkflowResult(BaseModel):
    """Result of generation workflow."""
    
    success: bool = Field(..., description="Whether workflow succeeded")
    config_used: Dict[str, Any] = Field(..., description="Configuration used")
    merge_result: Optional[Dict[str, Any]] = Field(None, description="Prompt merge result")
    generation_result: Optional[GenerationResponse] = Field(None, description="Code generation result") 
    errors: List[str] = Field(default_factory=list, description="Workflow errors")
    output_data: Optional[Any] = Field(None, description="Output data for JSON mode")


class GenerationWorkflow:
    """Complete generation workflow: merge prompts then generate code."""
    
    def __init__(self, base_dir: Optional[Path] = None):
        """Initialize generation workflow.
        
        Args:
            base_dir: Base directory for operations
        """
        self.base_dir = base_dir or Path.cwd()
        
        # Use the provided base_dir for templates (should contain templates/ directory)
        self.merger = create_merger(base_dir=self.base_dir)
        self.architect = CodeArchitect()
    
    def run(self, options: WorkflowOptions) -> WorkflowResult:
        """Run complete generation workflow.
        
        Args:
            options: Workflow options
            
        Returns:
            WorkflowResult with workflow outcome
        """
        if options.verbose:
            logging.getLogger().setLevel(logging.DEBUG)
        
        logger.info("Starting VIBE generation workflow")
        
        try:
            # Load and validate configuration
            config = self._load_config(options)
            logger.info(f"Loaded configuration for project: {config.project_name}")
            
            # Setup directories
            output_dir = options.output_dir or (self.base_dir / "build")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Save configuration for reference
            config_path = output_dir / "project_config.json"
            config_path.write_text(json.dumps(config.to_dict(), indent=2))
            
            # Merge prompts
            merge_result = self._merge_prompts(config, options)
            
            if not merge_result["success"]:
                return WorkflowResult(
                    success=False,
                    config_used=config.to_dict(),
                    merge_result=merge_result,
                    errors=merge_result.get("errors", ["Prompt merge failed"])
                )
            
            # Get merged prompt content
            merged_prompt_path = output_dir / "merged_prompt.md"
            if not merged_prompt_path.exists():
                return WorkflowResult(
                    success=False,
                    config_used=config.to_dict(),
                    merge_result=merge_result,
                    errors=["Merged prompt file not found"]
                )
            
            merged_prompt = merged_prompt_path.read_text(encoding="utf-8")
            
            # Load system prompt (needed for both dry run and full generation)
            system_prompt_path = options.templates_dir or (self.base_dir / "templates")
            system_prompt_path = system_prompt_path / "system_prompt_architect.md"
            
            if not system_prompt_path.exists():
                # Try legacy location
                system_prompt_path = self.base_dir / "VIBE-CODING-INIT" / "templates" / "system_prompt_architect.md"
            
            if system_prompt_path.exists():
                system_prompt = system_prompt_path.read_text(encoding="utf-8")
            else:
                system_prompt = "You are an expert software architect. Generate a complete project structure based on the provided configuration and requirements."
            
            # Generate code architecture
            if options.dry_run:
                dry_run_result = self.architect.generate_dry_run(
                    config=config,
                    prompt_text=merged_prompt,
                    system_prompt=system_prompt
                )
                
                # Convert DryRunResponse to GenerationResponse for consistency
                generation_result = GenerationResponse(
                    success=True,
                    project_path="",
                    archive_path=None,
                    files_created=[f["path"] for f in dry_run_result.files],
                    logs=[f"Dry run completed with {len(dry_run_result.files)} files"],
                    errors=[]
                )
                
                # Store dry run data for JSON output
                dry_run_data = {
                    "files": dry_run_result.files,
                    "estimated_time": dry_run_result.estimated_time,
                    "conflicts": dry_run_result.conflicts,
                }
            else:
                generation_result = self.architect.generate_project(
                    config=config,
                    prompt_text=merged_prompt,
                    system_prompt=system_prompt,
                    output_dir=output_dir,
                    create_archive=True
                )
                dry_run_data = None
            
            # Prepare final result
            result = WorkflowResult(
                success=generation_result.success,
                config_used=config.to_dict(),
                merge_result=merge_result,
                generation_result=generation_result,
                errors=generation_result.errors
            )
            
            # Handle dry run with JSON output
            if options.dry_run and options.json_output and dry_run_data:
                result.output_data = dry_run_data
            
            logger.info(f"Workflow completed. Success: {result.success}")
            return result
            
        except Exception as e:
            logger.error(f"Workflow failed: {e}")
            return WorkflowResult(
                success=False,
                config_used={},
                errors=[f"Workflow error: {str(e)}"]
            )
    
    def _load_config(self, options: WorkflowOptions) -> ProjectConfig:
        """Load project configuration from options.
        
        Args:
            options: Workflow options
            
        Returns:
            ProjectConfig instance
            
        Raises:
            ValueError: If no configuration provided or invalid
        """
        if not options.config_file and not options.config_json:
            raise ValueError("Either config_file or config_json must be provided")
        
        if options.config_file:
            if not options.config_file.exists():
                raise ValueError(f"Configuration file not found: {options.config_file}")
            
            try:
                config_data = json.loads(options.config_file.read_text())
            except Exception as e:
                raise ValueError(f"Failed to parse configuration file: {e}")
        elif options.config_json:
            try:
                config_data = json.loads(options.config_json)
            except Exception as e:
                raise ValueError(f"Failed to parse configuration JSON: {e}")
        else:
            raise ValueError("Either config_file or config_json must be provided")
        
        return ProjectConfig.from_dict(config_data)
    
    def _merge_prompts(self, config: ProjectConfig, options: WorkflowOptions) -> Dict[str, Any]:
        """Merge prompts using configuration.
        
        Args:
            config: Project configuration
            options: Workflow options
            
        Returns:
            Dictionary with merge results
        """
        try:
            # Setup output directory
            output_dir = options.output_dir or (self.base_dir / "build")
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Create config dictionary from project config
            config_dict = config.to_dict()
            
            # Generate the merged prompt using the real merger
            merged_prompt_path = self.merger.merge_from_config(config_dict)
            
            # Copy the merged prompt to the expected output directory if different
            expected_path = output_dir / "merged_prompt.md"
            if merged_prompt_path != expected_path:
                import shutil
                shutil.copy2(merged_prompt_path, expected_path)
                logger.info(f"Copied merged prompt from {merged_prompt_path} to {expected_path}")
            
            # Return success result
            return {
                "success": True,
                "templates_used": ["master_init_template"],
                "output_file": str(expected_path),
                "variables_replaced": len(config_dict)
            }
            
        except Exception as e:
            logger.error(f"Prompt merge failed: {e}")
            return {
                "success": False,
                "errors": [f"Merge error: {str(e)}"]
            }
    
    def run_from_cli_args(
        self,
        config_path: Optional[Path] = None,
        config_json: Optional[str] = None,
        dry_run: bool = False,
        json_output: bool = False,
        verbose: bool = False,
        model: str = "claude-3-5-sonnet-20241022"
    ) -> WorkflowResult:
        """Run workflow from CLI arguments - convenience method.
        
        Args:
            config_path: Path to configuration file
            config_json: Configuration as JSON string
            dry_run: Run in dry-run mode
            json_output: Return JSON output
            verbose: Enable verbose logging
            model: Claude model to use
            
        Returns:
            WorkflowResult
        """
        options = WorkflowOptions(
            config_file=config_path,
            config_json=config_json,
            dry_run=dry_run,
            json_output=json_output,
            verbose=verbose,
            model=model
        )
        
        return self.run(options)


def merge_and_run(
    config_path: Optional[Path] = None,
    config_json: Optional[str] = None,
    dry_run: bool = False,
    json_output: bool = False,
    verbose: bool = False
) -> WorkflowResult:
    """Legacy function for backward compatibility.
    
    Args:
        config_path: Path to configuration file
        config_json: Configuration JSON string
        dry_run: Run in dry-run mode
        json_output: Return JSON output
        verbose: Enable verbose logging
        
    Returns:
        WorkflowResult
    """
    workflow = GenerationWorkflow()
    return workflow.run_from_cli_args(
        config_path=config_path,
        config_json=config_json,
        dry_run=dry_run,
        json_output=json_output,
        verbose=verbose
    )
