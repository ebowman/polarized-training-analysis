# Prompt Validation System

## Overview
The Prompt Validation System ensures that all prompt templates are safe, effective, and aligned with training best practices. It validates both the structure and content of prompts before they can be used for workout generation.

## Validation Layers

### 1. Structural Validation
Ensures templates follow the required schema and format.

```yaml
structural_validation:
  required_elements:
    - template.id: "unique identifier"
    - template.name: "human-readable name"
    - template.category: "valid category"
    - template.metadata: "version and authorship"
    - parameters.required: "minimum required inputs"
    - prompt_sections: "core prompt content"
    - output_format: "structured output spec"
  
  schema_rules:
    - id_format: "^[a-z0-9-]+v[0-9]+$"
    - version_format: "^[0-9]+\\.[0-9]+\\.[0-9]+$"
    - category_values: ["context-based", "sport-specific", "equipment-based"]
    - required_sections: ["context_analysis", "recommendation_generation", "safety_checks"]
```

### 2. Safety Validation
Ensures all recommendations follow safe training principles.

```yaml
safety_validation:
  training_load_rules:
    - weekly_increase_max: 10%  # 10% rule
    - hard_session_separation: 48  # hours
    - consecutive_hard_days_max: 2
    - rest_days_min_per_week: 1
    - long_run_max_percentage: 30  # of weekly volume
  
  intensity_rules:
    - zone_5_max_weekly: 15%  # of total time
    - zone_4_5_combined_max: 20%
    - zone_1_2_minimum: 65%
    - high_intensity_recovery: 48  # hours
  
  progression_rules:
    - new_activity_start: "50% of target volume"
    - injury_return: "start at 50% pre-injury"
    - deload_week_frequency: "every 3-4 weeks"
    - taper_minimum: "1 week for 5k, 3 weeks for marathon"
```

### 3. Content Validation
Ensures prompt content is appropriate and effective.

```yaml
content_validation:
  language_checks:
    - no_medical_advice: true
    - no_injury_diagnosis: true
    - no_supplement_recommendations: true
    - appropriate_disclaimers: true
  
  training_philosophy:
    - evidence_based: true
    - follows_polarized_model: true
    - includes_recovery: true
    - progressive_overload: true
  
  completeness_checks:
    - has_warmup_cooldown: true
    - includes_modifications: true
    - specifies_intensity: true
    - provides_duration: true
```

### 4. Personalization Validation
Ensures prompts can adapt to individual needs.

```yaml
personalization_validation:
  required_adaptations:
    - fitness_level_scaling: ["beginner", "intermediate", "advanced"]
    - time_constraint_options: ["minimal", "moderate", "ample"]
    - injury_modifications: true
    - equipment_alternatives: true
  
  parameter_ranges:
    - weekly_hours: [3, 20]
    - intensity_preference: ["conservative", "moderate", "aggressive"]
    - experience_years: [0, 50]
    - age_range: [18, 90]
```

## Validation Process

### Step 1: Pre-Validation
```python
def pre_validate_template(template):
    """Initial template validation before processing"""
    
    # Check file format
    if not template.endswith('.yaml'):
        return ValidationError("Template must be YAML format")
    
    # Check file size (prevent huge templates)
    if file_size > 100_000:  # 100KB limit
        return ValidationError("Template too large")
    
    # Check for malicious content
    if contains_executable_code(template):
        return ValidationError("No executable code allowed")
    
    return ValidationSuccess()
```

### Step 2: Schema Validation
```python
def validate_schema(template_data):
    """Validate template follows required schema"""
    
    required_fields = [
        'template.id',
        'template.name',
        'template.category',
        'parameters.required',
        'prompt_sections',
        'output_format'
    ]
    
    for field in required_fields:
        if not has_field(template_data, field):
            return ValidationError(f"Missing required field: {field}")
    
    # Validate ID format
    if not matches_pattern(template_data['template']['id'], ID_PATTERN):
        return ValidationError("Invalid ID format")
    
    return ValidationSuccess()
```

### Step 3: Safety Validation
```python
def validate_safety(template_data):
    """Ensure template follows safety guidelines"""
    
    safety_rules = SafetyValidator()
    
    # Check training load progression
    if violates_progression_rules(template_data):
        return ValidationError("Unsafe progression detected")
    
    # Check intensity distribution
    if violates_intensity_rules(template_data):
        return ValidationError("Unsafe intensity distribution")
    
    # Check recovery requirements
    if insufficient_recovery(template_data):
        return ValidationError("Insufficient recovery planned")
    
    return ValidationSuccess()
```

