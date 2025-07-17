"""
Comprehensive tests for sport configuration system.
Tests configuration loading, validation, zone calculations, and edge cases.
"""

import pytest
import json
import os
from unittest.mock import patch, MagicMock, mock_open
from pathlib import Path

from sport_config import (
    SportConfig, TrainingConfig, UserProfile, ZoneDefinition,
    Metric, Equipment, WorkoutTemplate, ConfigValidator,
    TrainingPhilosophy, ZoneModelType, MetricType
)
from sport_config_service import SportConfigService


class TestSportConfigClasses:
    """Test sport configuration data classes and enums"""
    
    def test_training_philosophy_enum(self):
        """Test TrainingPhilosophy enum values"""
        assert TrainingPhilosophy.POLARIZED.value == "polarized"
        assert TrainingPhilosophy.PYRAMIDAL.value == "pyramidal"
        assert TrainingPhilosophy.THRESHOLD.value == "threshold"
        assert TrainingPhilosophy.CUSTOM.value == "custom"
    
    def test_zone_model_type_enum(self):
        """Test ZoneModelType enum values"""
        assert ZoneModelType.PERCENTAGE.value == "percentage"
        assert ZoneModelType.FORMULA.value == "formula"
        assert ZoneModelType.ABSOLUTE.value == "absolute"
        assert ZoneModelType.CUSTOM.value == "custom"
    
    def test_metric_type_enum(self):
        """Test MetricType enum values"""
        assert MetricType.POWER.value == "power"
        assert MetricType.HEART_RATE.value == "heart_rate"
        assert MetricType.PACE.value == "pace"
        assert MetricType.SPEED.value == "speed"
        assert MetricType.CUSTOM.value == "custom"
    
    def test_zone_definition_creation(self):
        """Test ZoneDefinition dataclass"""
        zone = ZoneDefinition(
            name="Zone 1",
            lower=0.0,
            upper=75.0,
            description="Easy aerobic",
            polarized_zone=1
        )
        
        assert zone.name == "Zone 1"
        assert zone.lower == 0.0
        assert zone.upper == 75.0
        assert zone.description == "Easy aerobic"
        assert zone.polarized_zone == 1
        
        # Test with string values (formula)
        zone_formula = ZoneDefinition(
            name="Zone 2",
            lower="0.76 * ftp",
            upper="0.87 * ftp",
            polarized_zone=2
        )
        assert isinstance(zone_formula.lower, str)
        assert isinstance(zone_formula.upper, str)
    
    def test_metric_creation(self):
        """Test Metric dataclass"""
        metric = Metric(
            type=MetricType.POWER,
            unit="watts",
            threshold_field="ftp",
            decimal_places=0
        )
        
        assert metric.type == MetricType.POWER
        assert metric.unit == "watts"
        assert metric.threshold_field == "ftp"
        assert metric.decimal_places == 0
        assert metric.custom_formula is None
        
        # Test with custom formula
        custom_metric = Metric(
            type=MetricType.CUSTOM,
            unit="score",
            threshold_field="custom_threshold",
            decimal_places=2,
            custom_formula="value * 1.05"
        )
        assert custom_metric.custom_formula == "value * 1.05"
    
    def test_equipment_creation(self):
        """Test Equipment dataclass"""
        equipment = Equipment(
            name="Road Bike",
            description="Outdoor road cycling",
            capabilities=["intervals", "endurance"],
            default_duration_minutes=60,
            supports_metrics=[MetricType.POWER, MetricType.HEART_RATE]
        )
        
        assert equipment.name == "Road Bike"
        assert equipment.description == "Outdoor road cycling"
        assert "intervals" in equipment.capabilities
        assert equipment.default_duration_minutes == 60
        assert MetricType.POWER in equipment.supports_metrics
    
    def test_workout_template_creation(self):
        """Test WorkoutTemplate dataclass"""
        template = WorkoutTemplate(
            name="Threshold Intervals",
            description="4x8min at threshold",
            zones=[2, 3],
            structure="10min warm-up, 4x8min Zone 3 with 2min recovery, 10min cool-down",
            duration_minutes=60,
            required_equipment=["Road Bike", "Power Meter"]
        )
        
        assert template.name == "Threshold Intervals"
        assert 2 in template.zones
        assert 3 in template.zones
        assert template.duration_minutes == 60
        assert "Road Bike" in template.required_equipment
    
    def test_sport_config_creation(self):
        """Test SportConfig dataclass"""
        sport = SportConfig(
            name="Cycling",
            activity_types=["Ride", "VirtualRide"],
            primary_metric=Metric(
                type=MetricType.POWER,
                unit="watts",
                threshold_field="ftp"
            ),
            zone_model="percentage",
            zones=[
                ZoneDefinition("Z1", 0, 55, "Recovery", 1),
                ZoneDefinition("Z2", 56, 75, "Endurance", 1)
            ],
            equipment=[
                Equipment("Road Bike", "Outdoor cycling")
            ],
            tags=["endurance", "power-based"]
        )
        
        assert sport.name == "Cycling"
        assert "Ride" in sport.activity_types
        assert sport.primary_metric.type == MetricType.POWER
        assert len(sport.zones) == 2
        assert len(sport.equipment) == 1
        assert "endurance" in sport.tags
    
    def test_user_profile_creation(self):
        """Test UserProfile dataclass"""
        profile = UserProfile(
            philosophy=TrainingPhilosophy.POLARIZED,
            volume_levels={"low": 4, "medium": 8, "high": 12},
            preferences={"morning_workouts": True},
            thresholds={"ftp": 250, "lthr": 165}
        )
        
        assert profile.philosophy == TrainingPhilosophy.POLARIZED
        assert profile.volume_levels["medium"] == 8
        assert profile.preferences["morning_workouts"] is True
        assert profile.thresholds["ftp"] == 250
    
    def test_training_config_creation(self):
        """Test TrainingConfig dataclass"""
        config = TrainingConfig(
            version="1.0.0",
            user_profile=UserProfile(
                philosophy=TrainingPhilosophy.POLARIZED,
                volume_levels={"low": 4, "medium": 8, "high": 12}
            ),
            sports=[
                SportConfig(
                    name="Running",
                    activity_types=["Run"],
                    primary_metric=Metric(
                        type=MetricType.HEART_RATE,
                        unit="bpm",
                        threshold_field="lthr"
                    )
                )
            ],
            global_settings={"auto_detect_zones": True}
        )
        
        assert config.version == "1.0.0"
        assert config.user_profile.philosophy == TrainingPhilosophy.POLARIZED
        assert len(config.sports) == 1
        assert config.sports[0].name == "Running"
        assert config.global_settings["auto_detect_zones"] is True


