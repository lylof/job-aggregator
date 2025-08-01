#!/usr/bin/env python3
"""
DIAGNOSTIC STAGE 1 SEUL - Test isolé de l'extraction d'URLs
Objectif : Vérifier si Stage 1 fonctionne correctement sans Stage 2
"""

import asyncio
import sys
import os
from typing import Dict, List, Any
from datetime import datetime

# Ajouter le chemin du projet
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jinascraper.core.orchestrator import ScrapingOrchestrator
from jinascraper.config.source_registry import SourceRegistry
from jinascraper.services.cache_manager import CacheManager
from jinascraper.utils.enhanced_logger import EnhancedLogger

class Stage1DiagnosticTool:
    """Outil de diagnostic pour tester uniquement Stage 1"""
    
    def __init__(self):
        self.logger = EnhancedLogger()
        self.results = {}
        
    async def test_stage1_only(self, source_names: List[str] = None) -> Dict[str, Any]:
        """Test Stage 1 uniquement pour diagnostiquer l'extraction d'URLs"""
        
        print("=" * 80)
        print("🔍 DIAGNOSTIC STAGE 1 SEUL - EXTRACTION D'URLS")
        print("=" * 80)
        print(f"⏰ Début du test : {datetime.now().strftime('%H:%M:%S')}")
        print()
        
        try:
            # 1. Initialisation des composants
            print("📋 ÉTAPE 1 : Initialisation des composants")
            source_registry = SourceRegistry()
            cache_manager = CacheManager()
            
            # Afficher les sources disponibles
            available_sources = list(source_registry.get_all_sources().keys())
            print(f"✅ Sources disponibles : {available_sources}")
            
            # Filtrer les sources si spécifié
            if source_names:
                test_sources = [s for s in source_names if s in available_sources]
                print(f"🎯 Sources à tester : {test_sources}")
            else:
                test_sources = available_sources[:2]  # Tester seulement 2 sources
                print(f"🎯 Test automatique sur : {test_sources}")
            
            print()
            
            # 2. Test d'extraction pour chaque source
            print("📋 ÉTAPE 2 : Test d'extraction par source")
            print("-" * 50)
            
            total_urls = 0
            source_results = {}
            
            for source_name in test_sources:
                print(f"\n🔍 Test source : {source_name}")
                print("-" * 30)
                
                try:
                    # Récupérer la configuration de la source
                    source_config = source_registry.get_source_config(source_name)
                    if not source_config:
                        print(f"❌ Configuration manquante pour {source_name}")
                        continue
                    
                    print(f"📍 URL de listing : {source_config.base.listing_url}")
                    print(f"🎯 Patterns attendus : {len(source_config.base.url_patterns)}")
                    
                    # Créer l'orchestrateur pour cette source
                    orchestrator = ScrapingOrchestrator(
                        source_registry=source_registry,
                        cache_manager=cache_manager
                    )
                    
                    # Tester l'extraction d'URLs (Stage 1 seulement)
                    print("⏳ Extraction des URLs en cours...")
                    
                    # Simuler l'extraction Stage 1
                    urls = await self._extract_urls_for_source(orchestrator, source_name)
                    
                    if urls:
                        print(f"✅ URLs extraites : {len(urls)}")
                        print("📋 Exemples d'URLs :")
                        for i, url in enumerate(urls[:3]):  # Afficher 3 exemples
                            print(f"   {i+1}. {url}")
                        
                        # Vérifier la qualité des URLs
                        clean_urls = [url for url in urls if self._is_url_clean(url)]
                        malformed_urls = len(urls) - len(clean_urls)
                        
                        if malformed_urls > 0:
                            print(f"⚠️  URLs malformées détectées : {malformed_urls}")
                            print("📋 Exemples d'URLs problématiques :")
                            for url in urls:
                                if not self._is_url_clean(url):
                                    print(f"   ❌ {url}")
                                    break
                        
                        source_results[source_name] = {
                            'status': 'success',
                            'urls_found': len(urls),
                            'clean_urls': len(clean_urls),
                            'malformed_urls': malformed_urls,
                            'sample_urls': urls[:3]
                        }
                        total_urls += len(urls)
                        
                    else:
                        print("❌ Aucune URL extraite")
                        source_results[source_name] = {
                            'status': 'failed',
                            'urls_found': 0,
                            'error': 'No URLs extracted'
                        }
                        
                except Exception as e:
                    print(f"❌ Erreur lors du test de {source_name}: {str(e)}")
                    source_results[source_name] = {
                        'status': 'error',
                        'error': str(e)
                    }
            
            # 3. Rapport final
            print("\n" + "=" * 80)
            print("📊 RAPPORT FINAL - DIAGNOSTIC STAGE 1")
            print("=" * 80)
            
            successful_sources = [s for s, r in source_results.items() if r['status'] == 'success']
            failed_sources = [s for s, r in source_results.items() if r['status'] != 'success']
            
            print(f"✅ Sources fonctionnelles : {len(successful_sources)}/{len(test_sources)}")
            print(f"❌ Sources en échec : {len(failed_sources)}")
            print(f"📊 Total URLs extraites : {total_urls}")
            
            if successful_sources:
                print(f"\n🎉 Sources OK : {', '.join(successful_sources)}")
                
            if failed_sources:
                print(f"\n⚠️  Sources problématiques : {', '.join(failed_sources)}")
                print("\n🔧 PROBLÈMES IDENTIFIÉS :")
                for source in failed_sources:
                    result = source_results[source]
                    print(f"   • {source}: {result.get('error', 'Erreur inconnue')}")
            
            # Analyse des URLs malformées
            total_malformed = sum(r.get('malformed_urls', 0) for r in source_results.values())
            if total_malformed > 0:
                print(f"\n⚠️  PROBLÈME CRITIQUE : {total_malformed} URLs malformées détectées")
                print("🔧 ACTION REQUISE : Corriger les URL cleaners")
            
            print(f"\n⏰ Fin du test : {datetime.now().strftime('%H:%M:%S')}")
            print("=" * 80)
            
            return {
                'total_sources_tested': len(test_sources),
                'successful_sources': len(successful_sources),
                'failed_sources': len(failed_sources),
                'total_urls': total_urls,
                'total_malformed': total_malformed,
                'source_results': source_results
            }
            
        except Exception as e:
            print(f"❌ ERREUR CRITIQUE : {str(e)}")
            return {'error': str(e)}
    
    async def _extract_urls_for_source(self, orchestrator, source_name: str) -> List[str]:
        """Extraire les URLs pour une source spécifique"""
        try:
            # Utiliser la méthode d'extraction de l'orchestrateur
            # mais seulement pour une source
            sources = {source_name: orchestrator.source_registry.get_source_config(source_name)}
            
            # Appeler la méthode d'extraction d'URLs
            result = await orchestrator._extract_urls_from_all_sources(sources)
            
            return result.get(source_name, [])
            
        except Exception as e:
            print(f"Erreur extraction pour {source_name}: {str(e)}")
            return []
    
    def _is_url_clean(self, url: str) -> bool:
        """Vérifier si une URL est propre (sans caractères parasites)"""
        # Vérifications de base pour détecter les URLs malformées
        problematic_chars = [')', '(', '[', ']', '\\n', '\\t']
        
        for char in problematic_chars:
            if char in url:
                return False
        
        # Vérifier que l'URL commence bien par http
        if not url.startswith(('http://', 'https://')):
            return False
            
        return True

