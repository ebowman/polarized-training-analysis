# Settings API Documentation

This document describes the backend API endpoints for the Settings component.

## Base URL
All endpoints are prefixed with `/api/settings`

## Authentication
Most endpoints require authentication. The backend uses the existing session-based authentication from the Strava OAuth flow.

## Environment Settings API

### Get Environment Settings
```
GET /api/settings/env
```

Returns all environment settings with sensitive values masked.

**Response:**
```json
{
  "success": true,
  "settings": {
    "MAX_HEART_RATE": "171",
    "FTP": "301",
    "STRAVA_CLIENT_ID": "167076",
    "STRAVA_CLIENT_SECRET": "b210************************fde0",
    "OPENAI_API_KEY": "sk-p************************************F7oA"
  },
  "example": {
    "MAX_HEART_RATE": "180",
    "FTP": "250"
  },
  "allowed_keys": ["MAX_HEART_RATE", "FTP", "AVERAGE_FTP_HR", ...]
}
```

### Update Single Environment Setting
```
PUT /api/settings/env/{key}
```

Updates a single environment variable.

**Request Body:**
```json
{
  "value": "310"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully updated FTP"
}
```

### Update Multiple Environment Settings
```
PUT /api/settings/env
```

Updates multiple environment variables at once.

**Request Body:**
```json
{
  "FTP": "310",
  "MAX_HEART_RATE": "175",
  "AVERAGE_FTP_HR": "155"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Successfully updated 3 settings",
  "updated": ["FTP", "MAX_HEART_RATE", "AVERAGE_FTP_HR"]
}
```

## Prompt Templates API

### List Prompt Templates
```
GET /api/settings/prompts
```

Returns all prompt templates.

**Response:**
```json
{
  "success": true,
  "templates": [
    {
      "id": "template_abc123",
      "name": "Workout Generator",
      "description": "Generates personalized workouts",
      "created_at": "2025-01-17T10:00:00",
      "updated_at": "2025-01-17T10:00:00",
      "is_default": true
    }
  ]
}
```

### Get Prompt Template
```
GET /api/settings/prompts/{template_id}
```

Returns a specific prompt template.

**Response:**
```json
{
  "success": true,
  "template": {
    "id": "template_abc123",
    "name": "Workout Generator",
    "description": "Generates personalized workouts",
    "prompt": "Generate a {workout_type} workout for {duration} minutes",
    "variables": {
      "workout_type": "Type of workout",
      "duration": "Duration in minutes"
    },
    "is_default": true,
    "created_at": "2025-01-17T10:00:00",
    "updated_at": "2025-01-17T10:00:00"
  }
}
```

### Create Prompt Template
```
POST /api/settings/prompts
```

Creates a new prompt template.

**Request Body:**
```json
{
  "name": "Recovery Workout",
  "description": "Template for recovery workouts",
  "prompt": "Generate a recovery workout for {sport} lasting {duration} minutes",
  "variables": {
    "sport": "Sport type (cycling, running, etc.)",
    "duration": "Duration in minutes"
  },
  "is_default": false
}
```

**Response:**
```json
{
  "success": true,
  "message": "Template created successfully",
  "template_id": "template_xyz789"
}
```

### Update Prompt Template
```
PUT /api/settings/prompts/{template_id}
```

Updates an existing prompt template.

**Request Body:**
```json
{
  "name": "Updated Recovery Workout",
  "description": "Updated description",
  "is_default": true
}
```

**Response:**
```json
{
  "success": true,
  "message": "Template updated successfully"
}
```

### Delete Prompt Template
```
DELETE /api/settings/prompts/{template_id}
```

Deletes a prompt template.

**Response:**
```json
{
  "success": true,
  "message": "Template deleted successfully"
}
```

### Convert Prompt to JSON
```
POST /api/settings/prompts/convert
```

Converts a natural language prompt to structured JSON.

**Request Body:**
```json
{
  "prompt": "Objective: Generate workout plan\nContext: For marathon training\nConstraints:\n- Max 10 hours per week"
}
```

**Response:**
```json
{
  "success": true,
  "json": {
    "prompt_text": "...",
    "variables": {
      "variable_name": "description"
    },
    "structure": {
      "objective": "Generate workout plan",
      "context": "For marathon training",
      "constraints": ["Max 10 hours per week"],
      "output_format": "",
      "examples": []
    },
    "metadata": {
      "extracted_at": "2025-01-17T10:00:00",
      "variable_count": 0,
      "has_objective": true,
      "has_constraints": true,
      "has_examples": false
    }
  }
}
```

## Zone Distribution Management

