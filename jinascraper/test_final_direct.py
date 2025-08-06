#!/usr/bin/env python3
"""Test direct final - approche dev senior."""

import asyncio
import sys
import os

# Add path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

async def test_database_with_source_name():
    """Test direct du DatabaseService avec source_name."""
    
    print("=== TEST DIRECT DATABASE SERVICE ===")
    
    try:
        from services.database_service import DatabaseService
        
        # Test data
        test_jobs = [{
            'title': 'Test Job Senior',
            'company': 'Test Company', 
            'profile': 'Test profile - should be mapped',  # ← Sera mappé
            'source_url': 'https://www.emploi.tg/test-senior-123',
            'extraction_method': 'gemini',
            'description': 'Test description'
        }]
        
        print(f"Input jobs: {len(test_jobs)}")
        print(f"First job has 'profile': {'profile' in test_jobs[0]}")
        
        # Create service
        db_service = DatabaseService()
        
        # Test avec source_name (LA CORRECTION)
        print("Testing with source_name='emploi_tg'...")
        result = await db_service.upsert_jobs_batch(test_jobs, 'emploi_tg')
        
        print(f"Result: {result}")
        
        # Vérifications
        success = result.get('success', False)
        saved = result.get('saved_jobs', 0)
        errors = result.get('errors', 0)
        
        print(f"Success: {success}")
        print(f"Saved: {saved}")
        print(f"Errors: {errors}")
        
        if success and saved > 0 and errors == 0:
            print("✓ CORRECTION SOURCE_SITE FONCTIONNE !")
            return True
        else:
            print("✗ Problème persiste")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_field_mapping_direct():
    """Test direct du field mapping."""
    
    print("\n=== TEST DIRECT FIELD MAPPING ===")
    
    try:
        from services.field_mapper import FieldMapper
        
        mapper = FieldMapper()
        
        test_data = {
            'title': 'Test Job',
            'company': 'Test Company',
            'profile': 'This should be mapped to profile_description',
            'source_url': 'https://test.com/job/123',
            'extraction_method': 'gemini'
        }
        
        print(f"Input: {list(test_data.keys())}")
        print(f"Has 'profile': {'profile' in test_data}")
        
        # Apply mapping
        result = mapper.map_job_fields(test_data, 'emploi_tg')
        
        print(f"Output: {list(result.keys())}")
        print(f"Has 'profile_description': {'profile_description' in result}")
        print(f"Has 'profile': {'profile' in result}")
        print(f"Has 'source_site': {'source_site' in result}")
        
        if result.get('source_site') == 'emploi_tg':
            print(f"source_site: {result['source_site']}")
        
        # Vérifications
        mapping_ok = 'profile_description' in result and 'profile' not in result
        source_site_ok = result.get('source_site') == 'emploi_tg'
        
        if mapping_ok and source_site_ok:
            print("✓ FIELD MAPPING FONCTIONNE !")
            return True
        else:
            print("✗ Field mapping problématique")
            return False
            
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Test principal."""
    
    print("TESTS DIRECTS - APPROCHE DEV SENIOR")
    print("=" * 50)
    
    # Test 1: Field Mapping
    test1 = await test_field_mapping_direct()
    
    # Test 2: Database Service  
    test2 = await test_database_with_source_name()
    
    print(f"\n=== RÉSULTATS FINAUX ===")
    print(f"Field Mapping: {'✓ OK' if test1 else '✗ KO'}")
    print(f"Database Service: {'✓ OK' if test2 else '✗ KO'}")
    
    if test1 and test2:
        print("\n🎉 TOUS LES TESTS PASSENT !")
        print("La correction devrait fonctionner en production.")
        return True
    else:
        print("\n❌ Certains tests échouent")
        return False

if __name__ == '__main__':
    success = asyncio.run(main())
    exit(0 if success else 1)