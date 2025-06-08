# 🤖 GitHub Copilot Agent Instructions

This file contains instructions for GitHub Copilot to effectively assist with development on the Vibe Coding Template project.

## 📋 Project Overview

**Project Type**: AI-powered project generator  
**Tech Stack**: Python, TypeScript, Next.js, Claude AI  
**Architecture**: Monorepo with core Python package and Next.js webapp  
**Purpose**: Generate complete software projects using AI

## 🏗️ Architecture Context

### Core Package (`packages/core/`)
- **Language**: Python 3.11+
- **Purpose**: AI generation workflows and prompt engineering
- **Key Classes**:
  - `GenerationWorkflow`: Main orchestration logic
  - `PromptMerger`: Template and prompt processing  
  - `ProjectConfig`: Configuration management
- **Dependencies**: Pydantic, OpenAI SDK, pathlib

### Webapp Package (`packages/webapp/`)
- **Language**: TypeScript/Next.js 14
- **Purpose**: Web interface and API integration
- **Key Features**: Real-time progress, file preview, error handling
- **Dependencies**: React, Tailwind CSS, Jest

## 🎯 Code Generation Guidelines

### Python Development
When working on Python code in the core package:

```python
# Use these imports consistently
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from pydantic import BaseModel, Field

# Follow this class structure
class ExampleModel(BaseModel):
    """Clear docstring describing the model purpose."""
    
    field_name: str = Field(description="Field description")
    optional_field: Optional[int] = None
    
    def process_data(self) -> Dict[str, Any]:
        """Process and return structured data."""
        return {"processed": True}
```

### TypeScript Development
When working on TypeScript code in the webapp:

```typescript
// Use consistent interfaces
interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
}

// Follow Next.js API route pattern
export async function POST(request: NextRequest): Promise<NextResponse> {
  try {
    const body = await request.json();
    // Process request
    return NextResponse.json({ success: true, data: result });
  } catch (error) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}
```

## 🔧 Key Patterns and Conventions

### File Structure Patterns
```
# Python files should follow this pattern
packages/core/src/vibe_core/
├── workflows/          # Business logic
├── models/            # Pydantic models
├── utils/             # Helper functions
└── generators/        # Code generation logic

# TypeScript files should follow this pattern
packages/webapp/
├── api/              # Next.js API routes
├── components/       # React components
├── __tests__/        # Test files
└── types/            # TypeScript definitions
```

### Error Handling Patterns

**Python:**
```python
try:
    result = await process_data(config)
    return WorkflowResult(success=True, data=result)
except Exception as error:
    logger.error(f"Processing failed: {error}")
    return WorkflowResult(success=False, error=str(error))
```

**TypeScript:**
```typescript
try {
  const result = await processData(config);
  return { success: true, data: result };
} catch (error) {
  console.error('Processing failed:', error);
  return { 
    success: false, 
    error: error instanceof Error ? error.message : 'Unknown error' 
  };
}
```

### Configuration Management

Always use environment variables for sensitive data:
```typescript
// Environment variable access
const openaiKey = process.env.OPENAI_API_KEY;
if (!openaiKey) {
  throw new Error('OPENAI_API_KEY is required');
}
```

## 🧪 Testing Patterns

### Python Tests
```python
import pytest
from vibe_core.models.project_config import ProjectConfig

def test_project_config_creation():
    """Test project configuration creation."""
    config = ProjectConfig(
        project_name="test-app",
        framework="nextjs",
        description="Test application"
    )
    assert config.project_name == "test-app"
    assert config.framework == "nextjs"
```

### TypeScript Tests
```typescript
import { describe, it, expect, jest } from '@jest/globals';

describe('API Route Tests', () => {
  it('should handle POST requests correctly', async () => {
    const mockRequest = {
      json: jest.fn().mockResolvedValue({ projectName: 'test' })
    };
    
    const response = await POST(mockRequest as any);
    const data = await response.json();
    
    expect(data.success).toBe(true);
  });
});
```

## 🚀 API Integration Patterns

### Core to Webapp Communication
The webapp communicates with the core Python package via subprocess calls:

```typescript
// API route pattern for calling Python core
const repoRoot = path.resolve(process.cwd(), "..", "..");
const coreDir = path.join(repoRoot, "packages", "core");

const pythonProcess = spawn('python', ['-m', 'vibe_core.cli', 'dry-run'], {
  cwd: coreDir,
  stdio: ['pipe', 'pipe', 'pipe']
});
```

### Response Serialization
Always ensure responses are JSON serializable:

```typescript
// Convert complex objects to serializable format
const serializableResult = {
  success: result.success,
  files: result.files.map(f => ({
    path: f.path.toString(),
    content: f.content,
    size: f.size
  })),
  metadata: {
    totalFiles: result.files.length,
    timestamp: new Date().toISOString()
  }
};
```

## 🎨 UI/UX Patterns

