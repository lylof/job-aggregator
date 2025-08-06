#!/usr/bin/env python3
"""Test du système de filtrage temporel."""

import asyncio
import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour les imports
sys.path.insert(0, str(Path(__file__).parent))

from services.temporal_filter import TemporalFilterService
from services.cache_manager import CacheManager
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

async def test_temporal_filter():
    """Test complet du système de filtrage temporel."""
    
    print("🧪 TEST DU SYSTÈME DE FILTRAGE TEMPOREL")
    print("=" * 50)
    
    try:
        # 1. Initialiser le cache manager
        print("\n1️⃣ Initialisation du cache manager...")
        cache_manager = CacheManager()
        await cache_manager.__aenter__()
        
        # 2. Créer le service de filtrage
        print("2️⃣ Création du service de filtrage temporel...")
        temporal_filter = TemporalFilterService(cache_manager=cache_manager)
        
        # 3. Test avec contenu emploi.tg réaliste
        print("3️⃣ Test avec contenu emploi.tg...")
        
        test_content = """
        DÉVELOPPEUR PYTHON SENIOR
        
        Entreprise: TechCorp Togo
        Localisation: Lomé, Togo
        
        Description du poste:
        Nous recherchons un développeur Python expérimenté...
        
        Profil recherché:
        - 5+ années d'expérience en Python
        - Connaissance de Django/FastAPI
        - Expérience avec PostgreSQL
        
        Publiée le 05.08.2025
        Date limite: 20.08.2025
        
        Contact: recrutement@techcorp.tg
        """
        
        test_url = "https://www.emploi.tg/offre-emploi-togo/dev-python-senior-123"
        
        # 4. Test mode normal (recent-only)
        print("4️⃣ Test mode normal (recent-only)...")
        temporal_filter.configure(recent_only=True, max_age_hours=None, force_all=False)
        
        result = await temporal_filter.should_process_job(test_content, test_url, "emploi_tg")
        
        print(f"   📊 Résultat: {result}")
        print(f"   ✅ Should process: {result['should_process']}")
        print(f"   📅 Publication date: {result['publication_date']}")
        print(f"   ⏰ Age hours: {result['age_hours']}")
        print(f"   🔍 Filter reason: {result['filter_reason']}")
        
        # 5. Test mode force-all
        print("\n5️⃣ Test mode force-all...")
        temporal_filter.configure(recent_only=False, max_age_hours=None, force_all=True)
        
        result_force = await temporal_filter.should_process_job(test_content, test_url, "emploi_tg")
        
        print(f"   📊 Résultat: {result_force}")
        print(f"   ✅ Should process: {result_force['should_process']}")
        print(f"   🔍 Filter reason: {result_force['filter_reason']}")
        
        # 6. Test mode max-age-hours
        print("\n6️⃣ Test mode max-age-hours (2h)...")
        temporal_filter.configure(recent_only=False, max_age_hours=2, force_all=False)
        
        result_max_age = await temporal_filter.should_process_job(test_content, test_url, "emploi_tg")
        
        print(f"   📊 Résultat: {result_max_age}")
        print(f"   ✅ Should process: {result_max_age['should_process']}")
        print(f"   ⏰ Age hours: {result_max_age['age_hours']}")
        print(f"   🔍 Filter reason: {result_max_age['filter_reason']}")
        
        # 7. Test parsing de dates
        print("\n7️⃣ Test parsing de différents formats de dates...")
        
        date_formats = [
            "Publiée le 05.08.2025",
            "Publié le 04.08.2025", 
            "Posté le 03.08.2025",
            "Créé le 02.08.2025",
            "Date: 01.08.2025"
        ]
        
        for date_format in date_formats:
            test_content_date = f"Job description...\n{date_format}\nMore content..."
            parsed_date = temporal_filter._parse_emploi_tg_date(test_content_date)
            print(f"   📅 '{date_format}' → {parsed_date}")
        
        # 8. Test mise à jour timestamp
        print("\n8️⃣ Test mise à jour timestamp...")
        await temporal_filter.update_last_scraping_timestamp("emploi_tg")
        print("   ✅ Timestamp mis à jour")
        
        # 9. Vérifier le timestamp
        cutoff_time = await temporal_filter._get_cutoff_time("emploi_tg")
        print(f"   ⏰ Cutoff time: {cutoff_time}")
        
        print("\n🎉 TOUS LES TESTS RÉUSSIS !")
        
        # Cleanup
        await cache_manager.__aexit__(None, None, None)
        
    except Exception as e:
        logger.error("Erreur pendant les tests", error=str(e))
        print(f"\n❌ ERREUR: {e}")
        return False
    
    return True

async def test_cli_integration():
    """Test d'intégration avec le CLI."""
    
    print("\n🔧 TEST D'INTÉGRATION CLI")
    print("=" * 30)
    
    print("Commandes à tester manuellement :")
    print("1️⃣ Mode normal (pas de filtrage):")
    print("   python cli.py scrape --sources emploi_tg --max-urls 3 --verbose")
    
    print("\n2️⃣ Mode recent-only (filtrage intelligent):")
    print("   python cli.py scrape --sources emploi_tg --max-urls 3 --recent-only --verbose")
    
    print("\n3️⃣ Mode max-age-hours (2 heures):")
    print("   python cli.py scrape --sources emploi_tg --max-urls 3 --max-age-hours 2 --verbose")
    
    print("\n4️⃣ Mode force-all (ignorer filtrage):")
    print("   python cli.py scrape --sources emploi_tg --max-urls 3 --force-all --verbose")
    
    print("\n💡 Observe les logs pour voir le filtrage en action !")

if __name__ == "__main__":
    print("🚀 DÉMARRAGE DES TESTS DE FILTRAGE TEMPOREL")
    
    # Test du service
    success = asyncio.run(test_temporal_filter())
    
    if success:
        # Test d'intégration CLI
        asyncio.run(test_cli_integration())
    else:
        print("❌ Tests échoués")
        sys.exit(1)