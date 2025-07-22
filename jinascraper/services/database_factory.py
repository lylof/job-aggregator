"""Database factory for selecting the appropriate database service."""

from typing import Union, Type
import structlog

from ..config import config
from .database_service import DatabaseService
from .prisma_service import PrismaService

logger = structlog.get_logger(__name__)


class DatabaseFactory:
    """Factory for creating database service instances."""
    
    @staticmethod
    def get_database_service() -> Union[DatabaseService, PrismaService]:
        """Get the appropriate database service based on configuration."""
        provider = config.database_provider.lower()
        
        if provider == "prisma":
            logger.info("Using Prisma database service")
            return PrismaService()
        elif provider == "supabase":
            logger.info("Using Supabase database service")
            return DatabaseService()
        else:
            logger.warning(f"Unknown database provider: {provider}, defaulting to Prisma")
            return PrismaService()