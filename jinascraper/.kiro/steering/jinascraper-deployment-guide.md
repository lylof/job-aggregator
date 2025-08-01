# 🚀 GUIDE DÉPLOIEMENT ET CONFIGURATION - JINASCRAPER
**Date:** 31 Janvier 2025  
**Version:** 2.0  
**Audience:** DevOps, Équipe technique  
**Statut:** Guide de production

---

## 🎯 OBJECTIF

Ce guide fournit les procédures complètes de déploiement, configuration et mise en production du système JinaScraper, basé sur l'audit technique de janvier 2025.

---

## 📋 PRÉREQUIS SYSTÈME

### 🖥️ **ENVIRONNEMENT MINIMUM**

| Composant | Minimum | Recommandé | Production |
|-----------|---------|------------|------------|
| **CPU** | 2 cores | 4 cores | 8 cores |
| **RAM** | 4 GB | 8 GB | 16 GB |
| **Stockage** | 20 GB | 50 GB | 100 GB |
| **Python** | 3.11+ | 3.12+ | 3.12+ |
| **Redis** | 6.0+ | 7.0+ | 7.0+ |
| **PostgreSQL** | 13+ | 15+ | 15+ |

### 🌐 **ACCÈS RÉSEAU REQUIS**

```yaml
# APIs externes
outbound_access:
  - r.jina.ai:443          # Jina Reader API
  - generativelanguage.googleapis.com:443  # Gemini API
  - redis.server:6379      # Redis (si externe)
  - postgres.server:5432   # PostgreSQL (si externe)

# Ports internes
internal_ports:
  - 8000  # API REST (optionnel)
  - 6379  # Redis local
  - 5432  # PostgreSQL local
```

---

## 🔧 INSTALLATION ÉTAPE PAR ÉTAPE

### 1️⃣ **PRÉPARATION ENVIRONNEMENT**

```bash
# Mise à jour système
sudo apt update && sudo apt upgrade -y

# Installation Python 3.12
sudo apt install python3.12 python3.12-venv python3.12-dev -y

# Installation Redis
sudo apt install redis-server -y
sudo systemctl enable redis-server
sudo systemctl start redis-server

# Installation PostgreSQL
sudo apt install postgresql postgresql-contrib -y
sudo systemctl enable postgresql
sudo systemctl start postgresql
```

### 2️⃣ **CONFIGURATION BASE DE DONNÉES**

```bash
# Création utilisateur et base
sudo -u postgres psql << EOF
CREATE USER jinascraper WITH PASSWORD 'secure_password_here';
CREATE DATABASE jinascraper_db OWNER jinascraper;
GRANT ALL PRIVILEGES ON DATABASE jinascraper_db TO jinascraper;
\q
EOF

# Test connexion
psql -h localhost -U jinascraper -d jinascraper_db -c "SELECT version();"
```

### 3️⃣ **INSTALLATION APPLICATION**

```bash
# Clonage du projet
git clone <repository_url> /opt/jinascraper
cd /opt/jinascraper

# Création environnement virtuel
python3.12 -m venv venv
source venv/bin/activate

# Installation dépendances
pip install --upgrade pip
pip install -r jinascraper/requirements.txt

# Vérification installation
python -c "import jinascraper; print('Installation OK')"
```

### 4️⃣ **CONFIGURATION ENVIRONNEMENT**

```bash
# Copie du fichier de configuration
cp jinascraper/.env.example jinascraper/.env

# Édition configuration
nano jinascraper/.env
```

**Contenu `.env` de production :**

```env
# APIs Externes
JINA_API_KEY=jina_your_production_key_here
GEMINI_API_KEY=your_gemini_production_key_here

# Base de données
DATABASE_URL=postgresql://jinascraper:secure_password_here@localhost:5432/jinascraper_db
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_supabase_anon_key

# Cache Redis
REDIS_URL=redis://localhost:6379/0
REDIS_TTL_SECONDS=604800

# Configuration scraping
MAX_CONCURRENT_REQUESTS=10
REQUEST_DELAY_SECONDS=1.0
TIMEOUT_SECONDS=45

# Logging
LOG_LEVEL=INFO
STRUCTURED_LOGGING=true
ENVIRONMENT=production

# Sécurité
SECRET_KEY=your_secret_key_here_32_chars_min
ALLOWED_HOSTS=localhost,127.0.0.1,your-domain.com
```

### 5️⃣ **INITIALISATION BASE DE DONNÉES**

