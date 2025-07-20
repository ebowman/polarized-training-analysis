# Prompt Template System Design

## Overview
The Prompt Template System provides a flexible, modular approach to generating personalized workout recommendations across different scenarios and constraints. It uses a hierarchical structure with a main prompt controller and specialized sub-prompts.

## Architecture

### 1. Main Prompt Controller
The main prompt acts as the orchestrator, determining which sub-prompts to activate based on user context and preferences.

```yaml
main_prompt:
  role: "workout_recommendation_orchestrator"
  responsibilities:
    - Analyze user context and constraints
    - Select appropriate sub-prompts
    - Merge and prioritize recommendations
    - Ensure consistency across modalities
  
  core_principles:
    - Safety first
    - Progressive overload
    - Recovery balance
    - Individual adaptation
```

### 2. Sub-Prompt Categories

#### A. Context-Based Templates
Templates that adapt to specific situations or environments:

1. **General Training** (Default)
2. **Travel/Vacation Mode**
3. **Hotel Gym Limited Equipment**
4. **Home Training Only**
5. **Injury Recovery Mode**
6. **Competition Preparation**

#### B. Sport-Specific Templates
Templates focused on particular sports or activities:

1. **Cycling Focus**
2. **Running Focus**
3. **Swimming Focus**
4. **Triathlon Training**
5. **Strength & Power Focus**
6. **Mixed Martial Arts**

#### C. Equipment-Based Templates
Templates that work with specific equipment limitations:

1. **Full Gym Access**
2. **Home Gym (Dumbbells Only)**
3. **Bodyweight Only**
4. **Minimal Equipment (Bands, Mat)**
5. **Sport-Specific Equipment**

## Template Structure

### Base Template Schema
```yaml
template:
  id: string
  name: string
  category: string
  description: string
  
  metadata:
    version: string
    last_updated: date
    author: string
    tags: array
  
  parameters:
    required:
      - fitness_level
      - available_time
      - goals
    optional:
      - equipment
      - preferences
      - constraints
  
  prompt_sections:
    context_analysis: string
    goal_prioritization: string
    constraint_handling: string
    recommendation_generation: string
    safety_checks: string
    
  output_format:
    structure: string
    required_fields: array
    optional_fields: array
```

### Customizable Variables
Each template supports variables that users can customize:

```yaml
variables:
  training_volume:
    type: range
    min: 3
    max: 20
    unit: hours_per_week
    
  intensity_preference:
    type: enum
    values: [conservative, moderate, aggressive]
    
  recovery_needs:
    type: enum
    values: [minimal, standard, enhanced]
    
  variety_level:
    type: enum
    values: [low, medium, high]
```

## Example Templates

### 1. General Training Template
```yaml
template:
  id: "general-training-v1"
  name: "General Training Template"
  category: "context-based"
  description: "Standard template for regular training scenarios"
  
  prompt_sections:
    context_analysis: |
      Analyze the user's current fitness level, goals, and available equipment.
      Consider their training history and progression rate.
      
    goal_prioritization: |
      Primary goals: {user.primary_goals}
      Secondary goals: {user.secondary_goals}
      Time frame: {user.target_timeframe}
      
    recommendation_generation: |
      Generate a {user.training_duration} week training plan that:
      - Follows polarized training principles (80/20 rule)
      - Includes {user.training_modalities} 
      - Targets {user.weekly_hours} hours per week
      - Progressively builds toward {user.goals}
```

### 2. Hotel Gym Template
```yaml
template:
  id: "hotel-gym-v1"
  name: "Hotel Gym Limited Equipment"
  category: "equipment-based"
  description: "Optimized for typical hotel gym limitations"
  
  equipment_assumptions:
    likely_available:
      - treadmill
      - elliptical
      - dumbbells (5-50 lbs)
      - cable machine
      - mat space
    rarely_available:
      - barbell
      - squat rack
      - specialized equipment
      
  prompt_sections:
    equipment_adaptation: |
      Modify standard exercises to work with limited equipment:
      - Replace barbell movements with dumbbell variations
      - Use cable machine for compound movements
      - Incorporate more unilateral work
      - Emphasize time under tension
```

