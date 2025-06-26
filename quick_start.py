#!/usr/bin/env python3
"""
LANCEUR SIMPLE DU CRAWLER UNIFIÉ
"""

import sys
import os
sys.path.append('.')

import asyncio

async def main():
    print("🚀 LANCEMENT DU CRAWLER UNIFIÉ")
    print("=" * 50)
    
    # Import du crawler unifié
    from crawler.main_crawler_unified import main as crawler_main
    
    # Lancement
    await crawler_main()

if __name__ == "__main__":
    asyncio.run(main()) 