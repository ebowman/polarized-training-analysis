# User Template Customization Guide

## Overview
This guide explains how users can customize existing prompt templates to match their specific needs and save personalized versions for future use.

## Customization Workflow

### Step 1: Select Base Template
Users start by choosing a base template that most closely matches their needs:

```python
# Example selection interface
available_templates = {
    "general-training-v1": "Balanced multi-sport training",
    "hotel-gym-v1": "Limited equipment travel workouts",
    "cycling-focus-v1": "FTP improvement and cycling performance",
    "running-focus-v1": "Race preparation and running performance",
    "swimming-focus-v1": "Technique and swimming endurance"
}

selected_template = "cycling-focus-v1"
```

### Step 2: Customize Variables
Each template exposes customizable variables that users can adjust:

```yaml
# User's custom settings for cycling template
my_cycling_settings:
  # Override default variables
  variables:
    training_volume:
      value: 12  # hours per week (was 8)
    
    intensity_preference:
      value: "aggressive"  # was "moderate"
    
    indoor_outdoor_ratio:
      value: "mostly_indoor"  # Peloton focused
    
    time_to_peak:
      value: 16  # weeks to target event
  
  # Personal parameters
  personal_data:
    current_ftp: 301
    target_ftp: 320
    weight_kg: 75
    bike_type: "peloton"
    power_meter_available: true
    
  # Custom constraints
  constraints:
    max_session_duration: 90  # minutes
    available_days: ["Mon", "Tue", "Thu", "Sat", "Sun"]
    blackout_times: ["Wed PM", "Fri PM"]
    
  # Preferences
  preferences:
    favorite_instructors: ["Matt Wilpers", "Denis Morton"]
    avoid_workout_types: ["arms_and_shoulders"]
    music_preference: ["rock", "electronic"]
```

### Step 3: Add Personal Context
Users can add personal context that modifies how the template generates recommendations:

```yaml
personal_context:
  training_history:
    years_cycling: 3
    previous_ftp_tests: [250, 275, 290, 301]
    best_20min_power: 317
    typical_weekly_hours: 8-10
    
  lifestyle_factors:
    work_schedule: "9-5 weekdays"
    family_commitments: "weekends busy until 10am"
    travel_frequency: "2x per month"
    stress_level: "moderate"
    
  injury_considerations:
    past_injuries: ["mild knee pain when over 2 hours"]
    current_limitations: ["avoid out-of-saddle work"]
    physio_recommendations: ["focus on cadence over power"]
    
  goals_and_motivation:
    primary_goal: "Complete 100-mile charity ride"
    secondary_goals: ["improve climbing", "increase endurance"]
    motivation_style: "data-driven and competitive"
    accountability_preference: "weekly check-ins"
```

### Step 4: Create Custom Modifications
Users can modify specific sections of the template:

```yaml
custom_modifications:
  # Modify the warm-up protocol
  prompt_sections:
    warmup_override: |
      My preferred warm-up (every ride):
      - 5 minutes easy spin (Zone 1)
      - 3x1 minute progressive builds (Z1→Z3)
      - 2 minutes easy
      - 3x30 second high cadence (100+ rpm)
      - 3 minutes build to workout intensity
      Total: 15 minutes
    
    # Add custom workout preferences
    workout_preferences: |
      Peloton-specific preferences:
      - Power Zone rides with Matt Wilpers on Tuesdays
      - Power Zone Max rides on Thursdays
      - Longer Power Zone Endurance rides on weekends
      - Recovery rides with Denis Morton
      - Avoid arms sections, skip when included
    
    # Personal recovery protocol
    recovery_protocol_override: |
      My recovery routine:
      - Post-ride: 10 min yoga flow
      - Protein shake within 30 min
      - Foam roll IT bands and quads
      - Evening: 20 min walk
      - Compression boots 2x/week
```

### Step 5: Save Custom Template
Users can save their customized template for future use:

```yaml
saved_template:
  metadata:
    name: "My Peloton FTP Builder"
    based_on: "cycling-focus-v1"
    created_date: "2025-01-17"
    last_modified: "2025-01-17"
    version: "1.0"
    
  description: |
    Personal cycling template optimized for:
    - Peloton-based training
    - FTP improvement from 301W to 320W
    - 12 hours/week availability
    - Aggressive progression with knee considerations
    
  sharing_settings:
    visibility: "private"  # or "public", "friends"
    allow_copying: false
    tags: ["peloton", "ftp", "power-zone", "indoor"]
```

## Advanced Customization Options

### 1. Conditional Logic
Users can add conditions that modify workouts based on circumstances:

```yaml
conditional_rules:
  - condition: "weekly_stress_high"
    action: "reduce_intensity_by_10%"
    
  - condition: "poor_sleep_previous_night"
    action: "replace_hard_session_with_easy"
    
  - condition: "traveling_this_week"
    action: "activate_hotel_gym_alternatives"
    
  - condition: "knee_discomfort_reported"
    action: "limit_session_to_60min_and_reduce_power"
```

