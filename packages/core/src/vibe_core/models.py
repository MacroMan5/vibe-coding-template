"""Pydantic models for project configuration in VIBE Core."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    """Configuration sent from the frontend for project generation.
    
    This model defines the structure of project configuration data
    that can be sent from the web interface or CLI.
    """

    project_name: str = Field(..., min_length=1, description="Name of the project")
    project_description: Optional[str] = Field(
        None, description="Brief description of the project"
    )
    architecture_style: Optional[str] = Field(
        None, description="Architecture pattern (e.g., 'microservices', 'monolith')"
    )
    cloud_provider: Optional[str] = Field(
        None, description="Target cloud provider (e.g., 'aws', 'azure', 'gcp')"
    )
    
    # Technology stack
    backend_framework: Optional[str] = Field(
        None, description="Backend framework (e.g., 'fastapi', 'django', 'express')"
    )
    frontend_framework: Optional[str] = Field(
        None, description="Frontend framework (e.g., 'react', 'vue', 'angular')"
    )
    database_type: Optional[str] = Field(
        None, description="Database type (e.g., 'postgresql', 'mongodb', 'mysql')"
    )
    
    # Features and requirements
    features: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Feature flags and configurations"
    )
    requirements: Optional[List[str]] = Field(
        default_factory=list, description="List of project requirements"
    )
    
    # Deployment and infrastructure
    deployment_target: Optional[str] = Field(
        None, description="Deployment target (e.g., 'docker', 'kubernetes', 'serverless')"
    )
    ci_cd_platform: Optional[str] = Field(
        None, description="CI/CD platform (e.g., 'github-actions', 'gitlab-ci', 'jenkins')"
    )
    
    # Team and project metadata
    team_size: Optional[int] = Field(None, ge=1, description="Size of the development team")
    project_timeline: Optional[str] = Field(
        None, description="Project timeline or deadline"
    )
    
    class Config:
        """Pydantic configuration."""
        extra = "allow"  # Allow additional fields


class GenerationRequest(BaseModel):
    """Request model for project generation."""
    
    config: ProjectConfig = Field(..., description="Project configuration")
    dry_run: bool = Field(False, description="Whether to perform a dry run")
    model: str = Field(
        "claude-3-5-sonnet-20241022", description="AI model to use for generation"
    )
    
    
class GenerationResponse(BaseModel):
    """Response model for project generation."""
    
    success: bool = Field(..., description="Whether generation was successful")
    project_path: Optional[str] = Field(None, description="Path to generated project")
    archive_path: Optional[str] = Field(None, description="Path to project archive")
    files_created: List[str] = Field(
        default_factory=list, description="List of created files"
    )
    logs: List[str] = Field(default_factory=list, description="Generation logs")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")


class DryRunResponse(BaseModel):
    """Response model for dry run operations."""
    
    files: List[Dict[str, str]] = Field(
        default_factory=list, description="Preview of files that would be created"
    )
    estimated_time: float = Field(0.0, description="Estimated generation time in seconds")
    conflicts: List[str] = Field(
        default_factory=list, description="Potential file conflicts"
    )


__all__ = [
    "ProjectConfig",
    "GenerationRequest",
    "GenerationResponse", 
    "DryRunResponse",
]
