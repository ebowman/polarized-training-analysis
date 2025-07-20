# Prompt Architecture: Main + Sub-Prompt System

## System Overview

The PolarFlow prompt system uses a hierarchical architecture with a main orchestrator prompt and specialized sub-prompts. This design enables flexible, context-aware workout recommendations while maintaining consistency and safety.

```
┌─────────────────────────┐
│   Main Orchestrator     │
│     (Controller)        │
└───────────┬─────────────┘
            │
    ┌───────┴───────┐
    │               │
┌───▼────┐    ┌────▼────┐
│Context  │    │ Sport   │
│ Based   │    │Specific │
└───┬─────┘    └────┬────┘
    │               │
┌───▼────────────┬──▼────┐
│   Equipment    │ Safety │
│    Based       │ Check  │
└────────────────┴───────┘
```

## Main Orchestrator Prompt

### Role and Responsibilities
The main orchestrator acts as the central controller that:

1. **Analyzes User Context**
   - Current fitness level
   - Available equipment
   - Time constraints
   - Goals and preferences
   - Special circumstances (travel, injury, etc.)

2. **Selects Appropriate Sub-Prompts**
   - Determines which templates to activate
   - Prioritizes based on user needs
   - Manages conflicts between templates

3. **Orchestrates Workflow**
   - Routes requests to sub-prompts
   - Collects and merges responses
   - Ensures consistency across recommendations
   - Applies safety validations

4. **Generates Final Output**
   - Combines sub-prompt outputs
   - Formats for user consumption
   - Adds personalization layer
   - Includes necessary disclaimers

### Main Orchestrator Structure
```yaml
main_orchestrator:
  initialization:
    - load_user_profile
    - assess_current_context
    - identify_active_constraints
    - determine_priority_order
  
  template_selection:
    rules:
      - if traveling: activate(hotel-gym-v1)
      - if injury_reported: activate(recovery-mode-v1)
      - if sport_specific_goal: activate(sport-template)
      - else: activate(general-training-v1)
    
    priority_order:
      1: safety_constraints
      2: equipment_limitations
      3: time_availability
      4: user_preferences
      5: performance_goals
  
  orchestration_flow:
    1: context_analysis
    2: template_selection
    3: parameter_extraction
    4: sub_prompt_execution
    5: response_collection
    6: conflict_resolution
    7: safety_validation
    8: output_generation
  
  merge_strategy:
    - collect_all_recommendations
    - identify_conflicts
    - apply_priority_rules
    - ensure_coherent_plan
    - validate_total_load
```

## Sub-Prompt Categories

### 1. Context-Based Sub-Prompts
Handle specific situations or environments:

```yaml
context_prompts:
  general_training:
    activation: "default when no special context"
    responsibility: "standard training recommendations"
    output: "complete weekly plan"
  
  hotel_gym:
    activation: "user indicates travel"
    responsibility: "adapt to limited equipment"
    output: "modified workouts + alternatives"
  
  vacation_mode:
    activation: "vacation duration > 3 days"
    responsibility: "maintain fitness while relaxing"
    output: "flexible activity options"
  
  injury_recovery:
    activation: "injury or pain reported"
    responsibility: "safe return to training"
    output: "modified plan + recovery focus"
```

### 2. Sport-Specific Sub-Prompts
Provide specialized training for specific sports:

```yaml
sport_prompts:
  cycling_focus:
    activation: "primary goal includes cycling"
    responsibility: "power-based training plans"
    output: "FTP improvement workouts"
  
  running_focus:
    activation: "running race goal identified"
    responsibility: "pace-based training"
    output: "race preparation plan"
  
  swimming_focus:
    activation: "swimming improvement requested"
    responsibility: "technique + endurance"
    output: "pool workout structure"
  
  triathlon:
    activation: "multi-sport event goal"
    responsibility: "balanced three-sport training"
    output: "integrated training plan"
```

### 3. Equipment-Based Sub-Prompts
Adapt to available equipment:

```yaml
equipment_prompts:
  full_gym:
    activation: "complete gym access"
    responsibility: "utilize all equipment"
    output: "comprehensive strength + cardio"
  
  home_minimal:
    activation: "limited home equipment"
    responsibility: "bodyweight + basic tools"
    output: "effective home workouts"
  
  outdoor_only:
    activation: "no indoor facilities"
    responsibility: "weather-resistant outdoor plans"
    output: "park/trail workouts"
```

### 4. Modifier Sub-Prompts
Apply modifications to any base workout:

```yaml
modifier_prompts:
  time_crunched:
    activation: "< 45 min available"
    modification: "compress workout, maintain intensity"
  
  fatigue_management:
    activation: "high fatigue reported"
    modification: "reduce intensity 20-30%"
  
  weather_adaptation:
    activation: "extreme weather conditions"
    modification: "provide indoor alternatives"
```

## Communication Protocol

### Sub-Prompt Interface
Each sub-prompt follows a standard interface:

```python
class SubPromptInterface:
    def can_activate(self, context: UserContext) -> bool:
        """Determine if this sub-prompt should activate"""
        pass
    
    def get_priority(self) -> int:
        """Return priority level (1-10, higher = more important)"""
        pass
    
    def generate_recommendations(self, 
                               parameters: Dict,
                               constraints: List) -> WorkoutPlan:
        """Generate workout recommendations"""
        pass
    
    def validate_output(self, plan: WorkoutPlan) -> ValidationResult:
        """Validate generated plan meets safety standards"""
        pass
```

