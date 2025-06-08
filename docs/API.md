# 📡 API Reference

Complete API documentation for the Vibe Coding Template project generator.

## 🌐 Base URL

**Development**: `http://localhost:3000`  
**Production**: `https://your-domain.com`

## 📋 Table of Contents

- [Authentication](#authentication)
- [API Endpoints](#api-endpoints)
  - [Dry Run](#dry-run)
  - [Generate Project](#generate-project)
  - [Health Check](#health-check)
- [Data Models](#data-models)
- [Error Handling](#error-handling)
- [Rate Limiting](#rate-limiting)
- [Examples](#examples)

## 🔐 Authentication

Currently, the API uses API key authentication (planned for v1.2).

```typescript
// Future authentication header
headers: {
  'Authorization': 'Bearer your-api-key',
  'Content-Type': 'application/json'
}
```

## 📡 API Endpoints

### 🔍 Dry Run

Preview generated files without creating them on disk.

**Endpoint**: `POST /api/dry-run`

#### Request

```typescript
interface DryRunRequest {
  projectName: string;          // Project name (alphanumeric, dashes, underscores)
  framework: Framework;         // Target framework
  description: string;          // Project description
  features?: string[];          // Optional features to include
  outputPath?: string;          // Optional output path for preview
}

type Framework = 
  | 'nextjs' 
  | 'react' 
  | 'vue' 
  | 'angular' 
  | 'python' 
  | 'fastapi' 
  | 'django'
  | 'express';
```

#### Response

```typescript
interface DryRunResponse {
  success: boolean;
  data?: {
    files: GeneratedFile[];
    summary: GenerationSummary;
    metadata: ProjectMetadata;
  };
  error?: string;
  logs?: string[];
}

interface GeneratedFile {
  path: string;               // Relative file path
  content: string;            // File content
  size: number;               // File size in bytes
  type: 'file' | 'directory'; // File type
}

interface GenerationSummary {
  totalFiles: number;         // Total number of files
  totalSize: number;          // Total size in bytes
  estimatedSize: string;      // Human-readable size
  generationTime: number;     // Time taken in seconds
  framework: string;          // Framework used
}
```

#### Example Request

```bash
curl -X POST http://localhost:3000/api/dry-run \
  -H "Content-Type: application/json" \
  -d '{
    "projectName": "my-awesome-app",
    "framework": "nextjs",
    "description": "A modern e-commerce platform with user authentication and payment processing",
    "features": ["auth", "database", "payments"]
  }'
```

#### Example Response

```json
{
  "success": true,
  "data": {
    "files": [
      {
        "path": "package.json",
        "content": "{\n  \"name\": \"my-awesome-app\",\n  \"version\": \"0.1.0\",\n  ...",
        "size": 1245,
        "type": "file"
      },
      {
        "path": "src/app/page.tsx",
        "content": "import React from 'react';\n\nexport default function HomePage() {\n  ...",
        "size": 892,
        "type": "file"
      }
    ],
    "summary": {
      "totalFiles": 12,
      "totalSize": 45231,
      "estimatedSize": "44.2 KB",
      "generationTime": 26.4,
      "framework": "nextjs"
    },
    "metadata": {
      "technologies": ["Next.js", "TypeScript", "Tailwind CSS", "Prisma"],
      "features": ["auth", "database", "payments"],
      "complexity": "medium"
    }
  },
  "logs": [
    "Initializing Next.js project generator",
    "Processing authentication templates",
    "Generating database schema",
    "Creating payment integration",
    "Finalizing project structure"
  ]
}
```

---

### 🚀 Generate Project

Create a complete project and write files to disk.

**Endpoint**: `POST /api/generate-project`

#### Request

```typescript
interface GenerateProjectRequest {
  projectName: string;          // Project name
  framework: Framework;         // Target framework
  description: string;          // Project description
  outputPath: string;           // Output directory path
  features?: string[];          // Optional features
  overwrite?: boolean;          // Overwrite existing files (default: false)
}
```

#### Response

```typescript
interface GenerateProjectResponse {
  success: boolean;
  data?: {
    projectPath: string;        // Full path to created project
    filesCreated: number;       // Number of files created
    summary: GenerationSummary;
    nextSteps: string[];        // Suggested next steps
  };
  error?: string;
  logs?: string[];
}
```

#### Example Request

```bash
curl -X POST http://localhost:3000/api/generate-project \
  -H "Content-Type: application/json" \
  -d '{
    "projectName": "my-awesome-app",
    "framework": "nextjs",
    "description": "A modern e-commerce platform",
    "outputPath": "/home/user/projects",
    "features": ["auth", "database", "payments"],
    "overwrite": false
  }'
```

#### Example Response

```json
{
  "success": true,
  "data": {
    "projectPath": "/home/user/projects/my-awesome-app",
    "filesCreated": 12,
    "summary": {
      "totalFiles": 12,
      "totalSize": 45231,
      "estimatedSize": "44.2 KB",
      "generationTime": 28.1,
      "framework": "nextjs"
    },
    "nextSteps": [
      "cd /home/user/projects/my-awesome-app",
      "npm install",
      "npm run dev",
      "Open http://localhost:3000 in your browser"
    ]
  },
  "logs": [
    "Creating project directory: /home/user/projects/my-awesome-app",
    "Generated package.json",
    "Generated src/app/page.tsx",
    "Generated tailwind.config.js",
    "Generated prisma/schema.prisma",
    "Generated .env.example",
    "Project generation completed successfully"
  ]
}
```

---

### ❤️ Health Check

Check API status and system health.

**Endpoint**: `GET /api/health`

#### Response

```typescript
interface HealthCheckResponse {
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
  services: {
    core: 'healthy' | 'unhealthy';
    database?: 'healthy' | 'unhealthy';
    ai_provider: 'healthy' | 'unhealthy';
  };
  uptime: number;              // Uptime in seconds
}
```

#### Example Response

```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00.000Z",
  "version": "1.0.0",
  "services": {
    "core": "healthy",
    "ai_provider": "healthy"
  },
  "uptime": 86400
}
```

---

## 📊 Data Models

### Project Configuration

```typescript
interface ProjectConfig {
  project_name: string;        // Validated project name
  framework: Framework;        // Target framework
  description: string;         // Project description
  features: string[];          // Enabled features
  output_path?: string;        // Output directory
  
  // Framework-specific options
  nextjs_options?: {
    app_router: boolean;       // Use App Router (default: true)
    typescript: boolean;       // Use TypeScript (default: true)
    tailwind: boolean;         // Include Tailwind CSS (default: true)
    eslint: boolean;           // Include ESLint (default: true)
  };
  
  react_options?: {
    typescript: boolean;
    routing: 'react-router' | 'reach-router' | 'none';
    state_management: 'redux' | 'zustand' | 'context' | 'none';
  };
  
  python_options?: {
    framework: 'fastapi' | 'django' | 'flask';
    database: 'postgresql' | 'mysql' | 'sqlite';
    orm: 'sqlalchemy' | 'django-orm' | 'peewee';
  };
}
```

### Generated File

```typescript
interface GeneratedFile {
  path: string;                // Relative file path
  content: string;             // File content
  size: number;                // File size in bytes
  type: 'file' | 'directory';  // File type
  encoding: 'utf-8' | 'binary'; // File encoding
  executable?: boolean;        // Is file executable
  template_source?: string;    // Source template file
}
```

### Workflow Result

```typescript
interface WorkflowResult {
  success: boolean;
  files: GeneratedFile[];
  errors: string[];
  warnings: string[];
  metadata: {
    generation_time: number;
    total_files: number;
    total_size: number;
    framework: string;
    features_used: string[];
  };
}
```

## ❌ Error Handling

### Error Response Format

```typescript
interface ErrorResponse {
  success: false;
  error: string;               // Error message
  code: string;                // Error code
  details?: any;               // Additional error details
  timestamp: string;           // Error timestamp
}
```

### Error Codes

| Code | Description | HTTP Status |
|------|-------------|-------------|
| `INVALID_REQUEST` | Invalid request format | 400 |
| `MISSING_FIELD` | Required field missing | 400 |
| `INVALID_FRAMEWORK` | Unsupported framework | 400 |
| `INVALID_PROJECT_NAME` | Invalid project name format | 400 |
| `PATH_NOT_FOUND` | Output path doesn't exist | 404 |
| `PERMISSION_DENIED` | Insufficient permissions | 403 |
| `GENERATION_FAILED` | AI generation failed | 500 |
| `TEMPLATE_ERROR` | Template processing error | 500 |
| `INTERNAL_ERROR` | Internal server error | 500 |

### Example Error Response

```json
{
  "success": false,
  "error": "Invalid project name format",
  "code": "INVALID_PROJECT_NAME",
  "details": {
    "provided": "my project!",
    "requirements": "Alphanumeric characters, dashes, and underscores only"
  },
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

## 🚦 Rate Limiting

API endpoints are rate-limited to ensure fair usage:

- **Dry Run**: 10 requests per minute
- **Generate Project**: 5 requests per minute
- **Health Check**: 60 requests per minute

Rate limit headers:
```
X-RateLimit-Limit: 10
X-RateLimit-Remaining: 8
X-RateLimit-Reset: 1642248600
```

## 📝 Examples

### Complete Next.js Project Generation

```typescript
// 1. First, do a dry run to preview
const dryRunResponse = await fetch('/api/dry-run', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    projectName: 'ecommerce-store',
    framework: 'nextjs',
    description: 'Modern e-commerce store with user auth and payments',
    features: ['auth', 'database', 'payments', 'admin']
  })
});

const dryRunData = await dryRunResponse.json();

if (dryRunData.success) {
  console.log(`Will generate ${dryRunData.data.summary.totalFiles} files`);
  
  // 2. If satisfied, generate the project
  const generateResponse = await fetch('/api/generate-project', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      projectName: 'ecommerce-store',
      framework: 'nextjs',
      description: 'Modern e-commerce store with user auth and payments',
      outputPath: '/home/user/projects',
      features: ['auth', 'database', 'payments', 'admin']
    })
  });
  
  const generateData = await generateResponse.json();
  
  if (generateData.success) {
    console.log(`Project created at: ${generateData.data.projectPath}`);
    console.log('Next steps:', generateData.data.nextSteps);
  }
}
```

### Python FastAPI Project

```typescript
const response = await fetch('/api/generate-project', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    projectName: 'api-service',
    framework: 'python',
    description: 'REST API service with authentication and database',
    outputPath: '/home/user/projects',
    features: ['fastapi', 'postgresql', 'auth', 'cors'],
    python_options: {
      framework: 'fastapi',
      database: 'postgresql',
      orm: 'sqlalchemy'
    }
  })
});
```

### React SPA with State Management

```typescript
const response = await fetch('/api/generate-project', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    projectName: 'dashboard-app',
    framework: 'react',
    description: 'Admin dashboard with charts and data tables',
    outputPath: '/home/user/projects',
    features: ['routing', 'state-management', 'charts', 'tables'],
    react_options: {
      typescript: true,
      routing: 'react-router',
      state_management: 'redux'
    }
  })
});
```

## 🔧 SDK Usage (Future)

```typescript
// Future SDK for easier integration
import { VibeClient } from '@vibe/client';

const client = new VibeClient({
  apiKey: 'your-api-key',
  baseUrl: 'https://api.vibe-coding.com'
});

// Dry run
const preview = await client.dryRun({
  projectName: 'my-app',
  framework: 'nextjs',
  description: 'A modern web application'
});

// Generate project
const project = await client.generateProject({
  projectName: 'my-app',
  framework: 'nextjs',
  description: 'A modern web application',
  outputPath: './projects'
});
```

## 📚 Additional Resources

- **[Development Guide](./DEVELOPMENT.md)** - Setup and development instructions
- **[GitHub Copilot Integration](./COPILOT.md)** - Copilot agent guidelines
- **[Project Management](./PROJECT_MANAGEMENT.md)** - Roadmap and planning

---

**For support or questions about the API, please check our [GitHub Issues](https://github.com/your-org/vibe_coding_template/issues) or contact support.**
