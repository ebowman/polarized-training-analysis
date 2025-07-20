# Integration Map: Preferences → Prompts → Configuration

## Overview

This document maps the complete integration flow from user preferences to generated configuration, identifying implemented components, gaps, and required connections.

## Current System Architecture

```
┌─────────────────────────────────┐
│  User Input Layer               │
├─────────────────────────────────┤
│ • workout_preferences.md        │ ← Natural language preferences
│ • Settings UI (/settings)       │ ← Direct configuration
│ • Zone Guide (/zone_mapping)    │ ← View-only (personalized)
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  Processing Layer               │
├─────────────────────────────────┤
│ • config_generator.py           │ ← AI-powered generation (EXISTS)
│ • ai_providers.py               │ ← OpenAI/Claude integration (EXISTS)
│ • Prompt Templates              │ ← YAML templates (EXISTS)
└──────────┬──────────────────────┘
           │
           ▼
┌─────────────────────────────────┐
│  Configuration Layer            │
├─────────────────────────────────┤
│ • sport_config.json             │ ← Structured configuration
│ • SportConfigService            │ ← Configuration management
│ • Zone calculations             │ ← Real-time personalization
└─────────────────────────────────┘
```

## Implemented Components

### 1. Natural Language Input
**File**: `workout_preferences.md`
- **Status**: ✅ Template exists
- **Purpose**: User writes preferences in natural language
- **Example Content**:
  - Training goals (FTP improvement, etc.)
  - Equipment (Peloton, Concept2, etc.)
  - Current fitness metrics
  - Training philosophy preferences

### 2. AI Configuration Generator
**File**: `config_generator.py`
- **Status**: ✅ Fully implemented
- **Key Features**:
  - `ConfigGenerator` class with AI provider support
  - Generates `sport_config.json` from preferences
  - Fallback logic for basic configurations
  - Support for multiple sports detection

**Key Methods**:
```python
generate_config(preferences_text) → TrainingConfig
_generate_config_json(preferences_text) → str  # AI prompt
_dict_to_config(config_dict) → TrainingConfig
update_config_from_preferences(existing_config, preferences_text) → TrainingConfig
```

### 3. AI Providers
**File**: `ai_providers.py`
- **Status**: ✅ Implemented (inferred)
- **Providers**: OpenAI, Claude
- **Integration**: Used by ConfigGenerator

### 4. Sport Configuration Service
**File**: `sport_config_service.py`
- **Status**: ✅ Fully implemented
- **Key Features**:
  - Zone calculations with multiple strategies
  - Training philosophy support
  - Custom zone distribution per sport
  - Real-time threshold updates

**Key Methods**:
```python
get_zone_distribution_target(sport_name) → Dict[int, float]
update_user_zone_distribution(zone_distribution) → bool
update_sport_zone_distribution(sport_name, zone_distribution) → bool
calculate_zones(sport, metric_type, threshold) → List[Tuple]
```

### 5. Zone Mapping Guide
**File**: `templates/zone_mapping_guide.html`
- **Status**: ✅ Fully implemented
- **Features**:
  - Shows personalized power zones (watts)
  - Shows personalized heart rate zones (bpm)
  - Displays training philosophy and distribution
  - Real-time calculations from sport config

### 6. Prompt Architecture
**Directory**: `prompts/`
- **Status**: ✅ Well-documented
- **Components**:
  - Main orchestrator architecture
  - Sport-specific templates (cycling, running, etc.)
  - Context-based templates
  - Template validation system

## Data Flow Analysis

### Current Working Flow

1. **Configuration → Display**:
   ```
   sport_config.json 
   → SportConfigService.get_zone_calculations()
   → web_server.py renders template
   → zone_mapping_guide.html shows personalized data
   ```
   **Status**: ✅ Working perfectly

2. **Settings UI → Configuration**:
   ```
   /settings page
   → User edits sport_config_json textarea
   → POST /api/settings
   → Updates sport_config.json
   ```
   **Status**: ✅ Working (manual JSON editing)

### Missing/Disconnected Flow

1. **Preferences → Configuration**:
   ```
   workout_preferences.md
   → ??? (No automatic trigger)
   → config_generator.py (exists but not integrated)
   → sport_config.json
   ```
   **Status**: ❌ Not connected to UI

## Identified Gaps

### 1. Missing UI Integration
- **Gap**: No UI button/page to trigger AI generation
- **Impact**: Users must run `python config_generator.py` manually
- **Solution**: Add "Generate from Preferences" button in settings

