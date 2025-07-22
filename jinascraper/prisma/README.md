# Prisma Database Integration for Jina Job Scraper

This directory contains the Prisma schema and configuration for the Jina Job Scraper project.

## Setup Instructions

### 1. Install Dependencies

First, make sure you have all the required dependencies installed:

```bash
pip install -r ../requirements.txt
```

### 2. Configure Environment Variables

Create a `.env` file in the `jinascraper` directory with the following variables:

```
# Database Configuration
DATABASE_PROVIDER=prisma
DATABASE_URL=postgresql://username:password@localhost:5432/jobscraper?schema=public
```

Replace the `DATABASE_URL` with your actual PostgreSQL connection string.

### 3. Initialize the Database

Run the initialization script to set up the database:

```bash
python jinascraper/init_prisma_db.py
```

This will:
- Generate the Prisma client
- Push the schema to the database
- Create initial data if needed

### 4. Verify the Setup

Run the test script to verify that everything is working correctly:

```bash
python jinascraper/test_prisma.py
```

## Using Prisma in the Application

The application uses a database factory pattern to select the appropriate database service:

```python
from jinascraper.services.database_factory import DatabaseFactory

# Get the database service based on configuration
db_service = DatabaseFactory.get_database_service()

# Use the service
await db_service.connect()
job = await db_service.get_job_by_url("https://example.com/job")
```

## Prisma Schema

The Prisma schema (`schema.prisma`) defines the database structure:

- `Job` model: Represents job offers with all their details
- `ScrapingStat` model: Stores statistics about scraping operations

## Migrations

To create and apply migrations when you change the schema:

1. Update the `schema.prisma` file
2. Run the following commands:

```bash
# Generate a migration
prisma migrate dev --name your_migration_name --schema ./jinascraper/prisma/schema.prisma

# Apply migrations
prisma migrate deploy --schema ./jinascraper/prisma/schema.prisma
```

## Prisma Studio

To explore your database with a visual interface:

```bash
prisma studio --schema ./jinascraper/prisma/schema.prisma
```

This will open a web interface at http://localhost:5555 where you can view and edit your data.