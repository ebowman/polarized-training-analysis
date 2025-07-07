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
import signal
import uuid
import threading
import time
from datetime import datetime
from flask import Flask, render_template, jsonify, request, redirect, session, url_for, Response
from training_analysis import TrainingAnalyzer
from strava_client import StravaClient
from download_manager import DownloadManager

app = Flask(__name__, template_folder='templates')
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key-change-in-production')

# Global variables for caching
cached_data = None
cache_timestamp = None
CACHE_DURATION = 300  # 5 minutes in seconds

# Global variables for AI session management
ai_sessions = {}  # session_id -> {"status": "pending|ready|error", "data": ..., "timestamp": ...}
ai_sessions_lock = threading.Lock()

# AI recommendation engine (initialize with error handling)
ai_engine = None
try:
    from ai_recommendations import AIRecommendationEngine
    ai_engine = AIRecommendationEngine()
    print("✅ AI recommendations enabled")
except Exception as e:
    print(f"⚠️  AI recommendations disabled: {e}")
    ai_engine = None

def cleanup_old_sessions():
    """Clean up old AI sessions (older than 1 hour)"""
    with ai_sessions_lock:
        current_time = time.time()
        expired_sessions = []
        for session_id, session_data in ai_sessions.items():
            if current_time - session_data.get('timestamp', 0) > 3600:  # 1 hour
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del ai_sessions[session_id]

def start_ai_generation(session_id: str, training_data: dict):
    """Start AI recommendation generation in background thread"""
    def generate():
        try:
            with ai_sessions_lock:
                ai_sessions[session_id] = {
                    "status": "pending",
                    "timestamp": time.time()
                }
            
            # Generate AI recommendations
            ai_recommendations = ai_engine.generate_ai_recommendations(training_data)
            
            # Save to history
            ai_engine.save_recommendation_history(ai_recommendations)
            
            # Convert to dict format for JSON response
            recommendations_dict = [
                {
                    'workout_type': rec.workout_type,
                    'duration_minutes': rec.duration_minutes,
                    'description': rec.description,
                    'structure': rec.structure,
                    'reasoning': rec.reasoning,
                    'equipment': rec.equipment,
                    'intensity_zones': rec.intensity_zones,
                    'priority': rec.priority,
                    'generated_at': rec.generated_at
                }
                for rec in ai_recommendations
            ]
            
            with ai_sessions_lock:
                ai_sessions[session_id] = {
                    "status": "ready",
                    "data": {
                        'ai_recommendations': recommendations_dict,
                        'generated_at': datetime.now().isoformat()
                    },
                    "timestamp": time.time()
                }
                
        except Exception as e:
            print(f"Error in background AI generation: {e}")
            with ai_sessions_lock:
                ai_sessions[session_id] = {
                    "status": "error",
                    "error": str(e),
                    "timestamp": time.time()
                }
    
    # Start background thread
    thread = threading.Thread(target=generate)
    thread.daemon = True
    thread.start()
    
    return session_id

def get_zone_calculations():
    """Helper function to calculate zone ranges from .env values"""
    import os
    from dotenv import load_dotenv
    
    load_dotenv()
    
    # Get current configuration
    max_hr = int(os.getenv('MAX_HEART_RATE', 171))
    ftp = int(os.getenv('FTP', 301))
    
    # Calculate HR zone ranges
    hr_zones = {
        'hr1_range': f"{int(max_hr * 0.50)}-{int(max_hr * 0.70)}",
        'hr2_range': f"{int(max_hr * 0.70)}-{int(max_hr * 0.82)}",
        'hr3_range': f"{int(max_hr * 0.82)}-{int(max_hr * 0.87)}",
        'hr4_range': f"{int(max_hr * 0.87)}-{int(max_hr * 0.93)}",
        'hr5_range': f"{int(max_hr * 0.93)}+",
        'hr_zone1_combined': f"{int(max_hr * 0.50)}-{int(max_hr * 0.82)} bpm",
        'hr_zone2_combined': f"{int(max_hr * 0.82)}-{int(max_hr * 0.93)} bpm",
        'hr_zone3_combined': f"{int(max_hr * 0.93)}+ bpm"
    }
    
    # Calculate power zone ranges
    power_zones = {
        'pz1_range': f"0-{int(ftp * 0.55)}W",
        'pz2_range': f"{int(ftp * 0.55)}-{int(ftp * 0.75)}W",
        'pz3_range': f"{int(ftp * 0.75)}-{int(ftp * 0.90)}W",
        'pz3_watts': int(ftp * 0.90),
        'pz4_range': f"{int(ftp * 0.90)}-{int(ftp * 1.05)}W",
        'pz5_range': f"{int(ftp * 1.05)}-{int(ftp * 1.20)}W",
        'pz6_range': f"{int(ftp * 1.20)}+W"
    }
    
    return {
        'max_hr': max_hr,
        'ftp': ftp,
        **hr_zones,
        **power_zones
    }

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
        analysis_file = 'cache/training_analysis_report.json'
        if os.path.exists(analysis_file):
            with open(analysis_file, 'r') as f:
                data = json.load(f)
                cached_data = data
                cache_timestamp = current_time
                return data
        
        # If no analysis file exists, check if download is in progress
        download_manager = DownloadManager()
        if download_manager.is_downloading():
            # Return a placeholder indicating download in progress
            return {
                'downloading': True,
                'download_state': download_manager.get_state(),
                'message': 'Data is currently being downloaded. Please wait...'
            }
        
        # Otherwise, raise an error indicating no data
        raise FileNotFoundError("No training data found. Please download workouts from Strava.")
        
    except Exception as e:
        print(f"Error getting training data: {e}")
        raise

