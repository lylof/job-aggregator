#!/usr/bin/env python3
"""
DIAGNOSTIC STAGE 2 SEUL - Test isolé de l'extraction de contenu détaillé
Objectif : Vérifier si Stage 2 fonctionne avec une URL propre de Stage 1
"""

import asyncio
import sys
import os
from typing import Dict, List, Any
from datetime import datetime

# Ajouter le chemin du projet
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from jinascraper.services.detail_scraper import DetailScraper
from jinascraper.services.gemini_service import GeminiService
from jinascraper.config.source_registry import SourceRegistry
from jinascraper.utils.enhanced_logger import create_logger

class Stage2DiagnosticTool:
    """Outil de diagnostic pour tester uniquement Stage 2"""
    
    def __init__(self):
        self.enhanced_logger = create_logger(verbose=True, quiet=False, use_colors=True, show_urls=3)
        
    async def test_stage2_with_clean_url(self, test_url: str, source_name: str = "emploi_tg") -> Dict[str, Any]:
        """Test Stage 2 avec une URL propre de Stage 1"""
        
        print("=" * 80)
        print("🔍 DIAGNOSTIC STAGE 2 SEUL - EXTRACTION DE CONTENU DÉTAILLÉ")
        print("=" * 80)
        print(f"⏰ Début du test : {datetime.now().strftime('%H:%M:%S')}")
        print(f"🎯 URL de test : {test_url}")
        print(f"📍 Source : {source_name}")
        print()
        
        try:
            # 1. Initialisation des services
            print("📋 ÉTAPE 1 : Initialisation des services Stage 2")
            
            source_registry = SourceRegistry()
            detail_scraper = DetailScraper()
            gemini_service = GeminiService()
            
            # Récupérer la configuration de la source
            source_config = source_registry.get_source_config(source_name)
            if not source_config:
                print(f"❌ Configuration manquante pour {source_name}")
                return {'error': f'Configuration manquante pour {source_name}'}
            
            print(f"✅ Services initialisés")
            print(f"✅ Configuration source récupérée : {source_name}")
            
            # 2. Test extraction de contenu via Jina Reader
            print("\n📋 ÉTAPE 2 : Test extraction de contenu (Jina Reader)")
            print("-" * 50)
            
            try:
                print(f"⏳ Extraction du contenu de : {test_url}")
                
                # Extraire le contenu brut avec Jina Reader
                job_data = await detail_scraper.extract_job_data(test_url, source_config)
                
                if job_data:
                    print(f"✅ Contenu extrait avec succès")
                    print(f"📊 Méthode d'extraction : {job_data.extraction_method}")
                    print(f"📝 Titre : {job_data.title or 'Non extrait'}")
                    print(f"🏢 Entreprise : {job_data.company or 'Non extrait'}")
                    print(f"📍 Localisation : {job_data.location or 'Non extrait'}")
                    print(f"📄 Description (extrait) : {(job_data.description or '')[:200]}...")
                    
                    # 3. Test enrichissement IA (Gemini)
                    print("\n📋 ÉTAPE 3 : Test enrichissement IA (Gemini)")
                    print("-" * 50)
                    
                    try:
                        print("⏳ Enrichissement des données via Gemini...")
                        
                        # Enrichir les données avec Gemini
                        enriched_data = await gemini_service.enrich_job_data(job_data)
                        
                        if enriched_data:
                            print("✅ Enrichissement réussi")
                            print(f"📊 Données enrichies disponibles")
                            
                            # Comparer avant/après enrichissement
                            print("\n📋 COMPARAISON AVANT/APRÈS ENRICHISSEMENT :")
                            print(f"   Titre : {job_data.title} → {enriched_data.title}")
                            print(f"   Entreprise : {job_data.company} → {enriched_data.company}")
                            print(f"   Localisation : {job_data.location} → {enriched_data.location}")
                            
                            return {
                                'stage2_success': True,
                                'jina_extraction': 'success',
                                'gemini_enrichment': 'success',
                                'original_data': job_data,
                                'enriched_data': enriched_data
                            }
                        else:
                            print("❌ Échec de l'enrichissement Gemini")
                            return {
                                'stage2_success': False,
                                'jina_extraction': 'success',
                                'gemini_enrichment': 'failed',
                                'original_data': job_data,
                                'error': 'Gemini enrichment failed'
                            }
                            
                    except Exception as e:
                        print(f"❌ Erreur Gemini : {str(e)}")
                        return {
                            'stage2_success': False,
                            'jina_extraction': 'success',
                            'gemini_enrichment': 'error',
                            'original_data': job_data,
                            'error': f'Gemini error: {str(e)}'
                        }
                else:
                    print("❌ Aucun contenu extrait par Jina Reader")
                    return {
                        'stage2_success': False,
                        'jina_extraction': 'failed',
                        'error': 'No content extracted by Jina Reader'
                    }
                    
            except Exception as e:
                print(f"❌ Erreur lors de l'extraction Jina : {str(e)}")
                return {
                    'stage2_success': False,
                    'jina_extraction': 'error',
                    'error': f'Jina extraction error: {str(e)}'
                }
                
        except Exception as e:
            print(f"❌ ERREUR CRITIQUE : {str(e)}")
            return {'error': str(e)}
    
    def generate_stage2_report(self, results: Dict[str, Any], test_url: str) -> None:
        """Générer un rapport de diagnostic pour Stage 2"""
        
        print("\n" + "=" * 80)
        print("📊 RAPPORT DIAGNOSTIC STAGE 2 - EXTRACTION DE CONTENU")
        print("=" * 80)
        
        if 'error' in results:
            print(f"❌ ERREUR CRITIQUE: {results['error']}")
            return
        
        # Statut global
        stage2_success = results.get('stage2_success', False)
        jina_status = results.get('jina_extraction', 'unknown')
        gemini_status = results.get('gemini_enrichment', 'unknown')
        
        print(f"🎯 URL testée: {test_url}")
        print(f"✅ Stage 2 global: {'✅ SUCCÈS' if stage2_success else '❌ ÉCHEC'}")
        print(f"📊 Jina Reader: {'✅ OK' if jina_status == 'success' else '❌ ÉCHEC'}")
        print(f"🤖 Gemini IA: {'✅ OK' if gemini_status == 'success' else '❌ ÉCHEC'}")
        
        # Diagnostic et recommandations
        print(f"\n🔧 DIAGNOSTIC ET RECOMMANDATIONS:")
        print("-" * 50)
        
        if jina_status == 'failed':
            print("❌ PROBLÈME CRITIQUE: Jina Reader ne peut pas extraire le contenu")
            print("🔧 ACTION: Vérifier les paramètres Jina pour Stage 2")
            print("   - Vérifier les sélecteurs CSS")
            print("   - Vérifier les timeouts")
            print("   - Tester manuellement l'URL")
            
        elif jina_status == 'error':
            print("❌ PROBLÈME CRITIQUE: Erreur technique Jina Reader")
            print("🔧 ACTION: Vérifier la connectivité et la configuration API")
            
        elif gemini_status == 'failed':
            print("⚠️  PROBLÈME PARTIEL: Jina OK mais Gemini échoue")
            print("🔧 ACTION: Vérifier la configuration Gemini")
            print("   - Vérifier la clé API Gemini")
            print("   - Vérifier les prompts d'enrichissement")
            
        elif gemini_status == 'error':
            print("⚠️  PROBLÈME PARTIEL: Erreur technique Gemini")
            print("🔧 ACTION: Vérifier la connectivité Gemini API")
            
        else:
            print("✅ STAGE 2 FONCTIONNE CORRECTEMENT")
            print("🎯 PROCHAINE ÉTAPE: Intégrer Stage 1 + Stage 2 dans le workflow complet")
        
        print("=" * 80)

