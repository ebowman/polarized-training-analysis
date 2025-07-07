#!/usr/bin/env python
"""
Strava Data Fetcher

This script fetches your recent workout data from Strava API with aggressive caching
to respect rate limits. It focuses on getting the most recent workouts with all
available detail data.

Usage:
1. First time: python strava_fetch.py --authorize
2. Subsequent runs: python strava_fetch.py
"""

import argparse
import json
import sys
from strava_client import StravaClient

def authorize_strava():
    """Handle the OAuth authorization flow"""
    client = StravaClient()
    
    print("=== Strava Authorization ===")
    print("1. Open this URL in your browser:")
    print(client.get_authorization_url())
    print("\n2. After authorizing, you'll be redirected to a URL like:")
    print("   http://localhost:8080/callback?code=AUTHORIZATION_CODE")
    print("\n3. Copy the code parameter from the URL and paste it here:")
    
    code = input("Enter the authorization code: ").strip()
    
    if not code:
        print("No code provided. Exiting.")
        sys.exit(1)
    
    try:
        token_data = client.exchange_code_for_tokens(code)
        print("\n✅ Authorization successful!")
        print(f"Access token expires at: {token_data.get('expires_at')}")
        return client
    except Exception as e:
        print(f"❌ Authorization failed: {e}")
        sys.exit(1)

def fetch_data(client, num_activities=10):
    """Fetch recent activities with all available data"""
    print(f"\n=== Fetching {num_activities} Most Recent Activities ===")
    
    try:
        athlete = client.get_athlete()
        print(f"Athlete: {athlete['firstname']} {athlete['lastname']}")
        print(f"Total activities: {athlete.get('activity_count', 'N/A')}")
        
        activities = client.get_recent_activities_with_details(num_activities)
        
        print(f"\n✅ Successfully fetched {len(activities)} activities")
        
        for i, activity in enumerate(activities, 1):
            print(f"\n{i}. {activity['name']}")
            print(f"   Date: {activity['start_date']}")
            print(f"   Type: {activity['type']}")
            print(f"   Distance: {activity.get('distance', 0)/1000:.2f} km")
            print(f"   Duration: {activity.get('elapsed_time', 0)//60} minutes")
            print(f"   Elevation: {activity.get('total_elevation_gain', 0)} m")
            
            if activity.get('streams'):
                stream_types = list(activity['streams'].keys())
                print(f"   Available streams: {', '.join(stream_types)}")
            else:
                print("   No stream data available")
        
        output_file = "cache/recent_activities.json"
        with open(output_file, 'w') as f:
            json.dump(activities, f, indent=2)
        
        print(f"\n💾 Full data saved to {output_file}")
        print(f"📁 Cached data stored in cache/ directory")
        
        return activities
        
    except Exception as e:
        print(f"❌ Error fetching data: {e}")
        sys.exit(1)

def main():
    parser = argparse.ArgumentParser(description="Fetch Strava workout data")
    parser.add_argument("--authorize", action="store_true", 
                       help="Perform OAuth authorization")
    parser.add_argument("--count", type=int, default=10,
                       help="Number of recent activities to fetch (default: 10)")
    
    args = parser.parse_args()
    
    if args.authorize:
        client = authorize_strava()
    else:
        try:
            client = StravaClient()
            if not client.access_token:
                print("❌ No access token found. Please run with --authorize first.")
                sys.exit(1)
        except Exception as e:
            print(f"❌ Error initializing client: {e}")
            print("Try running with --authorize to set up authentication.")
            sys.exit(1)
    
    fetch_data(client, args.count)

if __name__ == "__main__":
    main()
