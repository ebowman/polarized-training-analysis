"""
Test cases for Settings Page UI Integration
Author: Integration Tester Agent
Date: 2025-01-20

This file contains integration tests for the Settings page UI components
including zone distribution editor, config generation flow, and display.
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from flask import Flask, session
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from web_server import app as flask_app
from settings_api import SettingsAPI


class TestSettingsUIIntegration:
    """Integration tests for Settings page UI functionality"""
    
    @pytest.fixture
    def app(self):
        """Configure Flask app for testing"""
        flask_app.config['TESTING'] = True
        flask_app.config['SECRET_KEY'] = 'test-secret-key'
        return flask_app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def authenticated_client(self, client):
        """Create authenticated test client"""
        with client.session_transaction() as sess:
            sess['strava_access_token'] = 'test-token'
        return client
    
    def test_settings_page_loads(self, client):
        """Test that settings page loads successfully"""
        response = client.get('/settings')
        assert response.status_code == 200
        assert b'Settings' in response.data or b'settings' in response.data
    
    def test_zone_distribution_editor_data(self, authenticated_client):
        """Test zone distribution editor gets correct data"""
        with patch('settings_api.SportConfigService') as mock_service:
            # Mock the service
            service_instance = MagicMock()
            service_instance.get_zone_distribution_target.return_value = {1: 80.0, 2: 10.0, 3: 10.0}
            service_instance.get_training_philosophy.return_value = MagicMock(value='polarized')
            service_instance.get_all_sports.return_value = []
            mock_service.return_value = service_instance
            
            # Get zone distribution data
            response = authenticated_client.get('/api/settings/zone-distribution')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert data['data']['philosophy'] == 'polarized'
            assert data['data']['user_targets'] == {1: 80.0, 2: 10.0, 3: 10.0}
    
    def test_zone_distribution_update_flow(self, authenticated_client):
        """Test updating zone distribution through UI"""
        with patch('settings_api.SportConfigService') as mock_service:
            service_instance = MagicMock()
            service_instance.update_user_zone_distribution.return_value = True
            mock_service.return_value = service_instance
            
            # Update zone distribution
            new_distribution = {'1': 85, '2': 10, '3': 5}
            response = authenticated_client.put('/api/settings/zone-distribution/user',
                json={'zone_distribution': new_distribution},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            
            # Verify the service was called correctly
            service_instance.update_user_zone_distribution.assert_called_once()
            called_args = service_instance.update_user_zone_distribution.call_args[0][0]
            assert called_args == {1: 85, 2: 10, 3: 5}
    
    def test_config_generation_ui_flow(self, authenticated_client):
        """Test the complete UI flow for config generation"""
        with patch('settings_api.ClaudeProvider') as mock_claude:
            # Mock AI provider
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
                    "primary_metric": {"type": "power", "unit": "watts", "threshold_field": "ftp", "decimal_places": 0},
                    "zone_model": "percentage",
                    "zones": [
                        {"name": "Recovery", "lower": 0, "upper": 55, "description": "Easy recovery"},
                        {"name": "Endurance", "lower": 55, "upper": 75, "description": "Base building"},
                        {"name": "Tempo", "lower": 75, "upper": 90, "description": "Sustained effort"}
                    ],
                    "equipment": [],
                    "workout_templates": [],
                    "notes": ""
                }]
            })
            mock_claude.return_value = provider
            
            # Step 1: User enters preferences in UI
            preferences_data = {
                'preferences': 'I am a cyclist with FTP 250W, I train 5 days a week',
                'zone_distribution': {'1': 80, '2': 10, '3': 10}
            }
            
            # Step 2: Generate config
            response = authenticated_client.post('/api/settings/generate-config',
                json=preferences_data,
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            
            # Step 3: Verify config is suitable for UI display
            config = data['config']
            assert config['version'] == '1.0.0'
            assert config['user_profile']['philosophy'] == 'polarized'
            assert len(config['sports']) == 1
            
            sport = config['sports'][0]
            assert sport['name'] == 'Cycling'
            assert len(sport['zones']) == 3
            
            # Verify zone data for chart display
            for zone in sport['zones']:
                assert isinstance(zone['lower'], (int, float))
                assert isinstance(zone['upper'], (int, float))
                assert zone['lower'] < zone['upper']
    
    def test_env_settings_update_ui(self, authenticated_client):
        """Test updating environment settings through UI"""
        with patch('settings_api.set_key') as mock_set_key:
            with patch('settings_api.load_dotenv'):
                # Update FTP value
                response = authenticated_client.put('/api/settings/env/FTP',
                    json={'value': '275'},
                    headers={'Content-Type': 'application/json'}
                )
                
                assert response.status_code == 200
                data = json.loads(response.data)
                assert data['success'] is True
                
                # Verify set_key was called
                mock_set_key.assert_called_once()
                args = mock_set_key.call_args[0]
                assert args[1] == 'FTP'
                assert args[2] == '275'
    
    def test_prompt_template_management_ui(self, authenticated_client):
        """Test prompt template CRUD operations through UI"""
        # Create a new template
        template_data = {
            'name': 'Performance Template',
            'description': 'Template focused on performance',
            'prompt': 'Generate a config for high-performance training',
            'variables': {}
        }
        
        with patch('settings_api.PROMPTS_DIR', create=True) as mock_prompts_dir:
            mock_prompts_dir.glob.return_value = []
            
            # Mock file operations
            with patch('builtins.open', create=True) as mock_open:
                with patch('pathlib.Path.exists', return_value=False):
                    response = authenticated_client.post('/api/settings/prompts',
                        json=template_data,
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    assert response.status_code == 201
                    data = json.loads(response.data)
                    assert data['success'] is True
                    assert 'template_id' in data


class TestZoneDistributionEditor:
    """Test cases specifically for the zone distribution editor component"""
    
    @pytest.fixture
    def app(self):
        """Configure Flask app for testing"""
        flask_app.config['TESTING'] = True
        flask_app.config['SECRET_KEY'] = 'test-secret-key'
        return flask_app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    def test_zone_slider_constraints(self, client):
        """Test that zone sliders enforce proper constraints"""
        with patch('settings_api.SportConfigService') as mock_service:
            service_instance = MagicMock()
            service_instance.update_user_zone_distribution.return_value = False  # Invalid sum
            mock_service.return_value = service_instance
            
            # Try to update with invalid distribution (sum != 100)
            invalid_distribution = {'1': 60, '2': 30, '3': 30}  # Sum = 120
            response = client.put('/api/settings/zone-distribution/user',
                json={'zone_distribution': invalid_distribution},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert data['success'] is False
            assert 'must sum to 100%' in data['error']
    
    def test_philosophy_presets(self, client):
        """Test applying training philosophy presets"""
        test_cases = [
            ('polarized', {1: 80, 2: 10, 3: 10}),
            ('pyramidal', {1: 70, 2: 20, 3: 10}),
            ('threshold', {1: 50, 2: 35, 3: 15})
        ]
        
        with patch('settings_api.SportConfigService') as mock_service:
            service_instance = MagicMock()
            service_instance.update_user_zone_distribution.return_value = True
            mock_service.return_value = service_instance
            
            for philosophy, expected_distribution in test_cases:
                # Simulate applying preset
                response = client.put('/api/settings/zone-distribution/user',
                    json={'zone_distribution': expected_distribution},
                    headers={'Content-Type': 'application/json'}
                )
                
                assert response.status_code == 200
                
                # Verify correct distribution was set
                called_dist = service_instance.update_user_zone_distribution.call_args[0][0]
                assert called_dist == {int(k): v for k, v in expected_distribution.items()}
    
    def test_sport_specific_distribution(self, client):
        """Test setting sport-specific zone distributions"""
        with patch('settings_api.SportConfigService') as mock_service:
            service_instance = MagicMock()
            service_instance.update_sport_zone_distribution.return_value = True
            mock_service.return_value = service_instance
            
            # Update cycling-specific distribution
            cycling_dist = {'1': 75, '2': 15, '3': 10}
            response = client.put('/api/settings/zone-distribution/sport/Cycling',
                json={'zone_distribution': cycling_dist},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['success'] is True
            assert 'Cycling' in data['message']


class TestConfigDisplayIntegration:
    """Test cases for config display after generation"""
    
    @pytest.fixture
    def generated_config(self):
        """Sample generated config for testing"""
        return {
            'version': '1.0.0',
            'user_profile': {
                'philosophy': 'polarized',
                'volume_levels': {'low': 6, 'medium': 8, 'high': 12},
                'thresholds': {'ftp': 250, 'lthr': 165},
                'preferences': {'zone_distribution': {'1': 80, '2': 10, '3': 10}}
            },
            'sports': [{
                'name': 'Cycling',
                'activity_types': ['Ride', 'VirtualRide'],
                'primary_metric': {
                    'type': 'power',
                    'unit': 'watts',
                    'threshold_field': 'ftp',
                    'decimal_places': 0
                },
                'zone_model': 'percentage',
                'zones': [
                    {'name': 'Recovery', 'lower': 0, 'upper': 55, 'description': 'Recovery pace', 
                     'primary_range': '0-138W', 'secondary_range': None},
                    {'name': 'Endurance', 'lower': 55, 'upper': 75, 'description': 'Base building',
                     'primary_range': '138-188W', 'secondary_range': None},
                    {'name': 'Tempo', 'lower': 75, 'upper': 90, 'description': 'Sustained effort',
                     'primary_range': '188-225W', 'secondary_range': None}
                ],
                'equipment': [{'name': 'Peloton Bike', 'notes': 'Indoor training'}],
                'workout_templates': [{
                    'name': 'Endurance Ride',
                    'description': '60-90 minutes in Zone 2',
                    'structure': 'Steady Zone 2',
                    'target_zones': [2],
                    'duration_minutes': 75,
                    'frequency_per_week': 3
                }],
                'notes': 'Focus on base building',
                'zone_distribution': {1: 20, 2: 60, 3: 20}
            }]
        }
    
    def test_config_display_structure(self, generated_config):
        """Test that generated config has all required fields for display"""
        # User profile section
        assert 'user_profile' in generated_config
        profile = generated_config['user_profile']
        assert profile['philosophy'] == 'polarized'
        assert 'volume_levels' in profile
        assert 'thresholds' in profile
        
        # Sports section
        assert 'sports' in generated_config
        assert len(generated_config['sports']) > 0
        
        sport = generated_config['sports'][0]
        assert sport['name'] == 'Cycling'
        assert 'zones' in sport
        assert 'primary_metric' in sport
        
        # Zone details for chart display
        for zone in sport['zones']:
            assert 'name' in zone
            assert 'lower' in zone
            assert 'upper' in zone
            assert 'description' in zone
            assert 'primary_range' in zone
    
    def test_zone_calculation_display(self, generated_config):
        """Test zone calculations are correct for display"""
        sport = generated_config['sports'][0]
        ftp = generated_config['user_profile']['thresholds']['ftp']
        
        # Verify zone calculations
        for zone in sport['zones']:
            if zone['name'] == 'Recovery':
                assert zone['upper'] == 55  # 55% of FTP
                assert zone['primary_range'] == '0-138W'  # 0-55% of 250W
            elif zone['name'] == 'Endurance':
                assert zone['lower'] == 55
                assert zone['upper'] == 75
                assert zone['primary_range'] == '138-188W'  # 55-75% of 250W
    
    def test_workout_template_display(self, generated_config):
        """Test workout templates are properly structured for display"""
        sport = generated_config['sports'][0]
        assert 'workout_templates' in sport
        
        if sport['workout_templates']:
            template = sport['workout_templates'][0]
            assert 'name' in template
            assert 'description' in template
            assert 'duration_minutes' in template
            assert 'frequency_per_week' in template
            assert 'target_zones' in template


class TestErrorHandlingUI:
    """Test error handling in the UI"""
    
    @pytest.fixture
    def app(self):
        """Configure Flask app for testing"""
        flask_app.config['TESTING'] = True
        flask_app.config['SECRET_KEY'] = 'test-secret-key'
        return flask_app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    def test_no_ai_provider_error_display(self, client):
        """Test error display when no AI provider is available"""
        with patch('settings_api.OpenAIProvider') as mock_openai:
            with patch('settings_api.ClaudeProvider') as mock_claude:
                # Both providers unavailable
                mock_openai.return_value.is_available.return_value = False
                mock_claude.return_value.is_available.return_value = False
                
                response = client.post('/api/settings/generate-config',
                    json={'preferences': 'Test'},
                    headers={'Content-Type': 'application/json'}
                )
                
                assert response.status_code == 503
                data = json.loads(response.data)
                assert 'No AI provider available' in data['error']
                assert 'configure API keys' in data['error']
    
    def test_invalid_zone_sum_error(self, client):
        """Test error display for invalid zone distribution sum"""
        with patch('settings_api.SportConfigService') as mock_service:
            service_instance = MagicMock()
            service_instance.update_user_zone_distribution.return_value = False
            mock_service.return_value = service_instance
            
            response = client.put('/api/settings/zone-distribution/user',
                json={'zone_distribution': {'1': 90, '2': 20, '3': 10}},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 400
            data = json.loads(response.data)
            assert 'must sum to 100%' in data['error']
    
    def test_network_timeout_handling(self, client):
        """Test handling of network timeouts during config generation"""
        with patch('settings_api.ClaudeProvider') as mock_claude:
            provider = MagicMock()
            provider.is_available.return_value = True
            provider.generate.side_effect = TimeoutError("Request timed out")
            mock_claude.return_value = provider
            
            response = client.post('/api/settings/generate-config',
                json={'preferences': 'Test'},
                headers={'Content-Type': 'application/json'}
            )
            
            assert response.status_code == 500
            data = json.loads(response.data)
            assert data['success'] is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])