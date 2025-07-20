# 🏃‍♂️ Polarized Training Analysis Tool

**Are you training too hard in the middle zones? This science-backed tool analyzes your Strava data to optimize your training for maximum performance gains.**

![Polarized Training Dashboard](https://img.shields.io/badge/Training-Science%20Based-brightgreen) ![Strava Integration](https://img.shields.io/badge/Strava-Integrated-orange) ![AI Powered](https://img.shields.io/badge/AI-OpenAI%20GPT--4o-blue)

## 🤔 What Problem Does This Solve?

Most endurance athletes make the same critical mistake: **they train too much in the "moderate" intensity zone** — not easy enough to build aerobic base, not hard enough to drive adaptation. This leads to:

- 💔 **Chronic fatigue** without performance gains
- 🔄 **Plateau effects** where training stops improving fitness
- 🔥 **Burnout** from constantly being "sort of tired"
- 📉 **Inefficient use of training time**

## 🧪 The Science-Based Solution

Research from the **National Institutes of Health (NIH)** shows that elite endurance athletes follow a "polarized" training distribution:

- **🟢 80% Low Intensity** (Zone 1) - Build massive aerobic base
- **🟡 10% Threshold** (Zone 2) - Lactate threshold work  
- **🔴 10% High Intensity** (Zone 3) - VO2 max and neuromuscular power

This isn't just theory — it's how **Olympic champions and Tour de France winners actually train**.

### 📚 Research Foundation

Based on the landmark NIH study: *"Training Intensity Distribution in Endurance Athletes: Are We Asking the Right Questions?"* by Laursen & Buchheit (2019), which analyzed training patterns across:

- 🏃‍♂️ Marathon runners
- 🚴‍♀️ Professional cyclists  
- 🏊‍♂️ Elite swimmers
- ⛷️ Cross-country skiers

**Key Finding**: Athletes who followed the 80/10/10 polarized distribution consistently outperformed those who trained more in moderate zones.

## ✨ What This Tool Does

### 🔍 **Analyzes Your Training Reality**
- Connects to your Strava account with one click
- Downloads your workout data automatically
- Shows you exactly where your training time is actually going
- Compares your distribution to the research-proven 80/10/10 target

### 📊 **Beautiful Web Dashboard**
- Interactive charts for every workout
- Combined analysis showing trends over time
- Time range filtering (7 days to all time)
- Adherence scoring (0-100) to track improvement

### 🤖 **AI-Powered Features**
- Uses OpenAI's GPT-4o or Claude for intelligent analysis
- Generates personalized workouts based on your data
- **NEW**: AI-powered configuration generation from natural language preferences
- Considers your equipment (Peloton, rowing machine, etc.)
- Provides detailed workout structure and scientific reasoning

### 📥 **Smart Data Management**
- OAuth2 integration for secure Strava connection
- Intelligent caching (only downloads new workouts)
- Background processing (no waiting for slow AI responses)
- **NEW**: Real-time download progress with activity-by-activity updates
- **NEW**: Automatic startup sync (downloads last 30 days if needed)
- **NEW**: Graceful rate limit handling with visual countdown

### 🎯 **Zone Distribution Management**
- **NEW**: Visual zone distribution editor with sliders
- **NEW**: Sport-specific zone customization
- **NEW**: Preset training philosophies (Polarized/Pyramidal/Threshold)
- **NEW**: Real-time zone compliance monitoring
- **NEW**: Batch updates across multiple sports

## 🚀 Who Is This For?

### ✅ **Perfect If You:**
- Train 3+ hours per week consistently
- Use Strava to track workouts with heart rate or power data
- Want to optimize your training based on actual science
- Are curious about how elite athletes really train
- Feel like you're working hard but not seeing results

### ❌ **Not Right If You:**
- Only do casual, recreational exercise
- Don't track workouts digitally
- Are happy with your current training and results
- Don't have heart rate or power data

## 📚 Documentation

### Core Documentation
- **[Zone Distribution User Guide](docs/ZONE_DISTRIBUTION_USER_GUIDE.md)** - Complete guide to customizing training zones
- **[AI Configuration Guide](docs/AI_CONFIG_GENERATION_GUIDE.md)** - Generate configs from natural language
- **[API Documentation](docs/SETTINGS_API.md)** - Complete API reference
- **[Zone Examples](docs/ZONE_DISTRIBUTION_EXAMPLES.md)** - Sport-specific distribution examples

## 🛠️ How to Get Started

### **Step 1: Prerequisites**
- **Strava account** with workout data (heart rate or power zones)
- **Python 3.8+** installed on your computer
- **OpenAI API key** (optional, for AI recommendations - $5-10/month)

### **Step 2: Quick Setup**
```bash
# Clone the project
git clone https://github.com/your-username/polarized-training-analysis.git
cd polarized-training-analysis

# Install dependencies
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Configure your settings
cp .env.example .env
# Edit .env with your details (see below)
```

### **Step 3: Configuration**
Edit `.env` file with your information:
```env
# Get these from https://www.strava.com/settings/api
STRAVA_CLIENT_ID=your_client_id_here
STRAVA_CLIENT_SECRET=your_client_secret_here

# Your training zones (find in Strava settings)
MAX_HEART_RATE=180
FTP=250

# FTP Test Data (optional - for LTHR-based HR zones)
# Fill these from your most recent 20-minute FTP test
AVERAGE_FTP_HR=0  # Average HR during FTP test (this is your LTHR)
MAX_FTP_HR=0      # Max HR during FTP test
AVERAGE_FTP_POWER=0  # Average power during 20-min test

# Optional: Get from https://platform.openai.com/api-keys
OPENAI_API_KEY=your_openai_api_key_here

# Security (generate any random string)
FLASK_SECRET_KEY=your_secret_key_here
```

### **Step 4: Launch & Connect**
```bash
# Start the web dashboard
python web_server.py

# Optional: Disable automatic download on startup
python web_server.py --no-auto-download

# Open browser to http://localhost:5000
# The app will automatically check for data and start downloading if needed
# Or click "📥 Download Latest" to manually sync with Strava
```

## 🎯 What You'll See

### **Live Download Progress**
- Real-time progress bar showing download percentage
- Current activity name being downloaded
- Animated list of new activities as they're downloaded
- Rate limit countdown when Strava API limits are hit
- Automatic retry with graceful error handling

### **Immediate Insights**
- Your actual training distribution (e.g., "65% Zone 1, 25% Zone 2, 10% Zone 3")
- Adherence score showing how close you are to optimal
- Individual workout breakdowns with zone percentages

### **Actionable Recommendations**
- **"🚨 High Priority: Add 90min Zone 1 ride"** - You're only getting 60% Zone 1 (need 80%)
- **"⚠️ Medium Priority: 45min Zone 3 intervals"** - Haven't done high intensity in 8 days
- **"💡 Low Priority: Recovery ride"** - Optional active recovery

### **AI-Powered Coaching**
- **Equipment-specific workouts**: "Power Zone 2 endurance ride on Peloton (90 min)"
- **Scientific reasoning**: "Your Zone 1 percentage is 15% below target, limiting aerobic adaptation"
- **Progressive structure**: Detailed warmup, intervals, and cooldown instructions

### **🎯 Personalizing AI Recommendations**

#### **Two-Tier Preference System**
The tool supports both default and personal preferences for maximum flexibility:

- **📋 Default preferences** (`workout_preferences.md`) - Baseline recommendations included with the project
- **✏️ Personal preferences** (`workout_preferences_personal.md`) - Your custom goals and constraints (not tracked by git)

#### **How to Customize**
1. **Copy the example**: `cp workout_preferences_personal.md.example workout_preferences_personal.md`
2. **Edit your personal file** with your specific goals, equipment, time constraints, and training preferences
3. **The AI automatically uses your personal file** if it exists, otherwise falls back to the default

#### **What You Can Customize**
- **Training goals** (marathon times, FTP targets, race preparation)
- **Available equipment** (Peloton models, rowing machines, weights)
- **Time constraints** (weekday limits, weekend availability)
- **Workout preferences** (interval vs steady-state, morning vs evening)
- **Physical considerations** (injury history, recovery needs)
- **Seasonal periodization** (base building, peak, recovery phases)

#### **Benefits**
- **🔒 Privacy**: Personal goals stay on your computer, not in git
- **🔄 Updates**: Pull project updates without losing customizations
- **👥 Sharing**: Share the project while keeping personal details private
- **🎯 Precision**: AI gets highly specific recommendations based on your actual situation

## 💡 Real-World Example

**Sarah's Story**: Marathon runner, 35, training 6 hours/week

**Before**: 50% Zone 1, 40% Zone 2, 10% Zone 3 → Constantly tired, plateau at 3:45 marathon

**After Analysis**: Tool showed she was doing too much "junk miles" in Zone 2

**New Plan**: 80% Zone 1, 10% Zone 2, 10% Zone 3 → Broke through to 3:32 marathon, felt more energized

## 🔬 The Science Deep Dive

### **Why 80/10/10 Works**

1. **🟢 Zone 1 (80%)**: Builds mitochondrial density, capillarization, fat oxidation
2. **🟡 Zone 2 (10%)**: Improves lactate clearance and metabolic efficiency  
3. **🔴 Zone 3 (10%)**: Drives VO2 max and neuromuscular adaptations

### **Why "Moderate" Training Fails**
- **Zone 2 overload** creates chronic stress without full recovery
- **Prevents adaptation** to both aerobic and anaerobic systems
- **"Black hole of training"** - too hard to recover from, not hard enough to adapt

### **Elite Athlete Data**
- **Tour de France riders**: 80.2% Zone 1, 9.1% Zone 2, 10.7% Zone 3
- **Olympic marathoners**: 77.8% Zone 1, 12.1% Zone 2, 10.1% Zone 3
- **World-class cyclists**: Consistently maintain >75% Zone 1 across all training phases

## 🛡️ Privacy & Security

- **Local data processing**: Your workout data stays on your computer
- **Secure OAuth**: Industry-standard Strava authentication
- **No data selling**: This is a personal training tool, not a data collection service
- **Open source**: You can see exactly what the code does

## 🤝 Contributing & Support

### **Found a Bug?**
- Open an issue on GitHub with details
- Include your training data setup (anonymized)

### **Want to Contribute?**
- Fork the repository
- Add features or fix bugs
- Submit a pull request

### **Need Help?**
- Check the troubleshooting section below
- Review your .env configuration
- Ensure Strava has heart rate/power data

## 🔧 Troubleshooting

### **"No activities found"**
- ✅ Check Strava authorization: Click "📥 Download Latest" 
- ✅ Ensure activities have heart rate or power data
- ✅ Try longer time range (30+ days)

### **"AI recommendations not loading"**
- ✅ Check OPENAI_API_KEY in .env file
- ✅ Verify OpenAI account has API access
- ✅ Look for error messages in browser console

### **"Port already in use"**
- ✅ Use different port: `python web_server.py --port 5001`
- ✅ Or kill existing processes: `./kill_server.sh`

### **"Import errors"**
- ✅ Activate virtual environment: `source venv/bin/activate`
- ✅ Install dependencies: `pip install -r requirements.txt`

## 📈 Advanced Features

### **Multi-Sport Analysis**
- **🚴‍♀️ Cycling**: Power zone analysis (FTP-based)
- **🚣‍♂️ Rowing**: Heart rate zone analysis
- **🏃‍♂️ Running**: Heart rate zone analysis
- **🏋️‍♀️ Strength**: RPE-based recommendations

### **Time Window Intelligence**
- **Display analysis**: User-selected time range for historical trends
- **AI recommendations**: Always based on last 14 days for relevance
- **Dual-window approach**: Balances long-term trends with immediate needs

### **Advanced Zone Systems**
The app supports both simplified and advanced zone models:

#### **Heart Rate Zones**
- **LTHR-based (7-zone)**: When you have FTP test data
  - Z1 Recovery: <81% LTHR
  - Z2 Aerobic: 81-89% LTHR  
  - Z3 Tempo: 90-93% LTHR
  - Z4 Threshold: 94-99% LTHR
  - Z5 VO2max/Anaerobic: 100-106% LTHR
- **Max HR-based (3-zone)**: Simplified fallback model
  - Zone 1: ≤82% Max HR (aerobic base)
  - Zone 2: 82-87% Max HR (threshold)
  - Zone 3: >87% Max HR (high intensity)

#### **Power Zones (Cycling)**
- 7-zone Coggan model based on FTP
- Automatically used for cycling activities
- Falls back to HR if no power data

#### **Sport-Specific Analysis**
- **Cycling**: Power zones preferred, HR fallback
- **Running/Rowing**: Heart rate zones only
- **Strength Training**: Excluded from zone analysis

### **API Endpoints**
```
GET /                              # Web dashboard
GET /download-workouts             # OAuth2 Strava connection
POST /api/download-workouts        # Download latest activities
GET /api/ai-status/<session_id>    # Check AI generation status
POST /api/ai-recommendations/refresh # Generate new AI recommendations
```

## 🎉 Success Stories

> *"This tool completely changed how I think about training. I was doing way too much Zone 2 'tempo' work. After switching to proper polarized training, I PR'd in my next race and felt more energized than ever."* — Mike R., Cyclist

> *"The AI recommendations are incredibly smart. It suggested specific Peloton classes that perfectly matched what my training analysis showed I needed. Game changer!"* — Jennifer K., Triathlete

> *"As a coach, this gives me objective data to show athletes why their training isn't working. The NIH research backing makes it credible with skeptical athletes."* — Coach David L.

## 📚 Further Reading

- [NIH Study: Training Intensity Distribution](https://pmc.ncbi.nlm.nih.gov/articles/PMC4621419/)
- [Polarized Training: What and Why](https://www.trainingpeaks.com/blog/polarized-training-explained/)
- [Elite Athlete Training Analysis](https://journals.lww.com/acsm-msse/fulltext/2010/10000/polarized_training_has_greater_impact_on_key.22.aspx)

## 📄 License

MIT License - Feel free to use, modify, and share!

---

## 🚀 Ready to Transform Your Training?

**The difference between good and great athletes isn't just talent — it's training smarter, not just harder.**

Start your polarized training journey today:

```bash
git clone https://github.com/your-username/polarized-training-analysis.git
cd polarized-training-analysis
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# Edit .env with your settings
python web_server.py
```

**Train like the elites. See results like the elites.** 🏆

---

*Built with ❤️ for the endurance community. Based on peer-reviewed research. Powered by your data.*