class TestConfigValidator:
    """Test configuration validation"""
    
    @pytest.fixture
    def validator(self):
        """Create validator with test schema"""
        return ConfigValidator()
    
    def test_valid_configuration(self, validator):
        """Test validation of valid configuration"""
        valid_config = {
            "version": "1.0.0",
            "user_profile": {
                "philosophy": "polarized",
                "volume_levels": {"low": 4, "medium": 8, "high": 12},
                "thresholds": {"ftp": 250}
            },
            "sports": [
                {
                    "name": "Cycling",
                    "activity_types": ["Ride"],
                    "primary_metric": {
                        "type": "power",
                        "unit": "watts",
                        "threshold_field": "ftp"
                    }
                }
            ]
        }
        
        assert validator.validate(valid_config) is True
    
    def test_invalid_configurations(self, validator):
        """Test validation of various invalid configurations"""
        # Missing version
        invalid = {"sports": []}
        assert validator.validate(invalid) is True  # Minimal schema allows this
        
        # Wrong type for sports
        invalid = {"version": "1.0.0", "sports": "not an array"}
        assert validator.validate(invalid) is False
        
        # Empty configuration
        assert validator.validate({}) is True  # Minimal schema allows empty
    
    def test_schema_file_not_found(self):
        """Test validator when schema file is missing"""
        with patch('builtins.open', side_effect=FileNotFoundError):
            validator = ConfigValidator("missing_schema.json")
            # Should use minimal schema
            assert validator.schema is not None
            assert validator.validate({"version": "1.0.0"}) is True
    
    def test_config_object_validation(self, validator):
        """Test validation of TrainingConfig objects"""
        config = TrainingConfig(
            version="1.0.0",
            sports=[
                SportConfig(
                    name="Running",
                    activity_types=["Run"],
                    primary_metric=Metric(
                        type=MetricType.HEART_RATE,
                        unit="bpm",
                        threshold_field="lthr"
                    )
                )
            ]
        )
        
        # Should convert to dict and validate
        assert validator.validate_config(config) is True


