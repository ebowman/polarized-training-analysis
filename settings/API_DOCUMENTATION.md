# Settings API Documentation

## Generate Config Endpoint

### POST /api/settings/generate-config

Generate a structured sport configuration from natural language workout preferences using AI.

#### Authentication
This endpoint requires authentication (@require_auth decorator).

#### Request Body
```json
{
  "preferences_text": "Optional natural language description of workout preferences"
}
```

If `preferences_text` is not provided, the endpoint will attempt to load from:
1. `workout_preferences_personal.md` (if exists)
2. `workout_preferences.md` (fallback)

#### Response

##### Success Response (200 OK)
```json
{
  "success": true,
  "config": {
    "version": "1.0.0",
    "user_profile": {
      "philosophy": "polarized",
      "volume_levels": {
        "low": 5,
        "medium": 10,
        "high": 15
      },
      "preferences": {},
      "thresholds": {
        "ftp": 301,
        "lthr": 165
      }
    },
    "sports": [
      {
        "id": "cycling",
        "name": "Cycling",
        "activity_types": ["Ride", "VirtualRide"],
        "primary_metric": {
          "type": "power",
          "unit": "watts",
          "threshold_field": "ftp",
          "decimal_places": 0,
          "custom_formula": null
        },
        "zones": [
          {
            "name": "Zone 1",
            "lower": 0,
            "upper": 55,
            "description": "Recovery",
            "polarized_zone": 1
          }
        ]
      }
    ]
  },
  "detected_sports": ["Cycling", "Running", "Rowing"],
  "message": "Successfully generated sport configuration from preferences"
}
```

##### Error Responses

**400 Bad Request** - No AI provider configured
```json
{
  "success": false,
  "error": "No AI provider configured. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY in settings."
}
```

**400 Bad Request** - No preferences found
```json
{
  "success": false,
  "error": "No preferences text provided and no preferences file found. Please create workout_preferences.md or provide preferences_text."
}
```

**500 Internal Server Error** - Generation failed
```json
{
  "success": false,
  "error": "Failed to generate configuration: [error details]"
}
```

#### Example Usage

```python
import requests

# Example 1: With preferences text
response = requests.post(
    "http://localhost:5002/api/settings/generate-config",
    json={
        "preferences_text": """
        I cycle on my Peloton and run outdoors.
        My FTP is 250 watts and LTHR is 160 bpm.
        I follow polarized training.
        """
    },
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)

# Example 2: Load from file
response = requests.post(
    "http://localhost:5002/api/settings/generate-config",
    json={},  # Empty body
    headers={"Authorization": "Bearer YOUR_TOKEN"}
)
```

#### Implementation Notes

1. **AI Provider Selection**:
   - First tries OpenAI (if OPENAI_API_KEY is set)
   - Falls back to Claude (if ANTHROPIC_API_KEY or CLAUDE_API_KEY is set)
   - Returns error if no provider is configured

2. **Preference Loading**:
   - If preferences_text not provided, looks for files in order:
     - workout_preferences_personal.md
     - workout_preferences.md

3. **Configuration Generation**:
   - Uses AI to parse natural language into structured config
   - Falls back to pattern matching if AI parsing fails
   - Detects sports, equipment, thresholds, and training philosophy

4. **Response Format**:
   - Returns complete sport configuration in JSON format
   - Includes detected sports list for confirmation
   - Compatible with sport_config.json structure

#### Error Handling

The endpoint includes comprehensive error handling:
- Validates AI provider availability
- Checks for preferences source
- Logs detailed errors for debugging
- Returns user-friendly error messages
- Includes full stack traces in logs