The Zone Distribution API allows users to customize their training zone percentages both globally and per-sport. This enables fine-tuning of training intensity distribution to match individual goals and sport-specific requirements.

### Get Zone Distribution Settings
```
GET /api/settings/zone-distribution
```

Retrieves current zone distribution settings including user global targets and sport-specific overrides.

**Response:**
```json
{
  "success": true,
  "data": {
    "philosophy": "polarized",
    "user_targets": {
      "1": 80.0,
      "2": 10.0,
      "3": 10.0
    },
    "sport_distributions": {
      "Cycling": {
        "1": 85.0,
        "2": 5.0,
        "3": 10.0
      },
      "Running": {
        "1": 75.0,
        "2": 15.0,
        "3": 10.0
      }
    },
    "available_philosophies": {
      "polarized": {"1": 80.0, "2": 10.0, "3": 10.0},
      "pyramidal": {"1": 70.0, "2": 20.0, "3": 10.0},
      "threshold": {"1": 50.0, "2": 35.0, "3": 15.0}
    }
  }
}
```

**Notes:**
- Zone 1: Easy/Recovery intensity (typically below VT1/AeT)
- Zone 2: Moderate/Threshold intensity (between VT1 and VT2)
- Zone 3: Hard/VO2max intensity (above VT2/AnT)
- The `available_philosophies` field shows preset distributions for quick selection

### Update User Zone Distribution
```
PUT /api/settings/zone-distribution/user
```

Updates the user's global zone distribution targets. These targets apply to all sports unless overridden at the sport level. Requires authentication.

**Request Body:**
```json
{
  "zone_distribution": {
    "1": 75.0,
    "2": 15.0,
    "3": 10.0
  },
  "philosophy": "custom"  // Optional: Updates training philosophy
}
```

**Response:**
```json
{
  "success": true,
  "message": "User zone distribution updated successfully",
  "updated": {
    "zone_distribution": {
      "1": 75.0,
      "2": 15.0,
      "3": 10.0
    },
    "philosophy": "custom"
  }
}
```

**Example: Setting Polarized Distribution**
```json
{
  "zone_distribution": {
    "1": 80.0,
    "2": 10.0,
    "3": 10.0
  },
  "philosophy": "polarized"
}
```

### Update Sport Zone Distribution
```
PUT /api/settings/zone-distribution/sport/{sport_name}
```

Updates zone distribution targets for a specific sport. Sport-specific distributions override the user's global targets. Requires authentication.

**URL Parameters:**
- `sport_name`: The name of the sport (e.g., "Cycling", "Running", "Rowing")

**Request Body:**
```json
{
  "zone_distribution": {
    "1": 85.0,
    "2": 5.0,
    "3": 10.0
  },
  "reset_to_global": false  // Optional: Reset to global targets
}
```

**Response:**
```json
{
  "success": true,
  "message": "Zone distribution for Cycling updated successfully",
  "updated": {
    "sport": "Cycling",
    "zone_distribution": {
      "1": 85.0,
      "2": 5.0,
      "3": 10.0
    }
  }
}
```

**Example: Ultra-Polarized Cycling Distribution**
```json
{
  "zone_distribution": {
    "1": 90.0,
    "2": 5.0,
    "3": 5.0
  }
}
```

**Example: Reset to Global Targets**
```json
{
  "reset_to_global": true
}
```

**Validation:**
- Zone distributions must sum to exactly 100% (±0.1% for rounding)
- Zone numbers must be 1, 2, or 3
- Each zone percentage must be between 0 and 100
- Sport name must exist in configuration

## AI-Powered Configuration Generation

### Generate Configuration from Preferences
```
POST /api/settings/generate-config
```

Generates a complete sport configuration from natural language preferences using AI. This endpoint analyzes user-written preferences and creates a structured configuration including sports, zones, equipment, and training philosophy.

**Request Body:**
```json
{
  "preferences": "I'm a cyclist with an FTP of 301W...\nI also row on a Concept2...",
  "update_existing": false,  // Optional: Update vs replace config
  "ai_provider": "auto"     // Optional: "openai", "claude", or "auto"
}
```

**Response:**
```json
{
  "success": true,
  "message": "Configuration generated successfully",
  "config": {
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
        "lthr": 155
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
        }
      }
    ]
  },
  "detected_sports": ["Cycling", "Rowing"],
  "detected_philosophy": "polarized",
  "preview_mode": false  // true if config not saved
}
```

