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
from .supabase_export import upsert_job_to_supabase
from datetime import datetime

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

    LAST_SCRAP_FILE = "last_scrap.json"
    SOURCE_KEY = "emploi.tg"  # À adapter si tu ajoutes d'autres sources

    # Fonctions utilitaires pour le delta scraping

    def get_last_scrap():
        if not os.path.exists(LAST_SCRAP_FILE):
            return None
        with open(LAST_SCRAP_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data.get(SOURCE_KEY)

    def set_last_scrap(new_date):
        data = {}
        if os.path.exists(LAST_SCRAP_FILE):
            with open(LAST_SCRAP_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
        data[SOURCE_KEY] = new_date
        with open(LAST_SCRAP_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f)

    async with AsyncWebCrawler(config=browser_cfg) as crawler:
        # --- SCRAPING INCREMENTAL ---
        last_scrap = get_last_scrap()
        print(f"[DELTA SCRAP] Dernier scrap pour {SOURCE_KEY} : {last_scrap}")
        result = await crawler.arun(url, config=crawl_cfg)
        if result.success and result.extracted_content:
            try:
                data = json.loads(result.extracted_content)
                print(f"{len(data)} offres extraites :")
                # Filtrage delta : ne garder que les offres plus récentes que le dernier scrap
                if last_scrap:
                    try:
                        last_dt = datetime.fromisoformat(last_scrap)
                    except Exception:
                        print(f"[WARN] Format de date du dernier scrap invalide, on ignore le delta.")
                        last_dt = None
                    filtered = []
                    for item in data:
                        date_str = item.get("date_posted")
                        if not date_str:
                            filtered.append(item)  # On garde si pas de date (prudent)
                            continue
                        # Normalisation de la date (à adapter selon le format réel)
                        try:
                            # Exemples de formats : '2025-06-20', 'Publiée le 20.06.2025', etc.
                            if "Publiée le" in date_str:
                                date_str = date_str.replace("Publiée le", "").strip()
                            date_str = date_str.replace("/", ".").replace("-", ".")
                            dt = datetime.strptime(date_str, "%d.%m.%Y")
                        except Exception:
                            try:
                                dt = datetime.fromisoformat(date_str)
                            except Exception:
                                filtered.append(item)  # Si parsing impossible, on garde
                                continue
                        if not last_dt or dt > last_dt:
                            filtered.append(item)
                    print(f"[DELTA SCRAP] {len(filtered)} offres à traiter après filtrage delta.")
                    data = filtered
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

                                # 4. Si rien trouvé
                                if name not in final_fields:
                                    final_fields[name] = None
                                    extraction_sources[name] = "not_found"
                            
                            # 3. LLM enrichment sur l'offre entière (après la boucle des champs)
                            if ENRICH_LLM and GEMINI_API_KEY:
                                try:
                                    print("[LLM] Enrichissement de l'offre complète...")
                                    # Préparer les données pour l'enrichissement
                                    offer_data = {**merged, **final_fields}
                                    enriched_offer = enricher.enrich(offer_data)
                                    
                                    # Mettre à jour les champs enrichis
                                    for name in final_fields.keys():
                                        if final_fields[name] in [None, "", [], {}]:  # Si champ vide
                                            enriched_val = enriched_offer.get(name)
                                            if enriched_val not in [None, "", [], {}]:  # Si LLM a trouvé quelque chose
                                                final_fields[name] = enriched_val
                                                extraction_sources[name] = "llm"
                                                print(f"[LLM] Champ enrichi : {name} => {enriched_val}")
                                    
                                except Exception as e:
                                    print(f"[LLM] Erreur enrichissement : {e}")

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

                                # Export vers Supabase
                                export_ok = upsert_job_to_supabase(offer.model_dump())
                                if export_ok:
                                    print(f"[SUPABASE] Export OK: {mapped.get('source_url') or mapped.get('url')}")
                                else:
                                    print(f"[SUPABASE] Export FAIL: {mapped.get('source_url') or mapped.get('url')}")

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
                            print(f"[ERREUR] Décodage JSON détail pour l'offre {job_url} : {e}")
                            print(f"Contenu extrait : {detail_result.extracted_content[:500]}...\n--- Fin extrait ---")
                            continue
                    else:
                        print(f"[ERREUR] Extraction des détails échouée pour l'offre {job_url}.")
                        print(f"Message d'erreur : {getattr(detail_result, 'error_message', 'Non spécifié')}")
                        print(f"Statut success: {detail_result.success}, extrait: {bool(detail_result.extracted_content)}")
                        continue
            except Exception as e:
                print(f"[ERREUR] Décodage JSON principal : {e}")
                print(f"Contenu extrait : {result.extracted_content[:500]}...\n--- Fin extrait ---")
        else:
            print(f"[ERREUR] Crawl principal échoué.")
            print(f"Message d'erreur : {getattr(result, 'error_message', 'Non spécifié')}")
            print(f"Statut success: {result.success}, extrait: {bool(getattr(result, 'extracted_content', None))}")

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

    # Après export de toutes les offres, on met à jour la date du dernier scrap
    set_last_scrap(datetime.now().isoformat())
    print(f"[DELTA SCRAP] Date du dernier scrap mise à jour : {datetime.now().isoformat()}")

if __name__ == "__main__":
    asyncio.run(main()) 