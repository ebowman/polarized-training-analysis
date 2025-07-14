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
from flask import Flask, render_template, jsonify, request, redirect, session, url_for, Response, make_response
from training_analysis import TrainingAnalyzer
from strava_client import StravaClient
from download_manager import DownloadManager
from cache_manager import CacheManager

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
    print("🔄 Initializing AI engine at startup...")
    from ai_recommendations import AIRecommendationEngine
    ai_engine = AIRecommendationEngine()
    print("✅ AI recommendations enabled")
except Exception as e:
    print(f"⚠️  AI recommendations disabled: {type(e).__name__}: {e}")
    import traceback
    traceback.print_exc()
    ai_engine = None

# Global strava client instance (for test compatibility)
strava_client = None
if not app.config.get('TESTING'):
    try:
        strava_client = StravaClient()
    except Exception as e:
        print(f"⚠️  Strava client initialization failed: {e}")
        strava_client = None

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
                    'pathway_name': rec.pathway_name,
                    'today': {
                        'workout_type': rec.today.workout_type,
                        'duration_minutes': rec.today.duration_minutes,
                        'description': rec.today.description,
                        'structure': rec.today.structure,
                        'reasoning': rec.today.reasoning,
                        'equipment': rec.today.equipment,
                        'intensity_zones': rec.today.intensity_zones
                    },
                    'tomorrow': {
                        'workout_type': rec.tomorrow.workout_type,
                        'duration_minutes': rec.tomorrow.duration_minutes,
                        'description': rec.tomorrow.description,
                        'structure': rec.tomorrow.structure,
                        'reasoning': rec.tomorrow.reasoning,
                        'equipment': rec.tomorrow.equipment,
                        'intensity_zones': rec.tomorrow.intensity_zones
                    },
                    'overall_reasoning': rec.overall_reasoning,
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
            error_message = str(e)
            
            # Provide more specific error messages
            if "openai" in error_message.lower() and ("503" in error_message or "service" in error_message):
                error_message = "OpenAI service is temporarily unavailable. Please try again in a few moments."
            elif "rate limit" in error_message.lower():
                error_message = "OpenAI rate limit reached. Please wait a minute before trying again."
            elif "api key" in error_message.lower():
                error_message = "Invalid OpenAI API key. Please check your .env file configuration."
            elif "timeout" in error_message.lower():
                error_message = "Request timed out. The AI service might be overloaded. Please try again."
            
            with ai_sessions_lock:
                ai_sessions[session_id] = {
                    "status": "error",
                    "error": error_message,
                    "timestamp": time.time()
                }
    
    # Start background thread
    thread = threading.Thread(target=generate)
    thread.daemon = True
    thread.start()
    
    return session_id

