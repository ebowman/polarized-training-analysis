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
- **Download Latest Data**: Use web UI "📥 Download Latest" button (simplified flow)
- **Regenerate Analysis**: `python regenerate_analysis.py`
- **Check for Duplicates**: `python check_duplicates.py`

## Key Data Structures

### Training Analysis Models
```python
@dataclass
class ActivityAnalysis:
    activity_id: int
    name: str
    date: str
    sport_type: str
    duration_minutes: int
    zone1_minutes: int
    zone2_minutes: int  
    zone3_minutes: int
    zone1_percent: float
    zone2_percent: float
    zone3_percent: float
    average_hr: Optional[int] = None
    average_power: Optional[int] = None
```

### Zone Configuration Models
```python
@dataclass 
class TrainingZones:
    zone1_max: int      # Z1 Recovery: <81% LTHR
    zone2_max: int      # Z2 Aerobic: 81-89% LTHR
    zone3_max: int      # Z3 Tempo: 90-93% LTHR
    zone4_max: int      # Z4 Threshold: 94-99% LTHR
    zone5a_max: int     # Z5a VO2max: 100-102% LTHR
    zone5b_max: int     # Z5b Anaerobic: 103-106% LTHR
    zone5c_min: int     # Z5c Neuromuscular: >106% LTHR
    lthr: int           # Lactate Threshold Heart Rate
```

### Cache File Structure
```
cache/
├── _activities_{id}_.json              # Individual activity data
├── _activities_{id}_streams_*.json     # Activity time-series streams
├── _athlete_.json                      # Athlete profile
├── tokens.json                         # OAuth tokens
├── training_analysis_report.json       # Main analysis cache
└── ai_recommendation_history.json      # AI recommendation history
```

### Download System Architecture
- **DownloadManager**: Singleton pattern with thread-safe state management
- **DownloadStatus**: Enum tracking (idle, downloading, processing, completed, error)
- **Progress Tracking**: Real-time SSE stream for download progress
- **Simplified Flow**: Direct API call → OAuth if needed → auto-continue → progress → completion

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

### Training Analysis Algorithms

#### 3-Zone Polarized Training Model (80/10/10)
The system implements a research-based polarized training model with specific mathematical formulas:

**Zone Definitions:**
- **Zone 1 (Low intensity)**: 80% of training time - aerobic base building
- **Zone 2 (Threshold)**: 10% of training time - lactate threshold work  
- **Zone 3 (High intensity)**: 10% of training time - VO2max and neuromuscular power

**Zone Calculation Methods:**

*Heart Rate Zones (LTHR-based):*
```python
# 7-zone model mapped to 3-zone polarized
zone1_max = int(lthr * 0.81)    # Z1-Z2 → Zone 1 (Low)
zone2_max = int(lthr * 0.89)    # Z3-Z4 → Zone 2 (Threshold)  
zone3_max = int(lthr * 0.93)    # Z5-Z7 → Zone 3 (High)
```

*Power Zones (FTP-based):*
```python
# Coggan zones mapped to polarized model
zone1_max = int(ftp * 0.75)     # Z1-Z2 → Zone 1 (Low)
zone3_max = int(ftp * 0.90)     # Z3-Z4 → Zone 2 (Threshold)
zone5_max = int(ftp * 1.20)     # Z5-Z7 → Zone 3 (High)
```

#### Rolling Window Analysis
The system uses a sophisticated rolling window approach for daily training targets:

**Future Day Calculations:**
- Each future day calculates its 7-day rolling window ending on that date
- Sums actual zone minutes from historical days in the window
- Calculates zone deficits: `target_zone_minutes - actual_zone_minutes`
- Divides deficit by remaining future days to get daily targets

**Today's Target Algorithm:**
```javascript
// Calculate what's needed today based on tomorrow's rolling window
const tomorrowWindowStart = new Date(tomorrow);
tomorrowWindowStart.setDate(tomorrow.getDate() - 6);

// Sum zone minutes from 6 days of history
// Calculate deficit for each zone
// Today gets the full deficit since it's the only future day
```

#### Adherence Scoring
```python
# Weighted deviation scoring (Zone 1 most important)
zone1_deviation = abs(zone1_percent - 80.0)
zone2_deviation = abs(zone2_percent - 10.0)  
zone3_deviation = abs(zone3_percent - 10.0)

# Weighted formula: Zone 1 = 50%, Zone 2/3 = 25% each
total_deviation = (zone1_deviation * 0.5) + (zone2_deviation * 0.25) + (zone3_deviation * 0.25)
adherence_score = max(0, 100 - total_deviation)
```

