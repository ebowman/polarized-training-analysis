#!/usr/bin/env python3
"""
Sport Configuration System - Base Classes and Schema Validation

This module implements the foundation for a flexible, sport-agnostic
configuration system that replaces hardcoded sport-specific logic.
"""

import json
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass, field
from enum import Enum
import jsonschema
from pathlib import Path


class TrainingPhilosophy(Enum):
    """Training philosophy types"""
    POLARIZED = "polarized"
    PYRAMIDAL = "pyramidal"
    THRESHOLD = "threshold"
    CUSTOM = "custom"


class ZoneModelType(Enum):
    """Zone calculation model types"""
    PERCENTAGE = "percentage"
    FORMULA = "formula"
    ABSOLUTE = "absolute"
    CUSTOM = "custom"


class MetricType(Enum):
    """Supported metric types"""
    POWER = "power"
    HEART_RATE = "heart_rate"
    PACE = "pace"
    SPEED = "speed"
    CUSTOM = "custom"


@dataclass
class ZoneDefinition:
    """Definition of a training zone"""
    name: str
    lower: Union[float, str]  # Can be percentage, formula, or absolute value
    upper: Union[float, str]
    description: str = ""
    polarized_zone: int = 1  # Maps to 3-zone model (1, 2, or 3)


@dataclass
class Metric:
    """Metric configuration"""
    type: MetricType
    unit: str
    threshold_field: str  # Field name for threshold value (e.g., "ftp", "lthr")
    decimal_places: int = 0
    custom_formula: Optional[str] = None


@dataclass
class Equipment:
    """Equipment definition"""
    name: str
    description: str
    capabilities: List[str] = field(default_factory=list)
    default_duration_minutes: Optional[int] = None
    supports_metrics: List[MetricType] = field(default_factory=list)


@dataclass
class WorkoutTemplate:
    """Workout template definition"""
    name: str
    description: str
    zones: List[int]  # List of zone numbers
    structure: str
    duration_minutes: Optional[int] = None
    required_equipment: List[str] = field(default_factory=list)


@dataclass
class SportConfig:
    """Configuration for a single sport"""
    name: str
    activity_types: List[str]  # Strava activity types that map to this sport
    primary_metric: Metric
    secondary_metric: Optional[Metric] = None
    zone_model: str = "percentage"  # percentage, formula, absolute, custom
    zones: List[ZoneDefinition] = field(default_factory=list)
    equipment: List[Equipment] = field(default_factory=list)
    workout_templates: List[WorkoutTemplate] = field(default_factory=list)
    custom_fields: Dict[str, Any] = field(default_factory=dict)
    tags: List[str] = field(default_factory=list)  # Support for tagging (e.g., 'ancillary')
    zone_distribution: Optional[Dict[int, float]] = None  # Override zone distribution for this sport


@dataclass
class UserProfile:
    """User training profile configuration"""
    philosophy: TrainingPhilosophy
    volume_levels: Dict[str, int]  # low, medium, high hours per week
    preferences: Dict[str, Any] = field(default_factory=dict)
    thresholds: Dict[str, float] = field(default_factory=dict)  # ftp, lthr, etc.


@dataclass
class TrainingConfig:
    """Complete training configuration"""
    version: str = "1.0.0"
    user_profile: UserProfile = None
    sports: List[SportConfig] = field(default_factory=list)
    global_settings: Dict[str, Any] = field(default_factory=dict)


