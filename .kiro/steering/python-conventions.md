---
inclusion: always
---

# Python Conventions for Job Aggregator

## Naming & Structure
- Use explicit English names: `fetch_job_offers()`, `enrich_job_data()`, `JobOfferModel`
- Service classes: `JinaReaderService`, `GeminiEnrichmentService`, `SupabaseService`
- Job-related models: `JobOffer`, `CompanyInfo`, `JobLocation`, `SalaryRange`
- Async functions for I/O: `async def scrape_job_urls()`, `async def save_to_database()`

## Data Models (Pydantic Required)
```python
class JobOffer(BaseModel):
    title: str
    company: str
    location: Optional[str] = None
    salary_range: Optional[SalaryRange] = None
    posted_date: Optional[datetime] = None
    source_url: str
    extraction_method: Literal["jina", "crawl4ai", "manual"]
```

## Async Patterns
- All I/O operations must be async: database queries, HTTP requests, file operations
- Use `asyncio.gather()` for concurrent job processing
- Proper async context managers for database connections and HTTP sessions

## Error Handling for Scraping
```python
try:
    job_data = await jina_service.extract_job_data(url)
except JinaAPIError as e:
    logger.error(f"Jina extraction failed for {url}: {e}")
    # Fallback to alternative scraping method
except ValidationError as e:
    logger.error(f"Job data validation failed: {e}")
    # Skip invalid job posting
```

## Environment Configuration
- Load API keys from environment: `JINA_API_KEY`, `GEMINI_API_KEY`, `SUPABASE_URL`
- Service-specific config classes with Pydantic validation
- Never hardcode credentials or URLs

## Type Hints & Documentation
- All functions require type hints and docstrings
- Document job data extraction sources and methods
- Include examples for complex job processing functions

## Performance for Job Processing
- Use connection pooling for Supabase operations
- Implement URL deduplication with Redis/caching
- Process jobs in batches for bulk operations
- Use generators for large job datasets