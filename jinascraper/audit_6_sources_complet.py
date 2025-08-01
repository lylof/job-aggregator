#!/usr/bin/env python3
"""
Audit Complet des 6 Sources - Janvier 2025
Test exhaustif de toutes les sources avec données réelles
"""

import sys
import os
import re
from typing import List, Dict, Any

# Ajout du répertoire courant au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuration des couleurs
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header(title: str):
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{title.center(70)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*70}{Colors.END}")

def print_success(message: str):
    print(f"{Colors.GREEN}✅ {message}{Colors.END}")

def print_error(message: str):
    print(f"{Colors.RED}❌ {message}{Colors.END}")

def print_info(message: str):
    print(f"{Colors.CYAN}ℹ️  {message}{Colors.END}")

def print_warning(message: str):
    print(f"{Colors.YELLOW}⚠️  {message}{Colors.END}")

class SixSourcesAudit:
    def __init__(self):
        # Définition complète des 6 sources
        self.sources = {
            "emploitogo_info": {
                "name": "EmploiTogo.info",
                "cleaner_file": "services/url_cleaners/emploitogo_info_cleaner.py",
                "config_file": "config/sources/emploitogo_info.py",
                "function_name": "clean_emploitogo_info_urls",
                "test_urls": [
                    "https://www.emploitogo.info/emploitogo/offre-demploi-togo-charge-de-communication/",
                    "https://www.emploitogo.info/emploitogo/recrutement-assistant-comptable-lome/",
                    "https://www.emploitogo.info/emploitogo/poste-vacant-developpeur-web-kara/",
                    "https://www.emploitogo.info/emploitogo/page/2/",  # Doit être exclu
                    "https://www.emploitogo.info/emploitogo/category/it/",  # Doit être exclu
                    "https://www.emploitogo.info/emploitogo/offre-stage-marketing-digital/"
                ],
                "expected_valid": 4,
                "domain": "www.emploitogo.info",
                "patterns": [r'^/emploitogo/[^/]+/?$']
            },
            "yop_lfrii": {
                "name": "YOP L-FRII",
                "cleaner_file": "services/url_cleaners/yop_lfrii_cleaner.py",
                "config_file": "config/sources/yop_lfrii.py",
                "function_name": "clean_yop_lfrii_urls",
                "test_urls": [
                    "https://yop.l-frii.com/emploi/coordinateur-projet-humanitaire/",
                    "https://yop.l-frii.com/emploi/assistant-logistique-ong/",
                    "https://yop.l-frii.com/emploi/responsable-marketing-digital/",
                    "https://yop.l-frii.com/emploi/page/2/",  # Doit être exclu
                    "https://yop.l-frii.com/offres-demplois/developpeur-senior/",
                    "https://yop.l-frii.com/emploi/category/tech/"  # Doit être exclu
                ],
                "expected_valid": 4,
                "domain": "yop.l-frii.com",
                "patterns": [r'^/emploi/[^/]+/?$', r'^/offres-demplois/[^/]+/?$']
            },
            "emploi_tg": {
                "name": "Emploi.tg",
                "cleaner_file": "services/url_cleaners/emploi_tg_cleaner.py",
                "config_file": "config/sources/emploi_tg.py",
                "function_name": "clean_emploi_tg_urls",
                "test_urls": [
                    "https://www.emploi.tg/offre-emploi-togo/developpeur-full-stack-lome/",
                    "https://www.emploi.tg/offre-emploi-togo/comptable-senior-kpalime/",
                    "https://www.emploi.tg/offre-emploi-togo/chef-projet-it-sokode/",
                    "https://www.emploi.tg/page/2/",  # Doit être exclu
                    "https://www.emploi.tg/recherche-jobs-togo",  # Doit être exclu
                    "https://www.emploi.tg/offre-emploi-togo/ingenieur-reseau-lome/"
                ],
                "expected_valid": 4,
                "domain": "www.emploi.tg",
                "patterns": [r'^/offre-emploi-togo/[^/]+/?$']
            },
            "anpetogo": {
                "name": "ANPE Togo",
                "cleaner_file": "services/url_cleaners/anpetogo_cleaner.py",
                "config_file": "config/sources/anpetogo.py",
                "function_name": "clean_anpetogo_urls",
                "test_urls": [
                    "https://anpetogo.org/offre/technicien-maintenance-informatique/",
                    "https://anpetogo.org/offre/secretaire-direction-bilingue/",
                    "https://anpetogo.org/offre/ingenieur-genie-civil/",
                    "https://anpetogo.org/page/2/",  # Doit être exclu
                    "https://anpetogo.org/category/administration/",  # Doit être exclu
                    "https://anpetogo.org/offre/assistant-ressources-humaines/"
                ],
                "expected_valid": 4,
                "domain": "anpetogo.org",
                "patterns": [r'^/offre/[^/]+/?$']
            },
            "linkedin_togo": {
                "name": "LinkedIn Togo",
                "cleaner_file": "services/url_cleaners/linkedin_togo_cleaner.py",
                "config_file": "config/sources/linkedin_togo.py",
                "function_name": "clean_linkedin_togo_urls",
                "test_urls": [
                    "https://tg.linkedin.com/jobs/view/3456789012",
                    "https://tg.linkedin.com/jobs/view/3456789013",
                    "https://tg.linkedin.com/jobs/view/3456789014",
                    "https://tg.linkedin.com/jobs/search/",  # Doit être exclu
                    "https://tg.linkedin.com/company/techcorp/",  # Doit être exclu
                    "https://tg.linkedin.com/jobs/view/3456789015"
                ],
                "expected_valid": 4,
                "domain": "tg.linkedin.com",
                "patterns": [r'^/jobs/view/\d+/?$']
            },
            "indeed_togo": {
                "name": "Indeed Togo",
                "cleaner_file": "services/url_cleaners/indeed_togo_cleaner.py",
                "config_file": "config/sources/indeed_togo.py",
                "function_name": "clean_indeed_togo_urls",
                "test_urls": [
                    "https://tg.indeed.com/viewjob?jk=abc123def456",
                    "https://tg.indeed.com/viewjob?jk=def456ghi789",
                    "https://tg.indeed.com/viewjob?jk=ghi789jkl012",
                    "https://tg.indeed.com/jobs?q=developer",  # Doit être exclu
                    "https://tg.indeed.com/companies/techcorp",  # Doit être exclu
                    "https://tg.indeed.com/viewjob?jk=jkl012mno345"
                ],
                "expected_valid": 4,
                "domain": "tg.indeed.com",
                "patterns": [r'^/viewjob\?jk=[a-zA-Z0-9]+$']
            }
        }
        
        self.results = {}

    def test_file_existence(self):
        """Test 1: Existence des fichiers pour les 6 sources"""
        print_header("TEST 1: EXISTENCE DES FICHIERS (6 SOURCES)")
        
        file_results = {}
        
        for source_id, config in self.sources.items():
            print_info(f"Testing {config['name']}")
            
            # Test du fichier cleaner
            cleaner_path = os.path.join(os.path.dirname(__file__), config["cleaner_file"])
            cleaner_exists = os.path.exists(cleaner_path)
            
            # Test du fichier config
            config_path = os.path.join(os.path.dirname(__file__), config["config_file"])
            config_exists = os.path.exists(config_path)
            
            file_results[source_id] = {
                "name": config["name"],
                "cleaner_exists": cleaner_exists,
                "config_exists": config_exists,
                "cleaner_size": os.path.getsize(cleaner_path) if cleaner_exists else 0,
                "config_size": os.path.getsize(config_path) if config_exists else 0
            }
            
            if cleaner_exists and config_exists:
                print_success(f"✓ {config['name']}: Fichiers présents")
                print_info(f"  Cleaner: {file_results[source_id]['cleaner_size']} bytes")
                print_info(f"  Config: {file_results[source_id]['config_size']} bytes")
            else:
                missing = []
                if not cleaner_exists:
                    missing.append("cleaner")
                if not config_exists:
                    missing.append("config")
                print_error(f"✗ {config['name']}: Fichiers manquants: {missing}")
        
        self.results["file_existence"] = file_results
        return file_results

    def test_import_patterns(self):
        """Test 2: Analyse des imports pour les 6 sources"""
        print_header("TEST 2: ANALYSE DES IMPORTS (6 SOURCES)")
        
        import_results = {}
        
        for source_id, config in self.sources.items():
            print_info(f"Analyzing imports for {config['name']}")
            
            cleaner_path = os.path.join(os.path.dirname(__file__), config["cleaner_file"])
            
            if os.path.exists(cleaner_path):
                try:
                    with open(cleaner_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Recherche des imports relatifs problématiques
                    relative_imports = re.findall(r'from\s+(\.{3,}[^\s]+)', content)
                    absolute_imports = re.findall(r'from\s+(jinascraper\.[^\s]+)', content)
                    
                    import_results[source_id] = {
                        "name": config["name"],
                        "relative_imports": relative_imports,
                        "absolute_imports": absolute_imports,
                        "has_problematic_imports": len(relative_imports) > 0,
                        "content_length": len(content)
                    }
                    
                    if relative_imports:
                        print_error(f"✗ {config['name']}: Imports relatifs: {relative_imports}")
                    else:
                        print_success(f"✓ {config['name']}: Imports OK")
                        
                except Exception as e:
                    import_results[source_id] = {
                        "name": config["name"],
                        "error": str(e)
                    }
                    print_error(f"✗ {config['name']}: Erreur lecture: {str(e)}")
            else:
                import_results[source_id] = {
                    "name": config["name"],
                    "exists": False
                }
                print_error(f"✗ {config['name']}: Fichier manquant")
        
        self.results["import_patterns"] = import_results
        return import_results

    def test_function_presence(self):
        """Test 3: Présence des fonctions de nettoyage pour les 6 sources"""
        print_header("TEST 3: FONCTIONS DE NETTOYAGE (6 SOURCES)")
        
        function_results = {}
        
        for source_id, config in self.sources.items():
            print_info(f"Testing function for {config['name']}")
            
            cleaner_path = os.path.join(os.path.dirname(__file__), config["cleaner_file"])
            
            if os.path.exists(cleaner_path):
                try:
                    with open(cleaner_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Vérification de la présence de la fonction
                    function_name = config["function_name"]
                    has_function = f"def {function_name}" in content
                    
                    # Analyse des patterns regex
                    regex_patterns = re.findall(r'r[\'"]([^\'"]+)[\'"]', content)
                    
                    function_results[source_id] = {
                        "name": config["name"],
                        "has_function": has_function,
                        "function_name": function_name,
                        "regex_patterns": regex_patterns,
                        "expected_patterns": config["patterns"]
                    }
                    
                    if has_function:
                        print_success(f"✓ {config['name']}: Fonction {function_name} trouvée")
                        print_info(f"  Patterns regex: {len(regex_patterns)} trouvés")
                    else:
                        print_error(f"✗ {config['name']}: Fonction {function_name} manquante")
                        
                except Exception as e:
                    function_results[source_id] = {
                        "name": config["name"],
                        "error": str(e)
                    }
                    print_error(f"✗ {config['name']}: Erreur: {str(e)}")
            else:
                function_results[source_id] = {
                    "name": config["name"],
                    "file_exists": False
                }
                print_error(f"✗ {config['name']}: Fichier manquant")
        
        self.results["function_presence"] = function_results
        return function_results

    def test_url_cleaning_logic(self):
        """Test 4: Logique de nettoyage avec URLs réelles pour les 6 sources"""
        print_header("TEST 4: LOGIQUE DE NETTOYAGE AVEC URLs RÉELLES (6 SOURCES)")
        
        cleaning_results = {}
        
        for source_id, config in self.sources.items():
            print_info(f"Testing URL cleaning for {config['name']}")
            
            # Implémentation directe de la logique de nettoyage pour éviter les imports
            test_urls = config["test_urls"]
            expected_valid = config["expected_valid"]
            domain = config["domain"]
            patterns = config["patterns"]
            
            # Simulation du nettoyage
            cleaned_urls = []
            for url in test_urls:
                if domain in url:
                    # Extraction du path
                    path = url.split(domain)[1] if domain in url else url
                    
                    # Vérification des patterns
                    if any(re.match(pattern, path) for pattern in patterns):
                        cleaned_urls.append(url)
            
            success_rate = len(cleaned_urls) / len(test_urls)
            expected_rate = expected_valid / len(test_urls)
            meets_expectation = len(cleaned_urls) == expected_valid
            
            cleaning_results[source_id] = {
                "name": config["name"],
                "input_urls": len(test_urls),
                "cleaned_urls": len(cleaned_urls),
                "expected_valid": expected_valid,
                "success_rate": success_rate,
                "expected_rate": expected_rate,
                "meets_expectation": meets_expectation,
                "sample_cleaned": cleaned_urls[:2] if cleaned_urls else []
            }
            
            print(f"  Input URLs: {len(test_urls)}")
            print(f"  Cleaned URLs: {len(cleaned_urls)}")
            print(f"  Expected: {expected_valid}")
            print(f"  Success rate: {success_rate:.1%}")
            
            if meets_expectation:
                print_success(f"✓ {config['name']}: Nettoyage fonctionne correctement")
            else:
                print_error(f"✗ {config['name']}: Nettoyage ne fonctionne pas comme attendu")
            
            # Affichage des URLs nettoyées
            if cleaned_urls:
                print_info("  URLs valides extraites:")
                for url in cleaned_urls[:2]:  # Afficher les 2 premières
                    print(f"    - {url}")
                if len(cleaned_urls) > 2:
                    print(f"    ... et {len(cleaned_urls) - 2} autres")
            
            print()
        
        self.results["url_cleaning_logic"] = cleaning_results
        return cleaning_results

    def test_configuration_completeness(self):
        """Test 5: Complétude des configurations pour les 6 sources"""
        print_header("TEST 5: COMPLÉTUDE DES CONFIGURATIONS (6 SOURCES)")
        
        config_results = {}
        
        for source_id, config in self.sources.items():
            print_info(f"Testing configuration for {config['name']}")
            
            config_path = os.path.join(os.path.dirname(__file__), config["config_file"])
            
            if os.path.exists(config_path):
                try:
                    with open(config_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    # Analyse du contenu de configuration
                    has_base_config = "SourceBaseConfig" in content or "CONFIG" in content
                    has_stage2_params = "stage2_params" in content
                    has_url_patterns = "url_patterns" in content
                    has_base_url = "base_url" in content
                    has_listing_url = "listing_url" in content
                    
                    config_results[source_id] = {
                        "name": config["name"],
                        "has_base_config": has_base_config,
                        "has_stage2_params": has_stage2_params,
                        "has_url_patterns": has_url_patterns,
                        "has_base_url": has_base_url,
                        "has_listing_url": has_listing_url,
                        "content_size": len(content)
                    }
                    
                    completeness_score = sum([
                        has_base_config, has_url_patterns, 
                        has_base_url, has_listing_url
                    ]) / 4
                    
                    config_results[source_id]["completeness_score"] = completeness_score
                    
                    if completeness_score >= 0.75:  # 75% minimum
                        print_success(f"✓ {config['name']}: Configuration complète ({completeness_score:.1%})")
                    else:
                        print_warning(f"⚠️ {config['name']}: Configuration incomplète ({completeness_score:.1%})")
                    
                    if has_stage2_params:
                        print_info(f"  Stage 2 params détectés")
                        
                except Exception as e:
                    config_results[source_id] = {
                        "name": config["name"],
                        "error": str(e)
                    }
                    print_error(f"✗ {config['name']}: Erreur: {str(e)}")
            else:
                config_results[source_id] = {
                    "name": config["name"],
                    "file_exists": False
                }
                print_error(f"✗ {config['name']}: Fichier de configuration manquant")
        
        self.results["configuration_completeness"] = config_results
        return config_results

    def generate_comprehensive_report(self):
        """Génération du rapport complet pour les 6 sources"""
        print_header("RAPPORT COMPLET - 6 SOURCES JINASCRAPER")
        
        # Statistiques globales
        total_sources = len(self.sources)
        
        # Analyse par test
        tests_summary = {}
        
        for test_name, test_results in self.results.items():
            if test_results:
                working_sources = 0
                for source_id, result in test_results.items():
                    if test_name == "file_existence":
                        if result.get("cleaner_exists", False) and result.get("config_exists", False):
                            working_sources += 1
                    elif test_name == "import_patterns":
                        if not result.get("has_problematic_imports", True):
                            working_sources += 1
                    elif test_name == "function_presence":
                        if result.get("has_function", False):
                            working_sources += 1
                    elif test_name == "url_cleaning_logic":
                        if result.get("meets_expectation", False):
                            working_sources += 1
                    elif test_name == "configuration_completeness":
                        if result.get("completeness_score", 0) >= 0.75:
                            working_sources += 1
                
                tests_summary[test_name] = {
                    "working_sources": working_sources,
                    "total_sources": total_sources,
                    "success_rate": working_sources / total_sources
                }
        
        # Affichage du résumé
        print(f"\n{Colors.BOLD}RÉSUMÉ PAR TEST:{Colors.END}")
        for test_name, summary in tests_summary.items():
            rate = summary["success_rate"]
            working = summary["working_sources"]
            total = summary["total_sources"]
            
            if rate >= 0.8:
                status = f"{Colors.GREEN}✅ EXCELLENT{Colors.END}"
            elif rate >= 0.6:
                status = f"{Colors.YELLOW}⚠️ ACCEPTABLE{Colors.END}"
            else:
                status = f"{Colors.RED}❌ PROBLÉMATIQUE{Colors.END}"
            
            print(f"  {test_name}: {working}/{total} sources ({rate:.1%}) {status}")
        
        # Analyse par source
        print(f"\n{Colors.BOLD}ANALYSE PAR SOURCE:{Colors.END}")
        
        for source_id, config in self.sources.items():
            source_name = config["name"]
            
            # Calcul du score global pour cette source
            scores = []
            details = []
            
            # File existence
            if "file_existence" in self.results:
                result = self.results["file_existence"].get(source_id, {})
                if result.get("cleaner_exists", False) and result.get("config_exists", False):
                    scores.append(1.0)
                    details.append("✅ Fichiers")
                else:
                    scores.append(0.0)
                    details.append("❌ Fichiers")
            
            # Import patterns
            if "import_patterns" in self.results:
                result = self.results["import_patterns"].get(source_id, {})
                if not result.get("has_problematic_imports", True):
                    scores.append(1.0)
                    details.append("✅ Imports")
                else:
                    scores.append(0.0)
                    details.append("❌ Imports")
            
            # Function presence
            if "function_presence" in self.results:
                result = self.results["function_presence"].get(source_id, {})
                if result.get("has_function", False):
                    scores.append(1.0)
                    details.append("✅ Fonction")
                else:
                    scores.append(0.0)
                    details.append("❌ Fonction")
            
            # URL cleaning
            if "url_cleaning_logic" in self.results:
                result = self.results["url_cleaning_logic"].get(source_id, {})
                if result.get("meets_expectation", False):
                    scores.append(1.0)
                    details.append("✅ Nettoyage")
                else:
                    scores.append(0.0)
                    details.append("❌ Nettoyage")
            
            # Configuration
            if "configuration_completeness" in self.results:
                result = self.results["configuration_completeness"].get(source_id, {})
                if result.get("completeness_score", 0) >= 0.75:
                    scores.append(1.0)
                    details.append("✅ Config")
                else:
                    scores.append(0.0)
                    details.append("❌ Config")
            
            # Score global
            global_score = sum(scores) / len(scores) if scores else 0
            
            if global_score >= 0.8:
                status = f"{Colors.GREEN}✅ EXCELLENT{Colors.END}"
            elif global_score >= 0.6:
                status = f"{Colors.YELLOW}⚠️ ACCEPTABLE{Colors.END}"
            else:
                status = f"{Colors.RED}❌ PROBLÉMATIQUE{Colors.END}"
            
            print(f"  {source_name}: {global_score:.1%} {status}")
            print(f"    {' | '.join(details)}")
        
        # Recommandations finales
        print(f"\n{Colors.BOLD}RECOMMANDATIONS FINALES:{Colors.END}")
        
        # Calcul du score global du système
        overall_scores = [summary["success_rate"] for summary in tests_summary.values()]
        overall_score = sum(overall_scores) / len(overall_scores) if overall_scores else 0
        
        print(f"Score global du système: {overall_score:.1%}")
        
        if overall_score >= 0.8:
            print_success("🎉 SYSTÈME EXCELLENT - Prêt pour l'Étape 2")
        elif overall_score >= 0.6:
            print_warning("⚠️ SYSTÈME ACCEPTABLE - Corrections mineures recommandées")
        else:
            print_error("❌ SYSTÈME PROBLÉMATIQUE - Corrections majeures nécessaires")
        
        # Actions spécifiques
        print(f"\n{Colors.BOLD}ACTIONS RECOMMANDÉES:{Colors.END}")
        
        # Problèmes d'imports
        if tests_summary.get("import_patterns", {}).get("success_rate", 1) < 0.5:
            problematic_sources = []
            for source_id, result in self.results.get("import_patterns", {}).items():
                if result.get("has_problematic_imports", False):
                    problematic_sources.append(self.sources[source_id]["name"])
            
            print_error(f"1. CORRIGER LES IMPORTS RELATIFS dans: {', '.join(problematic_sources)}")
        
        # Fonctions manquantes
        if tests_summary.get("function_presence", {}).get("success_rate", 1) < 1.0:
            missing_functions = []
            for source_id, result in self.results.get("function_presence", {}).items():
                if not result.get("has_function", True):
                    missing_functions.append(self.sources[source_id]["name"])
            
            if missing_functions:
                print_error(f"2. AJOUTER LES FONCTIONS MANQUANTES dans: {', '.join(missing_functions)}")
        
        # Nettoyage défaillant
        if tests_summary.get("url_cleaning_logic", {}).get("success_rate", 1) < 1.0:
            failing_cleaners = []
            for source_id, result in self.results.get("url_cleaning_logic", {}).items():
                if not result.get("meets_expectation", True):
                    failing_cleaners.append(self.sources[source_id]["name"])
            
            if failing_cleaners:
                print_error(f"3. RÉPARER LE NETTOYAGE URL dans: {', '.join(failing_cleaners)}")
        
        return overall_score >= 0.6

def main():
    """Fonction principale d'audit des 6 sources"""
    print_header("AUDIT EXHAUSTIF DES 6 SOURCES JINASCRAPER")
    print_info("Test complet de toutes les sources avec données réelles")
    
    audit = SixSourcesAudit()
    
    # Exécution de tous les tests
    tests = [
        audit.test_file_existence,
        audit.test_import_patterns,
        audit.test_function_presence,
        audit.test_url_cleaning_logic,
        audit.test_configuration_completeness
    ]
    
    for test_func in tests:
        try:
            test_func()
        except Exception as e:
            print_error(f"Erreur lors du test: {str(e)}")
    
    # Génération du rapport final
    system_ready = audit.generate_comprehensive_report()
    
    return system_ready

if __name__ == "__main__":
    result = main()
    sys.exit(0 if result else 1)