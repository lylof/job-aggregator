---
name: "Phase 2 Enhanced Pipeline Validation"
description: "Validates Phase 2 implementation quality, data integrity, and performance"
trigger: "manual"
workingDirectory: "jinascraper"
---

# Phase 2 Enhanced Pipeline Validation Hook

This hook performs comprehensive validation for Phase 2 Enhanced Data Pipeline implementation, ensuring that Stage 2 functionality works correctly while preserving Stage 1 integrity.

## Validation Steps

### 1. Regression Testing
- Verify all existing Stage 1 tests continue to pass
- Validate URL cleaner fixes (EmploiTogo.info, YOP L-FRII)
- Check that no existing functionality is broken
- Measure Stage 1 performance impact

### 2. Stage 2 Functionality Testing
- Test Enhanced Detail Scraper with real URLs
- Validate Markdown extraction quality
- Check Gemini expert structuration
- Verify database persistence

### 3. Configuration Validation
- Test stage2_params loading and fallback behavior
- Validate source-specific configurations
- Check backward compatibility
- Test progressive activation capabilities

### 4. Data Quality Assessment
- Validate structured JSON schema compliance
- Check data completeness and quality scores
- Test deduplication and conflict resolution
- Verify metadata accuracy

## Quality Thresholds

```python
PHASE2_QUALITY_THRESHOLDS = {
    "stage1_regression": {"max_failures": 0, "performance_impact": 0.1},
    "stage2_success_rate": {"min_rate": 0.9, "per_source": True},
    "data_quality": {"min_score": 0.7, "required_fields": ["title", "company"]},
    "processing_time": {"max_seconds": 15, "p95_threshold": 20},
    "url_cleaners": {
        "emploitogo_info": {"min_success": 1.0},
        "yop_lfrii": {"min_success": 1.0}
    }
}
```

## Execution Commands

```bash
# Phase 1: Critical fixes validation
python jinascraper/services/url_cleaners/emploitogo_info_cleaner.py --test
python jinascraper/services/url_cleaners/yop_lfrii_cleaner.py --test

# Phase 2: Regression testing
python jinascraper/test_validation_complete.py
python jinascraper/test_architecture_complete.py
python jinascraper/test_url_cleaners_detailed.py

# Phase 3: Stage 2 functionality testing
python -c "
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

async def test_stage2_pipeline():
    try:
        # Test configuration extension
        from jinascraper.config import SourceRegistry
        registry = SourceRegistry()
        
        # Test sources with Stage 2 config
        test_sources = ['emploi_tg', 'anpetogo', 'linkedin_togo']
        for source_id in test_sources:
            config = registry.get_source(source_id)
            if config and hasattr(config, 'stage2_params'):
                print(f'✅ {source_id}: Stage 2 config available')
                if config.stage2_params:
                    jina_params = config.get_stage2_jina_params()
                    gemini_config = config.get_stage2_gemini_config()
                    print(f'   Jina params: {len(jina_params)} parameters')
                    print(f'   Gemini config: {gemini_config.get(\"model\", \"default\")}')
                else:
                    print(f'   Using fallback configuration')
            else:
                print(f'❌ {source_id}: Stage 2 config missing')
        
        # Test Enhanced Detail Scraper
        from jinascraper.services.enhanced_detail_scraper import EnhancedDetailScraper
        
        async with EnhancedDetailScraper() as scraper:
            # Test with sample URLs
            test_urls = [
                ('https://www.emploi.tg/offre-emploi-togo/test-job', 'emploi_tg'),
                ('https://anpetogo.org/offres/test-job', 'anpetogo')
            ]
            
            for url, source in test_urls:
                try:
                    result = await scraper.extract_enriched_job_data(url, source)
                    if result:
                        print(f'✅ {source}: Stage 2 extraction successful')
                        print(f'   Quality score: {result.extraction_quality_score}')
                        print(f'   Processing time: {result.stage2_processing_time_ms}ms')
                    else:
                        print(f'⚠️ {source}: Stage 2 extraction returned None')
                except Exception as e:
                    print(f'❌ {source}: Stage 2 extraction failed - {str(e)}')
        
        print('\\n✅ Stage 2 pipeline validation completed')
        
    except ImportError as e:
        print(f'❌ Import error: {e}')
        print('Stage 2 components not yet implemented')
    except Exception as e:
        print(f'❌ Validation error: {e}')

asyncio.run(test_stage2_pipeline())
"

# Phase 4: Database validation
python -c "
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

async def test_database_extension():
    try:
        from jinascraper.services.database_service import DatabaseService
        
        async with DatabaseService() as db:
            # Check if Stage 2 columns exist
            columns_query = '''
            SELECT column_name, data_type, is_nullable 
            FROM information_schema.columns 
            WHERE table_name = 'jobs' 
            AND column_name IN ('stage2_markdown', 'stage2_structured', 'processing_stage')
            '''
            
            result = await db.fetch_all(columns_query)
            
            if len(result) >= 3:
                print('✅ Database: Stage 2 columns present')
                for row in result:
                    print(f'   {row[\"column_name\"]}: {row[\"data_type\"]} (nullable: {row[\"is_nullable\"]})')
            else:
                print('❌ Database: Stage 2 columns missing')
                print('   Run database migration first')
            
            # Check indexes
            index_query = '''
            SELECT indexname, indexdef 
            FROM pg_indexes 
            WHERE tablename = 'jobs' 
            AND indexname LIKE '%stage2%'
            '''
            
            indexes = await db.fetch_all(index_query)
            print(f'✅ Database: {len(indexes)} Stage 2 indexes found')
            
    except Exception as e:
        print(f'❌ Database validation error: {e}')

asyncio.run(test_database_extension())
"

# Phase 5: Performance validation
python -c "
import time
import asyncio
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

async def test_performance_impact():
    try:
        from jinascraper.core.orchestrator import ScrapingOrchestrator
        
        # Test Stage 1 performance (baseline)
        start_time = time.time()
        
        async with ScrapingOrchestrator() as orchestrator:
            # Run Stage 1 only
            stage1_result = await orchestrator.run_stage1_exploration(['emploi_tg'])
            stage1_time = time.time() - start_time
            
            print(f'✅ Stage 1 Performance: {stage1_time:.2f}s')
            print(f'   URLs discovered: {len(stage1_result.get(\"new_urls\", []))}')
            
            # Test Stage 1 + Stage 2 if available
            if hasattr(orchestrator, 'run_full_cycle_with_stage2'):
                start_time = time.time()
                full_result = await orchestrator.run_full_cycle_with_stage2(
                    sources=['emploi_tg'], 
                    enable_stage2=True
                )
                full_time = time.time() - start_time
                
                print(f'✅ Stage 1+2 Performance: {full_time:.2f}s')
                
                if 'stage2_result' in full_result:
                    stage2_data = full_result['stage2_result']
                    print(f'   Stage 2 success rate: {stage2_data.get(\"success_rate\", 0):.2%}')
                    print(f'   Average quality: {stage2_data.get(\"average_quality_score\", 0):.2f}')
            else:
                print('⚠️ Stage 2 orchestration not yet implemented')
                
    except Exception as e:
        print(f'❌ Performance test error: {e}')

asyncio.run(test_performance_impact())
"
```