class ConfigValidator:
    """Validates configuration against JSON schema"""
    
    def __init__(self, schema_path: Optional[str] = None):
        self.schema_path = schema_path or "sport_config_schema.json"
        self._load_schema()
    
    def _load_schema(self):
        """Load JSON schema from file"""
        try:
            with open(self.schema_path, 'r') as f:
                self.schema = json.load(f)
        except FileNotFoundError:
            # Use minimal schema if file not found
            self.schema = {
                "$schema": "http://json-schema.org/draft-07/schema#",
                "type": "object",
                "properties": {
                    "version": {"type": "string"},
                    "user_profile": {"type": "object"},
                    "sports": {"type": "array"}
                }
            }
    
    def validate(self, config_dict: Dict[str, Any]) -> bool:
        """Validate configuration dictionary against schema"""
        try:
            jsonschema.validate(instance=config_dict, schema=self.schema)
            return True
        except jsonschema.exceptions.ValidationError as e:
            print(f"Configuration validation error: {e.message}")
            return False
    
    def validate_config(self, config: TrainingConfig) -> bool:
        """Validate TrainingConfig object"""
        config_dict = self._config_to_dict(config)
        return self.validate(config_dict)
    
    def _config_to_dict(self, config: TrainingConfig) -> Dict[str, Any]:
        """Convert TrainingConfig to dictionary for validation"""
        return {
            "version": config.version,
            "user_profile": self._user_profile_to_dict(config.user_profile) if config.user_profile else {},
            "sports": [self._sport_to_dict(sport) for sport in config.sports],
            "global_settings": config.global_settings
        }
    
    def _user_profile_to_dict(self, profile: UserProfile) -> Dict[str, Any]:
        """Convert UserProfile to dictionary"""
        return {
            "philosophy": profile.philosophy.value,
            "volume_levels": profile.volume_levels,
            "preferences": profile.preferences,
            "thresholds": profile.thresholds
        }
    
    def _sport_to_dict(self, sport: SportConfig) -> Dict[str, Any]:
        """Convert SportConfig to dictionary"""
        return {
            "name": sport.name,
            "activity_types": sport.activity_types,
            "primary_metric": self._metric_to_dict(sport.primary_metric),
            "secondary_metric": self._metric_to_dict(sport.secondary_metric) if sport.secondary_metric else None,
            "zone_model": sport.zone_model,
            "zones": [self._zone_to_dict(zone) for zone in sport.zones],
            "equipment": [self._equipment_to_dict(eq) for eq in sport.equipment],
            "workout_templates": [self._template_to_dict(tmpl) for tmpl in sport.workout_templates],
            "custom_fields": sport.custom_fields,
            "tags": sport.tags,
            "zone_distribution": sport.zone_distribution if sport.zone_distribution else None
        }
    
    def _metric_to_dict(self, metric: Metric) -> Dict[str, Any]:
        """Convert Metric to dictionary"""
        return {
            "type": metric.type.value,
            "unit": metric.unit,
            "threshold_field": metric.threshold_field,
            "decimal_places": metric.decimal_places,
            "custom_formula": metric.custom_formula
        }
    
    def _zone_to_dict(self, zone: ZoneDefinition) -> Dict[str, Any]:
        """Convert ZoneDefinition to dictionary"""
        return {
            "name": zone.name,
            "lower": zone.lower,
            "upper": zone.upper,
            "description": zone.description,
            "polarized_zone": zone.polarized_zone
        }
    
    def _equipment_to_dict(self, equipment: Equipment) -> Dict[str, Any]:
        """Convert Equipment to dictionary"""
        return {
            "name": equipment.name,
            "description": equipment.description,
            "capabilities": equipment.capabilities,
            "default_duration_minutes": equipment.default_duration_minutes,
            "supports_metrics": [m.value for m in equipment.supports_metrics]
        }
    
    def _template_to_dict(self, template: WorkoutTemplate) -> Dict[str, Any]:
        """Convert WorkoutTemplate to dictionary"""
        return {
            "name": template.name,
            "description": template.description,
            "zones": template.zones,
            "structure": template.structure,
            "duration_minutes": template.duration_minutes,
            "required_equipment": template.required_equipment
        }


