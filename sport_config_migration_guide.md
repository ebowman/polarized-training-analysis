# Sport Configuration Schema Migration Guide

## Overview
This guide explains how to migrate from the current sport configuration schema (v1.0.0) to the extended schema (v2.0.0) that supports configurable zone distribution percentages per sport.

## Key Changes

### 1. Zone Distribution Configuration
The new schema adds support for configurable zone distribution percentages at two levels:

#### Global Level (user_profile)
```json
"user_profile": {
  "default_zone_distribution": {
    "zone1": 80,
    "zone2": 10,
    "zone3": 10
  }
}
```

#### Sport Level (per sport)
```json
"sports": [{
  "name": "Cycling",
  "zone_distribution": {
    "zone1": 80,
    "zone2": 6,
    "zone3": 14
  }
}]
```

### 2. Priority Rules
- Sport-level `zone_distribution` overrides the global `default_zone_distribution`
- If a sport has no `zone_distribution`, it uses the global default
- If neither exists, the system can fall back to philosophy-based defaults

### 3. Backwards Compatibility
- The `polarized_zone` field in each zone definition is retained
- Existing files without `zone_distribution` will continue to work
- The `philosophy` field remains for reference but zone percentages take precedence

## Migration Steps

### Option 1: Manual Migration
1. Add `default_zone_distribution` to `user_profile`:
   ```json
   "default_zone_distribution": {
     "zone1": 80,
     "zone2": 10,
     "zone3": 10
   }
   ```

2. For each sport that needs different percentages, add `zone_distribution`:
   ```json
   "zone_distribution": {
     "zone1": 86,
     "zone2": 4,
     "zone3": 10
   }
   ```

3. Update version to "2.0.0"

### Option 2: Automated Migration Script
```python
def migrate_sport_config(config):
    # Update version
    config['version'] = '2.0.0'
    
    # Add default zone distribution based on philosophy
    philosophy = config.get('user_profile', {}).get('philosophy', 'polarized')
    if philosophy == 'polarized':
        default_dist = {"zone1": 80, "zone2": 10, "zone3": 10}
    elif philosophy == 'pyramidal':
        default_dist = {"zone1": 70, "zone2": 20, "zone3": 10}
    else:
        default_dist = {"zone1": 60, "zone2": 25, "zone3": 15}
    
    if 'user_profile' not in config:
        config['user_profile'] = {}
    config['user_profile']['default_zone_distribution'] = default_dist
    
    return config
```

## Examples

### Cycling with Custom Distribution
```json
{
  "name": "Cycling",
  "zone_distribution": {
    "zone1": 80,
    "zone2": 6,
    "zone3": 14
  },
  "zones": [
    {"name": "Recovery", "lower": 0, "upper": 55, "polarized_zone": 1},
    {"name": "Endurance", "lower": 56, "upper": 75, "polarized_zone": 1},
    {"name": "Tempo", "lower": 76, "upper": 90, "polarized_zone": 2},
    {"name": "Threshold", "lower": 91, "upper": 105, "polarized_zone": 2},
    {"name": "VO2 Max", "lower": 106, "upper": 120, "polarized_zone": 3},
    {"name": "Anaerobic", "lower": 121, "upper": 150, "polarized_zone": 3},
    {"name": "Neuromuscular", "lower": 151, "upper": 200, "polarized_zone": 3}
  ]
}
```

### Rowing with Different Distribution
```json
{
  "name": "Rowing",
  "zone_distribution": {
    "zone1": 86,
    "zone2": 4,
    "zone3": 10
  },
  "zones": [
    {"name": "UT2", "lower": 0, "upper": 75, "polarized_zone": 1},
    {"name": "UT1", "lower": 76, "upper": 85, "polarized_zone": 1},
    {"name": "AT", "lower": 86, "upper": 95, "polarized_zone": 2},
    {"name": "TR", "lower": 96, "upper": 105, "polarized_zone": 3},
    {"name": "AN", "lower": 106, "upper": 120, "polarized_zone": 3}
  ]
}
```

## Benefits

1. **Sport-Specific Optimization**: Different sports can have different optimal zone distributions
2. **Flexibility**: Easy to adjust training focus per sport
3. **Data-Driven**: Zone percentages can be adjusted based on actual training data
4. **Backwards Compatible**: Existing configurations continue to work

## Implementation Notes

- The zone distribution percentages must sum to 100
- Zone distributions affect training recommendations and analysis
- The UI should display actual percentages instead of just philosophy names
- Consider adding validation to ensure zone percentages are valid