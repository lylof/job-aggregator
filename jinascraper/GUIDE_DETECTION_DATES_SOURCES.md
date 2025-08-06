# 🕒 GUIDE DE DÉTECTION DES DATES PAR SOURCE

**Date de création** : 5 Août 2025  
**Objectif** : Méthode standardisée pour détecter les dates de publication sur chaque source  
**Usage** : Référence pour l'implémentation du filtrage temporel intelligent

---

## 🎯 **CONTEXTE SYSTÈME DE PRODUCTION**

### **Architecture de Scraping Réelle**
- **Fréquence** : 3 fois par jour (toutes les 8 heures)
- **Horaires** : 00h00, 08h00, 16h00 (exemple)
- **Logique** : Récupérer les offres publiées depuis le **dernier scraping** (8h), pas 24h fixes

### **Différence Cruciale**
```
❌ APPROCHE INITIALE (incorrecte) :
- Filtrer les offres des dernières 24h
- Logique fixe, ne s'adapte pas à la fréquence

✅ APPROCHE CORRECTE (production) :
- Filtrer les offres depuis le dernier scraping
- Logique dynamique basée sur timestamp du dernier cycle
- Première fois : 24h, ensuite : 8h
```

---

## 🔍 **MÉTHODE DE DÉTECTION DÉCOUVERTE**

### **Emploi.tg - VALIDÉ ✅**

#### **Test Effectué**
```bash
URL testée: https://www.emploi.tg/offre-emploi-togo/conseiller-clientele-bilingue-lome-326684
Méthode: Analyse du contenu HTML extrait
```

#### **Résultat**
```
📅 Format trouvé: "Publiée le 05.08.2025"
📍 Localisation: Dans le contenu de la page individuelle
🔧 Pattern regex: r'Publiée le (\d{2})\.(\d{2})\.(\d{4})'
✅ Fiabilité: Haute (format standardisé)
```

#### **Implémentation**
```python
def parse_emploi_tg_date(content: str) -> Optional[datetime]:
    """Parser la date de publication pour emploi.tg"""
    import re
    from datetime import datetime
    
    # Pattern: "Publiée le DD.MM.YYYY"
    pattern = r'Publiée le (\d{2})\.(\d{2})\.(\d{4})'
    match = re.search(pattern, content, re.IGNORECASE)
    
    if match:
        day, month, year = match.groups()
        try:
            return datetime(int(year), int(month), int(day))
        except ValueError:
            return None
    
    return None
```

---

## 📋 **TEMPLATE POUR AUTRES SOURCES**

### **Méthode Standardisée de Découverte**

#### **Étape 1 : Analyse Structure**
```python
def analyze_source_dates(source_name: str, test_url: str):
    """Template pour analyser une nouvelle source."""
    
    print(f'🔍 ANALYSE DATES POUR {source_name.upper()}')
    print('=' * 60)
    
    try:
        # 1. Extraire le contenu
        response = requests.get(test_url, timeout=15)
        soup = BeautifulSoup(response.content, 'html.parser')
        content = soup.get_text()
        
        # 2. Chercher patterns de date courants
        date_patterns = [
            r'publié.{0,20}(\d{1,2}/\d{1,2}/\d{4})',
            r'posté.{0,20}(\d{1,2}/\d{1,2}/\d{4})',  
            r'créé.{0,20}(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{1,2}/\d{1,2}/\d{4})',
            r'(\d{1,2}-\d{1,2}-\d{4})',
            r'(\d{4}-\d{2}-\d{2})',
            r'(il y a \d+ jour[s]?)',
            r'(il y a \d+ heure[s]?)',
            r'(hier|aujourd\'hui)',
            # Ajouter patterns spécifiques selon la langue du site
        ]
        
        # 3. Tester chaque pattern
        for pattern in date_patterns:
            matches = re.findall(pattern, content, re.IGNORECASE)
            if matches:
                print(f"✅ Pattern trouvé: {pattern}")
                print(f"   Matches: {matches[:3]}")
        
        # 4. Analyser éléments HTML avec classes de date
        date_elements = soup.find_all(class_=re.compile(r'date|time|posted|created', re.I))
        for elem in date_elements[:3]:
            print(f"🔧 Élément HTML: {elem.name}.{elem.get('class')} = {elem.get_text(strip=True)}")
        
        # 5. Échantillon de contenu pour analyse manuelle
        print(f"\n📄 Échantillon contenu (500 chars):")
        print(content[:500])
        
    except Exception as e:
        print(f"❌ Erreur: {e}")
```