@app.route('/download-workouts')
def download_workouts():
    """Initiate Strava OAuth2 flow to download latest workouts"""
    try:
        client = StravaClient()
        # Check if we already have valid tokens
        if client.access_token:
            try:
                client._ensure_valid_token()
                return redirect(url_for('download_progress'))
            except ValueError:
                # Token invalid, need to re-authorize
                pass
        
        # Generate OAuth URL with our callback
        redirect_uri = request.url_root.rstrip('/') + '/auth/callback'
        auth_url = client.get_authorization_url(redirect_uri)
        return redirect(auth_url)
        
    except Exception as e:
        return jsonify({'error': f'Failed to initiate OAuth: {str(e)}'}), 500

@app.route('/auth/callback')
def auth_callback():
    """Handle OAuth callback from Strava"""
    try:
        code = request.args.get('code')
        error = request.args.get('error')
        
        if error:
            return jsonify({'error': f'OAuth error: {error}'}), 400
        
        if not code:
            return jsonify({'error': 'No authorization code received'}), 400
        
        # Exchange code for tokens
        client = StravaClient()
        token_data = client.exchange_code_for_tokens(code)
        
        # Store success in session for the progress page
        session['auth_success'] = True
        session['athlete_name'] = token_data.get('athlete', {}).get('firstname', 'Athlete')
        
        return redirect(url_for('download_progress'))
        
    except Exception as e:
        return jsonify({'error': f'Failed to complete OAuth: {str(e)}'}), 500

@app.route('/download-progress')
def download_progress():
    """Show download progress page"""
    if not session.get('auth_success'):
        return redirect(url_for('index'))
    
    return render_template('download_progress.html', 
                         athlete_name=session.get('athlete_name', 'Athlete'))

