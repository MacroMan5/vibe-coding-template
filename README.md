# Vibe Coding Template

A modern AI-powered project generator built with Python and TypeScript.

## Architecture

This project uses a monorepo structure with two main packages:

- **`packages/core`** - Python backend with the AI generation logic
- **`packages/webapp`** - Next.js frontend for the web interface

## Quick Start

1. **Install dependencies:**
   ```bash
   npm install
   ```

2. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. **Start development:**
   ```bash
   npm run dev
   ```

4. **Access the webapp:**
   Open http://localhost:3000

## Development

### Core Package (Python)
- Location: `packages/core/`
- Contains the AI generation workflows and models
- Uses Python 3.11+ with Pydantic and OpenAI

### Webapp Package (Next.js)
- Location: `packages/webapp/`
- Modern React/Next.js interface
- TypeScript with Tailwind CSS

### Commands

```bash
# Install all dependencies
npm run install-all

# Run development server
npm run dev

# Build for production
npm run build

# Run tests
npm run test

# Lint all packages
npm run lint
```

## Environment Variables

Copy `.env.example` to `.env` and configure:

- `OPENAI_API_KEY` - Your OpenAI API key
- `ANTHROPIC_API_KEY` - Your Anthropic API key (optional)

## License

MIT License
