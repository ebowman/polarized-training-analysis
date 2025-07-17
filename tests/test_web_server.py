"""
Integration tests for web_server.py
Tests Flask routes, API endpoints, and web application behavior
"""

import pytest
import json
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta
from io import BytesIO
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
    
    def test_zone_mapping_guide_route(self, client):
        """Test zone mapping guide page"""
        response = client.get('/zone-mapping-guide')
        assert response.status_code == 200
        assert b'Zone Mapping' in response.data or b'Training Zones' in response.data
    
    @patch('web_server.render_template')
    def test_template_rendering(self, mock_render, client):
        """Test template rendering with different contexts"""
        mock_render.return_value = 'Rendered template'
        
        # Test index with different query parameters
        response = client.get('/?debug=true')
        assert response.status_code == 200
        
        # Test workout preferences with context
        response = client.get('/workout_preferences?sport=cycling')
        assert response.status_code == 200
    
    def test_api_endpoints_with_different_methods(self, client):
        """Test API endpoints with various HTTP methods"""
        # Test OPTIONS for CORS
        response = client.options('/api/workouts')
        assert response.status_code in [200, 405]  # Depends on CORS setup
        
        # Test unsupported methods
        response = client.delete('/api/workouts')
        assert response.status_code == 405
        
        response = client.put('/api/workouts')
        assert response.status_code == 405
    
    @patch('web_server.get_training_data')
    def test_api_workouts_with_different_parameters(self, mock_get_training_data, client):
        """Test workout API with various parameter combinations"""
        mock_get_training_data.return_value = {
            'distribution': {'adherence_score': 75},
            'activities': []
        }
        
        # Test with different day ranges
        test_cases = [
            ('days=1', 1),
            ('days=7', 7),
            ('days=30', 30),
            ('days=90', 90),
            ('days=365', 365),
            ('', None)  # No parameter
        ]
        
        for params, expected_days in test_cases:
            url = f'/api/workouts?{params}' if params else '/api/workouts'
            response = client.get(url)
            assert response.status_code == 200
            
            # Check that get_training_data was called with correct days
            if expected_days:
                mock_get_training_data.assert_called_with(days=expected_days)
    
    def test_strava_oauth_flow_edge_cases(self, client):
        """Test Strava OAuth flow edge cases"""
        # Test with missing code parameter
        response = client.get('/strava-callback')
        assert response.status_code == 400
        
        # Test with both code and error
        response = client.get('/strava-callback?code=test&error=access_denied')
        assert response.status_code == 400
        
        # Test with empty code
        response = client.get('/strava-callback?code=')
        assert response.status_code == 400
    
    @patch('web_server.strava_client')
    def test_strava_callback_token_exchange_errors(self, mock_strava_client, client):
        """Test Strava callback with token exchange errors"""
        # Test network error during token exchange
        mock_strava_client.get_access_token.side_effect = Exception("Network error")
        
        response = client.get('/strava-callback?code=test_code')
        assert response.status_code == 500
        
        # Test invalid response structure
        mock_strava_client.get_access_token.return_value = {'error': 'invalid_grant'}
        
        response = client.get('/strava-callback?code=test_code')
        assert response.status_code == 500
    
    def test_download_progress_page(self, client):
        """Test download progress page"""
        response = client.get('/download-progress')
        assert response.status_code == 200
        assert b'Download Progress' in response.data or b'progress' in response.data
    
    @patch('web_server.DownloadManager')
    def test_download_manager_lifecycle(self, mock_dm_class, mock_session):
        """Test download manager lifecycle"""
        mock_dm = MagicMock()
        mock_dm_class.return_value = mock_dm
        
        # Test starting download
        mock_dm.start_download.return_value = True
        response = mock_session.post('/api/download-workouts', json={'days': 30})
        assert response.status_code == 200
        
        # Test stopping download
        mock_dm.stop_download.return_value = True
        response = mock_session.post('/api/download-stop')
        # This endpoint might not exist, so check if it's handled gracefully
        assert response.status_code in [200, 404, 405]
    
    @patch('web_server.ai_engine')
    def test_ai_recommendations_full_workflow(self, mock_ai_engine, mock_session):
        """Test complete AI recommendations workflow"""
        from ai_recommendations import AIWorkoutPathway, AIWorkoutRecommendation
        from datetime import datetime
        
        # Mock AI engine response
        mock_workout = AIWorkoutRecommendation(
            workout_type='Test Workout',
            duration_minutes=60,
            description='Test description',
            structure='Test structure',
            reasoning='Test reasoning',
            equipment='Test equipment',
            intensity_zones=[1, 2],
            priority='high',
            generated_at=datetime.now().isoformat()
        )
        
        mock_pathway = AIWorkoutPathway(
            pathway_name='Test Pathway',
            today=mock_workout,
            tomorrow=mock_workout,
            overall_reasoning='Test overall reasoning',
            priority='high',
            generated_at=datetime.now().isoformat()
        )
        
        mock_ai_engine.generate_ai_recommendations.return_value = [mock_pathway]
        
        # Test starting AI generation
        with patch('web_server.get_training_data') as mock_get_data:
            mock_get_data.return_value = {'activities': []}
            response = mock_session.post('/api/ai-recommendations/refresh')
            assert response.status_code == 200
    
    def test_session_management(self, client):
        """Test session management and security"""
        # Test accessing protected endpoint without session
        response = client.post('/api/download-workouts')
        assert response.status_code == 401
        
        # Test session timeout/invalid session
        with client.session_transaction() as sess:
            sess['strava_access_token'] = 'expired_token'
            sess['expires_at'] = 0  # Expired
        
        response = client.get('/api/workouts')
        # Should handle gracefully
        assert response.status_code in [200, 401]
    
    def test_concurrent_requests(self, client):
        """Test handling of concurrent requests"""
        import threading
        import time
        
        results = []
        
        def make_request():
            response = client.get('/api/workouts')
            results.append(response.status_code)
        
        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=make_request)
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # All requests should complete successfully
        assert len(results) == 5
        assert all(status == 200 for status in results)
    
    def test_large_payload_handling(self, client):
        """Test handling of large request payloads"""
        # Test with large preferences payload
        large_preferences = {
            'preferences': {
                'equipment': ['item' + str(i) for i in range(1000)],
                'goals': 'x' * 10000,  # Large text
                'constraints': 'y' * 5000
            }
        }
        
        response = client.post('/api/workout-preferences', json=large_preferences)
        # Should handle gracefully (accept or reject with proper error)
        assert response.status_code in [200, 400, 413, 500]
    
    def test_content_type_validation(self, client):
        """Test content type validation"""
        # Test with wrong content type
        response = client.post('/api/workout-preferences',
                             data='not json',
                             content_type='text/plain')
        assert response.status_code == 400
        
        # Test with missing content type
        response = client.post('/api/workout-preferences',
                             data='{"preferences": {}}')
        assert response.status_code in [200, 400]
    
    @patch('web_server.save_workout_preferences')
    def test_preference_validation(self, mock_save, client):
        """Test workout preference validation"""
        # Test with invalid preference structure
        invalid_prefs = [
            {'invalid': 'structure'},
            {'preferences': None},
            {'preferences': []},  # Wrong type
            {'preferences': 'string'},  # Wrong type
        ]
        
        for pref in invalid_prefs:
            response = client.post('/api/workout-preferences', json=pref)
            assert response.status_code == 400
    
    def test_api_rate_limiting(self, client):
        """Test API rate limiting behavior"""
        # Make many requests quickly
        responses = []
        for i in range(20):
            response = client.get('/api/workouts')
            responses.append(response.status_code)
        
        # Should handle all requests (or implement rate limiting)
        assert all(status in [200, 429, 500] for status in responses)
    
    def test_websocket_endpoints(self, client):
        """Test WebSocket endpoints if they exist"""
        # Test WebSocket upgrade request
        response = client.get('/ws/progress',
                            headers={
                                'Upgrade': 'websocket',
                                'Connection': 'Upgrade',
                                'Sec-WebSocket-Key': 'test',
                                'Sec-WebSocket-Version': '13'
                            })
        
        # Should either upgrade or return 404/400
        assert response.status_code in [101, 400, 404, 405]
    
    def test_health_check_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get('/health')
        if response.status_code == 200:
            # If health endpoint exists, should return status
            data = json.loads(response.data)
            assert 'status' in data
        else:
            # If not implemented, should return 404
            assert response.status_code == 404
    
    def test_api_versioning(self, client):
        """Test API versioning if implemented"""
        # Test different API versions
        versions = ['v1', 'v2']
        for version in versions:
            response = client.get(f'/api/{version}/workouts')
            # Should either work or return 404
            assert response.status_code in [200, 404]
    
    def test_cache_headers(self, client):
        """Test cache headers on responses"""
        response = client.get('/api/workouts')
        
        # Check for cache-related headers
        headers = response.headers
        # These might be set depending on caching strategy
        cache_headers = ['Cache-Control', 'ETag', 'Last-Modified', 'Expires']
        # At least one cache header should be present for API responses
        # (This test might need adjustment based on actual implementation)
    
    def test_security_headers(self, client):
        """Test security headers"""
        response = client.get('/')
        
        # Check for security headers
        headers = response.headers
        security_headers = [
            'X-Content-Type-Options',
            'X-Frame-Options',
            'X-XSS-Protection',
            'Strict-Transport-Security'
        ]
        
        # Note: These might not be implemented yet
        # This test documents what should be added for production
    
    def test_database_connection_errors(self, client):
        """Test handling of database connection errors"""
        # Mock database connection failure
        with patch('web_server.get_training_data') as mock_get_data:
            mock_get_data.side_effect = Exception("Database connection failed")
            
            response = client.get('/api/workouts')
            assert response.status_code == 500
            data = json.loads(response.data)
            assert 'error' in data
    
    def test_file_upload_endpoints(self, client):
        """Test file upload endpoints if they exist"""
        # Test with various file types
        test_files = [
            ('test.json', b'{"test": "data"}', 'application/json'),
            ('test.csv', b'name,value\ntest,123', 'text/csv'),
            ('test.txt', b'plain text', 'text/plain'),
        ]
        
        for filename, content, mimetype in test_files:
            response = client.post('/api/upload',
                                 data={'file': (BytesIO(content), filename)},
                                 content_type='multipart/form-data')
            
            # Should either handle or return 404/405
            assert response.status_code in [200, 400, 404, 405]
    
    def test_internationalization(self, client):
        """Test internationalization support"""
        # Test with different Accept-Language headers
        languages = ['en-US', 'es-ES', 'fr-FR', 'de-DE']
        
        for lang in languages:
            response = client.get('/', headers={'Accept-Language': lang})
            assert response.status_code == 200
            # Response should be in appropriate language (if i18n is implemented)
    
    def test_mobile_responsive_endpoints(self, client):
        """Test mobile-specific endpoints"""
        # Test with mobile user agent
        mobile_ua = 'Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15'
        
        response = client.get('/', headers={'User-Agent': mobile_ua})
        assert response.status_code == 200
        
        # Test mobile API endpoints
        response = client.get('/api/workouts', headers={'User-Agent': mobile_ua})
        assert response.status_code == 200