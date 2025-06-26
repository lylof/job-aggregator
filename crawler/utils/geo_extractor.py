#!/usr/bin/env python3
"""
Extracteur de géolocalisation intelligent pour le Togo et l'Afrique de l'Ouest
"""

import re
from typing import Dict, Optional, Tuple, List

class GeoExtractor:
    """Extrait et normalise les informations géographiques des offres d'emploi"""
    
    # Villes principales du Togo avec coordonnées approximatives
    TOGO_CITIES = {
        'lomé': {'lat': 6.1319, 'lng': 1.2228, 'region': 'Maritime', 'canonical': 'Lomé'},
        'kara': {'lat': 9.5511, 'lng': 1.1875, 'region': 'Kara', 'canonical': 'Kara'},
        'sokodé': {'lat': 8.9833, 'lng': 1.1333, 'region': 'Centrale', 'canonical': 'Sokodé'},
        'kpalimé': {'lat': 6.9000, 'lng': 0.6333, 'region': 'Plateaux', 'canonical': 'Kpalimé'},
        'atakpamé': {'lat': 7.5333, 'lng': 1.1333, 'region': 'Plateaux', 'canonical': 'Atakpamé'},
        'bassar': {'lat': 9.2500, 'lng': 0.7833, 'region': 'Kara', 'canonical': 'Bassar'},
        'tsévié': {'lat': 6.4267, 'lng': 1.2133, 'region': 'Maritime', 'canonical': 'Tsévié'},
        'aného': {'lat': 6.2333, 'lng': 1.6000, 'region': 'Maritime', 'canonical': 'Aného'},
        'mango': {'lat': 10.3553, 'lng': 0.4719, 'region': 'Savanes', 'canonical': 'Mango'},
        'dapaong': {'lat': 10.8633, 'lng': 0.2072, 'region': 'Savanes', 'canonical': 'Dapaong'},
    }
    
    # Variantes courantes des noms de villes
    CITY_VARIANTS = {
        'lome': 'lomé',
        'lomê': 'lomé',
        'sokode': 'sokodé',
        'kpalime': 'kpalimé',
        'atakpame': 'atakpamé',
        'tsevie': 'tsévié',
        'aneho': 'aného',
    }
    
    # Patterns pour détecter le travail à distance
    REMOTE_PATTERNS = [
        r'télétravail',
        r'tele[- ]?travail',
        r'travail[- ]?(?:à|a)[- ]?distance',
        r'remote[- ]?work',
        r'home[- ]?office',
        r'en[- ]?ligne',
        r'virtuel',
        r'distanciel'
    ]
    
    # Patterns pour détecter les détails de localisation
    LOCATION_PATTERNS = [
        r'(?:à|en|sur|dans)\s+([a-zA-ZÀ-ÿ\-\s]{2,25})',  # "à Lomé", "en ville"
        r'ville[:\s]+([a-zA-ZÀ-ÿ\-\s]{2,25})',           # "Ville: Lomé"
        r'lieu[:\s]+([a-zA-ZÀ-ÿ\-\s]{2,25})',            # "Lieu: Kara"
        r'localisation[:\s]+([a-zA-ZÀ-ÿ\-\s]{2,25})',    # "Localisation: Sokodé"
        r'([a-zA-ZÀ-ÿ\-]{3,15})[,\s]*togo',              # "Lomé, Togo"
    ]
    
    def __init__(self):
        """Initialise l'extracteur de géolocalisation"""
        pass
    
    def extract_location_info(self, text: str) -> Dict[str, any]:
        """
        Extrait les informations de localisation d'un texte
        
        Args:
            text: Texte à analyser (titre + description)
            
        Returns:
            Dict avec city, region, coordinates, is_remote, raw_location
        """
        if not text:
            return self._empty_location()
        
        text_clean = self._normalize_text(text.lower())
        
        # 1. Détecter le télétravail
        is_remote = self._detect_remote_work(text_clean)
        
        # 2. Extraire la ville principale
        city_info = self._extract_city(text_clean)
        
        # 3. Extraire la localisation brute pour debug
        raw_location = self._extract_raw_location(text_clean)
        
        result = {
            'city': city_info.get('canonical'),
            'region': city_info.get('region'),
            'latitude': city_info.get('lat'),
            'longitude': city_info.get('lng'),
            'is_remote': is_remote,
            'raw_location': raw_location,
            'country': 'Togo'  # Par défaut pour ce projet
        }
        
        # Log pour debug
        if city_info.get('canonical'):
            print(f"[GEO] Ville détectée: {city_info['canonical']} ({city_info.get('region')})")
        if is_remote:
            print(f"[GEO] Télétravail détecté")
        
        return result
    
    def _normalize_text(self, text: str) -> str:
        """Normalise le texte pour améliorer la détection"""
        # Supprimer les accents pour la recherche
        replacements = {
            'é': 'e', 'è': 'e', 'ê': 'e', 'ë': 'e',
            'à': 'a', 'â': 'a', 'ä': 'a',
            'ô': 'o', 'ö': 'o',
            'ù': 'u', 'û': 'u', 'ü': 'u',
            'ç': 'c', 'ñ': 'n'
        }
        
        normalized = text
        for old, new in replacements.items():
            normalized = normalized.replace(old, new)
        
        return normalized
    
    def _detect_remote_work(self, text: str) -> bool:
        """Détecte si l'offre propose du télétravail"""
        for pattern in self.REMOTE_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        return False
    
    def _extract_city(self, text: str) -> Dict[str, any]:
        """Extrait la ville principale du texte"""
        
        # 1. Recherche directe des villes connues
        for city_key, city_data in self.TOGO_CITIES.items():
            # Recherche avec word boundaries
            pattern = r'\b' + re.escape(city_key) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                return city_data
        
        # 2. Recherche des variantes
        for variant, canonical_key in self.CITY_VARIANTS.items():
            pattern = r'\b' + re.escape(variant) + r'\b'
            if re.search(pattern, text, re.IGNORECASE):
                return self.TOGO_CITIES.get(canonical_key, {})
        
        # 3. Recherche avec patterns contextuels
        for pattern in self.LOCATION_PATTERNS:
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                location_candidate = match.group(1).strip()
                # Vérifier si c'est une ville connue
                location_clean = self._normalize_text(location_candidate.lower())
                if location_clean in self.TOGO_CITIES:
                    return self.TOGO_CITIES[location_clean]
                # Vérifier les variantes
                if location_clean in self.CITY_VARIANTS:
                    canonical_key = self.CITY_VARIANTS[location_clean]
                    return self.TOGO_CITIES.get(canonical_key, {})
        
        return {}
    
    def _extract_raw_location(self, text: str) -> Optional[str]:
        """Extrait la mention de localisation brute pour debug"""
        
        # Patterns pour capturer des mentions de lieu
        location_keywords = ['lieu', 'ville', 'localisation', 'adresse', 'région']
        
        for keyword in location_keywords:
            # Recherche "keyword: value"
            pattern = rf'{keyword}[:\s]+([^.;,\n]{{5,50}})'
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
        
        # Recherche de patterns géographiques génériques
        geo_patterns = [
            r'(?:situé|située|basé|localisé)[^.;,\n]{5,50}',
            r'(?:dans|à|en)\s+[A-ZÀ-ÿ][a-zA-ZÀ-ÿ\s-]{2,25}(?:[,.]|$)',
        ]
        
        for pattern in geo_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return match.group(0).strip()
        
        return None
    
    def _empty_location(self) -> Dict[str, any]:
        """Retourne une localisation vide"""
        return {
            'city': None,
            'region': None,
            'latitude': None,
            'longitude': None,
            'is_remote': False,
            'raw_location': None,
            'country': 'Togo'
        }
    
    def get_distance_between_cities(self, city1: str, city2: str) -> Optional[float]:
        """
        Calcule la distance approximative entre deux villes (en km)
        
        Args:
            city1, city2: Noms des villes
            
        Returns:
            Distance en kilomètres ou None si villes non trouvées
        """
        city1_norm = self._normalize_text(city1.lower())
        city2_norm = self._normalize_text(city2.lower())
        
        # Chercher dans les variantes aussi
        if city1_norm in self.CITY_VARIANTS:
            city1_norm = self.CITY_VARIANTS[city1_norm]
        if city2_norm in self.CITY_VARIANTS:
            city2_norm = self.CITY_VARIANTS[city2_norm]
        
        city1_data = self.TOGO_CITIES.get(city1_norm)
        city2_data = self.TOGO_CITIES.get(city2_norm)
        
        if not city1_data or not city2_data:
            return None
        
        # Formule de distance approximative (Haversine simplifiée)
        lat1, lng1 = city1_data['lat'], city1_data['lng']
        lat2, lng2 = city2_data['lat'], city2_data['lng']
        
        # Approximation simple pour de petites distances
        deg_to_km = 111  # 1 degré ≈ 111 km
        delta_lat = abs(lat2 - lat1)
        delta_lng = abs(lng2 - lng1)
        
        distance = ((delta_lat ** 2 + delta_lng ** 2) ** 0.5) * deg_to_km
        return round(distance, 1)
    
    def suggest_nearby_cities(self, city: str, max_distance: float = 50.0) -> List[str]:
        """
        Suggère des villes proches d'une ville donnée
        
        Args:
            city: Ville de référence
            max_distance: Distance maximale en km
            
        Returns:
            Liste des villes proches
        """
        city_norm = self._normalize_text(city.lower())
        reference_city = self.TOGO_CITIES.get(city_norm)
        
        if not reference_city:
            return []
        
        nearby = []
        for other_city, other_data in self.TOGO_CITIES.items():
            if other_city == city_norm:
                continue
            
            distance = self.get_distance_between_cities(city, other_data['canonical'])
            if distance and distance <= max_distance:
                nearby.append(other_data['canonical'])
        
        return nearby 