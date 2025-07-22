#!/usr/bin/env python
"""Script to check if all required dependencies are installed."""

import importlib
import sys
from typing import Dict, List, Tuple

# List of required packages for Phase 4
REQUIRED_PACKAGES = [
    # Core dependencies
    "fastapi",
    "uvicorn",
    "pydantic",
    
    # HTTP and async
    "httpx",
    "aiohttp",
    "asyncio",
    
    # AI Services
    "google.generativeai",
    
    # Database and caching
    "supabase",
    "redis",
    "asyncpg",
    
    # Utilities
    "dotenv",
    "structlog",
    "tenacity",
    "psutil",  # For memory monitoring
    "importlib_metadata",  # For dynamic plugin loading
    "bleach",  # For HTML sanitization
]


def check_dependencies() -> Tuple[List[str], List[str]]:
    """Check if all required dependencies are installed."""
    installed = []
    missing = []
    
    for package in REQUIRED_PACKAGES:
        try:
            importlib.import_module(package)
            installed.append(package)
        except ImportError:
            missing.append(package)
    
    return installed, missing


def print_status(installed: List[str], missing: List[str]) -> None:
    """Print the status of dependencies."""
    print("=" * 60)
    print("DEPENDENCY CHECK")
    print("=" * 60)
    
    print(f"\n✅ {len(installed)}/{len(REQUIRED_PACKAGES)} packages installed:")
    for package in installed:
        print(f"  - {package}")
    
    if missing:
        print(f"\n❌ {len(missing)}/{len(REQUIRED_PACKAGES)} packages missing:")
        for package in missing:
            print(f"  - {package}")
        
        print("\nTo install missing packages, run:")
        print("pip install -r jinascraper/requirements.txt")
    else:
        print("\n🎉 All required packages are installed!")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    installed, missing = check_dependencies()
    print_status(installed, missing)
    
    # Exit with error code if any packages are missing
    sys.exit(1 if missing else 0)