### 2. Missing API Endpoint
- **Gap**: No `/api/generate-config` endpoint
- **Impact**: Can't trigger generation from web UI
- **Solution**: Add endpoint in `web_server.py`

### 3. Preferences File Management
- **Gap**: No UI to edit `workout_preferences.md`
- **Impact**: Users must edit file directly
- **Solution**: Add preferences editor in settings or separate page

### 4. Zone Distribution UI
- **Gap**: Zone distribution editing requires JSON knowledge
- **Impact**: Not user-friendly for non-technical users
- **Solution**: Add visual zone distribution editor

### 5. Prompt Template Selection
- **Gap**: Prompt templates exist but aren't exposed to users
- **Impact**: Can't customize AI behavior easily
- **Solution**: Add template selection in generation UI

## Expected vs Actual Behavior

### Expected Flow
1. User writes preferences in natural language
2. Clicks "Generate Configuration" button
3. AI analyzes preferences and creates config
4. User reviews and adjusts generated config
5. Config is saved and immediately reflected in zone guide

### Actual Flow
1. User writes preferences in markdown file (no UI)
2. User runs Python script manually
3. Config is generated to sport_config.json
4. User must restart web server to see changes
5. No review/adjustment UI

## Proposed Implementation

### 1. Add Generation API Endpoint
```python
@app.route('/api/generate-config', methods=['POST'])
def generate_config():
    """Generate sport configuration from preferences"""
    preferences_text = request.json.get('preferences')
    
    generator = ConfigGenerator()
    config = generator.generate_config(preferences_text)
    
    # Convert to dict and return
    config_dict = config_to_dict(config)
    return jsonify({
        'success': True,
        'config': config_dict,
        'detected_sports': [s.name for s in config.sports]
    })
```

### 2. Add Preferences Editor UI
```html
<!-- In settings.html -->
<div id="preferences-tab" class="tab-content">
    <h2>Workout Preferences</h2>
    <textarea id="preferences-editor" rows="20">
        <!-- Load from workout_preferences.md -->
    </textarea>
    <button onclick="generateConfig()">Generate Configuration</button>
</div>
```

### 3. Add Zone Distribution Visual Editor
```html
<div class="zone-editor">
    <h3>Zone Distribution</h3>
    <div class="zone-slider">
        <label>Zone 1: <span id="zone1-value">80</span>%</label>
        <input type="range" min="0" max="100" value="80" 
               oninput="updateZoneDistribution(1, this.value)">
    </div>
    <!-- Repeat for zones 2 and 3 -->
</div>
```

### 4. Add Configuration Review Dialog
```javascript
async function generateConfig() {
    const preferences = document.getElementById('preferences-editor').value;
    
    const response = await fetch('/api/generate-config', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({preferences})
    });
    
    const result = await response.json();
    
    // Show review dialog
    showConfigReview(result.config);
}
```

## Integration Points Summary

### ✅ Working Integrations
1. sport_config.json → SportConfigService → Zone calculations
2. Zone calculations → Template rendering → Personalized display
3. Settings UI → Direct JSON editing → Configuration updates

### ❌ Missing Integrations
1. Preferences editor → AI generation trigger
2. AI generation → Configuration review UI
3. Zone distribution → Visual editing interface
4. Prompt templates → User selection UI
5. Generated config → Automatic reload/refresh

## Next Steps

1. **Priority 1**: Add `/api/generate-config` endpoint
2. **Priority 2**: Add preferences editor in settings UI
3. **Priority 3**: Add configuration review/approval dialog
4. **Priority 4**: Add visual zone distribution editor
5. **Priority 5**: Add prompt template selection

## Technical Requirements

### Backend
- Expose ConfigGenerator via web API
- Add preferences file read/write endpoints
- Add configuration validation before saving
- Add real-time config reload without restart

### Frontend
- Preferences editor with syntax highlighting
- Configuration diff viewer (current vs proposed)
- Zone distribution visualizer (pie chart or sliders)
- Prompt template selector with previews

### AI Integration
- Validate AI provider availability before generation
- Add progress indicator during generation
- Handle AI errors gracefully
- Cache generated configs for comparison

## Conclusion

The core components exist but lack UI integration. The system can generate configurations from preferences using AI, but users must interact via command line. Adding the missing UI components would complete the integration and provide a seamless experience from natural language preferences to personalized training configurations.