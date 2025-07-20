# Zone Breakdown Configuration Testing Strategy

## Overview
Comprehensive testing strategy for the zone breakdown percentage feature, covering unit tests, integration tests, migration tests, and UI tests.

## Test Categories

### 1. Unit Tests

#### Schema Validation Tests
```python
# test_sport_config_schema.py

def test_zone_breakdown_schema_validation():
    """Test that zone_breakdown_percentage schema is properly defined"""
    schema = load_sport_config_schema()
    
    # Verify schema structure
    sport_properties = schema["properties"]["sports"]["items"]["properties"]
    assert "zone_breakdown_percentage" in sport_properties
    
    zone_schema = sport_properties["zone_breakdown_percentage"]
    assert zone_schema["type"] == "object"
    assert set(zone_schema["properties"].keys()) == {"zone1", "zone2", "zone3"}
    assert zone_schema["required"] == ["zone1", "zone2", "zone3"]

def test_zone_percentage_constraints():
    """Test that zone percentages have proper constraints"""
    schema = load_sport_config_schema()
    zone_props = schema["properties"]["sports"]["items"]["properties"]["zone_breakdown_percentage"]["properties"]
    
    for zone in ["zone1", "zone2", "zone3"]:
        assert zone_props[zone]["minimum"] == 0
        assert zone_props[zone]["maximum"] == 100
        assert zone_props[zone]["type"] == "number"
```

#### Validation Logic Tests
```python
# test_zone_breakdown_validation.py

class TestZoneBreakdownValidation:
    
    def test_valid_zone_breakdown(self):
        """Test valid zone breakdown passes validation"""
        breakdown = {"zone1": 80, "zone2": 10, "zone3": 10}
        assert validate_zone_breakdown(breakdown) == (True, "Valid")
    
    def test_invalid_sum(self):
        """Test zone breakdown must sum to 100"""
        breakdown = {"zone1": 80, "zone2": 10, "zone3": 20}  # Sum = 110
        valid, msg = validate_zone_breakdown(breakdown)
        assert not valid
        assert "must sum to 100%" in msg
    
    def test_negative_percentage(self):
        """Test negative percentages are invalid"""
        breakdown = {"zone1": 90, "zone2": 20, "zone3": -10}
        valid, msg = validate_zone_breakdown(breakdown)
        assert not valid
        assert "between 0-100%" in msg
    
    def test_over_100_percentage(self):
        """Test percentages over 100 are invalid"""
        breakdown = {"zone1": 150, "zone2": -30, "zone3": -20}
        valid, msg = validate_zone_breakdown(breakdown)
        assert not valid
    
    def test_extreme_distributions(self):
        """Test extreme but valid distributions"""
        # All in zone 1
        assert validate_zone_breakdown({"zone1": 100, "zone2": 0, "zone3": 0})[0]
        
        # Heavy threshold focus
        assert validate_zone_breakdown({"zone1": 40, "zone2": 50, "zone3": 10})[0]
```

### 2. Migration Tests

#### Automatic Migration Tests
```python
# test_config_migration.py

class TestConfigMigration:
    
    def test_migration_adds_zone_breakdown(self):
        """Test migration adds zone_breakdown_percentage to sports"""
        config = {
            "version": "1.0.0",
            "user_profile": {"philosophy": "polarized"},
            "sports": [
                {"name": "Cycling", "zones": [...]},
                {"name": "Running", "zones": [...]}
            ]
        }
        
        migrated = migrate_sport_config(config)
        
        for sport in migrated["sports"]:
            assert "zone_breakdown_percentage" in sport
            assert sport["zone_breakdown_percentage"] == {
                "zone1": 80, "zone2": 10, "zone3": 10
            }
    
    def test_migration_uses_philosophy_defaults(self):
        """Test migration uses philosophy-specific defaults"""
        configs = [
            ({"philosophy": "polarized"}, {"zone1": 80, "zone2": 10, "zone3": 10}),
            ({"philosophy": "pyramidal"}, {"zone1": 70, "zone2": 20, "zone3": 10}),
            ({"philosophy": "threshold"}, {"zone1": 50, "zone2": 35, "zone3": 15}),
        ]
        
        for user_profile, expected in configs:
            config = {
                "user_profile": user_profile,
                "sports": [{"name": "Test"}]
            }
            migrated = migrate_sport_config(config)
            assert migrated["sports"][0]["zone_breakdown_percentage"] == expected
    
    def test_migration_preserves_existing_breakdown(self):
        """Test migration doesn't overwrite existing zone_breakdown"""
        existing_breakdown = {"zone1": 75, "zone2": 15, "zone3": 10}
        config = {
            "sports": [{
                "name": "Cycling",
                "zone_breakdown_percentage": existing_breakdown
            }]
        }
        
        migrated = migrate_sport_config(config)
        assert migrated["sports"][0]["zone_breakdown_percentage"] == existing_breakdown
    
    def test_migration_backup_creation(self):
        """Test migration creates backup before modifying"""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_path = Path(tmpdir) / "sport_config.json"
            config_path.write_text(json.dumps({"sports": [{"name": "Test"}]}))
            
            migrate_config_file(config_path)
            
            # Check backup exists
            backup_files = list(Path(tmpdir).glob("sport_config.json.backup.*"))
            assert len(backup_files) == 1
```

