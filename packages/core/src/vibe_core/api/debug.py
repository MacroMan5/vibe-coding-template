"""Debug API for VIBE Core development and testing."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field

from ..models.project import ProjectConfig

logger = logging.getLogger(__name__)


class DebugRequest(BaseModel):
    """Request model for debug API."""
    
    project_config: ProjectConfig = Field(..., description="Project configuration")
    merged_prompt: Optional[str] = Field(None, description="Merged prompt content")
    simulate_generation: bool = Field(True, description="Whether to simulate file generation")
    include_logs: bool = Field(True, description="Whether to include debug logs")


class DebugResponse(BaseModel):
    """Response model for debug API."""
    
    logs: List[str] = Field(default_factory=list, description="Debug logs")
    outputs: List[str] = Field(default_factory=list, description="Simulated output files")
    config: ProjectConfig = Field(..., description="Processed configuration")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Additional metadata")
    success: bool = Field(True, description="Whether operation succeeded")
    errors: List[str] = Field(default_factory=list, description="Any errors encountered")


class DebugAPI:
    """Debug API for testing and development."""
    
    def __init__(self):
        """Initialize debug API."""
        self.app = FastAPI(
            title="VIBE Core Debug API",
            description="Debug API for VIBE Core development and testing",
            version="1.0.0"
        )
        self._setup_routes()
    
    def _setup_routes(self) -> None:
        """Setup API routes."""
        
        @self.app.post("/debug-agent", response_model=DebugResponse)
        async def debug_agent(request: DebugRequest) -> DebugResponse:
            """Debug agent execution endpoint."""
            return await self.debug_agent_execution(request)
        
        @self.app.get("/health")
        async def health_check() -> Dict[str, str]:
            """Health check endpoint."""
            return {"status": "healthy", "service": "vibe-core-debug"}
        
        @self.app.get("/config/validate")
        async def validate_config(config: ProjectConfig) -> Dict[str, Any]:
            """Validate project configuration."""
            return self.validate_project_config(config)
    
    async def debug_agent_execution(self, request: DebugRequest) -> DebugResponse:
        """Simulate agent execution for debugging.
        
        Args:
            request: Debug request
            
        Returns:
            DebugResponse with simulation results
        """
        logs = []
        outputs = []
        errors = []
        metadata = {}
        
        try:
            # Validate configuration
            config = request.project_config
            logs.append(f"Configuration parsed for project: {config.project_name}")
            
            # Simulate prompt processing
            if request.merged_prompt:
                prompt_length = len(request.merged_prompt)
                logs.append(f"Merged prompt loaded ({prompt_length} characters)")
                metadata["prompt_length"] = prompt_length
            else:
                logs.append("No merged prompt provided")
            
            # Simulate memory operations
            logs.append("Simulating memory recording")
            logs.append("Simulating context hydration")
            
            # Simulate file generation
            if request.simulate_generation:
                logs.append("Simulating plan generation")
                logs.append("Simulating file creation")
                
                # Generate mock file list based on configuration
                outputs = self._generate_mock_outputs(config)
                logs.append(f"Simulated {len(outputs)} output files")
            
            # Add metadata
            metadata.update({
                "project_name": config.project_name,
                "architecture_style": config.architecture_style,
                "cloud_provider": config.cloud_provider,
                "simulated": True
            })
            
            logger.info(f"Debug simulation completed for project: {config.project_name}")
            
            return DebugResponse(
                logs=logs,
                outputs=outputs,
                config=config,
                metadata=metadata,
                success=True,
                errors=errors
            )
            
        except Exception as e:
            error_msg = f"Debug simulation failed: {str(e)}"
            logger.error(error_msg)
            errors.append(error_msg)
            
            return DebugResponse(
                logs=logs,
                outputs=outputs,
                config=request.project_config,
                metadata=metadata,
                success=False,
                errors=errors
            )
    
    def validate_project_config(self, config: ProjectConfig) -> Dict[str, Any]:
        """Validate project configuration.
        
        Args:
            config: Project configuration to validate
            
        Returns:
            Validation results
        """
        issues = []
        warnings = []
        
        # Basic validation
        if not config.project_name:
            issues.append("Project name is required")
        elif len(config.project_name) < 2:
            issues.append("Project name must be at least 2 characters")
        
        # Check for invalid characters in project name
        if config.project_name and not config.project_name.replace("-", "").replace("_", "").isalnum():
            warnings.append("Project name contains special characters")
        
        # Validate architecture style
        valid_architectures = [
            "monolith", "microservices", "serverless", 
            "event-driven", "layered", "hexagonal"
        ]
        if config.architecture_style and config.architecture_style not in valid_architectures:
            warnings.append(f"Architecture style '{config.architecture_style}' is not in common patterns")
        
        # Validate cloud provider
        valid_providers = ["aws", "azure", "gcp", "vercel", "netlify", "heroku"]
        if config.cloud_provider and config.cloud_provider.lower() not in valid_providers:
            warnings.append(f"Cloud provider '{config.cloud_provider}' is not commonly supported")
        
        return {
            "valid": len(issues) == 0,
            "issues": issues,
            "warnings": warnings,
            "score": max(0.0, 1.0 - (len(issues) * 0.3) - (len(warnings) * 0.1))
        }
    
    def _generate_mock_outputs(self, config: ProjectConfig) -> List[str]:
        """Generate mock output file list based on configuration.
        
        Args:
            config: Project configuration
            
        Returns:
            List of mock file paths
        """
        outputs = [
            "README.md",
            "package.json",
            ".gitignore",
            "src/main.py",
            "src/__init__.py",
            "tests/test_main.py",
            "docs/API.md"
        ]
        
        # Add architecture-specific files
        if config.architecture_style == "microservices":
            outputs.extend([
                "services/user-service/main.py",
                "services/auth-service/main.py",
                "docker-compose.yml"
            ])
        elif config.architecture_style == "serverless":
            outputs.extend([
                "functions/handler.py",
                "serverless.yml",
                "requirements.txt"
            ])
        
        # Add cloud-specific files
        if config.cloud_provider == "aws":
            outputs.extend([
                "cloudformation.yml",
                "lambda_function.py"
            ])
        elif config.cloud_provider == "azure":
            outputs.extend([
                "azure-pipelines.yml",
                "arm-template.json"
            ])
        elif config.cloud_provider == "gcp":
            outputs.extend([
                "cloudbuild.yaml",
                "app.yaml"
            ])
        
        # Add technology-specific files
        if hasattr(config, 'technology_stack') and config.technology_stack:
            if "react" in [tech.lower() for tech in config.technology_stack]:
                outputs.extend([
                    "src/components/App.jsx",
                    "public/index.html"
                ])
            if "fastapi" in [tech.lower() for tech in config.technology_stack]:
                outputs.extend([
                    "src/api/routes.py",
                    "src/models/schemas.py"
                ])
        
        return outputs
    
    def get_app(self) -> FastAPI:
        """Get FastAPI application instance.
        
        Returns:
            FastAPI application
        """
        return self.app


# Create global instance
debug_api = DebugAPI()

def get_app() -> FastAPI:
    """Get FastAPI application instance - legacy compatibility.
    
    Returns:
        FastAPI application
    """
    return debug_api.get_app()
