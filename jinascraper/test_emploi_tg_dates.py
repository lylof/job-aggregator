#!/usr/bin/env python3
"""Test pour analyser la structure des dates sur emploi.tg"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime, timedelta

def analyze_emploi_tg_structure():
    """Analyser la structure HTML d'emploi.tg pour trouver les dates."""
    
    url = 'https://www.emploi.tg/recherche-jobs-togo'
    
    try:
        print('🔍 ANALYSE STRUCTURE EMPLOI.TG POUR DATES')
        print('=' * 60)
        
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Chercher les éléments de job
        job_elements = soup.select('h3 > a')[:5]  # Premiers 5 jobs
        
        print(f"✅ Trouvé {len(job_elements)} éléments de job")
        print()
        
        for i, job_link in enumerate(job_elements, 1):
            print(f"📋 JOB {i}:")
            print(f"   URL: {job_link.get('href', 'N/A')}")
            print(f"   Titre: {job_link.get_text(strip=True)[:60]}...")
            
            # Analyser la structure autour du job
            analyze_job_context(job_link, i)
            print("-" * 50)
        
        # Analyser la structure générale de la page
        print("\n🔍 ANALYSE STRUCTURE GÉNÉRALE:")
        analyze_page_structure(soup)
        
    except Exception as e:
        print(f"❌ Erreur: {e}")

def analyze_job_context(job_link, job_num):
    """Analyser le contexte autour d'un lien de job pour trouver des dates."""
    
    # Remonter dans la hiérarchie pour trouver le conteneur du job
    current = job_link
    for level in range(5):  # Remonter jusqu'à 5 niveaux
        if current.parent:
            current = current.parent
            
            # Chercher des dates dans ce niveau
            text_content = current.get_text()
            date_patterns = find_date_patterns(text_content)
            
            if date_patterns:
                print(f"   📅 Niveau {level+1}: {date_patterns[:2]}")
                
            # Chercher des éléments avec classes liées aux dates
            date_elements = current.find_all(class_=re.compile(r'date|time|posted|created', re.I))
            if date_elements:
                for elem in date_elements[:2]:
                    print(f"   🕒 Élément date: {elem.get_text(strip=True)}")

def find_date_patterns(text):
    """Trouver des patterns de date dans le texte."""
    
    date_patterns = []
    
    # Patterns français courants
    patterns = [
        r'\d{1,2}/\d{1,2}/\d{4}',  # 05/08/2025
        r'\d{1,2}-\d{1,2}-\d{4}',  # 05-08-2025
        r'\d{1,2}\s+(janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)\s+\d{4}',
        r'(hier|aujourd\'hui|il y a \d+ jour|il y a \d+ heure)',
        r'\d{4}-\d{2}-\d{2}',  # 2025-08-05
        r'(lundi|mardi|mercredi|jeudi|vendredi|samedi|dimanche)',
        r'il y a \d+',
        r'\d+ jour',
        r'\d+ heure',
    ]
    
    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE)
        date_patterns.extend(matches)
    
    return list(set(date_patterns))  # Supprimer les doublons

def analyze_page_structure(soup):
    """Analyser la structure générale de la page."""
    
    # Chercher des conteneurs de jobs
    job_containers = soup.find_all(['div', 'article', 'section'], class_=re.compile(r'job|offer|card', re.I))
    print(f"   Conteneurs de jobs potentiels: {len(job_containers)}")
    
    # Chercher des éléments avec des classes de date
    date_elements = soup.find_all(class_=re.compile(r'date|time|posted|created|published', re.I))
    print(f"   Éléments avec classes de date: {len(date_elements)}")
    
    if date_elements:
        for elem in date_elements[:3]:
            print(f"     - {elem.name}.{elem.get('class', [])} : {elem.get_text(strip=True)[:50]}")
    
    # Chercher des attributs data-* liés aux dates
    data_date_elements = soup.find_all(attrs={'data-date': True}) + soup.find_all(attrs={'data-time': True})
    if data_date_elements:
        print(f"   Éléments avec data-date/time: {len(data_date_elements)}")

if __name__ == "__main__":
    analyze_emploi_tg_structure()