---
inclusion: always
---

# Project Structure & Code Organization Rules

## Service Architecture Decisions

### When to Create New Services
- **New service**: Independent business domain (e.g., notifications, analytics)
- **Extend existing**: Related functionality within same domain
- **Shared utilities**: Cross-service code goes in `utils/` or `core/` folders

### Code Placement Rules
- **API routes**: `api/routers/` - group by resource (jobs, companies, users)
- **Business logic**: `api/services/` - one service per domain entity
- **Database models**: `api/models/` - SQLAlchemy models, one per table
- **Crawler sources**: `crawler/sources/` - one file per job site
- **Frontend pages**: `frontend/src/app/` - follow Next.js App Router structure
- **Reusable components**: `frontend/src/components/` - organized by feature

### JinaScraper Specific Rules (Added 24/07/2025)
- **Source configurations**: `jinascraper/config/sources/` - one file per job source
- **URL cleaners**: `jinascraper/services/url_cleaners/` - one cleaner per source
- **Core orchestration**: `jinascraper/core/` - central business logic
- **Shared utilities**: `jinascraper/utils/` - cross-component utilities
- **Tests**: `jinascraper/tests/` - organized by component type

## File Organization Patterns

### Naming Conventions (Enforced)
- **Python files**: `snake_case.py` (job_scraper.py, not jobScraper.py)
- **TypeScript files**: `kebab-case.tsx` for components, `camelCase.ts` for utilities
- **Database models**: Singular nouns (`JobOffer`, `Company`, not `JobOffers`)
- **API endpoints**: Plural resources (`/jobs`, `/companies`)
- **Configuration files**: Descriptive names (`config.py`, `alembic.ini`)

### Directory Structure Rules
- Each service maintains its own `requirements.txt` and `config.py`
- Database migrations only in `api/migrations/` (never in crawler)
- Static assets in `frontend/public/`, dynamic content via API
- Environment files at service root (`.env` per service)

## Integration & Communication Patterns

### Service Communication (Required)
- **Crawler → Database**: Direct Supabase writes with audit logging
- **API → Database**: SQLAlchemy ORM only, no direct SQL
- **Frontend → API**: HTTP requests via SWR, no direct database access
- **Bots → API**: HTTP endpoints only, never direct database

### Configuration Management
- Service-specific configs in each service root
- Shared environment variables in root `.env`
- Database connection strings via environment variables only
- API keys loaded at service startup, never hardcoded

### Data Flow Enforcement
1. **Job Discovery**: Crawler finds URLs → stores in `last_scrap_state.json`
2. **Data Extraction**: Jina API or Crawl4AI → structured job data
3. **AI Enrichment**: Gemini API enhances incomplete data
4. **Storage**: Validated data → Supabase with audit trail
5. **API Serving**: FastAPI serves cached data with SWR
6. **Frontend Display**: Next.js renders with Tailwind styling

## Development Workflow Rules

### Adding New Job Sources
1. Create new scraper in `crawler/sources/[site_name].py`
2. Add extraction schema to `crawler/extraction_schemas.py`
3. Register source in `crawler/main_crawler.py`
4. Test with audit mode before production

### Adding New API Endpoints
1. Define Pydantic models in `api/models/`
2. Create router in `api/routers/[resource].py`
3. Implement service logic in `api/services/[resource]_service.py`
4. Register router in `api/main.py`

### Adding Frontend Features
1. Create components in `frontend/src/components/[feature]/`
2. Add pages in `frontend/src/app/[route]/`
3. Use SWR for data fetching, Tailwind for styling
4. Follow TypeScript strict mode conventions

### Database Changes
1. Modify SQLAlchemy models in `api/models/`
2. Generate migration: `alembic revision --autogenerate -m "description"`
3. Review and edit migration file if needed
4. Apply: `alembic upgrade head`

## Quality & Maintenance Standards

### Required Patterns
- All Python I/O operations must be async
- Database queries through SQLAlchemy ORM only
- Error handling with structured logging
- Type hints required for all Python functions
- Pydantic validation for all data models
- Environment-based configuration (no hardcoded values)

### JinaScraper Critical Patterns (Added 24/07/2025)
- **ABSOLUTE IMPORTS ONLY**: No relative imports beyond 2 levels (`from ...module` FORBIDDEN)
- **NO sys.path MANIPULATION**: All imports must work without path modifications
- **SOURCE ISOLATION**: Each source must be completely independent
- **TEST COVERAGE**: Every URL cleaner must have comprehensive unit tests
- **QUALITY THRESHOLDS**: Each source must meet minimum URL extraction quotas