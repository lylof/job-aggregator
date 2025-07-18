#!/usr/bin/env python3
"""
EXTRACTEUR INTELLIGENT - Récupération automatique des données manquantes

Ce module analyse le contenu HTML et extrait intelligemment :
✅ Noms d'entreprises
✅ Localisations  
✅ Salaires
✅ Types de contrat
✅ Compétences requises
✅ Informations de contact
✅ Dates limites
✅ Et bien plus...

Usage: from crawler.utils.intelligent_extractor import IntelligentExtractor
"""

import re
import json
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup

class IntelligentExtractor:
    """Extracteur intelligent avec fallback robuste"""
    
    def __init__(self):
        # Villes du Togo avec leurs régions
        self.villes_togo = {
            'lomé': 'Maritime', 'kpalimé': 'Plateaux', 'atakpamé': 'Plateaux',
            'sokodé': 'Centrale', 'kara': 'Kara', 'dapaong': 'Savanes',
            'tsévié': 'Maritime', 'aného': 'Maritime', 'bassar': 'Kara',
            'niamtougou': 'Kara', 'vogan': 'Maritime', 'tabligbo': 'Maritime'
        }
        
        # Patterns pour extraction fallback
        self.salary_patterns = [
            r'(\d+\s*(?:000)?\s*-?\s*\d*\s*(?:000)?\s*(?:FCFA|F\s*CFA|francs?))',
            r'(Salaire\s*:?\s*[^\n]+)',
            r'(\d+\s*(?:millions?|k|K)\s*(?:FCFA|F\s*CFA)?)'
        ]
        
        self.contract_patterns = ['CDD', 'CDI', 'Stage', 'Freelance', 'Consultant', 'Temps partiel', 'Intérim']
        
        # AJOUT DES PATTERNS D'ENTREPRISES MANQUANTS
        self.company_patterns = [
            r"([A-Z][A-Za-z\s&-]+(?:SARL|SA|SAS|EURL|GIE|ONG|Association))",
            r"L'entreprise\s+([A-Z][A-Za-z\s&-]+)",
            r"La société\s+([A-Z][A-Za-z\s&-]+)",
            r"([A-Z][A-Za-z\s&-]+)\s+recrute",
            r"Entreprise\s*:?\s*([A-Z][A-Za-z\s&-]+)",
            r"Employeur\s*:?\s*([A-Z][A-Za-z\s&-]+)"
        ]
        
        self.company_selectors = [
            'h3 a[href*="/recruteur/"]',
            '.company-name', 
            '.card-block-company h3 a',
            '.company-info h3',
            'h2', 'h3'
        ]
        
        self.email_pattern = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        self.phone_patterns = [
            r'(\+228\s*\d{2}\s*\d{2}\s*\d{2}\s*\d{2})',
            r'(\d{2}\s*\d{2}\s*\d{2}\s*\d{2})'
        ]

    def extract_from_html(self, html_content: str, job_title: str = "") -> Dict[str, Any]:
        """Extraction fallback directe depuis le HTML"""
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            text = soup.get_text()
            
            extracted_data = {}
            
            # Extraction nom d'entreprise
            company = self._extract_company(soup)
            if company:
                extracted_data['company_name'] = company
                print(f"  📋 Entreprise: {company}")
            
            # Extraction salaire
            salary = self._extract_salary(text)
            if salary:
                extracted_data['salary'] = salary
                print(f"  💰 Salaire: {salary}")
            
            # Extraction type de contrat
            contract = self._extract_contract_type(text)
            if contract:
                extracted_data['employment_type'] = contract
                print(f"  📋 Contrat: {contract}")
            
            # Extraction email
            email = self._extract_email(text)
            if email:
                extracted_data['contact_email'] = email
                print(f"  📧 Email: {email}")
            
            # Extraction téléphone
            phone = self._extract_phone(text)
            if phone:
                extracted_data['contact_phone'] = phone
                print(f"  📞 Téléphone: {phone}")
            
            # Extraction compétences
            skills = self._extract_skills(soup, text)
            if skills:
                extracted_data['skills'] = skills
                print(f"  🎯 Compétences: {', '.join(skills[:3])}...")
            
            return extracted_data
            
        except Exception as e:
            print(f"  ❌ Erreur extraction HTML: {e}")
            return {}

    def _extract_company(self, soup: BeautifulSoup) -> Optional[str]:
        """Extrait le nom de l'entreprise"""
        for selector in self.company_selectors:
            try:
                element = soup.select_one(selector)
                if element and element.get_text(strip=True):
                    company = element.get_text(strip=True)
                    # Nettoyer le nom d'entreprise
                    company = re.sub(r'\s+', ' ', company)
                    if len(company) > 2 and not company.lower() in ['emploi', 'job', 'recrutement']:
                        return company
            except:
                continue
        return None

    def _extract_salary(self, text: str) -> Optional[str]:
        """Extrait le salaire"""
        for pattern in self.salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                salary = match.group(1).strip()
                # Nettoyer et valider
                if len(salary) > 3 and any(c.isdigit() for c in salary):
                    return salary
        return None

    def _extract_contract_type(self, text: str) -> Optional[str]:
        """Extrait le type de contrat"""
        for pattern in self.contract_patterns:
            if re.search(rf'\b{pattern}\b', text, re.IGNORECASE):
                return pattern
        return None

    def _extract_email(self, text: str) -> Optional[str]:
        """Extrait l'email de contact"""
        match = re.search(self.email_pattern, text)
        if match:
            email = match.group().lower()
            # Valider que ce n'est pas un email générique
            if not any(generic in email for generic in ['noreply', 'no-reply', 'example']):
                return email
        return None

    def _extract_phone(self, text: str) -> Optional[str]:
        """Extrait le numéro de téléphone"""
        for pattern in self.phone_patterns:
            match = re.search(pattern, text)
            if match:
                return match.group(1).strip()
        return None

    def _extract_skills(self, soup: BeautifulSoup, text: str) -> List[str]:
        """Extrait les compétences requises"""
        skills = []
        
        # Chercher dans les listes
        skill_sections = soup.find_all(['ul', 'ol'])
        for section in skill_sections:
            if any(keyword in section.get_text().lower() for keyword in ['compétence', 'skill', 'profil', 'qualification']):
                items = section.find_all('li')
                for item in items:
                    skill_text = item.get_text(strip=True)
                    if len(skill_text) > 2 and len(skill_text) < 100:
                        skills.append(skill_text)
        
        # Patterns de compétences communes
        skill_patterns = [
            r'(?:Maîtrise|Connaissance|Expérience)\s+(?:de|en|du)\s+([^.,\n]+)',
            r'(?:Diplôme|Formation)\s+en\s+([^.,\n]+)',
            r'(?:Bac\+?\d+)\s+en\s+([^.,\n]+)'
        ]
        
        for pattern in skill_patterns:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                skill = match.group(1).strip()
                if len(skill) > 2 and len(skill) < 50:
                    skills.append(skill)
        
        # Retourner les compétences uniques
        return list(set(skills))[:10]  # Limiter à 10 compétences

    def extract(self, html_content: str, job_title: str = "") -> Dict[str, Any]:
        """Point d'entrée principal pour l'extraction"""
        print("🧠 Extraction intelligente des données...")
        
        # Tentative d'extraction directe
        extracted_data = self.extract_from_html(html_content, job_title)
        
        if extracted_data:
            print("   └─ ✅ Données complétées intelligemment")
            for key, value in extracted_data.items():
                if isinstance(value, str) and len(value) > 50:
                    print(f"     📋 {key}: {value[:50]}...")
                elif isinstance(value, list):
                    print(f"     📋 {key}: {len(value)} éléments")
                else:
                    print(f"     📋 {key}: {value}")
        else:
            print("   └─ ⚠️  Aucune donnée supplémentaire extraite")
        
        return extracted_data

    def extract_all_data(self, html_content: str, existing_data: Dict[str, Any] = None) -> Dict[str, Any]:
        """Extrait intelligemment toutes les données disponibles du HTML"""
        
        if existing_data is None:
            existing_data = {}
        
        # Analyser le HTML
        soup = BeautifulSoup(html_content, 'html.parser')
        text_content = soup.get_text()
        
        # Extraire toutes les données
        extracted_data = {
            'company_name': self._extract_company_name(text_content, existing_data.get('company_name')),
            'location': self._extract_location(text_content, existing_data.get('location')),
            'salary': self._extract_salary(text_content),
            'contract_type': self._extract_contract_type(text_content),
            'contact_email': self._extract_email(text_content),
            'contact_phone': self._extract_phone(text_content),
            'skills': self._extract_skills(soup, text_content),
            'experience_level': self._extract_experience(text_content, existing_data.get('experience_level')),
            'education_level': self._extract_education(text_content, existing_data.get('education_level')),
            'application_deadline': self._extract_deadline(text_content, existing_data.get('application_deadline')),
            'sector': self._extract_sector(text_content, existing_data.get('sector')),
            'languages': self._extract_languages(text_content, existing_data.get('languages')),
            'remote_work_possible': self._detect_remote_work(text_content, existing_data.get('remote_work_possible'))
        }
        
        # Fusionner avec les données existantes (priorité aux nouvelles données si elles sont plus complètes)
        final_data = {}
        for key, new_value in extracted_data.items():
            existing_value = existing_data.get(key)
            
            # Garder la nouvelle valeur si elle est plus complète
            if new_value and (not existing_value or len(str(new_value)) > len(str(existing_value))):
                final_data[key] = new_value
            elif existing_value:
                final_data[key] = existing_value
        
        return final_data

    def _extract_company_name(self, text: str, existing: str = None) -> Optional[str]:
        """Extrait le nom de l'entreprise"""
        if existing and len(existing) > 5:
            return existing
            
        for pattern in self.company_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if isinstance(match, tuple):
                    match = match[0] if match[0] else match[1]
                
                # Nettoyer et valider
                company = match.strip()
                if len(company) > 3 and not company.lower() in ['emploi', 'togo', 'info', 'recrute']:
                    return company
        
        return existing

    def _extract_location(self, text: str, existing: str = None) -> Optional[str]:
        """Extrait la localisation"""
        if existing and len(existing) > 3:
            return existing
            
        text_lower = text.lower()
        
        # Chercher les villes du Togo
        for ville, region in self.villes_togo.items():
            if ville in text_lower:
                return f"{ville.title()}, {region}"
        
        # Patterns génériques
        location_patterns = [
            r"(?:à|basé|situé|localisé)\s+([A-Z][a-z]+)",
            r"([A-Z][a-z]+)\s*,\s*Togo",
            r"région\s+([A-Z][a-z]+)"
        ]
        
        for pattern in location_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return existing

    def _extract_experience(self, text: str, existing: str = None) -> Optional[str]:
        """Extrait le niveau d'expérience requis"""
        if existing and len(existing) > 5:
            return existing
            
        exp_patterns = [
            r"(\d+)\s*(?:ans?|années?)\s*(?:d'expérience|expérience)",
            r"(?:expérience|exp)\s*:?\s*(\d+\s*(?:ans?|années?))",
            r"(?:junior|senior|débutant|confirmé|expert)",
            r"(?:bac|bac\+\d+|\d+\s*années?\s*d'études)"
        ]
        
        for pattern in exp_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        
        return existing

    def _extract_education(self, text: str, existing: str = None) -> Optional[str]:
        """Extrait le niveau d'éducation requis"""
        if existing and len(existing) > 5:
            return existing
            
        edu_patterns = [
            r"(Bac\+\d+|Master|Licence|Doctorat|Ingénieur|Technicien)",
            r"(?:diplôme|formation)\s*:?\s*([^\n\r]{5,50})",
            r"(?:niveau|bac)\s*:?\s*([^\n\r]{5,30})"
        ]
        
        for pattern in edu_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                education = match.group(1) if match.groups() else match.group(0)
                return education.strip()
        
        return existing

    def _extract_deadline(self, text: str, existing: str = None) -> Optional[str]:
        """Extrait la date limite de candidature"""
        if existing and len(existing) > 5:
            return existing
            
        deadline_patterns = [
            r"(?:date limite|deadline|avant le|jusqu'au)\s*:?\s*(\d{1,2}[\/\-]\d{1,2}[\/\-]\d{4})",
            r"(?:candidature|dossier)\s*(?:avant|jusqu'au)\s*:?\s*([^\n\r]{5,30})"
        ]
        
        for pattern in deadline_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        return existing

    def _extract_sector(self, text: str, existing: str = None) -> Optional[str]:
        """Extrait le secteur d'activité"""
        if existing and len(existing) > 5:
            return existing
            
        sectors = [
            'Informatique', 'Finance', 'Banque', 'Assurance', 'Santé', 'Éducation',
            'Commerce', 'Marketing', 'Communication', 'Industrie', 'Agriculture',
            'Tourisme', 'Transport', 'Construction', 'Énergie', 'Télécommunications'
        ]
        
        text_lower = text.lower()
        for sector in sectors:
            if sector.lower() in text_lower:
                return sector
        
        return existing

    def _extract_languages(self, text: str, existing: str = None) -> Optional[str]:
        """Extrait les langues requises"""
        if existing and len(existing) > 5:
            return existing
            
        languages = ['Français', 'Anglais', 'Allemand', 'Espagnol', 'Portugais', 'Chinois']
        found_languages = []
        
        text_lower = text.lower()
        for lang in languages:
            if lang.lower() in text_lower:
                found_languages.append(lang)
        
        if found_languages:
            return ', '.join(found_languages)
        
        return existing

    def _detect_remote_work(self, text: str, existing: bool = None) -> bool:
        """Détecte si le télétravail est possible"""
        if existing is not None:
            return existing
            
        remote_keywords = [
            'télétravail', 'remote', 'distance', 'domicile', 'home office',
            'travail à distance', 'bureau à domicile', 'télétravail possible'
        ]
        
        text_lower = text.lower()
        for keyword in remote_keywords:
            if keyword in text_lower:
                return True
        
        return False 