**Example Request with Full Preferences:**
```json
{
  "preferences": "# My Training Goals\n\nI'm a competitive cyclist with an FTP of 301W and LTHR of 155 bpm. I train primarily on my Peloton bike and outdoors.\n\nI follow a polarized training approach, aiming for:\n- 80% easy riding (Zone 1)\n- 10% threshold work (Zone 2)\n- 10% VO2max intervals (Zone 3)\n\nI also cross-train with rowing on my Concept2 ergometer, typically 2-3 times per week for aerobic development.\n\nMy weekly volume varies:\n- Recovery weeks: 5-6 hours\n- Normal weeks: 10-12 hours\n- Big weeks: 15-20 hours"
}
```

**Features:**
- Detects sports from natural language (cycling, running, rowing, swimming, etc.)
- Extracts threshold values (FTP, LTHR, pace)
- Identifies training philosophy and zone distributions
- Recognizes equipment mentions (Peloton, Concept2, etc.)
- Creates appropriate zone models for each sport
- Generates workout templates based on preferences

**Validation:**
- Requires AI provider to be configured (OpenAI or Claude API key)
- Preferences text must be provided
- Generated configuration is validated before saving

**Error Responses:**
```json
{
  "success": false,
  "error": "No AI provider available. Please configure OPENAI_API_KEY or ANTHROPIC_API_KEY"
}
```

### Preview Configuration Generation
```
POST /api/settings/preview-config
```

Generates a configuration preview without saving it. Useful for reviewing AI-generated configurations before committing changes.

**Request/Response:** Same as `/api/settings/generate-config` but with `preview_mode: true` in response.

## Zone Distribution Editor Features

### Batch Update Zone Distributions
```
PUT /api/settings/zone-distribution/batch
```

Update multiple sport zone distributions in a single request.

**Request Body:**
```json
{
  "updates": [
    {
      "sport": "Cycling",
      "zone_distribution": {"1": 85.0, "2": 5.0, "3": 10.0}
    },
    {
      "sport": "Running",
      "zone_distribution": {"1": 75.0, "2": 15.0, "3": 10.0}
    }
  ],
  "update_philosophy": "custom"  // Optional
}
```

**Response:**
```json
{
  "success": true,
  "message": "Updated zone distributions for 2 sports",
  "updated": ["Cycling", "Running"],
  "failed": []
}
```

### Apply Philosophy Preset
```
POST /api/settings/zone-distribution/apply-philosophy
```

Apply a predefined training philosophy distribution to all or specific sports.

**Request Body:**
```json
{
  "philosophy": "polarized",  // "polarized", "pyramidal", or "threshold"
  "apply_to": "all",          // "all" or ["Cycling", "Running"]
  "override_custom": false     // Override existing custom distributions
}
```

**Response:**
```json
{
  "success": true,
  "message": "Applied polarized distribution to all sports",
  "applied": {
    "philosophy": "polarized",
    "distribution": {"1": 80.0, "2": 10.0, "3": 10.0},
    "sports_updated": ["Cycling", "Running", "Rowing"]
  }
}
```

## Error Responses

All endpoints may return error responses in the following format:

```json
{
  "success": false,
  "error": "Error message description"
}
```

Common HTTP status codes:
- 200: Success
- 201: Created (for POST requests)
- 400: Bad Request (validation errors)
- 401: Unauthorized (authentication required)
- 404: Not Found
- 500: Internal Server Error

## Validation Rules

### Environment Variables
- `MAX_HEART_RATE`: 2-3 digit number (e.g., 171)
- `FTP`: 2-4 digit number (e.g., 301)
- `AVERAGE_FTP_HR`: 0-3 digit number (can be 0)
- `MAX_FTP_HR`: 0-3 digit number (can be 0)
- `AVERAGE_FTP_POWER`: 0-4 digit number (can be 0)
- `AI_PROVIDER`: Must be "openai", "claude", or "auto"
- `STRAVA_CLIENT_ID`: Alphanumeric with dashes/underscores
- `STRAVA_CLIENT_SECRET`: Alphanumeric with dashes/underscores
- `OPENAI_API_KEY`: Must start with "sk-"
- `ANTHROPIC_API_KEY`: Must start with "sk-ant-"
- `FLASK_SECRET_KEY`: Alphanumeric with dashes/underscores

### Prompt Templates
- Template names must be non-empty
- Template IDs are automatically generated if not provided
- Only one template can be marked as default at a time
- Variables in prompts should be wrapped in curly braces: `{variable_name}`

## Security Considerations

1. **Authentication**: All write operations require authentication
2. **Input Validation**: All inputs are validated against patterns and allowed values
3. **File Security**: Filenames are sanitized to prevent directory traversal
4. **Sensitive Data**: API keys and secrets are masked in responses
5. **Environment Variables**: Only allowed keys can be modified