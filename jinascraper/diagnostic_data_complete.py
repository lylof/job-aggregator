#!/usr/bin/env python3
"""
Script de diagnostic complet pour afficher les données extraites
dans leur format {raw_markdown, structured_json}
"""

import asyncio
import json
import sys
import time
from pathlib import Path

# Ajouter le chemin du module
sys.path.append(str(Path(__file__).parent))

from services.detail_scraper import DetailScraper
from services.gemini_service import GeminiService
from config.source_registry import SourceRegistry


async def diagnostic_data_complete(test_url: str, source_name: str = "emploi_tg"):
    """
    Diagnostic complet avec affichage des données raw_markdown et structured_json.
    
    Args:
        test_url: URL à tester
        source_name: Nom de la source
    """
    print("=" * 100)
    print("🔍 DIAGNOSTIC COMPLET - DONNÉES RAW_MARKDOWN + STRUCTURED_JSON")
    print("=" * 100)
    print(f"🎯 URL: {test_url}")
    print(f"📍 Source: {source_name}")
    print()
    
    try:
        # Initialize services
        detail_scraper = DetailScraper()
        gemini_service = GeminiService()
        
        print("✅ Services initialisés")
        print()
        
        # ÉTAPE 1: Extraction Jina Reader (raw_markdown)
        print("📋 ÉTAPE 1: EXTRACTION JINA READER (RAW_MARKDOWN)")
        print("-" * 60)
        
        start_time = time.time()
        job_data = await detail_scraper.extract_job_data(test_url, source_name)
        jina_time = time.time() - start_time
        
        if not job_data:
            print("❌ Échec extraction Jina Reader")
            return
        
        # Récupérer le contenu brut
        raw_data = job_data.get('raw_data', {})
        raw_markdown = raw_data.get('content', '')
        
        print(f"✅ Extraction réussie en {jina_time:.2f}s")
        print(f"📊 Taille du contenu: {len(raw_markdown)} caractères")
        print()
        print("📝 CONTENU RAW_MARKDOWN:")
        print("=" * 80)
        print(raw_markdown[:2000] + "..." if len(raw_markdown) > 2000 else raw_markdown)
        print("=" * 80)
        print()
        
        # ÉTAPE 2: Structuration Gemini (structured_json)
        print("📋 ÉTAPE 2: STRUCTURATION GEMINI (STRUCTURED_JSON)")
        print("-" * 60)
        
        start_time = time.time()
        structured_data = await gemini_service.structure_job_data(raw_markdown, test_url, source_name)
        gemini_time = time.time() - start_time
        
        if structured_data:
            print(f"✅ Structuration réussie en {gemini_time:.2f}s")
            print()
            print("🔧 DONNÉES STRUCTURED_JSON:")
            print("=" * 80)
            print(json.dumps(structured_data, indent=2, ensure_ascii=False))
            print("=" * 80)
            print()
        else:
            print("❌ Échec structuration Gemini")
            print()
        
        # ÉTAPE 3: Format dual complet
        print("📋 ÉTAPE 3: FORMAT DUAL COMPLET {raw_markdown, structured_json}")
        print("-" * 60)
        
        dual_format = {
            "url": test_url,
            "source_site": source_name,
            "raw_markdown": raw_markdown,
            "structured_json": structured_data,
            "extraction_success": True,
            "structuring_success": bool(structured_data),
            "processing_times": {
                "jina_seconds": round(jina_time, 2),
                "gemini_seconds": round(gemini_time, 2),
                "total_seconds": round(jina_time + gemini_time, 2)
            },
            "metadata": {
                "raw_content_length": len(raw_markdown),
                "structured_fields_count": len(structured_data) if structured_data else 0,
                "extraction_timestamp": time.time()
            }
        }
        
        print("🎯 FORMAT DUAL COMPLET:")
        print("=" * 80)
        # Afficher le format dual mais limiter le raw_markdown pour la lisibilité
        display_format = dual_format.copy()
        if len(display_format["raw_markdown"]) > 500:
            display_format["raw_markdown"] = display_format["raw_markdown"][:500] + f"... [TRONQUÉ - {len(dual_format['raw_markdown'])} caractères total]"
        
        print(json.dumps(display_format, indent=2, ensure_ascii=False))
        print("=" * 80)
        print()
        
        # ÉTAPE 4: Analyse comparative
        print("📋 ÉTAPE 4: ANALYSE COMPARATIVE")
        print("-" * 60)
        
        # Données extraites par le detail_scraper (parsing regex)
        print("🔍 DONNÉES DETAIL_SCRAPER (Parsing Regex):")
        detail_fields = {
            "title": job_data.get('title'),
            "company": job_data.get('company'),
            "location": job_data.get('location'),
            "contract_type": job_data.get('contract_type'),
            "description": job_data.get('description', '')[:200] + "..." if job_data.get('description') else None
        }
        print(json.dumps(detail_fields, indent=2, ensure_ascii=False))
        print()
        
        # Données extraites par Gemini (IA)
        if structured_data:
            print("🤖 DONNÉES GEMINI (IA Structurée):")
            gemini_fields = {
                "title": structured_data.get('title'),
                "company": structured_data.get('company'),
                "location": structured_data.get('location'),
                "contract_type": structured_data.get('contract_type'),
                "salary_range": structured_data.get('salary_range'),
                "missions": structured_data.get('missions', [])[:3] if structured_data.get('missions') else [],
                "required_skills": structured_data.get('required_skills', [])[:3] if structured_data.get('required_skills') else []
            }
            print(json.dumps(gemini_fields, indent=2, ensure_ascii=False))
            print()
        
        # ÉTAPE 5: Métriques de qualité
        print("📋 ÉTAPE 5: MÉTRIQUES DE QUALITÉ")
        print("-" * 60)
        
        quality_metrics = {
            "extraction_success": True,
            "structuring_success": bool(structured_data),
            "data_completeness": {
                "detail_scraper_fields": sum(1 for v in detail_fields.values() if v),
                "gemini_fields": sum(1 for v in gemini_fields.values() if v) if structured_data else 0,
                "raw_content_quality": "excellent" if len(raw_markdown) > 10000 else "good" if len(raw_markdown) > 5000 else "limited"
            },
            "performance": {
                "jina_speed": "excellent" if jina_time < 5 else "good" if jina_time < 10 else "slow",
                "gemini_speed": "excellent" if gemini_time < 10 else "good" if gemini_time < 20 else "slow",
                "total_time": round(jina_time + gemini_time, 2)
            }
        }
        
        print("📊 MÉTRIQUES DE QUALITÉ:")
        print(json.dumps(quality_metrics, indent=2, ensure_ascii=False))
        print()
        
        print("=" * 100)
        print("✅ DIAGNOSTIC COMPLET TERMINÉ")
        print("=" * 100)
        
        return dual_format
        
    except Exception as e:
        print(f"❌ Erreur critique: {str(e)}")
        import traceback
        traceback.print_exc()
        return None


async def main():
    """Point d'entrée principal."""
    # URL de test par défaut
    test_url = "https://www.emploi.tg/offre-emploi-togo/conseiller-clientele-bilingue-lome-326684"
    
    # Permettre de passer une URL en argument
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    
    source_name = "emploi_tg"
    if len(sys.argv) > 2:
        source_name = sys.argv[2]
    
    await diagnostic_data_complete(test_url, source_name)


if __name__ == "__main__":
    asyncio.run(main())