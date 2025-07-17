# Sport Configuration Integration Guide

## Overview

The Polarized Training Analysis system uses a comprehensive sport configuration system that personalizes training zones, workout recommendations, and analysis for individual users. This guide covers how sport configuration integrates across the application.

## Core Components

### 1. Sport Configuration File (`sport_config.json`)

The central configuration file that defines:
- **User Profile**: Training philosophy, thresholds, preferences
- **Sports**: Individual sport definitions (Cycling, Running, etc.)
- **Zones**: Detailed zone definitions for each sport
- **Equipment**: Available equipment and preferences
- **Metrics**: Primary and secondary metrics for each sport

### 2. Sport Configuration Service (`sport_config_service.py`)

The main service that:
- Loads and validates sport configurations
- Calculates zones based on user thresholds
- Provides zone distribution targets
- Manages sport-specific settings

### 3. Integration Points

#### Web Server (`web_server.py`)
- **Zone Calculations**: `get_zone_calculations()` provides personalized zone data
- **Route Integration**: All major routes use sport config data
- **Template Variables**: Passes sport-specific data to templates

#### AI Recommendations (`ai_recommendations.py`)
- **Zone Context**: Includes personalized zones in AI prompts
- **Training Philosophy**: Uses config philosophy for recommendations
- **Equipment Awareness**: Suggests equipment from sport config

#### Training Analysis (`training_analysis.py`)
- **Zone Classification**: Uses sport config zones for activity analysis
- **Threshold-Based**: Calculates zones from user's actual thresholds
- **Sport-Specific**: Different zone models for different sports

## Feature Integration

### Zone Mapping Guide (`/zone_mapping_guide`)

**Before Sport Config**:
```html
<td>Zone 2: 55-75% FTP</td>
<td>Zone 3: 75-90% FTP</td>
```

**After Sport Config**:
```html
<td>Zone 2: {{ pz2_range }}</td>  <!-- "168-225W" -->
<td>Zone 3: {{ pz3_range }}</td>  <!-- "228-270W" -->
```

**Benefits**:
- Real watt/BPM ranges instead of percentages
- Automatically updates when thresholds change
- Sport-specific zone definitions
- Training philosophy integration

### AI Workout Recommendations

**Enhanced Context**:
```python
# AI prompt now includes:
zones = sport_config_service.calculate_zones(cycling_sport, MetricType.POWER, ftp)
zone_lines = [f"- {name}: {lower}-{upper}W = Polarized Zone {pz}" 
              for name, lower, upper, pz in zones]
```

**Results**:
- More accurate zone targeting in recommendations
- Equipment-specific suggestions
- Philosophy-aware training distribution
- Personalized intensity guidance

### Settings Page Integration

**Dynamic Configuration**:
- Sport config JSON editor
- Real-time validation
- Philosophy selection
- Threshold management

## Configuration Examples

### Basic Sport Config Structure
```json
{
  "version": "1.0.0",
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
      "primary_metric": {
        "type": "power",
        "threshold_field": "ftp"
      },
      "zones": [
        {
          "name": "Recovery",
          "lower": 0,
          "upper": 55,
          "polarized_zone": 1
        }
      ]
    }
  ]
}
```

### Zone Calculation Flow
```python
# 1. Load sport config
sport_config_service = SportConfigService()

# 2. Get sport definition
cycling_sport = sport_config_service.get_sport_by_name('Cycling')

# 3. Calculate zones
zones = sport_config_service.calculate_zones(
    cycling_sport, 
    MetricType.POWER, 
    ftp=301
)

# 4. Result: [(name, lower, upper, polarized_zone), ...]
# [("Recovery", 0, 165, 1), ("Endurance", 168, 225, 1), ...]
```

## Migration and Compatibility

### Feature Flag System
```python
USE_SPORT_CONFIG = os.getenv('USE_SPORT_CONFIG', 'true').lower() == 'true'

if USE_SPORT_CONFIG and SportConfigService:
    # Use sport config zones
    return _calculate_zones_with_sport_config(max_hr, ftp, lthr)
else:
    # Fall back to legacy calculations
    return _calculate_legacy_zones(max_hr, ftp, lthr)
```

### Backward Compatibility
- Legacy environment variable support
- Graceful fallback to defaults
- No breaking changes for existing users
- Optional sport config adoption

## Best Practices

### Configuration Management
1. **Validation**: Always validate sport config on load
2. **Defaults**: Provide sensible defaults for missing values
3. **Error Handling**: Graceful degradation when config is invalid
4. **Updates**: Support live configuration updates

### Zone Calculations
1. **Threshold Sync**: Keep thresholds synchronized across systems
2. **Sport-Specific**: Use appropriate metrics for each sport
3. **Fallbacks**: Handle missing or invalid threshold values
4. **Caching**: Cache calculated zones for performance

### Template Integration
1. **Conditional Rendering**: Handle missing zone data gracefully
2. **Personalization**: Show user-specific values when available
3. **Defaults**: Fall back to generic content when needed
4. **Testing**: Verify templates work with various config states

## Future Enhancements

### Planned Features
- **Multi-User Support**: User-specific configurations
- **Advanced Zones**: Custom zone formulas and models
- **Equipment Integration**: Equipment-specific zone adjustments
- **Historical Tracking**: Zone performance over time

### Extension Points
- **New Sports**: Easy addition of new sport definitions
- **Custom Metrics**: Support for sport-specific metrics
- **Zone Models**: Pluggable zone calculation strategies
- **Integration APIs**: External system integration

## Troubleshooting

### Common Issues
1. **Invalid Config**: Check JSON syntax and validation errors
2. **Missing Thresholds**: Verify FTP, Max HR, LTHR values
3. **Zone Calculation Errors**: Check metric types and sport definitions
4. **Template Rendering**: Ensure all required variables are provided

### Debug Tools
- **Validation**: Use sport config validation tools
- **Testing**: Run backward compatibility tests
- **Logging**: Check sport config service logs
- **Manual Testing**: Test zone calculations manually

## Related Documentation
- [Zone Mapping Guide](./ZONE_MAPPING_GUIDE.md)
- [Settings Implementation](../SETTINGS_IMPLEMENTATION_GUIDE.md)
- [Sport Config Service](../sport_config_service.py)
- [Backward Compatibility](../test_backward_compatibility.py)