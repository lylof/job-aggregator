#!/usr/bin/env python3
"""Integration tests for DatabaseService with field mapping."""

import unittest
import asyncio
import sys
import os
from unittest.mock import patch, MagicMock, AsyncMock
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Set PYTHONPATH to avoid import issues
os.environ['PYTHONPATH'] = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

try:
    from services.database_service import DatabaseService
    from services.field_mapper import FieldMapper
    from utils.schema_validator import SchemaValidator
except ImportError as e:
    print(f"Import error: {e}")
    print("Running simplified test without full imports...")
    
    # Create mock classes for testing
    class DatabaseService:
        def __init__(self):
            self.field_mapper = None
            self.schema_validator = None
        def connect(self):
            pass
        def _prepare_job_data(self, data, source):
            return data
    
    class FieldMapper:
        pass
    
    class SchemaValidator:
        pass


class TestDatabaseIntegration(unittest.TestCase):
    """Integration test cases for DatabaseService with field mapping."""
    
    def setUp(self):
        """Set up test fixtures."""
        # Mock Supabase client to avoid real database calls
        self.mock_supabase_client = MagicMock()
        self.mock_table = MagicMock()
        self.mock_supabase_client.table.return_value = self.mock_table
        
        # Create DatabaseService with mocked client
        with patch('services.database_service.create_client', return_value=self.mock_supabase_client):
            self.db_service = DatabaseService()
            self.db_service.connect()
    
    def test_initialization_with_field_mapping(self):
        """Test DatabaseService initialization with field mapping components."""
        self.assertIsInstance(self.db_service.field_mapper, FieldMapper)
        self.assertIsInstance(self.db_service.schema_validator, SchemaValidator)
    
    def test_prepare_job_data_with_mapping(self):
        """Test _prepare_job_data with field mapping."""
        test_data = {
            'title': 'Développeur Python',
            'company': 'TechCorp',
            'profile': 'Profil recherché: développeur expérimenté',  # ← Should be mapped
            'source_url': 'https://example.com/job/123',
            'extraction_method': 'gemini'
        }
        
        result = self.db_service._prepare_job_data(test_data, 'emploi_tg')
        
        # Check critical mapping was applied
        self.assertIn('profile_description', result)
        self.assertNotIn('profile', result)
        self.assertEqual(result['profile_description'], 'Profil recherché: développeur expérimenté')
        
        # Check source_site was added
        self.assertIn('source_site', result)
        self.assertEqual(result['source_site'], 'emploi_tg')
        
        # Check item_id was generated
        self.assertIn('item_id', result)
        self.assertTrue(result['item_id'].startswith('emploi_tg_'))
    
    def test_prepare_job_data_datetime_conversion(self):
        """Test datetime conversion in _prepare_job_data."""
        test_data = {
            'title': 'Test Job',
            'company': 'Test Company',
            'source_url': 'https://example.com/job/123',
            'extraction_method': 'gemini',
            'created_at': datetime.now(),
            'extraction_metadata': {
                'extracted_at': datetime.now()
            }
        }
        
        result = self.db_service._prepare_job_data(test_data, 'test_source')
        
        # Check datetime fields were converted to strings
        self.assertIsInstance(result['created_at'], str)
        self.assertIsInstance(result['extraction_metadata']['extracted_at'], str)
    
    async def test_upsert_job_with_mapping(self):
        """Test upsert_job with field mapping integration."""
        # Mock successful upsert response
        mock_response = MagicMock()
        mock_response.data = [{
            'id': 'test-id',
            'title': 'Développeur Python',
            'profile_description': 'Profil recherché'
        }]
        self.mock_table.upsert.return_value.execute.return_value = mock_response
        
        test_data = {
            'title': 'Développeur Python',
            'company': 'TechCorp',
            'profile': 'Profil recherché',  # ← Should be mapped
            'source_url': 'https://example.com/job/123',
            'extraction_method': 'gemini'
        }
        
        result = await self.db_service.upsert_job(test_data, 'emploi_tg')
        
        # Check result structure
        self.assertTrue(result['success'])
        self.assertIn('job_id', result)
        self.assertEqual(result['operation'], 'upsert')
        
        # Verify upsert was called with mapped data
        self.mock_table.upsert.assert_called_once()
        call_args = self.mock_table.upsert.call_args[0][0]
        self.assertIn('profile_description', call_args)
        self.assertNotIn('profile', call_args)
    
    async def test_upsert_jobs_batch_with_mapping(self):
        """Test batch upsert with field mapping."""
        # Mock successful batch upsert response
        mock_response = MagicMock()
        mock_response.data = [
            {'id': 'test-id-1', 'title': 'Job 1'},
            {'id': 'test-id-2', 'title': 'Job 2'}
        ]
        self.mock_table.upsert.return_value.execute.return_value = mock_response
        
        test_jobs = [
            {
                'title': 'Job 1',
                'company': 'Company 1',
                'profile': 'Profile 1',  # ← Should be mapped
                'source_url': 'https://example.com/job/1',
                'extraction_method': 'gemini'
            },
            {
                'title': 'Job 2',
                'company': 'Company 2',
                'profile': 'Profile 2',  # ← Should be mapped
                'source_url': 'https://example.com/job/2',
                'extraction_method': 'gemini'
            }
        ]
        
        result = await self.db_service.upsert_jobs_batch(test_jobs, 'emploi_tg')
        
        # Check result structure
        self.assertTrue(result['success'])
        self.assertEqual(result['total_jobs'], 2)
        self.assertEqual(result['saved_jobs'], 2)
        self.assertEqual(result['errors'], 0)
        
        # Verify batch upsert was called
        self.mock_table.upsert.assert_called_once()
        call_args = self.mock_table.upsert.call_args[0][0]
        
        # Check all jobs were mapped
        self.assertEqual(len(call_args), 2)
        for job in call_args:
            self.assertIn('profile_description', job)
            self.assertNotIn('profile', job)
            self.assertIn('source_site', job)
    
    async def test_error_handling_in_batch_upsert(self):
        """Test error handling in batch upsert with field mapping."""
        # Mock database error
        self.mock_table.upsert.return_value.execute.side_effect = Exception("Database error")
        
        test_jobs = [
            {
                'title': 'Test Job',
                'company': 'Test Company',
                'source_url': 'https://example.com/job/1',
                'extraction_method': 'gemini'
            }
        ]
        
        result = await self.db_service.upsert_jobs_batch(test_jobs, 'test_source')
        
        # Check error handling
        self.assertFalse(result['success'])
        self.assertEqual(result['total_jobs'], 1)
        self.assertEqual(result['saved_jobs'], 0)
        self.assertEqual(result['errors'], 1)
        self.assertIn('error_details', result)
    
    def test_field_mapping_with_invalid_data(self):
        """Test field mapping with invalid data that should be filtered."""
        test_data = {
            'title': 'Test Job',
            'company': 'Test Company',
            'profile': 'Test profile',
            'source_url': 'https://example.com/job/123',
            'extraction_method': 'gemini',
            'invalid_field': 'Should be removed',
            'another_invalid': 'Also removed'
        }
        
        result = self.db_service._prepare_job_data(test_data, 'test_source')
        
        # Valid fields should be present (after mapping)
        self.assertIn('title', result)
        self.assertIn('company', result)
        self.assertIn('profile_description', result)
        
        # Invalid fields should be removed
        self.assertNotIn('invalid_field', result)
        self.assertNotIn('another_invalid', result)
        self.assertNotIn('profile', result)  # Should be mapped away
    
    def test_source_specific_metadata_extraction(self):
        """Test extraction of source-specific metadata."""
        test_data = {
            'title': 'Test Job',
            'company': 'Test Company',
            'source_url': 'https://example.com/job/123',
            'extraction_method': 'gemini',
            'company_logo': 'https://example.com/logo.png',  # emploi_tg specific
            'company_website': 'https://example.com',  # emploi_tg specific
            'benefits': ['Health', 'Vacation']  # emploi_tg specific
        }
        
        result = self.db_service._prepare_job_data(test_data, 'emploi_tg')
        
        # Check extraction_metadata was created
        self.assertIn('extraction_metadata', result)
        self.assertIn('source_specific_data', result['extraction_metadata'])
        self.assertIn('emploi_tg_data', result['extraction_metadata']['source_specific_data'])
        
        # Check source-specific data was extracted
        emploi_tg_data = result['extraction_metadata']['source_specific_data']['emploi_tg_data']
        self.assertEqual(emploi_tg_data['company_logo'], 'https://example.com/logo.png')
        self.assertEqual(emploi_tg_data['company_website'], 'https://example.com')
        self.assertEqual(emploi_tg_data['benefits'], ['Health', 'Vacation'])
    
    def test_raw_data_preservation(self):
        """Test that raw_data is preserved in preparation."""
        test_data = {
            'title': 'Test Job',
            'company': 'Test Company',
            'profile': 'Test profile',
            'source_url': 'https://example.com/job/123',
            'extraction_method': 'gemini',
            'custom_field': 'Custom value'
        }
        
        result = self.db_service._prepare_job_data(test_data, 'test_source')
        
        # Check raw_data is preserved
        self.assertIn('raw_data', result)
        self.assertEqual(result['raw_data'], test_data)
    
    def test_item_id_generation_consistency(self):
        """Test that item_id generation is consistent."""
        test_data = {
            'title': 'Test Job',
            'company': 'Test Company',
            'source_url': 'https://example.com/job/123',
            'extraction_method': 'gemini'
        }
        
        result1 = self.db_service._prepare_job_data(test_data, 'test_source')
        result2 = self.db_service._prepare_job_data(test_data, 'test_source')
        
        # Same data should generate same item_id
        self.assertEqual(result1['item_id'], result2['item_id'])
        
        # Different source should generate different item_id
        result3 = self.db_service._prepare_job_data(test_data, 'different_source')
        self.assertNotEqual(result1['item_id'], result3['item_id'])
    
    def test_multiple_source_mappings(self):
        """Test field mapping for different sources."""
        sources_data = {
            'emploi_tg': {
                'title': 'Job 1',
                'company': 'Company 1',
                'company_logo': 'logo1.png',
                'source_url': 'https://emploi.tg/job/1',
                'extraction_method': 'gemini'
            },
            'linkedin_togo': {
                'title': 'Job 2',
                'company': 'Company 2',
                'company_size': '100-500',
                'industry': 'Tech',
                'source_url': 'https://linkedin.com/job/2',
                'extraction_method': 'gemini'
            },
            'indeed_togo': {
                'title': 'Job 3',
                'company': 'Company 3',
                'salary_estimate': '50k-60k',
                'source_url': 'https://indeed.com/job/3',
                'extraction_method': 'gemini'
            }
        }
        
        for source_name, data in sources_data.items():
            result = self.db_service._prepare_job_data(data, source_name)
            
            # Check source_site is set correctly
            self.assertEqual(result['source_site'], source_name)
            
            # Check source-specific data is extracted
            self.assertIn('extraction_metadata', result)
            source_data_key = f'{source_name}_data'
            self.assertIn(source_data_key, result['extraction_metadata']['source_specific_data'])
    
    async def test_concurrent_batch_operations(self):
        """Test concurrent batch operations with field mapping."""
        # Mock successful responses
        mock_response = MagicMock()
        mock_response.data = [{'id': 'test-id', 'title': 'Test Job'}]
        self.mock_table.upsert.return_value.execute.return_value = mock_response
        
        # Create multiple batches
        batches = []
        for i in range(3):
            batch = [
                {
                    'title': f'Job {i}-{j}',
                    'company': f'Company {i}-{j}',
                    'profile': f'Profile {i}-{j}',
                    'source_url': f'https://example.com/job/{i}-{j}',
                    'extraction_method': 'gemini'
                }
                for j in range(2)
            ]
            batches.append(batch)
        
        # Run concurrent operations
        tasks = [
            self.db_service.upsert_jobs_batch(batch, f'source_{i}')
            for i, batch in enumerate(batches)
        ]
        
        results = await asyncio.gather(*tasks)
        
        # Check all operations succeeded
        for result in results:
            self.assertTrue(result['success'])
            self.assertEqual(result['total_jobs'], 2)
            self.assertEqual(result['saved_jobs'], 2)
    
    def test_large_batch_processing(self):
        """Test processing of large batches with field mapping."""
        # Create large batch
        large_batch = []
        for i in range(100):
            job = {
                'title': f'Job {i}',
                'company': f'Company {i}',
                'profile': f'Profile {i}',
                'source_url': f'https://example.com/job/{i}',
                'extraction_method': 'gemini'
            }
            large_batch.append(job)
        
        # Process each job through field mapping
        processed_jobs = []
        for job in large_batch:
            processed = self.db_service._prepare_job_data(job, 'test_source')
            processed_jobs.append(processed)
        
        # Check all jobs were processed correctly
        self.assertEqual(len(processed_jobs), 100)
        
        for i, job in enumerate(processed_jobs):
            self.assertIn('profile_description', job)
            self.assertNotIn('profile', job)
            self.assertEqual(job['title'], f'Job {i}')
            self.assertEqual(job['source_site'], 'test_source')
    
    def test_edge_cases_handling(self):
        """Test handling of edge cases in field mapping."""
        edge_cases = [
            # Empty strings
            {
                'title': '',
                'company': '',
                'profile': '',
                'source_url': 'https://example.com/job/1',
                'extraction_method': 'gemini'
            },
            # None values
            {
                'title': 'Test Job',
                'company': 'Test Company',
                'profile': None,
                'source_url': 'https://example.com/job/2',
                'extraction_method': 'gemini'
            },
            # Very long strings
            {
                'title': 'A' * 1000,
                'company': 'B' * 500,
                'profile': 'C' * 2000,
                'source_url': 'https://example.com/job/3',
                'extraction_method': 'gemini'
            }
        ]
        
        for i, test_data in enumerate(edge_cases):
            result = self.db_service._prepare_job_data(test_data, f'test_source_{i}')
            
            # Basic structure should be maintained
            self.assertIn('title', result)
            self.assertIn('company', result)
            self.assertIn('source_site', result)
            self.assertIn('item_id', result)
            
            # profile should be mapped to profile_description
            if 'profile' in test_data:
                self.assertIn('profile_description', result)
                self.assertNotIn('profile', result)


# Async test runner
class AsyncTestRunner:
    """Helper class to run async tests."""
    
    @staticmethod
    def run_async_test(test_method):
        """Run an async test method."""
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            return loop.run_until_complete(test_method())
        finally:
            loop.close()


# Override test methods to handle async
def make_async_test(test_method):
    """Decorator to make async test methods work with unittest."""
    def wrapper(self):
        return AsyncTestRunner.run_async_test(lambda: test_method(self))
    return wrapper


# Apply async decorator to async test methods
TestDatabaseIntegration.test_upsert_job_with_mapping = make_async_test(
    TestDatabaseIntegration.test_upsert_job_with_mapping
)
TestDatabaseIntegration.test_upsert_jobs_batch_with_mapping = make_async_test(
    TestDatabaseIntegration.test_upsert_jobs_batch_with_mapping
)
TestDatabaseIntegration.test_error_handling_in_batch_upsert = make_async_test(
    TestDatabaseIntegration.test_error_handling_in_batch_upsert
)
TestDatabaseIntegration.test_concurrent_batch_operations = make_async_test(
    TestDatabaseIntegration.test_concurrent_batch_operations
)


if __name__ == '__main__':
    unittest.main()