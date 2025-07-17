# PolarFlow Refactoring Analysis

## Executive Summary

This document presents a comprehensive architectural analysis of the PolarFlow training analysis application, identifying key areas for refactoring to improve code quality, maintainability, and extensibility.

## 1. Major Architecture Issues Identified

### 1.1 Code Duplication (DRY Violations)

#### Zone Calculation Logic
- **Location**: `training_analysis.py` and `ai_recommendations.py`
- **Issue**: Zone percentage calculations are repeated multiple times
- **Example Pattern**:
  ```python
  # This pattern appears 6+ times across the codebase
  zone1_percent = total_zone1_minutes / total_minutes * 100
  zone2_percent = total_zone2_minutes / total_minutes * 100
  zone3_percent = total_zone3_minutes / total_minutes * 100
  ```

#### Zone Definition Classes
- **Location**: `training_analysis.py`
- **Issue**: `TrainingZones` and `PowerZones` classes have nearly identical structure
- **Duplication**: Zone calculation methods (`_get_hr_zone`, `_get_power_zone`) have similar logic

### 1.2 Configuration Management Complexity

#### Multiple Configuration Files
1. `sport_config.json` - Sport-specific configurations
2. `sport_config_schema.json` - JSON schema validation
3. `sport_config_example.json` - Example configuration
4. `workout_preferences.md` - User preferences in markdown
5. `workout_preferences_personal.md` - Personal preferences
6. `.env` - Environment variables
7. `cache/tokens.json` - OAuth tokens
8. `cache/training_analysis_report.json` - Cached analysis data

**Issues**:
- Configuration is scattered across multiple formats (JSON, Markdown, ENV)
- No single source of truth for configuration
- Mix of runtime and design-time configuration

### 1.3 Global State Management

#### Web Server Global Variables
```python
# Global variables in web_server.py
cached_data = None
cache_timestamp = None
ai_sessions = {}
strava_client = None
ai_engine = None
```

**Issues**:
- Thread safety concerns with global state
- Difficult to test in isolation
- State management scattered throughout the application

### 1.4 Tight Module Coupling

#### Circular Dependencies Risk
- `training_analysis.py` imports `sport_config_service.py`
- `sport_config_service.py` depends on zone calculation logic
- `ai_recommendations.py` duplicates logic from both

#### Data Flow Issues
- Activities flow through: Strava API → Cache → Analysis → Web Server → Frontend
- Each layer has its own data transformation logic
- No clear data model separation

## 2. Refactoring Opportunities

### 2.1 Extract Common Zone Calculation Logic

**Current State**: Zone calculations spread across multiple files
**Proposed Solution**: Create a unified `ZoneCalculator` class

```python
# Proposed: zone_calculator.py
class ZoneCalculator:
    def calculate_zone_percentages(self, zone_minutes: Dict[int, float]) -> Dict[int, float]:
        """Centralized zone percentage calculation"""
        total = sum(zone_minutes.values())
        if total == 0:
            return {k: 0.0 for k in zone_minutes}
        return {k: (v / total * 100) for k, v in zone_minutes.items()}
    
    def map_to_polarized_zones(self, detailed_zones: Dict[int, float], 
                              mapping: Dict[int, int]) -> Dict[int, float]:
        """Map detailed zones to 3-zone polarized model"""
        polarized = {1: 0.0, 2: 0.0, 3: 0.0}
        for zone, minutes in detailed_zones.items():
            polarized_zone = mapping.get(zone, 1)
            polarized[polarized_zone] += minutes
        return polarized
```

### 2.2 Unify Configuration Management

**Proposed Solution**: Single configuration service with multiple adapters

```python
# Proposed: config_manager.py
class ConfigManager:
    def __init__(self):
        self.sources = [
            JSONConfigSource('sport_config.json'),
            EnvConfigSource('.env'),
            MarkdownConfigSource('workout_preferences.md'),
            CacheConfigSource('cache/')
        ]
    
    def get_config(self, key: str, default=None):
        """Get configuration from appropriate source"""
        for source in self.sources:
            if source.has_key(key):
                return source.get(key, default)
        return default
```

### 2.3 Implement Dependency Injection

**Current**: Hard-coded dependencies and global state
**Proposed**: Dependency injection container

```python
# Proposed: dependencies.py
class ServiceContainer:
    def __init__(self):
        self._services = {}
        self._singletons = {}
    
    def register(self, name: str, factory, singleton=False):
        self._services[name] = (factory, singleton)
    
    def get(self, name: str):
        if name in self._singletons:
            return self._singletons[name]
        
        factory, is_singleton = self._services[name]
        instance = factory()
        
        if is_singleton:
            self._singletons[name] = instance
        
        return instance
```

### 2.4 Separate Data Models from Business Logic

**Proposed Structure**:
```
models/
├── activity.py      # Activity data models
├── analysis.py      # Analysis result models
├── workout.py       # Workout recommendation models
└── zones.py         # Zone definition models

services/
├── strava_service.py     # Strava API interaction
├── analysis_service.py   # Training analysis logic
├── ai_service.py         # AI recommendations
└── cache_service.py      # Caching logic

api/
├── routes.py        # API route definitions
└── middleware.py    # Request/response handling
```

