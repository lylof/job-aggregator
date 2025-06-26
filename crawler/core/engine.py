import json
import os
from datetime import datetime
import asyncio

class SourceRunner:
    def __init__(self, source):
        self.source = source
        self.state_file = f"last_scrap_state.json"
        self.source_key = self.source.name
        self.seen_ids = set()
        self._load_state()

    def _load_state(self):
        try:
            with open(self.state_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            src_state = data.get(self.source_key, {})
            self.seen_ids = set(src_state.get("seen_ids", []))
            from datetime import datetime as _dt
            last_run_str = src_state.get("last_run_utc")
            try:
                self.last_run_time = _dt.fromisoformat(last_run_str) if last_run_str else None
            except Exception:
                self.last_run_time = None
        except Exception:
            self.seen_ids = set()

    def _save_state(self, new_ids):
        try:
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
            except Exception:
                data = {}
            data.setdefault(self.source_key, {})
            data[self.source_key]["seen_ids"] = list(self.seen_ids.union(new_ids))
            data[self.source_key]["last_run_utc"] = datetime.utcnow().isoformat()
            with open(self.state_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[ERROR] Failed to save state: {e}")

    async def crawl(self):
        from bs4 import BeautifulSoup
        import aiohttp

        print(f"[INFO] Crawling source: {self.source_key}")
        import logging
        # Réduire le bruit des messages "Error while closing connector"
        logging.getLogger("aiohttp.client").setLevel(logging.CRITICAL)
        from crawler.supabase_export import upsert_job_to_supabase
        from crawler.utils.html_cleaner import clean_html_content
        from crawler.utils.job_classifier import JobClassifier
        from crawler.utils.geo_extractor import GeoExtractor
        from datetime import datetime
        try:
            from crawler.llm_enrichment import GeminiEnricher
            GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")
            # Désactiver l'enrichissement LLM pour les clés de test
            if GEMINI_API_KEY and GEMINI_API_KEY not in ["DEMO_MODE_PLACEHOLDER", "your_gemini_api_key_here"]:
                enricher = GeminiEnricher(api_key=GEMINI_API_KEY)
                print(f"[LLM] Enrichissement activé avec Gemini")
            else:
                enricher = None
                if GEMINI_API_KEY in ["DEMO_MODE_PLACEHOLDER", "your_gemini_api_key_here"]:
                    print(f"[LLM] Enrichissement désactivé - clé API de test détectée")
                else:
                    print(f"[LLM] Enrichissement désactivé - pas de GEMINI_API_KEY")
        except Exception as e:
            enricher = None
            print(f"[LLM] Erreur initialisation enrichissement : {e}")

        from datetime import timedelta
        max_age_days = int(os.getenv("MAX_JOB_AGE_DAYS", "7"))  # défaut 7 jours
        oldest_allowed_by_env = datetime.utcnow().date() - timedelta(days=max_age_days)
        # Si on a une exécution précédente, on prend la date la plus récente entre cutoff env et last_run
        if getattr(self, "last_run_time", None):
            cutoff_date = max(oldest_allowed_by_env, self.last_run_time.date())
        else:
            cutoff_date = oldest_allowed_by_env

        new_ids = set()
        exported = 0
        errors = 0
        pages = 0
        
        # Initialiser le classificateur
        classifier = JobClassifier()
        
        # Initialiser l'extracteur géographique
        geo_extractor = GeoExtractor()
        session_timeout = aiohttp.ClientTimeout(total=60)
        async with aiohttp.ClientSession(timeout=session_timeout) as session:
            for start_url in self.source.get_listing_urls():
                next_url = start_url
                while next_url:
                    pages += 1
                    try:
                        async with session.get(next_url) as resp:
                            html = await resp.text()
                    except Exception as e:
                        logging.error(f"[NETWORK] Impossible de récupérer {next_url}: {e}")
                        break
                    schema = self.source.get_listing_schema()
                    soup = BeautifulSoup(html, "html.parser")
                    offers = []
                    for offer in soup.select(schema["baseSelector"]):
                        item = {}
                        # Champs de base (ex: url)
                        for field in schema.get("baseFields", []):
                            selector = field.get("selector")
                            if selector in (None, "", ":scope", ":self"):
                                sel = offer  # élément courant
                            else:
                                sel = offer.select_one(selector)
                            if not sel:
                                item[field["name"]] = None
                                continue
                            if field["type"] == "attribute":
                                item[field["name"]] = sel.get(field["attribute"])
                            else:
                                item[field["name"]] = sel.get_text(strip=True)
                        # Champs supplémentaires
                        for field in schema.get("fields", []):
                            selector = field.get("selector")
                            if selector in (None, "", ":scope", ":self"):
                                sel = offer
                            else:
                                sel = offer.select_one(selector)
                            if not sel:
                                item[field["name"]] = None
                                continue
                            if field["type"] == "attribute":
                                item[field["name"]] = sel.get(field["attribute"])
                            elif field["type"] == "html":
                                item[field["name"]] = str(sel)
                            else:
                                item[field["name"]] = sel.get_text(strip=True)
                        offers.append(item)
                    # Filtrage incrémental : on continue si au moins une offre nouvelle
                    found_new = False
                    page_has_recent = False
                    for offer in offers:
                        uid = self.source.get_item_unique_id(offer)
                        if not uid:
                            continue
                        if uid in self.seen_ids or uid in new_ids:
                            continue
                        found_new = True
                        print(f"[NEW] {uid}")
                        # --- Extraction détail ---
                        detail_url = offer.get("url")
                        if not detail_url:
                            logging.warning(f"[WARN] Pas d'URL détail pour {uid}")
                            continue
                        try:
                            async with session.get(detail_url) as detail_resp:
                                detail_html = await detail_resp.text()
                            detail_schema = self.source.get_detail_schema()
                            detail_soup = BeautifulSoup(detail_html, "html.parser")
                            for field in detail_schema.get("fields", []):
                                # Champ spécial copié depuis la liste
                                if field.get("type") == "url-from-listing":
                                    offer[field["name"]] = detail_url
                                    continue
                                selector = field.get("selector")
                                if selector in (None, "", ":scope", ":self"):
                                    sel = detail_soup  # élément racine
                                else:
                                    sel = detail_soup.select_one(selector)
                                if not sel:
                                    offer[field["name"]] = None
                                    continue
                                if field["type"] == "attribute":
                                    offer[field["name"]] = sel.get(field["attribute"])
                                elif field["type"] == "html":
                                    raw_html = str(sel)
                                    # Nettoyer le HTML pour les champs de description
                                    if field["name"] in ["job_description", "profile_required", "description"]:
                                        offer[field["name"]] = clean_html_content(raw_html)
                                    else:
                                        offer[field["name"]] = raw_html
                                elif field["type"] == "text-list":
                                    offer[field["name"]] = [s.get_text(strip=True) for s in detail_soup.select(selector)]
                                elif field["type"] == "keyword":
                                    text = sel.get_text(separator=" ", strip=True).lower()
                                    keywords = [kw.lower() for kw in field.get("keywords", [])]
                                    offer[field["name"]] = any(kw in text for kw in keywords)
                                elif field["type"] == "key-value-list":
                                    items_dict = {}
                                    for kv in detail_soup.select(selector):
                                        label_el = kv.select_one(field.get("label_selector", "strong"))
                                        value_el = kv.select_one(field.get("value_selector", "span"))
                                        if label_el and value_el:
                                            items_dict[label_el.get_text(strip=True)] = value_el.get_text(strip=True)
                                    offer[field["name"]] = items_dict
                                else:
                                    offer[field["name"]] = sel.get_text(strip=True)
                            # Normalisation spécifique plugin
                            if hasattr(self.source, "normalize_date"):
                                date_field = detail_schema.get("dateField")
                                if date_field and offer.get(date_field):
                                    offer[date_field] = self.source.normalize_date(offer[date_field])
                            # Filtre temporel : on ignore les offres trop anciennes
                            recent_enough = True
                            date_field = detail_schema.get("dateField")
                            if date_field and offer.get(date_field):
                                val = offer.get(date_field)
                                if isinstance(val, str):
                                    try:
                                        dt_parsed = datetime.fromisoformat(val)
                                        if dt_parsed.date() <= cutoff_date:
                                            recent_enough = False
                                    except Exception:
                                        pass
                            if not recent_enough:
                                continue  # ignore export et ne marque pas comme nouvelle
                            page_has_recent = True
                            # --- Classification automatique ---
                            offer_category = classifier.classify_offer(
                                offer.get('title', ''),
                                offer.get('job_description', ''),
                                offer.get('company_name', '')
                            )
                            offer['offer_category'] = offer_category
                            
                            # --- Extraction géographique ---
                            geo_text = f"{offer.get('title', '')} {offer.get('job_description', '')} {offer.get('location', '')}"
                            geo_info = geo_extractor.extract_location_info(geo_text)
                            
                            # Ajouter les informations géographiques aux données de l'offre
                            if geo_info.get('city'):
                                offer['detected_city'] = geo_info['city']
                                offer['detected_region'] = geo_info['region']
                                offer['detected_latitude'] = geo_info['latitude']
                                offer['detected_longitude'] = geo_info['longitude']
                            
                            if geo_info.get('is_remote'):
                                offer['remote_work_detected'] = True
                            
                            # --- Enrichissement LLM (optionnel) ---
                            if enricher:
                                offer = enricher.enrich(offer)
                            # --- Export Supabase ---
                            offer["source"] = self.source_key
                            offer["scrape_timestamp"] = datetime.utcnow().isoformat()
                            ok = upsert_job_to_supabase(offer)
                            if ok:
                                new_ids.add(uid)
                                exported += 1
                            else:
                                errors += 1
                        except Exception as e:
                            logging.exception(f"[ERROR] Extraction/Export {uid} raised an exception:")
                            errors += 1
                    # Pagination : on continue si (1) au moins une nouvelle offre et (2) la page contenait une offre récente
                    if found_new and page_has_recent:
                        next_url = self.source.get_next_page_url(html, next_url)
                    else:
                        next_url = None
        self._save_state(new_ids)
        print(f"[INFO] {len(new_ids)} nouvelles offres collectées pour {self.source_key} | Exportées: {exported} | Erreurs: {errors} | Pages parcourues: {pages}")