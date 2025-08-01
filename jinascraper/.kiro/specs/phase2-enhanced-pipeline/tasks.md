# Implementation Tasks - Phase 2: Enhanced Data Pipeline

## Overview

Ce document détaille les tâches d'implémentation pour la Phase 2 du projet jinascraper. L'approche est sécurisée et incrémentale, garantissant qu'aucun code existant ne soit cassé.

## Task Breakdown

### Phase 1: Critical Fixes (Priority: URGENT - 24h)

#### Task 1.1: Fix EmploiTogo.info URL Cleaner
**Estimation:** 2h  
**Priority:** CRITICAL

- [ ] 1.1.1 Update emploitogo_info_cleaner.py pattern
  - Modify the regex pattern from current broken patterns to `r'^/emploitogo/[^/]+/?$'`
  - Test with real URLs from the validation report
  - Ensure 100% success rate on test URLs
  - _Requirements: 6.1, 6.3_

- [ ] 1.1.2 Create regression test for EmploiTogo.info
  - Write unit test with the 3 failing URLs from the report
  - Validate that new pattern matches all test cases
  - Add test to automated test suite
  - _Requirements: 7.1, 7.3_

#### Task 1.2: Fix YOP L-FRII URL Cleaner  
**Estimation:** 2h  
**Priority:** CRITICAL

- [ ] 1.2.1 Update yop_lfrii_cleaner.py pattern
  - Modify the regex pattern from current broken patterns to `r'^/emploi/[^/]+/?$'`
  - Test with real URLs from the validation report
  - Ensure 100% success rate on test URLs
  - _Requirements: 6.2, 6.3_

- [ ] 1.2.2 Create regression test for YOP L-FRII
  - Write unit test with the 3 failing URLs from the report
  - Validate that new pattern matches all test cases
  - Add test to automated test suite
  - _Requirements: 7.1, 7.3_

#### Task 1.3: Comprehensive Regression Testing
**Estimation:** 4h  
**Priority:** CRITICAL

- [ ] 1.3.1 Run complete test suite validation
  - Execute all existing tests to ensure no regressions
  - Run the 15 automated tests from the validation report
  - Verify that Stage 1 functionality is completely intact
  - _Requirements: 7.1, 7.2_

- [ ] 1.3.2 Validate URL cleaner fixes with real data
  - Test both fixed cleaners with live URLs
  - Measure success rates and compare to targets
  - Document results and confirm 100% success
  - _Requirements: 6.4, 7.4_

### Phase 2: Configuration Extension (Week 1, Days 1-2)

#### Task 2.1: Extend Base Configuration
**Estimation:** 4h  
**Priority:** HIGH

- [ ] 2.1.1 Add stage2_params to SourceBaseConfig
  - Add optional `stage2_params: Optional[Dict[str, Any]] = None` field to base_config.py
  - Implement `get_stage2_jina_params()` method with intelligent fallback
  - Implement `get_stage2_gemini_config()` method with defaults
  - Ensure 100% backward compatibility with existing configurations
  - _Requirements: 1.1, 1.2, 1.4_

- [ ] 2.1.2 Create configuration validation
  - Add validation method for stage2_params structure
  - Implement error handling for malformed configurations
  - Add logging for configuration loading and validation
  - _Requirements: 1.5, 8.1_

#### Task 2.2: Update Source Configurations
**Estimation:** 6h  
**Priority:** HIGH

- [ ] 2.2.1 Add Stage 2 config to emploi_tg.py
  - Add stage2_params with optimized Jina parameters for Emploi.tg
  - Configure css_selector_only for job content isolation
  - Set appropriate Gemini configuration
  - Test configuration loading and parameter retrieval
  - _Requirements: 1.3, 9.1_

- [ ] 2.2.2 Add Stage 2 config to anpetogo.py
  - Add stage2_params optimized for ANPE Togo structure
  - Configure selectors for government job posting format
  - Test with sample ANPE URLs
  - _Requirements: 1.3, 9.1_

- [ ] 2.2.3 Add Stage 2 config to linkedin_togo.py
  - Add stage2_params for LinkedIn job structure
  - Handle LinkedIn's specific content layout
  - Test with LinkedIn Togo job URLs
  - _Requirements: 1.3, 9.1_

### Phase 3: Database Extension (Week 1, Days 2-3)

#### Task 3.1: Create Database Migration
**Estimation:** 3h  
**Priority:** HIGH

- [ ] 3.1.1 Write safe database migration script
  - Create SQL script to add stage2_markdown, stage2_structured, processing_stage columns
  - Add stage2_processed_at and stage2_processing_time_ms for metadata
  - Ensure all columns are NULL by default for safety
  - Test migration on development database
  - _Requirements: 2.1, 2.3_

