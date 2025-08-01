"""
JinaScraper Application - Main orchestrator class for CLI interface.
"""

import asyncio
import time
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any
import structlog

from .core.orchestrator import ScrapingOrchestrator
from .models import ScrapingResult
from .utils.enhanced_logger import create_logger


logger = structlog.get_logger(__name__)


@dataclass
class ScrapeOptions:
    """Configuration options for scraping operations."""
    sources: Optional[List[str]] = None  # --sources
    max_urls: int = 100                  # --max-urls
    dry_run: bool = False               # --dry-run
    verbose: bool = False               # --verbose
    quiet: bool = False                 # --quiet
    show_urls: int = 3                  # --show-urls
    use_colors: bool = True             # --no-color (inverted)


@dataclass
class ScrapeResults:
    """Results from a scraping operation."""
    success: bool
    jobs_processed: int
    sources_processed: int
    processing_time_seconds: float
    errors: List[str]
    scraping_result: Optional[ScrapingResult] = None


class JinaScraperApp:
    """
    Main application class that orchestrates scraping operations.
    
    This class serves as a thin wrapper around the core orchestrator,
    providing a clean interface for CLI operations.
    """
    
    def __init__(self):
        """Initialize the JinaScraper application."""
        self.orchestrator = None
        self.enhanced_logger = None
        logger.info("JinaScraperApp initialized")
    
    async def run_full_scrape(self, options: ScrapeOptions) -> ScrapeResults:
        """
        Execute a full scraping cycle with the given options.
        
        Args:
            options: Configuration options for the scraping operation
            
        Returns:
            ScrapeResults containing the outcome and metrics
        """
        start_time = time.time()
        errors = []
        
        # Initialize enhanced logger
        self.enhanced_logger = create_logger(
            verbose=options.verbose,
            quiet=options.quiet,
            use_colors=options.use_colors,
            show_urls=options.show_urls
        )
        
        # Print startup header
        self.enhanced_logger.print_header("JINASCRAPER - DÉMARRAGE")
        
        # Print configuration
        config = {
            "Sources": options.sources or ["Toutes"],
            "URLs max": options.max_urls,
            "Mode": "Dry-run" if options.dry_run else "Production",
            "Verbosité": "Verbose" if options.verbose else ("Quiet" if options.quiet else "Normal")
        }
        self.enhanced_logger.print_configuration(config)
        
        try:
            # Initialize orchestrator with async context manager
            async with ScrapingOrchestrator() as orchestrator:
                self.orchestrator = orchestrator
                
                # Pass enhanced logger to orchestrator
                orchestrator.set_enhanced_logger(self.enhanced_logger)
                
                # Configure orchestrator based on options
                if options.sources:
                    self.enhanced_logger.print_info(f"Filtrage des sources: {options.sources}")
                
                if options.dry_run:
                    self.enhanced_logger.print_info("Mode dry-run activé - aucune donnée ne sera sauvegardée")
                
                # Execute the scraping cycle with source filtering
                scraping_result = await orchestrator.run_full_cycle(sources_filter=options.sources)
                
                # Calculate processing time
                processing_time = time.time() - start_time
                
                # Build results
                results = ScrapeResults(
                    success=scraping_result.success,
                    jobs_processed=scraping_result.jobs_processed,
                    sources_processed=len(options.sources) if options.sources else 1,
                    processing_time_seconds=processing_time,
                    errors=errors,
                    scraping_result=scraping_result
                )
                
                # Print final report
                self.enhanced_logger.print_final_report(
                    success=results.success,
                    jobs_processed=results.jobs_processed,
                    sources_processed=results.sources_processed,
                    duration=results.processing_time_seconds,
                    errors=results.errors
                )
                
                return results
                
        except Exception as e:
            error_msg = f"Scraping failed: {str(e)}"
            errors.append(error_msg)
            logger.error(error_msg, exc_info=True)
            
            return ScrapeResults(
                success=False,
                jobs_processed=0,
                sources_processed=0,
                processing_time_seconds=time.time() - start_time,
                errors=errors
            )
    
    def generate_scrape_report(self, results: ScrapeResults, options: ScrapeOptions) -> bool:
        """
        Generate and display a scraping report.
        
        Args:
            results: Results from the scraping operation
            options: Original scraping options
            
        Returns:
            bool: True if report generation succeeded
        """
        try:
            print("\n" + "="*60)
            print("🔍 JINASCRAPER REPORT")
            print("="*60)
            
            # Basic metrics
            print(f"✅ Status: {'SUCCESS' if results.success else 'FAILED'}")
            print(f"📊 Jobs Processed: {results.jobs_processed}")
            print(f"🌐 Sources Processed: {results.sources_processed}")
            print(f"⏱️  Processing Time: {results.processing_time_seconds:.2f}s")
            
            # Options used
            print(f"\n📋 Configuration:")
            print(f"   Sources Filter: {options.sources or 'All'}")
            print(f"   Max URLs: {options.max_urls}")
            print(f"   Dry Run: {options.dry_run}")
            print(f"   Verbose: {options.verbose}")
            
            # Detailed results if available
            if results.scraping_result:
                sr = results.scraping_result
                print(f"\n📈 Detailed Metrics:")
                print(f"   Success Rate: {(sr.jobs_processed / max(sr.jobs_found, 1)) * 100:.1f}%")
                print(f"   Jobs Found: {sr.jobs_found}")
                print(f"   Processing Time: {sr.processing_time_seconds:.2f}s")
                print(f"   Source Site: {sr.source_site}")
                print(f"   Timestamp: {sr.timestamp}")

            
            # Errors if any
            if results.errors:
                print(f"\n❌ Errors ({len(results.errors)}):")
                for error in results.errors:
                    print(f"   - {error}")
            
            print("="*60)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate report: {str(e)}")
            return False

    async def run_stage1_diagnostic(self, options: ScrapeOptions) -> Dict[str, Any]:
        """
        🔍 DIAGNOSTIC - Test Stage 1 uniquement (extraction d'URLs).
        
        Args:
            options: Configuration options pour le diagnostic
            
        Returns:
            Dict contenant les résultats du diagnostic
        """
        start_time = time.time()
        
        # Initialize enhanced logger
        self.enhanced_logger = create_logger(
            verbose=options.verbose,
            quiet=False,  # Toujours verbose pour diagnostic
            use_colors=options.use_colors,
            show_urls=options.show_urls
        )
        
        self.enhanced_logger.print_info("🔍 DIAGNOSTIC STAGE 1 - EXTRACTION D'URLS UNIQUEMENT")
        
        try:
            # Initialize source registry separately
            from .config.source_registry import SourceRegistry
            source_registry = SourceRegistry()
            
            # Initialize orchestrator
            async with ScrapingOrchestrator() as orchestrator:
                self.orchestrator = orchestrator
                orchestrator.set_enhanced_logger(self.enhanced_logger)
                
                # Get available sources
                all_sources = source_registry.get_all_sources()
                test_sources = {}
                
                if options.sources:
                    # Test sources spécifiées
                    for source_name in options.sources:
                        if source_name in all_sources:
                            test_sources[source_name] = all_sources[source_name]
                        else:
                            self.enhanced_logger.print_warning(f"Source inconnue: {source_name}")
                else:
                    # Test 2 premières sources par défaut
                    source_names = list(all_sources.keys())[:2]
                    for name in source_names:
                        test_sources[name] = all_sources[name]
                
                self.enhanced_logger.print_info(f"Sources à tester: {list(test_sources.keys())}")
                
                # Test extraction d'URLs pour chaque source
                diagnostic_results = {}
                total_urls = 0
                total_malformed = 0
                
                for source_name, source_config in test_sources.items():
                    self.enhanced_logger.print_info(f"\n🔍 Test source: {source_name}")
                    # Récupérer la configuration Stage1 si c'est un ConfigAdapter
                    if hasattr(source_config, 'stage1_config'):
                        stage1_config = source_config.stage1_config
                    else:
                        stage1_config = source_config
                    
                    self.enhanced_logger.print_info(f"URL listing: {stage1_config.base.listing_url}")
                    
                    try:
                        # Extraire URLs pour cette source
                        # Utiliser le listing scraper directement
                        from .services.listing_scraper import ListingScraper
                        listing_scraper = ListingScraper()
                        
                        # Passer l'URL string, pas l'objet config
                        source_urls = await listing_scraper.extract_job_urls(
                            listing_url=stage1_config.base.listing_url,
                            source_name=source_name,
                            css_selector=stage1_config.css_selector_jobs
                        )
                        
                        if source_urls:
                            # Analyser la qualité des URLs
                            clean_urls = []
                            malformed_urls = []
                            
                            for url in source_urls:
                                if self._is_url_clean(url):
                                    clean_urls.append(url)
                                else:
                                    malformed_urls.append(url)
                            
                            self.enhanced_logger.print_success(f"✅ URLs extraites: {len(source_urls)}")
                            self.enhanced_logger.print_info(f"   URLs propres: {len(clean_urls)}")
                            
                            if malformed_urls:
                                self.enhanced_logger.print_warning(f"   URLs malformées: {len(malformed_urls)}")
                                self.enhanced_logger.print_warning("   Exemples problématiques:")
                                for url in malformed_urls[:2]:
                                    self.enhanced_logger.print_warning(f"     ❌ {url}")
                            
                            # Afficher exemples d'URLs propres
                            self.enhanced_logger.print_info("   Exemples d'URLs propres:")
                            for i, url in enumerate(clean_urls[:3]):
                                self.enhanced_logger.print_info(f"     {i+1}. {url}")
                            
                            diagnostic_results[source_name] = {
                                'status': 'success',
                                'urls_found': len(source_urls),
                                'clean_urls': len(clean_urls),
                                'malformed_urls': len(malformed_urls),
                                'sample_urls': clean_urls[:3]
                            }
                            
                            total_urls += len(source_urls)
                            total_malformed += len(malformed_urls)
                            
                        else:
                            self.enhanced_logger.print_error(f"❌ Aucune URL extraite pour {source_name}")
                            diagnostic_results[source_name] = {
                                'status': 'failed',
                                'error': 'No URLs extracted'
                            }
                            
                    except Exception as e:
                        self.enhanced_logger.print_error(f"❌ Erreur pour {source_name}: {str(e)}")
                        diagnostic_results[source_name] = {
                            'status': 'error',
                            'error': str(e)
                        }
                
                # Résultats finaux
                processing_time = time.time() - start_time
                successful_sources = [s for s, r in diagnostic_results.items() if r['status'] == 'success']
                
                return {
                    'sources_tested': list(test_sources.keys()),
                    'successful_sources': successful_sources,
                    'total_urls': total_urls,
                    'total_malformed': total_malformed,
                    'processing_time': processing_time,
                    'source_results': diagnostic_results
                }
                
        except Exception as e:
            self.enhanced_logger.print_error(f"❌ Erreur critique du diagnostic: {str(e)}")
            return {'error': str(e)}
    
    def _is_url_clean(self, url: str) -> bool:
        """Vérifier si une URL est propre (sans caractères parasites)."""
        problematic_chars = [')', '(', '[', ']', '\\n', '\\t', ')[']
        
        for char in problematic_chars:
            if char in url:
                return False
        
        if not url.startswith(('http://', 'https://')):
            return False
            
        return True
    
    def generate_diagnostic_report(self, results: Dict[str, Any], options: ScrapeOptions) -> bool:
        """
        Générer un rapport de diagnostic pour Stage 1.
        
        Args:
            results: Résultats du diagnostic
            options: Options utilisées
            
        Returns:
            bool: True si le rapport a été généré avec succès
        """
        try:
            print("\n" + "="*80)
            print("📊 RAPPORT DIAGNOSTIC STAGE 1 - EXTRACTION D'URLS")
            print("="*80)
            
            if 'error' in results:
                print(f"❌ ERREUR CRITIQUE: {results['error']}")
                return False
            
            # Métriques principales
            successful = len(results['successful_sources'])
            total_tested = len(results['sources_tested'])
            
            print(f"🎯 Sources testées: {total_tested}")
            print(f"✅ Sources fonctionnelles: {successful}/{total_tested}")
            print(f"📊 Total URLs extraites: {results['total_urls']}")
            print(f"⚠️  URLs malformées: {results['total_malformed']}")
            print(f"⏱️  Temps de traitement: {results['processing_time']:.2f}s")
            
            # Détail par source
            print(f"\n📋 DÉTAIL PAR SOURCE:")
            print("-" * 50)
            
            for source_name in results['sources_tested']:
                source_result = results['source_results'][source_name]
                
                if source_result['status'] == 'success':
                    urls_found = source_result['urls_found']
                    clean_urls = source_result['clean_urls']
                    malformed = source_result['malformed_urls']
                    
                    print(f"✅ {source_name}:")
                    print(f"   URLs trouvées: {urls_found}")
                    print(f"   URLs propres: {clean_urls}")
                    if malformed > 0:
                        print(f"   ⚠️  URLs malformées: {malformed}")
                    
                else:
                    print(f"❌ {source_name}: {source_result.get('error', 'Erreur inconnue')}")
            
            # Diagnostic et recommandations
            print(f"\n🔧 DIAGNOSTIC ET RECOMMANDATIONS:")
            print("-" * 50)
            
            if successful == 0:
                print("❌ PROBLÈME CRITIQUE: Aucune source ne fonctionne")
                print("🔧 ACTION: Vérifier la configuration des sources et l'API Jina")
                
            elif results['total_malformed'] > 0:
                print(f"⚠️  PROBLÈME: {results['total_malformed']} URLs malformées détectées")
                print("🔧 ACTION: Corriger les URL cleaners pour nettoyer les caractères parasites")
                
            elif successful < total_tested:
                failed_sources = [s for s in results['sources_tested'] if s not in results['successful_sources']]
                print(f"⚠️  PROBLÈME PARTIEL: Sources en échec: {', '.join(failed_sources)}")
                print("🔧 ACTION: Vérifier la configuration de ces sources spécifiques")
                
            else:
                print("✅ STAGE 1 FONCTIONNE CORRECTEMENT")
                print("🎯 PROCHAINE ÉTAPE: Tester Stage 2 avec ces URLs")
            
            print("="*80)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate diagnostic report: {str(e)}")
            return False

    async def run_stage2_diagnostic(self, test_url: str, source_name: str, options: ScrapeOptions) -> Dict[str, Any]:
        """
        🔍 DIAGNOSTIC - Test Stage 2 uniquement (extraction de contenu détaillé).
        
        Args:
            test_url: URL à tester pour l'extraction de contenu
            source_name: Nom de la source pour la configuration
            options: Options de diagnostic
            
        Returns:
            Dict contenant les résultats du diagnostic Stage 2
        """
        start_time = time.time()
        
        # Initialize enhanced logger
        self.enhanced_logger = create_logger(
            verbose=options.verbose,
            quiet=False,
            use_colors=options.use_colors,
            show_urls=options.show_urls
        )
        
        self.enhanced_logger.print_info("🔍 DIAGNOSTIC STAGE 2 - EXTRACTION DE CONTENU DÉTAILLÉ")
        self.enhanced_logger.print_info(f"🎯 URL de test : {test_url}")
        self.enhanced_logger.print_info(f"📍 Source : {source_name}")
        
        try:
            # Initialize services
            from .config.source_registry import SourceRegistry
            from .services.detail_scraper import DetailScraper
            from .services.gemini_service import GeminiService
            
            source_registry = SourceRegistry()
            detail_scraper = DetailScraper()
            gemini_service = GeminiService()
            
            # Get source configuration
            source_config = source_registry.get_source(source_name)
            if not source_config:
                return {'error': f'Configuration manquante pour {source_name}'}
            
            self.enhanced_logger.print_success("✅ Services initialisés")
            
            # Test Stage 2 - Content extraction
            self.enhanced_logger.print_info("\n📋 ÉTAPE 1 : Test extraction de contenu (Jina Reader)")
            
            try:
                # Extract content using detail scraper
                # Passer les paramètres dans le bon ordre : job_url, source_site, source_name
                job_data = await detail_scraper.extract_job_data(test_url, source_name, source_name)
                
                if job_data:
                    self.enhanced_logger.print_success("✅ Contenu extrait avec succès")
                    self.enhanced_logger.print_info(f"📊 Type de données : {type(job_data)}")
                    
                    # Le detail_scraper retourne un dict, pas un objet JobOffer
                    if isinstance(job_data, dict):
                        self.enhanced_logger.print_info(f"📝 Titre : {job_data.get('title', 'Non extrait')}")
                        self.enhanced_logger.print_info(f"🏢 Entreprise : {job_data.get('company', 'Non extrait')}")
                        self.enhanced_logger.print_info(f"📍 Localisation : {job_data.get('location', 'Non extrait')}")
                        self.enhanced_logger.print_info(f"📊 Méthode : {job_data.get('extraction_method', 'Non spécifiée')}")
                    else:
                        self.enhanced_logger.print_info(f"📊 Méthode : {getattr(job_data, 'extraction_method', 'Non spécifiée')}")
                        self.enhanced_logger.print_info(f"📝 Titre : {getattr(job_data, 'title', 'Non extrait')}")
                        self.enhanced_logger.print_info(f"🏢 Entreprise : {getattr(job_data, 'company', 'Non extrait')}")
                        self.enhanced_logger.print_info(f"📍 Localisation : {getattr(job_data, 'location', 'Non extrait')}")
                    
                    # Test Gemini enrichment
                    self.enhanced_logger.print_info("\n📋 ÉTAPE 2 : Test enrichissement IA (Gemini)")
                    
                    try:
                        # Créer un objet JobOffer à partir du dict pour Gemini
                        from .models import JobOffer, ExtractionMethod, JobLocation, ExtractionMetadata
                        
                        if isinstance(job_data, dict):
                            # Créer l'objet JobLocation si location existe
                            location_obj = None
                            if job_data.get('location'):
                                location_obj = JobLocation(
                                    city=job_data.get('location'),
                                    country="Togo"
                                )
                            
                            # Créer l'objet ExtractionMetadata (requis)
                            extraction_metadata = ExtractionMetadata(
                                method=ExtractionMethod.JINA,
                                source_site=source_name
                            )
                            
                            # Convertir le dict en objet JobOffer pour Gemini
                            job_offer = JobOffer(
                                title=job_data.get('title', ''),
                                company=job_data.get('company', ''),
                                location=location_obj,
                                description=job_data.get('description', ''),
                                source_url=test_url,
                                extraction_method=ExtractionMethod.JINA,
                                extraction_metadata=extraction_metadata
                            )
                        else:
                            job_offer = job_data
                        
                        # Utiliser structure_job_data avec le contenu brut
                        if isinstance(job_data, dict):
                            # Le contenu brut est dans raw_data.content
                            raw_data = job_data.get('raw_data', {})
                            raw_content = raw_data.get('content', '')
                            
                            if not raw_content:
                                # Fallback sur d'autres champs
                                raw_content = (job_data.get('description') or 
                                             str(job_data))
                        else:
                            raw_content = str(job_data)
                        
                        self.enhanced_logger.print_info(f"📊 Contenu pour Gemini : {len(raw_content)} caractères")
                        
                        # Afficher le contenu brut si verbose
                        if options.verbose and len(raw_content) > 0:
                            self.enhanced_logger.print_info("\n📝 CONTENU RAW_MARKDOWN:")
                            self.enhanced_logger.print_info("=" * 80)
                            # Limiter l'affichage pour éviter de surcharger la console
                            display_content = raw_content[:2000] + "..." if len(raw_content) > 2000 else raw_content
                            print(display_content)
                            self.enhanced_logger.print_info("=" * 80)
                        
                        if len(raw_content) > 100:  # Seulement si on a du contenu substantiel
                            enriched_data = await gemini_service.structure_job_data(raw_content, test_url, source_name)
                        else:
                            self.enhanced_logger.print_warning("⚠️ Contenu insuffisant pour Gemini")
                            enriched_data = None
                        
                        if enriched_data:
                            self.enhanced_logger.print_success("✅ Enrichissement réussi")
                            
                            # Afficher les données structurées si verbose
                            if options.verbose:
                                self.enhanced_logger.print_info("\n🔧 DONNÉES STRUCTURED_JSON:")
                                self.enhanced_logger.print_info("=" * 80)
                                import json
                                from datetime import datetime, date
                                
                                # Fonction pour sérialiser les dates
                                def json_serializer(obj):
                                    if isinstance(obj, (datetime, date)):
                                        return obj.isoformat()
                                    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")
                                
                                print(json.dumps(enriched_data, indent=2, ensure_ascii=False, default=json_serializer))
                                self.enhanced_logger.print_info("=" * 80)
                            
                            return {
                                'stage2_success': True,
                                'jina_extraction': 'success',
                                'gemini_enrichment': 'success',
                                'original_data': job_data,
                                'enriched_data': enriched_data,
                                'raw_content': raw_content,
                                'processing_time': time.time() - start_time
                            }
                        else:
                            self.enhanced_logger.print_error("❌ Échec enrichissement Gemini")
                            
                            # FALLBACK : Essayer OpenRouter
                            self.enhanced_logger.print_info("\n📋 ÉTAPE 3 : Fallback OpenRouter")
                            
                            try:
                                from .services.openrouter_service import OpenRouterService
                                
                                openrouter_service = OpenRouterService()
                                
                                # Test de connexion rapide
                                connection_ok = await openrouter_service.test_connection()
                                if not connection_ok:
                                    self.enhanced_logger.print_warning("⚠️ OpenRouter connection test failed")
                                
                                # Structurer avec OpenRouter
                                openrouter_data = await openrouter_service.structure_job_data(
                                    raw_content, test_url, source_name
                                )
                                
                                if openrouter_data:
                                    self.enhanced_logger.print_success("✅ Enrichissement OpenRouter réussi")
                                    
                                    # Afficher les données structurées si verbose
                                    if options.verbose:
                                        self.enhanced_logger.print_info("\n🔧 DONNÉES OPENROUTER_JSON:")
                                        self.enhanced_logger.print_info("=" * 80)
                                        import json
                                        print(json.dumps(openrouter_data, indent=2, ensure_ascii=False))
                                        self.enhanced_logger.print_info("=" * 80)
                                    
                                    return {
                                        'stage2_success': True,
                                        'jina_extraction': 'success',
                                        'gemini_enrichment': 'failed',
                                        'openrouter_enrichment': 'success',
                                        'original_data': job_data,
                                        'enriched_data': openrouter_data,
                                        'raw_content': raw_content,
                                        'processing_time': time.time() - start_time,
                                        'fallback_used': 'openrouter'
                                    }
                                else:
                                    self.enhanced_logger.print_error("❌ Échec enrichissement OpenRouter")
                                    
                            except Exception as openrouter_error:
                                self.enhanced_logger.print_error(f"❌ Erreur OpenRouter: {str(openrouter_error)}")
                            
                            return {
                                'stage2_success': False,
                                'jina_extraction': 'success',
                                'gemini_enrichment': 'failed',
                                'original_data': job_data,
                                'processing_time': time.time() - start_time
                            }
                            
                    except Exception as e:
                        self.enhanced_logger.print_error(f"❌ Erreur Gemini : {str(e)}")
                        return {
                            'stage2_success': False,
                            'jina_extraction': 'success',
                            'gemini_enrichment': 'error',
                            'original_data': job_data,
                            'error': f'Gemini error: {str(e)}',
                            'processing_time': time.time() - start_time
                        }
                else:
                    self.enhanced_logger.print_error("❌ Aucun contenu extrait par Jina Reader")
                    return {
                        'stage2_success': False,
                        'jina_extraction': 'failed',
                        'error': 'No content extracted by Jina Reader',
                        'processing_time': time.time() - start_time
                    }
                    
            except Exception as e:
                self.enhanced_logger.print_error(f"❌ Erreur extraction Jina : {str(e)}")
                return {
                    'stage2_success': False,
                    'jina_extraction': 'error',
                    'error': f'Jina extraction error: {str(e)}',
                    'processing_time': time.time() - start_time
                }
                
        except Exception as e:
            self.enhanced_logger.print_error(f"❌ Erreur critique : {str(e)}")
            return {'error': str(e)}
    
    def generate_stage2_diagnostic_report(self, results: Dict[str, Any], test_url: str, options: ScrapeOptions) -> bool:
        """
        Générer un rapport de diagnostic pour Stage 2.
        
        Args:
            results: Résultats du diagnostic Stage 2
            test_url: URL testée
            options: Options utilisées
            
        Returns:
            bool: True si le rapport a été généré avec succès
        """
        try:
            print("\n" + "="*80)
            print("📊 RAPPORT DIAGNOSTIC STAGE 2 - EXTRACTION DE CONTENU")
            print("="*80)
            
            if 'error' in results:
                print(f"❌ ERREUR CRITIQUE: {results['error']}")
                return False
            
            # Métriques principales
            stage2_success = results.get('stage2_success', False)
            jina_status = results.get('jina_extraction', 'unknown')
            gemini_status = results.get('gemini_enrichment', 'unknown')
            processing_time = results.get('processing_time', 0)
            
            print(f"🎯 URL testée: {test_url}")
            print(f"✅ Stage 2 global: {'✅ SUCCÈS' if stage2_success else '❌ ÉCHEC'}")
            print(f"📊 Jina Reader: {'✅ OK' if jina_status == 'success' else '❌ ÉCHEC'}")
            print(f"🤖 Gemini IA: {'✅ OK' if gemini_status == 'success' else '❌ ÉCHEC'}")
            
            # Vérifier si OpenRouter a été utilisé comme fallback
            openrouter_status = results.get('openrouter_enrichment', None)
            fallback_used = results.get('fallback_used', None)
            
            if openrouter_status:
                print(f"🔄 OpenRouter Fallback: {'✅ OK' if openrouter_status == 'success' else '❌ ÉCHEC'}")
            
            print(f"⏱️  Temps de traitement: {processing_time:.2f}s")
            
            # Données extraites si disponibles
            if 'original_data' in results:
                original = results['original_data']
                print(f"\n📋 DONNÉES EXTRAITES:")
                if isinstance(original, dict):
                    print(f"   Titre: {original.get('title', 'Non extrait')}")
                    print(f"   Entreprise: {original.get('company', 'Non extrait')}")
                    print(f"   Localisation: {original.get('location', 'Non extrait')}")
                    print(f"   Méthode: {original.get('extraction_method', 'Non spécifiée')}")
                else:
                    print(f"   Titre: {getattr(original, 'title', 'Non extrait')}")
                    print(f"   Entreprise: {getattr(original, 'company', 'Non extrait')}")
                    print(f"   Localisation: {getattr(original, 'location', 'Non extrait')}")
                    print(f"   Méthode: {getattr(original, 'extraction_method', 'Non spécifiée')}")
            
            # Diagnostic et recommandations
            print(f"\n🔧 DIAGNOSTIC ET RECOMMANDATIONS:")
            print("-" * 50)
            
            if jina_status == 'failed':
                print("❌ PROBLÈME CRITIQUE: Jina Reader ne peut pas extraire le contenu")
                print("🔧 ACTION: Vérifier les paramètres Jina pour Stage 2")
                print("   - Vérifier les sélecteurs CSS")
                print("   - Vérifier les timeouts")
                print("   - Tester manuellement l'URL")
                
            elif jina_status == 'error':
                print("❌ PROBLÈME CRITIQUE: Erreur technique Jina Reader")
                print("🔧 ACTION: Vérifier la connectivité et la configuration API")
                
            elif gemini_status == 'failed':
                print("⚠️  PROBLÈME PARTIEL: Jina OK mais Gemini échoue")
                print("🔧 ACTION: Vérifier la configuration Gemini")
                print("   - Vérifier la clé API Gemini")
                print("   - Vérifier les prompts d'enrichissement")
                
            elif gemini_status == 'error':
                print("⚠️  PROBLÈME PARTIEL: Erreur technique Gemini")
                print("🔧 ACTION: Vérifier la connectivité Gemini API")
                
            # Diagnostic spécifique pour OpenRouter fallback
            if openrouter_status == 'success':
                print("✅ FALLBACK RÉUSSI: OpenRouter a compensé l'échec de Gemini")
                print("💡 RECOMMANDATION: Considérer OpenRouter comme alternative principale")
                
            elif openrouter_status == 'failed':
                print("❌ FALLBACK ÉCHOUÉ: OpenRouter n'a pas pu compenser")
                print("🔧 ACTION: Vérifier la clé API OpenRouter")
                
            if stage2_success:
                provider_used = "Gemini" if gemini_status == 'success' else "OpenRouter" if openrouter_status == 'success' else "Inconnu"
                print(f"✅ STAGE 2 FONCTIONNE CORRECTEMENT (Provider: {provider_used})")
                print("🎯 PROCHAINE ÉTAPE: Intégrer Stage 1 + Stage 2 dans le workflow complet")
            else:
                print("❌ STAGE 2 ÉCHOUE COMPLÈTEMENT")
                print("🔧 ACTION URGENTE: Résoudre les problèmes d'extraction et d'enrichissement")
            
            print("="*80)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to generate Stage 2 diagnostic report: {str(e)}")
            return False