import asyncio
import json
import os
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.extraction_strategy import JsonCssExtractionStrategy
from .extraction_schemas import job_offer_extraction_schema, job_detail_extraction_schema
from .models import JobOffer
from .config import get_target_url
from .llm_enrichment import GeminiEnricher
from bs4 import BeautifulSoup
import csv # Ajout pour l'export CSV

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

    audit_records = [] # Liste pour stocker les enregistrements d'audit

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
                            # Force application_url à être le lien source
                            if 'source_url' in merged:
                                merged['application_url'] = merged['source_url']
                            elif 'url' in merged:
                                merged['application_url'] = merged['url']
                            # Pipeline d'extraction en cascade pour chaque champ du schéma
                            soup = BeautifulSoup(getattr(detail_result, 'cleaned_html', '') or getattr(detail_result, 'markdown', ''), 'html.parser')
                            final_fields = {}
                            extraction_sources = {}
                            raw_extracted_fields = {} # Pour l'audit

                            for field in job_detail_extraction_schema["fields"]:
                                name = field["name"]
                                value = merged.get(name)
                                raw_extracted_fields[name] = value # Capture la valeur brute

                                # 1. Si valeur trouvée par CSS, on garde
                                if value not in [None, "", [], {}]:
                                    final_fields[name] = value
                                    extraction_sources[name] = "css"
                                    continue
                                # 2. Regex sur le HTML du bloc parent (si selector existe)
                                selector = field.get("selector")
                                parent_html = ""
                                if selector:
                                    try:
                                        parent = soup.select_one(selector)
                                        if parent:
                                            parent_html = str(parent)
                                    except Exception:
                                        pass
                                # Exemples de regex par champ (à affiner selon besoin)
                                regex_map = {
                                    "number_of_positions": r"Nombre de poste\(s\)\s*:?\s*(\d+)",
                                    "salary": r"Salaire proposé\s*:?\s*([\d\s\-\.]+[A-Za-z]+)",
                                    "languages": r"Langues?\s*:?\s*([A-Za-z,\s]+)",
                                    "valid_through": r"(\d{2}[./-]\d{2}[./-]\d{4})", # Ajout de regex pour valid_through
                                    "contact_email": r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}", # Ajout de regex pour email
                                }
                                regex = regex_map.get(name)
                                found = None
                                if regex and parent_html:
                                    import re
                                    m = re.search(regex, parent_html, re.IGNORECASE)
                                    if m:
                                        found = m.group(1).strip()
                                if found:
                                    final_fields[name] = found
                                    extraction_sources[name] = "regex"
                                    continue
                                # 2b. Heuristique pour remote_possible
                                if name == "remote_possible":
                                    desc = merged.get("job_description", "")
                                    prof = merged.get("profile_required", "")
                                    keywords = ["télétravail", "remote", "à distance", "home office"]
                                    found_remote = any(kw in desc.lower() or kw in prof.lower() for kw in keywords)
                                    final_fields[name] = found_remote if (desc or prof) else None
                                    extraction_sources[name] = "heuristic" if (desc or prof) else "not_found"
                                    continue
                                # 2c. Heuristique pour valid_through (si pas trouvé par regex)
                                if name == "valid_through" and not final_fields.get(name):
                                    import re
                                    text = merged.get("job_description", "") + " " + merged.get("profile_required", "") + " " + merged.get("date_posted", "") # Rechercher aussi dans date_posted
                                    m = re.search(r"(\d{2}[./-]\d{2}[./-]\d{4})", text)
                                    if m:
                                        final_fields[name] = m.group(1)
                                        extraction_sources[name] = "heuristic"
                                        continue

                                # 3. LLM fallback si activé
                                if ENRICH_LLM and GEMINI_API_KEY:
                                    try:
                                        # On ne complète que si la valeur est absente
                                        if final_fields.get(name) in [None, "", [], {}]: # Utilise final_fields ici
                                            html_fallback = parent_html or getattr(detail_result, 'cleaned_html', '') or getattr(detail_result, 'markdown', '')
                                            prompt = f"Dans ce HTML, quelle est la valeur exacte du champ '{name}' ? Donne uniquement la valeur brute, rien d'autre.\nHTML:\n{html_fallback}"
                                            enriched = enricher.enrich({name: None, "html": html_fallback})
                                        llm_val = enriched.get(name)
                                        if llm_val not in [None, "", [], {}]:
                                            final_fields[name] = llm_val
                                            extraction_sources[name] = "llm"
                                                print(f"[LLM enrich] Champ complété : {name} => {llm_val}")
                                            continue
                                    except Exception as e:
                                        print(f"[LLM fallback] Erreur extraction {name}: {e}")
                                # 4. Si rien trouvé
                                if name not in final_fields:
                                final_fields[name] = None
                                extraction_sources[name] = "not_found"

                            # MAPPING et type conversion
                            mapped = {}
                            for k in JobOffer.model_fields.keys():
                                v = final_fields.get(k)
                                # Conversion des listes en chaîne pour sector, job_type, tags, languages, skills
                                if k in ["sector", "job_type", "tags", "languages", "skills"] and isinstance(v, list):
                                    v = ", ".join([str(x) for x in v if x])
                                # Conversion number_of_positions en int
                                if k == "number_of_positions" and v is not None:
                                    try:
                                        v = int(v)
                                    except Exception:
                                        v = None
                                # Conversion remote_possible en bool
                                if k == "remote_possible" and v is not None:
                                    if isinstance(v, str):
                                        v = v.strip().lower() in ("true", "oui", "yes", "1")
                                    elif isinstance(v, bool):
                                        pass
                                    else:
                                        v = None
                                # Gérer l'injection de source_url si le schéma est défini avec un type 'url-from-listing'
                                if k == "source_url" and item.get("url"):
                                    v = item.get("url")
                                    extraction_sources[k] = "listing_url"

                                mapped[k] = v

                            mapped['raw_extracted_fields'] = raw_extracted_fields # Valeurs brutes avant enrichissement
                            mapped['extraction_sources'] = extraction_sources # Source de chaque champ

                            try:
                                offer = JobOffer(**mapped)
                                print(json.dumps(offer.model_dump(), indent=2, ensure_ascii=False))

                                # Enregistrement pour le rapport d'audit
                                audit_record = {"url": job_url}
                                for field_name, field_type in JobOffer.model_fields.items():
                                    audit_record[f'{field_name}_final'] = mapped.get(field_name)
                                    audit_record[f'{field_name}_raw'] = raw_extracted_fields.get(field_name)
                                    audit_record[f'{field_name}_source'] = extraction_sources.get(field_name, "not_found")
                                audit_records.append(audit_record)

                            except Exception as e:
                                print(f"Erreur de validation : {e}\nDonnées fusionnées : {mapped}")
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

    # Export du rapport d'audit à la fin du crawl
    if audit_records:
        audit_file_path = "audit_report.csv"
        with open(audit_file_path, 'w', newline='', encoding='utf-8') as csvfile:
            # Utilise les clés du premier enregistrement pour les entêtes, plus les colonnes raw et source
            fieldnames = ["url"] + [
                f'{k}_{suffix}' for k in JobOffer.model_fields.keys() for suffix in ['final', 'raw', 'source']
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(audit_records)
        print(f"\nRapport d'audit exporté vers {audit_file_path}")

if __name__ == "__main__":
    asyncio.run(main()) 