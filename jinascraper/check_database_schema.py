#!/usr/bin/env python3
"""Check if database schema is properly set up."""

import os
import asyncio
from dotenv import load_dotenv

load_dotenv()

async def check_database_schema():
    """Check database schema and tables."""
    print("🔧 Checking database schema...")
    
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    try:
        from supabase import create_client
        supabase = create_client(supabase_url, supabase_key)
        
        # Check jobs table structure
        print("\n📊 Checking jobs table...")
        try:
            result = supabase.table('jobs').select('*').limit(1).execute()
            print("✅ Jobs table exists and accessible")
            
            if result.data:
                job = result.data[0]
                print(f"📋 Sample job fields: {list(job.keys())}")
            else:
                print("📋 Jobs table is empty")
                
        except Exception as e:
            print(f"❌ Jobs table issue: {str(e)}")
        
        # Check scraping_stats table
        print("\n📊 Checking scraping_stats table...")
        try:
            result = supabase.table('scraping_stats').select('*').limit(1).execute()
            print("✅ Scraping_stats table exists and accessible")
            
            if result.data:
                stat = result.data[0]
                print(f"📋 Sample stat fields: {list(stat.keys())}")
            else:
                print("📋 Scraping_stats table is empty")
                
        except Exception as e:
            if "relation \"scraping_stats\" does not exist" in str(e):
                print("⚠️ Scraping_stats table doesn't exist - needs to be created")
            else:
                print(f"❌ Scraping_stats table issue: {str(e)}")
        
        # Check views
        print("\n📊 Checking database views...")
        try:
            result = supabase.table('active_jobs').select('*').limit(1).execute()
            print("✅ Active_jobs view exists")
        except Exception as e:
            print(f"⚠️ Active_jobs view issue: {str(e)}")
        
        try:
            result = supabase.table('jobs_by_source_stats').select('*').limit(1).execute()
            print("✅ Jobs_by_source_stats view exists")
        except Exception as e:
            print(f"⚠️ Jobs_by_source_stats view issue: {str(e)}")
        
        print("\n🎉 Database schema check completed!")
        return True
        
    except Exception as e:
        print(f"❌ Schema check failed: {str(e)}")
        return False

if __name__ == "__main__":
    asyncio.run(check_database_schema())