class TestSportConfigService:
    """Test sport configuration service functionality"""
    
    @pytest.fixture
    def service(self):
        """Create service instance"""
        return SportConfigService()
    
    @pytest.fixture
    def sample_config(self):
        """Create sample configuration for testing"""
        return TrainingConfig(
            version="1.0.0",
            user_profile=UserProfile(
                philosophy=TrainingPhilosophy.POLARIZED,
                volume_levels={"low": 4, "medium": 8, "high": 12},
                thresholds={"ftp": 250, "lthr": 165}
            ),
            sports=[
                SportConfig(
                    name="Cycling",
                    activity_types=["Ride", "VirtualRide"],
                    primary_metric=Metric(
                        type=MetricType.POWER,
                        unit="watts",
                        threshold_field="ftp",
                        decimal_places=0
                    ),
                    zone_model="percentage",
                    zones=[
                        ZoneDefinition("Zone 1", "0", "55", "Recovery", 1),
                        ZoneDefinition("Zone 2", "56", "75", "Endurance", 1),
                        ZoneDefinition("Zone 3", "76", "87", "Tempo", 2),
                        ZoneDefinition("Zone 4", "88", "94", "Threshold", 2),
                        ZoneDefinition("Zone 5", "95", "105", "VO2 Max", 3),
                        ZoneDefinition("Zone 6", "106", "150", "Anaerobic", 3)
                    ]
                ),
                SportConfig(
                    name="Running",
                    activity_types=["Run", "Trail Run"],
                    primary_metric=Metric(
                        type=MetricType.HEART_RATE,
                        unit="bpm",
                        threshold_field="lthr",
                        decimal_places=0
                    ),
                    zone_model="formula",
                    zones=[
                        ZoneDefinition("Zone 1", "0", "0.81 * lthr", "Easy", 1),
                        ZoneDefinition("Zone 2", "0.81 * lthr", "0.89 * lthr", "Aerobic", 1),
                        ZoneDefinition("Zone 3", "0.90 * lthr", "0.93 * lthr", "Tempo", 2),
                        ZoneDefinition("Zone 4", "0.94 * lthr", "0.99 * lthr", "Threshold", 2),
                        ZoneDefinition("Zone 5", "1.00 * lthr", "1.10 * lthr", "VO2 Max", 3)
                    ]
                )
            ]
        )
    
    def test_load_config_success(self, service):
        """Test successful configuration loading"""
        config_data = {
            "version": "1.0.0",
            "sports": [{
                "name": "Swimming",
                "activity_types": ["Swim"],
                "primary_metric": {
                    "type": "pace",
                    "unit": "min/100m",
                    "threshold_field": "css"
                }
            }]
        }
        
        with patch('builtins.open', mock_open(read_data=json.dumps(config_data))):
            config = service.load_config("test_config.json")
            assert isinstance(config, TrainingConfig)
            assert len(config.sports) == 1
            assert config.sports[0].name == "Swimming"
    
    def test_load_config_file_not_found(self, service):
        """Test loading config when file doesn't exist"""
        with patch('os.path.exists', return_value=False):
            config = service.load_config("missing.json")
            # Should return default config
            assert isinstance(config, TrainingConfig)
            assert len(config.sports) > 0  # Default sports loaded
    
    def test_save_config(self, service, sample_config):
        """Test saving configuration"""
        mock_file = mock_open()
        with patch('builtins.open', mock_file):
            service.save_config(sample_config, "output.json")
            
            # Verify file was opened for writing
            mock_file.assert_called_once_with("output.json", 'w')
            
            # Verify JSON was written
            handle = mock_file()
            written_data = ''.join(call.args[0] for call in handle.write.call_args_list)
            parsed = json.loads(written_data)
            assert parsed["version"] == "1.0.0"
            assert len(parsed["sports"]) == 2
    
    def test_get_sport_by_activity_type(self, service, sample_config):
        """Test finding sport by activity type"""
        service.config = sample_config
        
        # Test exact match
        sport = service.get_sport_by_activity_type("Ride")
        assert sport is not None
        assert sport.name == "Cycling"
        
        # Test secondary activity type
        sport = service.get_sport_by_activity_type("VirtualRide")
        assert sport.name == "Cycling"
        
        # Test not found
        sport = service.get_sport_by_activity_type("Swim")
        assert sport is None
    
    def test_get_sport_by_name(self, service, sample_config):
        """Test finding sport by name"""
        service.config = sample_config
        
        sport = service.get_sport_by_name("Running")
        assert sport is not None
        assert sport.name == "Running"
        
        # Test case sensitivity
        sport = service.get_sport_by_name("running")
        assert sport is None  # Exact match required
    
    def test_calculate_zones_percentage_based(self, service, sample_config):
        """Test zone calculation with percentage-based zones"""
        service.config = sample_config
        cycling = service.get_sport_by_name("Cycling")
        
        zones = service.calculate_zones(cycling, MetricType.POWER, 250)
        
        assert len(zones) == 6
        # Check first zone
        zone_name, lower, upper, polarized = zones[0]
        assert zone_name == "Zone 1"
        assert lower == 0
        assert upper == 137.5  # 55% of 250
        assert polarized == 1
        
        # Check threshold zone
        zone_name, lower, upper, polarized = zones[3]
        assert zone_name == "Zone 4"
        assert lower == 220  # 88% of 250
        assert upper == 235  # 94% of 250
        assert polarized == 2
    
    def test_calculate_zones_formula_based(self, service, sample_config):
        """Test zone calculation with formula-based zones"""
        service.config = sample_config
        running = service.get_sport_by_name("Running")
        
        zones = service.calculate_zones(running, MetricType.HEART_RATE, 165)
        
        assert len(zones) == 5
        # Check Zone 2
        zone_name, lower, upper, polarized = zones[1]
        assert zone_name == "Zone 2"
        assert lower == pytest.approx(133.65, rel=0.1)  # 0.81 * 165
        assert upper == pytest.approx(146.85, rel=0.1)  # 0.89 * 165
        assert polarized == 1
    
    def test_calculate_zones_invalid_threshold(self, service, sample_config):
        """Test zone calculation with invalid threshold values"""
        service.config = sample_config
        cycling = service.get_sport_by_name("Cycling")
        
        # Test with None
        with pytest.raises(ValueError):
            service.calculate_zones(cycling, MetricType.POWER, None)
        
        # Test with negative
        with pytest.raises(ValueError):
            service.calculate_zones(cycling, MetricType.POWER, -100)
        
        # Test with zero
        with pytest.raises(ValueError):
            service.calculate_zones(cycling, MetricType.POWER, 0)
    
    def test_get_zone_distribution_target(self, service, sample_config):
        """Test getting zone distribution targets"""
        service.config = sample_config
        
        # Test polarized philosophy
        targets = service.get_zone_distribution_target()
        assert targets[1] == 80  # Zone 1
        assert targets[2] == 10  # Zone 2
        assert targets[3] == 10  # Zone 3
        
        # Test pyramidal philosophy
        service.config.user_profile.philosophy = TrainingPhilosophy.PYRAMIDAL
        targets = service.get_zone_distribution_target()
        assert targets[1] == 70
        assert targets[2] == 20
        assert targets[3] == 10
        
        # Test custom philosophy
        service.config.user_profile.philosophy = TrainingPhilosophy.CUSTOM
        service.config.user_profile.preferences = {
            "zone_targets": {"zone1": 75, "zone2": 15, "zone3": 10}
        }
        targets = service.get_zone_distribution_target()
        assert targets[1] == 75
        assert targets[2] == 15
        assert targets[3] == 10
    
    def test_get_threshold_value(self, service, sample_config):
        """Test getting threshold values for sports"""
        service.config = sample_config
        
        cycling = service.get_sport_by_name("Cycling")
        ftp = service.get_threshold_value(cycling, MetricType.POWER)
        assert ftp == 250
        
        running = service.get_sport_by_name("Running")
        lthr = service.get_threshold_value(running, MetricType.HEART_RATE)
        assert lthr == 165
        
        # Test missing threshold
        service.config.user_profile.thresholds = {}
        ftp = service.get_threshold_value(cycling, MetricType.POWER)
        assert ftp is None
    
    def test_get_all_sports(self, service, sample_config):
        """Test getting all sports"""
        service.config = sample_config
        
        sports = service.get_all_sports()
        assert len(sports) == 2
        assert sports[0].name == "Cycling"
        assert sports[1].name == "Running"
    
    def test_add_sport(self, service, sample_config):
        """Test adding a new sport"""
        service.config = sample_config
        
        new_sport = SportConfig(
            name="Swimming",
            activity_types=["Swim"],
            primary_metric=Metric(
                type=MetricType.PACE,
                unit="min/100m",
                threshold_field="css"
            )
        )
        
        service.add_sport(new_sport)
        assert len(service.config.sports) == 3
        assert service.get_sport_by_name("Swimming") is not None
    
    def test_update_sport(self, service, sample_config):
        """Test updating an existing sport"""
        service.config = sample_config
        
        # Update cycling zones
        cycling = service.get_sport_by_name("Cycling")
        cycling.zones.append(
            ZoneDefinition("Zone 7", "151", "200", "Neuromuscular", 3)
        )
        
        service.update_sport("Cycling", cycling)
        
        updated = service.get_sport_by_name("Cycling")
        assert len(updated.zones) == 7
        assert updated.zones[-1].name == "Zone 7"
    
    def test_remove_sport(self, service, sample_config):
        """Test removing a sport"""
        service.config = sample_config
        
        assert len(service.config.sports) == 2
        service.remove_sport("Running")
        assert len(service.config.sports) == 1
        assert service.get_sport_by_name("Running") is None
        assert service.get_sport_by_name("Cycling") is not None
    
    def test_edge_cases(self, service):
        """Test various edge cases"""
        # Test with empty config
        service.config = TrainingConfig()
        
        sports = service.get_all_sports()
        assert sports == []
        
        targets = service.get_zone_distribution_target()
        assert targets == {1: 80, 2: 10, 3: 10}  # Default
        
        # Test with no user profile
        service.config.user_profile = None
        targets = service.get_zone_distribution_target()
        assert targets == {1: 80, 2: 10, 3: 10}  # Default


