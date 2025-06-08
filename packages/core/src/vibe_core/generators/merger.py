"""Prompt merging and template processing for VIBE code generation.

This module provides functionality to merge prompt templates with configuration
data, enabling dynamic prompt generation for AI-powered code generation.
"""

from __future__ import annotations

import json
import logging
import re
import yaml
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from pydantic import BaseModel, Field, validator

logger = logging.getLogger(__name__)


class PromptMetadata(BaseModel):
    """Metadata for a prompt template."""
    
    stack: Optional[List[str]] = Field(None, description="Required technology stacks")
    auth_required: bool = Field(False, description="Whether authentication is required")
    database_required: bool = Field(False, description="Whether database is required")
    priority: int = Field(0, description="Prompt priority for ordering")
    conditions: Dict[str, Any] = Field(default_factory=dict, description="Conditional requirements")


class PromptTemplate(BaseModel):
    """A prompt template with metadata and content."""
    
    path: Path = Field(..., description="Path to the template file")
    metadata: PromptMetadata = Field(..., description="Template metadata")
    content: str = Field(..., description="Template content")
    variables: List[str] = Field(default_factory=list, description="Variables found in template")


class MergedPrompt(BaseModel):
    """Result of merging multiple prompt templates."""
    
    content: str = Field(..., description="Merged prompt content")
    templates_used: List[str] = Field(..., description="List of template files used")
    variables_replaced: Dict[str, str] = Field(..., description="Variables that were replaced")
    config_used: Dict[str, Any] = Field(..., description="Configuration used for merging")


