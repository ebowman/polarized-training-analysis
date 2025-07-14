#!/usr/bin/env python
"""
Cache Manager for Polarized Training Analysis

Handles proper loading and merging of cached activity data.
Ensures all cached activities are included in analysis, not just newly downloaded ones.
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional


class CacheManager:
    """Manages cached Strava activity data"""
    
    def __init__(self, cache_dir: str = 'cache'):
        self.cache_dir = cache_dir
        self.analysis_file = os.path.join(cache_dir, 'training_analysis_report.json')
        
    def load_all_cached_activities(self) -> List[Dict]:
        """
        Load all cached activities from individual cache files.
        Returns a list of all detailed activities found in cache.
        """
        all_activities = []
        
        if not os.path.exists(self.cache_dir):
            return all_activities
        
        # Load individual activity cache files
        for filename in os.listdir(self.cache_dir):
            if filename.startswith('_activities_') and filename.endswith('_.json'):
                try:
                    filepath = os.path.join(self.cache_dir, filename)
                    with open(filepath, 'r') as f:
                        activity = json.load(f)
                        if isinstance(activity, dict) and 'id' in activity:
                            # Try to load associated streams
                            activity_id = activity['id']
                            streams_pattern = f'_activities_{activity_id}_streams_'
                            for stream_file in os.listdir(self.cache_dir):
                                if stream_file.startswith(streams_pattern) and stream_file.endswith('.json'):
                                    try:
                                        stream_path = os.path.join(self.cache_dir, stream_file)
                                        with open(stream_path, 'r') as sf:
                                            streams = json.load(sf)
                                            activity['streams'] = streams
                                            break
                                    except Exception as e:
                                        print(f"Error loading streams for activity {activity_id}: {e}")
                            all_activities.append(activity)
                except Exception as e:
                    print(f"Error loading cache file {filename}: {e}")
                    continue
        
        # Sort by date (newest first)
        all_activities.sort(
            key=lambda x: x.get('start_date', ''), 
            reverse=True
        )
        
        return all_activities
    
    def merge_with_new_activities(self, new_activities: List[Dict]) -> List[Dict]:
        """
        Merge new activities with existing cached activities.
        Prevents duplicates and maintains all historical data.
        """
        # Load all existing cached activities
        existing_activities = self.load_all_cached_activities()
        
        # Create a set of existing activity IDs
        existing_ids = {act['id'] for act in existing_activities}
        
        # Add only truly new activities
        for activity in new_activities:
            if activity.get('id') not in existing_ids:
                existing_activities.append(activity)
        
        # Sort by date (newest first)
        existing_activities.sort(
            key=lambda x: x.get('start_date', ''), 
            reverse=True
        )
        
        return existing_activities
    
    def save_analysis_report(self, report_data: Dict):
        """Save the training analysis report"""
        os.makedirs(self.cache_dir, exist_ok=True)
        with open(self.analysis_file, 'w') as f:
            json.dump(report_data, f, indent=2)
    
    def load_analysis_report(self) -> Optional[Dict]:
        """Load the training analysis report if it exists"""
        if os.path.exists(self.analysis_file):
            try:
                with open(self.analysis_file, 'r') as f:
                    return json.load(f)
            except Exception as e:
                print(f"Error loading analysis report: {e}")
        return None
    
    def ensure_analysis_includes_all_activities(self):
        """
        Ensure the analysis report includes all cached activities.
        This fixes the issue where only newly downloaded activities appear.
        """
        from training_analysis import TrainingAnalyzer
        
        # Load all cached activities
        all_activities = self.load_all_cached_activities()
        
        if not all_activities:
            print("No cached activities found")
            return None
        
        print(f"Found {len(all_activities)} cached activities")
        
        # Analyze all activities
        analyzer = TrainingAnalyzer()
        analyzed_activities, ancillary_work = analyzer.analyze_activities(all_activities)
        
        print(f"Analyzed {len(analyzed_activities)} activities")
        print(f"Found {ancillary_work['strength_training_count']} strength training sessions ({ancillary_work['strength_training_minutes']} minutes)")
        
        # Calculate training distribution
        if analyzed_activities:
            distribution = analyzer.calculate_training_distribution(analyzed_activities)
            
            # Generate summary statistics (method doesn't exist, using distribution instead)
            summary = distribution
            
            # Get workout recommendations
            recommendations = analyzer.get_workout_recommendations(analyzed_activities)
            
            # Create the report data in the expected format
            report_data = {
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
                        'type': rec.workout_type.value if hasattr(rec.workout_type, 'value') else str(rec.workout_type),
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
                        'activity_id': a.activity_id,
                        'name': a.name,
                        'date': a.date,
                        'sport_type': a.sport_type,
                        'duration_minutes': a.duration_minutes,
                        'zone1_percent': a.zone1_percent,
                        'zone2_percent': a.zone2_percent,
                        'zone3_percent': a.zone3_percent,
                        'average_hr': a.average_hr,
                        'average_power': a.average_power
                    }
                    for a in analyzed_activities
                ],
                'all_activities': all_activities  # Include all activities with strength training
            }
            
            # Save the updated report
            self.save_analysis_report(report_data)
            
            return report_data
        
        return None