### 3. Cycling Focus Template
```yaml
template:
  id: "cycling-focus-v1"
  name: "Cycling Performance Focus"
  category: "sport-specific"
  description: "Optimized for cycling performance and FTP improvement"
  
  sport_specific_parameters:
    ftp_current: number
    ftp_target: number
    bike_type: [road, mountain, indoor, triathlon]
    power_meter: boolean
    
  prompt_sections:
    periodization: |
      Structure training blocks:
      - Base Phase: Zone 2 volume building
      - Build Phase: Threshold and VO2max work
      - Peak Phase: Race-specific intensity
      
    power_zone_distribution: |
      Weekly distribution:
      - Zone 1-2: 70-80% of ride time
      - Zone 3-4: 15-20% of ride time
      - Zone 5+: 5-10% of ride time
```

## Prompt Composition Logic

### 1. Template Selection Algorithm
```python
def select_template(user_context):
    # Priority order for template selection
    priorities = [
        check_injury_status,
        check_travel_mode,
        check_equipment_limitations,
        check_sport_specific_goals,
        check_time_constraints
    ]
    
    selected_templates = []
    for check in priorities:
        template = check(user_context)
        if template:
            selected_templates.append(template)
    
    return merge_templates(selected_templates)
```

### 2. Template Merging Strategy
When multiple templates apply:
- Safety constraints take highest priority
- Equipment limitations override ideal recommendations
- Sport-specific guidance enhances general recommendations
- User preferences fine-tune final output

### 3. Validation Rules
```yaml
validation:
  safety_checks:
    - max_weekly_volume_increase: 10%
    - min_recovery_between_hard_sessions: 48h
    - max_consecutive_hard_days: 2
    
  consistency_checks:
    - total_weekly_hours_matches_target: true
    - intensity_distribution_follows_polarized: true
    - all_equipment_available: true
    
  preference_checks:
    - includes_enjoyed_activities: true
    - avoids_disliked_activities: true
    - matches_schedule_constraints: true
```

## Storage and Management

### 1. Template Repository Structure
```
/prompts/
├── templates/
│   ├── context-based/
│   │   ├── general-training.yaml
│   │   ├── travel-mode.yaml
│   │   └── hotel-gym.yaml
│   ├── sport-specific/
│   │   ├── cycling-focus.yaml
│   │   ├── running-focus.yaml
│   │   └── swimming-focus.yaml
│   └── equipment-based/
│       ├── full-gym.yaml
│       ├── home-gym.yaml
│       └── bodyweight-only.yaml
├── user-templates/
│   └── {user-id}/
│       └── custom-templates.yaml
└── shared-templates/
    └── community-templates.yaml
```

### 2. Template Versioning
- Semantic versioning (e.g., v1.2.3)
- Backward compatibility for user customizations
- Migration tools for template updates

### 3. User Customization Workflow
1. User selects base template
2. System presents customizable variables
3. User adjusts variables to preference
4. System validates configuration
5. Custom template saved to user profile

## Implementation Considerations

### 1. Performance Optimization
- Cache compiled templates
- Lazy load sport-specific modules
- Pre-compute common combinations

### 2. Extensibility
- Plugin architecture for new sports
- Community template marketplace
- API for external integrations

### 3. Privacy & Security
- Encrypt user custom templates
- Anonymize shared templates
- Audit trail for template modifications

## Future Enhancements

1. **AI Learning Integration**
   - Learn from user feedback
   - Adapt templates based on outcomes
   - Personalize beyond initial parameters

2. **Multi-User Support**
   - Family/team templates
   - Coach-athlete collaboration
   - Group training coordination

3. **Advanced Analytics**
   - Template effectiveness tracking
   - A/B testing framework
   - Outcome correlation analysis

4. **Integration Capabilities**
   - Wearable device data import
   - Training platform sync
   - Calendar integration