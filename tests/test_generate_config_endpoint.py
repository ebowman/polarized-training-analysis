"""
Simple test for the generate-config endpoint
Author: Integration Tester Agent
Date: 2025-01-20

This file tests the basic functionality of the /api/settings/generate-config endpoint
"""

import pytest
import json
from unittest.mock import patch, MagicMock
from flask import Flask
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from settings_api import register_settings_routes


class TestGenerateConfigEndpoint:
    """Basic tests for generate-config endpoint"""
    
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
    
    def test_endpoint_exists(self, client):
        """Test that the endpoint exists and responds"""
        response = client.post('/api/settings/generate-config',
            json={},
            headers={'Content-Type': 'application/json'})
        # Should get 400 (missing data) not 404
        assert response.status_code in [400, 401, 403]  # Not 404
    
    def test_missing_preferences_error(self, client):
        """Test error when preferences are missing"""
        response = client.post('/api/settings/generate-config',
            json={},
            headers={'Content-Type': 'application/json'}
        )
        
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'preferences' in data['error'].lower()
    
    def test_endpoint_with_valid_request(self, client):
        """Test endpoint with valid request structure"""
        # Mock all the dependencies
        with patch('config_generator.ConfigGenerator') as mock_gen_class:
            with patch('ai_providers.OpenAIProvider') as mock_openai:
                with patch('ai_providers.ClaudeProvider') as mock_claude:
                    # Setup mocks
                    mock_provider = MagicMock()
                    mock_provider.is_available.return_value = True
                    mock_claude.return_value = mock_provider
                    mock_openai.return_value.is_available.return_value = False
                    
                    # Mock config generation
                    mock_config = MagicMock()
                    mock_config.version = '1.0.0'
                    mock_config.user_profile = MagicMock()
                    mock_config.user_profile.philosophy = MagicMock(value='polarized')
                    mock_config.user_profile.volume_levels = {}
                    mock_config.user_profile.thresholds = {}
                    mock_config.user_profile.preferences = {}
                    mock_config.sports = []
                    
                    mock_generator = MagicMock()
                    mock_generator.generate_config.return_value = mock_config
                    mock_gen_class.return_value = mock_generator
                    
                    # Make request
                    response = client.post('/api/settings/generate-config',
                        json={'preferences': 'I am a cyclist'},
                        headers={'Content-Type': 'application/json'}
                    )
                    
                    # Should succeed
                    assert response.status_code == 200
                    data = json.loads(response.data)
                    assert data['success'] is True
                    assert 'config' in data
    
    def test_zone_distribution_in_request(self, client):
        """Test that zone distribution is included in preferences"""
        with patch('config_generator.ConfigGenerator') as mock_gen_class:
            with patch('ai_providers.ClaudeProvider') as mock_claude:
                # Setup mocks
                mock_provider = MagicMock()
                mock_provider.is_available.return_value = True
                mock_claude.return_value = mock_provider
                
                # Mock config
                mock_config = MagicMock()
                mock_config.version = '1.0.0'
                mock_config.user_profile = MagicMock()
                mock_config.user_profile.philosophy = MagicMock(value='polarized')
                mock_config.user_profile.volume_levels = {}
                mock_config.user_profile.thresholds = {}
                mock_config.user_profile.preferences = {}
                mock_config.sports = []
                
                mock_generator = MagicMock()
                mock_generator.generate_config.return_value = mock_config
                mock_gen_class.return_value = mock_generator
                
                # Make request with zone distribution
                response = client.post('/api/settings/generate-config',
                    json={
                        'preferences': 'Test preferences',
                        'zone_distribution': {'1': 80, '2': 15, '3': 5}
                    },
                    headers={'Content-Type': 'application/json'}
                )
                
                assert response.status_code == 200
                
                # Verify zone distribution was passed to generator
                mock_generator.generate_config.assert_called_once()
                call_args = mock_generator.generate_config.call_args[0][0]
                assert 'Zone Distribution Targets:' in call_args
                assert 'Zone 1: 80%' in call_args


if __name__ == "__main__":
    pytest.main([__file__, "-v"])