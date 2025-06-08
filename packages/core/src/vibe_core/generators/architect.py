"""Code architecture generator using Claude AI for VIBE Core."""

from __future__ import annotations

import json
import logging
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional
from zipfile import ZipFile

import anthropic

from ..models import ProjectConfig, DryRunResponse, GenerationResponse
from ..parsers.claude import ClaudeResponseParser, FileObject
from ..utils.context import ContextManager
from ..utils.env import load_api_keys
from ..utils.memory import JsonVectorMemory


class CodeArchitect:
    """AI-powered code architecture generator using Claude.
    
    This class handles the generation of project structures and code
    using Claude AI models based on project configuration.
    """

    def __init__(
        self,
        model: str = "claude-3-5-sonnet-20241022",
        memory_path: Optional[Path] = None,
    ) -> None:
        """Initialize the CodeArchitect.
        
        Args:
            model: Claude model to use for generation
            memory_path: Path to memory store file
        """
        self.model = model
        self.logger = logging.getLogger(__name__)
        
        # Load API keys
        load_api_keys()
        
        # Initialize Claude client
        self.client = anthropic.Anthropic()
        
        # Initialize parser
        self.parser = ClaudeResponseParser()
        
        # Initialize memory if path provided
        self.memory = JsonVectorMemory(memory_path) if memory_path else None
        self.context_manager = (
            ContextManager(self.memory) if self.memory else None
        )

    def load_config(self, config_path: Path) -> Dict[str, Any]:
        """Load project configuration from JSON file.
        
        Args:
            config_path: Path to configuration file
            
        Returns:
            Configuration dictionary
        """
        with open(config_path) as f:
            return json.load(f)

    def read_template(self, template_path: Path) -> str:
        """Read template file content.
        
        Args:
            template_path: Path to template file
            
        Returns:
            Template content as string
        """
        return template_path.read_text()

    def call_claude(
        self, system_prompt: str, user_prompt: str, output_file: Optional[Path] = None
    ) -> str:
        """Call Claude API with streaming response.
        
        Args:
            system_prompt: System prompt for Claude
            user_prompt: User prompt with project details
            output_file: Optional file to stream response to
            
        Returns:
            Complete response text
        
        Raises:
            anthropic.APIError: If API call fails
        """
        response_text = ""
        
        try:
            with self.client.messages.stream(
                model=self.model,
                max_tokens=4096,
                system=system_prompt,
                messages=[{"role": "user", "content": user_prompt}],
            ) as stream:
                if output_file:
                    with output_file.open("w") as f:
                        for chunk in stream.text_stream:
                            print(chunk, end="", flush=True)
                            f.write(chunk)
                            response_text += chunk
                else:
                    for chunk in stream.text_stream:
                        response_text += chunk
                        
            return response_text
            
        except anthropic.APIError as exc:
            self.logger.error("Anthropic API request failed: %s", exc)
            raise
        except Exception as exc:
            self.logger.error("Unexpected error calling Anthropic: %s", exc)
            raise

    def write_files(
        self, files: List[FileObject], output_dir: Path, dry_run: bool = False
    ) -> None:
        """Write generated files to output directory.
        
        Args:
            files: List of FileObject instances to write
            output_dir: Directory to write files to
            dry_run: If True, only preview without writing
        """
        for file_obj in files:
            file_obj.write_to(output_dir, dry_run)

    def create_archive(self, project_dir: Path, archive_path: Path) -> None:
        """Create ZIP archive from project directory.
        
        Args:
            project_dir: Source directory to archive
            archive_path: Path for the created archive
        """
        with ZipFile(archive_path, "w") as zf:
            for path in project_dir.rglob("*"):
                if path.is_file():
                    zf.write(path, path.relative_to(project_dir))
        self.logger.info("Archive created at %s", archive_path)

    def verify_files(
        self, files: List[FileObject], output_dir: Path
    ) -> bool:
        """Verify that all generated files exist.
        
        Args:
            files: List of FileObject instances to verify
            output_dir: Directory where files should exist
            
        Returns:
            True if all files exist, False otherwise
        """
        missing = []
        for file_obj in files:
            file_path = output_dir / file_obj.path
            if not file_path.exists():
                missing.append(file_obj.path)
                
        if missing:
            self.logger.error("Missing files: %s", ", ".join(missing))
            return False
            
        self.logger.info("All files verified")
        return True

    def generate_dry_run(
        self,
        config: ProjectConfig,
        prompt_text: str,
        system_prompt: str,
    ) -> DryRunResponse:
        """Perform a dry run generation without writing files.
        
        Args:
            config: Project configuration
            prompt_text: Merged prompt text
            system_prompt: System prompt for Claude
            
        Returns:
            DryRunResponse with preview information
        """
        # Hydrate memory if available
        if self.context_manager:
            self.context_manager.hydrate_from_text(
                prompt_text, context="merged_prompt"
            )

        # Combine prompts
        combined_prompt = (
            f"{prompt_text}\n\nConfiguration:\n{config.model_dump_json(indent=2)}"
        )

        # Call Claude
        response_text = self.call_claude(system_prompt, combined_prompt)
        
        # Parse response
        files = self.parser.parse(response_text)
        
        # Create preview data
        preview_files = [
            {"path": f.path, "content": f.content[:100] + "..." if len(f.content) > 100 else f.content}
            for f in files
        ]
        
        # Check for conflicts
        file_counts = Counter(f.path for f in files)
        conflicts = [path for path, count in file_counts.items() if count > 1]
        
        return DryRunResponse(
            files=preview_files,
            estimated_time=round(len(files) * 0.1, 2),
            conflicts=conflicts,
        )

    def generate_project(
        self,
        config: ProjectConfig,
        prompt_text: str,
        system_prompt: str,
        output_dir: Path,
        create_archive: bool = True,
    ) -> GenerationResponse:
        """Generate a complete project structure.
        
        Args:
            config: Project configuration
            prompt_text: Merged prompt text
            system_prompt: System prompt for Claude
            output_dir: Directory to generate project in
            create_archive: Whether to create a ZIP archive
            
        Returns:
            GenerationResponse with generation results
        """
        logs = []
        errors = []
        
        try:
            # Hydrate memory if available
            if self.context_manager:
                self.context_manager.hydrate_from_text(
                    prompt_text, context="merged_prompt"
                )
                logs.append("Memory hydrated with prompt context")

            # Prepare project directory
            project_dir = output_dir / config.project_name
            project_dir.mkdir(parents=True, exist_ok=True)
            logs.append(f"Created project directory: {project_dir}")

            # Combine prompts
            combined_prompt = (
                f"{prompt_text}\n\nConfiguration:\n{config.model_dump_json(indent=2)}"
            )

            # Call Claude
            response_file = project_dir / "claude_response.txt"
            self.logger.info("Generating with Claude model %s", self.model)
            response_text = self.call_claude(
                system_prompt, combined_prompt, response_file
            )
            logs.append(f"Claude response saved to {response_file}")

            # Parse and write files
            files = self.parser.parse(response_text)
            self.write_files(files, project_dir)
            
            file_paths = [f.path for f in files]
            logs.append(f"Generated {len(files)} files")

            # Create archive if requested
            archive_path = None
            if create_archive:
                archive_path = project_dir.with_suffix(".zip")
                self.create_archive(project_dir, archive_path)
                logs.append(f"Archive created: {archive_path}")

            # Verify files
            if self.verify_files(files, project_dir):
                logs.append("File verification successful")
            else:
                errors.append("Some files failed verification")

            return GenerationResponse(
                success=True,
                project_path=str(project_dir),
                archive_path=str(archive_path) if archive_path else None,
                files_created=file_paths,
                logs=logs,
                errors=errors,
            )

        except Exception as exc:
            error_msg = f"Generation failed: {exc}"
            self.logger.error(error_msg)
            errors.append(error_msg)
            
            return GenerationResponse(
                success=False,
                project_path=None,
                archive_path=None,
                files_created=[],
                logs=logs,
                errors=errors,
            )
