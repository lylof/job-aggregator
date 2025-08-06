#!/usr/bin/env python3
"""Test du filtrage temporel sur Stage 1 uniquement."""

import asyncio
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent))

from services.temporal_filter import TemporalFilterService
from services.cache_manager import CacheManager
from services.jina_client import JinaClient
import structlog

# Configuration du logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="%H:%M:%S"),
        structlog.dev.ConsoleRenderer()
    ],
    wrapper_class=structlog.stdlib.BoundLogger,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)

async def test_stage1_with_temporal_filtering():
    """Test Stage 1 avec simulation du filtrage temporel."""
    
    print("🧪 TEST STAGE 1 AVEC FILTRAGE TEMPOREL SIMULÉ")
    print("=" * 60)
    
    try:
        # 1. Extraire les URLs comme d'habitude (Stage 1)
        print("\n1️⃣ Extraction des URLs (Stage 1 normal)...")
        
        jina_client = JinaClient()
        
        # Paramètres pour emploi.tg
        params = {
            "gather_all_links_at_the_end": "true",
            "remove_all_images": "true", 
            "timeout": "30"
        }
        
        headers = {"X-Target-Selector": "h3 > a"}
        
        # Extraction des URLs
        response = await jina_client.make_request(
            "https://www.emploi.tg/recherche-jobs-togo",
            params,
            headers
        )
        
        content = response.get("content", "")
        
        # Parser les URLs (simulation simplifiée)
        import re
        url_pattern = r'https://www\.emploi\.tg/offre-emploi-togo/[^\s<>"\\\']+'
        urls = re.findall(url_pattern, content)
        urls = list(set(urls))  # Déduplication
        
        print(f"   ✅ URLs extraites: {len(urls)}")
        print(f"   📊 Exemples: {urls[:3]}")
        
        # 2. Simulation du filtrage temporel sur chaque URL
        print("\n2️⃣ Simulation du filtrage temporel...")
        
        cache_manager = CacheManager()
        await cache_manager.__aenter__()
        
        temporal_filter = TemporalFilterService(cache_manager=cache_manager)
        
        # Configuration en mode recent-only
        temporal_filter.configure(recent_only=True, max_age_hours=None, force_all=False)
        
        # Test de filtrage sur quelques URLs
        filtered_urls = []
        processed_urls = []
        
        for i, url in enumerate(urls[:5]):  # Tester seulement 5 URLs pour économiser
            print(f"\n   🔍 Test URL {i+1}: {url}")
            
            # Extraire le contenu de cette URL
            try:
                job_response = await jina_client.make_request(url, {"timeout": "30"})
                job_content = job_response.get("content", "")
                
                if job_content:
                    # Appliquer le filtrage temporel
                    filter_result = await temporal_filter.should_process_job(
                        job_content, url, "emploi_tg"
                    )
                    
                    processed_urls.append({
                        'url': url,
                        'should_process': filter_result['should_process'],
                        'publication_date': filter_result['publication_date'],
                        'age_hours': filter_result['age_hours'],
                        'filter_reason': filter_result['filter_reason']
                    })
                    
                    if filter_result['should_process']:
                        filtered_urls.append(url)
                        print(f"      ✅ TRAITÉ - {filter_result['filter_reason']}")
                    else:
                        print(f"      ❌ FILTRÉ - {filter_result['filter_reason']}")
                        
                    if filter_result['publication_date']:
                        print(f"      📅 Date: {filter_result['publication_date']}")
                    if filter_result['age_hours']:
                        print(f"      ⏰ Âge: {filter_result['age_hours']}h")
                else:
                    print(f"      ⚠️ Pas de contenu extrait")
                    
            except Exception as e:
                print(f"      ❌ Erreur: {e}")
        
        # 3. Résultats du filtrage
        print("\n3️⃣ Résultats du filtrage temporel...")
        
        total_tested = len(processed_urls)
        total_filtered = len([u for u in processed_urls if u['should_process']])
        total_blocked = total_tested - total_filtered
        
        print(f"   📊 URLs testées: {total_tested}")
        print(f"   ✅ URLs à traiter: {total_filtered}")
        print(f"   ❌ URLs filtrées: {total_blocked}")
        
        if total_tested > 0:
            filter_rate = (total_blocked / total_tested) * 100
            print(f"   📈 Taux de filtrage: {filter_rate:.1f}%")
            
            if filter_rate > 0:
                print(f"   💰 Économies estimées: {filter_rate:.1f}% des appels IA")
            else:
                print("   💡 Toutes les offres sont récentes - pas d'économies cette fois")
        
        # 4. Détail des résultats
        print("\n4️⃣ Détail par URL...")
        for i, result in enumerate(processed_urls, 1):
            status = "✅ TRAITÉ" if result['should_process'] else "❌ FILTRÉ"
            print(f"   {i}. {status} - {result['filter_reason']}")
            if result['publication_date']:
                print(f"      📅 {result['publication_date']} (âge: {result['age_hours']}h)")
        
        # 5. Projection sur toutes les URLs
        print("\n5️⃣ Projection sur toutes les URLs...")
        if total_tested > 0 and filter_rate > 0:
            estimated_filtered = int((len(urls) * filter_rate) / 100)
            estimated_processed = len(urls) - estimated_filtered
            
            print(f"   📊 URLs totales extraites: {len(urls)}")
            print(f"   ✅ URLs estimées à traiter: {estimated_processed}")
            print(f"   ❌ URLs estimées filtrées: {estimated_filtered}")
            print(f"   💰 Économies estimées: {filter_rate:.1f}% des appels IA")
        else:
            print(f"   📊 URLs totales extraites: {len(urls)}")
            print("   💡 Toutes les offres seraient traitées (pas d'économies)")
        
        print("\n🎉 TEST TERMINÉ AVEC SUCCÈS !")
        
        # Cleanup
        await cache_manager.__aexit__(None, None, None)
        
    except Exception as e:
        logger.error("Erreur pendant le test", error=str(e))
        print(f"\n❌ ERREUR: {e}")
        return False
    
    return True

if __name__ == "__main__":
    print("🚀 DÉMARRAGE DU TEST STAGE 1 + FILTRAGE TEMPOREL")
    
    success = asyncio.run(test_stage1_with_temporal_filtering())
    
    if not success:
        print("❌ Test échoué")
        sys.exit(1)
    else:
        print("\n✅ Test réussi - Le filtrage temporel fonctionne sur Stage 1 !")