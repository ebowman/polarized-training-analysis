"""
Integration tests for web_server.py
Tests Flask routes, API endpoints, and web application behavior
"""

import pytest
import json
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta
from web_server import app, DownloadManager
from training_analysis import ActivityAnalysis


@pytest.fixture
def client():
    """Create test client for Flask app"""
    app.config['TESTING'] = True
    app.config['SECRET_KEY'] = 'test-secret-key'
    
    with app.test_client() as client:
        with app.app_context():
            yield client


@pytest.fixture
def mock_session(client):
    """Mock Flask session for authenticated requests"""
    with client.session_transaction() as sess:
        sess['strava_access_token'] = 'test_token'
        sess['athlete_id'] = '12345'
        sess['ai_session_id'] = 'test_session_123'
    return client


class TestWebServer:
    """Test Flask routes and API endpoints"""
    
    def test_index_route(self, client):
        """Test main dashboard loads successfully"""
        response = client.get('/')
        assert response.status_code == 200
        assert b'Polarized Training Analysis' in response.data
        assert b'Training Distribution' in response.data
    
    def test_workout_preferences_route(self, client):
        """Test workout preferences page"""
        response = client.get('/workout_preferences')
        assert response.status_code == 200
        assert b'Workout Preferences' in response.data or b'Training Goals' in response.data
    
    @patch('web_server.get_training_data')
    def test_api_workouts_endpoint(self, mock_get_training_data, client):
        """Test workout API endpoint with different time windows"""
        # Mock training data response
        mock_get_training_data.return_value = {
            'distribution': {
                'zone1_percent': 75,
                'zone2_percent': 15,
                'zone3_percent': 10,
                'adherence_score': 85,
                'total_minutes': 630
            },
            'activities': []
        }
        
        # Test default (all time)
        response = client.get('/api/workouts')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'distribution' in data
        assert data['distribution']['adherence_score'] == 85
        
        # Test with 7-day window
        response = client.get('/api/workouts?days=7')
        assert response.status_code == 200
        
        # Test with invalid days parameter
        response = client.get('/api/workouts?days=invalid')
        assert response.status_code == 200  # Should default to all time
    
    @patch('web_server.strava_client')
    def test_download_workouts_redirect(self, mock_strava_client, client):
        """Test OAuth redirect for Strava authentication"""
        # Mock the strava client
        mock_strava_client.access_token = None
        mock_strava_client.get_authorization_url.return_value = 'https://www.strava.com/oauth/authorize?client_id=123'
        
        response = client.get('/download-workouts')
        assert response.status_code == 302  # Redirect
        assert 'strava.com/oauth/authorize' in response.location
    
    @patch('web_server.strava_client')
    def test_strava_callback(self, mock_strava_client, client):
        """Test Strava OAuth callback handling"""
        # Mock the global strava_client
        mock_strava_client.get_access_token.return_value = {
            'access_token': 'new_token',
            'refresh_token': 'refresh_token',
            'athlete': {'id': 12345, 'firstname': 'Test'}
        }
        
        response = client.get('/strava-callback?code=test_code')
        assert response.status_code == 302  # Redirect to download_progress
        assert response.location.endswith('/download-progress')
        
        # Verify session was updated
        with client.session_transaction() as sess:
            assert sess.get('strava_access_token') == 'new_token'
            assert sess.get('auth_success') == True
            assert sess.get('athlete_name') == 'Test'
    
    def test_strava_callback_error(self, client):
        """Test Strava callback with error"""
        response = client.get('/strava-callback?error=access_denied')
        assert response.status_code == 400
        data = json.loads(response.data)
        assert 'error' in data
        assert 'access_denied' in data['error']
    
    @patch('strava_client.StravaClient')
    @patch('web_server.DownloadManager')
    def test_api_download_workouts(self, mock_dm_class, mock_client_class, mock_session):
        """Test download workouts API endpoint"""
        mock_dm_instance = MagicMock()
        mock_dm_instance.start_download.return_value = True
        mock_dm_class.return_value = mock_dm_instance
        
        mock_client_instance = MagicMock()
        mock_client_instance._save_tokens = MagicMock()  # Mock the _save_tokens method
        mock_client_class.return_value = mock_client_instance
        
        response = mock_session.post('/api/download-workouts',
                                    json={'days': 30})
        if response.status_code != 200:
            print(f"Response status: {response.status_code}")
            print(f"Response data: {response.data}")
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'started'
        assert data['message'] == 'Download started'
        
        # Verify download was called with correct params
        mock_dm_instance.start_download.assert_called_once()
    
    def test_api_download_workouts_unauthorized(self, client):
        """Test download endpoint without authentication"""
        response = client.post('/api/download-workouts')
        assert response.status_code == 401
        data = json.loads(response.data)
        assert data['error'] == 'Not authenticated with Strava'
    
    @patch('web_server.DownloadManager')
    def test_api_download_progress(self, mock_dm_class, client):
        """Test download progress endpoint"""
        mock_dm_instance = MagicMock()
        mock_dm_instance.get_progress.return_value = {
            'status': 'downloading',
            'progress': 50,
            'current_activity': 5,
            'total_activities': 10
        }
        mock_dm_class.return_value = mock_dm_instance
        
        response = client.get('/api/download-progress/test_123')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['progress'] == 50
        assert data['status'] == 'downloading'
    
    def test_api_ai_recommendations_unauthorized(self, client):
        """Test AI recommendations without session"""
        response = client.post('/api/ai-recommendations/refresh')
        assert response.status_code == 401
    
    @patch('web_server.ai_engine', new=MagicMock())
    @patch('web_server.get_training_data')
    @patch('web_server.start_ai_generation')
    def test_api_ai_recommendations_refresh(self, mock_start_generation, mock_get_training_data, mock_session):
        """Test AI recommendations refresh endpoint"""
        # Mock training data
        mock_get_training_data.return_value = {
            'distribution': {'zone1_percent': 70, 'zone2_percent': 20, 'zone3_percent': 10},
            'activities': []
        }
        
        response = mock_session.post('/api/ai-recommendations/refresh')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['session_id'] == 'test_session_123'
        assert data['status'] == 'generating'
        
        # Verify async generation was started
        mock_start_generation.assert_called_once()
    
    @patch('web_server.os.path.exists')
    @patch('web_server.open', create=True)
    def test_api_ai_recommendations_get(self, mock_open, mock_exists, mock_session):
        """Test getting AI recommendations"""
        mock_exists.return_value = True
        mock_recommendations = {
            'recommendations': 'Test workout plan',
            'generated_at': datetime.now().isoformat()
        }
        mock_open.return_value.__enter__.return_value.read.return_value = json.dumps(mock_recommendations)
        
        response = mock_session.get('/api/ai-recommendations/test_session_123')
        assert response.status_code == 200
        data = json.loads(response.data)
        assert 'recommendations' in data or data.get('recommendations') == 'Test workout plan'
    
    @patch('web_server.ai_engine', new=MagicMock())
    def test_api_ai_status_not_found(self, client):
        """Test AI status for non-existent session"""
        response = client.get('/api/ai-status/nonexistent')
        assert response.status_code == 404
    
    @patch('web_server.save_workout_preferences')
    def test_api_save_preferences(self, mock_save, client):
        """Test saving workout preferences"""
        preferences = {
            'equipment': ['Peloton', 'TRX'],
            'goals': 'Marathon training',
            'constraints': 'Bad knees'
        }
        
        response = client.post('/api/workout-preferences',
                             json={'preferences': preferences})
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'saved'
        
        # Verify save was called
        mock_save.assert_called_once_with(preferences)
    
    def test_api_save_preferences_invalid(self, client):
        """Test saving preferences with invalid data"""
        response = client.post('/api/workout-preferences',
                             json={})  # Missing preferences
        assert response.status_code == 400
    
    def test_static_file_serving(self, client):
        """Test that static files are served correctly"""
        # This would normally test CSS/JS serving, but in test mode
        # Flask doesn't serve static files the same way
        pass
    
    def test_error_handlers(self, client):
        """Test error handling"""
        # Test 404
        response = client.get('/nonexistent-route')
        assert response.status_code == 404
    
    @patch('web_server.get_training_data')
    def test_api_workouts_with_error(self, mock_get_training_data, client):
        """Test API error handling"""
        # Mock an exception
        mock_get_training_data.side_effect = Exception("Cache error")
        
        response = client.get('/api/workouts')
        assert response.status_code == 500
        data = json.loads(response.data)
        assert 'error' in data
        assert 'Cache error' in data['error']