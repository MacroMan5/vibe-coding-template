# 🧑‍💻 Development Guide

This guide provides detailed instructions for developers working on the Vibe Coding Template project.

## 🏁 Getting Started

### Development Environment Setup

1. **System Requirements:**
   - Node.js >=18.0.0
   - Python >=3.11
   - Git 2.0+
   - VS Code (recommended)

2. **Required Extensions (VS Code):**
   - Python
   - TypeScript and JavaScript
   - Tailwind CSS IntelliSense
   - ESLint
   - Prettier

3. **Clone and Setup:**
   ```bash
   git clone <repository-url>
   cd vibe_coding_template
   npm run install-all
   cp .env.example .env
   # Edit .env with your API keys
   ```

## 🏗️ Project Structure Deep Dive

### Core Package (`packages/core/`)

```
packages/core/
├── src/
│   └── vibe_core/
│       ├── workflows/           # Generation workflows
│       │   ├── __init__.py
│       │   └── generation_workflow.py
│       ├── models/              # Pydantic models
│       │   ├── __init__.py
│       │   └── project_config.py
│       ├── utils/               # Utility functions
│       │   ├── __init__.py
│       │   └── prompt_merger.py
│       └── generators/          # Code generators
│           ├── __init__.py
│           └── base_generator.py
├── templates/                   # Project templates
│   ├── nextjs/
│   ├── react/
│   └── python/
├── agent_prompts/               # AI prompts
│   ├── system_prompts/
│   └── user_prompts/
└── requirements.txt             # Python dependencies
```

### Webapp Package (`packages/webapp/`)

```
packages/webapp/
├── api/                        # Next.js API routes
│   ├── dry-run.ts
│   └── generate-project.ts
├── components/                 # React components
│   ├── ui/
│   └── forms/
├── __tests__/                  # Test files
│   ├── dryRun.test.ts
│   └── generateProject.test.ts
├── styles/                     # CSS and Tailwind
├── public/                     # Static assets
└── package.json               # Dependencies
```

## 🔄 Development Workflow

### 1. Core Development (Python)

**Working with Workflows:**
```python
# Create new workflow
from vibe_core.workflows.base_workflow import BaseWorkflow

class CustomWorkflow(BaseWorkflow):
    def execute(self, config: ProjectConfig) -> WorkflowResult:
        # Implementation
        pass
```

**Adding New Models:**
```python
# Add to models/
from pydantic import BaseModel
from typing import Optional, List

class NewModel(BaseModel):
    field_name: str
    optional_field: Optional[int] = None
    list_field: List[str] = []
```

**Testing Core Logic:**
```bash
cd packages/core
python -m pytest tests/ -v
```

### 2. Frontend Development (Next.js)

**Creating Components:**
```typescript
// components/ui/NewComponent.tsx
import React from 'react';

interface NewComponentProps {
  title: string;
  onAction?: () => void;
}

export const NewComponent: React.FC<NewComponentProps> = ({ 
  title, 
  onAction 
}) => {
  return (
    <div className="p-4 border rounded-lg">
      <h3 className="text-lg font-semibold">{title}</h3>
      {onAction && (
        <button 
          onClick={onAction}
          className="mt-2 px-4 py-2 bg-blue-500 text-white rounded"
        >
          Action
        </button>
      )}
    </div>
  );
};
```

**API Route Development:**
```typescript
// api/new-endpoint.ts
import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    
    // Process request
    const result = await processRequest(body);
    
    return NextResponse.json({ 
      success: true, 
      data: result 
    });
  } catch (error) {
    return NextResponse.json(
      { success: false, error: error.message },
      { status: 500 }
    );
  }
}
```

**Testing Frontend:**
```bash
cd packages/webapp
npm test
npm run test:watch  # Watch mode
```

## 🧪 Testing Strategy

### Unit Tests
- **Core**: Python unit tests for models, utilities, and workflows
- **Webapp**: TypeScript/JavaScript tests for components and API routes

### Integration Tests
- End-to-end API testing
- Workflow integration tests
- Cross-package communication tests

### Test Commands
```bash
# Run all tests
npm run test

# Run specific package tests
npm run test --workspace=packages/core
npm run test --workspace=packages/webapp

# Run with coverage
npm run test:coverage
```

## 🔧 Configuration Management

### Environment Variables