### Multi-Sport Support
- **Cycling**: Power zones (preferred) with HR fallback
- **Running/Rowing**: Heart rate zones exclusively
- **Strength Training**: Tracked separately as "ancillary work"
- **Sport-Specific Analysis**: Different zone models per activity type

### Web Dashboard Components & Frontend Architecture

#### Chart.js Visualizations
The frontend uses Chart.js for interactive data visualization:

**Combined Training Distribution Chart:**
- **Type**: Bar chart with dual y-axes
- **Purpose**: Shows actual vs target 80/10/10 zone distribution
- **Display Format**: `actualmin/targetmin` (e.g., "230min/288min")
- **Features**: Custom tooltips, color-coded adherence, time range filtering

**Volume Tracking Chart:**
- **Type**: Stacked bar chart with future projections
- **Purpose**: Daily volume tracking with zone-specific future targets
- **Data Streams**: 
  - Past/present: actual zone minutes by day
  - Future: separate Zone 1/2/3 "Needed" bars with rolling window calculations
- **Interactive Features**: Zone-specific tooltips showing daily targets

**Individual Workout Charts:**
- **Type**: Simple bar charts per workout
- **Purpose**: Per-activity zone breakdown
- **Features**: 3-zone visualization, percentage tooltips

#### Frontend Data Flow
```javascript
// Main data pipeline
fetch('/api/workouts') → JavaScript processing → Chart.js rendering
```

**Key Functions:**
- `loadData()` - Primary data fetching and orchestration
- `displayCombinedChart()` - Creates main distribution chart
- `displayVolumeTracking()` - Builds daily volume chart with projections
- `downloadLatest()` - **NEW**: Simplified download with progress tracking

#### Time Range Controls
- **User Selection**: 7, 14, 21, 28 days via dropdown
- **Persistent Storage**: Cookie-based preference storage
- **Dynamic Targets**: Scales 360min/week target proportionally
- **Chart Updates**: Triggers data reanalysis and chart recreation

### AI Recommendations
- **Equipment-Aware**: Considers user's available equipment (Peloton, etc.)
- **Science-Based**: References NIH research and training principles
- **Personalized**: Uses workout preferences and training history
- **Background Processing**: Async generation with session tracking

## API Endpoints

### Web Routes
- `GET /` - Main dashboard
- `GET /download-workouts` - Strava OAuth initiation (legacy)
- `GET /download-progress` - Legacy download progress page
- `GET /workout_preferences` - AI preferences management
- `GET /strava-callback` - OAuth callback handler

### Core API Endpoints
- `GET /api/workouts` - Training data JSON (5-minute cache)
- `POST /api/download-latest` - **NEW**: Simplified download with real-time progress
- `POST /api/download-workouts` - Legacy download endpoint
- `GET /api/download-progress` - SSE stream for download progress
- `GET /api/ai-status/<session_id>` - Check AI generation status
- `POST /api/ai-recommendations/refresh` - Generate new AI recommendations
- `POST /api/ai-recommendations/pathways` - Recovery pathway recommendations

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

#### Common Problems & Solutions

**Download Issues:**
- **Button greyed out**: Check DownloadManager singleton state, ensure proper cleanup
- **Unexpected redirects**: Verify OAuth callback parameters and session state
- **Import errors**: Ensure all required imports (e.g., DownloadStatus) are included
- **Progress not updating**: Check SSE connection and event source error handling

**Chart Issues:**
- **Charts not rendering**: Verify Chart.js library load, check canvas elements exist
- **Memory leaks**: Ensure chart destruction before recreation (`chart.destroy()`)
- **Data not updating**: Check 5-minute cache expiration and data refresh logic

**Zone Calculation Issues:**
- **Missing zone data**: Verify HR/power streams exist in activity data
- **Incorrect percentages**: Check 7-zone to 3-zone mapping logic
- **Future projections wrong**: Verify rolling window calculations and deficit math

#### Development Debugging
- **Python errors**: Check console output and Flask debug mode
- **Frontend issues**: Browser developer tools Network/Console tabs
- **API responses**: Check `/api/workouts` endpoint response format
- **Cache issues**: Inspect `cache/` directory for corrupt JSON files
- **OAuth problems**: Verify .env Strava API keys and redirect URIs

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