# Requirements: Configurable Zone Breakdown Feature

## Executive Summary

This document defines the requirements for implementing a configurable zone breakdown feature that allows users to specify their preferred training zone distribution (e.g., 80/10/10, 70/20/10, 60/30/10) through workout preferences and have the system automatically generate appropriate `sport_config.json` configurations.

## Current State Analysis

### 1. Hardcoded Zone Distributions

Currently, the system hardcodes zone distributions in multiple locations:

#### Primary Locations:
- **sport_config_service.py** (lines 293-303): Hardcoded distributions for each philosophy
  - Polarized: 80/10/10
  - Pyramidal: 70/20/10
  - Threshold: 60/30/10
  - Custom: Falls back to polarized if no preferences

- **zone_calculator.py** (lines 350-352): Duplicate hardcoded values
- **web_server.py** (line 391): Hardcoded 80/10/10 for zone mapping guide
- **ai_recommendations.py** (lines 732, 762): Hardcoded 80/10/10 references
- **constants.py** (line 13): Comment about 80/10/10 approach
- **Templates** (index.html): Multiple hardcoded references to 80/10/10
- **config_generator.py** (line 130): AI prompt hardcodes "Zone 1: 80%, Zone 2: 10%, Zone 3: 10%"

### 2. Current Configuration Structure

The `sport_config.json` currently supports:
```json
{
  "user_profile": {
    "philosophy": "polarized",  // or "pyramidal", "threshold", "custom"
    "preferences": {},  // Currently unused for zone distribution
    "thresholds": {...}
  }
}
```

### 3. TrainingPhilosophy Enum

Supports four values:
- POLARIZED = "polarized"
- PYRAMIDAL = "pyramidal"
- THRESHOLD = "threshold"
- CUSTOM = "custom"

The CUSTOM option exists but lacks implementation for custom zone distributions.

## Requirements

### 1. User Preference Format

Users should be able to specify zone breakdowns in `workout_preferences.md` using clear, intuitive formats:

#### Option A: Percentage Format
```markdown
## Training Zone Distribution
- Zone 1 (Easy/Aerobic): 75%
- Zone 2 (Threshold/Tempo): 15%
- Zone 3 (High Intensity/VO2Max): 10%
```

#### Option B: Ratio Format
```markdown
## Training Zone Distribution
75/15/10 (Zone 1/Zone 2/Zone 3)
```

#### Option C: Named Philosophy with Custom Values
```markdown
## Training Philosophy
Custom Polarized: 75% easy, 15% threshold, 10% high intensity
```

### 2. AI-Driven Configuration Generation

The system should:

1. **Parse preferences** from `workout_preferences.md`
2. **Validate** zone distributions (must sum to 100%)
3. **Generate** appropriate `sport_config.json` entries:
   ```json
   {
     "user_profile": {
       "philosophy": "custom",
       "preferences": {
         "zone_distribution": {
           "1": 75.0,
           "2": 15.0,
           "3": 10.0
         }
       }
     }
   }
   ```

### 3. System Integration Points

All the following components need updates to support custom zone distributions:

#### A. Core Services
1. **sport_config_service.py**
   - Update `get_zone_distribution_target()` to properly read custom distributions
   - Add validation for custom distributions
   - Add method to update zone distribution preferences

2. **zone_calculator.py**
   - Remove hardcoded values
   - Always delegate to sport_config_service

3. **ai_recommendations.py**
   - Make zone target references dynamic
   - Update deficit calculations to use configured targets
   - Update all hardcoded percentage references

#### B. Web Components
1. **web_server.py**
   - Update zone mapping guide endpoint to use dynamic values
   - Pass actual zone targets to templates

2. **Templates (index.html, zone_mapping_guide.html)**
   - Replace hardcoded 80/10/10 with dynamic values
   - Update JavaScript calculations to use passed targets
   - Update UI text to reflect configured philosophy

#### C. Configuration Management
1. **config_generator.py**
   - Update AI prompt to look for zone distribution preferences
   - Remove hardcoded "Zone 1: 80%, Zone 2: 10%, Zone 3: 10%" from line 130
   - Add logic to parse zone distributions from preferences text
   - Generate appropriate sport_config entries with custom distributions
   - Validate distributions sum to 100%
   - If no distribution specified, ask AI to determine based on user's goals and experience