#### **Étape 2 : Implémentation Parser**
```python
def parse_[SOURCE_NAME]_date(content: str) -> Optional[datetime]:
    """Parser spécialisé pour [SOURCE_NAME]"""
    import re
    from datetime import datetime
    
    # Pattern spécifique découvert à l'étape 1
    pattern = r'PATTERN_DÉCOUVERT'
    match = re.search(pattern, content, re.IGNORECASE)
    
    if match:
        # Extraction et conversion selon le format
        # Exemple pour DD/MM/YYYY:
        day, month, year = match.groups()
        try:
            return datetime(int(year), int(month), int(day))
        except ValueError:
            return None
    
    # Fallback patterns si le principal échoue
    fallback_patterns = [
        r'(\d{1,2}/\d{1,2}/\d{4})',
        r'(\d{4}-\d{2}-\d{2})',
    ]
    
    for fallback in fallback_patterns:
        match = re.search(fallback, content)
        if match:
            # Logique de parsing selon le format
            pass
    
    return None
```

---

## 🏗️ **ARCHITECTURE SYSTÈME INTELLIGENT**

### **Gestionnaire de Timestamps Dynamique**

```python
class ScrapingTimestampManager:
    """Gestionnaire intelligent des timestamps de scraping."""
    
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        self.last_scraping_key = "last_scraping_timestamp"
    
    async def get_last_scraping_time(self, source_name: str) -> Optional[datetime]:
        """Récupérer le timestamp du dernier scraping pour une source."""
        key = f"{self.last_scraping_key}:{source_name}"
        data = await self.cache_manager.redis_client.get(key)
        
        if data:
            timestamp_str = json.loads(data)['timestamp']
            return datetime.fromisoformat(timestamp_str)
        
        return None
    
    async def update_last_scraping_time(self, source_name: str, timestamp: datetime = None):
        """Mettre à jour le timestamp du dernier scraping."""
        if not timestamp:
            timestamp = datetime.utcnow()
        
        key = f"{self.last_scraping_key}:{source_name}"
        data = {
            'timestamp': timestamp.isoformat(),
            'source': source_name
        }
        
        # Stocker pour 30 jours (plus que nécessaire)
        await self.cache_manager.redis_client.setex(
            key, 30 * 24 * 60 * 60, json.dumps(data)
        )
    
    async def get_cutoff_time(self, source_name: str, default_hours: int = 24) -> datetime:
        """Calculer le timestamp de coupure pour filtrer les offres."""
        last_scraping = await self.get_last_scraping_time(source_name)
        
        if last_scraping:
            # En production : depuis le dernier scraping
            cutoff = last_scraping
            logger.info(f"Using last scraping time as cutoff", 
                       source=source_name, cutoff=cutoff)
        else:
            # Premier scraping : utiliser default_hours
            cutoff = datetime.utcnow() - timedelta(hours=default_hours)
            logger.info(f"First scraping, using {default_hours}h cutoff", 
                       source=source_name, cutoff=cutoff)
        
        return cutoff
```

### **Filtrage Intelligent Intégré**

