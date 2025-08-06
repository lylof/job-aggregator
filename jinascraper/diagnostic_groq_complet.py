#!/usr/bin/env python3
"""
DIAGNOSTIC COMPLET ET POINTILLEUX - PROBLÈME GROQ
=================================================

Ce script diagnostique précisément pourquoi Groq n'apparaît pas dans les logs CLI.
Basé sur les recherches approfondies et l'analyse du code.
"""

import os
import sys
import traceback
import importlib.util
from pathlib import Path

def print_section(title):
    """Affiche une section avec style."""
    print(f"\n{'='*60}")
    print(f"🔍 {title}")
    print('='*60)

def test_groq_package():
    """Test 1: Vérifier le package groq."""
    print_section("TEST 1: PACKAGE GROQ")
    
    try:
        import groq
        from groq import AsyncGroq
        print("✅ Package groq importé avec succès")
        print(f"   Version: {getattr(groq, '__version__', 'inconnue')}")
        print(f"   Localisation: {groq.__file__}")
        
        # Test création client
        api_key = os.getenv("GROQ_API_KEY", "")
        if api_key:
            client = AsyncGroq(api_key=api_key)
            print("✅ Client AsyncGroq créé avec succès")
            print(f"   Clé API (derniers 10 chars): ...{api_key[-10:]}")
        else:
            print("❌ GROQ_API_KEY non trouvée dans l'environnement")
            
        return True
    except ImportError as e:
        print(f"❌ Erreur import groq: {e}")
        return False
    except Exception as e:
        print(f"❌ Erreur création client: {e}")
        return False

def test_imports_relatifs():
    """Test 2: Tester les imports relatifs problématiques."""
    print_section("TEST 2: IMPORTS RELATIFS")
    
    # Test import config
    try:
        # Méthode 1: Import relatif
        print("🔧 Test import relatif: from ..config import config")
        spec = importlib.util.spec_from_file_location("groq_service", "services/groq_service.py")
        if spec and spec.loader:
            module = importlib.util.module_from_spec(spec)
            # Simuler l'environnement d'import
            sys.modules['groq_service'] = module
            spec.loader.exec_module(module)
            print("✅ Import relatif réussi (avec spec)")
        else:
            print("❌ Impossible de créer spec pour groq_service")
    except Exception as e:
        print(f"❌ Erreur import relatif: {e}")
        print(f"   Type: {type(e).__name__}")
        traceback.print_exc()
    
    # Test import absolu
    try:
        print("\n🔧 Test import absolu: from config.settings import config")
        from config.settings import config
        print("✅ Import absolu config réussi")
        print(f"   Groq API keys: {len(getattr(config, 'groq_api_keys', []))}")
    except Exception as e:
        print(f"❌ Erreur import absolu config: {e}")
        traceback.print_exc()
    
    # Test import models
    try:
        print("\n🔧 Test import models")
        from models import JobOffer, ExtractionMethod, ExtractionMetadata
        print("✅ Import models réussi")
    except Exception as e:
        print(f"❌ Erreur import models: {e}")
        traceback.print_exc()

def test_groq_service_initialization():
    """Test 3: Tester l'initialisation du service Groq."""
    print_section("TEST 3: INITIALISATION GROQ SERVICE")
    
    try:
        # Ajouter le chemin pour les imports
        current_dir = Path(__file__).parent
        sys.path.insert(0, str(current_dir))
        
        print("🔧 Tentative d'import GroqService...")
        
        # Import direct avec gestion d'erreur
        try:
            from services.groq_service import GroqService
            print("✅ Import GroqService réussi")
        except Exception as e:
            print(f"❌ Erreur import GroqService: {e}")
            print("🔧 Tentative avec import manuel...")
            
            # Import manuel avec spec
            spec = importlib.util.spec_from_file_location(
                "groq_service", 
                current_dir / "services" / "groq_service.py"
            )
            if spec and spec.loader:
                groq_module = importlib.util.module_from_spec(spec)
                
                # Mock des dépendances problématiques
                import types
                mock_config = types.SimpleNamespace()
                mock_config.groq_api_keys = [os.getenv("GROQ_API_KEY", "")]
                mock_config.groq_api_key = os.getenv("GROQ_API_KEY", "")
                
                # Injecter les mocks
                sys.modules['config'] = types.SimpleNamespace(config=mock_config)
                sys.modules['models'] = types.SimpleNamespace(
                    JobOffer=object,
                    ExtractionMethod=types.SimpleNamespace(GROQ="groq"),
                    ExtractionMetadata=object
                )
                
                spec.loader.exec_module(groq_module)
                GroqService = groq_module.GroqService
                print("✅ Import GroqService réussi (avec mocks)")
            else:
                raise ImportError("Impossible de créer spec pour groq_service")
        
        # Test initialisation
        print("\n🔧 Tentative d'initialisation GroqService...")
        groq_service = GroqService()
        print("✅ GroqService initialisé avec succès")
        print(f"   Modèles: {groq_service.models}")
        print(f"   Clés configurées: {len(groq_service.api_keys)}")
        print(f"   Modèle sélectionné: {groq_service._select_best_model()}")
        
        return True
        
    except Exception as e:
        print(f"❌ Erreur initialisation GroqService: {e}")
        print(f"   Type: {type(e).__name__}")
        traceback.print_exc()
        return False

