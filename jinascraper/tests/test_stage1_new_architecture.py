"""
Test principal pour l'Étape 1 (Exploration) utilisant la nouvelle architecture de configuration.
Ce script teste l'extraction des URLs d'offres d'emploi à partir des pages de listing
pour toutes les sources configurées dans le registre.
"""

import asyncio
import json
import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

# Ajouter le répertoire parent au path pour pouvoir importer les modules
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from jinascraper.config import SourceRegistry, JINA_BASE_CONFIG
from jinascraper.services import JinaClient, ListingScraper
from jinascraper.services.url_cleaner import clean_urls_by_source


async def test_source(
    listing_scraper: ListingScraper,
    source_id: str,
    verbose: bool = True
) -> Dict[str, Any]:
    """
    Teste l'extraction des URLs d'offres d'emploi pour une source spécifique.
    
    Args:
        listing_scraper: Service ListingScraper
        source_id: Identifiant de la source à tester
        verbose: Afficher les détails du test
        
    Returns:
        Résultats du test
    """
    # Récupérer la configuration de la source
    source_config = SourceRegistry.get_source(source_id)
    if not source_config:
        print(f"❌ Source {source_id} non trouvée dans le registre")
        return {
            "source_id": source_id,
            "success": False,
            "error": "Source non trouvée dans le registre",
            "urls": []
        }
    
    if verbose:
        print(f"\n📍 Test de la source: {source_config.name}")
        print(f"   URL: {source_config.listing_url}")
        print(f"   Type: {source_config.source_type.value}")
    
    try:
        # Obtenir les paramètres Jina spécifiques à la source
        jina_params = source_config.get_jina_params(JINA_BASE_CONFIG)
        
        if verbose:
            print(f"   Paramètres Jina: {len(jina_params)} paramètres configurés")
            if "css_selector_only" in jina_params:
                print(f"   Sélecteur CSS: {jina_params['css_selector_only']}")
        
        # Extraire les URLs d'offres d'emploi
        start_time = datetime.now()
        
        # Utiliser la méthode extract_job_urls avec les paramètres spécifiques à la source
        urls = await listing_scraper.extract_job_urls(
            source_config.listing_url,
            source_name=source_id
        )
        
        # Nettoyer les URLs avec le nettoyeur spécifique à la source
        cleaned_urls = clean_urls_by_source(urls, source_id)
        
        duration = (datetime.now() - start_time).total_seconds()
        
        if verbose:
            print(f"   ✅ Extraction réussie en {duration:.2f}s")
            print(f"   URLs brutes: {len(urls)}")
            print(f"   URLs nettoyées: {len(cleaned_urls)}")
            
            if len(cleaned_urls) > 0:
                print(f"   Exemple: {cleaned_urls[0]}")
        
        return {
            "source_id": source_id,
            "source_name": source_config.name,
            "success": True,
            "urls_count": len(cleaned_urls),
            "raw_urls_count": len(urls),
            "duration_seconds": duration,
            "urls": cleaned_urls[:10]  # Limiter à 10 URLs pour la lisibilité
        }
        
    except Exception as e:
        if verbose:
            print(f"   ❌ Erreur: {str(e)}")
        
        return {
            "source_id": source_id,
            "source_name": source_config.name if source_config else source_id,
            "success": False,
            "error": str(e),
            "urls": []
        }


async def test_all_sources(verbose: bool = True) -> Dict[str, Any]:
    """
    Teste l'extraction des URLs d'offres d'emploi pour toutes les sources actives.
    
    Args:
        verbose: Afficher les détails du test
        
    Returns:
        Résultats du test pour toutes les sources
    """
    if verbose:
        print("🚀 TEST ÉTAPE 1 (EXPLORATION) - NOUVELLE ARCHITECTURE")
        print("=" * 60)
    
    # Récupérer toutes les sources actives
    sources = SourceRegistry.get_active_sources()
    source_ids = list(sources.keys())
    
    if verbose:
        print(f"Sources actives: {len(source_ids)}")
        for source_id, source_config in sources.items():
            status = "🟢" if not source_config.disabled else "🔴"
            print(f"  {status} {source_id}: {source_config.name}")
    
    # Créer les services nécessaires
    async with JinaClient() as jina_client:
        async with ListingScraper(jina_client) as listing_scraper:
            # Tester chaque source séquentiellement
            results = {}
            for source_id in source_ids:
                result = await test_source(listing_scraper, source_id, verbose)
            results[source_id] = result
    
    # Calculer les statistiques
    success_count = sum(1 for r in results.values() if r["success"])
    total_urls = sum(r.get("urls_count", 0) for r in results.values())
    
    if verbose:
        print("\n" + "=" * 60)
        print("RÉSUMÉ")
        print("=" * 60)
        print(f"Sources testées: {len(source_ids)}")
        print(f"Sources réussies: {success_count}/{len(source_ids)}")
        print(f"URLs totales: {total_urls}")
        
        # Afficher les résultats par source
        for source_id, result in results.items():
            status = "✅" if result["success"] else "❌"
            urls_count = result.get("urls_count", 0)
            print(f"{status} {source_id}: {urls_count} URLs")
    
    # Créer le rapport complet
    report = {
        "timestamp": datetime.now().isoformat(),
        "sources_tested": len(source_ids),
        "sources_successful": success_count,
        "total_urls": total_urls,
        "results": results
    }
    
    return report


async def save_report(report: Dict[str, Any], output_dir: str = "jinascraper/test_reports") -> str:
    """
    Sauvegarde le rapport de test dans un fichier JSON.
    
    Args:
        report: Rapport de test
        output_dir: Répertoire de sortie
        
    Returns:
        Chemin du fichier de rapport
    """
    # Créer le répertoire de sortie s'il n'existe pas
    os.makedirs(output_dir, exist_ok=True)
    
    # Générer le nom du fichier
    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M")
    filename = f"{timestamp}_stage1_new_architecture.json"
    filepath = os.path.join(output_dir, filename)
    
    # Sauvegarder le rapport
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, indent=2, ensure_ascii=False)
    
    print(f"\nRapport sauvegardé: {filepath}")
    return filepath


async def main():
    """Point d'entrée principal."""
    report = await test_all_sources(verbose=True)
    await save_report(report)
    
    # Retourner 0 si tous les tests ont réussi, sinon 1
    success = report["sources_successful"] == report["sources_tested"]
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)