**Development (.env.local):**
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
NODE_ENV=development
DEBUG=true
```

**Production (.env.production):**
```env
OPENAI_API_KEY=sk-...
NODE_ENV=production
DEBUG=false
```

### Configuration Files

**TypeScript Configuration (`tsconfig.json`):**
```json
{
  "compilerOptions": {
    "target": "ES2022",
    "lib": ["dom", "dom.iterable", "ES6"],
    "allowJs": true,
    "skipLibCheck": true,
    "strict": true,
    "forceConsistentCasingInFileNames": true,
    "noEmit": true,
    "esModuleInterop": true,
    "module": "esnext",
    "moduleResolution": "node",
    "resolveJsonModule": true,
    "isolatedModules": true,
    "jsx": "preserve",
    "incremental": true,
    "plugins": [
      {
        "name": "next"
      }
    ],
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

## 🚀 Deployment

### Local Development
```bash
npm run dev
```

### Production Build
```bash
npm run build
npm run start
```

### Docker Deployment
```dockerfile
# Dockerfile
FROM node:18-alpine

WORKDIR /app

COPY package*.json ./
RUN npm ci --only=production

COPY . .
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]
```

## 🐛 Debugging

### Backend Debugging (Python)
```python
# Add debug logging
import logging
logging.basicConfig(level=logging.DEBUG)

# Use debugger
import pdb; pdb.set_trace()
```

### Frontend Debugging (Next.js)
```typescript
// Console debugging
console.log('Debug info:', data);

// VS Code debugging
// Add breakpoints in VS Code
// Use "Debug: Start Debugging" command
```

### API Debugging
```bash
# Use curl to test APIs
curl -X POST http://localhost:3000/api/dry-run \
  -H "Content-Type: application/json" \
  -d '{"projectName": "test", "framework": "nextjs"}'
```

## 📝 Code Style

### TypeScript/JavaScript
- Use Prettier for formatting
- Follow ESLint rules
- Use TypeScript strict mode
- Prefer functional components
- Use async/await over promises

### Python
- Follow PEP 8
- Use type hints
- Use Pydantic for data validation
- Use f-strings for formatting
- Add docstrings to functions

### Example Code Style

**TypeScript:**
```typescript
interface UserData {
  id: string;
  name: string;
  email: string;
}

const processUser = async (userData: UserData): Promise<boolean> => {
  try {
    const result = await saveUser(userData);
    return result.success;
  } catch (error) {
    console.error('Failed to process user:', error);
    return false;
  }
};
```

**Python:**
```python
from typing import List, Optional
from pydantic import BaseModel

class User(BaseModel):
    id: str
    name: str
    email: str

async def process_user(user_data: User) -> bool:
    """Process user data and return success status."""
    try:
        result = await save_user(user_data)
        return result.success
    except Exception as error:
        logger.error(f"Failed to process user: {error}")
        return False
```

## 🔄 Git Workflow

### Branch Naming
- `feature/feature-name` - New features
- `bugfix/bug-name` - Bug fixes
- `hotfix/issue-name` - Critical fixes
- `docs/update-name` - Documentation updates

### Commit Messages
```
type(scope): description

feat(api): add user authentication endpoint
fix(ui): resolve mobile responsive issues
docs(readme): update installation instructions
test(core): add unit tests for workflow logic
```

### Pull Request Process
1. Create feature branch from `main`
2. Make changes and add tests
3. Run test suite: `npm run test`
4. Run linting: `npm run lint`
5. Create pull request with description
6. Request code review
7. Address feedback and merge

## 🏆 Best Practices

### General
- Write tests for new features
- Keep functions small and focused
- Use meaningful variable names
- Add comments for complex logic
- Handle errors gracefully

### Performance
- Use lazy loading for large components
- Optimize API responses
- Cache frequently accessed data
- Use appropriate data structures

### Security
- Validate all user inputs
- Use environment variables for secrets
- Sanitize data before processing
- Follow OWASP guidelines

## 🆘 Troubleshooting

### Common Issues

**Python Import Errors:**
```bash
# Ensure packages are installed
cd packages/core
pip install -r requirements.txt
```

**Node Module Issues:**
```bash
# Clear node_modules and reinstall
rm -rf node_modules package-lock.json
npm install
```

**API Connection Issues:**
```bash
# Check environment variables
cat .env
# Verify API keys are valid
```

**Build Failures:**
```bash
# Check TypeScript errors
npm run type-check
# Fix lint issues
npm run lint:fix
```

### Getting Help
- Check existing GitHub issues
- Create new issue with reproduction steps
- Use discussion forums for questions
- Review documentation thoroughly

---

**Happy coding! 🚀**