### Message Passing
```yaml
message_format:
  request:
    from: "main_orchestrator"
    to: "cycling_focus_v1"
    parameters:
      user_ftp: 301
      available_hours: 10
      goals: ["improve_ftp", "century_ride"]
    constraints:
      - "knee_sensitivity"
      - "morning_only"
  
  response:
    from: "cycling_focus_v1"
    to: "main_orchestrator"
    recommendations:
      week_plan: {...}
      key_workouts: [...]
      notes: "Modified for knee protection"
    confidence: 0.95
```

## Conflict Resolution

### Common Conflicts and Resolutions
```yaml
conflict_scenarios:
  time_vs_volume:
    scenario: "User wants high volume but has limited time"
    resolution: "Prioritize intensity over volume"
    sub_prompt_precedence: ["time_crunched", "general_training"]
  
  injury_vs_goals:
    scenario: "User has race goal but reports injury"
    resolution: "Safety first, modify goals"
    sub_prompt_precedence: ["injury_recovery", "sport_specific"]
  
  equipment_vs_ideal:
    scenario: "Ideal workout needs unavailable equipment"
    resolution: "Best available alternative"
    sub_prompt_precedence: ["equipment_based", "sport_specific"]
```

### Merge Algorithm
```python
def merge_recommendations(sub_prompt_outputs: List[WorkoutPlan]) -> WorkoutPlan:
    """Merge multiple sub-prompt outputs into coherent plan"""
    
    # Sort by priority
    sorted_outputs = sort_by_priority(sub_prompt_outputs)
    
    # Start with highest priority as base
    merged_plan = sorted_outputs[0]
    
    # Incorporate elements from other sub-prompts
    for output in sorted_outputs[1:]:
        if not conflicts_with(output, merged_plan):
            merged_plan.add_elements(output)
        else:
            merged_plan.add_alternatives(output)
    
    # Validate total training load
    if exceeds_safe_load(merged_plan):
        merged_plan = reduce_to_safe_load(merged_plan)
    
    return merged_plan
```

## Dynamic Prompt Loading

### Lazy Loading Strategy
```python
class PromptLoader:
    def __init__(self):
        self.loaded_prompts = {}
        self.prompt_registry = load_prompt_registry()
    
    def get_prompt(self, prompt_id: str) -> SubPrompt:
        """Load prompt only when needed"""
        if prompt_id not in self.loaded_prompts:
            self.loaded_prompts[prompt_id] = load_prompt_from_disk(prompt_id)
        return self.loaded_prompts[prompt_id]
    
    def activate_prompts(self, context: UserContext) -> List[SubPrompt]:
        """Determine and load necessary prompts"""
        active_prompts = []
        for prompt_id, prompt_meta in self.prompt_registry.items():
            if should_activate(prompt_meta, context):
                active_prompts.append(self.get_prompt(prompt_id))
        return active_prompts
```

## Performance Optimization

### Caching Strategy
```yaml
caching:
  user_preferences:
    ttl: 7_days
    invalidate_on: ["preference_update", "goal_change"]
  
  template_outputs:
    ttl: 24_hours
    key: "user_id:context_hash:template_id"
  
  compiled_prompts:
    ttl: 30_days
    invalidate_on: ["template_update"]
```

### Parallel Processing
```python
async def generate_recommendations_parallel(context: UserContext):
    """Process sub-prompts in parallel for speed"""
    
    active_prompts = identify_active_prompts(context)
    
    # Execute sub-prompts in parallel
    tasks = [
        prompt.generate_recommendations(context)
        for prompt in active_prompts
    ]
    
    results = await asyncio.gather(*tasks)
    
    # Merge results
    final_plan = merge_recommendations(results)
    
    return final_plan
```

## Extension Points

### Adding New Sub-Prompts
1. Create template following standard schema
2. Implement SubPromptInterface
3. Register in prompt registry
4. Define activation rules
5. Test with various contexts

### Custom User Prompts
Users can create their own sub-prompts:
```yaml
custom_prompt:
  base: "general-training-v1"
  overrides:
    warm_up: "my_custom_warmup"
    cool_down: "my_custom_cooldown"
  additions:
    pre_workout_ritual: "..."
    post_workout_notes: "..."
```

## Monitoring and Analytics

### Prompt Performance Tracking
```yaml
analytics:
  prompt_usage:
    track: ["activation_frequency", "user_satisfaction", "completion_rate"]
  
  effectiveness:
    measure: ["goal_achievement", "injury_rate", "adherence"]
  
  performance:
    monitor: ["response_time", "token_usage", "cache_hit_rate"]
```

### Continuous Improvement
```python
def analyze_prompt_effectiveness():
    """Analyze which prompts produce best outcomes"""
    
    results = query_user_outcomes()
    
    for prompt_id in get_all_prompts():
        effectiveness = calculate_effectiveness(prompt_id, results)
        if effectiveness < threshold:
            flag_for_review(prompt_id)
        
    return effectiveness_report()
```

## Summary

The main + sub-prompt architecture provides:
- **Flexibility**: Easy to add new contexts or sports
- **Modularity**: Each prompt has single responsibility
- **Scalability**: Lazy loading and caching for performance
- **Personalization**: User-specific prompt combinations
- **Safety**: Multiple validation layers
- **Maintainability**: Clear interfaces and separation of concerns

This architecture ensures that PolarFlow can adapt to any user's needs while maintaining consistency, safety, and effectiveness in workout recommendations.