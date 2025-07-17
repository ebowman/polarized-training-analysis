"""Singleton download manager for Strava activities with progress tracking"""
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from enum import Enum
import json
import os
import requests
from cache_manager import CacheManager
from logging_config import get_logger, StravaAPIError, CacheError

logger = get_logger(__name__)


class DownloadStatus(Enum):
    IDLE = "idle"
    INITIALIZING = "initializing"
    DOWNLOADING = "downloading"
    PROCESSING = "processing"
    COMPLETED = "completed"
    ERROR = "error"
    RATE_LIMITED = "rate_limited"


class DownloadManager:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        self.status = DownloadStatus.IDLE
        self.progress = 0
        self.total_activities = 0
        self.processed_activities = 0
        self.current_activity_name = ""
        self.message = ""
        self.new_activities = []
        self.error = None
        self.download_thread = None
        self.subscribers = []
        self.rate_limit_retry_after = None
        self._initialized = True
    
    def add_subscriber(self, subscriber):
        """Add a subscriber function that will be called on updates"""
        self.subscribers.append(subscriber)
    
    def remove_subscriber(self, subscriber):
        """Remove a subscriber"""
        if subscriber in self.subscribers:
            self.subscribers.remove(subscriber)
    
    def _notify_subscribers(self):
        """Notify all subscribers of state change"""
        state = self.get_state()
        for subscriber in self.subscribers[:]:  # Copy to avoid modification during iteration
            try:
                subscriber(state)
            except Exception as e:
                logger.error(f"Error notifying subscriber: {e}", exc_info=True)
    
    def get_state(self) -> Dict[str, Any]:
        """Get current download state"""
        return {
            "status": self.status.value,
            "progress": self.progress,
            "total_activities": self.total_activities,
            "processed_activities": self.processed_activities,
            "current_activity_name": self.current_activity_name,
            "message": self.message,
            "new_activities": self.new_activities,
            "error": str(self.error) if self.error else None,
            "rate_limit_retry_after": self.rate_limit_retry_after
        }
    
    def is_downloading(self) -> bool:
        """Check if currently downloading"""
        return self.status in [
            DownloadStatus.INITIALIZING, 
            DownloadStatus.DOWNLOADING, 
            DownloadStatus.PROCESSING,
            DownloadStatus.RATE_LIMITED
        ]
    
    def _update_state(self, **kwargs):
        """Update state and notify subscribers"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self._notify_subscribers()
    
    def _download_worker(self, client, days_back: int = 30, min_days: int = 14):
        """Worker thread for downloading activities"""
        try:
            from strava_client import StravaClient
            from training_analysis import TrainingAnalyzer
            
            self._update_state(
                status=DownloadStatus.INITIALIZING,
                message="Checking existing activities...",
                progress=0
            )
            
            # Get current cached activities IDs by checking actual cache files
            current_activity_ids = set()
            cache_dir = 'cache'
            if os.path.exists(cache_dir):
                import glob
                activity_files = glob.glob(os.path.join(cache_dir, '_activities_*.json'))
                activity_files = [f for f in activity_files if 'streams' not in f]
                
                for file_path in activity_files:
                    try:
                        # Extract activity ID from filename
                        filename = os.path.basename(file_path)
                        # Format: _activities_12345_.json
                        activity_id_str = filename.replace('_activities_', '').replace('_.json', '')
                        if activity_id_str.isdigit():
                            current_activity_ids.add(int(activity_id_str))
                    except Exception as e:
                        logger.warning(f"Could not parse activity ID from {file_path}: {e}")
            
            logger.debug(f"Found {len(current_activity_ids)} activities in cache directory")
            
            # Calculate date range (use UTC to match Strava's timezone)
            end_date = datetime.now(timezone.utc)
            start_date = end_date - timedelta(days=days_back)
            
            self._update_state(
                message=f"Fetching activities from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}...",
                progress=5
            )
            
            # Fetch activities page by page until we reach our date range
            all_activities = []
            page = 1
            per_page = 30
            
            while True:
                try:
                    self._update_state(
                        message=f"Fetching activities page {page}...",
                        progress=min(10 + (page - 1) * 5, 30)
                    )
                    
                    # Use get_activities which goes through _api_request and handles token refresh
                    activities = client.get_activities(per_page=per_page, page=page)
                    
                    if not activities:
                        break
                    
                    # Log first page for debugging
                    if page == 1:
                        logger.debug(f"First page has {len(activities)} activities")
                        if activities:
                            newest = datetime.fromisoformat(activities[0]['start_date'].replace('Z', '+00:00'))
                            oldest = datetime.fromisoformat(activities[-1]['start_date'].replace('Z', '+00:00'))
                            logger.debug(f"Newest activity: {activities[0]['name']} at {newest}")
                            logger.debug(f"Oldest on page: {activities[-1]['name']} at {oldest}")
                            logger.debug(f"Date range: {start_date} to {end_date}")
                    
                    # Filter activities within our date range
                    found_old_activity = False
                    for activity in activities:
                        activity_date = datetime.fromisoformat(activity['start_date'].replace('Z', '+00:00'))
                        if activity_date >= start_date:
                            all_activities.append(activity)
                        else:
                            # We've gone past our date range
                            found_old_activity = True
                    
                    # Check if ALL activities on this page are past our date range
                    if found_old_activity and len([a for a in activities 
                        if datetime.fromisoformat(a['start_date'].replace('Z', '+00:00')) >= start_date]) == 0:
                        break
                    
                    page += 1
                    time.sleep(0.1)  # Rate limiting
                    
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 429:  # Rate limited
                        retry_after = int(e.response.headers.get('X-RateLimit-Limit', 900))
                        logger.warning(f"Rate limited while fetching activities page {page}, retrying in {retry_after} seconds")
                        self._update_state(
                            status=DownloadStatus.RATE_LIMITED,
                            message=f"Rate limited. Retrying in {retry_after} seconds...",
                            rate_limit_retry_after=retry_after
                        )
                        time.sleep(retry_after)
                        continue
                    else:
                        logger.error(f"HTTP error fetching activities page {page}: {e}")
                        raise StravaAPIError(f"Failed to fetch activities page {page}: {e}") from e
            
            self._update_state(
                total_activities=len(all_activities),
                message=f"Found {len(all_activities)} activities in date range. Checking for new ones...",
                progress=35
            )
            
            # Identify new activities
            new_activity_ids = []
            for activity in all_activities:
                if activity['id'] not in current_activity_ids:
                    new_activity_ids.append(activity['id'])
            
            logger.info(f"Found {len(all_activities)} activities from Strava in date range")
            logger.info(f"Have {len(current_activity_ids)} activities in cache")
            logger.info(f"Found {len(new_activity_ids)} new activities")
            
            if not new_activity_ids:
                # Check if we have minimum required data
                if len(current_activity_ids) < min_days:
                    self._update_state(
                        status=DownloadStatus.ERROR,
                        message=f"Insufficient data: Only {len(current_activity_ids)} activities found, need at least {min_days} days",
                        progress=100,
                        error="Insufficient data for analysis"
                    )
                    return
                
                self._update_state(
                    status=DownloadStatus.COMPLETED,
                    message="No new activities found. Cache is up to date.",
                    progress=100
                )
                return
            
            self._update_state(
                status=DownloadStatus.DOWNLOADING,
                message=f"Downloading {len(new_activity_ids)} new activities...",
                progress=40
            )
            
            # Download detailed data for new activities
            detailed_activities = []
            for idx, activity_id in enumerate(new_activity_ids):
                # Find activity in our list
                activity = next(a for a in all_activities if a['id'] == activity_id)
                
                self._update_state(
                    current_activity_name=activity['name'],
                    processed_activities=idx + 1,
                    message=f"Downloading: {activity['name']} ({idx + 1}/{len(new_activity_ids)})",
                    progress=40 + int((idx / len(new_activity_ids)) * 40)
                )
                
                try:
                    # Get detailed activity data
                    details = client.get_activity_details(activity_id)
                    
                    # Try to get streams
                    try:
                        streams = client.get_activity_streams(activity_id)
                        details['streams'] = streams
                    except requests.exceptions.HTTPError as e:
                        if e.response.status_code == 404:
                            logger.info(f"No streams available for activity {activity_id}")
                            details['streams'] = None
                        elif e.response.status_code == 429:  # Rate limited
                            # Get retry-after from headers (Strava uses different header names)
                            retry_after = 15  # Default to 15 seconds
                            if 'Retry-After' in e.response.headers:
                                retry_after = int(e.response.headers['Retry-After'])
                            elif 'X-RateLimit-Limit' in e.response.headers:
                                # If we hit the 15-minute limit, wait longer
                                retry_after = 900  # 15 minutes
                            
                            logger.warning(f"Rate limited while fetching streams for activity {activity_id}, waiting {retry_after} seconds")
                            self._update_state(
                                status=DownloadStatus.RATE_LIMITED,
                                message=f"Rate limited. Waiting {retry_after} seconds...",
                                rate_limit_retry_after=retry_after
                            )
                            
                            # Wait with progress updates
                            for i in range(retry_after):
                                self._update_state(
                                    message=f"Rate limited. Waiting {retry_after - i} seconds...",
                                    rate_limit_retry_after=retry_after - i
                                )
                                time.sleep(1)
                            
                            # Retry this activity
                            try:
                                streams = client.get_activity_streams(activity_id)
                                details['streams'] = streams
                                self._update_state(
                                    status=DownloadStatus.DOWNLOADING,
                                    message=f"Resumed: {activity['name']} ({idx + 1}/{len(new_activity_ids)})",
                                    rate_limit_retry_after=None
                                )
                            except Exception as retry_error:
                                # If still failing, just skip streams
                                logger.warning(f"Skipping streams for activity {activity_id} after rate limit retry: {retry_error}")
                                details['streams'] = None
                        else:
                            logger.error(f"HTTP error fetching streams for activity {activity_id}: {e}")
                            raise StravaAPIError(f"Failed to fetch streams for activity {activity_id}: {e}") from e
                    except Exception as e:
                        # For any other stream errors, just skip streams
                        logger.warning(f"Error getting streams for activity {activity_id}: {e}")
                        details['streams'] = None
                    
                    detailed_activities.append(details)
                    self.new_activities.append(activity['name'])
                    
                    time.sleep(0.5)  # Increased delay to avoid rate limits
                    
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 429:  # Rate limited on activity details
                        # Handle rate limit for activity details
                        retry_after = int(e.response.headers.get('Retry-After', 15))
                        logger.warning(f"Rate limited on activity details for {activity_id}, waiting {retry_after} seconds")
                        self._update_state(
                            status=DownloadStatus.RATE_LIMITED,
                            message=f"Rate limited on activity details. Waiting {retry_after} seconds...",
                            rate_limit_retry_after=retry_after
                        )
                        
                        for i in range(retry_after):
                            self._update_state(
                                message=f"Rate limited. Waiting {retry_after - i} seconds...",
                                rate_limit_retry_after=retry_after - i
                            )
                            time.sleep(1)
                        
                        # Retry the whole activity
                        idx -= 1  # Retry this activity
                        continue
                    else:
                        logger.error(f"HTTP error downloading activity {activity_id}: {e}")
                        # Skip this activity and continue
                except Exception as e:
                    logger.error(f"Error downloading activity {activity_id}: {e}")
                    # Continue with other activities
            
            # Process and save
            self._update_state(
                status=DownloadStatus.PROCESSING,
                message="Processing activities and regenerating analysis...",
                progress=85
            )
            
            # For full analysis, we need to get ALL activities with details, not just new ones
            # This is because the cached data is simplified and doesn't have all the raw data
            logger.info(f"Downloaded {len(detailed_activities)} new activities")
            logger.info(f"Need to fetch all {len(all_activities)} activities for complete analysis")
            
            # Use CacheManager to properly merge new activities with all cached ones
            cache_manager = CacheManager()
            all_detailed_activities = cache_manager.merge_with_new_activities(detailed_activities)
            
            # Sort by date (newest first)
            all_detailed_activities.sort(
                key=lambda x: x.get('start_date', ''), 
                reverse=True
            )
            
            # Run analysis using same pattern as web_server.py
            analyzer = TrainingAnalyzer()
            analyses, ancillary_work = analyzer.analyze_activities(all_detailed_activities)
            
            if not analyses:
                raise ValueError("No analyzable activities found")
            
            # Calculate distribution
            distribution = analyzer.calculate_training_distribution(analyses)
            
            # Get workout recommendations
            recommendations = analyzer.get_workout_recommendations(analyses)
            
            # Format data for web interface
            data = {
                'config': {
                    'max_hr': analyzer.max_hr,
                    'ftp': analyzer.ftp,
                    'lthr': analyzer.lthr,
                    'ftp_power': analyzer.ftp_power,
                    'hr_zones': {
                        'zone1_max': analyzer.hr_zones.zone1_max,
                        'zone2_max': analyzer.hr_zones.zone2_max,
                        'zone3_max': analyzer.hr_zones.zone3_max,
                        'zone4_max': analyzer.hr_zones.zone4_max,
                        'zone5a_max': analyzer.hr_zones.zone5a_max,
                        'zone5b_max': analyzer.hr_zones.zone5b_max,
                        'zone5c_min': analyzer.hr_zones.zone5c_min,
                        'lthr': analyzer.hr_zones.lthr
                    },
                    'power_zones': {
                        'zone1_max': analyzer.power_zones.zone1_max,
                        'zone2_max': analyzer.power_zones.zone2_max,
                        'zone3_max': analyzer.power_zones.zone3_max,
                        'zone4_max': analyzer.power_zones.zone4_max,
                        'zone5_max': analyzer.power_zones.zone5_max,
                        'zone6_max': analyzer.power_zones.zone6_max,
                        'zone7_min': analyzer.power_zones.zone7_min,
                        'ftp': analyzer.power_zones.ftp
                    },
                    'generated_at': datetime.now().isoformat()
                },
                'distribution': {
                    'total_activities': distribution.total_activities,
                    'total_minutes': distribution.total_minutes,
                    'zone1_percent': distribution.zone1_percent,
                    'zone2_percent': distribution.zone2_percent,
                    'zone3_percent': distribution.zone3_percent,
                    'adherence_score': distribution.adherence_score,
                    'recommendations': distribution.recommendations
                },
                'ancillary_work': ancillary_work,
                'workout_recommendations': [
                    {
                        'workout_type': rec.workout_type.value,
                        'primary_zone': rec.primary_zone,
                        'duration_minutes': rec.duration_minutes,
                        'description': rec.description,
                        'structure': rec.structure,
                        'reasoning': rec.reasoning,
                        'priority': rec.priority
                    }
                    for rec in recommendations
                ],
                'activities': [
                    {
                        'id': a.activity_id,
                        'name': a.name,
                        'date': a.date,
                        'duration_minutes': a.duration_minutes,
                        'zone1_percent': a.zone1_percent,
                        'zone2_percent': a.zone2_percent,
                        'zone3_percent': a.zone3_percent,
                        'average_hr': a.average_hr,
                        'average_power': a.average_power
                    }
                    for a in analyses
                ],
                'all_activities': all_detailed_activities  # Include all activities with strength training
            }
            
            # Save to file using CacheManager
            cache_manager.save_analysis_report(data)
            
            self._update_state(
                status=DownloadStatus.COMPLETED,
                message=f"Successfully downloaded {len(detailed_activities)} new activities!",
                progress=100
            )
            
        except Exception as e:
            logger.error(f"Download error: {e}", exc_info=True)
            self._update_state(
                status=DownloadStatus.ERROR,
                message=f"Download failed: {str(e)}",
                error=e,
                progress=100
            )
    
    def start_download(self, client, days_back: int = 30, min_days: int = 14, force_check: bool = False) -> bool:
        """Start download process if not already running
        
        Args:
            client: StravaClient instance
            days_back: Number of days to look back
            min_days: Minimum number of activities required
            force_check: If True, always fetch from Strava even if we think we're up to date
        """
        with self._lock:
            if self.is_downloading():
                return False
            
            # Reset state
            self.status = DownloadStatus.INITIALIZING
            self.progress = 0
            self.processed_activities = 0
            self.total_activities = 0
            self.current_activity_name = ""
            self.message = "Starting download..."
            self.new_activities = []
            self.error = None
            self.rate_limit_retry_after = None
            
            # Start worker thread
            self.download_thread = threading.Thread(
                target=self._download_worker,
                args=(client, days_back, min_days),
                daemon=True
            )
            self.download_thread.start()
            
            return True
    
    def reset_state(self):
        """Reset download manager to idle state"""
        with self._lock:
            self.status = DownloadStatus.IDLE
            self.progress = 0
            self.processed_activities = 0
            self.total_activities = 0
            self.current_activity_name = ""
            self.message = ""
            self.new_activities = []
            self.error = None
            self.rate_limit_retry_after = None