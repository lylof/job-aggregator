-- Schema for Jina Job Scraper - Supabase Database
-- Created for Togo job aggregation platform

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create jobs table
CREATE TABLE IF NOT EXISTS jobs (
    -- Primary key
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    
    -- Unique identifier for deduplication
    item_id VARCHAR(255) UNIQUE NOT NULL,
    
    -- Required job information
    title VARCHAR(500) NOT NULL,
    company VARCHAR(255) NOT NULL,
    source_url TEXT NOT NULL,
    source_site VARCHAR(100) NOT NULL,
    
    -- Optional job details
    description TEXT,
    location VARCHAR(255),
    salary_range VARCHAR(255),
    contract_type VARCHAR(100),
    experience_level VARCHAR(255),
    education_level VARCHAR(255),
    sector VARCHAR(255),
    
    -- Job requirements and details
    missions TEXT[],
    required_skills TEXT[],
    profile_description TEXT,
    
    -- Dates
    posted_date DATE,
    application_deadline DATE,
    
    -- Contact information
    contact_email VARCHAR(255),
    contact_phone VARCHAR(50),
    
    -- Extraction metadata
    extraction_method VARCHAR(50) NOT NULL,
    extraction_metadata JSONB,
    quality_score DECIMAL(3,2),
    
    -- Raw data for debugging
    raw_data JSONB,
    
    -- System fields
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Constraints
    CONSTRAINT valid_quality_score CHECK (quality_score >= 0 AND quality_score <= 1),
    CONSTRAINT valid_extraction_method CHECK (extraction_method IN ('jina', 'gemini', 'crawl4ai', 'manual')),
    CONSTRAINT valid_dates CHECK (application_deadline IS NULL OR posted_date IS NULL OR application_deadline >= posted_date)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_jobs_source_url ON jobs(source_url);
CREATE INDEX IF NOT EXISTS idx_jobs_source_site ON jobs(source_site);
CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_jobs_posted_date ON jobs(posted_date DESC) WHERE posted_date IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_jobs_is_active ON jobs(is_active) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_jobs_company ON jobs(company);
CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location) WHERE location IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_jobs_contract_type ON jobs(contract_type) WHERE contract_type IS NOT NULL;

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_jobs_active_created ON jobs(is_active, created_at DESC) WHERE is_active = TRUE;
CREATE INDEX IF NOT EXISTS idx_jobs_source_active ON jobs(source_site, is_active, created_at DESC) WHERE is_active = TRUE;

-- Full-text search index
CREATE INDEX IF NOT EXISTS idx_jobs_search ON jobs USING gin(to_tsvector('french', title || ' ' || COALESCE(description, '') || ' ' || company));

-- Create scraping_stats table for monitoring
CREATE TABLE IF NOT EXISTS scraping_stats (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    source_site VARCHAR(100) NOT NULL,
    scrape_date DATE NOT NULL,
    urls_discovered INTEGER DEFAULT 0,
    urls_processed INTEGER DEFAULT 0,
    jobs_created INTEGER DEFAULT 0,
    jobs_updated INTEGER DEFAULT 0,
    success_rate DECIMAL(5,2),
    processing_time_seconds INTEGER,
    errors_count INTEGER DEFAULT 0,
    error_details JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- Unique constraint to prevent duplicate stats for same source/date
    UNIQUE(source_site, scrape_date)
);

-- Index for scraping stats
CREATE INDEX IF NOT EXISTS idx_scraping_stats_date ON scraping_stats(scrape_date DESC);
CREATE INDEX IF NOT EXISTS idx_scraping_stats_source ON scraping_stats(source_site, scrape_date DESC);

-- Create function to update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Create trigger to automatically update updated_at
DROP TRIGGER IF EXISTS update_jobs_updated_at ON jobs;
CREATE TRIGGER update_jobs_updated_at
    BEFORE UPDATE ON jobs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Create function to generate item_id from URL
CREATE OR REPLACE FUNCTION generate_item_id(source_url TEXT, source_site TEXT)
RETURNS TEXT AS $$
BEGIN
    -- Create a hash-based item_id from URL and source
    RETURN source_site || '_' || encode(digest(source_url, 'sha256'), 'hex')::varchar(16);
END;
$$ LANGUAGE plpgsql;

-- Create view for active jobs with computed fields
CREATE OR REPLACE VIEW active_jobs AS
SELECT 
    id,
    item_id,
    title,
    company,
    description,
    location,
    salary_range,
    contract_type,
    experience_level,
    education_level,
    sector,
    missions,
    required_skills,
    profile_description,
    posted_date,
    application_deadline,
    contact_email,
    source_url,
    source_site,
    extraction_method,
    quality_score,
    created_at,
    updated_at,
    -- Computed fields
    CASE 
        WHEN posted_date IS NOT NULL THEN CURRENT_DATE - posted_date
        ELSE NULL
    END as days_since_posted,
    CASE 
        WHEN application_deadline IS NOT NULL THEN application_deadline - CURRENT_DATE
        ELSE NULL
    END as days_until_deadline,
    array_length(missions, 1) as missions_count,
    array_length(required_skills, 1) as skills_count
