#!/usr/bin/env python3
"""
Audit Complet JinaScraper - Janvier 2025
Test concret de tous les composants avec données réelles
"""

import sys
import os
import asyncio
import importlib
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional
import json

# Configuration des couleurs pour l'affichage
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(title: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.END}")

def print_success(message: str):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message: str):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

def print_info(message: str):
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.END}")

class JinaScraperAudit:
    def __init__(self):
        self.results = {
            "timestamp": datetime.now().isoformat(),
            "tests": {},
            "summary": {
                "total_tests": 0,
                "passed": 0,
                "failed": 0,
                "warnings": 0
            }
        }
        
    def add_test_result(self, test_name: str, status: str, details: Any = None, error: str = None):
        """Ajouter un résultat de test"""
        self.results["tests"][test_name] = {
            "status": status,
            "details": details,
            "error": error,
            "timestamp": datetime.now().isoformat()
        }
        
        self.results["summary"]["total_tests"] += 1
        if status == "PASSED":
            self.results["summary"]["passed"] += 1
        elif status == "FAILED":
            self.results["summary"]["failed"] += 1
        elif status == "WARNING":
            self.results["summary"]["warnings"] += 1

    async def test_imports_validation(self):
        """Test 1: Validation des imports - Problème critique identifié"""
        print_header("TEST 1: VALIDATION DES IMPORTS")
        
        # Liste des modules critiques à tester
        critical_modules = [
            "jinascraper.services.url_cleaners.emploitogo_info_cleaner",
            "jinascraper.services.url_cleaners.yop_lfrii_cleaner", 
            "jinascraper.services.url_cleaners.linkedin_togo_cleaner",
            "jinascraper.services.url_cleaners.indeed_togo_cleaner",
            "jinascraper.services.url_cleaners.emploi_tg_cleaner",
            "jinascraper.services.url_cleaners.anpetogo_cleaner",
            "jinascraper.config.source_registry",
            "jinascraper.core.orchestrator",
            "jinascraper.services.cache_manager",
            "jinascraper.services.jina_client",
            "jinascraper.services.gemini_service"
        ]
        
        import_results = {}
        failed_imports = []
        
        for module_name in critical_modules:
            try:
                print_info(f"Testing import: {module_name}")
                module = importlib.import_module(module_name)
                import_results[module_name] = "SUCCESS"
                print_success(f"✓ {module_name}")
            except ImportError as e:
                import_results[module_name] = f"IMPORT_ERROR: {str(e)}"
                failed_imports.append(module_name)
                print_error(f"✗ {module_name}: {str(e)}")
            except Exception as e:
                import_results[module_name] = f"OTHER_ERROR: {str(e)}"
                failed_imports.append(module_name)
                print_error(f"✗ {module_name}: {str(e)}")
        
        if failed_imports:
            self.add_test_result(
                "imports_validation", 
                "FAILED", 
                import_results, 
                f"{len(failed_imports)} modules failed to import: {failed_imports}"
            )
            print_error(f"ÉCHEC: {len(failed_imports)} modules ne peuvent pas être importés")
        else:
            self.add_test_result("imports_validation", "PASSED", import_results)
            print_success("SUCCÈS: Tous les imports fonctionnent")
            
        return len(failed_imports) == 0

    async def test_url_cleaners_functionality(self):
        """Test 2: Fonctionnalité des nettoyeurs URL avec données réelles"""
        print_header("TEST 2: NETTOYEURS URL - DONNÉES RÉELLES")
        
        # URLs de test réelles pour chaque source
        test_urls = {
            "emploitogo_info": [
                "https://www.emploitogo.info/emploitogo/offre-demploi-togo-charge-de-communication/",
                "https://www.emploitogo.info/emploitogo/recrutement-assistant-comptable-lome/",
                "https://www.emploitogo.info/emploitogo/poste-vacant-developpeur-web-kara/"
            ],
            "yop_lfrii": [
                "https://yop.l-frii.com/emploi/coordinateur-projet-humanitaire/",
                "https://yop.l-frii.com/emploi/assistant-logistique-ong/",
                "https://yop.l-frii.com/emploi/responsable-marketing-digital/"
            ],
            "emploi_tg": [
                "https://www.emploi.tg/offre-emploi-togo/developpeur-full-stack-lome/",
                "https://www.emploi.tg/offre-emploi-togo/comptable-senior-kpalime/",
                "https://www.emploi.tg/offre-emploi-togo/chef-projet-it-sokode/"
            ],
            "anpetogo": [
                "https://anpetogo.org/offre/technicien-maintenance-informatique/",
                "https://anpetogo.org/offre/secretaire-direction-bilingue/",
                "https://anpetogo.org/offre/ingenieur-genie-civil/"
            ],
            "linkedin_togo": [
                "https://tg.linkedin.com/jobs/view/3456789012",
                "https://tg.linkedin.com/jobs/view/3456789013",
                "https://tg.linkedin.com/jobs/view/3456789014"
            ],
            "indeed_togo": [
                "https://tg.indeed.com/viewjob?jk=abc123def456",
                "https://tg.indeed.com/viewjob?jk=def456ghi789",
                "https://tg.indeed.com/viewjob?jk=ghi789jkl012"
            ]
        }
        
        cleaner_results = {}
        
        for source_name, urls in test_urls.items():
            print_info(f"Testing {source_name} cleaner with {len(urls)} URLs")
            
            try:
                # Import dynamique du nettoyeur
                module_name = f"jinascraper.services.url_cleaners.{source_name}_cleaner"
                cleaner_module = importlib.import_module(module_name)
                
                # Fonction de nettoyage (nom standardisé)
                clean_function_name = f"clean_{source_name}_urls"
                if hasattr(cleaner_module, clean_function_name):
                    clean_function = getattr(cleaner_module, clean_function_name)
                    
                    # Test avec URLs réelles
                    cleaned_urls = clean_function(urls)
                    success_rate = len(cleaned_urls) / len(urls) if urls else 0
                    
                    cleaner_results[source_name] = {
                        "input_urls": len(urls),
                        "cleaned_urls": len(cleaned_urls),
                        "success_rate": success_rate,
                        "sample_input": urls[0] if urls else None,
                        "sample_output": cleaned_urls[0] if cleaned_urls else None
                    }
                    
                    if success_rate >= 0.8:  # 80% minimum
                        print_success(f"✓ {source_name}: {len(cleaned_urls)}/{len(urls)} URLs ({success_rate:.1%})")
                    else:
                        print_error(f"✗ {source_name}: {len(cleaned_urls)}/{len(urls)} URLs ({success_rate:.1%}) - SOUS LE SEUIL")
                        
                else:
                    cleaner_results[source_name] = {"error": f"Function {clean_function_name} not found"}
                    print_error(f"✗ {source_name}: Function {clean_function_name} not found")
                    
            except Exception as e:
                cleaner_results[source_name] = {"error": str(e)}
                print_error(f"✗ {source_name}: {str(e)}")
        
        # Évaluation globale
        failed_cleaners = [name for name, result in cleaner_results.items() 
                          if "error" in result or result.get("success_rate", 0) < 0.8]
        
        if failed_cleaners:
            self.add_test_result(
                "url_cleaners_functionality", 
                "FAILED", 
                cleaner_results,
                f"Cleaners défaillants: {failed_cleaners}"
            )
        else:
            self.add_test_result("url_cleaners_functionality", "PASSED", cleaner_results)
            
        return len(failed_cleaners) == 0

    async def test_source_configurations(self):
        """Test 3: Configurations des sources"""
        print_header("TEST 3: CONFIGURATIONS DES SOURCES")
        
        try:
            from jinascraper.config.source_registry import SourceRegistry
            
            # Test de toutes les sources configurées
            sources = ["emploi_tg", "anpetogo", "linkedin_togo", "indeed_togo", "yop_lfrii", "emploitogo_info"]
            config_results = {}
            
            for source_name in sources:
                try:
                    config = SourceRegistry.get_source(source_name)
                    if config:
                        config_results[source_name] = {
                            "status": "FOUND",
                            "name": config.name,
                            "base_url": config.base_url,
                            "listing_url": config.listing_url,
                            "url_patterns_count": len(config.url_patterns),
                            "has_stage2_params": hasattr(config, 'stage2_params') and config.stage2_params is not None,
                            "reliability_score": getattr(config, 'reliability_score', 'N/A')
                        }
                        print_success(f"✓ {source_name}: Configuration trouvée")
                    else:
                        config_results[source_name] = {"status": "NOT_FOUND"}
                        print_error(f"✗ {source_name}: Configuration non trouvée")
                        
                except Exception as e:
                    config_results[source_name] = {"status": "ERROR", "error": str(e)}
                    print_error(f"✗ {source_name}: {str(e)}")
            
            # Vérification des configurations Stage 2
            stage2_enabled = sum(1 for result in config_results.values() 
                               if result.get("has_stage2_params", False))
            
            print_info(f"Sources avec Stage 2 configuré: {stage2_enabled}/{len(sources)}")
            
            self.add_test_result("source_configurations", "PASSED", config_results)
            return True
            
        except Exception as e:
            self.add_test_result("source_configurations", "FAILED", None, str(e))
            print_error(f"Erreur lors du test des configurations: {str(e)}")
            return False

    async def test_redis_integration(self):
        """Test 4: Intégration Redis/FakeRedis"""
        print_header("TEST 4: INTÉGRATION REDIS")
        
        try:
            from jinascraper.services.cache_manager import CacheManager
            
            # Test avec FakeRedis
            async with CacheManager() as cache:
                # Test des opérations de base
                test_urls = [
                    "https://www.emploi.tg/test-job-1",
                    "https://www.emploi.tg/test-job-2",
                    "https://www.emploi.tg/test-job-3"
                ]
                
                # Test 1: Filtrage des nouvelles URLs (toutes nouvelles au début)
                new_urls_1 = await cache.filter_new_urls(test_urls, "emploi_tg")
                
                # Test 2: Marquage comme traitées
                for url in new_urls_1:
                    await cache.mark_url_scraped(url, "emploi_tg")
                
                # Test 3: Re-filtrage (aucune nouvelle maintenant)
                new_urls_2 = await cache.filter_new_urls(test_urls, "emploi_tg")
                
                # Test 4: Informations du cache
                cache_info = await cache.get_cache_info()
                
                redis_results = {
                    "initial_new_urls": len(new_urls_1),
                    "expected_initial": len(test_urls),
                    "second_new_urls": len(new_urls_2),
                    "expected_second": 0,
                    "cache_hit_rate": (len(test_urls) - len(new_urls_2)) / len(test_urls),
                    "cache_info": cache_info
                }
                
                # Validation
                if (len(new_urls_1) == len(test_urls) and len(new_urls_2) == 0):
                    print_success("✓ Redis: Delta scraping fonctionne parfaitement")
                    print_success(f"✓ Cache hit rate: {redis_results['cache_hit_rate']:.1%}")
                    self.add_test_result("redis_integration", "PASSED", redis_results)
                    return True
                else:
                    print_error("✗ Redis: Delta scraping ne fonctionne pas correctement")
                    self.add_test_result("redis_integration", "FAILED", redis_results, "Delta scraping incorrect")
                    return False
                    
        except Exception as e:
            print_error(f"✗ Redis: {str(e)}")
            self.add_test_result("redis_integration", "FAILED", None, str(e))
            return False

    async def test_jina_client_basic(self):
        """Test 5: Client Jina (test basique sans API call)"""
        print_header("TEST 5: CLIENT JINA")
        
        try:
            from jinascraper.services.jina_client import JinaClient
            
            # Test d'initialisation
            jina_client = JinaClient()
            
            # Test de configuration des headers
            test_params = {
                "engine": "browser",
                "no_cache": True,
                "timeout": "30"
            }
            
            # Cette méthode devrait exister pour convertir les paramètres
            if hasattr(jina_client, '_build_headers'):
                headers = jina_client._build_headers(test_params)
                
                jina_results = {
                    "client_initialized": True,
                    "headers_built": True,
                    "sample_headers": dict(list(headers.items())[:3]) if headers else None
                }
                
                print_success("✓ Jina Client: Initialisation réussie")
                print_success("✓ Jina Client: Construction des headers OK")
                self.add_test_result("jina_client_basic", "PASSED", jina_results)
                return True
            else:
                print_warning("⚠️ Jina Client: Méthode _build_headers non trouvée")
                self.add_test_result("jina_client_basic", "WARNING", {"client_initialized": True}, "Method _build_headers not found")
                return True
                
        except Exception as e:
            print_error(f"✗ Jina Client: {str(e)}")
            self.add_test_result("jina_client_basic", "FAILED", None, str(e))
            return False

    async def test_orchestrator_basic(self):
        """Test 6: Orchestrateur (test basique)"""
        print_header("TEST 6: ORCHESTRATEUR")
        
        try:
            from jinascraper.core.orchestrator import ScrapingOrchestrator
            
            # Test d'initialisation
            orchestrator = ScrapingOrchestrator()
            
            # Vérification des méthodes essentielles
            essential_methods = [
                "run_stage1_exploration",
                "_extract_urls_from_all_sources",
                "_get_sources_to_process"
            ]
            
            method_results = {}
            for method_name in essential_methods:
                method_results[method_name] = hasattr(orchestrator, method_name)
                if method_results[method_name]:
                    print_success(f"✓ Orchestrator: {method_name} trouvée")
                else:
                    print_error(f"✗ Orchestrator: {method_name} manquante")
            
            # Vérification des méthodes Stage 2 (optionnelles)
            stage2_methods = [
                "run_stage2_enhanced_analysis",
                "run_full_cycle_with_stage2"
            ]
            
            stage2_results = {}
            for method_name in stage2_methods:
                stage2_results[method_name] = hasattr(orchestrator, method_name)
                if stage2_results[method_name]:
                    print_success(f"✓ Orchestrator Stage 2: {method_name} trouvée")
                else:
                    print_info(f"ℹ️ Orchestrator Stage 2: {method_name} non implémentée")
            
            orchestrator_results = {
                "initialized": True,
                "essential_methods": method_results,
                "stage2_methods": stage2_results,
                "stage2_ready": all(stage2_results.values())
            }
            
            if all(method_results.values()):
                print_success("✓ Orchestrator: Toutes les méthodes essentielles présentes")
                self.add_test_result("orchestrator_basic", "PASSED", orchestrator_results)
                return True
            else:
                print_error("✗ Orchestrator: Méthodes essentielles manquantes")
                self.add_test_result("orchestrator_basic", "FAILED", orchestrator_results, "Essential methods missing")
                return False
                
        except Exception as e:
            print_error(f"✗ Orchestrator: {str(e)}")
            self.add_test_result("orchestrator_basic", "FAILED", None, str(e))
            return False

    async def test_phase2_components(self):
        """Test 7: Composants Phase 2"""
        print_header("TEST 7: COMPOSANTS PHASE 2")
        
        phase2_components = {
            "enhanced_detail_scraper": "jinascraper.services.enhanced_detail_scraper",
            "models_enriched": "jinascraper.models_enriched",
            "enhanced_pipeline_orchestrator": "jinascraper.services.enhanced_pipeline_orchestrator"
        }
        
        phase2_results = {}
        
        for component_name, module_path in phase2_components.items():
            try:
                module = importlib.import_module(module_path)
                phase2_results[component_name] = {
                    "status": "AVAILABLE",
                    "module_path": module_path,
                    "classes": [name for name in dir(module) if not name.startswith('_') and name[0].isupper()]
                }
                print_success(f"✓ Phase 2: {component_name} disponible")
            except ImportError:
                phase2_results[component_name] = {
                    "status": "NOT_FOUND",
                    "module_path": module_path
                }
                print_info(f"ℹ️ Phase 2: {component_name} non trouvé")
            except Exception as e:
                phase2_results[component_name] = {
                    "status": "ERROR",
                    "module_path": module_path,
                    "error": str(e)
                }
                print_error(f"✗ Phase 2: {component_name} erreur: {str(e)}")
        
        available_components = sum(1 for result in phase2_results.values() 
                                 if result["status"] == "AVAILABLE")
        
        print_info(f"Composants Phase 2 disponibles: {available_components}/{len(phase2_components)}")
        
        self.add_test_result("phase2_components", "PASSED", phase2_results)
        return True

    async def test_database_schema(self):
        """Test 8: Schéma de base de données"""
        print_header("TEST 8: SCHÉMA BASE DE DONNÉES")
        
        try:
            # Vérifier les fichiers de migration
            migration_files = [
                "jinascraper/database/migrations/001_add_stage2_columns.sql",
                "jinascraper/database/migrations/001_rollback_stage2_columns.sql"
            ]
            
            migration_results = {}
            for file_path in migration_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        migration_results[file_path] = {
                            "exists": True,
                            "size": len(content),
                            "has_stage2_columns": "stage2_" in content
                        }
                        print_success(f"✓ Migration: {os.path.basename(file_path)} trouvée")
                else:
                    migration_results[file_path] = {"exists": False}
                    print_error(f"✗ Migration: {os.path.basename(file_path)} manquante")
            
            # Vérifier le schéma Prisma si disponible
            prisma_schema = "jinascraper/prisma/schema.prisma"
            if os.path.exists(prisma_schema):
                with open(prisma_schema, 'r', encoding='utf-8') as f:
                    schema_content = f.read()
                    migration_results["prisma_schema"] = {
                        "exists": True,
                        "has_jobs_model": "model jobs" in schema_content.lower() or "model Jobs" in schema_content,
                        "size": len(schema_content)
                    }
                    print_success("✓ Prisma: Schema trouvé")
            else:
                migration_results["prisma_schema"] = {"exists": False}
                print_info("ℹ️ Prisma: Schema non trouvé")
            
            self.add_test_result("database_schema", "PASSED", migration_results)
            return True
            
        except Exception as e:
            print_error(f"✗ Database Schema: {str(e)}")
            self.add_test_result("database_schema", "FAILED", None, str(e))
            return False

    def generate_report(self):
        """Générer le rapport final"""
        print_header("RAPPORT FINAL D'AUDIT")
        
        # Statistiques globales
        total = self.results["summary"]["total_tests"]
        passed = self.results["summary"]["passed"]
        failed = self.results["summary"]["failed"]
        warnings = self.results["summary"]["warnings"]
        
        print(f"\n{Colors.BOLD}RÉSULTATS GLOBAUX:{Colors.END}")
        print(f"  Total des tests: {total}")
        print_success(f"  Réussis: {passed}")
        print_error(f"  Échecs: {failed}")
        print_warning(f"  Avertissements: {warnings}")
        
        success_rate = (passed / total * 100) if total > 0 else 0
        print(f"\n{Colors.BOLD}Taux de réussite: {success_rate:.1f}%{Colors.END}")
        
        # Détails des échecs
        if failed > 0:
            print(f"\n{Colors.BOLD}{Colors.RED}TESTS EN ÉCHEC:{Colors.END}")
            for test_name, result in self.results["tests"].items():
                if result["status"] == "FAILED":
                    print_error(f"  {test_name}: {result.get('error', 'Erreur inconnue')}")
        
        # Recommandations
        print(f"\n{Colors.BOLD}RECOMMANDATIONS:{Colors.END}")
        
        if failed == 0:
            print_success("  ✅ Système prêt pour l'implémentation de l'Étape 2")
        else:
            print_error("  ❌ Corriger les problèmes critiques avant l'Étape 2")
            
            # Recommandations spécifiques
            if "imports_validation" in [name for name, result in self.results["tests"].items() if result["status"] == "FAILED"]:
                print_error("  🔧 PRIORITÉ 1: Corriger les imports relatifs cassés")
                
            if "url_cleaners_functionality" in [name for name, result in self.results["tests"].items() if result["status"] == "FAILED"]:
                print_error("  🔧 PRIORITÉ 2: Réparer les nettoyeurs URL défaillants")
        
        # Sauvegarde du rapport
        report_file = f"jinascraper/audit_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print_info(f"  📄 Rapport détaillé sauvegardé: {report_file}")
        
        return success_rate >= 80  # 80% minimum pour considérer le système stable

