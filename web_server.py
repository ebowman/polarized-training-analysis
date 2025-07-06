#!/usr/bin/env python
"""
Web Server for Polarized Training Analysis

Serves the training analysis visualization webpage and provides API endpoints
for accessing workout data.

Usage:
    python web_server.py [--port PORT] [--host HOST]
"""

import argparse
import json
import os
import sys
from datetime import datetime
from flask import Flask, render_template, jsonify, send_from_directory
from training_analysis import TrainingAnalyzer
from strava_client import StravaClient

app = Flask(__name__, template_folder='templates')

# Global variables for caching
cached_data = None
cache_timestamp = None
CACHE_DURATION = 300  # 5 minutes in seconds

def get_training_data(force_refresh=False):
    """Get training data, using cache if available and not expired"""
    global cached_data, cache_timestamp
    
    current_time = datetime.now().timestamp()
    
    # Check if we have cached data and it's still valid
    if not force_refresh and cached_data and cache_timestamp:
        if current_time - cache_timestamp < CACHE_DURATION:
            return cached_data
    
    try:
        # Try to load from existing analysis file first
        analysis_file = 'training_analysis_report.json'
        if os.path.exists(analysis_file):
            with open(analysis_file, 'r') as f:
                data = json.load(f)
                cached_data = data
                cache_timestamp = current_time
                return data
        
        # If no analysis file exists, generate new analysis
        print("No existing analysis found, generating new analysis...")
        
        # Initialize Strava client
        client = StravaClient()
        if not client.access_token:
            raise ValueError("No Strava access token found. Please run: python strava_fetch.py --authorize")
        
        # Get recent activities
        activities = client.get_recent_activities_with_details(30)
        if not activities:
            raise ValueError("No activities found")
        
        # Analyze activities
        analyzer = TrainingAnalyzer()
        analyses = analyzer.analyze_activities(activities)
        
        if not analyses:
            raise ValueError("No analyzable activities found")
        
        # Calculate distribution
        distribution = analyzer.calculate_training_distribution(analyses)
        
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
        
        # Save to file for future use
        with open(analysis_file, 'w') as f:
            json.dump(data, f, indent=2)
        
        cached_data = data
        cache_timestamp = current_time
        return data
        
    except Exception as e:
        print(f"Error getting training data: {e}")
        raise

@app.route('/')
def index():
    """Main page with workout visualizations"""
    return render_template('index.html')

@app.route('/api/workouts')
def api_workouts():
    """API endpoint to get workout data as JSON"""
    try:
        data = get_training_data()
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workouts/refresh')
def api_refresh():
    """API endpoint to force refresh of workout data"""
    try:
        data = get_training_data(force_refresh=True)
        return jsonify(data)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def api_status():
    """API endpoint to check server status"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'cache_age': (datetime.now().timestamp() - cache_timestamp) if cache_timestamp else None
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

def main():
    parser = argparse.ArgumentParser(description="Web server for training analysis visualization")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the server on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind the server to")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("POLARIZED TRAINING ANALYSIS WEB SERVER")
    print("=" * 60)
    print(f"Starting server on http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    try:
        app.run(host=args.host, port=args.port, debug=args.debug)
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
