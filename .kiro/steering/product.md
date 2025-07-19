---
inclusion: always
---

# Product Guidelines & Business Rules

## Domain Context

Job aggregation platform that scrapes, enriches, and serves job postings through multiple interfaces (web, API, bots). Primary source is emploi.tg with AI-powered data enhancement via Google Gemini.

## Business Logic Rules

### Job Processing Pipeline
- **Delta Processing**: Only process new jobs since last successful crawl
- **Deduplication**: Jobs with identical URL or title+company combination are considered duplicates
- **Enrichment Priority**: Missing salary, location, or job type should trigger AI enrichment
- **Source Attribution**: Always track extraction method (jina, crawl4ai, manual) and source URL

### Data Quality Standards
- **Required Fields**: title, company, source_url, extraction_method
- **Optional but Preferred**: location, salary_range, posted_date, job_type, description
- **Validation Rules**: URLs must be valid, dates cannot be future, salary ranges must be logical
- **Enrichment Triggers**: Incomplete job postings should be queued for AI enhancement

## User Experience Patterns

### Web Frontend
- Display jobs with clear source attribution
- Show enrichment status (original vs AI-enhanced data)
- Provide filtering by location, salary, company, job type
- Handle loading states gracefully during data fetching

### API Responses
- Include metadata about data freshness and source
- Provide pagination for large result sets
- Return structured error messages with helpful context
- Support filtering and sorting parameters

### Bot Interfaces
- Provide concise job summaries for notifications
- Include direct links to original job postings
- Support admin commands for crawl status and statistics

## Integration Conventions

### Service Communication
- Crawler publishes job data to Supabase with audit trail
- API serves cached data with SWR for performance
- Bots consume API endpoints rather than direct database access
- All services log structured data for monitoring

### Error Handling
- Graceful degradation when AI enrichment fails
- Fallback scraping methods when primary extraction fails
- User-friendly error messages that don't expose internal details
- Comprehensive logging for debugging and monitoring

## Operational Requirements

### Performance Expectations
- Crawl completion within 30 minutes for full site scan
- API response times under 500ms for standard queries
- Frontend page loads under 2 seconds
- Bot responses within 5 seconds

### Data Freshness
- New job postings available within 1 hour of publication
- Stale job removal after 30 days without updates
- Crawl frequency: every 6 hours during business days
- Manual crawl triggers available for administrators

### Quality Assurance
- Generate audit reports after each crawl cycle
- Track extraction success rates by method and source
- Monitor AI enrichment accuracy and cost
- Alert on significant data quality degradation