def start_pathway_ai_generation(session_id: str, training_data: dict, pathway_context: dict):
    """Start AI recommendation generation for recovery pathways with context"""
    def generate():
        try:
            with ai_sessions_lock:
                ai_sessions[session_id] = {
                    "status": "pending",
                    "timestamp": time.time()
                }
            
            # Generate AI recommendations with context
            pathway_recommendations = ai_engine.generate_pathway_recommendations(training_data, pathway_context)
            
            # Convert to dict format
            recommendations_dict = {}
            for pathway_type, rec in pathway_recommendations.items():
                if rec:
                    recommendations_dict[pathway_type] = {
                        'workout_type': rec.workout_type,
                        'duration_minutes': rec.duration_minutes,
                        'description': rec.description,
                        'structure': rec.structure,
                        'reasoning': rec.reasoning,
                        'equipment': rec.equipment,
                        'intensity_zones': rec.intensity_zones,
                        'priority': rec.priority
                    }
            
            with ai_sessions_lock:
                ai_sessions[session_id] = {
                    "status": "ready",
                    "data": {
                        'pathway_recommendations': recommendations_dict,
                        'generated_at': datetime.now().isoformat()
                    },
                    "timestamp": time.time()
                }
                
        except Exception as e:
            print(f"Error in pathway AI generation: {e}")
            error_message = str(e)
            
            # Provide more specific error messages
            if "service" in error_message.lower() and "unavailable" in error_message.lower():
                error_message = "AI service is temporarily unavailable. Please try again in a few moments."
            elif "rate limit" in error_message.lower():
                error_message = "AI rate limit reached. Please wait a minute before trying again."
            
            with ai_sessions_lock:
                ai_sessions[session_id] = {
                    "status": "error",
                    "error": error_message,
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
        # First, try to load existing analysis report
        cache_manager = CacheManager()
        existing_report = cache_manager.load_analysis_report()
        
        if existing_report:
            # Verify it has the expected structure
            if 'distribution' in existing_report and 'activities' in existing_report:
                # Add last 7 days ancillary work if not present
                if 'ancillary_work_7days' not in existing_report:
                    # Load all cached activities to calculate 7-day ancillary work
                    all_activities = cache_manager.load_all_cached_activities()
                    analyzer = TrainingAnalyzer()
                    existing_report['ancillary_work_7days'] = analyzer.filter_ancillary_work(all_activities, days=7)
                
                # Add all_activities if not present (for showing strength training in the list)
                if 'all_activities' not in existing_report:
                    existing_report['all_activities'] = cache_manager.load_all_cached_activities()
                
                cached_data = existing_report
                cache_timestamp = current_time
                return existing_report
        
        # If no valid report exists, try to regenerate from cached activities
        report_data = cache_manager.ensure_analysis_includes_all_activities()
        
        if report_data:
            cached_data = report_data
            cache_timestamp = current_time
            return report_data
        
        # If no cached activities exist, check if download is in progress
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
        # Use global strava_client for test compatibility
        if strava_client is None:
            return jsonify({'error': 'Strava client not initialized'}), 500
            
        # Check if we already have valid tokens
        if strava_client.access_token:
            try:
                strava_client._ensure_valid_token()
                # Set session state for users with existing valid tokens
                session['auth_success'] = True
                session['athlete_name'] = 'Athlete'  # Default name for existing tokens
                # Copy tokens to session so download API can use them
                session['strava_access_token'] = strava_client.access_token
                session['strava_refresh_token'] = strava_client.refresh_token
                session['strava_expires_at'] = strava_client.token_expires_at
                session.permanent = True
                return redirect(url_for('download_progress'))
            except Exception as e:
                # Token invalid or refresh failed, need to re-authorize
                print(f"Token validation/refresh failed: {e}")
                # Clear invalid tokens
                strava_client.access_token = None
                strava_client.refresh_token = None
                strava_client.token_expires_at = None
        
        # Generate OAuth URL with our callback
        redirect_uri = request.url_root.rstrip('/') + '/strava-callback'
        auth_url = strava_client.get_authorization_url(redirect_uri)
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
        session['strava_access_token'] = token_data.get('access_token')  # For auth checks
        session['strava_refresh_token'] = token_data.get('refresh_token')  # For token refresh
        session['strava_expires_at'] = token_data.get('expires_at')  # For expiration check
        session.permanent = True  # Make session persistent
        
        # Debug logging
        print(f"OAuth callback - Setting session data:")
        print(f"  - auth_success: {session.get('auth_success')}")
        print(f"  - athlete_name: {session.get('athlete_name')}")
        print(f"  - access_token exists: {bool(session.get('strava_access_token'))}")
        print(f"  - refresh_token exists: {bool(session.get('strava_refresh_token'))}")
        print(f"  - expires_at: {session.get('strava_expires_at')}")
        
        return redirect(url_for('download_progress'))
        
    except Exception as e:
        return jsonify({'error': f'Failed to complete OAuth: {str(e)}'}), 500

@app.route('/strava-callback')
def strava_callback():
    """Handle OAuth callback from Strava (test compatibility route)"""
    # Check for error parameter
    error = request.args.get('error')
    if error:
        return jsonify({'error': f'OAuth error: {error}'}), 400
    
    # Get authorization code
    code = request.args.get('code')
    if not code:
        return jsonify({'error': 'No authorization code received'}), 400
    
    try:
        # Use global strava_client for test compatibility
        if strava_client is None:
            return jsonify({'error': 'Strava client not initialized'}), 500
            
        # Exchange code for tokens
        token_data = strava_client.get_access_token(code) if hasattr(strava_client, 'get_access_token') else strava_client.exchange_code_for_tokens(code)
        
        # Store in session
        session['strava_access_token'] = token_data.get('access_token')
        session['strava_refresh_token'] = token_data.get('refresh_token')
        session['strava_expires_at'] = token_data.get('expires_at')  # Add missing expires_at
        session['athlete_id'] = token_data.get('athlete', {}).get('id')
        session['auth_success'] = True
        session['athlete_name'] = token_data.get('athlete', {}).get('firstname', 'Athlete')
        session.permanent = True  # Make session persistent
        
        # Debug logging
        print(f"Strava callback - Setting session data:")
        print(f"  - auth_success: {session.get('auth_success')}")
        print(f"  - athlete_name: {session.get('athlete_name')}")
        print(f"  - access_token exists: {bool(session.get('strava_access_token'))}")
        print(f"  - refresh_token exists: {bool(session.get('strava_refresh_token'))}")
        print(f"  - expires_at: {session.get('strava_expires_at')}")
        
        return redirect(url_for('download_progress'))
        
    except Exception as e:
        return jsonify({'error': f'Failed to complete OAuth: {str(e)}'}), 500

@app.route('/download-progress')
def download_progress():
    """Show download progress page"""
    # Debug logging
    print(f"Download progress page - Session check:")
    print(f"  - Session keys: {list(session.keys())}")
    print(f"  - auth_success: {session.get('auth_success')}")
    print(f"  - athlete_name: {session.get('athlete_name')}")
    print(f"  - access_token exists: {bool(session.get('strava_access_token'))}")
    
    if not session.get('auth_success'):
        return redirect(url_for('index'))
    
    return render_template('download_progress.html', 
                         athlete_name=session.get('athlete_name', 'Athlete'))

@app.route('/api/download-workouts', methods=['POST'])
def api_download_workouts():
    """API endpoint to start downloading latest workouts from Strava"""
    # Debug logging
    print(f"Download API - Session check:")
    print(f"  - Session keys: {list(session.keys())}")
    print(f"  - auth_success: {session.get('auth_success')}")
    print(f"  - athlete_name: {session.get('athlete_name')}")
    print(f"  - access_token exists: {bool(session.get('strava_access_token'))}")
    print(f"  - refresh_token exists: {bool(session.get('strava_refresh_token'))}")
    print(f"  - expires_at: {session.get('strava_expires_at')}")
    
    # Check if user is authorized
    if not session.get('strava_access_token'):
        return jsonify({'error': 'Not authenticated with Strava'}), 401
        
    try:
        # Get request data
        data = request.get_json() or {}
        days = data.get('days', 30)
        force = data.get('force', False)
        
        # Create a StravaClient with the session token
        from strava_client import StravaClient
        client = StravaClient()
        # Override the cached token with the session token
        access_token = session.get('strava_access_token')
        refresh_token = session.get('strava_refresh_token')
        expires_at = session.get('strava_expires_at')
        
        if access_token:
            client.access_token = access_token
            if refresh_token:
                client.refresh_token = refresh_token
            if expires_at:
                client.token_expires_at = expires_at
            # Save tokens to cache so subsequent operations work
            client._save_tokens()
            print(f"Setup client with tokens: access={bool(access_token)}, refresh={bool(refresh_token)}, expires_at={expires_at}")
        
        # Get download manager instance
        download_manager = DownloadManager()
        
        # Start the download
        started = download_manager.start_download(client, days_back=days, force_check=force)
        
        if not started:
            # Already downloading
            return jsonify({
                'status': 'already_downloading',
                'state': download_manager.get_state()
            })
        
        return jsonify({
            'status': 'started',
            'message': 'Download started'
        })
        
    except Exception as e:
        print(f"Error starting download: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/download-progress/<download_id>')
def api_download_progress(download_id):
    """Get download progress for a specific download"""
    download_manager = DownloadManager()
    progress = download_manager.get_progress(download_id)
    
    if progress is None:
        return jsonify({'error': 'Download not found'}), 404
    
    return jsonify(progress)

@app.route('/api/reset-download', methods=['POST'])
def api_reset_download():
    """Reset download state to allow new downloads"""
    try:
        download_manager = DownloadManager()
        download_manager.reset_state()
        return jsonify({
            'status': 'success',
            'message': 'Download state reset'
        })
    except Exception as e:
        print(f"Error resetting download state: {e}")
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
    
    # Add cache buster
    import time
    cache_buster = int(time.time())
    
    response = make_response(render_template('index.html', ai_session_id=ai_session_id, cache_buster=cache_buster))
    # Add no-cache headers to prevent browser caching issues
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

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

@app.route('/api/ai-recommendations/pathways', methods=['POST'])
def api_ai_recommendations_pathways():
    """API endpoint to generate AI recommendations for recovery pathways"""
    # This endpoint works with already-loaded data, so we just check if data exists
    if not os.path.exists('cache/training_analysis_report.json'):
        return jsonify({'error': 'No training data available'}), 404
        
    # Try to reinitialize AI engine if it's not available
    global ai_engine
    if not ai_engine:
        try:
            print("🔄 Attempting to initialize AI engine...")
            from ai_recommendations import AIRecommendationEngine
            ai_engine = AIRecommendationEngine()
            print("✅ AI recommendations re-enabled")
        except ValueError as e:
            print(f"❌ AI engine ValueError: {e}")
            return jsonify({'error': 'AI recommendations are not configured. Check your AI API key in .env file.'}), 503
        except Exception as e:
            print(f"❌ AI engine initialization error: {type(e).__name__}: {e}")
            import traceback
            traceback.print_exc()
            return jsonify({'error': f'AI service initialization failed: {str(e)}'}), 503
    
    try:
        # Get pathway data from request
        data = request.get_json()
        pathways = data.get('pathways', [])
        
        if not pathways:
            return jsonify({'error': 'No pathways provided'}), 400
            
        # Extract pathway context from the first pathway (they all share the same context)
        pathway_context = pathways[0].get('context', {}) if pathways else {}
        
        # Get training data
        training_data = get_training_data()
        
        # Generate new session ID
        session_id = str(uuid.uuid4())
        
        # Start AI generation for pathways in background with context
        start_pathway_ai_generation(session_id, training_data, pathway_context)
        
        return jsonify({
            'status': 'generating',
            'session_id': session_id,
            'message': 'AI pathway recommendations generation started'
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/ai-recommendations/refresh', methods=['POST'])
def api_ai_recommendations_refresh():
    """API endpoint to generate fresh AI recommendations"""
    # Check if user is authorized
    if not session.get('strava_access_token'):
        return jsonify({'error': 'Unauthorized'}), 401
        
    # Try to reinitialize AI engine if it's not available
    global ai_engine
    if not ai_engine:
        try:
            from ai_recommendations import AIRecommendationEngine
            ai_engine = AIRecommendationEngine()
            print("✅ AI recommendations re-enabled")
        except ValueError as e:
            # Missing or invalid API key
            return jsonify({'error': 'AI recommendations are not configured. Check your OpenAI API key in .env file.'}), 503
        except Exception as e:
            # Other initialization errors
            return jsonify({'error': f'AI service initialization failed: {str(e)}'}), 503
    
    try:
        # Force refresh training data first
        training_data = get_training_data(force_refresh=True)
        
        # Generate new session ID or use existing from session
        session_id = session.get('ai_session_id', str(uuid.uuid4()))
        session['ai_session_id'] = session_id
        
        # Start AI generation in background
        start_ai_generation(session_id, training_data)
        
        return jsonify({
            'status': 'generating',
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

@app.route('/api/ai-recommendations', methods=['GET'])
def api_ai_recommendations_get():
    """API endpoint to get AI recommendations (test compatibility)"""
    # Check if user is authorized (simplified check for tests)
    if not session.get('strava_access_token'):
        return jsonify({'error': 'Unauthorized'}), 401
        
    if not ai_engine:
        return jsonify({'error': 'AI recommendations are not available'}), 503
        
    # Return empty recommendations for now
    return jsonify({'recommendations': []})

@app.route('/api/ai-recommendations/<session_id>')
def api_ai_recommendations_by_session(session_id):
    """API endpoint to get AI recommendations by session ID"""
    # Check if user is authorized
    if not session.get('strava_access_token'):
        return jsonify({'error': 'Unauthorized'}), 401
        
    # Check session status
    with ai_sessions_lock:
        session_data = ai_sessions.get(session_id)
        
    if not session_data:
        # Try to load from file (for test compatibility)
        filename = f'cache/ai_recommendations_{session_id}.json'
        if os.path.exists(filename):
            with open(filename, 'r') as f:
                return jsonify(json.load(f))
        return jsonify({'error': 'Session not found'}), 404
        
    if session_data['status'] == 'ready':
        return jsonify(session_data['data'])
    elif session_data['status'] == 'error':
        return jsonify({'error': session_data.get('error', 'Unknown error')}), 500
    else:
        return jsonify({'status': 'pending'}), 202

@app.route('/api/save-preferences', methods=['POST'])
def api_save_preferences():
    """API endpoint to save workout preferences"""
    try:
        data = request.get_json()
        if not data or 'content' not in data:
            return jsonify({'error': 'Missing content in request'}), 400
            
        success = save_workout_preferences(data['content'])
        if success:
            return jsonify({'status': 'success', 'message': 'Preferences saved'})
        else:
            return jsonify({'error': 'Failed to save preferences'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/workout-preferences', methods=['POST'])
def api_workout_preferences():
    """API endpoint to save workout preferences (test compatibility)"""
    try:
        data = request.get_json()
        if not data or 'preferences' not in data:
            return jsonify({'error': 'Missing preferences in request'}), 400
            
        # Call the mocked function for tests
        save_workout_preferences(data['preferences'])
        
        return jsonify({'status': 'saved'})
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

# Wrapper functions for test compatibility
def load_cached_data():
    """Load cached training data (test compatibility wrapper)"""
    return get_training_data()

def generate_ai_recommendations_async(session_id, training_data):
    """Generate AI recommendations asynchronously (test compatibility wrapper)"""
    return start_ai_generation(session_id, training_data)

def save_workout_preferences(preferences_content):
    """Save workout preferences to file"""
    preferences_file = 'workout_preferences_personal.md'
    try:
        with open(preferences_file, 'w') as f:
            f.write(preferences_content)
        return True
    except Exception as e:
        print(f"Error saving preferences: {e}")
        return False

def main():
    # Set up signal handlers for clean shutdown
    signal.signal(signal.SIGINT, signal_handler)   # Ctrl+C
    signal.signal(signal.SIGTERM, signal_handler)  # Termination signal
    
    parser = argparse.ArgumentParser(description="Web server for training analysis visualization")
    parser.add_argument("--port", type=int, default=8080, help="Port to run the server on")
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
