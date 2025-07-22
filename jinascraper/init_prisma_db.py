#!/usr/bin/env python
"""Initialize Prisma database for Jina Job Scraper."""

import asyncio
import os
import sys
from pathlib import Path

# Add the parent directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Load environment variables
from dotenv import load_dotenv
load_dotenv("jinascraper/.env")
load_dotenv(".env")

import structlog
from prisma import Prisma
from prisma.cli import run_command

logger = structlog.get_logger(__name__)


async def init_prisma_db():
    """Initialize Prisma database."""
    logger.info("Initializing Prisma database...")
    
    # Generate Prisma client
    logger.info("Generating Prisma client...")
    try:
        run_command(["generate"], cwd="jinascraper/prisma")
        logger.info("Prisma client generated successfully")
    except Exception as e:
        logger.error("Failed to generate Prisma client", error=str(e))
        return False
    
    # Push schema to database
    logger.info("Pushing schema to database...")
    try:
        run_command(["db", "push"], cwd="jinascraper/prisma")
        logger.info("Schema pushed to database successfully")
    except Exception as e:
        logger.error("Failed to push schema to database", error=str(e))
        return False
    
    # Verify connection
    logger.info("Verifying database connection...")
    try:
        prisma = Prisma()
        await prisma.connect()
        
        # Check if we can query the database
        job_count = await prisma.job.count()
        stats_count = await prisma.scrapingstat.count()
        
        logger.info("Database connection verified", job_count=job_count, stats_count=stats_count)
        
        # Insert initial scraping stats if needed
        if stats_count == 0:
            logger.info("Inserting initial scraping stats...")
            from datetime import datetime
            
            sources = ["emploi_tg", "emploitogo_info", "yop_lfrii", "anpe_togo", "linkedin_togo"]
            today = datetime.now().date()
            
            for source in sources:
                await prisma.scrapingstat.create(
                    data={
                        "sourceSite": source,
                        "scrapeDate": today,
                        "urlsDiscovered": 0,
                        "urlsProcessed": 0,
                        "jobsCreated": 0,
                        "successRate": 0.0
                    }
                )
            
            logger.info("Initial scraping stats inserted successfully")
        
        await prisma.disconnect()
        return True
    except Exception as e:
        logger.error("Failed to verify database connection", error=str(e))
        return False


if __name__ == "__main__":
    success = asyncio.run(init_prisma_db())
    sys.exit(0 if success else 1)