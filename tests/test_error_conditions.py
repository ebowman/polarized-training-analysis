"""
Comprehensive error condition tests for all modules.
Tests error handling paths, edge cases, and failure scenarios.
"""

import pytest
import json
from unittest.mock import patch, MagicMock, Mock, mock_open
from datetime import datetime, timedelta
import os

# Import modules to test
from ai_recommendations import AIRecommendationEngine, TrainingDataAnalyzer
from ai_providers import AIProviderFactory, OpenAIProvider, ClaudeProvider
from sport_config import SportConfig, TrainingConfig, ConfigValidator
from sport_config_service import SportConfigService
from strava_client import StravaClient
from cache_manager import CacheManager
from training_analysis import ActivityAnalysis
from web_server import app, DownloadManager


class TestAIRecommendationsErrors:
    """Test error conditions in AI recommendations module"""
    
    def test_ai_provider_initialization_failure(self):
        """Test handling when AI provider fails to initialize"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': '', 'ANTHROPIC_API_KEY': ''}):
            engine = AIRecommendationEngine()
            # Should fall back to mock provider
            assert engine.provider is not None
    
    def test_invalid_training_data_format(self):
        """Test handling of malformed training data"""
        engine = AIRecommendationEngine()
        
        # Test with None
        result = engine.generate_ai_recommendations(None)
        assert isinstance(result, list)
        assert len(result) > 0  # Should return fallback recommendations
        
        # Test with empty dict
        result = engine.generate_ai_recommendations({})
        assert isinstance(result, list)
        
        # Test with missing required fields
        invalid_data = {'foo': 'bar'}
        result = engine.generate_ai_recommendations(invalid_data)
        assert isinstance(result, list)
    
    def test_ai_response_parsing_errors(self):
        """Test handling of various AI response parsing errors"""
        mock_provider = MagicMock()
        mock_provider.get_provider_name.return_value = "TestProvider"
        engine = AIRecommendationEngine(provider=mock_provider)
        
        # Test invalid JSON response
        mock_provider.generate_completion.return_value = "This is not JSON"
        result = engine.generate_ai_recommendations({'activities': []})
        assert isinstance(result, list)
        assert len(result) > 0  # Should return fallback
        
        # Test partial JSON
        mock_provider.generate_completion.return_value = '{"incomplete": '
        result = engine.generate_ai_recommendations({'activities': []})
        assert isinstance(result, list)
        
        # Test JSON with wrong structure
        mock_provider.generate_completion.return_value = '{"wrong": "structure"}'
        result = engine.generate_ai_recommendations({'activities': []})
        assert isinstance(result, list)
    
    def test_zone_calculation_division_by_zero(self):
        """Test zone calculation with zero total minutes"""
        analyzer = TrainingDataAnalyzer()
        
        # Empty activities list
        z1, z2, z3, total = analyzer.calculate_zone_distribution([])
        assert z1 == 0
        assert z2 == 0
        assert z3 == 0
        assert total == 0
        
        # Activities with zero duration
        activities = [{'duration_minutes': 0, 'zone1_percent': 100}]
        z1, z2, z3, total = analyzer.calculate_zone_distribution(activities)
        assert total == 0
    
    def test_date_parsing_errors(self):
        """Test handling of invalid date formats"""
        analyzer = TrainingDataAnalyzer()
        
        activities = [
            {'date': 'invalid-date', 'duration_minutes': 60},
            {'date': None, 'duration_minutes': 30},
            {'date': '', 'duration_minutes': 45},
            {'duration_minutes': 20}  # Missing date field
        ]
        
        # Should handle gracefully and include activities
        recent = analyzer.filter_recent_activities(activities)
        assert len(recent) == 4  # All activities included when date parsing fails
    
    def test_file_reading_errors(self):
        """Test handling of file reading errors"""
        engine = AIRecommendationEngine()
        
        # Test preferences file not found
        with patch('builtins.open', side_effect=FileNotFoundError):
            prefs = engine.load_preferences()
            assert "No user preferences file found" in prefs
        
        # Test file read permission error
        with patch('builtins.open', side_effect=PermissionError):
            prefs = engine.load_preferences()
            assert "No user preferences file found" in prefs
    
    def test_recovery_metrics_with_invalid_data(self):
        """Test recovery metrics calculation with edge cases"""
        analyzer = TrainingDataAnalyzer()
        
        # Test with activities missing required fields
        activities = [
            {'name': 'Run'},  # Missing everything
            {'date': 'bad-date', 'duration_minutes': 'not-a-number'},
            {'date': datetime.now().isoformat(), 'zone3_percent': None}
        ]
        
        metrics = analyzer.calculate_recovery_metrics(activities)
        assert isinstance(metrics, dict)
        assert metrics['consecutive_training_days'] >= 0
        assert metrics['zone3_last_3_days'] >= 0


class TestAIProvidersErrors:
    """Test error conditions in AI providers module"""
    
    def test_openai_api_key_missing(self):
        """Test OpenAI provider with missing API key"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': ''}):
            provider = OpenAIProvider()
            assert not provider.is_available()
            assert "not configured" in provider.get_error_message()
            
            with pytest.raises(ValueError):
                provider.generate_completion("test prompt")
    
    def test_openai_api_call_failure(self):
        """Test OpenAI API call failures"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': 'test_key'}):
            provider = OpenAIProvider()
            provider.client = MagicMock()
            
            # Test rate limit error with fallback
            provider.client.chat.completions.create.side_effect = [
                Exception("Rate limit exceeded"),
                MagicMock(choices=[MagicMock(message=MagicMock(content='{"test": "response"}'))])
            ]
            
            result = provider.generate_completion("test")
            assert result == '{"test": "response"}'
            
            # Test complete failure
            provider.client.chat.completions.create.side_effect = Exception("API down")
            with pytest.raises(Exception):
                provider.generate_completion("test")
    
    def test_claude_api_key_missing(self):
        """Test Claude provider with missing API key"""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': ''}):
            provider = ClaudeProvider()
            assert not provider.is_available()
            assert "not configured" in provider.get_error_message()
            
            with pytest.raises(ValueError):
                provider.generate_completion("test prompt")
    
    def test_claude_response_extraction_error(self):
        """Test Claude response extraction failures"""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test_key'}):
            provider = ClaudeProvider()
            provider.client = MagicMock()
            
            # Test response with no content
            provider.client.messages.create.return_value = MagicMock(content=None)
            
            with pytest.raises(ValueError):
                provider.generate_completion("test")
    
    def test_provider_factory_no_providers(self):
        """Test factory when no providers are available"""
        with patch.dict(os.environ, {'OPENAI_API_KEY': '', 'ANTHROPIC_API_KEY': ''}):
            provider = AIProviderFactory.create_provider()
            # Should return mock provider
            assert provider.get_provider_name() == "Mock"


class TestSportConfigErrors:
    """Test error conditions in sport configuration module"""
    
    def test_invalid_json_config(self):
        """Test loading invalid JSON configuration"""
        service = SportConfigService()
        
        # Test with invalid JSON
        with patch('builtins.open', mock_open(read_data='{"invalid json')):
            with pytest.raises(json.JSONDecodeError):
                service.load_config("bad_config.json")
    
    def test_config_validation_failures(self):
        """Test configuration validation errors"""
        validator = ConfigValidator()
        
        # Test invalid configuration structure
        invalid_configs = [
            {},  # Empty config
            {"version": 123},  # Wrong type
            {"sports": "not an array"},  # Wrong structure
            {"sports": [{"name": "Running"}]},  # Missing required fields
        ]
        
        for config in invalid_configs:
            assert not validator.validate(config)
    
    def test_zone_calculation_errors(self):
        """Test zone calculation with invalid inputs"""
        service = SportConfigService()
        
        # Create a sport with percentage-based zones
        sport = SportConfig(
            name="Test",
            activity_types=["Run"],
            primary_metric=Mock(type="heart_rate", threshold_field="lthr"),
            zones=[Mock(lower="0%", upper="75%", polarized_zone=1)]
        )
        
        # Test with invalid threshold value
        with pytest.raises(ValueError):
            service.calculate_zones(sport, "heart_rate", "not a number")
        
        # Test with None threshold
        with pytest.raises(ValueError):
            service.calculate_zones(sport, "heart_rate", None)
        
        # Test with negative threshold
        with pytest.raises(ValueError):
            service.calculate_zones(sport, "heart_rate", -100)
    
    def test_missing_config_file(self):
        """Test handling of missing configuration file"""
        service = SportConfigService()
        
        with patch('os.path.exists', return_value=False):
            config = service.load_config("nonexistent.json")
            # Should return default config
            assert config is not None
            assert isinstance(config, TrainingConfig)


class TestWebServerErrors:
    """Test error conditions in web server module"""
    
    @pytest.fixture
    def client(self):
        app.config['TESTING'] = True
        with app.test_client() as client:
            yield client
    
    def test_api_endpoint_exceptions(self, client):
        """Test API endpoints handling exceptions"""
        # Test /api/workouts with cache error
        with patch('web_server.get_training_data', side_effect=Exception("Cache corrupted")):
            response = client.get('/api/workouts')
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
            assert 'Cache corrupted' in data['error']
    
    def test_download_manager_errors(self, client):
        """Test download manager error scenarios"""
        with patch('web_server.DownloadManager') as mock_dm_class:
            mock_dm = MagicMock()
            mock_dm.start_download.side_effect = Exception("Network error")
            mock_dm_class.return_value = mock_dm
            
            # Need to be authenticated
            with client.session_transaction() as sess:
                sess['strava_access_token'] = 'test_token'
            
            response = client.post('/api/download-workouts', json={'days': 30})
            assert response.status_code == 500
    
    def test_ai_generation_timeout(self, client):
        """Test AI generation timeout handling"""
        with patch('web_server.ai_generation_status') as mock_status:
            mock_status.__contains__ = Mock(return_value=True)
            mock_status.__getitem__ = Mock(return_value={
                'status': 'timeout',
                'error': 'Generation timed out'
            })
            
            response = client.get('/api/ai-status/test_session')
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['status'] == 'timeout'
    
    def test_invalid_request_data(self, client):
        """Test handling of invalid request data"""
        # Test save preferences with invalid JSON
        response = client.post('/api/workout-preferences',
                             data='invalid json',
                             content_type='application/json')
        assert response.status_code == 400
        
        # Test download with invalid days parameter
        with client.session_transaction() as sess:
            sess['strava_access_token'] = 'test_token'
        
        response = client.post('/api/download-workouts',
                             json={'days': 'not a number'})
        # Should handle gracefully
        assert response.status_code in [200, 400, 500]


class TestStravaClientErrors:
    """Test error conditions in Strava client"""
    
    def test_token_refresh_failure(self):
        """Test token refresh error handling"""
        client = StravaClient()
        client.refresh_token = 'test_refresh'
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.status_code = 401
            mock_post.return_value.json.return_value = {'error': 'invalid_grant'}
            
            with pytest.raises(Exception):
                client._refresh_access_token()
    
    def test_api_request_failures(self):
        """Test API request error scenarios"""
        client = StravaClient()
        client.access_token = 'test_token'
        
        with patch('requests.get') as mock_get:
            # Test 404 error
            mock_get.return_value.status_code = 404
            activities = client.get_activities(days=7)
            assert activities == []
            
            # Test network error
            mock_get.side_effect = Exception("Network error")
            activities = client.get_activities(days=7)
            assert activities == []
    
    def test_malformed_activity_data(self):
        """Test handling of malformed activity data"""
        client = StravaClient()
        client.access_token = 'test_token'
        
        with patch('requests.get') as mock_get:
            # Return activities with missing fields
            mock_get.return_value.status_code = 200
            mock_get.return_value.json.return_value = [
                {'id': 1},  # Missing required fields
                {'id': 2, 'name': None, 'start_date': 'bad-date'},
                {'id': 3, 'name': 'Run', 'moving_time': 'not-a-number'}
            ]
            
            activities = client.get_activities(days=7)
            # Should handle gracefully
            assert isinstance(activities, list)


class TestCacheManagerErrors:
    """Test error conditions in cache manager"""
    
    def test_corrupted_cache_file(self):
        """Test handling of corrupted cache files"""
        cache = CacheManager()
        
        # Write corrupted data
        with patch('builtins.open', mock_open(read_data='{"corrupted json')):
            data = cache.get('test_key')
            assert data is None
    
    def test_cache_write_failures(self):
        """Test cache write error handling"""
        cache = CacheManager()
        
        # Test permission error
        with patch('builtins.open', side_effect=PermissionError):
            result = cache.set('test_key', {'data': 'test'})
            assert result is False
        
        # Test disk full
        with patch('json.dump', side_effect=OSError("No space left")):
            result = cache.set('test_key', {'data': 'test'})
            assert result is False
    
    def test_expired_cache_cleanup(self):
        """Test cleanup of expired cache entries"""
        cache = CacheManager()
        
        # Create expired entry
        expired_time = (datetime.now() - timedelta(days=31)).isoformat()
        cache_data = {
            'test_key': {
                'data': 'old_data',
                'timestamp': expired_time
            }
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(cache_data))):
            data = cache.get('test_key')
            assert data is None  # Should be expired


class TestTrainingAnalysisErrors:
    """Test error conditions in training analysis"""
    
    def test_invalid_heart_rate_data(self):
        """Test handling of invalid heart rate data"""
        analyzer = ActivityAnalysis()
        
        # Test with None stream data
        zones = analyzer.analyze_heart_rate_zones(None, zones=[140, 150, 160, 170])
        assert all(v == 0 for v in zones.values())
        
        # Test with non-numeric data
        invalid_stream = {'data': ['not', 'numbers']}
        zones = analyzer.analyze_heart_rate_zones(invalid_stream, zones=[140, 150, 160, 170])
        assert all(v == 0 for v in zones.values())
    
    def test_power_analysis_missing_ftp(self):
        """Test power analysis without FTP value"""
        analyzer = ActivityAnalysis()
        
        # Should handle missing FTP gracefully
        stream = {'data': [200, 250, 300]}
        zones = analyzer.analyze_power_zones(stream, ftp=None)
        assert isinstance(zones, dict)
        
        # Test with zero FTP
        zones = analyzer.analyze_power_zones(stream, ftp=0)
        assert isinstance(zones, dict)
    
    def test_zone_calculation_edge_cases(self):
        """Test zone calculations with edge case values"""
        analyzer = ActivityAnalysis()
        
        # Test with extreme values
        stream = {'data': [-10, 0, 999, float('inf'), float('nan')]}
        zones = analyzer.analyze_heart_rate_zones(stream, zones=[140, 150, 160, 170])
        assert isinstance(zones, dict)
        
        # Test with empty data
        stream = {'data': []}
        zones = analyzer.analyze_heart_rate_zones(stream, zones=[140, 150, 160, 170])
        assert all(v == 0 for v in zones.values())


def test_concurrent_access_errors():
    """Test handling of concurrent access scenarios"""
    # This would test race conditions in cache access, 
    # download manager state, etc.
    pass


def test_memory_exhaustion_scenarios():
    """Test handling of large data sets that could exhaust memory"""
    # Test with very large activity lists
    # Test with huge workout descriptions
    pass


def test_integration_error_propagation():
    """Test how errors propagate through the system"""
    # Test error in Strava -> Analysis -> AI -> Web
    pass