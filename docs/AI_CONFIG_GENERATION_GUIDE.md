# AI-Powered Configuration Generation Guide

## Overview

The AI Configuration Generation feature transforms natural language workout preferences into structured sport configurations. This guide explains how to write effective preferences and use the generation workflow.

## Quick Start

### 1. Write Your Preferences

Create a file `workout_preferences_personal.md` or use the in-app editor:

```markdown
# My Training Profile

I'm a competitive cyclist with an FTP of 301W. I train on a Peloton bike 
and follow a polarized approach. I also row for cross-training.

My goals:
- Increase FTP to 320W
- Train 10-15 hours per week
- Race local criteriums
```

### 2. Generate Configuration

**Via Web UI**:
1. Go to Settings → Preferences tab
2. Paste or write your preferences
3. Click "Generate Configuration"
4. Review and save

**Via API**:
```bash
curl -X POST http://localhost:5000/api/settings/generate-config \
  -H "Content-Type: application/json" \
  -d @- << EOF
{
  "preferences": "I'm a cyclist with FTP 301W..."
}
EOF
```

**Via Command Line**:
```bash
python config_generator.py
```

## Writing Effective Preferences

### Structure Template

```markdown
# My Training Profile

## Current Fitness Level
- [Sport]: [Metric] = [Value]
- Example: Cycling FTP: 301W
- Example: Running LTHR: 155 bpm

## Equipment
- [Equipment name] for [sport]
- Example: Peloton bike for indoor cycling
- Example: Concept2 Model D for rowing

## Training Philosophy
- I follow a [philosophy] approach
- My typical week: [volume] hours
- Zone distribution preference: [percentages]

## Goals
- [Specific, measurable goals]
- Timeline: [when to achieve]

## Additional Context
- Injury history
- Time constraints
- Preferences (indoor/outdoor, group/solo)
```

### Keywords the AI Recognizes

**Sports**:
- Cycling, biking, riding
- Running, jogging
- Rowing, erging
- Swimming
- Triathlon

**Equipment**:
- Peloton, Zwift, trainer
- Concept2, WaterRower
- Treadmill
- Garmin, Wahoo, power meter

**Metrics**:
- FTP (Functional Threshold Power)
- LTHR (Lactate Threshold Heart Rate)
- Threshold pace
- VO2max
- Critical power

**Training Philosophies**:
- Polarized (80/10/10)
- Pyramidal (70/20/10)
- Threshold-focused
- High-volume, low-volume

### Example Preferences

#### Example 1: Detailed Cyclist

```markdown
# Cycling Training Preferences

## Current Status
I'm a 35-year-old competitive cyclist focusing on criterium racing. My current FTP is 301W (4.1 W/kg at 73kg). I've been training seriously for 3 years.

## Equipment
- Peloton Bike+ for structured indoor workouts
- Canyon Aeroad with Garmin Vector 3 power pedals for outdoor rides
- Garmin Edge 830 cycling computer
- Wahoo TICKR heart rate monitor (max HR: 185, LTHR: 155)

## Training Approach
I follow a polarized training model:
- 80% of rides at endurance pace (Zone 1: <225W)
- 10% at threshold (Zone 2: 270-300W)  
- 10% for VO2max/sprint work (Zone 3: >300W)

Weekly volume varies by phase:
- Base period: 12-15 hours
- Build period: 10-12 hours  
- Race period: 8-10 hours
- Recovery weeks: 5-6 hours

## 2024 Goals
1. Increase FTP to 320W by June
2. Win local criterium series
3. Complete a century ride under 5 hours
4. Maintain year-round consistency

## Constraints & Preferences
- Can train early mornings (5-7am) and weekends
- Prefer indoor intervals during weekdays
- Long outdoor rides on weekends
- Need to balance with family time
```

#### Example 2: Multi-Sport Athlete

```markdown
# Multi-Sport Training Configuration

## About Me
Former runner transitioning to triathlon. Currently train 8-10 hours/week across three sports.

## Current Fitness
- Running: 5K PR 18:30, LTHR 162 bpm
- Cycling: Estimated FTP 220W (new to power)
- Swimming: 1:45/100m pace for distance sets

## Equipment  
- Running: Garmin Forerunner 945
- Cycling: Peloton Bike (no outdoor bike yet)
- Swimming: Local pool access 3x/week
- Cross-training: Concept2 rower

## Training Philosophy
Following a pyramidal approach while building cycling fitness:
- Want more Zone 2 work to build aerobic base
- Keep some intensity for running speed
- Focus on technique for swimming

## Goals for This Year
- Complete first Olympic distance triathlon
- Run a sub-18 5K
- Build cycling FTP to 250W
- Improve swim efficiency
```

#### Example 3: Simple Preferences

```markdown
I ride my Peloton bike 4-5 times per week. My FTP is 280W. I like doing Power Zone rides and following a polarized training plan. I also run twice a week for cross-training, usually easy pace for 30-45 minutes.
```

