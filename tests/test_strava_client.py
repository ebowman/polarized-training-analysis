"""
Unit tests for strava_client.py
Tests Strava API integration with mocked HTTP requests
"""

import pytest
from unittest.mock import patch, MagicMock, Mock
from datetime import datetime, timedelta
import json
from strava_client import StravaClient


class TestStravaClient:
    """Test the StravaClient class"""
    
    @pytest.fixture
    def client(self):
        """Create a StravaClient instance"""
        return StravaClient()
    
    @pytest.fixture
    def mock_env(self, monkeypatch):
        """Mock environment variables"""
        monkeypatch.setenv('STRAVA_CLIENT_ID', 'test_client_id')
        monkeypatch.setenv('STRAVA_CLIENT_SECRET', 'test_client_secret')
    
    def test_initialization(self, client, mock_env):
        """Test client initialization with environment variables"""
        assert client.client_id == 'test_client_id'
        assert client.client_secret == 'test_client_secret'
        assert client.redirect_uri == 'http://localhost:5000/strava-callback'
    
    def test_get_authorization_url(self, client):
        """Test authorization URL generation"""
        url = client.get_authorization_url()
        
        assert 'https://www.strava.com/oauth/authorize' in url
        assert 'client_id=' in url
        assert 'redirect_uri=' in url
        assert 'scope=read,activity:read' in url
        assert 'response_type=code' in url
    
    @patch('strava_client.requests.post')
    def test_get_access_token_success(self, mock_post, client):
        """Test successful OAuth token exchange"""
        mock_response = Mock()
        mock_response.json.return_value = {
            'access_token': 'new_access_token',
            'refresh_token': 'new_refresh_token',
            'expires_at': 1234567890,
            'athlete': {
                'id': 12345,
                'firstname': 'Test',
                'lastname': 'User'
            }
        }
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response
        
        result = client.get_access_token('test_auth_code')
        
        assert result['access_token'] == 'new_access_token'
        assert result['refresh_token'] == 'new_refresh_token'
        assert result['athlete']['id'] == 12345
        
        # Verify API call
        mock_post.assert_called_once_with(
            'https://www.strava.com/oauth/token',
            data={
                'client_id': client.client_id,
                'client_secret': client.client_secret,
                'code': 'test_auth_code',
                'grant_type': 'authorization_code'
            }
        )
    
    @patch('strava_client.requests.post')
    def test_get_access_token_failure(self, mock_post, client):
        """Test failed OAuth token exchange"""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("API Error")
        mock_post.return_value = mock_response
        
        with pytest.raises(Exception, match="API Error"):
            client.get_access_token('bad_code')
    
    @patch('strava_client.requests.get')
    def test_fetch_activities_single_page(self, mock_get, client):
        """Test fetching activities (single page)"""
        mock_activities = [
            {
                'id': 123,
                'name': 'Morning Run',
                'type': 'Run',
                'start_date': '2024-01-01T07:00:00Z',
                'elapsed_time': 3600,
                'distance': 10000
            },
            {
                'id': 124,
                'name': 'Evening Ride',
                'type': 'Ride',
                'start_date': '2024-01-01T18:00:00Z',
                'elapsed_time': 5400,
                'distance': 30000
            }
        ]
        
        mock_response = Mock()
        mock_response.json.return_value = mock_activities
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        activities = client.fetch_activities('test_token')
        
        assert len(activities) == 2
        assert activities[0]['name'] == 'Morning Run'
        assert activities[1]['name'] == 'Evening Ride'
        
        # Verify API call
        mock_get.assert_called_once()
        call_args = mock_get.call_args
        assert 'https://www.strava.com/api/v3/athlete/activities' in call_args[0][0]
        assert call_args[1]['headers']['Authorization'] == 'Bearer test_token'
    
    @patch('strava_client.requests.get')
    def test_fetch_activities_with_pagination(self, mock_get, client):
        """Test fetching activities with pagination"""
        # First page - 200 activities
        page1_activities = [{'id': i, 'name': f'Activity {i}'} for i in range(200)]
        # Second page - 50 activities
        page2_activities = [{'id': i+200, 'name': f'Activity {i+200}'} for i in range(50)]
        # Third page - empty (signals end)
        page3_activities = []
        
        mock_responses = [Mock(), Mock(), Mock()]
        mock_responses[0].json.return_value = page1_activities
        mock_responses[1].json.return_value = page2_activities
        mock_responses[2].json.return_value = page3_activities
        
        for response in mock_responses:
            response.raise_for_status = Mock()
        
        mock_get.side_effect = mock_responses
        
        activities = client.fetch_activities('test_token')
        
        assert len(activities) == 250
        assert activities[0]['name'] == 'Activity 0'
        assert activities[249]['name'] == 'Activity 249'
        
        # Verify pagination calls
        assert mock_get.call_count == 3
    
    @patch('strava_client.requests.get')
    def test_fetch_activities_with_after_timestamp(self, mock_get, client):
        """Test fetching activities after specific timestamp"""
        mock_response = Mock()
        mock_response.json.return_value = []
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        after_time = int(datetime(2024, 1, 1).timestamp())
        client.fetch_activities('test_token', after=after_time)
        
        # Verify 'after' parameter was included
        call_args = mock_get.call_args
        assert call_args[1]['params']['after'] == after_time
    
    @patch('strava_client.requests.get')
    def test_fetch_activity_details(self, mock_get, client):
        """Test fetching detailed activity data"""
        mock_detail = {
            'id': 123,
            'name': 'Morning Run',
            'type': 'Run',
            'elapsed_time': 3600,
            'distance': 10000,
            'average_heartrate': 145,
            'max_heartrate': 175,
            'average_watts': None,
            'weighted_average_watts': None,
            'laps': [
                {
                    'id': 1,
                    'elapsed_time': 1800,
                    'distance': 5000,
                    'average_heartrate': 140
                }
            ]
        }
        
        mock_response = Mock()
        mock_response.json.return_value = mock_detail
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        details = client.fetch_activity_details(123, 'test_token')
        
        assert details['id'] == 123
        assert details['average_heartrate'] == 145
        assert len(details['laps']) == 1
        
        # Verify API call
        mock_get.assert_called_once_with(
            'https://www.strava.com/api/v3/activities/123',
            headers={'Authorization': 'Bearer test_token'}
        )
    
    @patch('strava_client.requests.get')
    def test_fetch_activity_streams(self, mock_get, client):
        """Test fetching activity streams (time series data)"""
        mock_streams = {
            'time': {'data': [0, 1, 2, 3, 4, 5]},
            'heartrate': {'data': [120, 125, 130, 135, 140, 145]},
            'watts': {'data': [150, 160, 170, 180, 190, 200]}
        }
        
        mock_response = Mock()
        mock_response.json.return_value = mock_streams
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        streams = client.fetch_activity_streams(
            123, 
            'test_token',
            keys=['time', 'heartrate', 'watts']
        )
        
        assert 'time' in streams
        assert 'heartrate' in streams
        assert 'watts' in streams
        assert len(streams['heartrate']['data']) == 6
        
        # Verify API call
        call_args = mock_get.call_args
        assert '123/streams' in call_args[0][0]
        assert call_args[1]['params']['keys'] == 'time,heartrate,watts'
    
    @patch('strava_client.requests.get')
    def test_error_handling_rate_limit(self, mock_get, client):
        """Test handling of rate limit errors"""
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.headers = {'X-RateLimit-Limit': '100', 'X-RateLimit-Usage': '100'}
        mock_response.raise_for_status.side_effect = Exception("Rate limit exceeded")
        mock_get.return_value = mock_response
        
        with pytest.raises(Exception, match="Rate limit exceeded"):
            client.fetch_activities('test_token')
    
    def test_basic_functionality(self, client):
        """Test basic Strava client functionality"""
        # Test that client initializes properly
        assert hasattr(client, 'client_id')
        assert hasattr(client, 'client_secret')
        assert hasattr(client, 'redirect_uri')
        
        # Test authorization URL contains required parameters
        auth_url = client.get_authorization_url()
        assert 'client_id' in auth_url
        assert 'redirect_uri' in auth_url
        assert 'scope' in auth_url