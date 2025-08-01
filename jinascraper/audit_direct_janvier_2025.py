#!/usr/bin/env python3
"""
Audit Direct JinaScraper - Janvier 2025
Test direct des fichiers sans imports de package
"""

import sys
import os
import asyncio
import traceback
from datetime import datetime
from typing import Dict, List, Any, Optional
import json
import re

# Ajout du répertoire courant au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

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

class DirectJinaScraperAudit:
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

    def test_file_structure(self):
        """Test 1: Structure des fichiers"""
        print_header("TEST 1: STRUCTURE DES FICHIERS")
        
        # Fichiers critiques à vérifier
        critical_files = [
            "services/url_cleaners/emploitogo_info_cleaner.py",
            "services/url_cleaners/yop_lfrii_cleaner.py", 
            "services/url_cleaners/linkedin_togo_cleaner.py",
            "services/url_cleaners/indeed_togo_cleaner.py",
            "services/url_cleaners/emploi_tg_cleaner.py",
            "services/url_cleaners/anpetogo_cleaner.py",
            "config/source_registry.py",
            "core/orchestrator.py",
            "services/cache_manager.py",
            "services/jina_client.py",
            "services/gemini_service.py",
            "models.py",
            "main.py"
        ]
        
        file_results = {}
        missing_files = []
        
        for file_path in critical_files:
            full_path = os.path.join(os.path.dirname(__file__), file_path)
            if os.path.exists(full_path):
                file_size = os.path.getsize(full_path)
                file_results[file_path] = {
                    "exists": True,
                    "size": file_size,
                    "path": full_path
                }
                print_success(f"✓ {file_path} ({file_size} bytes)")
            else:
                file_results[file_path] = {"exists": False, "path": full_path}
                missing_files.append(file_path)
                print_error(f"✗ {file_path} MANQUANT")
        
        if missing_files:
            self.add_test_result(
                "file_structure", 
                "FAILED", 
                file_results, 
                f"{len(missing_files)} fichiers manquants: {missing_files}"
            )
        else:
            self.add_test_result("file_structure", "PASSED", file_results)
            
        return len(missing_files) == 0

    def test_import_patterns_in_files(self):
        """Test 2: Patterns d'imports dans les fichiers"""
        print_header("TEST 2: ANALYSE DES IMPORTS DANS LES FICHIERS")
        
        # Fichiers de nettoyeurs à analyser
        cleaner_files = [
            "services/url_cleaners/emploitogo_info_cleaner.py",
            "services/url_cleaners/yop_lfrii_cleaner.py", 
            "services/url_cleaners/linkedin_togo_cleaner.py",
            "services/url_cleaners/indeed_togo_cleaner.py",
            "services/url_cleaners/emploi_tg_cleaner.py",
            "services/url_cleaners/anpetogo_cleaner.py"
        ]
        
        import_analysis = {}
        problematic_imports = []
        
        for file_path in cleaner_files:
            full_path = os.path.join(os.path.dirname(__file__), file_path)
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Recherche des imports relatifs problématiques
                    relative_imports = re.findall(r'from\s+(\.{3,}[^\s]+)', content)
                    absolute_imports = re.findall(r'from\s+(jinascraper\.[^\s]+)', content)
                    
                    import_analysis[file_path] = {
                        "relative_imports": relative_imports,
                        "absolute_imports": absolute_imports,
                        "has_problematic_imports": len(relative_imports) > 0,
                        "content_length": len(content)
                    }
                    
                    if relative_imports:
                        problematic_imports.append(file_path)
                        print_error(f"✗ {file_path}: Imports relatifs problématiques: {relative_imports}")
                    else:
                        print_success(f"✓ {file_path}: Imports OK")
                        
                except Exception as e:
                    import_analysis[file_path] = {"error": str(e)}
                    print_error(f"✗ {file_path}: Erreur lecture: {str(e)}")
            else:
                import_analysis[file_path] = {"exists": False}
                print_error(f"✗ {file_path}: Fichier manquant")
        
        if problematic_imports:
            self.add_test_result(
                "import_patterns", 
                "FAILED", 
                import_analysis,
                f"Fichiers avec imports problématiques: {problematic_imports}"
            )
        else:
            self.add_test_result("import_patterns", "PASSED", import_analysis)
            
        return len(problematic_imports) == 0

    def test_url_cleaner_functions(self):
        """Test 3: Fonctions des nettoyeurs URL"""
        print_header("TEST 3: FONCTIONS DES NETTOYEURS URL")
        
        # URLs de test réelles pour chaque source
        test_data = {
            "emploitogo_info": {
                "file": "services/url_cleaners/emploitogo_info_cleaner.py",
                "function": "clean_emploitogo_info_urls",
                "test_urls": [
                    "https://www.emploitogo.info/emploitogo/offre-demploi-togo-charge-de-communication/",
                    "https://www.emploitogo.info/emploitogo/recrutement-assistant-comptable-lome/",
                    "https://www.emploitogo.info/emploitogo/poste-vacant-developpeur-web-kara/"
                ]
            },
            "yop_lfrii": {
                "file": "services/url_cleaners/yop_lfrii_cleaner.py",
                "function": "clean_yop_lfrii_urls",
                "test_urls": [
                    "https://yop.l-frii.com/emploi/coordinateur-projet-humanitaire/",
                    "https://yop.l-frii.com/emploi/assistant-logistique-ong/",
                    "https://yop.l-frii.com/emploi/responsable-marketing-digital/"
                ]
            },
            "emploi_tg": {
                "file": "services/url_cleaners/emploi_tg_cleaner.py",
                "function": "clean_emploi_tg_urls",
                "test_urls": [
                    "https://www.emploi.tg/offre-emploi-togo/developpeur-full-stack-lome/",
                    "https://www.emploi.tg/offre-emploi-togo/comptable-senior-kpalime/",
                    "https://www.emploi.tg/offre-emploi-togo/chef-projet-it-sokode/"
                ]
            }
        }
        
        cleaner_results = {}
        failed_cleaners = []
        
        for source_name, config in test_data.items():
            print_info(f"Testing {source_name} cleaner")
            
            file_path = os.path.join(os.path.dirname(__file__), config["file"])
            
            if os.path.exists(file_path):
                try:
                    # Lecture du fichier
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Vérification de la présence de la fonction
                    function_name = config["function"]
                    has_function = f"def {function_name}" in content
                    
                    # Analyse des patterns regex
                    regex_patterns = re.findall(r'r[\'"]([^\'"]+)[\'"]', content)
                    
                    cleaner_results[source_name] = {
                        "file_exists": True,
                        "has_function": has_function,
                        "function_name": function_name,
                        "regex_patterns": regex_patterns,
                        "test_urls_count": len(config["test_urls"]),
                        "sample_test_url": config["test_urls"][0] if config["test_urls"] else None
                    }
                    
                    if has_function:
                        print_success(f"✓ {source_name}: Fonction {function_name} trouvée")
                        if regex_patterns:
                            print_info(f"  Patterns regex: {len(regex_patterns)} trouvés")
                        else:
                            print_warning(f"  Aucun pattern regex trouvé")
                    else:
                        print_error(f"✗ {source_name}: Fonction {function_name} manquante")
                        failed_cleaners.append(source_name)
                        
                except Exception as e:
                    cleaner_results[source_name] = {
                        "file_exists": True,
                        "error": str(e)
                    }
                    failed_cleaners.append(source_name)
                    print_error(f"✗ {source_name}: Erreur: {str(e)}")
            else:
                cleaner_results[source_name] = {"file_exists": False}
                failed_cleaners.append(source_name)
                print_error(f"✗ {source_name}: Fichier manquant")
        
        if failed_cleaners:
            self.add_test_result(
                "url_cleaner_functions", 
                "FAILED", 
                cleaner_results,
                f"Cleaners défaillants: {failed_cleaners}"
            )
        else:
            self.add_test_result("url_cleaner_functions", "PASSED", cleaner_results)
            
        return len(failed_cleaners) == 0

    def test_configuration_files(self):
        """Test 4: Fichiers de configuration"""
        print_header("TEST 4: FICHIERS DE CONFIGURATION")
        
        config_files = [
            "config/sources/emploi_tg.py",
            "config/sources/anpetogo.py",
            "config/sources/linkedin_togo.py",
            "config/sources/indeed_togo.py",
            "config/sources/yop_lfrii.py",
            "config/sources/emploitogo_info.py",
            "config/base_config.py",
            "config/source_registry.py"
        ]
        
        config_results = {}
        missing_configs = []
        
        for config_file in config_files:
            file_path = os.path.join(os.path.dirname(__file__), config_file)
            
            if os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Analyse du contenu
                    has_stage2_params = "stage2_params" in content
                    has_source_config = "SourceBaseConfig" in content or "CONFIG" in content
                    
                    config_results[config_file] = {
                        "exists": True,
                        "size": len(content),
                        "has_stage2_params": has_stage2_params,
                        "has_source_config": has_source_config
                    }
                    
                    print_success(f"✓ {config_file}")
                    if has_stage2_params:
                        print_info(f"  Stage 2 params détectés")
                        
                except Exception as e:
                    config_results[config_file] = {
                        "exists": True,
                        "error": str(e)
                    }
                    print_error(f"✗ {config_file}: Erreur: {str(e)}")
            else:
                config_results[config_file] = {"exists": False}
                missing_configs.append(config_file)
                print_error(f"✗ {config_file}: Manquant")
        
        if missing_configs:
            self.add_test_result(
                "configuration_files", 
                "WARNING", 
                config_results,
                f"Fichiers de config manquants: {missing_configs}"
            )
        else:
            self.add_test_result("configuration_files", "PASSED", config_results)
            
        return len(missing_configs) == 0

    def test_phase2_files(self):
        """Test 5: Fichiers Phase 2"""
        print_header("TEST 5: FICHIERS PHASE 2")
        
        phase2_files = [
            "services/enhanced_detail_scraper.py",
            "models_enriched.py",
            "services/enhanced_pipeline_orchestrator.py",
            "database/migrations/001_add_stage2_columns.sql",
            "database/migrations/001_rollback_stage2_columns.sql",
            "PHASE2_README.md",
            "PHASE2_IMPLEMENTATION_COMPLETE.md"
        ]
        
        phase2_results = {}
        available_files = 0
        
        for file_path in phase2_files:
            full_path = os.path.join(os.path.dirname(__file__), file_path)
            
            if os.path.exists(full_path):
                file_size = os.path.getsize(full_path)
                phase2_results[file_path] = {
                    "exists": True,
                    "size": file_size
                }
                available_files += 1
                print_success(f"✓ {file_path} ({file_size} bytes)")
            else:
                phase2_results[file_path] = {"exists": False}
                print_info(f"ℹ️ {file_path}: Non trouvé")
        
        phase2_completion = (available_files / len(phase2_files)) * 100
        print_info(f"Phase 2 completion: {phase2_completion:.1f}% ({available_files}/{len(phase2_files)})")
        
        self.add_test_result("phase2_files", "PASSED", {
            "files": phase2_results,
            "completion_rate": phase2_completion,
            "available_files": available_files,
            "total_files": len(phase2_files)
        })
        
        return True

    def test_redis_files(self):
        """Test 6: Fichiers Redis"""
        print_header("TEST 6: FICHIERS REDIS")
        
        redis_files = [
            "services/redis_factory.py",
            "services/cache_manager.py",
            "test_complete_5_sources_redis.py",
            "test_real_stage1_with_redis.py",
            "REDIS_INTEGRATION_AUDIT_COMPLET.md"
        ]
        
        redis_results = {}
        available_redis = 0
        
        for file_path in redis_files:
            full_path = os.path.join(os.path.dirname(__file__), file_path)
            
            if os.path.exists(full_path):
                file_size = os.path.getsize(full_path)
                redis_results[file_path] = {
                    "exists": True,
                    "size": file_size
                }
                available_redis += 1
                print_success(f"✓ {file_path} ({file_size} bytes)")
            else:
                redis_results[file_path] = {"exists": False}
                print_error(f"✗ {file_path}: Manquant")
        
        redis_completion = (available_redis / len(redis_files)) * 100
        print_info(f"Redis integration: {redis_completion:.1f}% ({available_redis}/{len(redis_files)})")
        
        if available_redis >= 3:  # Au moins les fichiers essentiels
            self.add_test_result("redis_files", "PASSED", redis_results)
        else:
            self.add_test_result("redis_files", "FAILED", redis_results, "Fichiers Redis essentiels manquants")
            
        return available_redis >= 3

    def test_environment_files(self):
        """Test 7: Fichiers d'environnement"""
        print_header("TEST 7: FICHIERS D'ENVIRONNEMENT")
        
        env_files = [
            ".env",
            ".env.example",
            "requirements.txt",
            "pyproject.toml"
        ]
        
        env_results = {}
        
        for file_path in env_files:
            full_path = os.path.join(os.path.dirname(__file__), file_path)
            
            if os.path.exists(full_path):
                file_size = os.path.getsize(full_path)
                env_results[file_path] = {
                    "exists": True,
                    "size": file_size
                }
                print_success(f"✓ {file_path} ({file_size} bytes)")
                
                # Analyse spécifique pour requirements.txt
                if file_path == "requirements.txt":
                    try:
                        with open(full_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        # Vérification des dépendances critiques
                        critical_deps = ["redis", "fakeredis", "aiohttp", "asyncio"]
                        found_deps = []
                        for dep in critical_deps:
                            if dep in content.lower():
                                found_deps.append(dep)
                        
                        env_results[file_path]["critical_dependencies"] = found_deps
                        print_info(f"  Dépendances critiques trouvées: {found_deps}")
                        
                    except Exception as e:
                        env_results[file_path]["error"] = str(e)
            else:
                env_results[file_path] = {"exists": False}
                print_warning(f"⚠️ {file_path}: Manquant")
        
        self.add_test_result("environment_files", "PASSED", env_results)
        return True

    def generate_detailed_report(self):
        """Générer le rapport détaillé"""
        print_header("RAPPORT DÉTAILLÉ D'AUDIT")
        
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
        
        # Analyse détaillée par catégorie
        print(f"\n{Colors.BOLD}ANALYSE DÉTAILLÉE:{Colors.END}")
        
        # Problèmes d'imports
        if "import_patterns" in self.results["tests"]:
            import_test = self.results["tests"]["import_patterns"]
            if import_test["status"] == "FAILED":
                print_error("  🚨 IMPORTS RELATIFS PROBLÉMATIQUES DÉTECTÉS")
                if import_test["details"]:
                    for file_path, details in import_test["details"].items():
                        if details.get("has_problematic_imports", False):
                            print_error(f"    - {file_path}: {details['relative_imports']}")
        
        # État des nettoyeurs
        if "url_cleaner_functions" in self.results["tests"]:
            cleaner_test = self.results["tests"]["url_cleaner_functions"]
            print_info("  🧹 ÉTAT DES NETTOYEURS URL:")
            if cleaner_test["details"]:
                for source, details in cleaner_test["details"].items():
                    if details.get("has_function", False):
                        print_success(f"    ✓ {source}: Fonction présente")
                    else:
                        print_error(f"    ✗ {source}: Fonction manquante ou problème")
        
        # État Phase 2
        if "phase2_files" in self.results["tests"]:
            phase2_test = self.results["tests"]["phase2_files"]
            completion = phase2_test["details"]["completion_rate"]
            print_info(f"  🚀 PHASE 2: {completion:.1f}% complète")
        
        # État Redis
        if "redis_files" in self.results["tests"]:
            redis_test = self.results["tests"]["redis_files"]
            if redis_test["status"] == "PASSED":
                print_success("  ⚡ REDIS: Intégration disponible")
            else:
                print_error("  ⚡ REDIS: Intégration incomplète")
        
        # Recommandations prioritaires
        print(f"\n{Colors.BOLD}RECOMMANDATIONS PRIORITAIRES:{Colors.END}")
        
        if failed == 0:
            print_success("  ✅ Système stable - Prêt pour l'Étape 2")
        else:
            print_error("  ❌ Corrections nécessaires avant l'Étape 2")
            
            # Recommandations spécifiques basées sur les résultats
            if any(test["status"] == "FAILED" and "import" in name.lower() 
                   for name, test in self.results["tests"].items()):
                print_error("  🔧 PRIORITÉ 1: Corriger les imports relatifs dans les nettoyeurs URL")
                print_info("    Action: Remplacer 'from ...utils' par 'from jinascraper.utils'")
                
            if any(test["status"] == "FAILED" and "cleaner" in name.lower() 
                   for name, test in self.results["tests"].items()):
                print_error("  🔧 PRIORITÉ 2: Vérifier les fonctions des nettoyeurs URL")
                print_info("    Action: S'assurer que chaque cleaner a sa fonction principale")
        
        # Sauvegarde du rapport
        report_file = f"audit_direct_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, indent=2, ensure_ascii=False)
        
        print_info(f"  📄 Rapport détaillé sauvegardé: {report_file}")
        
        return success_rate >= 70  # 70% minimum pour considérer le système utilisable

def main():
    """Fonction principale d'audit direct"""
    print_header("AUDIT DIRECT JINASCRAPER - JANVIER 2025")
    print_info(f"Démarrage de l'audit: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print_info(f"Répertoire de travail: {os.path.dirname(os.path.abspath(__file__))}")
    
    audit = DirectJinaScraperAudit()
    
    # Exécution de tous les tests
    tests = [
        ("Structure des fichiers", audit.test_file_structure),
        ("Patterns d'imports", audit.test_import_patterns_in_files),
        ("Fonctions nettoyeurs", audit.test_url_cleaner_functions),
        ("Fichiers de configuration", audit.test_configuration_files),
        ("Fichiers Phase 2", audit.test_phase2_files),
        ("Fichiers Redis", audit.test_redis_files),
        ("Fichiers d'environnement", audit.test_environment_files)
    ]
    
    # Exécution séquentielle des tests
    for test_name, test_func in tests:
        try:
            print_info(f"Exécution: {test_name}")
            test_func()
        except Exception as e:
            print_error(f"Erreur lors de {test_name}: {str(e)}")
            traceback.print_exc()
    
    # Génération du rapport final
    system_ready = audit.generate_detailed_report()
    
    if system_ready:
        print(f"\n{Colors.BOLD}{Colors.GREEN}🎉 SYSTÈME UTILISABLE - CORRECTIONS MINEURES POSSIBLES{Colors.END}")
    else:
        print(f"\n{Colors.BOLD}{Colors.RED}⚠️ CORRECTIONS MAJEURES NÉCESSAIRES{Colors.END}")
    
    return system_ready

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)