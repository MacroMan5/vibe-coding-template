"""VIBE Core - AI-powered project generation engine.

This package contains the core functionality for the VIBE coding template system,
including AI model integration, template processing, and project generation.
"""

__version__ = "0.1.0"
__author__ = "VIBE Coding Team"

from .generators import CodeArchitect
from .parsers import ClaudeResponseParser, FileObject
from .utils import ContextManager, JsonVectorMemory
from .models import ProjectConfig, GenerationResponse, DryRunResponse
# CLI is available as vibe_core.cli - avoid circular imports
from .validators import ProjectIntegrityValidator, PromptValidator
from .api import DebugAPI
from .workflows import GenerationWorkflow

__all__ = [
    "CodeArchitect",
    "ClaudeResponseParser",
    "FileObject",
    "ContextManager",
    "JsonVectorMemory",
    "ProjectConfig",
    "GenerationResponse", 
    "DryRunResponse",
    "ProjectIntegrityValidator",
    "PromptValidator",
    "DebugAPI",
    "GenerationWorkflow",
]
