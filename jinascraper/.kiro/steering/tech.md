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

### JinaScraper Core (✅ PRODUCTION READY)
- **Python 3.11+**: Base language with async/await patterns
- **Click**: CLI interface framework
- **Pydantic**: Data validation and serialization
- **Structlog**: Structured logging with correlation IDs
- **AsyncIO**: Asynchronous I/O operations

### Data Extraction & AI
- **Jina AI Reader API**: Primary web content extraction service (✅ ACTIVE)
- **Google Gemini API**: Structured data extraction and enrichment (✅ ACTIVE)
- **Redis/FakeRedis**: URL caching and deduplication (✅ 100% hit rate)
- **aiohttp**: Async HTTP client for API calls

### Database & Persistence
- **Supabase**: Primary database with PostgreSQL backend (✅ CONFIGURED)
- **Prisma ORM**: Database operations and migrations (✅ READY)
- **SQLAlchemy**: Alternative ORM for complex queries
- **Pydantic Models**: Data validation and type safety

### Legacy Components (Maintained for Compatibility)
- **FastAPI**: API backend (available but not primary interface)
- **Next.js 14**: Frontend (available but CLI is primary interface)
- **Crawl4AI + Playwright**: Alternative scraping (fallback option)

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
# JinaScraper CLI (Primary Interface)
python cli.py scrape                        # Full scraping cycle
python cli.py scrape --dry-run --verbose    # Test mode with detailed logs
python cli.py scrape --sources emploi_tg    # Specific source

# Development & Testing
python jinascraper/test_imports_fixed.py    # Validate imports
python jinascraper/check_redis_simple.py    # Test Redis connection
python jinascraper/audit_complet_janvier_2025.py  # Full audit

# Database Operations
python jinascraper/init_prisma_db.py        # Initialize Prisma database
# Migrations handled automatically by Prisma

# Legacy Commands (Still Available)
cd api && python main.py                    # API server (if needed)
cd frontend && npm run dev                   # Frontend (if needed)
cd crawler && python main_crawler.py        # Legacy crawler
```

## Configuration Management

- Service-specific configs: `api/config.py`, `crawler/config.py`
- Environment variables in `.env` files per service
- Supabase connection strings via environment
- Separate development and production configurations