- [ ] 3.1.2 Create database indexes for performance
  - Add index on processing_stage for filtering
  - Add GIN index on stage2_structured for JSON queries
  - Add partial index for Stage 2 data queries
  - Measure index creation time and impact
  - _Requirements: 2.3, Performance NFR_

- [ ] 3.1.3 Create rollback migration script
  - Write script to safely remove added columns if needed
  - Test rollback procedure on development database
  - Document rollback process and conditions
  - _Requirements: 2.4, Reliability NFR_

#### Task 3.2: Extend Data Models
**Estimation:** 4h  
**Priority:** HIGH

- [ ] 3.2.1 Create EnrichedJobData model
  - Define Pydantic model for Stage 2 enriched data
  - Include all fields for markdown, structured data, and metadata
  - Add validation rules and type hints
  - Create serialization/deserialization methods
  - _Requirements: 2.2, 2.5_

- [ ] 3.2.2 Create Stage2StructuredData schema
  - Define comprehensive JSON schema for structured job data
  - Include all job fields: title, company, location, salary, etc.
  - Add validation for required vs optional fields
  - Create example data for testing
  - _Requirements: 4.1, 4.2, 4.4_

### Phase 4: Enhanced Detail Scraper Service (Week 1, Days 3-5)

#### Task 4.1: Create Enhanced Detail Scraper
**Estimation:** 8h  
**Priority:** HIGH

- [ ] 4.1.1 Implement EnhancedDetailScraper class
  - Create new service file services/enhanced_detail_scraper.py
  - Implement async context manager and initialization
  - Add source configuration detection and Stage 2 enablement check
  - Implement error handling and logging throughout
  - _Requirements: 3.1, 3.4, 8.2_

- [ ] 4.1.2 Implement optimized Markdown extraction
  - Create _extract_optimized_markdown method using Stage 2 Jina parameters
  - Handle css_selector_only for content isolation
  - Add content quality validation (minimum length, structure)
  - Implement retry logic with exponential backoff
  - _Requirements: 3.2, 3.3_

- [ ] 4.1.3 Implement batch processing capabilities
  - Create extract_multiple_enriched_jobs method with concurrency control
  - Add semaphore-based rate limiting for API calls
  - Implement progress tracking and error aggregation
  - Add comprehensive logging for batch operations
  - _Requirements: 3.1, 3.4, Performance NFR_

#### Task 4.2: Integrate Gemini Expert Structuration
**Estimation:** 6h  
**Priority:** HIGH

- [ ] 4.2.1 Create expert prompt builder
  - Implement _build_expert_prompt method with comprehensive job schema
  - Include all job fields: title, company, location, contract, salary, requirements, etc.
  - Add specific instructions for Togo job market context
  - Include data validation and normalization rules
  - _Requirements: 4.1, 4.3, 4.4_

- [ ] 4.2.2 Implement Gemini expert integration
  - Create _structure_with_gemini_expert method
  - Handle structured output configuration and JSON parsing
  - Add retry logic for API failures
  - Implement response validation and quality scoring
  - _Requirements: 4.2, 4.5, 8.3_

- [ ] 4.2.3 Add data quality assessment
  - Implement _calculate_quality_score method with field weighting
  - Add validation for required fields and data completeness
  - Create quality thresholds and alerting
  - Add quality metrics to logging and monitoring
  - _Requirements: 8.4, Quality Metrics_

### Phase 5: Gemini Service Enhancement (Week 1, Day 5)

#### Task 5.1: Extend Gemini Service
**Estimation:** 4h  
**Priority:** MEDIUM

- [ ] 5.1.1 Add expert structuration method to GeminiService
  - Implement structure_job_data_expert method in existing gemini_service.py
  - Add structured output configuration for JSON responses
  - Implement retry logic with exponential backoff
  - Add comprehensive error handling and logging
  - _Requirements: 4.1, 4.2_

- [ ] 5.1.2 Add configuration flexibility
  - Support different Gemini models (flash, pro)
  - Add temperature and token limit configuration
  - Implement cost tracking and optimization
  - Add performance metrics collection
  - _Requirements: 4.5, 8.1_

### Phase 6: Orchestrator Integration (Week 1, Days 6-7)

#### Task 6.1: Extend Orchestrator for Stage 2
**Estimation:** 6h  
**Priority:** HIGH

- [ ] 6.1.1 Add Stage 2 methods to ScrapingOrchestrator
  - Implement run_stage2_enhanced_analysis method
  - Add run_full_cycle_with_stage2 method with optional Stage 2
  - Ensure complete backward compatibility with existing methods
  - Add comprehensive error handling and fallback logic
  - _Requirements: 5.1, 5.2, 5.4_