```bash
# Migration schéma
python jinascraper/database/migrations/init_schema.py

# Ou avec Prisma (si utilisé)
cd jinascraper
npx prisma migrate deploy
npx prisma generate
```

### 6️⃣ **TESTS DE VALIDATION**

```bash
# Test configuration
python cli.py --help

# Test diagnostic complet
python cli.py diagnose --verbose

# Test cycle complet
python cli.py scrape --sources emploi_tg --limit 3 --verbose

# Audit complet
python audit_complet_janvier_2025_v2.py
```

---

## 🔒 CONFIGURATION SÉCURITÉ

### 🛡️ **SÉCURISATION SYSTÈME**

```bash
# Création utilisateur dédié
sudo useradd -r -s /bin/false jinascraper
sudo chown -R jinascraper:jinascraper /opt/jinascraper

# Permissions fichiers
chmod 600 /opt/jinascraper/jinascraper/.env
chmod +x /opt/jinascraper/cli.py

# Configuration firewall
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 8000/tcp  # API (si exposée)
sudo ufw enable
```

### 🔐 **GESTION SECRETS**

```bash
# Utilisation de secrets manager (recommandé)
# AWS Secrets Manager, Azure Key Vault, etc.

# Ou chiffrement local
sudo apt install gpg -y

# Chiffrer le fichier .env
gpg --symmetric --cipher-algo AES256 jinascraper/.env
rm jinascraper/.env

# Script de déchiffrement
cat > /opt/jinascraper/decrypt_env.sh << 'EOF'
#!/bin/bash
gpg --quiet --batch --yes --decrypt --passphrase="$ENV_PASSPHRASE" \
    jinascraper/.env.gpg > jinascraper/.env
EOF
chmod +x /opt/jinascraper/decrypt_env.sh
```

---

## 🔄 DÉPLOIEMENT AUTOMATISÉ

### 🐳 **DOCKER (RECOMMANDÉ)**

**Dockerfile :**

```dockerfile
FROM python:3.12-slim

# Installation dépendances système
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    redis-tools \
    && rm -rf /var/lib/apt/lists/*

# Création utilisateur
RUN useradd -r -s /bin/false jinascraper

# Copie application
WORKDIR /app
COPY jinascraper/ ./jinascraper/
COPY cli.py requirements.txt ./

# Installation dépendances Python
RUN pip install --no-cache-dir -r requirements.txt

# Configuration
USER jinascraper
EXPOSE 8000

# Point d'entrée
CMD ["python", "cli.py", "scrape", "--continuous"]
```

**docker-compose.yml :**

```yaml
version: '3.8'

services:
  jinascraper:
    build: .
    environment:
      - REDIS_URL=redis://redis:6379/0
      - DATABASE_URL=postgresql://jinascraper:password@postgres:5432/jinascraper_db
    depends_on:
      - redis
      - postgres
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  redis:
    image: redis:7-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped

  postgres:
    image: postgres:15-alpine
    environment:
      - POSTGRES_DB=jinascraper_db
      - POSTGRES_USER=jinascraper
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

volumes:
  redis_data:
  postgres_data:
```

### ⚙️ **SYSTEMD SERVICE**

```bash
# Création service systemd
sudo tee /etc/systemd/system/jinascraper.service << EOF
[Unit]
Description=JinaScraper Job Aggregator
After=network.target redis.service postgresql.service
Requires=redis.service postgresql.service

[Service]
Type=simple
User=jinascraper
Group=jinascraper
WorkingDirectory=/opt/jinascraper
Environment=PATH=/opt/jinascraper/venv/bin
ExecStartPre=/opt/jinascraper/decrypt_env.sh
ExecStart=/opt/jinascraper/venv/bin/python cli.py scrape --continuous
ExecReload=/bin/kill -HUP \$MAINPID
Restart=always
RestartSec=10

# Sécurité
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/jinascraper/logs

[Install]
WantedBy=multi-user.target
EOF

# Activation service
sudo systemctl daemon-reload
sudo systemctl enable jinascraper
sudo systemctl start jinascraper

# Vérification
sudo systemctl status jinascraper
```

---

## 📊 MONITORING ET OBSERVABILITÉ

### 📈 **MÉTRIQUES PROMETHEUS**