### Component Structure
```typescript
interface ComponentProps {
  title: string;
  onAction?: () => void;
  loading?: boolean;
}

export const Component: React.FC<ComponentProps> = ({ 
  title, 
  onAction, 
  loading = false 
}) => {
  return (
    <div className="p-4 border rounded-lg shadow-sm">
      <h3 className="text-lg font-semibold text-gray-900">{title}</h3>
      {onAction && (
        <button 
          onClick={onAction}
          disabled={loading}
          className="mt-2 px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
        >
          {loading ? 'Processing...' : 'Action'}
        </button>
      )}
    </div>
  );
};
```

### Tailwind CSS Classes
Use consistent Tailwind patterns:
- Spacing: `p-4`, `m-2`, `space-y-4`
- Colors: `bg-blue-600`, `text-gray-900`, `border-gray-200`
- Layout: `flex`, `grid`, `space-between`
- Responsive: `sm:`, `md:`, `lg:` prefixes

## 🔍 Debugging and Logging

### Python Logging
```python
import logging

logger = logging.getLogger(__name__)

def process_workflow(config: ProjectConfig) -> WorkflowResult:
    logger.info(f"Starting workflow for project: {config.project_name}")
    try:
        # Process
        logger.debug("Processing templates...")
        result = generate_files(config)
        logger.info(f"Generated {len(result.files)} files")
        return result
    except Exception as error:
        logger.error(f"Workflow failed: {error}", exc_info=True)
        raise
```

### TypeScript Logging
```typescript
const logger = {
  info: (message: string, data?: any) => {
    console.log(`[INFO] ${message}`, data || '');
  },
  error: (message: string, error?: any) => {
    console.error(`[ERROR] ${message}`, error || '');
  }
};
```

## 📦 Package Management

### Adding Dependencies

**Python (core package):**
```bash
cd packages/core
pip install new-package
pip freeze > requirements.txt
```

**TypeScript (webapp package):**
```bash
cd packages/webapp
npm install new-package
# or for dev dependencies
npm install -D new-dev-package
```

## 🔐 Security Considerations

### Input Validation
```python
from pydantic import BaseModel, validator

class ProjectConfig(BaseModel):
    project_name: str
    
    @validator('project_name')
    def validate_project_name(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Project name cannot be empty')
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Project name must be alphanumeric with dashes/underscores')
        return v.strip().lower()
```

### Environment Variable Security
```typescript
// Never log or expose sensitive data
const apiKey = process.env.OPENAI_API_KEY;
if (!apiKey) {
  throw new Error('Missing required API key');
}

// Use in requests without logging
const response = await openai.chat.completions.create({
  // config
});
```

## 🎯 Performance Optimization

### Python Performance
```python
# Use async/await for I/O operations
import asyncio
from typing import List

async def process_files_concurrently(files: List[str]) -> List[ProcessedFile]:
    tasks = [process_file(file) for file in files]
    return await asyncio.gather(*tasks)
```

### TypeScript Performance
```typescript
// Use React.memo for expensive components
const ExpensiveComponent = React.memo<Props>(({ data }) => {
  const processedData = useMemo(() => 
    expensiveProcessing(data), [data]
  );
  
  return <div>{processedData}</div>;
});
```

## 🚦 Common Issues and Solutions

### Path Resolution Issues
```python
# Always use pathlib for cross-platform compatibility
from pathlib import Path

base_dir = Path(__file__).parent.parent
template_dir = base_dir / "templates"
```

```typescript
// Use path.resolve for absolute paths
import path from 'path';

const repoRoot = path.resolve(process.cwd(), '..', '..');
const coreDir = path.join(repoRoot, 'packages', 'core');
```

### Serialization Issues
```python
# Convert Path objects to strings for JSON serialization
from pathlib import Path

def to_dict(self) -> Dict[str, Any]:
    return {
        'path': str(self.path),  # Convert Path to string
        'content': self.content,
        'size': len(self.content)
    }
```

## 📋 Code Review Checklist

When reviewing or generating code, ensure:

- [ ] Type hints are used (Python) / interfaces defined (TypeScript)
- [ ] Error handling is implemented
- [ ] Input validation is present
- [ ] Logging is appropriate
- [ ] Tests are written for new functionality
- [ ] Documentation is updated
- [ ] Environment variables are used for configuration
- [ ] Path handling is cross-platform compatible
- [ ] Response objects are serializable

## 🎯 Context-Aware Suggestions

When the user mentions:
- **"API"** → Focus on Next.js API routes and Python CLI integration
- **"UI/Frontend"** → Focus on React components and Tailwind styling
- **"Generation/AI"** → Focus on Python workflows and prompt engineering
- **"Testing"** → Focus on Jest tests and Python pytest patterns
- **"Configuration"** → Focus on environment variables and Pydantic models
- **"Performance"** → Focus on async patterns and optimization
- **"Error"** → Focus on error handling and logging patterns

---

**Use these guidelines to provide contextually relevant, high-quality code suggestions that follow the project's established patterns and conventions.**