### 3. Integration Tests

#### SportConfigService Integration
```python
# test_sport_config_service_integration.py

class TestSportConfigServiceIntegration:
    
    def test_service_reads_zone_breakdown(self):
        """Test service correctly reads zone breakdown from config"""
        config = create_test_config_with_zone_breakdown()
        service = SportConfigService(config)
        
        cycling = service.get_sport_config("Cycling")
        assert cycling.zone_breakdown_percentage == {"zone1": 80, "zone2": 10, "zone3": 10}
    
    def test_service_calculates_with_zone_breakdown(self):
        """Test zone calculations respect zone breakdown configuration"""
        service = SportConfigService()
        service.update_sport_zone_breakdown("Cycling", {"zone1": 75, "zone2": 15, "zone3": 10})
        
        # Verify calculations use the breakdown
        calculations = service.get_zone_calculations("Cycling")
        assert calculations["zone_distribution"] == {"zone1": 75, "zone2": 15, "zone3": 10}
    
    def test_backward_compatibility(self):
        """Test service works with configs missing zone_breakdown"""
        legacy_config = create_legacy_config_without_zone_breakdown()
        service = SportConfigService(legacy_config)
        
        # Should use philosophy defaults
        cycling = service.get_sport_config("Cycling")
        breakdown = service.get_zone_breakdown("Cycling")
        assert breakdown == {"zone1": 80, "zone2": 10, "zone3": 10}  # Polarized default
```

#### API Endpoint Tests
```python
# test_api_endpoints.py

class TestZoneBreakdownAPI:
    
    def test_get_zone_breakdown_endpoint(self, client):
        """Test GET /api/sports/{sport}/zone-breakdown"""
        response = client.get("/api/sports/Cycling/zone-breakdown")
        assert response.status_code == 200
        
        data = response.json()
        assert "zone1" in data
        assert "zone2" in data
        assert "zone3" in data
        assert sum(data.values()) == 100
    
    def test_update_zone_breakdown_endpoint(self, client):
        """Test PUT /api/sports/{sport}/zone-breakdown"""
        new_breakdown = {"zone1": 75, "zone2": 15, "zone3": 10}
        
        response = client.put(
            "/api/sports/Cycling/zone-breakdown",
            json=new_breakdown
        )
        assert response.status_code == 200
        
        # Verify update
        response = client.get("/api/sports/Cycling/zone-breakdown")
        assert response.json() == new_breakdown
    
    def test_invalid_zone_breakdown_rejected(self, client):
        """Test API rejects invalid zone breakdowns"""
        invalid_breakdown = {"zone1": 80, "zone2": 10, "zone3": 20}  # Sum = 110
        
        response = client.put(
            "/api/sports/Cycling/zone-breakdown",
            json=invalid_breakdown
        )
        assert response.status_code == 400
        assert "must sum to 100%" in response.json()["error"]
```

### 4. UI Component Tests

#### Settings Page Tests
```python
# test_settings_zone_breakdown.py

class TestSettingsZoneBreakdown:
    
    def test_zone_breakdown_display(self, browser):
        """Test zone breakdown is displayed in settings"""
        browser.get("/settings")
        
        # Find zone breakdown section
        zone_section = browser.find_element_by_id("zone-breakdown-config")
        assert zone_section.is_displayed()
        
        # Check values are displayed
        zone1_input = browser.find_element_by_name("zone1_percentage")
        assert zone1_input.get_attribute("value") == "80"
    
    def test_zone_breakdown_editing(self, browser):
        """Test editing zone breakdown values"""
        browser.get("/settings")
        
        # Edit zone 1
        zone1_input = browser.find_element_by_name("zone1_percentage")
        zone1_input.clear()
        zone1_input.send_keys("75")
        
        # Edit zone 3
        zone3_input = browser.find_element_by_name("zone3_percentage")
        zone3_input.clear()
        zone3_input.send_keys("15")
        
        # Save
        browser.find_element_by_id("save-settings").click()
        
        # Verify save successful
        assert "Settings saved" in browser.page_source
    
    def test_validation_feedback(self, browser):
        """Test UI shows validation errors"""
        browser.get("/settings")
        
        # Set invalid values
        zone1_input = browser.find_element_by_name("zone1_percentage")
        zone1_input.clear()
        zone1_input.send_keys("90")
        
        # Try to save
        browser.find_element_by_id("save-settings").click()
        
        # Check error message
        error = browser.find_element_by_class_name("validation-error")
        assert "must sum to 100%" in error.text
```

### 5. AI Integration Tests

