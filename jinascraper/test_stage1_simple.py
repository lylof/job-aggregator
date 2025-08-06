#!/usr/bin/env python3
"""Test simple du filtrage temporel sur Stage 1."""

import re
from datetime import datetime, timedelta

def simulate_temporal_filtering():
    """Simulation du filtrage temporel sur les URLs extraites."""
    
    print("🧪 SIMULATION FILTRAGE TEMPOREL - STAGE 1")
    print("=" * 50)
    
    # URLs extraites du test précédent (emploi.tg)
    sample_urls = [
        "https://www.emploi.tg/offre-emploi-togo/conseiller-clientele-bilingue-lome-326684",
        "https://www.emploi.tg/offre-emploi-togo/gestion-projet-social-zone-adetikope-328559", 
        "https://www.emploi.tg/offre-emploi-togo/charge-relation-client-hf-209529",
        "https://www.emploi.tg/offre-emploi-togo/community-manager-polyvalent-lome-djidjole-322888",
        "https://www.emploi.tg/offre-emploi-togo/stagiaire-community-manager-createur-contenu-lome-322983",
        "https://www.emploi.tg/offre-emploi-togo/cuisinier-hf-grand-popo-323880",
        "https://www.emploi.tg/offre-emploi-togo/gerant-etablissement-hotelier-grand-popo-324119",
        "https://www.emploi.tg/offre-emploi-togo/responsable-vente-hf-lome-324142",
        "https://www.emploi.tg/offre-emploi-togo/commercial-terrain-lome-324824",
        "https://www.emploi.tg/offre-emploi-togo/comptable-experimentee-lome-324837",
        "https://www.emploi.tg/offre-emploi-togo/c-lome-325015",
        "https://www.emploi.tg/offre-emploi-togo/representante-pays-togo-lome-togo-325393",
        "https://www.emploi.tg/offre-emploi-togo/commerciale-lome-325834",
        "https://www.emploi.tg/offre-emploi-togo/developpeur-web-lome-325839",
        "https://www.emploi.tg/offre-emploi-togo/administrateur-reseaux-securite-lome-326302",
        "https://www.emploi.tg/offre-emploi-togo/responsable-prospection-developpement-plantations-tchamba-326584",
        "https://www.emploi.tg/offre-emploi-togo/vendeur-showroom-kara-326990",
        "https://www.emploi.tg/offre-emploi-togo/secretaire-lome-327056",
        "https://www.emploi.tg/offre-emploi-togo/responsable-commercial-lome-327388",
        "https://www.emploi.tg/offre-emploi-togo/sales-representative-remote-327745",
        "https://www.emploi.tg/offre-emploi-togo/consultante-junior-expertise-comptable-lome-328371",
        "https://www.emploi.tg/offre-emploi-togo/auditeur-junior-hf-lome-328372",
        "https://www.emploi.tg/offre-emploi-togo/stagiaire-developpement-systemes-embarques-electroniques-lome-328594",
        "https://www.emploi.tg/offre-emploi-togo/software-developer-remote-328638",
        "https://www.emploi.tg/offre-emploi-togo/gerant-projet-social-adetikope-328697"
    ]
    
    print(f"📊 URLs extraites (Stage 1): {len(sample_urls)}")
    print(f"📅 Date actuelle: {datetime.now().strftime('%d/%m/%Y %H:%M')}")
    
    # Analyse des IDs dans les URLs pour estimer l'âge
    print("\n🔍 ANALYSE DES IDs POUR ESTIMATION D'ÂGE")
    print("-" * 40)
    
    url_analysis = []
    
    for url in sample_urls:
        # Extraire l'ID numérique de l'URL
        match = re.search(r'-(\d+)$', url)
        if match:
            job_id = int(match.group(1))
            url_analysis.append({
                'url': url,
                'id': job_id,
                'title': url.split('/')[-1].replace('-' + str(job_id), '').replace('-', ' ').title()
            })
    
    # Trier par ID (approximation de l'âge)
    url_analysis.sort(key=lambda x: x['id'])
    
    # Simulation du filtrage basé sur l'ID
    # Les IDs plus petits = offres plus anciennes
    min_id = min(item['id'] for item in url_analysis)
    max_id = max(item['id'] for item in url_analysis)
    
    print(f"   📈 ID minimum: {min_id}")
    print(f"   📈 ID maximum: {max_id}")
    print(f"   📊 Écart d'IDs: {max_id - min_id}")
    
    # Simulation de différents seuils de filtrage
    scenarios = [
        {"name": "Très récent (24h)", "threshold": 0.9, "description": "Seulement les 10% plus récents"},
        {"name": "Récent (3 jours)", "threshold": 0.7, "description": "Seulement les 30% plus récents"}, 
        {"name": "Modéré (1 semaine)", "threshold": 0.5, "description": "Seulement les 50% plus récents"},
        {"name": "Permissif (2 semaines)", "threshold": 0.3, "description": "Seulement les 70% plus récents"}
    ]
    
    print("\n📊 SIMULATION DE DIFFÉRENTS SEUILS DE FILTRAGE")
    print("=" * 55)
    
    for scenario in scenarios:
        threshold_id = min_id + (max_id - min_id) * scenario["threshold"]
        
        filtered_urls = [item for item in url_analysis if item['id'] >= threshold_id]
        blocked_urls = [item for item in url_analysis if item['id'] < threshold_id]
        
        filter_rate = (len(blocked_urls) / len(url_analysis)) * 100
        
        print(f"\n🎯 {scenario['name']}")
        print(f"   📝 {scenario['description']}")
        print(f"   🔢 Seuil ID: ≥ {threshold_id:.0f}")
        print(f"   ✅ URLs à traiter: {len(filtered_urls)}")
        print(f"   ❌ URLs filtrées: {len(blocked_urls)}")
        print(f"   💰 Économies: {filter_rate:.1f}% des appels IA")
        
        if len(blocked_urls) > 0:
            print(f"   📋 Exemples filtrés:")
            for item in blocked_urls[:3]:
                print(f"      • {item['title']} (ID: {item['id']})")
    
    # Estimation réaliste pour emploi.tg
    print("\n🎯 ESTIMATION RÉALISTE POUR EMPLOI.TG")
    print("=" * 40)
    
    # Basé sur l'observation que les IDs récents sont dans les 328xxx
    recent_threshold = 328000
    recent_urls = [item for item in url_analysis if item['id'] >= recent_threshold]
    old_urls = [item for item in url_analysis if item['id'] < recent_threshold]
    
    realistic_filter_rate = (len(old_urls) / len(url_analysis)) * 100
    
    print(f"📅 Seuil réaliste: IDs ≥ {recent_threshold} (offres récentes)")
    print(f"✅ URLs récentes à traiter: {len(recent_urls)}")
    print(f"❌ URLs anciennes filtrées: {len(old_urls)}")
    print(f"💰 Économies réalistes: {realistic_filter_rate:.1f}% des appels IA")
    
    if len(old_urls) > 0:
        print(f"\n📋 Offres anciennes qui seraient filtrées:")
        for item in old_urls:
            print(f"   • {item['title']} (ID: {item['id']})")
    
    print(f"\n📋 Offres récentes qui seraient traitées:")
    for item in recent_urls[:5]:
        print(f"   • {item['title']} (ID: {item['id']})")
    
    # Impact sur les coûts
    print(f"\n💡 IMPACT SUR LES COÛTS D'APIS")
    print("=" * 30)
    
    if realistic_filter_rate > 0:
        print(f"🎯 Avec filtrage temporel:")
        print(f"   • {len(recent_urls)} offres traitées avec IA")
        print(f"   • {len(old_urls)} offres filtrées (économies)")
        print(f"   • {realistic_filter_rate:.1f}% d'économies sur Gemini/OpenRouter")
        print(f"   • Quotas préservés pour nouvelles offres")
    else:
        print("💡 Toutes les offres sont récentes")
        print("   • Pas d'économies cette fois")
        print("   • Mais le système est prêt pour les prochains cycles")
    
    print(f"\n🚀 CONCLUSION")
    print("=" * 15)
    print("✅ Le filtrage temporel sur Stage 1 permettrait:")
    print(f"   • D'identifier {len(old_urls)} offres anciennes")
    print(f"   • D'économiser {realistic_filter_rate:.1f}% des appels IA")
    print("   • De préserver les quotas pour les offres importantes")
    print("   • D'accélérer les cycles de scraping")

if __name__ == "__main__":
    simulate_temporal_filtering()