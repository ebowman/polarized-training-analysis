# Polarized Training Analysis

A comprehensive tool for analyzing your training data to assess adherence to the polarized training approach, based on the research paper ["Training Intensity Distribution in Endurance Athletes: Are We Asking the Right Questions?"](https://pmc.ncbi.nlm.nih.gov/articles/PMC4621419/).

## Overview

The polarized training approach suggests that endurance athletes should spend approximately:
- **80%** of training time in Zone 1 (Low Intensity)
- **10%** of training time in Zone 2 (Threshold)  
- **10%** of training time in Zone 3 (High Intensity)

This tool downloads your training data from Strava, analyzes your heart rate and power zones, and provides detailed insights into how well you're following this proven training methodology.

## Features

### 📊 **Web Dashboard**
- Interactive bar charts for each workout showing zone distribution
- Combined chart showing aggregate training distribution vs. targets
- Time range filtering (7 days to all time)
- Real-time data refresh
- Responsive design for mobile and desktop

### 📈 **Training Analysis**
- Heart rate zone analysis based on maximum heart rate
- Power zone analysis based on Functional Threshold Power (FTP)
- Adherence scoring (0-100 scale)
- Personalized recommendations for training optimization

### 🔄 **Data Integration**
- Automatic Strava API integration with caching
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
```

## Strava API Setup

### 1. Create a Strava Application
1. Go to [Strava API Settings](https://www.strava.com/settings/api)
2. Create a new application
3. Set Authorization Callback Domain to `localhost`
4. Note your Client ID and Client Secret

### 2. Authorization
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

### Data Management

#### Fetch New Data
```bash
# Fetch 20 most recent activities
python strava_fetch.py --count 20

# Force refresh (ignore cache)
python strava_fetch.py --count 10
```

## Training Zones

### Heart Rate Zones
- **Zone 1**: ≤ 82% of Max HR (Low Intensity)
- **Zone 2**: 82-87% of Max HR (Threshold)
- **Zone 3**: ≥ 87% of Max HR (High Intensity)

### Power Zones
- **Zone 1**: ≤ 65% of FTP (Low Intensity)
- **Zone 2**: 65-88% of FTP (Threshold)
- **Zone 3**: ≥ 88% of FTP (High Intensity)

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

### Individual Workout Charts
- Bar chart for each workout showing zone breakdown
- Workout metadata (name, date, duration, average HR/power)
- Color-coded zones for easy identification

## API Endpoints

- `GET /` - Web dashboard
- `GET /api/workouts` - Get workout data as JSON
- `GET /api/workouts/refresh` - Force refresh workout data
- `GET /api/status` - Server status and cache info

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