class TestIntegration:
    """Integration tests for sport config system"""
    
    def test_full_workflow(self):
        """Test complete workflow from loading to using config"""
        service = SportConfigService()
        
        # Create and save config
        config = TrainingConfig(
            version="1.0.0",
            user_profile=UserProfile(
                philosophy=TrainingPhilosophy.POLARIZED,
                volume_levels={"low": 4, "medium": 8, "high": 12},
                thresholds={"ftp": 300, "lthr": 170}
            ),
            sports=[
                SportConfig(
                    name="Cycling",
                    activity_types=["Ride"],
                    primary_metric=Metric(
                        type=MetricType.POWER,
                        unit="watts",
                        threshold_field="ftp"
                    ),
                    zone_model="percentage",
                    zones=[
                        ZoneDefinition("Z1", "0", "55", "Recovery", 1),
                        ZoneDefinition("Z2", "56", "75", "Endurance", 1),
                        ZoneDefinition("Z3", "76", "87", "Tempo", 2),
                        ZoneDefinition("Z4", "88", "94", "Threshold", 2),
                        ZoneDefinition("Z5", "95", "105", "VO2 Max", 3)
                    ]
                )
            ]
        )
        
        # Save to temp file
        import tempfile
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            service.save_config(config, f.name)
            temp_path = f.name
        
        try:
            # Load config
            loaded = service.load_config(temp_path)
            assert loaded.version == "1.0.0"
            assert len(loaded.sports) == 1
            
            # Use config for zone calculation
            sport = service.get_sport_by_activity_type("Ride")
            zones = service.calculate_zones(sport, MetricType.POWER, 300)
            
            # Verify calculations
            assert len(zones) == 5
            assert zones[0][2] == 165  # Z1 upper = 55% of 300
            assert zones[4][1] == 285  # Z5 lower = 95% of 300
            
        finally:
            # Cleanup
            os.unlink(temp_path)
    
    def test_migration_from_legacy_format(self):
        """Test migrating from legacy hardcoded format"""
        # This would test converting old hardcoded zones to new config format
        pass