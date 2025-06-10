import asyncio
import json
import os
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from .extraction_schemas import job_offer_extraction_schema, job_detail_extraction_schema
from .models import JobOffer
from .config import get_target_url
from .llm_enrichment import GeminiEnricher

async def main():
    url = get_target_url()
    if not url:
        print("Veuillez définir CRAWL_TARGET_URL dans le fichier .env")
        return

    browser_cfg = BrowserConfig(headless=True, verbose=True, text_mode=True)
    extraction = JsonCssExtractionStrategy(job_offer_extraction_schema)
    crawl_cfg = CrawlerRunConfig(
        extraction_strategy=extraction,
        cache_mode=CacheMode.BYPASS,
        remove_overlay_elements=True,
        exclude_external_links=True,
        verbose=True,
        wait_for="css=.page-search-jobs-content .card.card-job"
    )

    ENRICH_LLM = True  # Mettre à False pour désactiver l'enrichissement LLM
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")  # À configurer dans l'env
    if ENRICH_LLM and not GEMINI_API_KEY:
        print("[WARN] GEMINI_API_KEY non défini, enrichissement LLM désactivé.")
        ENRICH_LLM = False
    if ENRICH_LLM:
        enricher = GeminiEnricher(api_key=GEMINI_API_KEY)

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        result = await crawler.arun(url, config=crawl_cfg)
        if result.success and result.extracted_content:
            try:
                data = json.loads(result.extracted_content)
                print(f"{len(data)} offres extraites :")
                # Extraction des détails pour chaque offre
                detail_extraction = JsonCssExtractionStrategy(job_detail_extraction_schema)
                detail_cfg = CrawlerRunConfig(
                    extraction_strategy=detail_extraction,
                    cache_mode=CacheMode.BYPASS,
                    remove_overlay_elements=True,
                    exclude_external_links=True,
                    verbose=False,
                    wait_for="css:article.page-application-content"
                )
                for i, item in enumerate(data):
                    job_url = item.get("url")
                    if not job_url:
                        print(f"Offre {i+1} sans URL, détails non extraits.")
                        continue
                    print(f"\n--- Offre {i+1} ---")
                    print("Extraction des détails depuis :", job_url)
                    detail_result = await crawler.arun(job_url, config=detail_cfg)
                    if detail_result.success and detail_result.extracted_content:
                        try:
                            detail_data = json.loads(detail_result.extracted_content)
                            if isinstance(detail_data, list) and detail_data:
                                detail_dict = detail_data[0]
                            else:
                                detail_dict = {}
                            merged = {**item, **detail_dict}
                            if 'source_url' not in merged and 'url' in merged:
                                merged['source_url'] = merged['url']
                            try:
                                offer = JobOffer(**merged)
                                # Enrichissement LLM si activé
                                if ENRICH_LLM:
                                    try:
                                        enriched = enricher.enrich(offer.model_dump())
                                        offer = JobOffer(**enriched)
                                    except Exception as e:
                                        print(f"[LLM enrich error] {e}")
                                print(json.dumps(offer.model_dump(), indent=2, ensure_ascii=False))
                            except Exception as e:
                                print(f"Erreur de validation : {e}\nDonnées fusionnées : {merged}")
                        except Exception as e:
                            print(f"Erreur lors du décodage JSON détail : {e}")
                            print(detail_result.extracted_content)
                    else:
                        print(f"Erreur lors de l'extraction des détails : {detail_result.error_message}")
            except Exception as e:
                print(f"Erreur lors du décodage JSON : {e}")
                print(result.extracted_content)
            else:
            print(f"Erreur lors du crawl : {result.error_message}")

if __name__ == "__main__":
    asyncio.run(main()) 