- [ ] 6.1.2 Implement data persistence for Stage 2
  - Create _save_enriched_jobs method for batch database operations
  - Implement upsert logic to handle URL conflicts
  - Add transaction handling and rollback capabilities
  - Create comprehensive logging for database operations
  - _Requirements: 5.5, 2.2_

- [ ] 6.1.3 Add source detection and routing
  - Implement _detect_source_from_url method for URL-based source detection
  - Create _process_urls_by_source method for source-specific processing
  - Add source-specific configuration loading and validation
  - Implement progressive source activation capabilities
  - _Requirements: 9.1, 9.2, 9.3_

#### Task 6.2: Add Monitoring and Metrics
**Estimation:** 4h  
**Priority:** MEDIUM

- [ ] 6.2.1 Implement comprehensive metrics collection
  - Add processing time tracking for each Stage 2 step
  - Implement success rate calculation by source
  - Create quality score aggregation and reporting
  - Add API cost tracking and optimization alerts
  - _Requirements: 8.1, 8.3, 8.4_

- [ ] 6.2.2 Create performance reporting
  - Implement _calculate_average_quality method
  - Add detailed performance logging with structured data
  - Create summary reports for Stage 2 cycles
  - Add alerting for performance degradation
  - _Requirements: 8.2, 8.5_

### Phase 7: Testing and Validation (Week 2, Days 1-3)

#### Task 7.1: Unit Tests
**Estimation:** 8h  
**Priority:** HIGH

- [ ] 7.1.1 Create EnhancedDetailScraper tests
  - Write comprehensive unit tests for all public methods
  - Mock external dependencies (Jina, Gemini, Database)
  - Test error handling and edge cases
  - Achieve >90% code coverage for the new service
  - _Requirements: 7.1, 7.2_

- [ ] 7.1.2 Create configuration extension tests
  - Test stage2_params loading and validation
  - Test fallback behavior when stage2_params is None
  - Test configuration merging and parameter retrieval
  - Validate backward compatibility with existing configurations
  - _Requirements: 1.4, 1.5_

- [ ] 7.1.3 Create data model tests
  - Test EnrichedJobData model validation and serialization
  - Test Stage2StructuredData schema validation
  - Test quality score calculation with various data completeness levels
  - Validate JSON serialization/deserialization
  - _Requirements: 2.2, 4.4_

#### Task 7.2: Integration Tests
**Estimation:** 6h  
**Priority:** HIGH

- [ ] 7.2.1 Create end-to-end Stage 2 tests
  - Test complete Stage 2 pipeline with real URLs
  - Validate Markdown extraction with actual job pages
  - Test Gemini structuration with real content
  - Verify database persistence and retrieval
  - _Requirements: 7.3, 7.4_

- [ ] 7.2.2 Create orchestrator integration tests
  - Test run_full_cycle_with_stage2 with multiple sources
  - Validate Stage 1 + Stage 2 integration
  - Test error handling and fallback scenarios
  - Verify that Stage 1 continues working when Stage 2 fails
  - _Requirements: 5.4, 7.1_

- [ ] 7.2.3 Create database migration tests
  - Test migration script execution on clean database
  - Test rollback script functionality
  - Validate data integrity after migration
  - Test performance impact of new indexes
  - _Requirements: 2.4, Reliability NFR_

#### Task 7.3: Performance and Load Testing
**Estimation:** 4h  
**Priority:** MEDIUM

- [ ] 7.3.1 Create performance benchmarks
  - Measure Stage 2 processing time per job
  - Test concurrent processing capabilities
  - Validate API rate limiting and backoff behavior
  - Measure database query performance with new schema
  - _Requirements: Performance NFR, Scalability NFR_

- [ ] 7.3.2 Create load testing scenarios
  - Test Stage 2 with 100+ jobs simultaneously
  - Validate system behavior under API failures
  - Test memory usage and resource consumption
  - Verify graceful degradation under load
  - _Requirements: Scalability NFR, Reliability NFR_

### Phase 8: Documentation and Deployment (Week 2, Days 4-5)

#### Task 8.1: Create Documentation
**Estimation:** 4h  
**Priority:** MEDIUM

- [ ] 8.1.1 Update configuration documentation
  - Document stage2_params structure and options
  - Create configuration examples for each source
  - Document fallback behavior and best practices
  - Update existing configuration guides
  - _Requirements: Maintainability NFR_

- [ ] 8.1.2 Create Stage 2 usage documentation
  - Document EnhancedDetailScraper API and usage
  - Create examples for orchestrator Stage 2 methods
  - Document monitoring and troubleshooting procedures
  - Create migration and rollback procedures
  - _Requirements: Maintainability NFR_

