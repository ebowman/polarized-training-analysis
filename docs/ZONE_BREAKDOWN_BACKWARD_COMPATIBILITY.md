# Zone Breakdown Backward Compatibility Design

## Overview
This document outlines the backward compatibility strategy for introducing zone breakdown percentage configuration while ensuring existing systems continue to function without modification.

## Compatibility Principles

1. **Non-Breaking Changes Only**: Existing code must work unchanged
2. **Graceful Degradation**: Missing fields handled with sensible defaults
3. **Progressive Enhancement**: New features available when supported
4. **Clear Migration Path**: Easy upgrade process for existing users

## Implementation Strategy

### 1. Schema Evolution

#### Additive Changes Only
```json
{
  "sports": [{
    "name": "Cycling",
    "zones": [...],  // Existing field - unchanged
    "zone_breakdown_percentage": {  // New optional field
      "zone1": 80,
      "zone2": 10,
      "zone3": 10
    }
  }]
}
```

#### Schema Versioning
```json
{
  "version": "1.1.0",  // Increment minor version
  "$schema_version": "1.1.0",  // Track schema version
  "min_compatible_version": "1.0.0"  // Minimum version that can read this
}
```

### 2. Service Layer Compatibility

#### SportConfigService Updates
```python
class SportConfigService:
    
    def get_zone_breakdown(self, sport_name: str) -> Dict[str, float]:
        """
        Get zone breakdown with backward compatibility.
        
        Priority order:
        1. Explicit zone_breakdown_percentage in sport config
        2. Global default based on user philosophy
        3. Hardcoded polarized default
        """
        sport = self.get_sport_config(sport_name)
        
        # New way: explicit configuration
        if hasattr(sport, 'zone_breakdown_percentage') and sport.zone_breakdown_percentage:
            return sport.zone_breakdown_percentage
        
        # Fallback 1: Use philosophy defaults
        if self.config.user_profile and hasattr(self.config.user_profile, 'philosophy'):
            philosophy = self.config.user_profile.philosophy
            return self._get_philosophy_defaults(philosophy)
        
        # Fallback 2: Ultimate default (polarized)
        return {"zone1": 80.0, "zone2": 10.0, "zone3": 10.0}
    
    def _get_philosophy_defaults(self, philosophy: str) -> Dict[str, float]:
        """Get default zone breakdown for training philosophy"""
        defaults = {
            "polarized": {"zone1": 80.0, "zone2": 10.0, "zone3": 10.0},
            "pyramidal": {"zone1": 70.0, "zone2": 20.0, "zone3": 10.0},
            "threshold": {"zone1": 50.0, "zone2": 35.0, "zone3": 15.0},
            "custom": {"zone1": 80.0, "zone2": 10.0, "zone3": 10.0}
        }
        return defaults.get(philosophy, defaults["polarized"])
```

### 3. API Compatibility

#### Existing Endpoints (Unchanged)
```python
# These continue to work exactly as before
GET /api/sports/{sport}/zones  # Returns zone definitions
GET /api/sports/{sport}/config  # Returns full sport config
POST /api/sports/{sport}/update  # Updates sport config
```

#### New Endpoints (Additive)
```python
# New endpoints for zone breakdown feature
GET /api/sports/{sport}/zone-breakdown  # Get zone breakdown
PUT /api/sports/{sport}/zone-breakdown  # Update zone breakdown
GET /api/config/zone-defaults  # Get philosophy defaults
```

#### Response Compatibility
```python
# Old response format (still supported)
{
  "sport": "Cycling",
  "zones": [...]
}

# New response format (includes zone breakdown if available)
{
  "sport": "Cycling",
  "zones": [...],
  "zone_breakdown_percentage": {  // Only included if configured
    "zone1": 80,
    "zone2": 10,
    "zone3": 10
  }
}
```

### 4. Database/Storage Compatibility

#### Migration Strategy
```python
class ConfigMigration:
    
    def migrate_to_v1_1(self, config: dict) -> dict:
        """
        Migrate config from v1.0.0 to v1.1.0.
        Non-destructive, only adds new fields.
        """
        # Update version
        config["version"] = "1.1.0"
        
        # Add zone breakdown if missing
        for sport in config.get("sports", []):
            if "zone_breakdown_percentage" not in sport:
                # Don't add it here - let runtime handle defaults
                # This keeps the file minimal
                pass
        
        return config
    
    def is_migration_needed(self, config: dict) -> bool:
        """Check if migration is needed"""
        current_version = config.get("version", "1.0.0")
        return version.parse(current_version) < version.parse("1.1.0")
```

### 5. UI Compatibility

#### Progressive Enhancement
```javascript
// Settings page checks for feature availability
class SettingsPage {
  
  async loadSportConfig(sport) {
    const config = await api.getSportConfig(sport);
    
    // Always show basic zones
    this.displayZones(config.zones);
    
    // Only show zone breakdown if available
    if (config.zone_breakdown_percentage) {
      this.displayZoneBreakdown(config.zone_breakdown_percentage);
      this.enableZoneBreakdownEditing();
    } else {
      // Hide zone breakdown section for older configs
      this.hideZoneBreakdownSection();
    }
  }
  
  supportsZoneBreakdown() {
    // Feature detection
    return this.config.version >= "1.1.0";
  }
}
```

### 6. Import/Export Compatibility

