# Implementation Plan

- [x] 1. Create core field mapping service


  - Create `services/field_mapper.py` with FieldMapper class
  - Implement field mapping dictionary with profile → profile_description mapping
  - Add method to map AI fields to database schema fields
  - _Requirements: 1.1, 1.2, 3.1_





- [x] 2. Implement schema validation utilities
  - Create `utils/schema_validator.py` with SchemaValidator class

  - Define VALID_COLUMNS set with all Supabase table columns

  - Implement field filtering method to remove invalid columns




  - Add logging for filtered fields with job URL context
  - _Requirements: 2.1, 2.2, 2.3_


- [ ] 3. Enhance DatabaseService with field mapping
  - Modify `services/database_service.py` to integrate FieldMapper
  - Update `_prepare_job_data()` method to apply field mapping before preparation
  - Add schema validation step after field mapping
  - Ensure backward compatibility with existing job data structure
  - _Requirements: 1.1, 1.3, 4.2_

- [ ] 4. Add comprehensive error handling and logging
  - Implement graceful degradation for mapping failures
  - Add structured logging for field transformations and validation errors
  - Create custom exceptions for field mapping and schema validation errors
  - Ensure jobs continue processing even if some fields fail mapping
  - _Requirements: 1.3, 2.3, 3.3_

- [ ] 5. Create unit tests for field mapping functionality
  - Write `tests/test_field_mapper.py` with comprehensive mapping tests
  - Test profile → profile_description mapping specifically
  - Test handling of unknown fields and invalid data types
  - Verify logging output for mapping operations
  - _Requirements: 1.1, 1.2, 3.1_

- [ ] 6. Create unit tests for schema validation
  - Write `tests/test_schema_validator.py` with validation tests
  - Test filtering of invalid columns against Supabase schema
  - Test preservation of valid fields and removal of invalid ones
  - Verify warning logs for filtered fields

  - _Requirements: 2.1, 2.2, 2.3_

- [x] 7. Create integration tests with database service


  - Write `tests/test_database_service_mapping.py` for end-to-end testing

  - Test complete flow from AI data with 'profile' field to successful database save
  - Test batch processing of 25 jobs with field mapping applied
  - Verify statistics accuracy after mapping corrections
  - _Requirements: 4.1, 4.3_

- [x] 8. Test with real AI-generated data containing profile field

  - Create test data that mimics current AI output with 'profile' field
  - Run integration test with DatabaseService.upsert_jobs_batch()
  - Verify successful save to Supabase with profile_description populated
  - Confirm no schema errors occur during batch processing
  - _Requirements: 1.1, 4.1, 4.2_



- [ ] 9. Validate fix with complete JinaScraper workflow




  - Run full scraping cycle with emploi_tg source (2 jobs for testing)
  - Verify all extracted jobs are successfully saved to database
  - Check that scraping_stats table shows correct saved job count
  - Confirm no "Could not find column" errors in logs
  - _Requirements: 4.1, 4.3_

- [ ] 10. Implement multi-source universal adapters
  - Create source-specific mappers for all 6 existing sources
  - Implement UniversalSourceAdapter with methods for each source
  - Add extraction_metadata population for source-specific data
  - Test with real data from emploi_tg, linkedin_togo, indeed_togo, anpetogo, emploitogo_info, yop_lfrii
  - _Requirements: 1.1, 4.1, 4.2_

- [ ] 11. Add monitoring and audit capabilities
  - Enhance logging to track field mapping statistics per scraping cycle
  - Add metrics for successful mappings vs failed mappings per source
  - Create audit trail for all field transformations applied
  - Update scraping statistics to include mapping success rates by source
  - _Requirements: 3.3, 2.3_