#### Preference Analysis Tests
```python
# test_ai_preference_analysis.py

class TestAIPreferenceAnalysis:
    
    def test_ai_extracts_zone_preferences(self):
        """Test AI correctly extracts zone preferences from text"""
        preferences = """
        I follow a polarized approach but prefer a bit more easy riding,
        maybe 85% in zone 1. I can only handle about 5% hard efforts.
        """
        
        result = analyze_zone_preferences(preferences)
        
        assert result["zone1"] == 85
        assert result["zone3"] == 5
        assert result["zone2"] == 10  # Calculated to sum to 100
    
    def test_ai_handles_missing_preferences(self):
        """Test AI uses defaults when no preferences specified"""
        preferences = "I like to ride my bike and run sometimes."
        
        result = analyze_zone_preferences(preferences)
        
        # Should use polarized defaults
        assert result == {"zone1": 80, "zone2": 10, "zone3": 10}
    
    def test_sport_specific_analysis(self):
        """Test AI generates sport-specific breakdowns"""
        preferences = """
        I can handle more intensity on the bike (maybe 15% hard efforts)
        but need to keep running easy due to injury history (only 5% hard).
        """
        
        result = analyze_sport_specific_zones(preferences)
        
        assert result["Cycling"]["zone3"] == 15
        assert result["Running"]["zone3"] == 5
```

### 6. Performance Tests

```python
# test_zone_breakdown_performance.py

class TestZoneBreakdownPerformance:
    
    def test_migration_performance(self, benchmark):
        """Test migration completes in reasonable time"""
        large_config = create_large_config(sport_count=50)
        
        result = benchmark(migrate_sport_config, large_config)
        
        # Should complete in under 100ms even for large configs
        assert benchmark.stats["mean"] < 0.1
    
    def test_validation_performance(self, benchmark):
        """Test validation is fast"""
        breakdown = {"zone1": 80, "zone2": 10, "zone3": 10}
        
        result = benchmark(validate_zone_breakdown, breakdown)
        
        # Should complete in microseconds
        assert benchmark.stats["mean"] < 0.001
```

### 7. End-to-End Tests

```python
# test_e2e_zone_breakdown.py

class TestE2EZoneBreakdown:
    
    def test_full_workflow(self, app_client):
        """Test complete workflow from preferences to active config"""
        
        # 1. Upload preferences
        response = app_client.post("/api/preferences/upload", 
            files={"file": ("prefs.md", "I prefer 85% easy riding")}
        )
        assert response.status_code == 200
        
        # 2. Generate config
        response = app_client.post("/api/config/generate-from-preferences")
        assert response.status_code == 200
        
        config = response.json()
        assert config["sports"][0]["zone_breakdown_percentage"]["zone1"] == 85
        
        # 3. Review and save
        response = app_client.post("/api/config/save", json=config)
        assert response.status_code == 200
        
        # 4. Verify in use
        response = app_client.get("/api/sports/Cycling/zone-breakdown")
        assert response.json()["zone1"] == 85
```

## Test Data Fixtures

```python
# conftest.py

@pytest.fixture
def sample_zone_breakdowns():
    """Sample zone breakdowns for testing"""
    return {
        "polarized": {"zone1": 80, "zone2": 10, "zone3": 10},
        "pyramidal": {"zone1": 70, "zone2": 20, "zone3": 10},
        "threshold": {"zone1": 50, "zone2": 35, "zone3": 15},
        "invalid_sum": {"zone1": 80, "zone2": 10, "zone3": 20},
        "negative": {"zone1": 90, "zone2": 20, "zone3": -10},
        "extreme": {"zone1": 100, "zone2": 0, "zone3": 0}
    }

@pytest.fixture
def test_config_with_breakdown():
    """Test config with zone breakdown already set"""
    return {
        "version": "1.0.0",
        "user_profile": {"philosophy": "polarized"},
        "sports": [{
            "name": "Cycling",
            "zone_breakdown_percentage": {"zone1": 80, "zone2": 10, "zone3": 10}
        }]
    }
```

## Coverage Requirements

- **Unit Test Coverage**: Minimum 90%
- **Integration Test Coverage**: Minimum 80%
- **Critical Path Coverage**: 100%

## Test Execution Plan

### Phase 1: Unit Tests (Before Implementation)
- Write schema validation tests
- Write validation logic tests
- Write migration logic tests

### Phase 2: Integration Tests (During Implementation)
- Test service integration
- Test API endpoints
- Test data flow

### Phase 3: UI Tests (After UI Implementation)
- Test display components
- Test editing workflow
- Test validation feedback

### Phase 4: End-to-End Tests (Final Phase)
- Test complete workflows
- Test edge cases
- Performance testing

## Continuous Testing

### Pre-commit Hooks
```yaml
- repo: local
  hooks:
    - id: test-zone-breakdown
      name: Zone Breakdown Tests
      entry: pytest tests/test_zone_breakdown_*.py
      language: system
      pass_filenames: false
```

### CI Pipeline
```yaml
test-zone-breakdown:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v2
    - name: Run Zone Breakdown Tests
      run: |
        pytest tests/test_zone_breakdown_*.py -v --cov=sport_config
        pytest tests/test_sport_config_service.py::*zone* -v
```

## Success Metrics

1. **All tests passing** before merge
2. **No regression** in existing functionality
3. **Performance benchmarks** met
4. **User acceptance** through beta testing