"""Service de filtrage temporel intelligent pour les offres d'emploi."""

import re
import json
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import structlog

logger = structlog.get_logger(__name__)


class TemporalFilterService:
    """Service de filtrage des offres selon leur date de publication."""
    
    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        self.last_scraping_key = "last_scraping_timestamp"
        
        # Parsers de date par source
        self.date_parsers = {
            'emploi_tg': self._parse_emploi_tg_date,
            # Autres sources à ajouter progressivement
        }
    
    async def should_process_job(
        self, 
        content: str, 
        url: str, 
        source_name: str,
        options: Any  # ScrapeOptions
    ) -> bool:
        """
        Déterminer si un job doit être traité selon sa date et les options.
        
        Args:
            content: Contenu extrait par Jina
            url: URL du job
            source_name: Nom de la source
            options: Options de scraping (ScrapeOptions)
            
        Returns:
            True si le job doit être traité
        """
        
        # Mode force : traiter tous les jobs
        if options.force_all:
            logger.info("Force mode enabled - processing all jobs", 
                       url=url, source=source_name)
            return True
        
        # Si pas de filtrage temporel demandé, comportement par défaut
        if not options.recent_only and not options.max_age_hours:
            logger.debug("No temporal filtering requested", 
                        url=url, source=source_name)
            return True
        
        # Parser la date de publication
        publication_date = await self._parse_publication_date(content, source_name)
        
        if not publication_date:
            # Si pas de date trouvée, traiter quand même (sécurité)
            logger.warning("No publication date found - processing anyway", 
                          url=url, source=source_name)
            return True
        
        # Calculer le timestamp de coupure
        cutoff_time = await self._get_cutoff_time(source_name, options)
        
        # Décision de filtrage
        should_process = publication_date >= cutoff_time
        age_hours = (datetime.utcnow() - publication_date).total_seconds() / 3600
        
        logger.info("Temporal filtering decision",
                   url=url,
                   source=source_name,
                   publication_date=publication_date.isoformat(),
                   cutoff_time=cutoff_time.isoformat(),
                   age_hours=round(age_hours, 1),
                   should_process=should_process,
                   filter_mode="recent_only" if options.recent_only else f"max_age_{options.max_age_hours}h")
        
        return should_process
    
    async def update_last_scraping_time(self, source_name: str, timestamp: datetime = None):
        """Mettre à jour le timestamp du dernier scraping."""
        if not timestamp:
            timestamp = datetime.utcnow()
        
        key = f"{self.last_scraping_key}:{source_name}"
        data = {
            'timestamp': timestamp.isoformat(),
            'source': source_name,
            'updated_at': datetime.utcnow().isoformat()
        }
        
        # Stocker pour 30 jours
        await self.cache_manager.redis_client.setex(
            key, 30 * 24 * 60 * 60, json.dumps(data)
        )
        
        logger.info("Last scraping timestamp updated", 
                   source=source_name, timestamp=timestamp.isoformat())
    
    async def _get_cutoff_time(self, source_name: str, options: Any) -> datetime:
        """Calculer le timestamp de coupure selon les options."""
        
        # Option max_age_hours a priorité
        if options.max_age_hours:
            cutoff = datetime.utcnow() - timedelta(hours=options.max_age_hours)
            logger.debug(f"Using max_age_hours cutoff", 
                        source=source_name, 
                        max_age_hours=options.max_age_hours,
                        cutoff=cutoff.isoformat())
            return cutoff
        
        # Mode recent_only : depuis le dernier scraping
        if options.recent_only:
            last_scraping = await self._get_last_scraping_time(source_name)
            
            if last_scraping:
                logger.debug("Using last scraping time as cutoff", 
                           source=source_name, cutoff=last_scraping.isoformat())
                return last_scraping
            else:
                # Premier scraping : 24h par défaut
                cutoff = datetime.utcnow() - timedelta(hours=24)
                logger.info("First scraping detected - using 24h default cutoff", 
                           source=source_name, cutoff=cutoff.isoformat())
                return cutoff
        
        # Fallback : 24h
        return datetime.utcnow() - timedelta(hours=24)
    
    async def _get_last_scraping_time(self, source_name: str) -> Optional[datetime]:
        """Récupérer le timestamp du dernier scraping."""
        key = f"{self.last_scraping_key}:{source_name}"
        
        try:
            data = await self.cache_manager.redis_client.get(key)
            if data:
                timestamp_data = json.loads(data)
                timestamp_str = timestamp_data['timestamp']
                return datetime.fromisoformat(timestamp_str)
        except Exception as e:
            logger.error("Failed to get last scraping time", 
                        source=source_name, error=str(e))
        
        return None
    
    async def _parse_publication_date(self, content: str, source_name: str) -> Optional[datetime]:
        """Parser la date de publication selon la source."""
        parser = self.date_parsers.get(source_name)
        
        if parser:
            try:
                return parser(content)
            except Exception as e:
                logger.error("Date parsing failed", 
                           source=source_name, error=str(e))
                return None
        else:
            logger.warning(f"No date parser available for source {source_name}")
            return None
    
    def _parse_emploi_tg_date(self, content: str) -> Optional[datetime]:
        """Parser spécialisé pour emploi.tg."""
        
        # Pattern principal : "Publiée le DD.MM.YYYY"
        pattern = r'Publiée le (\d{2})\.(\d{2})\.(\d{4})'
        match = re.search(pattern, content, re.IGNORECASE)
        
        if match:
            day, month, year = match.groups()
            try:
                return datetime(int(year), int(month), int(day))
            except ValueError as e:
                logger.error("Invalid date format in emploi.tg", 
                           day=day, month=month, year=year, error=str(e))
                return None
        
        # Patterns de fallback
        fallback_patterns = [
            r'(\d{1,2}/\d{1,2}/\d{4})',  # DD/MM/YYYY
            r'(\d{4}-\d{2}-\d{2})',      # YYYY-MM-DD
        ]
        
        for fallback in fallback_patterns:
            match = re.search(fallback, content)
            if match:
                date_str = match.group(1)
                try:
                    if '/' in date_str:
                        # Format DD/MM/YYYY
                        day, month, year = date_str.split('/')
                        return datetime(int(year), int(month), int(day))
                    elif '-' in date_str:
                        # Format YYYY-MM-DD
                        return datetime.fromisoformat(date_str)
                except ValueError:
                    continue
        
        return None
    
    async def get_filtering_stats(self, source_name: str) -> Dict[str, Any]:
        """Obtenir des statistiques sur le filtrage temporel."""
        last_scraping = await self._get_last_scraping_time(source_name)
        
        stats = {
            'source': source_name,
            'has_last_scraping': last_scraping is not None,
            'last_scraping_time': last_scraping.isoformat() if last_scraping else None,
            'hours_since_last_scraping': None,
            'available_parsers': list(self.date_parsers.keys()),
            'has_parser': source_name in self.date_parsers
        }
        
        if last_scraping:
            hours_since = (datetime.utcnow() - last_scraping).total_seconds() / 3600
            stats['hours_since_last_scraping'] = round(hours_since, 1)
        
        return stats