def test_detail_scraper_integration():
    """Test 4: Tester l'intégration dans DetailScraper."""
    print_section("TEST 4: INTÉGRATION DETAIL SCRAPER")
    
    try:
        print("🔧 Simulation du lazy loading dans DetailScraper...")
        
        # Simuler le code exact du detail_scraper
        groq_service = None
        
        if groq_service is None:
            try:
                print("   Tentative: from .groq_service import GroqService")
                # Simuler l'import local
                from services.groq_service import GroqService
                groq_service = GroqService()
                print("✅ Lazy loading Groq réussi")
                print(f"   Service créé: {type(groq_service).__name__}")
            except Exception as e:
                print(f"❌ Lazy loading Groq échoué: {e}")
                print(f"   Type d'erreur: {type(e).__name__}")
                print("   ⚠️  Groq sera ignoré silencieusement")
                groq_service = None
        
        if groq_service is not None:
            print("✅ Groq serait utilisé dans le pipeline")
        else:
            print("❌ Groq sera ignoré - fallback vers Gemini")
            
    except Exception as e:
        print(f"❌ Erreur test intégration: {e}")
        traceback.print_exc()

def test_environment_variables():
    """Test 5: Vérifier les variables d'environnement."""
    print_section("TEST 5: VARIABLES D'ENVIRONNEMENT")
    
    # Variables Groq
    groq_key = os.getenv("GROQ_API_KEY", "")
    groq_keys = os.getenv("GROQ_API_KEYS", "")
    
    print(f"GROQ_API_KEY: {'✅ Présente' if groq_key else '❌ Absente'}")
    if groq_key:
        print(f"   Longueur: {len(groq_key)} caractères")
        print(f"   Derniers 10 chars: ...{groq_key[-10:]}")
    
    print(f"GROQ_API_KEYS: {'✅ Présente' if groq_keys else '❌ Absente'}")
    if groq_keys:
        keys_list = [k.strip() for k in groq_keys.split(",") if k.strip()]
        print(f"   Nombre de clés: {len(keys_list)}")
    
    # Variables autres
    pythonpath = os.getenv("PYTHONPATH", "")
    print(f"PYTHONPATH: {'✅ Défini' if pythonpath else '❌ Non défini'}")
    if pythonpath:
        print(f"   Valeur: {pythonpath}")

def test_sys_path():
    """Test 6: Analyser sys.path."""
    print_section("TEST 6: ANALYSE SYS.PATH")
    
    current_dir = str(Path(__file__).parent.absolute())
    print(f"Répertoire courant: {current_dir}")
    print(f"Présent dans sys.path: {'✅ Oui' if current_dir in sys.path else '❌ Non'}")
    
    print(f"\nPremiers éléments de sys.path:")
    for i, path in enumerate(sys.path[:5]):
        print(f"   {i}: {path}")
    
    # Vérifier les chemins relatifs
    services_path = Path(__file__).parent / "services"
    config_path = Path(__file__).parent / "config"
    
    print(f"\nChemin services: {services_path}")
    print(f"   Existe: {'✅ Oui' if services_path.exists() else '❌ Non'}")
    print(f"Chemin config: {config_path}")
    print(f"   Existe: {'✅ Oui' if config_path.exists() else '❌ Non'}")

def main():
    """Fonction principale du diagnostic."""
    print("🚨 DIAGNOSTIC COMPLET - PROBLÈME GROQ")
    print("=====================================")
    print("Analyse pointilleuse basée sur les recherches approfondies")
    
    # Exécuter tous les tests
    tests = [
        test_groq_package,
        test_environment_variables,
        test_sys_path,
        test_imports_relatifs,
        test_groq_service_initialization,
        test_detail_scraper_integration
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} échoué: {e}")
            results.append(False)
    
    # Résumé final
    print_section("RÉSUMÉ DIAGNOSTIC")
    passed = sum(1 for r in results if r)
    total = len(results)
    
    print(f"Tests réussis: {passed}/{total}")
    
    if passed == total:
        print("✅ Tous les tests passent - Groq devrait fonctionner")
    elif passed >= total // 2:
        print("⚠️  Problèmes partiels détectés - Groq peut être instable")
    else:
        print("❌ Problèmes majeurs détectés - Groq ne fonctionnera pas")
    
    print("\n🎯 RECOMMANDATIONS:")
    print("1. Vérifier les imports relatifs dans groq_service.py")
    print("2. S'assurer que GROQ_API_KEY est définie")
    print("3. Tester l'initialisation isolée du service")
    print("4. Vérifier les logs de warning dans detail_scraper.py")

if __name__ == "__main__":
    main()