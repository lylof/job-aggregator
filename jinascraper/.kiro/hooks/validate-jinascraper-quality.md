---
name: "Validate JinaScraper Quality"
description: "Validates code quality, imports, and source functionality for JinaScraper project"
trigger: "manual"
workingDirectory: "jinascraper"
---

# JinaScraper Quality Validation Hook

This hook performs comprehensive quality validation for the JinaScraper project, ensuring architectural integrity and source functionality.

## Validation Steps

### 1. Import Validation
- Verify all modules import without errors
- Check for forbidden relative imports (`from ...module`)
- Validate package structure integrity

### 2. Source Functionality Test
- Test URL extraction for all 5 priority sources
- Validate URL cleaning effectiveness
- Check against quality thresholds

### 3. Architecture Compliance
- Verify steering file compliance
- Check for obsolete files or structures
- Validate test coverage

## Quality Thresholds

```python
EXPECTED_RESULTS = {
    "linkedin_togo": {"min_urls": 35, "target": 40},
    "anpetogo": {"min_urls": 12, "target": 15}, 
    "emploi_tg": {"min_urls": 20, "target": 25},
    "yop_lfrii": {"min_urls": 15, "target": 20},
    "emploitogo_info": {"min_urls": 10, "target": 15}
}
```

## Execution Command

```bash
# Run comprehensive validation
python -m pytest tests/test_imports_validation.py -v
python tests/test_stage1_new_architecture.py
python -c "
import sys
from pathlib import Path
sys.path.insert(0, str(Path.cwd()))

# Import validation
try:
    from jinascraper.config import SourceRegistry
    from jinascraper.services import JinaClient, ListingScraper
    from jinascraper.services.url_cleaner import clean_urls_by_source
    print('✅ All critical imports successful')
except ImportError as e:
    print(f'❌ Import error: {e}')
    sys.exit(1)

# Quick source validation
registry = SourceRegistry()
sources = ['linkedin_togo', 'anpetogo', 'emploi_tg', 'yop_lfrii', 'emploitogo_info']
for source in sources:
    config = registry.get_source(source)
    if config:
        print(f'✅ {source}: Configuration loaded')
    else:
        print(f'❌ {source}: Configuration missing')
"
```

## Success Criteria

- ✅ All imports work without `sys.path` manipulation
- ✅ All 5 sources have valid configurations
- ✅ No relative imports beyond 2 levels
- ✅ All URL cleaners have corresponding tests
- ✅ Source extraction meets minimum thresholds

## Failure Actions

If validation fails:
1. Review the AUDIT_TECHNIQUE_COMPLET.md
2. Follow the PLAN_DE_BATAILLE.md Phase 0 steps
3. Fix import issues before proceeding
4. Re-run validation until all checks pass

---

*Hook created following critical audit of 24/07/2025*