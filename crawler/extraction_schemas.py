# Schéma d'extraction principal pour la page de détail d'une offre d'emploi
job_detail_extraction_schema = {
    "name": "JobDetail",
    "baseSelector": "body",
    "fields": [
        # Champs principaux connus (toujours présents ou fréquents)
        {"name": "title", "selector": ".page-title h1.text-center", "type": "text"},
        {"name": "company_name", "selector": "h3 a", "type": "text"},
        {"name": "company_logo_url", "selector": "picture img", "type": "attribute", "attribute": "src"},
        {"name": "company_website", "selector": "li:has(strong:-soup-contains('Site Internet')) a", "type": "attribute", "attribute": "href"},
        {"name": "company_description", "selector": ".company-description .truncated-text", "type": "text"},
        {"name": "location", "selector": ".withicon.location-dot span", "type": "text"},
        {"name": "remote_possible", "selector": ".job-description, .job-qualifications", "type": "keyword", "keywords": ["télétravail", "remote", "à distance"]},
        {"name": "date_posted", "selector": ".page-application-details p", "type": "text"},
        {"name": "valid_through", "selector": "li:has(strong:-soup-contains('Date limite')) span", "type": "text"},
        {"name": "contract_type", "selector": ".withicon.file-signature span", "type": "text"},
        {"name": "job_description", "selector": ".job-description", "type": "html"},
        {"name": "profile_required", "selector": ".job-qualifications", "type": "html"},
        {"name": "skills", "selector": "ul.skills li", "type": "text-list"},
        {"name": "education_level", "selector": ".withicon.graduation-cap span", "type": "text"},
        {"name": "experience_level", "selector": ".withicon.chart span", "type": "text"},
        {"name": "salary", "selector": "li:has(strong:-soup-contains('Salaire')) span", "type": "text"},
        {"name": "languages", "selector": "li:has(strong:-soup-contains('Langues exigées')) span", "type": "text-list"},
        {"name": "number_of_positions", "selector": "li:has(strong:-soup-contains('Nombre de poste')) span", "type": "text"},
        {"name": "application_url", "selector": ".block-links a.btn-primary", "type": "attribute", "attribute": "href"},
        {"name": "source_url", "selector": None, "type": "url-from-listing"},  # à injecter depuis la page liste
        {"name": "sector", "selector": "li:has(strong:-soup-contains('Secteur d´activité')) span", "type": "text-list"},
        {"name": "job_type", "selector": "li:has(strong:-soup-contains('Métier')) span", "type": "text-list"},
        {"name": "tags", "selector": "ul.skills li", "type": "text-list"},
        {"name": "contact_email", "selector": "li:has(strong:-soup-contains('Email')) span", "type": "text"},
        {"name": "other_benefits", "selector": ".page-application-content em.text-md", "type": "text"},
        # Champs additionnels potentiels
        {"name": "contact_phone", "selector": "li:has(strong:-soup-contains('Téléphone')) span", "type": "text"},
        {"name": "date_limite", "selector": "li:has(strong:-soup-contains('Date limite')) span", "type": "text"},
        {"name": "reference", "selector": "li:has(strong:-soup-contains('Référence')) span", "type": "text"},
        # Extraction générique de toutes les paires label/valeur dans les listes d'infos (pour champs dynamiques)
        {
            "name": "extra_fields",
            "selector": "ul.list-unstyled li",
            "type": "key-value-list",
            "label_selector": "strong",
            "value_selector": "span"
        }
    ]
}

# Schéma d'extraction pour la page principale (liste des offres)
job_offer_extraction_schema = {
    "name": "JobOffers",
    "baseSelector": ".page-search-jobs-content .card.card-job",
    "baseFields": [
        {"name": "url", "type": "attribute", "attribute": "data-href"}
    ],
    "fields": [
        {"name": "title", "selector": "h3 a", "type": "text"},
        {"name": "company_name", "selector": ".card-job-company", "type": "text"},
        {"name": "location", "selector": "ul li strong", "type": "text"},
        {"name": "description", "selector": ".card-job-description p", "type": "text"},
        # Extraction générique pour champs additionnels sur la carte d'offre
        {
            "name": "extra_fields",
            "selector": "ul li",
            "type": "key-value-list",
            "label_selector": "strong",
            "value_selector": "span"
        }
    ]
} 