### Step 4: Content Validation
```python
def validate_content(template_data):
    """Validate prompt content quality"""
    
    content_checker = ContentValidator()
    
    # Check for prohibited content
    prohibited_terms = [
        'diagnose', 'cure', 'medical advice',
        'guaranteed results', 'no pain no gain'
    ]
    
    for term in prohibited_terms:
        if term in template_content:
            return ValidationError(f"Prohibited term found: {term}")
    
    # Check for required disclaimers
    required_disclaimers = [
        'consult healthcare provider',
        'listen to your body',
        'modify as needed'
    ]
    
    for disclaimer in required_disclaimers:
        if disclaimer not in template_content:
            return ValidationWarning(f"Missing disclaimer: {disclaimer}")
    
    return ValidationSuccess()
```

### Step 5: Output Validation
```python
def validate_output(generated_workout):
    """Validate generated workout meets standards"""
    
    output_validator = OutputValidator()
    
    # Check workout completeness
    if not has_warmup(generated_workout):
        return ValidationError("Missing warmup")
    
    if not has_cooldown(generated_workout):
        return ValidationError("Missing cooldown")
    
    # Check intensity matches prescription
    if not intensity_matches_zones(generated_workout):
        return ValidationError("Intensity doesn't match zones")
    
    # Check total volume
    if exceeds_safe_volume(generated_workout):
        return ValidationError("Volume exceeds safe limits")
    
    return ValidationSuccess()
```

## Validation Rules Engine

### Rule Categories

1. **Training Load Rules**
```yaml
training_load_rules:
  beginner:
    max_weekly_increase: 5%
    max_session_duration: 60min
    max_intensity_percentage: 10%
    required_rest_days: 2
  
  intermediate:
    max_weekly_increase: 10%
    max_session_duration: 90min
    max_intensity_percentage: 15%
    required_rest_days: 1-2
  
  advanced:
    max_weekly_increase: 10%
    max_session_duration: 180min
    max_intensity_percentage: 20%
    required_rest_days: 1
```

2. **Sport-Specific Rules**
```yaml
sport_specific_rules:
  running:
    max_weekly_mileage_increase: 10%
    long_run_max: 30% of weekly
    min_easy_pace_differential: 60s/mile
    max_quality_sessions: 3
  
  cycling:
    max_weekly_tss_increase: 10%
    max_single_ride_tss: 300
    recovery_ride_intensity: <65% FTP
    high_intensity_limit: 20%
  
  swimming:
    max_weekly_volume_increase: 15%
    technique_minimum: 20%
    max_continuous_distance: 4000m
    stroke_variety_requirement: true
```

3. **Recovery Rules**
```yaml
recovery_rules:
  between_hard_sessions:
    same_sport: 48h
    different_sport: 24h
    same_muscle_groups: 48h
  
  weekly_requirements:
    complete_rest_days: 1-2
    easy_days: 2-3
    recovery_weeks: "1 every 3-4 weeks"
  
  post_competition:
    5k: 2-3 days easy
    10k: 3-4 days easy
    half_marathon: 5-7 days easy
    marathon: 14-21 days easy
```

## Validation Reporting

### Validation Report Structure
```yaml
validation_report:
  template_id: "template-id"
  validation_date: "2025-01-17"
  overall_status: "PASS|FAIL|WARNING"
  
  checks_performed:
    structural: "PASS"
    safety: "PASS"
    content: "WARNING"
    personalization: "PASS"
  
  issues_found:
    - level: "WARNING"
      category: "content"
      message: "Missing injury prevention section"
      suggestion: "Add injury prevention guidelines"
    
  recommendations:
    - "Consider adding more beginner modifications"
    - "Include nutrition timing guidance"
    - "Add bad weather alternatives"
  
  score: 92/100
```

### Continuous Improvement
```yaml
validation_analytics:
  common_failures:
    - missing_warmup: 15%
    - excessive_intensity: 12%
    - poor_progression: 8%
  
  template_performance:
    - user_satisfaction: 4.5/5
    - injury_rate: 2%
    - adherence_rate: 78%
    - goal_achievement: 65%
  
  improvement_tracking:
    - validation_passes_trend: "increasing"
    - average_score_trend: "improving"
    - user_feedback_incorporation: 85%
```

## Implementation Guidelines

### For Template Authors
1. Run validation before submission
2. Address all errors before publishing
3. Consider warnings for improvement
4. Test with multiple user profiles
5. Include comprehensive safety notes

### For System Implementers
1. Validate on template upload
2. Re-validate on template updates
3. Log all validation results
4. Alert on critical failures
5. Provide clear error messages

### For End Users
1. Only use validated templates
2. Report suspicious recommendations
3. Provide feedback on template quality
4. Customize within safe parameters
5. Always prioritize safety over performance