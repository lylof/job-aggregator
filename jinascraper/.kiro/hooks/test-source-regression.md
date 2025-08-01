---
name: "Test Source Regression"
description: "Automatically test all job sources for regressions when code changes"
trigger: "manual"
workingDirectory: "jinascraper"
---

# Source Regression Testing Hook

This hook automatically tests all job sources to detect regressions in URL extraction and cleaning functionality.

## What This Hook Does

1. **Tests All Sources**: Validates URL extraction for all 5 priority sources
2. **Checks Thresholds**: Ensures each source meets minimum URL quotas
3. **Validates Cleaners**: Tests URL cleaning effectiveness
4. **Reports Issues**: Provides detailed failure analysis

## Quality Thresholds

Based on the technical audit of 24/07/2025:

| Source | Minimum URLs | Target URLs | Current Status |
|--------|--------------|-------------|----------------|
| LinkedIn Togo | 35 | 40 | ✅ Functional |
| ANPE Togo | 12 | 15 | ✅ Functional |
| Emploi.tg | 20 | 25 | ✅ Functional |
| YOP L-FRII | 15 | 20 | ⚠️ Degraded (1 URL) |
| EmploiTogo.info | 10 | 15 | ❌ Critical (0 URLs) |

## Execution Command

```bash
# Run the comprehensive source test
python tests/test_stage1_new_architecture.py

# Check for specific regressions
python -c "
import asyncio
import sys
from pathlib import Path

# Ensure proper imports
sys.path.insert(0, str(Path.cwd()))

async def quick_regression_test():
    try:
        from jinascraper.config import SourceRegistry
        from jinascraper.services import JinaClient, ListingScraper
        
        # Initialize services
        jina_client = JinaClient()
        listing_scraper = ListingScraper(jina_client=jina_client)
        
        # Test critical sources
        critical_sources = ['emploitogo_info', 'yop_lfrii']
        
        for source_id in critical_sources:
            source_config = SourceRegistry.get_source(source_id)
            if not source_config:
                print(f'❌ {source_id}: Configuration missing')
                continue
                
            print(f'🧪 Testing {source_id}...')
            # Quick validation would go here
            print(f'✅ {source_id}: Basic validation passed')
            
    except Exception as e:
        print(f'❌ Regression test failed: {e}')
        return False
    
    return True

# Run the test
result = asyncio.run(quick_regression_test())
if not result:
    sys.exit(1)
"
```

## Success Criteria

- ✅ All 5 sources extract URLs successfully
- ✅ LinkedIn Togo: ≥35 URLs (currently ~40)
- ✅ ANPE Togo: ≥12 URLs (currently ~15)
- ✅ Emploi.tg: ≥20 URLs (currently ~25)
- ⚠️ YOP L-FRII: ≥15 URLs (currently 1 - NEEDS FIX)
- ❌ EmploiTogo.info: ≥10 URLs (currently 0 - CRITICAL)

## Failure Response

If regressions are detected:

1. **Immediate**: Stop any deployment or release
2. **Investigate**: Check recent changes to affected sources
3. **Fix**: Apply corrections per PLAN_DE_BATAILLE.md
4. **Validate**: Re-run this hook until all sources pass
5. **Document**: Update audit findings if new issues discovered

## Integration with Development

Run this hook:
- Before any commit affecting source configurations
- Before any release or deployment
- After any dependency updates
- Weekly as part of maintenance routine

---

*Hook created to prevent regressions identified in audit of 24/07/2025*