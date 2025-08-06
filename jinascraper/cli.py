#!/usr/bin/env python3
"""JinaScraper CLI - Command line interface for job scraping operations."""

import asyncio
import sys
import os
import click
from pathlib import Path
from dotenv import load_dotenv

# Exécution depuis le repo (script direct) ET depuis package (python -m jinascraper.cli)
# 1) Ajouter le répertoire courant et le parent au PYTHONPATH si nécessaire
cwd = os.path.abspath(os.path.dirname(__file__))
parent = os.path.abspath(os.path.join(cwd, os.pardir))
for p in (cwd, parent):
    if p not in sys.path:
        sys.path.insert(0, p)

# 2) CORRECTION CRITIQUE: Charger les variables d'environnement
env_paths = [
    Path(cwd) / ".env",  # jinascraper/.env
    Path(parent) / ".env",  # root .env
    ".env"  # current directory
]

for env_path in env_paths:
    if Path(env_path).exists():
        load_dotenv(env_path)
        print(f"🔧 Variables d'environnement chargées depuis {env_path}")
        break
else:
    print("⚠️  Aucun fichier .env trouvé")

# 2) Importer app de manière robuste (local d'abord, puis packagé)
try:
    from app import JinaScraperApp, ScrapeOptions  # local import
except Exception:
    from jinascraper.app import JinaScraperApp, ScrapeOptions  # package import


@click.group()
def cli():
    """JinaScraper - AI-powered job scraping for Togo."""
    pass


@cli.command()
@click.option('--sources', help='Comma-separated list of sources to scrape')
@click.option('--max-urls', default=100, help='Maximum URLs to process per source')
@click.option('--dry-run', is_flag=True, help='Run without saving data')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
@click.option('--quiet', is_flag=True, help='Minimal logging output')
@click.option('--show-urls', default=3, help='Number of sample URLs to display')
@click.option('--no-color', is_flag=True, help='Disable colored output')
# 🚀 NOUVELLES OPTIONS POUR FILTRAGE TEMPOREL
@click.option('--recent-only', is_flag=True, help='Only process jobs published since last scraping (production mode)')
@click.option('--max-age-hours', type=int, help='Maximum age of jobs in hours (overrides recent-only)')
@click.option('--force-all', is_flag=True, help='Process all jobs ignoring temporal filters (development mode)')
def scrape(sources, max_urls, dry_run, verbose, quiet, show_urls, no_color, recent_only, max_age_hours, force_all):
    """Execute a full scraping cycle."""
    sources_list = sources.split(',') if sources else None
    options = ScrapeOptions(
        sources=sources_list, 
        max_urls=max_urls, 
        dry_run=dry_run, 
        verbose=verbose,
        quiet=quiet,
        show_urls=show_urls,
        use_colors=not no_color,
        # 🚀 NOUVELLES OPTIONS TEMPORELLES
        recent_only=recent_only,
        max_age_hours=max_age_hours,
        force_all=force_all
    )
    app = JinaScraperApp()
    
    try:
        results = asyncio.run(app.run_full_scrape(options))
        report_success = app.generate_scrape_report(results, options)
        exit_code = 0 if results.success and report_success else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        click.echo("\n⚠️  Scraping interrupted by user")
        sys.exit(1)
    except Exception as e:
        click.echo(f"FATAL ERROR: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option('--sources', help='Comma-separated list of sources to test')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
def diagnose(sources, verbose):
    """🔍 DIAGNOSTIC - Test Stage 1 only (URL extraction)."""
    click.echo("=" * 80)
    click.echo("🔍 DIAGNOSTIC STAGE 1 SEUL - EXTRACTION D'URLS")
    click.echo("=" * 80)
    
    sources_list = sources.split(',') if sources else None
    options = ScrapeOptions(
        sources=sources_list, 
        max_urls=50,  # Limiter pour le diagnostic
        dry_run=True,  # Toujours en dry-run pour diagnostic
        verbose=verbose,
        quiet=False,
        show_urls=5,
        use_colors=True
    )
    
    app = JinaScraperApp()
    
    try:
        # Utiliser une méthode de diagnostic spéciale
        results = asyncio.run(app.run_stage1_diagnostic(options))
        app.generate_diagnostic_report(results, options)
        sys.exit(0)
    except KeyboardInterrupt:
        click.echo("\n⚠️  Diagnostic interrupted by user")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Diagnostic error: {str(e)}")
        sys.exit(1)


@cli.command()
@click.option('--url', help='Specific URL to test for Stage 2')
@click.option('--source', default='emploi_tg', help='Source name for configuration')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
def diagnose2(url, source, verbose):
    """🔍 DIAGNOSTIC - Test Stage 2 only (content extraction)."""
    click.echo("=" * 80)
    click.echo("🔍 DIAGNOSTIC STAGE 2 SEUL - EXTRACTION DE CONTENU")
    click.echo("=" * 80)
    
    # URL par défaut si non spécifiée
    test_url = url or "https://www.emploi.tg/offre-emploi-togo/conseiller-clientele-bilingue-lome-326684"
    
    options = ScrapeOptions(
        sources=[source], 
        max_urls=1,
        dry_run=True,
        verbose=verbose,
        quiet=False,
        show_urls=1,
        use_colors=True
    )
    
    app = JinaScraperApp()
    
    try:
        results = asyncio.run(app.run_stage2_diagnostic(test_url, source, options))
        app.generate_stage2_diagnostic_report(results, test_url, options)
        sys.exit(0)
    except KeyboardInterrupt:
        click.echo("\n⚠️  Diagnostic interrupted by user")
        sys.exit(1)
    except Exception as e:
        click.echo(f"❌ Diagnostic error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    cli()