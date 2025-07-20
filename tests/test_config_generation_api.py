"""
Test cases for the Config Generation API endpoint
Author: Integration Tester Agent
Date: 2025-01-20

This file contains comprehensive tests for the /api/settings/generate-config endpoint
including success cases, error handling, validation, and integration with zone distribution.
"""

import pytest
import json
from unittest.mock import patch, MagicMock, Mock
from flask import Flask
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from settings_api import register_settings_routes, SettingsAPI
from sport_config import TrainingConfig, SportConfig, UserProfile, TrainingPhilosophy


class TestConfigGenerationAPI:
    """Test cases for config generation API endpoint"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app with settings routes"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.secret_key = 'test-secret-key'
        register_settings_routes(app)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def mock_ai_provider(self):
        """Mock AI provider for testing"""
        provider = MagicMock()
        provider.is_available.return_value = True
        provider.generate.return_value = json.dumps({
            "version": "1.0.0",
            "user_profile": {
                "philosophy": "polarized",
                "volume_levels": {"low": 6, "medium": 8, "high": 12},
                "thresholds": {"ftp": 250, "lthr": 165},
                "preferences": {"zone_distribution": {"1": 80, "2": 10, "3": 10}}
            },
            "sports": [
                {
                    "name": "Cycling",
                    "activity_types": ["Ride", "VirtualRide"],
                    "primary_metric": {
                        "type": "power",
                        "unit": "watts",
                        "threshold_field": "ftp",
                        "decimal_places": 0
                    },
                    "zone_model": "percentage",
                    "zones": [
                        {
                            "name": "Recovery",
                            "lower": 0,
                            "upper": 55,
                            "description": "Easy recovery pace"
                        },
                        {
                            "name": "Endurance",
                            "lower": 55,
                            "upper": 75,
                            "description": "Aerobic base building"
                        },
                        {
                            "name": "Tempo",
                            "lower": 75,
                            "upper": 90,
                            "description": "Sustained effort"
                        }
                    ],
                    "equipment": [],
                    "workout_templates": [],
                    "notes": "Generated from preferences"
                }
            ]
        })
        return provider
    
    def test_generate_config_success(self, client, mock_ai_provider):
        """Test successful config generation from preferences"""
        with patch('ai_providers.OpenAIProvider') as mock_openai:
            with patch('ai_providers.ClaudeProvider') as mock_claude:
                with patch('config_generator.ConfigGenerator') as mock_generator_class:
                    # Set up mock providers
                    mock_claude.return_value = mock_ai_provider
                    mock_openai.return_value.is_available.return_value = False
                    
                    # Mock the generator
                    mock_generator = MagicMock()
                    mock_config = MagicMock()
                    mock_config.version = '1.0.0'
                    mock_config.user_profile.philosophy.value = 'polarized'
                    mock_config.user_profile.volume_levels = {"low": 6, "medium": 8, "high": 12}
                    mock_config.user_profile.thresholds = {"ftp": 250, "lthr": 165}
                    mock_config.user_profile.preferences = {"zone_distribution": {"1": 80, "2": 10, "3": 10}}
                    
                    mock_sport = MagicMock()
                    mock_sport.name = 'Cycling'
                    mock_sport.activity_types = ["Ride", "VirtualRide"]
                    mock_sport.primary_metric.type.value = 'power'
                    mock_sport.primary_metric.unit = 'watts'
                    mock_sport.primary_metric.threshold_field = 'ftp'
                    mock_sport.primary_metric.decimal_places = 0
                    mock_sport.secondary_metric = None
                    mock_sport.zone_model.value = 'percentage'
                    mock_sport.zones = []
                    mock_sport.equipment = []
                    mock_sport.workout_templates = []
                    mock_sport.notes = 'Generated from preferences'
                    mock_sport.zone_distribution = None
                    
                    mock_config.sports = [mock_sport]
                    mock_generator.generate_config.return_value = mock_config
                    mock_generator_class.return_value = mock_generator
                
                # Test request
                response = client.post('/api/settings/generate-config',
                    json={
                        'preferences': 'I am a cyclist who trains with power. My FTP is 250W.'
                    },
                    headers={'Content-Type': 'application/json'}
                )
                
                assert response.status_code == 200
                data = json.loads(response.data)
                
                assert data['success'] is True
                assert 'config' in data
                assert 'provider_used' in data
                
                config = data['config']
                assert config['version'] == '1.0.0'
                assert config['user_profile']['philosophy'] == 'polarized'
                assert len(config['sports']) == 1
                assert config['sports'][0]['name'] == 'Cycling'
    
    def test_generate_config_with_zone_distribution(self, client, mock_ai_provider):
        """Test config generation with custom zone distribution"""
        with patch('ai_providers.ClaudeProvider') as mock_claude:
            mock_claude.return_value = mock_ai_provider
            
            response = client.post('/api/settings/generate-config',
                json={
                    'preferences': 'I want to focus on endurance training',
                    'zone_distribution': {
                        '1': 85,
                        '2': 10,
                        '3': 5
                    }
                },
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            
            # Verify that zone distribution was passed to the generator
            mock_ai_provider.generate.assert_called_once()
            call_args = mock_ai_provider.generate.call_args[0][0]
            assert 'Zone Distribution Targets:' in call_args
            assert 'Zone 1: 85%' in call_args
            assert 'Zone 2: 10%' in call_args
            assert 'Zone 3: 5%' in call_args
    
    def test_generate_config_missing_preferences(self, client):
        """Test error when preferences are missing"""
        response = client.post('/api/settings/generate-config',
            json={},
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
        assert 'Missing preferences' in data['error']
    
    def test_generate_config_no_ai_provider(self, client):
        """Test error when no AI provider is available"""
        with patch('ai_providers.OpenAIProvider') as mock_openai:
            with patch('ai_providers.ClaudeProvider') as mock_claude:
                # Both providers unavailable
                mock_openai.return_value.is_available.return_value = False
                mock_claude.return_value.is_available.return_value = False
                
                response = client.post('/api/settings/generate-config',
                    json={'preferences': 'Test preferences'},
                    headers={'Content-Type': 'application/json'}
                )
                
                assert response.status_code == 503
                data = json.loads(response.data)
                assert data['success'] is False
                assert 'No AI provider available' in data['error']
    
    def test_generate_config_ai_provider_selection(self, client, mock_ai_provider):
        """Test AI provider selection based on environment settings"""
        mock_openai_provider = MagicMock()
        mock_openai_provider.is_available.return_value = True
        mock_openai_provider.generate.return_value = mock_ai_provider.generate.return_value
        
        with patch('ai_providers.OpenAIProvider') as mock_openai:
            with patch('ai_providers.ClaudeProvider') as mock_claude:
                mock_openai.return_value = mock_openai_provider
                mock_claude.return_value = mock_ai_provider
                
                # Test with AI_PROVIDER=openai
                with patch.dict('os.environ', {'AI_PROVIDER': 'openai'}):
                    response = client.post('/api/settings/generate-config',
                        json={'preferences': 'Test'},
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data['provider_used'] == 'MagicMock'  # OpenAI was selected
    
    def test_generate_config_invalid_json_response(self, client):
        """Test handling of invalid JSON from AI provider"""
        with patch('ai_providers.ClaudeProvider') as mock_claude:
            bad_provider = MagicMock()
            bad_provider.is_available.return_value = True
            bad_provider.generate.return_value = "Invalid JSON {{"
            mock_claude.return_value = bad_provider
            
            response = client.post('/api/settings/generate-config',
                json={'preferences': 'Test preferences'},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'Failed to generate configuration' in data['error']
    
    def test_generate_config_exception_handling(self, client):
        """Test exception handling in config generation"""
        with patch('ai_providers.ClaudeProvider') as mock_claude:
            bad_provider = MagicMock()
            bad_provider.is_available.return_value = True
            bad_provider.generate.side_effect = Exception("AI provider error")
            mock_claude.return_value = bad_provider
            
            response = client.post('/api/settings/generate-config',
                json={'preferences': 'Test preferences'},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert data['success'] is False
    
    def test_generate_config_complex_preferences(self, client, mock_ai_provider):
        """Test config generation with complex multi-sport preferences"""
        complex_preferences = """
        I am a triathlete who trains in cycling, running, and swimming.
        For cycling, I use power zones based on my FTP of 280W.
        For running, I prefer heart rate zones with LTHR of 170.
        I follow a polarized training approach with 80/10/10 distribution.
        I have a Peloton bike and train 4 times per week.
        """
        
        with patch('ai_providers.ClaudeProvider') as mock_claude:
            mock_claude.return_value = mock_ai_provider
            
            response = client.post('/api/settings/generate-config',
                json={'preferences': complex_preferences},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
    
    def test_generate_config_auto_provider_fallback(self, client, mock_ai_provider):
        """Test auto provider mode with fallback"""
        with patch('ai_providers.OpenAIProvider') as mock_openai:
            with patch('ai_providers.ClaudeProvider') as mock_claude:
                # Primary (Claude) unavailable, fallback to OpenAI
                mock_claude.return_value.is_available.return_value = False
                mock_openai.return_value = mock_ai_provider
                
                with patch.dict('os.environ', {
                    'AI_PROVIDER': 'auto',
                    'AI_PRIMARY_PROVIDER': 'claude',
                    'AI_FALLBACK_PROVIDER': 'openai'
                }):
                    response = client.post('/api/settings/generate-config',
                        json={'preferences': 'Test'},
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    assert response.status_code == 200
                    # Verify fallback was used
                    mock_openai.assert_called()


class TestZoneDistributionAPI:
    """Test cases for zone distribution endpoints"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app with settings routes"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.secret_key = 'test-secret-key'
        register_settings_routes(app)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def mock_sport_service(self):
        """Mock SportConfigService"""
        service = MagicMock()
        service.get_zone_distribution_target.return_value = {1: 80.0, 2: 10.0, 3: 10.0}
        service.get_training_philosophy.return_value = TrainingPhilosophy.POLARIZED
        
        # Mock sports
        sport1 = MagicMock()
        sport1.name = 'Cycling'
        sport1.zone_distribution = {1: 75.0, 2: 15.0, 3: 10.0}
        
        sport2 = MagicMock()
        sport2.name = 'Running'
        sport2.zone_distribution = {1: 85.0, 2: 10.0, 3: 5.0}
        
        service.get_all_sports.return_value = [sport1, sport2]
        service.update_user_zone_distribution.return_value = True
        service.update_sport_zone_distribution.return_value = True
        
        return service
    
    def test_get_zone_distribution(self, client, mock_sport_service):
        """Test getting zone distribution settings"""
        with patch('sport_config_service.SportConfigService') as mock_service_class:
            mock_service_class.return_value = mock_sport_service
            
            response = client.get('/api/settings/zone-distribution')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            
            assert data['success'] is True
            assert data['data']['philosophy'] == 'polarized'
            assert data['data']['user_targets'] == {1: 80.0, 2: 10.0, 3: 10.0}
            assert 'Cycling' in data['data']['sport_distributions']
            assert 'Running' in data['data']['sport_distributions']
    
    def test_update_user_zone_distribution(self, client, mock_sport_service):
        """Test updating user's global zone distribution"""
        with patch('sport_config_service.SportConfigService') as mock_service_class:
            mock_service_class.return_value = mock_sport_service
            
            response = client.put('/api/settings/zone-distribution/user',
                json={'zone_distribution': {'1': 85, '2': 10, '3': 5}},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            
            # Verify service was called with correct data
            mock_sport_service.update_user_zone_distribution.assert_called_once_with(
                {1: 85, 2: 10, 3: 5}
            )
    
    def test_update_sport_zone_distribution(self, client, mock_sport_service):
        """Test updating sport-specific zone distribution"""
        with patch('sport_config_service.SportConfigService') as mock_service_class:
            mock_service_class.return_value = mock_sport_service
            
            response = client.put('/api/settings/zone-distribution/sport/Cycling',
                json={'zone_distribution': {'1': 70, '2': 20, '3': 10}},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            
            # Verify service was called
            mock_sport_service.update_sport_zone_distribution.assert_called_once_with(
                'Cycling', {1: 70, 2: 20, 3: 10}
            )
    
    def test_update_zone_distribution_invalid_sum(self, client, mock_sport_service):
        """Test error when zone distribution doesn't sum to 100%"""
        mock_sport_service.update_user_zone_distribution.return_value = False
        
        with patch('sport_config_service.SportConfigService') as mock_service_class:
            mock_service_class.return_value = mock_sport_service
            
            response = client.put('/api/settings/zone-distribution/user',
                json={'zone_distribution': {'1': 80, '2': 15, '3': 10}},  # Sum = 105
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'must sum to 100%' in data['error']


class TestConfigGenerationIntegration:
    """Integration tests for config generation with UI flow"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.secret_key = 'test-secret-key'
        register_settings_routes(app)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    def test_full_config_generation_flow(self, client):
        """Test complete flow from preferences to config display"""
        with patch('ai_providers.ClaudeProvider') as mock_claude:
            # Mock provider that generates valid config
            provider = MagicMock()
            provider.is_available.return_value = True
            provider.generate.return_value = json.dumps({
                "version": "1.0.0",
                "user_profile": {
                    "philosophy": "polarized",
                    "volume_levels": {"low": 6, "medium": 8, "high": 12},
                    "thresholds": {"ftp": 250, "lthr": 165},
                    "preferences": {"zone_distribution": {"1": 80, "2": 10, "3": 10}}
                },
                "sports": [{
                    "name": "Cycling",
                    "activity_types": ["Ride"],
                    "primary_metric": {
                        "type": "power",
                        "unit": "watts",
                        "threshold_field": "ftp",
                        "decimal_places": 0
                    },
                    "zone_model": "percentage",
                    "zones": [
                        {"name": "Z1", "lower": 0, "upper": 55, "description": "Recovery"},
                        {"name": "Z2", "lower": 55, "upper": 75, "description": "Endurance"},
                        {"name": "Z3", "lower": 75, "upper": 90, "description": "Tempo"}
                    ],
                    "equipment": [],
                    "workout_templates": [],
                    "notes": "Generated"
                }]
            })
            mock_claude.return_value = provider
            
            # Step 1: User enters preferences
            preferences = "I am a cyclist with FTP 250W, following polarized training"
            
            # Step 2: Generate config
            response = client.post('/api/settings/generate-config',
                json={'preferences': preferences},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 200
            config_data = json.loads(response.data)
            
            # Step 3: Verify config structure for UI display
            config = config_data['config']
            
            # Check all required fields for UI
            assert 'version' in config
            assert 'user_profile' in config
            assert 'sports' in config
            
            # Check user profile fields
            profile = config['user_profile']
            assert profile['philosophy'] == 'polarized'
            assert 'volume_levels' in profile
            assert 'thresholds' in profile
            
            # Check sport config
            sport = config['sports'][0]
            assert sport['name'] == 'Cycling'
            assert 'zones' in sport
            assert len(sport['zones']) == 3
            
            # Check zone structure
            for zone in sport['zones']:
                assert 'name' in zone
                assert 'lower' in zone
                assert 'upper' in zone
                assert 'description' in zone


class TestErrorHandlingAndValidation:
    """Test error handling and validation scenarios"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.secret_key = 'test-secret-key'
        register_settings_routes(app)
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    def test_malformed_json_request(self, client):
        """Test handling of malformed JSON in request"""
        response = client.post('/api/settings/generate-config',
            data='{"invalid json',
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 400
    
    def test_empty_preferences(self, client):
        """Test handling of empty preferences string"""
        response = client.post('/api/settings/generate-config',
            json={'preferences': ''},
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert data['success'] is False
    
    def test_very_long_preferences(self, client):
        """Test handling of very long preference text"""
        # Create a very long preference string (10KB)
        long_preferences = "I like cycling. " * 1000
        
        with patch('ai_providers.ClaudeProvider') as mock_claude:
            provider = MagicMock()
            provider.is_available.return_value = True
            provider.generate.return_value = '{"version": "1.0.0", "user_profile": {}, "sports": []}'
            mock_claude.return_value = provider
            
            response = client.post('/api/settings/generate-config',
                json={'preferences': long_preferences},
                headers={'Content-Type': 'application/json'}
            )
            
            # Should handle gracefully
            assert response.status_code in [200, 400, 413]  # Success, bad request, or payload too large


if __name__ == "__main__":
    pytest.main([__file__, "-v"])