class ConfigLoader:
    """Loads configuration from various sources"""
    
    @staticmethod
    def from_file(file_path: str) -> TrainingConfig:
        """Load configuration from JSON file"""
        with open(file_path, 'r') as f:
            config_dict = json.load(f)
        return ConfigLoader.from_dict(config_dict)
    
    @staticmethod
    def from_dict(config_dict: Dict[str, Any]) -> TrainingConfig:
        """Create TrainingConfig from dictionary"""
        config = TrainingConfig(
            version=config_dict.get("version", "1.0.0"),
            global_settings=config_dict.get("global_settings", {})
        )
        
        # Load user profile
        if "user_profile" in config_dict:
            profile_dict = config_dict["user_profile"]
            config.user_profile = UserProfile(
                philosophy=TrainingPhilosophy(profile_dict["philosophy"]),
                volume_levels=profile_dict.get("volume_levels", {}),
                preferences=profile_dict.get("preferences", {}),
                thresholds=profile_dict.get("thresholds", {})
            )
        
        # Load sports
        for sport_dict in config_dict.get("sports", []):
            sport = ConfigLoader._load_sport(sport_dict)
            config.sports.append(sport)
        
        return config
    
    @staticmethod
    def _load_sport(sport_dict: Dict[str, Any]) -> SportConfig:
        """Load SportConfig from dictionary"""
        # Load primary metric
        primary_metric_dict = sport_dict["primary_metric"]
        primary_metric = Metric(
            type=MetricType(primary_metric_dict["type"]),
            unit=primary_metric_dict["unit"],
            threshold_field=primary_metric_dict["threshold_field"],
            decimal_places=primary_metric_dict.get("decimal_places", 0),
            custom_formula=primary_metric_dict.get("custom_formula")
        )
        
        # Load secondary metric if exists
        secondary_metric = None
        if sport_dict.get("secondary_metric"):
            sec_metric_dict = sport_dict["secondary_metric"]
            secondary_metric = Metric(
                type=MetricType(sec_metric_dict["type"]),
                unit=sec_metric_dict["unit"],
                threshold_field=sec_metric_dict["threshold_field"],
                decimal_places=sec_metric_dict.get("decimal_places", 0),
                custom_formula=sec_metric_dict.get("custom_formula")
            )
        
        sport = SportConfig(
            name=sport_dict["name"],
            activity_types=sport_dict["activity_types"],
            primary_metric=primary_metric,
            secondary_metric=secondary_metric,
            zone_model=sport_dict.get("zone_model", "percentage"),
            custom_fields=sport_dict.get("custom_fields", {}),
            tags=sport_dict.get("tags", []),
            zone_distribution=sport_dict.get("zone_distribution")
        )
        
        # Load zones
        for zone_dict in sport_dict.get("zones", []):
            zone = ZoneDefinition(
                name=zone_dict["name"],
                lower=zone_dict["lower"],
                upper=zone_dict["upper"],
                description=zone_dict.get("description", ""),
                polarized_zone=zone_dict.get("polarized_zone", 1)
            )
            sport.zones.append(zone)
        
        # Load equipment
        for eq_dict in sport_dict.get("equipment", []):
            equipment = Equipment(
                name=eq_dict["name"],
                description=eq_dict["description"],
                capabilities=eq_dict.get("capabilities", []),
                default_duration_minutes=eq_dict.get("default_duration_minutes"),
                supports_metrics=[MetricType(m) for m in eq_dict.get("supports_metrics", [])]
            )
            sport.equipment.append(equipment)
        
        # Load workout templates
        for tmpl_dict in sport_dict.get("workout_templates", []):
            template = WorkoutTemplate(
                name=tmpl_dict["name"],
                description=tmpl_dict["description"],
                zones=tmpl_dict["zones"],
                structure=tmpl_dict["structure"],
                duration_minutes=tmpl_dict.get("duration_minutes"),
                required_equipment=tmpl_dict.get("required_equipment", [])
            )
            sport.workout_templates.append(template)
        
        return sport


def create_default_config() -> TrainingConfig:
    """Create a default configuration for backward compatibility"""
    config = TrainingConfig()
    
    # Default user profile (polarized training)
    config.user_profile = UserProfile(
        philosophy=TrainingPhilosophy.POLARIZED,
        volume_levels={"low": 5, "medium": 10, "high": 15},
        thresholds={"ftp": 250, "lthr": 165},
        preferences={"zone_distribution": {1: 80.0, 2: 10.0, 3: 10.0}}
    )
    
    # Default cycling configuration
    cycling = SportConfig(
        name="Cycling",
        activity_types=["Ride", "VirtualRide"],
        primary_metric=Metric(
            type=MetricType.POWER,
            unit="watts",
            threshold_field="ftp"
        ),
        secondary_metric=Metric(
            type=MetricType.HEART_RATE,
            unit="bpm",
            threshold_field="lthr"
        ),
        zone_model="percentage"
    )
    
    # Add default cycling zones (Coggan power zones mapped to 3-zone)
    cycling.zones = [
        ZoneDefinition("Recovery", 0, 55, "Easy recovery", 1),
        ZoneDefinition("Endurance", 56, 75, "Aerobic endurance", 1),
        ZoneDefinition("Tempo", 76, 90, "Moderate effort", 2),
        ZoneDefinition("Threshold", 91, 105, "Lactate threshold", 2),
        ZoneDefinition("VO2 Max", 106, 120, "Maximum aerobic power", 3),
        ZoneDefinition("Anaerobic", 121, 150, "Short intense efforts", 3),
        ZoneDefinition("Neuromuscular", 151, 200, "Sprint power", 3)
    ]
    
    config.sports.append(cycling)
    
    # Default running configuration
    running = SportConfig(
        name="Running",
        activity_types=["Run"],
        primary_metric=Metric(
            type=MetricType.HEART_RATE,
            unit="bpm",
            threshold_field="lthr"
        ),
        zone_model="percentage"
    )
    
    # Add default running zones
    running.zones = [
        ZoneDefinition("Zone 1", 0, 85, "Easy aerobic", 1),
        ZoneDefinition("Zone 2", 85, 89, "Moderate aerobic", 1),
        ZoneDefinition("Zone 3", 90, 94, "Threshold", 2),
        ZoneDefinition("Zone 4", 95, 99, "VO2 Max", 3),
        ZoneDefinition("Zone 5", 100, 110, "Max effort", 3)
    ]
    
    config.sports.append(running)
    
    return config