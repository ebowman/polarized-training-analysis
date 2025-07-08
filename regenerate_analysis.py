#!/usr/bin/env python3
"""
Regenerate training analysis from all cached activities
"""

import json
import os
from datetime import datetime
from training_analysis import TrainingAnalyzer
import glob

def load_all_cached_activities():
    """Load all cached activities from the cache directory"""
    activities = []
    cache_dir = 'cache'
    
    # Find all activity files (not stream files)
    activity_files = glob.glob(os.path.join(cache_dir, '_activities_*.json'))
    activity_files = [f for f in activity_files if 'streams' not in f]
    
    print(f"Found {len(activity_files)} activity files in cache")
    
    for file_path in activity_files:
        try:
            with open(file_path, 'r') as f:
                activity = json.load(f)
                
                # Load corresponding streams file if it exists
                activity_id = activity['id']
                streams_pattern = os.path.join(cache_dir, f'_activities_{activity_id}_streams_*.json')
                streams_files = glob.glob(streams_pattern)
                
                if streams_files:
                    streams_file = streams_files[0]  # Take the first one
                    try:
                        with open(streams_file, 'r') as sf:
                            streams = json.load(sf)
                            activity['streams'] = streams
                    except Exception as e:
                        print(f"Warning: Could not load streams for activity {activity_id}: {e}")
                        activity['streams'] = None
                else:
                    activity['streams'] = None
                
                activities.append(activity)
                
        except Exception as e:
            print(f"Error loading activity file {file_path}: {e}")
    
    # Sort by date (newest first)
    activities.sort(key=lambda x: x.get('start_date', ''), reverse=True)
    
    return activities

def main():
    print("=" * 60)
    print("REGENERATING TRAINING ANALYSIS FROM ALL CACHED ACTIVITIES")
    print("=" * 60)
    
    # Load all cached activities
    activities = load_all_cached_activities()
    
    if not activities:
        print("❌ No activities found in cache directory")
        return
    
    print(f"Loaded {len(activities)} activities from cache")
    
    # Show date range
    if activities:
        newest_date = activities[0]['start_date']
        oldest_date = activities[-1]['start_date']
        print(f"Date range: {oldest_date[:10]} to {newest_date[:10]}")
    
    # Initialize training analyzer
    print("\nAnalyzing training data...")
    analyzer = TrainingAnalyzer()
    
    # Analyze activities
    analyses = analyzer.analyze_activities(activities)
    
    if not analyses:
        print("❌ No analyzable activities found.")
        print("Activities need heart rate data or power data for analysis")
        return
    
    print(f"Successfully analyzed {len(analyses)} activities")
    
    # Calculate training distribution
    distribution = analyzer.calculate_training_distribution(analyses)
    
    # Get workout recommendations
    recommendations = analyzer.get_workout_recommendations(analyses)
    
    # Create the same format as the download_manager produces
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
    output_file = 'cache/training_analysis_report.json'
    with open(output_file, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✅ Training analysis regenerated successfully!")
    print(f"📊 Report saved to: {output_file}")
    
    # Print summary
    print("\n" + "=" * 60)
    print("ANALYSIS SUMMARY")
    print("=" * 60)
    print(f"Activities analyzed: {distribution.total_activities}")
    print(f"Total training time: {distribution.total_minutes} minutes ({distribution.total_minutes/60:.1f} hours)")
    print(f"Zone 1 (Low): {distribution.zone1_percent:.1f}% [Target: 80%]")
    print(f"Zone 2 (Threshold): {distribution.zone2_percent:.1f}% [Target: 10%]")
    print(f"Zone 3 (High): {distribution.zone3_percent:.1f}% [Target: 10%]")
    print(f"Adherence Score: {distribution.adherence_score:.1f}/100")
    
    print(f"\nGeneral Recommendations:")
    for i, rec in enumerate(distribution.recommendations[:3], 1):
        print(f"  {i}. {rec}")
    
    print(f"\n🎯 Next Workout Recommendations (based on last 14 days):")
    for i, rec in enumerate(recommendations, 1):
        duration_hours = rec.duration_minutes // 60
        duration_mins = rec.duration_minutes % 60
        duration_str = f"{duration_hours}h {duration_mins}m" if duration_hours > 0 else f"{rec.duration_minutes}m"
        
        zone_icon = "🟢" if rec.primary_zone == 1 else "🟡" if rec.primary_zone == 2 else "🔴"
        priority_icon = "🚨" if rec.priority == "high" else "⚠️" if rec.priority == "medium" else "💡"
        
        print(f"\n  {i}. {priority_icon} {zone_icon} {rec.description} ({duration_str})")
        print(f"     Structure: {rec.structure}")
        print(f"     Why: {rec.reasoning}")
    
    print(f"\n🔄 You can now refresh the web interface to see the updated analysis.")

if __name__ == "__main__":
    main()