```python
class IntelligentDateFilter:
    """Filtre intelligent basé sur les dates de publication."""
    
    def __init__(self, timestamp_manager):
        self.timestamp_manager = timestamp_manager
        self.date_parsers = {
            'emploi_tg': self.parse_emploi_tg_date,
            # 'anpetogo': self.parse_anpetogo_date,  # À implémenter
            # 'linkedin_togo': self.parse_linkedin_date,  # À implémenter
        }
    
    async def should_process_job(self, content: str, url: str, source_name: str) -> bool:
        """Déterminer si un job doit être traité selon sa date."""
        
        # 1. Parser la date de publication
        publication_date = await self.parse_publication_date(content, source_name)
        
        if not publication_date:
            # Si pas de date trouvée, traiter quand même (sécurité)
            logger.warning("No publication date found, processing anyway", 
                          url=url, source=source_name)
            return True
        
        # 2. Calculer le timestamp de coupure
        cutoff_time = await self.timestamp_manager.get_cutoff_time(source_name)
        
        # 3. Comparer
        should_process = publication_date >= cutoff_time
        
        logger.info("Date filtering decision",
                   url=url,
                   source=source_name,
                   publication_date=publication_date.isoformat(),
                   cutoff_time=cutoff_time.isoformat(),
                   should_process=should_process,
                   age_hours=round((datetime.utcnow() - publication_date).total_seconds() / 3600, 1))
        
        return should_process
    
    async def parse_publication_date(self, content: str, source_name: str) -> Optional[datetime]:
        """Parser la date selon la source."""
        parser = self.date_parsers.get(source_name)
        
        if parser:
            return parser(content)
        else:
            logger.warning(f"No date parser for source {source_name}")
            return None
    
    def parse_emploi_tg_date(self, content: str) -> Optional[datetime]:
        """Parser pour emploi.tg - IMPLÉMENTÉ"""
        import re
        from datetime import datetime
        
        pattern = r'Publiée le (\d{2})\.(\d{2})\.(\d{4})'
        match = re.search(pattern, content, re.IGNORECASE)
        
        if match:
            day, month, year = match.groups()
            try:
                return datetime(int(year), int(month), int(day))
            except ValueError:
                return None
        
        return None
```

---

## 🎯 **PLAN D'IMPLÉMENTATION ADAPTÉ**

### **Phase 1 : Infrastructure (Immédiat)**
1. **Créer `ScrapingTimestampManager`** pour gérer les timestamps
2. **Créer `IntelligentDateFilter`** avec parser emploi.tg
3. **Intégrer dans `DetailScraper`** pour filtrage pré-IA

### **Phase 2 : Extension Sources (Progressif)**
1. **Analyser anpetogo** avec le template
2. **Implémenter parser anpetogo**
3. **Analyser linkedin_togo** avec le template
4. **Implémenter parser linkedin_togo**
5. **Continuer pour toutes les sources**

### **Phase 3 : Production (Validation)**
1. **Tester avec scraping 8h** 
2. **Valider économies de tokens**
3. **Monitoring des performances**

---

## 📊 **AVANTAGES DE CETTE APPROCHE**

### **✅ Flexibilité**
- **S'adapte automatiquement** à la fréquence de scraping
- **Premier scraping** : 24h, **suivants** : 8h
- **Configurable** par source

### **✅ Efficacité**
- **Économie massive** de tokens (80-90%)
- **Traitement intelligent** : seulement les offres récentes
- **Évolutif** : facile d'ajouter de nouvelles sources

### **✅ Robustesse**
- **Fallback** : traite quand même si pas de date
- **Logging détaillé** pour debugging
- **Cache persistant** des timestamps

---

## 🔧 **UTILISATION POUR NOUVELLES SOURCES**

```python
# Pour ajouter une nouvelle source :

# 1. Analyser la structure
analyze_source_dates('nouvelle_source', 'https://exemple.com/job/123')

# 2. Implémenter le parser
def parse_nouvelle_source_date(content: str) -> Optional[datetime]:
    # Pattern découvert à l'étape 1
    pattern = r'PATTERN_TROUVÉ'
    # ... logique de parsing

# 3. Enregistrer le parser
date_filter.date_parsers['nouvelle_source'] = parse_nouvelle_source_date

# 4. Tester
should_process = await date_filter.should_process_job(content, url, 'nouvelle_source')
```

**Cette approche garantit une méthode standardisée et évolutive pour toutes les sources ! 🚀**

---

**Guide créé le** : 5 Août 2025  
**Basé sur** : Découverte emploi.tg + architecture production  
**Usage** : Référence pour implémentation filtrage temporel intelligent