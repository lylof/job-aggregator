#!/usr/bin/env python3
"""
CRAWLER UNIFIÉ - Fusion des deux architectures + Améliorations Phase 2 + Monitoring Sentry

Ce crawler combine :
✅ Le moteur Crawl4AI qui fonctionne (main_crawler.py)
✅ Le système multi-sources (AbstractSource)
✅ Les améliorations Phase 2 (classification + géolocalisation + nettoyage HTML)
✅ Monitoring Sentry pour analyse d'erreurs en temps réel

Usage: python crawler/main_crawler_unified.py
"""

import asyncio
import json
import os
import importlib
import pkgutil
from datetime import datetime
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from crawler.models import JobOffer
from crawler.llm_enrichment import GeminiEnricher
from crawler.supabase_export import upsert_job_to_supabase
from crawler.utils.job_classifier import JobClassifier
from crawler.utils.geo_extractor import GeoExtractor
from crawler.utils.intelligent_extractor import IntelligentExtractor
from crawler.utils.html_cleaner import clean_html_content
from crawler.sentry_config import init_sentry, capture_crawling_error, capture_extraction_error, log_crawling_performance
from bs4 import BeautifulSoup
import csv

try:
    from crawler.sentry_config import init_sentry, capture_crawling_error, capture_extraction_error, log_crawling_performance, capture_message
except ImportError:
    init_sentry = None
    capture_crawling_error = None
    capture_extraction_error = None
    log_crawling_performance = None
    capture_message = None

def discover_sources():
    """Découvre automatiquement toutes les sources disponibles"""
    sources = []
    sources_dir = "crawler.sources"
    
    try:
        import crawler.sources as sources_module
        for _, module_name, _ in pkgutil.iter_modules(sources_module.__path__):
            try:
                module = importlib.import_module(f"{sources_dir}.{module_name}")
                for attr_name in dir(module):
                    attr = getattr(module, attr_name)
                    if (isinstance(attr, type) and 
                        hasattr(attr, '__bases__') and 
                        any('AbstractSource' in str(base) for base in attr.__bases__)):
                        try:
                            source_instance = attr()
                            sources.append(source_instance)
                            print(f"✅ Source découverte : {source_instance.name}")
                        except Exception as e:
                            print(f"⚠️  Erreur lors de l'initialisation de {attr.__name__}: {e}")
            except Exception as e:
                print(f"⚠️  Erreur lors de l'import du module {module_name}: {e}")
    except Exception as e:
        print(f"❌ Erreur lors de la découverte des sources: {e}")
    
    return sources