async def main():
    """Fonction principale de diagnostic"""
    
    # Permettre de spécifier des sources en argument
    if len(sys.argv) > 1:
        source_names = sys.argv[1].split(',')
        print(f"🎯 Test des sources spécifiées : {source_names}")
    else:
        source_names = None
        print("🎯 Test automatique des sources disponibles")
    
    diagnostic = Stage1DiagnosticTool()
    results = await diagnostic.test_stage1_only(source_names)
    
    # Afficher le résumé final
    if 'error' not in results:
        print(f"\n🎯 RÉSUMÉ EXÉCUTIF :")
        print(f"   • Stage 1 fonctionne : {'✅ OUI' if results['successful_sources'] > 0 else '❌ NON'}")
        print(f"   • URLs extraites : {results['total_urls']}")
        print(f"   • URLs malformées : {results['total_malformed']}")
        
        if results['total_malformed'] > 0:
            print(f"\n🚨 PROCHAINE ÉTAPE : Corriger les URL cleaners")
        elif results['successful_sources'] > 0:
            print(f"\n✅ PROCHAINE ÉTAPE : Tester Stage 2 avec ces URLs")
        else:
            print(f"\n❌ PROCHAINE ÉTAPE : Corriger la configuration des sources")

if __name__ == "__main__":
    asyncio.run(main())