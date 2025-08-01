---
inclusion: always
---

# Phase 2 Implementation Guidelines

## 🎯 Phase 2 Enhanced Data Pipeline - Implementation Standards

### Critical Implementation Principles

#### 1. Zero-Breaking Changes Policy
- **NEVER modify existing methods** - only extend or add new ones
- **ALWAYS maintain backward compatibility** - existing code must continue working
- **USE optional parameters** with safe defaults for all extensions
- **TEST regression thoroughly** before any deployment

#### 2. Safe Configuration Extension Pattern
```python
# ✅ CORRECT - Safe extension
@dataclass
class SourceBaseConfig:
    # ... existing fields unchanged ...
    stage2_params: Optional[Dict[str, Any]] = None  # Safe default

# ❌ WRONG - Breaking change
@dataclass 
class SourceBaseConfig:
    # ... existing fields ...
    stage2_params: Dict[str, Any]  # Required field breaks existing code
```

#### 3. Database Migration Safety Rules
- **ALWAYS use NULL defaults** for new columns
- **CREATE indexes concurrently** to avoid locks
- **TEST migration on copy** of production data first
- **PREPARE rollback script** before executing migration
- **MONITOR performance** after migration

#### 4. Service Integration Pattern
```python
# ✅ CORRECT - New service, no modification of existing
class EnhancedDetailScraper:
    # New functionality in separate service
    pass

# ❌ WRONG - Modifying existing service
class DetailScraper:
    # Adding Stage 2 methods here risks breaking existing functionality
```

### Phase 2 Specific Standards

#### Configuration Management
- **Source configs** must remain backward compatible
- **stage2_params** must be completely optional
- **Fallback logic** must use existing Stage 1 parameters
- **Validation** must not break on missing Stage 2 config

#### Error Handling Strategy
```python
# Stage 2 failures must NEVER impact Stage 1
try:
    stage2_result = await enhanced_scraper.extract_enriched_job_data(url, source)
except Exception as e:
    logger.error("Stage 2 failed, continuing with Stage 1", error=str(e))
    # Stage 1 continues normally
    stage1_result = await detail_scraper.extract_job_data(url, source)
```

#### Database Operations
- **Use UPSERT patterns** to handle conflicts safely
- **Separate Stage 2 columns** from Stage 1 data
- **Maintain data integrity** with proper constraints
- **Log all database operations** for audit trail

#### Testing Requirements
- **100% regression test coverage** - all existing tests must pass
- **New functionality tests** - >90% coverage for Stage 2 code
- **Integration tests** - full pipeline validation
- **Performance tests** - ensure no Stage 1 degradation

### Code Quality Standards

#### Logging and Monitoring
```python
# Structured logging with correlation IDs
logger.info("Stage 2 extraction started",
           url=job_url,
           source=source_name,
           correlation_id=correlation_id,
           stage="stage2_extraction")
```

#### Performance Considerations
- **Async/await patterns** for all I/O operations
- **Semaphore-based rate limiting** for API calls
- **Connection pooling** for database operations
- **Caching strategies** for repeated operations

#### Security Guidelines
- **Validate all inputs** from external APIs
- **Sanitize data** before database storage
- **Use parameterized queries** to prevent injection
- **Log security-relevant events** for audit

### Deployment Strategy

#### Pre-deployment Checklist
- [ ] All existing tests pass (100% success rate)
- [ ] New tests achieve >90% coverage
- [ ] Database migration tested on staging
- [ ] Rollback procedures documented and tested
- [ ] Monitoring and alerting configured

#### Progressive Rollout
1. **Database migration** during low-traffic period
2. **Code deployment** with Stage 2 disabled
3. **Single source activation** (emploi_tg first)
4. **Progressive activation** of remaining sources
5. **Full activation** after 48h stability

#### Rollback Triggers
- Stage 1 functionality degradation
- Stage 2 success rate <70% for 2 hours
- Database performance impact >20%
- Critical errors in production logs
- User-reported functionality issues

### Monitoring and Alerting

#### Key Metrics to Track
- **Stage 1 performance** - must remain unchanged
- **Stage 2 success rate** - target >90%
- **Data quality scores** - target >0.7
- **Processing times** - target <15s per job
- **API costs** - monitor for unexpected increases

#### Alert Conditions
- Stage 2 failure rate >20% for 30 minutes
- Stage 1 performance degradation >10%
- Database query times >2x baseline
- API rate limit violations
- Memory usage >80% for 15 minutes

### Documentation Requirements

#### Code Documentation
- **Docstrings** for all new classes and methods
- **Type hints** for all function parameters and returns
- **Examples** in docstrings for complex methods
- **Error conditions** documented with expected behavior

#### Operational Documentation
- **Configuration guide** for Stage 2 parameters
- **Troubleshooting guide** for common issues
- **Migration procedures** with step-by-step instructions
- **Rollback procedures** with timing estimates

### Quality Gates

#### Before Merge
- [ ] All tests pass locally
- [ ] Code review approved by senior developer
- [ ] Documentation updated
- [ ] No security vulnerabilities detected

#### Before Deployment
- [ ] Staging environment validation complete
- [ ] Performance benchmarks within acceptable range
- [ ] Database migration tested successfully
- [ ] Rollback procedures validated

#### Before Full Activation
- [ ] Single source validation successful
- [ ] 24-hour stability period completed
- [ ] Monitoring and alerting functional
- [ ] Team trained on new functionality

---

*Guidelines established for Phase 2 Enhanced Data Pipeline implementation*  
*Compliance mandatory for all Phase 2 development work*