### 4. Validation Requirements

1. **Zone Distribution Validation**
   - Sum must equal 100% (±0.1% for rounding)
   - Each zone must be between 0-100%
   - Zone 1 should typically be the largest percentage
   - Warning if distributions are extreme (e.g., Zone 3 > 30%)

2. **Preference Parsing**
   - Handle multiple formats gracefully
   - Provide clear error messages for invalid formats
   - Default to standard distributions if parsing fails

### 5. User Experience Requirements

1. **Settings Page Enhancement**
   - Add zone distribution configuration UI
   - Visual representation of current distribution
   - Preset options (Polarized, Pyramidal, Threshold, Custom)
   - Custom input with validation

2. **Zone Mapping Guide**
   - Display actual configured targets
   - Show how current training compares to targets
   - Provide recommendations based on deficits

3. **AI Recommendations**
   - Use configured targets for all calculations
   - Adjust recommendations based on custom distributions
   - Explain why certain workouts are recommended

### 6. Backward Compatibility

1. **Migration Path**
   - Existing configs without zone_distribution should work
   - Default to philosophy-based distributions
   - Smooth upgrade path for existing users

2. **API Compatibility**
   - Maintain existing API contracts
   - Add new endpoints for zone distribution management
   - Version API changes appropriately

## Implementation Priority

1. **Phase 1: Core Support**
   - Update sport_config_service.py to read custom distributions
   - Update zone_calculator.py to use service
   - Add preference parsing to config_generator.py

2. **Phase 2: UI Integration**
   - Update web_server.py endpoints
   - Modify templates to use dynamic values
   - Add settings page configuration

3. **Phase 3: AI Enhancement**
   - Update ai_recommendations.py
   - Enhance workout recommendations
   - Add distribution-aware coaching tips

## Success Criteria

1. Users can specify any zone distribution that sums to 100%
2. All UI components display the configured distribution
3. AI recommendations adapt to custom distributions
4. No hardcoded 80/10/10 references remain in the codebase
5. Settings page allows easy distribution configuration
6. Zone mapping guide shows personalized targets

## Technical Debt to Address

1. Remove duplicate hardcoded values across files
2. Centralize zone distribution logic in sport_config_service
3. Update all string formatting to use configured values
4. Ensure consistent data types (float vs int percentages)
5. Add comprehensive tests for custom distributions

## Risks and Mitigations

1. **Risk**: Invalid user input
   - **Mitigation**: Robust validation and clear error messages

2. **Risk**: Breaking existing functionality
   - **Mitigation**: Comprehensive testing and backward compatibility

3. **Risk**: Confusing UI
   - **Mitigation**: Clear labels and helpful tooltips

4. **Risk**: Performance impact
   - **Mitigation**: Cache calculated distributions

## Example Configurations

### Example 1: Custom Polarized Distribution
**User Preference in workout_preferences.md:**
```markdown
## Training Zone Distribution
I prefer a slightly less polarized approach:
- Zone 1 (Easy): 75%
- Zone 2 (Threshold): 15%  
- Zone 3 (High Intensity): 10%
```

**Generated sport_config.json:**
```json
{
  "user_profile": {
    "philosophy": "custom",
    "preferences": {
      "zone_distribution": {
        "1": 75.0,
        "2": 15.0,
        "3": 10.0
      }
    }
  }
}
```

### Example 2: Named Philosophy
**User Preference:**
```markdown
I follow a pyramidal training approach
```

**Generated sport_config.json:**
```json
{
  "user_profile": {
    "philosophy": "pyramidal"
  }
}
```
(System uses built-in 70/20/10 distribution)

### Example 3: Sport-Specific (Future Enhancement)
**User Preference:**
```markdown
## Training Philosophy
- Cycling: Polarized (80/10/10)
- Running: Pyramidal (70/20/10)
- Swimming: Threshold-focused (60/30/10)
```

## Future Enhancements

1. **Sport-Specific Distributions**: Different distributions per sport
2. **Seasonal Variations**: Change distributions by training phase
3. **Auto-Optimization**: AI suggests distribution based on progress
4. **Distribution History**: Track how distributions change over time
5. **Team/Coach Integration**: Share distributions with coaches