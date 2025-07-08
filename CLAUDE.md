# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with the Polarized Training Analysis Tool codebase.

## Project Overview
This is a Python Flask web application that analyzes Strava training data using polarized training principles (80/10/10 intensity distribution). It provides:
- Web dashboard with training distribution visualizations
- AI-powered workout recommendations using OpenAI
- OAuth2 Strava integration for data fetching
- Real-time download progress tracking

## Tech Stack
- **Backend**: Python 3.8+, Flask web framework
- **Frontend**: HTML/JavaScript with Chart.js for visualizations
- **Data Processing**: pandas, numpy for training analysis
- **AI**: OpenAI API (currently configured for o3 model)
- **External APIs**: Strava API for workout data
- **Storage**: JSON file-based caching system

## Key Commands

### Development & Testing
- **Start Server**: `python web_server.py` (default port 5000)
- **Start Server (custom port)**: `python web_server.py --port 5001`
- **Stop Server**: `./kill_server.sh` or `./kill_server.sh 5001`
- **Install Dependencies**: `pip install -r requirements.txt`
- **Activate Virtual Environment**: `source venv/bin/activate`

### Data Management
- **Download Latest Data**: Use web UI "📥 Download Latest" button
- **Regenerate Analysis**: `python regenerate_analysis.py`
- **Check for Duplicates**: `python check_duplicates.py`

### AI Recommendations
- **Test AI System**: Access `/workout_preferences` endpoint
- **Refresh AI Recommendations**: POST to `/api/ai-recommendations/refresh`

## Architecture & File Structure

### Core Application Files
- `web_server.py` - Main Flask application with routes and API endpoints
- `training_analysis.py` - Core analysis engine with TrainingAnalyzer class
- `strava_client.py` - Strava API integration and OAuth handling
- `download_manager.py` - Background download management with progress tracking
- `ai_recommendations.py` - OpenAI integration for workout recommendations

### Data & Templates
- `templates/` - Jinja2 HTML templates (index.html is main dashboard)
- `cache/` - JSON files for Strava data caching
- `requirements.txt` - Python dependencies

### Configuration Files
- `.env` - Environment variables (Strava API keys, OpenAI key, etc.)
- `workout_preferences.md` - Default AI recommendation preferences
- `workout_preferences_personal.md` - Personal AI preferences (git-ignored)

## Key Features to Understand

### Training Analysis
- **3-Zone Model**: Zone 1 (80%), Zone 2 (10%), Zone 3 (10%)
- **Multi-Sport Support**: Cycling (power), running/rowing (heart rate)
- **Time Window Analysis**: User-selectable display range, AI uses last 14 days
- **Adherence Scoring**: 0-100 score comparing actual vs target distribution

### Web Dashboard Components
- **Combined Training Distribution**: Main chart showing actual vs target zones
- **Individual Workout Analysis**: Per-activity breakdowns
- **Time Range Filtering**: 7 days to all-time analysis
- **Download Progress**: Real-time activity-by-activity download tracking

### AI Recommendations
- **Equipment-Aware**: Considers user's available equipment (Peloton, etc.)
- **Science-Based**: References NIH research and training principles
- **Personalized**: Uses workout preferences and training history
- **Background Processing**: Async generation with session tracking

## API Endpoints

### Web Routes
- `GET /` - Main dashboard
- `GET /download-workouts` - Strava OAuth initiation
- `GET /workout_preferences` - AI preferences management

### API Endpoints
- `GET /api/workouts` - Training data JSON
- `POST /api/download-workouts` - Trigger data download
- `GET /api/ai-status/<session_id>` - Check AI generation status
- `POST /api/ai-recommendations/refresh` - Generate new AI recommendations

## Development Guidelines

### Code Style
- **Python**: Follow PEP 8 standards
- **Comments**: Focus on why, not what
- **Error Handling**: Use try/except blocks for external API calls
- **Logging**: Use print statements for user feedback

### AI Model Configuration
- **Current Model**: OpenAI GPT-4o (configurable in ai_recommendations.py)
- **Context**: Uses training data + personal preferences for recommendations
- **Rate Limiting**: Handles OpenAI API limits gracefully

### Data Flow
1. **Strava OAuth** → User authorizes app
2. **Background Download** → fetch activities with progress tracking
3. **Analysis Engine** → process activities into 3-zone model
4. **Web Dashboard** → display charts and summaries
5. **AI Recommendations** → generate personalized workout suggestions

## Common Tasks

### Adding New Features
1. Backend logic in relevant .py files
2. API endpoints in web_server.py
3. Frontend updates in templates/index.html
4. Test with `python web_server.py`

### Debugging Issues
- Check console output for Python errors
- Browser developer tools for frontend issues
- Verify .env configuration for API keys
- Check cache/ directory for data integrity

### Performance Considerations
- **Caching**: 5-minute cache for training data
- **Background Processing**: AI recommendations generated async
- **Rate Limiting**: Graceful handling of Strava API limits
- **Data Efficiency**: Only download new activities, not full history

## Security Notes
- **Local Processing**: All data stays on user's machine
- **OAuth2**: Secure Strava authentication
- **API Keys**: Stored in .env file, not version controlled
- **Session Management**: Flask sessions for AI recommendation tracking

## Known Limitations
- **Heart Rate/Power Required**: Activities without intensity data are ignored
- **Strava Dependency**: Requires Strava account and API access
- **Single User**: Designed for individual use, not multi-user
- **File-Based Storage**: Uses JSON files, not a database

## Testing Strategy
- **Manual Testing**: Use web interface with real Strava data
- **API Testing**: Direct endpoint testing with curl/Postman
- **Data Validation**: Check cache files and analysis output
- **Cross-Browser**: Test frontend in different browsers

## Future Considerations
- **Database Migration**: Consider PostgreSQL for multi-user support
- **Advanced Analytics**: Additional metrics beyond 3-zone model
- **Mobile Support**: Responsive design improvements
- **Export Features**: CSV/PDF report generation