async def main():
    """Fonction principale de diagnostic Stage 2"""
    
    # URL de test propre obtenue du diagnostic Stage 1
    test_url = "https://www.emploi.tg/offre-emploi-togo/conseiller-clientele-bilingue-lome-326684"
    
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
        print(f"🎯 URL de test spécifiée : {test_url}")
    else:
        print(f"🎯 URL de test par défaut : {test_url}")
    
    diagnostic = Stage2DiagnosticTool()
    results = await diagnostic.test_stage2_with_clean_url(test_url)
    
    # Générer le rapport
    diagnostic.generate_stage2_report(results, test_url)
    
    # Résumé exécutif
    if 'error' not in results:
        stage2_works = results.get('stage2_success', False)
        print(f"\n🎯 RÉSUMÉ EXÉCUTIF :")
        print(f"   • Stage 2 fonctionne : {'✅ OUI' if stage2_works else '❌ NON'}")
        
        if stage2_works:
            print(f"   • Jina Reader : ✅ Extraction réussie")
            print(f"   • Gemini IA : ✅ Enrichissement réussi")
            print(f"\n✅ PROCHAINE ÉTAPE : Intégrer Stage 1 + Stage 2")
        else:
            jina_status = results.get('jina_extraction', 'unknown')
            if jina_status != 'success':
                print(f"\n🚨 PROCHAINE ÉTAPE : Corriger la configuration Jina pour Stage 2")
            else:
                print(f"\n🚨 PROCHAINE ÉTAPE : Corriger la configuration Gemini")

if __name__ == "__main__":
    asyncio.run(main())