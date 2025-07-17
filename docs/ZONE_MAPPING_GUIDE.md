# Zone Mapping Guide - Sport Config Integration

## Overview

The Zone Mapping Guide (`/zone_mapping_guide`) is a comprehensive reference page that helps users understand different training zone systems and how they relate to each other. With sport config integration, the guide now provides **personalized zone information** based on the user's actual thresholds and training philosophy.

## Features

### 🎯 Personalized Configuration Display
- **Training Philosophy**: Shows user's chosen approach (Polarized, Pyramidal, etc.)
- **Individual Thresholds**: Displays actual FTP, Max HR, and LTHR values
- **Zone Distribution Targets**: Custom percentages based on training philosophy

### 📊 Dynamic Zone Tables

#### Power Zones (Cycling)
- **Real Watt Ranges**: Calculated from user's actual FTP
- **Sport-Specific**: Uses zones defined in sport config for Cycling
- **Example**: Zone 2 shows "168-225W" instead of "55-75% FTP"

#### Heart Rate Zones (Rowing/Running)
- **Real BPM Ranges**: Calculated from user's Max HR and LTHR
- **Sport-Specific**: Uses zones defined in sport config for Running/Rowing
- **Example**: Zone 2 shows "119-140 bpm" instead of "70-82% Max HR"

### 🏃 Personalized Workout Examples
- **Cycling**: "60-min Power Zone 2 Endurance Ride (168-225W)"
- **Rowing**: "45-min HR Zone 2 Steady State (119-140 bpm)"
- **Training Distribution**: Shows actual zone targets (80/10/10 vs 70/20/10)

## Technical Implementation

### Data Flow
```
sport_config.json → SportConfigService → get_zone_calculations() → zone_mapping_guide.html
```

### Template Variables
The template receives personalized data from `get_zone_calculations()`:

```python
{
    'training_philosophy': 'polarized',
    'zone_targets': {1: 80.0, 2: 10.0, 3: 10.0},
    'ftp': 301,
    'max_hr': 171,
    'lthr': 153,
    'pz1_range': '0-165W',
    'pz2_range': '168-225W',
    # ... more power zones
    'hr1_range': '85-119',
    'hr2_range': '119-140',
    # ... more heart rate zones
    'hr_zone1_combined': '85-140 bpm',
    'hr_zone2_combined': '140-159 bpm',
    'hr_zone3_combined': '159+ bpm'
}
```

### Dynamic Rendering
- **Conditional Tables**: Only shows zones that exist in sport config
- **Fallback Values**: Uses defaults when sport config unavailable
- **Real-Time Updates**: Changes automatically when sport config is modified

## Configuration Requirements

### Sport Config Structure
The zone guide uses zones defined in `sport_config.json`:

```json
{
  "user_profile": {
    "philosophy": "polarized",
    "thresholds": {
      "ftp": 301,
      "lthr": 153,
      "max_hr": 171
    }
  },
  "sports": [
    {
      "name": "Cycling",
      "primary_metric": {"type": "power", "threshold_field": "ftp"},
      "zones": [
        {"name": "Recovery", "lower": 0, "upper": 55, "polarized_zone": 1},
        {"name": "Endurance", "lower": 56, "upper": 75, "polarized_zone": 1}
        // ... more zones
      ]
    }
  ]
}
```

### Environment Variables
Falls back to these when sport config unavailable:
- `FTP`: Functional Threshold Power (watts)
- `MAX_HEART_RATE`: Maximum heart rate (bpm)
- `AVERAGE_FTP_HR`: Lactate threshold heart rate (bpm)

## Benefits

### For Users
1. **Actionable Guidance**: Precise watt/BPM ranges instead of percentages
2. **Equipment-Specific**: Matches Peloton power zones and Concept2 HR zones
3. **Training Philosophy Aware**: Reflects chosen training approach
4. **Always Current**: Updates automatically with threshold changes

### For Developers
1. **Dynamic Content**: Template adapts to sport config changes
2. **Maintainable**: Single source of truth for zone calculations
3. **Extensible**: Easy to add new sports or zone systems
4. **Backward Compatible**: Works with or without sport config

## Usage Examples

### Basic Zone Reference
Users can quickly look up their personal zones:
- "What's my Power Zone 3 range?" → "228-270W"
- "What heart rate for easy rowing?" → "119-140 bpm"

### Workout Planning
- Peloton: "Take a Power Zone 2-3 Endurance ride" → Use 168-270W
- Concept2: "Row in HR Zone 2" → Target 119-140 bpm

### Training Distribution
- Zone 1 target: 80% (or custom from philosophy)
- Zone 2 target: 10% (or custom from philosophy)  
- Zone 3 target: 10% (or custom from philosophy)

## Route Information

- **URL**: `/zone_mapping_guide`
- **Method**: GET
- **Template**: `templates/zone_mapping_guide.html`
- **Data Source**: `get_zone_calculations()` from `web_server.py`

## Related Files

- **Template**: `templates/zone_mapping_guide.html`
- **Data Function**: `web_server.py:get_zone_calculations()`
- **Sport Config**: `sport_config.json`
- **Service**: `sport_config_service.py`

## Testing

The zone guide can be tested by:
1. Modifying sport config thresholds
2. Changing training philosophy
3. Adding/removing zone definitions
4. Verifying template renders correctly

All changes should be reflected immediately in the zone guide display.