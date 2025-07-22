"""URL cleaning facade for job sources."""

import re
import importlib
import inspect
import os
from pathlib import Path
from urllib.parse import urlparse
from ..utils.type_helpers import List, Dict, Any, Optional, Callable

import structlog

logger = structlog.get_logger(__name__)

# Dynamic cleaner registry
URL_CLEANERS: Dict[str, Callable[[List[str]], List[str]]] = {}


def clean_url(url: str) -> str:
    """
    Clean a URL by removing unwanted characters.
    
    Args:
        url: URL to clean
        
    Returns:
        Cleaned URL
    """
    # Remove problematic characters at the end
    url = re.sub(r'[.,;:!?)\\]$', '', url)
    
    # Remove trailing parenthesis
    url = url.rstrip(')')
    
    return url


def clean_generic_urls(urls: List[str]) -> List[str]:
    """
    Clean and filter URLs using generic rules.
    
    Args:
        urls: List of URLs to clean
        
    Returns:
        List of cleaned and filtered URLs
    """
    cleaned_urls = []
    
    for url in urls:
        # Basic cleaning
        url = clean_url(url)
        
        # Basic validation
        try:
            parsed = urlparse(url)
            if parsed.scheme in ('http', 'https') and parsed.netloc:
                if url not in cleaned_urls:
                    cleaned_urls.append(url)
        except Exception:
            continue
    
    return cleaned_urls


def discover_url_cleaners() -> None:
    """
    Dynamically discover and register URL cleaners from the url_cleaners directory.
    Each cleaner module should have a function named clean_X_urls where X is the source name.
    """
    global URL_CLEANERS
    
    # Get the directory of the url_cleaners package
    cleaners_dir = Path(__file__).parent / "url_cleaners"
    
    if not cleaners_dir.exists() or not cleaners_dir.is_dir():
        logger.warning(f"URL cleaners directory not found: {cleaners_dir}")
        return
    
    # Find all Python files in the directory
    for file_path in cleaners_dir.glob("*.py"):
        if file_path.name == "__init__.py":
            continue
        
        module_name = file_path.stem
        
        try:
            # Import the module dynamically
            module = importlib.import_module(f"..url_cleaners.{module_name}", package=__name__)
            
            # Find cleaner functions in the module
            for name, func in inspect.getmembers(module, inspect.isfunction):
                if name.startswith("clean_") and name.endswith("_urls"):
                    # Extract source name from function name (clean_X_urls -> X)
                    source_name = name[6:-5]  # Remove "clean_" and "_urls"
                    
                    # Special case for ANPE (clean_anpe_urls -> anpetogo)
                    if source_name == "anpe":
                        source_name = "anpetogo"
                    
                    # Register the cleaner function
                    URL_CLEANERS[source_name] = func
                    logger.info(f"Registered URL cleaner for source: {source_name}")
        
        except Exception as e:
            logger.error(f"Error loading URL cleaner module {module_name}: {str(e)}")

# Initialize the URL cleaners registry
discover_url_cleaners()


def clean_urls_by_source(urls: List[str], source_name: str) -> List[str]:
    """
    Clean URLs based on the source.
    
    Args:
        urls: List of URLs to clean
        source_name: Name of the source
        
    Returns:
        List of cleaned URLs
    """
    # Get the appropriate cleaner from the registry
    cleaner = URL_CLEANERS.get(source_name)
    
    if not cleaner:
        logger.warning(f"No specific cleaner found for source {source_name}, using generic cleaner")
        return clean_generic_urls(urls)
    
    logger.info(f"Using {source_name} specific cleaner for {len(urls)} URLs")
    return cleaner(urls)