#### Task 8.2: Deployment Preparation
**Estimation:** 3h  
**Priority:** HIGH

- [ ] 8.2.1 Create deployment checklist
  - Validate all tests pass in staging environment
  - Verify database migration procedures
  - Test rollback procedures and timing
  - Create deployment monitoring checklist
  - _Requirements: Reliability NFR_

- [ ] 8.2.2 Create monitoring setup
  - Configure logging for Stage 2 operations
  - Set up alerting for failure rates and performance
  - Create dashboards for Stage 2 metrics
  - Test alert triggers and escalation procedures
  - _Requirements: 8.4, 8.5_

### Phase 9: Production Deployment and Validation (Week 2, Days 6-7)

#### Task 9.1: Staged Production Deployment
**Estimation:** 4h  
**Priority:** HIGH

- [ ] 9.1.1 Deploy database migration
  - Execute migration script in production
  - Verify migration completion and data integrity
  - Test rollback capability (without executing)
  - Monitor database performance post-migration
  - _Requirements: 2.1, 2.4_

- [ ] 9.1.2 Deploy application code
  - Deploy Stage 2 code with feature flags disabled
  - Verify all existing functionality continues working
  - Run production regression tests
  - Monitor system performance and error rates
  - _Requirements: 7.1, Reliability NFR_

#### Task 9.2: Progressive Stage 2 Activation
**Estimation:** 6h  
**Priority:** HIGH

- [ ] 9.2.1 Enable Stage 2 for single source (emploi_tg)
  - Activate Stage 2 configuration for Emploi.tg only
  - Monitor processing performance and success rates
  - Validate data quality and completeness
  - Run for 24 hours and collect metrics
  - _Requirements: 9.1, 9.2_

- [ ] 9.2.2 Progressive activation for remaining sources
  - Enable Stage 2 for anpetogo after emploi_tg validation
  - Enable Stage 2 for linkedin_togo after anpetogo validation
  - Monitor each activation for 12 hours before proceeding
  - Document any issues and resolutions
  - _Requirements: 9.3, 9.4_

#### Task 9.3: Production Validation
**Estimation:** 4h  
**Priority:** HIGH

- [ ] 9.3.1 Validate Stage 2 data quality in production
  - Sample and review structured data from each source
  - Validate JSON schema compliance and completeness
  - Check quality scores and identify improvement opportunities
  - Compare Stage 2 data richness vs Stage 1
  - _Requirements: Quality Metrics, Success Criteria_

- [ ] 9.3.2 Performance and stability validation
  - Monitor system performance with Stage 2 active
  - Validate that Stage 1 performance is unaffected
  - Check error rates and success metrics
  - Verify monitoring and alerting functionality
  - _Requirements: Performance NFR, Success Criteria_

## Success Criteria Validation

### Phase 2.1 Completion Criteria
- [ ] All 15 existing tests continue to pass (100% regression test success)
- [ ] 2 URL cleaners fixed with 100% success rate on test URLs
- [ ] Stage 2 successfully processes jobs from at least 3 sources
- [ ] No measurable performance impact on Stage 1 operations
- [ ] Database migration completed without downtime
- [ ] All new code achieves >90% test coverage
- [ ] Documentation updated and complete

### Quality Gates
- [ ] Stage 2 success rate >90% across all enabled sources
- [ ] Average data quality score >0.7 (70% field completeness)
- [ ] Average processing time <15 seconds per job
- [ ] Zero critical errors in production for 48 hours
- [ ] Monitoring and alerting fully functional

## Risk Mitigation

### High-Risk Tasks
1. **Database Migration (Task 3.1)**: Test extensively in staging, have rollback ready
2. **URL Cleaner Fixes (Tasks 1.1, 1.2)**: Validate with real URLs before deployment
3. **Production Deployment (Task 9.1)**: Use feature flags, deploy during low-traffic hours

### Rollback Procedures
- **Configuration Changes**: Revert stage2_params to None
- **Database Migration**: Execute rollback script (removes added columns)
- **Application Code**: Revert to previous version, disable Stage 2 features
- **Full Rollback Time**: <1 hour for complete system restoration

## Dependencies and Prerequisites

### External Dependencies
- Jina AI API access and rate limits
- Google Gemini API access and quotas
- Database migration permissions
- Production deployment access

### Internal Dependencies
- All existing tests must pass before starting
- Stage 1 functionality must be fully stable
- Configuration system must be working correctly
- Database service must be operational

---

*Implementation tasks validated for Phase 2.1 Enhanced Data Pipeline*  
*Total estimated effort: ~80 hours over 2 weeks*  
*Critical path: URL fixes → Configuration → Database → Service → Integration → Testing*