"""
Configuration Sentry pour Job Aggregator Crawler
Monitoring et analyse d'erreurs avancée
"""

import os
try:
    import sentry_sdk
    from sentry_sdk.integrations.logging import LoggingIntegration
    from sentry_sdk.integrations.stdlib import StdlibIntegration
    from sentry_sdk.integrations.excepthook import ExcepthookIntegration
except ImportError:
    sentry_sdk = None
    LoggingIntegration = None
    StdlibIntegration = None
    ExcepthookIntegration = None

# Configuration des DSN
SENTRY_DSNS = {
    "production": "https://355f2969714c599087c8fd2c3347bc83@o4509588073676800.ingest.us.sentry.io/4509588149370880",
    "development": "https://84ed887d33dff31ef19c6968e618bf44@o4509588073676800.ingest.us.sentry.io/4509588149370880"
}

def init_sentry(dsn=None):
    if sentry_sdk is None:
        print("⚠️  Sentry SDK non installé, monitoring désactivé.")
        return
    if dsn:
        sentry_sdk.init(
            dsn=dsn,
            integrations=[
                LoggingIntegration() if LoggingIntegration else None,
                StdlibIntegration() if StdlibIntegration else None,
                ExcepthookIntegration() if ExcepthookIntegration else None
            ],
            traces_sample_rate=1.0,
            before_send=before_send_filter,
        )
        print("✅ Sentry initialisé")
    else:
        print("⚠️  DSN Sentry non fourni, monitoring désactivé.")

def before_send_filter(event, hint):
    """Filtre et enrichit les événements"""
    event.setdefault('tags', {}).update({'component': 'crawler', 'project': 'job-aggregator'})
    
    if 'exception' in event:
        exc_info = hint.get('exc_info')
        if exc_info and len(exc_info) > 1:
            exception = exc_info[1]
            if any(err in str(exception) for err in ['Connection timeout', 'Read timeout', 'robots.txt']):
                event['level'] = 'warning'
    return event

def capture_crawling_error(error, url=None, source=None, extra_data=None):
    """Capture erreur de crawling avec contexte"""
    with sentry_sdk.push_scope() as scope:
        if url:
            scope.set_tag("failed_url", url)
        if source:
            scope.set_tag("source_site", source)
        if extra_data:
            for key, value in extra_data.items():
                scope.set_extra(key, value)
        scope.set_tag("error_type", "crawling")
        sentry_sdk.capture_exception(error)

def capture_extraction_error(error, url=None, selector=None, html_snippet=None):
    """Capture erreur d'extraction"""
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("error_type", "extraction")
        scope.set_tag("failed_selector", selector)
        scope.set_context("extraction", {
            "url": url,
            "selector": selector,
            "html_preview": html_snippet[:500] if html_snippet else None
        })
        sentry_sdk.capture_exception(error)

def capture_enrichment_error(error, job_data=None, llm_provider=None):
    """Capture erreur d'enrichissement LLM"""
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("error_type", "enrichment")
        scope.set_tag("llm_provider", llm_provider)
        scope.set_context("enrichment", {
            "job_title": job_data.get('title') if job_data else None,
            "llm_provider": llm_provider,
            "job_id": job_data.get('id') if job_data else None
        })
        sentry_sdk.capture_exception(error)

def log_crawling_performance(source, url, duration, items_found):
    """
    Log des métriques de performance
    """
    with sentry_sdk.push_scope() as scope:
        scope.set_tag("metric_type", "performance")
        scope.set_tag("source_site", source)
        
        scope.set_context("performance", {
            "url": url,
            "duration_seconds": duration,
            "items_extracted": items_found,
            "extraction_rate": items_found / duration if duration > 0 else 0
        })
        
        sentry_sdk.capture_message(
            f"Crawling completed: {source} - {items_found} items in {duration:.2f}s",
            level="info"
        )

# Décorateur pour automatiser la capture d'erreurs
def monitor_crawling_function(source_name=None):
    """
    Décorateur pour monitorer automatiquement les fonctions de crawling
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                capture_crawling_error(
                    error=e,
                    source=source_name,
                    extra_data={
                        "function_name": func.__name__,
                        "args": str(args)[:200],
                        "kwargs": str(kwargs)[:200]
                    }
                )
                raise
        return wrapper
    return decorator 