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
from typing import Dict, List, Optional, Any
from bs4 import BeautifulSoup

class IntelligentExtractor:
    """Extracteur intelligent pour récupérer toutes les données disponibles"""
    
    def __init__(self):
        # Villes du Togo avec leurs régions
        self.villes_togo = {
            'lomé': 'Maritime', 'kpalimé': 'Plateaux', 'atakpamé': 'Plateaux',
            'sokodé': 'Centrale', 'kara': 'Kara', 'dapaong': 'Savanes',
            'tsévié': 'Maritime', 'aného': 'Maritime', 'bassar': 'Kara',
            'niamtougou': 'Kara', 'vogan': 'Maritime', 'tabligbo': 'Maritime'
        }
        
        # Patterns de reconnaissance
        self.company_patterns = [
            r"([A-Z][A-Za-z\s&\-\.]+(?:SARL|SA|SAS|EURL|GIE|ONG|Association|Groupe|Société|Entreprise))",
            r"(?:L'entreprise|La société|Le groupe|La compagnie)\s+([A-Z][A-Za-z\s&\-\.]+)",
            r"([A-Z][A-Za-z\s&\-\.]{3,})\s+(?:recrute|recherche|sollicite)",
            r"(?:Chez|Rejoignez)\s+([A-Z][A-Za-z\s&\-\.]+)",
            r"([A-Z][A-Z\s&\-\.]+)\s*-\s*(?:Togo|Lomé|Kara)"
        ]
        
        self.salary_patterns = [
            r"(\d+(?:\.\d+)?\s*(?:000|K)?\s*(?:à|-)?\s*\d*(?:\.\d+)?\s*(?:000|K)?\s*FCFA)",
            r"(?:salaire|rémunération|traitement)\s*:?\s*([^\n\r]{5,50})",
            r"(\d+\s*(?:000|K)?\s*FCFA\s*(?:net|brut)?)",
            r"(?:entre|de)\s+(\d+\s*(?:000|K)?\s*(?:à|et)\s*\d+\s*(?:000|K)?\s*FCFA)"
        ]
        
        self.contract_patterns = [
            r"\b(CDI|CDD|Stage|Freelance|Consultant|Temps partiel|Temps plein|Intérim|Vacation)\b",
            r"(?:contrat|type)\s*:?\s*(CDI|CDD|Stage|Freelance|Consultant)",
            r"\b(Stagiaire|Consultant|Freelancer|Employé|Cadre)\b"
        ]
        
        self.email_patterns = [
            r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
            r"(?:email|mail|contact)\s*:?\s*([A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,})"
        ]
        
        self.phone_patterns = [
            r"(?:\+228|228)?\s*\d{2}\s*\d{2}\s*\d{2}\s*\d{2}",
            r"(?:tel|téléphone|phone)\s*:?\s*((?:\+228|228)?\s*\d{2}\s*\d{2}\s*\d{2}\s*\d{2})"
        ]

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
            'salary': self._extract_salary(text_content, existing_data.get('salary')),
            'contract_type': self._extract_contract_type(text_content, existing_data.get('contract_type')),
            'contact_email': self._extract_email(text_content, existing_data.get('contact_email')),
            'contact_phone': self._extract_phone(text_content, existing_data.get('contact_phone')),
            'skills': self._extract_skills(text_content, soup, existing_data.get('skills')),
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

    def _extract_salary(self, text: str, existing: str = None) -> Optional[str]:
        """Extrait le salaire"""
        if existing and ('fcfa' in existing.lower() or 'cfa' in existing.lower()):
            return existing
            
        for pattern in self.salary_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                salary = match.group(1).strip()
                if len(salary) > 3:
                    return salary
        
        return existing

    def _extract_contract_type(self, text: str, existing: str = None) -> Optional[str]:
        """Extrait le type de contrat"""
        if existing and existing.upper() in ['CDI', 'CDD', 'STAGE', 'FREELANCE']:
            return existing
            
        for pattern in self.contract_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                contract = match.group(1).strip().upper()
                if contract in ['CDI', 'CDD', 'STAGE', 'FREELANCE', 'CONSULTANT']:
                    return contract
        
        # Détection par mots-clés
        text_lower = text.lower()
        if 'stage' in text_lower or 'stagiaire' in text_lower:
            return 'STAGE'
        elif 'freelance' in text_lower or 'consultant' in text_lower:
            return 'FREELANCE'
        elif 'cdi' in text_lower:
            return 'CDI'
        elif 'cdd' in text_lower:
            return 'CDD'
        
        return existing

    def _extract_email(self, text: str, existing: str = None) -> Optional[str]:
        """Extrait l'email de contact"""
        if existing and '@' in existing:
            return existing
            
        for pattern in self.email_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                email = match.group(1) if match.groups() else match.group(0)
                if '@' in email and '.' in email:
                    return email.strip()
        
        return existing

    def _extract_phone(self, text: str, existing: str = None) -> Optional[str]:
        """Extrait le numéro de téléphone"""
        if existing and len(existing) > 8:
            return existing
            
        for pattern in self.phone_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                phone = match.group(1) if match.groups() else match.group(0)
                # Nettoyer le numéro
                phone = re.sub(r'[^\d+]', '', phone)
                if len(phone) >= 8:
                    return phone
        
        return existing

    def _extract_skills(self, text: str, soup: BeautifulSoup, existing: str = None) -> Optional[str]:
        """Extrait les compétences requises"""
        if existing and len(existing) > 20:
            return existing
            
        # Chercher les listes de compétences
        skills_sections = soup.find_all(['ul', 'ol'], string=re.compile(r'compétence|skill|requis|profil', re.I))
        
        skills = []
        
        # Compétences techniques courantes
        tech_skills = [
            'Python', 'Java', 'JavaScript', 'PHP', 'C++', 'HTML', 'CSS', 'SQL',
            'Excel', 'Word', 'PowerPoint', 'Photoshop', 'AutoCAD', 'SAP',
            'Odoo', 'Sage', 'Comptabilité', 'Marketing', 'Communication'
        ]
        
        text_lower = text.lower()
        for skill in tech_skills:
            if skill.lower() in text_lower:
                skills.append(skill)
        
        # Patterns de compétences
        skill_patterns = [
            r"(?:compétences?|skills?)\s*:?\s*([^\n\r]{10,100})",
            r"(?:maîtrise|connaissance)\s+(?:de|en)\s+([A-Za-z\s,]+)",
            r"(?:expérience|expertise)\s+(?:en|avec)\s+([A-Za-z\s,]+)"
        ]
        
        for pattern in skill_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            for match in matches:
                if len(match) > 5:
                    skills.append(match.strip())
        
        if skills:
            return ', '.join(skills[:5])  # Limiter à 5 compétences
        
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