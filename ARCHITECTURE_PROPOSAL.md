# Architecture Proposal: Sport-Agnostic Polarized Training Analysis

## Executive Summary

This proposal outlines a transformation of the Polarized Training Analysis Tool from a sport-specific implementation to a flexible, sport-agnostic architecture. The key innovation is replacing hardcoded sport assumptions with a configuration-driven approach using JSON schemas generated from user preferences.

## Current Architecture Problems

1. **Hardcoded Sport Logic**: Activities are categorized by fixed lists (e.g., cycling uses power, running uses HR)
2. **Brand-Specific Dependencies**: References to Peloton, Concept2 throughout codebase
3. **Inflexible Zone Systems**: Cannot adapt to different training methodologies
4. **Limited Extensibility**: Adding new sports requires code changes

## Proposed Architecture

### 1. Configuration-Driven Core

**Key Components:**
- **Sport Configuration Service**: Central service that loads and manages sport configurations
- **Dynamic Zone Calculator**: Adapts to any zone model (percentage, formula, absolute)
- **Metric Abstraction Layer**: Handles any intensity metric (power, HR, pace, speed, custom)
- **Equipment Registry**: Manages equipment capabilities and workout types

```python
# Example: New SportConfigService
class SportConfigService:
    def __init__(self, config_path: str):
        self.config = self._load_config(config_path)
        self.sports = self._build_sport_registry()
    
    def get_sport_for_activity(self, activity_type: str) -> Sport:
        # Dynamic lookup based on configuration
        pass
    
    def get_zone_calculator(self, sport_id: str, metric: str) -> ZoneCalculator:
        # Returns appropriate calculator for sport/metric combo
        pass
```

### 2. AI-Powered Configuration Generation

**Workflow:**
1. User writes natural language preferences in `workout_preferences_personal.md`
2. AI service analyzes preferences and generates `sport_config.json`
3. System validates against schema and loads configuration
4. All components use configuration instead of hardcoded values

```python
# Example: Configuration Generator
class ConfigurationGenerator:
    def generate_from_preferences(self, preferences_path: str) -> dict:
        # Read markdown preferences
        preferences = self._read_preferences(preferences_path)
        
        # Use AI to extract structured data
        prompt = self._build_extraction_prompt(preferences)
        config = self._call_ai_service(prompt)
        
        # Validate against schema
        self._validate_config(config)
        
        return config
```

### 3. Refactored Component Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                        Web Interface                         │
├─────────────────────────────────────────────────────────────┤
│                      Flask Application                       │
├─────────────────────────────────────────────────────────────┤
│                    Configuration Layer                       │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │Sport Config │  │ AI Generator │  │ Schema Validator │  │
│  │  Service    │  │              │  │                  │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                     Analysis Engine                          │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Dynamic   │  │   Flexible   │  │     Metric      │  │
│  │Zone Calc    │  │Sport Handler │  │   Abstraction   │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│                      Data Sources                            │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────────┐  │
│  │   Strava    │  │   Garmin     │  │   CSV Import    │  │
│  │   Client    │  │   Connect    │  │                  │  │
│  └─────────────┘  └──────────────┘  └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### 4. Key Design Patterns

**Strategy Pattern for Zone Calculations:**
```python
class ZoneCalculator(ABC):
    @abstractmethod
    def calculate_zone(self, value: float, sport: Sport) -> int:
        pass

class PercentageZoneCalculator(ZoneCalculator):
    # For FTP/LTHR percentage-based zones
    
class FormulaZoneCalculator(ZoneCalculator):
    # For formula-based zones (e.g., LTHR-30)
    
class AbsoluteZoneCalculator(ZoneCalculator):
    # For pace/speed-based zones
```

**Factory Pattern for Sport Creation:**
```python
class SportFactory:
    def create_sport(self, config: dict) -> Sport:
        # Builds sport with appropriate zone models, metrics, etc.
        pass
```

**Observer Pattern for Configuration Updates:**
```python
class ConfigurationObserver:
    def on_config_change(self, new_config: dict):
        # Components can react to configuration changes
        pass
```

## Implementation Strategy

### Phase 1: Foundation (2-3 weeks)
1. Create configuration schema and validation
2. Build SportConfigService and related classes
3. Implement AI configuration generator
4. Create migration utilities for existing users

### Phase 2: Core Refactoring (3-4 weeks)
1. Replace hardcoded sport lists with configuration lookups
2. Refactor TrainingAnalyzer to use dynamic zone calculations
3. Update UI to be configuration-driven
4. Implement metric abstraction layer

### Phase 3: Enhanced Features (2-3 weeks)
1. Add support for custom metrics and zones
2. Implement equipment registry and capabilities
3. Create sport-specific workout templates
4. Add configuration UI for advanced users

### Phase 4: Data Source Expansion (2 weeks)
1. Abstract data source interface
2. Add support for additional platforms
3. Implement activity type mapping system

## Migration Path

### For Existing Users:
1. **Automatic Migration Tool**: Reads current .env and generates initial sport_config.json
2. **Backward Compatibility**: Support legacy configuration during transition
3. **Gradual Rollout**: Feature flag to enable new system

```python
# Migration example
def migrate_to_new_config():
    # Read existing configuration
    env_config = load_env_variables()
    preferences = read_workout_preferences()
    
    # Generate new configuration
    new_config = {
        "version": "1.0.0",
        "metric_thresholds": {
            "max_heart_rate": env_config.get("MAX_HEART_RATE", 180),
            "functional_threshold_power": env_config.get("FTP", 250),
            # ... map other values
        },
        "sports": generate_default_sports(),
        # ... rest of configuration
    }
    
    # Validate and save
    validate_config(new_config)
    save_config(new_config, "sport_config.json")
```

## Benefits

1. **Extensibility**: Add any sport without code changes
2. **Flexibility**: Support custom zone models and metrics
3. **Personalization**: Each user can define their own training approach
4. **Maintainability**: Cleaner separation of concerns
5. **Future-Proof**: Easy to add new features and integrations

## Risks and Mitigation

| Risk | Impact | Mitigation |
|------|--------|------------|
| Complex migration | High | Provide automatic migration tool |
| AI misinterpretation | Medium | Manual override and validation UI |
| Performance impact | Low | Cache processed configurations |
| User confusion | Medium | Clear documentation and examples |

## Configuration Examples

### Triathlete Configuration:
- Multiple sports with different zone systems
- Brick workout support
- Combined analysis across sports

### Ultra Runner Configuration:
- Custom pace zones for different terrains
- Elevation-adjusted zones
- Long-duration workout templates

### CrossFit Athlete Configuration:
- Mixed modal training zones
- Custom metrics (reps, rounds)
- Skill-based progression tracking

## Next Steps

1. **Review and Approval**: Gather feedback on proposal
2. **Prototype**: Build proof-of-concept for key components
3. **User Testing**: Validate with diverse athlete types
4. **Incremental Rollout**: Phase implementation to minimize disruption

## Conclusion

This architecture transformation will position the Polarized Training Analysis Tool as a truly flexible platform that can adapt to any sport or training methodology while maintaining its core strength in polarized training analysis. The configuration-driven approach ensures that users have complete control over how their training is analyzed without requiring any coding knowledge.