import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

from logging_config import get_logger, StravaAPIError, ConfigurationError

load_dotenv()
logger = get_logger(__name__)

class StravaClient:
    """Client for interacting with the Strava API.
    
    This client handles OAuth authentication, token management, API requests,
    and caching of responses to minimize API calls.
    
    Attributes:
        client_id: Strava OAuth client ID
        client_secret: Strava OAuth client secret
        cache_dir: Directory for storing cached API responses
        access_token: Current access token for API requests
        refresh_token: Token for refreshing access when expired
        token_expires_at: Unix timestamp when access token expires
        redirect_uri: OAuth redirect URI for authorization flow
    """
    
    def __init__(self, cache_dir: str = "cache"):
        """Initialize the Strava client.
        
        Args:
            cache_dir: Directory path for storing cache files. Defaults to "cache".
            
        Raises:
            ValueError: If STRAVA_CLIENT_ID or STRAVA_CLIENT_SECRET environment
                variables are not set.
        """
        self.client_id = os.getenv("STRAVA_CLIENT_ID")
        self.client_secret = os.getenv("STRAVA_CLIENT_SECRET")
        self.cache_dir = cache_dir
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        self.redirect_uri = "http://localhost:5000/strava-callback"  # For test compatibility
        
        if not self.client_id or not self.client_secret:
            logger.error("Missing Strava credentials in environment")
            raise ConfigurationError("STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET must be set in .env file")
        
        os.makedirs(self.cache_dir, exist_ok=True)
        self._load_tokens()
    
    def _load_tokens(self):
        """Load OAuth tokens from cache file.
        
        Reads previously saved access token, refresh token, and expiration
        timestamp from the tokens.json file in the cache directory. If the
        file doesn't exist or is missing data, the attributes remain None.
        """
        token_file = os.path.join(self.cache_dir, "tokens.json")
        if os.path.exists(token_file):
            try:
                with open(token_file, 'r') as f:
                    tokens = json.load(f)
                    self.access_token = tokens.get("access_token")
                    self.refresh_token = tokens.get("refresh_token")
                    self.token_expires_at = tokens.get("expires_at")
                    logger.debug("Loaded tokens from cache")
            except (json.JSONDecodeError, IOError) as e:
                logger.error(f"Failed to load tokens from cache: {e}")
                # Continue with None values
    
    def _save_tokens(self):
        """Save OAuth tokens to cache file.
        
        Persists the current access token, refresh token, and expiration
        timestamp to tokens.json in the cache directory for reuse across
        sessions.
        """
        token_file = os.path.join(self.cache_dir, "tokens.json")
        tokens = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.token_expires_at
        }
        try:
            with open(token_file, 'w') as f:
                json.dump(tokens, f)
            logger.debug("Saved tokens to cache")
        except IOError as e:
            logger.error(f"Failed to save tokens to cache: {e}")
    
    def get_authorization_url(self, redirect_uri: str = None) -> str:
        """Get URL for OAuth authorization"""
        scope = "read,activity:read"  # Match test expectations
        if redirect_uri is None:
            redirect_uri = self.redirect_uri
        return (f"https://www.strava.com/oauth/authorize?"
                f"client_id={self.client_id}&"
                f"response_type=code&"
                f"redirect_uri={redirect_uri}&"
                f"approval_prompt=force&"
                f"scope={scope}")
    
    def exchange_code_for_tokens(self, code: str) -> Dict:
        """Exchange authorization code for access tokens"""
        url = "https://www.strava.com/oauth/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "code": code,
            "grant_type": "authorization_code"
        }
        
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.refresh_token = token_data["refresh_token"]
            self.token_expires_at = token_data["expires_at"]
            
            self._save_tokens()
            logger.info("Successfully exchanged code for tokens")
            return token_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to exchange code for tokens: {e}")
            raise StravaAPIError(f"Failed to exchange authorization code: {e}") from e
    
    def refresh_access_token(self) -> Dict:
        """Refresh the access token using refresh token"""
        if not self.refresh_token:
            logger.error("No refresh token available for refresh")
            raise ConfigurationError("No refresh token available")
        
        url = "https://www.strava.com/oauth/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token"
        }
        
        try:
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            token_data = response.json()
            self.access_token = token_data["access_token"]
            self.refresh_token = token_data["refresh_token"]
            self.token_expires_at = token_data["expires_at"]
            
            self._save_tokens()
            logger.info("Successfully refreshed access token")
            return token_data
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to refresh access token: {e}")
            raise StravaAPIError(f"Failed to refresh access token: {e}") from e
    
    def _ensure_valid_token(self):
        """Ensure we have a valid access token"""
        if not self.access_token:
            logger.error("No access token available")
            raise ConfigurationError("No access token available. Please authorize first.")
        
        if self.token_expires_at and time.time() >= self.token_expires_at:
            logger.info("Token expired, refreshing...")
            self.refresh_access_token()
    
    def _get_cache_file(self, endpoint: str, params: Dict = None) -> str:
        """Generate cache file path for given endpoint and params.
        
        Creates a unique filename based on the API endpoint and request parameters
        to enable caching of different API responses. Forward slashes in the
        endpoint are replaced with underscores to create valid filenames.
        
        Args:
            endpoint: API endpoint path (e.g., "/athlete/activities")
            params: Query parameters dictionary. Will be sorted and included
                in the filename to differentiate cached responses.
                
        Returns:
            Full path to the cache file.
            
        Example:
            >>> client._get_cache_file("/athlete/activities", {"page": 1})
            "cache/_athlete_activities_page_1.json"
        """
        param_str = "_".join(f"{k}_{v}" for k, v in sorted((params or {}).items()))
        cache_key = f"{endpoint}_{param_str}".replace("/", "_")
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def _is_cache_valid(self, cache_file: str, max_age_hours: int = 1) -> bool:
        """Check if cache file is valid (exists and not too old).
        
        Determines whether a cached response can be used instead of making
        a new API request based on the file's existence and age.
        
        Args:
            cache_file: Path to the cache file to check
            max_age_hours: Maximum age in hours before cache is considered stale.
                Defaults to 1 hour.
                
        Returns:
            True if the cache file exists and is newer than max_age_hours,
            False otherwise.
            
        Example:
            >>> client._is_cache_valid("cache/athlete.json", max_age_hours=24)
            True  # If file exists and is less than 24 hours old
        """
        if not os.path.exists(cache_file):
            return False
        
        try:
            file_age = time.time() - os.path.getmtime(cache_file)
            return file_age < (max_age_hours * 3600)
        except OSError as e:
            logger.warning(f"Failed to check cache file age: {e}")
            return False
    
    def _api_request(self, endpoint: str, params: Dict = None, cache_hours: int = 1) -> Dict:
        """Make API request with caching"""
        cache_file = self._get_cache_file(endpoint, params)
        
        if self._is_cache_valid(cache_file, cache_hours):
            logger.debug(f"Using cached data for {endpoint}")
            try:
                with open(cache_file, 'r') as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError) as e:
                logger.warning(f"Failed to read cache file: {e}")
                # Continue to fetch fresh data
        
        self._ensure_valid_token()
        
        url = f"https://www.strava.com/api/v3{endpoint}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        logger.info(f"Making API request to {endpoint}")
        
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            # Handle token expiration (Strava returns 401 or sometimes 400 for auth issues)
            if e.response.status_code in [400, 401]:
                logger.warning(f"Auth error ({e.response.status_code}), attempting to refresh token...")
                try:
                    self.refresh_access_token()
                    logger.info("Token refreshed successfully, retrying request...")
                    # Retry with new token
                    headers = {"Authorization": f"Bearer {self.access_token}"}
                    response = requests.get(url, headers=headers, params=params)
                    response.raise_for_status()
                    logger.info(f"Request succeeded after token refresh")
                except Exception as refresh_error:
                    logger.error(f"Failed to refresh token: {refresh_error}")
                    raise StravaAPIError(f"Token refresh failed: {refresh_error}. Please re-authorize the application.") from refresh_error
            else:
                logger.error(f"API request failed: {e}")
                raise StravaAPIError(f"API request to {endpoint} failed: {e}") from e
        
        data = response.json()
        
        try:
            with open(cache_file, 'w') as f:
                json.dump(data, f, indent=2)
        except IOError as e:
            logger.warning(f"Failed to cache response: {e}")
            # Continue - caching failure is not critical
        
        time.sleep(0.1)  # Rate limiting
        return data
    
    def get_athlete(self) -> Dict:
        """Get current athlete profile"""
        return self._api_request("/athlete")
    
    def get_activities(self, page: int = 1, per_page: int = 30) -> List[Dict]:
        """Get list of activities"""
        params = {"page": page, "per_page": per_page}
        return self._api_request("/athlete/activities", params)
    
    def get_activity_details(self, activity_id: int) -> Dict:
        """Get detailed information about a specific activity"""
        return self._api_request(f"/activities/{activity_id}", cache_hours=24)
    
    def get_activity_streams(self, activity_id: int, 
                           stream_types: List[str] = None) -> Dict:
        """Get activity streams (time series data)"""
        if stream_types is None:
            stream_types = ["time", "distance", "latlng", "altitude", "velocity_smooth", 
                          "heartrate", "cadence", "watts", "temp", "moving", "grade_smooth"]
        
        params = {"keys": ",".join(stream_types), "key_by_type": True}
        return self._api_request(f"/activities/{activity_id}/streams", params, cache_hours=24)
    
    def get_recent_activities_with_details(self, count: int = 10) -> List[Dict]:
        """Get recent activities with all available details"""
        activities = self.get_activities(per_page=count)
        
        detailed_activities = []
        for activity in activities:
            logger.info(f"Fetching details for activity: {activity['name']} ({activity['id']})")
            
            details = self.get_activity_details(activity['id'])
            
            try:
                streams = self.get_activity_streams(activity['id'])
                details['streams'] = streams
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    logger.info(f"No streams available for activity {activity['id']}")
                    details['streams'] = None
                else:
                    logger.error(f"Failed to fetch streams for activity {activity['id']}: {e}")
                    raise StravaAPIError(f"Failed to fetch activity streams: {e}") from e
            except Exception as e:
                logger.error(f"Unexpected error fetching streams for activity {activity['id']}: {e}")
                details['streams'] = None
            
            detailed_activities.append(details)
        
        return detailed_activities
    
    # Wrapper methods for test compatibility
    def get_access_token(self, code: str) -> Dict:
        """Exchange authorization code for access tokens (test compatibility)"""
        return self.exchange_code_for_tokens(code)
    
    def fetch_activities(self, access_token: str, page: int = 1, per_page: int = 200, after: int = None) -> List[Dict]:
        """Fetch activities with pagination support (test compatibility)"""
        # If not paginating, just return single page
        if page > 1 or per_page < 200:
            params = {
                'page': page,
                'per_page': per_page
            }
            if after:
                params['after'] = after
                
            # Use the _api_request method which handles token refresh
            return self._api_request("/athlete/activities", params, cache_hours=0)
        
        # Otherwise do full pagination
        all_activities = []
        current_page = 1
        
        while True:
            params = {
                'page': current_page,
                'per_page': per_page
            }
            if after:
                params['after'] = after
                
            # Use _api_request method which handles token refresh and 401 errors
            activities = self._api_request("/athlete/activities", params, cache_hours=0)
            
            all_activities.extend(activities)
            
            # Continue until we get an empty response
            if not activities:
                break
                
            current_page += 1
            
        return all_activities
    
    def fetch_activity_details(self, activity_id: int, access_token: str) -> Dict:
        """Fetch detailed activity data (test compatibility)"""
        # Use the _api_request method which handles token refresh
        return self._api_request(f"/activities/{activity_id}", cache_hours=24)
    
    def fetch_activity_streams(self, activity_id: int, access_token: str, keys: List[str] = None) -> Dict:
        """Fetch activity streams (test compatibility)"""
        if keys is None:
            keys = ["time", "heartrate", "watts"]
            
        params = {
            "keys": ",".join(keys),
            "key_by_type": True
        }
        
        # Use the _api_request method which handles token refresh
        return self._api_request(f"/activities/{activity_id}/streams", params, cache_hours=24)