#### Export Format
```python
def export_config(config: TrainingConfig, version: str = None) -> dict:
    """
    Export config in requested version format.
    Allows exporting in older format for compatibility.
    """
    exported = config.to_dict()
    
    if version == "1.0.0":
        # Remove new fields for v1.0.0 compatibility
        for sport in exported.get("sports", []):
            sport.pop("zone_breakdown_percentage", None)
        exported["version"] = "1.0.0"
    
    return exported
```

#### Import Handling
```python
def import_config(data: dict) -> TrainingConfig:
    """
    Import config from any supported version.
    Automatically migrates if needed.
    """
    version = data.get("version", "1.0.0")
    
    # Apply migrations in sequence
    if version < "1.1.0":
        data = migrate_to_v1_1(data)
    
    return TrainingConfig.from_dict(data)
```

### 7. Testing for Compatibility

#### Compatibility Test Suite
```python
class TestBackwardCompatibility:
    
    def test_v1_0_config_loads_correctly(self):
        """Test that v1.0.0 configs load without errors"""
        old_config = load_fixture("sport_config_v1.0.0.json")
        
        service = SportConfigService(old_config)
        
        # Should work without zone_breakdown_percentage
        cycling = service.get_sport_config("Cycling")
        assert cycling is not None
        
        # Should provide defaults
        breakdown = service.get_zone_breakdown("Cycling")
        assert breakdown == {"zone1": 80, "zone2": 10, "zone3": 10}
    
    def test_mixed_version_sports(self):
        """Test config with some sports having zone breakdown, others not"""
        config = {
            "sports": [
                {
                    "name": "Cycling",
                    "zone_breakdown_percentage": {"zone1": 75, "zone2": 15, "zone3": 10}
                },
                {
                    "name": "Running"
                    # No zone_breakdown_percentage
                }
            ]
        }
        
        service = SportConfigService(config)
        
        # Cycling should use explicit values
        assert service.get_zone_breakdown("Cycling")["zone1"] == 75
        
        # Running should use defaults
        assert service.get_zone_breakdown("Running")["zone1"] == 80
```

### 8. Communication Strategy

#### User Notification
```python
class FeatureNotification:
    
    def check_and_notify(self, config):
        """Notify users about new features available"""
        if not hasattr(config, 'zone_breakdown_percentage'):
            return {
                "feature": "Zone Breakdown Configuration",
                "message": "New feature available! You can now customize zone distribution percentages.",
                "action": "Go to Settings > Sport Configuration",
                "learn_more": "/docs/zone-breakdown-guide"
            }
```

#### Documentation Updates
- Add "New in v1.1.0" badges to new features
- Maintain v1.0.0 documentation separately
- Provide migration guides
- Include compatibility matrix

### 9. Rollback Strategy

#### Safe Rollback
```python
def prepare_rollback_file(config):
    """
    Create a v1.0.0 compatible version for rollback.
    """
    # Create backup of current config
    backup_path = f"sport_config.backup.{timestamp}.json"
    save_config(config, backup_path)
    
    # Create v1.0.0 compatible version
    v1_config = export_config(config, version="1.0.0")
    
    return v1_config, backup_path
```

#### Feature Flags
```python
# config.py
FEATURES = {
    "zone_breakdown_percentage": os.getenv("ENABLE_ZONE_BREAKDOWN", "true") == "true"
}

# service.py
if FEATURES["zone_breakdown_percentage"]:
    # New feature code
    return sport.zone_breakdown_percentage
else:
    # Legacy behavior
    return calculate_from_philosophy()
```

## Compatibility Matrix

| Component | v1.0.0 | v1.1.0 | Notes |
|-----------|---------|---------|--------|
| Schema | ✅ | ✅ | Additive changes only |
| API | ✅ | ✅ | New endpoints, old unchanged |
| Service | ✅ | ✅ | Fallback to defaults |
| UI | ✅ | ✅ | Progressive enhancement |
| Import | ✅ | ✅ | Auto-migration |
| Export | ✅ | ✅ | Version-specific export |

## Migration Timeline

### Phase 1: Silent Release (Week 1-2)
- Deploy with feature flag disabled
- Monitor for any issues
- Gather early feedback

### Phase 2: Opt-in Beta (Week 3-4)
- Enable for beta users
- Collect feedback
- Refine based on usage

### Phase 3: General Availability (Week 5)
- Enable for all users
- Show feature notification
- Monitor adoption

### Phase 4: Deprecation Notice (Month 6)
- Mark old methods as deprecated
- Encourage migration
- Set EOL date

## Monitoring and Metrics

### Compatibility Metrics
```python
# Track usage of new vs. old features
metrics.track("zone_breakdown.usage", {
    "has_explicit_config": bool(sport.zone_breakdown_percentage),
    "using_defaults": not bool(sport.zone_breakdown_percentage),
    "philosophy": config.user_profile.philosophy
})

# Track migration success
metrics.track("config.migration", {
    "from_version": old_version,
    "to_version": new_version,
    "success": success,
    "duration_ms": duration
})
```

### Error Monitoring
- Track any compatibility-related errors
- Monitor for unexpected behavior
- Alert on rollback triggers

## Conclusion

This backward compatibility design ensures that:
1. Existing users experience no disruption
2. New features are available progressively
3. Migration is automatic and safe
4. Rollback is always possible
5. Future evolution is supported

The approach prioritizes user experience and system stability while enabling new functionality.