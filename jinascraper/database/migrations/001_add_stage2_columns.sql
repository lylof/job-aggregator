-- Migration: Add Stage 2 Enhanced Pipeline columns
-- Description: Adds columns for storing Stage 2 enriched job data
-- Version: 2.1
-- Date: 2025-01-26

-- Add Stage 2 columns to job_offers table
ALTER TABLE job_offers 
ADD COLUMN IF NOT EXISTS stage2_markdown TEXT,
ADD COLUMN IF NOT EXISTS stage2_structured JSONB,
ADD COLUMN IF NOT EXISTS stage2_processed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS stage2_processing_time_ms INTEGER,
ADD COLUMN IF NOT EXISTS extraction_quality_score DECIMAL(3,2),
ADD COLUMN IF NOT EXISTS processing_stage VARCHAR(20) DEFAULT 'stage1';

-- Create indexes for performance
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_offers_processing_stage 
ON job_offers(processing_stage);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_offers_stage2_processed_at 
ON job_offers(stage2_processed_at) 
WHERE stage2_processed_at IS NOT NULL;

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_offers_quality_score 
ON job_offers(extraction_quality_score) 
WHERE extraction_quality_score IS NOT NULL;

-- Create GIN index for JSONB structured data
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_job_offers_stage2_structured_gin 
ON job_offers USING GIN(stage2_structured);

-- Add constraints
ALTER TABLE job_offers 
ADD CONSTRAINT chk_extraction_quality_score 
CHECK (extraction_quality_score >= 0.0 AND extraction_quality_score <= 1.0);

ALTER TABLE job_offers 
ADD CONSTRAINT chk_processing_stage 
CHECK (processing_stage IN ('stage1', 'stage2', 'failed'));

ALTER TABLE job_offers 
ADD CONSTRAINT chk_stage2_processing_time 
CHECK (stage2_processing_time_ms >= 0);

-- Create view for Stage 2 enriched jobs
CREATE OR REPLACE VIEW enriched_job_offers AS
SELECT 
    id,
    source_url,
    title,
    company,
    location,
    salary_range,
    posted_date,
    source_site,
    stage2_markdown,
    stage2_structured,
    stage2_processed_at,
    stage2_processing_time_ms,
    extraction_quality_score,
    processing_stage,
    created_at,
    updated_at
FROM job_offers 
WHERE processing_stage = 'stage2' 
AND stage2_structured IS NOT NULL;

-- Create function to calculate enrichment statistics
CREATE OR REPLACE FUNCTION get_enrichment_stats()
RETURNS TABLE(
    total_jobs BIGINT,
    stage1_jobs BIGINT,
    stage2_jobs BIGINT,
    failed_jobs BIGINT,
    avg_quality_score DECIMAL(3,2),
    avg_processing_time_ms INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        COUNT(*) as total_jobs,
        COUNT(*) FILTER (WHERE processing_stage = 'stage1') as stage1_jobs,
        COUNT(*) FILTER (WHERE processing_stage = 'stage2') as stage2_jobs,
        COUNT(*) FILTER (WHERE processing_stage = 'failed') as failed_jobs,
        ROUND(AVG(extraction_quality_score), 2) as avg_quality_score,
        ROUND(AVG(stage2_processing_time_ms))::INTEGER as avg_processing_time_ms
    FROM job_offers;
END;
$$ LANGUAGE plpgsql;

-- Add comments for documentation
COMMENT ON COLUMN job_offers.stage2_markdown IS 'Clean markdown content extracted in Stage 2';
COMMENT ON COLUMN job_offers.stage2_structured IS 'JSON structured data from Gemini expert processing';
COMMENT ON COLUMN job_offers.stage2_processed_at IS 'Timestamp when Stage 2 processing completed';
COMMENT ON COLUMN job_offers.stage2_processing_time_ms IS 'Total processing time for Stage 2 in milliseconds';
COMMENT ON COLUMN job_offers.extraction_quality_score IS 'Quality score (0.0-1.0) based on data completeness';
COMMENT ON COLUMN job_offers.processing_stage IS 'Current processing stage: stage1, stage2, or failed';

COMMENT ON VIEW enriched_job_offers IS 'View of jobs that have completed Stage 2 enrichment';
COMMENT ON FUNCTION get_enrichment_stats() IS 'Returns statistics about job enrichment pipeline';

-- Migration completed successfully
INSERT INTO migration_log (version, description, executed_at) 
VALUES ('001', 'Add Stage 2 Enhanced Pipeline columns', NOW())
ON CONFLICT (version) DO NOTHING;