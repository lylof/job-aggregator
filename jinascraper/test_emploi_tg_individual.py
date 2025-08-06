#!/usr/bin/env python3
"""Test pour analyser une page individuelle d'emploi.tg pour les dates."""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime

def test_individual_job_page():
    """Tester une page individuelle pour voir si elle contient des dates."""
    
    # URL d'un job spécifique (depuis les logs précédents)
    job_url = "https://www.emploi.tg/offre-emploi-togo/conseiller-clientele-bilingue-lome-326684"
    
    try:
        print('🔍 ANALYSE PAGE INDIVIDUELLE EMPLOI.TG')
        print('=' * 60)
        print(f"URL testée: {job_url}")
        print()
        
        response = requests.get(job_url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Chercher tous les textes qui pourraient contenir des dates
        all_text = soup.get_text()
        
        # Patterns de date plus spécifiques
        date_patterns = [
            r'publié.{0,20}(\d{1,2}/\d{1,2}/\d{4})',
            r'posté.{0,20}(\d{1,2}/\d{1,2}/\d{4})',
            r'créé.{0,20}(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{1,2}-\d{1,2}-\d{4})',
            r'(\d{4}-\d{2}-\d{2})',
            r'(il y a \d+ jour[s]?)',
            r'(il y a \d+ heure[s]?)',
            r'(hier)',
            r'(aujourd\'hui)',
            r'(\d{1,2}\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4})',
        ]
        
        print("📅 RECHERCHE DE DATES DANS LE CONTENU:")
        dates_found = []
        
        for pattern in date_patterns:
            matches = re.findall(pattern, all_text, re.IGNORECASE)
            if matches:
                dates_found.extend(matches)
                print(f"   Pattern '{pattern[:30]}...': {matches[:3]}")
        
        if not dates_found:
            print("   ❌ Aucune date trouvée avec les patterns")
        
        # Chercher des éléments spécifiques avec des classes/IDs liés aux dates
        print("\n🔍 RECHERCHE D'ÉLÉMENTS AVEC CLASSES DE DATE:")
        date_elements = soup.find_all(class_=re.compile(r'date|time|posted|created|published|meta', re.I))
        
        for elem in date_elements[:5]:
            text = elem.get_text(strip=True)
            if text:
                print(f"   {elem.name}.{elem.get('class', [])}: {text[:100]}")
        
        # Chercher dans les métadonnées
        print("\n📋 MÉTADONNÉES:")
        meta_elements = soup.find_all('meta')
        for meta in meta_elements:
            name = meta.get('name', '') + meta.get('property', '')
            if any(word in name.lower() for word in ['date', 'time', 'published', 'created']):
                print(f"   {name}: {meta.get('content', 'N/A')}")
        
        # Chercher des scripts JSON-LD (structured data)
        print("\n🔧 STRUCTURED DATA:")
        scripts = soup.find_all('script', type='application/ld+json')
        for script in scripts:
            try:
                import json
                data = json.loads(script.string)
                if 'datePosted' in str(data) or 'datePublished' in str(data):
                    print(f"   JSON-LD trouvé avec dates: {str(data)[:200]}...")
            except:
                pass
        
        # Afficher un échantillon du contenu pour analyse manuelle
        print("\n📄 ÉCHANTILLON DU CONTENU (premiers 500 chars):")
        print(all_text[:500])
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

if __name__ == "__main__":
    test_individual_job_page()