async def process_source(source, crawler, enricher, classifier, geo_extractor, intelligent_extractor, audit_records):
    """Traite une source spécifique avec toutes les améliorations Phase 2"""
    
    print(f"\n🔍 === TRAITEMENT SOURCE: {source.name.upper()} ===")
    
    LAST_SCRAP_FILE = "last_scrap.json"
    
    def get_last_scrap():
        if not os.path.exists(LAST_SCRAP_FILE):
            return None
        with open(LAST_SCRAP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(source.name)

    def set_last_scrap(new_date):
        data = {}
        if os.path.exists(LAST_SCRAP_FILE):
            with open(LAST_SCRAP_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        data[source.name] = new_date
        with open(LAST_SCRAP_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)

    last_scrap = get_last_scrap()
    print(f"[DELTA SCRAP] Dernier scrap pour {source.name} : {last_scrap}")
    
    total_processed = 0
    
    for listing_url in source.get_listing_urls():
        print(f"\n📋 Crawling listing: {listing_url}")
        
        listing_schema = source.get_listing_schema()
        extraction = JsonCssExtractionStrategy(listing_schema)
        crawl_cfg = CrawlerRunConfig(
            extraction_strategy=extraction,
            cache_mode=CacheMode.BYPASS,
            remove_overlay_elements=True,
            exclude_external_links=True,
            verbose=True,
            wait_for=f"css={listing_schema['baseSelector']}"
        )
        
        result = await crawler.arun(listing_url, config=crawl_cfg)
        
        if not result.success or not result.extracted_content:
            print(f"❌ Échec crawl listing {listing_url}")
            
            # === FALLBACK HTTP POUR WORDPRESS (emploitogo.info) ===
            fallback_data = None
            if hasattr(source, 'use_fallback_http') and source.use_fallback_http:
                print(f"🔄 Tentative fallback HTTP pour WordPress...")
                try:
                    fallback_data = source.fallback_http_crawl(listing_url, is_listing=True)
                    if fallback_data:
                        print(f"✅ Fallback HTTP réussi: {len(fallback_data)} offres trouvées")
                        # Créer un faux result.extracted_content avec les données fallback
                        result.extracted_content = json.dumps(fallback_data)
                        result.success = True
                    else:
                        print(f"❌ Fallback HTTP échoué aussi")
                except Exception as fallback_error:
                    print(f"💥 Erreur fallback HTTP: {fallback_error}")
                    capture_crawling_error(
                        error=fallback_error,
                        url=listing_url,
                        source=source.name,
                        extra_data={"type": "fallback_http", "original_crawl_failed": True}
                    )
            
            # Si ni Crawl4AI ni fallback ne fonctionnent, capturer l'erreur
            if not result.success:
                capture_crawling_error(
                    error=Exception(f"Échec crawl listing: {result.error if hasattr(result, 'error') else 'Erreur inconnue'}"),
                    url=listing_url,
                    source=source.name,
                    extra_data={"type": "listing_crawl", "success": result.success, "fallback_attempted": fallback_data is not None}
                )
                continue
            
        try:
            data = json.loads(result.extracted_content)
            print(f"📊 {len(data)} offres extraites du listing")
            
            for i, item in enumerate(data):
                job_url = item.get("url")
                if not job_url:
                    print(f"Offre {i+1} sans URL, ignorée.")
                    continue
                
                print(f"\n--- Offre {i+1}/{len(data)} ---")
                print(f"🔗 URL: {job_url}")
                
                # === CRAWL DES DÉTAILS DE L'OFFRE ===
                print("📄 Récupération des détails...")
                detail_result = None  # Initialiser la variable
                try:
                    # Construire l'URL complète si nécessaire
                    if not job_url.startswith('http'):
                        if source.name == "emploi_tg":
                            detail_url = f"https://www.emploi.tg{job_url}"
                        elif source.name == "emploitogo_info":
                            detail_url = job_url  # Déjà une URL complète
                        else:
                            detail_url = f"https://{source.name}.com{job_url}"
                    else:
                        detail_url = job_url
                    
                    # Configuration pour le crawl des détails
                    detail_schema = source.get_detail_schema()
                    detail_extraction = JsonCssExtractionStrategy(detail_schema)
                    detail_crawl_cfg = CrawlerRunConfig(
                        extraction_strategy=detail_extraction,
                        cache_mode=CacheMode.BYPASS,
                        remove_overlay_elements=True,
                        exclude_external_links=True,
                        verbose=False,  # Moins verbeux pour les détails
                        wait_for=f"css={detail_schema['baseSelector']}"
                    )
                    
                    detail_result = await crawler.arun(detail_url, config=detail_crawl_cfg)
                    
                    if detail_result.success and detail_result.extracted_content:
                        try:
                            detail_data = json.loads(detail_result.extracted_content)
                            if isinstance(detail_data, list) and len(detail_data) > 0:
                                detail_data = detail_data[0]  # Prendre le premier élément
                            
                            # Fusionner les données de listing avec les détails
                            item.update(detail_data)
                            print("   └─ ✅ Détails récupérés")
                        except json.JSONDecodeError:
                            print("   └─ ⚠️  Erreur parsing JSON détails")
                    else:
                        print("   └─ ⚠️  Échec récupération détails")
                        
                except Exception as e:
                    print(f"   └─ ❌ Erreur crawl détails: {e}")
                    detail_result = None  # S'assurer que detail_result est None en cas d'erreur
                    
                    # Capturer l'erreur dans Sentry
                    capture_crawling_error(
                        error=e,
                        url=detail_url,
                        source=source.name,
                        extra_data={"type": "detail_crawl", "job_title": item.get('title', 'N/A')}
                    )
                
                # === AMÉLIORATIONS PHASE 2 ===
                
                # 0. EXTRACTION INTELLIGENTE DES DONNÉES MANQUANTES
                print("🧠 Extraction intelligente des données...")
                if detail_result and detail_result.html:
                    # Utiliser l'extracteur intelligent pour compléter les données manquantes
                    intelligent_data = intelligent_extractor.extract_all_data(detail_result.html, item)
                    
                    # Fusionner les données intelligentes avec les données existantes
                    for key, value in intelligent_data.items():
                        if value and (not item.get(key) or len(str(value)) > len(str(item.get(key, '')))):
                            item[key] = value
                    
                    print(f"   └─ ✅ Données complétées intelligemment")
                    
                    # Afficher les nouvelles données trouvées
                    new_data_found = []
                    if intelligent_data.get('company_name'):
                        new_data_found.append(f"Entreprise: {intelligent_data['company_name'][:30]}...")
                    if intelligent_data.get('salary'):
                        new_data_found.append(f"Salaire: {intelligent_data['salary'][:20]}...")
                    if intelligent_data.get('contract_type'):
                        new_data_found.append(f"Contrat: {intelligent_data['contract_type']}")
                    if intelligent_data.get('contact_email'):
                        new_data_found.append(f"Email: {intelligent_data['contact_email']}")
                    
                    if new_data_found:
                        for data in new_data_found[:3]:  # Afficher max 3 éléments
                            print(f"     📋 {data}")
                
                # 1. CLASSIFICATION AUTOMATIQUE
                print("🏷️  Classification automatique...")
                classification_result = classifier.classify_offer(
                    item.get('title', ''),
                    item.get('job_description', ''),
                    item.get('company_name', '')
                )
                item['offer_category'] = classification_result
                print(f"   └─ Catégorie: {classification_result}")
                
                # 2. EXTRACTION GÉOGRAPHIQUE
                print("🌍 Extraction géographique...")
                location_text = f"{item.get('location', '')} {item.get('job_description', '')}"
                geo_result = geo_extractor.extract_location_info(location_text)
                
                # Ajouter les données géographiques
                item['detected_city'] = geo_result['city']
                item['detected_region'] = geo_result['region']
                item['detected_latitude'] = geo_result['latitude']
                item['detected_longitude'] = geo_result['longitude']
                item['remote_work_detected'] = geo_result['is_remote']
                
                if geo_result['city']:
                    print(f"   └─ Ville: {geo_result['city']}, Région: {geo_result['region']}")
                if geo_result['is_remote']:
                    print(f"   └─ Télétravail détecté: {geo_result['is_remote']}")
                
                # 3. NETTOYAGE HTML
                print("🧹 Nettoyage HTML...")
                if item.get('job_description'):
                    item['job_description'] = clean_html_content(item['job_description'])
                
                # === ENRICHISSEMENT LLM (SI DISPONIBLE) ===
                if enricher:
                    print("🤖 Enrichissement LLM...")
                    try:
                        enriched_data = enricher.enrich_job_offer(item)
                        item.update(enriched_data)
                        print("   └─ ✅ Enrichissement LLM appliqué")
                    except Exception as e:
                        print(f"   └─ ⚠️  Enrichissement LLM échoué: {e}")
                        # Capturer l'erreur d'enrichissement dans Sentry
                        capture_enrichment_error(
                            error=e,
                            job_data=item,
                            llm_provider="Gemini"
                        )
                
                # === EXPORT VERS SUPABASE ===
                print("💾 Export vers Supabase...")
                try:
                    # Normaliser la date si nécessaire
                    normalized_date = item.get('date_posted')
                    if normalized_date and hasattr(source, 'normalize_date'):
                        normalized_date = source.normalize_date(normalized_date)
                    
                    # Créer un objet JobOffer avec les données enrichies
                    job_offer = JobOffer(
                        title=item.get('title', ''),
                        company_name=item.get('company_name', ''),
                        location=item.get('location', ''),
                        job_description=item.get('job_description', ''),
                        source_url=detail_url,
                        date_posted=normalized_date,
                        # Nouveaux champs Phase 2
                        offer_category=item.get('offer_category'),
                        detected_city=item.get('detected_city'),
                        detected_region=item.get('detected_region'),
                        detected_latitude=item.get('detected_latitude'),
                        detected_longitude=item.get('detected_longitude'),
                        remote_work_detected=item.get('remote_work_detected', False),
                        # Champs enrichis LLM
                        company_logo_url=item.get('company_logo_url'),
                        company_website=item.get('company_website'),
                        company_description=item.get('company_description'),
                        skills=item.get('skills'),
                        salary=item.get('salary'),
                        languages=item.get('languages'),
                        sector=item.get('sector'),
                        education_level=item.get('education_level'),
                        experience_level=item.get('experience_level'),
                        contract_type=item.get('contract_type'),
                        remote_possible=item.get('remote_possible')
                    )
                    
                    # Convertir l'objet JobOffer en dictionnaire pour Supabase
                    job_dict = job_offer.model_dump()
                    
                    # Export vers Supabase
                    success = upsert_job_to_supabase(job_dict)
                    if success:
                        print("   └─ ✅ Sauvegardé en base de données")
                    else:
                        print("   └─ ❌ Échec sauvegarde base de données")
                    
                except Exception as e:
                    print(f"   └─ ❌ Erreur export Supabase: {e}")
                    # Capturer l'erreur d'export dans Sentry
                    capture_crawling_error(
                        error=e,
                        url=detail_url,
                        source=source.name,
                        extra_data={"type": "supabase_export", "job_title": item.get('title', 'N/A')}
                    )
                
                print("✅ Offre traitée avec améliorations Phase 2")
                total_processed += 1
                    
        except Exception as e:
            print(f"❌ Erreur décodage JSON listing: {e}")
            continue
    
    set_last_scrap(datetime.now().isoformat())
    print(f"\n✅ Source {source.name} terminée: {total_processed} offres traitées")
    
    # Enregistrer les métriques de performance dans Sentry
    try:
        for listing_url in source.get_listing_urls():
            log_crawling_performance(
                source=source.name,
                url=listing_url,
                duration=60,  # Estimation - vous pouvez mesurer le temps réel
                items_found=total_processed
            )
    except Exception as e:
        print(f"⚠️  Erreur logging performance: {e}")
    
    return total_processed

async def main():
    """Point d'entrée principal du crawler unifié"""
    
    # === INITIALISATION SENTRY ===
    print("🔧 Initialisation Sentry...")
    try:
        init_sentry(environment="production")
        print("✅ Sentry initialisé - Monitoring actif")
        
        # Remplacer sentry_sdk.capture_message par capture_message si disponible
        if capture_message:
            capture_message("Crawler unifié démarré", level="info")
        
    except Exception as e:
        print(f"⚠️  Sentry non disponible: {e}")
    
    print("🚀 CRAWLER UNIFIÉ - DÉMARRAGE")
    print("=" * 60)
    print("✅ Moteur: Crawl4AI")
    print("✅ Multi-sources: Activé")
    print("✅ Phase 2: Classification + Géolocalisation + Nettoyage HTML")
    print("✅ Crawl détails: ACTIVÉ")
    print("✅ Export: Supabase activé")
    print("✅ Monitoring: Sentry activé")
    print("=" * 60)
    
    browser_cfg = BrowserConfig(headless=True, verbose=True, text_mode=True)
    
    classifier = JobClassifier()
    geo_extractor = GeoExtractor()
    intelligent_extractor = IntelligentExtractor()
    print("✅ Classification et géolocalisation initialisées")
    
    ENRICH_LLM = True
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
    enricher = None
    
    if ENRICH_LLM and GEMINI_API_KEY:
        enricher = GeminiEnricher(api_key=GEMINI_API_KEY)
        print("✅ Enrichissement LLM activé")
    else:
        print("⚠️  Enrichissement LLM désactivé (pas de clé API)")
    
    sources = discover_sources()
    if not sources:
        print("❌ Aucune source trouvée!")
        return
    
    print(f"📋 {len(sources)} source(s) découverte(s)")
    
    audit_records = []
    total_global = 0
    
    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        print("\n🔥 DÉBUT DU CRAWLING MULTI-SOURCES")
        
        for source in sources:
            try:
                processed = await process_source(
                    source, crawler, enricher, classifier, geo_extractor, intelligent_extractor, audit_records
                )
                total_global += processed
            except Exception as e:
                print(f"❌ Erreur source {source.name}: {e}")
                continue
    
    print(f"\n🎉 CRAWLING TERMINÉ")
    print("=" * 60)
    print(f"📊 Total offres traitées: {total_global}")
    print(f"📋 Sources traitées: {len(sources)}")
    
    print("🎯 CRAWLER UNIFIÉ TERMINÉ AVEC SUCCÈS!")

if __name__ == "__main__":
    asyncio.run(main()) 