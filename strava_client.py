import os
import json
import time
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dotenv import load_dotenv

load_dotenv()

class StravaClient:
    def __init__(self, cache_dir: str = "cache"):
        self.client_id = os.getenv("STRAVA_CLIENT_ID")
        self.client_secret = os.getenv("STRAVA_CLIENT_SECRET")
        self.cache_dir = cache_dir
        self.access_token = None
        self.refresh_token = None
        self.token_expires_at = None
        
        if not self.client_id or not self.client_secret:
            raise ValueError("STRAVA_CLIENT_ID and STRAVA_CLIENT_SECRET must be set in .env file")
        
        os.makedirs(self.cache_dir, exist_ok=True)
        self._load_tokens()
    
    def _load_tokens(self):
        """Load tokens from cache file"""
        token_file = os.path.join(self.cache_dir, "tokens.json")
        if os.path.exists(token_file):
            with open(token_file, 'r') as f:
                tokens = json.load(f)
                self.access_token = tokens.get("access_token")
                self.refresh_token = tokens.get("refresh_token")
                self.token_expires_at = tokens.get("expires_at")
    
    def _save_tokens(self):
        """Save tokens to cache file"""
        token_file = os.path.join(self.cache_dir, "tokens.json")
        tokens = {
            "access_token": self.access_token,
            "refresh_token": self.refresh_token,
            "expires_at": self.token_expires_at
        }
        with open(token_file, 'w') as f:
            json.dump(tokens, f)
    
    def get_authorization_url(self) -> str:
        """Get URL for OAuth authorization"""
        scope = "read,activity:read_all,profile:read_all"
        redirect_uri = "http://localhost:8080/callback"
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
        
        response = requests.post(url, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data["refresh_token"]
        self.token_expires_at = token_data["expires_at"]
        
        self._save_tokens()
        return token_data
    
    def refresh_access_token(self) -> Dict:
        """Refresh the access token using refresh token"""
        if not self.refresh_token:
            raise ValueError("No refresh token available")
        
        url = "https://www.strava.com/oauth/token"
        data = {
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "refresh_token": self.refresh_token,
            "grant_type": "refresh_token"
        }
        
        response = requests.post(url, data=data)
        response.raise_for_status()
        
        token_data = response.json()
        self.access_token = token_data["access_token"]
        self.refresh_token = token_data["refresh_token"]
        self.token_expires_at = token_data["expires_at"]
        
        self._save_tokens()
        return token_data
    
    def _ensure_valid_token(self):
        """Ensure we have a valid access token"""
        if not self.access_token:
            raise ValueError("No access token available. Please authorize first.")
        
        if self.token_expires_at and time.time() >= self.token_expires_at:
            print("Token expired, refreshing...")
            self.refresh_access_token()
    
    def _get_cache_file(self, endpoint: str, params: Dict = None) -> str:
        """Generate cache file path for given endpoint and params"""
        param_str = "_".join(f"{k}_{v}" for k, v in sorted((params or {}).items()))
        cache_key = f"{endpoint}_{param_str}".replace("/", "_")
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def _is_cache_valid(self, cache_file: str, max_age_hours: int = 1) -> bool:
        """Check if cache file is valid (exists and not too old)"""
        if not os.path.exists(cache_file):
            return False
        
        file_age = time.time() - os.path.getmtime(cache_file)
        return file_age < (max_age_hours * 3600)
    
    def _api_request(self, endpoint: str, params: Dict = None, cache_hours: int = 1) -> Dict:
        """Make API request with caching"""
        cache_file = self._get_cache_file(endpoint, params)
        
        if self._is_cache_valid(cache_file, cache_hours):
            print(f"Using cached data for {endpoint}")
            with open(cache_file, 'r') as f:
                return json.load(f)
        
        self._ensure_valid_token()
        
        url = f"https://www.strava.com/api/v3{endpoint}"
        headers = {"Authorization": f"Bearer {self.access_token}"}
        
        print(f"Making API request to {endpoint}")
        response = requests.get(url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
        
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
            print(f"Fetching details for activity: {activity['name']} ({activity['id']})")
            
            details = self.get_activity_details(activity['id'])
            
            try:
                streams = self.get_activity_streams(activity['id'])
                details['streams'] = streams
            except requests.exceptions.HTTPError as e:
                if e.response.status_code == 404:
                    print(f"No streams available for activity {activity['id']}")
                    details['streams'] = None
                else:
                    raise
            
            detailed_activities.append(details)
        
        return detailed_activities