### 2. Progressive Adjustments
Templates can evolve based on progress:

```yaml
progressive_adjustments:
  ftp_milestones:
    - reached_ftp: 310
      adjustments:
        - increase_threshold_percentage: 2%
        - add_vo2max_session: true
        
    - reached_ftp: 315
      adjustments:
        - introduce_race_pace_work: true
        - increase_long_ride_intensity: true
  
  adaptation_tracking:
    - monitor: "heart_rate_drift"
      threshold: "< 5%"
      action: "increase_threshold_duration"
      
    - monitor: "power_consistency"
      threshold: "< 3% variation"
      action: "progress_to_next_level"
```

### 3. Integration Preferences
Connect with external services and devices:

```yaml
integrations:
  data_sources:
    - source: "peloton_api"
      sync: "automatic"
      metrics: ["power", "heart_rate", "cadence"]
      
    - source: "apple_health"
      sync: "daily"
      metrics: ["sleep", "hrv", "steps"]
      
    - source: "myfitnesspal"
      sync: "meals"
      metrics: ["calories", "macros"]
  
  export_preferences:
    - format: "ics"  # Calendar
      destination: "google_calendar"
      include: ["workout_time", "type", "duration"]
      
    - format: "fit"  # Garmin
      destination: "garmin_connect"
      include: ["planned_workout_structure"]
```

### 4. Template Combinations
Users can combine multiple templates:

```yaml
template_combination:
  primary_template: "cycling-focus-v1"
  secondary_templates:
    - template: "hotel-gym-v1"
      activation: "when_traveling"
      priority: "maintain_fitness"
      
    - template: "running-focus-v1"
      activation: "1x_per_week"
      purpose: "cross_training"
      
  combination_rules:
    - maintain_total_weekly_hours: true
    - prioritize_primary_sport: true
    - ensure_recovery_balance: true
```

## Sharing and Community Templates

### Sharing Your Template
```yaml
sharing_configuration:
  template_info:
    title: "Sub-3 Hour Marathon Builder"
    author: "RunnerJoe"
    description: "12-week program that got me from 3:15 to 2:58"
    
  sharing_options:
    visibility: "public"
    license: "CC-BY-SA"  # Creative Commons
    allow_modifications: true
    require_attribution: true
    
  success_metrics:
    users_achieved_goal: 45
    average_improvement: "12 minutes"
    injury_rate: "5%"
    completion_rate: "78%"
    
  included_materials:
    - template_file: true
    - sample_workouts: true
    - progress_tracking_sheet: true
    - nutrition_guide: false  # premium only
```

### Using Community Templates
```yaml
community_template_search:
  filters:
    sport: "cycling"
    goal: "ftp_improvement"
    experience_level: "intermediate"
    equipment: "peloton"
    rating: "> 4.5 stars"
    
  sort_by: "most_successful"
  
  safety_verification:
    validated: true
    medical_review: true
    user_reported_issues: 0
```

## Template Version Control

### Tracking Changes
```yaml
version_history:
  v1.0:
    date: "2025-01-01"
    changes: "Initial template"
    
  v1.1:
    date: "2025-01-10"
    changes:
      - "Reduced Thursday intensity after fatigue"
      - "Added extra recovery day"
      - "Increased warm-up duration"
    
  v1.2:
    date: "2025-01-17"
    changes:
      - "Adjusted for 16-week timeline"
      - "Added knee-friendly modifications"
      - "Integrated power meter data"
```

### Rollback Options
Users can revert to previous versions if new changes don't work well:

```python
def rollback_template(version):
    """Revert to a previous template version"""
    
    backup = load_template_version(version)
    if validate_template(backup):
        current_template = backup
        log_rollback(reason="New version caused excess fatigue")
        return "Rolled back successfully"
```

## Best Practices for Customization

### Do's:
1. ✅ Start with small modifications
2. ✅ Test changes for 1-2 weeks before making more
3. ✅ Keep notes on what works
4. ✅ Share successful templates with the community
5. ✅ Regular review and updates based on progress

### Don'ts:
1. ❌ Ignore safety validations
2. ❌ Make drastic changes all at once
3. ❌ Skip warmups or cooldowns
4. ❌ Exceed recommended progression rates
5. ❌ Ignore pain or excessive fatigue

## Support and Resources

### Getting Help
- Template customization tutorials
- Community forums for template sharing
- Expert review service (premium)
- AI-assisted customization suggestions
- Template effectiveness analytics

### Feedback Loop
Users are encouraged to provide feedback on templates:
- Rate template effectiveness
- Report any issues or injuries
- Suggest improvements
- Share success stories
- Contribute to template evolution