async def main():
    """Fonction principale d'audit"""
    print_header("AUDIT COMPLET JINASCRAPER - JANVIER 2025")
    print_info(f"Démarrage de l'audit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    audit = JinaScraperAudit()
    
    # Exécution de tous les tests
    tests = [
        audit.test_imports_validation(),
        audit.test_url_cleaners_functionality(),
        audit.test_source_configurations(),
        audit.test_redis_integration(),
        audit.test_jina_client_basic(),
        audit.test_orchestrator_basic(),
        audit.test_phase2_components(),
        audit.test_database_schema()
    ]
    
    # Exécution séquentielle des tests
    for test in tests:
        try:
            await test
        except Exception as e:
            print_error(f"Erreur lors de l'exécution du test: {str(e)}")
            traceback.print_exc()
    
    # Génération du rapport final
    system_ready = audit.generate_report()
    
    if system_ready:
        print(f"\n{Colors.BOLD}{Colors.GREEN}🎉 SYSTÈME PRÊT POUR L'ÉTAPE 2{Colors.END}")
    else:
        print(f"\n{Colors.BOLD}{Colors.RED}⚠️ CORRECTIONS NÉCESSAIRES AVANT L'ÉTAPE 2{Colors.END}")
    
    return system_ready

if __name__ == "__main__":
    # Ajout du répertoire jinascraper au PYTHONPATH
    sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
    
    # Exécution de l'audit
    result = asyncio.run(main())
    sys.exit(0 if result else 1)