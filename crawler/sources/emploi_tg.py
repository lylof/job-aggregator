from crawler.core.source_abc import AbstractSource
from crawler.extraction_schemas import job_offer_extraction_schema, job_detail_extraction_schema

class EmploiTgSource(AbstractSource):
    @property
    def name(self):
        return "emploi_tg"

    def get_listing_urls(self):
        return ["https://www.emploi.tg/recherche-jobs-togo"]

    def get_listing_schema(self):
        """Schéma de la page de résultats (listing) pour emploi.tg avec nouveaux sélecteurs."""
        return {
            "name": "JobOffersTG",
            "baseSelector": "div.offre-item",  # Chaque offre est contenue dans un div.offre-item
            "baseFields": [
                {"name": "url", "selector": "h2 a", "type": "attribute", "attribute": "href"}
            ],
            "fields": [
                {"name": "title", "selector": "h2 a", "type": "text"},
                {"name": "company_name", "selector": "a[href*='/recruteur/']", "type": "text"},
                {"name": "location", "selector": "span[title='Lieu']", "type": "text"},
                {"name": "date_posted", "selector": "span[title='Date de publication']", "type": "text"}
            ]
        }

    def get_detail_schema(self):
        """Schéma de la page détail pour emploi.tg avec mise à jour des sélecteurs."""
        from copy import deepcopy
        schema = deepcopy(job_detail_extraction_schema)
        # Mises à jour/ajouts spécifiques
        updates = {
            "date_posted": {"selector": "time[datetime]", "type": "attribute", "attribute": "datetime"},
            "employment_type": {"selector": "p:has(strong:-soup-contains('Type de contrat')) span", "type": "text"},
            "application_url": {"selector": "a:-soup-contains('Postuler')", "type": "attribute", "attribute": "href"},
            "region": {"selector": "p:has(strong:-soup-contains('Région')) span", "type": "text"},
            "city": {"selector": "p:has(strong:-soup-contains('Ville')) span", "type": "text"},
            "experience_level": {"selector": "p:has(strong:-soup-contains('Niveau d\'expérience')) span", "type": "text"},
            "education_level": {"selector": "p:has(strong:-soup-contains('Niveau d\'études')) span", "type": "text"},
            "salary": {"selector": "p:has(strong:-soup-contains('Salaire proposé')) span", "type": "text"},
        }
        # Appliquer ou ajouter
        field_names = {f["name"] for f in schema["fields"]}
        for name, spec in updates.items():
            if name in field_names:
                for f in schema["fields"]:
                    if f["name"] == name:
                        f.update(spec)
                        break
            else:
                spec_with_name = {**spec, "name": name}
                schema["fields"].append(spec_with_name)
        schema["dateField"] = "date_posted"
        return schema

    def get_item_unique_id(self, item_data):
        return item_data.get("url")

    def get_next_page_url(self, page_html, current_url):
        # À compléter : logique pour trouver l'URL de la page suivante sur emploi.tg
        # Peut utiliser BeautifulSoup ou autre si besoin
        return None

    def normalize_date(self, raw_date):
        if not raw_date:
            return None
        import re
        from datetime import datetime
        raw_date = str(raw_date)
        if "Publiée le" in raw_date:
            raw_date = raw_date.replace("Publiée le", "").strip()
        raw_date = raw_date.replace("/", ".").replace("-", ".")
        try:
            dt = datetime.strptime(raw_date, "%d.%m.%Y")
            return dt.date().isoformat()
        except Exception:
            try:
                dt = datetime.fromisoformat(raw_date)
                return dt.date().isoformat()
            except Exception:
                return None