## AI Generation Process

### What the AI Analyzes

1. **Sport Detection**
   - Identifies mentioned sports
   - Maps to Strava activity types
   - Creates sport configurations

2. **Metric Extraction**
   - Finds threshold values (FTP, LTHR)
   - Determines primary metrics per sport
   - Sets up zone calculations

3. **Philosophy Recognition**
   - Detects training approach keywords
   - Sets zone distribution percentages
   - Configures philosophy in profile

4. **Equipment Parsing**
   - Identifies specific equipment
   - Adds to sport configurations
   - Sets equipment capabilities

5. **Zone Creation**
   - Creates appropriate zone models
   - Maps to 3-zone polarized system
   - Sets zone boundaries

### Generated Configuration Structure

```json
{
  "version": "1.0.0",
  "user_profile": {
    "philosophy": "polarized",
    "volume_levels": {
      "low": 5,
      "medium": 10,
      "high": 15
    },
    "thresholds": {
      "ftp": 301,
      "lthr": 155,
      "max_hr": 185
    }
  },
  "sports": [
    {
      "name": "Cycling",
      "activity_types": ["Ride", "VirtualRide"],
      "primary_metric": {
        "type": "power",
        "unit": "watts",
        "threshold_field": "ftp"
      },
      "zones": [...],
      "zone_breakdown_percentage": {
        "1": 80.0,
        "2": 10.0,
        "3": 10.0
      },
      "equipment": [
        {
          "name": "Peloton",
          "capabilities": ["power_meter", "cadence", "indoor"]
        }
      ]
    }
  ]
}
```

## Best Practices

### DO:
- ✅ Include specific numbers (FTP, heart rates, paces)
- ✅ Mention equipment brands and models
- ✅ State training philosophy explicitly
- ✅ Include weekly volume ranges
- ✅ List concrete goals with timelines
- ✅ Mention any constraints or preferences

### DON'T:
- ❌ Use vague terms ("I'm pretty fit")
- ❌ Forget to mention all sports you do
- ❌ Leave out threshold values if known
- ❌ Use non-standard terminology
- ❌ Write in complex narrative form

## Reviewing Generated Configuration

### What to Check

1. **Sports Coverage**
   - All mentioned sports included?
   - Correct activity type mappings?
   - Appropriate primary metrics?

2. **Threshold Values**
   - FTP, LTHR correctly extracted?
   - Values in reasonable ranges?
   - Applied to correct sports?

3. **Zone Setup**
   - Zones follow expected model?
   - Boundaries make sense?
   - Mapped to 3-zone system?

4. **Philosophy & Distribution**
   - Matches stated preference?
   - Percentages sum to 100%?
   - Sport-specific overrides correct?

### Making Adjustments

After generation, you can:

1. **Edit JSON directly** in the Sport Config tab
2. **Use Zone Distribution Editor** for percentages
3. **Modify individual values** via UI
4. **Regenerate** with updated preferences

## Advanced Features

### Incremental Updates

Update existing config with new preferences:

```json
{
  "preferences": "I just got a power meter for running...",
  "update_existing": true
}
```

### AI Provider Selection

Choose specific AI provider:

```json
{
  "preferences": "...",
  "ai_provider": "openai"  // or "claude"
}
```

### Preview Mode

Generate without saving:

```bash
curl -X POST http://localhost:5000/api/settings/preview-config
```

## Troubleshooting

### Common Issues

**"No AI provider available"**
- Set OPENAI_API_KEY or ANTHROPIC_API_KEY in .env
- Check API key validity
- Ensure credits/balance available

**"Failed to parse configuration"**
- AI response was incomplete
- Try regenerating
- Simplify preferences
- Check for special characters

**Missing sports/equipment**
- Be more explicit in preferences
- Use recognized keywords
- Mention sport multiple times
- Include activity context

### AI Provider Differences

**OpenAI (GPT-4)**:
- Better at complex preferences
- Handles narrative style well
- More creative interpretations

**Claude**:
- More structured output
- Better at following templates
- Consistent JSON formatting

## Integration Examples

### Workflow Automation

```python
# Generate and apply configuration
from config_generator import ConfigGenerator

generator = ConfigGenerator()
config = generator.generate_config()

# Apply to system
config_service.update_config(config)
```

### Scheduled Updates

```python
# Weekly preference review
def weekly_config_update():
    if preferences_changed():
        new_config = generator.generate_config()
        notify_user_of_changes(new_config)
```

## Summary

The AI Configuration Generator bridges the gap between how athletes think about training and how software needs structured data. By writing natural language preferences, you can quickly generate comprehensive configurations that include:

- Multiple sports with appropriate metrics
- Equipment-specific settings  
- Personalized zone distributions
- Training philosophy alignment
- Threshold-based calculations

The key to success is being specific about your numbers, equipment, and goals while using recognized terminology that the AI can parse effectively.