FROM jobs 
WHERE is_active = TRUE;

-- Create view for job statistics by source
CREATE OR REPLACE VIEW jobs_by_source_stats AS
SELECT 
    source_site,
    COUNT(*) as total_jobs,
    COUNT(*) FILTER (WHERE is_active = TRUE) as active_jobs,
    COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE - INTERVAL '7 days') as jobs_last_7_days,
    COUNT(*) FILTER (WHERE created_at >= CURRENT_DATE - INTERVAL '30 days') as jobs_last_30_days,
    AVG(quality_score) FILTER (WHERE quality_score IS NOT NULL) as avg_quality_score,
    MAX(created_at) as last_job_created,
    COUNT(DISTINCT company) as unique_companies
FROM jobs
GROUP BY source_site
ORDER BY total_jobs DESC;

-- Create view for recent scraping activity
CREATE OR REPLACE VIEW recent_scraping_activity AS
SELECT 
    s.source_site,
    s.scrape_date,
    s.urls_discovered,
    s.urls_processed,
    s.jobs_created,
    s.jobs_updated,
    s.success_rate,
    s.processing_time_seconds,
    s.errors_count,
    s.created_at,
    -- Calculate efficiency metrics
    CASE 
        WHEN s.urls_discovered > 0 THEN (s.jobs_created::decimal / s.urls_discovered * 100)
        ELSE 0
    END as conversion_rate_percent
FROM scraping_stats s
ORDER BY s.scrape_date DESC, s.source_site;

-- Insert initial configuration data
INSERT INTO scraping_stats (source_site, scrape_date, urls_discovered, urls_processed, jobs_created, success_rate)
VALUES 
    ('emploi_tg', CURRENT_DATE, 0, 0, 0, 0.0),
    ('emploitogo_info', CURRENT_DATE, 0, 0, 0, 0.0),
    ('yop_lfrii', CURRENT_DATE, 0, 0, 0, 0.0),
    ('anpe_togo', CURRENT_DATE, 0, 0, 0, 0.0),
    ('linkedin_togo', CURRENT_DATE, 0, 0, 0, 0.0)
ON CONFLICT (source_site, scrape_date) DO NOTHING;

-- Create RLS (Row Level Security) policies if needed
-- ALTER TABLE jobs ENABLE ROW LEVEL SECURITY;
-- ALTER TABLE scraping_stats ENABLE ROW LEVEL SECURITY;

-- Grant permissions (adjust based on your Supabase setup)
-- GRANT SELECT, INSERT, UPDATE ON jobs TO authenticated;
-- GRANT SELECT ON active_jobs TO authenticated;
-- GRANT SELECT ON jobs_by_source_stats TO authenticated;
-- GRANT SELECT ON recent_scraping_activity TO authenticated;

-- Comments for documentation
COMMENT ON TABLE jobs IS 'Main table storing job offers scraped from various Togo job sites';
COMMENT ON COLUMN jobs.item_id IS 'Unique identifier for deduplication, generated from source_url hash';
COMMENT ON COLUMN jobs.extraction_method IS 'Method used to extract job data: jina, gemini, crawl4ai, or manual';
COMMENT ON COLUMN jobs.quality_score IS 'AI-generated quality score from 0.0 to 1.0 indicating data completeness';
COMMENT ON COLUMN jobs.raw_data IS 'Original scraped data in JSON format for debugging and reprocessing';

COMMENT ON TABLE scraping_stats IS 'Statistics and monitoring data for scraping operations';
COMMENT ON VIEW active_jobs IS 'View of active jobs with computed fields for easier querying';
COMMENT ON VIEW jobs_by_source_stats IS 'Aggregated statistics by job source for monitoring dashboard';
COMMENT ON VIEW recent_scraping_activity IS 'Recent scraping activity with efficiency metrics';

-- Create sample data for testing (optional)
/*
INSERT INTO jobs (
    item_id, title, company, source_url, source_site, description, location, 
    salary_range, contract_type, extraction_method, quality_score
) VALUES (
    'emploi_tg_sample_001',
    'Développeur Full Stack H/F',
    'TechCorp Lomé',
    'https://www.emploi.tg/offre-emploi-togo/dev-fullstack-001',
    'emploi_tg',
    'Nous recherchons un développeur full stack expérimenté pour rejoindre notre équipe.',
    'Lomé',
    '400,000 - 600,000 XOF/mois',
    'CDI',
    'gemini',
    0.95
) ON CONFLICT (item_id) DO NOTHING;
*/