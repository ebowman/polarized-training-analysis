#!/usr/bin/env python
"""
Polarized Training Analysis

Main program that downloads training data from Strava and analyzes adherence to 
polarized training approach based on the research paper:
"Training Intensity Distribution in Endurance Athletes: Are We Asking the Right Questions?"

Usage:
    python polarized_training_analysis.py [--days N] [--use-power] [--output report.txt]
"""

import argparse
import json
import sys
import os
from datetime import datetime, timedelta
from strava_client import StravaClient
from training_analysis import TrainingAnalyzer

def main():
    parser = argparse.ArgumentParser(description="Analyze training data for polarized training adherence")
    parser.add_argument("--days", type=int, default=30, 
                       help="Number of days to analyze (default: 30)")
    parser.add_argument("--use-power", action="store_true",
                       help="Use power zones instead of heart rate zones")
    parser.add_argument("--output", type=str, default="training_analysis_report.txt",
                       help="Output file for the analysis report")
    parser.add_argument("--max-hr", type=int, help="Override max heart rate")
    parser.add_argument("--ftp", type=int, help="Override FTP")
    parser.add_argument("--force-refresh", action="store_true",
                       help="Force refresh of training data from Strava")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("POLARIZED TRAINING ANALYSIS")
    print("=" * 60)
    
    try:
        # Initialize Strava client
        print("Initializing Strava client...")
        client = StravaClient()
        
        if not client.access_token:
            print("❌ No Strava access token found.")
            print("Please run: python strava_fetch.py --authorize")
            sys.exit(1)
        
        # Calculate how many activities we need to fetch
        # Estimate based on typical training frequency
        estimated_activities = max(10, args.days // 2)  # Assume training every other day
        
        print(f"Fetching recent {estimated_activities} activities...")
        
        # Get recent activities
        activities = client.get_recent_activities_with_details(estimated_activities)
        
        if not activities:
            print("❌ No activities found.")
            sys.exit(1)
        
        # Filter activities by date range
        cutoff_date = datetime.now() - timedelta(days=args.days)
        recent_activities = []
        
        for activity in activities:
            activity_date = datetime.fromisoformat(activity['start_date'].replace('Z', '+00:00'))
            if activity_date.replace(tzinfo=None) >= cutoff_date:
                recent_activities.append(activity)
        
        print(f"Found {len(recent_activities)} activities in the last {args.days} days")
        
        if not recent_activities:
            print("❌ No activities found in the specified date range.")
            sys.exit(1)
        
        # Initialize training analyzer
        print("Analyzing training data...")
        analyzer = TrainingAnalyzer(
            max_hr=args.max_hr,
            ftp=args.ftp
        )
        
        # Analyze activities
        analyses, ancillary_work = analyzer.analyze_activities(recent_activities)
        
        if not analyses:
            print("❌ No analyzable activities found.")
            print("Activities need heart rate data")
            sys.exit(1)
        
        print(f"Successfully analyzed {len(analyses)} activities")
        if ancillary_work['strength_training_count'] > 0:
            print(f"Found {ancillary_work['strength_training_count']} strength training sessions ({ancillary_work['strength_training_minutes']} minutes)")
        
        # Calculate training distribution
        distribution = analyzer.calculate_training_distribution(analyses)
        
        # Get workout recommendations (uses fixed 14-day window internally)
        recommendations = analyzer.get_workout_recommendations(analyses)
        
        # Generate report
        report = analyzer.generate_report(distribution, analyses)
        
        # Save report to file
        with open(args.output, 'w') as f:
            f.write(report)
        
        # Print summary to console
        print("\n" + "=" * 60)
        print("ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Activities analyzed: {distribution.total_activities}")
        print(f"Total training time: {distribution.total_minutes} minutes")
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
        
        print(f"\n✅ Full report saved to: {args.output}")
        
        # Save analysis data as JSON for further processing
        analysis_data = {
            'config': {
                'max_hr': analyzer.max_hr,
                'ftp': analyzer.ftp,
                'days_analyzed': args.days,
                'use_power': args.use_power
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
                    'zone3_percent': a.zone3_percent
                }
                for a in analyses
            ]
        }
        
        json_output = args.output.replace('.txt', '.json')
        with open(json_output, 'w') as f:
            json.dump(analysis_data, f, indent=2)
        
        print(f"📊 Analysis data saved to: {json_output}")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
