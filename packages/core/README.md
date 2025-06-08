# VIBE Core

The core engine for VIBE Coding Template - an AI-powered project generation system.

## Overview

VIBE Core provides the foundational components for generating project architectures using AI models like Claude Sonnet 4. It includes:

- **AI Integration**: Direct integration with Anthropic Claude and OpenAI models
- **Template Processing**: Advanced template engine for project scaffolding  
- **Memory Management**: Persistent vector memory for context awareness
- **Response Parsing**: Intelligent parsing of AI-generated code structures
- **CLI Interface**: Command-line tools for automated workflows

## Installation

```bash
# Install from source
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"

# Install with documentation dependencies
pip install -e ".[docs]"
```

## Quick Start

### CLI Usage

```bash
# Interactive project creation
vibe init

# Generate project from config
vibe generate -c project-config.json

# Dry run preview
vibe generate -c project-config.json --dry-run

# Parse Claude response file
vibe parse response.txt output/
```

### Python API

```python
from vibe_core import CodeArchitect, ProjectConfig

# Create project configuration
config = ProjectConfig(
    project_name="my-awesome-app",
    project_description="A modern web application",
    backend_framework="fastapi",
    frontend_framework="react",
    database_type="postgresql"
)

# Initialize architect
architect = CodeArchitect(model="claude-3-5-sonnet-20241022")

# Generate project
result = architect.generate_project(
    config=config,
    prompt_text="Create a modern full-stack application...",
    system_prompt="You are an expert software architect...",
    output_dir=Path("./output")
)

if result.success:
    print(f"Project generated at: {result.project_path}")
    print(f"Archive created: {result.archive_path}")
```

## Architecture

### Core Components

- **`generators/`**: AI-powered code generation engines
  - `CodeArchitect`: Main project generation class
  
- **`parsers/`**: Response parsing utilities
  - `ClaudeResponseParser`: Parse structured AI responses
  
- **`utils/`**: Utility modules
  - `JsonVectorMemory`: Persistent memory with embeddings
  - `ContextManager`: Context retrieval and management
  - `env`: Environment configuration
  
- **`models.py`**: Pydantic data models
  - `ProjectConfig`: Project configuration schema
  - `GenerationResponse`: Generation result data
  
- **`cli/`**: Command-line interface
  - Rich CLI with interactive features

### Memory System

VIBE Core includes a sophisticated memory system that:

- Stores project context using OpenAI embeddings
- Enables semantic search across previous generations
- Maintains learning across sessions
- Provides context-aware responses

### Template Engine

The template system supports:

- Jinja2-based template processing
- Modular prompt composition
- Dynamic variable injection
- Multi-model compatibility

## Development

### Setup Development Environment

```bash
# Clone and install
git clone https://github.com/your-org/vibe-coding-template.git
cd vibe-coding-template/packages/core
pip install -e ".[dev]"

# Run tests
pytest

# Run with coverage
pytest --cov=src/vibe_core --cov-report=html

# Lint and format
ruff check src/ tests/
black src/ tests/
mypy src/
```

### Testing

```bash
# Unit tests
pytest tests/unit/

# Integration tests  
pytest tests/integration/

# Specific test
pytest tests/test_architect.py::test_generate_project
```

### Environment Variables

Create a `.env` file with required API keys:

```bash
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
```

## API Reference

### CodeArchitect

Main class for AI-powered project generation.

#### Methods

- `generate_project(config, prompt_text, system_prompt, output_dir)`: Generate complete project
- `generate_dry_run(config, prompt_text, system_prompt)`: Preview generation without writing files
- `call_claude(system_prompt, user_prompt)`: Direct Claude API interaction

### ProjectConfig

Configuration model for project generation.

#### Fields

- `project_name`: Name of the project (required)
- `project_description`: Brief description
- `backend_framework`: Backend technology choice
- `frontend_framework`: Frontend technology choice
- `database_type`: Database type selection
- `cloud_provider`: Target cloud platform
- `features`: Additional feature flags
- `requirements`: List of project requirements

### JsonVectorMemory

Persistent memory store with semantic search capabilities.


### Submitting Changes

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](../../LICENSE) file for details.
