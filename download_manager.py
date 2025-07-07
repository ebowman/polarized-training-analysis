"""Singleton download manager for Strava activities with progress tracking"""
import threading
import time
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from enum import Enum
import json
import os
import requests


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
                print(f"Error notifying subscriber: {e}")
    
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
            
            # Get current cached activities
            current_activities = {}
            if os.path.exists('training_analysis_report.json'):
                with open('training_analysis_report.json', 'r') as f:
                    existing_data = json.load(f)
                    for activity in existing_data.get('activities', []):
                        current_activities[activity['id']] = activity
            
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
                    
                    activities = client.get_activities(per_page=per_page, page=page)
                    
                    if not activities:
                        break
                    
                    # Filter activities within our date range
                    for activity in activities:
                        activity_date = datetime.fromisoformat(activity['start_date'].replace('Z', '+00:00'))
                        if activity_date >= start_date:
                            all_activities.append(activity)
                        else:
                            # We've gone past our date range
                            break
                    
                    # Check if we've gone past our date range
                    if activities and datetime.fromisoformat(activities[-1]['start_date'].replace('Z', '+00:00')) < start_date:
                        break
                    
                    page += 1
                    time.sleep(0.1)  # Rate limiting
                    
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 429:  # Rate limited
                        retry_after = int(e.response.headers.get('X-RateLimit-Limit', 900))
                        self._update_state(
                            status=DownloadStatus.RATE_LIMITED,
                            message=f"Rate limited. Retrying in {retry_after} seconds...",
                            rate_limit_retry_after=retry_after
                        )
                        time.sleep(retry_after)
                        continue
                    else:
                        raise
            
            self._update_state(
                total_activities=len(all_activities),
                message=f"Found {len(all_activities)} activities in date range. Checking for new ones...",
                progress=35
            )
            
            # Identify new activities
            new_activity_ids = []
            for activity in all_activities:
                if activity['id'] not in current_activities:
                    new_activity_ids.append(activity['id'])
            
            if not new_activity_ids:
                # Check if we have minimum required data
                if len(current_activities) < min_days:
                    self._update_state(
                        status=DownloadStatus.ERROR,
                        message=f"Insufficient data: Only {len(current_activities)} activities found, need at least {min_days} days",
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
                            print(f"No streams available for activity {activity_id}")
                            details['streams'] = None
                        elif e.response.status_code == 429:  # Rate limited
                            # Get retry-after from headers (Strava uses different header names)
                            retry_after = 15  # Default to 15 seconds
                            if 'Retry-After' in e.response.headers:
                                retry_after = int(e.response.headers['Retry-After'])
                            elif 'X-RateLimit-Limit' in e.response.headers:
                                # If we hit the 15-minute limit, wait longer
                                retry_after = 900  # 15 minutes
                            
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
                            except:
                                # If still failing, just skip streams
                                print(f"Skipping streams for activity {activity_id} after rate limit")
                                details['streams'] = None
                        else:
                            raise
                    except Exception as e:
                        # For any other stream errors, just skip streams
                        print(f"Error getting streams for activity {activity_id}: {e}")
                        details['streams'] = None
                    
                    detailed_activities.append(details)
                    self.new_activities.append(activity['name'])
                    
                    time.sleep(0.5)  # Increased delay to avoid rate limits
                    
                except requests.exceptions.HTTPError as e:
                    if e.response.status_code == 429:  # Rate limited on activity details
                        # Handle rate limit for activity details
                        retry_after = int(e.response.headers.get('Retry-After', 15))
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
                        print(f"HTTP error downloading activity {activity_id}: {e}")
                        # Skip this activity and continue
                except Exception as e:
                    print(f"Error downloading activity {activity_id}: {e}")
                    # Continue with other activities
            
            # Process and save
            self._update_state(
                status=DownloadStatus.PROCESSING,
                message="Processing activities and regenerating analysis...",
                progress=85
            )
            
            # Merge with existing activities
            all_detailed_activities = list(current_activities.values())
            all_detailed_activities.extend(detailed_activities)
            
            # Sort by date (newest first)
            all_detailed_activities.sort(
                key=lambda x: x['start_date'], 
                reverse=True
            )
            
            # Run analysis using same pattern as web_server.py
            analyzer = TrainingAnalyzer()
            analyses = analyzer.analyze_activities(all_detailed_activities)
            
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
                ]
            }
            
            # Save to file
            with open('training_analysis_report.json', 'w') as f:
                json.dump(data, f, indent=2)
            
            self._update_state(
                status=DownloadStatus.COMPLETED,
                message=f"Successfully downloaded {len(detailed_activities)} new activities!",
                progress=100
            )
            
        except Exception as e:
            print(f"Download error: {e}")
            self._update_state(
                status=DownloadStatus.ERROR,
                message=f"Download failed: {str(e)}",
                error=e,
                progress=100
            )
    
    def start_download(self, client, days_back: int = 30, min_days: int = 14) -> bool:
        """Start download process if not already running"""
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