@app.route('/api/download-workouts', methods=['POST'])
def api_download_workouts():
    """API endpoint to start downloading latest workouts from Strava"""
    try:
        client = StravaClient()
        
        # Ensure we have valid tokens
        client._ensure_valid_token()
        
        # Get download manager instance
        download_manager = DownloadManager()
        
        # Try to start download
        if not download_manager.start_download(client, days_back=30, min_days=14):
            return jsonify({
                'status': 'already_downloading',
                'message': 'Download already in progress',
                'state': download_manager.get_state()
            })
        
        return jsonify({
            'status': 'started',
            'message': 'Download started',
            'state': download_manager.get_state()
        })
        
    except Exception as e:
        print(f"Error starting download: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-progress')
def download_progress_stream():
    """SSE endpoint for real-time download progress updates"""
    def generate():
        download_manager = DownloadManager()
        
        # Send initial state
        state = download_manager.get_state()
        yield f"data: {json.dumps(state)}\n\n"
        
        # Subscribe to updates
        last_state = state
        while True:
            current_state = download_manager.get_state()
            
            # Only send if state changed
            if current_state != last_state:
                yield f"data: {json.dumps(current_state)}\n\n"
                last_state = current_state
                
                # If download is complete or errored, stop streaming
                if current_state['status'] in ['completed', 'error', 'idle']:
                    # Clear cache if successful
                    if current_state['status'] == 'completed':
                        global cached_data, cache_timestamp
                        cached_data = None
                        cache_timestamp = None
                    break
            
            time.sleep(0.5)  # Check for updates every 500ms
    
    return Response(generate(), mimetype='text/event-stream')

@app.route('/api/download-status')
def download_status():
    """Get current download status"""
    download_manager = DownloadManager()
    return jsonify(download_manager.get_state())

@app.route('/')
def index():
    """Main page with workout visualizations"""
    # Clean up old sessions periodically
    cleanup_old_sessions()
    
    # Generate AI session if AI engine is available
    ai_session_id = None
    if ai_engine:
        try:
            # Get training data for AI generation
            training_data = get_training_data()
            
            # Generate unique session ID
            ai_session_id = str(uuid.uuid4())
            
            # Start AI generation in background
            start_ai_generation(ai_session_id, training_data)
            
        except Exception as e:
            print(f"Error starting AI generation: {e}")
            ai_session_id = None
    
    return render_template('index.html', ai_session_id=ai_session_id)

@app.route('/zone_mapping_guide')
def zone_mapping_guide():
    """Serve the zone mapping guide with dynamic HR/power calculations"""
    return render_template('zone_mapping_guide.html', **get_zone_calculations())

@app.route('/workout_preferences')
def workout_preferences():
    """Serve the workout preferences with dynamic HR/power calculations"""
    return render_template('workout_preferences.html', **get_zone_calculations())

@app.route('/api/workouts')
def api_workouts():
    """API endpoint to get workout data as JSON"""
    try:
        data = get_training_data()
        return jsonify(data)
    except ValueError as e:
        # Check if it's an auth error
        if "No Strava access token" in str(e):
            return jsonify({
                'error': 'No data available. Please connect to Strava first.',
                'needs_auth': True,
                'auth_url': '/download-workouts'
            }), 401
        return jsonify({'error': str(e)}), 500
    except FileNotFoundError:
        return jsonify({
            'error': 'No training data found. Please download workouts from Strava.',
            'needs_download': True,
            'download_url': '/download-workouts'
        }), 404
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

@app.route('/api/ai-status/<session_id>')
def api_ai_status(session_id):
    """API endpoint to check AI recommendation status"""
    if not ai_engine:
        return jsonify({'error': 'AI recommendations are not available. Check your OpenAI API key in .env file.'}), 503
    
    with ai_sessions_lock:
        session_data = ai_sessions.get(session_id)
    
    if not session_data:
        return jsonify({'error': 'Invalid or expired session ID'}), 404
    
    # Return status without data for pending/error states
    if session_data['status'] == 'pending':
        return jsonify({'status': 'pending'})
    elif session_data['status'] == 'error':
        return jsonify({'status': 'error', 'error': session_data.get('error', 'Unknown error')})
    elif session_data['status'] == 'ready':
        return jsonify({
            'status': 'ready',
            **session_data['data']
        })
    else:
        return jsonify({'error': 'Invalid session status'}), 500

@app.route('/api/ai-recommendations/refresh', methods=['POST'])
def api_ai_recommendations_refresh():
    """API endpoint to generate fresh AI recommendations"""
    if not ai_engine:
        return jsonify({'error': 'AI recommendations are not available. Check your OpenAI API key in .env file.'}), 503
    
    try:
        # Force refresh training data first
        training_data = get_training_data(force_refresh=True)
        
        # Generate new session ID
        session_id = str(uuid.uuid4())
        
        # Start AI generation in background
        start_ai_generation(session_id, training_data)
        
        return jsonify({
            'status': 'started',
            'session_id': session_id,
            'message': 'AI recommendation generation started'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai-recommendations/history')
def api_ai_recommendations_history():
    """API endpoint to get AI recommendation history"""
    if not ai_engine:
        return jsonify({'error': 'AI recommendations are not available. Check your OpenAI API key in .env file.'}), 503
    
    try:
        history = ai_engine.load_recommendation_history()
        return jsonify({
            'history': history,
            'total_entries': len(history)
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def api_status():
    """API endpoint to check server status"""
    return jsonify({
        'status': 'ok',
        'timestamp': datetime.now().isoformat(),
        'cache_age': (datetime.now().timestamp() - cache_timestamp) if cache_timestamp else None,
        'ai_enabled': os.getenv('OPENAI_API_KEY') is not None
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

def cleanup_and_exit():
    """Clean up resources before shutting down"""
    print("\n🛑 Shutting down server...")
    
    # Cancel any running AI generation threads
    with ai_sessions_lock:
        active_sessions = len([s for s in ai_sessions.values() if s.get('status') == 'pending'])
        if active_sessions > 0:
            print(f"⏳ Waiting for {active_sessions} AI generation(s) to complete...")
            # Mark all pending sessions as cancelled
            for session_id, session_data in ai_sessions.items():
                if session_data.get('status') == 'pending':
                    session_data['status'] = 'error'
                    session_data['error'] = 'Server shutdown'
    
    print("✅ Server shutdown complete")
    sys.exit(0)

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    cleanup_and_exit()

def check_and_start_initial_download():
    """Check if we have sufficient data, if not start an automatic download"""
    try:
        # Check if we have any cached data
        if not os.path.exists('cache/training_analysis_report.json'):
            print("📊 No training data found. Starting initial download...")
            start_auto_download()
            return
        
        # Check age and quantity of data
        with open('cache/training_analysis_report.json', 'r') as f:
            data = json.load(f)
            activities = data.get('activities', [])
            
            if len(activities) < 14:
                print(f"📊 Only {len(activities)} activities found. Need at least 14 days for analysis.")
                print("Starting automatic download...")
                start_auto_download()
                return
            
            # Check if data is recent (optional - check oldest activity)
            if activities:
                newest_date = activities[0].get('date', '')
                if newest_date:
                    from datetime import datetime, timedelta
                    newest = datetime.fromisoformat(newest_date.replace('Z', '+00:00'))
                    if datetime.now(newest.tzinfo) - newest > timedelta(days=7):
                        print("📊 Latest activity is more than 7 days old. Starting download...")
                        start_auto_download()
                        return
            
            print(f"✅ Found {len(activities)} activities in cache. Ready to analyze!")
            
    except Exception as e:
        print(f"⚠️  Error checking training data: {e}")
        print("Starting fresh download...")
        start_auto_download()

def start_auto_download():
    """Start automatic download in background"""
    try:
        client = StravaClient()
        
        # Check if we have valid tokens
        if not client.access_token:
            print("⚠️  No Strava authentication found. Please visit /download-workouts to connect.")
            return
        
        try:
            client._ensure_valid_token()
        except:
            print("⚠️  Strava token expired. Please visit /download-workouts to reconnect.")
            return
        
        # Start download
        download_manager = DownloadManager()
        if download_manager.start_download(client, days_back=30, min_days=14):
            print("🚀 Background download started. Check progress at /download-workouts")
            
            # Monitor progress in background
            def monitor_progress():
                while download_manager.is_downloading():
                    state = download_manager.get_state()
                    print(f"📥 Download progress: {state['progress']}% - {state['message']}")
                    time.sleep(5)
                
                state = download_manager.get_state()
                if state['status'] == 'completed':
                    print(f"✅ Download completed! Downloaded {len(state['new_activities'])} new activities.")
                elif state['status'] == 'error':
                    print(f"❌ Download failed: {state['error']}")
            
            monitor_thread = threading.Thread(target=monitor_progress, daemon=True)
            monitor_thread.start()
        else:
            print("⚠️  Download already in progress")
            
    except Exception as e:
        print(f"❌ Failed to start auto-download: {e}")

def main():
    # Set up signal handlers for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    parser = argparse.ArgumentParser(description="Web server for training analysis visualization")
    parser.add_argument("--port", type=int, default=5000, help="Port to run the server on")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind the server to")
    parser.add_argument("--debug", action="store_true", help="Run in debug mode")
    parser.add_argument("--no-auto-download", action="store_true", help="Disable automatic download on startup")
    
    args = parser.parse_args()
    
    print("=" * 60)
    print("POLARIZED TRAINING ANALYSIS WEB SERVER")
    print("=" * 60)
    print(f"Starting server on http://{args.host}:{args.port}")
    print("Press Ctrl+C to stop the server")
    print("=" * 60)
    
    # Check data and start auto-download if needed
    if not args.no_auto_download:
        check_and_start_initial_download()
    else:
        print("ℹ️  Auto-download disabled")
    
    try:
        app.run(host=args.host, port=args.port, debug=args.debug, threaded=True)
    except KeyboardInterrupt:
        cleanup_and_exit()
    except Exception as e:
        print(f"💥 Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
