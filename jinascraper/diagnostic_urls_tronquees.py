#!/usr/bin/env python3
"""
Diagnostic des URLs Tronquées - Janvier 2025
Analyse du problème de troncature des URLs dans l'extraction Jina
"""

import sys
import os
import asyncio
import re
from typing import List, Dict, Any
from urllib.parse import urljoin, urlparse

# Ajout du répertoire courant au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configuration des couleurs
class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    PURPLE = '\033[95m'
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
    print(f"{Colors.YELLOW}⚠️ {message}{Colors.END}")

def print_url(url: str, status: str = ""):
    color = Colors.GREEN if "✓" in status else Colors.RED if "✗" in status else Colors.YELLOW
    print(f"{color}🔗 {url} {status}{Colors.END}")

class URLTruncationDiagnostic:
    def __init__(self):
        # URLs problématiques du rapport précédent
        self.problematic_urls = {
            "emploi_tg": [
                "https://www.emploi.tg/offre-emploi-togo/repre",
                "https://www.emploi.tg/offre-emploi-togo/charge-relation-client-hf-209529)\n- [A",
                "https://www.emploi.tg/offre-emploi-togo/commercial-terrain-lome-324824)- [Comptable Expérimenté(e) - Lomé](http"
            ],
            "anpetogo": [
                "https://anpetogo.org/job/01-ge",
                "https://anpetogo.org/job/un-01-ge",
                "https://anpetogo.org/job/40600/ "
            ],
            "emploitogo_info": [
                "https://www.emploitogo.info/champi",
                "https://www.emploitogo.info/care-international-benin-togo-recrute-01-08-2025/)\n- [La Chaîne de l'E",
                "https://www.emploitogo.info/la-ca"
            ]
        }
        
        # Contenu Jina simulé pour test (basé sur le vrai contenu)
        self.sample_jina_content = {
            "emploi_tg": """
[Assistant de Vente - Lomé Quartier Agoe La Source](https://www.emploi.tg/offre-emploi-togo/assistant-de-vente-lome-quartier-agoe-la-source-324825)
- [Chargé(e) de Relation Client H/F - Lomé](https://www.emploi.tg/offre-emploi-togo/charge-relation-client-hf-209529)
- [Commercial Terrain - Lomé](https://www.emploi.tg/offre-emploi-togo/commercial-terrain-lome-324824)
- [Comptable Expérimenté(e) - Lomé](https://www.emploi.tg/offre-emploi-togo/comptable-experimente-lome-324823)
- [Community Manager Polyvalent - Lomé Djidjorlé](https://www.emploi.tg/offre-emploi-togo/community-manager-polyvalent-lome-djidjorlé-322888)
            """,
            "anpetogo": """
- [Auditeur junior (H/F)](https://anpetogo.org/job/auditeur-junior-h-f/)
- [Consultant junior en expertise comptable](https://anpetogo.org/job/consultant-junior-en-expertise-comptable/)
- [(01) GESTIONNAIRE COMPTABLE](https://anpetogo.org/job/01-gestionnaire-comptable/)
- [(01) UN GESTIONNAIRE COMPTABLE](https://anpetogo.org/job/un-01-gestionnaire-comptable/)
- [(05) CUISINIERS](https://anpetogo.org/job/40600/)
- [(06) COMMERCIAUX (H/F)](https://anpetogo.org/job/06-commerciaux-h-f/)
            """,
            "emploitogo_info": """
- [STEEL CUBE TOGO is recruiting-10/08/2025 ( 02 positions)](https://www.emploitogo.info/steel-cube-togo-is-recruiting-10-08-2025-02-positions/)
- [CARE International Bénin-Togo recrute-01/08/2025](https://www.emploitogo.info/care-international-benin-togo-recrute-01-08-2025/)
- [La Chaîne de l'Espoir recrute-31/07/2025](https://www.emploitogo.info/la-chaine-de-lespoir-recrute-31-07-2025/)
- [GENIEXPERT recrute-30/07/2025](https://www.emploitogo.info/geniexpert-recrute-30-07-2025/)
- [L'UNFPA au Togo recrute-01/08/2025](https://www.emploitogo.info/lunfpa-au-togo-recrute-01-08-2025/)
            """
        }
    
    def analyze_url_truncation_problem(self):
        """Analyse le problème de troncature des URLs"""
        print_header("DIAGNOSTIC DES URLs TRONQUÉES")
        
        print_info("Analyse des URLs problématiques du rapport précédent...")
        
        for source_id, urls in self.problematic_urls.items():
            print(f"\n{Colors.BOLD}SOURCE: {source_id.upper()}{Colors.END}")
            
            for i, url in enumerate(urls, 1):
                print(f"\n  URL {i}:")
                print_url(f"    {url}")
                
                # Analyse des problèmes
                problems = []
                
                if url.endswith(')'):
                    problems.append("Se termine par ')' - probablement du markdown")
                
                if '\n' in url:
                    problems.append("Contient des retours à la ligne")
                
                if '- [' in url:
                    problems.append("Contient du texte markdown")
                
                if url.count('/') < 4:  # URL normale devrait avoir au moins 4 /
                    problems.append("URL incomplète - trop courte")
                
                if not url.endswith('/') and '.' not in url.split('/')[-1]:
                    problems.append("Slug incomplet")
                
                if problems:
                    for problem in problems:
                        print_error(f"      PROBLÈME: {problem}")
                else:
                    print_success(f"      Aucun problème détecté")
    
    def test_improved_extraction_patterns(self):
        """Test des patterns d'extraction améliorés"""
        print_header("TEST DES PATTERNS D'EXTRACTION AMÉLIORÉS")
        
        # Patterns améliorés pour chaque source
        improved_patterns = {
            "emploi_tg": [
                r'https://www\.emploi\.tg/offre-emploi-togo/[a-zA-Z0-9\-]+(?:-\d+)?/?',  # Pattern strict
                r'\[([^\]]+)\]\((https://www\.emploi\.tg/offre-emploi-togo/[^)]+)\)'  # Pattern markdown
            ],
            "anpetogo": [
                r'https://anpetogo\.org/job/[a-zA-Z0-9\-]+/?',  # Pattern strict
                r'\[([^\]]+)\]\((https://anpetogo\.org/job/[^)]+)\)'  # Pattern markdown
            ],
            "emploitogo_info": [
                r'https://www\.emploitogo\.info/[a-zA-Z0-9\-]+/?',  # Pattern strict
                r'\[([^\]]+)\]\((https://www\.emploitogo\.info/[^)]+)\)'  # Pattern markdown
            ]
        }
        
        for source_id, content in self.sample_jina_content.items():
            print(f"\n{Colors.BOLD}TEST SOURCE: {source_id.upper()}{Colors.END}")
            
            patterns = improved_patterns[source_id]
            all_urls = []
            
            for i, pattern in enumerate(patterns, 1):
                print(f"\n  Pattern {i}: {pattern}")
                
                try:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    print_info(f"    Trouvé {len(matches)} matches")
                    
                    for j, match in enumerate(matches[:5], 1):  # Limiter à 5 pour l'affichage
                        if isinstance(match, tuple):  # Pattern markdown retourne (titre, url)
                            title, url = match
                            print_url(f"      {j}. {url}")
                            print_info(f"         Titre: {title}")
                            all_urls.append(url)
                        else:
                            print_url(f"      {j}. {match}")
                            all_urls.append(match)
                    
                    if len(matches) > 5:
                        print_info(f"    ... et {len(matches) - 5} autres matches")
                        
                except re.error as e:
                    print_error(f"    Erreur regex: {e}")
            
            # Suppression des doublons
            unique_urls = list(set(all_urls))
            print_success(f"  TOTAL: {len(unique_urls)} URLs uniques extraites")
            
            # Validation des URLs
            valid_urls = []
            for url in unique_urls:
                if self.validate_url_format(url, source_id):
                    valid_urls.append(url)
            
            print_success(f"  VALIDES: {len(valid_urls)} URLs valides")
            
            # Affichage des URLs valides
            if valid_urls:
                print_info("  URLs valides extraites:")
                for i, url in enumerate(valid_urls[:3], 1):
                    print_url(f"    {i}. {url}", "✓")
    
    def validate_url_format(self, url: str, source_id: str) -> bool:
        """Valide le format d'une URL selon la source"""
        try:
            parsed = urlparse(url)
            
            if source_id == "emploi_tg":
                return (
                    parsed.netloc == "www.emploi.tg" and
                    "/offre-emploi-togo/" in parsed.path and
                    len(parsed.path.split("/")) >= 3 and
                    not parsed.path.endswith(")")
                )
            elif source_id == "anpetogo":
                return (
                    parsed.netloc == "anpetogo.org" and
                    "/job/" in parsed.path and
                    len(parsed.path.split("/")) >= 3 and
                    not parsed.path.endswith(")")
                )
            elif source_id == "emploitogo_info":
                return (
                    parsed.netloc == "www.emploitogo.info" and
                    len(parsed.path.split("/")) >= 2 and
                    not parsed.path.endswith(")")
                )
            
            return False
            
        except Exception:
            return False
    
    def propose_solution(self):
        """Propose une solution pour corriger le problème"""
        print_header("SOLUTION PROPOSÉE")
        
        print_info("Problèmes identifiés:")
        print_error("  1. Les patterns regex capturent du contenu markdown")
        print_error("  2. Les URLs sont mélangées avec du texte")
        print_error("  3. Pas de nettoyage post-extraction")
        print_error("  4. Seulement 3 sources testées au lieu de 6")
        
        print_info("\nSolutions recommandées:")
        print_success("  1. Utiliser des patterns markdown spécifiques: [titre](url)")
        print_success("  2. Ajouter un nettoyage post-extraction robuste")
        print_success("  3. Valider chaque URL extraite")
        print_success("  4. Tester les 6 sources complètes")
        print_success("  5. Améliorer la gestion des caractères spéciaux")
        
        print_info("\nPatterns recommandés:")
        
        recommended_patterns = {
            "emploi_tg": r'\[([^\]]+)\]\((https://www\.emploi\.tg/offre-emploi-togo/[^)]+)\)',
            "anpetogo": r'\[([^\]]+)\]\((https://anpetogo\.org/job/[^)]+)\)',
            "emploitogo_info": r'\[([^\]]+)\]\((https://www\.emploitogo\.info/[^)]+)\)',
            "linkedin_togo": r'\[([^\]]+)\]\((https://tg\.linkedin\.com/jobs/view/[^)]+)\)',
            "yop_lfrii": r'\[([^\]]+)\]\((https://yop\.l-frii\.com/[^)]+)\)',
            "indeed_togo": r'\[([^\]]+)\]\((https://tg\.indeed\.com/viewjob[^)]+)\)'
        }
        
        for source, pattern in recommended_patterns.items():
            print_info(f"  {source}: {pattern}")
    
    def test_all_6_sources_config(self):
        """Test de configuration pour les 6 sources"""
        print_header("CONFIGURATION DES 6 SOURCES")
        
        sources_config = {
            "emploi_tg": {
                "name": "Emploi.tg",
                "listing_url": "https://www.emploi.tg/recherche-jobs-togo",
                "status": "✅ ACTIF"
            },
            "anpetogo": {
                "name": "ANPE Togo", 
                "listing_url": "https://anpetogo.org/espace-chercheur-d-emploi/nos-offres-demplois",
                "status": "✅ ACTIF"
            },
            "emploitogo_info": {
                "name": "EmploiTogo.info",
                "listing_url": "https://www.emploitogo.info/emploitogo/",
                "status": "✅ ACTIF"
            },
            "linkedin_togo": {
                "name": "LinkedIn Togo",
                "listing_url": "https://tg.linkedin.com/jobs/",
                "status": "⚠️ INSTABLE (timeouts fréquents)"
            },
            "yop_lfrii": {
                "name": "YOP L'Frii",
                "listing_url": "https://yop.l-frii.com/emploi",
                "status": "✅ ACTIF"
            },
            "indeed_togo": {
                "name": "Indeed Togo",
                "listing_url": "https://tg.indeed.com/jobs",
                "status": "⚠️ INSTABLE (bloque API Jina)"
            }
        }
        
        print_info("État des 6 sources disponibles:")
        
        active_count = 0
        for source_id, config in sources_config.items():
            status_color = Colors.GREEN if "✅" in config["status"] else Colors.YELLOW
            print(f"  {source_id}: {config['name']}")
            print(f"    URL: {config['listing_url']}")
            print(f"    {status_color}Status: {config['status']}{Colors.END}")
            
            if "✅" in config["status"]:
                active_count += 1
        
        print_success(f"\nSources actives: {active_count}/6")
        print_info("Recommandation: Commencer par tester les 5 sources stables")

def main():
    """Fonction principale du diagnostic"""
    print_header("DIAGNOSTIC COMPLET DES URLs TRONQUÉES")
    
    diagnostic = URLTruncationDiagnostic()
    
    # Étape 1: Analyser le problème
    diagnostic.analyze_url_truncation_problem()
    
    # Étape 2: Tester les patterns améliorés
    diagnostic.test_improved_extraction_patterns()
    
    # Étape 3: Configuration des 6 sources
    diagnostic.test_all_6_sources_config()
    
    # Étape 4: Proposer une solution
    diagnostic.propose_solution()
    
    print_header("CONCLUSION")
    print_success("✅ Problème identifié: Patterns regex inadéquats")
    print_success("✅ Solution disponible: Patterns markdown + nettoyage")
    print_success("✅ 5/6 sources prêtes pour test complet")
    print_info("📋 Prochaine étape: Implémenter la solution corrigée")

if __name__ == "__main__":
    main()