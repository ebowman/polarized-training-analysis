"""Tests for CacheManager functionality"""
import pytest
import json
import os
import tempfile
import shutil
from unittest.mock import patch, MagicMock

from cache_manager import CacheManager


class TestCacheManager:
    """Test cases for CacheManager"""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary cache directory"""
        temp_dir = tempfile.mkdtemp()
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def cache_manager(self, temp_cache_dir):
        """Create a CacheManager with temp directory"""
        with patch('cache_manager.CacheManager.__init__') as mock_init:
            mock_init.return_value = None
            manager = CacheManager()
            manager.cache_dir = temp_cache_dir
            manager.analysis_file = os.path.join(temp_cache_dir, 'training_analysis_report.json')
            return manager
    
    def test_load_all_cached_activities_with_streams(self, cache_manager, temp_cache_dir):
        """Test that load_all_cached_activities loads associated streams"""
        # Create test activity file
        activity_data = {
            'id': 12345,
            'name': 'Test Ride',
            'start_date': '2025-07-12T10:00:00Z',
            'sport_type': 'Ride'
        }
        activity_file = os.path.join(temp_cache_dir, '_activities_12345_.json')
        with open(activity_file, 'w') as f:
            json.dump(activity_data, f)
        
        # Create test streams file
        streams_data = {
            'watts': {'data': [100, 150, 200, 250, 300]},
            'time': {'data': [0, 1, 2, 3, 4]}
        }
        streams_file = os.path.join(temp_cache_dir, '_activities_12345_streams_test.json')
        with open(streams_file, 'w') as f:
            json.dump(streams_data, f)
        
        # Load activities
        activities = cache_manager.load_all_cached_activities()
        
        # Verify activity loaded with streams
        assert len(activities) == 1
        assert activities[0]['id'] == 12345
        assert 'streams' in activities[0]
        assert activities[0]['streams']['watts']['data'] == [100, 150, 200, 250, 300]
    
    def test_load_all_cached_activities_without_streams(self, cache_manager, temp_cache_dir):
        """Test loading activities when no streams file exists"""
        # Create test activity file without streams
        activity_data = {
            'id': 67890,
            'name': 'Test Run',
            'start_date': '2025-07-11T08:00:00Z',
            'sport_type': 'Run'
        }
        activity_file = os.path.join(temp_cache_dir, '_activities_67890_.json')
        with open(activity_file, 'w') as f:
            json.dump(activity_data, f)
        
        # Load activities
        activities = cache_manager.load_all_cached_activities()
        
        # Verify activity loaded without streams
        assert len(activities) == 1
        assert activities[0]['id'] == 67890
        assert 'streams' not in activities[0]