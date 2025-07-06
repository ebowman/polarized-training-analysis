# Polarized Training Analysis

A comprehensive tool for analyzing your training data to assess adherence to the polarized training approach, based on the research paper ["Training Intensity Distribution in Endurance Athletes: Are We Asking the Right Questions?"](https://pmc.ncbi.nlm.nih.gov/articles/PMC4621419/).

## Overview

The polarized training approach suggests that endurance athletes should spend approximately:
- **80%** of training time in Zone 1 (Low Intensity)
- **10%** of training time in Zone 2 (Threshold)  
- **10%** of training time in Zone 3 (High Intensity)

This tool downloads your training data from Strava, analyzes your heart rate and power zones, and provides detailed insights into how well you're following this proven training methodology. It also generates intelligent, research-based workout recommendations to help you maintain optimal training distribution.

## Features

### 📊 **Web Dashboard**
- Interactive bar charts for each workout showing zone distribution
- Combined chart showing aggregate training distribution vs. targets
- Time range filtering (7 days to all time)
- **📥 One-Click Strava Download** with OAuth2 integration
- Intelligent workout recommendations with detailed structure and reasoning
- **🤖 AI-Powered Recommendations** using OpenAI o3 with session-based loading
- Real-time data refresh with smart caching
- **📋 Recommendation History** with browser-based storage
- Responsive design for mobile and desktop

### 📈 **Training Analysis**
- Heart rate zone analysis based on maximum heart rate
- Power zone analysis based on Functional Threshold Power (FTP)
- Adherence scoring (0-100 scale)
- Research-based workout recommendations with dual-window approach

### 🕐 **Dual-Window Analysis Approach**
Based on sports science research, the tool uses two different time windows:

- **Display Analysis**: User-selected time range (7 days to all time)
  - Shows historical trends and long-term adherence
  - Allows exploration of different training periods
  - Used for zone distribution charts and summaries

- **Workout Recommendations**: Fixed 14-day window
  - Based on research showing 1-2 weeks as optimal for immediate training decisions
  - Captures recent training stress and recovery needs
  - Prevents recommendations from being skewed by viewing preferences
  - Aligns with elite athlete patterns (2 hard sessions per week)

### 🎯 **Intelligent Workout Recommendations**
The tool generates specific, actionable workout recommendations using advanced analysis:

- **Dual Metrics Analysis**: Considers both percentage distribution AND absolute time in each zone
- **Volume Assessment**: Evaluates if total training volume meets minimum thresholds
- **Intensity Requirements**: Ensures adequate Zone 3 time for fitness maintenance (≥30min/week)
- **Recovery Patterns**: Analyzes recent workout intensity and recommends appropriate recovery
- **Smart Prioritization**: High-priority recommendations for critical training gaps
- **Detailed Structure**: Complete workout descriptions with warmup, intervals, and cooldown
- **Scientific Reasoning**: Evidence-based explanations for each recommendation

**Key Analysis Factors:**
- **Total Training Volume**: Minimum 3 hours/week for meaningful adaptation
- **Zone 3 Minimum**: At least 30 minutes/week of high-intensity work
- **Zone 1 Baseline**: Minimum 70% of total time for aerobic base
- **Recovery Timing**: Days since last high-intensity session
- **Pattern Recognition**: Recent workout type distribution

**Example Recommendations:**
- 🚨 🟢 Volume building workout (108m): "Your weekly volume (142min) is below minimum (180min)"
- 🚨 🔴 High-intensity intervals (75m): "You're only getting 15min/week of Zone 3 (need ≥30min)"
- ⚠️ 🟢 Long aerobic base ride (3h 12m): "You need 15.3% more Zone 1 training"
- 💡 🟡 Tempo workout (45m): "Optional technique work to maintain neuromuscular fitness"

### 🔄 **Data Integration**
- **One-Click Download**: OAuth2 integration for seamless Strava authorization
- **Smart Caching**: Only downloads new activities, preserves existing cache
- **Background Processing**: Non-blocking downloads with progress indicators
- Downloads activity details and streams (heart rate, power, time)
- Respects API rate limits with intelligent caching

## Installation

### 1. Clone the Repository
```bash
git clone <repository-url>
cd strava-polarized-training
```

### 2. Create Virtual Environment
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Set Up Environment Variables
```bash
cp .env.example .env
```

Edit `.env` with your values:
```env
# Strava API Configuration
STRAVA_CLIENT_ID=your_client_id_here
STRAVA_CLIENT_SECRET=your_client_secret_here

# Training Analysis Configuration
MAX_HEART_RATE=180
FTP=250

# OpenAI API Configuration (for AI recommendations)
OPENAI_API_KEY=your_openai_api_key_here

# Flask Configuration (for web security)
FLASK_SECRET_KEY=your_secret_key_here
```

## Strava API Setup

### 1. Create a Strava Application
1. Go to [Strava API Settings](https://www.strava.com/settings/api)
2. Create a new application
3. Set Authorization Callback Domain to `localhost`
4. Note your Client ID and Client Secret

### 2. Authorization
You can authorize the application in two ways:

**Option A: Web Interface (Recommended)**
1. Start the web server: `python web_server.py`
2. Open your browser to `http://localhost:5000`
3. Click "📥 Download Latest" to begin OAuth2 flow
4. Authorize with Strava in your browser

**Option B: Command Line**
```bash
python strava_fetch.py --authorize
```

Follow the prompts to authorize the application with your Strava account.

## Usage

### Command Line Analysis

#### Basic Analysis
```bash
# Analyze last 30 days using heart rate zones
python polarized_training_analysis.py --days 30

# Analyze last 60 days using power zones
python polarized_training_analysis.py --days 60 --use-power

# Custom FTP and max heart rate
python polarized_training_analysis.py --max-hr 185 --ftp 280
```

#### Web Dashboard
```bash
# Start the web server
python web_server.py

# Custom port and host
python web_server.py --port 8080 --host 0.0.0.0
```

Then open your browser to `http://localhost:5000`

## AI-Powered Recommendations

### 🤖 **OpenAI o3 Integration**
The tool now includes AI-powered workout recommendations using OpenAI's advanced o3 model with **session-based processing** for optimal performance:

- **Non-Blocking Generation**: AI recommendations load in background with visual progress
- **Session Management**: Reliable processing even for slow OpenAI responses
- **Personalized Plans**: Based on your training goals, equipment, and recent data
- **Your Training Goals**: Customizable preferences in `workout_preferences.md`
- **Equipment Available**: Peloton, Concept2 RowERG, dumbbells, bodyweight
- **Recent Training Data**: Your last 14 days of Strava activities
- **NIH Research**: Evidence-based polarized training principles
- **Personal Context**: FTP goals, training history, recovery needs

### 📝 **Customizing Your Preferences**
Edit `workout_preferences.md` to personalize AI recommendations:

```markdown
## Primary Training Goals
- **Cycling FTP Improvement**: Training to raise my cycling FTP on Peloton
- **Multi-Modal Fitness**: Rowing, strength training, etc.

## Equipment & Training Modalities
- **Peloton bike**: FTP improvement and power development
- **Concept2 RowERG**: Cardiovascular endurance
- **Dumbbells**: Functional strength training
```

### 🔄 **Using AI Features**
1. **Automatic Recommendations**: AI suggestions start generating when you load the dashboard
2. **Background Processing**: Shows progress spinner while OpenAI generates recommendations
3. **Refresh for Variety**: Click "🔄 Refresh AI" for different workout options
4. **View History**: Click "📋 History" to see previous AI recommendations
5. **Equipment-Specific**: Each recommendation specifies required equipment
6. **Reliable Loading**: Session-based system handles slow/failed API responses gracefully

### 💡 **AI Recommendation Examples**
- **"Power Zone 2 Endurance Ride (90m)"** - Structured power zone training for base building
- **"HR Zone 2 Steady State Row (45m)"** - Cross-training at 120-140 bpm for recovery
- **"Functional Strength Circuit (30m)"** - RPE 6-7 strength training for endurance athletes

### 🔧 **Setup Requirements**
1. Get an OpenAI API key from [platform.openai.com](https://platform.openai.com)
2. Add it to your `.env` file: `OPENAI_API_KEY=your_key_here`
3. Restart the web server to enable AI features

If you don't have an OpenAI API key, the tool will still work perfectly with the built-in algorithm-based recommendations.

### Data Management

#### Fetch New Data
```bash
# Fetch 20 most recent activities
python strava_fetch.py --count 20

# Force refresh (ignore cache)
python strava_fetch.py --count 10
```

## Training Zone Systems

This tool uses multiple zone systems to provide the most accurate training guidance:

### 📊 **Polarized Training Zones (for overall analysis)**
Research-based 3-zone system for training distribution:
- **Polarized Zone 1**: Low Intensity - **80%** target (aerobic base)
- **Polarized Zone 2**: Threshold - **10%** target (lactate threshold)  
- **Polarized Zone 3**: High Intensity - **10%** target (VO2 max)

### 🚴 **Power Zones (for Peloton cycling)**
Activity-specific zones based on your FTP (301W):
- **Power Zone 1-3**: 0-90% FTP → Maps to Polarized Zone 1
- **Power Zone 4**: 90-105% FTP → Maps to Polarized Zone 2
- **Power Zone 5-6**: 105%+ FTP → Maps to Polarized Zone 3

### 🚣 **Heart Rate Zones (for rowing/other activities)**
Activity-specific zones based on max HR (171 bpm):
- **HR Zone 1-2**: 86-140 bpm → Maps to Polarized Zone 1
- **HR Zone 3-4**: 140-159 bpm → Maps to Polarized Zone 2
- **HR Zone 5**: 159+ bpm → Maps to Polarized Zone 3

### 🏋️ **Strength Training**
Uses RPE (Rate of Perceived Exertion) 1-10 scale instead of zones.

**📖 See `zone_mapping_guide.md` for detailed explanations and examples.**

## File Structure

```
├── README.md                          # This file
├── requirements.txt                   # Python dependencies
├── .env.example                      # Environment variables template
├── .gitignore                        # Git ignore rules
├── strava_client.py                  # Strava API client
├── strava_fetch.py                   # Data fetching script
├── training_analysis.py              # Core analysis engine
├── polarized_training_analysis.py    # Command-line analysis tool
├── web_server.py                     # Web dashboard server
├── templates/
│   └── index.html                    # Web dashboard template
└── cache/                            # Cached API responses
```

## Output Files

- `training_analysis_report.txt` - Detailed text report
- `training_analysis_report.json` - Analysis data in JSON format
- `recent_activities.json` - Latest fetched activities
- `cache/` - Cached API responses (auto-generated)

## Web Dashboard Features

### Time Range Filtering
- **7-365 days**: Analyze specific time periods
- **All time**: View complete training history
- **Real-time updates**: Instant filtering without page reload

### Combined Analysis Chart
- Shows your actual vs. target zone distribution
- Weighted by training time (longer workouts have more influence)
- Visual comparison with polarized training targets
- Updates dynamically with time range selection

### Individual Workout Charts
- Bar chart for each workout showing zone breakdown
- Workout metadata (name, date, duration, average HR/power)
- Color-coded zones for easy identification
- Filtered by selected time range

### Workout Recommendations Section
- Color-coded priority cards (high/medium/low priority)
- Zone icons and duration badges
- Detailed workout structure with specific instructions
- Reasoning explanations for each recommendation
- Always based on last 14 days regardless of viewing period

## API Endpoints

### Core Endpoints
- `GET /` - Web dashboard
- `GET /api/workouts` - Get workout data as JSON
- `GET /api/workouts/refresh` - Force refresh workout data
- `GET /api/status` - Server status and cache info

### OAuth2 & Data Download
- `GET /download-workouts` - Initiate Strava OAuth2 flow
- `GET /auth/callback` - Handle OAuth2 callback from Strava
- `GET /download-progress` - Show download progress page
- `POST /api/download-workouts` - Download latest workouts from Strava

### AI Recommendations (Session-Based)
- `GET /api/ai-status/<session_id>` - Check AI generation status (pending/ready/error)
- `POST /api/ai-recommendations/refresh` - Start new AI generation session
- `GET /api/ai-recommendations/history` - Get AI recommendation history

## Troubleshooting

### Common Issues

**No activities found**
- Check your Strava authorization: `python strava_fetch.py --authorize`
- Ensure activities have heart rate or power data
- Try increasing the time range: `--days 90`

**API rate limit exceeded**
- The tool uses aggressive caching to respect Strava's rate limits
- Wait 15 minutes or use cached data
- Check `cache/` directory for existing data

**Import errors**
- Ensure virtual environment is activated: `source venv/bin/activate`
- Install dependencies: `pip install -r requirements.txt`

**Web server issues**
- Check if port 5000 is available
- Run analysis first: `python polarized_training_analysis.py`
- Try different port: `python web_server.py --port 8080`

### Debug Mode
```bash
# Enable debug logging
python web_server.py --debug

# Force refresh all data
python polarized_training_analysis.py --force-refresh
```

## Research Background

This tool is based on the research paper:

**"Training Intensity Distribution in Endurance Athletes: Are We Asking the Right Questions?"**
*Laursen, P. B., & Buchheit, M. (2019). Sports Medicine, 49(2), 153-173.*

The polarized training model suggests that the most effective training distribution for endurance athletes is:
- High volume at low intensity (Zone 1)
- Minimal time at moderate intensity (Zone 2)
- Strategic high-intensity work (Zone 3)

This approach has been validated across multiple sports and athlete populations.

### Time Window Research

The dual-window approach is based on the following research findings:

- **Minimum Assessment Period**: Research shows polarized distribution should be assessed over "at least a week, if not longer"
- **Optimal Analysis Window**: 4-12 weeks provides meaningful training distribution analysis
- **Immediate Recommendations**: 1-2 weeks captures recent training stress and recovery needs
- **Elite Patterns**: Elite athletes typically perform 2 high-intensity sessions per week, creating 14-day training patterns
- **Physiological Windows**: Training adaptations and recovery occur over 7-14 day periods

## Contributing

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd strava-polarized-training

# Create development environment
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Set up pre-commit hooks (optional)
# pip install pre-commit
# pre-commit install
```

### Making Changes
1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Acknowledgments

- Strava API for providing comprehensive training data
- The research community for establishing the polarized training methodology
- Chart.js for beautiful, interactive visualizations

## Support

For issues, feature requests, or questions:
1. Check the troubleshooting section above
2. Search existing issues
3. Create a new issue with detailed information

---

**Happy Training! 🏃‍♂️🚴‍♀️🏊‍♂️**

*Remember: The best training plan is the one you can stick to consistently. Use this tool to optimize your training, but listen to your body and adjust as needed.*