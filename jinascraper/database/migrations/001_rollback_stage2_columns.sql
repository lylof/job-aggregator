-- Rollback: Remove Stage 2 Enhanced Pipeline columns
-- Description: Removes all Stage 2 related columns and objects
-- Version: 001_rollback
-- Date: 2025-01-26

-- Drop function
DROP FUNCTION IF EXISTS get_enrichment_stats();

-- Drop view
DROP VIEW IF EXISTS enriched_job_offers;

-- Drop indexes
DROP INDEX CONCURRENTLY IF EXISTS idx_job_offers_stage2_structured_gin;
DROP INDEX CONCURRENTLY IF EXISTS idx_job_offers_quality_score;
DROP INDEX CONCURRENTLY IF EXISTS idx_job_offers_stage2_processed_at;
DROP INDEX CONCURRENTLY IF EXISTS idx_job_offers_processing_stage;

-- Drop constraints
ALTER TABLE job_offers DROP CONSTRAINT IF EXISTS chk_stage2_processing_time;
ALTER TABLE job_offers DROP CONSTRAINT IF EXISTS chk_processing_stage;
ALTER TABLE job_offers DROP CONSTRAINT IF EXISTS chk_extraction_quality_score;

-- Drop columns
ALTER TABLE job_offers 
DROP COLUMN IF EXISTS processing_stage,
DROP COLUMN IF EXISTS extraction_quality_score,
DROP COLUMN IF EXISTS stage2_processing_time_ms,
DROP COLUMN IF EXISTS stage2_processed_at,
DROP COLUMN IF EXISTS stage2_structured,
DROP COLUMN IF EXISTS stage2_markdown;

-- Remove migration log entry
DELETE FROM migration_log WHERE version = '001';

-- Rollback completed successfully