## Success Criteria

### Phase 1 (Critical Fixes)
- ✅ EmploiTogo.info URL cleaner: 100% success rate
- ✅ YOP L-FRII URL cleaner: 100% success rate
- ✅ All existing tests continue to pass
- ✅ No regression in Stage 1 functionality

### Phase 2 (Configuration & Database)
- ✅ stage2_params loading works for all sources
- ✅ Fallback behavior functions correctly
- ✅ Database migration completed successfully
- ✅ New columns and indexes created properly

### Phase 3 (Stage 2 Implementation)
- ✅ EnhancedDetailScraper extracts data successfully
- ✅ Gemini expert structuration produces valid JSON
- ✅ Data quality scores meet minimum thresholds
- ✅ Processing times within acceptable limits

### Phase 4 (Integration)
- ✅ Orchestrator integration works correctly
- ✅ Stage 1 + Stage 2 pipeline functions end-to-end
- ✅ Error handling preserves Stage 1 functionality
- ✅ Database persistence works reliably

## Failure Actions

If validation fails:

### Critical Failures (Stop deployment)
- Any existing test failures
- Stage 1 performance degradation >10%
- Database migration errors
- Security vulnerabilities detected

### Warning Conditions (Investigate before proceeding)
- Stage 2 success rate <90%
- Data quality scores <0.7
- Processing times >15 seconds
- Memory usage increases >20%

### Recovery Procedures
1. **Configuration Issues**: Revert stage2_params to None
2. **Database Issues**: Execute rollback migration
3. **Service Issues**: Disable Stage 2 features via feature flags
4. **Performance Issues**: Scale back concurrent processing

## Monitoring Integration

This hook integrates with the monitoring system to:
- Track validation results over time
- Alert on quality degradation
- Measure performance trends
- Generate compliance reports

## Automated Execution

```bash
# Run full validation suite
./validate-phase2.sh

# Run specific validation phase
./validate-phase2.sh --phase=1  # Critical fixes only
./validate-phase2.sh --phase=2  # Configuration validation
./validate-phase2.sh --phase=3  # Stage 2 functionality
./validate-phase2.sh --phase=4  # Integration testing
```

---

*Hook created for Phase 2 Enhanced Data Pipeline validation*  
*Execute before any Phase 2 deployment or activation*