class PromptMerger:
    """Merges prompt templates with configuration data.
    
    This class handles loading prompt templates, applying conditional logic,
    variable replacement, and generating the final merged prompt for AI models.
    
    Example:
        >>> merger = PromptMerger("prompts/")
        >>> config = {"backend": {"stack": "fastapi"}, "auth": {"type": "jwt"}}
        >>> result = merger.merge_prompts(config)
        >>> print(result.content)
    """

    # Pattern for variable substitution: {{variable.name}}
    VARIABLE_PATTERN = re.compile(r"{{\s*([\w\.]+)\s*}}")
    
    def __init__(self, prompt_dir: Union[str, Path]) -> None:
        """Initialize the prompt merger.
        
        Args:
            prompt_dir: Directory containing prompt template files
        """
        self.prompt_dir = Path(prompt_dir)
        self.templates: List[PromptTemplate] = []
        
        if not self.prompt_dir.exists():
            logger.warning(f"Prompt directory does not exist: {self.prompt_dir}")
        else:
            self._load_templates()

    def _load_templates(self) -> None:
        """Load all prompt templates from the prompt directory."""
        self.templates = []
        
        for template_path in sorted(self.prompt_dir.glob("*.md")):
            try:
                template = self._load_template(template_path)
                self.templates.append(template)
                logger.debug(f"Loaded template: {template_path.name}")
            except Exception as e:
                logger.error(f"Failed to load template {template_path}: {e}")
        
        logger.info(f"Loaded {len(self.templates)} prompt templates")

    def _load_template(self, template_path: Path) -> PromptTemplate:
        """Load a single prompt template file.
        
        Args:
            template_path: Path to the template file
            
        Returns:
            Loaded PromptTemplate instance
        """
        content = template_path.read_text(encoding='utf-8')
        metadata, template_content = self._parse_frontmatter(content)
        
        # Extract variables from template content
        variables = self._extract_variables(template_content)
        
        return PromptTemplate(
            path=template_path,
            metadata=PromptMetadata(**metadata),
            content=template_content,
            variables=variables
        )

    def _parse_frontmatter(self, content: str) -> tuple[Dict[str, Any], str]:
        """Parse YAML frontmatter from template content.
        
        Args:
            content: Template file content
            
        Returns:
            Tuple of (metadata dict, content without frontmatter)
        """
        if not content.startswith("---"):
            return {}, content
            
        parts = content.split("---", 2)
        if len(parts) < 3:
            return {}, content
            
        try:
            _, frontmatter, template_content = parts
            metadata = yaml.safe_load(frontmatter) or {}
            return metadata, template_content.lstrip()
        except yaml.YAMLError as e:
            logger.warning(f"Failed to parse frontmatter: {e}")
            return {}, content

    def _extract_variables(self, content: str) -> List[str]:
        """Extract variable names from template content.
        
        Args:
            content: Template content
            
        Returns:
            List of unique variable names found
        """
        variables = set()
        for match in self.VARIABLE_PATTERN.finditer(content):
            variables.add(match.group(1))
        return sorted(list(variables))

    def select_templates(self, config: Dict[str, Any]) -> List[PromptTemplate]:
        """Select templates based on configuration and metadata conditions.
        
        Args:
            config: Configuration data
            
        Returns:
            List of selected templates
        """
        selected = []
        
        for template in self.templates:
            if self._should_include_template(template.metadata, config):
                selected.append(template)
                logger.debug(f"Selected template: {template.path.name}")
            else:
                logger.debug(f"Skipped template: {template.path.name}")
        
        # Sort by priority
        selected.sort(key=lambda t: t.metadata.priority, reverse=True)
        return selected

    def _should_include_template(
        self, 
        metadata: PromptMetadata, 
        config: Dict[str, Any]
    ) -> bool:
        """Determine if a template should be included based on metadata and config.
        
        Args:
            metadata: Template metadata
            config: Configuration data
            
        Returns:
            True if template should be included
        """
        # Check stack requirements
        if metadata.stack:
            current_stack = self._get_config_value(
                config, "backend.stack", "backend_stack", default=""
            ).lower()
            
            allowed_stacks = [s.lower() for s in metadata.stack]
            if current_stack and current_stack not in allowed_stacks:
                return False
        
        # Check authentication requirements
        if metadata.auth_required:
            auth_type = self._get_config_value(
                config, "auth.type", "auth_type", default="none"
            ).lower()
            
            if auth_type == "none":
                return False
        
        # Check database requirements
        if metadata.database_required:
            db_type = self._get_config_value(
                config, "database.type", "database_type", default="none"
            ).lower()
            
            if db_type == "none":
                return False
        
        # Check custom conditions
        for condition_key, expected_value in metadata.conditions.items():
            actual_value = self._get_config_value(config, condition_key)
            if actual_value != expected_value:
                return False
        
        return True

    def _get_config_value(
        self, 
        config: Dict[str, Any], 
        *keys: str, 
        default: Any = ""
    ) -> Any:
        """Get configuration value with fallback keys.
        
        Args:
            config: Configuration dictionary
            *keys: Possible keys to check (in order)
            default: Default value if no keys found
            
        Returns:
            First found value or default
        """
        flat_config = self._flatten_config(config)
        
        for key in keys:
            if key in flat_config:
                return flat_config[key]
        
        return default

    def _flatten_config(self, data: Any, parent: str = "") -> Dict[str, Any]:
        """Flatten nested configuration using dot notation.
        
        Args:
            data: Data to flatten
            parent: Parent key path
            
        Returns:
            Flattened dictionary with dot notation keys
        """
        items = {}
        
        if isinstance(data, dict):
            for key, value in data.items():
                path = f"{parent}.{key}" if parent else key
                if isinstance(value, (dict, list)):
                    items.update(self._flatten_config(value, path))
                else:
                    items[path] = value
                    if not parent:  # Maintain top-level keys
                        items.setdefault(key, value)
        elif isinstance(data, Sequence) and not isinstance(data, (str, bytes)):
            for idx, value in enumerate(data):
                path = f"{parent}.{idx}" if parent else str(idx)
                if isinstance(value, (dict, list)):
                    items.update(self._flatten_config(value, path))
                else:
                    items[path] = value
        
        return items

    def replace_variables(
        self, 
        content: str, 
        config: Dict[str, Any]
    ) -> tuple[str, Dict[str, str]]:
        """Replace variables in content with configuration values.
        
        Args:
            content: Content with variables to replace
            config: Configuration data
            
        Returns:
            Tuple of (processed content, variables replaced dict)
        """
        flat_config = self._flatten_config(config)
        variables_replaced = {}
        
        def replace_func(match):
            variable_name = match.group(1)
            replacement = str(flat_config.get(variable_name, ""))
            variables_replaced[variable_name] = replacement
            return replacement
        
        processed_content = self.VARIABLE_PATTERN.sub(replace_func, content)
        return processed_content, variables_replaced

    def merge_prompts(self, config: Dict[str, Any]) -> MergedPrompt:
        """Merge selected prompt templates into a single prompt.
        
        Args:
            config: Configuration data for template selection and variables
            
        Returns:
            MergedPrompt with combined content and metadata
        """
        selected_templates = self.select_templates(config)
        
        if not selected_templates:
            logger.warning("No templates selected for merging")
            return MergedPrompt(
                content="",
                templates_used=[],
                variables_replaced={},
                config_used=config
            )
        
        sections = []
        all_variables_replaced = {}
        templates_used = []
        
        for template in selected_templates:
            processed_content, variables_replaced = self.replace_variables(
                template.content, config
            )
            
            sections.append(processed_content.strip())
            all_variables_replaced.update(variables_replaced)
            templates_used.append(str(template.path.name))
        
        merged_content = "\n\n".join(sections)
        
        logger.info(f"Merged {len(selected_templates)} templates into prompt")
        
        return MergedPrompt(
            content=merged_content,
            templates_used=templates_used,
            variables_replaced=all_variables_replaced,
            config_used=config
        )

    def generate_plan_section(self, config: Dict[str, Any]) -> str:
        """Generate a project plan section based on configuration.
        
        Args:
            config: Configuration data
            
        Returns:
            Generated plan section content
        """
        stack = self._get_config_value(config, "backend.stack", "backend_stack", default="FastAPI")
        auth_type = self._get_config_value(config, "auth.type", "auth_type", default="none")
        db_type = self._get_config_value(config, "database.type", "database_type", default="none")
        
        steps = [
            "Create the project structure and configuration",
            f"Set up {stack} backend framework",
        ]
        
        if db_type != "none":
            steps.append(f"Configure {db_type} database and ORM")
            steps.append("Create database models and migrations")
        
        steps.extend([
            "Generate REST API endpoints and handlers",
            "Add request/response validation",
        ])
        
        if auth_type != "none":
            steps.append(f"Integrate {auth_type} authentication")
            steps.append("Add authorization and permissions")
        
        steps.extend([
            "Add error handling and logging",
            "Create tests and documentation",
            "Set up CI/CD pipeline and deployment",
        ])
        
        return "\n".join(f"{i+1}. {step}" for i, step in enumerate(steps))

    def add_template_from_string(
        self, 
        name: str, 
        content: str, 
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """Add a template from string content (useful for testing).
        
        Args:
            name: Template name
            content: Template content
            metadata: Optional metadata dictionary
        """
        template_metadata = PromptMetadata(**(metadata or {}))
        variables = self._extract_variables(content)
        
        template = PromptTemplate(
            path=Path(name),
            metadata=template_metadata,
            content=content,
            variables=variables
        )
        
        self.templates.append(template)
        logger.debug(f"Added template from string: {name}")

    def get_template_info(self) -> List[Dict[str, Any]]:
        """Get information about all loaded templates.
        
        Returns:
            List of template information dictionaries
        """
        info = []
        for template in self.templates:
            info.append({
                "name": template.path.name,
                "path": str(template.path),
                "variables": template.variables,
                "metadata": template.metadata.dict(),
                "content_length": len(template.content)
            })
        return info


# Backward compatibility functions
def merge_prompts(prompt_paths: List[Path], config: Dict[str, Any]) -> str:
    """Legacy function for merging prompts.
    
    Args:
        prompt_paths: List of prompt file paths
        config: Configuration data
        
    Returns:
        Merged prompt content
    """
    if not prompt_paths:
        return ""
    
    # Create temporary merger with first prompt's directory
    prompt_dir = prompt_paths[0].parent
    merger = PromptMerger(prompt_dir)
    
    # Filter templates to only include the specified paths
    filtered_templates = [
        t for t in merger.templates 
        if t.path in prompt_paths
    ]
    merger.templates = filtered_templates
    
    result = merger.merge_prompts(config)
    return result.content


def create_prompt_merger(prompt_dir: Union[str, Path]) -> PromptMerger:
    """Create a PromptMerger instance.
    
    Args:
        prompt_dir: Directory containing prompt templates
        
    Returns:
        Configured PromptMerger instance
    """
    return PromptMerger(prompt_dir)