### 2.5 Implement Strategy Pattern for Zone Models

**Current**: Multiple if/else chains for different zone calculation methods
**Proposed**: Strategy pattern implementation

```python
# Proposed: zone_strategies.py
from abc import ABC, abstractmethod

class ZoneStrategy(ABC):
    @abstractmethod
    def calculate_zones(self, threshold: float) -> List[Tuple[float, float]]:
        pass

class PercentageZoneStrategy(ZoneStrategy):
    def __init__(self, percentages: List[Tuple[float, float]]):
        self.percentages = percentages
    
    def calculate_zones(self, threshold: float) -> List[Tuple[float, float]]:
        return [(threshold * p[0], threshold * p[1]) for p in self.percentages]

class FormulaZoneStrategy(ZoneStrategy):
    def __init__(self, formulas: List[str]):
        self.formulas = formulas
    
    def calculate_zones(self, threshold: float) -> List[Tuple[float, float]]:
        # Evaluate formulas with threshold as variable
        return [self._evaluate_formula(f, threshold) for f in self.formulas]
```

## 3. Modularization Improvements

### 3.1 Frontend/Backend Separation

**Current Issues**:
- JavaScript embedded in HTML templates
- No clear API contract
- Mixed responsibilities in web_server.py

**Proposed Solution**:
1. Extract all JavaScript to separate files
2. Define clear REST API endpoints
3. Consider moving to a proper frontend framework (React/Vue)

### 3.2 Extract Business Rules

**Current**: Business rules scattered throughout codebase
**Proposed**: Centralized rules engine

```python
# Proposed: rules_engine.py
class TrainingRules:
    POLARIZED_TARGETS = {'zone1': 80, 'zone2': 10, 'zone3': 10}
    MIN_WEEKLY_VOLUME = 180  # minutes
    MIN_ZONE3_PER_WEEK = 30  # minutes
    
    @staticmethod
    def calculate_adherence_score(distribution: Dict[str, float]) -> float:
        """Centralized adherence calculation"""
        # All business logic in one place
        pass
```

### 3.3 Implement Repository Pattern

**For Data Access**:
```python
# Proposed: repositories.py
class ActivityRepository:
    def __init__(self, cache_manager, strava_client):
        self.cache = cache_manager
        self.strava = strava_client
    
    def get_activities(self, days: int, force_refresh: bool = False) -> List[Activity]:
        if not force_refresh:
            cached = self.cache.get_activities(days)
            if cached:
                return cached
        
        activities = self.strava.fetch_activities(days)
        self.cache.save_activities(activities)
        return activities
```

## 4. Testing Improvements

### 4.1 Current Testing Challenges
- Global state makes unit testing difficult
- Tight coupling requires extensive mocking
- No clear boundaries between components

### 4.2 Proposed Testing Strategy
1. **Dependency Injection** enables easy mocking
2. **Repository Pattern** allows in-memory test implementations
3. **Separated Business Logic** enables pure function testing

## 5. Migration Strategy

### Phase 1: Extract Common Logic (Low Risk)
1. Create `zone_calculator.py` with shared logic
2. Update existing code to use new calculator
3. Add comprehensive tests

### Phase 2: Configuration Unification (Medium Risk)
1. Implement `ConfigManager`
2. Migrate configurations one by one
3. Maintain backward compatibility

### Phase 3: Dependency Injection (Medium Risk)
1. Implement service container
2. Register services
3. Update instantiation points

### Phase 4: Model/Service Separation (High Risk)
1. Create model classes
2. Extract services
3. Update all references

### Phase 5: Frontend Modernization (High Risk)
1. Extract JavaScript
2. Define API contracts
3. Consider framework migration

## 6. Benefits of Refactoring

### Immediate Benefits
- **Reduced Duplication**: Less code to maintain
- **Improved Testability**: Easier to write unit tests
- **Better Organization**: Clear separation of concerns

### Long-term Benefits
- **Easier Feature Addition**: Clear extension points
- **Improved Performance**: Optimized data flow
- **Better Maintainability**: Cleaner, more understandable code
- **Enhanced Flexibility**: Easy to swap implementations

## 7. Risk Mitigation

### Testing Strategy
1. Write comprehensive tests for current behavior
2. Refactor incrementally with tests passing
3. Use feature flags for gradual rollout

### Backward Compatibility
1. Maintain existing APIs during transition
2. Use adapter pattern for legacy code
3. Deprecate old patterns gradually

## 8. Conclusion

The PolarFlow application has grown organically, leading to technical debt that impacts maintainability and extensibility. This refactoring plan addresses core architectural issues while providing a pragmatic migration path. The proposed changes will result in a more modular, testable, and maintainable codebase that can evolve with future requirements.

### Priority Order
1. **High Priority**: Zone calculation extraction (high impact, low risk)
2. **High Priority**: Configuration unification (high impact, medium risk)
3. **Medium Priority**: Dependency injection (medium impact, medium risk)
4. **Medium Priority**: Model/Service separation (high impact, high risk)
5. **Low Priority**: Frontend modernization (medium impact, high risk)

By following this incremental approach, the team can improve code quality while maintaining system stability and delivering value to users.