#!/usr/bin/env python3
"""
LANCEUR SIMPLE DU CRAWLER UNIFIÉ + SENTRY
"""

import sys
import os
sys.path.append('.')

import asyncio

async def main():
    print("🚀 LANCEMENT DU CRAWLER UNIFIÉ + SENTRY")
    print("=" * 50)
    
    # === INITIALISATION SENTRY ===
    try:
        from crawler.sentry_config import init_sentry
        
        print("🔧 Initialisation Sentry...")
        init_sentry(environment="production")
        print("✅ Sentry initialisé - Monitoring actif")
        
        # Message de démarrage
        sentry_sdk.capture_message("Crawler unifié démarré via quick_start", level="info")
        
    except Exception as e:
        print(f"⚠️  Sentry non disponible: {e}")
        import traceback
        traceback.print_exc()
    
    # Import du crawler unifié
    from crawler.main_crawler_unified import main as crawler_main
    
    # Lancement
    await crawler_main()

if __name__ == "__main__":
    asyncio.run(main()) 