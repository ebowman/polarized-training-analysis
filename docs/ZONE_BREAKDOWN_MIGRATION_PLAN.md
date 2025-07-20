# Zone Breakdown Configuration Migration Plan

## Overview
This document outlines the migration strategy for adding zone breakdown percentage configuration to existing sport.json files while maintaining backward compatibility.

## Schema Extension

### New Field Location
The zone breakdown configuration will be added to each sport in the `sports` array:

```json
{
  "sports": [
    {
      "name": "Cycling",
      // ... existing fields ...
      "zone_breakdown_percentage": {
        "zone1": 80,
        "zone2": 10,
        "zone3": 10
      }
    }
  ]
}
```

### Field Definition
```json
"zone_breakdown_percentage": {
  "type": "object",
  "description": "Percentage distribution for polarized training zones",
  "properties": {
    "zone1": {
      "type": "number",
      "minimum": 0,
      "maximum": 100,
      "description": "Percentage for low intensity (polarized zone 1)"
    },
    "zone2": {
      "type": "number",
      "minimum": 0,
      "maximum": 100,
      "description": "Percentage for moderate intensity (polarized zone 2)"
    },
    "zone3": {
      "type": "number",
      "minimum": 0,
      "maximum": 100,
      "description": "Percentage for high intensity (polarized zone 3)"
    }
  },
  "required": ["zone1", "zone2", "zone3"],
  "additionalProperties": false
}
```

## Migration Strategy

### Automatic Migration Process

1. **Detection Phase**
   - Check if `zone_breakdown_percentage` exists for each sport
   - If missing, trigger migration

2. **Philosophy-Based Defaults**
   ```python
   DEFAULT_ZONE_BREAKDOWNS = {
       "polarized": {"zone1": 80, "zone2": 10, "zone3": 10},
       "pyramidal": {"zone1": 70, "zone2": 20, "zone3": 10},
       "threshold": {"zone1": 50, "zone2": 35, "zone3": 15},
       "custom": {"zone1": 80, "zone2": 10, "zone3": 10}  # Default to polarized
   }
   ```

3. **Migration Logic**
   ```python
   def migrate_sport_config(config):
       philosophy = config.get("user_profile", {}).get("philosophy", "polarized")
       default_breakdown = DEFAULT_ZONE_BREAKDOWNS.get(philosophy, DEFAULT_ZONE_BREAKDOWNS["polarized"])
       
       for sport in config.get("sports", []):
           if "zone_breakdown_percentage" not in sport:
               sport["zone_breakdown_percentage"] = default_breakdown.copy()
       
       return config
   ```

4. **Validation**
   - Ensure zone percentages sum to 100%
   - Validate each percentage is between 0-100
   - Log any validation issues

### Backward Compatibility

1. **Reading Legacy Files**
   - If `zone_breakdown_percentage` is missing, use defaults
   - Don't fail on missing field
   - Log migration actions for transparency

2. **API Compatibility**
   ```python
   def get_zone_breakdown(sport_config):
       # New way: read from config
       if "zone_breakdown_percentage" in sport_config:
           return sport_config["zone_breakdown_percentage"]
       
       # Legacy fallback: use philosophy defaults
       philosophy = self.config.user_profile.philosophy
       return DEFAULT_ZONE_BREAKDOWNS.get(philosophy, DEFAULT_ZONE_BREAKDOWNS["polarized"])
   ```

3. **UI Compatibility**
   - Settings page shows zone breakdown if available
   - Allows editing zone percentages
   - Validates on save

## Integration Workflow

### From workout_preferences_personal.md to sport.json

1. **AI Analysis Phase**
   - Parse workout_preferences_personal.md
   - Extract training philosophy preference
   - Identify sport-specific zone preferences if mentioned
   - Generate recommended zone breakdowns

2. **Generation Template**
   ```python
   def generate_sport_config_from_preferences(preferences_text):
       # Extract philosophy
       philosophy = extract_philosophy(preferences_text)
       
       # Generate zone breakdown
       zone_breakdown = customize_zone_breakdown(
           base=DEFAULT_ZONE_BREAKDOWNS[philosophy],
           preferences=preferences_text
       )
       
       # Apply to each sport
       for sport in sports:
           sport["zone_breakdown_percentage"] = zone_breakdown
   ```

3. **User Confirmation**
   - Show generated configuration
   - Allow manual adjustments
   - Save to sport_config.json

## Testing Strategy

### Unit Tests
```python
def test_migration_adds_zone_breakdown():
    """Test that migration adds zone_breakdown_percentage"""
    config = {"sports": [{"name": "Cycling"}]}
    migrated = migrate_sport_config(config)
    assert "zone_breakdown_percentage" in migrated["sports"][0]

def test_zone_breakdown_validation():
    """Test zone breakdown percentage validation"""
    breakdown = {"zone1": 80, "zone2": 10, "zone3": 10}
    assert validate_zone_breakdown(breakdown) == True
    
    invalid = {"zone1": 80, "zone2": 10, "zone3": 20}  # Sum = 110
    assert validate_zone_breakdown(invalid) == False
```

### Integration Tests
- Test migration with existing sport.json files
- Test UI updates with zone breakdown
- Test zone calculation with custom breakdowns
- Test backward compatibility with legacy files

## Implementation Timeline

1. **Phase 1: Schema Update** (Current)
   - Update sport_config_schema.json
   - Add validation logic

2. **Phase 2: Migration Logic**
   - Implement automatic migration
   - Add to SportConfigService

3. **Phase 3: UI Integration**
   - Update settings page
   - Add zone breakdown editor

4. **Phase 4: AI Integration**
   - Connect to workout_preferences_personal.md
   - Generate configurations

## Risk Mitigation

1. **Data Loss Prevention**
   - Create backup before migration
   - Validate after migration
   - Provide rollback option

2. **User Communication**
   - Show migration notification
   - Explain new feature benefits
   - Provide documentation

3. **Gradual Rollout**
   - Feature flag for zone breakdown
   - Monitor for issues
   - Collect user feedback

## Success Metrics

1. **Technical Metrics**
   - 100% successful migrations
   - No data loss
   - Backward compatibility maintained

2. **User Metrics**
   - Zone breakdown customization usage
   - Settings page engagement
   - Support ticket volume

## Conclusion

This migration plan ensures a smooth transition to zone breakdown configuration while maintaining full backward compatibility. The automatic migration based on training philosophy provides sensible defaults while allowing full customization through the UI and AI-assisted configuration generation.