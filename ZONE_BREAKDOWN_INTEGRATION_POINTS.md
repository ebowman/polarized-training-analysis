# Zone Breakdown Configuration - Integration Points Checklist

## Files Requiring Updates

### 1. Core Configuration Generation
- [ ] **config_generator.py**
  - Line 130: Remove hardcoded "Zone 1: 80%, Zone 2: 10%, Zone 3: 10%"
  - Add zone distribution parsing logic
  - Update AI prompt to detect zone preferences
  - Generate custom zone_distribution in preferences

### 2. Service Layer
- [ ] **sport_config_service.py**
  - Lines 293-303: Update get_zone_distribution_target() to use preferences
  - Add validation for custom distributions
  - Add method to update zone distributions
  - Ensure CUSTOM philosophy properly reads from preferences

### 3. Calculation Layer
- [ ] **zone_calculator.py**
  - Lines 350-352: Remove hardcoded distribution values
  - Always delegate to sport_config_service
  - Add caching for performance

### 4. AI Recommendations
- [ ] **ai_recommendations.py**
  - Line 732: Replace hardcoded "80% Z1, 10% Z2, 10% Z3"
  - Line 762: Make zone targets dynamic
  - Update all deficit calculations
  - Use configured targets throughout

### 5. Web Server
- [ ] **web_server.py**
  - Line 391: Replace hardcoded zone_targets
  - Pass actual targets from sport_config_service
  - Update zone mapping guide endpoint

### 6. Templates
- [ ] **templates/index.html**
  - Line 817: Update adherence score description
  - Line 1770: Update zone deficit calculations
  - Line 2568: Update zone deficit calculations
  - Line 2960: Update zone imbalance calculations
  - Replace all hardcoded 80/10/10 references

- [ ] **templates/zone_mapping_guide.html**
  - Line 318: Already supports dynamic targets, verify working

### 7. Documentation & Comments
- [ ] **constants.py**
  - Line 13: Update comment about 80/10/10 approach
  
- [ ] **README.md**
  - Update references to fixed 80/10/10 distribution
  - Add section on configurable distributions

### 8. Test Files
- [ ] **test_zone_calculator.py**
  - Line 192: Update test to use configurable values
  
- [ ] **test_backward_compatibility.py**
  - Lines 37, 102: Update adherence score tests

- [ ] **tests/test_sport_config.py**
  - Lines 567, 572: Update default expectation tests

- [ ] **tests/test_ai_recommendations.py**
  - Line 46: Update target_distribution test data
  - Line 510: Update mock service return values

### 9. Settings & UI (New Development)
- [ ] **Create settings page components**
  - Zone distribution configuration UI
  - Visual representation (pie chart/bars)
  - Preset selections
  - Custom input with validation

## Implementation Order

1. **Phase 1: Core Support (Backend)**
   - sport_config_service.py modifications
   - zone_calculator.py updates
   - config_generator.py AI prompt updates

2. **Phase 2: Frontend Integration**
   - web_server.py endpoint updates
   - Template dynamic value updates
   - JavaScript calculation updates

3. **Phase 3: AI & Recommendations**
   - ai_recommendations.py dynamic targets
   - Update all hardcoded references
   - Enhance recommendation logic

4. **Phase 4: UI Enhancement**
   - Settings page development
   - Zone distribution configurator
   - Visual feedback and validation

5. **Phase 5: Testing & Documentation**
   - Update all test files
   - Update documentation
   - Add new tests for custom distributions

## Validation Checklist

Before considering implementation complete:
- [ ] No hardcoded 80/10/10 remains in codebase
- [ ] All templates use dynamic values
- [ ] AI recommendations adapt to custom targets
- [ ] Settings page allows easy configuration
- [ ] Tests pass with various distributions
- [ ] Documentation updated
- [ ] Backward compatibility maintained