```python
# jinascraper/utils/metrics.py
from prometheus_client import Counter, Histogram, Gauge, start_http_server

# Métriques définies
URLS_EXTRACTED = Counter('jinascraper_urls_extracted_total', 'URLs extracted', ['source'])
JOBS_PROCESSED = Counter('jinascraper_jobs_processed_total', 'Jobs processed', ['status'])
STAGE_DURATION = Histogram('jinascraper_stage_duration_seconds', 'Stage duration', ['stage'])
ACTIVE_SOURCES = Gauge('jinascraper_sources_active', 'Active sources count')

def start_metrics_server(port=9090):
    """Démarre le serveur de métriques"""
    start_http_server(port)
```

### 🚨 **ALERTES**

```yaml
# alerts.yml
groups:
  - name: jinascraper
    rules:
      - alert: JinaScraperDown
        expr: up{job="jinascraper"} == 0
        for: 1m
        labels:
          severity: critical
        annotations:
          summary: "JinaScraper is down"

      - alert: NoURLsExtracted
        expr: increase(jinascraper_urls_extracted_total[1h]) == 0
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "No URLs extracted in the last hour"

      - alert: HighErrorRate
        expr: rate(jinascraper_jobs_processed_total{status="error"}[5m]) > 0.1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High error rate detected"
```

---

## 🔄 CI/CD PIPELINE

### 🏗️ **GITHUB ACTIONS**

```yaml
# .github/workflows/deploy.yml
name: Deploy JinaScraper

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
      postgres:
        image: postgres:15-alpine
        env:
          POSTGRES_PASSWORD: postgres
          POSTGRES_DB: jinascraper_test
        ports:
          - 5432:5432

    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
          
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r jinascraper/requirements.txt
          
      - name: Run tests
        env:
          REDIS_URL: redis://localhost:6379/0
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/jinascraper_test
          JINA_API_KEY: ${{ secrets.JINA_API_KEY }}
          GEMINI_API_KEY: ${{ secrets.GEMINI_API_KEY }}
        run: |
          python jinascraper/test_imports_fixed.py
          python cli.py diagnose --sources emploi_tg --verbose
          python audit_complet_janvier_2025_v2.py

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Deploy to production
        env:
          DEPLOY_HOST: ${{ secrets.DEPLOY_HOST }}
          DEPLOY_USER: ${{ secrets.DEPLOY_USER }}
          DEPLOY_KEY: ${{ secrets.DEPLOY_KEY }}
        run: |
          echo "$DEPLOY_KEY" > deploy_key
          chmod 600 deploy_key
          scp -i deploy_key -r . $DEPLOY_USER@$DEPLOY_HOST:/opt/jinascraper/
          ssh -i deploy_key $DEPLOY_USER@$DEPLOY_HOST "
            cd /opt/jinascraper
            source venv/bin/activate
            pip install -r jinascraper/requirements.txt
            sudo systemctl restart jinascraper
          "
```

---

## 🎯 CHECKLIST DE DÉPLOIEMENT

### ✅ **PRÉ-DÉPLOIEMENT**

- [ ] Environnement système préparé
- [ ] Base de données configurée et testée
- [ ] Redis installé et fonctionnel
- [ ] Clés API obtenues et configurées
- [ ] Tests locaux réussis
- [ ] Sauvegardes configurées

### ✅ **DÉPLOIEMENT**

- [ ] Application installée
- [ ] Configuration environnement validée
- [ ] Services systemd configurés
- [ ] Monitoring activé
- [ ] Tests de validation réussis
- [ ] Documentation mise à jour

### ✅ **POST-DÉPLOIEMENT**

- [ ] Service démarré et stable
- [ ] Métriques collectées
- [ ] Alertes configurées
- [ ] Logs structurés
- [ ] Performance validée
- [ ] Équipe formée

---

## 🚨 PROCÉDURES D'URGENCE

### 🔥 **ROLLBACK RAPIDE**

```bash
# Arrêt service
sudo systemctl stop jinascraper

# Restauration version précédente
cd /opt/jinascraper
git checkout <previous_commit>
source venv/bin/activate
pip install -r jinascraper/requirements.txt

# Redémarrage
sudo systemctl start jinascraper
sudo systemctl status jinascraper
```

### ⚡ **DIAGNOSTIC RAPIDE**

```bash
# Vérification santé système
python cli.py diagnose --sources emploi_tg --verbose

# Logs récents
sudo journalctl -u jinascraper -n 50

# Métriques système
htop
df -h
free -h
```

---

*Guide de déploiement mis à jour le 31 janvier 2025*  
*Basé sur l'audit complet et les tests CLI validés*  
*Version 2.0 - Production Ready*