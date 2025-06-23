from crawler.core.source_abc import AbstractSource

class EmploitogoInfoSource(AbstractSource):
    @property
    def name(self):
        return "emploitogo_info"

    def get_listing_urls(self):
        return ["https://emploitogo.info/emploitogo/"]

    def get_listing_schema(self):
        # Sélecteurs réels d'après le HTML fourni
        return {
            "name": "JobOffers",
            "baseSelector": "div.post-item",
            "baseFields": [
                {"name": "url", "type": "attribute", "attribute": "href", "selector": "h3.entry-title a"}
            ],
            "fields": [
                {"name": "title", "selector": "h3.entry-title a", "type": "text"},
                {"name": "date_posted", "selector": "ul.entry-meta li.meta-date", "type": "text"},
                {"name": "description", "selector": "div.entry-excerpt", "type": "text"}
            ]
        }

    def get_detail_schema(self):
        # Sélecteurs réels d'après le HTML fourni
        return {
            "name": "JobDetail",
            "baseSelector": "body",
            "dateField": "date_posted",
            "fields": [
                {"name": "title", "selector": "h1.entry-title", "type": "text"},
                {"name": "company_name", "selector": ".meta-author .author-name", "type": "text"},
                {"name": "date_posted", "selector": ".meta-date", "type": "text"},
                {"name": "job_description", "selector": "div.entry-content.article-content", "type": "html"},
                {"name": "company_logo_url", "selector": ".entry-featured img", "type": "attribute", "attribute": "src"}
            ]
        }

    def get_item_unique_id(self, item_data):
        return item_data.get("url")

    def get_next_page_url(self, page_html, current_url):
        # Extraction de l'URL de la page suivante à partir du HTML (pagination)
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(page_html, "html.parser")
        next_link = soup.select_one("a.pagi-item.pagi-icon.pagi-item-next")
        if next_link and next_link.has_attr("href"):
            return next_link["href"]
        return None

    def normalize_date(self, raw_date):
        # Format attendu : '21 juin 2025'
        import locale
        import logging
        from datetime import datetime
        # Tenter de configurer la locale française, sinon utiliser une alternative
        try:
            locale.setlocale(locale.LC_TIME, 'fr_FR.UTF-8')
        except locale.Error:
            try:
                locale.setlocale(locale.LC_TIME, 'French_France.1252') # Pour Windows
            except locale.Error:
                logging.warning("Locale 'fr_FR.UTF-8' non supportée. Le parsing de date peut échouer.")
        
        if not raw_date:
            return None
            
        try:
            # Nettoyage de la date brute
            clean_date = raw_date.strip()
            # Parsing de la date
            dt = datetime.strptime(clean_date, "%d %B %Y")
            return dt.date().isoformat()
        except (ValueError, TypeError) as e:
            # Fallback avec dateutil (plus tolérant)
            try:
                from dateutil import parser as dateparser
                dt = dateparser.parse(clean_date, dayfirst=True, languages=["fr"])
                if dt is not None:
                    return dt.date().isoformat()
            except Exception:
                pass
            logging.error(f"[DATE PARSE FAIL] Impossible de parser '{raw_date}'. Erreur: {e}")
            return None
