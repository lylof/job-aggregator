---
inclusion: always
---

# Technology Stack & Development Guidelines

## Architecture

Multi-service architecture with clear separation:
- **API Backend**: FastAPI with Python 3.11+
- **Frontend**: Next.js 14 with TypeScript
- **Crawler Engine**: Python-based web scraping
- **Bot Services**: Admin and notification bots
- **Database**: PostgreSQL via Supabase

## Core Technologies by Service

### API Backend
- **FastAPI**: Async web framework with Pydantic validation
- **SQLAlchemy + Alembic**: ORM and database migrations
- **asyncpg**: Async PostgreSQL driver
- **Uvicorn**: ASGI server

### Frontend
- **Next.js 14**: App Router with TypeScript strict mode
- **Tailwind CSS + Radix UI**: Styling and accessible components
- **SWR**: Data fetching and caching

### Crawler & AI
- **Crawl4AI + Playwright**: Web scraping and browser automation
- **Jina AI Reader API**: Primary web content extraction service
- **Google Gemini API**: Structured data extraction and enrichment
- **Redis**: URL caching and deduplication

## Development Patterns

### Python Code Standards
- **Python 3.11+** required for all backend services
- **Black** formatting mandatory
- **Type hints** required for all functions
- **async/await** patterns for I/O operations
- **Pydantic models** for all data validation
- **Pytest** for unit testing

### API Design
- RESTful endpoints with proper HTTP status codes
- Structured error responses with middleware
- Environment-based configuration (`.env` files)
- CORS configured for local development

### Frontend Conventions
- Functional components with React hooks
- TypeScript strict mode enabled
- Tailwind utility-first CSS approach
- SWR for server state management

## External Service Integration

- **Supabase**: Primary database with connection strings in environment
- **Jina AI**: Web scraping via API (not local crawling)
- **Google Gemini**: AI enrichment and structured extraction
- **Redis**: Caching layer for processed URLs

## Essential Commands

```bash
# API Backend
cd api && python main.py                    # Run development server
cd api && alembic upgrade head              # Apply migrations

# Frontend  
cd frontend && npm run dev                  # Development server

# Crawler
cd crawler && python main_crawler.py       # Run scraping
```

## Configuration Management

- Service-specific configs: `api/config.py`, `crawler/config.py`
- Environment variables in `.env` files per service
- Supabase connection strings via environment
- Separate development and production configurations