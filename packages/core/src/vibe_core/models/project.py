"""Project configuration models for VIBE Core."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ProjectConfig(BaseModel):
    """Configuration for project generation.
    
    This model represents the configuration sent from the frontend
    or provided via CLI for project generation.
    """
    
    project_name: str = Field(..., min_length=1, description="Name of the project to generate")
    architecture_style: Optional[str] = Field(None, description="Architecture pattern to use")
    cloud_provider: Optional[str] = Field(None, description="Target cloud provider")
    description: Optional[str] = Field(None, description="Project description")
    technology_stack: Optional[List[str]] = Field(default_factory=list, description="Technologies to use")
    features: Optional[List[str]] = Field(default_factory=list, description="Features to implement")
    
    # Allow additional fields for flexibility
    model_config = {"extra": "allow"}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return self.model_dump()
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProjectConfig":
        """Create instance from dictionary."""
        return cls(**data)


class GenerationMetadata(BaseModel):
    """Metadata for a generation session."""
    
    timestamp: str = Field(..., description="Generation timestamp")
    model_used: str = Field(..., description="AI model used for generation")
    config_hash: str = Field(..., description="Hash of the configuration")
    files_generated: int = Field(0, description="Number of files generated")
    success: bool = Field(True, description="Whether generation was successful")
    
    model_config = {"extra": "allow"}


class ValidationResult(BaseModel):
    """Result of project validation."""
    
    valid: bool = Field(..., description="Whether project is valid")
    errors: List[str] = Field(default_factory=list, description="Validation errors")
    warnings: List[str] = Field(default_factory=list, description="Validation warnings")
    score: float = Field(0.0, ge=0.0, le=1.0, description="Validation score")
