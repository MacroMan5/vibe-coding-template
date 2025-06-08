"""Prompt validation for VIBE Core."""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional

from pydantic import BaseModel, Field

from ..models.project import ProjectConfig
from ..generators.merger import PromptMerger

logger = logging.getLogger(__name__)


class PromptValidationResult(BaseModel):
    """Result of prompt validation."""
    
    valid: bool = Field(..., description="Whether prompt is valid")
    issues: List[str] = Field(default_factory=list, description="Validation issues")
    suggestions: List[str] = Field(default_factory=list, description="Improvement suggestions")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Prompt metadata")
    quality_score: float = Field(0.0, ge=0.0, le=1.0, description="Quality score")


class PromptValidator:
    """Validates and improves merged prompts."""
    
    def __init__(self):
        """Initialize prompt validator."""
        self.merger = PromptMerger()
    
    def validate_prompt(self, prompt_path: Path) -> PromptValidationResult:
        """Validate a merged prompt file.
        
        Args:
            prompt_path: Path to prompt file to validate
            
        Returns:
            PromptValidationResult with validation details
        """
        if not prompt_path.exists():
            return PromptValidationResult(
                valid=False,
                issues=[f"Prompt file does not exist: {prompt_path}"],
                quality_score=0.0
            )
        
        try:
            content = prompt_path.read_text(encoding="utf-8")
        except Exception as e:
            return PromptValidationResult(
                valid=False,
                issues=[f"Could not read prompt file: {e}"],
                quality_score=0.0
            )
        
        issues = []
        suggestions = []
        metadata = {}
        
        # Check basic structure
        if not content.strip():
            issues.append("Prompt is empty")
        
        # Check for YAML frontmatter
        frontmatter = self.merger._parse_frontmatter(content)
        if frontmatter:
            metadata = frontmatter
        else:
            suggestions.append("Consider adding YAML frontmatter with metadata")
        
        # Check content length
        if len(content) < 100:
            issues.append("Prompt is very short, may not provide enough context")
        elif len(content) > 50000:
            suggestions.append("Prompt is very long, consider breaking into sections")
        
        # Check for common required sections
        required_sections = [
            "project",
            "requirements",
            "architecture",
            "implementation"
        ]
        
        content_lower = content.lower()
        missing_sections = []
        
        for section in required_sections:
            if section not in content_lower:
                missing_sections.append(section)
        
        if missing_sections:
            suggestions.append(f"Consider adding sections for: {', '.join(missing_sections)}")
        
        # Check for template variables
        if "{{" in content and "}}" in content:
            # Count variables
            import re
            variables = re.findall(r'\{\{([^}]+)\}\}', content)
            metadata["template_variables"] = list(set(variables))
            
            if len(variables) > 20:
                suggestions.append("Many template variables found, ensure they're all necessary")
        
        # Calculate quality score
        quality_score = self._calculate_quality_score(content, issues, suggestions)
        
        return PromptValidationResult(
            valid=len(issues) == 0,
            issues=issues,
            suggestions=suggestions,
            metadata=metadata,
            quality_score=quality_score
        )
    
    def validate_and_update_prompt(
        self, 
        prompt_path: Path, 
        config_path: Path
    ) -> PromptValidationResult:
        """Validate prompt and potentially update it based on config.
        
        Args:
            prompt_path: Path to merged prompt file
            config_path: Path to project configuration
            
        Returns:
            PromptValidationResult after validation and potential updates
        """
        # First validate current prompt
        result = self.validate_prompt(prompt_path)
        
        # Load configuration
        try:
            config_data = json.loads(config_path.read_text())
            config = ProjectConfig.from_dict(config_data)
        except Exception as e:
            result.issues.append(f"Could not load configuration: {e}")
            return result
        
        # Check if prompt matches configuration
        content = prompt_path.read_text(encoding="utf-8")
        
        # Verify project name is mentioned
        if config.project_name and config.project_name.lower() not in content.lower():
            result.suggestions.append(f"Project name '{config.project_name}' not found in prompt")
        
        # Verify architecture style if specified
        if config.architecture_style and config.architecture_style.lower() not in content.lower():
            result.suggestions.append(f"Architecture style '{config.architecture_style}' not mentioned")
        
        # Verify cloud provider if specified
        if config.cloud_provider and config.cloud_provider.lower() not in content.lower():
            result.suggestions.append(f"Cloud provider '{config.cloud_provider}' not mentioned")
        
        # Update quality score based on configuration alignment
        if result.suggestions:
            result.quality_score = max(0.0, result.quality_score - 0.1 * len(result.suggestions))
        
        logger.info(f"Prompt validation complete. Valid: {result.valid}, Score: {result.quality_score:.2f}")
        
        return result
    
    def _calculate_quality_score(
        self, 
        content: str, 
        issues: List[str], 
        suggestions: List[str]
    ) -> float:
        """Calculate quality score for prompt.
        
        Args:
            content: Prompt content
            issues: List of validation issues
            suggestions: List of suggestions
            
        Returns:
            Quality score between 0.0 and 1.0
        """
        score = 1.0
        
        # Penalize for issues (severe)
        score -= len(issues) * 0.2
        
        # Penalize for suggestions (mild)
        score -= len(suggestions) * 0.05
        
        # Bonus for good length
        length = len(content)
        if 1000 <= length <= 10000:
            score += 0.1
        elif 500 <= length <= 20000:
            score += 0.05
        
        # Bonus for structure
        if "# " in content:  # Has headings
            score += 0.05
        
        if "```" in content:  # Has code blocks
            score += 0.05
        
        # Bonus for YAML frontmatter
        if content.startswith("---"):
            score += 0.1
        
        return max(0.0, min(1.0, score))
    
    def improve_prompt(self, prompt_path: Path, config: ProjectConfig) -> str:
        """Generate an improved version of the prompt.
        
        Args:
            prompt_path: Path to current prompt
            config: Project configuration
            
        Returns:
            Improved prompt content
        """
        current_content = prompt_path.read_text(encoding="utf-8")
        
        # Parse existing frontmatter
        frontmatter = self.merger._parse_frontmatter(current_content)
        if not frontmatter:
            frontmatter = {}
        
        # Update metadata
        frontmatter.update({
            "project_name": config.project_name,
            "generated_at": "{{ timestamp }}",
            "version": "2.0"
        })
        
        if config.architecture_style:
            frontmatter["architecture"] = config.architecture_style
        
        if config.cloud_provider:
            frontmatter["cloud_provider"] = config.cloud_provider
        
        # Build improved content
        lines = ["---"]
        for key, value in frontmatter.items():
            lines.append(f"{key}: {value}")
        lines.extend(["---", ""])
        
        # Remove existing frontmatter from content
        content_without_frontmatter = self.merger._extract_content(current_content)
        
        # Add improved sections
        if "# Project Overview" not in content_without_frontmatter:
            lines.extend([
                "# Project Overview",
                "",
                f"**Project Name:** {config.project_name}",
                f"**Description:** {config.description or 'Modern application built with VIBE methodology'}",
                ""
            ])
        
        lines.append(content_without_frontmatter)
        
        return "\n".join(lines)


def validate_and_update_prompt(prompt_path: Path, config_path: Path) -> PromptValidationResult:
    """Legacy function for backward compatibility.
    
    Args:
        prompt_path: Path to prompt file
        config_path: Path to configuration file
        
    Returns:
        PromptValidationResult
    """
    validator = PromptValidator()
    return validator.validate_and_update_prompt(prompt_path, config_path)
